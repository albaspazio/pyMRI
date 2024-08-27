import os
import traceback

from Global import Global
from Project import Project
from models.FSLModels import FSLModels
from group.spm_utilities import Covariate, Nuisance

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
        proj_dir        = "/data/MRI/projects/test"
        project         = Project(proj_dir, globaldata)     # automatically load PROJDIR/script/data.dat if present
        SESS_ID         = 1

        fslmodels       = FSLModels(project)
        input_template  = os.path.join(project.glm_template_dir, "template_1group_1cov_1var.fsf")
        outfolder       = os.path.join(project.group_analysis_dir, "glm_models")
        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        all_grp = project.load_subjects("all", SESS_ID, must_exist=False)
        group1  = project.load_subjects("g1", SESS_ID, must_exist=False)
        group2  = project.load_subjects("g2", SESS_ID, must_exist=False)
        group3  = project.load_subjects("g3", SESS_ID, must_exist=False)

        # ONE GROUP

        # regressors = [Nuisance("age"), Nuisance("gender")]
        # fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [all_grp], ofn="grp1", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)
        #
        # regressors = [Covariate("age"), Covariate("gender")]
        # fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [all_grp], ofn="grp1", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)
        #
        # regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        # fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [all_grp], ofn="grp1", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)
        #
        # regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        # fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [all_grp], ofn="grp1_simple", create_model=False, group_mean_contrasts=0)
        #
        # regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        # fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [all_grp], ofn="grp1_simple_compcovs", create_model=False, group_mean_contrasts=0, compare_covs=True)


        # TWO GROUPS

        regressors = [Nuisance("age"), Nuisance("gender")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2], ofn="grp1_vs_grp2", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)
        #
        regressors = [Covariate("FS0"), Covariate("FS1")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2], ofn="grp1_vs_grp2", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2], ofn="grp1_vs_grp2", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2], ofn="grp1_vs_grp2_simple", create_model=False, group_mean_contrasts=0, cov_mean_contrasts=0)

        # THREE GROUPS

        regressors = [Nuisance("age"), Nuisance("gender")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2, group3], ofn="grp1_vs_grp2_vs_grp3", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)

        regressors = [Covariate("FS0"), Covariate("FS1")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2, group3], ofn="grp1_vs_grp2_vs_grp3", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2, group3], ofn="grp1_vs_grp2_vs_grp3", create_model=False, group_mean_contrasts=2, cov_mean_contrasts=2)

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        fslmodels.create_Mgroups_Ncov_Xnuisance_glm_file(input_template, outfolder, regressors, [group1, group2, group3], ofn="grp1_vs_grp2_vs_grp3_simple", create_model=False, group_mean_contrasts=0, cov_mean_contrasts=0)


    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


