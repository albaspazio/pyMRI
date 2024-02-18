import os

from Global import Global
from Project import Project
from group.PostModel import PostModel
from group.SPMConstants import SPMConstants
from group.SPMContrasts import SPMContrasts
from utility.fileutilities import sed_inplace
from utility.matlab import call_matlab_spmbatch


class SPMPostModel:
    """
    This class contains the static methods that are used to run the SPM post-processing.
    """
    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    @staticmethod
    def batchrun_spm_stats_postmodel(project:Project, _global:Global, statsdir:str, post_model:PostModel, analysis_name:str, analysis_seq:str="mpr", eng=None, runit:bool=True):
        """
        This function is used to calculate the contrasts and report their results on a given, already estimated, SPM.mat.

        Args:
            project (Project): The project object.
            _global (Global): The global object.
            statsdir (str): The directory where the SPM results are stored.
            post_model (PostModel): The post-model object.
            analysis_name (str): The name of the analysis.
            analysis_seq (str, optional): The sequence of the analysis. Defaults to "mpr".
            eng (matlab.engine.matlabengine.MatlabEngine, optional): The Matlab engine. Defaults to None.
            runit (bool, optional): A flag indicating whether to run the analysis or not. Defaults to True.

        Returns:
            None: None.
        """
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
            # SPMContrasts.replace_1WAnova_contrasts(out_batch_job, spmmat, post_model)
            SPMContrasts.replace_contrasts(out_batch_job, spmmat, post_model)

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
    def batchrun_spm_stats_predefined_postmodel(project:Project, _global:Global, statsdir:str, template_name:str, analysis_seq:str="mpr", eng=None, runit:bool=True):
        """
        This function is used to apply an existing contrasts template (in a non-standard location) on an already estimated SPM.mat and report the results.

        Args:
            project (Project): The project object.
            _global (Global): The global object.
            statsdir (str): The directory where the SPM results are stored.
            template_name (str): The name of the template.
            analysis_seq (str, optional): The sequence of the analysis. Defaults to "mpr".
            eng (matlab.engine.matlabengine.MatlabEngine, optional): The Matlab engine. Defaults to None.
            runit (bool, optional): A flag indicating whether to run the analysis or not. Defaults to True.

        Returns:
            None: None.
        """
        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(template_name, analysis_seq)

        spmmat = os.path.join(statsdir, "SPM.mat")

        sed_inplace(out_batch_job, "<SPM_MAT>", spmmat)

        if runit:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])  # open a new session and then end it
            else:
                call_matlab_spmbatch(out_batch_start, eng=eng, endengine=False)  # I assume that the caller will end the matlab session and def dir have been already specified

