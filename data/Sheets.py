from typing import List

from data.SubjectsData import SubjectsData
from utility.list import UnionNoRepO, same_elements


class Sheets(dict):

    def __new__(cls, sh_name:List[str]=None, main_id:int=0):
        return super(Sheets, cls).__new__(cls, None)

    def __init__(self, sh_name:List[str]=None, main_id:int=0):

        super().__init__()
        self.schema_sheets_names    = sh_name
        self.main_id                = main_id

    @property
    def main(self) -> SubjectsData:
        try:
            return self[self.schema_sheets_names[self.main_id]]
        except:
            return None

    @property
    def all_subjects(self):
        all_subjs = []
        for sh in self:
            labs = self[sh].subj_labels
            all_subjs = UnionNoRepO(all_subjs, labs)
        return all_subjs

    # check whether all sheets contain the same list of subjects
    @property
    def is_consistent(self) -> bool:

        all_subjs = self.all_subjects
        for sh in self:
            if not same_elements(self[sh].subj_labels, all_subjs):
                return False

        return True

    def copy(self):
        sheets = Sheets(self.schema_sheets_names, self.main_id)
        for sh in self:
            sheets[sh] = self[sh]

        return sheets

    def is_equal(self, sheets:'Sheets'):
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