import os
import json
import traceback
from shutil import copyfile

from Global import Global
from Project import Project
from utility import startup_utilities

from myfsl.utils.run import rrun

from utility import import_data_file

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
        DO_MELODIC_RES      = False
        DO_SBFC_RES         = True

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
        input_rsn_image     = "dr_stage2_ic0000.nii.gz"

        arr_roi_2_extract_melodic   = [{"roi": "R_ATN_longitudinal2x56_x_age_maskrsn_tfce_corrp_tstat6", "rsn": "R_ATN"},
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


        # create baseline images
        curdir = os.getcwd()
        for rsn in arr_rsn_labels:
            rsndir      = os.path.join(DR_DIR, rsn)
            rsn_tempdir = os.path.join(rsndir, "tempXXXX")
            os.makedirs(rsn_tempdir, exist_ok=True)
            copyfile(os.path.join(rsndir, input_rsn_image), os.path.join(rsn_tempdir, input_rsn_image))
            os.chdir(rsn_tempdir)
            rrun("fslsplit " + input_rsn_image)

            rsn_tempdirpre = os.path.join(rsn_tempdir, "pre")
            rsn_tempdirpost = os.path.join(rsn_tempdir, "post")



    except Exception as e:
        traceback.print_exc()
        print(e)