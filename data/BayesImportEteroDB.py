import datetime
import io
from typing import List

import msoffcrypto
import numpy
import pandas
import pandas as pd
import os

from data.BayesDB import BayesDB
from utility.exceptions import DataFileException
from data.SubjectsData import SubjectsData
from data.Sheets import Sheets

class BayesImportEteroDB:
    """
    This class provides methods to import data from EteroDB files into a BayesDB object.
    Args:
        data (str or dict): The path to the EteroDB file or a dictionary of the sheets.
        password (str, optional): The password for decrypting the EteroDB file. Defaults to "".

    Attributes:
        schema_sheets_names (list): A list of the names of the sheets in the EteroDB schema.
        subj (str): The subject ID.
        session (int): The session number.
        group (str): The group name.
        scales_data (dict): A dictionary of the scale names and their data.
        scales_data_ex (dict): A dictionary of the extended scale names and their data.
        date_format (str): The date format used in the EteroDB files.
        round_decimals (int): The number of decimal places to round numeric values to.
        dates (dict): A dictionary of the sheet names and the columns to format as dates.
        to_be_rounded (dict): A dictionary of the sheet names and the columns to round.
        main_name (str): The name of the main sheet.
        password (str): The password for decrypting the EteroDB file.
        filepath (str): The path to the EteroDB file.
        sheets (dict): A dictionary of the sheet names and their dataframes.
    """
    schema_sheets_names = ["main", "SA", "CLINIC", "PHARLOAD", "HAM", "PANSS", "SANS", "SAPS", "TATE", "TLC", "YMRS"]

    subj                = ""
    session             = 1
    group               = ""

    # scales_data = {
    #     "HAM":[{"HAM_A1":3},{"HAM_A2":4},{"HAM_A3":5},{"HAM_A4":6},{"HAM_A5":7},{"HAM_A6":8},{"HAM_A7":9},{"HAM_A8":10},{"HAM_A9":11},{"HAM_A10":12},{"HAM_A11":13},{"HAM_A12":14},{"HAM_A13":15},{"HAM_A14":16},{"HAM_ATOT":17},{"HAM_D1":20},{"HAM_D2":26},{"HAM_D3":32},{"HAM_D4":38},{"HAM_D5":42},{"HAM_D6":46},{"HAM_D7":50},{"HAM_D8":56},{"HAM_D9":62},{"HAM_D10":68},{"HAM_D11":74},{"HAM_D12":80},{"HAM_D13":84},{"HAM_D14":88},{"HAM_D15":92},{"HAM_D16":98},{"HAM_D17":108},{"HAM_D18A":112},{"HAM_D18B":116},{"HAM_D19":120},{"HAM_D20":125},{"HAM_D21":130},{"HAM_DTOT":134}],
    #     "PANSS":  [{"PANSS_p1":3},{"PANSS_p2":4},{"PANSS_p3":5},{"PANSS_p4":6},{"PANSS_p5":7},{"PANSS_p6":8},{"PANSS_p7":9},{"PANSS_n1":12},{"PANSS_n2":13},{"PANSS_n3":14},{"PANSS_n4":15},{"PANSS_n5":16},{"PANSS_n6":17},{"PANSS_n7":18},{"PANSS_g1":21},{"PANSS_g2":22},{"PANSS_g3":23},{"PANSS_g4":24},{"PANSS_g5":25},{"PANSS_g6":26},{"PANSS_g7":27},{"PANSS_g8":28},{"PANSS_g9":29},{"PANSS_g10":30},{"PANSS_g11":31},{"PANSS_g12":32},{"PANSS_g13":33},{"PANSS_g14":34},{"PANSS_g15":35},{"PANSS_g16":36},{"PANSS_TOT_P": 10},{"PANSS_TOT_N": 19},{"PANSS_TOT_G": 37},{"PANSS_TOT": 38}],
    #     "SANS":   [{"SANS_1": 3}, {"SANS_2": 4}, {"SANS_3": 5}, {"SANS_4": 6}, {"SANS_5": 7}, {"SANS_6": 8}, {"SANS_7": 9}, {"SANS_8": 10}, {"SANS_9": 12}, {"SANS_10": 13}, {"SANS_11": 14}, {"SANS_12": 15}, {"SANS_13": 16}, {"SANS_14": 18}, {"SANS_15": 19}, {"SANS_16": 20}, {"SANS_17": 21}, {"SANS_18": 23}, {"SANS_19": 24}, {"SANS_20": 25}, {"SANS_21": 26}, {"SANS_22": 27}, {"SANS_23": 29}, {"SANS_24": 30}, {"SANS_25": 31}, {"SANS_TOT": 32}],
    #     "SAPS":   [{"SAPS_1":3}, {"SAPS_2":4}, {"SAPS_3":5}, {"SAPS_4":6}, {"SAPS_5":7}, {"SAPS_6":8}, {"SAPS_7":9}, {"SAPS_8":11}, {"SAPS_9":12}, {"SAPS_10":13},{"SAPS_11":14}, {"SAPS_12":15}, {"SAPS_13":16}, {"SAPS_14":17}, {"SAPS_15":18}, {"SAPS_16":19}, {"SAPS_17":20}, {"SAPS_18":21}, {"SAPS_19":22}, {"SAPS_20":23}, {"SAPS_21":25}, {"SAPS_22":26}, {"SAPS_23":27}, {"SAPS_24":28}, {"SAPS_25":29}, {"SAPS_26":31}, {"SAPS_27":32}, {"SAPS_28":33}, {"SAPS_29":34}, {"SAPS_30":35}, {"SAPS_31":36}, {"SAPS_32":37}, {"SAPS_33":38}, {"SAPS_34":39},{"SAPS_TOT":40}],
    #     "TLC":    [{"TLC_1": 2}, {"TLC_2": 8}, {"TLC_3": 14}, {"TLC_4": 20}, {"TLC_5": 26}, {"TLC_6": 32},{"TLC_7": 38}, {"TLC_8": 44}, {"TLC_9": 50}, {"TLC_10": 56}, {"TLC_11": 61}, {"TLC_12": 66},{"TLC_13": 71}, {"TLC_14": 76}, {"TLC_15": 81}, {"TLC_16": 86}, {"TLC_17": 91}, {"TLC_18": 96},{"TLC_19": 101}, {"TLC_20": 106}, {"TLC_TOT":112}],
    #     "YMRS":   [{"YMRS_1": 2}, {"YMRS_2": 8}, {"YMRS_3": 14}, {"YMRS_4": 20}, {"YMRS_5": 26}, {"YMRS_6": 32},{"YMRS_7": 38}, {"YMRS_8": 44}, {"YMRS_9": 50}, {"YMRS_10": 56}, {"YMRS_11": 62}, {"YMRS_TOT":68}]
    # }
    #
    # scales_data_ex = {
    #     "TATE":   [{"1a": 2}, {"1b": 3}, {"1c": 4}, {"2a": 5}, {"2b": 6}, {"2c": 7}, {"3a": 8}, {"3b": 9}, {"3c": 10},{"3d": 11}, {"3e": 12}, {"3f": 13}, {"4a": 14}, {"4b": 15}, {"4c": 16}, {"5a": 17}, {"5b": 18},{"5c": 19}, {"5d": 20}, {"5e": 21}, {"5f": 22}, {"6a": 23}, {"6b": 24}, {"6c": 25}, {"6d": 26},{"6e": 27}, {"6f": 28}, {"6g": 29}, {"6h": 30}, {"6i": 31}, {"6j": 32}, {"6k": 33}, {"6l": 34},{"6m": 35}, {"6n": 36}, {"7a": 37}, {"7b": 38}, {"7c": 39}, {"7d": 40}, {"7e": 41}, {"7f": 42},{"7g": 43}]
    # }

    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    round_decimals      = 2

    # format: each key (e.g. main) is a sheet name.
    # each value is a list of dictionary specifying the rows to be modified (key) and the id of the column to modify

    dates               = {"main":[{"DATA DI NASCITA SOGGETTO":1},{"DATA DI NASCITA MADRE":1},{"DATA DI NASCITA PADRE":1}, {"DATA RECLUTAMENTO":1}]}
    to_be_rounded       = {"main":[{"ETA":1}]}

    def __init__(self, data=None, main_id=0, password:str=""):
        super().__init__()

        self.main_id            = main_id
        self.password           = password

        self.main_name          = self.schema_sheets_names[self.main_id]
        self.filepath           = ""
        self.sheets = Sheets(self.schema_sheets_names, self.main_id)

        if data is not None:
            self.load(data)

        self.__format_dates()
        self.__round_columns()

        # adjust each sheet
        first_sheets            = self.set_main()

        self.sheets["main"]     = SubjectsData(first_sheets[0])
        self.sheets["SH"]       = SubjectsData(first_sheets[1])
        self.sheets["CLINIC"]   = SubjectsData(first_sheets[2])
        self.sheets["PHARLOAD"] = SubjectsData(self.set_pharload())
        self.sheets["HAM"]      = SubjectsData(self.set_ham())
        self.sheets["PANSS"]    = SubjectsData(self.set_panss())
        self.sheets["SANS"]     = SubjectsData(self.set_sans())
        self.sheets["SAPS"]     = SubjectsData(self.set_saps())
        self.sheets["TATE"]     = SubjectsData(self.set_tate())
        self.sheets["TLC"]      = SubjectsData(self.set_tlc())
        self.sheets["YMRS"]     = SubjectsData(self.set_ymrs())

        # self.calc_tot()

    def load(self, data=None, validcols:list=None, cols2num:list=None, delimiter='\t') -> dict:
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
                raise DataFileException("BayesImportEteroDB.load", "given data param (" + data + ") is not a valid file")

            # Check if the file is an Excel file
            if not data.endswith(".xls") and not data.endswith(".xlsx"):
                raise Exception("Error in BayesImportEteroDB.load: unknown data file format")

            # Set the filepath
            self.filepath = data

            # Check if a password is set
            if self.password != "":
                # Decrypt the Excel file
                data = self.decrypt_excel(data, self.password)

            # Read the Excel file
            xls = pd.ExcelFile(data)

            # Loop through the sheets
            for sheet_name in xls.sheet_names:

                if sheet_name in self.schema_sheets_names:
                    self.sheets[sheet_name] = pd.read_excel(xls, sheet_name)

        elif isinstance(data, dict):
            # Check if the given data is a dictionary of sheets
            # TODO: Check if the dictionary contains valid sheets
            self.sheets = data

        else:
            raise Exception("Error in MXLSDB.load: unknown data format, not a str, not a dict")

        return self.sheets

    def sheet_df(self, name: str) -> pandas.DataFrame:
        """
        Returns the pandas dataframe for the given sheet name.

        Args:
            name (str): The name of the sheet.

        Raises:
            Exception: If the sheet name is not valid.

        Returns:
            pandas.DataFrame: The dataframe for the given sheet name.
        """
        if name not in self.schema_sheets_names:
            raise Exception("Error in MSHDB.sheet: ")
        return self.sheets[name]

    def decrypt_excel(self, fpath: str, pwd: str) -> io.BytesIO:
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
                self.sheet_df(sh).iloc[row_id, value] = round(df.iloc[row_id, value], self.round_decimals)

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


                id_row  = [index for index, value in enumerate(list(df["LABELS"])) if label in value][0]
                val     = df.iloc[id_row, value]

                if isinstance(val, datetime.datetime):
                    # series = df["LABELS"]
                    # row_id = series[series.str.contains(label)].index   #list(df["LABELS"]).index(label)
                    self.sheet_df(sh).iloc[id_row, value] = df.iloc[id_row, value].strftime(self.date_format)
                else:
                    self.sheet_df(sh).iloc[id_row, value] = ""
                    # formatted_date = df.loc[df['LABELS'] == label]["VALUES"].iat[0].strftime(self.date_format)

    def add_2_bayes(self, bayes_db: str |BayesDB) -> BayesDB:
        """
        This function adds the data from the current instance of the class to a BayesDB object.

        Args:
            bayes_db (Union[str, BayesDB]): The path to the BayesDB file or an instance of the BayesDB class.

        Returns:
            BayesDB: The updated instance of the BayesDB class.

        Raises:
            ValueError: If the given bayes_db is neither a string nor an instance of the BayesDB class.
        """
        if isinstance(bayes_db, str):
            pass
        elif isinstance(bayes_db, BayesDB):
            pass
        else:
            raise ValueError(f"Invalid bayes_db type: {type(bayes_db)}")

    def export_bayes(self, outfile=None, bayes_main_id: int = 0) -> BayesDB:
        """
        Exports the data from the current instance of the class to a BayesDB object.

        Args:
            outfile (str, optional): The path to the output BayesDB file. If not specified, the data will be returned as an instance of the BayesDB class.
            bayes_main_id (int, optional): The ID of the main sheet in the BayesDB file. Defaults to 0.

        Returns:
            BayesDB: The BayesDB object containing the data from the current instance of the class.

        Raises:
            ValueError: If the given bayes_main_id is not an integer.
        """
        if not isinstance(bayes_main_id, int):
            raise ValueError(f"Invalid bayes_main_id type: {type(bayes_main_id)}")
        #
        # try:
        #     sheets["main"] = SubjectsData(self.get_main())
        #     for s in self.scales_data:
        #         sheets[s] = SubjectsData(self.get_scale(s))
        #
        #     # for s in self.scales_data_ex:
        #     #     sheets[s] = SubjectsData(self.get_scale(s))
        # except Exception as e:
        #     raise Exception(f"Error in BayesImportEteroDB.export_bayes: {e}")
        return BayesDB(self.sheets)

    def get_main(self) -> pandas.DataFrame:
        pass
    def set_main(self) -> pandas.DataFrame:
        """
        This function returns the main dataframe of the EteroDB file.

        Returns:
            pandas.DataFrame: The main dataframe of the EteroDB file.
        """
        self.main_columns = [   "subj", "session", "group", "centre", "mri_code", "immfen_code", "birth_date",
                                "recruitment_date", "age", "gender", "auto", "etero"]

        self.default_cols = [   "mri", "oa", "nk", "t", "m", "b", "prot",
                                "mat", "mri_oa", "mri_nk", "mri_t", "mri_m", "mri_b", "mri_prot"]

        df = self.sheets["main"]

        main    = {}
        SA      = {}
        CLINIC  = {}

        main["subj"]            = df.iloc[2,1] + " " + df.iloc[3,1]
        main["session"]         = df.iloc[4,1]
        main["group"]           = df.iloc[13,1]

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
        CLINIC["hospitalization"] = df.iloc[11,1]
        CLINIC["origin"]          = df.iloc[12,1]
        CLINIC["primary_diagnosis"] = df.iloc[14,1]
        CLINIC["bd_phase"]            = df.iloc[15,1]
        CLINIC["psicomotricity"]      = df.iloc[16,1]
        CLINIC["ideation"]            = df.iloc[17,1]
        CLINIC["humour"]              = df.iloc[18,1]
        CLINIC["psicothic_sympt"]     = df.iloc[19,1]
        CLINIC["psicothic_features"]  = df.iloc[20,1]
        main["dominant_hand"]       = df.iloc[21,1]
        main["height"]              = df.iloc[22,1]
        main["weight"]              = df.iloc[23,1]
        main["BMI"]                 = df.iloc[24,1]
        main["birth_type"]          = df.iloc[25,1]
        main["birth_place"]         = df.iloc[26,1]
        main["mother_surname"]      = df.iloc[27,1]
        main["mother_birthdate"]    = df.iloc[28,1]
        main["father_surname"]      = df.iloc[29,1]
        main["father_birthdate"]    = df.iloc[30,1]
        main["gestation_weeks"]     = df.iloc[31,1]
        main["nascitaXXXXXXXX"]     = df.iloc[32,1]
        main["birth_weight"]        = df.iloc[33,1]
        main["weight_category"]     = df.iloc[34,1]
        main["birth_issues"]        = df.iloc[35,1]
        main["perinatal_infections"] = df.iloc[36,1]
        main["alimentation_birth"]  = df.iloc[37,1]
        CLINIC["psych_motor_develop"] = df.iloc[38,1]
        main["brothers_sisters"]    = df.iloc[39,1]
        main["marital_status"]      = df.iloc[40,1]
        main["family_type"]         = df.iloc[41,1]
        main["education"]           = df.iloc[42,1]
        main["years_education"]     = df.iloc[43,1]
        main["supp_teacher"]        = df.iloc[44,1]
        main["job"]                 = df.iloc[45,1]
        main["socioecon_cond"]      = df.iloc[46,1]
        main["residency"]           = df.iloc[47,1]
        main["period"]              = df.iloc[48,1]
        main["period_onset_age"]    = df.iloc[49,1]
        main["finalized_pregnancies"] = df.iloc[50,1]
        main["tot_pregnancies"]     = df.iloc[51,1]
        main["physical_activity"]   = df.iloc[52,1]
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

        for k in self.default_cols:
            main[k] = 0

        main["etero"]           = 1

        return [pd.DataFrame.from_dict([main]),
                pd.DataFrame.from_dict([SA]),
                pd.DataFrame.from_dict([CLINIC])]

    def set_pharload(self) -> pandas.DataFrame:
        df = self.sheets["PHARLOAD"]

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["Dose_Antipsicotico"]    = df.iloc[1,2]
        sh["Carico_Antipsicotico"]  = df.iloc[2,10]
        sh["Dose_Stabilizzatore"]   = df.iloc[1,4]
        sh["Carico_Stabilizzatore"] = df.iloc[3,10]
        sh["Dose_Benzodiazepine"]   = df.iloc[1,6]
        sh["Carico_Benzodiazepine"] = df.iloc[4,10]
        sh["Dose_Antidepressivo"]   = df.iloc[1,8]
        sh["Carico_Antidepressivo"] = df.iloc[5,10]
        sh["Carico_Totale"]         = df.iloc[6,10]

        return pd.DataFrame.from_dict([sh])

    def set_ham(self) -> pandas.DataFrame|None:
        df = self.sheets["HAM"]

        if df.iloc[1, 2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["HAM_A1"]    = df.iloc[1,2]
        sh["HAM_A2"]    = df.iloc[2,2]
        sh["HAM_A3"]    = df.iloc[3,2]
        sh["HAM_A4"]    = df.iloc[4,2]
        sh["HAM_A5"]    = df.iloc[5,2]
        sh["HAM_A6"]    = df.iloc[6,2]
        sh["HAM_A7"]    = df.iloc[7,2]
        sh["HAM_A8"]    = df.iloc[8,2]
        sh["HAM_A9"]    = df.iloc[9,2]
        sh["HAM_A10"]   = df.iloc[10,2]
        sh["HAM_A11"]   = df.iloc[11,2]
        sh["HAM_A12"]   = df.iloc[12,2]
        sh["HAM_A13"]   = df.iloc[13,2]
        sh["HAM_A14"]   = df.iloc[14,2]
        sh["HAM_ATOT"]  = df.iloc[15,2]

        sh["HAM_D1"]    = df.iloc[18,2]
        sh["HAM_D2"]    = df.iloc[24,2]
        sh["HAM_D3"]    = df.iloc[30,2]
        sh["HAM_D4"]    = df.iloc[36,2]
        sh["HAM_D5"]    = df.iloc[40,2]
        sh["HAM_D6"]    = df.iloc[44,2]
        sh["HAM_D7"]    = df.iloc[48,2]
        sh["HAM_D8"]    = df.iloc[54,2]
        sh["HAM_D9"]    = df.iloc[60,2]
        sh["HAM_D10"]   = df.iloc[66,2]
        sh["HAM_D11"]   = df.iloc[72,2]
        sh["HAM_D12"]   = df.iloc[78,2]
        sh["HAM_D13"]   = df.iloc[82,2]
        sh["HAM_D14"]   = df.iloc[86,2]
        sh["HAM_D15"]  = df.iloc[90,2]
        sh["HAM_D16"]  = df.iloc[96,2]
        # sh["HAM_D16B"]  = df.iloc[101,2]
        sh["HAM_D17"]  = df.iloc[106,2]
        sh["HAM_D18A"]  = df.iloc[110,2]
        sh["HAM_D18B"]  = df.iloc[114,2]
        sh["HAM_D19"]  = df.iloc[118,2]
        sh["HAM_D20"]  = df.iloc[123,2]
        sh["HAM_D21"]  = df.iloc[128,2]
        sh["HAM_DTOT"]  = df.iloc[132,2]

        return pd.DataFrame.from_dict([sh])

    def set_panss(self) -> pandas.DataFrame|None:
        df = self.sheets["PANSS"]

        if df.iloc[1,2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["PANSS_p1"]    = df.iloc[1,2]
        sh["PANSS_p2"]    = df.iloc[2,2]
        sh["PANSS_p3"]    = df.iloc[3,2]
        sh["PANSS_p4"]    = df.iloc[4,2]
        sh["PANSS_p5"]    = df.iloc[5,2]
        sh["PANSS_p6"]    = df.iloc[6,2]
        sh["PANSS_p7"]    = df.iloc[7,2]
        sh["PANSS_TOT_P"] = df.iloc[8,2]

        sh["PANSS_n1"]    = df.iloc[10,2]
        sh["PANSS_n2"]    = df.iloc[11,2]
        sh["PANSS_n3"]    = df.iloc[12,2]
        sh["PANSS_n4"]    = df.iloc[13,2]
        sh["PANSS_n5"]    = df.iloc[14,2]
        sh["PANSS_n6"]    = df.iloc[15,2]
        sh["PANSS_n7"]    = df.iloc[16,2]
        sh["PANSS_TOT_N"] = df.iloc[17,2]

        sh["PANSS_g1"]    = df.iloc[19,2]
        sh["PANSS_g2"]    = df.iloc[20,2]
        sh["PANSS_g3"]    = df.iloc[21,2]
        sh["PANSS_g4"]    = df.iloc[22,2]
        sh["PANSS_g5"]    = df.iloc[23,2]
        sh["PANSS_g6"]    = df.iloc[24,2]
        sh["PANSS_g7"]    = df.iloc[25,2]
        sh["PANSS_g8"]    = df.iloc[26,2]
        sh["PANSS_g9"]    = df.iloc[27,2]
        sh["PANSS_g10"]   = df.iloc[28,2]
        sh["PANSS_g11"]   = df.iloc[29,2]
        sh["PANSS_g12"]   = df.iloc[30,2]
        sh["PANSS_g13"]   = df.iloc[31,2]
        sh["PANSS_g14"]   = df.iloc[32,2]
        sh["PANSS_g15"]   = df.iloc[33,2]
        sh["PANSS_g16"]   = df.iloc[34,2]
        sh["PANSS_TOT_G"] = df.iloc[35,2]

        sh["PANSS_TOT"] = df.iloc[36,2]

        return pd.DataFrame.from_dict([sh])

    def set_sans(self) -> pandas.DataFrame|None:
        df              = self.sheets["SANS"]

        if df.iloc[1,2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["SANS_1"]    = df.iloc[1,2]
        sh["SANS_2"]    = df.iloc[2,2]
        sh["SANS_3"]    = df.iloc[3,2]
        sh["SANS_4"]    = df.iloc[4,2]
        sh["SANS_5"]    = df.iloc[5,2]
        sh["SANS_6"]    = df.iloc[6,2]
        sh["SANS_7"]    = df.iloc[7,2]
        sh["SANS_8"]    = df.iloc[8,2]
        sh["SANS_9"]    = df.iloc[10,2]
        sh["SANS_10"]   = df.iloc[11,2]
        sh["SANS_11"]   = df.iloc[12,2]
        sh["SANS_12"]   = df.iloc[13,2]
        sh["SANS_13"]   = df.iloc[14,2]
        sh["SANS_14"]   = df.iloc[16,2]
        sh["SANS_15"]   = df.iloc[17,2]
        sh["SANS_16"]   = df.iloc[18,2]
        sh["SANS_17"]   = df.iloc[19,2]
        sh["SANS_18"]   = df.iloc[21,2]
        sh["SANS_19"]   = df.iloc[22,2]
        sh["SANS_20"]   = df.iloc[23,2]
        sh["SANS_21"]   = df.iloc[24,2]
        sh["SANS_22"]   = df.iloc[25,2]
        sh["SANS_23"]   = df.iloc[27,2]
        sh["SANS_24"]   = df.iloc[28,2]
        sh["SANS_25"]   = df.iloc[29,2]
        sh["SANS_TOT"]  = df.iloc[30,2]

        return pd.DataFrame.from_dict([sh])

    def set_saps(self) -> pandas.DataFrame|None:
        df = self.sheets["SAPS"]

        if df.iloc[1,2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["SAPS_1"]    = df.iloc[1,2]
        sh["SAPS_2"]    = df.iloc[2,2]
        sh["SAPS_3"]    = df.iloc[3,2]
        sh["SAPS_4"]    = df.iloc[4,2]
        sh["SAPS_5"]    = df.iloc[5,2]
        sh["SAPS_6"]    = df.iloc[6,2]
        sh["SAPS_7"]    = df.iloc[7,2]

        sh["SAPS_8"]    = df.iloc[9,2]
        sh["SAPS_9"]    = df.iloc[10,2]
        sh["SAPS_10"]   = df.iloc[11,2]
        sh["SAPS_11"]   = df.iloc[12,2]
        sh["SAPS_12"]   = df.iloc[13,2]
        sh["SAPS_13"]   = df.iloc[14,2]
        sh["SAPS_14"]   = df.iloc[15,2]
        sh["SAPS_15"]   = df.iloc[16,2]
        sh["SAPS_16"]   = df.iloc[17,2]
        sh["SAPS_17"]   = df.iloc[18,2]
        sh["SAPS_18"]   = df.iloc[19,2]
        sh["SAPS_19"]   = df.iloc[20,2]
        sh["SAPS_20"]   = df.iloc[21,2]

        sh["SAPS_21"]   = df.iloc[23,2]
        sh["SAPS_22"]   = df.iloc[24,2]
        sh["SAPS_23"]   = df.iloc[25,2]
        sh["SAPS_24"]   = df.iloc[26,2]
        sh["SAPS_25"]   = df.iloc[27,2]

        sh["SAPS_26"]   = df.iloc[29,2]
        sh["SAPS_27"]   = df.iloc[30,2]
        sh["SAPS_28"]   = df.iloc[31,2]
        sh["SAPS_29"]   = df.iloc[32,2]
        sh["SAPS_30"]   = df.iloc[33,2]
        sh["SAPS_31"]   = df.iloc[34,2]
        sh["SAPS_32"]   = df.iloc[35,2]
        sh["SAPS_33"]   = df.iloc[36,2]
        sh["SAPS_34"]   = df.iloc[37,2]

        sh["SAPS_TOT"]   = df.iloc[38,2]

        return pd.DataFrame.from_dict([sh])

    def set_tlc(self) -> pandas.DataFrame|None:
        df = self.sheets["TLC"]

        if df.iloc[1,2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["TLC_1"]    = df.iloc[1,2]
        sh["TLC_2"]    = df.iloc[6,2]
        sh["TLC_3"]    = df.iloc[12,2]
        sh["TLC_4"]    = df.iloc[18,2]
        sh["TLC_5"]    = df.iloc[24,2]
        sh["TLC_6"]    = df.iloc[30,2]
        sh["TLC_7"]    = df.iloc[36,2]
        sh["TLC_8"]    = df.iloc[42,2]
        sh["TLC_9"]    = df.iloc[48,2]
        sh["TLC_10"]   = df.iloc[54,2]
        sh["TLC_11"]   = df.iloc[59,2]
        sh["TLC_12"]   = df.iloc[64,2]
        sh["TLC_13"]   = df.iloc[69,2]
        sh["TLC_14"]   = df.iloc[74,2]
        sh["TLC_15"]   = df.iloc[79,2]
        sh["TLC_16"]   = df.iloc[84,2]
        sh["TLC_17"]   = df.iloc[89,2]
        sh["TLC_18"]   = df.iloc[94,2]
        sh["TLC_19"]   = df.iloc[99,2]
        sh["TLC_20"]   = df.iloc[104,2]

        sh["TLC_TOT"]  = df.iloc[110,2]

        return pd.DataFrame.from_dict([sh])

    def set_tate(self) -> pandas.DataFrame|None:
        df = self.sheets["TATE"]

        if df.iloc[1,2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["TATE_A1"]    = df.iloc[1,2]

        return pd.DataFrame.from_dict([sh])

    def set_ymrs(self) -> pandas.DataFrame|None:
        df = self.sheets["YMRS"]

        if df.iloc[1,2] == "INSERISCI":
            self.sheet_df("main")
            return None

        sh              = {}
        sh["subj"]      = self.subj
        sh["session"]   = self.session
        sh["group"]     = self.group

        sh["YMRS_1"]    = df.iloc[0,2]
        sh["YMRS_2"]    = df.iloc[6,2]
        sh["YMRS_3"]    = df.iloc[12,2]
        sh["YMRS_4"]    = df.iloc[18,2]
        sh["YMRS_5"]    = df.iloc[24,2]
        sh["YMRS_6"]    = df.iloc[30,2]
        sh["YMRS_7"]    = df.iloc[36,2]
        sh["YMRS_8"]    = df.iloc[42,2]
        sh["YMRS_9"]    = df.iloc[48,2]
        sh["YMRS_10"]   = df.iloc[54,2]
        sh["YMRS_11"]   = df.iloc[60,2]
        sh["YMRS_TOT"]  = df.iloc[66,2]

        return pd.DataFrame.from_dict([sh])

    # presently unused
    def get_scale(self, scale_name: str) -> pandas.DataFrame:
        """
        This function returns a pandas dataframe containing the data for the specified scale.

        Args:
            scale_name (str): The name of the scale.

        Returns:
            pandas.DataFrame: A pandas dataframe containing the data for the specified scale.

        Raises:
            ValueError: If the given scale name is not valid.
        """
        if scale_name not in self.scales_data:
            raise ValueError(f"Invalid scale name: {scale_name}")

        scale = {"subj": self.subj, "session": self.session, "group": self.group}
        scale_data = self.scales_data[scale_name]
        df = self.sheet_df(scale_name)
        values_id = df.columns.get_loc("VALUES")

        for item in scale_data:
            row_id = list(item.values())[0] - 2  # ID are set including the header
            value = df.iloc[row_id, values_id]
            scale[list(item.keys())[0]] = value

        return pd.DataFrame.from_dict([scale])

    # def calc_tot(self):
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
