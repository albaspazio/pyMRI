import os

from group.SPMContrasts import SPMContrasts
from group.spm_utilities import PostModel
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


class SPMPostModel:

    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    @staticmethod
    def batchrun_spm_stats_postmodel(project, _global, statsdir, post_model, analysis_name, analysis_seq="mpr", eng=None, runit=True):

        if post_model.isSpm:
            prefix = "spm_" + analysis_name
        else:
            prefix = "ct_" + analysis_name

        spmmat = os.path.join(statsdir, "SPM.mat")

        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(post_model.template_name, analysis_seq, prefix)

        postmodel_type = post_model.type
        if postmodel_type == PostModel.MULTREGR:
            SPMContrasts.replace_1group_multregr_contrasts(out_batch_job, spmmat, post_model)

        elif postmodel_type == PostModel.OWA:
            SPMContrasts.replace_1WAnova_contrasts(out_batch_job, spmmat, post_model)

        elif postmodel_type == PostModel.TSTT:
            SPMContrasts.replace_contrasts(out_batch_job, spmmat, post_model)

        # elif postmodel_type == PostModel.TWA:
        # elif postmodel_type == PostModel.OSTT:
        else:
            raise Exception("Error in batchrun_spm_stats_postmodel: given postmodel analysis type (" + postmodel_type + ") is not managed")

        sed_inplace(out_batch_job, "<MULT_CORR>"        , post_model.results_params.mult_corr)
        sed_inplace(out_batch_job, "<PVALUE>"           , str(post_model.results_params.pvalue))
        sed_inplace(out_batch_job, "<CLUSTER_EXTEND>"   , str(post_model.results_params.cluster_extend))

        if runit:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])
            else:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir], eng=eng)

    # apply an existing contrasts template (in a non-standard location) on an already estimated SPM.mat and report the results
    # only need to set the SPM.mat path
    @staticmethod
    def batchrun_spm_stats_predefined_postmodel(project, _global, statsdir, template_name, analysis_seq="mpr", eng=None, runit=True):

        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(template_name, analysis_seq)

        spmmat = os.path.join(statsdir, "SPM.mat")

        sed_inplace(out_batch_job, "<SPM_MAT>", spmmat)

        if runit:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])  # open a new session and then end it
            else:
                call_matlab_spmbatch(out_batch_start, eng=eng, endengine=False)  # I assume that the caller will end the matlab session and def dir have been already specified
