import os
from distutils.file_util import copy_file

from data.utilities         import validate_data_with_covs
from group.SPMCovariates    import SPMCovariates
from group.SPMPostModel     import SPMPostModel
from group.SPMStatsUtils import SPMStatsUtils, Covariate, Nuisance
from utility.matlab         import call_matlab_spmbatch
from utility.utilities      import sed_inplace


# create factorial designs, multiple regressions, t-test
class FSLModels:

    def __init__(self, proj):

        self.subjects_list  = None
        self.working_dir    = ""

        self.project        = proj
        self.globaldata     = self.project.globaldata

    # ---------------------------------------------------
    # create a FSF file starting from a template and filling in:
    # - N covariates
    # - X nuisance (without associated contrast)
    # values contained in $SUBJECTS_FILE
    # covariates/nuisance regressors will be appended starting from the (NUM_GROUPS+1)th column_id
    # must write $OUT_FSF_NAME variable
    # ---------------------------------------------------
    # input_fsf     : /home/...../proj_label/script/glm/.....fsf
    # odp           : path where save the file
    # covs          : list of Covariate and Nuisance instances, indicating whether adding respectively a contrast or not
    # grouplabel_or_subjlist : list of grouplabel_or_subjlist or subjects' labels
    #                 eg: 3 groups  ["grp1","grp2","grp3"] or [["s11", "s12", ..., "s1n"], ["s21", ..."s2m"], ["s31", ..., "s3k"]]
    # ofn           : string indicating output file prefix
    # data_file     : String|None   if None, use that loaded in project
    # create_model  : Bool          if True call feat_model at the end to create .mat/.con file for randomise analysis...if 0 no..to be used for Feat analysis
    # mean_contrast : Int           0: no mean,1: only positive, 2: positive and negative. nif True, create the mean contrast (valid when NUM_COVS>0)
    # cov_comp      : Bool          if True, create also covariate comparison contrast: e.g.  [0  1 -1], [0 -1  1]
    # rndpostfix    : String        to be appended to output GLM files, useful when you create several design simultaneously


    def create_Ncov_Xnuisance_glm_file(self, input_fsf, odp, covs, grouplabel_or_subjlist, ofn="mult_cov", data_file=None,
                                       create_model=True, mean_contrast=1, cov_comp=False, rndpostfix=""):

        # ------------------------------------------------------------------------------------
        # sanity checks
        if os.path.exists(input_fsf) is False:
            raise Exception("Error in FSLModels.create_Ncov_Xnuisance_glm_file, input fsf file is missing...exiting")

        if bool(covs) is True:
            data_file = self.project.validate_data(data_file)
            validate_data_with_covs(data_file, covs)

        ngroups = len(grouplabel_or_subjlist)  # number of groups in the design. each group will have its regressor (EV).
        if ngroups > 2:
            raise Exception("Error in FSLModels.create_Ncov_Xnuisance_glm_file, no more than two groups are supported")

        # ----------------------------------------------------------------------------------
        # get subjects
        subj_labels = []
        nsubjs      = 0
        for grp in grouplabel_or_subjlist:
            labels = self.project.get_subjects_labels(grp)
            subj_labels.append(labels)
            nsubjs += len(labels)

        # ------------------------------------------------------------------------------------
        # divide regressors in covariates and nuisances
        covs_label = []
        nuis_label = []
        for regr in covs:
            if isinstance(regr, Covariate):
                covs_label.append(regr.name)
            elif isinstance(regr, Nuisance):
                nuis_label.append(regr.name)
        ncovs = len(covs_label)
        nnuis = len(nuis_label)

        # at least one valid contrast must exist
        if ncovs == 0 and mean_contrast == 0:
            raise Exception("Error in FSLModels.create_Ncov_Xnuisance_glm_file, NEITHER COVS or MEAN contrast were specified..dont know what to do, so....exiting")

        # ------------------------------------------------------------------------------------
        # define output filename...add covs/nuis to given ofn containing groups info
        for rname in covs_label:
            ofn += ("_" + rname)
        if nnuis > 0:
            ofn += "_x_"
            for rname in nuis_label:
                ofn += ("_" + rname)

        output_glm_fsf = os.path.join(odp, ofn)
        os.makedirs(odp, exist_ok=True)
        copy_file(input_fsf, output_glm_fsf)

        # ------------------------------------------------------------------------------------
        # RULES TO CREATE THE CONTRASTS
        # 1 group:
        # COVARIATES > 0 : each covariate have 1 EV and 2 contrast + 2 contrasts for group mean (unless mean_contrast=0).
        # COVARIATES = 0 : 1 contrasts for group mean (2 if mean_contrast=2)
        # 2+ groups:
        # COVARIATES > 0 : each covariate have 1 EV + 1 contrast for each group .....group comparisons are not performed, we create #mean_contrast for each group
        # COVARIATES = 0 : group comparisons +  #mean_contrast x group

        tot_EV = ncovs*ngroups + nnuis + ngroups

        if ngroups == 1:
            tot_cont = 2*ncovs + mean_contrast
        elif ngroups == 2:
            if ncovs > 0:
                mean_contrast = 0
                tot_cont = 2*ncovs*(ngroups + 1)
            else:
                tot_cont = ngroups*(ngroups-1) + mean_contrast*ngroups

        # ------------------------------------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------------------------------------

        print("---------------- S U M M A R Y -------------------------------------------------------------------------------")
        print("creating Ncov_Xnuisance with the following parameters:")
        print("filename :" + output_glm_fsf)
        print("NUM_COVS, NUM_NUIS, NUM_GROUPS : " + str(ncovs) + ", " + str(ncovs) + ", " + str(ngroups))
        print("ARR_COV= " + str(covs_label))
        print("ARR_NUIS= " + str(nuis_label))
        print("NUM_GROUPS=" + str(ngroups))

        # ---------------------------------------------------
        # overridding GLM file
        # ---------------------------------------------------
        string  = "# ==================================================================\n"
        string += "# ====== START OVERRIDE ============================================\n"
        string += "# ==================================================================\n"

        # Number of subjects
        string += "set fmri(npts) "     + str(nsubjs) + "\n"
        string += "set fmri(multiple) " + str(nsubjs) + "\n"

        # Number of EVs
        string += "set fmri(evs_orig) " + str(tot_EV) + "\n"
        string += "set fmri(evs_real) " + str(tot_EV) + "\n"

        # Number of contrasts
        string += "set fmri(ncon_orig) " + str(tot_cont) + "\n"
        string += "set fmri(ncon_real) " + str(tot_cont) + "\n"

        string += "#====================== init EV data" + "\n"

        for ev in range(1, tot_EV+1):
            string += "set fmri(shape" + str(ev) + ") 2"  + "\n"
            string += "set fmri(convolve" + str(ev) + ") 0"  + "\n"
            string += "set fmri(convolve_phase" + str(ev) + ") 0"  + "\n"
            string += "set fmri(tempfilt_yn" + str(ev) + ") 0"  + "\n"
            string += "set fmri(deriv_yn" + str(ev) + ") 0"  + "\n"
            string += "set fmri(custom" + str(ev) + ") dummy" + "\n"

            for ev2 in range(0, tot_EV+1):
                string += "set fmri(ortho" + str(ev) + "." + str(ev2) + ") 0" + "\n"

        # ---------------------------------------------------
        # GROUPS
        string += "====================== init to 0 groups' means"
        for s in range(1, nsubjs+1):
            string += "set fmri(groupmem." + str(s) + ") 1" + "\n"
            for gr in range(1, ngroups+1):
                string += "set fmri(evg" + str(s) + "." + str(gr) + ") 0" + "\n"

        string += "====================== set groups' means to actual values"
        for s in range(1, len(subj_labels[0]) + 1):
            string += "set fmri(evg" + str(s) + ".1) 1" + "\n"

        for gr in range(2, ngroups+1):
            idgrpA = gr-2
            idgrpB = gr-1




