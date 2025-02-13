from typing import List
import copy

import numpy as np

from data.SID import SID
from myutility.exceptions import DataFileException


class SIDList(list):
    """
    A list of SID objects.

    Attributes:
        list: A list of SID objects.

    Methods:
        filter: Filters the list based on select conditions.
        is_in: Checks if a list of SID objects is present in the current list.
        union_norep: Unions two lists of SID objects, removing duplicates.
        are_equal: Checks if two lists of SID objects are equal.
        contains: Checks if a SID object is present in the current list.
    """

    def __init__(self, subjects: List[SID]=None):
        """
        Initializes the SIDList.

        Args:
            subjects (List[SID]): A list of SID objects.
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
    def ids(self) -> List[int]:
        """
        Returns a list of IDs from the SID objects in the list.

        Returns:
            List[int]: A list of IDs.
        """
        _list = [s.id for s in self]
        return np.array(_list).flatten().tolist()

    @property
    def sessions(self) -> List[int]:
        """
        Returns a list of sessions from the SID objects in the list.

        Returns:
            List[int]: A list of sessions.
        """
        return [s.session for s in self]

    def filter(self, sd, select_conds=None) -> 'SIDList':
        """
        Filters the list based on select conditions.

        Args:
            sd (SubjectData): The SubjectData object.
            select_conds (List[SelectCondition]): A list of select conditions.

        Returns:
            SIDList: The filtered list.
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
            return SIDList(res)

    def is_in(self, sids: 'SIDList', context_self:bool=False) -> 'SIDList':
        """
        Checks if a list of SID objects is present in the current list.
        ID of the returned SID may be in the context of self or sids according to context_self value.

        Args:
            subj_list (SIDList): The list of SID objects.
            context_self (bool): define whether ids of the returned SID elements are in the context of self or sids
        Returns:
            SIDList: The list of SID objects that are present in the current list. in the context of either self or sids.

        """
        res = []
        if len(self) == 0:
            return SIDList()

        for sid in sids:
            doexist = False
            for ss in self:
                if sid.is_equal(ss):
                    doexist = True
                    break
            if doexist:
                if context_self is True:
                    res.append(ss)
                else:
                    res.append(sid)

        return SIDList(res)

    def append_novel(self, subj_list: 'SIDList') -> 'SIDList':
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

    def are_equal(self, subj_list: 'SIDList') -> bool:
        """
        Checks if two lists of SID objects are equal.
        check whether all elems of subj_list are present in self and then the reverse

        Args:
            subj_list (SIDList): The list of SID objects to be compared.

        Returns:
            bool: True if the two lists are equal, False otherwise.
        """
        if subj_list is None or not isinstance(subj_list, SIDList):
            raise DataFileException("Error in SIDList.are_equal: given subj_list (" + str(subj_list) +  ") is not a SIDList")

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


    def contains(self, subj: SID) -> bool:
        """
        Checks if a SID object is present in the current list.

        Args:
            subj (SID): The SID object to be checked.

        Returns:
            bool: True if the SID object is present, False otherwise.
        """
        for s in self:
            if s.is_equal(subj):
                return True
        return False
