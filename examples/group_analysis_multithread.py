
import os

from Global import Global
from GroupAnalysis import GroupAnalysis
from Project import Project
from utility import startup_utilities, import_data_file

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
    # analysis.create_fslvbm_from_spm(subjects, os.path.join(project.vbm_dir, analysis_name, "subjects"), os.path.join(project.vbm_dir, analysis_name, "fslvbm"))


    #==================================================================================================================
    # THICKNESS DATA:
    # SPM.mat evaluation must be done through the cat gui. only then, you can define contrast and write results
    # thus put a breakpoint between : create_cat_thickness_2samplesttest_1cov_stats_1 & create_spm_2samplesttest_contrasts_results
    #==================================================================================================================

    # mat_blind_distance_vs_ctrl = analysis.create_cat_thickness_2samplesttest_1cov_stats_1("/data/MRI/projects/T15/group_analysis/mpr/thickness/blind_distance_vs_ctrl", "controls", "blind_full_far", "age")
    # analysis.create_spm_2samplesttest_contrasts_results(mat_blind_distance_vs_ctrl, "blind_minor", "blind_full_far")

    mat_blind_distance_vs_severely = analysis.create_cat_thickness_2samplesttest_1cov_stats_1("/data/MRI/projects/T15/group_analysis/mpr/thickness/blind_distance_vs_severely", "blind_severely", "blind_full_far", "age")
    analysis.create_spm_2samplesttest_contrasts_results(mat_blind_distance_vs_severely, "blind_severely > blind_full_far", "blind_full_far > blind_severely")

    # mat_blind_distance_vs_minor = analysis.create_cat_thickness_2samplesttest_1cov_stats_1("/data/MRI/projects/T15/group_analysis/mpr/thickness/blind_distance_vs_minor", "blind_minor", "blind_full_far", "age")
    # analysis.create_spm_2samplesttest_contrasts_results(mat_blind_distance_vs_minor, "blind_minor", "blind_full_far")





    # # test getting filtered data columns
    # datafile = os.path.join(project.script_dir, "data.dat")
    # data = import_data_file.read_tabbed_file_with_header(datafile)
    # # age = import_data_file.get_dict_column(data, "age")
    # # age = import_data_file.get_filtered_dict_column(data, "age", "subj", project.get_list_by_label("test"))
    # age = import_data_file.get_filtered_dict_column(data, "age", "cat_dist", ['0'])
    # str = import_data_file.list2spm_text_column(age)





