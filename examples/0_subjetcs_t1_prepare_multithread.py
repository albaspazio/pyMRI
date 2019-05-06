from threading import Thread
# from Queue import Queue

from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities
from pymri.Subject import Subject
from pymri.utility import fslfun


if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir   = "/data/MRI/scripts"
    proj_dir            = "/data/MRI/projects/T15"
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
    num_cpu     = 2

    # load whole list & create its file system
    subjects    = project.load_subjects("full", SESS_ID)
    # project.run_subjects_methods("create_file_system", [], project.get_subjects_labels(), nthread=num_cpu)

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    kwparams    = []

    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # for p in range(len(subjects)):
    #     kwparams.append({"extpath":"/data/MRI/projects/T15/subjects/" + subjects[p].label + "/s1/mpr", "cleanup":0})

    # kwparams    = []
    # subjects = ["T15_N_001", "T15_N_002", "T15_N_003", "T15_N_004", "T15_N_005", "T15_N_006", "T15_N_007"]
    # for p in range(len(subjects)):
    #     kwparams.append({"extpath":"/data/MRI/projects/T15/subjects/" + subjects[p] + "/s1/mpr", "cleanup":0})

    # project.run_subjects_methods("mpr2nifti", kwparams, subjects, nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRINT HEADER
    # ---------------------------------------------------------------------------------------------------------------------
    # for s in subjects:
    #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
    #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))

    # ---------------------------------------------------------------------------------------------------------------------
    # RESLICING
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects("test2", SESS_ID)
    # project.run_subjects_methods("reslice_image", [{"dir":"sag->axial"}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRE BET
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects("test2", SESS_ID)
    project.run_subjects_methods("anatomical_processing_prebet", [], project.get_subjects_labels(), nthread=num_cpu)


    # kwparams    = []
    # for p in range(len(subjects)):
    #     kwparams.append({"extpath":"/data/MRI/projects/T15/subjects/" + subjects[p].label + "/s1/mpr", "cleanup":0})