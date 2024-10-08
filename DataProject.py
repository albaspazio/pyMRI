from __future__ import annotations

import json
import os
from typing import List, Any, Tuple

from data.SIDList import SIDList
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from myutility.exceptions import SubjectListException, DataFileException
from myutility.list import is_list_of


class DataProject:
    """
    A class for managing data and analysis scripts for a project composed by a single dataframe
    It only loads that excel and load its subjects once at startup.
    Exposes some convenient project folder and wrap some calls to its data:SubjectsData property
    From Project, it uses the concept of subjects_lists.json in order to may process the same subjects groups easily

    Args:
        proj_dir (str): path to project dir.
        data : str | SubjectsData, optional. The path to the data file, by default "data.dat" or a SubjectsData instance.
                                             If not specified, the data file will be loaded from the default location.

    Attributes:
        proj_dir (str): The directory containing the project's scripts.
        input_data_dir (str): The directory containing the project's input data.
        output_data_dir (str): The directory containing the project's output data.
        #r_dir (str): The directory containing the project's R scripts.
        #stats_input (str): The directory containing the project's input data for R scripts.
        #stats_output (str): The directory containing the project's output data for R scripts.
        subjects_lists_file (str): The path to the file containing the project's subject lists.
        subjects_labels (list): A list of subject labels associated with the project.
        nsubj (int): The number of subjects associated with the project.
        data (SubjectsData): A SubjectsData instance containing the project's data.
    """
    data:SubjectsData = None

    def __init__(self, proj_dir:str, data:str|SubjectsData="data.xlsx"):

        self.proj_dir           = proj_dir

        self.input_data_dir     = os.path.join(self.proj_dir, "input_data")
        self.output_data_dir    = os.path.join(self.proj_dir, "output_data")
        # self.r_dir              = os.path.join(self.proj_dir, "r")
        # self.stats_input        = os.path.join(self.r_dir, "indata")
        # self.stats_output       = os.path.join(self.r_dir, "results")

        self.subjects_lists_file    = os.path.join(self.proj_dir, "subjects_lists.json")

        os.makedirs(self.proj_dir,       exist_ok=True)
        os.makedirs(self.input_data_dir, exist_ok=True)
        os.makedirs(self.output_data_dir,exist_ok=True)
        # os.makedirs(self.r_dir,          exist_ok=True)
        # os.makedirs(self.stats_input,    exist_ok=True)
        # os.makedirs(self.stats_output,   exist_ok=True)

        self.nsubj              = 0

        # load all available subjects list into self.subjects_lists
        with open(self.subjects_lists_file) as json_file:
            subjects            = json.load(json_file)
            self.subjects_lists = subjects["subjects"]

        self.data = self.load_data(data)

    @property
    def subjects_labels(self) -> List[str]:
        """
        Returns the list of subject labels taken from self.data if is not None, otherwise returns an empty list.
        Ignore the concept of session. is the union of all subjects values (should practically coincide with subjects @ sess=1)

        Returns:
            List[str]: A list of strings representing the labels of the subjects contained in the dataframe.
        """
        if self.data is not None:
            return self.data.subjects_labels
        else:
            return []

    # load a data_file if exist
    def load_data(self, data:str|SubjectsData) -> SubjectsData|None:
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
                    return d
                else:
                    return SubjectsData()
            else:
                return None

        elif isinstance(data, SubjectsData):
            return data
        else:
            raise TypeError("ERROR in Project.load_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

    def validate_data(self, data:SubjectsData | str | None = None) -> SubjectsData:
        """
        Validate and return the SubjectsData object based on the provided data.
        If data is None, return the existing data if available. If data is a SubjectsData instance, return it.
        If data is a string, load the data from the file path and return the SubjectsData object.

        Parameters:
            data (SubjectsData | str | None): The data to validate and return.

        Returns:
            SubjectsData: The validated SubjectsData object.

        Raises:
            DataFileException: If the given data is not a SubjectsData instance, a string path to a data file, or if the file path is invalid.
        """
        if data is None:
            if self.data.num > 0:
                return self.data
            else:
                raise DataFileException("ERROR in Project.validate_data: given data param (" + str(data) + ") is None and project's data is not loaded")
        else:
            if isinstance(data, SubjectsData):
                return data
            elif isinstance(data, str):
                if os.path.exists(data):
                    return SubjectsData(data)
                else:
                    raise DataFileException("ERROR in Project.validate_data: given data param (" + str(data) + ") is a string that does not point to a valid file to load")
            else:
                raise DataFileException("ERROR in Project.validate_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

    def get_subjects_labels(self, grlab_subjlabs_subjs: str | List[str]=None) -> List[str]:
        """
        get a list of subject labels eventually accessing the lists defined in subjects_lists.json

        Args:
            grlab_subjlabs_subjs (str or list, optional): The group label or subject labels. If not specified, the loaded subject labels will be returned.

        Returns:
            list: The subject labels.

        Raises:
            SubjectListException: If the group label is not valid and must_exist is True.

        """

        if grlab_subjlabs_subjs is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("Error in get_subjects_labels", "given grlab_subjlabs_subjs is None and no group is loaded")
            else:
                return self.subjects_labels         # if != form 0, they have been already validated

        elif isinstance(grlab_subjlabs_subjs, str):  # must be a group_label and have its associated subjects list
            for grp in self.subjects_lists:
                if grp["label"] == grlab_subjlabs_subjs:
                    return grp["list"]
            raise SubjectListException("Error in get_subjects_labels", "given group_label (" + grlab_subjlabs_subjs + ") does not exist in subjects_lists")

        elif is_list_of(grlab_subjlabs_subjs, str):
            return grlab_subjlabs_subjs   # [string]

        # elif is_list_of(grlab_subjlabs_subjs, Subject):
        #     return [s.label for s in grlab_subjlabs_subjs]   # [Subject]
        else:
            # grlab_subjlabs_subjs does not belong to expected types
            raise SubjectListException("Error in get_subjects_labels", "the given grlab_subjlabs_subjs param is not a valid param (None, string  or string list), is: " + str(grlab_subjlabs_subjs))

    # ==================================================================================================================
    #region (subj_labels/group label | column(s) | sess_ids) -> List[dict] | Tuple[List[List[Any]], List[str], List[int]]  (also add sids.labels, sids.sess_ids)

    def get_subjects_datarows(self, grlab_subjlabs_subjs: str | List[str], sess_ids: List[int] | None = None, data:SubjectsData=None) -> List[dict]:
        """
        Get subjects dict data by their labels/sessions.
        if sess_ids is not specified, returns all available sessions for each given subj_labels
        otherwise returns only given sessions

        Args:
            subj_labels (list): The labels of the subjects.
            sess_ids:List[int] | None : the list of requested sessions

        Returns:
            List[dict]: The subject data.

        Raises:
            SubjectListException: If a subject does not exist and must_exist is True.
            DataFileException: if selected subjects does not have a row in the dataframe
        """
        # sanity checks
        if sess_ids is not None:
            if is_list_of(sess_ids, int) is False:
                raise DataFileException("Error in DataProject.get_subjectsdict_by_labels: given sessions is not a list of int")

        valid_data  = self.validate_data(data)
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs)
        sids        = valid_data.filter_subjects(subj_labels, sess_ids)

        return self.data.get_sids_dict(sids)

    def get_subjects_values_by_cols(self, grlab_subjlabs_subjs: str | List[str], columns_list:List[str], sess_ids: List[int] | None=None,
                                    data:SubjectsData=None, select_conds:List[FilterValues]=None, demean_flags:List[bool]=None) -> Tuple[List[List[Any]], List[str], List[int]]:
        """
        Get the values of the requested columns for a specific session of given subjects.

        Args:
            grlab_subjlabs_subjs (str or list): The group label or subject labels.
            columns_list (list): A list of column names.
            sess_ids (List[int], optional): The session ID of the subjects to load. Defaults to 1.
            data (SubjectsData, optional): A SubjectsData instance containing the data. If not specified, the project's data will be used.
            sort (bool, optional): Whether to sort the output by subject. Defaults to False.
            demean_flags (list, optional): A list of booleans indicating whether to demean the values for each column. If not specified, all columns will be demeaned.

        Returns:
            tuple: a tuple containing a list of: values, labels, sessions

        Raises:
            SubjectListException: If a subject does not exist and must_exist is True.
            DataFileException: if selected subjects does not have a row in the dataframe
        """
        # sanity checks
        if sess_ids is not None:
            if is_list_of(sess_ids, int) is False:
                raise DataFileException("Error in DataProject.get_subjectsdict_by_labels: given sessions is not a list of int")

        valid_data  = self.validate_data(data)
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs)
        sids        = valid_data.filter_subjects(subj_labels, sess_ids, conditions=select_conds)

        return (valid_data.get_subjects_values_by_cols(sids, columns_list, demean_flags=demean_flags),
                sids.labels,
                sids.sessions)

    def get_filtered_column(self, grlab_subjlabs_subjs:str|List[str], column:str, sess_ids:List[int]|None=None,
                            data:str|SubjectsData=None, select_conds:List[FilterValues]=None, sort:bool=False, demean_flag:bool=False, ndecim:int=4) -> Tuple[List[Any], List[str], List[int]]:
        """
        Returns a list of values and a list of labels for a given column, filtered by given conditions.

        Parameters:
            grlab_subjlabs_subjs (str or List[str]): The group label or a list of subjects' label/instances.
            column (str): The column label.
            data (SubjectsData or str, optional): The data to use. If None, the project's data is used. If a string, the string is interpreted as a path to a data file to load.
            sort (bool, optional): If True, sort the output by subject.
            sess_id (int, optional): The session ID.
            select_conds (list, optional): A list of filter conditions.
            demean_flag:bool
            ndecim:int

        Returns:
            tuple: A tuple containing a list of: values, labels, sessions

        Raises:
            SubjectListException: If a subject does not exist and must_exist is True.
            DataFileException: If the given data is neither a SubjectsData instance nor a string path to a data file.
        """

        # sanity checks
        if sess_ids is not None:
            if is_list_of(sess_ids, int) is False:
                raise DataFileException("Error in DataProject.get_subjectsdict_by_labels: given sessions is not a list of int")

        valid_data  = self.validate_data(data)
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs)
        sids        = valid_data.filter_subjects(subj_labels, sess_ids, conditions=select_conds)

        return (valid_data.get_subjects_column(sids, column, sort=sort, demean=demean_flag, ndecim=ndecim),
                sids.labels,
                sids.sessions)

    # endregion ==================================================================================================================
