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
from data.SID import SID
from myutility.exceptions import DataFileException
from data.SubjectsData import SubjectsData
from data.Sheets import Sheets


class LimeAutoImporter:
    """
    This class provides methods to import data from an excel file generated by Lime Survey web site containing AUTO tests.
    Args:
        data (str): The path to the excel file to be parsed.
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
    input_sheets_names:dict     = {}
    output_sheets_names:dict    = {}

    subj                = ""
    session             = 1
    group               = ""

    schemas_json:str    = ""
    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    round_decimals      = 2

    # format: each key (e.g. main) is a sheet name.
    # each value is a list of dictionary specifying the rows to be modified (key) and the id of the column to modify
    # these values are defined in the json
    to_be_rounded:dict   = {}
    dates:dict           = {}

    sheets:Sheets        = None

    def __init__(self,  import_schema_file: str,
                        bayes_schema_file:str,
                        data:str=None,
                        password:str= ""):
        super().__init__()

        self.password           = password
        self.filepath           = ""
        self.bayes_schema_file  = bayes_schema_file

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

        with open(bayes_schema_file) as json_file:
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
                raise DataFileException("LimeAutoImporter.load", "given data param (" + data + ") is not a valid file")

            # Check if the file is an Excel file
            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise Exception("Error in BayesImportEteroDB.load: unknown data file format")

            # Set the filepath
            self.filepath = data

            # Check if a password is set
            if self.password != "":
                # Decrypt the Excel file
                data = self.__decrypt_excel(data, self.password)

            # Read the Excel file
            xls = pd.ExcelFile(data)
            df  = pd.read_excel(xls)

        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str")

        bayesdb = BayesDB(self.bayes_schema_file, calc_flags=False)

        for sh in self.output_sheets_names:
            bayesdb.set_sheet_sd(sh, SubjectsData())

        nsubjects = df.shape[0]

        for n in range(nsubjects):
            bayesdb = self.__set_subject(bayesdb, df.iloc[n,])

        # self.check_tot()
        return bayesdb # BayesDB(self.sheets, calc_flags=False)


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

        Parameters:
            sh (str): The name of the sheet.
            col (dict): A dictionary with the column name as the key and the number of decimal places as the value.

        Returns:
            None
        """
        for sh in self.to_be_rounded:
            df: pandas.DataFrame = self.sheets[sh]
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

        Parameters:
            sh (str): The name of the sheet.
            col (dict): A dictionary with the column name as the key and the id of the column to format as a date as the value.

        Returns:
            None
        """
        for sh in self.dates:
            df: pandas.DataFrame = self.sheets[sh]
            if df.size == 0:
                continue

            for col in self.dates[sh]:
                label = list(col.keys())[0]
                value = list(col.values())[0]

                # row_id = list(df["LABELS"]).index(label)
                # self.sheet_df(sh).iloc[row_id, value] = df.iloc[row_id, value].strftime(self.date_format)


                id_row  = [i for i, v in enumerate(list(df["LABELS"])) if label in v][0]
                val     = df.iloc[id_row, value]

                if isinstance(val, datetime.datetime):
                    # series = df["LABELS"]
                    # row_id = series[series.str.contains(label)].index   #list(df["LABELS"]).index(label)
                    self.sheets.sheet_df(sh).iloc[id_row, value] = df.iloc[id_row, value].strftime(self.date_format)
                else:
                    self.sheets.sheet_df(sh).iloc[id_row, value] = ""
                    # formatted_date = df.loc[df['LABELS'] == label]["VALUES"].iat[0].strftime(self.date_format)

    def __set_subject(self, bayesdb:BayesDB, subj:pandas.Series)-> BayesDB:
        """
        This function returns the main dataframe of the EteroDB file.

        Returns:
            pandas.DataFrame: The main dataframe of the EteroDB file.
        """
        # self.main_columns = {   "subj":"", "session":1, "group":"", "centre":"", "birth_date":"",
        #                         "recruitment_date":"", "age":0, "gender":"", "auto":0, "etero":0}

        self.main_default_cols  = { "mri":0, "oa":0, "nk":0, "t":0, "m":0, "b":0, "prot":0,
                                    "mat":0, "mri_oa":0, "mri_nk":0, "mri_t":0, "mri_m":0, "mri_b":0, "mri_prot":0}

        main                    = {}

        main["subj"]            = subj["Cognome"] + " " + subj["Nome"]
        main["session"]         = subj["session"]
        main["group"]           = subj["group"]
        main["auto"]            = 1

        subj_sd:SID       = SID(main["subj"], main["session"], -1)

        bayesdb.get_sheet_sd("main").add_row(subj_sd, main)

        try:
            for scale_name in self.input_sheets_names:
                sh = {"subj":main["subj"], "session":main["session"], "group":main["group"]}

                for item in self.import_schema[scale_name]:

                    c       = self.import_schema[scale_name][item]
                    value   = subj.iloc[c]

                    if isinstance(value, str):

                        if " (" in value:
                            nvalue = int(value.split(" ")[0])
                        elif value == "No" or value == "Falso":
                            nvalue = 0
                        elif value == "Sì" or value == "Vero":
                            nvalue = 1
                        else:
                            nvalue = value
                    else:
                        nvalue = value

                    sh[item] = nvalue

                bayesdb.get_sheet_sd(scale_name).add_row(subj_sd, sh)

            return bayesdb

        except Exception as e:
            a = 1






    # presently unused
    def __set_sheet(self, scale_name: str):
        """
        This function creates a new SubjectsData in each sheet

        Args:
            scale_name (str): The name of the scale.

        Returns:
            pandas.DataFrame: A pandas dataframe containing the data for the specified scale.

        Raises:
            ValueError: If the given scale name is not valid.
        """
        df = self.sheets.sheet_df(scale_name)
        sh = {"subj": self.subj, "session": self.session, "group": self.group}

        for item in self.import_schema[scale_name]:
            r = self.import_schema[scale_name][item][0]
            c = self.import_schema[scale_name][item][1]

            if r < df.shape[0] and c < df.shape[1]:
                sh[item] = df.iloc[r, c]
            else:
                msg = "Error in __set_sheet limit exceeded in sheet: " + scale_name + ", df is [" + str(df.shape[0]) + "," + str(df.shape[1]) + "] and requested indices are: " + str(r) + "," + str(c)
                raise Exception(msg)

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
