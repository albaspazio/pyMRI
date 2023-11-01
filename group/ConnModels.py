import os
from distutils.file_util import copy_file

from group.spm_utilities import Covariate, Nuisance

# create factorial designs, multiple regressions, t-test
from utility.myfsl.utils.run import rrun
from utility.fileutilities import remove_ext, append_text_file, write_text_file


class ConnModels:

    def __init__(self, proj):

        self.subjects_list  = None
        self.working_dir    = ""

        self.project        = proj
        self.globaldata     = self.project.globaldata

        self.string         = ""    # used to compose models override

    # grouplabels is a list of string, also used as name of the group covariate
    def create_regressors_file(self, odp, regressors, grouplabels, ofn="conn_covs", data_file=None, ofn_postfix="", subj_must_exist=False):

        self.string = ""
        # ------------------------------------------------------------------------------------
        # sanity checks
        if bool(regressors):
            data = self.project.validate_data(data_file)
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
        subj_labels_by_groups   = []
        all_subj                = []
        nsubjs      = 0
        for grp in grouplabels:
            labels = self.project.get_subjects_labels(grp, must_exist=subj_must_exist)
            subj_labels_by_groups.append(labels)
            all_subj += labels
            nsubjs += len(labels)

        covs_values = self.project.get_filtered_columns_by_values(covs_label, all_subj, data=data)[0]
        nuis_values = self.project.get_filtered_columns_by_values(nuis_label, all_subj, data=data)[0]

        # ------------------------------------------------------------------------------------
        # define output filename...add regressors/nuis to given ofn containing groups info
        output_covsfile = os.path.join(odp, ofn + ofn_postfix)
        os.makedirs(odp, exist_ok=True)

        # ------------------------------------------------------------------------------------
        for gr in grouplabels:
            self.string = self.string + gr + " "
        for nuis in nuis_label:
            self.string = self.string + nuis + " "
        for covs in covs_label:
            str_covs = ""
            for i in range(ngroups):
                str_covs = str_covs + covs + "_" + str(i+1) + " "
            self.string = self.string + str_covs
        self.string = self.string[:-1]

        self.addline2string()

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
                    cov_value           = str(covs_values[cov_id][curr_subjid])
                    covsvalue           = ["0" for _ in range(ngroups)]
                    covsvalue[gr_id]    = cov_value
                    value_string        = " ".join(covsvalue)
                    string              = string + " " + value_string

                self.addline2string(string)
                curr_subjid = curr_subjid + 1

        write_text_file(output_covsfile, self.string)

    def addline2string(self, line=""):
        self.string += line
        self.string += "\n"
        