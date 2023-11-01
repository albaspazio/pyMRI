import os
import traceback

from Global import Global
from Project import Project
from group.ConnModels import ConnModels
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
        proj_dir        = "/data/MRI/projects/nk"
        project         = Project(proj_dir, globaldata)     # automatically load PROJDIR/script/data.dat if present
        SESS_ID         = 1

        connmodels      = ConnModels(project)
        outfolder       = os.path.join(project.group_analysis_dir, "glm_models")
        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================

        # ONE GROUP

        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk"], "td_nk_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("dis_dur")]
        connmodels.create_regressors_file(outfolder, regressors, ["psi_nk"], "td_nk_FS0_disdur")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("dis_dur")]
        connmodels.create_regressors_file(outfolder, regressors, ["psi_nk"], "td_nk_FS0_disdur_x_age_gender")


        # TWO GROUPS

        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk", "psi_nk"], "td_vs_psi_x_age_gender")
        #
        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk", "psi_nk"], "td_vs_psi_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk", "psi_nk"], "td_vs_psi_fs0_fs1_x_age_gender")

        # THREE GROUPS

        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk", "sk_nk", "bd_nk"], "td_sk_bd_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk", "sk_nk", "bd_nk"], "td_sk_bd_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, ["td_nk", "sk_nk", "bd_nk"], "td_sk_bd_fs0_fs1_x_age_gender")

    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


