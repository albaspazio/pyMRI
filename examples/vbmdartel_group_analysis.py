import os
import traceback

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from group.SPMModels import SPMModels
from group.SPMStatsUtils import Covariate, Nuisance, PostModel, ResultsParams

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
        #project.add_icv_to_data(group_label) # add icv to all data

        analysis            = GroupAnalysis(project)
        spm_analysis        = SPMModels(project)

        # template
        vbm_template_name   = "a_template"
        vbm_template_dir    = os.path.join(project.vbm_dir, vbm_template_name) # vbm_template_dir    = analysis.create_vbm_spm_template_normalize(vbm_template_name, subjects)

        # STATS
        # def batchrun_spm_vbm_dartel_stats_factdes_1group_multregr(self, root_outdir, analysis_name, groups_instances, covs,
        #                                                           data_file=None, glob_calc="subj_icv", cov_interactions=None,
        #                                                           expl_mask="icv", spm_template_name="spm_stats_1group_multiregr_check_estimate",
        #                                                           spm_contrasts_template_name="", runit=True):
        groups_instances    = [project.get_subjects("grp1", SESS_ID)]
        covs                = [Covariate("gender"), Covariate("age")]
        anal_name           = "multregr_age_gender"
        postmodel           = PostModel("spm_stats_contrasts_results",
                                        covs, [], res_params=ResultsParams("FWE", 0.01, 10))
        spm_analysis.batchrun_spm_vbm_dartel_stats_factdes_1group_multregr(vbm_template_dir, anal_name, groups_instances, covs, post_model=postmodel, runit=False)


        # def batchrun_spm_vbm_dartel_stats_factdes_2samplesttest(self, root_outdir, analysis_name, groups_instances=None, covs=None,
        #                                                         data_file=None, glob_calc="subj_icv", cov_interaction=None,
        #                                                         expl_mask="icv", spm_template_name="spm_stats_2samples_ttest_check_estimate",
        #                                                         spm_contrasts_template_name="spm_stats_2samplesttest_contrasts_results",
        #                                                         stats_params=None, runit=True, c1_name = "A > B", c2_name = "B > A"):
        groups_instances    = [ project.get_subjects("grp1"),
                                project.get_subjects("grp2")]
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "2stt_age_gender"
        postmodel           = PostModel("spm_stats_2samples_ttest_contrasts_results",
                                        covs, ["grp1 > grop2", "grp2 > grp1"], ResultsParams("FWE", 0.01, 10))
        spm_analysis.batchrun_spm_vbm_dartel_stats_factdes_2samplesttest(vbm_template_dir, anal_name, groups_instances, covs, post_model=postmodel, runit=False)



        # def batchrun_spm_vbm_dartel_stats_factdes_1Wanova(self, root_outdir, analysis_name, groups_instances, covs,
        #                                                   data_file=None, glob_calc="subj_icv", cov_interaction=None,
        #                                                   expl_mask="icv", spm_template_name="spm_stats_1Wanova_check_estimate",
        #                                                   spm_contrasts_template_name="", runit=True):
        groups_instances    = [ project.get_subjects("grp1"),
                                project.get_subjects("grp2"),
                                project.get_subjects("grp3")]
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "1Wanova_3_groups_age_gender"
        postmodel           = PostModel("fullpath2template", regressors=covs)
        spm_analysis.batchrun_spm_vbm_dartel_stats_factdes_1Wanova(vbm_template_dir, anal_name, groups_instances, covs, post_model=postmodel, runit=False)


        # def batchrun_spm_vbm_dartel_stats_factdes_2Wanova(self, root_outdir, analysis_name, factors, covs=None,
        #                                                   data_file=None, glob_calc="subj_icv", cov_interaction=None,
        #                                                   expl_mask="icv", spm_template_name="spm_stats_2Wanova_check_estimate",
        #                                                   spm_contrasts_template_name="", runit=True):
        factors    = {"labels":["f1", "f2"], "cells": [[project.get_subjects("grp1"), project.get_subjects("grp2")],
                                                       [project.get_subjects("grp3"), project.get_subjects("grp4")]]}
        covs                = [Nuisance("gender"), Nuisance("age")]
        anal_name           = "2Wanova_age_gender"
        postmodel           = PostModel("fullpath2template", regressors=covs)
        spm_analysis.batchrun_spm_vbm_dartel_stats_factdes_2Wanova(vbm_template_dir, anal_name, factors, covs, post_model=postmodel, runit=False)


    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


