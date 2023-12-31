from typing import List

import msoffcrypto
import pandas
import pandas as pd
import os

from data.Sheets import Sheets
from data.BayesDB import BayesDB
from utility.exceptions import DataFileException


class BayesImportEteroDB:

    schema_sheets_names = ["main", "HAM A-D", "PANS", "SANS", "SAPS", "TATE", "TLC", "YMRS"]

    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    round_decimals      = 2

    # format: each key (e.g. main) is a sheet name.
    # each value is a list of dictionary specifying the rows to be modified (key) and the id of the column to modify

    dates               = {"main":[{"birth_date":1}, {"recruitment_date":1}]}
    to_be_rounded       = {"main":[{"age":1}]}

    def __init__(self, data=None, password:str=""):
        super().__init__()
        self.main_name          = self.schema_sheets_names[0]      # e.g. "main"
        self.password           = password
        self.filepath           = ""
        self.sheets             = {}

        if data is not None:
            self.load(data)

        self.__format_dates()
        self.__round_columns()

        self.calc_tot()

    def load(self, data=None, validcols:list=None, cols2num:list=None, delimiter='\t') -> dict:

        if isinstance(data, str):

            if not os.path.exists(data):
                raise DataFileException("BayesImportEteroDB.load", "given data param (" + data + ") is not a valid file")

            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise Exception("Error in BayesImportEteroDB.load: unknown data file format")

            self.filepath   = data

            if self.password != "":
                data = self.decrypt_excel(data, self.password)

            xls = pd.ExcelFile(data)

            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet)
                self.sheets[sheet] = df

        elif isinstance(data, dict):
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

    def calc_tot(self):

        flags   = [ {"main":["mri_code"]},
                    {"OA":["oa"]},
                    {"sangue":["NK"]}, {"sangue":["T_HELP", "T_REG"]}, {"sangue":["MONO"]}, {"sangue":["B"]}, {"sangue":["PROT"]},
                    {"MATRICS":["matrics_date"]},
                    {"main":["mri_code"], "OA":["oa"]},
                    {"main":["mri_code"], "sangue":["NK"]}, {"main":["mri_code"], "sangue":["T_HELP", "T_REG"]}, {"main":["mri_code"], "sangue":["MONO"]}, {"main":["mri_code"], "sangue":["B"]}, {"main":["mri_code"], "sangue":["PROT"]}
                  ]

    def __round_columns(self):
        for sh in self.to_be_rounded:
            df:pandas.DataFrame = self.sheets[sh]
            if df.size == 0:
                continue
            for col in self.to_be_rounded[sh]:
                label = list(col.keys())[0]
                value = list(col.values())[0]

                row_id = list(df["LABELS"]).index(label)
                self.sheets[sh].iloc[row_id, value] = round(df.iloc[row_id, value], self.round_decimals)

    def __format_dates(self):
        for sh in self.dates:
            df:pandas.DataFrame = self.sheets[sh]
            if df.size == 0:
                continue

            for col in self.dates[sh]:
                label = list(col.keys())[0]
                value = list(col.values())[0]

                row_id = list(df["LABELS"]).index(label)
                self.sheets[sh].iloc[row_id, value] = df.iloc[row_id, value].strftime(self.date_format)
                # formatted_date = df.loc[df['LABELS'] == label]["VALUES"].iat[0].strftime(self.date_format)

    def add_2_bayes(self, bayes_db) -> BayesDB:

        if isinstance(bayes_db, str):
            pass
        elif isinstance(bayes_db, BayesDB):
            pass
        else:
            pass

    def export_bayes(self, outfile) -> BayesDB:

        pass

