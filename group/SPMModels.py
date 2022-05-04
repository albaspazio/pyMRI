import os
import traceback

from data.utilities import validate_data_with_covs
from group.SPMCovariates import SPMCovariates
from group.SPMContrasts import SPMContrasts
from group.SPMStatsUtils import SPMStatsUtils
from utility.exceptions import DataFileException
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


# create factorial designs, multiple regressions, t-test
class SPMModels:

    def __init__(self, proj):

        self.subjects_list  = None
        self.working_dir    = ""

        self.project        = proj
        self.globaldata     = self.project.globaldata

    # ---------------------------------------------------
    # region VBM
    def batchrun_spm_vbm_dartel_stats_factdes_1group_multregr(self, darteldir, analysis_name, grp_labels, cov_names,
                                                              data_file=None, glob_calc="subj_icv", cov_interactions=None,
                                                              expl_mask="icv", sess_id=1,
                                                              spm_template_name="spm_stats_1group_multiregr_check_estimate",
                                                              spm_contrasts_template_name="", runit=True):
        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                        = os.path.join(darteldir, "stats", analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            subjs_dir = os.path.join(darteldir, "subjects")
            self.compose_images_string_1GROUP_MULTREGR(grp_labels[0], out_batch_job, {"type":"dartel", "folder":subjs_dir}, sess_id)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, grp_labels, data_file)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if len(cov_names) > 0:
                SPMCovariates.spm_replace_stats_add_manycov_1group(out_batch_job, grp_labels[0], self.project, cov_names, cov_interactions, data_file)
            else:
                print("ERROR : No covariates in a multiple regression")
                return ""

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            # call matlab
            # ---------------------------------------------------------------------------
            if runit is True:
                eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
            else:
                eng = {}

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.batchrun_spm_stats_predefined_contrasts_results(self.project, self.globaldata, statsdir, spm_contrasts_template_name, eng, runit)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except DataFileException as e:
            raise DataFileException("create_spm_vbm_dartel_stats_factdes_multregr", e.param)

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # ---------------------------------------------------

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>, <ITV_SCORES>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def batchrun_spm_vbm_dartel_stats_factdes_1Wanova(self, darteldir, analysis_name, groups_labels, cov_names,
                                                      data_file=None, glob_calc="subj_icv", cov_interaction=None,
                                                      expl_mask="icv", sess_id=1,
                                                      spm_template_name="spm_stats_1Wanova_check_estimate",
                                                      spm_contrasts_template_name="", runit=True):
        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)   # return data_file header

            # create template files
            out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                        = os.path.join(darteldir, "stats", analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            subjs_dir = os.path.join(darteldir, "subjects")
            self.compose_images_string_1W(groups_labels, out_batch_job, {"type": "dartel", "folder":subjs_dir}, sess_id)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_labels, data_file)

            # check whether adding a covariate
            SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, groups_labels, cov_names, cov_interaction, data_file)

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # call matlab
            if runit is True:
                eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir])
            else:
                eng = {}

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.batchrun_spm_stats_predefined_contrasts_results(self.project, self.globaldata, statsdir, spm_contrasts_template_name, eng, runit)


            return os.path.join(statsdir, "SPM.mat")

        except DataFileException as e:
            raise DataFileException("batchrun_spm_vbm_dartel_stats_factdes_1Wanova", e.param)

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <FACTORS_CELLS> must be something like :
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).levels = [1
    #                                                          1];
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).scans = {
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_T15_C_001.gii'
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/rh.sphere.T1_T15_C_001.gii'
    # };
    # cells is [factor][level][subjects_label]
    # factors in a dict with field {"groups_labels":[], "labels":[], "cells": []}
    def batchrun_vbm_dartel_stats_factdes_2Wanova(self, darteldir, analysis_name, factors, cov_names=None,
                                                  data_file=None, glob_calc="subj_icv", cov_interaction=None,
                                                  expl_mask="icv", sess_id=1,
                                                  spm_template_name="spm_stats_2Wanova_check_estimate",
                                                  spm_contrasts_template_name="", runit=True):
        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                        = os.path.join(darteldir, "stats", analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose cells string
            self.compose_images_string_2W(factors, out_batch_job, {"type":"ct"}, sess_id)

            # check whether adding a covariate
            SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, factors["groups_labels"], cov_names, cov_interaction, data_file)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, factors["groups_labels"], data_file)

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            print("running SPM batch template: " + statsdir)
            if runit is True:
                eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir])
            else:
                eng = {}

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.batchrun_spm_stats_predefined_contrasts_results(self.project, self.globaldata, statsdir, spm_contrasts_template_name, eng)
            eng.quit()

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUP1_IMAGES>, <GROUP2_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # GROUPx_IMAGES are :  'mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_XXXXXXXXXX.gii,1'
    # statsparams = {"mult_corr":"", "pvalue":0.05, "clust_ext":0}
    def batchrun_vbm_dartel_stats_factdes_2samplesttest(self, darteldir, analysis_name, groups_labels=None, cov_names=None,
                                                        data_file=None, glob_calc="subj_icv", cov_interaction=None,
                                                        expl_mask="icv", sess_id=1,
                                                        spm_template_name="spm_stats_2samples_ttest_check_estimate",
                                                        spm_contrasts_template_name="spm_stats_2samplesttest_contrasts_results",
                                                        stats_params=None, runit=True):
        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            if groups_labels is None:
                groups_labels = ["g1", "g2"]

            # create template files
            out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                        = os.path.join(darteldir, "stats", analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            self.compose_images_string_2sTT(groups_labels, out_batch_job, {"type":"ct"}, sess_id)

            # check whether adding a covariate
            SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, groups_labels, cov_names, cov_interaction, data_file)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_labels, data_file)

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            if runit is True:
                call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir])

            # ---------------------------------------------------------------------------
            SPMContrasts.batchrun_spm_stats_2samplesttest_contrasts_results(self.project, self.globaldata, os.path.join(statsdir, "SPM.mat"),
                                                                            groups_labels[0] + " > " + groups_labels[1],
                                                                            groups_labels[1] + " > " + groups_labels[0],
                                                                            spm_contrasts_template_name,
                                                                            stats_params, runit)

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # endregion
    # ---------------------------------------------------
    # region SURFACES THICKNESS (CAT12)
    # ---------------------------------------------------


    #
    def batchrun_cat_thickness_stats_factdes_1group_multregr(self, thicknessdir, analysis_name, groups_labels, cov_names,
                                                             data_file=None, glob_calc="", cov_interactions=None,
                                                             expl_mask=None, sess_id=1,
                                                             spm_template_name="spm_stats_1group_multiregr_check_estimate",
                                                             spm_contrasts_template_name="", runit=True):
        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                       = os.path.join(thicknessdir, analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            self.compose_images_string_1GROUP_MULTREGR(groups_labels[0], out_batch_job, {"type":"ct"}, sess_id)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_labels, data_file)

            # check whether adding a covariate
            if len(cov_names) > 0:
                SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, groups_labels, cov_names, cov_interactions, data_file)
            else:
                print("ERROR : No covariates in a multiple regression")
                return ""

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            # call matlab
            # ---------------------------------------------------------------------------
            if runit is True:
                eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
            else:
                eng = {}

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.batchrun_spm_stats_predefined_contrasts_results(self.project, self.globaldata, statsdir, spm_contrasts_template_name, eng)
            eng.quit()

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def batchrun_cat_thickness_stats_factdes_1Wanova(self, thicknessdir, analysis_name, groups_labels, cov_names=None,
                                                     data_file=None, glob_calc="", cov_interaction=None,
                                                     expl_mask=None, sess_id=1,
                                                     spm_template_name="spm_stats_1Wanova_check_estimate",
                                                     spm_contrasts_template_name="", runit=True):

        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                       = os.path.join(thicknessdir, analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            self.compose_images_string_1W(groups_labels, out_batch_job, {"type": "ct"}, sess_id)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_labels, data_file)

            # check whether adding a covariate
            SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, groups_labels, cov_names, cov_interaction, data_file)

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            if runit is True:
                eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
            else:
                eng = {}
            # ---------------------------------------------------------------------------
            # check whether running a given contrasts batch. script must only modify SPM.mat file
            # ---------------------------------------------------------------------------
            if spm_contrasts_template_name != "":
                SPMContrasts.batchrun_spm_stats_predefined_contrasts_results(self.project, self.globaldata, statsdir, spm_contrasts_template_name, eng, runit)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <FACTORS_CELLS> must be something like :
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).levels = [1
    #                                                          1];
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).scans = {
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_T15_C_001.gii'
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/rh.sphere.T1_T15_C_001.gii'
    # };
    # cells is [factor][level][subjects_label]
    # factors in a dict with field {"groups_labels":[], "labels":[], "cells": []}
    def batchrun_cat_thickness_stats_factdes_2Wanova(self, thicknessdir, analysis_name, factors, cov_names=None,
                                                     data_file=None, glob_calc="", cov_interaction=None,
                                                     expl_mask=None, sess_id=1,
                                                     spm_template_name="cat_thickness_stats_2Wanova_check_estimate",
                                                     spm_contrasts_template_name="", runit=True):

        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                       = os.path.join(thicknessdir, analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose cells string
            self.compose_images_string_2W(factors, out_batch_job, {"type":"ct"}, sess_id)

            # check whether adding a covariate
            SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, factors["groups_labels"], cov_names, cov_interaction, data_file)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, factors["groups_labels"], data_file)

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            print("running SPM batch template: " + statsdir)
            if runit is True:
                eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir])
            else:
                eng = {}

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.batchrun_spm_stats_predefined_contrasts_results(self.project, self.globaldata, statsdir, spm_contrasts_template_name, eng)
            eng.quit()

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUP1_IMAGES>, <GROUP2_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # GROUPx_IMAGES are :  'mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_XXXXXXXXXX.gii,1'
    # statsparams = {"mult_corr":"", "pvalue":0.05, "clust_ext":0}
    def batchrun_cat_thickness_stats_factdes_2samplesttest(self, thicknessdir, analysis_name, groups_labels=None, cov_names=None,
                                                           data_file=None, glob_calc="", cov_interaction=None,
                                                           expl_mask=None, sess_id=1,
                                                           spm_template_name="cat_thickness_stats_2samples_ttest_check_estimate",
                                                           spm_contrasts_template_name="spm_stats_2samplesttest_contrasts_results",
                                                           stats_params=None, runit=True):

        try:
            # sanity check
            validate_data_with_covs(data_file, cov_names)

            if groups_labels is None:
                groups_labels = ["g1", "g2"]

            # create template files
            out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr")
            statsdir                       = os.path.join(thicknessdir, analysis_name)
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            self.compose_images_string_2sTT(groups_labels, out_batch_job, {"type":"ct"}, sess_id)

            # check whether adding a covariate
            SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, groups_labels, cov_names, cov_interaction, data_file)

            # global calculation
            SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_labels, data_file)

            # explicit mask
            SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            if runit is True:
                call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir])

            # ---------------------------------------------------------------------------
            SPMContrasts.batchrun_spm_stats_2samplesttest_contrasts_results(self.project, self.globaldata, os.path.join(statsdir, "SPM.mat"),
                                                                            groups_labels[0] + " > " + groups_labels[1],
                                                                            groups_labels[1] + " > " + groups_labels[0],
                                                                            spm_contrasts_template_name,
                                                                            stats_params, runit)

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""
    # endregion

    # ---------------------------------------------------
    #region ACCESSORY (images composition, data validation)
    # ---------------------------------------------------------------------------
    # compose images string
    # ---------------------------------------------------------------------------
    # image_description: {"type": ct | dartel | vbm, "folder": root path for dartel}
    def compose_images_string_1GROUP_MULTREGR(self, grp_label, out_batch_job, img_description, sess_id=1):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_1W: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if os.path.isdir(img_description["folder"]) is False:
                print("ERROR in compose_images_string_1W: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        cells_images = "\r"

        subjs = self.project.get_subjects(grp_label, sess_id)
        img = ""
        for subj in subjs:
            if img_type == "ct":
                img = eval("subj.t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            cells_images = cells_images + "\'" + img + "\'\r"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    def compose_images_string_1W(self, groups_labels, out_batch_job, img_description, sess_id=1):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_1W: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if os.path.isdir(img_description["folder"]) is False:
                print("ERROR in compose_images_string_1W: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        cells_images = ""
        gr = 0
        for grp in groups_labels:
            gr              = gr + 1
            cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(" + str(gr) + ").scans = "

            subjs           = self.project.get_subjects(grp, sess_id)
            img             = ""
            grp1_images     = "{\n"
            for subj in subjs:

                if img_type == "ct":
                    img = eval("subj.t1_cat_resampled_surface")
                elif img_type == "dartel":
                    img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                grp1_images = grp1_images + "\'" + img + "\'\n"
            grp1_images = grp1_images + "\n};"

            cells_images = cells_images + grp1_images + "\n"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    def compose_images_string_2W(self, factors, out_batch_job, img_description, sess_id=1):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_2W: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if os.path.isdir(img_description["folder"]) is False:
                print("ERROR in compose_images_string_2W: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        factors_labels  = factors["labels"]
        cells           = factors["cells"]

        # nfactors = len(factors_labels)
        nlevels = [len(cells), len(cells[0])]  # nlevels for each factor

        # checks
        # if nfactors != len(cells):
        #     print("Error: num of factors labels (" + str(nfactors) + ") differs from cells content (" + str(len(cells)) + ")")
        #     return

        cells_images = ""
        ncell = 0
        for f1 in range(0, nlevels[0]):
            for f2 in range(0, nlevels[1]):
                ncell           = ncell + 1
                cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(ncell) + ").levels = [" + str(f1 + 1) + "\n" + str(f2 + 1) + "];\n"
                cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(ncell) + ").scans = {\n"

                subjs           = self.project.get_subjects(cells[f1][f2], sess_id)
                img             = ""
                for subj in subjs:

                    if img_type == "ct":
                        img = eval("subj.t1_cat_resampled_surface")
                    elif img_type == "dartel":
                        img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                    cells_images = cells_images + "'" + img + "'\n"
                cells_images = cells_images + "};"

        sed_inplace(out_batch_job, "<FACTOR1_NAME>",    factors_labels[0])
        sed_inplace(out_batch_job, "<FACTOR1_NLEV>",    str(nlevels[0]))
        sed_inplace(out_batch_job, "<FACTOR2_NAME>",    factors_labels[1])
        sed_inplace(out_batch_job, "<FACTOR2_NLEV>",    str(nlevels[1]))
        sed_inplace(out_batch_job, "<FACTORS_CELLS>",   cells_images)

    def compose_images_string_2sTT(self, groups_labels, out_batch_job, img_description, sess_id=1):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_2sTT: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if os.path.isdir(img_description["folder"]) is False:
                print("ERROR in compose_images_string_2sTT: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        subjs1      = self.project.get_subjects(groups_labels[0], sess_id)
        subjs2      = self.project.get_subjects(groups_labels[1], sess_id)

        grp1_images = "{\n"
        img         = ""
        for subj in subjs1:

            if img_type == "ct":
                img = eval("subj.t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            grp1_images = grp1_images + "\'" + img + "\'\n"
        grp1_images = grp1_images + "\n}"

        grp2_images = "{\n"
        for subj in subjs2:

            if img_type == "ct":
                img = eval("subj.t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            grp2_images = grp2_images + "\'" + img + "\'\n"
        grp2_images = grp2_images + "\n}"

        # set job file
        sed_inplace(out_batch_job, "<GROUP1_IMAGES>", grp1_images)
        sed_inplace(out_batch_job, "<GROUP2_IMAGES>", grp2_images)
    #endregion
    # ---------------------------------------------------
