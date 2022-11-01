import os

from Global import Global
from Project import Project
from group.spm_utilities import FmriProcParams, Contrast, SubjCondition
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
        group_label = "test"

        TR              = 0.72
        num_slices      = 72
        slice_timing    = [0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465,
                           0.155, 0.5425, 0.2325, 0.6225]
        st_refslice     = 0.31
        time_bins       = 9     # 72/8

        fmri_params     = FmriProcParams(TR, num_slices, slice_timing, st_refslice, time_bins)

        contrasts_trg   = [Contrast("c1", "[1 0 1 0 1]"),
                           Contrast("c2: same > neutral", "[-1 0 1]"),
                           Contrast("c3: neutral > same", "[1 0 -1]")
                          ]

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        epi_names       = ["target", "frame"]

        # ---------------------------------------------------------------------------------------------------------------------
        subjects        = project.load_subjects(group_label, SESS_ID)
        kwparams = []
        for s in subjects:
            kwparams.append({"epi_images":[os.path.join(s.fmri_dir, s.label + "-fmri_" + epi_names[0] ), os.path.join(s.fmri_dir, s.label + "-fmri_" + epi_names[1])],
                             "fmri_params":fmri_params, "spm_template_name":"subj_spm_fmri_full_preprocessing_mni"})
        project.run_subjects_methods("epi", "spm_fmri_preprocessing", kwparams, ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1st level stat analysis: two separate sessions, 3 regressors
        # ---------------------------------------------------------------------------------------------------------------------
        subjects        = project.load_subjects(group_label, SESS_ID)
        epi_names       = ["target", "frame"]
        images_type     = "swar"

        import matlab.engine
        eng = matlab.engine.start_matlab()

        kwparams     = []

        for s in subjects:
            rp_filenames = []
            input_images = []
            sessions_cond= []

            for epi_name in epi_names:
                conditions = eng.load(os.path.join(project.script_dir, "fmri", "fmri_logs", s.label + "_" + epi_name + ".mat"), nargout=1)

                session = []
                session.append(SubjCondition(epi_name + ": neutral",    sort(conditions["task_onsets"]["onsets_neutral"][:]._data)))
                session.append(SubjCondition(epi_name + ": same",       sort(conditions["task_onsets"]["onsets_same"][:]._data)))
                session.append(SubjCondition(epi_name + ": opposite",   sort(conditions["task_onsets"]["onsets_opposite"][:]._data)))
                sessions_cond.append(session)

                input_images.append(os.path.join(s.fmri_dir, images_type + s.label + "-fmri_" + epi_name + ".nii"))
                rp_filenames.append(os.path.join(s.fmri_dir, "rp_" + s.label + "-fmri_" + epi_name + ".txt"))

            kwparams.append({"analysis_name": "stats_2sessions_3regr", "fmri_params": fmri_params, "contrasts": contrasts_trg, "res_report": result_report,
                             "input_images": input_images, "conditions_lists": sessions_cond, "rp_filenames": rp_filenames})

        project.run_subjects_methods("epi", "spm_fmri_1st_level_analysis", kwparams, ncore=num_cpu)






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
        #         kwparams.append({"in_ap_images":[in_ap_img], "in_pa_img":s.fmri_pa_data, "acq_params": project.topup_fmri_params})
        #         project.run_subjects_methods("epi", "topup_corrections", kwparams, project.get_subjects_labels(), nthread=num_cpu)

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

    except Exception as e:
        print(e)
        exit()

