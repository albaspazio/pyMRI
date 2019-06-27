import os
from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities


if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir = "/data/MRI/scripts"
    proj_dir = "/data/MRI/projects/T15"
    # proj_dir = "/data/MRI/projects/T3"
    fsl_code = "600"

    if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
        print("Error")
        exit()

    globaldata = Global(global_script_dir)
    # ======================================================================================================================

    project = Project(proj_dir, globaldata, hasT1=True)
    SESS_ID = 1

    # subject = Subject("test", 1, project)
    # subject.create_file_system()
    # subject.mpr2nifti(subject.t1_dir, 1)

    subjects    = project.load_subjects("controls_test", SESS_ID)

    subject     = subjects[0]
    # hdr = fslfun.read_header(subject.t1_data)
    # print(str(fslfun.get_image_dimension(subject.t1_data)))


    # subject.reslice_image("sag->axial")
    # subject.anatomical_processing_prebet()
    # subject.anatomical_processing_bet(betfparam=0.45, do_reg=False, do_overwrite=True)
    # subject.post_anatomical_processing()
    # subject.do_first("L_Amyg,R_Amyg", odn="first")
    # subject.do_first()

    subject.anatomical_processing_spm_segment()
