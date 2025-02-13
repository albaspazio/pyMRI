from __future__ import annotations

import os
from distutils.file_util import copy_file
from typing import List, Any

from Global import Global
from Project import Project
from data.SubjectsData import SubjectsData
from group.spm_utilities import Regressor, Covariate, Nuisance
from myutility.exceptions import SubjectListException
from myutility.list import is_list_of

# create factorial designs, multiple regressions, t-test
from myutility.myfsl.utils.run import rrun
from myutility.fileutilities import remove_ext, append_text_file, write_text_file
from subject.Subject import Subject


class ConnModels:
    """
    This class provides methods for creating and managing the connection models used in the CONN tool.

    Args:
        proj (Project): The Project object that this class is associated with.

    Attributes:
        subjects_list (list): A list of Subject objects that are part of the current project.
        working_dir (str): The directory where temporary files are stored.
        project (Project): The ConnProject object that this class is associated with.
        globaldata (GlobalData): The GlobalData object that is associated with the current project.
        string (str): A string that is used to compose the connection model files.
    """

    def __init__(self, proj:Project):
        self.subjects_list      = None
        self.working_dir        = ""
        self.project:Project    = proj
        self.globaldata:Global  = self.project.globaldata
        self.string             = ""  # used to compose models override

    def create_regressors_file(self, odp:str, regressors:List[Regressor], groups_instances:List[List[Subject]], group_labels:List[str]=None, ofn:str="conn_covs",
                                data:str|SubjectsData=None, ofn_postfix:str="", subj_must_exist:bool=False):
        """
        This method creates a regressors file that can be used with the Conn tool. The regressors file contains
        the regressors and covariates that will be used in the analysis.

        Args:
            odp (str): The output directory path where the regressors file will be created.
            regressors (list): A list of regressors that will be included in the analysis. The regressors can be
                covariates or nuisances.
            groups_instances (List[List[Subject]]): A list of group labels that will be used to create the factorial design. Each group
                label will be used as an explanatory variable (EV).
            group_labels:List[str]: used to name output files
            ofn (str, optional): The name of the regressors file. The default value is "conn_covs".
            data (str|SubjectsData, optional): The path to the data file that contains the subject data or
                a SubjectsData. If not specified, the data (file) associated with the current project will be used.
            ofn_postfix (str, optional): A postfix that will be added to the name of the regressors file. The default
                value is an empty string.
            subj_must_exist (bool, optional): A boolean value that indicates whether the subjects in the group labels
                must exist in the data file. If set to False, subjects that do not exist in the data file will be
                ignored. The default value is True.
        """
        # ------------------------------------------------------------------------------------
        # sanity checks
        if not is_list_of(groups_instances[0], Subject):
            raise SubjectListException("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file: given subjects is not a list of Subject", str(groups_instances))

        if bool(regressors):
            data = self.project.validate_data(data)  # SubjectsData
            data.validate_covs(regressors)
        else:
            data = None

        ngroups = len(groups_instances)  # number of groups in the design. each group will have its regressor (EV).
        if ngroups > 3:
            raise Exception("Error in ConnModels.create_regressors_file_ofsubset, no more than three groups are supported")

        # ----------------------------------------------------------------------------------
        # get subjects values
        # create a list with all Subject instances
        subjs_instances = []
        for subjs in groups_instances:
            subjs_instances = subjs_instances + subjs

        # ------------------------------------------------------------------------------------
        # divide regressors in covariates and nuisances
        covs_label = []
        nuis_label = []
        for regr in regressors:
            if isinstance(regr, Covariate):
                covs_label.append(regr.name)
            elif isinstance(regr, Nuisance):
                nuis_label.append(regr.name)
        # ncovs = len(covs_label)
        # nnuis = len(nuis_label)

        covs_values = self.project.get_subjects_values_by_cols(subjs_instances, covs_label)[0]
        nuis_values = self.project.get_subjects_values_by_cols(subjs_instances, nuis_label)[0]

        # ------------------------------------------------------------------------------------
        # define output filename...add regressors/nuis to given ofn containing groups info
        output_covsfile = os.path.join(odp, ofn + ofn_postfix)
        os.makedirs(odp, exist_ok=True)

        # ------------------------------------------------------------------------------------
        # add file header with regressors labels
        self.string = ""
        for gr in group_labels:
            self.string = self.string + gr + " "
        for nuis in nuis_label:
            self.string = self.string + nuis + " "
        for covs in covs_label:
            str_covs = ""
            for i in range(ngroups):
                str_covs = str_covs + covs + "_" + str(i + 1) + " "
            self.string = self.string + str_covs

        self.string = self.string[:-1]  # removes last char
        self.__addline2string()

        # ------------------------------------------------------------------------------------
        # prepare groups' regressors string
        if ngroups == 1:
            groups_strings = ["1"]
        elif ngroups == 2:
            groups_strings = ["1 0", "0 1"]
        elif ngroups == 3:
            groups_strings = ["1 0 0", "0 1 0", "0 0 1"]
        elif ngroups == 4:
            groups_strings = ["1 0 0 0", "0 1 0 0", "0 0 1 0", "0 0 0 1"]
        else:
            print("cannot manage more than 4 groups")
            return

        # ------------------------------------------------------------------------------------
        # write file
        curr_subjid = 0
        for gr_id, gr in enumerate(groups_instances):
            for _ in groups_instances[gr_id]:
                string = groups_strings[gr_id]

                for nuis_id, _ in enumerate(nuis_values):
                    string = string + " " + str(nuis_values[nuis_id][curr_subjid])

                for cov_id, voc in enumerate(covs_values):
                    cov_value = str(covs_values[cov_id][curr_subjid])
                    covsvalue = ["0" for _ in range(ngroups)]
                    covsvalue[gr_id] = cov_value
                    value_string = " ".join(covsvalue)
                    string = string + " " + value_string

                self.__addline2string(string)
                curr_subjid = curr_subjid + 1

        write_text_file(output_covsfile, self.string)

    def create_regressors_file_ofsubset(self, odp:str, regressors:List[Regressor], whole_group_instances:List[Subject], groups_instances:List[List[Subject]], group_labels:List[str]=None,
                                        ofn:str="conn_covs", data_file=None, ofn_postfix:str="", subj_must_exist:bool=False, debug:bool=False):
        """
        This function creates a regressors file for the CONN tool, for a subset of the subjects in the current project.
        to be used when user want to insert groups description/covariates of a subset of the subjects included in the whole conn project.
        In this case, the script must insert zeros outside the rows described in grouplabels.
        the script assumes that all subjects specified in grouplabels, belong to Conn projects
        Args:
            odp (str): The output directory path where the regressors file will be created.
            regressors (list): A list of regressors that will be included in the analysis. The regressors can be
                covariates or nuisances.
            whole_group_instances (list): The list of all subjects that will be included in the regressors file.
            represents the subjects order in the conn project. The subjects can be specified by their group labels or by their subject labels.
            groups_instances:List[List[Subject]]: The list of group instances that will be used to create the factorial design. Each group
                label will be used as an explanatory variable (EV).
            group_labels:List[str]: used to name output files
            ofn (str, optional): The name of the regressors file. The default value is "conn_covs".
            data_file (str, optional): The path to the data file that contains the subject data. If not specified,
                the data file associated with the current project will be used.
            ofn_postfix (str, optional): A postfix that will be added to the name of the regressors file. The default
                value is an empty string.
            subj_must_exist (bool, optional): A boolean value that indicates whether the subjects in the group labels
                must exist in the data file. If set to False, subjects that do not exist in the data file will be
                ignored. The default value is True.

        Returns:
            None
        """
        # ------------------------------------------------------------------------------------
        # sanity checks
        if not is_list_of(groups_instances[0], Subject):
            raise SubjectListException("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file: given subjects is not a list of Subject", str(groups_instances))

        if bool(regressors):
            data:SubjectsData = self.project.validate_data(data_file)
            data.validate_covs(regressors)
        else:
            data = None

        ngroups = len(groups_instances)  # number of groups in the design. each group will have its regressor (EV).
        if ngroups > 3:
            raise Exception("Error in ConnModels.create_regressors_file_ofsubset, no more than three groups are supported")

        # ----------------------------------------------------------------------------------
        # create a list with all Subject instances
        subjs_instances = []
        for subjs in groups_instances:
            subjs_instances = subjs_instances + subjs

        # ------------------------------------------------------------------------------------
        # divide regressors in covariates and nuisances
        covs_label = []
        nuis_label = []
        for regr in regressors:
            if isinstance(regr, Covariate):
                covs_label.append(regr.name)
            elif isinstance(regr, Nuisance):
                nuis_label.append(regr.name)
        ncovs = len(covs_label)
        nnuis = len(nuis_label)

        tot_expected_columns = ngroups*(1 + ncovs) + nnuis  # one for each group, ngroup for each covariate, one for each nuisance

        empty_row = " ".join(["0" for _ in range(tot_expected_columns)])  # row value for subjects in the conn project but not in the given grouplabels subset

        # ------------------------------------------------------------------------------------
        # define output filename...add regressors/nuis to given ofn containing groups info
        output_covsfile = os.path.join(odp, ofn + ofn_postfix)
        os.makedirs(odp, exist_ok=True)

        # ------------------------------------------------------------------------------------
        # add file header with regressors labels
        for gr in group_labels:
            self.string = self.string + gr + " "
        for nuis in nuis_label:
            self.string = self.string + nuis + " "
        for covs in covs_label:
            str_covs = ""
            for i in range(ngroups):
                str_covs = str_covs + covs + "_" + str(i+1) + " "
            self.string = self.string + str_covs

        self.string = self.string[:-1]
        self.__addline2string()

        # ------------------------------------------------------------------------------------
        # prepare groups' regressors string
        if ngroups == 1:
            groups_strings = ["1"]
        elif ngroups == 2:
            groups_strings = ["1 0", "0 1"]
        elif ngroups == 3:
            groups_strings = ["1 0 0", "0 1 0", "0 0 1"]
        elif ngroups == 4:
            groups_strings = ["1 0 0 0", "0 1 0 0", "0 0 1 0", "0 0 0 1"]
        else:
            print("cannot manage more than 4 groups")
            return

        # subjs_data = data.filter_subjects(whole_subjest_labels)

        # ------------------------------------------------------------------------------------
        # write file: cycle through the subjects of the entire dataset
        for subj in whole_group_instances:

            slab = subj.label
            # determine to which group belong
            group_id = -1       # does not belong
            for gr_id, gr in enumerate(groups_instances):
                if slab in gr:
                    group_id = gr_id

            if group_id == -1:
                self.__addline2string(empty_row)
            else:
                string = groups_strings[group_id]

                for nuis in nuis_label:
                    string = string + " " + str(data.get_subject_col_value(subj, nuis))

                for cov in covs_label:
                    cov_value = str(data.get_subject_col_value(subj, cov))
                    covsvalue = ["0" for _ in range(ngroups)]
                    covsvalue[group_id] = cov_value
                    value_string = " ".join(covsvalue)
                    string = string + " " + value_string

                self.__addline2string(string)

        write_text_file(output_covsfile, self.string)
        print("create model file " + output_covsfile)

    def __addline2string(self, line:str=""):
        """
        This function appends a line to the self.string attribute.

        Args:
            line (str, optional): The line to be appended to the self.string attribute. If not specified, an empty
                string will be used.

        Returns:
            None
        """
        self.string += line
        self.string += "\n"
