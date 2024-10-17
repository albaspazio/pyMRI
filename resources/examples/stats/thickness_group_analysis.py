import os
import traceback

from Global import Global
from Project import Project
from data.utilities import FilterValues
from group.GroupAnalysis import GroupAnalysis
from group.SPMConstants import SPMConstants
from group.SPMModels import SPMModels
from group.spm_utilities import Nuisance, Covariate, CatConvResultsParams, ResultsParams, TContrast, FContrast
from group.PostModel import PostModel

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = Global(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        data_file = "data.xlsx"

        project_dir = "/data/MRI/projects/test"
        project = Project(project_dir, globaldata, data_file)  # automatically load PROJDIR/script/data.dat if present

        subjproject_dir = "/data/MRI/projects/test"
        subjproject = Project(subjproject_dir, globaldata)

        SESS_ID = 1
        num_cpu = 1
        group_label = "all"

        sign_imm_cells  = []
        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        subjects = subjproject.load_subjects(group_label, [SESS_ID], must_exist=False)

        analysis            = GroupAnalysis(project)
        spm_analysis        = SPMModels(project)


        # ==================================================================================================================
        # region ANOVA (3 groups)
        # ==================================================================================================================
        groups_instances    = [subjproject.get_subjects("g1", must_exist=False),
                               subjproject.get_subjects("g2", must_exist=False),
                               subjproject.get_subjects("g3", must_exist=False)]

        covs                = [Nuisance("age"), Nuisance("gender")]
        anal_name           = "anova_td_vs_sk_vs_bd_x_age_gender"

        contrasts           = [FContrast("group", "[1 -1 0\n0 1 -1]"),
                               TContrast("g1 > g2", "[1 -1 0]"), TContrast("g2 > g1", "[-1 1 0]"),
                               TContrast("g1 > g3", "[1 0 -1]"), TContrast("g3 > g1", "[-1 0 1]"),
                               TContrast("g2 > g3", "[0 1 -1]"), TContrast("g3 > g2", "[0 -1 1]")]

        post_model          = PostModel(SPMConstants.OWA, covs, contrasts=contrasts, res_params=ResultsParams("none", 0.001, 0),
                                         res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
        spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.OWA, SPMConstants.CT, anal_name,
                                          groups_instances, covs=covs, post_model=post_model, runit=False,
                                          mustExist=False)
        #endregion

        # ==================================================================================================================
        # region TWO-SAMPLES T-TESTs
        # ==================================================================================================================
        # BD vs CTRL
        groups_instances    = [project.get_subjects("g1", must_exist=False),
                               subjproject.get_subjects("g2", must_exist=False)]
        covs                = [Nuisance("age")]
        anal_name           = "g1_vs_g2_imm_x_age"
        constrasts          = [TContrast("g1 > g2", "[1 -1]"), TContrast("g2 > g1", "[-1 1]")]

        post_model          = PostModel(SPMConstants.TSTT, covs, contrasts=constrasts,
                                        res_params=ResultsParams("none", 0.001, 0),
                                        res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)

        # def batchrun_group_stats(self, root_outdir, stat_type, anal_type, anal_name, groups_instances, input_images=None,
        #                          covs=None, cov_interactions=None, cov_centering=False, data_file=None,
        #                          glob_calc=None, expl_mask="icv", spm_template_name=None,
        #                          post_model=None, runit=True):
        spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.TSTT, SPMConstants.CT, anal_name,
                                          groups_instances, covs=covs, post_model=post_model, runit=False,
                                          mustExist=False)

        #endregion

        # ==================================================================================================================
        # region TWO-WAY ANOVA
        # ==================================================================================================================
        # BD vs CTRL

        sel_male = FilterValues("gender", "=", 1)
        group1_male = project.get_subjects("g1", must_exist=False, select_conds=[sel_male])

        groups_instances    = [project.get_subjects("g1", must_exist=False),
                               subjproject.get_subjects("g2", must_exist=False)]
        covs                = [Nuisance("age")]
        anal_name           = "g1_vs_g2_imm_x_age"
        constrasts          = [TContrast("g1 > g2", "[1 -1]"), TContrast("g2 > g1", "[-1 1]")]

        post_model          = PostModel(SPMConstants.TWA, covs, contrasts=constrasts,
                                        res_params=ResultsParams("none", 0.001, 0),
                                        res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)

        # def batchrun_group_stats(self, root_outdir, stat_type, anal_type, anal_name, groups_instances, input_images=None,
        #                          covs=None, cov_interactions=None, cov_centering=False, data_file=None,
        #                          glob_calc=None, expl_mask="icv", spm_template_name=None,
        #                          post_model=None, runit=True):
        spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.TWA, SPMConstants.CT, anal_name,
                                          groups_instances, covs=covs, post_model=post_model, runit=False,
                                          mustExist=False)

        #endregion

        # ==================================================================================================================
        # region MULTIPLE REGRESSIONS
        # ==================================================================================================================
        # DIS DUR IN BD
        groups_instances = [project.get_subjects("g3", [SESS_ID], must_exist=False)]
        covs = [Nuisance("age"), Covariate("dis_dur")]
        anal_name = "multregr_bd_dis_dur"

        post_model = PostModel(SPMConstants.MULTREGR, covs,
                               res_params=ResultsParams("none", 0.001, 0),
                               res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
        spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.MULTREGR, SPMConstants.CT, anal_name,
                                          groups_instances, covs=covs, post_model=post_model, runit=False,
                                          mustExist=False)
        #endregion

        # ==================================================================================================================
    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


