import json
import os
import traceback

from Global import Global
from Project import Project
from data import plot_data
from data.SubjectsData import SubjectsData
from data.utilities import process_results
from myutility.images.Image import Image
from myutility.myfsl.fslfun import run_notexisting_img
from myutility.myfsl.utils.run import rrun

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "601"
    try:
        globaldata = Global(fsl_code)

    except Exception as e:
        print(e)
        exit()

    # ======================================================================================================================
    # HEADER
    # ======================================================================================================================
    proj_dir = "/media/alba/dados/MRI/projects/temperamento_murcia"
    project = Project(proj_dir, globaldata)
    SESS_ID = 1
    num_cpu = 4
    group_label = "single"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    try:
        # ======================================================================================================================
        # init vars
        # ======================================================================================================================
        subjects_list_name = "subjects_2x56"
        num_cpu = 1

        DO_REGISTER = False
        DO_MELODIC_RES = False
        DO_SBFC_RES = True

        SESS_ID = 1
        template_file_name = "subjects_2x56_melodic_ST"
        population_name = "subjects_2x56"
        PTHRESH = 0.95

        arr_images_names = ["R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6",
                            "R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat3",
                            "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat6",
                            "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat3"]
        arr_rsn_id = [10, 8]
        arr_rsn_labels = ["R_ATN", "L_ATN"]
        input_rsn_image = "dr_stage2_ic0000_diff.nii.gz"

        arr_roi_2_extract_melodic = [{"roi": "R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6", "rsn": "R_ATN"},
                                     {"roi": "L_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6", "rsn": "L_ATN"}]

        # ======================================================================================================================
        # ======================================================================================================================
        project = Project(proj_dir, globaldata)

        project.load_subjects(subjects_list_name)
        subjects = project.subjects
        NUM_SUBJ = len(subjects)

        # load rs template
        with open(template_file_name + ".json") as templfile:
            melodic_template = json.load(templfile)

        TEMPL_STATS_DIR = os.path.join(project.melodic_templates_dir, template_file_name, "stats")
        DR_DIR = os.path.join(project.melodic_dr_dir, "templ_" + template_file_name, population_name)
        RESULTS2_OUT_DIR = os.path.join(DR_DIR, "results", "std2")
        RESULTS4_OUT_DIR = os.path.join(DR_DIR, "results", "std4")
        std_MNI_2mm_brain = os.path.join(globaldata.fsl_data_std_dir, "MNI152_T1_2mm_brain")

        subjects_data = SubjectsData(os.path.join(project.dir, "data_2x56.txt"))

        # -----------------------------------------------------
        # SBFC
        # -----------------------------------------------------
        RESULTS_SBFC_OUT_DIR = os.path.join(project.sbfc_dir, population_name)

        # PE's 2nd level dir
        sbfc_2nd_level_PE_dir = os.path.join(project.group_analysis_dir,
                                             "sbfc/subjects_2x56/2nd_level/feat_2nd_R_ATN_longitudinal2x56_T1NoGo_x_age_SES5_template_group_feat_s56.gfeat/cope1.feat/stats")

        # 3rd level results mask
        sbfc_3rd_level_RES_img = os.path.join(project.group_analysis_dir,
                                              "sbfc/subjects_2x56/3rd_level/thresh_2.3/stats_R_ATN_longitudinal2x56_T1NoGo_x_age_SES51_mult_cov_x_age_SES.gfeat/cope1.feat/rendered_thresh_zstat5")
        # -----------------------------------------------------
        # registering results to standard 2mm
        # -----------------------------------------------------
        if DO_REGISTER:

            # calculate tranform from bgimage(4mm) to standard(2mm)
            # => /dr/templ_subjects_2x56_melodic_ST/subjects_2x56/results/std2/bg_image_std.nii.gz
            templ2std_mat = os.path.join(TEMPL_STATS_DIR, "bg2std.mat")
            bg_image_std = os.path.join(RESULTS2_OUT_DIR, "bg_image_std.nii.gz")
            run_notexisting_img(bg_image_std,
                                "flirt -in " + melodic_template["TEMPLATE_BG_IMAGE"] + " -ref " + os.path.join(
                                    globaldata.fsl_data_std_dir,
                                    "MNI152_T1_2mm_brain") + " -out " + bg_image_std + " -omat " + templ2std_mat)

            # -----------------------------------------------------
            # transform RSN image to standard(4mm) to standard(2mm)
            # => group_templates/subjects_2x56_melodic_ST/stats'
            # -----------------------------------------------------
            cnt = 0
            for rsn_id in arr_rsn_id:
                src_res_file = os.path.join(TEMPL_STATS_DIR, "thresh_zstat" + str(rsn_id))
                dest_res_file = Image(os.path.join(TEMPL_STATS_DIR, arr_rsn_labels[cnt]))

                if not dest_res_file.exist:
                    rrun(f"flirt - in {src_res_file} -ref {std_MNI_2mm_brain} -applyxfm -init {templ2std_mat} -out {dest_res_file}")
                    rrun(f"fslmaths {dest_res_file} -thr 2.7 {dest_res_file}")

                cnt = cnt + 1

            # -----------------------------------------------------
            # transform rs results from 4mm to 2mm
            # -----------------------------------------------------
            for foldimg in arr_images_names:
                img             = os.path.basename(foldimg)
                src_res_file    = Image(os.path.join(DR_DIR, foldimg))
                dest_res_file   = os.path.join(RESULTS2_OUT_DIR, img)
                inputmat        = os.path.join(RESULTS2_OUT_DIR, "bg2std.mat")

                if not src_res_file.exist:
                    print(src_res_file + " is missing !!")
                    exit(1)

                if not os.path.exists(templ2std_mat):
                    print(inputmat + " is missing !!")
                    exit(1)

                rrun(f"flirt -in {src_res_file} -ref {std_MNI_2mm_brain} -applyxfm -init {templ2std_mat} -out {dest_res_file}")
                # $FSLDIR/bin/fslmaths $dest_res_file -thr $PTHRESH $dest_res_file

        # -----------------------------------------------------
        # extracting PE from rs analysis (dr_stage2_000X_diff)
        # -----------------------------------------------------
        if DO_MELODIC_RES:
            for roi in arr_roi_2_extract_melodic:

                ic_image = Image(os.path.join(DR_DIR, roi["rsn"], input_rsn_image), must_exist=True, msg="IC image is missing")
                maskpath = Image(os.path.join(RESULTS4_OUT_DIR, roi["roi"]), must_exist=True, msg="ROI mask is missing")

                maskname = os.path.basename(roi["roi"])
                raw_res_file_name = os.path.join(RESULTS4_OUT_DIR, melodic_template["template_name"] + "_" + maskname + "_raw.txt")
                res_file_name = os.path.join(RESULTS4_OUT_DIR, melodic_template["template_name"] + "_" + maskname + ".txt")
                print(maskname)
                rrun(f"fslmeants -i {ic_image} -o {raw_res_file_name} -m {maskpath}")
                # str_lists = process_results2tp(raw_res_file_name, subjects, res_file_name)
                str_lists = process_results(raw_res_file_name, subjects, res_file_name)

                # plot_data.histogram_plot_2groups(str_lists, os.path.join(RESULTS4_OUT_DIR, "fig_" + roi["roi"] + "_" + roi["rsn"] + ".png"), "4", 1)

                data = [float(d) * (-1) for d in subjects_data.get_subjects_column(colname="T2NoGo")]  # NoGo are errors: I want hits..since data are demeaned I can just invert the sign
                plot_data.scatter_plot_2groups(str_lists, data, os.path.join(RESULTS4_OUT_DIR, "fig_" + roi["roi"] + "_" + roi["rsn"] + ".png"), "4", 1, colors=("white", "green"))
                plot_data.scatter_plot_2groups(str_lists, data, os.path.join(RESULTS4_OUT_DIR, "fig_" + roi["roi"] + "_" + roi["rsn"] + ".png"), "4", 1, colors=("red", "white"))

        # -----------------------------------------------------
        # extracting PE from 2nd level SBFC analysis
        # -----------------------------------------------------
        if DO_SBFC_RES:

            res_mask = sbfc_3rd_level_RES_img + "_mask"
            rrun(f"fslmaths {sbfc_3rd_level_RES_img} -thr 2.3 -bin {res_mask}")
            sbfc_pe_ctrl = []
            sbfc_pe_train = []
            for s in range(24):
                img = os.path.join(sbfc_2nd_level_PE_dir, "pe" + str(s + 1) + ".nii.gz")
                pe = rrun(f"fslstats {img} -m -k {res_mask}")
                sbfc_pe_ctrl.append(float(pe))

            for s in range(24, NUM_SUBJ):
                img = os.path.join(sbfc_2nd_level_PE_dir, "pe" + str(s + 1) + ".nii.gz")
                pe = rrun(f"fslstats {img} -m -k {res_mask}")
                sbfc_pe_train.append(float(pe))

            data = [float(d) * (-1) for d in subjects_data.get_subjects_column(colname="T1NoGo")]  # NoGo are errors: I want hits..since data are demeaned I can just invert the sign
            plot_data.scatter_plot_dataserie(sbfc_pe_train, data[24:], os.path.join(RESULTS_SBFC_OUT_DIR, "fig_T1NoGo" + ".png"), "green","training")
            plot_data.scatter_plot_dataserie(sbfc_pe_ctrl, data[0:24], os.path.join(RESULTS_SBFC_OUT_DIR, "fig_T1NoGo" + ".png"), "red", "controls")

    except Exception as e:
        traceback.print_exc()
        print(e)
