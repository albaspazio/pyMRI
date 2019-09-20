import os

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
    proj_dir    = "/media/campus/SeagateBackupPlusDrive/MRI/projects/bisection_pisa"
    project     = Project(proj_dir, globaldata)
    SESS_ID     = 1
    num_cpu     = 4
    group_label = "single"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    kwparams    = []

    epi_names = ["bis1", "bis2", "bis3", "loc1", "loc2"]
    epi_names_ex = ["bis1", "bis2", "bis3", "loc1", "loc3"]

    # ---------------------------------------------------------------------------------------------------------------------
    # CREATE FILE SYSTEM
    # ---------------------------------------------------------------------------------------------------------------------
    # load whole list & create its file system
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("create_file_system", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # for p in range(len(subjects)):
    #     for e in range(len(epi_names)):
    #         kwparams.append({"extpath":"/media/Data/Projects/fMRI_Pisa/epidata/" + subjects[p].label + "/" + epi_names[e], "cleanup":0, "session_label":epi_names[e]})
    # project.run_subjects_methods("epi2nifti", kwparams, project.get_subjects_labels(), nthread=num_cpu)
    #
    # # ---------------------------------------------------------------------------------------------------------------------
    # PRINT HEADER
    # ---------------------------------------------------------------------------------------------------------------------
    # for s in subjects:
    #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
    #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))


    # ---------------------------------------------------------------------------------------------------------------------
    # MERGE NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("epi_merge", [{"premerge_labels":epi_names}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # FIND THE EPI VOLUME CLOSEST TO PEPOLAR VOLUME AND USE IT TO CORRECT EPI DISTORSION
    # ---------------------------------------------------------------------------------------------------------------------
    subjects = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("epi_pepolar_correction", [], project.get_subjects_labels(), nthread=num_cpu)
