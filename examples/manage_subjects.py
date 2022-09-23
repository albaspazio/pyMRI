from Global import Global
from Project import Project
from subject.Subject import Subject
from group.SPMStatsUtils import SPMStatsUtils

import os

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
        project = Project(proj_dir, globaldata)
        SESS_ID = 1
        num_cpu = 4
        group_label = "test"

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        kwparams = []

        subjects = project.load_subjects(group_label, SESS_ID, must_exist=False)
        # ---------------------------------------------------------------------------------------------------------------------
        # CREATE FILE SYSTEM
        # ---------------------------------------------------------------------------------------------------------------------
        # project.run_subjects_methods("", "create_file_system", [], group_or_subjlabels=group_label, ncore=num_cpu, must_exist=False)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1.1: EXTRACT ZIP
        # ---------------------------------------------------------------------------------------------------------------------
        # for p in range(len(subjects)):
        #     kwparams.append({"src_zip": "/data/MRI/OT/dicom/3t/roelof/" + subjects[p].label + ".zip",
        #                      "dest_dir":"/data/MRI/OT/dicom/3t/roelof/" + subjects[p].label,
        #                      "replace":False})
        # project.run_subjects_methods("", "unzip_data", kwparams, group_or_subjlabels=group_label, ncore=1, must_exist=False)

        # ---------------------------------------------------------------------------------------------------------------------
        # CONVERT 2 NIFTI
        # ---------------------------------------------------------------------------------------------------------------------
        # associations = []
        # associations.append({"contains": "mprage_sag_adni.nii.gz",          "postfix": "-t1",           "type": Subject.TYPE_T1})
        # associations.append({"contains": "task_bold_target",                "postfix": "-fmri_target",  "type": Subject.TYPE_FMRI})
        # associations.append({"contains": "task_bold_frame",                 "postfix": "-fmri_frame",   "type": Subject.TYPE_FMRI})
        # associations.append({"contains": "RS_bold_moco_2.5mm_TRUE_AXIAL",   "postfix": "-rs",           "type": Subject.TYPE_RS})
        # associations.append({"contains": "RS_bold_moco_2.5mm_PA_-180",      "postfix": "-rs_PA",        "type": Subject.TYPE_RS})
        # associations.append({"contains": "RS_bold_moco_2.5mm_-180_PA_new",  "postfix": "-rs_PA2",       "type": Subject.TYPE_RS})
        # associations.append({"contains": "ep2d_DTI_single_b_1000_AP.nii.gz","postfix": "-dti",          "type": Subject.TYPE_DTI})
        # associations.append({"contains": "ep2d_DTI_single_b_0_PA",          "postfix": "-dti_PA",       "type": Subject.TYPE_DTI_B0})
        #
        # kwparams = []
        # for p in range(len(subjects)):
        #     kwparams.append({"extpath": "/data/MRI/OT/dicom/3t/roelof/" + subjects[p].label, "associations": associations, "cleanup": 0, "convert":False, "rename":True})
        # project.run_subjects_methods("", "renameNifti", kwparams, group_or_subjlabels=group_label, ncore=num_cpu, must_exist=False)

        # ---------------------------------------------------------------------------------------------------------------------
        # PRINT HEADER
        # ---------------------------------------------------------------------------------------------------------------------
        # for s in subjects:
        #     # print(s.label + "\t" + str(fslfun.get_image_dimension(s.t1_data)))
        #     print(s.label + "\t" + str(read_header(s.t1_data, ["nx","ny","nz","dx","dy","dz","descrip"])))
        # subj = project.get_subject_by_label("021_td_Ogliastro_Matilde_topupnew")
        # read_header(subj.t1_data, ["nx", "ny", "nz", "dx", "dy", "dz", "descrip"])
        # ---------------------------------------------------------------------------------------------------------------------
        # 3: CHECK IMAGES
        # ---------------------------------------------------------------------------------------------------------------------
        # project.run_subjects_methods("", "check_images", [{"t1":True, "rs":True, "dti":True, "t2":False, "fmri":["-fmri_target", "-fmri_frame"]}], project.get_subjects_labels(), nthread=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        # 4: SET ORIGIN
        # ---------------------------------------------------------------------------------------------------------------------
        # project.prepare_mpr_for_setorigin1(group_label)
        # project.prepare_mpr_for_setorigin2(group_label)

        # ---------------------------------------------------------------------------------------------------------------------
        # 5: WELLCOME (subjects must now exist)
        # ---------------------------------------------------------------------------------------------------------------------
        subjects = project.load_subjects(group_label, SESS_ID)

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
        #              do_susc_corr=False,
        #
        #              do_rs=True, do_epirm2vol=0, rs_pa_data=None,
        #              do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="resting", feat_preproc_model="singlesubj_feat_preproc_noreg_melodic",
        #              do_featinitreg=False, do_melodic=True, mel_odn="postmel", mel_preproc_model="singlesubj_melodic_noreg", do_melinitreg=False, replace_std_filtfun=True,
        #
        #              do_fmri=True, fmri_params=None, fmri_images=None, fmri_pa_data=None,
        #
        #              do_dtifit=True, do_pa_eddy=False, do_eddy_gpu=False, do_bedx=False, do_bedx_gpu=False, bedpost_odn="bedpostx",
        #              do_xtract=False, xtract_odn="xtract", xtract_refspace="native", xtract_gpu=False, xtract_meas="vol,prob,length,FA,MD,L1,L23",
        #              do_struct_conn=False, struct_conn_atlas_path="freesurfer", struct_conn_atlas_nroi=0)

        kwparams = [{"do_spm_seg": False, "do_cat_seg": True, "do_epirm2vol": 590, "do_fmri": False, "feat_preproc_model": "singlesubj_feat_preproc_noreg_melodic_hp2000"}]

        # kwparams = [{ "do_anat":True, "do_epirm2vol":590, "do_dtifit":False, "do_overwrite":False,
        #               "feat_preproc_model":"singlesubj_feat_preproc_noreg_melodic_hp2000"}]

        project.run_subjects_methods("", "wellcome", kwparams, ncore=num_cpu)

        # project.run_subjects_methods("dti", "eddy", [{"exe_ver":"eddy_cuda9.1", "config":"b02b0_1.cnf", "json":os.path.join(project.script_dir, "dti_ap.json")}], project.get_subjects_labels(), nthread=1)
        # project.run_subjects_methods("dti", "fit", [], project.get_subjects_labels(), nthread=num_cpu)

        # SPMStatsUtils.batchrun_cat_surface_smooth(project, globaldata, subjects, nproc=15)

        # ==================================================================================================================
        # DTI EDDY
        # ==================================================================================================================
        # kwparams = [{"exe_ver":"eddy_cuda9.1", "config":"b02b0_1.cnf", "json":os.path.join(project.script_dir, "dti_ap.json")}]

        # project.run_subjects_methods("dti", "eddy", kwparams, project.get_subjects_labels(), nthread=1)

        # ==================================================================================================================
        # CHECK ALL REGISTRATION
        # ==================================================================================================================
        # outdir      = os.path.join(project.group_analysis_dir, "registration_check_2_std")
        # project.check_all_coregistration(outdir, project.get_subjects_labels(), _from=["rs", "fmri", "dti", "hr"], _to=["std"], num_cpu=num_cpu)

        # ===========================================================================================
        # RENAME SUBJECTS
        # ===========================================================================================
        # subjects    = project.load_subjects("ctrl", SESS_ID)
        # kwparams    = []
        # for s in subjects:
        #     kwparams.append({"new_label":"0" + s.label})
        # project.run_subjects_methods("", "rename", kwparams, ncore=1)

        # ===========================================================================================
        # topup correction
        # closest_vol = subj.epi.topup_correction(subj.rs_data, subj.rs_pa_data, project.topup_rs_params, ap_ref_vol=0)
        # subj.epi.coregister_epis(add_prefix2name(subj.rs_data, "r"), subj.rs_data_dist, img2transform=[subj.rs_data_dist], ref_vol=5)

        # kwparams = [{"inimg": "/data/MRI/projects/roelof/subjects/021_td_Ogliastro_Matilde_topupold/s1/resting/021_td_Ogliastro_Matilde_topupold-rs_distorted_ref"},
        #             {"inimg": "/data/MRI/projects/roelof/subjects/021_td_Ogliastro_Matilde_topupold/s1/resting/021_td_Ogliastro_Matilde_topupold-rs_distorted"},
        #             {"inimg": "/data/MRI/projects/roelof/subjects/021_td_Ogliastro_Matilde_topupold/s1/resting/021_td_Ogliastro_Matilde_topupold-rs_distorted_ref_lin"}]
        # project.run_subjects_methods("epi", "normalize", kwparams, ncore=3)

        # subj.dti.eddy(exe_ver="eddy_cuda9.1", config="b02b0_1.cnf", json=os.path.join(project.script_dir, "dti_ap.json"))
        # subj.transform.transform_mpr(overwrite=True)
        # subj.transform.transform_dti_t2(ignore_t2=True, overwrite=True)

        # subj.transform.transform_roi("dtiTOstd", pathtype="abs", islin=False, rois=[subj.dti_nodiff_data])
        # subj.transform.transform_roi("dtiTOhr", pathtype="abs", islin=False, rois=[subj.dti_nodiff_data])
        # subj.transform.transform_roi("hrTOstd", pathtype="abs", islin=False, rois=[subj.t1_data])

        # subj.mpr.fs_reconall(numcpu=18)
        # subj.dti.xtract("xtract", "bedpostx_gpu", use_gpu=True)
        # subj.dti.xtract_check(os.path.join(subj.dti_dir, "xtract"))
        # subj.dti.xtract_viewer()
        # subj.dti.xtract_stats(meas="vol,prob,length,FA,MD,L23")

        # kwparams = []
        # for p in range(len(subjects)):
        #     kwparams.append({"in_ap_img":subjects[p].rs_data, "in_pa_img":subjects[p].rs_pa_data, "acq_params": project.topup_rs_params, "ap_ref_vol":295})
        #     project.run_subjects_methods("epi", "topup_correction", kwparams, project.get_subjects_labels(), nthread=num_cpu)

        # ===========================================================================================
        # rename all ctrl subjects
        # ===========================================================================================
        # group_label = "test"
        # subjects = project.load_subjects(group_label, SESS_ID)
        #
        # for subj in subjects:
        #     subj.rename("0" + subj.label)
        # ===========================================================================================
        # rename all SK subjects
        # ===========================================================================================
        # group_label = "sk"
        # subjects = project.load_subjects(group_label, SESS_ID)
        #
        # for subj in subjects:
        #     new_lab = subj.label
        #     subj.rename("10" + subj.label[1:])

        # subj = Subject("0027_TD_Rosina_Anna", project)
        # subj.rename("0027_td_Rosina_Anna")
        # ==================================================================================================================
        # CHECK ANALYSIS
        # ==================================================================================================================
        # project.can_run_analysis("vbm_spm")
        # project.can_run_analysis("ct")
        # project.can_run_analysis("tbss")
        # project.can_run_analysis("bedpost")
        # project.can_run_analysis("xtract_single")
        # project.can_run_analysis("xtract_group")
        # project.can_run_analysis("melodic", group_or_subjlabels="all_rs")
        # project.can_run_analysis("sbfc")
    except Exception as e:
        print(e)
        exit()

