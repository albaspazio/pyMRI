import os
import traceback
from shutil import move

from data.SubjectsDataDict import SubjectsDataDict
from group.SPMCovariates import SPMCovariates
from group.SPMContrasts import SPMContrasts
from group.SPMStatsUtils import SPMStatsUtils
from utility.exceptions import DataFileException
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


# create factorial designs, multiple regressions, t-test
class SPMModels:

    def __init__(self, proj):

        self.subjects_list = None
        self.working_dir = ""

        self.project = proj
        self._global = self.project._global

    # ---------------------------------------------------
    # region VBM
    # ---------------------------------------------------

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>, <ITV_SCORES>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def create_spm_vbm_dartel_stats_factdes_1Wanova(self, darteldir, groups_labels, cov_name, cov_interaction=1,
                                                    data_file=None, glob_calc="subj_icv", cov_interactions=None,
                                                    expl_mask="icv", sess_id=1,
                                                    spm_template_name="spm_stats_1Wanova_check_estimate"):

        try:
            # sanity check
            self.validate_data(data_file, [cov_name])   # return data_file header

            # create template files
            out_batch_job, out_batch_start = self.project.create_batch_files(spm_template_name, "mpr")
            statsdir                       = os.path.join(darteldir, "stats")
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            subjs_dir = os.path.join(darteldir, "subjects")
            self.compose_images_string_1W(groups_labels, out_batch_job, {"type": "dartel", "folder":subjs_dir}, sess_id)

            # global calculation
            SPMStatsUtils.global_calculation(self.project, out_batch_job, glob_calc, groups_labels, data_file)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if cov_name != "":
                SPMCovariates.spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, self.project, cov_name, cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # explicit mask
            SPMStatsUtils.explicit_mask(self._global, out_batch_job, expl_mask)

            # call matlab
            call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

            return os.path.join(statsdir, "SPM.mat")

        except DataFileException as e:
            raise DataFileException("create_spm_vbm_dartel_stats_factdes_1Wanova", e.param)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def create_spm_vbm_dartel_stats_factdes_multregr(self, darteldir, grp_label, cov_names,
                                                     data_file=None, glob_calc="subj_icv", cov_interactions=None,
                                                     expl_mask="icv", sess_id=1,
                                                     spm_template_name="spm_stats_1group_multiregr_check_estimate",
                                                     spm_contrasts_template_name="",
                                                     mult_corr="FWE", pvalue=0.05, cluster_extend=0):
        try:
            # sanity check
            self.validate_data(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start  = self.project.create_batch_files(spm_template_name, "mpr")
            statsdir                        = os.path.join(darteldir, "stats")
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            subjs_dir = os.path.join(darteldir, "subjects")
            self.compose_images_string_1GROUP_MULTREGR(grp_label, out_batch_job, {"type":"dartel", "folder":subjs_dir}, sess_id)

            # global calculation
            SPMStatsUtils.global_calculation(self.project, out_batch_job, glob_calc, [grp_label], data_file)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if len(cov_names) > 0:
                SPMCovariates.spm_stats_add_manycov_1group(out_batch_job, grp_label, self.project, cov_names, cov_interactions, data_file)
            else:
                print("ERROR : No covariates in a multiple regression")
                return ""

            # explicit mask
            SPMStatsUtils.explicit_mask(self._global, out_batch_job, expl_mask)

            # ---------------------------------------------------------------------------
            # call matlab
            # ---------------------------------------------------------------------------
            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=False)

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.create_spm_stats_predefined_contrasts_results(self.project, self._global, statsdir, spm_contrasts_template_name, eng)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except DataFileException as e:
            raise DataFileException("create_spm_vbm_dartel_stats_factdes_multregr", e.param)

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # endregion

    # ---------------------------------------------------
    # region SURFACES THICKNESS (CAT12)
    # ---------------------------------------------------


    #
    def create_cat_thickness_stats_factdes_1group_multregr(self, statsdir, grp_label, cov_names, anal_name,
                                                           cov_interactions=None, data_file=None, sess_id=1,
                                                           spm_template_name="spm_stats_1group_multiregr_check_estimate",
                                                           spm_contrasts_template_name="", mult_corr="FWE", pvalue=0.05,
                                                           cluster_extend=0):
        try:
            # sanity check
            self.validate_data(data_file, cov_names)

            # create template files
            out_batch_job, out_batch_start = self.project.create_batch_files(spm_template_name, "mpr")
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            self.compose_images_string_1GROUP_MULTREGR(grp_label, out_batch_job, {"type":"ct"}, sess_id)

            # global calculation
            SPMStatsUtils.global_calculation(self.project, out_batch_job)
            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            if len(cov_names) > 0:
                SPMCovariates.spm_stats_add_manycov_1group(out_batch_job, grp_label, self.project, cov_names, cov_interactions, data_file)
            else:
                print("ERROR : No covariates in a multiple regression")
                return ""

            # explicit mask
            SPMStatsUtils.explicit_mask(self._global, out_batch_job)

            # ---------------------------------------------------------------------------
            # call matlab
            # ---------------------------------------------------------------------------
            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=False)

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                SPMContrasts.create_spm_stats_predefined_contrasts_results(self.project, self._global, statsdir, spm_contrasts_template_name, eng)

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
    def create_cat_thickness_stats_factdes_1Wanova(self, statsdir, groups_labels, cov_name, cov_interaction=1,
                                                   data_file=None, sess_id=1,
                                                   spm_template_name="spm_stats_1Wanova_check_estimate",
                                                   spm_contrasts_template_name=""):

        try:
            # sanity check
            self.validate_data(data_file, [cov_name])

            # create template files
            out_batch_job, out_batch_start = self.project.create_batch_files(spm_template_name, "mpr")
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose images string
            self.compose_images_string_1W(groups_labels, out_batch_job, {"type": "ct"}, sess_id)

            # global calculation
            SPMStatsUtils.global_calculation(self.project, out_batch_job)
            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if cov_name != "":
                SPMCovariates.spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, self.project, cov_name, cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # explicit mask
            SPMStatsUtils.explicit_mask(self._global, out_batch_job)
            # ---------------------------------------------------------------------------
            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=False)

            # ---------------------------------------------------------------------------
            # check whether running a given contrasts batch. script must only modify SPM.mat file
            # ---------------------------------------------------------------------------
            if spm_contrasts_template_name != "":
                SPMContrasts.create_spm_stats_predefined_contrasts_results(self.project, self._global, statsdir, spm_contrasts_template_name, eng)

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
    def create_cat_thickness_stats_factdes_2Wanova(self, statsdir, factors_labels, cells, cov_name="",
                                                   cov_interaction=1, data_file=None, sess_id=1,
                                                   spm_template_name="cat_thickness_stats_2Wanova_check_estimate"):

        try:
            # sanity check
            self.validate_data(data_file, [cov_name])

            # create template files
            out_batch_job, out_batch_start = self.project.create_batch_files(spm_template_name, "mpr")
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # compose cells string
            self.compose_images_string_2W(factors_labels, cells, out_batch_job, {"type":"ct"}, sess_id)

            groups_labels = []  # will host the subjects labels for covariate specification
            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if cov_name != "":
                SPMCovariates.spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, self.project, cov_name, cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # global calculation
            SPMStatsUtils.global_calculation(self.project, out_batch_job)

            # explicit mask
            SPMStatsUtils.explicit_mask(self._global, out_batch_job)
            # ---------------------------------------------------------------------------
            print("running SPM batch template: " + statsdir)
            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=False)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUP1_IMAGES>, <GROUP2_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # GROUPx_IMAGES are :  'mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_XXXXXXXXXX.gii,1'
    def create_cat_thickness_stats_factdes_2samplesttest(self, statsdir, grp1_label, grp2_label, cov_name="",
                                                         cov_interaction=1, data_file=None, sess_id=1,
                                                         spm_template_name="cat_thickness_stats_2samples_ttest_check_estimate",
                                                         mult_corr="FWE", pvalue=0.05, cluster_extend=0,
                                                         grp_labels=None):

        try:
            # sanity check
            self.validate_data(data_file, [cov_name])

            if grp_labels is None:
                grp_labels = ["g1", "g2"]

            # create template files
            out_batch_job, out_batch_start = self.project.create_batch_files(spm_template_name, "mpr")
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # get subjects lists
            if isinstance(grp1_label, str):
                grp_labels[0] = grp1_label
            if isinstance(grp2_label, str):
                grp_labels[1] = grp2_label

            self.compose_images_string_2sTT(grp1_label, grp2_label, out_batch_job, {"type":"ct"}, sess_id)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            if cov_name != "":
                SPMCovariates.spm_stats_add_1cov_manygroups(out_batch_job, [grp1_label, grp2_label], self.project, cov_name, cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # global calculation
            SPMStatsUtils.global_calculation(self.project, out_batch_job)

            # explicit mask
            SPMStatsUtils.explicit_mask(self._global, out_batch_job)

            # ---------------------------------------------------------------------------
            call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

            # ---------------------------------------------------------------------------
            SPMContrasts.create_spm_stats_2samplesttest_contrasts_results(self.project, self._global, os.path.join(statsdir, "SPM.mat"),
                                                                  grp_labels[0] + " > " + grp_labels[1],
                                                                  grp_labels[1] + " > " + grp_labels[0],
                                                                  "spm_stats_2samplesttest_contrasts_results",
                                                                  mult_corr, pvalue, cluster_extend)

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # endregion

    # ---------------------------------------------------
    #region ACCESSORY (images composition, data validation)
    # ---------------------------------------------------------------------------
    # validate data
    # ---------------------------------------------------------------------------
    def validate_data(self, data_file=None, cov_names=None):

        if cov_names is None:
            cov_names = []

        header = []
        if data_file is not None:
            if os.path.exists(data_file) is False:
                raise DataFileException("validate_data", "given data_file (" + str(data_file) + ") does not exist")

            header = SubjectsDataDict(data_file).get_header()  # get_header_of_tabbed_file(data_file)

            # if all(elem in header for elem in cov_names) is False:  if I don't want to understand which cov is absent
            missing_covs = ""
            for cov_name in cov_names:
                if cov_name in header is False:
                    missing_covs = missing_covs + cov_name + ", "

            if len(missing_covs) > 0:
                raise DataFileException("validate_data", "the following header are NOT present in the given datafile: " + missing_covs)

        return header

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
                img = eval(subj + ".t1_cat_resampled_surface")
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
                    img = eval(subj + ".t1_cat_resampled_surface")
                elif img_type == "dartel":
                    img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                grp1_images = grp1_images + "\'" + img + "\'\n"
            grp1_images = grp1_images + "\n};"

            cells_images = cells_images + grp1_images + "\n"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    def compose_images_string_2W(self, factors_labels, cells, out_batch_job, img_description, sess_id=1):

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


        nfactors = len(factors_labels)
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
                        img = eval(subj + ".t1_cat_resampled_surface")
                    elif img_type == "dartel":
                        img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                    cells_images = cells_images + "'" + img + "'\n"
                cells_images = cells_images + "};"

        sed_inplace(out_batch_job, "<FACTOR1_NAME>",    factors_labels[0])
        sed_inplace(out_batch_job, "<FACTOR1_NLEV>",    str(nlevels[0]))
        sed_inplace(out_batch_job, "<FACTOR2_NAME>",    factors_labels[1])
        sed_inplace(out_batch_job, "<FACTOR2_NLEV>",    str(nlevels[1]))
        sed_inplace(out_batch_job, "<FACTORS_CELLS>",   cells_images)

    def compose_images_string_2sTT(self, grp1_label, grp2_label, out_batch_job, img_description, sess_id=1):

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

        subjs1      = self.project.get_subjects(grp1_label, sess_id)
        subjs2      = self.project.get_subjects(grp2_label, sess_id)

        grp1_images = "{\n"
        img         = ""
        for subj in subjs1:

            if img_type == "ct":
                img = eval(subj + ".t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            grp1_images = grp1_images + "\'" + img + "\'\n"
        grp1_images = grp1_images + "\n}"

        grp2_images = "{\n"
        for subj in subjs2:

            if img_type == "ct":
                img = eval(subj + ".t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            grp2_images = grp2_images + "\'" + img + "\'\n"
        grp2_images = grp2_images + "\n}"

        # set job file
        sed_inplace(out_batch_job, "<GROUP1_IMAGES>", grp1_images)
        sed_inplace(out_batch_job, "<GROUP2_IMAGES>", grp2_images)

    #endregion

    # ---------------------------------------------------
