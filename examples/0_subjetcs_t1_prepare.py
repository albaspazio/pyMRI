from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities
from pymri.Subject import Subject

if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir = "/data/MRI/scripts"
    proj_dir = "/data/MRI/projects/T15"
    fsl_code = "600"

    if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
        print("Error")
        exit()

    globaldata = Global(global_script_dir)
    # ======================================================================================================================

    project = Project(proj_dir, globaldata, hasT1=True)
    SESS_ID = 1

    subject = Subject("T15_N_001", 1, project)
    subject.create_file_system()

    subject.mpr2nifti("/data/MRI/projects/T15/subjects/T15_N_001/s1/mpr", 1)


    subject.reslice_image("sag->axial")
    subject.anatomical_processing(do_cleanup=False)
    subject.post_anatomical_processing()
    # subject.do_first("L_Amyg,R_Amyg", odn="first")
    subject.do_first()

    num_cpu = 1

