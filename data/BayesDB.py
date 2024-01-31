from typing import List

import pandas

from data.MSHDB import MSHDB
from data.SubjectSD import SubjectSD
from data.SubjectSDList import SubjectSDList
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues


class BayesDB(MSHDB):

    second_col_name = "session"
    third_col_name  = "group"

    schema_sheets_names = [ "main", "socio-ana", "clinica", "sangue", "ceres", "carico_farm",
                            "AASP", "ASI", "CCAS", "HAM A-D", "MATRICS", "MEQ", "MW S-D", "OA", "PANSS",
                            "PAS", "PSQI", "SANS", "SAPS", "SPQ", "STQ", "TATE", "TEMPS", "TLC", "YMRS", "ZTPI"]

    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    dates               = {"main":["birth_date", "recruitment_date"], "MATRICS":["matrics_date"]}
    to_be_rounded       = {"main":["age"]}

    def __init__(self, data=None, can_different_subjs=False, password:str="", calc_flags:bool=True, sortonload=True):
        super().__init__(data, self.schema_sheets_names, 0, True, "subj", can_different_subjs=can_different_subjs, password=password, sortonload=sortonload)
        if calc_flags:
            self.calc_flags()

    # ======================================================================================
    # region OVERRIDE
    def sort_values(self, df:pandas.DataFrame) -> pandas.DataFrame:
        return df.sort_values(by=[self.first_col_name, self.second_col_name], ignore_index=True)

    def is_valid(self, df:pandas.DataFrame) -> pandas.DataFrame:
        if df.columns[0] != self.first_col_name or df.columns[1] != self.second_col_name:
            if self.suppress_nosubj:
                df.columns.values[0] = self.first_col_name
                df.columns.values[1] = self.second_col_name
                print("Warning in BayesDB.load: either first or second column was not called subj or session, I renamed them....check if it's ok")
            else:
                raise Exception("Error in BayesDB.load: either first (" + df.columns.values[0] + ") or second (" + df.columns.values[1] + ") column was not called subj or session ")
        return df

    def add_default_columns(self, subjs:SubjectSDList, df:pandas.DataFrame):
        df[self.first_col_name]  = subjs.labels
        df[self.second_col_name] = subjs.sessions
        return df

    def remove_extra_columns(self, hdr:list) -> list:

        hdr.remove(self.first_col_name)
        hdr.remove(self.second_col_name)
        if "group" in hdr:
            hdr.remove("group")
        return hdr

    def add_default_rows(self, subjs:SubjectSDList=None):
        df                          = pandas.DataFrame()
        df[self.first_col_name]     = subjs.labels
        df[self.second_col_name]    = subjs.sessions
        df[self.third_col_name]     = self.get_groups(subjs)

        return df

    def add_default_row(self, subj:SubjectSD):
        return {self.first_col_name: subj.label, self.second_col_name:subj.session, "group":self.get_groups(SubjectSDList([subj]))[0]}

    def add_new_columns(self, shname: str, subjdf: pandas.DataFrame):

        if self.second_col_name not in subjdf.columns.values:
            raise Exception("Error in addColumns: given subjdf does not contain a session column")
        super().add_new_columns(shname, subjdf)

    def remove_subjects(self, subjects2remove:SubjectSDList, update=False) -> 'BayesDB':

        mshdb = super().remove_subjects(subjects2remove, update)
        return BayesDB(mshdb.sheets)

    def rename_subjects(self, assoc_dict, update=False) -> 'BayesDB':

        mshdb = super().rename_subjects(assoc_dict, update)
        return BayesDB(mshdb.sheets)

    def add_new_subjects(self, newdb:'MSHDB', can_diff_subjs=None, copy_previous_sess=None, update=False) -> 'BayesDB':

        mshdb   = super().add_new_subjects(newdb, can_diff_subjs, copy_previous_sess, update)
        bayesdb = BayesDB(mshdb.sheets)

        bayesdb = bayesdb.sort()
        bayesdb.calc_flags()
        if update:
            self = bayesdb

        return bayesdb

    #endregion

    def get_groups(self, subjs:SubjectSDList=None) -> List[str]:

        if subjs is None:
            subjs = self.subjects

        return self.main.get_subjects_column(subjs, "group")

    # region GET LISTS OF INTERESTS
    def mrilabels(self, subj_labels:List[str]=None) -> list:

        total = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("mri"   , "==", 1)])
        td    = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("group", "==", "TD"), FilterValues("mri", "==", 1)])
        bd    = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("group", "==", "BD"), FilterValues("mri", "==", 1)])
        sk    = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("group", "==", "SZ"), FilterValues("mri", "==", 1)])

        return [total, td, bd, sk]

    def bloodlabels(self, subj_labels:List[str]=None) -> list:

        total   = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("immfen_code"    , "exist" , 0)])
        th      = self.sheet_sd("sangue").select_subjlist(subj_labels, colconditions=[FilterValues("T_HELP", "==", 1)])
        tr      = self.sheet_sd("sangue").select_subjlist(subj_labels, colconditions=[FilterValues("T_REG", "==", 1)])
        nk      = self.sheet_sd("sangue").select_subjlist(subj_labels, colconditions=[FilterValues("NK", "==", 1)])
        mono    = self.sheet_sd("sangue").select_subjlist(subj_labels, colconditions=[FilterValues("MONO", "==", 1)])
        bi      = self.sheet_sd("sangue").select_subjlist(subj_labels, colconditions=[FilterValues("B", "==", 1)])

        return [total, th, tr, nk, mono, bi]

    def bisection_labels(self, subj_labels:List[str]=None):
        total   = self.sheets.main.select_subjlist(subj_labels, colconditions=[FilterValues("oa", "==", 1)])

        return [total]
    # endregion

    def calc_flags(self, outfile:str=None):

        cols2write = [      "mri",
                            "oa",
                            "nk", "t", "m", "b", "prot",
                            "mat",
                            "mri_oa",
                            "mri_nk","mri_t","mri_m","mri_b","mri_prot"
                  ]

        in_sheets_cells = [{"main":["mri_code"]},
                           {"OA":["oa"]},
                           {"sangue":["NK"]}, {"sangue":["T_HELP", "T_REG"]}, {"sangue":["MONO"]}, {"sangue":["B"]}, {"sangue":["PROT"]},
                           {"MATRICS":["matrics_date"]},
                           {"main":["mri_code"], "OA":["oa"]},
                           {"main":["mri_code"], "sangue":["NK"]}, {"main":["mri_code"], "sangue":["T_HELP", "T_REG"]}, {"main":["mri_code"], "sangue":["MONO"]}, {"main":["mri_code"], "sangue":["B"]}, {"main":["mri_code"], "sangue":["PROT"]}
                           ]

        for id,val in enumerate(cols2write):
            # e.g. "mri_oa"
            dest_col_lab = val

            if val == "mri_oa":
                a=1

            if val == "oa":
                a=1

            for subj in self.subjects:
                values = []

                for id_1, src_sheet_lab in enumerate(list(in_sheets_cells[id].keys())):   # e.g. ["main", "OA"]
                    # e.g. "main"
                    if src_sheet_lab in self.sheets:
                        src_sd:SubjectsData = self.sheet_sd(src_sheet_lab)
                        # SubjectSD(i,lab,sess)
                        for in_col in list(in_sheets_cells[id].values())[id_1]:      # e.g. ["mri_code"]
                            # e.g. "mri_code"
                            if in_col not in src_sd.header:
                                values.append(0)
                            elif src_sd.is_cell_empty(subj.id, in_col):
                                values.append(0)
                            else:
                                if src_sd.get_subject_col_value(subj, in_col) == 0:
                                    values.append(0)
                                else:
                                    values.append(1)

                if all(values) is True:
                    val = 1
                else:
                    val = 0
                self.main.set_subj_session_value(subj, dest_col_lab, val)

        if outfile is not None:
            self.save(outfile)

    def sort(self, by_items:List[str]=["subj", "session"], ascending=[True, True]):
        for sh in self.sheets:
            self.sheet_sd(sh).df = self.sheet_sd(sh).df.sort_values(by=by_items, ascending=ascending, ignore_index=True)

        return self