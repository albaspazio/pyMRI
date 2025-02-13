from __future__ import annotations

import os
from typing import List

from Global import Global
from Project import Project
from subject.Subject import Subject
from data.SubjectsData import SubjectsData

from group.SPMCovariates    import SPMCovariates
from group.SPMPostModel     import SPMPostModel, PostModel
from group.SPMStatsUtils    import SPMStatsUtils
from group.SPMConstants     import SPMConstants
from group.spm_utilities    import GrpInImages, Regressor, Contrast

from myutility.matlab         import call_matlab_spmbatch
from myutility.fileutilities  import sed_inplace
from myutility.list import is_list_of

# create factorial designs, multiple regressions, t-test
class SPMModels:
    """
    This class contains methods for running group analyses using SPM.
    """
    def __init__(self, proj:Project):
        """
        Initialize the SPMModels class.

        Parameters
        ----------
        proj : instance of Project
            The project object that contains information about the project.
        """
        self.project:Project    = proj
        self.globaldata:Global  = self.project.globaldata

    def batchrun_group_stats(self,  root_outdir:str,        # group analysis root folder :  fmri_dir/ct_dir/vbm_template_dir
                                    stat_type:int,          # MULTREGR, tstt, ostt, owa, twa
                                    anal_type:int,          # vbm, ct, fmri, dartel
                                    anal_name:str,          # output analysis name
                                    groups_instances:List[List[Subject]], #
                                    input_images:GrpInImages=None,  # instance of class GrpInImages, containing info to retrieve input images
                                    covs:List[Regressor]=None, cov_interactions:List[int]=None, cov_centering:bool=False, data:str|SubjectsData=None,
                                    glob_calc:str=None, expl_mask:str="icv", spm_template_name:str=None,
                                    post_model:PostModel=None, runit:bool=True, mustExist:bool=True):
        """
        Run a group analysis using SPM.

        Parameters
        ----------
        root_outdir : str
            The root output directory for the group analysis.
        stat_type : int
            The type of statistical analysis to perform. Can be one of SPMConstants values: "MULTREGR", "OSTT", "TSTT", "OWA", or "TWA".
        anal_type : int
            The type of analysis to perform. Can be one of SPMConstants values: VBM_DARTEL, CAT, or FMRI.
        anal_name : str
            The name of the analysis. This will be used to create the output directory and other filenames.
        groups_instances : List[List[Subject]]
            The list of group instances to analyze.
        input_images : instance of GrpInImages, optional
            The input images object, containing information about the input images. If not provided, it will be
            automatically retrieved based on the analysis type.
        covs : List[Regressor], optional
            The list of covariates to add to the analysis.
        cov_interactions :  List[int], optional
            The list of covariate interactions to add to the analysis.
        cov_centering : bool, optional
            Whether to center the covariates before adding them to the analysis.
        data : str, optional
            The name of the data file to use. If not provided, it will be automatically retrieved from the project.
        glob_calc : str, optional
            The global calculation to perform.
        expl_mask : str, optional
            The explicit mask to use.
        spm_template_name : str, optional
            The name of the SPM template to use. If not provided, it will be automatically determined based on the
            analysis type and statistical analysis.
        post_model : instance of PostModel, optional
            The post-model to use. If not provided, a standard multilevel regression analysis will be performed.
        runit : bool, optional
            Whether to actually run SPM or just print the commands.
        mustExist : bool, optional
            Whether to raise an exception if the input images do not exist.
        Returns
        -------
        str
            The path to the SPM.mat file generated by the analysis.
        """
        # ---------------------------------------------------------------------------------------------------------------------------------
        # sanity check
        subj_data_dict = None
        if bool(covs):
            subj_data_dict = self.project.validate_data(data)
            subj_data_dict.validate_covs(covs)
        else:
            if stat_type == SPMConstants.MULTREGR:
                raise Exception("Error in batchrun_group_stats: covs cannot be empty or none when one group mult regr is asked")

        if stat_type not in SPMConstants.stats_types:
            raise Exception("Error in batchrun_group_stats: unrecognized stat type: " + str(stat_type))

        if anal_type not in SPMConstants.analysis_types:
            raise Exception("Error in batchrun_group_stats: unrecognized analysis type: " + str(anal_type))

        if bool(post_model):
            if not os.path.exists(post_model.template_name + ".m") and post_model.type != SPMConstants.MULTREGR and not is_list_of(post_model.contrasts, Contrast):
                raise Exception("Error in SPMModels.batchrun_group_stats, a post model template is not given and contrasts list is not of type Contrast")

        # ---------------------------------------------------------------------------------------------------------------------------------
        statsdir        = ""
        batch_folder    = ""
        batch_prefix    = ""

        if anal_type == SPMConstants.VBM_DARTEL:
            subjs_dir = os.path.join(root_outdir, "subjects")
            if input_images is None:
                input_images = GrpInImages(anal_type, subjs_dir)

            if glob_calc is None:
                glob_calc   = "subj_icv"

            if expl_mask is None:
                glob_calc   = "icv"

            batch_folder    = "mpr"
            batch_prefix    = "vbmdartel_"
            statsdir        = os.path.join(root_outdir, "stats", anal_name)

        elif anal_type == SPMConstants.CT or anal_type == SPMConstants.GYR or anal_type == SPMConstants.SDEP:
            input_images = GrpInImages(anal_type)
            glob_calc       = ""

            batch_folder    = "mpr"
            batch_prefix    = "cat_"
            expl_mask       = None
            statsdir        = os.path.join(root_outdir, anal_name)

        elif anal_type == SPMConstants.FMRI:
            if input_images is None:
                raise Exception("Error in batchrun_fmri_stats_factdes_2samplesttest: input_images cannot be None")
            glob_calc       = ""
            batch_folder    = "fmri"
            batch_prefix    = ""
            expl_mask       = None
            statsdir        = os.path.join(root_outdir, anal_name)

        # ---------------------------------------------------------------------------------------------------------------------------------
        # create template files
        if spm_template_name is None:
            if stat_type == SPMConstants.MULTREGR:
                spm_template_name = "group_model_spm_stats_1group_multiregr_estimate"
            elif stat_type == SPMConstants.OSTT:
                spm_template_name = "group_model_spm_stats_1sample_ttest_estimate"
            elif stat_type == SPMConstants.TSTT:
                spm_template_name = "group_model_spm_stats_2samples_ttest_estimate"
            elif stat_type == SPMConstants.OWA:
                spm_template_name = "group_model_spm_stats_1Wanova_estimate"
            elif stat_type == SPMConstants.TWA:
                spm_template_name = "group_model_spm_stats_2Wanova_estimate"
        out_batch_job, out_batch_start  = self.project.adapt_batch_files(spm_template_name, batch_folder, batch_prefix + anal_name)

        # -------------------------------------------------------------------------------------------------------------------------
        os.makedirs(statsdir, exist_ok=True)
        sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

        # compose images string
        if stat_type == SPMConstants.MULTREGR:
            SPMStatsUtils.compose_images_string_1GROUP_MULTREGR(groups_instances[0], out_batch_job, input_images, mustExist)
        elif stat_type == SPMConstants.OSTT:
            SPMStatsUtils.compose_images_string_1sTT(groups_instances[0], out_batch_job, input_images, mustExist)
        elif stat_type == SPMConstants.TSTT:
            SPMStatsUtils.compose_images_string_2sTT(groups_instances, out_batch_job, input_images, mustExist)
        elif stat_type == SPMConstants.OWA:
            SPMStatsUtils.compose_images_string_1W(groups_instances, out_batch_job, input_images, mustExist)
        elif stat_type == SPMConstants.TWA:
            SPMStatsUtils.compose_images_string_2W(groups_instances, out_batch_job, input_images, mustExist)

        # global calculation
        SPMStatsUtils.spm_replace_global_calculation(self.project, out_batch_job, glob_calc, groups_instances,
                                                     subj_data_dict)

        # check whether adding a covariate
        SPMCovariates.spm_replace_stats_add_covariates(self.project, out_batch_job, groups_instances, covs, 1,
                                                       cov_interactions, subj_data_dict, cov_centering)

        # explicit mask
        SPMStatsUtils.spm_replace_explicit_mask(self.globaldata, out_batch_job, expl_mask)

        # model estimate
        if anal_type == SPMConstants.CT or SPMConstants.GYR or SPMConstants.SDEP:
            sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=True))
        else:
            sed_inplace(out_batch_job, "<MODEL_ESTIMATE>", SPMStatsUtils.get_spm_model_estimate(isSurf=False))

        # ---------------------------------------------------------------------------
        print("running SPM batch template: " + statsdir)
        if runit:
            eng = call_matlab_spmbatch(out_batch_start, [self.globaldata.spm_functions_dir, self.globaldata.spm_dir], endengine=False)
        else:
            eng = None

        # -------------------------------------------------------------------------------------------------------------------------
        # check whether running a given contrasts batch or a standard multregr. script must only modify SPM.mat file
        if bool(post_model):
            if os.path.exists(post_model.template_name + ".m"):
                SPMPostModel.batchrun_spm_stats_predefined_postmodel(self.project, self.globaldata, statsdir, post_model.template_name, batch_folder, eng, runit)
            else:
                SPMPostModel.batchrun_spm_stats_postmodel(self.project, self.globaldata, statsdir, post_model, anal_name, batch_folder, eng, runit)

        # ---------------------------------------------------------------------------
        if bool(eng):
            eng.quit()
        return os.path.join(statsdir, "SPM.mat")



