import ntpath
import os
import traceback

from group.SPMContrasts import SPMContrasts
from group.SPMResults import SPMResults
from group.SPMStatsUtils import ResultsParams
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


class SPMPostModel:

    # run a prebuilt batch file in a non-standard location, which only need to set the stat folder and SPM.mat path
    @staticmethod
    def batchrun_spm_stats_predefined_postmodel(project, _global, statsdir, post_model, eng=None, runit=True):

        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(post_model.template_name, "mpr")

        spm_mat_path = os.path.join(statsdir, "SPM.mat")

        sed_inplace(out_batch_job, "<SPM_MAT>", spm_mat_path)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        if runit is True:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])  # open a new session and then end it
            else:
                call_matlab_spmbatch(out_batch_start, eng=eng, endengine=False)  # I assume that the caller will end the matlab session and def dir have been already specified


    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def batchrun_spm_stats_2samplesttest_postmodel(project, _global, statsdir, post_model, eng=None, runit=True):

        spmmat = os.path.join(statsdir, "SPM.mat")
        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(post_model.template_name, "mpr")

        sed_inplace(out_batch_job, "<SPM_MAT>"          , spmmat)
        sed_inplace(out_batch_job, "<STATS_DIR>"        , statsdir)
        sed_inplace(out_batch_job, "<C1_NAME>"          , post_model.regressors[0].name)
        sed_inplace(out_batch_job, "<C2_NAME>"          , post_model.regressors[1].name)
        sed_inplace(out_batch_job, "<MULT_CORR>"        , post_model.results_params.mult_corr)
        sed_inplace(out_batch_job, "<PVALUE>"           , str(post_model.results_params.pvalue))
        sed_inplace(out_batch_job, "<CLUSTER_EXTEND>"   , str(post_model.results_params.cluster_extend))

        # SPMResults.runbatch_cat_results_trasformation(out_batch_job, 3, post_model.results_params.mult_corr, post_model.results_params.pvalue, post_model.results_params.cluster_extend)

        if runit is True:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])
            else:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir], eng=eng, endengine=False)


    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def batchrun_spm_stats_1group_multregr_postmodel(project, _global, statsdir, post_model, eng=None, runit=True):

        spmmat = os.path.join(statsdir, "SPM.mat")

        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(post_model.template_name, "mpr")

        sed_inplace(out_batch_job, "<SPM_MAT>"  , spmmat)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        SPMContrasts.replace_1group_multregr_contrasts(out_batch_job, post_model)

        sed_inplace(out_batch_job, "<MULT_CORR>"        , post_model.results_params.mult_corr)
        sed_inplace(out_batch_job, "<PVALUE>"           , str(post_model.results_params.pvalue))
        sed_inplace(out_batch_job, "<CLUSTER_EXTEND>"   , str(post_model.results_params.cluster_extend))

        if runit is True:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])
            else:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir], eng=eng, endengine=False)

