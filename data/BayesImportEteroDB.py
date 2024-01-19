import io
from typing import List

import msoffcrypto
import pandas
import pandas as pd
import os

from data.BayesDB import BayesDB
from utility.exceptions import DataFileException
from data.SubjectsData import SubjectsData
from data.Sheets import Sheets

class BayesImportEteroDB:

    schema_sheets_names = ["main", "HAM A-D", "PANSS", "SANS", "SAPS", "TATE", "TLC", "YMRS"]

    subj                = ""
    session             = 1
    group               = ""

    scales_data = {
        "HAM A-D":[{"HAMA1":3},{"HAMA2":4},{"HAMA3":5},{"HAMA4":6},{"HAMA5":7},{"HAMA6":8},{"HAMA7":9},{"HAMA8":10},{"HAMA9":11},{"HAMA10":12},{"HAMA11":13},{"HAMA12":14},{"HAMA13":15},{"HAMA14":16},{"HAMATOT":17},{"HAMD1":20},{"HAMD2":26},{"HAMD3":32},{"HAMD4":38},{"HAMD5":42},{"HAMD6":46},{"HAMD7":50},{"HAMD8":56},{"HAMD9":62},{"HAMD10":68},{"HAMD11":74},{"HAMD12":80},{"HAMD13":84},{"HAMD14":88},{"HAMD15":92},{"HAMD16":98},{"HAMD17":108},{"HAMD18A":112},{"HAMD18B":116},{"HAMD19":120},{"HAMD20":125},{"HAMD21":130},{"HAMDTOT":134}],
        "PANSS":  [{"PANSS_p1":3},{"PANSS_p2":4},{"PANSS_p3":5},{"PANSS_p4":6},{"PANSS_p5":7},{"PANSS_p6":8},{"PANSS_p7":9},{"PANSS_n1":12},{"PANSS_n2":13},{"PANSS_n3":14},{"PANSS_n4":15},{"PANSS_n5":16},{"PANSS_n6":17},{"PANSS_n7":18},{"PANSS_g1":21},{"PANSS_g2":22},{"PANSS_g3":23},{"PANSS_g4":24},{"PANSS_g5":25},{"PANSS_g6":26},{"PANSS_g7":27},{"PANSS_g8":28},{"PANSS_g9":29},{"PANSS_g10":30},{"PANSS_g11":31},{"PANSS_g12":32},{"PANSS_g13":33},{"PANSS_g14":34},{"PANSS_g15":35},{"PANSS_g16":36},{"PANSS_TOT_P": 10},{"PANSS_TOT_N": 19},{"PANSS_TOT_G": 37},{"PANSS_TOT": 38}],
        "SANS":   [{"SANS_1": 3}, {"SANS_2": 4}, {"SANS_3": 5}, {"SANS_4": 6}, {"SANS_5": 7}, {"SANS_6": 8}, {"SANS_7": 9}, {"SANS_8": 10}, {"SANS_9": 12}, {"SANS_10": 13}, {"SANS_11": 14}, {"SANS_12": 15}, {"SANS_13": 16}, {"SANS_14": 18}, {"SANS_15": 19}, {"SANS_16": 20}, {"SANS_17": 21}, {"SANS_18": 23}, {"SANS_19": 24}, {"SANS_20": 25}, {"SANS_21": 26}, {"SANS_22": 27}, {"SANS_23": 29}, {"SANS_24": 30}, {"SANS_25": 31}, {"SANS_TOT": 32}],
        "SAPS":   [{"SAPS_1":3}, {"SAPS_2":4}, {"SAPS_3":5}, {"SAPS_4":6}, {"SAPS_5":7}, {"SAPS_6":8}, {"SAPS_7":9}, {"SAPS_8":11}, {"SAPS_9":12}, {"SAPS_10":13},{"SAPS_11":14}, {"SAPS_12":15}, {"SAPS_13":16}, {"SAPS_14":17}, {"SAPS_15":18}, {"SAPS_16":19}, {"SAPS_17":20}, {"SAPS_18":21}, {"SAPS_19":22}, {"SAPS_20":23}, {"SAPS_21":25}, {"SAPS_22":26}, {"SAPS_23":27}, {"SAPS_24":28}, {"SAPS_25":29}, {"SAPS_26":31}, {"SAPS_27":32}, {"SAPS_28":33}, {"SAPS_29":34}, {"SAPS_30":35}, {"SAPS_31":36}, {"SAPS_32":37}, {"SAPS_33":38}, {"SAPS_34":39},{"SAPS_TOT":40}],
        "TLC":    [{"TLC_1": 2}, {"TLC_2": 8}, {"TLC_3": 14}, {"TLC_4": 20}, {"TLC_5": 26}, {"TLC_6": 32},{"TLC_7": 38}, {"TLC_8": 44}, {"TLC_9": 50}, {"TLC_10": 56}, {"TLC_11": 61}, {"TLC_12": 66},{"TLC_13": 71}, {"TLC_14": 76}, {"TLC_15": 81}, {"TLC_16": 86}, {"TLC_17": 91}, {"TLC_18": 96},{"TLC_19": 101}, {"TLC_20": 106}, {"TLC_TOT":112}],
        "YMRS":   [{"YMRS_1": 2}, {"YMRS_2": 8}, {"YMRS_3": 14}, {"YMRS_4": 20}, {"YMRS_5": 26}, {"YMRS_6": 32},{"YMRS_7": 38}, {"YMRS_8": 44}, {"YMRS_9": 50}, {"YMRS_10": 56}, {"YMRS_11": 62}, {"YMRS_TOT":68}]
    }

    scales_data_ex = {
        "TATE":   [{"1a": 2}, {"1b": 3}, {"1c": 4}, {"2a": 5}, {"2b": 6}, {"2c": 7}, {"3a": 8}, {"3b": 9}, {"3c": 10},{"3d": 11}, {"3e": 12}, {"3f": 13}, {"4a": 14}, {"4b": 15}, {"4c": 16}, {"5a": 17}, {"5b": 18},{"5c": 19}, {"5d": 20}, {"5e": 21}, {"5f": 22}, {"6a": 23}, {"6b": 24}, {"6c": 25}, {"6d": 26},{"6e": 27}, {"6f": 28}, {"6g": 29}, {"6h": 30}, {"6i": 31}, {"6j": 32}, {"6k": 33}, {"6l": 34},{"6m": 35}, {"6n": 36}, {"7a": 37}, {"7b": 38}, {"7c": 39}, {"7d": 40}, {"7e": 41}, {"7f": 42},{"7g": 43}]
    }


    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    round_decimals      = 2

    # format: each key (e.g. main) is a sheet name.
    # each value is a list of dictionary specifying the rows to be modified (key) and the id of the column to modify

    dates               = {"main":[{"DATA DI NASCITA":1}, {"DATA RECLUTAMENTO":1}]}
    to_be_rounded       = {"main":[{"ETA":1}]}

    def __init__(self, data=None, password:str=""):
        super().__init__()
        self.main_name          = "main"
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

            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name)
                self.sheets[sheet_name] = df

        elif isinstance(data, dict):
            # TODO check is a dict of sheetname:subjectsdata
            self.sheets = data

        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str, not a dict")

        return self.sheets

    def sheet_df(self, name:str) -> pandas.DataFrame:
        if name not in self.schema_sheets_names:
            raise Exception("Error in MSHDB.sheet: ")
        return self.sheets[name]

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
                self.sheet_df(sh).iloc[row_id, value] = round(df.iloc[row_id, value], self.round_decimals)

    def __format_dates(self):
        for sh in self.dates:
            df:pandas.DataFrame = self.sheets[sh]
            if df.size == 0:
                continue

            for col in self.dates[sh]:
                label = list(col.keys())[0]
                value = list(col.values())[0]

                row_id = list(df["LABELS"]).index(label)
                self.sheet_df(sh).iloc[row_id, value] = df.iloc[row_id, value].strftime(self.date_format)
                # formatted_date = df.loc[df['LABELS'] == label]["VALUES"].iat[0].strftime(self.date_format)

    def add_2_bayes(self, bayes_db) -> BayesDB:

        if isinstance(bayes_db, str):
            pass
        elif isinstance(bayes_db, BayesDB):
            pass
        else:
            pass

    def export_bayes(self, outfile=None, bayes_main_id:int=0) -> BayesDB:

        sheets = Sheets(self.schema_sheets_names, 0)
        try:
            sheets["main"] = SubjectsData(self.get_main())
            for s in self.scales_data:
                sheets[s] = SubjectsData(self.get_scale(s))

            # for s in self.scales_data_ex:
            #     sheets[s] = SubjectsData(self.get_scale(s))
        except:
            raise Exception("Error in BayesImportEteroDB.export_bayes: ")
        return BayesDB(sheets)


    def get_main(self) -> pandas.DataFrame:

        self.main_columns = [   "subj", "session", "group", "centre", "mri_code", "immfen_code", "birth_date",
                                "recruitment_date", "age", "gender", "auto", "etero"]

        self.default_cols = [   "mri", "oa", "nk", "t", "m", "b", "prot",
                                "mat", "mri_oa", "mri_nk", "mri_t", "mri_m", "mri_b", "mri_prot"]

        self.subj               = self.sheet_df("main").iloc[2,1]
        self.session            = self.sheet_df("main").iloc[3,1]
        self.group              = self.sheet_df("main").iloc[8,1]

        main = {}
        main["subj"]            = self.subj
        main["session"]         = self.session
        main["group"]           = self.group
        main["centre"]          = self.sheet_df("main").iloc[7,1]
        main["mri_code"]        = ""
        main["immfen_code"]     = ""
        main["birth_date"]      = self.sheet_df("main").iloc[4,1]
        main["recruitment_date"]= self.sheet_df("main").iloc[1,1]
        main["age"]             = self.sheet_df("main").iloc[5,1]
        main["gender"]          = self.sheet_df("main").iloc[6,1]
        main["auto"]            = 0
        main["etero"]           = 1

        for k in self.default_cols:
            main[k] = 0

        return pd.DataFrame.from_dict([main])

    def get_scale(self, scale_name:str)-> pandas.DataFrame:
        scale       = {"subj":self.subj, "session":self.session, "group":self.group}
        scale_data  = self.scales_data[scale_name]
        df          = self.sheet_df(scale_name)
        values_id   = df.columns.get_loc("VALUES")
        for item in scale_data:
            row_id                      = list(item.values())[0] - 2  # ID are set including the header
            value                       = df.iloc[row_id,values_id]
            scale[list(item.keys())[0]] = value

        return pd.DataFrame.from_dict([scale])

    def get_scale_ex(self, scale_name:str)-> pandas.DataFrame:
        scale       = {"subj":self.subj, "session":self.session, "group":self.group}
        scale_data  = self.scales_data[scale_name]
        df          = self.sheet_df(scale_name)
        values1_id   = df.columns.get_loc("VALUES_1")
        values2_id   = df.columns.get_loc("VALUES_2")
        values3_id   = df.columns.get_loc("VALUES_3")

        for item in scale_data:
            row_id                      = list(item.values())[0]-1  # ID are set including the header
            value                       = self.sheet_df(scale_name).iloc[row_id,"VALUES"]
            scale[list(item.keys())[0]] = value

        return pd.DataFrame.from_dict([scale])