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
    proj_dir = "/data/MRI/projects/T15"
    project = Project(proj_dir, globaldata)
    SESS_ID = 1
    num_cpu = 8
    group_label = "all"

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    kwparams = []

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
    # project.run_subjects_methods("prebet", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # FREESURFER 1: autorecon1
    # ---------------------------------------------------------------------------------------------------------------------
    # talairach transf, conforming, skull-stripping
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("fs_reconall", [{"step":"-autorecon1"}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("bet", [{"do_reg":True, "betfparam":[0.5]}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION
    # ---------------------------------------------------------------------------------------------------------------------
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("spm_segment", [{"do_overwrite":True, "do_bet_overwrite":True}], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION INTERACTIVE (SET ORIGIN BEFORE)
    # ---------------------------------------------------------------------------------------------------------------------
    # it let user set the image origin before proceeding. suitable for some mpr that otherwise do not segment properly.
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("spm_segment", [{"do_overwrite":True, "do_bet_overwrite":False, "set_origin":True}], project.get_subjects_labels(), nthread=1)

    # ---------------------------------------------------------------------------------------------------------------------
    # CAT SEGMENTATION & THICKNESS
    # ---------------------------------------------------------------------------------------------------------------------
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    # default usage analyzes in parallel num_cpu subjects using one CPU for each.
    segmentation_template = os.path.join(project.group_analysis_dir, "templates", "com", "mw_com_prior_Age_0070.nii")
    coregistration_template = os.path.join(project.group_analysis_dir, "templates", "com",
                                           "mw_com_Template_1_Age_0070.nii")
    calc_surfaces = 1
    subjects = project.load_subjects(group_label, SESS_ID)
    project.run_subjects_methods("cat_segment", [
        {"do_overwrite": True, "seg_templ": segmentation_template, "coreg_templ": coregistration_template,
         "calc_surfaces": calc_surfaces, "num_proc": 1}], project.get_loaded_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM TISSUE VOLUMES
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("spm_tissue_volumes", [], project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # COMPARE BRAIN EXTRACTION
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.compare_brain_extraction(os.path.join(project.mpr_dir, group_label))

    # ---------------------------------------------------------------------------------------------------------------------
    # INTERACTIVE FREESURFER BRAIN SELECTION (check whether using freesurfer brainmask in place of BET one)
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("use_fs_brainmask", [{"do_clean":True}], project.get_subjects_labels(), nthread=1)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # kwparams    = []
    # for s in range(len(subjects)):
    #     kwparams.append({"do_nonlinreg":True, "betfparam":0.5, "do_overwrite":True})
    # project.run_subjects_methods("postbet", kwparams, project.get_subjects_labels(), nthread=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST ANATOMICAL PROCESSING
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.load_subjects(group_label, SESS_ID)
    # project.run_subjects_methods("finalize", [], project.get_subjects_labels(), nthread=num_cpu)
