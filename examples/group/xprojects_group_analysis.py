import traceback

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from group.SPMModels import SPMModels
from group.PostModel import PostModel
from group.spm_utilities import Nuisance

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
        SESS_ID = 1

        ctrl_proj_dir   = "/data/MRI/projects/controls"
        ctrl_project    = Project(ctrl_proj_dir, globaldata)

        pat_proj_dir    = "/data/MRI/projects/patients"
        pat_project     = Project(pat_proj_dir, globaldata)

        group_analysis  = GroupAnalysis(pat_project)        # reference project for group-level analysis is the patients’ one
        spm_analysis    = SPMModels(pat_project)

        ctrl_group_label    = "ctrl_for_patients_study"     # an age-matched subset of all controls
        patient_group_label = "all_patients"                # the patient group of interest
        ctrl_subjects       = ctrl_project.get_subjects(ctrl_group_label, SESS_ID)
        pat_subjects        = ctrl_project.get_subjects(patient_group_label, SESS_ID)

        covs                = [Nuisance("gender"), Nuisance("age")]
        populations_name    = "a_population"
        analysis_name       = "an_analysis"

        all_subjects = ctrl_subjects.append(pat_subjects)  # create a list concatenating controls’ list with patient one

        population_dir      = group_analysis.create_vbm_spm_template_normalize(populations_name, all_subjects) # create a template of the given population
        post_model          = PostModel("cat_stats_2samples_ttest_contrasts_results", regressors=covs, isSpm=False)

        spm_analysis.batchrun_spm_vbm_dartel_stats_factdes_2samplesttest(population_dir, analysis_name, [ctrl_subjects, pat_subjects], covs, post_model)


    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


