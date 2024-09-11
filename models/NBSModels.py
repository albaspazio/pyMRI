from __future__ import annotations

import os
from distutils.file_util import copy_file
from typing import List, Any

from Global import Global
from Project import Project
from data.SubjectsData import SubjectsData
from group.spm_utilities import Regressor, Covariate, Nuisance

# create factorial designs, multiple regressions, t-test
from myutility.myfsl.utils.run import rrun
from myutility.fileutilities import remove_ext, append_text_file, write_text_file


class NBSModels:
    """
    This class provides methods for creating and managing the connection models used in the NBS tool.

    Args:
        proj (Project): The Project object that this class is associated with.

    Attributes:
        subjects_list (list): A list of Subject objects that are part of the current project.
        working_dir (str): The directory where temporary files are stored.
        project (Project): The ConnProject object that this class is associated with.
        globaldata (GlobalData): The GlobalData object that is associated with the current project.
        string (str): A string that is used to compose the connection models files.
    """

    def __init__(self, proj:Project):
        self.subjects_list      = None
        self.working_dir        = ""
        self.project:Project    = proj
        self.globaldata:Global  = self.project.globaldata
        self.string             = ""  # used to compose models override

    def create_regressors_file(self, odp:str, regressors:List[Regressor], grouplabels:List[str], ofn:str="nbs_model",
                                data:str|SubjectsData=None, ofn_postfix:str="", subj_must_exist:bool=False):
        """
        This method creates a regressors file that can be used with the NBS tool. The regressors file contains
        the regressors and covariates that will be used in the analysis.

        Args:
            odp (str): The output directory path where the regressors file will be created.
            regressors (list): A list of regressors that will be included in the analysis. The regressors can be
                covariates or nuisances.
            grouplabels (list): A list of group labels that will be used to create the factorial design. Each group
                label will be used as an explanatory variable (EV).
            ofn (str, optional): The name of the regressors file. The default value is "conn_covs".
            data (str|SubjectsData, optional): The path to the data file that contains the subject data or
                a SubjectsData. If not specified, the data (file) associated with the current project will be used.
            ofn_postfix (str, optional): A postfix that will be added to the name of the regressors file. The default
                value is an empty string.
            subj_must_exist (bool, optional): A boolean value that indicates whether the subjects in the group labels
                must exist in the data file. If set to False, subjects that do not exist in the data file will be
                ignored. The default value is True.
        """
        self.string = ""
        # ------------------------------------------------------------------------------------
        # sanity checks
        if bool(regressors):
            data = self.project.validate_data(data)  # SubjectsData
            data.validate_covs(regressors)
        else:
            data = None

        if not isinstance(grouplabels[0], str):
            print("create_regressors_file wants a list of group labels and not of Subjects' list to specify group")
            return

        ngroups = len(grouplabels)  # number of groups in the design. each group will have its regressor (EV).

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

        # ----------------------------------------------------------------------------------
        # get subjects values
        subj_labels_by_groups = []
        all_subj = []
        nsubjs = 0
        for grp in grouplabels:
            labels = self.project.get_subjects_labels(grp, must_exist=subj_must_exist)
            subj_labels_by_groups.append(labels)
            all_subj += labels
            nsubjs += len(labels)

        covs_values = self.project.get_subjects_values_by_cols(all_subj, covs_label)
        nuis_values = self.project.get_subjects_values_by_cols(all_subj, nuis_label)

        # ------------------------------------------------------------------------------------
        # define output filename...add regressors/nuis to given ofn containing groups info
        output_covsfile = os.path.join(odp, ofn + ofn_postfix)
        os.makedirs(odp, exist_ok=True)

        # ------------------------------------------------------------------------------------
        # for gr in grouplabels:
        #     self.string = self.string + gr + " "
        # for nuis in nuis_label:
        #     self.string = self.string + nuis + " "
        # for covs in covs_label:
        #     str_covs = ""
        #     for i in range(ngroups):
        #         str_covs = str_covs + covs + "_" + str(i + 1) + " "
        #     self.string = self.string + str_covs
        # self.string = self.string[:-1]
        #
        # self.__addline2string()

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

        curr_subjid = 0

        for gr_id, gr in enumerate(subj_labels_by_groups):
            for _ in subj_labels_by_groups[gr_id]:
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
