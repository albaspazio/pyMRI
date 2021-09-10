from Global import Global
from Project import Project

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
    group_label = "controls_test"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================

    # subject = Subject("test", 1, project)
    # subject.create_file_system()
    # subject.mpr2nifti(subject.t1_dir, 1)

    subjects = project.load_subjects(group_label, SESS_ID)

    subject = subjects[0]
    # hdr = fslfun.read_header(subject.t1_data)
    # print(str(fslfun.get_image_dimension(subject.t1_data)))

    # subject.reslice_image("sag->axial")
    # subject.anatomical_processing_prebet()
    # subject.anatomical_processing_bet(betfparam=0.45, do_reg=False, do_overwrite=True)
    # subject.post_anatomical_processing()
    # subject.do_first("L_Amyg,R_Amyg", odn="first")
    # subject.do_first()

    subject.spm_segment()
