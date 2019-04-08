import os

from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities
from pymri.Subject import Subject
from pymri.utility import fslfun
from pymri.fsl.utils.run import rrun

if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir   = "/data/MRI/scripts"
    proj_dir            = "/data/MRI/projects/T3"
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

    subjects    = project.load_subjects("full", SESS_ID)


    for subject in subjects:

        # subject.mpr2nifti(subject.t1_dir, 1)
        hdr = fslfun.read_header(subject.t1_data)
        print(str(fslfun.get_image_dimension(subject.t1_data)))
        # rrun("fsleyes " + subject.t1_data)


