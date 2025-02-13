import os
import traceback

from Global import Global
from Project import Project
from models.ConnModels import ConnModels
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


        td_nk = project.get_subjects("td_nk")
        psi_nk = project.get_subjects("psi_nk")
        bd_nk = project.get_subjects("bd_nk")
        sk_nk = project.get_subjects("sk_nk")
        all_nk = project.get_subjects("all_nk")

        # ======================================================================================================================
        # PROCESSING 1: test create_regressors_file
        # ======================================================================================================================

        # ONE GROUP
        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk], ["td"], ofn="td_nk_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("dis_dur")]
        connmodels.create_regressors_file(outfolder, regressors, [psi_nk], ["psi"], ofn="td_nk_FS0_disdur")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("dis_dur")]
        connmodels.create_regressors_file(outfolder, regressors, [psi_nk], ["psi"], ofn="td_nk_FS0_disdur_x_age_gender")

        # TWO GROUPS
        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, psi_nk], ["td", "psi"],ofn="td_vs_psi_x_age_gender")
        #
        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, psi_nk], ["td", "psi"],ofn="td_vs_psi_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, psi_nk], ["td", "psi"],ofn="td_vs_psi_fs0_fs1_x_age_gender")

        # THREE GROUPS
        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"],ofn="td_sk_bd_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"],ofn="td_sk_bd_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"],ofn="td_sk_bd_fs0_fs1_x_age_gender")

        # ======================================================================================================================
        # PROCESSING 2: test create_regressors_file_ofsubset
        # ======================================================================================================================

        # ONE GROUP
        # regressors = [Nuisance("age"), Nuisance("gender")]
        # connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk], ["td"], "subset_td_nk_x_age_gender")
        #
        # regressors = [Covariate("FS0"), Covariate("dis_dur")]
        # connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [psi_nk], ["psi"], "subset_td_nk_FS0_disdur")
        #
        # regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("dis_dur")]
        # connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [psi_nk], ["psi"], "subset_td_nk_FS0_disdur_x_age_gender")

        # TWO GROUPS
        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk, psi_nk], ["td", "psi"], ofn="subset_td_vs_psi_x_age_gender")
        #
        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk, sk_nk], ["td", "sk"],ofn="subset_td_vs_sk_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk, bd_nk], ["td", "bd"],ofn="subset_td_vs_bd_fs0_fs1_x_age_gender")

        # THREE GROUPS
        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"],ofn="subset_td_sk_bd_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"],ofn="subset_td_sk_bd_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file_ofsubset(outfolder, regressors, all_nk, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"],ofn="subset_td_sk_bd_fs0_fs1_x_age_gender")

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================

        # ONE GROUP

        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk], ["td"],ofn="td_nk_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("dis_dur")]
        connmodels.create_regressors_file(outfolder, regressors, [psi_nk], ["psi"], ofn="td_nk_FS0_disdur")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("dis_dur")]
        connmodels.create_regressors_file(outfolder, regressors, [psi_nk], ["psi"], ofn="td_nk_FS0_disdur_x_age_gender")


        # TWO GROUPS

        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, psi_nk], ["td", "psi"], ofn="td_vs_psi_x_age_gender")
        #
        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, psi_nk], ["td", "psi"], ofn="td_vs_psi_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, psi_nk], ["td", "psi"], ofn="td_vs_psi_fs0_fs1_x_age_gender")

        # THREE GROUPS

        regressors = [Nuisance("age"), Nuisance("gender")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"], ofn="td_sk_bd_x_age_gender")

        regressors = [Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"], ofn="td_sk_bd_fs0_fs1")

        regressors = [Nuisance("age"), Nuisance("gender"), Covariate("FS0"), Covariate("FS1")]
        connmodels.create_regressors_file(outfolder, regressors, [td_nk, sk_nk, bd_nk], ["td", "sk", "bd"], "td_sk_bd_fs0_fs1_x_age_gender")

    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


