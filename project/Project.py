from __future__ import annotations

import json
import os
import pandas
from copy import deepcopy
from typing import List, Tuple, Any

from data.SIDList import SIDList
from data.SubjectsData import SubjectsData
from data.SID import SID
from data.utilities import FilterValues
from myutility.exceptions import SubjectListException, DataFileException, SubjectExistException
from myutility.list import is_list_of
from subject.Subject import Subject
from subject.SubjectsList import SubjectsList


class Project:
    """
    Base project class. Manages a SubjectsData dataframe and subject lists.
    Does not require MRI tools (FSL/SPM). Can be used standalone or extended by ProjectMRI.
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

        # populate subjects from excel data
        self._subjects = SubjectsList()
        self._build_subjects()
        
        # validate subjects_lists.json against excel
        self._validate_subjects_json()

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

    def _create_subject(self, sid:SID) -> Subject:
        """
        Factory method: create a Subject instance with sid immediately assigned.
        
        Creates a Subject and immediately assigns its sid from self.data.
        Subclasses override this to create domain-specific types (e.g., SubjectMRI).
        
        Parameters
        ----------
        sid : SID
            Subject SID got from SubjectsData

        Returns
        -------
        Subject
            A new Subject instance with sid assigned.
        
        Raises
        ------
        DataFileException
            If (label, sess_id) not found in self.data.
        """
        subj = Subject(sid.label, self, sid.session)
        subj.sid = sid  # Raises DataFileException if not found
        return subj

    def _build_subjects(self) -> None:
        """
        Build and populate self._subjects from self.data.
        
        Iterates through self.data.subjects (SIDList) and creates a Subject for each,
        with sid already assigned via _create_subject(). Called only from __init__.
        """
        self._subjects = SubjectsList()
        for sid in self.data.subjects:
            subj = self._create_subject(sid)
            self._subjects.append(subj)

    @property
    def subjects(self) -> SubjectsList:
        """
        Read-only property: the SubjectsList of all subjects in this project.
        
        Populated at __init__ from self.data (excel). Each Subject has its sid
        already assigned to its project.data.
        
        Returns
        -------
        SubjectsList
            The list of all subjects in the project.
        """
        return self._subjects

    def _validate_subjects_json(self) -> None:
        """
        Validate subjects_lists.json against excel data.
        
        Emits UserWarning for labels in subjects_lists.json not present in excel.
        Non-blocking: init completes even if warnings are emitted.
        """
        import warnings
        
        if not hasattr(self, 'subjects_lists_file') or not self.subjects_lists:
            return
        
        all_excel_labels = set(self.data.subjects_labels) if self.data.num > 0 else set()
        missing = set()
        
        for grp in self.subjects_lists:
            for label in grp.get("list", []):
                if label not in all_excel_labels:
                    missing.add(label)
        
        if missing:
            warnings.warn(
                f"subjects_lists.json contiene {len(missing)} label non presenti nell'excel: {sorted(missing)}",
                UserWarning, stacklevel=2
            )

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
            List of Subject instances (or SubjectMRI at ProjectMRI runtime) with the requested
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
            raise SubjectListException("get_subjects",f"group_or_subjlabels must be str or List[str], got {type(group_or_subjlabels)}")
        
        # Build SubjectsList from labels and sessions
        subjects = SubjectsList()
        for label in subj_labels:
            # Determine which sessions to use
            if sess_ids is None:
                sessions = self.data.get_subject_available_sessions(label, error_if_empty=not must_exist)
            else:
                sessions = sess_ids
            
            # Create Subject for each label/session combination (uses factory method)
            for sess_id in sessions:
                try:
                    sid = self.data.get_sid(label, sess_id)
                    subj = self._create_subject(sid)
                    subjects.append(subj)
                except DataFileException:
                    if must_exist:
                        raise SubjectListException("get_subjects", f"Subject '{label}' with session {sess_id} does not exist")
        return subjects

    def get_subject(self, subjlabel: str, sess_id: int = 1, must_exist: bool = False) -> Subject:
        return self.get_subjects([subjlabel], [sess_id], must_exist)[0]

    def get_subject_session(self, subj_label: str, sess: int = 1, must_exist: bool = True) -> Subject:
        """
        Get an independent SubjectMRI instance for the given label/session.

        Returns Subject type (which is SubjectMRI at runtime).
        """
        if must_exist:
            for subj in self.subjects:
                if subj.label == subj_label:
                    if subj.sessid == sess:
                        return deepcopy(subj)
                    else:
                        return subj.get_properties(sess)
            raise SubjectExistException(
                "Error in ProjectMRI.get_subject: given subject (" + subj_label + " does not exist")
        else:
            sid = self.data.get_sid(subj_label, sess)
            return self._create_subject(sid)


    @property
    def nsubj(self) -> int:
        return len(self.subjects)

    # endregion

    # ==================================================================================================================
    # region SUBJECTS LABELS

    @property
    def subjects_labels(self) -> List[str]:
        return self.subjects.labels


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
        sids = valid_data.filter_sids(None, sids=self.subjects2sids(subjects))
        return valid_data.get_sids_dict(sids)

    def get_subjects_values_by_cols(self, subjects: SubjectsList, columns_list: List[str],
                                    data: SubjectsData = None,
                                    select_conds: List[FilterValues] = None,
                                    demean_flags: List[bool] = None, ndecim: int = 4) -> Tuple[List[List[Any]], List[str], List[int]]:
        """
        Get values for given columns and subjects.

        Args:
            subjects: SubjectsList of subjects to query.
            columns_list: Column names to retrieve.
            data: optional SubjectsData override.
            select_conds: optional filter conditions.
            demean_flags: optional demean flags per column.
            ndecim: decimal places for demeaning.

        Returns:
            Tuple: (values matrix, labels list, sessions list)
        """
        valid_data = self.validate_data(data)
        sids = valid_data.filter_sids(select_conds, sids=self.subjects2sids(subjects))

        return (valid_data.get_subjects_values_by_cols(sids, columns_list, demean_flags=demean_flags, ndecim=ndecim),
                sids.labels,
                sids.sessions)
    def get_subjects_dataframe(self, subjects: SubjectsList, columns: List[str],
                                   data: SubjectsData = None) -> pandas.DataFrame:
            """
            Extract a DataFrame from SubjectsList with specified columns.

            Args:
                subjects: SubjectsList of subjects to include.
                columns: Column names to include in the result.
                data: optional SubjectsData override. If None, uses self.data.

            Returns:
                pandas.DataFrame: Filtered DataFrame with subjects' rows and specified columns.
            """
            valid_data = self.validate_data(data)
            sids = self.subjects2sids(subjects)
            return valid_data.select_df(sids, columns)

    def get_subjects_values_by_col(self, subjects: SubjectsList, column: str,
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
        sids = valid_data.filter_sids(select_conds, sids=self.subjects2sids(subjects))

        return (valid_data.get_subjects_column(sids, column, sort=sort, demean=demean_flag, ndecim=ndecim),
                sids.labels,
                sids.sessions)

    def validate_subjects(self, subjs: SubjectsList | None = None) -> SubjectsList:
        """
        Validates and returns a SubjectsList.

        If subjs is None, returns self.subjects_labels (all loaded subjects).
        Otherwise, validates that input is a non-empty list of Subject instances.

        Parameters
        ----------
        subjs : SubjectsList, optional
            List of subjects to validate.

        Returns
        -------
        SubjectsList
            Validated list of subjects.

        Raises
        ------
        SubjectExistException
            If subjs is None and no subjects loaded, or if subjs is not a valid Subject list.
        """
        if subjs is None:
            # Fallback: return all subjects loaded in data
            all_subjects = SubjectsList()
            for label in self.subjects_labels:
                for sess_id in self.data.get_subject_available_sessions(label, error_if_empty=False):
                    all_subjects.append(Subject(label, self, sess_id))
            if len(all_subjects) == 0:
                raise SubjectExistException("validate_subjects",
                    "given subjs param is None and project has no loaded subjects")
            return all_subjects
        else:
            if is_list_of(subjs, Subject) and len(subjs) > 0:
                return subjs
            else:
                raise SubjectExistException("validate_subjects",
                    f"given subjs param is not a valid Subject list or is empty: {type(subjs)}")

    def are_subjects_valid(self, subjects: SubjectsList) -> bool:
        for subj in subjects:
            if not subj.exist:
                return False
        return True

    # endregion

    #region SIDS

    def subjects2sids(self, subjects: SubjectsList = None) -> SIDList:
        """
        Converts a SubjectsList to a SIDList.
        
        Each Subject's sid is already assigned to its own project.data at init,
        so this method uses subj.sid directly rather than calling self.data.get_sid().
        This enables cross-project analysis: soggetti from different projects each
        resolve in their own excel.

        Parameters
        ----------
        subjects : SubjectsList, optional
            List of subjects to convert. If None, uses validate_subjects().

        Returns
        -------
        SIDList
            Corresponding SIDList for data queries.
        """
        subjects = self.validate_subjects(subjects)
        sids = [subj.sid for subj in subjects]
        return SIDList(sids)

    def sids2subjects(self, sids: SIDList = None) -> SubjectsList:
        """
        Converts a SIDList to a SubjectsList.

        Parameters
        ----------
        sids : SIDList, optional
            List of subject identifiers to convert.

        Returns
        -------
        SubjectsList
            List of Subject instances corresponding to the given SIDs.
        """
        if sids is None:
            sids = self.data.subjects
        return SubjectsList([Subject(sid.label, self, sid.session) for sid in sids])

    # endregion
