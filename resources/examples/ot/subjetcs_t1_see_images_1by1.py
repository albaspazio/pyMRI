import os

from project.MRIGlobal import MRIGlobal
from project.MRIProject import MRIProject
from myutility.myfsl.utils.run import rrun

# NOTE: Using relative paths with os.path.dirname(__file__) for project discovery

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "601"
    try:
        globaldata = MRIGlobal(fsl_code)

    except Exception as e:
        print(e)
        exit()

    # ======================================================================================================================
    # HEADER
    # ======================================================================================================================
    proj_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "T15")  # NOTE: relative path to project directory
    project = MRIProject(proj_dir, globaldata)
    SESS_ID = 1
    group_label = "all"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    subjects = project.load_subjects("full", [SESS_ID])
    for subject in subjects:
        # subject.mpr2nifti(subject.t1_dir, 1)
        hdr = subject.t1_data.read_header()
        print(str(subject.t1_data.get_image_dimension()))
        rrun(f"fsleyes {subject.t1_data} {subject.t1_brain_data}")
