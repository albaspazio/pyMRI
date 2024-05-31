import os

from Global import Global
from Project import Project
from group.GroupAnalysis import GroupAnalysis
from data.SubjectsDataDict import SubjectsDataDict
from utility.utilities import remove_items_from_list
from data.plot_data import scatter_plot_dataserie
#                                                           project.tbss_dir
# this script takes one or more TBSS stats results (projectx/group_analysis/tbss/, population, "stats", "FA/L23", analysis_name, ..._tfce_corrp_tstat1.nii.gz)
# and - tbss_clusterize_results_by_atlas......divide res maps into the 43 xtract's tracts, calc overlap
#     - tbss_summarize_clusterized_folder.....
if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = Global(fsl_code)

        # ======================================================================================================================
        proj_dir    = "/data/MRI/projects/past_controls"
        project     = Project(proj_dir, globaldata)
        num_cpu     = 1
        analysis    = GroupAnalysis(project)

        # ==================================================================================================================
        # GET SUBJECTS AND SP PARAM OF INTEREST
        group_label     = "test"  # 57
        subjects        = project.load_subjects(group_label, must_exist=False)

        datafile        = os.path.join(project.script_dir, "data_sensoryprofile_bis_57.txt")  # is a tab limited data matrix with a header in the first row
        data            = SubjectsDataDict(datafile)
        # ==================================================================================================================

        population      = "controls57_FMRIB58"  # "controls57"
        analysis_name   = "age_gender"
        data_labels     = ["age", "sp_sts", "sp_lr", "bis_t"]

        tbss_folder     = os.path.join(project.tbss_dir, population)
        stats_folder    = os.path.join(tbss_folder, "stats")

        doplot          = False
        # ==================================================================================================================
        tbssmaps            = ["tbss_FA_ctrl57_sp_sts_sp_lr_bis_t_x_age_gender_tfce_corrp_tstat1", "tbss_L23_ctrl57_sp_lr_sp_sts_sp_srs_sp_sa_bis_t_x_age_gender_tfce_corrp_tstat4"]
        tbssmaps            = ["tbss_FA_sp_lr_sp_sts_sp_srs_sp_sa_x_age_gender_tfce_corrp_tstat4", "tbss_L23_sp_lr_sp_sts_sp_srs_sp_sa_x_age_gender_tfce_corrp_tstat5"]
        tbssmaps            = ["tbss_FA_ctrl57_sp_sts_bis_t_x_age_gender_tfce_corrp_tstat1"]
        # sp_sts              = data.get_filtered_column("sp_sts")                                # tuple[2] of  [values], subj_label
        # age_spsts           = data.get_filtered_columns(["age", "sp_sts"])                      # tuple[2] of  [values], subj_label
        # age_spsts_bist      = data.get_filtered_columns(["age", "sp_sts", "bis_t"])             # tuple[2] of  [values], subj_label
        age_spsts_splr_bist = data.get_filtered_columns_by_subjects(data_labels)                              # tuple[2] of  [values], subj_label


        # ==================================================================================================================
        # create xtract tabbed file for a group of subjects reading their individual stats.csv file
        # ==================================================================================================================
        sign_tract_in_tbss  = ["af_r", "atr_l", "atr_r", "cbd_l", "cbp_l", "cst_r", "fa_l", "fa_r", "fmi", "mdlf_r", "or_r", "slf1_l", "slf1_r", "slf2_r", "slf3_r", "uf_l", "str_r"] #, "cc"]
        res_file            = os.path.join(project.tbss_dir, "valid_xtract_fa_l23.dat")
        analysis.xtract_export_group_data(subjects, res_file, values=["mean_FA", "mean_L23"], tracts=sign_tract_in_tbss)

        # ==================================================================================================================
        # segment tbss results by XTRACT:
        # - define over which tracts the tbss results span and divide the tbss results maps in tracts.
        # - calculate the mean values within each results' subpart
        # - plot correlations
        # ==================================================================================================================
        results = []
        for tbssmap in tbssmaps:

            if "L23" in tbssmap:
                measure = "L23"
            elif "FA" in tbssmap:
                measure = "FA"
            elif "L1" in tbssmap:
                measure = "L1"
            elif "MD" in tbssmap:
                measure = "MD"

            resmaps_root_dir    = os.path.join(stats_folder, measure, analysis_name)
            res_img             = os.path.join(resmaps_root_dir, tbssmap)
            subjects_images     = os.path.join(tbss_folder, measure)

            out_folder          = os.path.join(tbss_folder, "results", measure, tbssmap)
            plot_folder         = os.path.join(out_folder, "plots")

            # uses the union between template FA_skeleton and xtract's main tracts to clusterize a tbss output
            # analysis.tbss_clusterize_results_by_atlas(res_img, out_folder, tracts_labels=globaldata.dti_xtract_labels, tracts_dir=globaldata.dti_xtract_dir)  #, log_file=measure+"_tbss_segm_on_xtract.txt")

            # extract values FROM CLUSTERIZED TBSS RESULTS (from a significant tbss image, get mean dti values calculated with given tracts)
            # res_file = analysis.tbss_summarize_clusterized_folder(out_folder, age_spsts_splr_bist, ["age", "sp_sts", "sp_lr", "bis_t"], tbss_folder, subj_img_postfix="_FA_to_target_" + measure)    # for other modalities
            # res_file = "/data/MRI/projects/past_controls/group_analysis/tbss/controls57_FMRIB58/results/scatter_tracts_tbss_FA_ctrl57_sp_sts_sp_lr_bis_t_x_age_gender_tfce_corrp_tstat1_age_sp_sts_sp_lr_bis_t.dat"

            data                = SubjectsDataDict(res_file)
            valid_tract_labels  = remove_items_from_list(data.header, data_labels + ["subj"])  # in data.header we have subj and the data column
            if doplot:
                os.makedirs(plot_folder, exist_ok=True)
                for id,data_label in enumerate(data_labels):
                    for idt,trlab in enumerate(valid_tract_labels):
                        fig_file = os.path.join(plot_folder, trlab + "_" + data_label + ".png")
                        scatter_plot_dataserie(data.get_subjects_column(colname=data_label), data.get_subjects_column(colname=trlab), fig_file)

    except Exception as e:
        print(e)
        exit()





















    # ==================================================================================================================
    # segment tbss results by HBC
    # ==================================================================================================================
    # results = []
    # out_folder  = os.path.join(project.tbss_dir, "results_sp_sts_hbc_fmrib58")
    # atlas_dir   = "/data/MRI/templates/tracts/hbc/mean_skeleton"
    # labels      = read_list_from_file(os.path.join("/data/MRI/templates/tracts/hbc", "labels.txt"))
    # for roi in tbssmap:
    #     res_img = os.path.join(resmaps_root_dir, roi)
    #     analysis.clusterize_tbss_results_by_atlas(res_img, labels, atlas_dir, out_folder)



    # ==================================================================================================================
    # FROM GENERIC ROI
    # ==================================================================================================================
    # subj_img_postfix = "_FA_FA_to_target"
    # for roi in tbssmap:
    #     roi_img = os.path.join(resmaps_root_dir, roi)
    #     rrun("fslmaths " + roi_img + " -thr 0.95 -bin " + roi_img + "_mask")
    # out_folder  = os.path.join(project.tbss_dir, "results_sp_sts_htc_fmrib58")
    #
    # results = []
    # for roi in tbssmap:
    #     roi_mask_img = os.path.join(resmaps_root_dir, roi + "_mask")
    #     roi_row = []
    #
    #     for subj in subjects:
    #         subj_img        = os.path.join(subjects_images, subj.dti_fit_label + subj_img_postfix)
    #         subj_img_masked = os.path.join(subjects_images, subj.dti_fit_label + subj_img_postfix + "_masked")
    #
    #         rrun("fslmaths " + subj_img + " -mas " + roi_mask_img + " " + subj_img_masked)
    #         val = float(rrun("fslstats " + subj_img_masked + " -M").strip())
    #         imrm([subj_img_masked])
    #         roi_row.append(val)
    #
    #     results.append(roi_row)
    #
    # fig_file = os.path.join(stats_folder, "sp_sts.png")
    # plot_data.scatter_plot_dataserie(sp_sts[0], results[0], fig_file)
