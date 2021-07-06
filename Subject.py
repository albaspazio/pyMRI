import traceback
import glob
import os

from copy import deepcopy
from shutil import move

from SubjectDti import SubjectDti
from SubjectEpi import SubjectEpi
from SubjectMpr import SubjectMpr
from SubjectTransforms import SubjectTransforms
from utility.fslfun import runsystem
from utility.images import imtest, immv, imcp, is_image, img_split_ext
from myfsl.utils.run import rrun


class Subject:

    TYPE_T1 = 1
    TYPE_RS = 2
    TYPE_FMRI = 3
    TYPE_DTI = 4
    TYPE_T2 = 5

    def __init__(self, label, sessid, project):

        self.label = label
        self.sessid = sessid

        self.project = project
        self._global = project._global

        self.fsl_dir = self._global.fsl_dir
        self.fsl_bin = self._global.fsl_bin
        self.fsl_data_std_dir = self._global.fsl_data_std_dir

        self.project_subjects_dir = project.subjects_dir

        self.set_file_system(self.sessid)

        self.transform  = SubjectTransforms(self, self._global)
        self.mpr        = SubjectMpr(self, self._global)
        self.dti        = SubjectDti(self, self._global)
        self.epi        = SubjectEpi(self, self._global)

    def get_sess_file_system(self, sess):
        return self.set_file_system(sess, True)

    # this method has 2 usages:
    # 1) DEFAULT : to create filesystem names at startup    => returns : self  (DOUBT !! alternatively may always return a deepcopy)
    # 2) to get a copy with names of another session        => returns : deepcopy(self)
    def set_file_system(self, sess, rollback=False):

        self.dir = os.path.join(self.project.subjects_dir, self.label, "s" + str(sess))

        self.roi_dir        = os.path.join(self.dir, "roi")
        self.roi_rs_dir     = os.path.join(self.roi_dir, "reg_rs")
        self.roi_fmri_dir   = os.path.join(self.roi_dir, "reg_fmri")
        self.roi_dti_dir    = os.path.join(self.roi_dir, "reg_dti")
        self.roi_t2_dir     = os.path.join(self.roi_dir, "reg_t2")
        self.roi_std_dir    = os.path.join(self.roi_dir, "reg_std")
        self.roi_std4_dir   = os.path.join(self.roi_dir, "reg_std4")
        self.roi_t1_dir     = os.path.join(self.roi_dir, "reg_t1")

        # ------------------------------------------------------------------------------------------------------------------------
        # T1/MPR
        # ------------------------------------------------------------------------------------------------------------------------
        self.t1_dir         = os.path.join(self.dir, "mpr")
        self.t1_anat_dir    = os.path.join(self.t1_dir, "anat")
        self.fast_dir       = os.path.join(self.t1_dir, "fast")
        self.first_dir      = os.path.join(self.t1_dir, "first")
        self.sienax_dir     = os.path.join(self.t1_dir, "sienax")
        self.t1_fs_dir      = os.path.join(self.t1_dir, "freesurfer")
        self.t1_fs_mri_dir  = os.path.join(self.t1_fs_dir, "mri")
        self.t1_spm_dir     = os.path.join(self.t1_anat_dir, "spm_proc")
        self.t1_cat_dir     = os.path.join(self.t1_anat_dir, "cat_proc")

        self.t1_image_label         = self.label + "-t1"
        self.t1_data                = os.path.join(self.t1_dir, self.t1_image_label)
        self.t1_brain_data          = os.path.join(self.t1_dir, self.t1_image_label + "_brain")
        self.t1_brain_data_mask     = os.path.join(self.t1_dir, self.t1_image_label + "_brain_mask")
        self.t1_fs_brainmask_data   = os.path.join(self.t1_fs_dir, "mri", "brainmask")
        self.t1_fs_data             = os.path.join(self.t1_fs_dir, "mri", "T1")  # T1 coronal [1x1x1] after conform

        self.first_all_none_origsegs = os.path.join(self.first_dir, self.t1_image_label + "_all_none_origsegs")
        self.first_all_fast_origsegs = os.path.join(self.first_dir, self.t1_image_label + "_all_fast_origsegs")

        self.t1_segment_gm_path         = os.path.join(self.roi_t1_dir, "mask_t1_gm")
        self.t1_segment_wm_path         = os.path.join(self.roi_t1_dir, "mask_t1_wm")
        self.t1_segment_csf_path        = os.path.join(self.roi_t1_dir, "mask_t1_csf")
        self.t1_segment_wm_bbr_path     = os.path.join(self.roi_t1_dir, "wmseg4bbr")
        self.t1_segment_wm_ero_path     = os.path.join(self.roi_t1_dir, "mask_t1_wmseg4Nuisance")
        self.t1_segment_csf_ero_path    = os.path.join(self.roi_t1_dir, "mask_t1_csfseg4Nuisance")

        self.t1_cat_surface_dir                     = os.path.join(self.t1_cat_dir, "surf")
        self.t1_cat_resampled_surface               = os.path.join(self.t1_cat_surface_dir, "s15.mesh.thickness.resampled_32k.T1_" + self.label + ".gii")
        self.t1_cat_resampled_surface_longitudinal  = os.path.join(self.t1_cat_surface_dir, "s15.mesh.thickness.resampled_32k.rT1_" + self.label + ".gii")

        self.hr2std_warp  = os.path.join(self.roi_std_dir, "hr2std_warp")
        self.std2hr_warp  = os.path.join(self.roi_t1_dir, "std2hr_warp")

        self.hr2std_mat  = os.path.join(self.roi_std_dir, "hr2std.mat")
        self.std2hr_mat  = os.path.join(self.roi_t1_dir, "std2hr.mat")


        # ------------------------------------------------------------------------------------------------------------------------
        # DTI
        # ------------------------------------------------------------------------------------------------------------------------
        self.dti_dir            = os.path.join(self.dir, "dti")
        self.bedpost_X_dir      = os.path.join(self.dti_dir, "bedpostx")
        self.probtrackx_dir     = os.path.join(self.dti_dir, "probtrackx")
        self.trackvis_dir       = os.path.join(self.dti_dir, "trackvis")
        self.tv_matrices_dir    = os.path.join(self.dti_dir, "tv_matrices")

        self.dti_image_label    = self.label + "-dti"
        self.dti_ec_image_label = self.dti_image_label + "_ec"
        self.dti_fit_label      = self.dti_image_label + "_fit"

        self.dti_bval_label         = os.path.join(self.dti_dir, self.label + "-dti.bval")
        self.dti_bvec_label         = os.path.join(self.dti_dir, self.label + "-dti.bvec")
        self.dti_rotated_bvec_label = os.path.join(self.dti_dir, self.label + "-dti_rotated.bvec")

        self.dti_data       = os.path.join(self.dti_dir, self.dti_image_label)
        self.dti_ec_data    = os.path.join(self.dti_dir, self.dti_ec_image_label)
        self.dti_fit_data   = os.path.join(self.dti_dir, self.dti_fit_label)

        self.dti_nodiff_data            = os.path.join(self.dti_dir, "nodif")
        self.dti_nodiff_brain_data      = os.path.join(self.dti_dir, "nodif_brain")
        self.dti_nodiff_brainmask_data  = os.path.join(self.dti_dir, "nodif_brain_mask")

        self.trackvis_transposed_bvecs = "bvec_vert.txt"

        # ------------------------------------------------------------------------------------------------------------------------
        # RS
        # ------------------------------------------------------------------------------------------------------------------------
        self.rs_image_label = self.label + "-rs"
        self.rs_dir         = os.path.join(self.dir, "resting")
        self.rs_data        = os.path.join(self.rs_dir, self.rs_image_label)
        self.sbfc_dir       = os.path.join(self.rs_dir, "sbfc")
        self.rs_series_dir  = os.path.join(self.sbfc_dir, "series")
        self.rs_examplefunc = os.path.join(self.roi_rs_dir, "example_func")

        self.rs_series_csf  = os.path.join(self.rs_series_dir, "csf_ts")
        self.rs_series_wm   = os.path.join(self.rs_series_dir, "wm_ts")

        self.rs_final_regstd_dir    = os.path.join(self.rs_dir, "reg_std")

        self.rs_final_regstd_image  = os.path.join(self.rs_final_regstd_dir, "filtered_func_data")  # image after first preprocessing, aroma and nuisance regression.
        self.rs_final_regstd_mask   = os.path.join(self.rs_final_regstd_dir, "mask")  # image after first preprocessing, aroma and nuisance regression.
        self.rs_final_regstd_bgimage= os.path.join(self.rs_final_regstd_dir, "bg_image")  # image after first preprocessing, aroma and nuisance regression.

        self.rs_post_preprocess_image_label             = self.rs_image_label + "_preproc"
        self.rs_post_aroma_image_label                  = self.rs_image_label + "_preproc_aroma"
        self.rs_post_nuisance_image_label               = self.rs_image_label + "_preproc_aroma_nuisance"
        self.rs_post_nuisance_melodic_image_label       = self.rs_image_label + "_preproc_aroma_nuisance_melodic"
        self.rs_post_nuisance_std4_image_label          = self.rs_image_label + "_preproc_aroma_nuisance_std4"
        self.rs_post_nuisance_melodic_std4_image_label  = self.rs_image_label + "_preproc_aroma_nuisance_melodic_std4"

        self.rs_regstd_dir              = os.path.join(self.rs_dir, "resting.ica", "reg_std")
        self.rs_regstd_image            = os.path.join(self.rs_regstd_dir, "filtered_func_data")
        self.rs_regstd_denoise_dir      = os.path.join(self.rs_dir, "resting.ica", "reg_std_denoised")
        self.rs_regstd_denoise_image    = os.path.join(self.rs_regstd_denoise_dir, "filtered_func_data")

        self.rs_aroma_dir           = os.path.join(self.rs_dir, "ica_aroma")
        self.rs_aroma_image         = os.path.join(self.rs_aroma_dir, "denoised_func_data_nonaggr")
        self.rs_regstd_aroma_dir    = os.path.join(self.rs_aroma_dir, "reg_standard")
        self.rs_regstd_aroma_image  = os.path.join(self.rs_regstd_aroma_dir, "filtered_func_data")

        self.rs_mask_t1_wmseg4nuis_epi  = os.path.join(self.roi_dir, "reg_rs", "mask_t1_wmseg4Nuisance_epi")
        self.rs_mask_t1_csfseg4nuis_epi = os.path.join(self.roi_dir, "reg_rs", "mask_t1_csfseg4Nuisance_epi")

        self.mc_params_dir  = os.path.join(self.rs_dir, self.rs_image_label + ".ica", "mc")
        self.mc_abs_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_abs_mean.rms")
        self.mc_rel_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_rel_mean.rms")

        self.rs2std_warp    = os.path.join(self.roi_std_dir, "rs2std_warp")
        self.std2rs_warp    = os.path.join(self.roi_rs_dir, "std2rs_warp")

        self.rs2std_mat     = os.path.join(self.roi_std_dir, "rs2std.mat")
        self.std2rs_mat     = os.path.join(self.roi_rs_dir, "std2rs.mat")

        self.rs2hr_mat       = os.path.join(self.roi_t1_dir, "rs2hr.mat")
        self.hr2rs_mat       = os.path.join(self.roi_rs_dir, "hr2rs.mat")


        # ------------------------------------------------------------------------------------------------------------------------
        # fMRI
        # ------------------------------------------------------------------------------------------------------------------------
        self.fmri_image_label   = self.label + "-fmri"
        self.fmri_dir           = os.path.join(self.dir, "fmri")
        self.fmri_data          = os.path.join(self.fmri_dir, self.fmri_image_label)
        self.fmri_data_mc       = os.path.join(self.fmri_dir, "r" + self.fmri_image_label)
        self.fmri_examplefunc   = os.path.join(self.fmri_dir, "example_func")

        self.fmri_pe_data       = os.path.join(self.fmri_dir, self.fmri_image_label + "_pe")
        self.fmri_acq_params    = os.path.join(self.fmri_dir, "acqparams.txt")

        self.fmri_aroma_dir         = os.path.join(self.fmri_dir, "ica_aroma")
        self.fmri_aroma_image       = os.path.join(self.fmri_aroma_dir, "denoised_func_data_nonaggr")
        self.fmri_regstd_aroma_dir  = os.path.join(self.fmri_aroma_dir, "reg_standard")
        self.fmri_regstd_aroma_image= os.path.join(self.fmri_regstd_aroma_dir, "filtered_func_data")

        self.fmri2std_warp     = os.path.join(self.roi_std_dir, "fmri2std_warp")
        self.std2fmri_warp     = os.path.join(self.roi_fmri_dir, "std2fmri_warp")

        self.fmri2hr_mat       = os.path.join(self.roi_t1_dir, "fmri2hr.mat")
        self.hr2fmri_mat       = os.path.join(self.roi_fmri_dir, "hr2fmri.mat")

        # ------------------------------------------------------------------------------------------------------------------------
        # OTHER (DE/T2/WB/PE)
        # ------------------------------------------------------------------------------------------------------------------------
        self.de_dir         = os.path.join(self.dir, "t2")
        self.de_image_label = "de"
        self.de_data        = os.path.join(self.de_dir, self.de_image_label)
        self.de_brain_data  = os.path.join(self.de_dir, self.de_image_label + "_brain")

        self.has_T2 = False
        self.t2_dir         = self.de_dir
        self.t2_image_label = "t2"
        self.t2_data        = os.path.join(self.t2_dir, self.t2_image_label)
        self.t2_brain_data  = os.path.join(self.t2_dir, self.t2_image_label + "_brain")

        self.wb_dir         = os.path.join(self.dir, "wb")
        self.wb_image_label = self.label + "-wb_epi"
        self.wb_data        = os.path.join(self.wb_dir, self.wb_image_label)
        self.wb_brain_data  = os.path.join(self.wb_dir, self.wb_image_label + "_brain")

        self.DCM2NII_IMAGE_FORMATS = [".nii", ".nii.gz", ".hdr", ".hdr.gz", ".img", ".img.gz"]

        self_copy = deepcopy(self)
        if rollback is True:
            self.set_file_system(self.sessid, False)
            return self_copy
        else:
            self.sessid = sess
            return self

    # ==================================================================================================
    # GENERAL
    # ==================================================================================================
    def create_file_system(self):

        os.makedirs(os.path.join(self.dir, "mpr"), exist_ok=True)
        os.makedirs(os.path.join(self.dir, "fmri"), exist_ok=True)
        os.makedirs(os.path.join(self.dir, "dti"), exist_ok=True)
        os.makedirs(os.path.join(self.dir, "t2"), exist_ok=True)
        os.makedirs(os.path.join(self.dir, "resting"), exist_ok=True)

        os.makedirs(self.roi_t1_dir, exist_ok=True)
        os.makedirs(self.roi_std_dir, exist_ok=True)
        os.makedirs(self.roi_dti_dir, exist_ok=True)
        os.makedirs(self.roi_rs_dir, exist_ok=True)
        os.makedirs(self.roi_fmri_dir, exist_ok=True)
        os.makedirs(self.roi_t2_dir, exist_ok=True)

    def check_images(self, t1=False, rs=False, dti=False, t2=False, fmri=False):

        missing_images = []

        if t1 is True:
            if not imtest(self.t1_data):
                missing_images.append("t1")

        if rs is True:
            if not imtest(self.rs_data):
                missing_images.append("rs")

        if fmri is True:
            if not imtest(self.fmri_data):
                missing_images.append("fmri")

        if dti is True:
            if not imtest(self.dti_data):
                missing_images.append("dti")

        if t2 is True:
            if not imtest(self.t2_data):
                missing_images.append("t2")

        print(missing_images)

        return missing_images

    def reslice_image(self, direction):

        if direction == "sag->axial":
            bckfilename = self.t1_image_label + "_sag"
            conversion_str = " -z -x y "
        else:
            print("invalid conversion")
            return

        bckfilepath = os.path.join(self.t1_dir, bckfilename)
        if imtest(bckfilepath):
            return

        imcp(self.t1_data, bckfilepath)  # create backup copy
        rrun("fslswapdim " + self.t1_data + conversion_str + self.t1_data)  # run reslicing

    # ==================================================================================================================================================
    # WELCOME
    # ==================================================================================================================================================

    def wellcome(self, do_anat=True, odn="anat", imgtype=1, smooth=10,
                 biascorr_type=SubjectMpr.BIAS_TYPE_STRONG,
                 do_reorient=True, do_crop=True,
                 do_bet=True, betfparam=[0.5],
                 do_sienax=False, bet_sienax_param_string="-SNB -f 0.2",
                 do_reg=True, do_nonlinreg=True,
                 do_seg=True, do_spm_seg=True, spm_seg_over_bet=False, spm_seg_over_fs=False,  # over-ride bet an
                 do_cleanup=True, do_strongcleanup=False, do_overwrite=False,
                 use_lesionmask=False, lesionmask="lesionmask",
                 do_freesurfer=False,
                 do_first=False, first_struct="", first_odn="",
                 do_epirm2vol=0, do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="resting",
                 feat_preproc_model="singlesubj_feat_preproc", do_featinitreg=False,
                 do_melodic=True, mel_odn="resting", mel_preproc_model="singlesubj_melodic", do_melinitreg=False, replace_std_filtfun=True,
                 do_dtifit=True, do_bedx=True, do_bedx_cuda=False, bedpost_odn="bedpostx",
                 do_autoptx_tract=False,
                 do_struct_conn=False, struct_conn_atlas_path="freesurfer", struct_conn_atlas_nroi=0,
                 std_image=""):

        self.has_T2         = 0
        BET_F_VALUE_T2      = "0.5"
        feat_preproc_model  = os.path.join(self.project.script_dir, "glm", "templates", feat_preproc_model)
        melodic_model       = os.path.join(self.project.script_dir, "glm", "templates", mel_preproc_model)

        # ==============================================================================================================================================================
        #  T1 data
        # ==============================================================================================================================================================
        if os.path.exists(self.t1_dir):

            os.makedirs(self.roi_t1_dir, exist_ok=True)
            os.makedirs(self.roi_std_dir, exist_ok=True)
            os.makedirs(self.fast_dir, exist_ok=True)

            if do_anat is True:
                self.mpr.prebet(
                    odn=odn, imgtype=imgtype, smooth=smooth,
                    biascorr_type=biascorr_type,
                    do_reorient=do_reorient, do_crop=do_crop,
                    do_bet=do_bet, do_overwrite=do_overwrite,
                    use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                self.mpr.bet(
                    odn=odn, imgtype=imgtype,
                    do_bet=do_bet, betfparam=betfparam,
                    do_reg=do_reg, do_nonlinreg=do_nonlinreg,
                    do_overwrite=do_overwrite,
                    use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                if do_spm_seg is True:
                    self.mpr.spm_segment(
                        odn=odn,
                        do_bet_overwrite=spm_seg_over_bet,
                        do_overwrite=do_overwrite,
                        spm_template_name="spm_segment_dartelimport_template")

                self.mpr.postbet(
                    odn=odn, imgtype=imgtype, smooth=smooth,
                    betfparam=betfparam,
                    do_reg=do_reg, do_nonlinreg=do_nonlinreg,
                    do_seg=do_seg,
                    do_cleanup=do_cleanup, do_strongcleanup=do_strongcleanup, do_overwrite=do_overwrite,
                    use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                self.mpr.finalize(odn=odn)

            if do_sienax is True:
                print(self.label + " : sienax with " + bet_sienax_param_string)
                rrun("sienax " + self.t1_data + " -B " + bet_sienax_param_string + " -r")

            self.transform.transform_mpr()
            if do_first is True:
                if imtest(self.first_all_fast_origsegs) is False and imtest(self.first_all_none_origsegs) is False:
                    self.mpr.first(first_struct, odn=first_odn)

            if do_freesurfer is True:
                self.mpr.fs_reconall()

        # ==============================================================================================================================================================
        # WB data
        # ==============================================================================================================================================================
        if os.path.exists(self.wb_dir):
            if imtest(self.wb_data) is True:
                if imtest(self.wb_brain_data) is False:
                    print(self.label + " : bet on WB")
                    rrun("bet " + self.wb_data + " " + self.wb_brain_data + " -f " + BET_F_VALUE_T2 + " -g 0 -m")

        # ==============================================================================================================================================================
        # RS data
        # ==============================================================================================================================================================
        # preprocessing step considered valid (filtered_func_data, bg_image and mask)
        # is stored in resting/reg_standard with a resolution of 4mm to be used for melodic group analysis
        if os.path.exists(self.rs_dir):
            os.makedirs(self.roi_rs_dir, exist_ok=True)

            if imtest(self.rs_data) is False:
                print("rs image (" + self.rs_data + ") is missing...continuing")
            else:
                log_file = os.path.join(self.rs_dir, "log_rs_processing.txt")
                log = open(log_file, "a")

                os.makedirs(os.path.join(self.project.group_analysis_dir, "resting", "dr"), exist_ok=True)
                os.makedirs(os.path.join(self.project.group_analysis_dir, "resting", "group_templates"), exist_ok=True)
                os.makedirs(self.rs_final_regstd_dir, exist_ok=True)

                if do_epirm2vol > 0:
                    # check if I have to remove the first (TOT_VOL-DO_RMVOL_TO_NUM) volumes
                    tot_vol_num = int(rrun("fslnvols " + self.rs_data, logFile=log).split('\n')[0])

                    vol2remove = tot_vol_num - do_epirm2vol

                    if vol2remove > 0:
                        try:
                            immv(self.rs_data, self.rs_data + "_fullvol", logFile=log)
                            rrun("fslroi " + self.rs_data + "_fullvol " + self.rs_data + " " + str(vol2remove) + " -1", logFile=log)
                        except Exception as e:
                            print("UNRECOVERABLE ERROR: " + e)
                            immv(self.rs_data + "_fullvol", self.rs_data, logFile=log)
                            return

                # FEAT PRE PROCESSING
                preproc_img     = os.path.join(self.rs_dir, self.rs_post_preprocess_image_label)        # output image of first preproc resting.featfeat
                filtfuncdata    = os.path.join(self.rs_dir, feat_preproc_odn + ".feat", "filtered_func_data")
                preproc_feat_dir= os.path.join(self.rs_dir, feat_preproc_odn + ".feat")     # /s1/resting/resting.feat
                if imtest(preproc_img) is False:
                    if os.path.isfile(feat_preproc_model + ".fsf") is False:
                        print("===========>>>> FEAT_PREPROC template file (" + self.label + " " + feat_preproc_model + ".fsf) is missing...skipping feat preprocessing")
                    else:
                        if os.path.isdir(preproc_feat_dir) is False:
                            self.epi.fsl_feat("rs", self.rs_image_label, "resting.feat", feat_preproc_model, do_initreg=do_featinitreg, std_image=std_image)

                            # if func_data were coregistered, then calculate reg_standard and copy files to roi/reg_rs-fmri folder
                            out_dir = os.path.join(self.rs_dir, "resting.feat")
                            if os.path.exists(os.path.join(out_dir, "reg")) is True:
                                rrun(os.path.join(self._global.fsl_bin, "featregapply") + " " + out_dir)
                                self.subject.epi.reg_copy_feat("rs", std_image)

                            imcp(filtfuncdata, preproc_img, logFile=log)
                        else:
                            if imtest(filtfuncdata) is True:
                                imcp(filtfuncdata, preproc_img, logFile=log)
                            else:
                                print("ERROR in wellcome of subject " + self.label + ". resting preprocessing...preproc feat corrupted")
                                return

                # do AROMA processing
                preproc_aroma_img = os.path.join(self.rs_dir, self.rs_post_aroma_image_label)    # output image of aroma processing
                try:
                    if do_aroma is True:
                        if imtest(preproc_aroma_img) is False:
                            self.epi.aroma("rs", preproc_feat_dir)  # do not register to standard
                            imcp(self.rs_aroma_image, os.path.join(self.rs_dir, self.rs_post_aroma_image_label))
                    else:
                        imcp(preproc_img, os.path.join(self.rs_dir, self.rs_post_aroma_image_label))

                except Exception as e:
                    print("UNRECOVERABLE ERROR: " + str(e))
                    return

                # do nuisance removal (WM, CSF & highpass temporal filtering)....create the following file: $RS_IMAGE_LABEL"_preproc_aroma_nuisance"
                if do_nuisance is True and imtest(self.rs_final_regstd_image) is False:

                    exfun   = os.path.join(self.rs_dir, self.rs_post_nuisance_image_label)
                    mask    = os.path.join(self.rs_dir, feat_preproc_odn + ".feat", "reg_standard", "mask")

                    exfun4  = os.path.join(self.roi_std4_dir, self.rs_post_nuisance_std4_image_label)
                    mask4   = os.path.join(self.roi_std4_dir, "mask_std4")

                    self.epi.remove_nuisance(self.rs_post_aroma_image_label, hpfsec=hpfsec)
                    self.transform.transform_roi("epi2std4", "abs", thresh=0, rois=[exfun, mask])   # add _std4 to roi name

                    immv(exfun4, self.rs_final_regstd_image, logFile=log)
                    imcp(mask4,  self.rs_final_regstd_mask,  logFile=log)

                # NOW reg_standard contains a denoised file with its mask and background image. nevertheless, we also do a resting to check the output,
                # doing another MC and HPF results seems to improve...although they should not...something that should be investigated....

                # MELODIC
                mel_out_dir     = os.path.join(self.rs_dir, mel_odn + ".ica")

                exfun           = os.path.join(self.rs_dir, self.rs_post_nuisance_melodic_image_label)
                mask            = os.path.join(self.rs_dir, mel_odn + ".ica", "reg_standard", "mask")
                bg_image        = os.path.join(self.rs_dir, mel_odn + ".ica", "reg_standard", "bg_image")

                exfun4          = os.path.join(self.roi_std4_dir, self.rs_post_nuisance_melodic_std4_image_label)
                mask4           = os.path.join(self.roi_std4_dir, "mask_std4")
                bg_image4       = os.path.join(self.roi_std4_dir, "bg_image_std4")

                if os.path.isdir(mel_out_dir) is False and do_melodic is True:
                    if os.path.isfile(melodic_model + ".fsf") is False:
                        print("===========>>>> resting template file (" + self.label + " " + melodic_model + ".fsf) is missing...skipping 1st level resting")
                    else:
                        self.epi.fsl_feat("rs",  self.rs_post_nuisance_image_label, mel_odn + ".ica", melodic_model, do_initreg=do_melinitreg, std_image=std_image)  # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_feat.sh $SUBJ_NAME $PROJ_DIR -model $MELODIC_MODEL -odn $MELODIC_OUTPUT_DIR.ica -std_img $STANDARD_IMAGE -initreg $DO_FEAT_PREPROC_INIT_REG -ifn $RS_POST_NUISANCE_IMAGE_LABEL

                        # if func_data were coregistered, then calculate reg_standard and copy files to roi/reg_rs-fmri folder
                        out_dir = os.path.join(self.rs_dir, mel_odn + ".ica")
                        if os.path.exists(os.path.join(out_dir, "reg")) is True:
                            rrun(os.path.join(self._global.fsl_bin, "featregapply") + " " + out_dir)
                            self.epi.reg_copy_feat("rs", std_image)

                        if imtest(os.path.join(mel_out_dir, "reg_standard", "filtered_func_data")) is True :
                            imcp(os.path.join(mel_out_dir, "reg_standard", "filtered_func_data"), exfun, logFile=log)
                            self.transform.transform_roi("epi2std4", "abs", thresh=0, rois=[bg_image])  # add _std4 to roi name
                            imcp(bg_image4, self.rs_final_regstd_bgimage)

                        if replace_std_filtfun is True:
                            self.transform.transform_roi("epi2std4", "abs", thresh=0, rois=[exfun, mask])  # add _std4 to roi name

                            imcp(mask4, self.rs_final_regstd_mask)
                            immv(exfun4, self.rs_final_regstd_image)


                # calculate the remaining transformations   .....3/4/2017 si blocca qui...devo commentarlo per andare avanti !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                self.transform.transform_epi("rs")  # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_transforms_calculate_epi.sh $SUBJ_NAME $PROJ_DIR

                # coregister fast-highres to epi
                if imtest(os.path.join(self.roi_rs_dir, "t1_wm_rs")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, "mask_t1_wm") + " -ref " + os.path.join(self.roi_rs_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.roi_rs_dir, "t1_wm_rs"))

                if imtest(os.path.join(self.roi_rs_dir, "t1_csf_rs")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, "mask_t1_csf") + " -ref " + os.path.join(self.roi_rs_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.roi_rs_dir, "t1_csf_rs"))

                if imtest(os.path.join(self.roi_rs_dir, "t1_gm_rs")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, "mask_t1_gm") + " -ref " + os.path.join(self.roi_rs_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.roi_rs_dir, "t1_gm_rs"))

                if imtest(os.path.join(self.roi_rs_dir, "t1_brain_rs")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, self.t1_brain_data) + " -ref " + os.path.join(self.roi_rs_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.roi_rs_dir, "t1_brain_rs"))

                # mask & binarize
                rrun("fslmaths " + os.path.join(self.roi_rs_dir, "t1_gm_rs.nii.gz") + " -thr 0.2 -bin " + os.path.join(self.roi_rs_dir, "mask_t1_gm_rs.nii.gz"), logFile=log)
                rrun("fslmaths " + os.path.join(self.roi_rs_dir, "t1_wm_rs.nii.gz") + " -thr 0.2 -bin " + os.path.join(self.roi_rs_dir, "mask_t1_wm_rs.nii.gz"), logFile=log)
                rrun("fslmaths " + os.path.join(self.roi_rs_dir, "t1_csf_rs.nii.gz") + " -thr 0.2 -bin " + os.path.join(self.roi_rs_dir, "mask_t1_csf_rs.nii.gz"), logFile=log)
                rrun("fslmaths " + os.path.join(self.roi_rs_dir, "t1_brain_rs.nii.gz") + " -thr 0.2 -bin " + os.path.join(self.roi_rs_dir, "mask_t1_brain_rs.nii.gz"), logFile=log)

                log.close()

        # ==============================================================================================================================================================
        # T2 data
        # ==============================================================================================================================================================
        if os.path.isdir(self.de_dir) is False:
            if imtest(self.t2_data) is True:
                self.has_T2 = True
                os.makedirs(os.path.join(self.roi_dir, "reg_t2"), exist_ok=True)

            if imtest(self.t2_brain_data) is False:
                print(self.label + " : bet on t2")
                rrun("bet " + self.t2_data + " " + self.t2_brain_data + " -f " + BET_F_VALUE_T2 + " -g 0.2 -m")

        # ==============================================================================================================================================================
        # DTI data
        # ==============================================================================================================================================================
        if os.path.isdir(self.dti_dir) is True and do_dtifit is True:
            log_file = os.path.join(self.dti_dir, "log_dti_processing.txt")
            log = open(log_file, "a")

            if imtest(os.path.join(self.dti_dir, self.dti_fit_label + "_FA")) is False:
                print("===========>>>> " + self.label + " : dtifit")
                self.dti.ec_fit()  # run .	$GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_ec_fit.sh $SUBJ_NAME $PROJ_DIR
                rrun("fslmaths " + os.path.join(self.dti_dir, self.dti_fit_label) + "_L2 -add " + os.path.join(self.dti_dir, self.dti_fit_label + "_L3") + " -div 2 " + os.path.join(self.dti_dir, self.dti_fit_label + "_L23"), logFile=log)

                self.dti_autoptx_tractography()

            os.makedirs(self.roi_dti_dir, exist_ok=True)

            if self.has_T2 is True:
                self.transform.transform_dti_t2()
            else:
                self.transform.transform_dti()

            if imtest(os.path.join(self.dti_dir, bedpost_odn, "mean_S0samples")) is False:
                if os.path.isfile(os.path.join(self.dti_dir, self.dti_rotated_bvec + ".gz")) is True:
                    runsystem("gunzip " + os.path.join(self.dti_dir, self.dti_rotated_bvec + ".gz"), logFile=log)

            if do_bedx is True:
                self.dti.bedpostx()  # .sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME

            if do_bedx_cuda is True:
                self.dti.bedpostx_gpu()  # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_bedpostx_CUDA.sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME

            if do_autoptx_tract is True:
                if imtest(os.path.join(self.dti_dir, bedpost_odn, "mean_S0samples")) is False:
                    print("subj " + self.label + " ,you requested the autoPtx tractorgraphy, but bedpostx was not performed.....skipping")
                else:
                    self.dti.autoptx_tractography()  # . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_autoptx_tractography.sh $SUBJ_NAME $PROJ_DIR

            if do_struct_conn is True and os.path.isfile(os.path.join(self.tv_matrices_dir, "fa_AM.mat")) is False:
                self.dti.conn_matrix(struct_conn_atlas_path, struct_conn_atlas_nroi)  # . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_conn_matrix.sh $SUBJ_NAME $PROJ_DIR

            log.close()


    # ==================================================================================================================================================
    # DATA CONVERSIONS
    # ==================================================================================================================================================
    # routines to convert original images to nifti format. assumes data are in an external folder and converted data are copied and renamed properly
    # postconvert_cleanup:
    #   0: don't do anything
    #   1: delete only files (when original file are already in the final folder)
    #   2: delete original folder
    # associations is a list of dictionaries {contains, type, extra}
    # 0	Success
    # 1	Unspecified error (see console output for details)
    # 2	No DICOM images found in input folder
    # 3	Exit from report version (result of dcm2niix -v)
    # 4	Corrupt DICOM file (Irrecoverable error during conversion)
    # 5	Input folder invalid
    # 6	Output folder invalid
    # 7	Unable to write to output folder (check file permissions)
    # 8	Converted some but not all of the input DICOMs
    # 9	Unable to rename files (result of dcm2niix -r y ~/in)

    def renameNifti(self, extpath, associations, options="-z o -f %f_%p_%t_%s_%d ", cleanup=0):

        try:
            if "." in extpath:
                print("ERROR : input path " + str(extpath) + " cannot contain dots !!!")
                return

            rrun("dcm2niix " + options + extpath)  # it returns :. usefs coXXXXXX, oXXXXXXX and XXXXXXX images

            files = glob.glob(os.path.join(extpath, "*"))

            converted_images = []
            original_images = []

            for f in files:

                if f.endswith("dcm"):
                    continue

                if is_image(f, self.DCM2NII_IMAGE_FORMATS) is True:
                    converted_images.append(f)
                else:
                    original_images.append(f)

            for img in converted_images:
                name = os.path.basename(img)
                fullext = img_split_ext(name)[1]
                name_noext = img_split_ext(name)[0]

                for ass in associations:

                    if ass['contains'] in name:
                        if ass['type'] == self.TYPE_T1:
                            dest_file = os.path.join(self.t1_dir, self.t1_image_label + fullext)
                            os.rename(img, dest_file)
                        elif ass['type'] == self.TYPE_T2:
                            dest_file = os.path.join(self.t2_dir, self.t2_image_label + fullext)
                            os.rename(img, dest_file)
                        elif ass['type'] == self.TYPE_RS:
                            dest_file = os.path.join(self.rs_dir, self.rs_image_label + fullext)
                            os.rename(img, dest_file)
                        elif ass['type'] == self.TYPE_DTI:
                            dest_file = os.path.join(self.dti_dir, self.dti_image_label + fullext)
                            os.rename(img, dest_file)
                            os.rename(os.path.join(extpath, name_noext + '.bval'),
                                      os.path.join(self.dti_dir, self.dti_image_label + '.bval'))
                            os.rename(os.path.join(extpath, name_noext + '.bvec'),
                                      os.path.join(self.dti_dir, self.dti_image_label + '.bvec'))
                        elif ass['type'] == self.TYPE_FMRI:
                            dest_file = os.path.join(self.fmri_dir, self.fmri_image_label + ass['extra'] + fullext)
                            os.rename(img, dest_file)

            if cleanup == 1:
                for img in original_images:
                    os.remove(img)
            elif cleanup == 2:
                os.rmdir(extpath)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def mpr2nifti(self, extpath, cleanup=0):

        try:
            if "." in extpath:
                print("ERROR : input path " + str(extpath) + " cannot contain dots !!!")
                return

            rrun("dcm2nii " + extpath)  # it returns :. usefs coXXXXXX, oXXXXXXX and XXXXXXX images

            files = glob.glob(os.path.join(extpath, "*"))

            converted_images = []
            original_images = []

            for f in files:
                if is_image(f, self.DCM2NII_IMAGE_FORMATS) is True:
                    converted_images.append(f)
                else:
                    original_images.append(f)

            for img in converted_images:
                name = os.path.basename(img)
                fullext = img_split_ext(name)[1]

                if name.startswith("co") is True:
                    dest_file = os.path.join(self.t1_dir, "co-" + self.t1_image_label + fullext)
                    # os.rename(img, dest_file)
                    os.remove(img)
                elif name.startswith("o") is True:
                    dest_file = os.path.join(self.t1_dir, "o-" + self.t1_image_label + fullext)
                    # os.rename(img, dest_file)
                    os.remove(img)
                else:
                    dest_file = os.path.join(self.t1_dir, self.t1_image_label + fullext)
                    move(img, dest_file)

            if cleanup == 1:
                for img in original_images:
                    os.remove(img)
            elif cleanup == 2:
                os.rmdir(extpath)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def mri_merger(self, input_files, outputname, dimension="-t", type='fmri'):

        if type == 'fmri':
            folder = self.fmri_dir
        else:
            folder = self.rs_dir

        cur_dir = os.path.curdir
        os.chdir(folder)

        rrun("fslmerge " + dimension + " " + outputname + " " + " ".join(input_files))
        os.chdir(cur_dir)

    # ==================================================================================================================================================

