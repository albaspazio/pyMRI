import os
import traceback

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from group.SPMModels import SPMModels
from group.SPMPostModel import PostModel
from group.spm_utilities import Covariate, Nuisance

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = Global(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        proj_dir = "/data/MRI/projects/test"
        project = Project(proj_dir, globaldata)     # automatically load PROJDIR/script/data.dat if present
        SESS_ID = 1
        num_cpu = 1
        group_label = "all"

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        subjects = project.load_subjects(group_label, SESS_ID)

        analysis            = GroupAnalysis(project)
        spm_analysis        = SPMModels(project)


        # ==================================================================================================================
        # THICKNESS DATA:
        # ==================================================================================================================
        #
        # def batchrun_cat_thickness_stats_factdes_1group_multregr(self, root_outdir, analysis_name, groups_instances, regressors,
        #                                                          data_file=None, glob_calc="", cov_interactions=None,
        #                                                          expl_mask=None, spm_template_name="spm_stats_1group_multiregr_check_estimate",
        #                                                          spm_contrasts_template_name="", runit=True):
        groups_instances    = [project.get_subjects("grp1", SESS_ID)]
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "multregr_age_gender"
        statsdir            = os.path.join(project.group_analysis_dir, "mpr/thickness")
        post_model          = PostModel("cat_stats_contrasts_results", regressors=covs, isSpm=False)
        spm_analysis.batchrun_cat_thickness_stats_factdes_1group_multregr(statsdir, anal_name, groups_instances, covs, post_model=post_model, runit=False)


        # def batchrun_cat_thickness_stats_factdes_2samplesttest(self, root_outdir, analysis_name, groups_instances=None, regressors=None,
        #                                                        data_file=None, glob_calc="", cov_interaction=None,
        #                                                        expl_mask=None, spm_template_name="cat_thickness_stats_2samples_ttest_check_estimate",
        #                                                        spm_contrasts_template_name="spm_stats_2samplesttest_contrasts_results",
        #                                                        stats_params=None, runit=True, c1_name="A > B", c2_name="B > A"):
        groups_instances    = [ project.get_subjects("grp1"),
                                project.get_subjects("grp2")]
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "2stt_age_gender"
        statsdir            = os.path.join(project.group_analysis_dir, "mpr/thickness")
        post_model          = PostModel("cat_stats_2samples_ttest_contrasts_results", regressors=covs, isSpm=False)
        spm_analysis.batchrun_cat_thickness_stats_factdes_2samplesttest(statsdir, anal_name, groups_instances, covs, post_model=post_model, runit=False)


        # def batchrun_cat_thickness_stats_factdes_1Wanova(self, root_outdir, analysis_name, groups_instances, regressors=None,
        #                                                  data_file=None, glob_calc="", cov_interaction=None,
        #                                                  expl_mask=None, spm_template_name="spm_stats_1Wanova_check_estimate",
        #                                                  spm_contrasts_template_name="", runit=True):
        groups_instances    = [ project.get_subjects("grp1"),
                                project.get_subjects("grp2"),
                                project.get_subjects("grp3")]
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "1Wanova_3_groups_age_gender"
        statsdir            = os.path.join(project.group_analysis_dir, "mpr/thickness")
        post_model          = PostModel("fullpath2template", regressors=covs, isSpm=False)
        spm_analysis.batchrun_cat_thickness_stats_factdes_1Wanova(statsdir, anal_name, groups_instances, covs, post_model=post_model, runit=False)


        # def batchrun_cat_thickness_stats_factdes_2Wanova(self, root_outdir, analysis_name, factors, regressors=None,
        #                                                  data_file=None, glob_calc="", cov_interaction=None,
        #                                                  expl_mask=None, spm_template_name="cat_thickness_stats_2Wanova_check_estimate",
        #                                                  spm_contrasts_template_name="", runit=True):
        factors             = {"labels":["f1", "f2"], "cells": [[project.get_subjects("grp1"), project.get_subjects("grp2")],
                                                                [project.get_subjects("grp3"), project.get_subjects("grp4")]]}
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "2Wanova_age_gender"
        statsdir            = os.path.join(project.group_analysis_dir, "mpr/thickness")
        post_model          = PostModel("fullpath2template", regressors=covs, isSpm=False)
        spm_analysis.batchrun_cat_thickness_stats_factdes_2Wanova(statsdir, anal_name, factors, covs, post_model=post_model, runit=False)


    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


