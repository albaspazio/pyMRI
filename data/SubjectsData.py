import os
from typing import List

import numpy as np
import pandas
import pandas as pd

from data.utilities import demean_serie, FilterValues
from data.SubjectSD import SubjectSD
from data.SubjectSDList import SubjectSDList
from utility.exceptions import DataFileException
from utility.list import same_elements, unique, indices
from utility.utilities import argsort, reorder_list

# =====================================================================================
# DATA MANAGEMENT WITH PANDA
# =====================================================================================
# assumes that the first column represents subjects' labels, and the second their session.
# The combination of these two columns must be unique and represent the KEY to obtain subject's rows within the db
# the class creates an internal property df:DataFrame filled with either an excel or a csv (by default tabbed) text file

# there is a property (subjects) which represent all subjects' three main information (id, label, session) and store in a list of SubjectSD instance (SubjectSDList)
# id is the index within the dataframe

# there is one method (filter_subjects) that select/filter subjects from a list of subjects label, their sessions and a list of conditions over other columns values
# all methods accessing/selecting subject(s) receive either a SubjectSD or SubjectSDList instance obtained using "filter_subjects"

# data can be selected/extracted in six ways, each returning a different type:
# - labels str                      : subjects (@)
# - indices                         : subj_ids (@), subj_session_id (@)
# - DF                              : select_df (*,@), select_columns_df, select_rows_df (*,@)
# - Dict | List[Dict]               : get_subject_session, get_subjects (*,@)
# - Value | List[] |List[List[]]    : get_subject_col_value, get_subjects_column, get_subjects_values_by_cols
# - List[], subjects             : get_filtered_column (*)

# method with (*) can further select only specific rows among those given according to columns values
# method with (@) can specify the desidered sessions or all sessions (giving sessions=[])

# the method returning values (without subj information) cannot further select,
# otherwise caller wouldn't know which subjects/rows were not removed
# to do this, exist for a single column: get_filtered_column which return a tuple = [values], [subjlabels]

# CAN ALSO return a list of subjlabels that fullfil all the given conditions (==, >, <, <==>,..) on specific columns

class SubjectsData():

    first_col_name  = "subj"
    second_col_name = "session"

    def __init__(self, data=None, validcols=None, cols2num=None, delimiter='\t', check_data=True):

        super().__init__()
        self.filepath = data
        self.df = None
        if data is not None:
            self.load(data, validcols, cols2num, delimiter, check_data)

        self.valid_dtypes = ['Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'float64', 'float32']

    # =========================================================================================================
    # region PROPERTIES
    @property
    def header(self) -> list:
        if self.df is None:
            return []
        else:
            return list(self.df.columns.values)

    @property
    def num(self) -> int:
        return self.df.shape[0]

    @property
    def isValid(self) -> bool:
        return self.first_col_name in self.header and self.second_col_name in self.header

    @property
    def subjects(self) -> SubjectSDList:
        return SubjectSDList([SubjectSD(index, row[self.first_col_name], row[self.second_col_name]) for index, row in self.df.iterrows()])

    # endregion

    # =====================================================================================
    # DATA EXTRACTION FROM A "SUBJ" DICTIONARY {"a_subj_label":{"a":..., "b":...., }}
    # must include a subject columns !!!
    # validcols=[list of column to include]
    # cols2num defines whether checking string(ed) type and convert them: cols2num must be a list of:
    #       1) string: all listed columns are converted to float
    #       2) dictionary: each listed columns is converted to a specific type [{"colname":"type"}, ....]
    # filepath CANNOT be empty
    def load(self, data, validcols: list = None, cols2num: list = None, delimiter='\t', check_data=True) -> pandas.DataFrame:

        if isinstance(data, str):

            if not os.path.exists(data):
                raise DataFileException("SubjectsData.load", "given filepath param (" + data + ") is not a file")

            if data.endswith(".csv") or data.endswith(".dat") or data.endswith(".txt"):
                self.df     = pd.read_csv(data, delimiter=delimiter)
            elif data.endswith(".xls") or data.endswith(".xlsx"):
                self.df     = pd.read_excel(data)
            else:
                raise Exception("Error in SubjectData.load: unknown data file format")

        elif isinstance(data, pandas.DataFrame):
            self.df = data
        else:
            raise Exception("Error in SubjectData.load: unknown data format, not a str, not a pandas.DataFrame")

        # verify first column is called "subj" and second "session"
        if check_data:
            if self.df.columns[0] != self.first_col_name or self.df.columns[1] != self.second_col_name:
                raise Exception("Error in SubjectData.load: first column is not called subj")

        # check unnamed columns
        for col in self.header:
            if "unnamed" in col.lower():
                self.remove_columns([col], update=True)

        # filter columns
        if validcols is not None:
            self.select_columns_df(validcols, update=True)

        # convert data
        if cols2num is not None:
            if isinstance(cols2num[0], str):
                for c in cols2num:
                    self.df[c].astype(float)
            elif isinstance(cols2num[0], dict):
                for c in cols2num:
                    if list(c.keys())[0] not in self.header:
                        raise Exception("SubjectsData.load", "asked to convert columns. but one given entry of cols2num (" + list(c.keys())[0] + ") does not indicate an existing column")

                    if list(c.values())[0] not in self.valid_dtypes:
                        raise Exception("SubjectsData.load", "asked to convert columns. but one given entry of cols2num (" + list(c.values())[0] + ") does not indicate a valid data type")
                    self.df.astype(c)

        return self.df

    # ======================================================================================
    #region GET SubjectSDList
    # only methods the select a SubjectSDList managing a list of subjects' label, sessios and filtering conditions on other columns
    def filter_subjects(self, subj_labels:List[str]=None, sessions:List[int]=None, conditions:List[FilterValues]=None) -> SubjectSDList:

        if subj_labels is None:
            subj_labels = self.subjects.labels

        subjs = SubjectSDList([s for s in self.subjects if s.label in subj_labels])

        if sessions is not None:
            if isinstance(sessions, int):
                sessions = [sessions for s in subjs.labels]     # 1-fill
            subjs = SubjectSDList([s for s in subjs if s.session in sessions])

        if conditions is not None:
            res = []
            for s in subjs:
                add = True
                for selcond in conditions:
                    if not selcond.isValid(self.get_subject_col_value(s, selcond.colname)):
                        add = False
                if add:
                    res.append(s)
            return SubjectSDList(res)
        else:
            return subjs

    #endregion

    # ======================================================================================
    #region GET a DataFrame subset
    # SUBSET self.DF or given DF by rows and cols
    # may further select only those rows that respect all the select_conds
    def select_df(self, subjs:SubjectSDList=None, validcols:List[str]=None, df:pandas.DataFrame=None, update=False) -> pandas.DataFrame:

        if df is None:
            df = self.df.copy()

        if subjs is None and validcols is None:
            return df

        df = self.select_rows_df(subjs, df, False)
        df = self.select_columns_df(validcols, df, False).copy()

        if update:
            self.df = df

        return df

    # extract only columns contained in given validcols
    def select_columns_df(self, validcols:List[str]=None, df:pandas.DataFrame=None, update=False) -> pandas.DataFrame:

        if df is None:
            df = self.df.copy()

        if validcols is None:
            return df
        else:
            vcs = validcols.copy()
            for vc in vcs:
                if vc not in self.header:
                    raise Exception("Error in SubjectsData.filter_columns: given validcols list contains a column (" + vc + ") not present in the original df...exiting")

            if update:
                self.df = df[vcs]
                return self.df
            else:
                return df[vcs].copy()

    # extract only rows contained in given subjects
    # if(select_conds) -> apply AND filter = keep only those rows that fullfil all the specified conditions
    def select_rows_df(self, subjs:SubjectSDList=None, df:pandas.DataFrame=None, update=False) -> pandas.DataFrame:

        if df is None:
            df = self.df.copy()

        if subjs is None:
            subjs = self.subjects

        newdf   = pd.DataFrame()
        rows    = df.iloc[subjs.ids]
        newdf   = newdf._append(rows, ignore_index=True)

        # for s in subjs:
        #     sids = self.subj_ids(slab, sessions, df)
        #
        #     if select_conds is None:
        #         rows = df.iloc[sids]
        #         newdf = newdf._append(rows, ignore_index=True)
        #     else:
        #         for sid in sids:
        #             add = True
        #             row = df.iloc[sid]
        #
        #             for selcond in select_conds:
        #                 if not selcond.isValid(self.get_subject_session_col_value(sid, selcond.colname)):
        #                     add = False
        #             if add:
        #                 newdf = newdf._append(row, ignore_index=True)

        if update is True:
            self.df = newdf

        return newdf

    #endregion

    # ======================================================================================
    #region GET subject(s) as dict or List[dict]
    def get_subject(self, subj:SubjectSD, validcols:List[str]=None) -> dict:
        if subj.id >= self.num:
            raise Exception("Error in get_subject: given id (" + subj.id + ") exceeds the total number of elements")

        if validcols is None:
            validcols = self.header
        else:
            for vc in validcols:
                if vc not in self.header:
                    raise Exception("Error in SubjectsData.filter_columns: given validcols list contains a column (" + vc + ") not present in the original df...exiting")
        return self.df.loc[subj.id, validcols].to_dict()

    # def get_subjects(self, subj_labels:List[str]=None, sessions:List[int]=[1], validcols:List[str]=None, select_conds:List[FilterValues]=None) -> List[dict]:
    def get_subjects(self, subjs:SubjectSDList=None, validcols:List[str]=None) -> List[dict]:
        df = self.select_df(subjs, validcols)
        return [row.to_dict() for index, row in df.iterrows()]
    #endregion

    # ======================================================================================
    #region GET subjects labels (select some rows within the given list of subjects)
    def select_subjlist(self, subj_labels:List[str]=None, sessions:List[int]=[1], colconditions:List[FilterValues]=None) -> List[str]:
        return self.filter_subjects(subj_labels, sessions, colconditions).labels
    #endregion

    # ======================================================================================
    # region GET Values as:
    # - single value (of a subjlab/colname)
    # - List[colvalues]
    # - List[List] of colnames x subjs values
    # they DO NOT filter conditions
    def get_subject_col_value(self, subj:SubjectSD, colname:str):
        try:
            if colname not in self.header:
                raise Exception("get_subject_col_value error: colname (" + colname + ") is not present in df")
            else:
                return self.get_subject(subj)[colname]
        except Exception as e:
            raise Exception("get_subject_session_col_value error: subj_id=" + subj.id + ", colname:" + colname)

    # return a list of values from a given column
    def get_subjects_column(self, subjs:SubjectSDList=None, colname:str = None, df: pandas.DataFrame = None) -> list:

        if df is None:
            df = self.df.copy()

        if colname is None:
            return []
        else:
            if colname not in list(df.columns.values):
                raise Exception("get_column error: colname (" + colname + ") is not present in df")

            df = self.select_rows_df(subjs)
            return list(df[colname])

    # returns a filtered matrix [colnames x subjs] of values
    def get_subjects_values_by_cols(self, subjs:SubjectSDList=None, colnames:List[str]=None, demean_flags:List[bool]=None, ndecim:int=4) -> list:

        # before a select_df, given columns must contain both keys (subj_label and session)
        if len(colnames) > 0:
            if "subj" not in colnames:
                newcols = ["subj"] + colnames
            elif "session" not in colnames:
                newcols = ["session"] + colnames
            else:
                newcols = colnames
        else:
            newcols = colnames

        df = self.select_df(subjs, newcols)
        try:
            # create ncols x nsubj array
            values = [self.get_subjects_column(subjs, colname, df) for colname in colnames]

            if demean_flags is not None:
                if len(colnames) != len(demean_flags):
                    msg = "Error in get_filtered_columns...lenght of colnames is different from demean_flags"
                    raise Exception(msg)
                else:
                    # demean requested columns
                    for idcol, dem_col in enumerate(demean_flags):
                        if dem_col:
                            values[idcol] = demean_serie(values[idcol], ndecim)

        except KeyError as k:
            raise DataFileException("SubjectsData.get_subjects_values_by_cols", "")

        return values
    #endregion

    # ======================================================================================
    #region GET two vectors (values, valid subjlabels) within the given [subj labels]
    def get_filtered_column(self, subjs:SubjectSDList=None, colname=None, sort=False, demean=False, ndecim=4) -> tuple:

        if colname is None:
            raise Exception("Error in SubjectsData.get_filtered_column: colname is None")

        if subjs is None:
            subjs = self.subjects

        res = self.get_subjects_column(subjs, colname)

        if demean:
            res = demean_serie(res, ndecim)

        if sort:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(subjs.labels, sort_schema)

        return res, subjs.labels
    #endregion

    # ======================================================================================
    # region GET string Value (of a subjlab/colname) or List[string colvalues] or a List[List] of colnames x subjs string values
    # the list of subjects' values of each column are transformed in a single string with values separated by \n
    def get_subject_session_col_value_str(self, subj:SubjectSD, colname:str, ndecimals:int=3):
        return self.__to_str([self.get_subject_col_value(subj, colname)], ndecimals)

    def get_subjects_column_str(self, subjs:SubjectSDList=None, colname=None, ndecimals=3):
        return self.__to_str(self.get_subjects_column(subjs, colname), ndecimals)

    def get_subjects_values_by_cols_str(self, subjs:SubjectSDList=None, colnames:List[str]=None, demean_flags:List[bool]=None, ndecim:int=4):
        values  = self.get_subjects_values_by_cols(subjs, colnames)
        res_str = []
        for colvalues in values:
            res_str.append(self.__to_str(colvalues, ndecim))
        return res_str
    #endregion

    # ==================================================================================================
    # region ADD/UPDATE DATA

    def set_subj_session_value(self, subj:SubjectSD, col_label: str, value):
        if col_label not in self.header:
            raise Exception("Error in SubjectsData.set_subj_value: given col_label does not belong to header")
        else:
            col_id = self.col_id(col_label)

        self.df.iat[subj.id, col_id] = value

    # add new subjects: can be
    # - List[SubjectsData] e.g. several object containing one subject only
    # - List[SubjectsData] one item that contains in its df several subjects
    def add_sd(self, newsubjs:List['SubjectsData'], can_overwrite=False, can_add_incomplete=False) -> None:

        if not isinstance(newsubjs, list):
            raise Exception("Error in SubjectsData.add_sd, given newsubjs is not a list")
        else:
            if not isinstance(newsubjs[0], SubjectsData):
                raise Exception("Error in SubjectsData.add, newsubjs is not a list of SubjectsData")

        for subj in newsubjs:
            if isinstance(subj, SubjectsData):

                if subj.df.columns[0] != self.first_col_name or subj.df.columns[1] != self.second_col_name:
                    raise Exception("Error in SubjectsData.add, SubjectsData does not contain subj column as 1st one or sessions as second")

                self.df = pd.concat([self.df, subj.df], ignore_index=True)

            elif isinstance(subj, dict):
                df = pandas.DataFrame.from_dict(subj)
                self.df = pd.concat([self.df, df], ignore_index=True)

            else:
                raise Exception("Error in SubjectsData.add, an element of newsubjs is not a SubjectsData")

    # add new columns / update existing columns to existing subjects (cannot add new subjects)
    def add_columns_df(self, subjsdf: pandas.DataFrame, can_overwrite=False, can_add_incomplete=False):

        if not isinstance(subjsdf, pandas.DataFrame):
            raise Exception("Error in SubjectsData.add_columns_df, given subjsdf is not a DataFrame")

        new_sd = SubjectsData(subjsdf)

        if new_sd.subjects.is_in(self.subjects):
            subjsdf = subjsdf.drop(self.first_col_name)
            subjsdf = subjsdf.drop(self.second_col_name)
            for col in subjsdf.columns.values:
                if col in self.header:
                    if can_overwrite:
                        self.update_column(new_sd.subjects, col, subjsdf[col])
                    else:
                        print("Warning in SubjectsData.add_df...col (" + col + ") already exist and can_overwrite is False...skipping add this column")
                        return
                else:
                    self.add_column(col, subjsdf[col], new_sd.subjects)
        else:
            print("Warning in SubjectsData.add_columns_df...trying to add new columns, but new subjects are also present...skipping this operation")

    def add_column(self, col_label, values, subjs:SubjectSDList=None, position=None, df=None):

        if col_label in self.header:
            raise Exception("Error in SubjectsData add_column: col_label (" + col_label + ") already exist...exiting")

        if subjs is None:
            subjs = self.subjects

        if position is None:
            position = len(self.header)     # add as last column

        nv = len(values)
        nl = len(subjs)

        if nv != nl:
            if nv == 1:
                values      = [ values[0] for s in subjs]   # if given value is just one, duplicate it for each subject
            else:
                raise Exception("Error in SubjectsData.add_column, n value (" + str(nv) + ") != n subjs (" + str(nl) + ")")

        nanvalues   = [ np.nan for s in subjs]
        self.df.insert(position, column=col_label, value=nanvalues)

        for i, s in enumerate(subjs):
            self.df.at[s.id, col_label] = values[i]

        if df is not None:
            self.save_data(df)

    def update_column(self, subjs:SubjectSDList, col_label, values, df=None):

        if col_label not in self.header:
            raise Exception("Error in SubjectsData add_column: update_column (" + col_label + ") does not exist...exiting")

        nv = len(values)
        nl = len(subjs)

        if nv != nl:
            raise Exception("Error in SubjectsData.add_column, n value (" + str(nv) + ") != n subjs (" + str(nl) + ")")

        for i,s in enumerate(subjs):
            # ids = self.subj_ids(val)
            self.df.at[s.id, col_label] = values[i]

        if df is not None:
            self.save_data(df)

    # if row is None adds only a subj col
    def add_row(self, subj:SubjectSD, row=None):

        if self.exist_subjects(SubjectSDList([subj])):
            raise Exception("Error in SubjectsData.add_row. subject (" + subj.label + ") already exist")

        if row is None:
            row = {self.first_col_name: subj.label, self.second_col_name: subj.session}

        self.df.loc[len(self.df)] = row

    # assoc_dict is a dictionary where key is current name and value is the new one
    def rename_subjects(self, assoc_dict):

        for i, (k_oldlab, v_newlab) in enumerate(assoc_dict.items()):
            subj_id = self.get_subjid_by_session(k_oldlab)
            self.df.iloc[subj_id][self.first_col_name] = v_newlab

    # endregion

    # ==================================================================================================
    # region REMOVE SUBJ DATA
    def remove_subjects(self, subjects2remove:SubjectSDList, df:pandas.DataFrame=None, update=False):

        if df is None:
            df = self.df.copy()

        labels  = list(df[self.first_col_name])

        for subj in subjects2remove:
            # ids = labels.index(subjlab)
            df.drop([subj.id], inplace=True)
            df.reset_index(drop=True, inplace=True)

        sd = SubjectsData(df)

        if update:
            self.df = df

        return sd

    def remove_columns(self, cols2remove:List[str], df:pandas.DataFrame=None, update=False):

        if not isinstance(cols2remove, list):
            raise Exception("Error in SubjectsData.remove_columns: given cols param is not a list")

        if df is None:
            df = self.df.copy()

        for col in cols2remove:
            if col in list(df.columns.values):
                df = df.drop(col, axis=1)

        if update:
            self.df = df

        return df

    # endregion

    # ==================================================================================================
    # region EXIST
    def get_subj_session(self, subj_lab:str, session:int=1) -> SubjectSD:
        if ((self.df[self.first_col_name] == subj_lab) & (self.df[self.second_col_name] == session)).any():
            id = self.get_subjid_by_session(subj_lab, session)[0]
            return SubjectSD(id, subj_lab, session)
        else:
            return None

    def exist_subjects(self, subjs:SubjectSDList) -> bool:
        return subjs.is_in(self.subjects)
        # return all(item in self.subj_labels for id, item in enumerate(subjs_labels))

    def exist_column(self, colname):
        return colname in self.header

    def exist_filled_column(self, colname, subjs:SubjectSDList=None):

        if not self.exist_column(colname):
            return False

        if subjs is None:
            subjs = self.subjects

        for s in subjs:
            elem = self.get_subject_col_value(s, colname)
            if len(str(elem)) == 0:
                return False
        return True
    #endregion

    # ======================================================================================
    #region ACCESSORY

    def get_subjid_by_session(self, subj_lab:str, session:int=1, df=None) -> int:

        if df is None:
            df = self.df.copy()

        return df.index[(df["session"] == session) & (df["subj"] == subj_lab)]

    def get_subject_available_sessions(self, subj_lab:str, df=None) -> List[int]:

        if df is None:
            df = self.df.copy()

        mask    = df["subj"].isin(subj_lab)
        df      = df[mask]

        return list(df["session"])

    def is_cell_not_empty(self, subj_id:int, col_str:str=None, df=None) -> bool:

        if df is None:
            df = self.df.copy()

        if col_str not in df.columns.values[:]:
            raise Exception("SubjectsData.is_cell_not_empty: given col (" + str(col_str) + ") does not exist in df")

        col_id = self.col_id(col_str, df)

        try:
            return not df.isnull().iloc[subj_id, col_id]
        except:
            raise Exception("SubjectsData.is_cell_not_empty: given col (" + str(col_str) + ") does not exist in df")

    def is_cell_empty(self, subj_id:int, col_str:str=None, df=None) -> bool:
        return not self.is_cell_not_empty(subj_id, col_str, df)

    def col_id(self, col_lab, df=None) -> int:
        if df is None:
            df = self.df.copy()
        return df.columns.get_loc(col_lab)

    def validate_covs(self, covs)-> None:

        # if all(elem in header for elem in regressors) is False:  if I don't want to understand which cov is absent
        missing_covs = ""
        for cov in covs:
            if not cov.name in self.header:
                missing_covs = missing_covs + cov.name + ", "

        if len(missing_covs) > 0:
            raise DataFileException("validate_covs", "the following header are NOT present in the given datafile: " + missing_covs)

    # save some columns of a subset of the subjects in given file
    def save_data(self, outdata_file=None, subjs:SubjectSDList=None, incolnames=None, outcolnames=None, separator="\t"):

        if outdata_file is None:
            outdata_file = self.filepath

        if incolnames is None:
            incolnames = self.header

        df = self.select_columns_df(incolnames) # get a copy of all the rows of the given incolnames

        # rename columns if asked
        if outcolnames is not None:
            if len(outcolnames) != len(incolnames):
                raise Exception("Error in SubjectsData.save_data: given outcolnames length differs from column number")
            else:
                df.columns.values[:] = outcolnames

        df = self.select_rows_df(subjs, df)

        if outdata_file.endswith(".csv") or outdata_file.endswith(".dat") or outdata_file.endswith(".txt"):
            df.to_csv(outdata_file, sep=separator, index=False)
        elif outdata_file.endswith(".xls") or outdata_file.endswith(".xlsx"):
            df.to_excel(outdata_file, index=False)
        else:
            raise Exception("Error in SubjectData.load: unknown data file format")

    def is_equal(self, sd:'SubjectsData') -> bool:

        report = ""
        if not same_elements(self.header, sd.header):
            report = report + "different header"
            return False

        if not same_elements(self.subjects.labels, sd.subjects.labels):
            report = report + "\ndifferent subjects"
            return False

        for col in self.header:
            col_values = self.get_subjects_column(colname=col)
            if not same_elements(col_values, sd.get_subjects_column(colname=col)):
                report = report + "\ndifferent values in col: " + col

        if report != "":
            print("SubjectsData.is_equal the two data are different")
            return False

    def outlier(self, colname, _range=1.5, df:pandas.DataFrame=None):

        if df is None:
            df = self.df.copy()

        Q1 = df[colname].quantile(0.25)
        Q3 = df[colname].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - _range * IQR
        upper_bound = Q3 + _range * IQR
        outliers = df[(df[colname] < lower_bound) | (df[colname] > upper_bound)]

    # get a data list and return a \n separated string, suitable for spm template files
    @staticmethod
    def __to_str(datalist, ndecimals=3):

        datastr = ""
        for r in datalist:
            rr = str(round(r * ndecimals * 10) / (ndecimals * 10))
            datastr = datastr + rr + "\n"
        return datastr

    #endregion

    # =====================================================================================
