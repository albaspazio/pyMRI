from typing import List

from data.SubjectSD import SubjectSD


class SubjectSDList(list):

    def __init__(self, subjects:List[SubjectSD]):
        super().__init__(item for item in subjects)

    @property
    def labels(self) -> List[str]:
        return [s.label for s in self]

    @property
    def ids(self) -> List[int]:
        return [s.id for s in self]

    @property
    def sessions(self) -> List[int]:
        return [s.session for s in self]

    def filter(self, sd, select_conds=None) -> 'SubjectSDList':

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

    def is_in(self, subj_list:'SubjectSDList') -> 'SubjectSDList':
        res = []
        for s in self:
            doexist = False
            for ss in subj_list:
                if s.is_equal(ss):
                    doexist = True
                    break
            if doexist:
                res.append(s)

        return SubjectSDList(res)

    def union_norep(self, subj_list:'SubjectSDList'):
        for s in subj_list:
            add = True
            for ss in self:
                if s.is_equal(ss):
                    add = False
                    break
            if add:
                self.append(s)

    def are_equal(self, subj_list:'SubjectSDList') -> bool:
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

    def contains(self, subj:SubjectSD) -> bool:
        for s in self:
            if s.is_equal(subj):
                return True
        return False
