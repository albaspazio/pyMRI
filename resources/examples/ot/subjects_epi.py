import os

from project.MRIGlobal import MRIGlobal
from project.MRIProject import MRIProject

# NOTE: Using relative paths with os.path.dirname(__file__) for project discovery

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
    proj_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "SeagateBackupPlusDrive", "MRI", "projects", "bisection_pisa")  # NOTE: relative path to project directory
    project = MRIProject(proj_dir, globaldata)
    SESS_ID = 1
    num_cpu = 4
    group_label = "single"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    kwparams = []

    epi_names = ["bis1", "bis2", "bis3", "loc1", "loc2"]
    epi_names_ex = ["bis1", "bis2", "bis3", "loc1", "loc3"]

    # ---------------------------------------------------------------------------------------------------------------------
    # CREATE FILE SYSTEM
    # ---------------------------------------------------------------------------------------------------------------------
    # load whole list & create its file system
    subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "create_file_system", [], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # for p in range(len(subjects)):
    #     for e in range(len(epi_names)):
    #         kwparams.append({"extpath":"/media/Data/Projects/fMRI_Pisa/epidata/" + subjects[p].label + "/" + epi_names[e], "cleanup":0, "session_label":epi_names[e]})
    # project.run_subjects_methods("epi2nifti", kwparams, ncore=num_cpu)
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
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "epi_merge", [{"premerge_labels":epi_names}], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # FIND THE EPI VOLUME CLOSEST TO PEPOLAR VOLUME AND USE IT TO CORRECT EPI DISTORSION
    # ---------------------------------------------------------------------------------------------------------------------
    subjects = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("epi", "epi_pepolar_correction", [], ncore=num_cpu, subjects=subjects)
