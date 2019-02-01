from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities
from pymri.Subject import Subject

if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir = "/media/alba/data/MRI/scripts"
    proj_dir = "/media/alba/dados/MRI/projects/temperamento_murcia"
    fsl_code = "509"

    if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
        print("Error")
        exit()

    globaldata = Global(global_script_dir)
    # ======================================================================================================================

    project = Project(proj_dir, globaldata, hasT1=True)
    SESS_ID = 1
    subject = Subject("001", 1, project)
    subject.create_file_system()

    subject.reslice_image("sag->axial")
    subject.anatomical_processing(do_cleanup=False)
    subject.post_anatomical_processing()
    # subject.do_first("L_Amyg,R_Amyg", odn="first")
    subject.do_first()

    num_cpu = 1
