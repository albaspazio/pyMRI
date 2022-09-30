from Global import Global
from Project import Project
from utility.myfsl.utils.run import rrun

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
    proj_dir = "/data/MRI/projects/T15"
    project = Project(proj_dir, globaldata)
    SESS_ID = 1
    group_label = "all"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    subjects = project.load_subjects("full", SESS_ID)
    for subject in subjects:
        # subject.mpr2nifti(subject.t1_dir, 1)
        hdr = subject.t1_data.read_header()
        print(str(subject.t1_data.get_image_dimension()))
        rrun("fsleyes " + subject.t1_data + " " + subject.t1_brain_data)
