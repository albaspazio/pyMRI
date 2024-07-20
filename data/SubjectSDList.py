from typing import List

from data.SubjectSD import SubjectSD


class SubjectSDList(list):
    """
    A list of SubjectSD objects.

    Attributes:
        list: A list of SubjectSD objects.

    Methods:
        filter: Filters the list based on select conditions.
        is_in: Checks if a list of SubjectSD objects is present in the current list.
        union_norep: Unions two lists of SubjectSD objects, removing duplicates.
        are_equal: Checks if two lists of SubjectSD objects are equal.
        contains: Checks if a SubjectSD object is present in the current list.
    """

    def __init__(self, subjects: List[SubjectSD]):
        """
        Initializes the SubjectSDList.

        Args:
            subjects (List[SubjectSD]): A list of SubjectSD objects.
        """
        super().__init__(item for item in subjects)

    @property
    def labels(self) -> List[str]:
        """
        Returns a list of labels from the SubjectSD objects in the list.

        Returns:
            List[str]: A list of labels.
        """
        return [s.label for s in self]

    @property
    def ids(self) -> List[int]:
        """
        Returns a list of IDs from the SubjectSD objects in the list.

        Returns:
            List[int]: A list of IDs.
        """
        return [s.id for s in self]

    @property
    def sessions(self) -> List[int]:
        """
        Returns a list of sessions from the SubjectSD objects in the list.

        Returns:
            List[int]: A list of sessions.
        """
        return [s.session for s in self]

    def filter(self, sd, select_conds=None) -> 'SubjectSDList':
        """
        Filters the list based on select conditions.

        Args:
            sd (SubjectData): The SubjectData object.
            select_conds (List[SelectCondition]): A list of select conditions.

        Returns:
            SubjectSDList: The filtered list.
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
            return SubjectSDList(res)

    def is_in(self, subj_list: 'SubjectSDList') -> 'SubjectSDList':
        """
        Checks if a list of SubjectSD objects is present in the current list.

        Args:
            subj_list (SubjectSDList): The list of SubjectSD objects.

        Returns:
            SubjectSDList: The list of SubjectSD objects that are present in the current list.
        """
        res = []
        if len(self) == 0:
            return SubjectSDList([])

        for s in self:
            doexist = False
            for ss in subj_list:
                if s.is_equal(ss):
                    doexist = True
                    break
            if doexist:
                res.append(s)

        return SubjectSDList(res)

    def union_norep(self, subj_list: 'SubjectSDList'):
        """
        Unions two lists of SubjectSD objects, removing duplicates.

        Args:
            subj_list (SubjectSDList): The list of SubjectSD objects to be unioned.
        """
        for s in subj_list:
            add = True
            for ss in self:
                if s.is_equal(ss):
                    add = False
                    break
            if add:
                self.append(s)

    def are_equal(self, subj_list: 'SubjectSDList') -> bool:
        """
        Checks if two lists of SubjectSD objects are equal.

        Args:
            subj_list (SubjectSDList): The list of SubjectSD objects to be compared.

        Returns:
            bool: True if the two lists are equal, False otherwise.
        """
        exist = False
        for s in subj_list:
            exist = False
            for ss in self:
                if s.is_equal(ss):
                    exist = True
                    break
            if not exist:
                return False

        return exist

    def contains(self, subj: SubjectSD) -> bool:
        """
        Checks if a SubjectSD object is present in the current list.

        Args:
            subj (SubjectSD): The SubjectSD object to be checked.

        Returns:
            bool: True if the SubjectSD object is present, False otherwise.
        """
        for s in self:
            if s.is_equal(subj):
                return True
        return False
