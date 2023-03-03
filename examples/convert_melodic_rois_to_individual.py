import os

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from group.group_analysis import convert_melodic_rois_to_individual

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = Global(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        proj_dir_bd    = "/data/MRI/projects/past_bipolar"
        proj_dir_td    = "/data/MRI/projects/past_controls"

        project_bd     = Project(proj_dir_bd, globaldata)
        project_td     = Project(proj_dir_td, globaldata)

        SESS_ID     = 1
        num_cpu     = 18
        group_label_bd = "bd_rs"
        group_label_td = "all_rs"

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        subjects_bd = project_bd.load_subjects(group_label_bd, SESS_ID)
        subjects_td = project_td.load_subjects(group_label_td, SESS_ID)

        # TR = 2.0
        template_name = "templ_ctrl_bd_all266"
        population_name = "bd_ctrl_all266"

        dr_dir          = os.path.join(project_bd.melodic_dr_dir, template_name, population_name)
        mel_res4_dir    = os.path.join(dr_dir, "results", "standard4")

        analysis_bd = GroupAnalysis(project_bd)
        roi_names = ["CEREB_bd_gt_ctrl_x_age_rIX"]

        rois_paths = []
        for roi in roi_names:
            rois_paths.append(os.path.join(mel_res4_dir, roi))

        # project, templ_name, popul_name, rois_list, subjs, thr=0.1, report_file="transform_report", num_cpu=1, mni_2mm_brain=None
        convert_melodic_rois_to_individual(project_bd, template_name, population_name, rois_paths, [subjects_bd, subjects_td], 0.25,num_cpu=num_cpu)

    except Exception as e:
        print(e)
        exit()






