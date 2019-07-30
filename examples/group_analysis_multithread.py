
import os

from pymri.Global import Global
from pymri.GroupAnalysis import GroupAnalysis
from pymri.Project import Project
from pymri.utility import startup_utilities


if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir   = "/data/MRI/bash-fsl-pipeline"
    proj_dir            = "/data/MRI/projects/T15"
    # proj_dir            = "/data/MRI/projects/T3"
    fsl_code            = "601"

    if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
        print("Error")
        exit()

    globaldata = Global(global_script_dir)

    # ======================================================================================================================
    # SUBJECTS
    # ======================================================================================================================
    project     = Project(proj_dir, globaldata, hasT1=True)
    SESS_ID     = 1
    num_cpu     = 1
    group_label = "all"

    subjects    = project.load_subjects(group_label, SESS_ID)

    # ======================================================================================================================
    # VBM
    # ======================================================================================================================

    # template
    analysis_name   = "c28_b50"
    outdir          = os.path.join(project.vbm_dir, analysis_name)


    analysis = GroupAnalysis(project)
    # analysis.create_vbm_spm_template_normalize(analysis_name, subjects)

    # analysis.add_icv_2_data_matrix(subjects, os.path.join(project.dir, "data.dat"))

    analysis.create_fslvbm_from_spm(subjects, os.path.join(project.vbm_dir, analysis_name, "subjects"), os.path.join(project.vbm_dir, analysis_name, "fslvbm"))




