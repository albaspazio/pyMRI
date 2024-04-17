from __future__ import annotations

import os
from distutils.file_util import copy_file
from typing import List

from Global import Global
from Project import Project
from data.SubjectsData import SubjectsData
from models.FSLConFile import FSLConFile
from group.spm_utilities import Regressor, Covariate, Nuisance
from subject.Subject import Subject
from utility.fileutilities import remove_ext, append_text_file, read_list_from_file
# create factorial designs, multiple regressions, t-test
from utility.myfsl.utils.run import rrun


class FSLModels:
    """
    Initialize the FSLModels class.

    Args:
        proj (object): A Project instance.
    """

    def __init__(self, proj:Project):

        self.subjects_list  = None
        self.working_dir    = ""

        self.project:Project    = proj
        self.globaldata:Global  = self.project.globaldata

        self.string             = ""    # used to compose models override

    # ---------------------------------------------------
    def create_Mgroups_Ncov_Xnuisance_glm_file(self, input_fsf: str, odp: str, regressors: List[Regressor], grlab_subjlabs_subjs: str | List[str] | List[Subject], grp_names=None, ofn: str = "mult_cov", data: str | SubjectsData = None, create_model: bool = True, group_mean_contrasts: int = 1, cov_mean_contrasts: int = 2, compare_covs: bool = False, ofn_postfix: str = "", subj_must_exist: bool = False):
        """
        This function creates a FSL GLM file starting from a template. Manage multiple groups, with covariates and nuisance regressors.
        - N covariates
        - X nuisance (without associated contrast)
        values contained in $SUBJECTS_FILE
        covariates/nuisance regressors will be appended starting from the (NUM_GROUPS+1)-th column_id
        must write $OUT_FSF_NAME variable

        ------------------------------------------------------------------------------------
        RULES TO CREATE REGRESSORS AND CONTRASTS
        ------------------------------------------------------------------------------------
        each group        has one regressor
        each nuisance     has one regressor
        each covariate    has one regressor f.e. group

        1 group:

        COVARIATES > 0 :  - cov correlation                    : 1|2 f.e. cov
                          - group_mean_contrasts (0|1|2)      : 0|1|2
                          - covs comparisons (between either 2 or 3 covs)
        COVARIATES = 0 :  - group_mean_contrasts (1|2)        : 1|2

        2+ groups:
        COVARIATES > 0 :  - cov correlation within-group      : 1|2 f.e. cov f.e. group    cov-i: gr-j pos | gr-j neg, ....
                          - slopes comparisons between-group  :   2 f.e. cov               cov-i: gr1>gr2 and gr2>gr1
                          - group mean within-group           : 1|2 f.e. group             gr1: pos | neg
                          group comparisons are not performed

        COVARIATES = 0 :  - group_mean_contrasts x group
                          - group comparisons
        Parameters
        ----------
        input_fsf : str
            The path to the input FSL GLM file.  /home/...../proj_label/script/glm/.....fsf
        odp : str
            The path to the output directory.
        regressors : list
            A list of regressors, including covariates and nuisance regressors. indicating whether adding respectively a contrast or not
        grlab_subjlabs_subjs : list
            A list of group labels or subject labels. eg: 3 groups  ["grp1","grp2","grp3"] or [["s11", "s12", ..., "s1n"], ["s21", ..."s2m"], ["s31", ..., "s3k"]]
        ofn : str, optional
            The output file name prefix, by default "mult_cov".
        data : str, optional
            The path to the data file, by default None.
        create_model : bool, optional
            Whether to create the model, by default True. if True call feat_model at the end to create .mat/.con file for randomise analysis...
            if False no..to be used for Feat analysis
        group_mean_contrasts : int, optional
            The number of group mean contrasts, by default 1. 0: no mean,1: only positive, 2: positive and negative.
        cov_mean_contrasts : int, optional
            The number of covariate mean contrasts, by default 2. 0: no mean,1: only positive, 2: positive and negative.
        compare_covs : bool, optional
            Whether to compare covariates, by default False.
        ofn_postfix : str, optional
            A postfix for the output file name, by default "".
        subj_must_exist : bool, optional
            Whether to check if subjects exist, by default False.

        Returns
        -------
        None

        Raises
        ------
        Exception
            If the input FSL GLM file does not exist.
            :param grp_names:
        """
        try:
            self.string = ""
            # ------------------------------------------------------------------------------------
            # sanity checks
            if not os.path.exists(input_fsf):
                raise Exception("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file, input fsf file is missing...exiting")

            if bool(regressors):
                data = self.project.validate_data(data)
                data.validate_covs(regressors)
            else:
                data = None

            ngroups = len(grlab_subjlabs_subjs)  # number of groups in the design. each group will have its regressor (EV).
            if ngroups > 3:
                raise Exception("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file, no more than three groups are supported")

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

            # at least one valid contrast must exist
            if ngroups == 1 and ncovs == 0 and group_mean_contrasts == 0:
                raise Exception("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file, when one group is investigated, either cov_mean_contrasts or group_mean_contrasts must be > 0....exiting")

            # ----------------------------------------------------------------------------------
            # get subjects values
            subj_labels_by_groups   = []
            all_subj                = []
            nsubjs      = 0
            for grp in grlab_subjlabs_subjs:
                labels = self.project.get_subjects_labels(grp, must_exist=subj_must_exist)
                subj_labels_by_groups.append(labels)
                all_subj += labels
                nsubjs += len(labels)

            covs_values = self.project.get_subjects_values_by_cols(all_subj, covs_label)
            nuis_values = self.project.get_subjects_values_by_cols(all_subj, nuis_label)

            for id, val in enumerate(covs_values):
                if len(val) != nsubjs:
                    raise Exception("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file: number of cov values of cov " + covs_label[id] + " differs from subjects number")

            for id, val in enumerate(nuis_values):
                if len(val) != nsubjs:
                    raise Exception("Error in FSLModels.create_Mgroups_Ncov_Xnuisance_glm_file: number of cov values of cov " + covs_label[id] + " differs from subjects number")
            # ------------------------------------------------------------------------------------
            # define output filename...add regressors/nuis to given ofn containing groups info
            for rname in covs_label:
                ofn += ("_" + rname)
            if nnuis > 0:
                ofn += "_x"
                for rname in nuis_label:
                    ofn += ("_" + rname)

            output_glm_fsf = os.path.join(odp, ofn + ofn_postfix)
            os.makedirs(odp, exist_ok=True)
            copy_file(input_fsf, output_glm_fsf + ".fsf")

            # ------------------------------------------------------------------------------------
            # REGRESSORS AND CONTRASTS
            # ------------------------------------------------------------------------------------
            # number of regressors 1 f.e. group + 1 f.e. cov f.e. group + 1 f.e. nuisance
            tot_EV = ngroups + ncovs*ngroups + nnuis

            if ngroups == 1:
                within_grp_contrasts = 0
            elif ngroups == 2:
                within_grp_contrasts = 2  # a>b, b>a
            else:
                within_grp_contrasts = 6  # a>b, a>c, b>c, b>a, c>a, c>b

            tot_cont = cov_mean_contrasts * ncovs * ngroups # cov correlation within-group
            tot_cont += within_grp_contrasts * ncovs        # cov slopes comparisons between-group
            tot_cont += group_mean_contrasts * ngroups      # pos/neg group mean f.e. group

            if ncovs == 0:
                tot_cont += within_grp_contrasts            # between-groups comparisons

            between_cov_contrasts = 0
            if ngroups == 1 and ncovs > 1 and compare_covs:
                if ncovs == 2:
                    between_cov_contrasts = 2  # a>b, b>a
                elif ncovs == 3:
                    between_cov_contrasts = 6  # a>b, a>c, b>c, b>a, c>a, c>b
                else:
                    print("cannot compare more than three covariates, between-covariates comparisons is omitted")

            tot_cont += between_cov_contrasts
            # ------------------------------------------------------------------------------------
            # SUMMARY
            # ------------------------------------------------------------------------------------
            print("---------------- S U M M A R Y -------------------------------------------------------------------------------")
            print("creating Ncov_Xnuisance with the following parameters:")
            print("filename :" + output_glm_fsf)
            print("NUM_COVS, NUM_NUIS, NUM_GROUPS : " + str(ncovs) + ", " + str(nnuis) + ", " + str(ngroups))
            print("ARR_COV= " + str(covs_label))
            print("ARR_NUIS= " + str(nuis_label))
            print("NUM_GROUPS=" + str(ngroups))
            print("NUM_CONTRASTS=" + str(tot_cont))
            # ---------------------------------------------------
            # overridding GLM file
            # ---------------------------------------------------
            self.addline2string("")
            self.addline2string("")
            self.addline2string("")
            self.addline2string("")
            self.addline2string("")
            self.addline2string("")
            self.addline2string("")
            self.addline2string("# ==================================================================")
            self.addline2string("# ====== START OVERRIDE ============================================")
            self.addline2string("# ==================================================================")
            self.addline2string("")
            self.addline2string("subjects included")
            for slab in all_subj:
                self.addline2string(slab)
            self.addline2string("-------------------------------------------------------------------")

            # Number of subjects
            self.addline2string("set fmri(npts) "     + str(nsubjs))
            self.addline2string("set fmri(multiple) " + str(nsubjs))

            # Number of EVs
            self.addline2string("set fmri(evs_orig) " + str(tot_EV))
            self.addline2string("set fmri(evs_real) " + str(tot_EV))

            # Number of contrasts
            self.addline2string("set fmri(ncon_orig) " + str(tot_cont))
            self.addline2string("set fmri(ncon_real) " + str(tot_cont))

            self.addline2string("#====================== init EV data")
            for ev in range(1, tot_EV+1):
                self.addline2string("set fmri(shape" + str(ev) + ") 2")
                self.addline2string("set fmri(convolve" + str(ev) + ") 0")
                self.addline2string("set fmri(convolve_phase" + str(ev) + ") 0")
                self.addline2string("set fmri(tempfilt_yn" + str(ev) + ") 0")
                self.addline2string("set fmri(deriv_yn" + str(ev) + ") 0")
                self.addline2string("set fmri(custom" + str(ev) + ") dummy")

                for ev2 in range(0, tot_EV+1):
                    self.addline2string("set fmri(ortho" + str(ev) + "." + str(ev2) + ") 0")

            # ---------------------------------------------------
            # GROUPS
            self.addline2string("#====================== init to 0 groups' means")
            for s in range(1, nsubjs+1):
                self.addline2string("set fmri(groupmem." + str(s) + ") 1")
                for gr in range(1, ngroups+1):
                    self.addline2string("set fmri(evg" + str(s) + "." + str(gr) + ") 0")

            self.addline2string("#====================== set groups' means to actual values")
            subjid = 1
            for gr in range(1, ngroups+1):
                for _ in subj_labels_by_groups[gr - 1]:
                    self.addline2string("set fmri(evg" + str(subjid) + "." + str(gr) + ") 1")
                    subjid += 1

            self.addline2string("#====================== set groups' evtitle")
            for gr in range(1, ngroups + 1):
                self.addline2string("set fmri(evtitle" + str(gr) + ") \"grp" + str(gr) + "\"")

            # =================================================================================================
            #region N U I S A N C E
            col_id = 0
            self.addline2string("#====================== set nuisance event titles (event [1:$NUM_GROUPS] are the means and are not overwritten)")
            for nuis in nuis_label:
                cnt = col_id + 1 + ngroups
                self.addline2string("set fmri(evtitle" + str(cnt) + ") \"" + nuis + "\"")
                col_id += 1

            self.addline2string("#====================== set nuisance values")
            for s in range(nsubjs):
                for col_id in range(nnuis):
                    cnt  = col_id + 1 + ngroups
                    # cnt2 = (s-1)*nnuis + id
                    self.addline2string("set fmri(evg" + str(s+1) + "." + str(cnt) + ") " + str(nuis_values[col_id][s]) )

            #endregion
            # =================================================================================================
            #region C O V A R I A T E S
            ev = 0
            self.addline2string("#====================== set covariates event titles (event [1:$NUM_GROUPS] are the means and are not overwritten)")
            for cov in covs_label:
                for gr in range(1, ngroups+1):
                    evid = (ev+1)*ngroups + nnuis + gr
                    self.addline2string("set fmri(evtitle" + str(evid) + ") \"" + cov + " group" + str(gr) + "\"")
                ev += 1

            self.addline2string("#====================== init to 0 covariates EV")
            startEVid = ngroups + 1 + nnuis
            for s in range(1, nsubjs+1):
                for evid in range(startEVid, tot_EV+1):
                    self.addline2string("set fmri(evg" + str(s) + "." + str(evid) + ") 0")

            self.addline2string("#====================== set covariates values")

            for covid in range(ncovs):
                sid = 1
                for gr in range(ngroups):
                    evid = startEVid + covid*ngroups + gr
                    for s in range(len(subj_labels_by_groups[gr])):
                        self.addline2string("set fmri(evg" + str(sid) + "." + str(evid) + ") " + str(covs_values[covid][sid-1]))
                        sid += 1
                    # evid += 1
            #endregion

            # =================================================================================================
            #region C O N T R A S T S
            self.addline2string("#====================== reset contrast values")
            for evid in range(1, tot_EV+1):
                for conid in range(1, tot_cont+1):
                    self.addline2string("set fmri(con_real" + str(conid) + "." + str(evid) + ") 0")

            self.addline2string("#====================== set contrasts")
            contrid = 0 # contrasts' row
            evid    = 1 # covariate column
            if ngroups == 1:

                # 1) group mean contrasts if present
                if group_mean_contrasts > 0:
                    contrid += 1
                    self.addline2string("set fmri(conpic_real."         + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real."        + str(contrid) + ") \"group pos\"" )
                    self.addline2string("set fmri(con_real"             + str(contrid) + "." + str(evid) + ") 1" )

                    if group_mean_contrasts == 2:
                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group neg\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + "." + str(evid) + ") -1")

                # 2) pos|neg cov contrasts if present
                evid += (nnuis + 1)
                for cov in covs_label:
                    # ===== POS CONTRAST
                    contrid += 1
                    self.addline2string("set fmri(conpic_real."         + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real."        + str(contrid) + ") \"" + cov + " pos" + "\"")
                    self.addline2string("set fmri(con_real"             + str(contrid) + "." + str(evid) + ") 1")

                    if cov_mean_contrasts == 2:
                        # ===== NEG CONTRAST
                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"" + cov + " neg" + "\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + "." + str(evid) + ") -1")

                    evid += 1

                # 3) between cov contrasts (can be 3 at maximum)
                if between_cov_contrasts == 2:
                    evid = 1 + nnuis + 1
                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[0] + " > " + covs_label[1] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid) + ") 1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+1) + ") -1")

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[1] + " > " + covs_label[0] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid) + ") -1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+1) + ") 1")

                elif between_cov_contrasts == 6:
                    evid = 1 + nnuis + 1

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[0] + " > " + covs_label[1] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid) + ") 1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+1) + ") -1")

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[1] + " > " + covs_label[0] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid) + ") -1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+1) + ") 1")

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[0] + " > " + covs_label[2] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid) + ") 1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+2) + ") -1")

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[2] + " > " + covs_label[0] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid) + ") -1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+2) + ") 1")

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[1] + " > " + covs_label[2] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+1) + ") 1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+2) + ") -1")

                    contrid += 1
                    self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + covs_label[2] + " > " + covs_label[1] + "\"")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+1) + ") -1")
                    self.addline2string("set fmri(con_real" + str(contrid) + "." + str(evid+2) + ") 1")

            else:   # ngroups > 1

                # 1) write group mean contrasts if present
                if group_mean_contrasts > 0:
                    for evid in range(1, ngroups + 1):
                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group"+ str(evid) + " pos\"" )
                        self.addline2string("set fmri(con_real"         + str(contrid) + "." + str(evid) + ") 1" )

                        if group_mean_contrasts == 2:
                            contrid += 1
                            self.addline2string("set fmri(conpic_real." + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real."+ str(contrid) + ") \"group"+ str(evid) + " neg\"")
                            self.addline2string("set fmri(con_real"     + str(contrid) + "." + str(evid) + ") -1")

                if ncovs == 0:   # $ncovs = 0, MEAN_CONTRASTS = 1 or 2

                    # 2) pairwise comparisons between groups
                    if ngroups >= 2:

                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group1 > group2\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".1) 1")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".2) -1")

                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group2 > group1\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".1) -1")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".2) 1")

                    if ngroups == 3:

                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group1 > group3\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".1) 1")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".3) -1")
                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group3 > group1\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".1) -1")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".3) 1")

                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group2 > group3\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".2) 1")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".3) -1")
                        contrid += 1
                        self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                        self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"group3 > group2\"")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".2) -1")
                        self.addline2string("set fmri(con_real"         + str(contrid) + ".3) 1")

                else:   # ngroups > 1, ncovs > 0

                    for covid in range(ncovs):
                        cov_name = covs_label[covid]

                        # 2) within-groups cov correlations ( pos|neg correlation(s), for each covariate, for each group)
                        if cov_mean_contrasts > 0:
                            for gr in range(1, ngroups+1):
                                evid = ngroups + nnuis + covid*ngroups + gr

                                # ===== POS CONTRAST
                                contrid += 1
                                self.addline2string("set fmri(conpic_real."     + str(contrid) + ") 1")
                                self.addline2string("set fmri(conname_real."    + str(contrid) + ") \"" + cov_name + " group" + str(gr) + " pos\"")
                                self.addline2string("set fmri(con_real"         + str(contrid) + "." + str(evid) + ") 1")

                                if cov_mean_contrasts == 2:
                                    # ===== NEG CONTRAST
                                    contrid += 1
                                    self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                                    self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name + " group" + str(gr) + " neg\"")
                                    self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid) + ") -1")


                        # 3) test correlations differences between groups
                        evid        = ngroups + nnuis + covid*ngroups + 1
                        evid_plus1  = evid + 1
                        evid_plus2  = evid + 2

                        if ngroups >= 2:

                            contrid += 1
                            self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name + ": group1 > group2\"")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid) + ") 1")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus1) + ") -1")
                            contrid += 1
                            self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name +  ": group2 > group1\"")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid) + ") -1")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus1) + ") 1")

                        if ngroups == 3:

                            contrid += 1
                            self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name + ": group1 > group3\"")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid) + ") 1")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus2) + ") -1")
                            contrid += 1
                            self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name + ": group3 > group1\"")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid) + ") -1")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus2) + ") 1")

                            contrid += 1
                            self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name + ": group2 > group3\"")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus1) + ") 1")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus2) + ") -1")
                            contrid += 1
                            self.addline2string("set fmri(conpic_real."  + str(contrid) + ") 1")
                            self.addline2string("set fmri(conname_real." + str(contrid) + ") \"" + cov_name + ": group3 > group2\"")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus1) + ") -1")
                            self.addline2string("set fmri(con_real"      + str(contrid) + "." + str(evid_plus2) + ") 1")

            #endregion

            append_text_file(output_glm_fsf + ".fsf", self.string)
            # -----------------------------------------------------------------------------------------------
            # create model
            model_noext = remove_ext(output_glm_fsf)
            if create_model:
                rrun("feat_model " + model_noext)

            # if $? -gt 0:
            #     print("===> KO: Error in feat_model")
            #     return

            print("#===> OK: multiple covariate GLM model (" + model_noext + ".fsf) correctly created")

        except Exception as e:
            #traceback.print_exc()
            print(".")
            print(".")
            print("##################################################################################################################################################################################")
            print("#===> E R R O R : GLM model (" + model_noext + ".fsf) raised an error: ")
            print("##################################################################################################################################################################################")
            print(".")
            print(".")
            return

    def addline2string(self, line: str) -> None:
        """
        Add a line to the internal string buffer.

        Parameters
        ----------
        line : str
            The line to add to the buffer.

        Returns
        -------
        None

        """
        self.string += line
        self.string += "\n"

    @staticmethod
    def get_numpoints_from_fsl_model(mat_file:str):

        """
        Reads a .mat file and returns the number of time points in the model.

        Parameters
        ----------
        mat_file : str
            Path to the .mat file containing the model parameters.

        Returns
        -------
        int
            Number of time points in the model.

        Raises
        ------
        Exception
            If the .mat file does not contain the number of time points.
        """

        lines = read_list_from_file(mat_file)
        for l in lines:
            if "/NumPoints" in l:
                return int(list(l.split("\t"))[1])
        raise Exception("")

    @staticmethod
    def read_fsl_contrasts_file(con_file:str) -> FSLConFile:

        """
        Reads a .con file and returns an FSLConFile object containing the information.

        Parameters
        ----------
        con_file : str
            Path to the .con file to read.

        Returns
        -------
        FSLConFile
            Object containing information about the contrasts in the model.
        """

        confile = FSLConFile()

        lines   = read_list_from_file(con_file)
        nlines  = len(lines)

        for id,l in enumerate(lines):
            if "/ContrastName" in l:
                confile.names.append(list(l.split("\t"))[1])
            elif "/NumWaves" in l:
                confile.nwaves = int(list(l.split("\t"))[1])
            elif "/NumContrasts" in l:
                confile.ncontrasts =  int(list(l.split("\t"))[1])
            elif "/PPheights" in l:
                confile.pp_heights = l
            elif "/RequiredEffect" in l:
                confile.req_effect = l
            elif "/Matrix" in l:
                # should be the (nlines - ncontrasts - 1) [0-based] line
                for i in range(confile.ncontrasts):
                    confile.matrix.append(lines[id + 1 + i])

        return confile

