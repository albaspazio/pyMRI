from threading import Thread
# from Queue import Queue

from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities
from pymri.Subject import Subject
from pymri.utility import fslfun


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
    num_cpu     = 4
    group_label = "somecontrols"

    # load whole list & create its file system
    subjects    = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("create_file_system", [], project.get_subjects_labels(), nthread=num_cpu)

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    kwparams    = []

    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    for p in range(len(subjects)):
        kwparams.append({"extpath":"/data/MRI/projects/temp/" + subjects[p].label, "cleanup":0})
    project.run_subjects_methods("mpr2nifti", kwparams, project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRINT HEADER
    # ---------------------------------------------------------------------------------------------------------------------
    # for s in subjects:
    #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
    #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))

    # ---------------------------------------------------------------------------------------------------------------------
    # RESLICING
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("reslice_image", [{"dir":"sag->axial"}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRE BET
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("anatomical_processing_prebet", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # FREESURFER 1: autorecon1
    # ---------------------------------------------------------------------------------------------------------------------
    # talairach transf, conforming, skull-stripping
    subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("fs_reconall", [{"step":"-autorecon1"}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # BET
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("anatomical_processing_bet", [{"do_reg":False, "betfparam":[0.5]}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION
    # ---------------------------------------------------------------------------------------------------------------------
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    subjects    = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("anatomical_processing_spm_segment", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST BET
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects(group_label, SESS_ID)
    kwparams    = []
    for s in range(len(subjects)):
        kwparams.append({"do_nonlinreg":False, "betfparam":0.45})
    # project.run_subjects_methods("anatomical_processing_postbet", kwparams, project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST ANATOMICAL PROCESSING
    # ---------------------------------------------------------------------------------------------------------------------
    subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("post_anatomical_processing", [], project.get_subjects_labels(), nthread=num_cpu)

