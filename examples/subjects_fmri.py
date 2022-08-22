import os

from Global import Global
from Project import Project
from group.SPMStatsUtils import FmriProcParams
from subject.Subject import Subject
from numpy import sort

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
        proj_dir = "/data/MRI/projects/roelof"
        project  = Project(proj_dir, globaldata)
        SESS_ID  = 1
        num_cpu  = 1

        TR              = 0.72
        num_slices      = 72
        slice_timing    = [0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465,
                           0.155, 0.5425, 0.2325, 0.6225]
        ref_slice       = 0.31
        fmri_params     = FmriProcParams(TR, num_slices, slice_timing, ref_slice)

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        epi_names   = ["target", "frame"]

        # ---------------------------------------------------------------------------------------------------------------------
        group_label = "test"
        subjects    = project.load_subjects(group_label, SESS_ID)
        # ---------------------------------------------------------------------------------------------------------------------


        # ---------------------------------------------------------------------------------------------------------------------
        # PREPROCESSING (coregistration, segment, normalize, smooth)
        # ---------------------------------------------------------------------------------------------------------------------
        # def spm_fmri_preprocessing(self, num_slices, TR, TA=-1, acq_scheme=0, ref_slice=-1, slice_timing=None,
        #                            epi_images=None, smooth=6, spm_template_name='subj_spm_fmri_full_preprocessing'):
        kwparams = []
        for s in subjects:
            kwparams.append({"epi_images":[os.path.join(s.fmri_dir, s.label + "-fmri_" + epi_names[0]), os.path.join(s.fmri_dir, s.label + "-fmri_" + epi_names[1])],
                             "fmri_params":fmri_params, "spm_template_name":"subj_spm_fmri_full_preprocessing"})

        project.run_subjects_methods("epi", "spm_fmri_preprocessing", kwparams, ncore=num_cpu)




        # ---------------------------------------------------------------------------------------------------------------------
        # REMOVE SLICES
        # ---------------------------------------------------------------------------------------------------------------------
        # subjects = project.load_subjects("removeSlice", SESS_ID)
        # for s in subjects:
        #     for sess in epi_names:
        #         imgname = os.path.join(s.fmri_dir, s.label + "-epi_" + sess)
        #         remove_slices(imgname, 1)

        # ---------------------------------------------------------------------------------------------------------------------
        # FIND THE EPI VOLUME CLOSEST TO PEPOLAR VOLUME AND USE IT TO CORRECT EPI DISTORSION
        # ---------------------------------------------------------------------------------------------------------------------
        # for sess in epi_names_ex:
        #     kwparams = []
        #     for s in subjects:
        #         in_ap_img = os.path.join(s.fmri_dir, "a" + s.label + "-epi_" + sess)
        #         kwparams.append({"in_ap_img":in_ap_img, "in_pa_img":s.fmri_pa_data, "acq_params": project.topup_fmri_params})
        #         project.run_subjects_methods("epi", "topup_correction", kwparams, project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # SLICE TIMING
        # ---------------------------------------------------------------------------------------------------------------------
        # kwparams = []
        # for sess in epi_names:
        #     for s in subjects:
        #         imgname = os.path.join(s.fmri_dir, s.label + "-fmri_" + sess)
        #         kwparams.append({"epi_image": imgname, "fmri_params":fmri_params})
        #
        # project.run_subjects_methods("epi", "slice_timing", kwparams, ncore=num_cpu)

        # ==================================================================================================================
        # CHECK ALL REGISTRATION
        # ==================================================================================================================
        # subjects    = project.load_subjects(group_label, SESS_ID)

        # outdir      = os.path.join(project.group_analysis_dir, "registration_check_mpr_2_std")
        # project.check_all_coregistration(outdir, _from=["hr"], _to=["std"], num_cpu=num_cpu)

        # outdir      = os.path.join(project.group_analysis_dir, "registration_check_2_std")
        # project.check_all_coregistration(outdir, _from=["hr", "fmri"], _to=["std"], num_cpu=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # EPI CO-REGISTRATION TO TEMPLATE
        # ---------------------------------------------------------------------------------------------------------------------
        # subjects    = project.load_subjects(group_label, SESS_ID)
        # for p in range(len(subjects)):
        #     kwparams.append({"do_bbr":False, "is_rs":False, "epi_img":os.path.join(subjects[p].epi_dir, "ar" + subjects[p].epi_image_label)})
        # project.run_subjects_methods("transform_epi", kwparams, project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # TRANSFORM AR => WAR => SWAR (normalize & smooth)
        # ---------------------------------------------------------------------------------------------------------------------
        # subjects    = project.load_subjects(group_label, SESS_ID)
        # project.run_subjects_methods("epi_fsl2standard_smooth", [], project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # TRANSFORM WAR => SWAR  (smooth only)
        # ---------------------------------------------------------------------------------------------------------------------
        # to rename existing swar:
        # cd /data/MRI/projects/BISECTION_PISA2/subjects
        # for s in *; do echo $s; mv $s/s1/epi/swar$s-epi.nii $s/s1/epi/s1war$s-epi.nii; done
        # #
        # subjects    = project.load_subjects(group_label, SESS_ID)
        # project.run_subjects_methods("epi_smooth",  [{"epi_image":"WAR", "fwhm":6}] , project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1st level stat analysis 5 regressors
        # ---------------------------------------------------------------------------------------------------------------------
        # import matlab.engine
        # eng     = matlab.engine.start_matlab()
        # subjects = project.load_subjects(group_label, SESS_ID)
        # kwparams = []
        # for s in subjects:
        #     a       = eng.load(os.path.join(project.dir, "subjects", s.label, "s1", "epi", "stimuli", "sub" + s.label + ".mat"), nargout=1)
        #     onsets  = []
        #     onsets.append(a["sub_salva"]["Time_ref"][:]._data)
        #     onsets.append(a["sub_salva"]["Time_bisDX"][:]._data)
        #     onsets.append(a["sub_salva"]["Time_bisSX"][:]._data)
        #     onsets.append(a["sub_salva"]["Time_locDX"][:]._data)
        #     onsets.append(a["sub_salva"]["Time_locSX"][:]._data)
        #
        #     kwparams.append({"analysis_name":"stats_10cond_SWAR", "num_slices":num_slices, "TR":TR, "events_unit":"secs", "input_images": "SWAR", "spm_template_name":"/data/MRI/projects/BISECTION_PISA2/script/epi/spm/template_individual_stats_10contr_analysis_job.m", "onsets":onsets})
        #
        # project.run_subjects_methods("epi_spm_fmri_1st_level_analysis", kwparams, project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1st level stat analysis 3 regressors
        # ---------------------------------------------------------------------------------------------------------------------
        # import matlab.engine
        # eng      = matlab.engine.start_matlab()
        # subjects = project.load_subjects(group_label, SESS_ID)
        # kwparams = []
        # for s in subjects:
        #     a       = eng.load(os.path.join(project.dir, "subjects", s.label, "s1", "epi", "stimuli", "sub" + s.label + ".mat"), nargout=1)
        #     onsets  = []
        #
        #     onsets.append(a["sub_salva"]["Time_ref"][:]._data)
        #     onsets.append(sort(a["sub_salva"]["Time_bisDX"][:]._data + a["sub_salva"]["Time_bisSX"][:]._data))
        #     onsets.append(sort(a["sub_salva"]["Time_locDX"][:]._data + a["sub_salva"]["Time_locSX"][:]._data))
        #     kwparams.append({"analysis_name":"stats_3regr_7cond_AR", "num_slices":num_slices, "TR":TR, "events_unit":"secs", "input_images": "AR", "spm_template_name":"/data/MRI/projects/BISECTION_PISA2/script/epi/spm/template_individual_stats_3regr_7contr_analysis_job.m", "onsets":onsets})
        #
        # project.run_subjects_methods("epi_spm_fmri_1st_level_analysis", kwparams, project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1st level stat analysis: single sessions 3 regressors
        # ---------------------------------------------------------------------------------------------------------------------
        # images_type = "ra"
        #
        # import matlab.engine
        #
        # eng = matlab.engine.start_matlab()
        # subjects = project.load_subjects(group_label, SESS_ID)
        # kwparams = []
        # rp_filenames = []
        # input_images = []
        # for s in subjects:
        #     onsets = []
        #     for epi_name in epi_names:
        #         session = []
        #         a = eng.load(os.path.join(project.dir, "subjects", s.label, "s1", "fmri", "stimuli", s.label + "_" + epi_name + ".mat"), nargout=1)
        #
        #         if "bis" in epi_name:
        #             session.append(a["sub_salva_single"]["Time_ref"][:]._data)
        #             session.append(sort(a["sub_salva_single"]["Time_bisDX"][:]._data + a["sub_salva_single"]["Time_bisSX"][:]._data))
        #         else:
        #             session.append(sort(a["sub_salva_single"]["Time_locDX"][:]._data + a["sub_salva_single"]["Time_locSX"][:]._data))
        #         onsets.append(session)
        #         input_images.append(os.path.join(project.dir, "subjects", s.label, "s1", "fmri", images_type + s.label + "-epi_" + epi_name + ".nii"))
        #         rp_filenames.append(os.path.join(project.dir, "subjects", s.label, "s1", "fmri", "rp_a" + s.label + "-epi_" + epi_name + ".txt"))
        #
        #     kwparams.append({"analysis_name": "stats_multisessions_3regr_7cond_AR", "num_slices": num_slices, "TR": TR, "events_unit": "secs", "input_images": input_images, "spm_template_name": os.path.join(project.script_dir, "fmri", "spm", "template_individual_stats_multisessions_3regr_7contr_analysis"), "conditions_lists": onsets, "rp_filenames": rp_filenames})
        #
        # project.run_subjects_methods("epi", "spm_fmri_1st_level_multisessions_custom_analysis", kwparams, project.get_subjects_labels(), nthread=num_cpu)


    except Exception as e:
        print(e)
        exit()

