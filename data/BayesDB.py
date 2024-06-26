from __future__ import annotations

from typing import List

import pandas

from data.GDriveSheet import GDriveSheet
from data.MSHDB import MSHDB
from data.Sheets import Sheets
from data.SubjectSD import SubjectSD
from data.SubjectSDList import SubjectSDList
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues

class BayesDB(MSHDB):
    """
    The BayesDB class provides an interface to a collection of MSHDB sheets that contain data on multiple subjects.
    The class provides methods for loading, saving, sorting, and manipulating the data in the sheets. It also provides methods for calculating summary statistics and other derived variables.
    The class is designed to be flexible and extensible, allowing users to define their own custom sheets and columns.

    Parameters
    ----------
    data : str, Sheets, or GDriveSheet
        The data source for the database. This can be a path to an Excel file, a Google Sheet, or a Python dictionary containing the data.
    can_different_subjs : bool, optional
        If True, subjects can have different sessions in different sheets.
    password : str, optional
        The password for the encrypted Excel file.
    calc_flags : bool, optional
        If True, the class will calculate various flags based on the data in the main sheet.
    sortonload : bool, optional
        If True, the data will be sorted when the class is loaded.

    Attributes
    ----------
    sheets : list of Sheet
        The list of Sheet objects that make up the database.
    subjects : SubjectSDList
        The list of SubjectSD objects that are in the database.
    first_col_name : str
        The name of the first column (usually "subj").
    second_col_name : str
        The name of the second column (usually "session").
    third_col_name : str
        The name of the third column (usually "group").
    schema_sheets_names : list
        The list of sheet names that define the schema of the database.
    date_format : str
        The format string for dates.
    dates : dict
        A dictionary that maps sheet names to a list of date columns.
    to_be_rounded : dict
        A dictionary that maps sheet names to a list of columns that should be rounded to integers.

    Methods
    -------
    load(data=None, can_different_subjs=False, password="", calc_flags=True, sortonload=True)
        Load the data from the given file or DataFrame.
    save(outfile=None)
        Save the data to the given file.
    sort(by_items=["subj", "session"], ascending=[True, True])
        Sort the data by the given items and in the given order.
    is_valid(df)
        Check if the given DataFrame is valid.
    add_default_columns(subjs, df)
        Add the default columns (subj, session, group) to the given DataFrame.
    remove_extra_columns(hdr)
        Remove the extra columns from the given list.
    add_default_rows(subjs=None)
        Add the default rows (subj, session, group) to the given DataFrame.
    add_default_row(subj)
        Add the default row for the given subject.
    add_new_columns(shname, subjdf)
        Add the new columns in the given sheet.
    remove_subjects(subjects2remove, update=False)
        Remove the given subjects from the database.
    rename_subjects(assoc_dict, update=False)
        Rename the subjects in the database.
    add_new_subjects(newdb, can_diff_subjs=None, copy_previous_sess=None, update=False)
        Add the subjects from the given database.
    get_groups(subjs=None)
        Get the groups for the given subjects.
    mrilabels(subj_labels=None)
        Get the MRI labels for the given subjects.
    bloodlabels(subj_labels=None)
        Get the blood labels for the given subjects.
    bisection_labels(subj_labels=None)
        Get the bisection labels for the given subjects.
    calc_flags(outfile=None)
        Calculate the flags for the database.
    """

    second_col_name = "session"
    third_col_name  = "group"

    schema_sheets_names = [ "main", "socio-ana", "clinica", "sangue", "ceres", "carico_farm",
                            "AASP", "ASI", "CCAS", "HAM A-D", "MATRICS", "MEQ", "MW S-D", "OA", "PANSS",
                            "PAS", "PSQI", "SANS", "SAPS", "SPQ", "STQ", "TATE", "TEMPS", "TLC", "YMRS", "ZTPI"]

    date_format         = "%d-%b-%Y" #"%b/%d/%Y"    # DD/MM/YYYY
    dates               = {"main":["birth_date", "recruitment_date"], "MATRICS":["matrics_date"]}
    to_be_rounded       = {"main":["age"]}

    def __init__(self, data:str|Sheets|GDriveSheet=None, can_different_subjs:bool=False, password:str="", calc_flags:bool=True, sortonload:bool=True):
        """
        Initialize the class.
        """
        super().__init__(data, self.schema_sheets_names, 0, True, "subj", can_different_subjs=can_different_subjs, password=password, sortonload=sortonload)
        if calc_flags:
            self.calc_flags()

    # ======================================================================================
    # region OVERRIDE
    def sort_values(self, df:pandas.DataFrame) -> pandas.DataFrame:
        """
        Sort the given DataFrame by the first and second columns.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to be sorted.

        Returns
        -------
        pandas.DataFrame
            The sorted DataFrame.
        """
        return df.sort_values(by=[self.first_col_name, self.second_col_name], ignore_index=True)

    def is_valid(self, df:pandas.DataFrame) -> pandas.DataFrame:
        """
        Check if the given DataFrame has the correct columns.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame to be checked.

        Returns
        -------
        pandas.DataFrame
            The given DataFrame if it is valid, or an error message if it is not valid.
        """
        if df.columns[0] != self.first_col_name or df.columns[1] != self.second_col_name:
            if self.suppress_nosubj:
                df.columns.values[0] = self.first_col_name
                df.columns.values[1] = self.second_col_name
                print("Warning in BayesDB.load: either first or second column was not called subj or session, I renamed them....check if it's ok")
            else:
                raise Exception("Error in BayesDB.load: either first (" + df.columns.values[0] + ") or second (" + df.columns.values[1] + ") column was not called subj or session ")
        return df

    def add_default_columns(self, subjs:SubjectSDList, df:pandas.DataFrame):
        """
        Add the default columns (subj, session, group) to the given DataFrame.

        Parameters
        ----------
        subjs : SubjectSDList
            The list of SubjectSD objects.
        df : pandas.DataFrame
            The DataFrame to be modified.

        Returns
        -------
        pandas.DataFrame
            The given DataFrame with the default columns added.
        """
        df[self.first_col_name]  = subjs.labels
        df[self.second_col_name] = subjs.sessions
        return df

    def remove_extra_columns(self, hdr:list) -> list:
        """
        Remove the extra columns from the given list.

        Parameters
        ----------
        hdr : list
            The list of column headers.

        Returns
        -------
        list
            The list of column headers without the extra columns.
        """
        hdr.remove(self.first_col_name)
        hdr.remove(self.second_col_name)
        if "group" in hdr:
            hdr.remove("group")
        return hdr

    def add_default_rows(self, subjs:SubjectSDList=None):
        """
        Add the default rows (subj, session, group) to the given DataFrame.

        Parameters
        ----------
        subjs : SubjectSDList, optional
            The list of SubjectSD objects, by default None.

        Returns
        -------
        pandas.DataFrame
            The DataFrame with the default rows added.
        """
        df                          = pandas.DataFrame()
        df[self.first_col_name]     = subjs.labels
        df[self.second_col_name]    = subjs.sessions
        df[self.third_col_name]     = self.get_groups(subjs)

        return df

    def add_default_row(self, subj:SubjectSD):
        """
        Add the default row for the given subject.

        Parameters
        ----------
        subj : SubjectSD
            The SubjectSD object.

        Returns
        -------
        dict
            The default row for the given subject.
        """
        return {self.first_col_name: subj.label, self.second_col_name:subj.session, "group":self.get_groups(SubjectSDList([subj]))[0]}

    def add_new_columns(self, shname: str, subjdf: pandas.DataFrame):
        """
        Add new columns to the given sheet.

        Parameters
        ----------
        shname : str
            The name of the sheet.
        subjdf : pandas.DataFrame
            The DataFrame containing the data for the new columns.

        Raises
        ------
        Exception
            If the given DataFrame does not contain a session column.
        """
        if self.second_col_name not in subjdf.columns.values:
            raise Exception("Error in addColumns: given subjdf does not contain a session column")
        super().add_new_columns(shname, subjdf)

    def remove_subjects(self, subjects2remove:SubjectSDList, update=False) -> 'BayesDB':
        """
        Remove the given subjects from the database.

        Parameters
        ----------
        subjects2remove : SubjectSDList
            The list of SubjectSD objects to be removed.
        update : bool, optional
            If True, the changes will be reflected in the current object, by default False.

        Returns
        -------
        BayesDB
            The BayesDB object with the given subjects removed.
        """
        mshdb = super().remove_subjects(subjects2remove, update)
        return BayesDB(mshdb.sheets)

    def rename_subjects(self, assoc_dict, update=False) -> 'BayesDB':
        """
        Rename the subjects in the database.

        Parameters
        ----------
        assoc_dict : dict
            The dictionary that maps the old subject labels to the new labels.
        update : bool, optional
            If True, the changes will be reflected in the current object, by default False.

        Returns
        -------
        BayesDB
            The BayesDB object with the renamed subjects.
        """
        mshdb = super().rename_subjects(assoc_dict, update)
        return BayesDB(mshdb.sheets)

    def add_new_subjects(self, newdb:'MSHDB', can_diff_subjs=None, copy_previous_sess=None, update=False) -> 'BayesDB':
        """
        Add the subjects from the given database to the current database.

        Parameters
        ----------
        newdb : MSHDB
            The MSHDB object from which the subjects should be added.
        can_diff_subjs : bool, optional
            If True, subjects can have different sessions in different sheets, by default None.
        copy_previous_sess : bool, optional
            If True, the previous sessions will be copied to the new sheets, by default None.
        update : bool, optional
            If True, the changes will be reflected in the current object, by default False.

        Returns
        -------
        BayesDB
            The BayesDB object with the added subjects.
        """
        mshdb   = super().add_new_subjects(newdb, can_diff_subjs, copy_previous_sess, update)
        bayesdb = BayesDB(mshdb.sheets)

        bayesdb = bayesdb.sort()
        bayesdb.calc_flags()
        if update:
            self = bayesdb

        return bayesdb

    def get_groups(self, subjs:SubjectSDList=None) -> List[str]:
        """
        Get the groups for the given subjects.

        Parameters
        ----------
        subjs : SubjectSDList, optional
            The list of SubjectSD objects, by default None.

        Returns
        -------
        List[str]
            The list of groups.
        """
        if subjs is None:
            subjs = self.subjects

        return self.main.get_subjects_column(subjs, "group")

    # region GET LISTS OF INTERESTS
    def mrilabels(self, subj_labels:List[str]=None) -> list:
        """
        Get the MRI labels for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        list
            The list of MRI labels.
        """
        total = self.sheet_sd(self.main_name).select_subjlist(subj_labels, conditions=[FilterValues("mri"   , "==", 1)])
        td    = self.sheet_sd(self.main_name).select_subjlist(subj_labels, conditions=[FilterValues("group", "==", "TD"), FilterValues("mri", "==", 1)])
        bd    = self.sheet_sd(self.main_name).select_subjlist(subj_labels, conditions=[FilterValues("group", "==", "BD"), FilterValues("mri", "==", 1)])
        sk    = self.sheet_sd(self.main_name).select_subjlist(subj_labels, conditions=[FilterValues("group", "==", "SZ"), FilterValues("mri", "==", 1)])

        return [total, td, bd, sk]
    def bloodlabels(self, subj_labels: List[str] = None) -> List[List[str]]:
        """
        Get the blood labels for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        List[int]
            The list of blood labels.
        """
        total = self.sheet_sd(self.main_name).select_subjlist(subj_labels, conditions=[FilterValues("immfen_code", "exist", 0)])
        th = self.sheet_sd("sangue").select_subjlist(subj_labels, conditions=[FilterValues("T_HELP", "==", 1)])
        tr = self.sheet_sd("sangue").select_subjlist(subj_labels, conditions=[FilterValues("T_REG", "==", 1)])
        nk = self.sheet_sd("sangue").select_subjlist(subj_labels, conditions=[FilterValues("NK", "==", 1)])
        mono = self.sheet_sd("sangue").select_subjlist(subj_labels, conditions=[FilterValues("MONO", "==", 1)])
        bi = self.sheet_sd("sangue").select_subjlist(subj_labels, conditions=[FilterValues("B", "==", 1)])

        return [total, th, tr, nk, mono, bi]

    def bisection_labels(self, subj_labels: List[str] = None) -> List[int]:
        """
        Get the bisection labels for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        List[int]
            The list of bisection labels.
        """
        total = self.sheets.main.select_subjlist(
            subj_labels, colconditions=[FilterValues("oa", "==", 1)])

        return [total]    # endregion

    def calc_flags(self, outfile:Optional[str]=None):
        """
        Calculate the flags for the database.

        Parameters
        ----------
        outfile : str, optional
            The file to which the data should be saved, by default None.

        Returns
        -------
        None
            The function saves the data to the given file.
        """
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
        """Sort the database by the given items and in the given order.

        Parameters
        ----------
        by_items : List[str], optional
            The list of items by which to sort, by default ["subj", "session"].
        ascending : List[bool], optional
            A list of booleans indicating whether to sort in ascending order, by default [True, True].

        Returns
        -------
        BayesDB
            The sorted database.
        """
        for sh in self.sheets:
            self.sheet_sd(sh).df = self.sheet_sd(sh).df.sort_values(by=by_items, ascending=ascending, ignore_index=True)

        return self