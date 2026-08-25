import os
import traceback

from project.GlobalMRI import GlobalMRI
from project.ProjectMRI import ProjectMRI
from group.GroupAnalysis import GroupAnalysis
from myutility.utilities import Processes

# NOTE: Using relative paths with os.path.dirname(__file__) for project discovery

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = GlobalMRI(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        proj_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "nk")  # NOTE: relative path to project directory
        project = ProjectMRI(proj_dir, globaldata, "")

        subjproject = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "3T")  # NOTE: relative path to project directory
        subjproject = ProjectMRI(subjproject, globaldata, "")

        analysis = GroupAnalysis(project)

        population_label_psi= "psi_nk_28_FMRIB58"

        run_it = True
        # ==================================================================================================================

        models_subdir_name = "dti"

        gating_joined = "CD56BR_CD16NEGDIM_CD56DIM_CD16BR_CD56DIM_CD16DIMNEG_CD56NEG_CD16BR_NKG2C_CD57pos"

        corr_string_psi = "age_disdur"

        arr_populations_imm = ["sk_bd_imm", "td_psi_imm", "td_sk_bd_imm"]

        # many-process randomise wait for their completion before exiting (method does not return anything)
        analysis.start_tbss_randomize(population_label_psi, "FA", arr_populations_imm[0] + "_" + gating_joined, corr_string_psi, models_subdir_name, numcpu=4)
        analysis.start_tbss_randomize(population_label_psi, "L23", arr_populations_imm[0] + "_" + gating_joined, corr_string_psi, models_subdir_name, numcpu=4)

        # one-process randomise exit before completion returning the subprocess reference
        # thus user must explicitly wait for their completion
        processes:Processes = Processes()

        processes.append(analysis.start_tbss_randomize(population_label_psi, "MD", arr_populations_imm[0] + "_" + gating_joined, corr_string_psi, models_subdir_name, delay=5, perm=2, numcpu=1))
        processes.append(analysis.start_tbss_randomize(population_label_psi, "L1", arr_populations_imm[0] + "_" + gating_joined, corr_string_psi, models_subdir_name, delay=5, perm=2, numcpu=1))

        if run_it is True:
            processes.wait()
            processes.clear()

        a=1


    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()

