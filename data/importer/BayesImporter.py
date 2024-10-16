import datetime
import io
from typing import List
import json

import msoffcrypto
import numpy
import pandas
import pandas as pd
import os

from data.BayesDB import BayesDB
from myutility.exceptions import DataFileException
from data.SubjectsData import SubjectsData
from data.Sheets import Sheets


class BayesImporter:
    """
    This class provides methods to import data from an excel file into a BayesDB object.
    Args:
        import_schema (str) : path to json containing valid columns
        data (str or dict): The path to the excel file to be parsed or a dictionary of the sheets.
        bayes_schema (str) : path to json containing full bayes schema
        password (str, optional): The password for decrypting the excel file. Defaults to "".

    Attributes:
        input_sheets_names (list): A list of the names of the input sheets to be parsed automatically through the json schema.
        schema_sheets_names (list): A list of the names of the output sheets after parsing the excel.
        subj (str): The subject ID.
        session (int): The session number.
        group (str): The group name.
        date_format (str): The date format used in the EteroDB files.
        round_decimals (int): The number of decimal places to round numeric values to.
        dates (dict): A dictionary of the sheet names and the columns to format as dates.
        to_be_rounded (dict): A dictionary of the sheet names and the columns to round.
        schemas_json (str): full path of the json schema to parse the excel
        main_name (str): The name of the main sheet.
        password (str): The password for decrypting the EteroDB file.
        filepath (str): The path to the EteroDB file.
        sheets (dict): A dictionary of the sheet names and their dataframes.
    """
    input_sheets_names:list     = []
    schema_sheets_names:list    = []
    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    round_decimals      = 2
    # format: each key (e.g. main) is a sheet name.
    # each value is a list of dictionary specifying the rows to be modified (key) and the id of the column to modify
    # these values are defined in the json
    to_be_rounded:dict   = {}
    dates:dict           = {}

    subj                = ""
    session             = 1
    group               = ""

    import_schema:dict  = {}
    bayes_schema:dict   = {}

    empty_value         = "INSERISCI"

    sheets:Sheets       = None

    def __init__(self,  import_schema_file: str,
                        bayes_schema:str,
                        data: str | dict = None,
                        password: str = ""):
        super().__init__()

        self.bayes_schema_file  = bayes_schema
        self.import_schema_file = import_schema_file
        self.password           = password
        self.filepath           = ""

        with open(import_schema_file) as json_file:
            self.import_schema = json.load(json_file)

            self.input_sheets_names     = self.import_schema["in_sheets_names"]
            self.schema_sheets_names    = self.import_schema["out_sheets_names"]

            self.main_id                = self.import_schema["main_id"]
            self.date_format            = self.import_schema["date_format"]
            self.dates                  = self.import_schema["dates"]
            self.to_be_rounded          = self.import_schema["to_be_rounded"]
            self.round_decimals         = self.import_schema["round_decimals"]

        self.main_name                  = self.schema_sheets_names[self.main_id]

        with open(bayes_schema) as json_file:
            self.bayes_schema = json.load(json_file)

        if data is not None:
            self.load(data)

    def load(self, data:str|dict=None, validcols:list=None, cols2num:list=None, delimiter='\t') -> BayesDB:
        """
        Load data from a file or a dictionary of sheets.

        Parameters
        ----------
        data : str or dict
            The path to the file or a dictionary of sheets.
        validcols : list
            A list of valid columns.
        cols2num : list
            A list of columns to convert to numeric.
        delimiter : str
            The delimiter used in the file.

        Returns
        -------
        dict
            A dictionary of sheets.

        Raises
        ------
        DataFileException
            If the given data is not a valid file.
        Exception
            If the data file format is unknown.
        """
        if isinstance(data, str):
            # Check if the given data is a file
            if not os.path.exists(data):
                raise DataFileException("BayesImporter.load", "given data param (" + data + ") is not a valid file")

            # Check if the file is an Excel file
            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise Exception("Error in BayesImporter.load: unknown data file format")

            # Set the filepath
            self.filepath = data

            # Check if a password is set
            if self.password != "":
                # Decrypt the Excel file
                data = self.__decrypt_excel(data, self.password)

            # Read the Excel file
            xls = pd.ExcelFile(data)

            self.sheets = Sheets(sh_names=self.schema_sheets_names, main_id=self.main_id)

            # Loop through the sheets
            for sheet_name in xls.sheet_names:

                if sheet_name in self.schema_sheets_names:
                    self.sheets[sheet_name] = SubjectsData(pd.read_excel(xls, sheet_name), check_data=False)

        elif isinstance(data, dict):
            # Check if the given data is a dictionary of sheets
            # TODO: Check if the dictionary contains valid sheets
            self.sheets = Sheets(data, sh_names=self.schema_sheets_names, main_id=self.main_id)

        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str, not a dict")

        self.__format_dates()
        self.__round_columns()

        # adjust each sheet
        if "auto" in self.import_schema_file:
            self.__set_main_auto()
        else:
            self.__set_main()

        for sh in self.input_sheets_names:
            self.__set_sheet(sh)

        # self.check_tot()
        return BayesDB(self.bayes_schema_file, self.sheets, calc_flags=False)

    def __decrypt_excel(self, fpath: str, pwd: str) -> io.BytesIO:
        """Decrypts an Excel file using the given password.

        Args:
            fpath (str): The path to the Excel file.
            pwd (str): The password for decrypting the file.

        Returns:
            io.BytesIO: The decrypted Excel file as a BytesIO object.
        """
        unlocked_file = io.BytesIO()

        with open(fpath, "rb") as file:
            excel_file = msoffcrypto.OfficeFile(file)
            excel_file.load_key(password=pwd)
            excel_file.decrypt(unlocked_file)

        return unlocked_file

    def __round_columns(self):
        """
        Rounds the values of the specified columns to the specified number of decimal places.

        Returns:
            None
        """
        for sh in self.to_be_rounded:
            df: pandas.DataFrame = self.sheets.sheet_df(sh)
            if df.size == 0:
                continue
            for col in self.to_be_rounded[sh]:
                label = list(col.keys())[0]
                value = list(col.values())[0]

                row_id = list(df["LABELS"]).index(label)
                self.sheets.sheet_df(sh).iloc[row_id, value] = round(df.iloc[row_id, value], self.round_decimals)

    def __format_dates(self):
        """
        Formats the dates in the specified sheets.

        Returns:
            None
        """
        for sh in self.dates:
            df: pandas.DataFrame = self.sheets.sheet_df(sh)
            if df.size == 0:
                continue

            for col in self.dates[sh]:
                label = list(col.keys())[0]
                value = list(col.values())[0]

                id_row  = [i for i, v in enumerate(list(df["LABELS"])) if label in v][0]
                val     = df.iloc[id_row, value]

                if isinstance(val, datetime.datetime):
                    # series = df["LABELS"]
                    # row_id = series[series.str.contains(label)].index   #list(df["LABELS"]).index(label)
                    self.sheets.sheet_df(sh).iloc[id_row, value] = df.iloc[id_row, value].strftime(self.date_format)
                else:
                    self.sheets.sheet_df(sh).iloc[id_row, value] = ""
                    # formatted_date = df.loc[df['LABELS'] == label]["VALUES"].iat[0].strftime(self.date_format)

    def __set_main(self):
        """
        This function returns the main dataframe of the EteroDB file.

        Returns:
            pandas.DataFrame: The main dataframe of the EteroDB file.
        """
        # self.main_columns = {   "subj":"", "session":1, "group":"", "centre":"", "birth_date":"",
        #                         "recruitment_date":"", "age":0, "gender":"", "auto":0, "etero":0}

        self.main_default_cols = {"mri":0, "oa":0, "nk":0, "t":0, "m":0, "b":0, "prot":0,
                                "mat":0, "mri_oa":0, "mri_nk":0, "mri_t":0, "mri_m":0, "mri_b":0, "mri_prot":0}

        df = self.sheets.sheet_df("main")

        main    = {}
        SA      = {}
        CLINIC  = {}

        main["subj"]            = df.iloc[2,1] + " " + df.iloc[3,1]
        main["session"]         = df.iloc[4,1]
        main["group"]           = df.iloc[13,1]

        if main["session"] is numpy.nan:
            main["session"] = 1

        self.subj               = main["subj"]
        self.session            = main["session"]
        self.group              = main["group"]

        SA["subj"]              = self.subj
        SA["session"]           = self.session
        SA["group"]             = self.group

        CLINIC["subj"]          = self.subj
        CLINIC["session"]       = self.session
        CLINIC["group"]         = self.group

        main["recruiter"]       = df.iloc[0,1]
        main["recruitment_date"]= df.iloc[1,1]
        main["birth_date"]      = df.iloc[5,1]
        main["age"]             = df.iloc[6,1]
        main["gender"]          = df.iloc[7,1]
        main["centre"]          = df.iloc[8,1]

        SA["country"]           = df.iloc[9,1]
        SA["phone"]             = df.iloc[10,1]
        CLINIC["hospitalization"]       = df.iloc[11,1]
        CLINIC["origin"]                = df.iloc[12,1]
        CLINIC["primary_diagnosis"]     = df.iloc[14,1]
        CLINIC["bd_phase"]              = df.iloc[15,1]
        CLINIC["psicomotricity"]      =  df.iloc[16,1]
        CLINIC["ideation"]            = df.iloc[17,1]
        CLINIC["humour"]              = df.iloc[18,1]
        CLINIC["psicothic_sympt"]     = df.iloc[19,1]
        CLINIC["psicothic_features"]  = df.iloc[20,1]
        SA["dominant_hand"]         = df.iloc[21,1]
        SA["height"]                = df.iloc[22,1]
        SA["weight"]                = df.iloc[23,1]
        SA["BMI"]                   = df.iloc[24,1]
        SA["birth_type"]            = df.iloc[25,1]
        SA["birth_place"]           = df.iloc[26,1]
        SA["mother_surname"]        = df.iloc[27,1]
        SA["mother_birthdate"]      = df.iloc[28,1]
        SA["father_surname"]        = df.iloc[29,1]
        SA["father_birthdate"]      = df.iloc[30,1]
        SA["gestation_weeks"]       = df.iloc[31,1]
        SA["nascitaXXXXXXXX"]       = df.iloc[32,1]
        SA["birth_weight"]          = df.iloc[33,1]
        SA["weight_category"]       = df.iloc[34,1]
        SA["birth_issues"]          = df.iloc[35,1]
        SA["perinatal_infections"]  = df.iloc[36,1]
        SA["alimentation_birth"]    = df.iloc[37,1]
        CLINIC["psych_motor_develop"] = df.iloc[38,1]
        SA["brothers_sisters"]      = df.iloc[39,1]
        SA["marital_status"]        = df.iloc[40,1]
        SA["family_type"]           = df.iloc[41,1]
        SA["education"]             = df.iloc[42,1]
        SA["years_education"]       = df.iloc[43,1]
        SA["supp_teacher"]          = df.iloc[44,1]
        SA["job"]                   = df.iloc[45,1]
        SA["socioecon_cond"]        = df.iloc[46,1]
        SA["residency"]             = df.iloc[47,1]
        SA["period"]                = df.iloc[48,1]
        SA["period_onset_age"]      = df.iloc[49,1]
        SA["finalized_pregnancies"] = df.iloc[50,1]
        SA["tot_pregnancies"]       = df.iloc[51,1]
        CLINIC["physical_activity"]     = df.iloc[52,1]
        CLINIC["learn_disorders"]     = df.iloc[53,1]
        CLINIC["disdur"]              = df.iloc[54,1]
        CLINIC["nontreat_disdur"]     = df.iloc[55,1]
        CLINIC["onset_age"]           = df.iloc[56,1]
        CLINIC["first_phase"]         = df.iloc[57,1]
        CLINIC["first_treat_age"]     = df.iloc[58,1]
        CLINIC["first_hospitaliz"]    = df.iloc[59,1]
        CLINIC["num_hospit"]          = df.iloc[60,1]
        CLINIC["num_tso"]             = df.iloc[61,1]
        CLINIC["tsoXXXXXXXXXXXX"]     = df.iloc[62,1]
        CLINIC["interepis_symptoms"]  = df.iloc[63,1]
        CLINIC["suicidality"]         = df.iloc[64,1]
        CLINIC["suicidality_type"]    = df.iloc[65,1]
        CLINIC["etero_aggressivity"]  = df.iloc[66,1]

        for i, (k, v) in enumerate(self.main_default_cols.items()):
            main[k] = v

        main["etero"]           = 1

        self.sheets["main"]     = SubjectsData(pd.DataFrame.from_dict([main]))
        self.sheets["SA"]       = SubjectsData(pd.DataFrame.from_dict([SA]))
        self.sheets["CLINIC"]   = SubjectsData(pd.DataFrame.from_dict([CLINIC]))

    # provisional,
    # assumes the subject already exist in the DB, use main sheet info to get the correct subject's ID
    def __set_main_auto(self):
        """
        This function returns the main dataframe of the EteroDB file.

        Returns:
            pandas.DataFrame: The main dataframe of the EteroDB file.
        """
        # self.main_columns = {   "subj":"", "session":1, "group":"", "centre":"", "birth_date":"",
        #                         "recruitment_date":"", "age":0, "gender":"", "auto":0, "etero":0}

        df = self.sheets.sheet_df("main")

        main    = {}

        main["subj"]            = df.iloc[0,1] + " " + df.iloc[1,1]
        main["session"]         = df.iloc[2,1]
        main["group"]           = df.iloc[3,1]

        if main["session"] is numpy.nan:
            main["session"] = 1

        self.subj               = main["subj"]
        self.session            = main["session"]
        self.group              = main["group"]

        main["auto"]           = 1

        self.sheets["main"]     = SubjectsData(pd.DataFrame.from_dict([main]))

    # presently unused
    def __set_sheet(self, scale_name: str):
        """
        This function creates a new SubjectsData in each sheet.
        Only the excel columns with a non empty string in the first row are inserted in the dataframe when imported

        Args:
            scale_name (str): The name of the scale.

        Returns:
            pandas.DataFrame: A pandas dataframe containing the data for the specified scale.

        Raises:
            ValueError: If the given scale name is not valid.
        """
        df = self.sheets.sheet_df(scale_name)
        sh = {"subj": self.subj, "session": self.session, "group": self.group}

        try:
            for item in self.import_schema[scale_name]:

                if item == "CAN_BE_EMPTY":
                    continue

                r = self.import_schema[scale_name][item][0]
                c = self.import_schema[scale_name][item][1]

                if r < df.shape[0] and c < df.shape[1]:

                    value = df.iloc[r, c]

                    # check whether is an empty value
                    if value == self.empty_value:
                        still_valid = False     # by default is not a valid scale
                        # check if this empty value is allowed
                        if "CAN_BE_EMPTY" in self.import_schema[scale_name].keys():
                            # this scale allow at least one empty value
                            for i,canempty_elem in enumerate(self.import_schema[scale_name]["CAN_BE_EMPTY"]):
                                if canempty_elem[0] == r and canempty_elem[1] == c:
                                    sh[item]    = numpy.nan     # this value can be empty
                                    still_valid = True          # set the flag to avoid scale deletion
                                    continue                    # exit the for

                        if still_valid is False:
                            del self.sheets[scale_name]
                            print("Scale " + scale_name + " is incomplete, skipping it.....")
                            return
                    else:
                        sh[item] = value
                else:
                    msg = "Error in __set_sheet limit exceeded in sheet: " + scale_name + ", df is [" + str(df.shape[0]) + "," + str(df.shape[1]) + "] and requested indices are: " + str(r) + "," + str(c)
                    raise Exception(msg)
        except Exception as e:
            a = 1

        self.sheets[scale_name] = SubjectsData(pd.DataFrame.from_dict([sh]))

    # def check_tot(self):
    #     """
    #     This function calculates the total score for each subject based on the specified flags.
    #
    #     Args:
    #         flags (list): A list of dictionaries, where each dictionary specifies the sheets and columns to be used for calculation.
    #
    #     Returns:
    #         None
    #     """
    #     flags   = [ {"main":["mri_code"]},
    #                 {"BISA":["oa"]},
    #                 {"BLOOD":["NK"]}, {"BLOOD":["T_HELP", "T_REG"]}, {"BLOOD":["MONO"]}, {"BLOOD":["B"]}, {"BLOOD":["PROT"]},
    #                 {"MATRICS":["MATRICS_date"]},
    #                 {"main":["mri_code"], "BISA":["oa"]},
    #                 {"main":["mri_code"], "BLOOD":["NK"]}, {"main":["mri_code"], "BLOOD":["T_HELP", "T_REG"]}, {"main":["mri_code"], "BLOOD":["MONO"]}, {"main":["mri_code"], "BLOOD":["B"]}, {"main":["mri_code"], "BLOOD":["PROT"]}
    #               ]

        # for flag in flags:
        #     sheet_name = flag.keys()[0]
        #     col_name = flag.values()[0]
        #     df = self.sheets[sheet_name]
        #     if df.size == 0:
        #         continue
        #     for col in col_name:
        #         label = list(col.keys())[0]
        #         value = list(col.values())[0]
        #
        #         row_id = list(df["LABELS"]).index(label)
        #         self.sheet_df(sh).iloc[row_id, value] = round(df.iloc[row_id, value], self.round_decimals)
