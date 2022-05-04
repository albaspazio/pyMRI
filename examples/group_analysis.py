import os
import traceback

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from group.SPMModels import SPMModels

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
        proj_dir = "/data/MRI/projects/T15"
        project = Project(proj_dir, globaldata)     # automatically load PROJDIR/script/data.dat if present
        SESS_ID = 1
        num_cpu = 1
        group_label = "blind_28_seq1"

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        subjects = project.load_subjects(group_label, SESS_ID)
        # project.add_icv_to_data(group_label) # add icv to data

        analysis            = GroupAnalysis(project)
        spm_analysis        = SPMModels(project)

        # ==================================================================================================================
        # VBM DATA:
        # ==================================================================================================================
        # template
        vbm_analysis_name   = "c28_b50"
        vbm_outdir          = os.path.join(project.vbm_dir, vbm_analysis_name)

        # analysis.create_vbm_spm_template_normalize(vbm_analysis_name, subjects)

        # ==================================================================================================================
        # THICKNESS DATA:
        # ==================================================================================================================
        #
        # def batchrun_cat_thickness_stats_factdes_1group_multregr(self, statsdir, grp_label, cov_names, anal_name,
        #                                                        cov_interactions=None, data_file=None, sess_id=1,
        #                                                        spm_template_name="spm_stats_1group_multiregr_check_estimate",
        #                                                        spm_contrasts_template_name="", mult_corr="FWE", pvalue=0.05,
        #                                                        cluster_extend=0):
        group_label = "test"
        cov_names   = ["gender", "age"]
        anal_name   = "multregr_age_gender"
        statsdir    = "/data/MRI/projects/T15/group_analysis/mpr/thickness/" + anal_name

        # spm_analysis.batchrun_cat_thickness_stats_factdes_1group_multregr(statsdir, group_label, cov_names, spm_contrasts_template_name="")


        # def batchrun_cat_thickness_stats_factdes_1Wanova(self, statsdir, groups_labels, cov_name, cov_interaction=1,
        #                                                data_file=None, sess_id=1,
        #                                                spm_template_name="spm_stats_1Wanova_check_estimate",
        #                                                spm_contrasts_template_name=""):

        group_labels = ["t1", "t2", "t3"]
        cov_names   = ["gender", "age"]
        anal_name   = "1Wanova_3_groups_age_gender"
        statsdir    = "/data/MRI/projects/T15/group_analysis/mpr/thickness/" + anal_name

        # spm_analysis.batchrun_cat_thickness_stats_factdes_1Wanova(statsdir, group_labels, cov_names, spm_contrasts_template_name="")






    except Exception as e:
        traceback.print_exc()

        print(e)
        exit()


