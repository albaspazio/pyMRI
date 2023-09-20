import os
import traceback

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from group.SPMConstants import SPMConstants
from group.SPMModels import SPMModels
from group.spm_utilities import Nuisance, Covariate, CatConvResultsParams, ResultsParams, TContrast, FContrast
from group.SPMPostModel import PostModel

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
        data_file = "data.dat"

        project_dir = "/data/MRI/projects/nk"
        project = Project(project_dir, globaldata, data_file)  # automatically load PROJDIR/script/data.dat if present

        subjproject_dir = "/data/MRI/projects/3T"
        subjproject = Project(subjproject_dir, globaldata)

        SESS_ID = 1
        num_cpu = 1
        group_label = "all_nk"

        sign_imm_cells  = []
        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        subjects = subjproject.load_subjects(group_label, SESS_ID)

        analysis            = GroupAnalysis(project)
        spm_analysis        = SPMModels(project)


        # ==================================================================================================================
        # ANOVA (3 groups)
        # ==================================================================================================================
        groups_instances    = [ subjproject.get_subjects("td_nk"),
                                subjproject.get_subjects("sk_nk"),
                                subjproject.get_subjects("bd_nk")]

        covs                = [Nuisance("age"), Nuisance("gender")]
        anal_name           = "anova_td_vs_sk_vs_bd_x_age_gender"

        contrasts           = [FContrast("group", "[1 -1 0\n0 1 -1]"),
                               TContrast("TD > SK", "[1 -1 0]"), TContrast("SK > TD", "[-1 1 0]"),
                               TContrast("TD > BD", "[1 0 -1]"), TContrast("BD > TD", "[-1 0 1]"),
                               TContrast("SK > BD", "[0 1 -1]"), TContrast("BD > SK", "[0 -1 1]")]

        post_model          = PostModel(SPMConstants.OWA, covs, contrasts=contrasts, res_params=ResultsParams("none", 0.001, 0),
                                         res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
        spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.OWA, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)

        # ==================================================================================================================
        # TWO-SAMPLES T-TESTs
        # ==================================================================================================================
        # BD vs CTRL
        # groups_instances    = [ project.get_subjects("bd_imm_ct"),
        #                         ctrlproject.get_subjects("controls_4bd_imm")]
        # covs                = [Nuisance("age")]
        # anal_name           = "bd42_vs_ctrl26_imm_x_age"
        # constrasts          = [TContrast("BD > TD", "[1 -1]"), TContrast("TD > BD", "[-1 1]")]
        #
        # post_model          = PostModel(SPMConstants.TSTT, covs, contrasts=constrasts,
        #                                 res_params=ResultsParams("none", 0.001, 0),
        #                                 res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)

        # def batchrun_group_stats(self, root_outdir, stat_type, anal_type, anal_name, groups_instances, input_images=None,
        #                          covs=None, cov_interactions=None, cov_centering=False, data_file=None,
        #                          glob_calc=None, expl_mask="icv", spm_template_name=None,
        #                          post_model=None, runit=True):
        # spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.TSTT, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)


        # MAN vs DEP
        # groups_instances    = [ project.get_subjects("bd_imm_man"),
        #                         project.get_subjects("bd_imm_dep_ct")]
        # covs                = [Nuisance("age"), Nuisance("dis_dur")]
        # anal_name           = "bd_man21_vs_dep21_imm_x_age"
        # constrasts          = [TContrast("MAN > DEP", "[1 -1]"), TContrast("DEP > MAN", "[-1 1]")]
        # post_model          = PostModel(SPMConstants.TSTT, covs, contrasts=constrasts,
        #                                 res_params=ResultsParams("none", 0.001, 0),
        #                                 res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
        # spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.TSTT, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)


        # ==================================================================================================================
        # MULTIPLE REGRESSIONS
        # ==================================================================================================================
        # DIS DUR IN BD
        # groups_instances = [project.get_subjects("bd_imm_ct", SESS_ID)]
        # covs = [Nuisance("age"), Covariate("dis_dur")]
        # anal_name = "multregr_bd_dis_dur"
        #
        # post_model = PostModel(SPMConstants.MULTREGR, covs,
        #                        res_params=ResultsParams("none", 0.001, 0),
        #                        res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
        # spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.MULTREGR, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)





        # IMMUNO IN BD
        # groups_instances = [project.get_subjects("bd_imm_ct", SESS_ID)]
        # for var in sign_imm_cells:
        #     covs = [Nuisance("age"), Nuisance("dis_dur"), Covariate(var)]
        #     anal_name = "multregr_bd_" + var
        #
        #     post_model = PostModel(SPMConstants.MULTREGR, covs,
        #                            res_params=ResultsParams("none", 0.001, 0),
        #                            res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
        #     spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.MULTREGR, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)

        # IMMUNO IN DEP
        # groups_instances = [project.get_subjects("bd_imm_dep_ct", SESS_ID)]
        # for var in sign_imm_cells:
        #     covs = [Nuisance("age"), Nuisance("dis_dur"), Covariate(var)]
        #     anal_name = "multregr_bd_dep_" + var
        #
        #     post_model = PostModel(SPMConstants.MULTREGR, covs,
        #                            res_params=ResultsParams("none", 0.001, 0),
        #                            res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
            # spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.MULTREGR, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)

        # IMMUNO IN MAN
        # groups_instances = [project.get_subjects("bd_imm_man", SESS_ID)]
        # for var in sign_imm_cells:
        #     covs = [Nuisance("age"), Nuisance("dis_dur"), Covariate(var)]
        #     anal_name = "multregr_bd_man_" + var
        #
        #     post_model = PostModel(SPMConstants.MULTREGR, covs,
        #                            res_params=ResultsParams("none", 0.001, 0),
        #                            res_conv_params=CatConvResultsParams("none", 0.001, "none"), isSpm=False)
            # spm_analysis.batchrun_group_stats(project.ct_dir, SPMConstants.MULTREGR, SPMConstants.CAT, anal_name, groups_instances, covs=covs, post_model=post_model, runit=True)

    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


