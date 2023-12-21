import io
import os

import msoffcrypto
import pandas
import pandas as pd
from typing import List
import collections
from utility.exceptions import DataFileException
from data.utilities import FilterValues
from data.SubjectsData import SubjectsData
from utility.list import UnionNoRepO, same_elements, first_contained_in_second, intersection, get_intersecting
from data.Sheets import Sheets

class MSHDB:

    valid_dtypes = ['Int8', 'Int16', 'Int32', 'Int64', 'UInt8', 'UInt16', 'UInt32', 'UInt64', 'float64', 'float32']

    def __init__(self, data=None, sheetnames:List[str]=None, main_id:int=0, suppress_nosubj=True, first_col_name="subj", can_different_subjs=False, password:str=""):

        super().__init__()
        self.schema_sheets_names= sheetnames
        self.main_id            = main_id
        self.first_col_name     = first_col_name        # e.g. "subj"
        self.can_diff_subjs     = can_different_subjs
        self.password           = password

        self.main_name          = sheetnames[main_id]      # e.g. "main"

        self.filepath           = ""
        self.sheets             = Sheets(self.schema_sheets_names, main_id)

        if data is not None:
            self.load(data, suppress_nosubj)

    # self.main sheet contains the list of DB subjects
    @property
    def subj_labels(self) -> list:
        if self.main_name not in self.sheets:
            return []
        else:
            return self.sheets[self.main_name].subj_labels

    @property
    def sheet_labels(self) -> list:
        if bool(self.sheets):
            return len(self.sheets.keys())
        else:
            return 0

    def check_labels(self, newlabels:List[str], sheet:str) -> bool:
        if sheet == self.main_name:
            return True

        if self.main_name not in self.sheets:
            return True
        else:
            # HERE main sheets is loaded and self.labels is set
            if collections.Counter(newlabels) != collections.Counter(self.subj_labels):
                nl  = newlabels.copy()
                l   = self.subj_labels.copy()
                for lab in self.subj_labels[:]:
                    if (lab in nl):
                        l.remove(lab)
                        nl.remove(lab)

                raise Exception("Error in MSSubjectsData.load: labels of sheet " + sheet + " does not correspond to main one...correct XLS file\n")
            else:
                return True

    def load(self, data=None, validcols:list=None, cols2num:list=None, delimiter='\t', suppress_nosubj=True) -> Sheets:

        if isinstance(data, str):

            if not os.path.exists(data):
                raise DataFileException("MXLSDB.load", "given data param (" + data + ") is not a valid file")

            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise Exception("Error in MXLSDB.load: unknown data file format")

            self.filepath   = data

            if self.password != "":
                data = self.decrypt_excel(data, self.password)

            xls = pd.ExcelFile(data)

            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet)
                # verify first column is called like self.first_col_name
                if df.columns[0] != self.first_col_name:
                    if suppress_nosubj:
                        df.columns.values[0] = self.first_col_name
                        print("Warning in MXLSDB.load: first column was not called subj, I renamed it to subj....check if it's ok")
                    else:
                        raise Exception("Error in MXLSDB.load: first column is not called " + self.first_col_name)

                sd = SubjectsData(df)
                if not self.can_diff_subjs:
                    self.check_labels(sd.subj_labels, sheet)  # raise an exception

                self.sheets[sheet] = sd

        elif isinstance(data, Sheets):
            # TODO check is a dict of sheetname:subjectsdata
            self.sheets = data

        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str, not a dict")

        return self.sheets

    def decrypt_excel(self, fpath, pwd):
        unlocked_file = io.BytesIO()

        with open(fpath, "rb") as file:
            excel_file = msoffcrypto.OfficeFile(file)
            excel_file.load_key(password=pwd)
            excel_file.decrypt(unlocked_file)

        return unlocked_file
    # ======================================================================================
    #region SELECT (labs, sheets_cols) DataFrame
    # e.g. : sheets_cols = {"main": ["group", "Eta", "sesso"],
    #                       "SAPS": ["SAPS_TOT"],
    #                       "YMRS": ["YMRS_TOT"]}
    # SUBSET all excel by rows and sheets' cols
    def select_df(self, subj_labels: List[str] = None, sheets_cols: dict = None, outfile: str = "") -> pandas.DataFrame:

        if subj_labels is None and sheets_cols is None:
            return None

        df = pandas.DataFrame()

        df[self.first_col_name] = subj_labels

        for sheetname in sheets_cols:
            sd:SubjectsData = self.sheets[sheetname]
            cols:List[str]  = sheets_cols[sheetname]
            if cols[0] == "*":
                hdr = sd.header.copy()
                hdr.remove(self.first_col_name)
                if "group" in hdr:
                    hdr.remove("group")
                df = pd.concat([df, sd.select_df(subj_labels, hdr)], axis=1)
            else:
                df = pd.concat([df, sd.select_df(subj_labels, cols)], axis=1)

        if outfile != "":
            df.to_excel(outfile, index=False)

        return df

    def add_default_rows(self, subj_labels:List[str]=None):
        df                      = pandas.DataFrame()
        df[self.first_col_name] = subj_labels

        return df

    def add_default_row(self, subj_label:str):
        return {self.first_col_name: subj_label}

    # subjdf must contain a subj column (all its subjects must be already present)
    def add_new_columns(self, shname:str, subjdf:pandas.DataFrame):

        sheet_sd    = self.sheets[shname]

        if self.first_col_name not in subjdf.columns.values:
            raise Exception("Error in addColumns: given subjdf does not contain a subj column")

        new_subjlist = subjdf[self.first_col_name]
        if first_contained_in_second(new_subjlist, self.subj_labels):   # all subjects included in subjdf are already present in the db
            sheet_sd.add_columns_df(subjdf, can_overwrite=False)
        else:
            raise Exception("Error in MSSD")

    # add brand-new subjects:
    # Since it thought to may accept also incomplete sheets. it must preserve db integrity
    # (e.g. in some sheets there are data of s1, s2, s4, in other of s1, s3, s4)
    # ->    it must consider all four subjects and thus add a row with only the subj name where it's absent
    #       in the first sheet add s3 and in the second s2.
    # Moreover must create also all those sheets not present in new data with a row for each subject with just a subj column
    #
    # parse all sheets and determine the list of all subjects contained across all given sheets
    # if it finds a new subj that already existed -> raise exception
    def add_new_subjects(self, newdb, can_diff_subjs:None, update=False) -> 'MSHDB':

        if can_diff_subjs is None:
            can_diff_subjs = self.can_diff_subjs

        # this method cannot overwrite existing subjects: thus verify that added subjects are really new
        all_subjs = newdb.sheets.all_subjects    # all subjects included in all new sheets
        if intersection(self.subj_labels, all_subjs):
            raise Exception("Error in MSHDB.add_new_subjects: at least one new subject (" + str(get_intersecting(self.subj_labels, all_subjs)) + ") already exist in the db. not allowed. check new data")

        # verify that subjects lists are identical across sheets
        if can_diff_subjs is False and not self.sheets.is_consistent:
            raise Exception("Error in MSSubjectsData.add_subjects: sheets subjects differs")

        # start cycling through all existing sheets, adding missing sheets with new subj rows or adjusting the given sheets with missing subjects
        for sh in self.schema_sheets_names:

            if sh not in list(newdb.sheets.keys()):
                # new info are not in this sheet -> I must create a sd (with a single subj column containing the new subject list) and add this new sheet
                df = newdb.add_default_rows(all_subjs)
                newdb.sheets[sh] = SubjectsData(df)
            else:
                # one of the sheet containing new data -> I must add to the new data, a row for all other subjects not present in this new sheet
                ds = newdb.sheets[sh]
                for subjlab in all_subjs:
                    if subjlab not in ds.subj_labels:
                        # this subj exist in some other new sheets, but not here -> add it
                        ds.add_row(subjlab, newdb.add_default_row(subjlab))

        # has all sheets and all subjects are brand new

        if update is True:
            for sh in newdb.sheets:
                self.sheets[sh].add_sd([newdb.sheets[sh]])
            return True

        else:
            sheets = self.sheets.copy()
            for sh in newdb.sheets:
                sheets[sh].add_sd([newdb.sheets[sh]])
            return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)

    def remove_subjects(self, subjects2remove:List[str], update=False) -> 'MSHDB':

        sheets = self.sheets.copy()
        for sh in self.sheets:
            sheets[sh] = sheets[sh].remove_subjects(subjects2remove)

        if update:
            self.sheets = sheets.copy()
            return self
        else:
            return MSHDB(sheets, self.schema_sheets_names, self.main_id, first_col_name=self.first_col_name)

    def save_excel(self, outfile):

        with pd.ExcelWriter(outfile) as writer:
            for sh in self.schema_sheets_names:
                self.sheets[sh].df.to_excel(writer, sheet_name=sh, index=False)
        print("Saved file: " + outfile)

    def is_equal(self, db:'MSHDB'):
        return self.sheets.is_equal(db.sheets)