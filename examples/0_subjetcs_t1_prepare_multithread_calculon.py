# from Queue import Queue

from pymri.Global import Global
from pymri.Project import Project
from utility import startup_utilities

if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir   = "/media/alba/data/MRI/scripts"
    proj_dir            = "/media/alba/dados/MRI/projects/T15"
    fsl_code            = "600"

    if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
        print("Error")
        exit()

    globaldata = Global(global_script_dir)

    # ======================================================================================================================
    # SUBJECTS
    # ======================================================================================================================

    project     = Project(proj_dir, globaldata, hasT1=True)
    SESS_ID     = 1
    num_cpu     = 7

    subjects    = project.load_subjects("test", SESS_ID)

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================


    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # kwparams    = []
    # for p in range(len(subjects)):
    #     kwparams.append({"extpath":"/data/MRI/projects/T15/subjects/" + subjects[p].label + "/s1/mpr", "cleanup":0})
    #
    # kwparams    = []
    # subjects = ["T15_N_001", "T15_N_002", "T15_N_003", "T15_N_004", "T15_N_005", "T15_N_006", "T15_N_007"]
    # for p in range(len(subjects)):
    #     kwparams.append({"extpath":"/data/MRI/projects/T15/subjects/" + subjects[p] + "/s1/mpr", "cleanup":0})
    #
    # project.run_subjects_methods("mpr2nifti", kwparams, subjects, nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRINT HEADER
    # ---------------------------------------------------------------------------------------------------------------------
    # for s in subjects:
    #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
    #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))

    # ---------------------------------------------------------------------------------------------------------------------
    # ANATOMICAL PROCESSING
    # ---------------------------------------------------------------------------------------------------------------------

    project.run_subjects_methods("anatomical_processing_prebet", [], project.get_subjects_labels(), nthread=num_cpu)
