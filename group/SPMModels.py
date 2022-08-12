import os

from data.utilities import validate_data_with_covs
from group.SPMCovariates    import SPMCovariates
from group.SPMPostModel     import SPMPostModel
from group.SPMStatsUtils    import SPMStatsUtils
from utility.matlab         import call_matlab_spmbatch
from utility.utilities      import sed_inplace


# create factorial designs, multiple regressions, t-test
class SPMModels:

    def __init__(self, proj):

        self.subjects_list  = None
        self.working_dir    = ""

        self.project        = proj
        self.globaldata     = self.project.globaldata

    # ---------------------------------------------------
    # region VBM

    def batchrun_spm_vbm_dartel_stats_factdes_1group_multregr(self, root_outdir, analysis_name, groups_instances, covs,
                                                              data_file=None, glob_calc="subj_icv", cov_interactions=None, cov_centering=False,
                                                              expl_mask="icv", spm_template_name="group_model_spm_stats_1group_multiregr_estimate",
                                                              post_model=None, runit=True):
        # sanity check
        if bool(covs):
            data_file = self.project.validate_data(data_file)
            validate_data_with_covs(data_file, covs)

        # create template files
        out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr", "vbmdartel_" + analysis_name)
        statsdir                        = os.path.join(root_outdir, "stats", analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose images string
        subjs_dir = os.path.join(root_outdir, "subjects")
        SPMStatsUtils.compose_images_string_1GROUP_MULTREGR(groups_instances[0], out_batch_job, {"type":"dartel", "folder":subjs_dir})

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # ---------------------------------------------------------------------------
        # check whether adding a covariate
        # ---------------------------------------------------------------------------
        if len(covs) > 0:
            SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interactions, data_file, cov_centering)
        else:
            print("ERROR : No covariates in a multiple regression")
            return ""

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=False))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # check whether running a given contrasts batch or a standard multregr. script must only modify SPM.mat file
        if bool(post_model):
            if os.path.exists(post_model.template_name + ".m"):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_1group_multregr_postmodel(self.project, self.globaldata, statsdir, post_model, analysis_name, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")

    # ---------------------------------------------------
    # params to replace: <STATS_DIR>, <GROUP1_IMAGES>, <GROUP2_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # GROUPx_IMAGES are :  'mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_XXXXXXXXXX.gii,1'
    # statsparams = {"mult_corr":"", "pvalue":0.05, "clust_ext":0}
    def batchrun_spm_vbm_dartel_stats_factdes_2samplesttest(self, root_outdir, analysis_name, groups_instances=None, covs=None,
                                                            data_file=None, glob_calc="subj_icv", cov_interaction=None, cov_centering=False,
                                                            expl_mask="icv", spm_template_name="group_model_spm_stats_2samples_ttest_estimate",
                                                            post_model=None, runit=True):
        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr", "vbmdartel_" + analysis_name)
        statsdir                        = os.path.join(root_outdir, "stats", analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        subjs_dir = os.path.join(root_outdir, "subjects")
        SPMStatsUtils.compose_images_string_2sTT(groups_instances, out_batch_job, {"type":"dartel", "folder":subjs_dir})

        # check whether adding a covariate
        SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interaction, data_file, cov_centering)

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=False))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # ---------------------------------------------------------------------------
        # check whether running a given contrasts batch or a standard two-sampled ttest. script must only modify SPM.mat file
        if bool(post_model):
            if os.path.exists(post_model.template_name + ".m"):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_2samplesttest_postmodel(self.project, self.globaldata, statsdir, post_model, analysis_name, eng, runit)
        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)

        return os.path.join(statsdir, "SPM.mat")


    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>, <ITV_SCORES>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def batchrun_spm_vbm_dartel_stats_factdes_1Wanova(self, root_outdir, analysis_name, groups_instances, covs,
                                                      data_file=None, glob_calc="subj_icv", cov_interaction=None, cov_centering=False,
                                                      expl_mask="icv", spm_template_name="group_model_spm_stats_1Wanova_estimate",
                                                      post_model=None, runit=True):
        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr", "vbmdartel_" + analysis_name)
        statsdir                        = os.path.join(root_outdir, "stats", analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose images string
        subjs_dir = os.path.join(root_outdir, "subjects")
        SPMStatsUtils.compose_images_string_1W(groups_instances, out_batch_job, {"type": "dartel", "folder":subjs_dir})

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # check whether adding a covariate
        SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interaction, data_file, cov_centering)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=False))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # check whether running a given contrasts batch. script must only modify SPM.mat file
        if bool(post_model):
            SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <FACTORS_CELLS> must be something like :
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).levels = [1
    #                                                          1];
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).scans = {
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_T15_C_001.gii'
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/rh.sphere.T1_T15_C_001.gii'
    # };
    # cells is [factor][level][subjects_label]
    # factors in a dict with field {"groups_instances":[], "labels":[], "cells": []}
    def batchrun_spm_vbm_dartel_stats_factdes_2Wanova(self, root_outdir, analysis_name, factors, covs=None,
                                                      data_file=None, glob_calc="subj_icv", cov_interaction=None, cov_centering=False,
                                                      expl_mask="icv", spm_template_name="group_model_spm_stats_2Wanova_estimate",
                                                      post_model=None, runit=True):
        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr", "vbmdartel_" + analysis_name)
        statsdir                        = os.path.join(root_outdir, "stats", analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose cells string
        subjs_dir = os.path.join(root_outdir, "subjects")
        SPMStatsUtils.compose_images_string_2W(factors, out_batch_job, {"type":"dartel", "folder":subjs_dir})

        # check whether adding a covariate
        # concatenates all the levels of the two main factors in a single vector. being a simple covariate,
        all_instances = [[]]
        for i in factors["cells"][0]:
            all_instances[0] = all_instances[0] + i
        for i in factors["cells"][1]:
            all_instances[0] = all_instances[0] + i

        SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, all_instances, covs, 1, cov_interaction, data_file, cov_centering)

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, all_instances, data_file)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=False))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # check whether running a given contrasts batch. script must only modify SPM.mat file
        if bool(post_model):
            SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")


    # endregion
    # ---------------------------------------------------
    # region SURFACES THICKNESS (CAT12)
    # ---------------------------------------------------
    def batchrun_cat_thickness_stats_factdes_1group_multregr(self, root_outdir, analysis_name, groups_instances, covs,
                                                             data_file=None, glob_calc="", cov_interactions=None, cov_centering=False,
                                                             expl_mask=None, spm_template_name="group_model_spm_stats_1group_multiregr_estimate",
                                                             post_model=None, runit=True):
        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr", "ct_" + analysis_name)
        statsdir                       = os.path.join(root_outdir, analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose images string
        SPMStatsUtils.compose_images_string_1GROUP_MULTREGR(groups_instances[0], out_batch_job, {"type":"ct"})

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # check whether adding a covariate
        if len(covs) > 0:
            SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interactions, data_file, cov_centering)
        else:
            print("ERROR : No covariates in a multiple regression")
            return ""

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=True))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # check whether running a given contrasts batch. script must only modify SPM.mat file
        if bool(post_model):
            if os.path.exists(post_model.template_name + ".m"):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_1group_multregr_postmodel(self.project, self.globaldata, statsdir, post_model, analysis_name, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")

    # params to replace: <STATS_DIR>, <GROUP1_IMAGES>, <GROUP2_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # GROUPx_IMAGES are :  'mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_XXXXXXXXXX.gii,1'
    # statsparams = {"mult_corr":"", "pvalue":0.05, "clust_ext":0}
    def batchrun_cat_thickness_stats_factdes_2samplesttest(self, root_outdir, analysis_name, groups_instances=None, covs=None,
                                                           data_file=None, glob_calc="", cov_interaction=None, cov_centering=False,
                                                           expl_mask=None, spm_template_name="group_model_spm_stats_2samples_ttest_estimate",
                                                           post_model=None, runit=True):

        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr", "ct_" + analysis_name)
        statsdir                       = os.path.join(root_outdir, analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        SPMStatsUtils.compose_images_string_2sTT(groups_instances, out_batch_job, {"type":"ct"})

        # check whether adding a covariate
        SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interaction, data_file, cov_centering)

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=True))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # ---------------------------------------------------------------------------
        # check whether running a given contrasts batch or a standard two-samples ttest
        if bool(post_model):
            if os.path.exists(post_model.template_name + ".m"):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_2samplesttest_postmodel(self.project, self.globaldata, statsdir, post_model, analysis_name, eng, runit)
        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def batchrun_cat_thickness_stats_factdes_1Wanova(self, root_outdir, analysis_name, groups_instances, covs=None,
                                                     data_file=None, glob_calc="", cov_interaction=None, cov_centering=False,
                                                     expl_mask=None, spm_template_name="group_model_spm_stats_1Wanova_estimate",
                                                     post_model=None, runit=True):

        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr", "ct_" + analysis_name)
        statsdir                       = os.path.join(root_outdir, analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose images string
        SPMStatsUtils.compose_images_string_1W(groups_instances, out_batch_job, {"type": "ct"})

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # check whether adding a covariate
        SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interaction, data_file, cov_centering)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=True))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # check whether running a given contrasts batch or a standard multregr. script must only modify SPM.mat file
        if bool(post_model):
            if os.path.exists(post_model.template_name):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_1wanova_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <FACTORS_CELLS> must be something like :
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).levels = [1
    #                                                          1];
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).scans = {
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_T15_C_001.gii'
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/rh.sphere.T1_T15_C_001.gii'
    # };
    # cells is [factor][level][subjects_label]
    # factors in a dict with field {"groups_instances":[], "labels":[], "cells": []}
    def batchrun_cat_thickness_stats_factdes_2Wanova(self, root_outdir, analysis_name, factors, covs=None,
                                                     data_file=None, glob_calc="", cov_interaction=None, cov_centering=False,
                                                     expl_mask=None, spm_template_name="group_model_spm_stats_2Wanova_estimate",
                                                     post_model=None, runit=True):
        # sanity check
        if bool(covs):
            data = self.project.validate_data(data_file)
            validate_data_with_covs(data, covs)

        # create template files
        out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr", "ct_" + analysis_name)
        statsdir                       = os.path.join(root_outdir, analysis_name)
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose cells string
        SPMStatsUtils.compose_images_string_2W(factors, out_batch_job, {"type":"ct"})

        # check whether adding a covariate
        # concatenates all the levels of the two main factors in a single vector. being a simple covariate,
        all_instances = [[]]
        for i in factors["cells"][0]:
            all_instances[0] = all_instances[0] + i
        for i in factors["cells"][1]:
            all_instances[0] = all_instances[0] + i

        # check whether adding a covariate
        SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, all_instances, covs, 1, cov_interaction, data_file, cov_centering)

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, all_instances, data_file)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=True))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # check whether running a given contrasts batch. script must only modify SPM.mat file
        if bool(post_model):
            SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        os.remove(out_batch_start)
        return os.path.join(statsdir, "SPM.mat")

    # endregion
    # ---------------------------------------------------
