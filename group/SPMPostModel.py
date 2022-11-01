import os

from Global import Global
from group.SPMContrasts import SPMContrasts
from group.SPMConstants import SPMConstants
from group.spm_utilities import ResultsParams
from utility.matlab import call_matlab_spmbatch
from utility.fileutilities import sed_inplace, remove_ext


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
        if postmodel_type == SPMConstants.MULTREGR:
            SPMContrasts.replace_1group_multregr_contrasts(out_batch_job, spmmat, post_model)

        elif postmodel_type == SPMConstants.OWA:
            SPMContrasts.replace_1WAnova_contrasts(out_batch_job, spmmat, post_model)

        elif postmodel_type == SPMConstants.TSTT:
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


class PostModel:


    def __init__(self, _type, regressors, templ_name=None, contrasts=None, res_params=None, res_conv_params=None, isSpm=True):

        if _type not in SPMConstants.stats_types:
            raise Exception("Error in PostModel: given analysis tyoe (" + _type + ") is not recognized")

        if contrasts is None:
            contrasts = []

        if templ_name is None:
            if isSpm:
                templ_name = "group_postmodel_spm_stats_contrasts_results"
            else:
                templ_name = "group_postmodel_cat_stats_contrasts_results"

        templ_name = remove_ext(templ_name)

        # check if template name is valid according to the specification applied in Project.adapt_batch_files
        # it can be a full path (without extension) of an existing file, or a file name present in pymri/templates/spm (without "_job.m)
        if not os.path.exists(templ_name + ".m"):
            if not os.path.exists(os.path.join(Global.get_spm_template_dir(), templ_name + "_job.m")):
                raise Exception("given post_model template name (" + templ_name + ") is not valid")

        self.type           = _type
        self.template_name  = templ_name

        self.contrasts      = contrasts   # list of strings
        self.regressors     = regressors    # list of subtypes of Regressors
        self.isSpm          = isSpm

        if res_params is None:
            self.results_params = ResultsParams()   # standard (FWE, 0.05, 0)
        else:
            self.results_params = res_params  # of type (CatConv)ResultsParams

        # if res_conv_params is None, do not create a default value, means I don't want to convert results
        if not isSpm and bool(res_conv_params):
            self.results_conv_params = res_conv_params