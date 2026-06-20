from typing import List
import copy

import numpy as np

from data import SubjectsData
from data.SID import SID
from myutility.exceptions import DataFileException, SubjectListException
from subject.Subject import Subject


class SubjectsList(list):
    """
    A list of Subject instances.

    Attributes:
        list: A list of Subject instances.

    Methods:
        filter: Filters the list based on select conditions.
        is_in: Checks if a list of SID objects is present in the current list.
        union_norep: Unions two lists of SID objects, removing duplicates.
        are_equal: Checks if two lists of SID objects are equal.
        contains: Checks if a SID object is present in the current list.
    """

    def __init__(self, subjects: List[Subject]=None):
        """
        Initializes the SubjectsList.

        Args:
            subjects (List[Subject]): A list of Subject instances.
        """
        if subjects is None:
            subjects = []
        super().__init__(item for item in subjects)

    @property
    def labels(self) -> List[str]:
        """
        Returns a list of labels from the SID objects in the list.

        Returns:
            List[str]: A list of labels.
        """
        return [s.label for s in self]

    @property
    def sessions(self) -> List[int]:
        """
        Returns a list of sessions from the SID objects in the list.

        Returns:
            List[int]: A list of sessions.
        """
        return [s.session for s in self]

    def filter(self, sd:'SubjectsData', select_conds:'list[FilterValues]'=None) -> 'SubjectsList':
        """
        Filters the list based on select conditions.

        Args:
            sd (SubjectData): The SubjectData object.
            select_conds (List[SelectCondition]): A list of select conditions.

        Returns:
            SubjectsList: The filtered list.
        """
        res = []
        if select_conds is None:
            return self
        else:
            for s in self:
                add = True
                for selcond in select_conds:
                    if not selcond.isValid(sd.get_subject_col_value(s.id, selcond.colname)):
                        add = False
                if add:
                    res.append(s)
            return SubjectsList(res)

    def is_in(self, sids: 'SubjectsList') -> 'SubjectsList':
        """
        returns a list of Subject instances that are present in both list, ordered according to self.

        Args:
            subj_list (SubjectsList): The list of Subject instances.
        Returns:
            SubjectsList: The list of Subject instances that are present in the current list. ordered according to self.

        """
        res = []
        if len(self) == 0:
            return SubjectsList()

        for ss in self:
            doexist = False
            for sid in sids:
                if sid.is_equal(ss):
                    doexist = True
                    break
            if doexist:
                res.append(ss)

        return SubjectsList(res)

    def append_novel(self, subj_list: 'SubjectsList') -> 'SubjectsList':
        """
        Append self only with novel elements of given list SIDList.

        Args:
            subj_list (SIDList): The list of SID objects to be unioned.
        """

        for s in subj_list:
            add = True
            for ss in self:
                if s.is_equal(ss):
                    add = False
                    break
            if add:
                self.append(s)

    def are_equal(self, subj_list: 'SubjectsList') -> bool:
        """
        Checks if two lists of Subject instances are equal.
        check whether all elems of subj_list are present in self and then the reverse

        Args:
            subj_list (SubjectsList): The list of Subject instances to be compared.

        Returns:
            bool: True if the two lists are equal, False otherwise.
        """
        if subj_list is None or not isinstance(subj_list, SubjectsList):
            raise SubjectListException("Error in SubjectsList.are_equal: given subj_list (" + str(subj_list) +  ") is not a SubjectsList")

        for s in subj_list:
            exist = False
            for ss in self:
                if s.is_equal(ss):
                    exist = True
                    break
            if not exist:
                return False

        # at this point, all elements of subj_list exist in self. check the contrary (element of self that does not exist in subj_list)
        for ss in self:
            exist = False
            for s in subj_list:
                if s.is_equal(ss):
                    exist = True
                    break
            if not exist:
                return False

        return True


    def contains(self, subj: Subject) -> bool:
        """
        Checks if a SubjectsList object is present in the current list.

        Args:
            subj (Subject): The Subject object to be checked.

        Returns:
            bool: True if the Subject instance is present, False otherwise.
        """
        for s in self:
            if s.is_equal(subj):
                return True
        return False
