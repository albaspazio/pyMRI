from typing import List

import pandas

from data.MSHDB     import MSHDB
from data.Sheets    import Sheets
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from data.SubjectsData import SubjectsData

class BayesDB(MSHDB):

    schema_sheets_names = [ "main", "socio-ana", "clinica", "sangue", "ceres", "carico_farm",
                            "AASP", "ASI", "CCAS", "HAM A-D", "MATRICS", "MEQ", "MW S-D", "OA", "PANS",
                            "PAS", "PSQI", "SANS", "SAPS", "SPQ", "STQ", "TATE", "TEMPS", "TLC", "YMRS", "ZTPI"]

    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    dates               = {"main":["birth_date", "recruitment_date"], "MATRICS":["matrics_date"]}

    round_decimals      = 2
    to_be_rounded       = {"main":["age"]}



    def __init__(self, data=None, can_different_subjs=False, password:str=""):
        super().__init__(data, self.schema_sheets_names, 0, True, "subj", can_different_subjs=can_different_subjs, password=password)
        self.__format_dates()
        self.__round_columns()
        self.calc_stats()

    @property
    def main(self):
        return self.sheets.main

    def get_groups(self, subj_labels:List[str] = None) -> list:

        if subj_labels is None:
            subj_labels = self.subj_labels

        return self.main.get_subjects_column(subj_labels, "group")

    def add_default_rows(self, subj_labels:List[str]=None):
        df                      = pandas.DataFrame()
        df[self.first_col_name] = subj_labels
        df["group"]             = self.get_groups(subj_labels)

        return df

    def add_default_row(self, subj_label:str):
        return {self.first_col_name: subj_label, "group":self.get_groups([subj_label])[0]}

    def add_new_subjects(self, newdb, can_diff_subjs:None, update=False) -> 'BayesDB':

        mshdb = super().add_new_subjects(newdb, can_diff_subjs, update)
        return BayesDB(mshdb.sheets)

    def remove_subjects(self, subjects2remove:List[str], update=False) -> 'BayesDB':

        mshdb = super().remove_subjects(subjects2remove, update)
        return BayesDB(mshdb.sheets)

    #region GET LISTS OF INTERESTS
    def mrilabels(self, subj_labels:List[str]=None) -> list:

        total = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("mri"   , "==", 1)])
        td    = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("group", "==", "TD"), FilterValues("mri", "==", 1)])
        bd    = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("group", "==", "BD"), FilterValues("mri", "==", 1)])
        sk    = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("group", "==", "SZ"), FilterValues("mri", "==", 1)])

        return [total, td, bd, sk]

    def bloodlabels(self, subj_labels:List[str]=None) -> list:

        total   = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("immfen_code"    , "exist" , 0)])
        th      = self.sheets["sangue"].select_subjlist(subj_labels, colconditions=[FilterValues("T_HELP"   , "==", 1)])
        tr      = self.sheets["sangue"].select_subjlist(subj_labels, colconditions=[FilterValues("T_REG"    , "==", 1)])
        nk      = self.sheets["sangue"].select_subjlist(subj_labels, colconditions=[FilterValues("NK"       , "==", 1)])
        mono    = self.sheets["sangue"].select_subjlist(subj_labels, colconditions=[FilterValues("MONO"     , "==", 1)])
        bi      = self.sheets["sangue"].select_subjlist(subj_labels, colconditions=[FilterValues("B"        , "==", 1)])

        return [total, th, tr, nk, mono, bi]

    def bisection_labels(self, subj_labels:List[str]=None):
        total   = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("oa", "==", 1)])

        return [total]
    # endregion

    def __format_dates(self):
        for sh in self.dates:
            ds:SubjectsData = self.sheets[sh]
            if ds.num == 0:
                continue

            for col in self.dates[sh]:
                date_values = []
                for subj in ds.subj_labels:
                    value = ds.get_subject_col_value(subj, col)
                    try:
                        date_values.append(pandas.to_datetime(value))
                    except:
                        raise Exception("Error in BayesDB.__format_dates: value (" + value + ") in column " + col + " of sheet " + sh + " is not a valid date")

                try:
                    # change the datetime format
                    ds.df[col] = pandas.Series(date_values).dt.strftime(self.date_format)
                except:
                    raise Exception("Error in BayesDB.__format_dates: value (" + value + ") in column " + col + " of sheet " + sh + " cannot be formatted as desired")

    def __round_columns(self):
        for sh in self.to_be_rounded:
            ds:SubjectsData = self.sheets[sh]
            if ds.num == 0:
                continue
            for col in self.to_be_rounded[sh]:
                ds.df[col] = ds.df[col].round(self.round_decimals)


    def calc_stats(self):

        cols    = [ "mri",
                    "oa",
                    "nk", "t", "m", "b", "prot",
                    "mat",
                    "mri_oa",
                    "mri_nk","mri_t","mri_m","mri_b","mri_prot"
                  ]

        flags   = [ {"main":["mri_code"]},
                    {"OA":["oa"]},
                    {"sangue":["NK"]}, {"sangue":["T_HELP", "T_REG"]}, {"sangue":["MONO"]}, {"sangue":["B"]}, {"sangue":["PROT"]},
                    {"MATRICS":["matrics_date"]},
                    {"main":["mri_code"], "OA":["oa"]},
                    {"main":["mri_code"], "sangue":["NK"]}, {"main":["mri_code"], "sangue":["T_HELP", "T_REG"]}, {"main":["mri_code"], "sangue":["MONO"]}, {"main":["mri_code"], "sangue":["B"]}, {"main":["mri_code"], "sangue":["PROT"]}
                  ]


        for id,val in enumerate(cols):
            dest_col_lab        = val

            for id_1, src_sheet_lab in enumerate(list(flags[id].keys())):
                src_sd:SubjectsData = self.sheets[src_sheet_lab]

                for s in src_sd.subj_labels:
                    value = 1
                    for in_col in list(flags[id].values())[id_1]:

                        if in_col not in src_sd.header:
                            value = 0
                            break

                        # for in_col in in_cols:
                        if src_sd.is_cell_empty(s, in_col):
                            value = 0
                            break
                        else:
                            if src_sd.get_subject_col_value(s, in_col) == 0:
                                value = 0
                                break

                    self.main.set_subj_value(s, dest_col_lab, value)

