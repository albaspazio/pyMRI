import csv
import os

import pandas
import pandas as pd
from collections import Counter

from typing import List

from data.utilities import demean_serie, FilterValues
from utility.list import same_elements
from utility.exceptions import DataFileException
from utility.utilities import argsort, reorder_list, string2num, listToString
from utility.fileutilities import write_text_file


# =====================================================================================
# DATA MANAGEMENT WITH PANDA
# =====================================================================================
# assumes that the first column represents subjects' labels
# creates an internal property df:DataFrame filled with either an excel or a csv (by default tabbed) text file

# data can be extracted in four ways:
# - DF                              : select_df (***), select_columns_df, select_rows_df (***)
# - Dict | List[Dict]               : get_subject, get_subjects (***)
# - Value | List[] |List[List[]]    : get_subject_col_value, get_subjects_column, get_subjects_values_by_cols
# - List[], subj_labels             : get_filtered_column (***)
# method with (***) can further select only specific rows among those given according to columns values
# the method returning values (without subj information) cannot further select,
# otherwise caller wouldn't know which subjects/rows were not removed
# to do this, exist for a single column: get_filtered_column which return a tuple = [values], [subjlabels]

# CAN ALSO return a list of subjlabels that fullfil all the given conditions (==, >, <, <==>,..) on specific columns

class SubjectsData():

    first_col_name = "subj"
    def __init__(self, data=None, validcols=None, cols2num=None, delimiter='\t', suppress_nosubj=True):

        super().__init__()
        self.filepath = data
        self.df = None
        if data is not None:
            self.load(data, validcols, cols2num, delimiter, suppress_nosubj)

        self.valid_dtypes = ['Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'float64', 'float32']

    @property
    def header(self) -> list:
        if self.df is None:
            return []
        else:
            return list(self.df.columns.values)

    @property
    def subj_labels(self) -> list:
        return list(self.df[self.first_col_name])

    @property
    def num(self) -> int:
        return self.df.shape[0]

    @property
    def isValid(self) -> bool:
        return self.first_col_name in self.header

    def is_cell_not_empty(self, subj, col, df):

        if df is None:
            df = self.df

        if col not in df.columns.values[:]:
            raise Exception("SubjectsData.is_cell_not_empty: given col (" + str(col) + ") does not exist in df")

        if isinstance(subj, str):
            subj = self.subj_id(subj, df)

        if isinstance(col, str):
            col = self.col_id(col, df)

        try:
            return not self.df.isnull().iloc[subj, col]
        except:
            raise Exception("SubjectsData.is_cell_not_empty: given col (" + str(col) + ") does not exist in df")

    def is_cell_empty(self, subj, col, df=None):
        if df is None:
            df = self.df
        return not self.is_cell_not_empty(subj, col, df)

    # =====================================================================================
    # DATA EXTRACTION FROM A "SUBJ" DICTIONARY {"a_subj_label":{"a":..., "b":...., }}
    # =====================================================================================

    # must include a subject columns !!!
    # validcols=[list of column to include]
    # cols2num defines whether checking string(ed) type and convert them: cols2num must be a list of:
    #       1) string: all listed columns are converted to float
    #       2) dictionary: each listed columns is converted to a specific type [{"colname":"type"}, ....]
    # filepath CANNOT be empty
    def load(self, data, validcols:list=None, cols2num:list=None, delimiter='\t', suppress_nosubj=True) -> pandas.DataFrame:

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

        # verify first column is called "subj"
        if self.df.columns[0] != self.first_col_name:
            if suppress_nosubj:
                self.df.columns.values[0] = self.first_col_name
                print("Warning in SubjectData.load: first column was not called subj, I renamed it to subj....check if it's ok")
            else:
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
    #region select (GET a DataFrame subset)
    # SUBSET self.DF or given DF by rows and cols
    # may further select only those rows that respect all the select_conds
    def select_df(self, subj_labels:List[str]=None, validcols:List[str]=None, df:pandas.DataFrame=None, update=False, select_conds:List[FilterValues]=None) -> pandas.DataFrame:

        if df is None:
            df = self.df.copy()

        if subj_labels is None and validcols is None:
            return df

        df = self.select_rows_df(subj_labels, df, False, select_conds=select_conds)
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

    # extract only rows contained in given subj_labels
    # if(select_conds) -> apply AND filter = keep only those rows that fullfil all the specified conditions
    def select_rows_df(self, subj_labels:List[str]=None, df:pandas.DataFrame=None, update=False, select_conds:List[FilterValues]=None) -> pandas.DataFrame:

        if df is None:
            df = self.df.copy()

        if subj_labels is None:
            subj_labels = self.subj_labels

        newdf = pd.DataFrame()

        for slab in subj_labels:
            add = True

            sid = self.subj_id(slab, df)
            row = df.iloc[[sid]]

            if select_conds is not None:
                for selcond in select_conds:
                    if not selcond.isValid(self.get_subject_col_value(slab, selcond.colname)):
                        add = False
            if add:
                newdf = newdf._append(row, ignore_index=True)

        if update is True:
            self.df = newdf
        return newdf

    #endregion

    # ======================================================================================
    #region GET subject(s) as dict or List[dict]
    def get_subject(self, subj_lab:str, validcols:List[str]=None) -> dict:
        if subj_lab not in self.subj_labels:
            raise Exception("Error in get_subject: given label (" + subj_lab + ") is not present in df")

        if validcols is None:
            validcols = self.header
        else:
            for vc in validcols:
                if vc not in self.header:
                    raise Exception("Error in SubjectsData.filter_columns: given validcols list contains a column (" + vc + ") not present in the original df...exiting")
        return self.df.loc[self.subj_id(subj_lab), validcols].to_dict()

    def get_subjects(self, subj_labels:List[str]=None, validcols:List[str]=None, select_conds:List[FilterValues]=None) -> List[dict]:

        df = self.select_df(subj_labels, validcols, select_conds=select_conds)
        return [row.to_dict() for index, row in df.iterrows()]
    #endregion

    # ======================================================================================
    #region GET subjects labels (select some rows within the given list of subjects)
    def select_subjlist(self, subj_labels:List[str]=None, colconditions:List[FilterValues]=None) -> List[str]:

        if subj_labels is None:
            subj_labels = self.subj_labels

        df = self.df.copy()

        for cond in colconditions:

            # df = self.select_df(subj_labels, [self.first_col_name, cond.colname], df)
            new_slab = []
            for s in subj_labels:
                if cond.isValid(self.get_subject_col_value(s, cond.colname)):
                    new_slab.append(s)
            subj_labels = new_slab

        if len(subj_labels) == 0:
            print("Warning: SubjectsData.select_subjlist returned an empty list")
        return subj_labels
    #endregion

    # ======================================================================================
    # region GET Values as:
    # - single value (of a subjlab/colname)
    # - List[colvalues]
    # - List[List] of colnames x subjs values
    # they DO NOT filter conditions
    def get_subject_col_value(self, subj_lab:str, colname:str):
        try:
            if colname not in self.header:
                raise Exception("get_subject_col_value error: colname (" + colname + ") is not present in df")
            else:
                return self.get_subject(subj_lab)[colname]
        except Exception as e:
            raise Exception("get_subject_col_value error: slabel=" + subj_lab + ", colname:" + colname)

    # return a list of values from a given column
    def get_subjects_column(self, subj_labels:List[str]=None, colname:str = None, df: pandas.DataFrame = None) -> list:
        if df is None:
            if not self.exist_column(colname):
                raise Exception("get_column error: colname (" + colname + ") is not present in df")
            else:
                df = self.select_rows_df(subj_labels)
                return list(df[colname])
        else:
            # TODO still no check
            df = self.select_rows_df(subj_labels, df)
            return list(df[colname])

    # returns a filtered matrix [colnames x subjs] of values
    def get_subjects_values_by_cols(self, subj_labels:List[str]=None, colnames:List[str]=None, demean_flags:List[bool]=None, ndecim:int=4) -> list:

        df = self.select_df(subj_labels, colnames)
        try:
            # create ncols x nsubj array
            values = [self.get_subjects_column(subj_labels, colname, df=df) for colname in colnames]

            if demean_flags is not None:
                if len(colnames) != len(demean_flags):
                    msg = "Error in get_filtered_columns...lenght of colnames is different from demean_flags"
                    raise Exception(msg)
                else:
                    # demean requested columns
                    for idcol, dem_col in enumerate(demean_flags):
                        if dem_col:
                            values[idcol] = demean_serie(values[idcol], ndecim)

        except KeyError:
            raise DataFileException("SubjectsData.get_subjects_values_by_cols", "data of given subject (" + subj + ") is not present in the loaded data")

        return values
    #endregion

    # ======================================================================================
    #region returns two vectors (values, valid subjlabels) within the given [subj labels]
    def get_filtered_column(self, subj_labels: List[str] = None, colname=None, sort=False, demean=False, ndecim=4, select_conds:List[FilterValues]=None):

        if colname is None:
            raise Exception("Error in SubjectsData.get_filtered_column: colname is None")

        if subj_labels is None:
            subj_labels = self.subj_labels

        subj_labels = self.select_subjlist(subj_labels, select_conds)
        res         = self.get_subjects_column(subj_labels, colname)

        if demean:
            res = demean_serie(res, ndecim)

        if sort:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(subj_labels, sort_schema)

        return res, subj_labels
    #endregion

    # ======================================================================================
    # region GET string Value (of a subjlab/colname) or List[string colvalues] or a List[List] of colnames x subjs string values
    # the list of subjects' values of each column are transformed in a single string with values separated by \n
    def get_subject_col_value_str(self, subj_lab:str, colname:str, ndecimals:int=3):
        return self.__to_str([self.get_subject_col_value(subj_lab, colname)], ndecimals)

    def get_column_str(self, subj_labels=None, colname=None, ndecimals=3):
        return self.__to_str(self.get_subjects_column(subj_labels, colname), ndecimals)

    def get_subjects_values_str_by_cols(self, subj_labels:List[str]=None, colnames:List[str]=None, demean_flags:List[bool]=None, ndecim:int=4):
        values  = self.get_subjects_values_by_cols(subj_labels, colnames)
        res_str = []
        for colvalues in values:
            res_str.append(self.__to_str(colvalues, ndecimals))
        return res_str
    #endregion

    # ==================================================================================================
    # region ADD/UPDATE DATA

    def set_subj_value(self, subj, col_label: str, value):

        if isinstance(subj, str):
            ids = self.subj_id(subj)
        elif isinstance(subj, int):
            ids = subj
        else:
            raise Exception("Error in SubjectsData.set_subj_value: subj value is neither a string nor an int")

        self.df.at[ids, col_label] = value

    # add new subjects: can be
    # - List[SubjectsData] e.g. several object containing one subject only
    # - List[SubjectsData] one item that contains in its df several subjects
    # - List[Dict
    def add_sd(self, newsubjs: list, can_overwrite=False, can_add_incomplete=False) -> None:

        if not isinstance(newsubjs, list):
            raise Exception("Error in SubjectsData.add_sd, given newsubjs is not a list")
        else:
            if not isinstance(newsubjs[0], SubjectsData):
                raise Exception("Error in SubjectsData.add, newsubjs is not a list of SubjectsData")

        for subj in newsubjs:
            if isinstance(subj, SubjectsData):

                if subj.df.columns[0] != self.first_col_name:
                    raise Exception("Error in SubjectsData.add, SubjectsData does not contain subj column as 1st one")

                self.df = pd.concat([self.df, subj.df], ignore_index=True)

            elif isinstance(subj, dict):
                df = pandas.DataFrame.from_dict(subj)
                self.df = pd.concat([self.df, df], ignore_index=True)

            else:
                raise Exception("Error in SubjectsData.add, an element of newsubjs is not a SubjectsData")

    # add new columns / update existing columns to existing subjects (cannot add new subjects(
    def add_columns_df(self, subjsdf: pandas.DataFrame, can_overwrite=False, can_add_incomplete=False):

        if not isinstance(subjsdf, pandas.DataFrame):
            raise Exception("Error in SubjectsData.add_Df, given subjsdf is not a DataFrame")

        subjs_labels = subjsdf[self.first_col_name]
        if self.exist_subjects(subjs_labels):
            subjsdf = subjsdf.drop(self.first_col_name)
            for col in subjsdf.columns.values:
                if col in self.header:
                    if can_overwrite:
                        self.update_column(col, subjs_labels, subjsdf[col])
                    else:
                        print("Warning in SubjectsData.add_df...col (" + col + ") already exist and can_overwrite is False...skipping add this column")
                        return
                else:
                    self.add_column(col, subjs_labels, subjsdf[col])

    def add_column(self, col_label, labels, values, data_file=None):

        if col_label in self.header:
            raise Exception("Error in SubjectsData add_column: col_label (" + col_label + ") already exist...exiting")

        nv = len(values)
        nl = len(labels)

        if nv != nl:
            raise Exception("Error in SubjectsData.add_column, n value (" + str(nv) + ") != n subjs (" + str(nl) + ")")

        self.df[col_label] = np.nan

        for i, val in enumerate(labels):
            ids = self.subj_id(val)
            self.df.at[ids, col_label] = values[i]

        if data_file is not None:
            self.save_data(data_file)

    def update_column(self, col_label, labels, values, data_file=None):

        if col_label not in self.header:
            raise Exception(
                "Error in SubjectsData add_column: update_column (" + col_label + ") does not exist...exiting")

        nv = len(values)
        nl = len(labels)

        if nv != nl:
            raise Exception("Error in SubjectsData.add_column, n value (" + str(nv) + ") != n subjs (" + str(nl) + ")")

        for i, val in enumerate(labels):
            ids = self.subj_id(val)
            self.df.at[ids, col_label] = values[i]

        if data_file is not None:
            self.save_data(data_file)

    # if row is None adds only a subj col
    def add_row(self, subj_label, row=None):

        if subj_label in self.subj_labels:
            raise Exception("Error in SubjectsData.add_row. subject (" + subj_label + ") already exist")

        if row is None:
            row = {self.first_col_name: subj_label}

        self.df.loc[len(self.df)] = row

    # endregion

    # ==================================================================================================
    # region REMOVE SUBJ DATA
    def remove_subjects(self, subjects2remove:List[str], update=False):

        df = self.df.copy()

        for subjlab in subjects2remove:
            labels = list(df[self.first_col_name])
            ids = labels.index(subjlab)
            df.drop([df.index[ids]], inplace=True)
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

    # ======================================================================================
    #region ACCESSORY
    def exist_subject(self, subj_lab) -> bool:
        try:
            return subj_lab in self.subj_labels
        except:
            return False

    def exist_subjects(self, subjs_labels:List[str]) -> bool:
        return all(item in self.subj_labels for item in subjs_labels)

    def subj_id(self, subj_lab, df=None) -> int:
        if df is None:
            return self.subj_labels.index(subj_lab)
        else:
            return list(df[self.first_col_name]).index(subj_lab)

    def col_id(self, col_lab, df=None) -> int:
        if df is None:
            df = self.df
        return df.columns.get_loc(col_lab)

    def validate_covs(self, covs)-> None:

        # if all(elem in header for elem in regressors) is False:  if I don't want to understand which cov is absent
        missing_covs = ""
        for cov in covs:
            if not cov.name in self.header:
                missing_covs = missing_covs + cov.name + ", "

        if len(missing_covs) > 0:
            raise DataFileException("validate_covs", "the following header are NOT present in the given datafile: " + missing_covs)

    def exist_column(self, colname):
        return colname in self.header

    def exist_filled_column(self, colname, subj_labels=None):

        if not self.exist_column(colname):
            return False

        if subj_labels is None:
            labs = self.subj_labels
        else:
            labs = subj_labels

        for lab in labs:
            elem = self.get_subject_col_value(lab, colname)
            if len(str(elem)) == 0:
                return False
        return True

    # save some columns of a subset of the subjects in given file
    def save_data(self, outdata_file=None, subj_labels=None, incolnames=None, outcolnames=None, separator="\t"):

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

        df = self.select_rows_df(subj_labels, df)

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

        if not same_elements(self.subj_labels, sd.subj_labels):
            report = report + "\ndifferent subjects"
            return False

        for col in self.header:
            col_values = self.get_subjects_column(colname=col)
            if not same_elements(self.subj_labels, sd.subj_labels):
                report = report + "\ndifferent values in col: " + col

        if report != "":
            print("SubjectsData.is_equal the two data are different")
            return False

    # assoc_dict is a dictionary where key is current name and value is the new one
    def rename_subjects(self, assoc_dict):

        for i, (k_oldlab, v_newlab) in enumerate(assoc_dict.items()):
            subj_id                         = self.subj_id(k_oldlab)
            self.df.iloc[subj_id][self.first_col_name]   = v_newlab

    def outlier(self, colname, _range=1.5, df:pandas.DataFrame=None):

        if df is None:
            df = self.df

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
