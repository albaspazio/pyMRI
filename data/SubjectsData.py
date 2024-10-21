from __future__ import annotations

import os
from typing import List, Any, Tuple

import numpy as np
import pandas
import pandas as pd
from pandas import DataFrame

from data.SID import SID
from data.SIDList import SIDList
from data.utilities import demean_serie, FilterValues
from myutility.exceptions import DataFileException
from myutility.list import same_elements, reorder_list, _argsort


# =====================================================================================
# DATA MANAGEMENT WITH PANDA
# =====================================================================================
# assumes that the first column represents subjects' labels, and the second their session.
# The combination of these two columns must be unique and represent the KEY to obtain subject's rows within the db
# the class creates an internal property df:DataFrame filled with either an excel or a csv (by default tabbed) text file.
# @ init, data are always sorted by the first two columns in ascending order

# there is a property (subjects) which contains a list of SID instances (SIDList), SID is a class specifying the three main information (id, label, session) of a session
# id is the index within the dataframe. Almost all methods accept a SID(List) that link label, session and a specific row in the df

# there are only two methods that do not deal with SID/SIDS:
#  1) filter_subjects: accept as input a list of subject labels their sessions and list of conditions over other columns values and return a SIDList
#                       this method takes all the responsability to filter by session and conditions
#  2) get_sid:          accept one subject label and one sessions and return the associated SID or raise a DataFileException

# ALL other methods accessing/selecting subject(s) data receive either a SID or SIDList instance obtained using "filter_subjects"/get_sid

# data can be selected/extracted in six ways, each returning a different type:
# - SID | SIDList | SIDList         : get_sid (@), filter_subjects (*,@), subjects
# - SubjectsData                    : extract_subjset
# - DF                              : select_df, select_columns_df, select_rows_df
# - Dict | List[Dict]               : get_sid_dict, get_sids_dict
# - Value | List[] |List[List[]]    : get_subject_col_value, get_subjects_column, get_subjects_values_by_cols
# - str | List[str] | str           : get_subject_col_value_str, get_subjects_column_str, get_subjects_values_by_cols_str

# - List[str]                       : subjects_labels
# - indices                         : subj_ids, subj_session_id

# method with (*) can select only specific rows among those given according to columns values
# method with (@) can specify the desired sessions or all sessions (giving sessions=[])


class SubjectsData:
    """
    This class provides an interface to a data frame containing subject data.
    The data frame must contain two columns: "subj" and "session", which contain the subject label and session, respectively.
    """

    first_col_name          = "subj"
    second_col_name         = "session"
    df: pandas.DataFrame    = None

    def __init__(self, data:str|pandas.DataFrame|None=None, validcols:List[str]=None, cols2num:List[str]|dict=None, delimiter:str='\t', check_data:bool=True):
        """
        Initialize the SubjectsData object.

        Parameters
        ----------
        data : str or pandas.DataFrame, optional
            The file path or a pandas.DataFrame object.
        validcols : List[str], optional
            A list of column names to include in the data. If None, all columns will be included.
        cols2num : List[str] | dict, optional
            A list of column names or a dictionary of column names and data types. If a column name is listed, all values in the column will be converted to a float. If a dictionary is given, each column will be converted to the specified data type.
        delimiter : str, optional
            The delimiter used in the file. Only applicable when loading from a file.
        check_data : bool, optional
            Whether to check that the data contains the required columns, always to be done but when importing data that temporaneously may not have them (e.g when importing bayes etero or VolBrain files).

        Returns
        -------
        None

        Raises
        ------
        DataFileException
            If the given file path does not exist or if the file format is not supported.
        Exception
            If the data contains an invalid column name or if the data type conversion is not supported.
        """
        self.filepath   = data
        self.df         = pandas.DataFrame()
        if data is not None:
            self.load(data, validcols, cols2num, delimiter, check_data)

        self.valid_dtypes = ['Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'float64', 'float32']

    def load(self, data: str | pandas.DataFrame, validcols: List[str] = None, cols2num: List[str] | dict = None,
             delimiter: str = '\t', check_data: bool = True) -> pandas.DataFrame:
        """
        Load data from a file or a pandas.DataFrame.
        cols2num defines whether checking string(ed) type and convert them: cols2num must be a list of:
              1) string: all listed columns are converted to float
              2) dictionary: each listed columns is converted to a specific type [{"colname":"type"}, ....]

        Parameters
        ----------
        data : str or pandas.DataFrame
            The file path or a pandas.DataFrame object.
        validcols : List[str], optional
            A list of column names to include in the data. If None, all columns will be included.
        cols2num : List[str]|dict, optional
            A list of column names or a dictionary of column names and data types. If a column name is listed, all values in the column will be converted to a float. If a dictionary is given, each column will be converted to the specified data type.
        delimiter : str, optional
            The delimiter used in the file. Only applicable when loading from a file.
        check_data : bool, optional
            Whether to check that the data contains the required columns.

        Returns
        -------
        pandas.DataFrame
            The loaded data.

        Raises
        ------
        DataFileException
            If the given file path does not exist or if the file format is not supported.
        Exception
            If the data contains an invalid column name or if the data type conversion is not supported.
        """
        if isinstance(data, str):
            # Check if the given file path exists
            if not os.path.exists(data):
                raise DataFileException("SubjectsData.load", "given filepath param (" + data + ") is not a file")

            # Determine the file format and load the data
            if data.endswith(".csv") or data.endswith(".dat") or data.endswith(".txt"):
                self.df = pd.read_csv(data, delimiter=delimiter)
            elif data.endswith(".xls") or data.endswith(".xlsx"):
                self.df = pd.read_excel(data, dtype={self.first_col_name: str})
            else:
                raise Exception("Error in SubjectData.load: unknown data file format")

        elif isinstance(data, pandas.DataFrame):
            self.df = data

        else:
            raise Exception("Error in SubjectData.load: unknown data format, not a str, not a pandas.DataFrame")

        # Verify that the data contains the required columns and then sort
        if check_data:
            if self.df.columns[0] != self.first_col_name or self.df.columns[1] != self.second_col_name:
                raise Exception("Error in SubjectData.load: first column is not called subj")
            # sort by first two columns
            self.df.sort_values([self.first_col_name, self.second_col_name], ascending=[True, True], inplace=True)

        # Check for unnamed columns and remove them
        for col in self.header:
            if "unnamed" in col.lower():
                self.remove_columns([col], update=True)

        # Filter the columns
        if validcols is not None:
            self.select_columns_df(validcols, update=True)

        # Convert the data
        if cols2num is not None:
            if isinstance(cols2num[0], str):
                for c in cols2num:
                    self.df[c].astype(float)
            elif isinstance(cols2num[0], dict):
                for c in cols2num:
                    if list(c.keys())[0] not in self.header:
                        raise DataFileException("SubjectsData.load", "asked to convert columns. but one given entry of cols2num (" + list(c.keys())[0] + ") does not indicate an existing column")

                    if list(c.values())[0] not in self.valid_dtypes:
                        raise DataFileException("SubjectsData.load", "asked to convert columns. but one given entry of cols2num (" + list(c.values())[0] + ") does not indicate a valid data type")
                    self.df.astype(c)

        # sort by first two columns
        self.df.sort_values([self.first_col_name, self.second_col_name], ascending=[True, True], inplace=True)

        return self.df

    # =========================================================================================================
    # region PROPERTIES
    @property
    def header(self) -> list:
        """
        Returns the header of the data frame.

        Returns
        -------
        list
            The header of the data frame.
        """
        if self.df is None:
            return []
        else:
            return self.df.columns.to_list()

    @property
    def num(self) -> int:
        """
        Returns the number of rows in the data frame.

        Returns
        -------
        int
            The number of rows in the data frame.
        """
        return self.df.shape[0]

    @property
    def isValid(self) -> bool:
        """
        Returns whether the data frame contains the required columns.

        Returns
        -------
        bool
            Whether the data frame contains the required columns.
        """
        return self.first_col_name in self.header and self.second_col_name in self.header

    @property
    def subjects(self) -> SIDList:
        """
        Returns a list of SID objects.

        Returns
        -------
        SIDList
            A list of SID objects.
        """
        return SIDList([SID(row[self.first_col_name], row[self.second_col_name], index) for index, row in self.df.iterrows()])

    @property
    def subjects_labels(self) -> List[str]:
        """
        Returns a unique list of labels of all subjects.

        Returns:
            List[str]: A list of strings representing the labels of the subjects.
        """
        slab = []
        for s in self.subjects:
            if s.label not in slab:
                slab.append(s.label)
        return slab

    # endregion

    # ==================================================================================================
    # region EXIST -> bool

    def exist_subject_session(self, subj_lab:str, sess_id:int=1) -> bool:
        return ((self.df[self.first_col_name] == subj_lab) & (self.df[self.second_col_name] == sess_id)).any()

    def exist_subjects_session(self, subj_labels:List[str], sess_id:int=1) -> bool:
        for subj in subj_labels:
            if self.exist_subject_session(subj, sess_id) is False:
                return False
        return True

    def exist_subjects(self, sids: SIDList) -> bool:
        """
        Returns whether the given list of subjects exists in the data frame.

        Parameters:
            sids (SIDList): The list of subjects to check.

        Returns:
            bool: Whether the given list of subjects exists in the data frame.
        """
        return len(sids.is_in(self.subjects)) == len(sids)
        # return all(item in self.subj_labels for id, item in enumerate(subjs_labels))

    def exist_column(self, colname: str) -> bool:
        """
        Returns whether a given column exists in the data frame.

        Parameters:
            colname (str): The name of the column to check.

        Returns:
            bool: Whether the given column exists in the data frame.
        """
        return colname in self.header

    def exist_filled_column(self, colname, sids: SIDList = None) -> bool:
        """
        Returns whether a given column contains non-empty values for a given list of subjects.

        Parameters:
            colname (str): The name of the column to check.
            sids (SIDList): A list of subjects to check. If None, all subjects will be checked.

        Returns:
            bool: Whether the given column contains non-empty values for the given list of subjects.
        """
        if not self.exist_column(colname):
            return False

        if sids is None:
            sids = self.subjects

        for s in sids:
            elem = self.get_subject_col_value(s, colname)
            if len(str(elem)) == 0:
                return False
        return True
    #endregion ->

    # ======================================================================================
    #region (labels, session, [conds]) -> SID/SIDList
    # only methods of SubjectsData that returns a SIDList given a list of subjects' label, sessions and filtering conditions on other columns
    def filter_subjects(self, subj_labels: List[str] = None, sess_ids: List[int] = None,
                        conditions: List[FilterValues] = None) -> SIDList:
        """
        Filter subjects based on their labels, sessions, and conditions on other columns.

        Parameters
        ----------
        subj_labels: List[str], optional
            A list of subject labels to include. If None, all subjects will be included.
        sess_ids: List[int], optional
            A list of sessions to include. If None, all sessions will be included.
        conditions: List[FilterValues], optional
            A list of conditions to apply. If None, no conditions will be applied.

        Returns
        -------
        SIDList
            A list of filtered subjects.

        Raises
        -------
        DataFileException
            If subjects selected in previous steps does not have data contained in the select_cond

        """
        if subj_labels is None:
            subj_labels = self.subjects.labels

        sids:SIDList = SIDList()

        for slab in subj_labels:
            if sess_ids is None:
                # for each subject, I get all its sessions
                sess_ids = self.get_subject_available_sessions(slab)
            else:
                # for each subject, I get only given sessions
                sess_ids = sess_ids

            for sess in sess_ids:
                sids.append(self.get_sid(slab, sess))

        if conditions is not None:
            res = []
            for sid in sids:
                add = True
                for selcond in conditions:
                    if not selcond.isValid(self.get_subject_col_value(sid, selcond.colname)):
                        add = False
                if add:
                    res.append(sid)
            return SIDList(res)
        else:
            return sids

    def get_sid(self, subj_lab: str, sess_id: int = 1, must_exist:bool=True) -> SID | None:
        """
        Returns the subject with the given subject label and session, if it exists in the data frame.
        if not raise DataFileException if must_exist=True or simply return None if must_exist = False

        Parameters:
            subj_lab (str): The subject label.
            sess_id (int): The session number.
            must_exist (bool): set whether raising DataFileException or return None

        Returns:
            SID: The subject with the given subject label and session, if it exists in the data frame. Otherwise, returns None.
        """
        if self.exist_subject_session(subj_lab, sess_id):
            id_ = self.get_subjid_by_session(subj_lab, sess_id)
            return SID(subj_lab, sess_id, id_)
        else:
            if must_exist is True:
                raise DataFileException("Error in SubjectsData.get_sid: given subj (" + subj_lab + "|" + sess_id + ") does not exist")
            else:
                return None

    #endregion

    # ======================================================================================
    #region (SIDS|conditions) -> SIDS
    def filter_sids(self, conditions: List[FilterValues], sids: SIDList = None) -> SIDList:
        """
        Filter SIDList based on conditions on other columns.

        Parameters
        ----------
        sids: SIDList, optional
            A list of SIDS to filter. If None, all subjects will be included.
        conditions: List[FilterValues], optional
            A list of conditions to apply. If None, no conditions will be applied.

        Returns
        -------
        SIDList
            A list of filtered subjects.

        Raises
        -------
        DataFileException
            If subjects selected in previous steps does not have data contained in the select_cond

        """
        if sids is None:
            sids = self.subjects

        if conditions is not None:
            res = []
            for sid in sids:
                add = True
                for selcond in conditions:
                    if not selcond.isValid(self.get_subject_col_value(sid, selcond.colname)):
                        add = False
                if add:
                    res.append(sid)
            return SIDList(res)
        else:
            return sids

    #endregion

    # ======================================================================================
    #region (SIDS|validcols) -> SubjectsData
    def extract_subjset(self, sids:SIDList, validcols:List[str]=None) -> 'SubjectsData':
        '''
        Returns a subset of the present SubjectsData containing only the given subjects

        Parameters:
            sids (SIDList): A list of subjects to include.
            validcols (List[str]): A list of column names to include in the data. If None, all columns will be included.

        Returns:
            SubjectsData: A subset of the present SubjectsData containing only the given subjects.
        '''
        return SubjectsData(self.select_df(sids, validcols))

    #endregion

    # ======================================================================================
    #region (SIDS|validcols) -> DataFrame
    # may further select only those rows that respect all the select_conds
    def select_df(self, sids:SIDList=None, validcols:List[str]=None, df:pandas.DataFrame=None, update:bool=False) -> pandas.DataFrame:
        """
        Selects a subset of the data frame based on the given subjects and columns.

        Parameters
        ----------
        sids: SIDList, optional
            A list of subjects to include. If None, all subjects will be included.
        validcols: List[str], optional
            A list of column names to include. If None, all columns will be included.
        df: pandas.DataFrame, optional
            A pandas data frame to select from. If None, the internal data frame will be used.
        update: bool, optional
            Whether to update the internal data frame with the selected data.

        Returns
        -------
        pandas.DataFrame
            The selected data frame.
        """
        if df is None:
            df = self.df.copy()

        if sids is None and validcols is None:
            return df

        df = self.select_rows_df(sids, df, False)
        df = self.select_columns_df(validcols, df, False).copy()

        if update:
            self.df = df

        return df

    # extract only columns contained in given validcols
    def select_columns_df(self, validcols: List[str] = None, df: pandas.DataFrame = None, update:bool=False) -> pandas.DataFrame:
        """Selects a subset of the data frame based on the given columns.

        Parameters
        ----------
        validcols : List[str], optional
            A list of column names to include. If None, all columns will be included.
        df : pandas.DataFrame, optional
            A pandas data frame to select from. If None, the internal data frame will be used.
        update : bool, optional
            Whether to update the internal data frame with the selected data.

        Returns
        -------
        pandas.DataFrame
            The selected data frame.
        """
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
    def select_rows_df(self, sids: SIDList = None, df: pandas.DataFrame = None, update:bool=False) -> pandas.DataFrame:
        """
        Selects a subset of the data frame based on the given subjects.

        Parameters
        ----------
        sids: SIDList, optional
            A list of subjects to include. If None, all subjects will be included.
        df: pandas.DataFrame, optional
            A pandas data frame to select from. If None, the internal data frame will be used.
        update: bool, optional
            Whether to update the internal data frame with the selected data.

        Returns
        -------
        pandas.DataFrame
            The selected data frame.
        """
        if df is None:
            df = self.df.copy()

        if sids is None:
            sids = self.subjects

        newdf = pd.DataFrame()
        rows  = df.iloc[sids.ids]
        newdf = newdf._append(rows, ignore_index=True)

        if update is True:
            self.df = newdf

        return newdf

    #endregion

    # ======================================================================================
    #region (SID/SIDS|validcol(s)) -> dict/List[dict]
    def get_sid_dict(self, sid: SID, validcols: List[str] = None) -> dict:
        """
        Returns the data of a subject as a dictionary.

        Parameters
        ----------
        sid : SID
            The subject to retrieve data for.
        validcols : List[str], optional
            A list of column names to retrieve. If None, all columns will be retrieved.

        Returns
        -------
        dict
            The data of the subject as a dictionary.

        Raises
        ------
        ValueError
            If the given subject does not exist in the data frame.
        """
        if sid.id >= self.num:
            raise ValueError("Error in get_subject: given id ({sid.id}) exceeds the total number of elements")

        if validcols is None:
            validcols = self.header
        else:
            missing_col = []
            for vc in validcols:
                if vc not in self.header:
                    missing_col.append(vc)

            if len(missing_col) > 0:
                raise ValueError("Error in SubjectsData.get_subject: given validcols list contains columns (" + str(missing_col) + ") not present in the original df...exiting")

        return self.df.loc[sid.id, validcols].to_dict()

    def get_sids_dict(self, sids:SIDList=None, validcols:List[str]=None) -> List[dict]:
        """
        Returns a list of dictionaries containing the data for the selected subjects and columns.

        Parameters:
        sids (SIDList): A list of subjects to include. If None, all subjects will be included.
        validcols (List[str]): A list of column names to retrieve. If None, all columns will be retrieved.

        Returns:
        A list of dictionaries, where each dictionary contains the data for a single subject.

        """
        if sids is None:
            sids = self.subjects

        if validcols is None:
            validcols = self.header

        df = self.select_df(sids, validcols)
        return [row.to_dict() for index, row in df.iterrows()]
    #endregion

    # ======================================================================================
    # region (SID/SIDS|validcol(s)) -> Any | List[Any] | List[List[Any]]
    # they DO NOT filter conditions, expect that given SID(S) has been already filtered
    def get_subject_col_value(self, sid: SID, colname: str) -> Any:
        """
        Returns the value of a column for a given subject.

        Parameters
        ----------
        sid : SID
            The subject to retrieve data for.
        colname : str
            The name of the column to retrieve.

        Returns
        -------
        Any
            The value of the column for the given subject.

        Raises
        ------
        DataFileException
            If the given subject or column does not exist in the data frame.
        """
        if sid.id >= self.num:
            raise DataFileException("Error in get_subject_col_value: given subject id (" + str(sid.id) + ") exceeds the total number of elements")

        if colname not in self.header:
            raise DataFileException("Error in get_subject_col_value: given column name (" + colname + ") does not exist in the data frame")

        value = self.df.loc[sid.id, colname]
        if isinstance(value, pandas.Series):
            return value.values[0]
        else:
            return value

    # return a list of values from a given column
    def get_subjects_column(self, sids: SIDList = None, colname: str = None, sort:bool=False, demean:bool=False, ndecim:int=4) -> List[Any]:
        """
        Returns a list of values from a given column.
        Important, sids must be obtained by the same df used to extract values.

        Parameters
        ----------
        sids: SIDList, optional
            A list of subjects to include. If None, all subjects in the df will be included.
        colname: str, optional
            The name of the column to retrieve.
        df: pandas.DataFrame, optional
            A pandas data frame to select from. If None, the internal data frame will be used.

        Returns
        -------
        list
            A list of values from the given column.

        Raises
        ------
        DataFileException
            If the given column does not exist in the data frame.
        """
        if colname is None:
            raise DataFileException("Error in SubjectsData.get_subjects_column: colname is None")

        if colname not in self.header:
            raise DataFileException(f"Error in SubjectsData.get_subjects_column: colname ({colname}) is not present in df")

        if sids is None:
            sids = self.subjects

        df = self.select_rows_df(sids)

        values = list(df[colname])

        if demean:
            values = demean_serie(values, ndecim)

        if sort:
            sort_schema = _argsort(values)
            values.sort()
            lab = reorder_list(sids.labels, sort_schema)

        return values

    # returns a filtered matrix [colnames x sids] of values
    def get_subjects_values_by_cols(self, sids: SIDList = None, colnames: List[str] = None, demean_flags: List[bool] = None, ndecim: int = 4) -> List[List[Any]]:
        """
        Returns a list of values from a subset of columns.

        Parameters
        ----------
        sids: SIDList, optional
            A list of subjects to include. If None, all subjects will be included.
        colnames: List[str], optional
            A list of column names to retrieve. If None, all columns will be retrieved.
        demean_flags: List[bool], optional
            A list of booleans indicating whether to demean the corresponding column. If None, no demeaning will be performed.
        ndecim: int, optional
            The number of decimal places to use when demeaning.

        Returns
        -------
        List[List[Any]]
            A matrix [sid x column] of values from the selected columns.

        Raises
        ------
        DataFileException
            If the given column does not exist in the data frame.
        """
        # Create a ncols x nsubj array of values.
        values = [self.get_subjects_column(sids=sids, colname=colname) for colname in colnames]

        if demean_flags is not None:
            if len(colnames) != len(demean_flags):
                msg = "Error in get_filtered_columns...lenght of colnames is different from demean_flags"
                raise DataFileException(msg)
            else:
                # Demean the requested columns.
                for idcol, dem_col in enumerate(demean_flags):
                    if dem_col:
                        values[idcol] = demean_serie(values[idcol], ndecim)

        return values

    # ======================================================================================
    # region (SID/SIDS|validcol(s)) -> str | List[str]
    # the list of subjects' values of each column are transformed in a single string with values separated by \n
    def get_subject_col_value_str(self, sid:SID, colname:str, ndecimals:int=3) -> str:
        """
        Returns the value of a column for a given subject as a string.

        Parameters
        ----------
        sid : SID
            The subject to retrieve data for.
        colname : str
            The name of the column to retrieve.
        ndecimals : int, optional
            The number of decimal places to use when formatting the value.

        Returns
        -------
        str
            The value of the column for the given subject as a string.

        Raises
        ------
        ValueError
            If the given subject or column does not exist in the data frame.
        """
        return self.__to_str([self.get_subject_col_value(sid, colname)], ndecimals)

    def get_subjects_column_str(self, sids:SIDList=None, colname:str=None, ndecimals:int=3) -> List[str]:
        """
        Returns a list of values from a given column as strings.

        Parameters:
        sids (SIDList): A list of subjects to include. If None, all subjects will be included.
        colname (str): The name of the column to retrieve.
        ndecimals (int): The number of decimal places to use when formatting the values.

        Returns:
        A list of values from the given column as strings.

        Raises:
        ValueError: If the given column does not exist in the data frame.
        """
        return self.__to_str(self.get_subjects_column(sids, colname), ndecimals)

    def get_subjects_values_by_cols_str(self, sids:SIDList=None, colnames:List[str]=None,
                                        demean_flags:List[bool]=None, ndecim:int=4) -> str:
        """
        Returns a list of values from a subset of columns.

        Parameters
        ----------
        sids: SIDList, optional
            A list of subjects to include. If None, all subjects will be included.
        colnames: List[str], optional
            A list of column names to retrieve. If None, all columns will be retrieved.
        demean_flags: List[bool], optional
            A list of booleans indicating whether to demean the corresponding column. If None, no demeaning will be performed.
        ndecim: int, optional
            The number of decimal places to use when demeaning.

        Returns
        -------
        list
            A list of values from the selected columns.

        Raises
        ------
        ValueError
            If the given column does not exist in the data frame.
        """
        values  = self.get_subjects_values_by_cols(sids, colnames)
        res_str = []
        for colvalues in values:
            res_str.append(self.__to_str(colvalues, ndecim))
        return res_str
    #endregion

    # ======================================================================================
    # region (subj_label / subj_label|sess_id) -> sess_ids | id
    def get_subjid_by_session(self, subj_lab:str, sess_id:int=1, error_if_empty:bool=True) -> int:
        """
        Returns the index of the subject with the given subject label and session, if it exists in the data frame.

        Parameters:
            subj_lab (str): The subject label.
            sess_id (int): The session number.
            error_if_empty: bool : if subject does not exist (no session is available) raise an exception or return []

        Returns:
            int: The index of the subject with the given subject label and session, if it exists in the data frame. Otherwise, returns -1.

        Raises:
            DataFileException: If error_if_empty is True and no session is available for given subj_label.
        """
        if self.exist_subject_session(subj_lab, sess_id):
            return int(self.df.index[(self.df[self.second_col_name] == sess_id) & (self.df[self.first_col_name] == subj_lab)].values[0])
        else:
            if error_if_empty:
                raise DataFileException("SubjectsData.get_subjid_by_session")
            else:
                return -1

    def get_subject_available_sessions(self,subj_lab:str, df:pandas.DataFrame=None, error_if_empty:bool=True) -> List[int]:
        """
        Returns the list of available sessions for a given subject.

        Parameters:
            subj_lab (str): The subject label.
            df (pandas.DataFrame, optional): A pandas data frame to retrieve the sessions from. If None, the internal data frame will be used.
            error_if_empty: bool : if subject does not exist (no session is available) raise an exception or return []

        Returns:
            List[int]: The list of available sessions for the given subject.

        Raises:
            DataFileException: If error_if_empty is True and no session is available for given subj_label.
        """
        if df is None:
            df = self.df.copy()

        mask    = df[self.first_col_name].isin([subj_lab])
        df      = df[mask]

        sessions = list(df[self.second_col_name])

        if len(sessions) > 0:
            return sessions
        else:
            if error_if_empty:
                raise DataFileException("SubjectsData.get_subject_available_sessions: given subj " + subj_lab + " does not have any session")
            else:
                return []

    #endregion

    # ==================================================================================================
    # region ADD/UPDATE/REMOVE DATA

    def set_subj_session_value(self, sid: SID, col_label:str, value:Any) -> None:
        """
        Sets the value of a column for a given subject.

        Parameters
        ----------
        sid : SID
            The subject to set the value for.
        col_label : str
            The name of the column to set.
        value : Any
            The value to set for the given subject and column.

        Raises
        ------
        ValueError
            If the given subject or column does not exist in the data frame.
        """
        if sid.id >= self.num:
            raise ValueError(f"Error in set_subj_session_value: given subject id ({sid.id}) exceeds the total number of elements")

        if col_label not in self.header:
            raise ValueError(f"Error in set_subj_session_value: given column name ({col_label}) does not exist in the data frame")

        col_id = self.col_id(col_label)
        self.df.iat[sid.id, col_id] = value

    # add new subjects: can be
    # - List[SubjectsData] e.g. several object containing one subject only
    # - List[SubjectsData] one item that contains in its df several subjects
    def add_sd(self, newsubjs: List['SubjectsData'], can_overwrite:bool=False, can_add_incomplete:bool=False) -> None:
        """
        Adds a list of SubjectsData objects to the current SubjectsData object.

        Parameters
        ----------
        newsubjs: List['SubjectsData']
            A list of SubjectsData objects to add.
        can_overwrite: bool, optional
            Whether to allow overwriting of existing subjects.
        can_add_incomplete: bool, optional
            Whether to allow adding of incomplete subjects.

        Raises
        ------
        Exception
            If the given list is not a list of SubjectsData objects, or if an element of the list is not a SubjectsData object.
        """
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
    def add_columns_df(self, subjsdf: pandas.DataFrame, can_overwrite:bool=False, can_add_incomplete=False) -> None:
        """
        Adds a subset of columns from a given pandas.DataFrame to the current SubjectsData object.

        Parameters
        ----------
        subjsdf : pandas.DataFrame
            A pandas.DataFrame containing the subset of columns to add.
        can_overwrite : bool, optional
            Whether to allow overwriting of existing columns.
        can_add_incomplete : bool, optional
            Whether to allow adding of incomplete columns.

        Raises
        ------
        Exception
            If the given pandas.DataFrame is not a DataFrame, or if the given DataFrame does not contain the "subj" and "session" columns.
        """
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

    def add_column(self, col_label: str, values: list, sids: SIDList = None, position: int = None, df: pandas.DataFrame = None) -> None:
        """
        Adds a new column to the SubjectsData object.

        Parameters
        ----------
        col_label : str
            The name of the new column.
        values : list
            A list of values to add to the new column. If the length of the list is less than the number of subjects, the values will be repeated.
        sids : SIDList, optional
            A list of subjects to add the column to. If None, all subjects will be included.
        position : int, optional
            The position of the new column in the data frame. If None, the column will be added at the end.
        df : pandas.DataFrame, optional
            A pandas data frame to add the column to. If None, the internal data frame will be used.

        Raises
        ------
        ValueError
            If the given column name already exists in the data frame.
        """
        if col_label in self.header:
            raise ValueError(f"Error in SubjectsData add_column: col_label ({col_label}) already exist...exiting")

        if sids is None:
            sids = self.subjects

        if position is None:
            position = len(self.header)  # add as last column

        nv = len(values)
        nl = len(sids)

        if nv != nl:
            if nv == 1:
                values = [values[0] for s in sids]  # if given value is just one, duplicate it for each subject
            else:
                raise ValueError(f"Error in SubjectsData.add_column, n value ({nv}) != n sids ({nl})")

        nanvalues = [np.nan for s in sids]
        self.df.insert(position, column=col_label, value=nanvalues)

        for i, s in enumerate(sids):
            self.df.at[s.id, col_label] = values[i]

        if df is not None:
            self.save_data(df)

    def update_column(self, sids:SIDList, col_label, values, df=None) -> None:
        """
        Update the value of a column for a given list of subjects.

        Parameters:
        sids (SIDList): A list of subjects to update the value for.
        col_label (str): The name of the column to update.
        value: The value to set for the given subject and column.
        df: pandas.DataFrame, optional

        Raises:
        ValueError: If the given subject or column does not exist in the data frame.
        """
        if col_label not in self.header:
            raise ValueError("Error in SubjectsData add_column: update_column (" + col_label + ") does not exist...exiting")

        nv = len(values)
        nl = len(sids)

        if nv != nl:
            raise Exception("Error in SubjectsData.add_column, n value (" + str(nv) + ") != n sids (" + str(nl) + ")")

        for i,s in enumerate(sids):
            # ids = self.subj_ids(val)
            self.df.at[s.id, col_label] = values[i]

        if df is not None:
            self.save_data(df)

    # if row is None adds only a subj col
    def add_row(self, sid: SID, row=None) -> None:
        """
        Adds a new row to the SubjectsData object.

        Parameters
        ----------
        sid : SID
            The subject to add the row for.
        row : dict, optional
            A dictionary containing the values of the new row. If None, a default row will be used.

        Raises
        ------
        ValueError
            If the given subject already exists in the data frame.
        """
        if self.exist_subjects(SIDList([sid])):
            raise ValueError(f"Error in SubjectsData.add_row: subject ({sid.label}) already exist")

        if row is None:
            row = {self.first_col_name: sid.label, self.second_col_name: sid.session}

        if len(self.df) == 0:
            self.df = pandas.DataFrame(columns=list(row.keys()))

        self.df.loc[len(self.df)] = row

    # assoc_dict is a dictionary where key is current name and value is the new one
    def rename_subjects(self, assoc_dict) -> None:
        """
        Rename subjects in the data frame according to a given dictionary.

        Parameters
        ----------
        assoc_dict : Dict[str, str]
            A dictionary where the keys are the old subject labels and the values are the new subject labels.

        Returns
        -------
        None

        """
        for i, (k_oldlab, v_newlab) in enumerate(assoc_dict.items()):
            sessions = self.get_subject_available_sessions(k_oldlab)
            for sess in sessions:
                subj_id = self.get_subjid_by_session(k_oldlab, sess)
                self.df.loc[subj_id, self.first_col_name] = v_newlab

    # REMOVE SUBJ DATA
    def remove_subjects(self, subjects2remove: SIDList, df: pandas.DataFrame = None, update=False) -> SubjectsData:
        """
        Remove subjects from the data frame.

        Parameters
        ----------
        subjects2remove: SIDList
            A list of subjects to remove.
        df: pandas.DataFrame, optional
            A pandas data frame to remove the subjects from. If None, the internal data frame will be used.
        update: bool, optional
            Whether to update the internal data frame with the filtered data.

        Returns
        -------
        SubjectsData
            A SubjectsData object containing the filtered data.

        """
        if df is None:
            df = self.df.copy()

        labels = list(df[self.first_col_name])

        for sid in subjects2remove:
            # ids = labels.index(subjlab)
            id = df.index[(df[self.first_col_name] == sid.label) & (df['session'] == sid.session)].tolist()[0]
            df.drop(id, inplace=True)
            df.reset_index(drop=True, inplace=True)

        sd = SubjectsData(df)

        if update:
            self.df = df

        return sd

    def remove_columns(self, cols2remove:List[str], df:pandas.DataFrame=None, update=False) -> DataFrame:
        """
        Remove columns from the data frame.

        Parameters
        ----------
        cols2remove: List[str]
            A list of column names to remove.
        df: pandas.DataFrame, optional
            A pandas data frame to remove the columns from. If None, the internal data frame will be used.
        update: bool, optional
            Whether to update the internal data frame with the filtered data.

        Returns
        -------
        pandas.DataFrame
            The filtered data frame.

        """
        if not isinstance(cols2remove, list):
            raise Exception("Error in SubjectsData.remove_columns: given cols param is not a list")

        if df is None:
            df = self.df.copy()

        for col in cols2remove:
            if col in df.columns.to_list():
                df = df.drop(col, axis=1)

        if update:
            self.df = df

        return df

    # endregion

    # ======================================================================================
    #region ACCESSORY

    def is_cell_not_empty(self, subj_id: int, col_str: str = None, df=None) -> bool:
        """
        Returns whether the value of a cell is not empty.

        Parameters:
            subj_id (int): The index of the subject.
            col_str (str): The name of the column.
            df (pandas.DataFrame, optional): A pandas data frame to retrieve the data from. If None, the internal data frame will be used.

        Returns:
            bool: Whether the value of the cell is not empty.

        Raises:
            DataFileException: If the given column does not exist in the data frame.
        """
        if df is None:
            df = self.df.copy()

        if col_str not in df.columns.values[:]:
            raise DataFileException("SubjectsData.is_cell_not_empty: given col (" + str(col_str) + ") does not exist in df")

        col_id = self.col_id(col_str, df)

        try:
            return not df.isnull().iloc[subj_id, col_id]
        except:
            raise DataFileException("SubjectsData.is_cell_not_empty: given col (" + str(col_str) + ") does not exist in df")

    def is_cell_empty(self, subj_id:int, col_str:str=None, df=None) -> bool:
        """
        Returns whether the value of a cell is empty.

        Parameters:
        subj_id (int): The index of the subject.
        col_str (str): The name of the column.
        df (pandas.DataFrame, optional): A pandas data frame to retrieve the data from. If None, the internal data frame will be used.

        Returns:
        bool: Whether the value of the cell is empty.

        Raises:
        Exception: If the given column does not exist in the data frame.
        """
        return not self.is_cell_not_empty(subj_id, col_str, df)

    def col_id(self, col_lab: str, df: pandas.DataFrame = None) -> int:
        """
        Returns the index of the column with the given name.

        Parameters:
            col_lab (str): The name of the column.
            df (pandas.DataFrame, optional): A pandas data frame to retrieve the columns from. If None, the internal data frame will be used.

        Returns:
            int: The index of the column with the given name.

        """
        if df is None:
            df = self.df.copy()

        return df.columns.get_loc(col_lab)

    def validate_covs(self, covs)-> None:
        """
        Validate the given list of covariates.

        Parameters:
            covs (list): A list of covariates.

        Raises:
            DataFileException: If the given covariates are not present in the data file.
        """
        # if all(elem in header for elem in regressors) is False:  if I don't want to understand which cov is absent
        missing_covs = ""
        for cov in covs:
            if not cov.name in self.header:
                missing_covs = missing_covs + cov.name + ", "

        if len(missing_covs) > 0:
            raise DataFileException("validate_covs", "the following header are NOT present in the given datafile: " + missing_covs)

    # save some columns of a subset of the subjects in given file
    def save_data(self, outdata_file=None, sids:SIDList=None, incolnames=None, outcolnames=None, separator:str= "\t") -> None:
        """
        Save the data of a subset of the subjects in a file.

        Parameters
        ----------
        outdata_file : str, optional
            The path of the output file. If None, the current file path will be used.
        sids : SIDList, optional
            A list of subjects to include. If None, all subjects will be included.
        incolnames : List[str], optional
            A list of column names to include. If None, all columns will be included.
        outcolnames : List[str], optional
            A list of column names to use in the output file. If None, the input column names will be used.
        separator : str, optional
            The separator to use when saving the data.

        Raises
        ------
        Exception
            If the given output file format is not supported.
        """
        if outdata_file is None:
            outdata_file = self.filepath

        if incolnames is None:
            incolnames = self.header

        df = self.select_columns_df(incolnames)  # get a copy of all the rows of the given incolnames

        # rename columns if asked
        if outcolnames is not None:
            if len(outcolnames) != len(incolnames):
                raise Exception("Error in SubjectsData.save_data: given outcolnames length differs from column number")
            else:
                df.columns.values[:] = outcolnames

        df = self.select_rows_df(sids, df)

        if outdata_file.endswith(".csv") or outdata_file.endswith(".dat") or outdata_file.endswith(".txt"):
            df.to_csv(outdata_file, sep=separator, index=False)
        elif outdata_file.endswith(".xls") or outdata_file.endswith(".xlsx"):
            df.to_excel(outdata_file, index=False)
        else:
            raise Exception("Error in SubjectData.load: unknown data file format")

    def is_equal(self, sd: 'SubjectsData') -> bool:
        """
        Compares two SubjectsData objects and returns whether they are equal.

        Parameters:
            sd (SubjectsData): The SubjectsData object to compare to.

        Returns:
            bool: Whether the two SubjectsData objects are equal.
        """
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
            print("Report: " + report)
            return False

    def outlier(self, colname, _range=1.5, df: pandas.DataFrame = None) -> pandas.DataFrame:
        """
        Identify outliers in a column of a pandas dataframe.

        Parameters:
        colname (str): The name of the column to analyze.
        _range (float): The number of standard deviations to use for outlier detection.
        df (pandas.DataFrame, optional): The pandas dataframe to analyze. If None, the internal dataframe will be used.

        Returns:
        pandas.DataFrame: A dataframe containing the outlier values.

        """
        if df is None:
            df = self.df.copy()

        Q1 = df[colname].quantile(0.25)
        Q3 = df[colname].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - _range * IQR
        upper_bound = Q3 + _range * IQR
        outliers = df[(df[colname] < lower_bound) | (df[colname] > upper_bound)]

        return outliers

    # get a data list and return a \n separated string, suitable for spm template files
    @staticmethod
    def __to_str(datalist: List, ndecimals: int = 3) -> str:
        """
        Returns a list of values as a string, with each value rounded to a specified number of decimal places.

        Parameters:
        datalist (List): The list of values to convert to a string.
        ndecimals (int): The number of decimal places to use for rounding.

        Returns:
        str: The list of values as a string, with each value rounded to the specified number of decimal places.
        """
        datastr = ""
        for r in datalist:
            rr = str(round(r * ndecimals * 10) / (ndecimals * 10))
            datastr = datastr + rr + "\n"
        return datastr

    #endregion

    # =====================================================================================
