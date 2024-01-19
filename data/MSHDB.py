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

    valid_dtypes    = ['Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'float64', 'float32']
    dates           = {}
    to_be_rounded   = {}
    round_decimals  = 2
    date_format     = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY

    def __init__(self, data=None, sheetnames:List[str]=None, main_id:int=0, suppress_nosubj=True, first_col_name="subj", can_different_subjs=False, password:str=""):

        super().__init__()
        self.schema_sheets_names= sheetnames
        self.main_id            = main_id
        self.suppress_nosubj    = suppress_nosubj
        self.first_col_name     = first_col_name        # e.g. "subj"
        self.can_diff_subjs     = can_different_subjs
        self.password           = password

        self.main_name          = sheetnames[main_id]      # e.g. "main"

        self.data_source        = None

        self.sheets             = Sheets(self.schema_sheets_names, main_id)

        if data is not None:
            self.load(data)

        self.__format_dates()
        self.__round_columns()


    # self.main sheet contains the list of DB subjects
    @property
    def main(self) -> SubjectsData:
        return self.sheets.main

    # returns all unique subjects labels across all sessions
    @property
    def subjects(self) -> SubjectSDList:
        if self.main_name not in self.sheets:
            return SubjectSDList([])
        else:
            return self.main.subjects

    @property
    def sheet_labels(self) -> list:
        if bool(self.sheets):
            return list(self.sheets.keys())
        else:
            return []

    def load(self, data=None, validcols:list=None, cols2num:list=None, delimiter='\t') -> Sheets:

        self.data_source = data
        if isinstance(data, str):

            if not os.path.exists(data):
                raise DataFileException("MXLSDB.load", "given data param (" + data + ") is not a valid file")

            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise Exception("Error in MXLSDB.load: unknown data file format")

            if self.password != "":
                data = self.decrypt_excel(data, self.password)

            xls = pd.ExcelFile(data)

            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name)
                df = self.is_valid(df)  # verify first column is called like self.first_col_name
                df = df.sort_values(by=[self.first_col_name], ignore_index=True)

                sd = SubjectsData(df)
                # TODO
                # if not self.can_diff_subjs:
                #     self.check_labels(sd.subjects, sheet)  # raise an exception

                self.sheets[sheet_name] = sd

        elif isinstance(data, Sheets):
            # TODO check is a dict of sheetname:subjectsdata
            self.sheets = data

        elif isinstance(data, GDriveSheet):

            try:
                spreadsheet     = data.open_ss()

                for wsh in spreadsheet.worksheets():
                    rows    = wsh.get_all_records()
                    df      = pd.DataFrame(rows)
                    df      = self.is_valid(df)  # verify first column is called like self.first_col_name
                    df      = df.sort_values(by=[self.first_col_name], ignore_index=True)

                    sd      = SubjectsData(df)
                    # TODO
                    # if not self.can_diff_subjs:
                    #     self.check_labels(sd.subjects, sheet)  # raise an exception

                    self.sheets[wsh.title] = sd
            except gspread.exceptions.APIError as ex:
                print("GOOGLE API ERROR: " + ex.args[0]["message"])


        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str, not a Sheet")

        return self.sheets

    def sheet_sd(self, name:str) -> SubjectsData:
        if name not in self.schema_sheets_names:
            raise Exception("Error in MSHDB.sheet: ")
        return self.sheets[name]

    # ======================================================================================
    # region WILL BE OVERRIDDEN
    def is_valid(self, df:pandas.DataFrame) -> pandas.DataFrame:
        if df.columns[0] != self.first_col_name:
            if self.suppress_nosubj:
                df.columns.values[0] = self.first_col_name
                print("Warning in MXLSDB.load: first column was not called subj, I renamed it to subj....check if it's ok")
                return df
            else:
                raise Exception("Error in MXLSDB.load: first column is not called " + self.first_col_name)

    def add_default_columns(self, subjs:SubjectSDList, df:pandas.DataFrame):
        df[self.first_col_name] = subjs.labels
        return df

    def remove_extra_columns(self, hdr:list) -> list:
        hdr.remove(self.first_col_name)
        return hdr

    def add_default_rows(self, subjs:SubjectSDList=None):
        df                      = pandas.DataFrame()
        df[self.first_col_name] = subjs.labels

        return df

    def add_default_row(self, subj:SubjectSD):
        return {self.first_col_name: subj.label}

    # subjdf must contain a subj column (all its subjects must be already present)
    def add_new_columns(self, shname: str, subjdf: pandas.DataFrame):

        sheet_sd = self.sheet_sd(shname)

        if self.first_col_name not in subjdf.columns.values:
            raise Exception("Error in addColumns: given subjdf does not contain a subj column")

        new_sd = SubjectsData(subjdf)
        new_subjs = new_sd.subjects

        if new_subjs.is_in(self.subjects):  # all subjects included in subjdf are already present in the db
            sheet_sd.add_columns_df(subjdf, can_overwrite=False)
        else:
            raise Exception("Error in MSSD")

    def remove_subjects(self, subjects2remove:SubjectSDList, update=False) -> 'MSHDB':

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
    # if it finds a new subj that already existed -> raise exception
    def add_new_subjects(self, newdb:'MSHDB', can_diff_subjs=None, copy_previous_sess=None, update=False) -> 'MSHDB':

        if can_diff_subjs is None:
            can_diff_subjs = self.can_diff_subjs

        # verify that new subjects lists are identical across sheets
        if can_diff_subjs is False and not newdb.sheets.is_consistent:
            raise Exception("Error in MSSubjectsData.add_subjects: new subjects lists differ across sheets")

        # this method cannot overwrite existing subjects: thus verify that added subjects are really new
        all_subjs           = newdb.sheets.all_subjects    # all union (no rep) of all subjects-sessions included in all new sheets
        intersecting_subjs = all_subjs.is_in(self.subjects)
        if len(intersecting_subjs) > 0:
            raise Exception("Error in MSHDB.add_new_subjects: at least one new subject (" + str(intersecting_subjs.labels) + ") already exist in the db with a same session. this is not allowed. check new data")

        # start cycling through all existing sheets, adding missing sheets with all new subj rows or integrating the given sheets with missing subjects
        for sh in self.schema_sheets_names:

            if sh not in list(newdb.sheets.keys()):         # new data does NOT contain this sheet.

                # in case new subjects has a previous session, decide whether copying data from session 1 or create a default (subj/session/group) df
                if copy_previous_sess is None:
                    # create a new sheet sd with new subjects default info (subj, and e.g. group / session)
                    df = newdb.add_default_rows(all_subjs)
                else:
                    if sh in copy_previous_sess:
                        df  = pandas.DataFrame()
                        sd  = self.sheet_sd(sh)
                        for s in all_subjs:
                            if s.session > 1:
                                subj_session1 = sd.get_subj_session(s.label, 1)
                                if subj_session1 is None:
                                    raise Exception("Error in MSHDB.add_new_subjects: new subject is a follow-up, but session 1 is missing...aborting")
                                else:
                                    subj_row            = sd.get_subject(subj_session1)
                                    subj_row["session"] = s.session
                                    if len(df) == 0:
                                        df = pd.DataFrame(columns=list(subj_row.keys()))
                                        df.loc[len(df)] = subj_row
                                    else:
                                        df.loc[len(df)]     = subj_row
                            else:
                                df.loc[len(df)] = {self.first_col_name: s.label, self.second_col_name: s.session}

                    else:
                        df = newdb.add_default_rows(all_subjs)

                    # check if a previous session is pre
                newdb.sheets[sh]    = SubjectsData(df)

            else:                                       # new data contain this sheet

                # I must add to the new data, a row for all other subjects not present in this new sheet
                ds:SubjectsData = newdb.sheets[sh]
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
    def select_df(self, subjs:SubjectSDList=None, sheets_cols:dict=None, outfile: str = "") -> pandas.DataFrame:

        if subjs is None and sheets_cols is None:
            return None

        df = pandas.DataFrame()
        df = self.add_default_columns(subjs, df)

        for sheetname in sheets_cols:
            sd:SubjectsData = self.sheet_sd(sheetname)
            cols:List[str]  = sheets_cols[sheetname]
            if cols[0] == "*":
                hdr = sd.header.copy()
                hdr = self.remove_extra_columns(hdr)
                df  = pd.concat([df, sd.select_df(subjs, hdr)], axis=1)
            else:
                df  = pd.concat([df, sd.select_df(subjs, cols)], axis=1)

        if outfile != "":
            df.to_excel(outfile, index=False)

        return df

    def save(self, outdata=None, sort=None):

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
                    workbook            = writer.book
                    worksheet           = writer.sheets[sh]
                    (max_row, max_col)  = self.sheet_sd(sh).df.shape
                    column_settings     = [{"header": column} for column in self.sheet_sd(sh).df.columns]
                    worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})  # Add the Excel table structure. Pandas will add the data.
                    worksheet.set_column(0, max_col - 1, 12)  # Make the columns wider for clarity.

                print("Saved file: " + outdata)

        elif isinstance(outdata, GDriveSheet):
            outdata.update_file(self.sheets, backuptitle="bayesdb_" + datetime.now().strftime("%d%m%Y_%H%M%S"))
            print("Saved Google Sheet: ")

    def decrypt_excel(self, fpath, pwd):
        unlocked_file = io.BytesIO()

        with open(fpath, "rb") as file:
            excel_file = msoffcrypto.OfficeFile(file)
            excel_file.load_key(password=pwd)
            excel_file.decrypt(unlocked_file)

        return unlocked_file

    def __format_dates(self):
        for sh in self.dates:
            if sh in self.sheets.keys():
                sd:SubjectsData = self.sheet_sd(sh)
                if sd.num == 0:
                    continue

                for col in self.dates[sh]:
                    date_values = []
                    for subj in sd.subjects:
                        value = sd.get_subject_col_value(subj, col)
                        try:
                            date_values.append(pandas.to_datetime(value))
                        except:
                            raise Exception("Error in MSHDB.__format_dates: value (" + value + ") in column " + col + " of sheet " + sh + " is not a valid date")

                    try:
                        if len(date_values) > 0:
                            # change the datetime format
                            sd.df[col] = pandas.Series(date_values).dt.strftime(self.date_format)
                    except:
                        raise Exception("Error in MSHDB.__format_dates: value (" + date_values + ") in column " + col + " of sheet " + sh + " cannot be formatted as desired")

    def __round_columns(self):
        for sh in self.to_be_rounded:
            if sh in self.sheets.keys():
                ds:SubjectsData = self.sheet_sd(sh)
                if ds.num == 0:
                    continue
                for col in self.to_be_rounded[sh]:
                    ds.df[col] = ds.df[col].apply(lambda x: round(x, self.round_decimals) if str(x) != "" else x)

                    # ds.df[col] = ds.df[col].round(self.round_decimals)

    def is_equal(self, db:'MSHDB'):
        return self.sheets.is_equal(db.sheets)

    def add_column(self, col_label, values, subjs:SubjectSDList=None, position=None, df=None, update=False) -> 'MSHDB':

        sheets = self.sheets.copy()

        for sh in self.sheets:
            sheets[sh].add_column(col_label, values, subjs, position, df)

        if update:
            self.sheets = sheets

        return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)

    # presently not used. TODO: fix MSHDB.check_labels
    def check_labels(self, newsubjs:SubjectSDList, sheet:str) -> bool:
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
