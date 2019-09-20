import os
import json
import traceback

from Global import Global
from Project import Project

from utility.fslfun import imtest, run_notexisting_img
from myfsl.utils.run import rrun

from utility import import_data_file
from utility import plot_data


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
    project     = Project(proj_dir, globaldata)
    SESS_ID     = 1
    num_cpu     = 4
    group_label = "single"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    
    try:
        # ======================================================================================================================
        # init vars
        # ======================================================================================================================
        subjects_list_name  = "are_2groups_71"                      # label of the subjects list within the json file
        subjects_data_file  = "data_temperamento71_ARE2groups.txt"  # contains subjects data
        num_cpu             = 1

        DO_REGISTER         = True
        DO_MELODIC_RES      = False
        DO_SBFC_RES         = False

        SESS_ID             = 1
        template_file_name  = "subjects71_melodic_T71"
        population_name     = "subjects_temperamento71"
        PTHRESH             = 0.95

        arr_images_names    = ["aDMN/ARE_2groups_x_age_maskrsn/aDMN_ARE_2groups_x_age_maskrsn_tfce_corrp_tstat6",
                               "OFC/ARE_2groups_x_age_maskrsn/OFC_ARE_2groups_x_age_maskrsn_tfce_corrp_tstat6"]
        arr_rsn_id          = [2, 6]
        arr_rsn_labels      = ["OFC", "aDMN"]
        input_rsn_image     = "dr_stage2_ic0000.nii.gz"

        arr_roi_2_extract_melodic   = [{"roi": "aDMN_ARE_2groups_x_age_maskrsn_tfce_corrp_tstat6", "rsn": "R_ATN"},
                                       {"roi":"OFC_ARE_2groups_x_age_maskrsn_tfce_corrp_tstat6", "rsn":"L_ATN"}]

        # ======================================================================================================================
        # ======================================================================================================================
        project = Project(proj_dir, globaldata)

        project.load_subjects(subjects_list_name)
        subjects            = project.get_subjects_labels()
        NUM_SUBJ            = len(subjects)

        # load melodic template
        with open(template_file_name + ".json") as templfile:
            melodic_template = json.load(templfile)

        TEMPL_STATS_DIR         = os.path.join(project.melodic_templates_dir, template_file_name, "stats")
        DR_DIR                  = os.path.join(project.melodic_dr_dir, "templ_" + template_file_name, population_name)
        RESULTS2_OUT_DIR        = os.path.join(DR_DIR, "results", "standard2")
        RESULTS4_OUT_DIR        = os.path.join(DR_DIR, "results", "standard4")
        standard_MNI_2mm_brain  = os.path.join(globaldata.fsl_data_standard_dir, "MNI152_T1_2mm_brain")

        subjects_data           = import_data_file.tabbed_file_with_header2dict_list(os.path.join(project.dir, subjects_data_file))

        # -----------------------------------------------------
        # SBFC
        # -----------------------------------------------------
        RESULTS_SBFC_OUT_DIR    = os.path.join(project.sbfc_dir, population_name)

        # PE's 2nd level dir
        sbfc_2nd_level_PE_dir   = os.path.join(project.group_analysis_dir, "sbfc/subjects_2x56/2nd_level/feat_2nd_R_ATN_longitudinal2x56_T1NoGo_x_age_SES5_template_group_feat_s56.gfeat/cope1.feat/stats")

        # 3rd level results mask
        sbfc_3rd_level_RES_img  = os.path.join(project.group_analysis_dir, "sbfc/subjects_2x56/3rd_level/thresh_2.3/stats_R_ATN_longitudinal2x56_T1NoGo_x_age_SES51_mult_cov_x_age_SES.gfeat/cope1.feat/rendered_thresh_zstat5")
        # -----------------------------------------------------
        # registering results to standard 2mm
        # -----------------------------------------------------
        if DO_REGISTER is True:

            # calculate tranform from bgimage(4mm) to standard(2mm)
            # => /dr/templ_subjects_2x56_melodic_ST/subjects_2x56/results/standard2/bg_image_standard.nii.gz
            templ2standard_mat = os.path.join(TEMPL_STATS_DIR, "bg2standard.mat")
            bg_image_standard = os.path.join(RESULTS2_OUT_DIR, "bg_image_standard.nii.gz")
            run_notexisting_img(bg_image_standard, "flirt -in " + melodic_template["TEMPLATE_BG_IMAGE"] + " -ref " + os.path.join(globaldata.fsl_data_standard_dir, "MNI152_T1_2mm_brain") + " -out " + bg_image_standard + " -omat " + templ2standard_mat)

            # -----------------------------------------------------
            # transform RSN image to standard(4mm) to standard(2mm)
            # => group_templates/subjects_2x56_melodic_ST/stats'
            # -----------------------------------------------------
            cnt = 0
            for rsn_id in arr_rsn_id:
                src_res_file    = os.path.join(TEMPL_STATS_DIR, "thresh_zstat" + str(rsn_id))
                dest_res_file   = os.path.join(TEMPL_STATS_DIR, arr_rsn_labels[cnt])

                if imtest(dest_res_file) is False:
                    rrun("flirt - in " + src_res_file + " -ref " + standard_MNI_2mm_brain + " -applyxfm -init " + templ2standard_mat + " -out " + dest_res_file)
                    rrun("fslmaths " + dest_res_file + " -thr 2.7 " + dest_res_file)

                cnt = cnt+1

            # -----------------------------------------------------
            # transform melodic results from 4mm to 2mm
            # -----------------------------------------------------
            for foldimg in arr_images_names:
                img             = os.path.basename(foldimg)
                src_res_file    = os.path.join(DR_DIR, foldimg)
                dest_res_file   = os.path.join(RESULTS2_OUT_DIR, img)
                inputmat        = os.path.join(RESULTS2_OUT_DIR, "bg2standard.mat")

                if imtest(src_res_file) is False:
                    print(src_res_file + " is missing !!")
                    exit(1)

                if os.path.exists(templ2standard_mat) is False:
                    print(inputmat + " is missing !!")
                    exit(1)


                rrun("flirt -in " + src_res_file + " -ref " + standard_MNI_2mm_brain + " -applyxfm -init " + templ2standard_mat + " -out " + dest_res_file)
                # $FSLDIR/bin/fslmaths $dest_res_file -thr $PTHRESH $dest_res_file

        # -----------------------------------------------------
        # extracting PE from melodic analysis (dr_stage2_000X_diff)
        # -----------------------------------------------------
        if DO_MELODIC_RES is True:
            for roi in arr_roi_2_extract_melodic:

                ic_image = os.path.join(DR_DIR, roi["rsn"], input_rsn_image)
                if imtest(ic_image) is False:
                    raise Exception("IC image(" + ic_image + ") is missing")

                maskpath = os.path.join(RESULTS4_OUT_DIR, roi["roi"])

                if imtest(maskpath) is False:
                    raise Exception("ROI mask (" + maskpath  + ") image is missing")

                maskname            = os.path.basename(roi["roi"])
                raw_res_file_name   = os.path.join(RESULTS4_OUT_DIR, melodic_template["template_name"] + "_" + maskname + "_raw.txt")
                res_file_name       = os.path.join(RESULTS4_OUT_DIR, melodic_template["template_name"] + "_" + maskname + ".txt")
                print(maskname)
                rrun("fslmeants -i " + ic_image + " -o " + raw_res_file_name + " -m " + maskpath)
                # str_lists = process_results2tp(raw_res_file_name, subjects, res_file_name)
                str_lists           = import_data_file.process_results(raw_res_file_name, subjects, res_file_name)

                # plot_data.histogram_plot_2groups(str_lists, os.path.join(RESULTS4_OUT_DIR, "fig_" + roi["roi"] + "_" + roi["rsn"] + ".png"), "4", 1)

                data = [float(d) * (-1) for d in import_data_file.get_dict_column(subjects_data, "T2NoGo")]  # NoGo are errors: I want hits..since data are demeaned I can just invert the sign
                plot_data.scatter_plot_2groups(str_lists, data, os.path.join(RESULTS4_OUT_DIR, "fig_" + roi["roi"] + "_" + roi["rsn"] + ".png"), "4", 1, colors=("white", "green"))
                plot_data.scatter_plot_2groups(str_lists, data, os.path.join(RESULTS4_OUT_DIR, "fig_" + roi["roi"] + "_" + roi["rsn"] + ".png"), "4", 1, colors=("red", "white"))

        # -----------------------------------------------------
        # extracting PE from 2nd level SBFC analysis
        # -----------------------------------------------------
        if DO_SBFC_RES is True:

            res_mask = sbfc_3rd_level_RES_img + "_mask"
            rrun("fslmaths " + sbfc_3rd_level_RES_img + " -thr 2.3 -bin " + res_mask)
            sbfc_pe_ctrl = []
            sbfc_pe_train = []
            for s in range(24):
                img = os.path.join(sbfc_2nd_level_PE_dir, "pe" + str(s + 1) + ".nii.gz")
                pe = rrun("fslstats " + img + " -m -k " + res_mask)
                sbfc_pe_ctrl.append(float(pe))

            for s in range(24, NUM_SUBJ):
                img = os.path.join(sbfc_2nd_level_PE_dir, "pe" + str(s + 1) + ".nii.gz")
                pe = rrun("fslstats " + img + " -m -k " + res_mask)
                sbfc_pe_train.append(float(pe))

            data = [float(d) * (-1) for d in import_data_file.get_dict_column(subjects_data, "T1NoGo")]  # NoGo are errors: I want hits..since data are demeaned I can just invert the sign
            plot_data.scatter_plot_dataserie(sbfc_pe_train, data[24:], os.path.join(RESULTS_SBFC_OUT_DIR,"fig_T1NoGo" + ".png"), "green", "training")
            plot_data.scatter_plot_dataserie(sbfc_pe_ctrl, data[0:24], os.path.join(RESULTS_SBFC_OUT_DIR,"fig_T1NoGo" + ".png"), "red", "controls")



    except Exception as e:
        traceback.print_exc()
        print(e)