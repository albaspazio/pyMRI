import traceback

from Global import Global
from Project import Project
from group.spm_utilities import FmriProcParams
from subject.Subject import Subject
from group.SPMStatsUtils import SPMStatsUtils

import os

from utility.images.Image import Image

# NECESSARY STEPS TO IMPORT AND PREPROCESS A NEW SUBJECT
# 1) get data
#   - go to DICOM RESEARCH SERVER) :http://10.187.186.69:3333/
#   - fill in credentials:  osirixweb, risonanza
#   - search subject
#   - download the study
# 2) prepare data
#   - check in the antares.jointlab@google.com  "http://onedrive.live.com/.../JL/db/MRI_subjects_list.xlsx2 the first available progressive ID for the subjects within its diagnosis list
#       ID ranges from the following values according to subjects' diagnosis:
#       - td:   0001-0999
#       - sk:   1001-1999
#       - bd:   2001-2999
#       - bl:   3001-3999
#   - rename the zip as:   ID_diagnosis_surname_name
#   - move the zip to the dicom storage folder (e.g. "/data/MRI/OT/dicom/3t/mix")
#  3) run this script in the specified order
#
#
if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code            = "604"
    try:
        globaldata = Global(fsl_code)
        
        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        proj_dir        = "/data/MRI/projects/test"
        project         = Project(proj_dir, globaldata)
        SESS_ID         = 1
        num_cpu         = 1
        group_label     = "test"

        dicom_folder    = "/data/MRI/OT/dicom/3t/mix"
        # ======================================================================================================================
        # FMRI preprocessing parameters
        # ======================================================================================================================
        TR              = 0.72
        num_slices      = 72
        multiband_f     = 8
        time_bins       = num_slices/multiband_f     # 72/8 = 9
        slice_timing    = [0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465, 0.155, 0.5425, 0.2325, 0.6225, 0.31, 0, 0.3875, 0.0775, 0.465,
                           0.155, 0.5425, 0.2325, 0.6225]
        st_refslice     = 0.31

        fmri_params     = FmriProcParams(TR, num_slices, slice_timing, st_refslice, time_bins)

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        # subjects = project.load_subjects(group_label, SESS_ID, must_exist=False)
        # ---------------------------------------------------------------------------------------------------------------------
        # CREATE FILE SYSTEM
        # ---------------------------------------------------------------------------------------------------------------------
        # project.run_subjects_methods("", "create_file_system", [], group_or_subjlabels=group_label, ncore=num_cpu, must_exist=False)

        # ---------------------------------------------------------------------------------------------------------------------
        # 1.1: EXTRACT ZIP
        # ---------------------------------------------------------------------------------------------------------------------
        # kwparams = []
        # for p in range(len(subjects)):
        #     kwparams.append({"src_zip": os.path.join(dicom_folder, subjects[p].label + ".zip"),
        #                      "dest_dir":os.path.join(dicom_folder, subjects[p].label),
        #                      "replace":False})
        # project.run_subjects_methods("", "unzip_data", kwparams, group_or_subjlabels=group_label, ncore=1, must_exist=False)

        # ---------------------------------------------------------------------------------------------------------------------
        # CONVERT 2 NIFTI
        # ---------------------------------------------------------------------------------------------------------------------
        # associations = []
        # associations.append({"contains": "mprage_sag_adni.nii.gz",          "postfix": "-t1",           "type": Subject.TYPE_T1})
        # associations.append({"contains": "task_bold_target",                "postfix": "-fmri",         "type": Subject.TYPE_FMRI})
        # associations.append({"contains": "RS_bold_moco_2.5mm_TRUE_AXIAL",   "postfix": "-rs",           "type": Subject.TYPE_RS})
        # associations.append({"contains": "RS_bold_moco_2.5mm_PA_-180",      "postfix": "-rs_PA_old",    "type": Subject.TYPE_RS})
        # associations.append({"contains": "RS_bold_moco_2.5mm_-180_PA_new",  "postfix": "-rs_PA",        "type": Subject.TYPE_RS})
        # associations.append({"contains": "ep2d_DTI_single_b_1000_AP.nii.gz","postfix": "-dti",          "type": Subject.TYPE_DTI})
        # associations.append({"contains": "ep2d_DTI_single_b_0_PA",          "postfix": "-dti_PA",       "type": Subject.TYPE_DTI_B0})
        #
        # kwparams = []
        # for p in range(len(subjects)):
        #     kwparams.append({"extpath": os.path.join(dicom_folder, subjects[p].label), "associations": associations, "cleanup": 0, "convert":True, "rename":True})
        # project.run_subjects_methods("", "renameNifti", kwparams, group_or_subjlabels=group_label, ncore=1, must_exist=False)

        # ---------------------------------------------------------------------------------------------------------------------
        # load subjects list (at this point, subjects must exist, I remove must_exist=False, default is True)
        # ---------------------------------------------------------------------------------------------------------------------
        # subjects = project.load_subjects(group_label, SESS_ID)

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
        # project.run_subjects_methods("", "check_images", [{"t1":True, "rs":True, "dti":True, "t2":False, "fmri":["-fmri"]}], ncore=num_cpu)

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
        #              do_susc_corr=False,
        #
        #              do_rs=True, do_epirm2vol=0, rs_pa_data=None,
        #              do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="resting", feat_preproc_model="singlesubj_feat_preproc_noreg_melodic",
        #              do_featinitreg=False, do_melodic=True, mel_odn="postmel", mel_preproc_model="singlesubj_melodic_noreg", do_melinitreg=False, replace_std_filtfun=True,
        #
        #              do_fmri=True, fmri_params=None, fmri_labels=None, fmri_pa_data=None,
        #
        #              do_dtifit=True, do_pa_eddy=False, do_eddy_gpu=False, do_bedx=False, do_bedx_gpu=False, bedpost_odn="bedpostx",
        #              do_xtract=False, xtract_odn="xtract", xtract_refspace="native", xtract_gpu=False, xtract_meas="vol,prob,length,FA,MD,L1,L23",
        #              do_struct_conn=False, struct_conn_atlas_path="freesurfer", struct_conn_atlas_nroi=0)

        onlyfmrikwparams = [{ "do_fslanat":True,    "do_spm_seg":False,          "do_cat_seg":False,
                              "do_rs":False,        "do_epirm2vol":590,          "feat_preproc_model":"singlesubj_feat_preproc_noreg_melodic_hp2000",
                              "do_fmri":True,       "fmri_params":fmri_params,   "do_susc_corr":True,
                              "do_dtifit":False,    "do_pa_eddy":True,           "do_eddy_gpu":True,
                            }]

        allkwparams =      [{ "do_fslanat":True,    "do_spm_seg":False,          "do_cat_seg":False,
                              "do_rs":True,         "do_epirm2vol":590,          "feat_preproc_model":"singlesubj_feat_preproc_noreg_melodic_hp2000",
                              "do_fmri":True,       "fmri_params":fmri_params,   "do_susc_corr":True,
                              "do_dtifit":True,     "do_pa_eddy":True,           "do_eddy_gpu":True,
                            }]

        # kwparams = [{ "do_fslanat":True, "do_epirm2vol":590, "do_dtifit":False, "do_overwrite":False,
        #               "feat_preproc_model":"singlesubj_feat_preproc_noreg_melodic_hp2000"}]

        # project.run_subjects_methods("", "wellcome", kwparams, ncore=num_cpu)



        #==================================================================================================================
        # DTI EDDY
        #==================================================================================================================
        # kwparams = [{"exe_ver":"eddy_cuda9.1", "config":"b02b0_1.cnf", "json":os.path.join(project.script_dir, "dti_ap.json")}]
        # project.run_subjects_methods("dti", "eddy", kwparams, ncore=1)

        # project.run_subjects_methods("dti", "fit", [], ncore=num_cpu)

        #==================================================================================================================
        # CHECK ALL REGISTRATION
        #==================================================================================================================
        # outdir      = os.path.join(project.group_analysis_dir, "registration_check_fmri_2_std")
        # project.check_all_coregistration(outdir, project.get_subjects_labels(), _from=["rs", "fmri", "dti", "hr"], _to=["std"], num_cpu=num_cpu)
        # project.check_all_coregistration(outdir, project.get_subjects_labels(), _from=["fmri"], _to=["std"], num_cpu=num_cpu)

        # ===========================================================================================
        # TRANSFORM IMAGES
        # ===========================================================================================
        # def transform_roi(self, regtype, pathtype="standard", outdir="", outname="", mask="", orf="", thresh=0, islin=True, rois=None):
        # kwparams = []
        # for s in subjects:
        #     kwparams.append({"regtype":"fmriTOstd", "pathtype":"abs", "outdir":s.fmri_dir, "islin":False, "rois":[Image(s.fmri_data).add_prefix2name("a")]})
        # project.run_subjects_methods("transform", "transform_roi", kwparams, ncore=num_cpu)

        # ===========================================================================================
        # SINGLE SUBJECT PROCESSING
        # ===========================================================================================

        # subj = project.get_subject_by_label("021_td_Ogliastro_Matilde_topupold")
        # subj.rename("021_td_Ogliastro_Matilde")

        # subj = project.get_subject_by_label("X111022_Bode_JuxhinOnlyRivLong2ColImgOff", must_exist=False)
        # subj.rename("X111022_td_Bode_JuxhinOnlyRivLong2ColImgOff")

        # ===========================================================================================
        # topup correction
        # closest_vol = subj.epi.topup_correction(subj.rs_data, subj.rs_pa_data, project.topup_rs_params, ap_ref_vol=0)
        # subj.epi.coregister_epis(subj.rs_data.add_prefix2name("r"), subj.rs_data_dist, img2transform=[subj.rs_data_dist], ref_vol=5)
        #
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

        # SPMStatsUtils.batchrun_cat_surface_smooth(project, globaldata, subjects, nproc=15)


        # region RENAME

        # ===========================================================================================
        # rename all ctrl subjects
        # ===========================================================================================
        # group_label = "test"
        # subjects = project.load_subjects(group_label, SESS_ID)
        #
        # for subj in subjects:
        #     subj.rename("0" + subj.label)

        # subjects    = project.load_subjects("ctrl", SESS_ID)
        # kwparams    = []
        # for s in subjects:
        #     kwparams.append({"new_label":"0" + s.label})
        # project.run_subjects_methods("", "rename", kwparams, ncore=1)

        # ===========================================================================================
        # rename all SK subjects
        # ===========================================================================================
        # group_label = "sk"
        # subjects = project.load_subjects(group_label, SESS_ID)
        #
        # for subj in subjects:
        #     subj.rename("1" + subj.label)

        # ===========================================================================================
        # rename according to 2 lists
        # ===========================================================================================
        # a = ["0029_TD_Ferrari_Allegra", "0030_TD_Campodonico_Alessandra", "0031_TD_Bovio_Anna", "0032_TD_Russo_Antonio", "0033_TD_Proietti_Luca", "1023_SK_Milanti_Leonardo", "1024_SK_Esposito_Natashia", "1025_SK_Tergolina_Camilla", "1026_SK_Bebeci_Iridjon", "1027_SK_Firenze_Stefano", "2008_BD_Minasi_Riccardo", "2009_BD_Pitone_Giuseppe", "2010_BD_DeLongis_Simona", "2011_BD_Bruni_Manuela", "2012_BD_Pepe_Michele", "2013_BD_Orecchia_MariaLuisa"]
        # b = ["0029_td_Ferrari_Allegra", "0030_td_Campodonico_Alessandra", "0031_td_Bovio_Anna", "0032_td_Russo_Antonio", "0033_td_Proietti_Luca", "1023_sk_Milanti_Leonardo", "1024_sk_Esposito_Natashia", "1025_sk_Tergolina_Camilla", "1026_sk_Bebeci_Iridjon", "1027_sk_Firenze_Stefano", "2008_bd_Minasi_Riccardo", "2009_bd_Pitone_Giuseppe", "2010_bd_DeLongis_Simona", "2011_bd_Bruni_Manuela", "2012_bd_Pepe_Michele", "2013_bd_Orecchia_MariaLuisa"]
        # subjects = project.load_subjects(a, SESS_ID)
        #
        # for id, subj in enumerate(subjects):
        #     subj.rename(b[id])
        #
        # subj = Subject("0046_td_Sara_Albertinetti", project)
        # subj.rename("0046_td_Albertinetti_Sara")

        # endregion

        # ==================================================================================================================
        # CHECK ANALYSIS
        # ==================================================================================================================
        # project.can_run_analysis("vbm_spm")
        # project.can_run_analysis("fmri")
        # project.can_run_analysis("ct")
        # project.can_run_analysis("tbss")
        # project.can_run_analysis("bedpost")
        # project.can_run_analysis("xtract_single")
        # project.can_run_analysis("xtract_group")
        # project.can_run_analysis("melodic", group_or_subjlabels="all_rs")
        # project.can_run_analysis("sbfc")

    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()
