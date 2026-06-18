from __future__ import annotations

import json
import os
from typing import List, Tuple, Any

from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from myutility.exceptions import SubjectListException, DataFileException
from myutility.list import is_list_of


class Project:
    """
    Base project class. Manages a SubjectsData dataframe and subject lists.
    Does not require MRI tools (FSL/SPM). Can be used standalone or extended by MRIProject.
    """

    data: SubjectsData = None

    def __init__(self, proj_dir: str, data: str | SubjectsData = "data.xlsx"):
        if not os.path.exists(proj_dir):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.dir    = proj_dir
        self.label  = os.path.basename(self.dir)
        self.name   = os.path.basename(self.dir)

        # subclasses may set subjects_lists_file before calling super().__init__
        if not hasattr(self, 'subjects_lists_file'):
            self.subjects_lists_file = os.path.join(self.dir, "subjects_lists.json")

        os.makedirs(self.dir, exist_ok=True)

        # load all available subjects list into self.subjects_lists
        with open(self.subjects_lists_file) as json_file:
            subjects            = json.load(json_file)
            self.subjects_lists = subjects["subjects"]

        # load subjects data if possible
        self.data_file  = ""
        self.data       = SubjectsData()
        self.load_data(data)

    # ==================================================================================================================
    # region DATA

    def _resolve_data_path(self, filename: str) -> str:
        """
        Resolve a data filename to an absolute path.

        Args:
            filename (str): The filename or path to resolve.

        Returns:
            str: The resolved absolute path.

        Raises:
            DataFileException: If the file cannot be found.
        """
        if os.path.exists(filename):
            return filename

        search_dir = getattr(self, '_data_search_dir', self.dir)
        candidate = os.path.join(search_dir, filename)
        if os.path.isfile(candidate):
            return candidate

        raise DataFileException(f"ERROR in Project._resolve_data_path: data file '{filename}' not found")

    def load_data(self, data: str | SubjectsData) -> SubjectsData:
        """
        Load data into the project.

        Args:
            data (str|SubjectsData): The path to the data file or a SubjectsData instance.

        Returns:
            SubjectsData: The loaded data.

        Raises:
            DataFileException: if given data is neither a string nor a SubjectsData instance.
        """
        if isinstance(data, str):
            data_file = self._resolve_data_path(data)
            self.data = SubjectsData(data_file)
            self.data_file = data_file
        elif isinstance(data, SubjectsData):
            self.data = data
        else:
            raise DataFileException("ERROR in Project.load_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

        return self.data

    def validate_data(self, data: SubjectsData | str | None = None) -> SubjectsData:
        """
        Validate and return a SubjectsData. If None, returns the project's data if loaded.

        Args:
            data (SubjectsData | str | None): The data to validate.

        Returns:
            SubjectsData: The validated data.

        Raises:
            DataFileException: If data is invalid or not loaded.
        """
        if data is None:
            if self.data.num > 0:
                return self.data
            else:
                raise DataFileException("ERROR in Project.validate_data: given data param (" + str(data) + ") is None and project's data is not loaded")
        elif isinstance(data, SubjectsData):
            return data
        elif isinstance(data, str):
            data_file = self._resolve_data_path(data)
            return SubjectsData(data_file)
        else:
            raise DataFileException("ERROR in Project.validate_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

    # endregion

    # ==================================================================================================================
    # region SUBJECTS LABELS

    @property
    def subjects_labels(self) -> List[str]:
        if self.data is not None:
            return self.data.subjects_labels
        else:
            return []

    def get_subjects_labels(self, grlab_subjlabs_subjs: str | List[str] = None) -> List[str]:
        """
        Returns a list of subject labels, optionally resolving a group label via subjects_lists.json.

        Parameters
        ----------
        grlab_subjlabs_subjs : str or List[str], optional
            Group label, list of subject labels, or None (returns loaded subjects).

        Returns
        -------
        List[str]

        Raises
        ------
        SubjectListException
        """
        if grlab_subjlabs_subjs is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("get_subjects_labels", "given grlab_subjlabs_subjs is None and no group is loaded")
            else:
                return self.subjects_labels

        elif isinstance(grlab_subjlabs_subjs, str):
            for grp in self.subjects_lists:
                if grp["label"] == grlab_subjlabs_subjs:
                    return grp["list"]
            raise SubjectListException("get_subjects_labels", "given group_label (" + grlab_subjlabs_subjs + ") does not exist in subjects_lists")

        elif is_list_of(grlab_subjlabs_subjs, str):
            return grlab_subjlabs_subjs

        else:
            raise SubjectListException("get_subjects_labels", "the given grlab_subjlabs_subjs param is not a valid param (None, string or string list), is: " + str(grlab_subjlabs_subjs))

    # endregion

    # ==================================================================================================================
    # region QUERY HELPERS

    def get_subjects_datarows(self, grlab_subjlabs_subjs: str | List[str], sess_ids: List[int] | None = None, data: SubjectsData = None) -> List[dict]:
        """
        Get subjects dict data by their labels/sessions.

        Args:
            grlab_subjlabs_subjs: group label or list of subject labels.
            sess_ids: list of requested sessions (None = all).
            data: optional SubjectsData override.

        Returns:
            List[dict]: The subject data rows.
        """
        if sess_ids is not None:
            if is_list_of(sess_ids, int) is False:
                raise DataFileException("Error in Project.get_subjects_datarows: given sessions is not a list of int")

        valid_data  = self.validate_data(data)
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs)
        sids        = valid_data.filter_subjects(subj_labels, sess_ids)

        return self.data.get_sids_dict(sids)

    def get_subjects_values_by_cols(self, grlab_subjlabs_subjs: str | List[str], columns_list: List[str],
                                    sess_ids: List[int] | None = None, data: SubjectsData = None,
                                    select_conds: List[FilterValues] = None,
                                    demean_flags: List[bool] = None) -> Tuple[List[List[Any]], List[str], List[int]]:
        """
        Get values for given columns and subjects.

        Returns:
            Tuple: (values matrix, labels list, sessions list)
        """
        if sess_ids is not None:
            if is_list_of(sess_ids, int) is False:
                raise DataFileException("Error in Project.get_subjects_values_by_cols: given sessions is not a list of int")

        valid_data  = self.validate_data(data)
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs)
        sids        = valid_data.filter_subjects(subj_labels, sess_ids, conditions=select_conds)

        return (valid_data.get_subjects_values_by_cols(sids, columns_list, demean_flags=demean_flags),
                sids.labels,
                sids.sessions)

    def get_filtered_column(self, grlab_subjlabs_subjs: str | List[str], column: str,
                            sess_ids: List[int] | None = None, data: str | SubjectsData = None,
                            select_conds: List[FilterValues] = None,
                            sort: bool = False, demean_flag: bool = False, ndecim: int = 4) -> Tuple[List[Any], List[str], List[int]]:
        """
        Returns values and labels for a single column, filtered by given conditions.

        Returns:
            Tuple: (values list, labels list, sessions list)
        """
        if sess_ids is not None:
            if is_list_of(sess_ids, int) is False:
                raise DataFileException("Error in Project.get_filtered_column: given sessions is not a list of int")

        valid_data  = self.validate_data(data)
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs)
        sids        = valid_data.filter_subjects(subj_labels, sess_ids, conditions=select_conds)

        return (valid_data.get_subjects_column(sids, column, sort=sort, demean=demean_flag, ndecim=ndecim),
                sids.labels,
                sids.sessions)

    # endregion
