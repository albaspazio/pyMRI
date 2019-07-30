
import os

from pymri.Global import Global
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
    group_label = "single"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    kwparams    = []

    # ---------------------------------------------------------------------------------------------------------------------
    # CREATE FILE SYSTEM
    # ---------------------------------------------------------------------------------------------------------------------
    # load whole list & create its file system
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("create_file_system", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # for p in range(len(subjects)):
        # kwparams.append({"extpath":"/data/MRI/projects/T3/" + subjects[p].label, "cleanup":0})
    # project.run_subjects_methods("mpr2nifti", kwparams, project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRINT HEADER
    # ---------------------------------------------------------------------------------------------------------------------
    # for s in subjects:
    #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
    #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))

    # ---------------------------------------------------------------------------------------------------------------------
    # RESLICING
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("reslice_image", [{"dir":"sag->axial"}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRE BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_prebet", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # FREESURFER 1: autorecon1
    # ---------------------------------------------------------------------------------------------------------------------
    # talairach transf, conforming, skull-stripping
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_fs_reconall", [{"step":"-autorecon1"}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_bet", [{"do_reg":True, "betfparam":[0.5]}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION
    # ---------------------------------------------------------------------------------------------------------------------
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_spm_segment", [{"do_overwrite":True, "do_bet_overwrite":True, "set_origin":False}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION INTERACTIVE (SET ORIGIN BEFORE)
    # ---------------------------------------------------------------------------------------------------------------------
    # it let user set the image origin before proceeding. suitable for some mpr that otherwise do not segment properly.
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    subjects    = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("mpr_spm_segment", [{"do_overwrite":True, "do_bet_overwrite":False, "set_origin":True}], project.get_subjects_labels(), nthread=1)


    # ---------------------------------------------------------------------------------------------------------------------
    # SPM TISSUE VOLUMES
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_spm_tissue_volumes", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # COMPARE BRAIN EXTRACTION
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.compare_brain_extraction(os.path.join(project.mpr_dir, group_label))

    # ---------------------------------------------------------------------------------------------------------------------
    # INTERACTIVE FREESURFER BRAIN SELECTION (check whether using freesurfer brainmask in place of BET one)
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_use_fs_brainmask", [{"do_clean":True}], project.get_subjects_labels(), nthread=1)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # kwparams    = []
    # for s in range(len(subjects)):
    #     kwparams.append({"do_nonlinreg":True, "betfparam":0.5, "do_overwrite":True})
    # project.run_subjects_methods("mpr_postbet", kwparams, project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST ANATOMICAL PROCESSING
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("mpr_finalize", [], project.get_subjects_labels(), nthread=num_cpu)


