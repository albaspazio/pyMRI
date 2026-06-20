from __future__ import annotations

import json
import os
from typing import List, Tuple, Any

from data.SubjectsData import SubjectsData
from data.SID import SID
from data.utilities import FilterValues
from myutility.exceptions import SubjectListException, DataFileException
from myutility.list import is_list_of
from subject.Subject import Subject
from subject.SubjectsList import SubjectsList


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
    # region SUBJECTS MANAGEMENT

    def get_subjects(self, group_or_subjlabels: str | List[str], 
                     sess_ids: List[int] | None = None, 
                     must_exist: bool = False) -> SubjectsList:
        """
        Universal converter: group label or subject labels → SubjectsList.
        
        This is the central entry point for subject queries. It converts various input formats
        to a standardized SubjectsList that downstream methods can use.
        
        Parameters
        ----------
        group_or_subjlabels : str or List[str]
            Either:
            - Group label (str): looks up in subjects_lists.json (e.g., "controls", "patients")
            - Subject labels (List[str]): direct list of subject labels (e.g., ["0001", "0002"])
        sess_ids : List[int], optional
            Requested session IDs. If None, uses all available sessions for each subject.
        must_exist : bool, optional
            If True, raises SubjectListException if any subject doesn't exist in data.
            Default: False (silently skips missing subjects).
        
        Returns
        -------
        SubjectsList
            List of Subject instances (or SubjectMRI at MRIProject runtime) with the requested 
            label/session combinations.
        
        Raises
        ------
        SubjectListException
            If group_or_subjlabels is invalid or if must_exist=True and subjects are missing.
        
        Examples
        --------
        >>> # By group name
        >>> subjects = project.get_subjects("controls", sess_ids=[1])
        
        >>> # By explicit labels
        >>> subjects = project.get_subjects(["0001", "0002"], sess_ids=[1, 2])
        
        >>> # All available sessions
        >>> subjects = project.get_subjects("patients")
        """
        # Convert input to label list
        if isinstance(group_or_subjlabels, str):
            subj_labels = self._get_subjects_labels(group_or_subjlabels)
        elif is_list_of(group_or_subjlabels, str):
            subj_labels = group_or_subjlabels
        else:
            raise SubjectListException("get_subjects", 
                f"group_or_subjlabels must be str or List[str], got {type(group_or_subjlabels)}")
        
        # Build SubjectsList from labels and sessions
        subjects = SubjectsList()
        for label in subj_labels:
            # Determine which sessions to use
            if sess_ids is None:
                sessions = self.data.get_subject_available_sessions(label, error_if_empty=not must_exist)
            else:
                sessions = sess_ids
            
            # Create Subject for each label/session combination
            for sess_id in sessions:
                subj = Subject(label, self, sess_id)
                if subj.exist or not must_exist:
                    subjects.append(subj)
                elif must_exist:
                    raise SubjectListException("get_subjects", 
                        f"Subject '{label}' with session {sess_id} does not exist")
        
        return subjects

    # endregion

    # ==================================================================================================================
    # region SUBJECTS LABELS

    @property
    def subjects_labels(self) -> List[str]:
        if self.data is not None:
            return self.data.subjects_labels
        else:
            return []

    def _get_subjects_labels(self, group_label: str | None = None) -> List[str]:
        """
        Internal helper: resolve a group label to subject labels via subjects_lists.json.
        
        For direct access to subject labels from a SubjectsList, use: subjects.labels

        Parameters
        ----------
        group_label : str, optional
            Group label to look up in subjects_lists.json.
            If None, returns all loaded subjects' labels.

        Returns
        -------
        List[str]
            List of subject labels.

        Raises
        ------
        SubjectListException
            If group_label doesn't exist in subjects_lists or no subjects loaded.
        """
        if group_label is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("_get_subjects_labels", "given group_label is None and no group is loaded")
            else:
                return self.subjects_labels

        elif isinstance(group_label, str):
            for grp in self.subjects_lists:
                if grp["label"] == group_label:
                    return grp["list"]
            raise SubjectListException("_get_subjects_labels", "given group_label (" + group_label + ") does not exist in subjects_lists")

        else:
            raise SubjectListException("_get_subjects_labels", "given group_label must be str or None, got: " + str(type(group_label)))

    # endregion

    # ==================================================================================================================
    # region QUERY HELPERS

    def get_subjects_datarows(self, subjects: SubjectsList, data: SubjectsData = None) -> List[dict]:
        """
        Get subjects dict data.

        Args:
            subjects: SubjectsList of subjects to query.
            data: optional SubjectsData override.

        Returns:
            List[dict]: The subject data rows.
        """
        valid_data = self.validate_data(data)
        sids = valid_data.filter_subjects(subjects.labels, subjects.sessions)
        return self.data.get_sids_dict(sids)

    def get_subjects_values_by_cols(self, subjects: SubjectsList, columns_list: List[str],
                                    data: SubjectsData = None,
                                    select_conds: List[FilterValues] = None,
                                    demean_flags: List[bool] = None) -> Tuple[List[List[Any]], List[str], List[int]]:
        """
        Get values for given columns and subjects.

        Args:
            subjects: SubjectsList of subjects to query.
            columns_list: Column names to retrieve.
            data: optional SubjectsData override.
            select_conds: optional filter conditions.
            demean_flags: optional demean flags per column.

        Returns:
            Tuple: (values matrix, labels list, sessions list)
        """
        valid_data = self.validate_data(data)
        sids = valid_data.filter_subjects(subjects.labels, subjects.sessions, conditions=select_conds)

        return (valid_data.get_subjects_values_by_cols(sids, columns_list, demean_flags=demean_flags),
                sids.labels,
                sids.sessions)

    def get_filtered_column(self, subjects: SubjectsList, column: str,
                            data: str | SubjectsData = None,
                            select_conds: List[FilterValues] = None,
                            sort: bool = False, demean_flag: bool = False, ndecim: int = 4) -> Tuple[List[Any], List[str], List[int]]:
        """
        Returns values and labels for a single column, filtered by given conditions.

        Args:
            subjects: SubjectsList of subjects to query.
            column: Column name to retrieve.
            data: optional SubjectsData override.
            select_conds: optional filter conditions.
            sort: whether to sort results.
            demean_flag: whether to demean the column.
            ndecim: decimal places for demeaning.

        Returns:
            Tuple: (values list, labels list, sessions list)
        """
        valid_data = self.validate_data(data)
        sids = valid_data.filter_subjects(subjects.labels, subjects.sessions, conditions=select_conds)

        return (valid_data.get_subjects_column(sids, column, sort=sort, demean=demean_flag, ndecim=ndecim),
                sids.labels,
                sids.sessions)

    # endregion
