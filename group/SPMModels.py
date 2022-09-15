import os

from data.utilities import validate_data_with_covs
from group.SPMCovariates    import SPMCovariates
from group.SPMPostModel     import SPMPostModel
from group.SPMStatsUtils    import SPMStatsUtils
from group.spm_utilities import GrpInImages
from utility.matlab         import call_matlab_spmbatch
from utility.utilities      import sed_inplace


# create factorial designs, multiple regressions, t-test
class SPMModels:

    MULTREGR    = 1
    OSTT        = 2
    TSTT        = 3
    OWA         = 4
    TWA         = 5

    VBM_DARTEL  = 11
    CAT         = 12
    FMRI        = 13

    stats_types     = [MULTREGR, OSTT, TSTT, OWA, TWA]
    analysis_types  = [VBM_DARTEL, CAT, FMRI]

    def __init__(self, proj):

        self.project        = proj
        self.globaldata     = self.project.globaldata

    # anal_type is: vbm, cat, fmri
    # stat_type is: MULTREGR, tstt, ostt, owa, twa
    def batchrun_group_stats(self, root_outdir, stat_type, anal_type, anal_name, groups_instances, input_images=None,
                             covs=None, cov_interactions=None, cov_centering=False, data_file=None,
                             glob_calc=None, expl_mask="icv", spm_template_name="group_model_spm_stats_1group_multiregr_estimate",
                             post_model=None, runit=True):

        # ---------------------------------------------------------------------------------------------------------------------------------
        # sanity check
        if bool(covs):
            data_file = self.project.validate_data(data_file)
            validate_data_with_covs(data_file, covs)
        else:
            if stat_type == self.MULTREGR:
                raise Exception("Error in batchrun_group_stats: covs cannot be empty or none when one group mult regr is asked")

        if stat_type not in stats_types:
            raise Exception("Error in batchrun_group_stats: unrecognized stat type: " + str(stat_type))

        if anal_type not in anal_types:
            raise Exception("Error in batchrun_group_stats: unrecognized analysis type: " + str(anal_type))

        # ---------------------------------------------------------------------------------------------------------------------------------
        if anal_type == self.VBM_DARTEL:
            subjs_dir = os.path.join(root_outdir, "subjects")
            if input_images is None:
                input_images = GrpInImages("dartel", subjs_dir)

            if glob_calc is None:
                glob_calc   = "subj_icv"

            if expl_mask is None:
                glob_calc   = "icv"

            batch_folder    = "mpr"
            batch_prefix    = "vbmdartel_"
            statsdir        = os.path.join(root_outdir, "stats", analysis_name)

        elif anal_type == self.CAT:
            input_images = GrpInImages("ct")
            glob_calc       = ""
            statsdir        = os.path.join(root_outdir, anal_name)

            batch_folder    = "mpr"
            batch_prefix    = "cat_"
            expl_mask       = None
            statsdir        = os.path.join(root_outdir, analysis_name)

        elif anal_type == self.FMRI:
            if input_images is None:
                raise Exception("Error in batchrun_fmri_stats_factdes_2samplesttest: input_images cannot be None")
            glob_calc       = ""
            batch_folder    = "fmri"
            batch_prefix    = ""
            expl_mask       = None
            statsdir        = os.path.join(root_outdir, analysis_name)

        # -------------------------------------------------------------------------------------------------------------------------
        # create template files
        # -------------------------------------------------------------------------------------------------------------------------
        if spm_template_name is None:
            if stat_type == self.MULTREGR:
                spm_template_name = "group_model_spm_stats_1group_multiregr_estimate"
            elif stat_type == self.TSTT:
                spm_template_name = "group_model_spm_stats_2samples_ttest_estimate"
            elif stat_type == self.OWA:
                spm_template_name = "group_model_spm_stats_1Wanova_estimate"
            elif stat_type == self.TWA:
                spm_template_name = "group_model_spm_stats_2Wanova_estimate"
        out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, batch_folder, batch_prefix + analysis_name)

        # -------------------------------------------------------------------------------------------------------------------------
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # -------------------------------------------------------------------------------------------------------------------------
        # compose images string
        if stat_type == self.MULTREGR:
            SPMStatsUtils.compose_images_string_1GROUP_MULTREGR(groups_instances[0], out_batch_job, input_images)
            if spm_template_name is None:
                spm_template_name = "group_model_spm_stats_1group_multiregr_estimate"

        elif stat_type == self.TSTT:
            SPMStatsUtils.compose_images_string_2sTT(groups_instances, out_batch_job, input_images)
            if spm_template_name is None:
                spm_template_name = "group_model_spm_stats_2samples_ttest_estimate"

        elif stat_type == self.OWA:
            SPMStatsUtils.compose_images_string_1W(groups_instances, out_batch_job, input_images)
            if spm_template_name is None:
                spm_template_name = "group_model_spm_stats_1Wanova_estimate"

        elif stat_type == self.TWA:
            SPMStatsUtils.compose_images_string_2W(groups_instances, out_batch_job, input_images)
            if spm_template_name is None:
                spm_template_name = "group_model_spm_stats_2Wanova_estimate"

        # -------------------------------------------------------------------------------------------------------------------------
        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances, data_file)

        # -------------------------------------------------------------------------------------------------------------------------
        # check whether adding a covariate
        if len(covs) > 0:
            SPMCovariates.spm_replace_stats_add_simplecovariates(self.project, out_batch_job, groups_instances, covs, 1, cov_interactions, data_file, cov_centering)
        else:
            print("ERROR : No covariates in a multiple regression")
            return ""

        # -------------------------------------------------------------------------------------------------------------------------
        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # -------------------------------------------------------------------------------------------------------------------------
        # model estimate
        if anal_type == self.CAT:
            sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=True))
        else:
            sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=False))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = {}

        # -------------------------------------------------------------------------------------------------------------------------
        # check whether running a given contrasts batch or a standard multregr. script must only modify SPM.mat file
        if bool(post_model):
            if os.path.exists(post_model.template_name + ".m"):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model.template_name, batch_folder, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_postmodel(self.project, self.globaldata, statsdir, post_model, analysis_name, batch_folder, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        return os.path.join(statsdir, "SPM.mat")
