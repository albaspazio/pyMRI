from __future__ import annotations

import collections
import io
import os
from typing import List
from datetime import date, datetime

import gspread
import msoffcrypto
import pandas
import pandas as pd

from data.GDriveSheet import GDriveSheet
from data.Sheets import Sheets
from data.SubjectSD import SubjectSD
from data.SubjectSDList import SubjectSDList
from data.SubjectsData import SubjectsData
from utility.exceptions import DataFileException


class MSHDB:
    """
    Main class for managing a database of multiple Excel sheets.
    The database is organized as a collection of sheets, where each sheet contains data for a specific set of subjects.
    The database can be loaded from an Excel file, a Google Sheet, or from a Python dictionary.
    Once loaded, the sheets can be accessed and modified using the methods provided by the MSHDB class.

    Parameters
    ----------
    data : str, Sheets, or GDriveSheet
        The data source for the database. This can be a path to an Excel file, a Google Sheet, or a Python dictionary containing the data.
    sheetnames : list of str
        A list of the names of the sheets in the database. If not provided, the sheet names will be inferred from the data source.
    main_id : int
        The index of the main sheet in the sheetnames list.
    suppress_nosubj : bool
        If True, warnings will be suppressed when the first column of a sheet is not called "subj".
    first_col_name : str
        The name of the first column of each sheet.
    can_different_subjs : bool
        If True, subjects can appear in different sheets.
    password : str
        The password for decrypting an Excel file.
    sortonload : bool
        If True, the sheets will be sorted by the values in the first column when they are loaded.

    Attributes
    ----------
    sheets : Sheets
        A dictionary containing the sheets in the database, where the keys are the sheet names and the values are SubjectsData objects.
    main : SubjectsData
        The SubjectsData object for the main sheet.
    subjects : SubjectSDList
        A list of all the subjects in the database.
    sheet_labels : list
        A list of the sheet names in the database.
    data_source : str or Sheets or GDriveSheet
        The data source for the database.

    Methods
    -------
    load(data=None, validcols=None, cols2num=None, delimiter='\t', sort=True)
        Load the data into the database.
    sheet_sd(name)
        Return the SubjectsData object for a specific sheet.
    sort_values(df)
        Sort the rows of a DataFrame by a specified column.
    is_valid(df)
        Verify that the first column of a DataFrame is called "subj".
    add_default_columns(subjs, df)
        Add a column containing the subject labels to a DataFrame.
    remove_extra_columns(hdr)
        Remove a column from the header of a DataFrame.
    add_default_rows(subjs=None)
        Add a row containing the subject labels to a DataFrame.
    add_default_row(subj)
        Add a default row containing the subject information.
    add_new_columns(shname, subjdf)
        Add new columns to a sheet.
    rename_subjects(assoc_dict, update=False)
        Rename the subjects in the database.
    remove_subjects(subjects2remove, update=False)
        Remove subjects from the database.
    add_new_subjects(newdb, can_diff_subjs=None, copy_previous_sess=None, update=False)
        Add new subjects to the database.
    select_df(subjs=None, sheets_cols=None, outfile='')
        Select a subset of the data from the database.
    save(outdata=None, sort=None)
        Save the database to an Excel file or Google Sheet.
    decrypt_excel(fpath, pwd)
        Decrypt an Excel file.
    __format_dates()
        Format the date columns in the sheets.
    __round_columns()
        Round the numeric columns in the sheets.
    is_equal(db)
        Compare two databases for equality.
    add_column(col_label, values, subjs=None, position=None, df=None, update=False)
        Add a new column to the database.
    check_labels(newsubjs, sheet)
        Check the labels in a sheet against the main sheet.
    """

    valid_dtypes    = ['Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'float64', 'float32']
    dates           = {}
    to_be_rounded   = {}
    round_decimals  = 2
    date_format     = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY

    def __init__(self, data:str|Sheets|GDriveSheet=None, sheetnames:List[str]=None, main_id:int=0, suppress_nosubj:bool=True, first_col_name:str="subj", can_different_subjs:bool=False, password:str="", sortonload:bool=True):

        super().__init__()
        self.schema_sheets_names= sheetnames
        self.main_id            = main_id
        self.suppress_nosubj    = suppress_nosubj
        self.first_col_name     = first_col_name        # e.g. "subj"
        self.can_diff_subjs     = can_different_subjs
        self.password           = password

        self.main_name:str      = sheetnames[main_id]      # e.g. "main"

        self.data_source        = None

        self.sheets:Sheets      = Sheets(self.schema_sheets_names, main_id)

        if data is not None:
            self.load(data, sort=sortonload)

        self.__format_dates()
        self.__round_columns()

    # self.main sheet contains the list of DB subjects
    @property
    def main(self) -> SubjectsData:
        return self.sheet_sd(self.main_name)

    # returns all unique subjects labels across all sessions
    @property
    def subjects(self) -> SubjectSDList:
        """
        Returns:
            SubjectSDList: A list of all the subjects in the database.
        """
        if self.main_name not in self.sheets:
            return SubjectSDList([])
        else:
            return self.main.subjects

    @property
    def sheet_labels(self) -> list:
        """
        Returns:
            list: A list of the sheet names in the database.
        """
        if bool(self.sheets):
            return list(self.sheets.keys())
        else:
            return []

    def load(self, data:str|Sheets|GDriveSheet=None, validcols:List[str]=None, cols2num:list=None, delimiter='\t', sort=True) -> Sheets:
        """
        Load the data into the database.

        Parameters
        ----------
        data : str, Sheets, or GDriveSheet
            The data source for the database. This can be a path to an Excel file, a Google Sheet, or a Python dictionary containing the data.
        validcols : list
            A list of the column names to be loaded. If not provided, all columns will be loaded.
        cols2num : list
            A list of the column names and their data types. The data types must be one of the following: Int8, Int16, Int32, Int64, UInt8, UInt16, UInt32, UInt64, float64, or float32. If not provided, all columns will be loaded as strings.
        delimiter : str
            The delimiter used in the data file.
        sort : bool
            If True, the rows of the data will be sorted by the values in the first column.

        Returns
        -------
        Sheets
            A dictionary containing the sheets in the database, where the keys are the sheet names and the values are SubjectsData objects.

        Raises
        ------
        DataFileException
            If the data parameter is not a valid file.
        Exception
            If the data parameter is of an unknown format or if there is an error loading the data.

        """
        self.data_source = data
        if isinstance(data, str):
            # Check if the data parameter is a valid file
            if not os.path.exists(data):
                raise DataFileException("MXLSDB.load", "given data param (" + data + ") is not a valid file")
            # Check if the data parameter is an Excel file
            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise DataFileException("Error in MXLSDB.load: unknown data file format")
            # Check if a password is required to decrypt the Excel file
            if self.password != "":
                # Decrypt the Excel file
                data = self.decrypt_excel(data, self.password)
            # Read the Excel file into a Pandas DataFrame
            xls = pd.ExcelFile(data)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name)
                # Verify that the first column is valid
                df = self.is_valid(df)
                # Sort the data by the first column if requested
                if sort:
                    df = self.sort_values(df)
                # Create a SubjectsData object from the DataFrame
                sd = SubjectsData(df)
                # Add the SubjectsData object to the sheets dictionary
                # TODO: Check if this condition is necessary
                # if not self.can_diff_subjs:
                #     self.check_labels(sd.subjects, sheet)  # raise an exception
                self.sheets[sheet_name] = sd
        elif isinstance(data, Sheets):
            self.sheets = data
        elif isinstance(data, GDriveSheet):
            # Try to open the Google Sheet
            try:
                spreadsheet = data.open_ss()
                # Iterate through the worksheets in the Google Sheet
                for wsh in spreadsheet.worksheets():
                    # Get the data from the worksheet
                    rows = wsh.get_all_records()
                    # Create a Pandas DataFrame from the data
                    df = pd.DataFrame(rows)
                    # Verify that the first column is valid
                    df = self.is_valid(df)
                    # Sort the data by the first column if requested
                    if sort:
                        df = self.sort_values(df)
                    # Create a SubjectsData object from the DataFrame
                    sd = SubjectsData(df)
                    # Add the SubjectsData object to the sheets dictionary
                    # TODO: Check if this condition is necessary
                    # if not self.can_diff_subjs:
                    #     self.check_labels(sd.subjects, sheet)  # raise an exception
                    self.sheets[wsh.title] = sd
            except gspread.exceptions.APIError as ex:
                print("GOOGLE API ERROR: " + ex.args[0]["message"])
        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str, not a Sheet")
        # Return the sheets dictionary
        return self.sheets

    def sheet_sd(self, name: str) -> SubjectsData:
        """
        Returns the SubjectsData object for a specific sheet.

        Parameters
        ----------
        name : str
            The name of the sheet.

        Returns
        -------
        SubjectsData
            The SubjectsData object for the sheet.

        Raises
        ------
        Exception
            If the sheet does not exist.
        """
        if name not in self.schema_sheets_names:
            raise Exception("Error in MSHDB.sheet: ")
        return self.sheets[name]

    # ======================================================================================
    # region WILL BE OVERRIDDEN
    def sort_values(self, df: pandas.DataFrame) -> pandas.DataFrame:
        """
        Sort the rows of a DataFrame by a specified column.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to be sorted.

        Returns
        -------
        pandas.DataFrame
            The sorted DataFrame.

        """
        return df.sort_values(by=[self.first_col_name], ignore_index=True)

    def is_valid(self, df: pandas.DataFrame) -> pandas.DataFrame:
        """
        Verify that the first column of a DataFrame is called "subj".

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to be checked.

        Returns
        -------
        pandas.DataFrame
            The input DataFrame, with the first column renamed to "subj" if necessary.

        Raises
        ------
        Exception
            If the first column is not called "subj" and suppress_nosubj is False.

        """
        if df.columns[0] != self.first_col_name:
            if self.suppress_nosubj:
                df.columns.values[0] = self.first_col_name
                print("Warning in MXLSDB.load: first column was not called subj, I renamed it to subj....check if it's ok")
                return df
            else:
                raise Exception("Error in MXLSDB.load: first column is not called " + self.first_col_name)

    def add_default_columns(self, subjs: SubjectSDList, df: pandas.DataFrame) -> pandas.DataFrame:
        """
        Add a column containing the subject labels to a DataFrame.

        Parameters
        ----------
        subjs : SubjectSDList
            A list of SubjectSD objects.
        df : pandas.DataFrame
            A Pandas DataFrame.

        Returns
        -------
        pandas.DataFrame
            The input DataFrame with a new column containing the subject labels.

        """
        df[self.first_col_name] = subjs.labels
        return df


    def remove_extra_columns(self, hdr: list) -> list:
        """
        Remove a column from the header of a DataFrame.

        Parameters
        ----------
        hdr : list
            The header of the DataFrame.

        Returns
        -------
        list
            The input header with the specified column removed.

        """
        hdr.remove(self.first_col_name)
        return hdr

    def add_default_rows(self, subjs: SubjectSDList = None) -> pandas.DataFrame:
        """
        Add default rows to the database.

        Parameters
        ----------
        subjs : SubjectSDList, optional
            The list of subjects to add, by default None

        Returns
        -------
        pandas.DataFrame
            The dataframe with the default rows added.

        """
        df = pandas.DataFrame()
        df[self.first_col_name] = subjs.labels

        return df

    def add_default_row(self, subj: SubjectSD) -> dict:
        """
        Add a default row to the database for a specific subject.

        Parameters
        ----------
        subj : SubjectSD
            The subject to add the default row for.

        Returns
        -------
        dict
            The default row for the subject.

        """
        return {self.first_col_name: subj.label}

    def add_new_columns(self, shname: str, subjdf: pandas.DataFrame) -> None:
        """
        Add new columns to an existing sheet in the database.

        Parameters
        ----------
        shname : str
            The name of the sheet to add the columns to.
        subjdf : pandas.DataFrame
            The dataframe containing the new columns to add.

        Raises
        ------
        Exception
            If the new columns contain subjects that are not already in the database.

        """
        sheet_sd = self.sheet_sd(shname)

        if self.first_col_name not in subjdf.columns.values:
            raise Exception("Error in addColumns: given subjdf does not contain a subj column")

        new_sd = SubjectsData(subjdf)
        new_subjs = new_sd.subjects

        if new_subjs.is_in(self.subjects):  # all subjects included in subjdf are already present in the db
            sheet_sd.add_columns_df(subjdf, can_overwrite=False)
        else:
            raise Exception("Error in MSSD")

    def rename_subjects(self, assoc_dict: dict, update: bool = False) -> "MSHDB":
        """
        Rename subjects in the database.

        Parameters
        ----------
        assoc_dict : dict
            The dictionary of subject labels to new labels.
        update : bool, optional
            Whether to update the database with the new labels, by default False

        Returns
        -------
        MSHDB
            The updated MSHDB with the renamed subjects.

        """
        sheets = self.sheets.copy()
        for sh in self.sheets:
            sheets[sh].rename_subjects(assoc_dict)

        if update:
            self.sheets = sheets
            return self
        else:
            return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)

    def remove_subjects(self, subjects2remove: SubjectSDList, update: bool = False) -> "MSHDB":
        """
        Remove subjects from the database.

        Parameters
        ----------
        subjects2remove : SubjectSDList
            The list of subjects to remove.
        update : bool, optional
            Whether to update the database with the removed subjects, by default False

        Returns
        -------
        MSHDB
            The updated MSHDB with the removed subjects.

        """
        sheets = self.sheets.copy()
        for sh in self.sheets:
            sheets[sh] = sheets[sh].remove_subjects(subjects2remove)

        if update:
            self.sheets = sheets.copy()
            return self
        else:
            return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)

    # add brand-new subjects:
    # Since it thought to may accept also incomplete sheets. it must preserve db integrity
    # (e.g. in some sheets there are data of s1, s2, s4, in other of s1, s3, s4)
    # ->    it must consider all four subjects and thus add a row with only the subj name where it's absent
    #       in the first sheet add s3 and in the second s2.
    # Moreover must create also all those sheets not present in new data with a row for each subject with just a subj column
    # if "copy_previous_sess" is not None and subjects have a previous session: it tries to copy previous data of the sheet contained in the given list
    #
    #
    # parse all sheets and determine the list of all subjects contained across all given sheets
    # if it finds a new subj that already existed -> ignore that subject and add remaining
    def add_new_subjects(self, newdb: 'MSHDB', can_diff_subjs=None, copy_previous_sess=None, update=False) -> 'MSHDB':
        """
        Add brand-new subjects to the database.

        Parameters
        ----------
        newdb : 'MSHDB'
            The MSHDB object containing the new subjects.
        can_diff_subjs : bool, optional
            Whether the new subjects can have different subject lists across sheets, by default None (same as in the current database).
        copy_previous_sess : list, optional
            A list of sheet names containing previous sessions of subjects, by default None.
        update : bool, optional
            Whether to update the current database with the new subjects, by default False.

        Returns
        -------
        'MSHDB'
            The updated MSHDB object.

        Raises
        ------
        Exception
            If the new subjects have different subject lists across sheets and can_diff_subjs is False.
        """
        if can_diff_subjs is None:
            can_diff_subjs = self.can_diff_subjs

        # verify that new subjects lists are identical across sheets
        if can_diff_subjs is False and not newdb.sheets.is_consistent:
            raise Exception("Error in MSSubjectsData.add_subjects: new subjects lists differ across sheets")

        # this method cannot overwrite existing subjects: thus verify that added subjects are really new
        all_subjs = newdb.sheets.all_subjects  # all union (no rep) of all subjects-sessions included in all new sheets
        intersecting_subjs = all_subjs.is_in(self.subjects)
        if len(intersecting_subjs) > 0:
            # remove already existing subjects and update all_subjs
            newdb = newdb.remove_subjects(intersecting_subjs)
            all_subjs = newdb.sheets.all_subjects
            print("Warning in MSHDB.add_new_subjects: The following subjects/sessions (" + str(intersecting_subjs.labels) + ") were already present and will be ignored")

        # start cycling through all existing sheets, adding missing sheets with all new subj rows or integrating the given sheets with missing subjects
        for sh in self.schema_sheets_names:

            if sh not in list(newdb.sheets.keys()):  # new data does NOT contain this sheet.

                # in case new subjects has a previous session, decide whether copying data from session 1 or create a default (subj/session/group) df
                if copy_previous_sess is None:
                    # create a new sheet sd with new subjects default info (subj, and e.g. group / session)
                    df = newdb.add_default_rows(all_subjs)
                else:
                    if sh in copy_previous_sess:
                        df = pandas.DataFrame()
                        sd = self.sheet_sd(sh)
                        for s in all_subjs:
                            if s.session > 1:
                                subj_session1 = sd.get_subj_session(s.label, 1)
                                if subj_session1 is None:
                                    raise Exception("Error in MSHDB.add_new_subjects: new subject is a follow-up, but session 1 is missing...aborting")
                                else:
                                    subj_row = sd.get_subject(subj_session1)
                                    subj_row["session"] = s.session
                                    if len(df) == 0:
                                        df = pd.DataFrame(columns=list(subj_row.keys()))
                                        df.loc[len(df)] = subj_row
                                    else:
                                        df.loc[len(df)] = subj_row
                            else:
                                df.loc[len(df)] = {self.first_col_name: s.label, self.second_col_name: s.session}

                    else:
                        df = newdb.add_default_rows(all_subjs)

                    # check if a previous session is pre
                newdb.sheets[sh] = SubjectsData(df)

            else:  # new data contain this sheet

                # I must add to the new data, a row for all other subjects not present in this new sheet
                ds = newdb.sheets[sh]
                for subj in all_subjs:
                    if not ds.subjects.contains(subj):
                        # this subj exist in some other new sheets, but not here -> add it
                        # P.S. could have passed row=None and let SubjectsData manage it, but calling a MSHDB subclass method I'm sure it is more complete
                        ds.add_row(subj, newdb.add_default_row(subj))

        # has all sheets and all subjects are brand new
        if update is True:
            for sh in newdb.sheets:
                self.sheet_sd(sh).add_sd([newdb.sheet_sd(sh)])
                self.sheet_sd(sh).df = self.sheet_sd(sh).df.sort_values(by=[self.first_col_name], ignore_index=True)

            return True

        else:
            sheets = self.sheets.copy()
            for sh in newdb.sheets:
                sheets[sh].add_sd([newdb.sheets[sh]])
                sheets[sh].df = sheets[sh].df.sort_values(by=[self.first_col_name], ignore_index=True)
            return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)
    # endregion

    # ======================================================================================
    # region SELECT (labs, sheets_cols) DataFrame
    # e.g. : sheets_cols = {"main": ["group", "Eta", "sesso"],
    #                       "SAPS": ["SAPS_TOT"],
    #                       "YMRS": ["YMRS_TOT"]}
    # SUBSET all excel by rows and sheets' cols
    def select_df(self, subjs: SubjectSDList = None, sheets_cols: dict = None, outfile: str = "") -> pandas.DataFrame:
        """
        Selects data from the database and returns it as a Pandas DataFrame.

        Parameters
        ----------
        subjs : SubjectSDList, optional
            A list of SubjectSD objects, by default None
        sheets_cols : dict, optional
            A dictionary of sheet names and lists of columns to select, by default None
        outfile : str, optional
            The path to an output Excel file, by default None

        Returns
        -------
        pandas.DataFrame
            The selected data as a Pandas DataFrame.

        """
        if subjs is None and sheets_cols is None:
            return None

        df = pandas.DataFrame()
        df = self.add_default_columns(subjs, df)

        for sheetname in sheets_cols:
            sd: SubjectsData = self.sheet_sd(sheetname)
            cols: List[str] = sheets_cols[sheetname]
            if cols[0] == "*":
                hdr = sd.header.copy()
                hdr = self.remove_extra_columns(hdr)
                df = pd.concat([df, sd.select_df(subjs, hdr)], axis=1)
            else:
                df = pd.concat([df, sd.select_df(subjs, cols)], axis=1)

        if outfile != "":
            df.to_excel(outfile, index=False)

        return df

    def save(self, outdata=None, sort=None):
        """
        Save the database to an Excel file or a Google Sheet.

        Parameters
        ----------
        outdata : str or GDriveSheet, optional
            The path to an output Excel file or a Google Sheet, by default None
        sort : list or None, optional
            A list of column names to sort by, by default None

        """
        if outdata is None:
            outdata = self.data_source

        for sh in self.schema_sheets_names:
            if sort is not None:
                if isinstance(sort, list):
                    self.sheet_sd(sh).df.sort_values(by=sort, inplace=True)
                else:
                    raise Exception("Error in MSHDB.save_excel: sort parameter is not a list")

        if isinstance(outdata, str):
            with pd.ExcelWriter(outdata, engine="xlsxwriter") as writer:

                for sh in self.schema_sheets_names:
                    self.sheet_sd(sh).df.to_excel(writer, sheet_name=sh, startrow=1, header=False, index=False)

                    # create a table
                    workbook = writer.book
                    worksheet = writer.sheets[sh]
                    (max_row, max_col) = self.sheet_sd(sh).df.shape
                    column_settings = [{"header": column} for column in self.sheet_sd(sh).df.columns]
                    worksheet.add_table(0, 0, max_row, max_col - 1, {
                        "columns": column_settings})  # Add the Excel table structure. Pandas will add the data.
                    worksheet.set_column(0, max_col - 1, 12)  # Make the columns wider for clarity.

                print("Saved file: " + outdata)

        elif isinstance(outdata, GDriveSheet):
            outdata.update_file(self.sheets, backuptitle="bayesdb_" + datetime.now().strftime("%d%m%Y_%H%M%S"))
            print("Saved Google Sheet: ")

    def decrypt_excel(self, fpath, pwd):
        """
        Decrypt an Excel file.

        Parameters
        ----------
        fpath : str
            The path to the Excel file.
        pwd : str
            The password to decrypt the file with.

        Returns
        -------
        io.BytesIO
            The decrypted file as a BytesIO object.

        """
        unlocked_file = io.BytesIO()

        with open(fpath, "rb") as file:
            excel_file = msoffcrypto.OfficeFile(file)
            excel_file.load_key(password=pwd)
            excel_file.decrypt(unlocked_file)

        return unlocked_file

    def __format_dates(self):
        """
        Format date columns in the database.

        """
        for sh in self.dates:
            if sh in self.sheets.keys():
                sd: SubjectsData = self.sheet_sd(sh)
                if sd.num == 0:
                    continue

                for col in self.dates[sh]:
                    date_values = []
                    for subj in sd.subjects:
                        value = sd.get_subject_col_value(subj, col)
                        try:
                            date_values.append(pandas.to_datetime(value))
                        except:
                            raise Exception(
                                "Error in MSHDB.__format_dates: value (" + value + ") in column " + col + " of sheet " + sh + " is not a valid date")

                    try:
                        if len(date_values) > 0:
                            # change the datetime format
                            sd.df[col] = pandas.Series(date_values).dt.strftime(self.date_format)
                    except:
                        raise Exception(
                            "Error in MSHDB.__format_dates: value (" + date_values + ") in column " + col + " of sheet " + sh + " cannot be formatted as desired")

    def __round_columns(self):
        """
        Round numeric columns in the database.

        """
        for sh in self.to_be_rounded:
            if sh in self.sheets.keys():
                ds: SubjectsData = self.sheet_sd(sh)
                if ds.num == 0:
                    continue
                for col in self.to_be_rounded[sh]:
                    ds.df[col] = ds.df[col].apply(lambda x: round(x, self.round_decimals) if str(x) != "" else x)

                    # ds.df[col] = ds.df[col].round(self.round_decimals)

    def is_equal(self, db: 'MSHDB') -> bool:
        """
        Check if two MSHDB objects are equal.

        Parameters
        ----------
        db : 'MSHDB'
            The MSHDB object to compare with.

        Returns
        -------
        bool
            True if the two objects are equal, False otherwise.

        """
        return self.sheets.is_equal(db.sheets)

    def add_column(self, col_label, values, subjs:SubjectSDList=None, position=None, df=None, update=False) -> 'MSHDB':
        """
        Add a new column to the database.

        Parameters
        ----------
        col_label : str
            The label of the new column.
        values : list or numpy.ndarray
            The values to add to the new column. If values is a list, it must have the same length as the number of subjects in the database. If values is a numpy.ndarray, it must have the same shape as the number of subjects in the database.
        subjs : SubjectSDList, optional
            A list of SubjectSD objects, by default None
        position : int, optional
            The position of the new column, by default None
        df : pandas.DataFrame, optional
            A Pandas DataFrame containing the new column, by default None
        update : bool, optional
            Whether to update the current database with the new column, by default False

        Returns
        -------
        'MSHDB'
            The updated MSHDB object.

        """
        sheets = self.sheets.copy()

        for sh in self.sheets:
            sheets[sh].add_column(col_label, values, subjs, position, df)

        if update:
            self.sheets = sheets

        return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)

    # presently not used. TODO: fix MSHDB.check_labels
    def check_labels(self, newsubjs:SubjectSDList, sheet:str) -> bool:
        """
        Check if the labels of a sheet are consistent with the main sheet.

        Parameters
        ----------
        newsubjs : SubjectSDList
            The list of SubjectSD objects in the sheet.
        sheet : str
            The name of the sheet.

        Returns
        -------
        bool
            True if the labels are consistent, False otherwise.

        """
        if sheet == self.main_name:
            return True

        if self.main_name not in self.sheets:
            return True
        else:
            # HERE main sheets is loaded and self.labels is set
            if collections.Counter(newsubjs) != collections.Counter(self.subjects):
                nl  = newsubjs.copy()
                l   = self.subjects.copy()
                for lab in self.subjects:
                    if (lab.label in nl):
                        l.remove(lab)
                        nl.remove(lab)

                raise Exception("Error in MSSubjectsData.load: labels of sheet " + sheet + " does not correspond to main one...correct XLS file\n")
            else:
                return True
