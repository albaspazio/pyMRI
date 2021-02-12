import datetime
import traceback
import glob
import os
from copy import deepcopy
from shutil import copyfile, move, rmtree
from numpy import arange, concatenate, array

from utility.fslfun import run, runpipe, run_notexisting_img, runsystem, run_move_notexisting_img
from utility.manage_images import imtest, immv, imcp, imrm, quick_smooth, remove_ext, mass_images_move, is_image, mysplittext, imgname
from utility.utilities import sed_inplace, gunzip, write_text_file, compress
from utility.matlab import call_matlab_function, call_matlab_function_noret, call_matlab_spmbatch
from myfsl.utils.run import rrun
from Stats import Stats


class Subject:

    BIAS_TYPE_NO        = 0
    BIAS_TYPE_WEAK      = 1
    BIAS_TYPE_STRONG    = 2

    def __init__(self, label, sessid, project):

        self.label                  = label
        self.sessid                 = sessid

        self.project                = project
        self._global                = project._global
        self.fsl_dir                = self._global.fsl_dir
        self.fsl_bin                = self._global.fsl_bin
        self.fsl_data_standard_dir  = self._global.fsl_data_standard_dir

        self.project_subjects_dir   = project.subjects_dir

        self.set_file_system(self.sessid)

    def get_sess_file_system(self, sess):
        return self.set_file_system(sess, True)

    # this method has 2 usages:
    # 1) DEFAULT : to create filesystem names at startup    => returns : self  (DOUBT !! alternatively may always return a deepcopy)
    # 2) to get a copy with names of another session        => returns : deepcopy(self)
    def set_file_system(self, sess, rollback=False):

        self.dir                    = os.path.join(self.project.subjects_dir, self.label, "s" + str(sess))

        self.roi_dir                = os.path.join(self.dir, "roi")
        self.roi_epi_dir            = os.path.join(self.roi_dir, "reg_epi")
        self.roi_dti_dir            = os.path.join(self.roi_dir, "reg_dti")
        self.roi_t2_dir             = os.path.join(self.roi_dir, "reg_t2")
        self.roi_standard_dir       = os.path.join(self.roi_dir, "reg_standard")
        self.roi_standard4_dir      = os.path.join(self.roi_dir, "reg_standard4")
        self.roi_t1_dir             = os.path.join(self.roi_dir, "reg_t1")

        # ------------------------------------------------------------------------------------------------------------------------
        # T1/MPR
        # ------------------------------------------------------------------------------------------------------------------------
        self.t1_dir                 = os.path.join(self.dir, "mpr")
        self.t1_anat_dir            = os.path.join(self.t1_dir, "anat")
        self.fast_dir               = os.path.join(self.t1_dir, "fast")
        self.first_dir              = os.path.join(self.t1_dir, "first")
        self.sienax_dir             = os.path.join(self.t1_dir, "sienax")
        self.t1_fs_dir              = os.path.join(self.t1_dir, "freesurfer")
        self.t1_fs_mri_dir          = os.path.join(self.t1_fs_dir, "mri")
        self.t1_spm_dir             = os.path.join(self.t1_anat_dir, "spm_proc")
        self.t1_cat_dir             = os.path.join(self.t1_anat_dir, "cat_proc")

        self.t1_image_label         = self.label + "-t1"
        self.t1_data                = os.path.join(self.t1_dir, self.t1_image_label)
        self.t1_brain_data          = os.path.join(self.t1_dir, self.t1_image_label + "_brain")
        self.t1_brain_data_mask     = os.path.join(self.t1_dir, self.t1_image_label + "_brain_mask")
        self.t1_fs_brainmask_data   = os.path.join(self.t1_fs_dir, "mri", "brainmask")
        self.t1_fs_data             = os.path.join(self.t1_fs_dir, "mri", "T1")     # T1 coronal [1x1x1] after conform

        self.first_all_none_origsegs = os.path.join(self.first_dir, self.t1_image_label + "_all_none_origsegs")
        self.first_all_fast_origsegs = os.path.join(self.first_dir, self.t1_image_label + "_all_fast_origsegs")

        self.t1_segment_gm_path         = os.path.join(self.roi_t1_dir, "mask_t1_gm")
        self.t1_segment_wm_path         = os.path.join(self.roi_t1_dir, "mask_t1_wm")
        self.t1_segment_csf_path        = os.path.join(self.roi_t1_dir, "mask_t1_csf")
        self.t1_segment_wm_bbr_path     = os.path.join(self.roi_t1_dir, "wmseg4bbr")
        self.t1_segment_wm_ero_path     = os.path.join(self.roi_t1_dir, "mask_t1_wmseg4Nuisance")
        self.t1_segment_csf_ero_path    = os.path.join(self.roi_t1_dir, "mask_t1_csfseg4Nuisance")

        self.t1_cat_surface_dir         = os.path.join(self.t1_cat_dir, "surf")
        self.t1_cat_resampled_surface   = os.path.join(self.t1_cat_surface_dir, "s15.mesh.thickness.resampled_32k.T1_" + self.label + ".gii")
        self.t1_cat_resampled_surface_longitudinal   = os.path.join(self.t1_cat_surface_dir, "s15.mesh.thickness.resampled_32k.rT1_" + self.label + ".gii")

        # ------------------------------------------------------------------------------------------------------------------------
        # DTI
        # ------------------------------------------------------------------------------------------------------------------------
        self.dti_dir                    = os.path.join(self.dir, "dti")
        self.bedpost_X_dir              = os.path.join(self.dti_dir, "bedpostx")
        self.probtrackx_dir             = os.path.join(self.dti_dir, "probtrackx")
        self.trackvis_dir               = os.path.join(self.dti_dir, "trackvis")
        self.tv_matrices_dir            = os.path.join(self.dti_dir, "tv_matrices")

        self.dti_image_label            = self.label + "-dti"
        self.dti_ec_image_label         = self.dti_image_label + "_ec"
        self.dti_fit_label              = self.dti_image_label + "_fit"

        self.dti_bval_label             = os.path.join(self.dti_dir, self.label + "-dti.bval")
        self.dti_bvec_label             = os.path.join(self.dti_dir, self.label + "-dti.bvec")
        self.dti_rotated_bvec_label     = os.path.join(self.dti_dir, self.label + "-dti_rotated.bvec")

        self.dti_data                   = os.path.join(self.dti_dir,  self.dti_image_label)
        self.dti_ec_data                = os.path.join(self.dti_dir,  self.dti_ec_image_label)
        self.dti_fit_data               = os.path.join(self.dti_dir,  self.dti_fit_label)

        self.dti_nodiff_data            = os.path.join(self.dti_dir, "nodif")
        self.dti_nodiff_brain_data      = os.path.join(self.dti_dir, "nodif_brain")
        self.dti_nodiff_brainmask_data  = os.path.join(self.dti_dir, "nodif_brain_mask")

        self.trackvis_transposed_bvecs  = "bvec_vert.txt"

        # ------------------------------------------------------------------------------------------------------------------------
        # RS
        # ------------------------------------------------------------------------------------------------------------------------
        self.rs_image_label             = "resting"
        self.rs_dir                     = os.path.join(self.dir, "resting")
        self.rs_data                    = os.path.join(self.rs_dir, self.rs_image_label)
        self.sbfc_dir                   = os.path.join(self.rs_dir, "sbfc")
        self.rs_series_dir              = os.path.join(self.sbfc_dir, "series")
        self.rs_examplefunc             = os.path.join(self.roi_epi_dir, "example_func")

        self.rs_series_csf              = os.path.join(self.rs_series_dir, "csf_ts")
        self.rs_series_wm               = os.path.join(self.rs_series_dir, "wm_ts")

        self.rs_final_regstd_dir        = os.path.join(self.rs_dir, "reg_standard")
        self.rs_final_regstd_image      = os.path.join(self.rs_final_regstd_dir, "filtered_func_data")

        self.rs_post_preprocess_image_label                 = self.rs_image_label + "_preproc"
        self.rs_post_aroma_image_label                      = self.rs_image_label + "_preproc_aroma"
        self.rs_post_nuisance_image_label                   = self.rs_image_label + "_preproc_aroma_nuisance"
        self.rs_post_nuisance_melodic_image_label           = self.rs_image_label + "_preproc_aroma_nuisance_melodic"
        self.rs_post_nuisance_standard_image_label          = self.rs_image_label + "_preproc_aroma_nuisance_standard"
        self.rs_post_nuisance_melodic_standard_image_label  = self.rs_image_label + "_preproc_aroma_nuisance_melodic_resting"

        self.rs_regstd_dir              = os.path.join(self.rs_dir, "resting.ica", "reg_standard")
        self.rs_regstd_image            = os.path.join(self.rs_regstd_dir, "filtered_func_data")
        self.rs_regstd_denoise_dir      = os.path.join(self.rs_dir, "resting.ica", "reg_standard_denoised")
        self.rs_regstd_denoise_image    = os.path.join(self.rs_regstd_denoise_dir, "filtered_func_data")

        self.rs_aroma_dir               = os.path.join(self.rs_dir, "ica_aroma")
        self.rs_aroma_image             = os.path.join(self.rs_aroma_dir, "denoised_func_data_nonaggr")
        self.rs_regstd_aroma_dir        = os.path.join(self.rs_aroma_dir, "reg_standard")
        self.rs_regstd_aroma_image      = os.path.join(self.rs_regstd_aroma_dir, "filtered_func_data")

        self.mc_params_dir  = os.path.join(self.rs_dir, self.rs_image_label + ".ica", "mc")
        self.mc_abs_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_abs_mean.rms")
        self.mc_rel_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_rel_mean.rms")

        # ------------------------------------------------------------------------------------------------------------------------
        # OTHER (DE/T2/WB/PE)
        # ------------------------------------------------------------------------------------------------------------------------

        self.de_dir         = os.path.join(self.dir, "t2")
        self.de_image_label = "de"
        self.de_data        = os.path.join(self.de_dir, self.de_image_label)
        self.de_brain_data  = os.path.join(self.de_dir, self.de_image_label + "_brain")

        self.has_T2         = False
        self.t2_dir         = self.de_dir
        self.t2_image_label = "t2"
        self.t2_data        = os.path.join(self.t2_dir, self.t2_image_label)
        self.t2_brain_data  = os.path.join(self.t2_dir, self.t2_image_label + "_brain")

        self.wb_dir         = os.path.join(self.dir, "wb")
        self.wb_image_label = self.label + "-wb_epi"
        self.wb_data        = os.path.join(self.wb_dir, self.wb_image_label)
        self.wb_brain_data  = os.path.join(self.wb_dir, self.wb_image_label + "_brain")

        self.epi_image_label         = self.label + "-epi"
        self.epi_dir                 = os.path.join(self.dir, "epi")
        self.epi_data                = os.path.join(self.epi_dir, self.epi_image_label)
        self.epi_data_mc             = os.path.join(self.epi_dir, "r" + self.epi_image_label)

        self.epi_pe_data             = os.path.join(self.epi_dir, self.epi_image_label + "_pe")
        self.epi_acq_params          = os.path.join(self.epi_dir, "acqparams.txt")

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

        os.makedirs(os.path.join(self.dir, "mpr"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "epi"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "dti"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "t2"), exist_ok = True)

        os.makedirs(self.roi_t1_dir, exist_ok = True)
        os.makedirs(self.roi_standard_dir, exist_ok = True)
        os.makedirs(self.roi_dti_dir, exist_ok = True)
        os.makedirs(self.roi_epi_dir, exist_ok = True)
        os.makedirs(self.roi_t2_dir, exist_ok = True)

    def check_images(self, t1=False, rs=False, dti=False, t2=False):

        missing_images = []

        if t1 is True:
            if not imtest(self.t1_data):
                missing_images.append("t1")

        if rs is True:
            if not imtest(self.rs_data):
                missing_images.append("rs")

        if dti is True:
            if not imtest(self.dti_data):
                missing_images.append("dti")

        if t2 is True:
            if not imtest(self.t2_data):
                missing_images.append("t2")

        return missing_images

    def reslice_image(self, dir):

        if dir == "sag->axial":
            bckfilename = self.t1_image_label + "_sag"
            conversion_str = " -z -x y "
        else:
            print("invalid conversion")
            return

        bckfilepath = os.path.join(self.t1_dir, bckfilename)
        if imtest(bckfilepath):
            return

        imcp(self.t1_data, bckfilepath)          # create backup copy
        rrun("fslswapdim " + self.t1_data + conversion_str + self.t1_data)   # run reslicing

    # ==================================================================================================================================================
    # WELCOME
    # ==================================================================================================================================================

    def wellcome(self,  do_anat=True, odn = "anat", imgtype = 1, smooth = 10,
                        biascorr_type=BIAS_TYPE_STRONG,
                        do_reorient=True, do_crop=True,
                        do_bet=True, betfparam=[0.5],
                        do_sienax=True, bet_sienax_param_string="-SNB -f 0.2",
                        do_reg=True, do_nonlinreg=True,
                        do_seg=True, do_spm_seg=True, spm_seg_over_bet=False, spm_seg_over_fs=False,  # over-ride bet an
                        do_cleanup=True, do_strongcleanup=False, do_overwrite=False,
                        use_lesionmask=False, lesionmask="",
                        do_freesurfer=False,
                        do_first=False, first_struct="", first_odn="",
                        do_epirm2vol=0, do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="resting",
                        feat_preproc_model="singlesubj_feat_preproc", do_featinitreg=False,
                        do_melodic=True, mel_odn="resting",mel_preproc_model="singlesubj_melodic", do_melinitreg=False,
                        do_dtifit=True, do_bedx=True, do_bedx_cuda=False, bedpost_odn="bedpostx",
                        do_autoptx_tract=False,
                        do_struct_conn=False, struct_conn_atlas_path="freesurfer", struct_conn_atlas_nroi=0,
                        std_image=""):

        self.has_T2              = 0
        BET_F_VALUE_T2      = "0.5"
        feat_preproc_model  = os.path.join(self.project.script_dir, "glm", "templates", feat_preproc_model)
        melodic_model       = os.path.join(self.project.script_dir, "glm", "templates", mel_preproc_model)

        #==============================================================================================================================================================
        #  T1 data
        #==============================================================================================================================================================
        if os.path.exists(self.t1_dir):

            os.makedirs(self.roi_t1_dir, exist_ok=True)
            os.makedirs(self.roi_standard_dir, exist_ok=True)
            os.makedirs(self.fast_dir, exist_ok=True)

            if do_anat is True:
                self.mpr_prebet(
                    odn=odn, imgtype=imgtype, smooth=smooth,
                    biascorr_type=biascorr_type,
                    do_reorient=do_reorient, do_crop=do_crop,
                    do_bet=do_bet, do_overwrite=do_overwrite,
                    use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                self.mpr_bet(
                    odn=odn, imgtype=imgtype,
                    do_bet=do_bet, betfparam=betfparam,
                    do_reg=do_reg, do_nonlinreg=do_nonlinreg,
                    do_overwrite=do_overwrite,
                    use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                if do_spm_seg is True:
                    self.mpr_spm_segment(
                        odn=odn,
                        do_bet_overwrite=spm_seg_over_bet,
                        do_fs_overwrite=spm_seg_over_fs,
                        spm_template_name="spm_segment_dartelimport_template")

                self.mpr_postbet(
                        odn=odn, imgtype=imgtype, smooth=smooth,
                        betfparam=betfparam,
                        do_reg=do_reg, do_nonlinreg=do_nonlinreg,
                        do_seg=do_seg,
                        do_cleanup=do_cleanup, do_strongcleanup=do_strongcleanup, do_overwrite=do_overwrite,
                        use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                self.mpr_finalize(odn=odn)

            if do_sienax is True:
                print(self.label + " : sienax with " + bet_sienax_param_string)
                rrun("sienax " +  self.t1_data + " -B " + bet_sienax_param_string + " -r")

            self.transforms_mpr()
            if do_first is True:
              if imtest(self.first_all_fast_origsegs) is False and imtest(self.first_all_none_origsegs) is False:
                  self.mpr_first(first_struct, odn=first_odn)

            if do_freesurfer is True:
                self.mpr_fs_reconall()

        #==============================================================================================================================================================
        # WB data
        #==============================================================================================================================================================
        if os.path.exists(self.wb_dir):
            if imtest(self.wb_data) is True:
                if imtest(self.wb_brain_data) is False:
                    print(self.label + " : bet on WB")
                    rrun("bet " + self.wb_data + " " + self.wb_brain_data + " -f " + BET_F_VALUE_T2  + " -g 0 -m")

        #==============================================================================================================================================================
        # RS data
        #==============================================================================================================================================================
        if os.path.exists(self.rs_dir):
            os.makedirs(self.roi_epi_dir, exist_ok=True)

            if imtest(self.rs_data) is False:
                print("rs image (" + self.rs_data + ") is missing...continuing")
            else:
                log_file = os.path.join(self.rs_dir, "log_epi_processing.txt")
                log = open(log_file, "a")

                os.makedirs(os.path.join(self.project.group_analysis_dir, "melodic", "dr"), exist_ok=True)
                os.makedirs(os.path.join(self.project.group_analysis_dir, "melodic", "group_templates"), exist_ok=True)
                os.makedirs(self.rs_standard_dir, exist_ok=True)

                if do_epirm2vol > 0:
                    # check if I have to remove the first (TOT_VOL-DO_RMVOL_TO_NUM) volumes
                    tot_vol_num = rrun("fslnvols " + self.rs_data, logFile=log)
                    vol2remove  = tot_vol_num - do_epirm2vol

                    if vol2remove > 0:
                        immv(self.rs_data, self.rs_data + "_fullvol", logFile=log)
                        rrun("fslroi " + self.rs_data + "_fullvol " + self.rs_data + " " + str(vol2remove) + " " + str(tot_vol_num), logFile=log)

                # FEAT PRE PROCESSING
                if imtest(os.path.join(self.rs_dir, self.rs_post_preprocess_image_label)) is False:
                    if os.path.isfile(feat_preproc_model) is False:
                        print("===========>>>> FEAT_PREPROC template file (" + self.label + " " + feat_preproc_model + ".fsf) is missing...skipping feat preprocessing")
                    else:
                        if os.path.isdir(os.path.join(self.rs_dir, feat_preproc_odn)) is False:

                            self.epi_feat(do_initreg=do_featinitreg, std_image=std_image)  # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_feat.sh $SUBJ_NAME $PROJ_DIR -model $FEAT_PREPROC_MODEL -odn $FEAT_PREPROC_OUTPUT_DIR_NAME.feat -std_img $STANDARD_IMAGE -initreg $DO_FEAT_PREPROC_INIT_REG
                            imcp(os.path.join(self.rs_dir, feat_preproc_odn + ".feat", "filtered_func_data"), os.path.join(self.rs_dir, self.rs_post_preprocess_image_label), logFile=log)

                # do AROMA processing
                if do_aroma is True and imtest(os.path.join(self.rs_dir, self.rs_post_aroma_image_label)) is False:
                    self.epi_aroma()   #             run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_aroma.sh $SUBJ_NAME $PROJ_DIR -idn $FEAT_PREPROC_OUTPUT_DIR_NAME.feat  # do not register to standard
                    imcp(self.rs_aroma_image, os.path.join(self.rs_dir, self.rs_post_aroma_image_label))

                # do nuisance removal (WM, CSF & highpass temporal filtering)....create the following file: $RS_IMAGE_LABEL"_preproc_aroma_nuisance"
                if do_nuisance is True and imtest(os.path.join(self.rs_dir, self.rs_post_nuisance_image_label)) is False:
                    self.epi_resting_nuisance(hpfsec=hpfsec)  # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_resting_nuisance.sh $SUBJ_NAME $PROJ_DIR -hpfsec $HPF_SEC -ifn $RS_POST_AROMA_IMAGE_LABEL
                    self.transform_roi()     #             run . $GLOBAL_SCRIPT_DIR/process_subject/subject_transforms_roi.sh $SUBJ_NAME $PROJ_DIR -thresh 0 -regtype epi2std4 -pathtype abs $RS_DIR/$RS_POST_NUISANCE_IMAGE_LABEL
                    immv(os.path.join(self.roi_standard4_dir, self.rs_post_nuisance_standard_image_label), self.rs_final_regstd_image, logFile=log)

                imcp(os.path.join(self.rs_dir, feat_preproc_odn + ".feat", "reg_standard", "bg_image"), os.path.join(self.rs_final_regstd_dir, "bg_image"), logFile=log)
                imcp(os.path.join(self.rs_dir, feat_preproc_odn + ".feat", "reg_standard", "mask"), os.path.join(self.rs_final_regstd_dir, "mask"), logFile=log)

                # NOW reg_standard contains a denoised file with its mask and background image. nevertheless, we also do a melodic to check the output,
                # doing another MC and HPF results seems to improve...although they should not...something that should be investigated....

                # MELODIC

                if os.path.isdir(os.path.join(self.rs_dir, mel_odn + ".ica") is False and do_melodic is True):
                    if os.path.isfile(melodic_model + ".fsf"):
                        print("===========>>>> melodic template file (" + self.label + " " + melodic_model + ".fsf) is missing...skipping 1st level melodic")
                    else:
                        if os.path.isdir(os.path.join(self.rs_dir, mel_odn + ".ica")) is False:
                            self.epi_feat(do_initreg=do_melinitreg, std_image=std_image)     # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_feat.sh $SUBJ_NAME $PROJ_DIR -model $MELODIC_MODEL -odn $MELODIC_OUTPUT_DIR.ica -std_img $STANDARD_IMAGE -initreg $DO_FEAT_PREPROC_INIT_REG -ifn $RS_POST_NUISANCE_IMAGE_LABEL

                            if imtest(os.path.join(self.rs_dir, mel_odn + ".ica", "reg_standard", "filtered_func_data")) is True:
                                imcp(os.path.join(self.rs_dir, melodic_model + ".ica", "reg_standard", "filtered_func_data"), os.path.join(self.rs_final_regstd_dir, self.rs_post_nuisance_melodic_image_label + "_" + mel_odn), logFile=log)

                # calculate the remaining transformations   .....3/4/2017 si blocca qui...devo commentarlo per andare avanti !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                self.transform_epi() # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_transforms_calculate_epi.sh $SUBJ_NAME $PROJ_DIR

                # coregister fast-highres to epi
                print(self.label + ": coregister fast-highres to epi")

                if imtest(os.path.join(self.roi_epi_dir, "t1_wm_epi")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, "mask_t1_wm")      + " -ref " + os.path.join(self.roi_epi_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "highres2epi.mat") + " -out " + os.path.join(self.roi_epi_dir, "t1_wm_epi"))

                if imtest(os.path.join(self.roi_epi_dir, "t1_csf_epi")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, "mask_t1_csf")     + " -ref " + os.path.join(self.roi_epi_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "highres2epi.mat") + " -out " + os.path.join(self.roi_epi_dir, "t1_csf_epi"))

                if imtest(os.path.join(self.roi_epi_dir, "t1_gm_epi")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, "mask_t1_gm")      + " -ref " + os.path.join(self.roi_epi_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "highres2epi.mat") + " -out " + os.path.join(self.roi_epi_dir, "t1_gm_epi"))

                if imtest(os.path.join(self.roi_epi_dir, "t1_brain_epi")) is False:
                    rrun("flirt -in " + os.path.join(self.roi_t1_dir, self.t1_brain_data)+ " -ref " + os.path.join(self.roi_epi_dir, "example_func") + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "highres2epi.mat") + " -out " + os.path.join(self.roi_epi_dir, "t1_brain_epi"))

                # mask & binarize
                rrun("fslmaths " + os.path.join(self.roi_epi_dir, "t1_gm_epi.nii.gz")    + " -thr 0.2 -bin " + os.path.join(self.roi_epi_dir, "mask_t1_gm_epi.nii.gz"), logFile=log)
                rrun("fslmaths " + os.path.join(self.roi_epi_dir, "t1_wm_epi.nii.gz")    + " -thr 0.2 -bin " + os.path.join(self.roi_epi_dir, "mask_t1_wm_epi.nii.gz"), logFile=log)
                rrun("fslmaths " + os.path.join(self.roi_epi_dir, "t1_csf_epi.nii.gz")   + " -thr 0.2 -bin " + os.path.join(self.roi_epi_dir, "mask_t1_csf_epi.nii.gz"), logFile=log)
                rrun("fslmaths " + os.path.join(self.roi_epi_dir, "t1_brain_epi.nii.gz") + " -thr 0.2 -bin " + os.path.join(self.roi_epi_dir, "mask_t1_brain_epi.nii.gz"), logFile=log)

                log.close()
        #==============================================================================================================================================================
        # T2 data
        #==============================================================================================================================================================
        if os.path.isdir(self.de_dir) is False:
            if imtest(self.t2_data) is True:
                self.has_T2 = True
                os.makedirs(os.path.join(self.roi_dir, "reg_t2"), exist_ok=True)

            if imtest(self.t2_brain_data) is False:
                print(self.label + " : bet on t2")
                rrun("bet " + self.t2_data + " " + self.t2_brain_data + " -f " + BET_F_VALUE_T2 + " -g 0.2 -m")

        #==============================================================================================================================================================
        # DTI data
        #==============================================================================================================================================================
        if os.path.isdir(self.dti_dir) is True:
            log_file = os.path.join(self.dti_dir, "log_dti_processing.txt")
            log = open(log_file, "a")

            if do_dtifit is True and imtest(os.path.join(self.dti_dir, self.dti_fit_label + "_FA")) is False:
                print("===========>>>> " + self.label + " : dtifit")
                self.dti_ec_fit()   # run .	$GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_ec_fit.sh $SUBJ_NAME $PROJ_DIR
                rrun("fslmaths " + os.path.join(self.dti_dir, self.dti_fit_label) + "_L2 -add " + os.path.join(self.dti_dir, self.dti_fit_label + "_L3") + " -div 2 " + os.path.join(self.dti_dir, self.dti_fit_label + "_L23"), logFile=log)

                self.dti_autoptx_tractography()

            os.makedirs(self.roi_dti_dir, exist_ok=True)

            if self.has_T2 is True:
                self.transform_dti_t2()
            else:
                self.transform_dti()

            if imtest(os.path.join(self.dti_dir, bedpost_odn, "mean_S0samples")) is False:
                if os.path.isfile(os.path.join(self.dti_dir, self.dti_rotated_bvec + ".gz")) is True:
                    runsystem("gunzip " + os.path.join(self.dti_dir, self.dti_rotated_bvec + ".gz"), logFile=log)

            if do_bedx is True:
                self.dti_bedpostx() #.sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME

            if do_bedx_cuda is True:
                self.dti_bedpostx_gpu() #run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_bedpostx_CUDA.sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME

            if do_autoptx_tract is True:
                if imtest(os.path.join(self.dti_dir, bedpost_odn, "mean_S0samples")) is False:
                    print("subj " + self.label + " ,you requested the autoPtx tractorgraphy, but bedpostx was not performed.....skipping")
                else:
                    self.dti_autoptx_tractography() # . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_autoptx_tractography.sh $SUBJ_NAME $PROJ_DIR

            if do_struct_conn is True and os.path.isfile(os.path.join(self.tv_matrices_dir, "fa_AM.mat")) is False:
                self.dti_conn_matrix(struct_conn_atlas_path, struct_conn_atlas_nroi)  #. $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_conn_matrix.sh $SUBJ_NAME $PROJ_DIR

            log.close()

    # ==================================================================================================================================================
    # ANATOMICAL
    # ==================================================================================================================================================
    # pre-processing:
    def mpr_prebet(self,
                   odn="anat", imgtype=1, smooth=10,
                   biascorr_type=BIAS_TYPE_STRONG,
                   do_reorient=True, do_crop=True,
                   do_bet=True,
                   do_overwrite=False,
                   use_lesionmask=False, lesionmask=""
                   ):
        niter       = 5
        logfile     = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir      = os.getcwd()

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage  = self.t1_data
            anatdir     = os.path.join(self.t1_dir, odn)
            T1          = "T1"
        elif imgtype == 2:
            inputimage  = self.t2_data
            anatdir     = os.path.join(self.t2_dir, odn)
            T1          = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        # check original image presence, otherwise exit
        if imtest(inputimage) is False:
            print("ERROR: input anatomical image is missing....exiting")
            return False

        # check given lesionmask presence, otherwise exit
        if use_lesionmask is True and imtest(lesionmask) is False:
            print("ERROR: given Lesion mask is missing....exiting")
            return False

        # I CAN START PROCESSING !
        try:

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            # os.chdir(anatdir)
            T1 = os.path.join(anatdir, T1)  # T1 is now an absolute path

            # init or append log file
            if os.path.isfile(logfile):
                with open(logfile, "a") as text_file:
                    print("******************************************************************", file=text_file)
                    print("updating directory", file=text_file)
                    print(" ", file=text_file)
            else:
                with open(logfile, "w") as text_file:
                    # some initial reporting for the log file
                    print("Script invoked from directory = " + os.getcwd(), file=text_file)
                    print("Output directory " + anatdir, file=text_file)
                    print("Input image is " + inputimage, file=text_file)
                    print(" " + anatdir, file=text_file)

            log = open(logfile, "a")

            # copy original image to anat dir
            if imtest(T1) is False:
                rrun("fslmaths " + inputimage + " " + T1, logFile=log)

            # cp lesionmask to anat dir then (even it does not exist) update variable lesionmask=os.path.join(anatdir, "lesionmask")
            if use_lesionmask is True:
                # I previously verified that it exists
                rrun("fslmaths", [lesionmask, os.path.join(anatdir, "lesionmask")])
                lesionmask      = os.path.join(anatdir, "lesionmask")
                with open(logfile, "a") as text_file:
                    text_file.write("copied lesion mask " + lesionmask)
            else:
                lesionmask = os.path.join(anatdir, "lesionmask")

            lesionmaskinv = lesionmask + "inv"

            # ==================================================================================================================================================================
            # now the real work
            # ==================================================================================================================================================================

            #### FIXING NEGATIVE RANGE
            # required input: " + T1 + "
            # output: " + T1 + "

            minval =  float(rrun("fslstats " + T1 + " -p " + str(0), logFile=log))
            maxval =  float(rrun("fslstats " + T1 + " -p " + str(100), logFile=log))

            if minval < 0:
                if maxval > 0:
                    # if there are just some negative values among the positive ones then reset zero to the min value
                    rrun("fslmaths " + T1 + " -sub " + str(minval) + T1 + " -odt float", logFile=log)
                else:
                    rrun("fslmaths " + T1 + " -bin -binv zeromask", logFile=log)
                    rrun("fslmaths " + T1 + " -sub " + str(minval) + " -mas zeromask " + T1 + " -odt float", logFile=log)

            #### REORIENTATION 2 STANDARD
            # required input: " + T1 + "
            # output: " + T1 + " (modified) [ and " + T1 + "_orig and .mat ]
            if not os.path.isfile(T1 + "_orig2std.mat") or do_overwrite is True:
                if do_reorient is True:
                    print(self.label + " :Reorienting to standard orientation")
                    rrun("fslmaths " + T1 + " " + T1 + "_orig", logFile=log)
                    # os.system("fslreorient2std " + T1 + " > " + T1 + "_orig2std.mat")
                    run("fslreorient2std " + T1 + " > " + T1 + "_orig2std.mat", logFile=log)
                    rrun("convert_xfm -omat " + T1 + "_std2orig.mat -inverse " + T1 + "_orig2std.mat", logFile=log)
                    rrun("fslmaths " + T1 + " " + T1 + "_orig", logFile=log)

            #### AUTOMATIC CROPPING
            # required input: " + T1 + "
            # output: " + T1 + " (modified) [ and " + T1 + "_fullfov plus various .mats ]

            if imtest(T1 + "_fullfov") is False or do_overwrite is True:
                if do_crop is True:
                    print(self.label + " :Automatically cropping the image")
                    immv(T1, T1 + "_fullfov")
                    run(os.path.join(os.path.join(os.getenv('FSLDIR'), "bin"), "robustfov -i " + T1 + "_fullfov -r " + T1 + " -m " + T1 + "_roi2nonroi.mat | grep [0-9] | tail -1 > " + T1 + "_roi.log"), logFile=log)
                    # combine this mat file and the one above (if generated)
                    if do_reorient is True:
                        rrun("convert_xfm -omat " + T1 + "_nonroi2roi.mat -inverse " + T1 + "_roi2nonroi.mat", logFile=log)
                        rrun("convert_xfm -omat " + T1 + "_orig2roi.mat -concat " + T1 + "_nonroi2roi.mat " + T1 + "_orig2std.mat", logFile=log)
                        rrun("convert_xfm -omat " + T1 + "_roi2orig.mat -inverse " + T1 + "_orig2roi.mat", logFile=log)

            ### LESION MASK
            # if I set use_lesionmask: I already verified that the external lesionmask exist and I copied to anat folder and renamed as "lesionmask"
            transform = ""
            if imtest(lesionmask) is False or do_overwrite is True:
                # make appropriate (reoreinted and cropped) lesion mask (or a default blank mask to simplify the code later on)
                if use_lesionmask is True:
                    if not os.path.isfile(T1 + "_orig2std.mat"):
                        transform = T1 + "_orig2std.mat"
                    if not os.path.isfile(T1 + "_orig2roi.mat"):
                        transform = T1 + "_orig2roi.mat"
                    if transform is not "":
                        rrun("fslmaths " + lesionmask + " " + lesionmask + "_orig", logFile=log)
                        rrun("flirt -in " + lesionmask + "_orig" + " -ref " + T1 + " -applyxfm -interp nearestneighbour -init " + transform + " -out " + lesionmask, logFile=log)
                else:
                    rrun("fslmaths " +  T1 + " -mul 0 " + lesionmask, logFile=log)

                rrun("fslmaths " + lesionmask + " -bin "  + lesionmask, logFile=log)
                rrun("fslmaths " + lesionmask + " -binv " + lesionmaskinv, logFile=log)

            #### BIAS FIELD CORRECTION (main work, although also refined later on if segmentation is run)
            # required input: " + T1 + "
            # output: " + T1 + "_biascorr  [ other intermediates to be cleaned up ]
            if imtest(T1 + "_biascorr") is False or do_overwrite is True:
                if biascorr_type > self.BIAS_TYPE_NO:
                    if biascorr_type == self.BIAS_TYPE_STRONG:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.label + " :Estimating and removing field (stage 1 -large-scale fields)")
                        # for the first step (very gross bias field) don't worry about the lesionmask
                        # the following is a replacement for : run $FSLDIR/bin/fslmaths " + T1 + " -s 20 " + T1 + "_s20
                        quick_smooth(T1, T1 + "_s20", logFile=log)
                        rrun("fslmaths " + T1 + " -div " + T1 + "_s20 " + T1 + "_hpf", logFile=log)
                        
                        if do_bet is True:
                            # get a rough brain mask - it can be *VERY* rough (i.e. missing huge portions of the brain or including non-brain, but non-background) - use -f 0.1 to err on being over inclusive
                            rrun("bet " + T1 + "_hpf " + T1 + "_hpf_brain -m -f 0.1", logFile=log)
                        else:
                            rrun("fslmaths " + T1 + "_hpf " + T1 + "_hpf_brain", logFile=log)
                            rrun("fslmaths " + T1 + "_hpf_brain -bin " + T1 + "_hpf_brain_mask", logFile=log)

                        rrun("fslmaths " + T1 + "_hpf_brain_mask -mas " + lesionmaskinv + " " + T1 + "_hpf_brain_mask", logFile=log)
                        # get a smoothed version without the edge effects
                        rrun("fslmaths " + T1 + " -mas " + T1 + "_hpf_brain_mask " + T1 + "_hpf_s20", logFile=log)
                        quick_smooth(T1 + "_hpf_s20", T1 + "_hpf_s20", logFile=log)
                        quick_smooth(T1 + "_hpf_brain_mask", T1 + "_initmask_s20", logFile=log)
                        rrun("fslmaths " + T1 + "_hpf_s20 -div " + T1 + "_initmask_s20 -mas " + T1 + "_hpf_brain_mask " + T1 + "_hpf2_s20", logFile=log)
                        rrun("fslmaths " + T1 + " -mas " + T1 + "_hpf_brain_mask -div " + T1 + "_hpf2_s20 " + T1 + "_hpf2_brain", logFile=log)
                        # make sure the overall scaling doesn't change (equate medians)
                        med0 = rrun("fslstats " + T1 + " -k " + T1 + "_hpf_brain_mask -P 50", logFile=log)
                        med1 = rrun("fslstats " + T1 + " -k " + T1 + "_hpf2_brain -k " + T1 + "_hpf_brain_mask -P 50", logFile=log)
                        rrun("fslmaths " + T1 + "_hpf2_brain -div " + str(med1) + " -mul " + med0 + " " + T1 + "_hpf2_brain", logFile=log)
                        
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print( self.label + " :Estimating and removing bias field (stage 2 - detailed fields)")
                        rrun("fslmaths " + T1 + "_hpf2_brain -mas " + lesionmaskinv + " " + T1 + "_hpf2_maskedbrain", logFile=log)
                        rrun("fast -o " + T1 + "_initfast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_hpf2_maskedbrain", logFile=log)
                        rrun("fslmaths " + T1 + "_initfast_restore -mas " + lesionmaskinv + " " + T1 + "_initfast_maskedrestore", logFile=log)
                        rrun("fast -o " + T1 + "_initfast2 -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_initfast_maskedrestore", logFile=log)
                        rrun("fslmaths " + T1 + "_hpf_brain_mask " + T1 + "_initfast2_brain_mask", logFile=log)
                    else:
                        # weak bias
                        if do_bet is True:
                            # get a rough brain mask - it can be *VERY* rough (i.e. missing huge portions of the brain or including non-brain, but non-background) - use -f 0.1 to err on being over inclusive
                            rrun("bet " + T1 + " " + T1 + "_initfast2_brain -m -f 0.1", logFile=log)
                        else:
                            rrun("fslmaths " + T1 + " " + T1 + "_initfast2_brain", logFile=log)
                            rrun("fslmaths " + T1 + "_initfast2_brain -bin " + T1 + "_initfast2_brain_mask", logFile=log)

                        rrun("fslmaths " + T1 + "_initfast2_brain " + T1 + "_initfast2_restore", logFile=log)

                    # redo fast again to try and improve bias field
                    rrun("fslmaths " + T1 + "_initfast2_restore -mas " + lesionmaskinv + " " + T1 + "_initfast2_maskedrestore", logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_initfast2_maskedrestore", logFile=log)
                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.label + " :Extrapolating bias field from central region")
                    # use the latest fast output
                    rrun("fslmaths " + T1 + " -div " + T1 + "_fast_restore -mas " + T1 + "_initfast2_brain_mask " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslmaths " + T1 + "_initfast2_brain_mask -ero -ero -ero -ero -mas " + lesionmaskinv + " " + T1 + "_initfast2_brain_mask2", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_initfast2_brain_mask2 -o " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_initfast2_brain_mask -dilall -add 1 " + T1 + "_fast_bias  # alternative to fslsmoothfill
                    rrun("fslmaths " + T1 + " -div " + T1 + "_fast_bias " + T1 + "_biascorr", logFile=log)
                else:
                    rrun("fslmaths " + T1 + " " + T1 + "_biascorr", logFile=log)
            log.close()

        except Exception as e:
            traceback.print_exc()
            print(self.label + "  " + os.getcwd())
            log.close()
            print(e)

    def mpr_bet(self,
                odn="anat", imgtype=1,
                do_bet=True, betfparam=[], bettypeparam="-R",
                do_reg=True, do_nonlinreg=True,
                do_skipflirtsearch=False,
                do_overwrite=False,
                use_lesionmask=False, lesionmask="lesionmask"
                ):

        logfile = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir  = os.getcwd()

        # check anatomical image imgtype
        if imgtype is not 1:
            if do_nonlinreg is True:
                print(
                    "ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
                return False

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage = self.t1_data
            anatdir = os.path.join(self.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            inputimage = self.t2_data
            anatdir = os.path.join(self.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1              = os.path.join(anatdir, T1)  # T1 is now an absolute path
        lesionmask      = os.path.join(anatdir, lesionmask)
        lesionmaskinv   = os.path.join(anatdir, lesionmask + "inv")

        # check original image presence, otherwise exit
        if imtest(inputimage) is False:
            print("ERROR: input anatomical image is missing....exiting")
            return False

        # check given lesionmask presence, otherwise exit
        if use_lesionmask is True and imtest(lesionmask) is False:
            print("ERROR: given Lesion mask is missing....exiting")
            return False

        if len(betfparam) == 0:
            list_bet_fparams = [0.5]
        else:
            list_bet_fparams = betfparam

        # I CAN START PROCESSING !
        try:
            # create some params strings
            if do_skipflirtsearch is True:
                flirtargs = " -nosearch"
            else:
                flirtargs = " "

            if use_lesionmask is True:
                fnirtargs = " --inmask=" + lesionmaskinv
            else:
                fnirtargs = " "

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            # os.chdir(anatdir)

            # init or append log file
            if os.path.isfile(logfile):
                with open(logfile, "a") as text_file:
                    print("******************************************************************", file=text_file)
                    print("updating directory", file=text_file)
                    print(" ", file=text_file)
            else:
                with open(logfile, "w") as text_file:
                    # some initial reporting for the log file
                    print("Script invoked from directory = " + os.getcwd(), file=text_file)
                    print("Output directory " + anatdir, file=text_file)
                    print("Input image is " + inputimage, file=text_file)
                    print(" " + anatdir, file=text_file)

            log = open(logfile, "a")

            #### REGISTRATION AND BRAIN EXTRACTION
            # required input: " + T1 + "_biascorr
            # output: " + T1 + "_biascorr_brain " + T1 + "_biascorr_brain_mask " + T1 + "_to_MNI_lin " + T1 + "_to_MNI [plus transforms, inverse transforms, jacobians, etc.]
            if imtest(T1 + "_biascorr_brain") is False or do_overwrite is True:
                if do_reg is True:
                    if do_bet is False:
                        print(self.label + " :Skipping registration, as it requires a non-brain-extracted input image")
                    else:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.label + " :Registering to standard space (linear)")

                        if use_lesionmask is True:
                            flirtargs = flirtargs + " -inweight " + lesionmaskinv

                        rrun("flirt -interp spline -dof 12 -in " + T1 + "_biascorr -ref " + os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm") + " -dof 12 -omat " + T1 + "_to_MNI_lin.mat -out " + T1 + "_to_MNI_lin " + flirtargs, logFile=log)

                        if do_nonlinreg is True:

                            # nnlin co-reg T1 to standard
                            # inv warp of T1standard_mask => mask T1.
                            # mask T1 with above img
                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print( "Registering to standard space (non-linear)")
                            refmask = os.path.join(anatdir, "MNI152_T1_2mm_brain_mask_dil1")

                            rrun("fslmaths " + self._global.fsl_standard_mni_2mm_mask + " -fillh -dilF " + refmask, logFile=log)
                            rrun("fnirt --in=" + T1 + "_biascorr --ref=" + self._global.fsl_standard_mni_2mm_head + " --fout=" + T1 + "_to_MNI_nonlin_field --jout=" + T1 + "_to_MNI_nonlin_jac --iout=" + T1 + "_to_MNI_nonlin --logout=" + T1 + "_to_MNI_nonlin.txt --cout=" + T1 + "_to_MNI_nonlin_coeff --config=" + self._global.fsl_standard_mni_2mm_cnf + " --aff=" + T1 + "_to_MNI_lin.mat --refmask=" + refmask + " " + fnirtargs, logFile=log)

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.label + " :Performing brain extraction (using FNIRT)")
                            rrun("invwarp --ref=" + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_coeff -o " + os.path.join(anatdir, "MNI_to_T1_nonlin_field"), logFile=log)
                            rrun("applywarp --interp=nn --in=" + self._global.fsl_standard_mni_2mm_mask + " --ref=" + T1 + "_biascorr -w " + os.path.join(anatdir, "MNI_to_T1_nonlin_field") + " -o " + T1 + "_biascorr_brain_mask", logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr_brain_mask -fillh " + T1 + "_biascorr_brain_mask", logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr -mas " + T1 + "_biascorr_brain_mask " + T1 + "_biascorr_brain", logFile=log)
                        ## In the future, could check the initial ROI extraction here
                else:
                    if do_bet is True:

                        for i in range(len(list_bet_fparams)):
                            betopts = bettypeparam + " -f " + str(list_bet_fparams[i])

                            fp = "_" + str(list_bet_fparams[i]).replace(".", "")

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.label + " :Performing brain extraction (using BET)")
                            rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_brain" + fp + " -m " + betopts, logFile=log)  ## results sensitive to the f parameter

                        imcp(T1 + "_biascorr_brain" + fp, T1 + "_biascorr_brain")
                        imcp(T1 + "_biascorr_brain" + fp + "_mask", T1 + "_biascorr_brain_mask")
                    else:
                        rrun("fslmaths " + T1 + "_biascorr " + T1 + "_biascorr_brain", logFile=log)
                        rrun("fslmaths " + T1 + "_biascorr_brain -bin " + T1 + "_biascorr_brain_mask", logFile=log)
            log.close()



        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)


    # segment T1 with SPM and create  WM+GM and WM+GM+CSF masks
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    # if requested: replace brainmask (produced by FreeSurfer)  BUGGED !!! ignore it
    def mpr_spm_segment(self,
                        odn="anat", imgtype=1,
                        do_overwrite=False,
                        do_bet_overwrite=False,
                        add_bet_mask=True,
                        set_origin=False,
                        seg_templ="",
                        spm_template_name="spm_segment_tissuevolume"
                        ):

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir = os.path.join(self.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            anatdir = os.path.join(self.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        srcinputimage           = os.path.join(anatdir, T1 + "_biascorr")
        inputimage              = os.path.join(self.t1_spm_dir, T1 + "_" + self.label)

        # set dirs
        spm_script_dir          = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir           = os.path.join(spm_script_dir, "batch")
        in_script_template      = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start         = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template         = os.path.join(out_batch_dir, self.label + "_" + spm_template_name + "_job.m")
        output_start            = os.path.join(out_batch_dir, "start_" + self.label + "_" + spm_template_name + ".m")

        brain_mask              = os.path.join(self.t1_spm_dir, "brain_mask.nii.gz")
        skullstripped_mask      = os.path.join(self.t1_spm_dir, "skullstripped_mask.nii.gz")

        icv_file                = os.path.join(self.t1_spm_dir, "icv_" + self.label + ".dat")

        # check whether skipping
        if imtest(brain_mask) is True and do_overwrite is False:
            return
        try:

            logfile = os.path.join(self.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(out_batch_dir   , exist_ok = True)
            os.makedirs(self.t1_spm_dir   , exist_ok = True)

            gunzip(srcinputimage + ".nii.gz", inputimage + ".nii")

            # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
            if set_origin is True:
                input("press keyboard when finished setting the origin for subj " + self.label + " :")

            if seg_templ == "":
                seg_templ = os.path.join(self._global.spm_dir, "tpm", "TPM.nii")
            else:
                if imtest(seg_templ) is False:
                    print("Error in mpr_spm_segment: given tissues template image (" +  seg_templ + ") does not exist")

            copyfile(in_script_template , output_template)
            copyfile(in_script_start    , output_start)

            sed_inplace(output_template, "<T1_IMAGE>", inputimage + ".nii")
            sed_inplace(output_template, "<ICV_FILE>", icv_file)
            sed_inplace(output_template, '<SPM_DIR>', self._global.spm_dir)
            sed_inplace(output_template, '<TEMPLATE_TISSUES>', seg_templ)

            sed_inplace(output_start, "X", "1")
            sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

            call_matlab_spmbatch(output_start, [self._global.spm_functions_dir], log)

            # create brainmask (WM+GM) and skullstrippedmask (WM+GM+CSF)
            c1img               = os.path.join(anatdir, "spm_proc", "c1T1_" + self.label + ".nii")
            c2img               = os.path.join(anatdir, "spm_proc", "c2T1_" + self.label + ".nii")
            c3img               = os.path.join(anatdir, "spm_proc", "c3T1_" + self.label + ".nii")

            rrun("fslmaths " + c1img + " -add " + c2img                     + " -thr 0.1 -fillh " + brain_mask, logFile=log)
            rrun("fslmaths " + c1img + " -add " + c2img + " -add " + c3img  + " -thr 0.1 -bin "   + skullstripped_mask, logFile=log)

            # this codes have two aims:
            # 1) it resets like in the original image the dt header parameters that spm set to 0.
            #    otherwise it fails some operations like fnirt as it sees the mask and the brain data of different dimensions
            # 2) changing image origin in spm, changes how fsleyes display the image. while, masking in this ways, everything goes right
            rrun("fslmaths " + srcinputimage + ".nii.gz" + " -mas " + brain_mask + " -bin " + brain_mask)
            rrun("fslmaths " + srcinputimage + ".nii.gz" + " -mas " + skullstripped_mask + " -bin " + skullstripped_mask)

            if add_bet_mask is True:

                if imtest(os.path.join(self.t1_anat_dir, "T1_biascorr_brain_mask")) is True:
                    rrun("fslmaths " + brain_mask + " -add " + os.path.join(self.t1_anat_dir, "T1_biascorr_brain_mask") + " -bin " + brain_mask)
                elif imtest(self.t1_brain_data_mask) is True:
                    rrun("fslmaths " + brain_mask + " -add " + self.t1_brain_data_mask + " " + brain_mask)
                else:
                    print("warning in mpr_spm_segment: no other bet mask to add to spm one")

            if do_bet_overwrite is True:

                # copy SPM mask and use it to mask T1_biascorr
                imcp(brain_mask, self.t1_brain_data_mask, logFile=log)
                rrun("fslmaths " + inputimage + " -mas " + brain_mask + " " + self.t1_brain_data, logFile=log)

            imrm([inputimage + ".nii"])
            # if do_fs_overwrite is True:
            #
            #     fs_brain_mask       = os.path.join(self.t1_fs_dir, "brainmask.mgz")
            #     fs_brain_mask_fsl   = os.path.join(self.t1_fs_dir, "brainmask.nii.gz")
            #     fs_t1               = os.path.join(self.t1_fs_dir, "T1.mgz")
            #     fs_t1_fsl           = os.path.join(self.t1_fs_dir, "T1.nii.gz")
            #
            #     if not imtest(fs_t1):
            #         print("anatomical_processing_spm_segment was called with freesurfer replace, but fs has not been run")
            #         return
            #
            #     imcp(fs_brain_mask, os.path.join(self.t1_fs_dir, "brainmask_orig.mgz"), logFile=log)    # backup original brainmask
            #     rrun("mri_convert " + fs_t1 + " " + fs_t1_fsl, logFile=log)                          # convert t1.mgz
            #
            #     rrun("fslmaths " + fs_t1_fsl + " -mas " + brain_mask + " " + fs_brain_mask_fsl, logFile=log) # mask T1 with SPM brain_mask
            #     rrun("mri_convert " + fs_brain_mask_fsl + " " + fs_brain_mask, logFile=log)                  # convert brainmask back to mgz
            #
            #     imrm(fs_t1_fsl, logFile=log)
            #     imrm(fs_brain_mask_fsl, logFile=log)

            log.close()

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)


    # segment T1 with CAT and create  WM+GM mask (CSF is not created)
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    def mpr_cat_segment(self,
                        odn="anat", imgtype=1,
                        do_overwrite=False,
                        do_bet_overwrite=False,
                        add_bet_mask=True,
                        set_origin=False,
                        seg_templ="",
                        coreg_templ="",
                        calc_surfaces=0,
                        num_proc=1,
                        use_existing_nii=True,
                        spm_template_name="cat_segment_customizedtemplate_tiv_smooth"
                        ):

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir = os.path.join(self.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            anatdir = os.path.join(self.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        if seg_templ == "":
            seg_templ = self._global.spm_tissue_map
        else:
            if imtest(seg_templ) is False:
                print("ERROR in mpr_cat_segment: given template segmentation is not present")
                return

        if coreg_templ == "":
            coreg_templ = self._global.cat_dartel_template
        else:
            if imtest(coreg_templ) is False:
                print("ERROR in mpr_cat_segment: given template coregistration is not present")
                return

        srcinputimage           = os.path.join(anatdir, T1 + "_biascorr")
        inputimage              = os.path.join(self.t1_cat_dir, T1 + "_" + self.label)

        # set dirs
        spm_script_dir          = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir           = os.path.join(spm_script_dir, "batch")
        in_script_template      = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start         = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template         = os.path.join(out_batch_dir, self.label + "_" + spm_template_name + "_job.m")
        output_start            = os.path.join(out_batch_dir, "start_" + self.label + "_" + spm_template_name + ".m")

        brain_mask              = os.path.join(self.t1_cat_dir, "brain_mask.nii.gz")

        icv_file                = os.path.join(self.t1_cat_dir, "tiv_" + self.label + ".txt")

        # check whether skipping
        if imtest(brain_mask) is True and do_overwrite is False:
            return
        try:

            logfile = os.path.join(self.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(out_batch_dir   , exist_ok = True)
            os.makedirs(self.t1_cat_dir , exist_ok = True)

            # I may want to process with cat after having previously processed without having set image's origin.
            # thus I may have created a nii version in the cat_proc folder , with the origin properly set
            # unzip nii.gz -> nii in cat folder only if nii is absent or I want to overwrite it.
            if use_existing_nii is False:
                if os.path.exists(srcinputimage + ".nii.gz") is True:
                    gunzip(srcinputimage + ".nii.gz", inputimage + ".nii")
                else:
                    print("Error in subj: "+ self.label + ", method: mpr_cat_segment, biascorr image is absent")
            else:
                if os.path.exists(inputimage + ".nii") is False:
                    print("Error in subj: "+ self.label + ", method: mpr_cat_segment, given image in cat folder is absent")

            # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
            if set_origin is True:
                input("press keyboard when finished setting the origin for subj " + self.label + " :")

            copyfile(in_script_template , output_template)
            copyfile(in_script_start    , output_start)

            sed_inplace(output_template, "<T1_IMAGE>", inputimage + ".nii")
            sed_inplace(output_template, "<TEMPLATE_SEGMENTATION>", seg_templ)
            sed_inplace(output_template, "<TEMPLATE_COREGISTRATION>", coreg_templ)
            sed_inplace(output_template, "<CALC_SURFACES>", str(calc_surfaces))
            sed_inplace(output_template, "<TIV_FILE>", icv_file)
            sed_inplace(output_template, "<N_PROC>", str(num_proc))

            resample_string = ""
            if calc_surfaces == 1:
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.data_surf(1) = cfg_dep('CAT12: Segmentation: Left Thickness',substruct('.', 'val', '{}', {1}, '.', 'val','{}', {1}, '.', 'val', '{}', {1},'.', 'val', '{}', {1}),substruct('()', {1}, '.', 'lhthickness','()', {':'}));\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.merge_hemi = 1;\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.mesh32k = 1;\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.fwhm_surf = 15;\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.nproc = " + str(num_proc) + ";\n"

            sed_inplace(output_template, "<SURF_RESAMPLE>", resample_string)

            sed_inplace(output_start, "X", "1")
            sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

            call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], log)

            if use_existing_nii is False:
                imrm([inputimage + ".nii"])

            log.close()

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)


    def mpr_cat_segment_check(self,calc_surfaces=0):
        icv_file                = os.path.join(self.t1_cat_dir, "tiv_" + self.label + ".txt")

        if os.path.exists(os.path.join(self.t1_cat_dir, "report", "cat_T1_" + self.label + ".xml")) is False:
            print("Error in mpr_cat_segment_check of subj " + self.label + ", CAT REPORT is missing")
            return False

        if os.path.exists(icv_file) is False:
            print("Error in mpr_cat_segment_check of subj " + self.label + ", ICV_FILE is missing")
            return False

        if os.path.getsize(icv_file) == 0:
            print("Error in mpr_cat_segment_check of subj " + self.label + ", ICV_FILE is empty")
            return False

        if calc_surfaces > 0:

            if os.path.exists(os.path.join(self.t1_cat_surface_dir, "lh.thickness.T1_" + self.label)) is False:
                print("Error in mpr_cat_segment_check of subj " + self.label + ", lh thickness is missing")
                return False

            if os.path.exists(self.t1_cat_resampled_surface) is False:
                print("Error in mpr_cat_segment_check of subj " + self.label + ", RESAMPLED SURFACE is missing")
                return False

        return True

    # longitudinal segment T1 with CAT and create  WM+GM mask (CSF is not created)
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    def mpr_cat_segment_longitudinal(self,
                        sessions,
                        odn="anat", imgtype=1,
                        do_overwrite=False,
                        do_bet_overwrite=False,
                        add_bet_mask=True,
                        set_origin=False,
                        seg_templ="",
                        coreg_templ="",
                        calc_surfaces=0,
                        num_proc=1,
                        use_existing_nii=True,
                        spm_template_name="cat_segment_longitudinal_customizedtemplate_tiv_smooth"
                        ):

        current_session = self.sessid
        # define placeholder variables for input dir and image name

        if seg_templ == "":
            seg_templ = self._global.spm_tissue_map
        else:
            if imtest(seg_templ) is False:
                print("ERROR in mpr_cat_segment: given template segmentation is not present")
                return

        if coreg_templ == "":
            coreg_templ = self._global.cat_dartel_template
        else:
            if imtest(coreg_templ) is False:
                print("ERROR in mpr_cat_segment: given template coregistration is not present")
                return

        # set dirs
        spm_script_dir          = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir           = os.path.join(spm_script_dir, "batch")
        in_script_template      = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start         = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template         = os.path.join(out_batch_dir, self.label + "_" + spm_template_name + "_job.m")
        output_start            = os.path.join(out_batch_dir, "start_" + self.label + "_" + spm_template_name + ".m")

        copyfile(in_script_template, output_template)
        copyfile(in_script_start, output_start)

        try:

            logfile = os.path.join(self.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(out_batch_dir   , exist_ok = True)

            images_string       = ""
            images_list         = []

            # create images list
            for sess in sessions:

                subj = self.get_sess_file_system(sess)

                if imgtype == 1:
                    anatdir = os.path.join(subj.t1_dir, odn)
                    T1 = "T1"
                elif imgtype == 2:
                    anatdir = os.path.join(subj.t2_dir, odn)
                    T1 = "T2"
                else:
                    print("ERROR: PD input format is not supported")
                    return False

                srcinputimage   = os.path.join(anatdir, T1 + "_biascorr")
                inputimage      = os.path.join(subj.t1_cat_dir, T1 + "_" + subj.label)
                brain_mask      = os.path.join(subj.t1_cat_dir, "brain_mask.nii.gz")

                # check whether skipping
                if imtest(brain_mask) is True and do_overwrite is False:
                    return

                os.makedirs(subj.t1_cat_dir, exist_ok=True)

                # I may want to process with cat after having previously processed without having set image's origin.
                # thus I may have created a nii version in the cat_proc folder , with the origin properly set
                # unzip T1_biascorr.nii.gz -> nii in cat folder only if nii is absent or I want to overwrite it.
                if use_existing_nii is False:
                    if os.path.exists(srcinputimage + ".nii.gz") is True:
                        gunzip(srcinputimage + ".nii.gz", inputimage + ".nii")
                    else:
                        print("Error in subj: " + self.label + ", method: mpr_cat_segment, biascorr image is absent")
                else:
                    if os.path.exists(inputimage + ".nii") is False:
                        print("Error in subj: " + self.label + ", method: mpr_cat_segment, given image in cat folder is absent")

                # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
                if set_origin is True:
                    input("press keyboard when finished setting the origin for subj " + subj.label + " :")

                images_string = images_string + "'" + inputimage + ".nii,1'\n"
                images_list.append(inputimage + ".nii")


            sed_inplace(output_template, "<T1_IMAGES>", images_string)
            sed_inplace(output_template, "<TEMPLATE_SEGMENTATION>", seg_templ)
            sed_inplace(output_template, "<TEMPLATE_COREGISTRATION>", coreg_templ)
            sed_inplace(output_template, "<CALC_SURFACES>", str(calc_surfaces))
            sed_inplace(output_template, "<N_PROC>", str(num_proc))

            sed_inplace(output_start, "X", "1")
            sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

            eng = call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], log, endengine=False)

            if calc_surfaces == 1:
                for sess in sessions:
                    self.mpr_cat_surf_resample(sess, num_proc, isLong=True, endengine=False, eng=eng)

            for sess in sessions:
                self.mpr_cat_tiv_calculation(sess, isLong=True, endengine=False, eng=eng)

            if use_existing_nii is False:
                imrm([images_list])

            eng.quit()
            log.close()

            self.sessid = current_session

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    # the above scripts often fails after having correctly segmented the image and calculated the lh.thickness.rT1_XXXX image
    def mpr_cat_surfaces_complete_longitudinal(self, sessions, num_proc=1):

        try:
            for sess in sessions:
                self.mpr_cat_surf_resample(sess, num_proc, isLong=True, endengine=False)

            for sess in sessions:
                self.mpr_cat_tiv_calculation(sess, isLong=True)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def mpr_cat_segment_longitudinal_check(self, sessions, calc_surfaces=0):

        err = ""

        for sess in sessions:

            subj        = self.get_sess_file_system(sess)

            icv_file    = os.path.join(subj.t1_cat_dir, "tiv_r_" + subj.label + ".txt")
            report_file = os.path.join(subj.t1_cat_dir, "report", "cat_rT1_" + subj.label + ".xml")

            if os.path.exists(report_file) is False:
                err     = err + "Error in mpr_cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", CAT REPORT is missing" + "\n"

            if os.path.exists(icv_file) is False:
                err     = err + "Error in mpr_cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", ICV_FILE is missing" + "\n"
            else:
                if os.path.getsize(icv_file) == 0:
                    err     = err + "Error in mpr_cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", ICV_FILE is empty" + "\n"

            if calc_surfaces > 0:

                if os.path.exists(os.path.join(subj.t1_cat_surface_dir, "lh.thickness.rT1_" + subj.label)) is False:
                    err     = err + "Error in mpr_cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", lh thickness is missing" + "\n"

                if os.path.exists(subj.t1_cat_resampled_surface_longitudinal) is False:
                    err     = err + "Error in mpr_cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", RESAMPLED SURFACE is missing" + "\n"

        if err != "":
            print(err)

        return err

    def mpr_cat_surf_resample(self, session=1, num_proc=1, isLong=False, mesh32k=1, endengine=True, eng=None):

        spm_template_name       = "mpr_cat_surf_resample"
        # set dirs
        spm_script_dir          = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir           = os.path.join(spm_script_dir, "batch")
        in_script_start         = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template         = os.path.join(out_batch_dir, self.label + "_" + spm_template_name + "_job.m")
        output_start            = os.path.join(out_batch_dir, "start_" + self.label + "_" + spm_template_name + ".m")

        copyfile(in_script_start, output_start)

        subj = self.get_sess_file_system(session)

        surf_prefix = "T1"
        if isLong is True:
            surf_prefix = "rT1"
        surface = os.path.join(subj.t1_cat_dir, "surf", "lh.thickness." + surf_prefix + "_" + subj.label)

        resample_string = ""
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.data_surf = {'" + surface + "'};\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.merge_hemi = 1;\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.mesh32k = " + str(mesh32k) + ";\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.fwhm_surf = 15;\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.nproc = " + str(num_proc) + ";\n"

        write_text_file(output_template, resample_string)
        sed_inplace(output_start, "X", "1")
        sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

        call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine, eng=eng)


    def mpr_cat_tiv_calculation(self, session=1, isLong=False, endengine=True, eng=None):

        spm_template_name       = "mpr_cat_tiv_calculation"
        # set dirs
        spm_script_dir          = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir           = os.path.join(spm_script_dir, "batch")
        in_script_start         = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template         = os.path.join(out_batch_dir, self.label + "_" + spm_template_name + "_job.m")
        output_start            = os.path.join(out_batch_dir, "start_" + self.label + "_" + spm_template_name + ".m")

        copyfile(in_script_start, output_start)

        subj = self.get_sess_file_system(session)

        prefix = "cat_T1_"
        prefix_tiv = "tiv_"
        if isLong is True:
            prefix = "cat_rT1_"
            prefix_tiv = "tiv_r_"

        report_file = os.path.join(subj.t1_cat_dir, "report", prefix + subj.label + ".xml")
        tiv_file    = os.path.join(subj.t1_cat_dir, prefix_tiv + subj.label + ".txt")

        tiv_string = ""
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.data_xml = {'" + report_file + "'};\n"
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.calcvol_TIV = 1;\n"
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.calcvol_name = '" + tiv_file + "';\n"

        write_text_file(output_template, tiv_string)
        sed_inplace(output_start, "X", "1")
        sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

        call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine, eng=eng)


    def mpr_spm_tissue_volumes(self, spm_template_name="spm_icv_template", endengine=True, eng=None):

        seg_mat                = os.path.join(self.t1_spm_dir, "T1_biascorr_" + self.label + "_seg8.mat")
        icv_file                = os.path.join(self.t1_spm_dir, "icv_" + self.label + ".dat")

        # set dirs
        spm_script_dir          = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir           = os.path.join(spm_script_dir, "batch")
        in_script_template      = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start         = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template         = os.path.join(out_batch_dir, self.label + "_" + spm_template_name + "_job.m")
        output_start            = os.path.join(out_batch_dir, "start_" + self.label + "_" + spm_template_name + ".m")

        copyfile(in_script_template, output_template)
        copyfile(in_script_start, output_start)

        sed_inplace(output_template, "<SEG_MAT>", seg_mat)
        sed_inplace(output_template, "<ICV_FILE>", icv_file)
        sed_inplace(output_start, "X", "1")
        sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

        call_matlab_spmbatch(output_start, [self._global.spm_functions_dir], endengine=False, eng=eng)


    def mpr_surf_resampled_longitudinal_diff(self, sessions, outdir="", matlab_func="subtract_gifti"):

        if len(sessions) is not 2:
            print("Error in mpr_surf_resampled_longitudinal_diff...given sessions are not 2")
            return

        if outdir == "":
            outdir = self.t1_cat_surface_dir

        out_str = ""
        surfaces = []
        for sess in sessions:
            subj        = self.get_sess_file_system(sess)
            out_str     = out_str + str(sess) + "_"
            surfaces.append(subj.t1_cat_resampled_surface_longitudinal)

        res_surf = os.path.join(outdir, "surf_resampled_sess_" + out_str + self.label + ".gii")

        call_matlab_function_noret(matlab_func, [self._global.spm_functions_dir], "\"" + surfaces[1] + "\",  \"" + surfaces[0] + "\", \"" + res_surf + "\"")

    def mpr_postbet(self,
                    odn="anat", imgtype=1, smooth=10,
                    betfparam=0.5,
                    do_reg=True, do_nonlinreg=True,
                    do_seg=True,
                    do_cleanup=True, do_strongcleanup=False, do_overwrite=False,
                    use_lesionmask=False, lesionmask="lesionmask"
                    ):
        niter = 5
        logfile = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # check anatomical image imgtype
        if imgtype is not 1:
            if do_nonlinreg is True:
                print(
                    "ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
                return False

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage  = self.t1_data
            anatdir     = os.path.join(self.t1_dir, odn)
            T1          = "T1"
            T1_label    = "T1"
        elif imgtype == 2:
            inputimage  = self.t2_data
            anatdir     = os.path.join(self.t2_dir, odn)
            T1          = "T2"
            T1_label    = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1              = os.path.join(anatdir, T1)  # T1 is now an absolute path
        lesionmask      = os.path.join(anatdir, lesionmask)
        lesionmaskinv   = os.path.join(anatdir, lesionmask + "inv")

        # check original image presence, otherwise exit
        if imtest(inputimage) is False:
            print("ERROR: input anatomical image is missing....exiting")
            return False

        # check given lesionmask presence, otherwise exit
        if use_lesionmask is True and imtest(lesionmask) is False:
            print("ERROR: given Lesion mask is missing....exiting")
            return False

        # I CAN START PROCESSING !
        try:

            betopts = "-f " + str(betfparam)

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            # os.chdir(anatdir)

            # init or append log file
            if os.path.isfile(logfile):
                with open(logfile, "a") as text_file:
                    print("******************************************************************", file=text_file)
                    print("updating directory", file=text_file)
                    print(" ", file=text_file)
            else:
                with open(logfile, "w") as text_file:
                    # some initial reporting for the log file
                    print("Script invoked from directory = " + os.getcwd(), file=text_file)
                    print("Output directory " + anatdir, file=text_file)
                    print("Input image is " + inputimage, file=text_file)
                    print(" " + anatdir, file=text_file)

            log = open(logfile, "a")

            #### TISSUE-TYPE SEGMENTATION (uses the t1_brain whichever created, not necessarly the bet one.)
            # required input: T1_biascorr + label-t1_brain + label-t1_brain_mask
            # output:  T1_biascorr (modified) + T1_biascorr_brain (modified) + T1_fast* (as normally output by fast) + T1_fast_bias (modified)
            if imtest(T1 + "_fast_pve_1") is False or do_overwrite is True:
                if do_seg is True:

                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.label + " :Performing tissue-imgtype segmentation")
                    rrun("fslmaths " + self.t1_brain_data + " -mas " + lesionmaskinv + " " + T1 + "_biascorr_maskedbrain", logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " " + T1 + "_biascorr_maskedbrain", logFile=log)
                    immv(T1 + "_biascorr", T1 + "_biascorr_init", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_restore " + T1 + "_biascorr_brain", logFile=log)                         # overwrite brain

                    # extrapolate bias field and apply to the whole head image
                    # rrun("fslmaths " + T1 + "_biascorr_brain_mask -mas " + lesionmaskinv + " " + T1 + "_biascorr_brain_mask2", logFile=log)
                    rrun("fslmaths " + self.t1_brain_data_mask + " -mas " + lesionmaskinv + " " + T1 + "_biascorr_brain_mask2", logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_restore -mas " + T1 + "_biascorr_brain_mask2 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_biascorr_brain_mask2 -o " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_biascorr_brain_mask2 -dilall -add 1 " + T1 + "_fast_bias # alternative to fslsmoothfill", logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_bias " + T1 + "_biascorr", logFile=log)    # overwrite full image

                    imcp(T1 + "_biascorr_brain", self.t1_brain_data)
                    imcp(T1 + "_biascorr", self.t1_data)

                    if do_nonlinreg is True:

                        # regenerate the standard space version with the new bias field correction applied
                        if imtest(T1 + "_to_MNI_nonlin_field") is True:
                            rrun("applywarp -i " + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_field -r " + os.path.join(self.fsl_data_standard_dir,"MNI152_" + T1_label + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline",logFile=log)
                        else:
                            if imtest(os.path.join(self.roi_standard_dir, "highres2standard_warp")) is True:
                                rrun("applywarp -i " + T1 + "_biascorr -w " + os.path.join(self.roi_standard_dir, "highres2standard_warp") + " -r " + os.path.join(self.fsl_data_standard_dir,"MNI152_" + T1_label + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline",logFile=log)
                            else:
                                print("WARNING in mpr_postbet: either " + T1 + "_to_MNI_nonlin_field" + " or " + os.path.join(self.roi_standard_dir, "highres2standard_warp") + " is missing")

            #### SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION (only done if registration turned on, and segmentation done, and it is a T1 image)
            # required inputs: " + T1 + "_biascorr
            # output: " + T1 + "_vols.txt
            if os.path.isfile(T1 + "_vols.txt") is False or do_overwrite is True:

                if do_reg is True and do_seg is True and T1_label == "T1":
                    print(self.label + " :Skull-constrained registration (linear)")

                    rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_bet -s -m " + betopts, logFile=log)
                    rrun("pairreg " + os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain") + " " + T1 + "_biascorr_bet " + os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_skull") + " " + T1 + "_biascorr_bet_skull " + T1 + "2std_skullcon.mat", logFile=log)

                    if use_lesionmask is True:
                        rrun("fslmaths " + lesionmask + " -max " + T1 + "_fast_pve_2 " + T1 + "_fast_pve_2_plusmask -odt float", logFile=log)
                        # ${FSLDIR}/bin/fslmaths lesionmask -bin -mul 3 -max " + T1 + "_fast_seg " + T1 + "_fast_seg_plusmask -odt int

                    vscale = float(runpipe("avscale " + T1 + "2std_skullcon.mat | grep Determinant | awk '{ print $3 }'", logFile=log)[0].decode("utf-8").split("\n")[0])
                    ugrey  = float(runpipe("fslstats " + T1 + "_fast_pve_1 -m -v | awk '{ print $1 * $3 }'", logFile=log)[0].decode("utf-8").split("\n")[0])
                    uwhite = float(runpipe("fslstats " + T1 + "_fast_pve_2 -m -v | awk '{ print $1 * $3 }'", logFile=log)[0].decode("utf-8").split("\n")[0])

                    ngrey  = ugrey * vscale
                    nwhite = uwhite * vscale
                    ubrain = ugrey + uwhite
                    nbrain = ngrey + nwhite

                    with open(T1 + "_vols.txt", "w") as file_vol:
                        print( "Scaling factor from " + T1 + " to MNI (using skull-constrained linear registration) = " + str(vscale), file=file_vol)
                        print( "Brain volume in mm^3 (native/original space) = " + str(ubrain), file=file_vol)
                        print( "Brain volume in mm^3 (normalised to MNI) = " + str(nbrain), file=file_vol)

            #### CLEANUP
            if do_cleanup is True:
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning up intermediate files"
                rrun("imrm " + T1 + "_biascorr_bet_mask " + T1 + "_biascorr_bet " + T1 + "_biascorr_brain_mask2 " + T1 + "_biascorr_init " + T1 + "_biascorr_maskedbrain " + T1 + "_biascorr_to_std_sub " + T1 + "_fast_bias_idxmask " + T1 + "_fast_bias_init " + T1 + "_fast_bias_vol2 " + T1 + "_fast_bias_vol32 " + T1 + "_fast_totbias " + T1 + "_hpf* " + T1 + "_initfast* " + T1 + "_s20 " + T1 + "_initmask_s20", logFile=log)

            #### STRONG CLEANUP
            if do_strongcleanup is True:
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning all unnecessary files "
                rrun("imrm " + T1 + " " + T1 + "_orig " + T1 + "_fullfov", logFile=log)

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def mpr_finalize(self, odn="anat", imgtype=1):

        logfile     = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir      = os.getcwd()

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir     = os.path.join(self.t1_dir, odn)
            T1          = "T1"
            T1_label    = "T1"
        elif imgtype == 2:
            anatdir     = os.path.join(self.t2_dir, odn)
            T1          = "T2"
            T1_label    = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1              = os.path.join(anatdir, T1)  # T1 is now an absolute path
        # ==================================================================================================================================================================
        #### move and rename files according to myMRI system
        print("----------------------------------- starting t1_post_processing of subject " + self.label)
        try:
            log = open(logfile, "a")
            print("******************************************************************", file=log)
            print("starting t1_post_processing", file=log)
            print("******************************************************************", file=log)

            run_notexisting_img(self.t1_data + "_orig", "immv " + self.t1_data + " " + self.t1_data + "_orig", logFile=log)
            run_notexisting_img(self.t1_data, "imcp " + T1 + "_biascorr " + self.t1_data, logFile=log)
            run_notexisting_img(self.t1_brain_data, "imcp " + T1 + "_biascorr_brain " + self.t1_brain_data, logFile=log)
            run_notexisting_img(self.t1_brain_data + "_mask", "imcp " + T1 + "_biascorr_brain_mask " + self.t1_brain_data + "_mask", logFile=log)

            os.makedirs(self.fast_dir, exist_ok=True)

            mass_images_move(os.path.join(anatdir, "*fast*"), self.fast_dir, logFile=log)

            run_notexisting_img(T1 + "_fast_pve_1", "imcp " + os.path.join(self.fast_dir, T1_label + "_fast_pve_1 " + anatdir), logFile=log) # this file is tested by subject_t1_processing to skip the fast step. so by copying it back, I allow such skip.

            run_notexisting_img(self.t1_segment_csf_path, "fslmaths " + os.path.join(self.fast_dir, T1_label + "_fast_seg") + " -thr 1 -uthr 1 " + self.t1_segment_csf_path, logFile=log)
            run_notexisting_img(self.t1_segment_gm_path , "fslmaths " + os.path.join(self.fast_dir, T1_label + "_fast_seg") + " -thr 2 -uthr 2 " + self.t1_segment_gm_path, logFile=log)
            run_notexisting_img(self.t1_segment_wm_path , "fslmaths " + os.path.join(self.fast_dir, T1_label + "_fast_seg") + " -thr 3 " + self.t1_segment_wm_path, logFile=log)

            run_notexisting_img(self.t1_segment_csf_ero_path, "fslmaths " + os.path.join(self.fast_dir, T1_label + "_fast_pve_0 -thr 1 -uthr 1 " + self.t1_segment_csf_ero_path), logFile=log)
            run_notexisting_img(self.t1_segment_wm_bbr_path , "fslmaths " + os.path.join(self.fast_dir, T1_label + "_fast_pve_2 -thr 0.5 -bin " + self.t1_segment_wm_bbr_path), logFile=log)
            run_notexisting_img(self.t1_segment_wm_ero_path , "fslmaths " + os.path.join(self.fast_dir, T1_label + "_fast_pve_2 -ero " + self.t1_segment_wm_ero_path), logFile=log)

            mass_images_move(os.path.join(anatdir, "*_to_MNI*"), self.roi_standard_dir, logFile=log)
            mass_images_move(os.path.join(anatdir, "*_to_T1*"), self.roi_t1_dir, logFile=log)

            run_move_notexisting_img(os.path.join(self.roi_t1_dir, "standard2highres_warp"), "immv " + os.path.join(self.roi_t1_dir, "MNI_to_T1_nonlin_field") + " " +  os.path.join(self.roi_t1_dir, "standard2highres_warp"), logFile=log)
            run_move_notexisting_img(os.path.join(self.roi_standard_dir, "highres2standard_warp"), "immv " + os.path.join(self.roi_standard_dir, "T1_to_MNI_nonlin_field") + " " +  os.path.join(self.roi_standard_dir, "highres2standard_warp"), logFile=log)

            # first has been removed from the standard t1_processing pipeline
            # mkdir -p $FIRST_DIR
            # run mv first_results $FIRST_DIR
            # run $FSLDIR/bin/immv ${T1}_subcort_seg $FIRST_DIR

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def mpr_first(self, structures="", t1_image="", odn=""):

        logfile     = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir      = os.getcwd()

        # init params
        if t1_image == "":
            t1_image = self.t1_brain_data

        if structures != "":
            structs = "-s " + structures
            list_structs = structures.split(",")
        else:
            list_structs = []
            structs = ""

        output_roi_dir  = os.path.join(self.roi_t1_dir, odn)
        temp_dir        = os.path.join(self.first_dir, "temp")

        filename = remove_ext(t1_image)
        t1_image_label = os.path.basename(filename)

        try:
            os.makedirs(self.first_dir, exist_ok=True)
            os.makedirs(output_roi_dir, exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)

            # os.chdir(temp_dir)

            log = open(logfile, "a")

            print("******************************************************************", file=log)
            print("starting FIRST processing", file=log)
            print("******************************************************************", file=log)

            print(self.label + ": FIRST (of " + t1_image_label + " " +  structs + " " + odn + ")")

            image_label_path = os.path.join(self.first_dir, t1_image_label)

            rrun("first_flirt " + t1_image + " " + image_label_path + "_to_std_sub", logFile=log)
            rrun("run_first_all -i " + t1_image + " - o " + image_label_path + " -d -a " + image_label_path + "_to_std_sub.mat -b " + structs, logFile=log)

            for struct in list_structs:
                immv(image_label_path + "-" + struct + "_first.nii.gz", os.path.join(output_roi_dir, "mask_" + struct + "_highres.nii.gz"), logFile=log)

            #	#### SUB-CORTICAL STRUCTURE SEGMENTATION (done in subject_t1_first)
            #	# required input: " + T1 + "_biascorr
            #	# output: " + T1 + "_first*
            #	if imtest( " + T1 + "_subcort_seg` = 0 -o $do_overwrite = yes ]; then
            #		if [ $do_subcortseg = yes ] ; then
            #				print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Performing subcortical segmentation"
            #				# Future note, would be nice to use " + T1 + "_to_MNI_lin.mat to initialise first_flirt
            #				ffopts=""
            #				if [ $use_lesionmask = yes ] ; then ffopts="$ffopts -inweight lesionmaskinv" ; fi
            #				run $FSLDIR/bin/first_flirt " + T1 + "_biascorr " + T1 + "_biascorr_to_std_sub $ffopts
            #				run mkdir -p first_results
            #				run $FSLDIR/bin/run_first_all $firstreg -i " + T1 + "_biascorr -o first_results/" + T1 + "_first -a " + T1 + "_biascorr_to_std_sub.mat
            #				# rather complicated way of making a link to a non-existent file or files (as FIRST may run on the cluster) - the alernative would be fsl_sub and job holds...
            #				names=`$FSLDIR/bin/imglob -extensions " + T1 + "`;
            #				for fn in $names;
            #				do
            #					ext=`print( $fn | sed "s/" + T1 + ".//"`;
            #				  run cp -r first_results/" + T1 + "_first_all_fast_firstseg.${ext} " + T1 + "_subcort_seg.${ext}
            #				done
            #		fi
            #	fi

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    # FreeSurfer recon-all
    def mpr_fs_reconall(self, step="-all", do_overwrite=False, backtransfparams=" RL PA IS "):

        # check whether skipping
        if step == "-all" and imtest(os.path.join(self.t1_dir, "freesurfer", "aparc+aseg.nii.gz")) is True and do_overwrite is False:
            return

        if step == "-autorecon1" and imtest(os.path.join(self.t1_dir, "freesurfer", "mri", "brainmask.mgz")) is True and do_overwrite is False:
            return

        try:
            logfile = os.path.join(self.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            curdir = os.getcwd()

            rrun("mri_convert " + self.t1_data + ".nii.gz " + self.t1_data + ".mgz", logFile=log)

            os.environ['OLD_SUBJECTS_DIR'] = os.environ['SUBJECTS_DIR']
            os.environ['SUBJECTS_DIR'] = self.t1_dir

            rrun("recon-all -subject freesurfer" + " -i " + self.t1_data + ".mgz " + step, logFile=log)

            # calculate linear trasf to move coronal-conformed T1 back to original reference (specified by backtransfparams)
            # I convert T1.mgz => nii.gz, then I swapdim to axial and coregister to t1_data
            rrun("mri_convert " + self.t1_fs_data + ".mgz " + self.t1_fs_data + ".nii.gz")
            rrun("fslswapdim " + self.t1_fs_data + ".nii.gz" + backtransfparams + self.t1_fs_data + "_orig.nii.gz")
            rrun("flirt -in " + self.t1_fs_data + "_orig.nii.gz" + " -ref " + self.t1_data + " -omat " + os.path.join(self.t1_fs_mri_dir,"fscor2t1.mat") + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")
            imrm([self.t1_fs_data + ".nii.gz", self.t1_fs_data + "_orig.nii.gz"])

            if step == "-all":
                rrun("mri_convert " + os.path.join(self.t1_dir, "freesurfer", "mri", "aparc+aseg.mgz") + " " + os.path.join(self.t1_dir, "freesurfer", "aparc+aseg.nii.gz"), logFile=log)
                rrun("mri_convert " + os.path.join(self.t1_dir, "freesurfer", "mri", "aseg.mgz") + " "       + os.path.join(self.t1_dir, "freesurfer", "aseg.nii.gz"), logFile=log)
                os.system("rm " + self.dti_data + ".mgz")

            os.environ['SUBJECTS_DIR'] = os.environ['OLD_SUBJECTS_DIR']

        except Exception as e:
            traceback.print_exc()
            # log.close()
            print(e)

    # check whether substituting bet brain with the one created by freesurfer.
    # fs mask is usually bigger then fsl/spm brain, so may need some erosion
    # since the latter op create holes within the image. I create a mask with the latter and the bet mask (which must be coregistered since fs ones are coronal)
    def mpr_use_fs_brainmask(self, backtransfparams=" RL PA IS ", erosiontype=" -kernel boxv 5 ", is_interactive=True, do_clean=True):

        # convert fs brainmask to nii.gz => move to the same orientation as working image (usually axial) => erode it
        rrun("mri_convert " + self.t1_fs_brainmask_data + ".mgz " + self.t1_fs_brainmask_data + ".nii.gz")
        rrun("fslswapdim " + self.t1_fs_brainmask_data + ".nii.gz" + backtransfparams + self.t1_fs_brainmask_data + "_orig.nii.gz")
        rrun("fslmaths " + self.t1_fs_brainmask_data + "_orig.nii.gz" + erosiontype + " -ero " + self.t1_fs_brainmask_data + "_orig_ero.nii.gz")

        if is_interactive is True:
            rrun("fsleyes " + self.t1_data + " " + self.t1_brain_data + " " + self.t1_fs_brainmask_data + "_orig_ero.nii.gz")

            do_substitute = input("do you want to substitute bet image with this one? press y or n\n : ")

            if do_substitute == "y":
                self.mpr_use_fs_brainmask_exec(do_clean)

        else:
            self.mpr_use_fs_brainmask_exec(do_clean)

        if do_clean is True:
            imrm([self.t1_fs_brainmask_data + ".nii.gz", self.t1_fs_brainmask_data + "_orig.nii.gz", self.t1_fs_brainmask_data + "_orig_ero.nii.gz"])

    def mpr_use_fs_brainmask_exec(self, do_clean=True):

        # I may have manually edited self.t1_fs_brainmask + "_orig_ero.nii.gz"
        # although is at the same reference as working image, it still have to be co-registered
        # 1) I move this orig brainmask to the same space as t1 and t1_brain, applying the coronalconformed->original transformation to eroded brainmask_orig
        rrun("flirt -in " + self.t1_fs_brainmask_data + "_orig_ero.nii.gz" + " -ref " + self.t1_data + " -out " + self.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -applyxfm -init " + os.path.join(self.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

        # => I create its mask (with holes) and add to the bet's one (assumed as smaller but without holes)
        rrun("fslmaths " + self.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -bin -add " + self.t1_brain_data_mask + " -bin " + self.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz")

        imcp(self.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz", self.t1_brain_data_mask)  # substitute bet mask with this one
        rrun("fslmaths " + self.t1_data + " -mas " + self.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz" + " " + self.t1_brain_data)

        if do_clean is True:
            imrm([self.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz"])

    # check whether substituting bet brain with the one created by SPM-segment.
    # since the SPM GM+WM mask contains holes within the image. I create a mask with the latter and the bet mask (which must be coregistered since fs ones are coronal)
    def mpr_use_spm_brainmask(self, backtransfparams=" RL PA IS ", erosiontype=" -kernel boxv 5 ", is_interactive=True, do_clean=True):

        # convert fs brainmask to nii.gz => move to the same orientation as working image (usually axial) => erode it
        rrun("mri_convert " + self.t1_fs_brainmask_data + ".mgz " + self.t1_fs_brainmask_data + ".nii.gz")
        rrun("fslswapdim " + self.t1_fs_brainmask_data + ".nii.gz" + backtransfparams + self.t1_fs_brainmask_data + "_orig.nii.gz")
        rrun("fslmaths " + self.t1_fs_brainmask_data + "_orig.nii.gz" + erosiontype + " -ero " + self.t1_fs_brainmask_data + "_orig_ero.nii.gz")

        if is_interactive is True:
            rrun("fsleyes " + self.t1_data + " " + self.t1_brain_data + " " + self.t1_fs_brainmask_data + "_orig_ero.nii.gz")

            do_substitute = input("do you want to substitute bet image with this one? press y or n\n : ")

            if do_substitute == "y":
                self.mpr_use_spm_brainmask_exec(do_clean)

        else:
            self.mpr_use_spm_brainmask_exec(do_clean)

        if do_clean is True:
            imrm([self.t1_fs_brainmask_data + ".nii.gz", self.t1_fs_brainmask_data + "_orig.nii.gz", self.t1_fs_brainmask_data + "_orig_ero.nii.gz"])

    def mpr_use_spm_brainmask_exec(self, do_clean=True):

        # I may have manually edited self.t1_fs_brainmask + "_orig_ero.nii.gz"
        # although is at the same reference as working image, it still have to be co-registered
        # 1) I move this orig brainmask to the same space as t1 and t1_brain, applying the coronalconformed->original transformation to eroded brainmask_orig
        rrun("flirt -in " + self.t1_fs_brainmask_data + "_orig_ero.nii.gz" + " -ref " + self.t1_data + " -out " + self.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -applyxfm -init " + os.path.join(self.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

        # => I create its mask (with holes) and add to the bet's one (assumed as smaller but without holes)
        rrun("fslmaths " + self.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -bin -add " + self.t1_brain_data_mask + " -bin " + self.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz")

        imcp(self.t1_fs_brainmask_data + "_axial_ero_mask.nii.gz", self.t1_brain_data_mask)  # substitute bet mask with this one
        rrun("fslmaths " + self.t1_data + " -mas " + self.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz" + " " + self.t1_brain_data)

        if do_clean is True:
            imrm([self.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz"])

    # copy bet, spm and fs extracted brain to given directory
    def mpr_compare_brain_extraction(self, tempdir, backtransfparams=" RL PA IS "):

        # bet
        imcp(os.path.join(self.t1_anat_dir, "T1_biascorr_brain"), os.path.join(tempdir, self.label + "_bet.nii.gz"))

        # spm (assuming bet mask is smaller than spm's one and the latter contains holes...I make their union to mask the t1
        if imtest(os.path.join(self.t1_spm_dir, "brain_mask")) is True:
            rrun("fslmaths " + os.path.join(self.t1_spm_dir, "brain_mask") + " -add " + self.t1_brain_data_mask + " " + os.path.join(tempdir, self.label + "_bet_spm_mask"))
            rrun("fslmaths " + self.t1_data + " -mas " + os.path.join(tempdir,self.label + "_bet_spm_mask") + " " + os.path.join(tempdir, self.label + "_spm"))
            imrm([os.path.join(tempdir,self.label + "_bet_spm_mask")])
        else:
            print("subject " + self.label + " spm mask is not present")

        # freesurfer
        fsmask = os.path.join(self.t1_dir, "freesurfer", "mri", "brainmask")
        if imtest(fsmask) is True:
            rrun("mri_convert " + fsmask + ".mgz " + os.path.join(tempdir, self.label + "_brainmask.nii.gz"))

            rrun("fslswapdim " + os.path.join(tempdir, self.label + "_brainmask.nii.gz") + backtransfparams + os.path.join(tempdir, self.label + "_brainmask.nii.gz"))
            rrun("flirt -in " +  os.path.join(tempdir, self.label + "_brainmask.nii.gz") + " -ref " + self.t1_data + " -out " + os.path.join(tempdir, self.label + "_brainmask.nii.gz") + " -applyxfm -init " + os.path.join(self.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

            # rrun("fslmaths " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz") + " -bin " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz"))
            # rrun("fslmaths " + os.path.join(betdir, "T1_biascorr_brain") + " -mas " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz") + " " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz"))
        else:
            print("subject " + self.label + " freesurfer's brainmask is not present")

    # ==================================================================================================================================================
    # DIFFUSION
    # ==================================================================================================================================================

    def dti_ec_fit(self):

        if os.path.exist(self.dti_data) is False:
            return

        rrun("fslroi " + os.path.join(self.dti_data) + " " + self.dti_nodiff_data + " 0 1")
        rrun("bet " + self.dti_nodiff_data + " " + self.dti_nodiff_brain_data + " -m -f 0.3")   # also creates dti_nodiff_brain_mask_data

        if imtest(self.dti_ec_image) is False:
            print("starting eddy_correct on " + self.label)
            rrun("eddy_correct " + self.dti_data + " " + self.dti_ec_image + " 0")

        if os.path.exist(self.dti_rotated_bvec) is False:
            rrun("fdt_rotate_bvecs " + self.dti_bvec + " " + self.dti_rotated_bvec + " " + self.dti_data + ".ecclog")

        if imtest(self.dti_fit_data) is False:
            print("starting DTI fit on " + self.label)
            rrun("dtifit --sse -k " + self.dti_ec_data + " -o " + self.dti_fit_data + " -m " + self.dti_nodiff_brainmask_data + " -r " + self.dti_rotated_bvec + " -b " + self.dti_bval)

    def dti_probtrackx(self):
        pass

    def dti_bedpostx(self):
        pass

    def dti_bedpostx_gpu(self):
        pass

    def dti_conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass

    def dti_autoptx_tractography(self):
        pass

    # ==================================================================================================================================================
    # FUNCTIONAL
    # ==================================================================================================================================================
    # epi_spm_XXXXX are methods editing and lauching a SPM batch file

    # coregister epi (or a given image) to given volume of given image (usually the epi itself, the pepolar in case of distortion correction process)
    def epi_spm_motioncorrection(self, ref_vol=1, ref_image=None, epi2correct=None, spm_template_name="spm_fmri_realign_estimate_reslice_to_given_vol"):

        if ref_image is None:
            ref_image = self.epi_data
        else:
            if imtest(ref_image) is False:
                print ("Error in epi_spm_motioncorrection, given ref_image image is not valid....exiting")
                return

        if os.path.isfile(ref_image + ".nii.gz") and not os.path.isfile(ref_image + ".nii"):
            gunzip(ref_image + ".nii.gz", ref_image + ".nii")


        if epi2correct is None:
            epi2correct = self.epi_data
        else:
            if imtest(epi2correct) is False:
                print ("Error in epi_spm_motioncorrection, given epi2correct image is not valid....exiting")
                return

        if os.path.isfile(epi2correct + ".nii.gz") and not os.path.isfile(epi2correct + ".nii"):
            gunzip(epi2correct + ".nii.gz", epi2correct + ".nii")

        # 2.1: select the input spm template obtained from batch (we defined it in spm_template_name) + its run file …

        # set dirs
        spm_script_dir  = os.path.join(self.project.script_dir, "epi", "spm")
        out_batch_dir   = os.path.join(spm_script_dir, "batch")

        in_batch_start  = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
        in_batch_job    = os.path.join(self._global.spm_templates_dir, spm_template_name + '_job.m')

        # 2.1' … and establish location of output spm template + output run file:
        out_batch_job   = os.path.join(out_batch_dir, spm_template_name + self.label + '_job.m')
        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + self.label + '.m')

        os.makedirs(out_batch_dir, exist_ok=True)

        # 2.2: create "output spm template" by copying "input spm template" + changing general tags for our specific ones…
        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, '<REF_IMAGE,refvol>', ref_image + '.nii,' + str(ref_vol + 1))  # <-- i added 1 to ref_volume_pe bc spm counts the volumes from 1, not from 0 as FSL

        # 2.2' …now we want to select all the volumes from the epi file and insert that into the template:
        epi_nvols = int(rrun('fslnvols ' + epi2correct + '.nii'))
        epi_path_name = epi2correct + '.nii'
        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume = epi_path_name + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' + "'"

        sed_inplace(out_batch_job, '<TO_ALIGN_IMAGES,1-n_vols>', epi_all_volumes)

        # 2.3: run job --> create "output run spm template" by analogue process + call matlab and run it:
        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, 'X', '1')
        sed_inplace(out_batch_start, 'JOB_LIST', "\'" + out_batch_job + "\'")
        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir], endengine=False)

    def epi_get_closest_volume(self, ref_image_pe="", ref_volume_pe=-1):
        # will calculate the closest vol from self.epi_data to ref_image
        # Steps:
        # 0: get epi_pe central volume + unzip so SPM can use it
        # 1: merge all the sessions into one file ("_merged-sessions") + unzip so SPM can use it
        # 2: align all the volumes within merged file to epi_pe central volume (SPM12-Realign:Estimate)
        # 3: calculate the "less motion corrected" volume from the merged file with respect to the epi-pe in terms of rotation around x, y and z axis).

        if ref_image_pe is "":
            ref_image_pe = self.epi_pe_data

        if ref_volume_pe == -1:
            # 0
            epi_pe_nvols = int(rrun('fslnvols ' + ref_image_pe + '.nii.gz'))
            ref_volume_pe = epi_pe_nvols // 2

        # create temp folder, copy there epi and epi_pe, unzip and run mc (then I can simply remove it when ended)
        temp_distorsion_mc = os.path.join(self.epi_dir, "temp_distorsion_mc")
        os.makedirs(temp_distorsion_mc)
        temp_epi    = os.path.join(temp_distorsion_mc, self.epi_image_label)
        temp_epi_pe = os.path.join(temp_distorsion_mc, self.epi_image_label + "_pe")
        imcp(self.epi_data, temp_epi)
        imcp(ref_image_pe, temp_epi_pe)
        os.system('gzip -d -k ' + temp_epi_pe + '.nii.gz')
        os.system('gzip -d -k ' + temp_epi + '.nii.gz')
        self.epi_spm_motioncorrection(ref_volume_pe, temp_epi_pe, temp_epi, spm_template_name="spm_fmri_realign_estimate_to_given_vol")

        # 3: call matlab function that calculates best volume:
        best_vol = call_matlab_function("least_mov", [self._global.spm_functions_dir], "\"" + os.path.join(self.epi_dir, "temp_distorsion_mc", 'rp_' + self.label + '-epi_pe.txt' + "\""))[1]
        rmtree(temp_distorsion_mc)

        return best_vol

    # assumes opposite PE direction sequence is called label-epi_pe and acquisition parameters
    # - epi_ref_vol/pe_ref_vol =-1 means use the middle volume
    # 1: get number of volumes of epi_pe image in opposite phase-encoding direction and extract middle volume (add "_ref")
    # 2: look for the epi volume closest to epi_pe_ref volume
    # 3: merge the 2 ref volumes into one (add "_ref_merged")
    # 4: run topup using ref_merged, acq params; used_templates: "_topup"
    # 5: do motion correction with the chosen volume
    # 6: applytopup --> choose images whose distortion we want to correct
    def epi_pepolar_correction(self, motionfirst=True, epi_ref_vol=-1, ref_image_pe="", ref_volume_pe=-1):

        imcp(self.epi_data, self.epi_data + "_distorted") # this will refer to a file with all the sessions merged <--------!!

        # 1
        if ref_image_pe is "":
            ref_image_pe = self.epi_pe_data

        if ref_volume_pe == -1:
            nvols_pe = rrun("fslnvols " + ref_image_pe + '.nii.gz')
            central_vol_pe = int(nvols_pe) // 2
        else:
            central_vol_pe = ref_volume_pe

        rrun("fslselectvols -i " + ref_image_pe + " -o " + ref_image_pe + "_ref" + " --vols=" + str(central_vol_pe))

        # 2
        if epi_ref_vol == -1:
            central_vol = self.epi_get_closest_volume(ref_image_pe, ref_volume_pe)
        else:
            central_vol = epi_ref_vol

        rrun("fslselectvols -i " + self.epi_data + " -o " + self.epi_data + "_ref" + " --vols=" + str(central_vol))

        # 3
        rrun("fslmerge -t " + self.epi_data + "_PE_ref_merged" + " " + self.epi_data + "_ref" + " " + ref_image_pe + "_ref")
        # 4 —assumes merged epi volumes appear in the same order as acqparams.txt (--datain)
        rrun("topup --imain=" + self.epi_data + "_PE_ref_merged" + " --datain=" + self.epi_acq_params + " --config=b02b0.cnf --out=" + self.epi_data + "_PE_ref_topup" + " --iout=" + self.epi_data + "_PE_ref_topup_corrected")

        # 5 -motion correction using central_vol
        self.epi_spm_motioncorrection(central_vol)
        os.remove(self.epi_data + ".nii")               # remove old with-motion SUBJ-epi.nii
        os.remove(self.epi_data + ".nii.gz")            # remove old with-motion SUBJ-epi.nii.gz
        compress(self.epi_data_mc + ".nii", self.epi_data_mc + ".nii.gz", replace=True)    # zip rSUBJ-epi.nii => rSUBJ-epi.nii.gz

        # 6 —again these must be in the same order as --datain/acqparams.txt // "inindex=" values reference the images-to-correct corresponding row in --datain and --topup
        rrun("applytopup --imain=" + self.epi_data_mc + " --topup=" + self.epi_data + "_PE_ref_topup" + " --datain=" + self.epi_acq_params + " --inindex=1 --method=jac --interp=spline --out=" + self.epi_data_mc)

    def epi_get_slicetiming_params(self, nslices, scheme = 1, params=None):

        # =============Sequential ascending: 1=============
        if scheme == 1:
            params = arange(1, nslices + 1)

        # =============Sequential descending: 2=============
        elif scheme == 2:
            params = arange(nslices, 0, -1)

        # =============Interleaved ascending: 3=============
        elif scheme == 3:
            params = concatenate((arange(1, nslices + 1, 2), arange(2, nslices + 1, 2)))

        # =============Interleaved descending: 4=============
        elif scheme == 4:
            params = concatenate((arange(nslices, 0, -2), arange(nslices - 1, 0, -2)))

        elif scheme == 0:
            if params is None:
                print("error")
                return
            else:
                params = array(params)

        str_params = [ str(p) for p in params]
        return str_params

    def epi_remove_slices(self, numslice2remove=1, whichslices2remove="updown", remove_dimension="axial"):

        # dim_str = ""
        # if remove_dimension == "axial":
        #     dim_str = " -1 -1 "
        nslices = 36
        imcp(self.epi_data, self.epi_data + "full")
        # rrun('fslroi ' + self.epi_data + " " + self.epi_data + " -1 -1  1 35")
        rrun('fslroi ' + self.epi_data + " " + self.epi_data + " -1 -1  0 34")

    def epi_merge(self, premerge_labels):

        seq_string = " "
        for seq in premerge_labels:
            seq_string = seq_string + self.epi_data + "_" + seq + " "

        rrun('fslmerge -t ' + self.epi_data + " " + seq_string)

    def epi_split(self, subdirmame = ""):

        currdir = os.getcwd()
        outdir = os.path.join(self.epi_dir, subdirmame)
        os.makedirs(outdir, exist_ok=True)
        os.chdir(outdir)
        rrun('fslsplit ' + self.epi_data + " " + self.epi_image_label + "_" + " -t")
        os.chdir(currdir)

    def prepare_for_spm(self, subdirmame = "temp_split"):

        self.epi_split(subdirmame)
        outdir = os.path.join(self.epi_dir, subdirmame)
        os.chdir(outdir)
        for f in os.scandir():
            if f.is_file():
                gunzip(f.name, os.path.join(outdir, remove_ext(f.name) + ".nii"), replace=True)

    def epi_spm_fmri_preprocessing_motioncorrected(self , num_slices, TR , TA=-1 , acq_scheme=0, ref_slice = -1 , slice_timing = None):
        self.epi_spm_fmri_preprocessing(num_slices, TR, TA, acq_scheme, ref_slice, slice_timing, epi_image=self.epi_data_mc, spm_template_name='spm_fmri_preprocessing_norealign')

    def epi_spm_fmri_preprocessing(self, num_slices, TR, TA=-1, acq_scheme=0, ref_slice = -1, slice_timing = None, epi_image=None, spm_template_name='spm_fmri_preprocessing'):

        #default params:
        if epi_image is None:
            epi_image = self.epi_data
        else:
            if imtest(epi_image) is False:
                print("Error in subj: " + self.label + " epi_spm_fmri_preprocessing")
                return

        #TA - if not otherwise indicated, it assumes the acquisition is continuous and TA = TR - (TR/num slices)
        if TA == -1:
            TA = TR - (TR/num_slices)

        #takes central slice as a reference
        if ref_slice == -1:
             ref_slice = num_slices // 2 + 1

        #
        if slice_timing == None:
            slice_timing = self.epi_get_slicetiming_params(num_slices, acq_scheme)
        else:
            slice_timing = [str(p) for p in slice_timing]

        #set dirs
        in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + '_job.m')
        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        spm_script_dir = os.path.join(self.project.script_dir, "epi", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        out_batch_job = os.path.join(out_batch_dir, spm_template_name + self.label + '_job.m')
        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + self.label + '.m')

        #substitute for all the volumes + rest of params
        epi_nvols = int(rrun('fslnvols ' + epi_image + '.nii.gz'))
        epi_path_name = epi_image + '.nii'

        gunzip(epi_image + '.nii.gz', epi_path_name, replace=False)

        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume = epi_path_name + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' + "'"

        mean_image = os.path.join(self.epi_dir, "mean" + self.epi_image_label + ".nii")

        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)
        sed_inplace(out_batch_job, '<NUM_SLICES>', str(num_slices))
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<TA_VALUE>', str(TA))
        sed_inplace(out_batch_job, '<SLICETIMING_PARAMS>', ' '.join(slice_timing))
        sed_inplace(out_batch_job, '<REF_SLICE>', str(ref_slice))
        sed_inplace(out_batch_job, '<RESLICE_MEANIMAGE>', mean_image)
        sed_inplace(out_batch_job, '<T1_IMAGE>', self.t1_data + '.nii,1')
        sed_inplace(out_batch_job, '<SPM_DIR>', self._global.spm_dir)

        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, 'X', '1')
        sed_inplace(out_batch_start, 'JOB_LIST', "\'" + out_batch_job + "\'")

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])
        # eng = matlab.engine.start_matlab()
        # print("running SPM batch template: " + out_batch_start)  # , file=log)
        # eval("eng." + os.path.basename(os.path.splitext(out_batch_start)[0]) + "(nargout=0)")
        # eng.quit()

    # conditions_lists[{"name", "onsets", "duration"}, ....]
    def epi_spm_fmri_1st_level_analysis(self, analysis_name, TR, num_slices, conditions_lists, events_unit="secs", spm_template_name='spm_fmri_stats_1st_level', rp_filemame=""):

        #default params:
        stats_dir = os.path.join(self.epi_dir, "stats", analysis_name)
        os.makedirs(stats_dir, exist_ok=True)

        ref_slice = num_slices // 2 + 1

        if rp_filemame == "":
            rp_filemame = os.path.join(self.epi_dir, "rp_" + self.epi_image_label + ".txt")

        #set dirs
        in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + '_job.m')
        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        spm_script_dir = os.path.join(self.project.script_dir, "epi", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        out_batch_job = os.path.join(out_batch_dir, spm_template_name + self.label + '_job.m')
        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + self.label + '.m')

        #substitute for all the volumes
        epi_nvols = int(rrun('fslnvols ' + self.epi_data + '.nii.gz'))
        epi_path_name = os.path.join(self.epi_dir, "swar" + self.epi_image_label + '.nii')
        epi_all_volumes = ""
        for i in range(1, epi_nvols + 1):
            epi_volume = "'" + epi_path_name + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' # + "'"

        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, '<SPM_DIR>', stats_dir)
        sed_inplace(out_batch_job, '<EVENTS_UNIT>', events_unit)
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<MICROTIME_RES>', str(num_slices))
        sed_inplace(out_batch_job, '<MICROTIME_ONSET>', str(ref_slice))
        sed_inplace(out_batch_job, '<SMOOTHED_VOLS>', epi_all_volumes)
        sed_inplace(out_batch_job, '<MOTION_PARAMS>', rp_filemame)

        Stats.spm_stats_replace_conditions_string(out_batch_job, conditions_lists)

        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, 'X', '1')
        sed_inplace(out_batch_start, 'JOB_LIST', "\'" + out_batch_job + "\'")

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])
        # eng = matlab.engine.start_matlab()
        # print("running SPM batch template: " + out_batch_start)  # , file=log)
        # eval("eng." + os.path.basename(os.path.splitext(out_batch_start)[0]) + "(nargout=0)")
        # eng.quit()

    def epi_resting_nuisance(self, hpfsec=100):
        pass

    def epi_feat(self, do_initreg=False, std_image=""):

        if std_image == "":
            std_image = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain")
        pass

    def epi_aroma(self):
        pass

    def epi_sbfc_1multiroi_feat(self):
        pass

    def epi_sbfc_several_1roi_feat(self):
        pass

    # ==================================================================================================================================================
    # TRANSFORMS
    # ==================================================================================================================================================
    # path_type =   "standard"      : a roi name, located in the default folder (subjectXX/s1/roi/reg_YYY/INPUTPATH),
    #	            "rel"			: a path relative to SUBJECT_DIR (subjectXX/s1/INPUTPATH)
    #               "abs"			: a full path (INPUTPATH)

    def fnirt(self, ref, ofn="", odp="", refmask="", inimg="t1_brain"):

        if inimg == "t1_brain":
            img = self.t1_brain_data
        elif inimg == "t1":
            img = self.t1_data
        elif inimg == "t2_brain":
            img = self.t2_brain_data
        elif inimg == "t2":
            img = self.t2_brain
        else:
            print("ERROR in fnirt: unknown input image....returning")
            return

        if odp == "":
            odp = os.path.dirname(ref)

        if ofn == "":
            ofn = imgname(img) + "_2_" + imgname(ref)


        # inputs sanity check
        if imtest(img) is False:
            print("ERROR in fnirt: specified input image does not exist......returning")
            return

        if imtest(ref) is False:
            print("ERROR in fnirt: specified ref image does not exist......returning")
            return

        if os.path.isdir(odp) is False:
            print("ERROR in fnirt: specified output path does not exist......creating it !!")
            os.makedirs(odp, exist_ok=True)

        REF_STRING = ""
        if refmask != "":
            if imtest(refmask) is False:
                print("ERROR in fnirt: specified refmask image does not exist......returning")
                return
            REF_STRING= " --refmask=" + refmask


        rrun("flirt -in " + img + "-ref " + ref + " -omat " + os.path.join(odp, ofn + ".mat") + " -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")
        rrun("fnirt --iout= " + os.path.join(odp, ofn) + " --in=" + inimg + " --aff=" + os.path.join(odp, ofn + ".mat") + " --ref=" + ref + REF_STRING)


    def transform_roi(self, regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, std_img="", rois=[]):

        if std_img != "":
            if imtest(std_img) is False:
                print( "ERROR: given standard image file (" + std_img + ") does not exist......exiting")
                return
        else:
            std_img = self._global.fsl_standard_mni_2mm

        if mask != "":
            if imtest(mask) is False:
                print( "ERROR: mask image file (" + mask + ") do not exist......exiting")
                return

        if len(rois) == 0:
            print("Input ROI list is empty......exiting")
            return

        #==============================================================================================================
        print("registration_type " + regtype + ", do_linear = " + str(islin))

        self.has_T2=0
        if imtest(self.t2_data) is True:
            self.has_T2 = True


        linear_registration_type = {
                             "std2hr"     : self.transform_l_std2hr,
                             "std42hr"    : self.transform_l_std42hr,
                             "epi2hr"     : self.transform_l_epi2hr,
                             "dti2hr"     : self.transform_l_dti2hr,
                             "std2epi"    : self.transform_l_std2epi,
                             "std42epi"   : self.transform_l_std42epi,
                             "hr2epi"     : self.transform_l_hr2epi,
                             "dti2epi"    : self.transform_l_dti2epi,
                             "hr2std"     : self.transform_l_hr2std,
                             "epi2std"    : self.transform_l_epi2std,
                             "dti2std"    : self.transform_l_dti2std,
                             "std2std4"   : self.transform_l_std2std4,
                             "epi2std4"   : self.transform_l_epi2std4,
                             "hr2dti"     : self.transform_l_hr2dti,
                             "epi2dti"    : self.transform_l_epi2dti,
                             "std2dti"    : self.transform_l_std2dti
        }

        non_linear_registration_type = {
                             "std2hr"     : self.transform_nl_std2hr,
                             "std42hr"    : self.transform_nl_std42hr,
                             "epi2hr"     : self.transform_nl_epi2hr,
                             "dti2hr"     : self.transform_nl_dti2hr,
                             "std2epi"    : self.transform_nl_std2epi,
                             "std42epi"   : self.transform_nl_std42epi,
                             "hr2epi"     : self.transform_nl_hr2epi,
                             "dti2epi"    : self.transform_nl_dti2epi,
                             "hr2std"     : self.transform_nl_hr2std,
                             "epi2std"    : self.transform_nl_epi2std,
                             "dti2std"    : self.transform_nl_dti2std,
                             "std2std4"   : self.transform_nl_std2std4,
                             "epi2std4"   : self.transform_nl_epi2std4,
                             "hr2dti"     : self.transform_nl_hr2dti,
                             "epi2dti"    : self.transform_nl_epi2dti,
                             "std2dti"    : self.transform_nl_std2dti,
                             }

        for roi in rois:

            roi_name = os.path.basename(roi)
            print("converting " + roi_name)

            if islin is False:
                # is non linear
                output_roi = non_linear_registration_type[regtype](pathtype, roi_name, roi, std_img)
            else:
                output_roi = linear_registration_type[regtype](pathtype, roi_name, roi, std_img)

            if thresh > 0:
                output_roi_name     = os.path.basename(output_roi)
                output_input_roi    = os.path.dirname(output_roi)

                rrun("fslmaths " + output_roi + " -thr " + str(thresh) + " -bin " + os.path.join(output_input_roi, "mask_" + output_roi_name))

                v1 = rrun("fslstats " + os.path.join(output_input_roi, "mask_" + output_roi_name) + " -V")[0]

                if v1 == 0:
                    if orf != "":
                        print("subj: " + self.label + ", roi: " + roi_name + " ... is empty, thr: " + str(thresh)) # TODO: print to file

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO HR

    def transform_nl_std2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_t1_dir,roi_name + "_highres")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard_dir, "roi")

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
            
        rrun("applywarp -i " + input_roi + " -r " + self.t1_brain_data + " -o " + output_roi + " --warp=" + os.path.join(self.roi_t1_dir,"standard2highres_warp"))

    def transform_l_std2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_t1_dir,roi_name + "_highres")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_standard_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " +self.t1_brain_data + "-o " + os.path.join(self.roi_t1_dir,roi_name + "_highres") + " --warp=" + os.path.join(self.roi_t1_dir, "standard2highres_warp"))

    def transform_nl_std42hr(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_t1_dir,roi_name + "_highres")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard4_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(self.roi_t1_dir,roi_name + "_standard") + " -applyisoxfm 2")
        rrun("applywarp -i " +  os.path.join(self.roi_t1_dir, roi_name + "_standard") + " -r " + self.t1_brain_data + " -o " + output_roi + " --warp=" + os.path.join(self.roi_t1_dir, "standard2highres_warp"))
        imrm(os.path.join(self.roi_t1_dir,roi_name + "_standard"))

    def transform_l_std42hr(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_t1_dir,roi_name + "_highres")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard4_dir, roi)

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(self.roi_t1_dir,roi_name + "_standard") + " -applyisoxfm 2")
        rrun("applywarp -i " +  os.path.join(self.roi_t1_dir,roi_name + "_standard") + " -r " + self.t1_brain_data + " -o " + os.path.join(self.roi_epi_dir, roi_name + "_highres") + " --warp=" + os.path.join(self.roi_t1_dir, "standard2highres_warp"))
        imrm(os.path.join(self.roi_t1_dir, roi + "_standard"))

    def transform_nl_epi2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_t1_dir,roi_name + "_highres")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_epi_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
        rrun("flirt -in " + input_roi + " -ref " + self.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.roi_dti_dir, "epi2highres.mat") + " -interp trilinear")

    def transform_l_epi2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_t1_dir,roi_name + "_highres")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_epi_dir, roi)

        rrun("flirt -in " + input_roi + " -ref " + self.t1_brain_data + " -out " + os.path.join(self.roi_t1_dir, roi_name + "_highres") + " -applyxfm -init " + os.path.join(self.roi_dti_dir, "epi2highres.mat") + " -interp trilinear")

    def transform_nl_dti2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_dti_dir, roi + "_dti")
        if path_type == "abs":
            input_roi = roi
        else:
            input_roi = os.path.join(self.roi_dti_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
        if self.has_T2 is True:
            rrun("applywarp -i " + input_roi + " -r " + self.t1_brain_data + " -o " + output_roi + " --warp=" + os.path.join(self.roi_t1_dir, "dti2highres_warp"))
        else:
            rrun("flirt -in " + input_roi + " -ref " + self.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.roi_t1_dir, "dti2highres.mat") + " -interp trilinear")

    def transform_l_dti2hr(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_t1_dir, roi_name + "_highres")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_dti_dir, roi)

        if self.has_T2 is True:
            rrun("applywarp -i " + input_roi + " -r " +self.t1_brain_data + " -o " + os.path.join(self.roi_t1_dir, roi + "_highres") + " --warp=" + os.path.join(self.roi_t1_dir, "dti2highres_warp"))
        else:
            rrun("flirt -in " + input_roi + " -ref " + self.t1_brain_data + " -out " + os.path.join(self.roi_t1_dir, roi + "_highres") + " -applyxfm -init " + os.path.join(self.roi_dti_dir, "dti2highres.mat") + " -interp trilinear")

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO EPI

    def transform_nl_std2epi(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " + self.rs_examplefunc + " -o " + output_roi + " --warp=" + os.path.join(self.roi_epi_dir, "standard2epi_warp"))
    def transform_l_std2epi(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard_dir, "roi")

        rrun("flirt -in " + input_roi + " -ref " + self.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "standard2epi.mat"))

    def transform_nl_std42epi(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard4_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
            
        rrun("flirt -in " + input_roi + "-ref " + std_img + " -out " + os.path.join(self.roi_epi_dir, roi_name + "_standard") + " -applyisoxfm 2")
        rrun("applywarp -i " + os.path.join(self.roi_epi_dir, roi_name + "_standard") + " -r " + self.rs_examplefunc + " -o " + output_roi + " --warp=" + os.path.join(self.roi_epi_dir, "standard2epi_warp"))
        imrm(os.path.join(self.roi_epi_dir, roi_name + "_standard"))

    def transform_l_std42epi(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_standard4_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(self.roi_epi_dir,
                                                                                     roi_name + "_standard") + " -applyisoxfm 2")
        rrun("applywarp -i " + os.path.join(self.roi_epi_dir,
                                            roi_name + "_standard") + "-r " + self.rs_examplefunc + " -o " + os.path.join(
            self.roi_epi_dir, roi_name + "_epi") + " --warp=" + os.path.join(self.roi_epi_dir, "standard2epi_warp"))
        imrm(os.path.join(self.roi_epi_dir, roi_name + "_standard"))

    def transform_nl_hr2epi(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_t1_dir, roi)

        print("the hr2epi NON linear transformation does not exist.....using the linear one")
        rrun("flirt -in " + input_roi + " -ref " + self.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "highres2epi.mat") + " -interp trilinear")

    def transform_l_hr2epi(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_epi_dir, roi_name + "_epi")
        output_roi=os.path.join(self.roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_t1_dir,roi)

        rrun("flirt -in " + input_roi + " -ref " + self.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.roi_epi_dir, "highres2epi.mat") + " -interp trilinear")

    def transform_nl_dti2epi(self, path_type, roi_name, roi, std_img):
        print("registration type: dti2epi NOT SUPPORTED...exiting")

    def transform_l_dti2epi(self, path_type, roi_name, roi, std_img):
        print("registration type: dti2epi NOT SUPPORTED...exiting")

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD

    def transform_nl_hr2std(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_t1_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + os.path.join(self.roi_t1_dir, "highres2standard_warp"))

    def transform_l_hr2std(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_t1_dir,roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.roi_standard_dir, roi_name + "_standard") + " --warp=" + os.path.join(self.roi_t1_dir, "highres2standard_warp"))

    def transform_nl_epi2std(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi=os.path.join(self.roi_epi_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + os.path.join(self.roi_standard_dir, "epi2standard_warp"))

    def transform_l_epi2std(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_epi_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.roi_standard_dir, roi_name + "_standard") + " --warp=" + os.path.join(self.roi_standard_dir, "epi2standard_warp"))

    def transform_nl_dti2std(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_dti_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + os.path.join(self.roi_standard_dir, "dti2standard_warp"))

    def transform_l_dti2std(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_dti_dir,roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.roi_standard_dir, roi_name + "_standard") + " --warp=" + os.path.join(self.roi_standard_dir, "epi2standard_warp"))

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD4

    def transform_nl_std2std4(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard4_dir, roi_name + "_standard4")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard_dir, "roi")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")

    def transform_l_epi2std4(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard4_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi=roi
        else:
            input_roi=os.path.join(self.roi_epi_dir, roi)

        rrun("flirt -in " + input_roi + " -ref " + self.rs_examplefunc + " -out " + os.path.join(self.roi_standard4_dir, roi_name + "_standard2") + " -applyxfm -init " + os.path.join(self.roi_standard_dir, "epi2standard.mat") + " -interp trilinear")
        rrun("flirt -in " + os.path.join(self.roi_standard4_dir, roi_name + "_standard2") + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")
        imrm(os.path.join(self.roi_standard4_dir, roi_name + "_standard2"))

    def transform_nl_epi2std4(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard4_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_epi_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.roi_standard4_dir, roi_name) + "_standard2" + " --warp=" + os.path.join(self.roi_standard_dir, "epi2standard_warp"))
        rrun("flirt -in " + os.path.join(self.roi_standard4_dir, roi_name + "_standard2") + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")
        imrm(os.path.join(self.roi_standard4_dir, roi_name + "_standard2"))

    def transform_l_std2std4(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_standard4_dir, roi_name + "_standard")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard_dir, "roi")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + "-applyisoxfm 4")

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO DTI

    def transform_nl_hr2dti(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_dti_dir,roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_t1_dir, roi)

        if self.has_T2 is True and imtest(os.path.join(self.roi_t1_dir, "highres2dti_warp")) is True:
            rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.roi_dti_dir, "nobrain_diff") + " -o " + output_roi + " --warp=" + os.path.join(self.roi_t1_dir, "highres2dti_warp"))
        else:
            print("did not find the non linear registration from HR 2 DTI, I used a linear one")
            rrun("flirt -in " + input_roi + " -ref " + os.path.join(self.roi_dti_dir, "nobrain_diff") + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.roi_dti_dir, "highres2dti.mat") + " -interp trilinear")

    def transform_l_hr2dti(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_dti_dir, roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_t1_dir, roi)

        if self.has_T2 is True:
            rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.roi_dti_dir, "nobrain_diff") + " -o " + os.path.join(self.roi_dti_dir, roi_name + "_dti") + " --warp=" + os.path.join(self.roi_t1_dir, "highres2dti_warp"))
        else:
            rrun("flirt -in " + input_roi + " -ref " + os.path.join(self.roi_dti_dir, "nobrain_diff") + " -out " + os.path.join(self.roi_dti_dir,roi_name + "_dti") + " -applyxfm -init " + os.path.join(self.roi_dti_dir, "highres2dti.mat") + " -interp trilinear")

    def transform_nl_epi2dti(self, path_type, roi_name, roi, std_img):
        # output_roi=os.path.join(self.roi_dti_dir,roi_name + "_dti"
        # if [ "$path_type" = abs ]; then
        #     input_roi=roi
        # else:
        #     input_roi=os.path.join(self.roi_epi_dir, roi
        # fi
        # rrun("applywarp -i " + input_roi -r os.path.join(self.roi_dti_dir, nobrain_diff -o os.path.join(self.roi_standard4_dir, roi_name + "_standard2" --premat os.path.join(self.roi_t1_dir,epi2highres.mat --warp=os.path.join(self.roi_standard_dir, highres2standard_warp --postmat os.path.join(self.roi_dti_dir, standard2dti.mat;
        print("registration type: epi2dti NOT SUPPORTED...exiting")

    def transform_l_epi2dti(self, path_type, roi_name, roi, std_img):
        print("registration type: epi2dti NOT SUPPORTED...exiting")

    def transform_nl_std2dti(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_dti_dir,roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.roi_dir
        else:
            input_roi = os.path.join(self.roi_standard_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.roi_dti_dir, "nodif_brain") + " -o " + output_roi + "--warp=" + os.path.join(self.roi_dti_dir, "standard2dti_warp"))
    def transform_l_std2dti(self, path_type, roi_name, roi, std_img):
        output_roi=os.path.join(self.roi_dti_dir,roi_name + "_dti")
        if path_type == "abs":
            input_roi=roi
        elif path_type == "rel":
            input_roi=self.roi_dir
        else:
            input_roi=os.path.join(self.roi_standard_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.roi_dti_dir, "nodif_brain") + " -o " + os.path.join(self.roi_dti_dir, roi_name + "_dti") + " --warp=" + os.path.join(self.roi_dti_dir, "standard2dti_warp"))


    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def transform_epi(self, do_bbr=True, std_img_label="standard", std_img="", std_img_head="", std_img_mask_dil="", wmseg=""):
        
        if std_img == "":
            std_img             = self._global.fsl_standard_mni_2mm

        if std_img_head == "":
            std_img_head        = self._global.fsl_standard_mni_2mm_head

        if std_img_mask_dil == "":
            std_img_mask_dil    = self._global.fsl_standard_mni_2mm_mask_dil

        if wmseg == "":
            wmseg = self.t1_segment_wm_bbr_path

        os.makedirs(self.roi_epi_dir, exist_ok=True)
        os.makedirs(os.path.join(self.roi_dir, "reg_" + std_img_label), exist_ok=True)

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.t1_brain_data) is False:
            print("returning")
            return

        if imtest(std_img) is False:
            print("standard image (" + std_img + " not present....exiting")

        if imtest(self.rs_examplefunc) is False:
            rrun("fslmaths " + self.rs_data + " " + os.path.join(self.roi_epi_dir, "prefiltered_func_data") + " -odt float")
            rrun("fslroi " + os.path.join(self.roi_epi_dir, "prefiltered_func_data") + " " + self.rs_examplefunc + " 100 1")
            rrun("bet2 " + self.rs_examplefunc + " " + self.rs_examplefunc + " -f 0.3")

            rrun("imrm " + os.path.join(self.roi_epi_dir, "prefiltered_func_data*"))

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	
        # ---- EPI <--> HIGHRES
        epi2highres = os.path.join(self.roi_t1_dir, "epi2highres")

        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            rrun("flirt -ref " + self.t1_brain_data + " -in " + self.rs_examplefunc + " -dof 6 -omat " + epi2highres + "_init.mat")
            
            if imtest(self.t1_segment_wm_bbr_path) is False:
                    print("Running FAST segmentation for subj " + self.label)
                    temp_dir = os.path.join(self.roi_t1_dir, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.t1_brain_data))
                    rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + self.t1_segment_wm_bbr_path)
                    runsystem("rm -rf " + temp_dir)

            # => epi2highres.mat
            if os.path.isfile(epi2highres + ".mat") is False:
                rrun("flirt -ref " + self.t1_data + " -in " + self.rs_examplefunc + " -dof 6 -cost bbr -wmseg " + self.t1_segment_wm_bbr_path +
                     " -init " + epi2highres + "_init.mat" + " -omat " + epi2highres + ".mat" + " -out " + epi2highres + " -schedule " + os.path.join(self.fsl_dir, "etc", "flirtsch", "bbr.sch"))

            # => epi2highres.nii.gz
            if imtest(epi2highres) is False:
                rrun("applywarp -i " + self.rs_examplefunc + " -r " + self.t1_data + " -o " + epi2highres + "--premat=" + epi2highres + ".mat" + " --interp=spline")

            runsystem("rm " + epi2highres + "_init.mat")
        else:
            # NOT BBR
            if os.path.isfile(epi2highres + ".mat") is False:
                rrun("flirt -in " + self.rs_examplefunc + " -ref " + self.t1_brain_data + " -out " + epi2highres + " -omat " + epi2highres + ".mat" + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        highres2epi = os.path.join(self.roi_epi_dir, "highres2epi.mat")
        if os.path.isfile(highres2epi) is False:
            rrun("convert_xfm -inverse -omat " + highres2epi + " " + epi2highres + ".mat")
    
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	
        # ---- EPI <--> STANDARD
        epi2standard = os.path.join(self.roi_dir, "reg_" + std_img_label, "epi2standard")

        # => epi2standard.mat (as concat)
        if os.path.isfile(epi2standard + ".mat") is False:
            rrun("convert_xfm -omat " + epi2standard + ".mat" + " -concat " + os.path.join(self.roi_dir, "reg_" + std_img_label, "highres2standard.mat") + epi2highres + ".mat")

        # => standard2epi.mat
        standard2epi = os.path.join(self.roi_epi_dir, std_img_label + "2epi")
        if os.path.exist(standard2epi + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + standard2epi + ".mat " + epi2standard + ".mat")

        # => $ROI_DIR/reg_${std_img_label}/epi2standard.nii.gz
        if imtest(epi2standard) is False:
            rrun("flirt -ref " + std_img + " -in " + self.rs_examplefunc + " -out " + epi2standard + " -applyxfm -init " + epi2standard + ".mat" + " -interp trilinear")

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # epi -> highres -> standard
        if imtest(epi2standard + "_warp") is False:
            rrun("convertwarp --ref=" + std_img + " --premat=" + epi2highres + ".mat" + " --warp1=" + os.path.join(self.roi_dir, "reg_" + std_img_label, "highres2standard_warp") + " --out=" + epi2standard + "_warp")

        # invwarp: standard -> highres -> epi
        if imtest(standard2epi + "_warp") is False:
            rrun("invwarp -r " + os.path.join(self.roi_epi_dir, "example_func") + " -w " + os.path.join(self.roi_dir, "reg_" + std_img_label, "epi2standard_warp") + " -o " + standard2epi + "_warp")

    def transform_dti_t2(self):
        pass

    def transform_dti(self, std_img=""):

        if std_img == "":
            std_img = self._global.fsl_standard_mni_2mm

        if imtest(self.t1_brain_data) is False:
            print("T1_BRAIN_DATA (" + self.t1_brain_data + ") is missing....exiting")
            return

        if imtest(std_img) is False:
            print("standard image (" + std_img + ") is missing....exiting")
            return

        print(self.label + ":						STARTED : nonlin nodiff-t1-standard coregistration")
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        roi_no_dif  = os.path.join(self.roi_dti_dir , "nodif")
        no_dif      = os.path.join(self.dti_dir     , "nodif")
        if imtest(roi_no_dif + "_brain") is False:
            if imtest(no_dif + "_brain") is False:
                rrun("fslroi " + self.dti_data + " " + no_dif + " 0 1")
                rrun("bet " + no_dif + " " + no_dif + "_brain -m -f 0.3")

            imcp(no_dif + "_brain", roi_no_dif + "_brain")

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # dti -> highres
        dti2highres = os.path.join(self.roi_t1_dir, "dti2highres")
        if os.path.exist(dti2highres + ".mat") is False:
            rrun("flirt -in " + no_dif + "_brain" + " -ref " + self.t1_brain_data + " -out " + dti2highres + " -omat " + dti2highres + ".mat" +
                 " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear")

        if imtest(dti2highres + "_warp") is False:
            rrun("fnirt --in=" + roi_no_dif + "_brain" + " --ref=" + self.t1_brain_data + " --aff=" + dti2highres + ".mat" + " --cout=" + dti2highres + "_warp" + " --iout=" + roi_no_dif + "_brain2highres_nl" + " -v &>" + dti2highres + "_nl.txt")

        # highres -> dti
        highres2dti = os.path.join(self.roi_dti_dir, "highres2dti")
        if os.path.exist(highres2dti + ".mat") is False:
            rrun("convert_xfm -omat " + highres2dti + ".mat" + " -inverse " + dti2highres + ".mat")

        if imtest(highres2dti + "_warp") is False:
            rrun("invwarp -r " + roi_no_dif + "_brain" + " -w " + dti2highres + "_warp" + " -o " + highres2dti + "_warp")

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # dti -> highres -> standard
        dti2standard = os.path.join(self.roi_standard_dir, "dti2standard")
        if imtest(dti2standard + "_warp") is False:
            rrun("convertwarp --ref=" + std_img + " --warp1=" + os.path.join(self.roi_t1_dir, "dti2highres_warp") + " --warp2=" + os.path.join(self.roi_standard_dir, "highres2standard_warp") + " --out=" + dti2standard + "_warp")

        # standard -> highres -> dti
        standard2dti = os.path.join(self.roi_dti_dir, "standard2dti")
        if imtest(standard2dti + "_warp") is False:
            rrun("invwarp -r " + roi_no_dif + "_brain" + " -w " + dti2standard + "_warp" + " -o " + standard2dti + "_warp")

        #2: concat: standard -> highres -> dti
        #$FSLDIR/bin/convertwarp --ref=os.path.join(self.roi_dti_dir, nodif_brain --warp1=os.path.join(self.roi_t1_dir,standard2highres_warp --postmat=os.path.join(self.roi_dti_dir, highres2dti --out=os.path.join(self.roi_dti_dir, standard2dti_warp

    def transforms_mpr(self, std_img="", std_img_mask_dil="", std_img_label="standard"):
        pass

        if std_img == "":
            std_img             = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain")

        if std_img_mask_dil == "":
            std_img_mask_dil    = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain_mask_dil")

        if imtest(std_img) is False:
            print("file std_img: " + std_img + ".nii.gz is not present...skipping reg_nonlin_epi_t1_standard.sh")
            return

        if imtest(std_img_mask_dil) is False:
            print("file STD_IMAGE_MASK: " + std_img_mask_dil + ".nii.gz is not present...skipping reg_nonlin_epi_t1_standard.sh")
            return

        if imtest(self.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.t1_brain_data + ".nii.gz is not present...skipping reg_nonlin_epi_t1_standard.sh")
            return

        print( self.label + " :STARTED : nonlin t1-standard coregistration")

        # highres <--> standard

        os.makedirs(os.path.join(self.roi_dir, "reg_" + std_img_label), exist_ok=True)
        os.makedirs(os.path.join(self.roi_dir, "reg_" + std_img_label + "4"), exist_ok=True)
        os.makedirs(self.roi_t1_dir, exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # ---- HIGHRES <--------> STANDARD
        # => highres2standard.mat
        highres2standard = os.path.join(self.roi_dir, "reg_" + std_img_label, "highres2standard")
        if imtest(highres2standard + ".mat") is False:
            rrun("flirt -in " + self.t1_brain_data + " -ref " + std_img_label + " -out " + highres2standard + " -omat " + highres2standard + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => standard2highres.mat
        standard2highres = os.path.join(self.roi_t1_dir, std_img_label + "2highres")
        if imtest(standard2highres + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + standard2highres + ".mat " + highres2standard + ".mat")

        # NON LINEAR
        # => highres2standard_warp
        highres2standard_warp = os.path.join(self.roi_dir, "reg_" + std_img_label, "highres2standard_warp")
        if imtest(highres2standard_warp) is False:
            rrun("fnirt -- in =" + self.t1_brain_data + " --aff = " + highres2standard + ".mat --cout =" + highres2standard_warp + " --iout =" + highres2standard + "--jout =" + os.path.join(self.roi_t1_dir, "highres2highres_jac") + " --config = T1_2_MNI152_2mm --ref =" + std_img + " --refmask =" + std_img_mask_dil + "--warpres = 10, 10, 10")

        # => standard2highres_warp
        standard_warp2highres = os.path.join(self.roi_t1_dir, std_img_label + "2highres_warp")
        if imtest(standard_warp2highres) is False:
            rrun("invwarp -r " + self.t1_brain_data + " -w " + highres2standard_warp + " -o " + standard_warp2highres)

        ## => highres2${std_img_label}.nii.gz
        # [ `$FSLDIR/bin/imtest $ROI_DIR/reg_${std_img_label}/highres2standard` = 0 ] && rrun("applywarp -i " + T1_BRAIN_DATA -r $STD_IMAGE -o $ROI_DIR/reg_${std_img_label}/highres2standard -w $ROI_DIR/reg_${std_img_label}/highres2standard_warp

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # highres <--> standard4
        os.makedirs(os.path.join(self.roi_dir, "reg_"+ std_img_label + "4"), exist_ok=True)

        highres2standard4   = os.path.join(self.roi_dir, "reg_" + std_img_label + "4", "highres2standard")
        standard42highres   = os.path.join(self.roi_t1_dir, std_img_label + "42highres")
        hr2std4_warp        = os.path.join(self.roi_dir, "reg_" + std_img_label + "4", "highres2standard_warp.nii.gz")
        std42hr_warp        = os.path.join(self.roi_t1_dir, std_img_label + "42highres_warp.nii.gz")


        if os.path.isfile(highres2standard4 + ".mat") is False:
            rrun("flirt -in " + self.t1_brain_data + " -ref " + self._global.fsl_standard_mni_4mm + " -omat " + highres2standard4 + ".mat")

        if os.path.isfile(standard42highres + ".mat") is False:
            rrun("convert_xfm -omat " + standard42highres + ".mat" + " -inverse " + highres2standard4 + ".mat")

        # if imtest(hr2std4_warp) is False:
        #     rrun("fnirt --in " + self.t1_data + " --aff=" + highres2standard4 + ".mat" + " --cout=" + hr2std4_warp + " --iout=" + highres2standard4 +
        #          " --jout=" + highres2standard4 + "_jac" + " --config=" + os.path.join(self._global.global_data_templates, "gray_matter", "T1_2_MNI152_4mm") +
        #          " --ref=" + self._global.fsl_standard_mni_4mm + " --refmask=" + self._global.fsl_standard_mni_4mm + "_mask_dil" + " --warpres=10,10,10")
        #
        # if imtest(std42hr_warp) is False:
        #     rrun("inwarp -w " + hr2std4_warp + " -o " + std42hr_warp + " -r " + self.t1_brain_data)

        # ==================================================================================================================================================

        # [ ! -f $ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard.mat] & & $FSLDIR / bin / flirt - in $T1_BRAIN_DATA - ref $STD_IMAGE - out $ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard - omat $ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard.mat - cost corratio - dof 12 - searchrx - 90 90 - searchry - 90 90 - searchrz - 90 90 - interp trilinear
        # # => standard2highres.mat
        # [ ! -f $ROI_DIR / reg_t1 /${STD_IMAGE_LABEL}2highres.mat] & & $FSLDIR / bin / convert_xfm - inverse - omat $ROI_DIR / reg_t1 /${STD_IMAGE_LABEL}2highres.mat $ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard.mat
        #
        # # NON LINEAR
        # # => highres2standard_warp
        # [`$FSLDIR / bin / imtest $ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard_warp` = 0] & & $FSLDIR / bin / fnirt - - in =$T1_BRAIN_DATA - -aff =$ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard.mat - -cout =$ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard_warp - -iout =$ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard - -jout =$ROI_DIR / reg_t1 / highres2highres_jac - -config = T1_2_MNI152_2mm - -ref =$STD_IMAGE - -refmask =$STD_IMAGE_MASK - -warpres = 10, 10, 10
        #
        # # => standard2highres_warp
        # [`$FSLDIR / bin / imtest $ROI_DIR / reg_t1 /${STD_IMAGE_LABEL}2highres_warp` = 0] & & $FSLDIR / bin / invwarp - r $T1_BRAIN_DATA - w $ROI_DIR / reg_${STD_IMAGE_LABEL} / highres2standard_warp - o $ROI_DIR / reg_t1 /${STD_IMAGE_LABEL}2highres_warp
        #
        # ##	# => highres2${STD_IMAGE_LABEL}.nii.gz
        # ##	[ `$FSLDIR/bin/imtest $ROI_DIR/reg_${STD_IMAGE_LABEL}/highres2standard` = 0 ] && $FSLDIR/bin/applywarp -i $T1_BRAIN_DATA -r $STD_IMAGE -o $ROI_DIR/reg_${STD_IMAGE_LABEL}/highres2standard -w $ROI_DIR/reg_${STD_IMAGE_LABEL}/highres2standard_warp
        #
        # # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # # highres <--> standard4
        # mkdir - p $ROI_DIR / reg_${STD_IMAGE_LABEL}4
        #
        # highres2standard4_mat =$ROI_DIR / reg_${STD_IMAGE_LABEL}4 / highres2standard.mat
        # standard42highres_mat =$ROI_DIR / reg_t1 /${STD_IMAGE_LABEL}42highres.mat
        # hr2std4_warp =$ROI_DIR / reg_${STD_IMAGE_LABEL}4 / highres2standard_warp.nii.gz
        # std42hr_warp =$ROI_DIR / reg_t1 /${STD_IMAGE_LABEL}42highres_warp.nii.gz
        #
        # [ ! -f $highres2standard4_mat] & & $FSLDIR / bin / flirt - in $T1_BRAIN_DATA.nii.gz - ref $FSL_STANDARD_MNI_4mm - omat $highres2standard4_mat
        # [ ! -f $standard42highres_mat] & & $FSLDIR / bin / convert_xfm - omat $standard42highres_mat - inverse $highres2standard4_mat
        #
        # #	[ ! -f $hr2std4_warp ] && $FSLDIR/bin/fnirt --in=$T1_DATA --aff=$highres2standard4_mat --cout=$hr2std4_warp --iout=$ROI_DIR/reg_standard4/highres2standard --jout=$ROI_DIR/reg_standard4/highres2standard_jac --config=$GLOBAL_DATA_TEMPLATES/gray_matter/T1_2_MNI152_4mm --ref=$FSL_STANDARD_MNI_4mm --refmask=$GLOBAL_DATA_TEMPLATES/gray_matter/MNI152_T1_4mm_brain_mask_dil --warpres=10,10,10
        # #	[ ! -f $std42hr_warp ] && $FSLDIR/bin/invwarp -w $hr2std4_warp -o $std42hr_warp -r $T1_BRAIN_DATA
        # # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


    # ==================================================================================================================================================
    # DATA CONVERSIONS
    # ==================================================================================================================================================
    # routines to convert original images to nifti format. assumes data are in an external folder and converted data are copied and renamed properly

    # postconvert_cleanup:
    #   0: don't do anything
    #   1: delete only files (when original file are already in the final folder)
    #   2: delete original folder
    def mpr2nifti(self, extpath, cleanup=0):

        try:

            if "." in extpath:
                print("ERROR : input path " + str(extpath) + " cannot contain dots !!!")
                return

            rrun("dcm2nii " + extpath)      # it returns :. usefs coXXXXXX, oXXXXXXX and XXXXXXX images

            files = glob.glob(os.path.join(extpath, "*"))

            converted_images = []
            original_images = []

            for f in files:
                if is_image(f, self.DCM2NII_IMAGE_FORMATS) is True:
                    converted_images.append(f)
                else:
                    original_images.append(f)

            for img in converted_images:
                name    = os.path.basename(img)
                fullext = mysplittext(name)[1]

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
            elif cleanup == 2 :
                os.rmdir(extpath)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def epi2nifti(self, extpath, cleanup=0, session_label=""):

        try:

            if "." in extpath:
                print("ERROR : input path " + str(extpath) + " cannot contain dots !!!")
                return

            rrun("dcm2nii " + extpath)      # it returns :. usefs coXXXXXX, oXXXXXXX and XXXXXXX images

            files = glob.glob(os.path.join(extpath, "*"))

            converted_images = []
            original_images = []

            for f in files:
                if is_image(f, self.DCM2NII_IMAGE_FORMATS) is True:
                    converted_images.append(f)
                else:
                    original_images.append(f)

            for img in converted_images:
                name    = os.path.basename(img)
                fullext = mysplittext(name)[1]

                dest_file = os.path.join(self.epi_dir, self.epi_image_label + session_label + fullext)
                move(img, dest_file)


            if cleanup == 1:
                for img in original_images:
                    os.remove(img)
            elif cleanup == 2 :
                os.rmdir(extpath)

        except Exception as e:
            traceback.print_exc()
            print(e)


    def mri_merger(self, input_files, outputname, dimension="-t"):

        cur_dir = os.path.curdir
        os.chdir(self.epi_dir)

        rrun("fslmerge " + dimension + " " + outputname + " " + " ".join(input_files))
        os.chdir(cur_dir)


# ==================================================================================================================================================

