import os
import traceback

from group.SPMConstants import SPMConstants
from project.MRIGlobal import MRIGlobal
from project.MRIProject import MRIProject
from group.GroupAnalysis import GroupAnalysis
from models.SPMModels import SPMModels
from group.PostModel import PostModel
from group.spm_utilities import Nuisance
from subject.SubjectsList import SubjectsList

# NOTE: Using relative paths with os.path.dirname(__file__) for project discovery

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = MRIGlobal(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        SESS_ID = 1

        ctrl_proj_dir   = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "controls")  # NOTE: relative path to project directory
        ctrl_project    = MRIProject(ctrl_proj_dir, globaldata)

        pat_proj_dir    = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "patients")  # NOTE: relative path to project directory
        pat_project     = MRIProject(pat_proj_dir, globaldata)

        group_analysis  = GroupAnalysis(pat_project)        # reference project for group-level analysis is the patients’ one
        spm_analysis    = SPMModels(pat_project)

        ctrl_group_label    = "ctrl_for_patients_study"     # an age-matched subset of all controls
        patient_group_label = "all_patients"                # the patient group of interest
        ctrl_subjects       = ctrl_project.get_subjects(ctrl_group_label, sess_ids=[SESS_ID])
        pat_subjects        = pat_project.get_subjects(patient_group_label, sess_ids=[SESS_ID])

        covs                = [Nuisance("gender"), Nuisance("age")]
        populations_name    = "a_population"
        analysis_name       = "an_analysis"

        # For cross-project analysis: combine subjects from both projects
        all_subjects = SubjectsList()
        all_subjects.extend(ctrl_subjects)
        all_subjects.extend(pat_subjects)  # create a list concatenating controls’ list with patient one

        population_dir      = group_analysis.create_vbm_spm_template_normalize(populations_name, all_subjects) # create a template of the given population
        post_model          = PostModel(SPMConstants.TSTT, covs, "cat_stats_2samples_ttest_contrasts_results", isSpm=False)

        spm_analysis.batchrun_group_stats(population_dir, SPMConstants.TSTT, SPMConstants.VBM_DARTEL, analysis_name, [ctrl_subjects, pat_subjects], covs=covs, post_model=post_model, runit=True)


    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


