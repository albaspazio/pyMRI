import os
import json
import traceback

from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities

from pymri.utility.fslfun import imtest, run_notexisting_img
from pymri.fsl.utils.run import rrun

from pymri.utility import import_data_file
from pymri.utility import plot_data


if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir = "/media/alba/data/MRI/scripts"
    proj_dir = "/media/alba/dados/MRI/projects/temperamento_murcia"
    fsl_code = "509"

    try:
        if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
            print("Error")
            exit()

        globaldata = Global(global_script_dir)

        # ======================================================================================================================
        # init vars
        # ======================================================================================================================
        subjects_list_name  = "subjects56_longitudinal"
        num_cpu             = 1
        DO_REGISTER         = False
        SESS_ID             = 1
        template_file_name  = "subjects_2x56_melodic_ST"
        population_name     = "subjects_2x56"
        PTHRESH             = 0.95

        arr_images_names    = ["R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6",
                               "R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat3",
                               "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat6",
                               "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat3"]
        arr_rsn_id          = [10, 8]
        arr_rsn_labels      = ["R_ATN", "L_ATN"]
        input_rsn_image     = "dr_stage2_ic0000_diff.nii.gz"

        arr_roi_2_extract   = [{"roi":"R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6", "rsn":"R_ATN"},
                               {"roi":"L_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6", "rsn":"L_ATN"}]
        # ======================================================================================================================
        # ======================================================================================================================
        project = Project(proj_dir, globaldata, hasT1=True)

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

        subjects_data           = import_data_file.read_tabbed_file_with_header(os.path.join(project.dir, "data_2x56.txt"))

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
        # extracting z-score
        # -----------------------------------------------------
        for roi in arr_roi_2_extract:

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

    except Exception as e:
        traceback.print_exc()
        print(e)