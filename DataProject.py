import json
import os
from data.SubjectsDataDict import SubjectsDataDict
from utility.exceptions import SubjectListException


class DataProject:

    def __init__(self, name, globaldata, data="data.dat"):

        self.name               = name

        self.script_dir         = os.path.join(globaldata.project_scripts_dir, self.name)
        self.r_dir              = os.path.join(self.script_dir, "r")
        self.input_data_dir     = os.path.join(self.script_dir, "input_data")
        self.stats_input        = os.path.join(self.r_dir, "indata")
        self.stats_output       = os.path.join(self.r_dir, "results")

        os.makedirs(self.script_dir,    exist_ok=True)
        os.makedirs(self.r_dir,         exist_ok=True)
        os.makedirs(self.input_data_dir,exist_ok=True)
        os.makedirs(self.stats_input,   exist_ok=True)
        os.makedirs(self.stats_output,  exist_ok=True)

        self.globaldata = globaldata

        self.subjects           = []
        self.subjects_labels    = []
        self.nsubj              = 0

        # load all available subjects list into self.subjects_lists
        with open(os.path.join(self.script_dir, "subjects_lists.json")) as json_file:
            subjects            = json.load(json_file)
            self.subjects_lists = subjects["subjects"]

        # load subjects data if possible
        self.data_file = ""
        self.data = SubjectsDataDict()

        self.load_data(data)

    # load a data_file if exist
    def load_data(self, data_file):

        df = ""
        if os.path.exists(data_file):
            df = data_file
        elif os.path.exists(os.path.join(self.script_dir, data_file)):
            df = os.path.join(self.script_dir, data_file)

        if df != "":
            d = SubjectsDataDict(df)
            if d.num > 0:
                self.data       = d
                self.data_file  = df

        return self.data


    # if must_exist=true:   loads in self.subjects, a list of subjects instances associated to a valid grouplabel or a subjlabels list
    # if must_exist=false:  only create
    # returns this list
    def load_subjects(self, group_label, sess_id=1, must_exist=True):

        try:
            subjects           = self.get_subjects(group_label, sess_id, must_exist)

        except SubjectListException as e:
            raise SubjectListException("load_subjects", e.param)    # send whether the group label was not present
                                                                    # or one of the subjects was not valid

        if must_exist:
            self.subjects           = subjects
            self.subjects_labels    = [subj.label for subj in self.subjects]
            self.nsubj              = len(self.subjects)

        return subjects

    # get a deepcopy of subject with given label
    def get_subject_by_label(self, subj_label, sess=1):
        res = self.data.get_subjects([subj_label])
        if len(res) == 0:
            return None
        else:
            return res[0]


    # ==================================================================================================================
    #region GET SUBJECTS' LABELS or INSTANCES
    # ==================================================================================================================
    # GROUP_LABEL or SUBLABELS LIST => VALID SUBJECT INSTANCES LIST
    # create and returns a list of valid subjects instances given a grouplabel or a subjlabels list
    def get_subjects(self, group_or_subjlabels, sess_id=1, must_exist=True):
        valid_subj_labels = self.get_subjects_labels(group_or_subjlabels, sess_id, must_exist)
        return self.__get_subjects_from_labels(valid_subj_labels, sess_id, must_exist)

    # GROUP_LABEL or SUBLABELS LIST or SUBJINSTANCES LIST => VALID SUBLABELS LIST
    # returns [labels]
    def get_subjects_labels(self, grouplabel_or_subjlist=None, sess_id=1, must_exist=True):
        if grouplabel_or_subjlist is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("get_subjects_labels", "given grouplabel_or_subjlist is None and no group is loaded")
            else:
                return self.subjects_labels         # if != form 0, they have been already validated
        elif isinstance(grouplabel_or_subjlist, str):  # must be a group_label and have its associated subjects list
            return self.__get_valid_subjlabels_from_group(grouplabel_or_subjlist, sess_id, must_exist)

        elif isinstance(grouplabel_or_subjlist, list):
            if isinstance(grouplabel_or_subjlist[0], str) is True:
                # list of subjects' names
                if must_exist:
                    return self.__get_valid_subjlabels(grouplabel_or_subjlist, sess_id)
                else:
                    return grouplabel_or_subjlist   # [string]
            else:
                raise SubjectListException("get_subjects_labels", "the given grouplabel_or_subjlist param is not a string list, first value is: " + str(grouplabel_or_subjlist[0]))
        else:
            raise SubjectListException("get_subjects_labels", "the given grouplabel_or_subjlist param is not a valid param (None, string  or string list), is: " + str(grouplabel_or_subjlist))
    #endregion

    # =========================================================================
    #region PRIVATE VALIDATION ROUTINES
    # =========================================================================

    # GROUP_LAB => VALID SUBJLABELS LIST or []
    # check whether all subjects belonging to the given group_label are valid
    # returns such subject list if all valid
    def __get_valid_subjlabels_from_group(self, group_label, must_exist=True):
        for grp in self.subjects_lists:
            if grp["label"] == group_label:
                if must_exist:
                    return self.__get_valid_subjlabels(grp["list"])
                else:
                    return grp["list"]
        raise SubjectListException("__get_valid_subjlabels_from_group", "given group_label does not exist in subjects_lists")

    # SUBJLABELS LIST => VALID SUBJLABELS LIST or []
    # check whether all subjects listed in subj_labels are valid
    # returns given list if all valid
    def __get_valid_subjlabels(self, subj_labels, sess_id=1):
        for lab in subj_labels:
            if not self.data.exist(lab):
                raise SubjectListException("__get_valid_subjlabels", "given subject (" + lab + ") does not exist in data file")
        return subj_labels

    # SUBJLABELS LIST => VALID SUBJS data or []
    # create and returns a list of valid subjects data columns given a subjlabels list
    def __get_subjects_from_labels(self, subj_labels):
        return self.data.get_subjects(subj_labels)

    #endregion

    # ==================================================================================================================
    #region GET SUBJECTS DATA
    # ==================================================================================================================
    # returns a matrix (values x subjects) containing values of the requested columns of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_columns(self, columns_list, grouplabel_or_subjlist, data=None, sort=False, sess_id=1):

        subj_list  = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_columns(columns_list, subj_list, sort=sort)
        else:
            return None

    # returns a tuple with two vectors[nsubj] (filtered by subj labels) of the requested column
    # - [values]
    # - [labels]
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column(self, column, grouplabel_or_subjlist, data=None, sort=False, sess_id=1):

        subj_list   = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column(column, subj_list, sort=sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column_by_value(self, column, value, operation="=", grouplabel_or_subjlist=None, data=None, sort=False, sess_id=1):

        subj_list   = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_by_value(column, value, operation, subj_list, sort=sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    # def get_filtered_column_by_value(self, column, value, operation="=", subjects_label=None, data=None):
    def get_filtered_subj_dict_column_within_values(self, column, value1, value2, operation="<>", grouplabel_or_subjlist=None,
                                                    data=None, sort=False, sess_id=1):

        subj_list   = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_within_values(column, value1, value2, operation, subj_list, sort=sort)
        else:
            return None

    # validate data dictionary. if param is none -> takes it from self.data
    #                           otherwise try to load it
    def validate_data(self, data=None) -> SubjectsDataDict:

        if data is None:
            if bool(self.data):
                return self.data
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is None and project's data is not loaded")
        else:
            if isinstance(data, SubjectsDataDict):
                return data
            elif isinstance(data, str):
                if os.path.exists(data):
                    return SubjectsDataDict(data)
                else:
                    raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is a string that does not point to a valid file to load")
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is neither a SubjectsDataDict nor a string")

    #endregion ==================================================================================================================
