from __future__ import annotations

from typing import List, Optional

import pandas

from data.GDriveSheet import GDriveSheet
from data.MSHDB import MSHDB
from data.Sheets import Sheets
from data.SID import SID
from data.SIDList import SIDList
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from myutility.exceptions import DataFileException, SubjectExistException
from myutility.list import is_list_of, same_elements


class BayesDB(MSHDB):
    """
    The BayesDB class provides an interface to a collection of MSHDB sheets that contain data on multiple subjects.
    The class provides methods for loading, saving, sorting, and manipulating the data in the sheets. It also provides methods for calculating summary statistics and other derived variables.
    The class is designed to be flexible and extensible, allowing users to define their own custom sheets and columns.

    Parameters
    ----------
    data : str, Sheets, or GDriveSheet
        The data source for the database. This can be a path to an Excel file, a Google Sheet, or a Python dictionary containing the data.
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
    subjects : SIDList
        The list of SID objects that are in the database.
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
    remove_extra_columns(hdr)
        Remove the extra columns from the given list.

    overridden Methods
    -------
    sort(by_items=["subj", "session"], ascending=[True, True])
        Sort the data by the given items and in the given order.
    add_default_columns(subjs, df)
        Add the default columns (subj, session, group) to the given DataFrame.
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
    add_new_subjects(newdb, copy_previous_sess=None, update=False)
        Add the subjects from the given database.
    get_groups(subjs=None)
        Get the groups for the given subjects.
    mri_labels(subj_labels=None)
        Get the MRI labels for the given subjects.
    mri_sd(subj_labels=None)
        Get the MRI SubjectsSD for the given subjects.
    blood_labels(subj_labels=None)
        Get the blood labels for the given subjects.
    blood_sd(subj_labels=None)
        Get the blood SubjectsSD for the given subjects.
    bisection_labels(subj_labels=None)
        Get the bisection labels for the given subjects.
    bisection_sd(subj_labels=None)
        Get the bisection SubjectsSD for the given subjects.
    calc_flags(outfile=None)
        Calculate the flags for the database.
    """

    def __init__(self,  file_schema:str,
                        data: str | Sheets | GDriveSheet = None,
                        password: str = "",
                        calc_flags: bool = True,
                        sortonload: bool = True,
                        check_consistency:bool=True):
        """
        Initialize the class.
        """

        super().__init__(file_schema, data, True, password=password, sortonload=sortonload)

        if data is not None:
            if check_consistency:
                if not self.is_consistent:
                    raise Exception("Error in BayesDB init: source " + str(data) + " is not consistent")

        if calc_flags:
            self.calc_flags()


    @property
    def is_consistent(self) -> bool:

        # get subjects consistency
        subjs_cons:bool = self.sheets.is_consistent

        if subjs_cons is False:
            print("BayesDB.is_consistent found different subjects")

        # check groups consistencies
        groups = self.main.get_subjects_column(colname=self.extra_columns[0])
        for sh in self.sheets:
            try:
                if not same_elements(groups, self.get_sheet_sd(sh).get_subjects_column(colname=self.extra_columns[0])):
                    groups_cons = False
                    print("BayesDB.is_consistent found different groups across sheets")
                    break
            except Exception as e:
                raise Exception("Error in BayesDB.is_consistent: groups list of sheet " + sh + " has some issues")
        groups_cons = True
        return subjs_cons and groups_cons

    # ======================================================================================
    # region OVERRIDE
    def add_default_columns(self, subjs:SIDList, df:pandas.DataFrame) -> pandas.DataFrame:
        """
        Add the default columns (subj, session, group) to the given DataFrame.

        Parameters
        ----------
        subjs : SIDList
            The list of SID objects.
        df : pandas.DataFrame
            The DataFrame to be modified.

        Returns
        -------
        pandas.DataFrame
            The given DataFrame with the default columns added.
        """
        df[self.unique_columns[0]] = subjs.labels
        df[self.unique_columns[1]] = subjs.sessions
        return df

    def get_default_columns(self, sids:SIDList, groups:List[str]=None) -> pandas.DataFrame:
        """
        Add the default rows (subj, session, group) to the given DataFrame.

        Parameters
        ----------
        subjs : SIDList, optional
            The list of SID objects, by default None.

        Returns
        -------
        pandas.DataFrame
            The DataFrame with the default rows added.
        """
        df                          = pandas.DataFrame()
        df[self.unique_columns[0]]  = sids.labels
        df[self.unique_columns[1]]  = sids.sessions

        if groups is None:
            df[self.extra_columns[0]] = self.get_groups(subjs)
            return df
        else:
            if groups == []:
                return df
            else:
                if not is_list_of(groups, str):
                    raise DataFileException("Error in BayesDB,add_default_rows: given groups (" + str(groups) + ") is not a list of str")

                df[self.extra_columns[0]]   = groups
                return df

    def get_default_row(self, subj:SID) -> dict:
        """
        Add the default row for the given subject.

        Parameters
        ----------
        subj : SID
            The SID object.

        Returns
        -------
        dict
            The default row for the given subject.
        """
        return {self.unique_columns[0]: subj.label, self.unique_columns[1]:subj.session, "group":self.get_groups(SIDList([subj]))[0]}

    def remove_subjects(self, subjects2remove:SIDList, update=False) -> 'BayesDB':
        """
        Remove the given subjects from the database.

        Parameters
        ----------
        subjects2remove : SIDList
            The list of SID objects to be removed.
        update : bool, optional
            If True, the changes will be reflected in the current object, by default False.

        Returns
        -------
        BayesDB
            The BayesDB object with the given subjects removed.
        """
        db = super().remove_subjects(subjects2remove, update)

        if isinstance(db, BayesDB):
            return db
        else:
            return BayesDB(self.schema_file, db.sheets)

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
        return BayesDB(self.schema, mshdb.sheets)

    def add_new_subjects(self, newdb: 'MSHDB', can_update:bool=False, must_exist:bool=False, copy_previous_sess:list | None =None,
                         update=False) -> 'BayesDB':
        """
        Add the subjects from the given database to the current database.

        Parameters
        ----------
        newdb : MSHDB
            The MSHDB object from which the subjects should be added.
        can_update : bool, optional
            define whether already existing subjects shall be upgraded or ignored
        must_exist : bool, optional
            define whether subjects in newdb must exist (e.g. when adding only auot) or not
        copy_previous_sess : list | None, optional
            If True, the previous sessions will be copied to the new sheets, by default None.
        update : bool, optional
            If True, the changes will be reflected in the current object, by default False.

        Returns
        -------
        BayesDB
            The BayesDB object with the added subjects.
            :param must_exist:
            :param can_update:
        """
        bayesdb   = super().add_new_subjects(newdb, can_update=can_update, must_exist=must_exist, copy_previous_sess=copy_previous_sess, update=update)
        # bayesdb = BayesDB(mshdb.sheets)

        bayesdb = bayesdb.sort()
        bayesdb.calc_flags()
        if update:
            self = bayesdb

        return bayesdb

    def copy(self) -> 'BayesDB':
        '''
        return a deep copy of current instance
        :return: BayesDB
        '''
        cp           = super().copy()
        cp.__class__ = BayesDB
        return cp

    def get_groups(self, subjs:SIDList=None) -> List[str]:
        """
        Get the groups for the given subjects.

        Parameters
        ----------
        subjs : SIDList, optional
            The list of SID objects, by default None.

        Returns
        -------
        List[str]
            The list of groups.
        """
        if subjs is None:
            subjs = self.subjects

        return self.main.get_subjects_column(subjs, "group")

    def mri_sd(self, subj_labels:List[str]=None) -> list[SIDList]:
        """
        Get the SIDList for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        list
            The list of MRI labels.
        """
        total = self.get_sheet_sd(self.main_name).filter_subjects(subj_labels, conditions=[FilterValues("mri", "==", 1)])
        td    = self.get_sheet_sd(self.main_name).filter_subjects(subj_labels, conditions=[FilterValues("group", "==", "TD"), FilterValues("mri", "==", 1)])
        bd    = self.get_sheet_sd(self.main_name).filter_subjects(subj_labels, conditions=[FilterValues("group", "==", "BD"), FilterValues("mri", "==", 1)])
        sk    = self.get_sheet_sd(self.main_name).filter_subjects(subj_labels, conditions=[FilterValues("group", "==", "SZ"), FilterValues("mri", "==", 1)])

        return [total, td, bd, sk]

    # region GET LISTS OF INTERESTS
    def mri_labels(self, subj_labels:List[str]=None) -> list[list[str]]:
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

        lists = self.mri_sd(subj_labels)

        return [lists[0].labels, lists[1].labels, lists[2].labels, lists[3].labels]

    def blood_sd(self, subj_labels: List[str] = None) -> List[SIDList]:
        """
        Get the blood SIDList for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        List[int]
            The list of blood labels.
        """
        total   = self.get_sheet_sd(self.main_name).filter_subjects(subj_labels, conditions=[FilterValues("immfen_code", "exist", 0)])

        th      = self.get_sheet_sd("BLOOD").filter_subjects(subj_labels, conditions=[FilterValues("T_HELP", "==", 1)])
        tr      = self.get_sheet_sd("BLOOD").filter_subjects(subj_labels, conditions=[FilterValues("T_REG", "==", 1)])
        nk      = self.get_sheet_sd("BLOOD").filter_subjects(subj_labels, conditions=[FilterValues("NK", "==", 1)])
        mono    = self.get_sheet_sd("BLOOD").filter_subjects(subj_labels, conditions=[FilterValues("MONO", "==", 1)])
        bi      = self.get_sheet_sd("BLOOD").filter_subjects(subj_labels, conditions=[FilterValues("B", "==", 1)])

        return [total, th, tr, nk, mono, bi]
    def blood_labels(self, subj_labels: List[str] = None) -> List[List[str]]:
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

        lists = self.blood_sd(subj_labels)
        return [lists[0].labels, lists[1].labels, lists[2].labels, lists[3].labels, lists[4].labels, lists[5].labels]

    def bisection_sd(self, subj_labels: List[str] = None) -> SIDList:
        """
        Get the bisection SIDList for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        List[str]
            The list of bisection labels.
        """
        total = self.sheets.main.filter_subjects(subj_labels, conditions=[FilterValues("oa", "==", 1)])

        return [total]    # endregion
    def bisection_labels(self, subj_labels: List[str] = None) -> List[str]:
        """
        Get the bisection labels for the given subjects.

        Parameters
        ----------
        subj_labels : List[str], optional
            The list of subject labels, by default None.

        Returns
        -------
        List[str]
            The list of bisection labels.
        """
        return [self.bisection_sd(subj_labels).labels]    # endregion

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
                           {"BISA":["oa"]},
                           {"BLOOD":["NK"]}, {"BLOOD":["T_HELP", "T_REG"]}, {"BLOOD":["MONO"]}, {"BLOOD":["B"]}, {"BLOOD":["PROT"]},
                           {"MATRICS":["MATRICS_date"]},
                           {"main":["mri_code"], "BISA":["oa"]},
                           {"main":["mri_code"], "BLOOD":["NK"]}, {"main":["mri_code"], "BLOOD":["T_HELP", "T_REG"]}, {"main":["mri_code"], "BLOOD":["MONO"]}, {"main":["mri_code"], "BLOOD":["B"]}, {"main":["mri_code"], "BLOOD":["PROT"]}
                           ]

        for id,val in enumerate(cols2write):
            # e.g. "mri_oa"
            dest_col_lab = val

            for subj in self.subjects:
                values = []

                for id_1, src_sheet_lab in enumerate(list(in_sheets_cells[id].keys())):   # e.g. ["main", "BISA"]
                    # e.g. "main"
                    if src_sheet_lab in self.sheets:
                        src_sd:SubjectsData = self.get_sheet_sd(src_sheet_lab)
                        # SID(i,lab,sess)
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

    def sort(self, by_items:List[str]=None, ascending=[True, True]):
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
        if by_items is None:
            by_items = self.unique_columns

        for sh in self.sheets:
            self.get_sheet_sd(sh).df = self.get_sheet_sd(sh).df.sort_values(by=by_items, ascending=ascending, ignore_index=True)

        return self

    def compare_db(self, db2compare:BayesDB, diff_out_db:str, must_be_consistent:bool=False, sheets2compare:List[str]=None):

        if sheets2compare is None:
            sheets2compare = self.schema_sheets_names

        if must_be_consistent:
            if not db2compare.is_consistent:
                raise DataFileException("Error in MSHDB.compare_db: given db is not consistent...skipping comparison")

        try:
            if self.len != db2compare.len:
                raise DataFileException("LENGTH", db2compare.len)

            if not self.subjects.are_equal(db2compare.subjects):
                raise DataFileException("SUBJECTS")

            # can create a new MSHDB
            diff_db:BayesDB = BayesDB(self.schema_file)
            default_df      = self.get_default_columns(self.subjects, [])   # don't add groups info
            sheets2save     = []
            for sh in sheets2compare:
                are_equal = True
                # create a copy of self with only the first two columns filled and the other nan
                cols                = self.get_sheet_sd(sh).header[2:]
                df                  = pandas.DataFrame(columns=cols)
                diff_db.sheets[sh]  = SubjectsData(pandas.concat([default_df, df]))

                for col in cols:
                    for sid in self.subjects:
                        curr_value  = self.get_sheet_sd(sh).get_subject_col_value(sid, col)
                        other_value = db2compare.get_sheet_sd(sh).get_subject_col_value(sid, col)

                        if curr_value != other_value:
                            diff_db.get_sheet_sd(sh).set_subj_session_value(sid, col, other_value)
                            are_equal = False

                if are_equal is False:
                    sheets2save.append(sh)

            diff_db.save(diff_out_db, sheets2save)

        except Exception as e:
            raise Exception("Error in BayesDB.compare_db: sheet " + sh + " | " + e.msg)
