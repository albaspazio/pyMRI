import os
from typing import List

from Global import Global
from group.SPMConstants import SPMConstants
from group.spm_utilities import ResultsParams, CatConvResultsParams, Regressor
from utility.fileutilities import remove_ext


class PostModel:
    """
    This class represents a post-model.
    """
    def __init__(self, _type:int, regressors:List[Regressor], templ_name:str=None, contrasts:List[str]=None,
                 res_params:ResultsParams=None, res_conv_params:CatConvResultsParams=None, isSpm:bool=True):
        """
        This function initializes a post-model.

        Args:
            _type (str): The type of the analysis.
            regressors (List[Regressor]): The list of regressors.
            templ_name (str, optional): The name of the template. Defaults to None.
            contrasts (List[str], optional): The list of contrasts. Defaults to None.
            res_params (ResultsParams, optional): The results parameters. Defaults to None.
            res_conv_params (CatConvResultsParams, optional): The results conversion parameters. Defaults to None.
            isSpm (bool, optional): A flag indicating whether the analysis is SPM or not. Defaults to True.
        """
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