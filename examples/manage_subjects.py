from Global import Global
from Project import Project
from utility.exceptions import SubjectListException

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
        num_cpu = 17

        group_label = "all"

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        kwparams = []

        # ---------------------------------------------------------------------------------------------------------------------
        # 0: LOAD SUBJECTS
        # ---------------------------------------------------------------------------------------------------------------------
        # load whole list
        subjects = project.load_subjects(group_label, SESS_ID)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1: CREATE FILE SYSTEM
        # ---------------------------------------------------------------------------------------------------------------------
        # create file system
        # project.run_subjects_methods("", "create_file_system", [], ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1.1: EXTRACT ZIP
        # ---------------------------------------------------------------------------------------------------------------------
        # for subj in subjects:
        #     kwparams.append({"src_zip":"/data/MRI/OT/dicom/past_bp/" + subj.label + ".zip",
        #                      "dest_dir":"/data/MRI/OT/dicom/past_bp/"+ subj.label,
        #                      "replace":True})
        # project.run_subjects_methods("", "unzip_data", kwparams, ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 2: CONVERT 2 NIFTI
        # ---------------------------------------------------------------------------------------------------------------------
        # associations    = []
        # associations.append({"contains": "FSPGR", "postfix":"-t1", "type": Subject.TYPE_T1})
        # associations.append({"contains": "TENSOR", "postfix":"-dti", "type": Subject.TYPE_DTI})
        # associations.append({"contains": "Resting_state", "postfix":"-rs", "type": Subject.TYPE_RS})
        #
        # for subj in subjects:
        #     kwparams.append({"extpath": "/data/MRI/OT/dicom/past_bp/" + subj.label,
        #                      "associations": associations, "cleanup": 0, "rename":True})
        # project.run_subjects_methods("", "renameNifti", kwparams, ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # RESLICING
        # ---------------------------------------------------------------------------------------------------------------------
        # subjects    = project.load_subjects(group_label, SESS_ID)
        # project.run_subjects_methods("", "reslice_image", [{"direction":"sag->axial"}], ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 3: CHECK IMAGES
        # ---------------------------------------------------------------------------------------------------------------------
        # project.run_subjects_methods("", "check_images", [{"t1":True, "rs":True, "dti":True, "t2":False, "fmri":None}], ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # PRINT HEADER
        # ---------------------------------------------------------------------------------------------------------------------
        # for s in subjects:
        #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
        #     print(s.label + "\t" + str(fslfun.read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))

        # ---------------------------------------------------------------------------------------------------------------------
        # 4: SET ORIGIN
        # ---------------------------------------------------------------------------------------------------------------------
        # project.prepare_mpr_for_setorigin1(group_label)

        # project.prepare_mpr_for_setorigin2(group_label)

        # ---------------------------------------------------------------------------------------------------------------------
        # 5: WELLCOME
        # ---------------------------------------------------------------------------------------------------------------------
        # def wellcome(self, do_overwrite=False,
        #              do_fslanat=True, odn="anat", imgtype=1, smooth=10,
        #              biascorr_type=SubjectMpr.BIAS_TYPE_STRONG,
        #              do_reorient=True, do_crop=True,
        #              do_bet=True, betfparam=None,
        #              do_sienax=False, bet_sienax_param_string="-SNB -f 0.2",
        #              do_reg=True, do_nonlinreg=True, do_seg=True,
        #              do_spm_seg=False, spm_seg_templ="", spm_seg_over_bet=False,
        #              do_cat_seg=False, cat_use_dartel=False, do_cat_surf=True, cat_smooth_surf=None,
        #              do_cat_seg_long=False, cat_long_sessions=None,
        #              do_cleanup=True, do_strongcleanup=False,
        #              use_lesionmask=False, lesionmask="lesionmask",
        #              do_freesurfer=False, do_complete_fs=False, fs_seg_over_bet=False,
        #              do_first=False, first_struct="", first_odn="",
        #
        #              do_rs=True, do_epirm2vol=0, do_susc_corr=False,
        #              do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="rs", feat_preproc_model="singlesubj_feat_preproc_noreg_melodic",
        #              do_featinitreg=False, do_melodic=True, mel_odn="postmel", mel_preproc_model="singlesubj_melodic_noreg", do_melinitreg=False, replace_std_filtfun=True,
        #
        #              do_fmri=True,
        #
        #              do_dtifit=True, do_pa_eddy=False, do_eddy_gpu=False, do_bedx=False, do_bedx_gpu=False, bedpost_odn="bedpostx",
        #              do_xtract=False, xtract_odn="xtract", xtract_refspace="native", xtract_gpu=False, xtract_meas="vol,prob,length,FA,MD,L1,L23",
        #              do_struct_conn=False, struct_conn_atlas_path="freesurfer", struct_conn_atlas_nroi=0):

        # project.run_subjects_methods("", "wellcome", [{"do_spm_seg":True,
        #                                                "do_cat_seg": True,
        #                                                "do_epirm2vol":146,
        #                                                "feat_preproc_model":"singlesubj_feat_preproc_noreg_melodic",
        #                                                "do_bedx":True, "do_xtract":True}], ncore=num_cpu)
        #

        # ==================================================================================================================
        # POST WELLCOME CORRECTION
        # ==================================================================================================================
        # project.run_subjects_methods("mpr", "finalize", [], ncore=num_cpu)
        # project.run_subjects_methods("transform", "transform_mpr", [{"overwrite":True, "usehead_nl":False}], ncore=num_cpu)
        # project.run_subjects_methods("transform", "transform_dti_t2", [{"ignore_t2":True, "overwrite":True}], ncore=num_cpu)
        # project.run_subjects_methods("transform", "transform_rs", [{"do_bbr":False, "overwrite":True}], ncore=num_cpu)

        # ==================================================================================================================
        # CHECK ALL REGISTRATION
        # ==================================================================================================================
        # subjects    = project.load_subjects(group_label, SESS_ID)

        # outdir      = os.path.join(project.group_analysis_dir, "registration_check_mpr_2_std")
        # project.check_all_coregistration(outdir, _from=["hr"], _to=["std"], num_cpu=num_cpu)

        # outdir      = os.path.join(project.group_analysis_dir, "registration_check_2_std")
        # project.check_all_coregistration(outdir, _from=["hr", "rs", "dti"], _to=["std"], num_cpu=num_cpu)

        # ==================================================================================================================
        # CHECK ANALYSIS
        # ==================================================================================================================
        # project.can_run_analysis("vbm_spm")
        # project.can_run_analysis("ct")
        # project.can_run_analysis("tbss")
        # project.can_run_analysis("bedpost")
        # project.can_run_analysis("xtract_single")
        # project.can_run_analysis("xtract_group")
        # project.can_run_analysis("melodic")
        # project.can_run_analysis("sbfc")
        #
        # ==================================================================================================================
        # BEDPOSTX GPU
        # ==================================================================================================================
        # subjects    = project.load_subjects(grp_bip_all, SESS_ID)
        # project.run_subjects_methods("dti", "ec_fit", [], ncore=1)
        # project.run_subjects_methods("dti", "bedpostx", [{"use_gpu":True}], ncore=1)

        # project.can_run_analysis("xtract_group")

        # subjects = project.load_subjects(grp_bip_all, SESS_ID)
        # project.run_subjects_methods("dti", "xtract", [{"use_gpu": True}], ncore=1)

        # ===========================================================================================
        # SINGLE SUBJECT PROCESSING
        # ===========================================================================================

        # subj = project.get_subject_by_label("Gentile_Patrizia_EU")

        # subj.mpr.spm_segment(do_overwrite=True, add_bet_mask=True, do_bet_overwrite=True)
        # subj.mpr.fs_reconall(step="-autorecon1", numcpu=10)
        # subj.transform.view_space_images("dti")
        # subj.transform.transform_dti_t2(overwrite=True)
        # subj.dti.xtract("xtract", "bedpostx_gpu", use_gpu=True)
        # subj.dti.xtract_check(os.path.join(subj.dti_dir, "xtract"))
        # subj.dti.xtract_viewer()
        # subj.dti.xtract_stats(meas="vol,prob,length,FA,MD,L23")

        subj = project.get_subject_by_label("T15_C_038")
        subj.rename("S038")

    except SubjectListException as e:
        print(e)

    except Exception as e:
        print(e)
        exit()


