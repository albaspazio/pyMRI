from typing import List

import pandas

from data.SubjectsData import SubjectsData
from data.SIDList import SIDList


class Sheets(dict):
    """
    A class to store SubjectsData from multiple sheets in a consistent format.

    Parameters
    ----------
    sh_names : List[str], optional
        A list of sheet names, by default None
    main_id : int, optional
        The index of the main sheet, by default 0

    Attributes
    ----------
    schema_sheets_names : List[str]
        A list of sheet names in the schema
    main_id : int
        The index of the main sheet

    Methods
    -------
    __new__
    __init__
    main
    all_subjects
    is_consistent
    copy
    is_equal
    """

    def __new__(cls, data:dict=None, sh_names: List[str] = None, main_id: int = 0, init: bool = False):
        """
        The __new__ method is a special method that is called when a new instance of the Sheets class is created.

        Parameters
        ----------
        sh_names : List[str], optional
            A list of sheet names, by default None
        main_id : int, optional
            The index of the main sheet, by default 0

        Returns
        -------
        Sheets
            A new instance of the Sheets class
            :param init:

        """
        return super(Sheets, cls).__new__(cls, None)

    def __init__(self, data:dict=None, sh_names: List[str] = None, main_id: int = 0, init: bool = False):
        """
        The __init__ method is a special method that is called when an instance of the Sheets class is initialized.

        Parameters
        ----------
        sh_names : List[str], optional
            A list of sheet names, by default None
        main_id : int, optional
            The index of the main sheet, by default 0
        init: bool, optional
            indicates whether init the dict with empty SubjectsData instances
        Returns
        -------
        None

        """
        super().__init__()
        self.schema_sheets_names = sh_names
        self.main_id = main_id

        if init is True:
            for sh in sh_names:
                self[sh] = SubjectsData()

    @property
    def main(self) -> SubjectsData:
        """
        Returns the main sheet as a SubjectsData object.

        Returns
        -------
        SubjectsData
            The main sheet as a SubjectsData object

        """
        try:
            return self[self.schema_sheets_names[self.main_id]]
        except:
            return SubjectsData()


    def sheet(self, sh_name:str) -> SubjectsData:
        return self[sh_name]

    def sheet_df(self, sh_name:str) -> pandas.DataFrame:
        return self.sheet(sh_name).df

    @property
    def all_subjects(self) -> SIDList:
        """
        Returns a list of all subjects from all sheets as a SIDList object.

        Returns
        -------
        SIDList
            A list of all subjects from all sheets as a SIDList object

        """
        try:
            all_subjs = SIDList(self.main.subjects.copy())

            for sh in self:
                if sh == self.schema_sheets_names[self.main_id]:  # skip main
                    continue
                subjs = self[sh].subjects
                all_subjs.union_norep(subjs)

            return all_subjs
        except:
            return []

    @property
    def is_consistent(self) -> bool:
        """
        Returns True if all sheets contain the same list of subjects, False otherwise.

        Returns
        -------
        bool
            True if all sheets contain the same list of subjects, False otherwise

        """
        all_subjs:SIDList = self.all_subjects
        for sh in self:
            if not all_subjs.are_equal(self[sh].subjects):
                return False

        return True

    def copy(self) -> 'Sheets':
        """
        Returns a copy of the Sheets object.

        Returns
        -------
        Sheets
            A copy of the Sheets object

        """
        sheets = Sheets(sh_names=self.schema_sheets_names, main_id=self.main_id)
        for sh in self:
            sheets[sh] = self[sh]

        return sheets

    def is_equal(self, sheets: 'Sheets') -> bool:
        """
        Returns True if the Sheets objects are equal, False otherwise.

        Parameters
        ----------
        sheets : Sheets
            The Sheets object to compare with

        Returns
        -------
        bool
            True if the Sheets objects are equal, False otherwise

        """
        report = ""
        for sh in self:
            if bool(sheets[sh]):
                if not self[sh].is_equal(sheets[sh]):
                    report = report + "\n data in sheet " + sh + " is different"
            else:
                report = report + "\nsheet " + sh + " is missing in compared db"
        if report != "":
            print("Sheets.is_equal show the following differences")
            return False

    def remove_sheet(self, sh:str):
        del self[sh]