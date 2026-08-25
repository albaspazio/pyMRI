import os

from project.GlobalMRI import GlobalMRI
from project.ProjectMRI import ProjectMRI

# NOTE: Using relative paths with os.path.dirname(__file__) for project discovery

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "601"
    try:
        globaldata = GlobalMRI(fsl_code)

    except Exception as e:
        print(e)
        exit()

    # ======================================================================================================================
    # HEADER
    # ======================================================================================================================
    proj_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "T15")  # NOTE: relative path to project directory
    project = ProjectMRI(proj_dir, globaldata)
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
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "create_file_system", [], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # CONVERT 2 NIFTI
    # ---------------------------------------------------------------------------------------------------------------------
    # for p in range(len(subjects)):
    # kwparams.append({"extpath":"/data/MRI/projects/T3/" + subjects[p].label, "cleanup":0})
    # project.run_subjects_methods("mpr2nifti", kwparams, ncore=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRINT HEADER
    # ---------------------------------------------------------------------------------------------------------------------
    # for s in subjects:
    #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
    #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))

    # ---------------------------------------------------------------------------------------------------------------------
    # RESLICING
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "reslice_image", [{"dir":"sag->axial"}], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # PRE BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "prebet", [], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # FREESURFER 1: autorecon1
    # ---------------------------------------------------------------------------------------------------------------------
    # talairach transf, conforming, skull-stripping
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "fs_reconall", [{"step":"-autorecon1"}], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "bet", [{"do_reg":True, "betfparam":[0.5]}], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION
    # ---------------------------------------------------------------------------------------------------------------------
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "spm_segment", [{"do_overwrite":True, "do_bet_overwrite":True}], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM SEGMENTATION INTERACTIVE (SET ORIGIN BEFORE)
    # ---------------------------------------------------------------------------------------------------------------------
    # it let user set the image origin before proceeding. suitable for some mpr that otherwise do not segment properly.
    # the proj_script/mpr/spm/batch folder must be already in the matlab path
    # it may over-ride both BET and FS skull-stripping results
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "spm_segment", [{"do_overwrite":True, "do_bet_overwrite":False, "set_origin":True}], ncore=1, subjects=subjects)

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
    subjects = project.get_subjects(group_label, sess_ids=[SESS_ID])
    project.run_subjects_methods("mpr", "cat_segment", [{"do_overwrite": True, "seg_templ": segmentation_template, "coreg_templ": coregistration_template,
                                                         "calc_surfaces": calc_surfaces, "num_proc": 1}], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # SPM TISSUE VOLUMES
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, sess_ids=[SESS_ID])
    # project.run_subjects_methods("", "spm_tissue_volumes", [], ncore=num_cpu, subjects=subjects)

    # ---------------------------------------------------------------------------------------------------------------------
    # COMPARE BRAIN EXTRACTION
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, [SESS_ID])
    # project.compare_brain_extraction(os.path.join(project.mpr_dir, group_label))

    # ---------------------------------------------------------------------------------------------------------------------
    # INTERACTIVE FREESURFER BRAIN SELECTION (check whether using freesurfer brainmask in place of BET one)
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, [SESS_ID])
    # project.run_subjects_methods("use_fs_brainmask", [{"do_clean":True}], ncore=1)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST BET
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, [SESS_ID])
    # kwparams    = []
    # for s in range(len(subjects)):
    #     kwparams.append({"do_nonlinreg":True, "betfparam":0.5, "do_overwrite":True})
    # project.run_subjects_methods("postbet", kwparams, ncore=num_cpu)

    # ---------------------------------------------------------------------------------------------------------------------
    # POST ANATOMICAL PROCESSING
    # ---------------------------------------------------------------------------------------------------------------------
    # subjects    = project.get_subjects(group_label, [SESS_ID])
    # project.run_subjects_methods("finalize", [], ncore=num_cpu)
