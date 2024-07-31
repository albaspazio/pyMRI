from __future__ import annotations

import json
import os
from typing import List, Any

from Global import Global
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from utility.exceptions import SubjectListException


class DataProject:

    """
    A class for managing data and analysis scripts for a single project.

    Args:
        name (str): The name of the project.
        globaldata (GlobalData): A GlobalData instance containing global project settings and data.
        data : str | SubjectsData, optional. The path to the data file, by default "data.dat" or a SubjectsData instance.
                                             If not specified, the data file will be loaded from the default location.

    Attributes:
        name (str): The name of the project.
        globaldata (GlobalData): A GlobalData instance containing global project settings and data.
        proj_dir (str): The directory containing the project's scripts.
        r_dir (str): The directory containing the project's R scripts.
        input_data_dir (str): The directory containing the project's input data.
        output_data_dir (str): The directory containing the project's output data.
        stats_input (str): The directory containing the project's input data for R scripts.
        stats_output (str): The directory containing the project's output data for R scripts.
        subjects_lists_file (str): The path to the file containing the project's subject lists.
        subjects (list): A list of Subject instances associated with the project.
        subjects_labels (list): A list of subject labels associated with the project.
        nsubj (int): The number of subjects associated with the project.
        data_file (str): The path to the data file for the project.
        data (SubjectsData): A SubjectsData instance containing the project's data.
    """
    def __init__(self, name:str, proj_dir:str, data:str|SubjectsData="data.xlsx"):

        self.name               = name

        # self.proj_dir         = os.path.join(globaldata.project_scripts_dir, self.name)
        self.proj_dir         = proj_dir
        self.r_dir              = os.path.join(self.proj_dir, "r")
        self.input_data_dir     = os.path.join(self.proj_dir, "input_data")
        self.output_data_dir    = os.path.join(self.proj_dir, "output_data")
        self.stats_input        = os.path.join(self.r_dir, "indata")
        self.stats_output       = os.path.join(self.r_dir, "results")

        self.subjects_lists_file    = os.path.join(self.proj_dir, "subjects_lists.json")

        os.makedirs(self.proj_dir,       exist_ok=True)
        os.makedirs(self.r_dir,          exist_ok=True)
        os.makedirs(self.input_data_dir, exist_ok=True)
        os.makedirs(self.output_data_dir,exist_ok=True)
        os.makedirs(self.stats_input,    exist_ok=True)
        os.makedirs(self.stats_output,   exist_ok=True)

        # self.globaldata = globaldata

        self.subjects           = []
        self.subjects_labels    = []
        self.nsubj              = 0

        # load all available subjects list into self.subjects_lists
        with open(self.subjects_lists_file) as json_file:
            subjects            = json.load(json_file)
            self.subjects_lists = subjects["subjects"]

        # load subjects data if possible
        self.data_file = ""
        self.data = SubjectsData()

        self.load_data(data)

    # load a data_file if exist
    def load_data(self, data:str|SubjectsData) -> SubjectsData:
        """
        Load a data file for the project.

        Args:
            data (str, optional): The path to the data file. If not specified, the default data file for the project will be loaded.

        Returns:
            SubjectsData: The loaded data file.

        Raises:
            TypeError: if given data is neither a string nor a SubjectsData instance.
        """
        if isinstance(data, str):
            data_file = ""
            if os.path.exists(data):
                data_file = data
            elif os.path.isfile(os.path.join(self.proj_dir, data)):
                data_file = os.path.join(self.proj_dir, data)

            if data_file != "":
                d = SubjectsData(data_file)
                if d.num > 0:
                    self.data       = d
                    self.data_file  = data_file
        elif isinstance(data, SubjectsData):
            self.data       = data
        else:
            raise TypeError("ERROR in Project.load_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

        return self.data

    # if must_exist=true:   loads in self.subjects, a list of subjects instances associated to a valid grouplabel or a subjlabels list
    # if must_exist=false:  only create
    # returns this list
    def load_subjects(self, group_label:str, sess_id:int=1, must_exist:bool=True):
        """
        Load subjects for the project.

        Args:
            group_label (str): The label of the subject group.
            sess_id (int, optional): The session ID of the subjects to load. Defaults to 1.
            must_exist (bool, optional): Whether to raise an exception if a subject does not exist. Defaults to True.

        Returns:
            list: The loaded subjects.

        Raises:
            SubjectListException: If the group label is not valid or a subject does not exist and must_exist is True.

        """
        try:
            subjects           = self.get_subjects(group_label, must_exist)

        except SubjectListException as e:
            raise SubjectListException("load_subjects", e.param)    # send whether the group label was not present
                                                                    # or one of the subjects was not valid

        if must_exist:
            self.subjects           = subjects
            self.subjects_labels    = [subj.label for subj in self.subjects]
            self.nsubj              = len(self.subjects)

        return subjects

    # ==================================================================================================================
    # region GET SUBJECTS' LABELS or INSTANCES
    # ==================================================================================================================
    # get a deepcopy of subject with given label
    def get_subject_by_label(self, subj_label:str) -> dict:
        """
        Get a subject by its label.

        Args:
            subj_label (str): The label of the subject.

        Returns:
            dict: The subject data.

        """
        return self.data.get_subject(subj_label)

    # SUBJLABELS LIST => VALID SUBJS data or []
    # create and returns a list of valid subjects data columns given a subjlabels list
    def get_subjects_by_labels(self, subj_labels:List[str]) -> List[dict]:
        """
        Get subjects by their labels.

        Args:
            subj_labels (list): The labels of the subjects.

        Returns:
            List[dict]: The subject data.

        """
        return self.data.get_subjects(subj_labels)

    # GROUP_LABEL or SUBLABELS LIST => VALID SUBJECT INSTANCES LIST
    # create and returns a list of valid subjects instances given a grouplabel or a subjlabels list
    def get_subjects(self, group_or_subjlabels:str | List[str], must_exist:bool=True):
        """
        Get subjects.

        Args:
            group_or_subjlabels (str or list): The group label or subject labels.
            must_exist (bool, optional): Whether to raise an exception if a subject does not exist. Defaults to True.

        Returns:
            list: The subjects.

        Raises:
            SubjectListException: If a subject does not exist and must_exist is True.

        """
        valid_subj_labels = self.get_subjects_labels(group_or_subjlabels, must_exist)
        return self.get_subjects_by_labels(valid_subj_labels)

    # GROUP_LABEL or SUBLABELS LIST or SUBJINSTANCES LIST => VALID SUBLABELS LIST
    # returns [labels]
    def get_subjects_labels(self, grlab_subjlabs_subjs:str|List[str]=None, must_exist:bool=True) -> List[str]:
        """
        Get subject labels.

        Args:
            grlab_subjlabs_subjs (str or list, optional): The group label or subject labels. If not specified, the loaded subject labels will be returned.
            must_exist (bool, optional): Whether to raise an exception if a subject does not exist. Defaults to True.

        Returns:
            list: The subject labels.

        Raises:
            SubjectListException: If the group label is not valid and must_exist is True.

        """
        if grlab_subjlabs_subjs is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("get_subjects_labels", "given grlab_subjlabs_subjs is None and no group is loaded")
            else:
                return self.subjects_labels         # if != form 0, they have been already validated
        elif isinstance(grlab_subjlabs_subjs, str):  # must be a group_label and have its associated subjects list
            return self.__get_valid_subjlabels_from_group(grlab_subjlabs_subjs, must_exist)

        elif isinstance(grlab_subjlabs_subjs, list):
            if isinstance(grlab_subjlabs_subjs[0], str) is True:
                # list of subjects' names
                if must_exist:
                    return self.__get_valid_subjlabels(grlab_subjlabs_subjs)
                else:
                    return grlab_subjlabs_subjs   # [string]
            else:
                raise SubjectListException("get_subjects_labels", "the given grlab_subjlabs_subjs param is not a string list, first value is: " + str(grlab_subjlabs_subjs[0]))
        else:
            raise SubjectListException("get_subjects_labels", "the given grlab_subjlabs_subjs param is not a valid param (None, string  or string list), is: " + str(grlab_subjlabs_subjs))
    #endregion

    # =========================================================================
    #region PRIVATE VALIDATION ROUTINES
    # =========================================================================

    # GROUP_LAB => VALID SUBJLABELS LIST or []
    # check whether all subjects belonging to the given group_label are valid
    # returns such subject list if all valid
    def __get_valid_subjlabels_from_group(self, group_label:str, must_exist:bool=True):
        """
        Get valid subject labels from a group label.

        Args:
            group_label (str): The group label.
            must_exist (bool, optional): Whether to raise an exception if a subject does not exist. Defaults to True.

        Returns:
            List[str]: The valid subject labels.

        Raises:
            SubjectListException: If the group label is not valid and must_exist is True.

        """
        for grp in self.subjects_lists:
            if grp["label"] == group_label:
                if must_exist:
                    return self.__get_valid_subjlabels(grp["list"])
                else:
                    return grp["list"]
        raise SubjectListException("__get_valid_subjlabels_from_group", "given group_label does not exist in subjects_lists")

    # SUBJLABELS LIST => VALID SUBJLABELS LIST or []
    # check whether all subjects listed in subjects are valid
    # returns given list if all valid
    def __get_valid_subjlabels(self, subj_labels:List[str], sessions:List[int]=None) -> List[str]:
        """
        Check whether all subjects listed in subjects are valid.

        Args:
            subj_labels (List[str]): A list of subject labels.
            sessions (List[int], optional): A list of session IDs. If not specified, all sessions will be considered.

        Returns:
            List[str]: The valid subject labels.

        Raises:
            SubjectListException: If a subject does not exist in the data file.

        """
        if sessions is None:
            sessions = [1 for s in subj_labels]

        for id,lab in enumerate(subj_labels):
            if self.data.get_subj_session(lab, sessions[id]) is None:
                raise SubjectListException("__get_valid_subjlabels", "given subject (" + lab + " | " + str(sessions[id]) + ") does not exist in data file")
        return subj_labels
    #endregion

    # ==================================================================================================================
    #region GET SUBJECTS DATA
    # returns a matrix (values x subjects) containing values of the requested columns of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_subjects_values_by_cols(self, grlab_subjlabs_subjs:str|List[str], columns_list:List[str], data:SubjectsData=None, sort:bool=False,
                                    demean_flags:List[bool]=None, sess_id:int=1, must_exist:bool=False) -> List[List[Any]]:
        """
        Get the values of the requested columns for the given subjects.

        Args:
            grlab_subjlabs_subjs (str or list): The group label or subject labels.
            columns_list (list): A list of column names.
            data (SubjectsData, optional): A SubjectsData instance containing the data. If not specified, the project's data will be used.
            sort (bool, optional): Whether to sort the output by subject. Defaults to False.
            demean_flags (list, optional): A list of booleans indicating whether to demean the values for each column. If not specified, all columns will be demeaned.
            sess_id (int, optional): The session ID of the subjects to load. Defaults to 1.
            must_exist (bool, optional): Whether to raise an exception if a subject does not exist. Defaults to False.

        Returns:
            list: A list of subject values. Each element in the list is a list of values for a single subject.

        Raises:
            SubjectListException: If a subject does not exist and must_exist is True.
        """
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs, sess_id, must_exist)
        valid_data = self.validate_data(data)

        sessions = [sess_id for s in subj_labels]  # 1-fill

        subjsSD_list = valid_data.filter_subjects(subj_labels, sessions)

        if valid_data is not None:
            return valid_data.get_subjects_values_by_cols(subjsSD_list, columns_list, demean_flags=demean_flags)
        else:
            return []
    # endregion ==================================================================================================================

    # ==================================================================================================================
    #region returns a tuple with two vectors[nsubj] (filtered by subj labels) of the requested column

    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column(self, grlab_subjlabs_subjs:str|List[str], column:str, data:SubjectsData=None, sort:bool=False, select_conds:List[FilterValues]=None):

        subj_list   = self.get_subjects_labels(grlab_subjlabs_subjs)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column(subj_list, column, sort=sort, select_conds=select_conds)
        else:
            return None

    # endregion ==================================================================================================================

    # ==================================================================================================================
    # region ACCESSORY
    # validate data dictionary. if param is none -> takes it from self.data
    #                           otherwise try to load it
    def validate_data(self, data=None) -> SubjectsData:

        if data is None:
            if self.data.num > 0:
                return self.data
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is None and project's data is not loaded")
        else:
            if isinstance(data, SubjectsData):
                return data
            elif isinstance(data, str):
                if os.path.exists(data):
                    return SubjectsData(data)
                else:
                    raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is a string that does not point to a valid file to load")
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

    def add_data_column(self, colname, labels, values):
        self.data.add_column(colname, values, labels)

    #endregion ==================================================================================================================
