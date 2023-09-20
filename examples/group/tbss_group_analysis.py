import os
from Global import Global
from group.GroupAnalysis import GroupAnalysis
from Project import Project

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
        proj_dir = "/data/MRI/projects/test"
        project = Project(proj_dir, globaldata)
        SESS_ID = 1
        num_cpu = 1
        analysis = GroupAnalysis(project)

        # ==================================================================================================================
        # TBSS PREPARATION
        # ==================================================================================================================
        group_label = "a_group"
        population_label = "a_population"

        subjects_instances = project.get_subjects(group_label)
        main_folder = analysis.tbss_run_fa(subjects_instances, population_label, postreg="S")
        # main_folder = os.path.join(project.tbss_dir, population_label)
        analysis.tbss_run_alternatives(subjects_instances, main_folder, ["MD", "L1", "L23"])

        # ==================================================================================================================
        # parcelize MEAN SKELETON with XTRACT atlas:
        # ==================================================================================================================
        # xtract_folder = os.path.join(globaldata.framework_dir, "templates", "images", "xtract")
        # mask_tbss_skeleton_volumes_atlas(globaldata.fsl_std_mean_skeleton,
        #                                  os.path.join(xtract_folder, "xtract-tract-atlases-maxprob5-1mm"),
        #                                  os.path.join(xtract_folder, "xtract.json"))

        # ==================================================================================================================
        # parcelize MEAN SKELETON with HCP atlas:
        # ==================================================================================================================
        # hcp_folder = os.path.join("/data/MRI/templates/tracts/htc")
        # mask_tbss_skeleton_folder_atlas(globaldata.fsl_std_mean_skeleton, hcp_folder, thr=0.97)

        # ==================================================================================================================
        # exclude CREATE a new tbss 4d image
        # ==================================================================================================================
        srd_folder = os.path.join(project.tbss_dir, population_label)
        dest_folder = os.path.join(project.tbss_dir, "test")

        # analysis.create_analysis_folder_from_existing(srd_folder, dest_folder, [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19])

    except Exception as e:
        print(e)
        exit()



