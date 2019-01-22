import os

import json
import traceback

from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities

from pymri.utility.fslfun import imtest, run_notexisting_img
from pymri.fsl.utils.run import rrun


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
        subjects_list_name = "subjects56_longitudinal"
        num_cpu = 1
        DO_REGISTER = True
        SESS_ID = 1
        template_file_name    = "subjects_2x56_melodic_ST"

        population_name         = "subjects_2x56"
        # template_suffix=ST_2x58;template_filename=ST_2x58

        PTHRESH = 0.95

        # declare -a arr_images_names=("R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6" "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat6" "R_ATN/2x56_T1NoGo_x_age_maskrsn/R_ATN_longitudinal2x56_T1NoGo_x_age_maskrsn_tfce_corrp_tstat5" "R_ATN/2x56_ProlecPromedio_x_age_slopes_compar_maskrsn/R_ATN_longitudinal2x56_ProlecPromedio_x_age_slopes_compar_maskrsn_tfce_corrp_tstat6")

        arr_images_names    = ["R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6",
                               "R_ATN/2x56_x_age_maskrsn/R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat3",
                               "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat6",
                               "L_ATN/2x56_maskrsn/L_ATN_longitudinal2x56_maskrsn_tfce_corrp_tstat3"]
        arr_rsn_id          = [10, 8]
        arr_rsn_labels      = ["R_ATN", "L_ATN"]

        # ======================================================================================================================
        # ======================================================================================================================
        project = Project(proj_dir, globaldata, hasT1=True)

        subjects = project.load_subjects(subjects_list_name)
        NUM_SUBJ = len(subjects)

        # load melodic template
        with open(template_file_name + ".json") as templfile:
            melodic_template = json.load(templfile)

        RSN_DIR         = os.path.join(project.melodic_templates_dir, template_file_name, "stats")
        DR_DIR          = os.path.join(project.melodic_dr_dir, "templ_" + template_file_name, population_name)
        RESULTS_OUT_DIR = os.path.join(DR_DIR, "results", "standard2results")

        # registering results to standard 2mm
        if DO_REGISTER is True:
            # calculate tranform from bgimage(4mm) to standard(2mm)

            bg_image_standard = os.path.join(RESULTS_OUT_DIR, "bg_image_standard.nii.gz")
            run_notexisting_img(bg_image_standard, "flirt -in " + melodic_template["TEMPLATE_BG_IMAGE"] + " -ref " + os.path.join(globaldata.fsl_data_standard, "MNI152_T1_2mm_brain") + " -out " + bg_image_standard + " -mat " + os.path.join(RESULTS_OUT_DIR, "bg2standard.mat"))

            # transform RSN image to standard(4mm) to standard(2mm)
            cnt = 0
            for rsn_id in arr_rsn_id:
                src_res_file    = os.path.join(RSN_DIR, "thresh_zstat" + str(rsn_id))
                dest_res_file   = os.path.join(RSN_DIR, arr_rsn_labels[cnt])

                if imtest(dest_res_file) is False:
                    rrun("flirt - in " + src_res_file + " -ref " + os.path.join(globaldata.fsl_data_standard, "MNI152_T1_2mm_brain") + " -applyxfm -init " + os.path.join(RESULTS_OUT_DIR, "bg2standard.mat") + " -out " + dest_res_file)
                    rrun("fslmaths " + dest_res_file + " -thr 2.7 " + dest_res_file)

                cnt = cnt+1

            # transform melodic results from 4mm to 2mm
            for foldimg in arr_images_names:
                img             = os.path.basename(foldimg)
                src_res_file    = os.path.join(DR_DIR, foldimg)
                dest_res_file   = os.path.join(RESULTS_OUT_DIR, img)

                rrun("flirt -in " + src_res_file + " -ref " + os.path.join(globaldata.fsl_data_standard, "MNI152_T1_2mm_brain") + " -applyxfm -init " + os.path.join(RESULTS_OUT_DIR, "bg2standard.mat") + " -out " + dest_res_file)
                # $FSLDIR/bin/fslmaths $dest_res_file -thr $PTHRESH $dest_res_file

        # extracting z-score
        # arr_roi = [os.path.join(project.group_analysis_dir, "roi", "anggyr_standard_4mm.nii.gz") + " " + os.path.join(project.group_analysis_dir, "roi", "postcing_standard_4mm.nii.gz")]
        arr_roi = [os.path.join(project.group_analysis_dir, "roi", "3roi_2.nii.gz")]

        # test 1 : from dr_stage2_ic0000.nii.gz
        ic_image = os.path.join(RSN_DIR, "dr_stage2_ic0000.nii.gz")

        for roi in arr_roi:
            filename = os.path.basename(roi + ".nii.gz")
            print(filename)
            rrun("fslmeants -i " + ic_image + " -o " + os.path.join(RESULTS_OUT_DIR, melodic_template["template_name"] + "_" + filename + ".txt") + " -m " + roi)

    except Exception as e:
        traceback.print_exc()
        print(e)