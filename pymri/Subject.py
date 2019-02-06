import os

from pymri.utility.fslfun import imtest, immv, imcp, quick_smooth, run, runpipe, run_notexisting_img, runsystem, run_move_notexisting_img, remove_ext, mass_images_move
from pymri.fsl.utils.run import rrun

import datetime
import traceback

# from nipype.interfaces.fsl import 

class Subject:

    BIAS_TYPE_NO        = 0
    BIAS_TYPE_WEAK      = 1
    BIAS_TYPE_STRONG    = 2

    def __init__(self, label, sessid, project):

        self.label                  = label
        self.sessid                 = sessid

        self.project                = project
        self.fsl_dir                = project.globaldata.fsl_dir
        self.fsl_bin                = project.globaldata.fsl_bin
        self.fsl_data_standard_dir  = project.globaldata.fsl_data_standard_dir

        self.project_subjects_dir   = project.subjects_dir

        self.dir                    = os.path.join(project.subjects_dir, self.label, "s" + str(self.sessid))
        self.roi_dir                = os.path.join(self.dir, "roi")

        self.roi_t1_dir             = os.path.join(self.roi_dir, "reg_t1")
        self.roi_epi_dir            = os.path.join(self.roi_dir, "reg_epi")
        self.roi_dti_dir            = os.path.join(self.roi_dir, "reg_dti")
        self.roi_t2_dir             = os.path.join(self.roi_dir, "reg_t2")
        self.roi_standard_dir       = os.path.join(self.roi_dir, "reg_standard")
        self.roi_standard4_dir      = os.path.join(self.roi_dir, "reg_standard4")

        self.t1_image_label         = self.label + "-t1"
        self.t1_dir                 = os.path.join(self.dir, "mpr")
        self.t1_data                = os.path.join(self.t1_dir, self.t1_image_label)
        self.t1_brain_data          = os.path.join(self.t1_dir, self.t1_image_label + "_brain")
        self.t1_brain_data_mask     = os.path.join(self.t1_dir, self.t1_image_label + "_brain_mask")
        
        self.fast_dir               = os.path.join(self.t1_dir, "fast")
        self.first_dir              = os.path.join(self.t1_dir, "first")
        self.sienax_dir             = os.path.join(self.t1_dir, "sienax")


        self.first_all_none_origsegs = os.path.join(self.first_dir, self.t1_image_label + "_all_none_origsegs")
        self.first_all_fast_origsegs = os.path.join(self.first_dir, self.t1_image_label + "_all_fast_origsegs")

        #if [ ! -d $SUBJECT_DIR]; then print( "ERROR: subject dir ($SUBJECT_DIR) not present !!!.....exiting"; exit; fi
        
        self.t1_segment_gm_path         = os.path.join(self.roi_t1_dir, "mask_t1_gm")
        self.t1_segment_wm_path         = os.path.join(self.roi_t1_dir, "mask_t1_wm")
        self.t1_segment_csf_path        = os.path.join(self.roi_t1_dir, "mask_t1_csf")
        self.t1_segment_wm_bbr_path     = os.path.join(self.roi_t1_dir, "wmseg4bbr")
        self.t1_segment_wm_ero_path     = os.path.join(self.roi_t1_dir, "mask_t1_wmseg4Nuisance")
        self.t1_segment_csf_ero_path    = os.path.join(self.roi_t1_dir, "mask_t1_csfseg4Nuisance")

        self.dti_image_label            = self.label + "- dti"
        self.dti_EC_image_label         = self.label + "-dti_ec"
        self.dti_rotated_bvec           = self.label + "-dti_rotated.bvec"
        
        self.dti_bvec                   = self.label + "-dti.bvec"
        self.dti_bval                   = self.label + "-dti.bval"
        
        self.dti_dir                    = os.path.join(self.dir, "dti")
        self.dti_data                   = os.path.join(self.dti_dir,  self.dti_image_label)
        self.dti_fit_label              = self.dti_image_label + "_fit"
        self.bedpost_X_dir              = os.path.join(self.dti_dir, "bedpostx")
        self.probtrackx_dir             = os.path.join(self.dti_dir, "probtrackx")
        self.trackvis_dir               = os.path.join(self.dti_dir, "trackvis")
        self.tv_matrices_dir            = os.path.join(self.dti_dir, "tv_matrices")
        self.trackvis_transposed_bvecs = "bvec_vert.txt"

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

        self.rs_aroma_dir           = os.path.join(self.rs_dir, "ica_aroma")
        self.rs_aroma_image         = os.path.join(self.rs_aroma_dir, "denoised_func_data_nonaggr")
        self.rs_regstd_aroma_dir    = os.path.join(self.rs_aroma_dir, "reg_standard")
        self.rs_regstd_aroma_image  = os.path.join(self.rs_regstd_aroma_dir, "filtered_func_data")

        self.mc_params_dir  = os.path.join(self.rs_dir, self.rs_image_label + ".ica", "mc")
        self.mc_abs_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_abs_mean.rms")
        self.mc_rel_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_rel_mean.rms")

        self.de_dir         = os.path.join(self.dir, "t2")
        self.de_image_label = "de"
        self.de_data        = os.path.join(self.de_dir, self.de_image_label)
        self.de_brain_data  = os.path.join(self.de_dir, self.de_image_label + "_brain")

        self.t2_dir         = self.de_dir
        self.t2_image_label = "t2"
        self.t2_data        = os.path.join(self.t2_dir, self.t2_image_label)
        self.t2_brain_data  = os.path.join(self.t2_dir, self.t2_image_label + "_brain")

        self.wb_dir         = os.path.join(self.dir, "wb")
        self.wb_image_label = self.label + "-wb_epi"
        self.wb_data        = os.path.join(self.wb_dir, self.wb_image_label)
        self.wb_brain_data  = os.path.join(self.wb_dir, self.wb_image_label + "_brain")


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

    # ==================================================================================================================================================
    # WELCOME
    # ==================================================================================================================================================

    def wellcome(self,  do_anat=True, odn = "anat", imgtype = 1, smooth = 10,
                        biascorr_type=BIAS_TYPE_STRONG,
                        do_reorient=True, do_crop=True,
                        do_bet=True, betfparam=0.5,
                        do_sienax=True, bet_sienax_param_string="-SNB -f 0.2",
                        do_reg=True, do_nonlinreg=True,
                        do_seg=True, do_subcortseg=True,
                        do_skipflirtsearch=False,
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

        has_T2              = 0
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
                self.anatomical_processing(odn=odn, imgtype=imgtype, smooth=smooth,
                        biascorr_type=biascorr_type,
                        do_reorient=do_reorient, do_crop=do_crop,
                        do_bet=do_bet, betfparam=betfparam,
                        do_reg=do_reg, do_nonlinreg=do_nonlinreg,
                        do_seg=do_seg, do_subcortseg=do_subcortseg,
                        do_skipflirtsearch=do_skipflirtsearch,
                        do_cleanup=do_cleanup, do_strongcleanup=do_strongcleanup, do_overwrite=do_overwrite,
                        use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                self.post_anatomical_processing(odn=odn)

            if do_sienax is True:
                print(self.label + " : sienax with " + bet_sienax_param_string)
                rrun("sienax " +  self.t1_data + " -B " + bet_sienax_param_string + " -r")

            self.transforms_mpr()
            if do_first is True:
              if imtest(self.first_all_fast_origsegs) is False and imtest(self.first_all_none_origsegs) is False:
                  self.do_first(first_struct, odn=first_odn)

            if do_freesurfer is True:
                self.fs_reconall()

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
                has_T2 = True
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

            if has_T2 is True:
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
    def anatomical_processing(self,
                        odn="anat", imgtype=1, smooth=10,
                        biascorr_type=BIAS_TYPE_STRONG,
                        do_reorient=True, do_crop=True,
                        do_bet=True, betfparam=0.5,
                        do_reg=True, do_nonlinreg=True,
                        do_seg=True, do_subcortseg=True,
                        do_skipflirtsearch=False,
                        do_cleanup=True, do_strongcleanup=False, do_overwrite=False,
                        use_lesionmask=False, lesionmask=""
                    ):
        niter       = 5
        logfile     = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir      = os.getcwd()

        # check anatomical image imgtype
        if imgtype is not 1:
            if do_nonlinreg is True:
                print("ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
                return False

            if do_subcortseg is True:
                print("ERROR: Cannot perform subcortical segmentation (with FIRST) on a non-T1 image, please re-run with do_subcortseg=False")
                return False

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
            # create some params strings
            if do_skipflirtsearch is True:
                flirtargs = " -nosearch"
            else:
                flirtargs = " "

            if use_lesionmask is True:
                fnirtargs = " --inmask=lesionmaskinv"
            else:
                fnirtargs = " "

            betopts = "-f " + str(betfparam)

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            os.chdir(anatdir)

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
            if imtest(os.path.join(anatdir, T1)) is False:
                rrun("fslmaths " + inputimage + " " + os.path.join(anatdir, T1), logFile=log)

            # cp lesionmask to anat dir
            if use_lesionmask is True:
                # I previously verified that it exists
                rrun("fslmaths", [lesionmask, os.path.join(anatdir, "lesionmask")])
                with open(logfile, "a") as text_file:
                    text_file.write("copied lesion mask " + lesionmask)

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
            if imtest("lesionmask") is False or do_overwrite is True:
                # make appropriate (reoreinted and cropped) lesion mask (or a default blank mask to simplify the code later on)
                if use_lesionmask is True:
                    if not os.path.isfile(T1 + "_orig2std.mat"):
                        transform = T1 + "_orig2std.mat"
                    if not os.path.isfile(T1 + "_orig2roi.mat"):
                        transform = T1 + "_orig2roi.mat"
                    if transform is not "":
                        rrun("fslmaths lesionmask lesionmask_orig", logFile=log)
                        rrun("flirt -in lesionmask_orig -ref " + T1 + " -applyxfm -interp nearestneighbour -init " + transform + " -out lesionmask", logFile=log)
                else:
                    rrun("fslmaths " +  T1 + " -mul 0 lesionmask", logFile=log)

                rrun("fslmaths lesionmask -bin lesionmask", logFile=log)
                rrun("fslmaths lesionmask -binv lesionmaskinv", logFile=log)

            #### BIAS FIELD CORRECTION (main work, although also refined later on if segmentation rrun)
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

                        rrun("fslmaths " + T1 + "_hpf_brain_mask -mas lesionmaskinv " + T1 + "_hpf_brain_mask", logFile=log)
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
                        rrun("fslmaths " + T1 + "_hpf2_brain -mas lesionmaskinv " + T1 + "_hpf2_maskedbrain", logFile=log)
                        rrun("fast -o " + T1 + "_initfast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_hpf2_maskedbrain", logFile=log)
                        rrun("fslmaths " + T1 + "_initfast_restore -mas lesionmaskinv " + T1 + "_initfast_maskedrestore", logFile=log)
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
                    rrun("fslmaths " + T1 + "_initfast2_restore -mas lesionmaskinv " + T1 + "_initfast2_maskedrestore", logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_initfast2_maskedrestore", logFile=log)
                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.label + " :Extrapolating bias field from central region")
                    # use the latest fast output
                    rrun("fslmaths " + T1 + " -div " + T1 + "_fast_restore -mas " + T1 + "_initfast2_brain_mask " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslmaths " + T1 + "_initfast2_brain_mask -ero -ero -ero -ero -mas lesionmaskinv " + T1 + "_initfast2_brain_mask2", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_initfast2_brain_mask2 -o " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_initfast2_brain_mask -dilall -add 1 " + T1 + "_fast_bias  # alternative to fslsmoothfill
                    rrun("fslmaths " + T1 + " -div " + T1 + "_fast_bias " + T1 + "_biascorr", logFile=log)
                else:
                    rrun("fslmaths " + T1 + " " + T1 + "_biascorr", logFile=log)

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
                            flirtargs = flirtargs + " -inweight lesionmaskinv"

                        rrun("flirt -interp spline -dof 12 -in " + T1 + "_biascorr -ref " + os.path.join(self.fsl_data_standard_dir, "MNI152_" + T1 + "_2mm") + " -dof 12 -omat " + T1 + "_to_MNI_lin.mat -out " + T1 + "_to_MNI_lin " + flirtargs, logFile=log)

                        if do_nonlinreg is True:
                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print( "Registering to standard space (non-linear)")
                            refmask = "MNI152_" + T1 + "_2mm_brain_mask_dil1"

                            rrun("fslmaths " + os.path.join(self.fsl_data_standard_dir, "MNI152_" + T1 + "_2mm_brain_mask") + " -fillh -dilF " + refmask, logFile=log)
                            rrun("fnirt --in=" + T1 + "_biascorr --ref=" + os.path.join(self.fsl_data_standard_dir, "MNI152_" + T1 + "_2mm") + " --fout=" + T1 + "_to_MNI_nonlin_field --jout=" + T1 + "_to_MNI_nonlin_jac --iout=" + T1 + "_to_MNI_nonlin --logout=" + T1 + "_to_MNI_nonlin.txt --cout=" + T1 + "_to_MNI_nonlin_coeff --config=" + os.path.join(self.fsl_dir, "etc", "flirtsch", T1 + "_2_MNI152_2mm.cnf") + " --aff=" + T1 + "_to_MNI_lin.mat --refmask=" + refmask + " " + fnirtargs, logFile=log)

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.label + " :Performing brain extraction (using FNIRT)")
                            rrun("invwarp --ref=" + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_coeff -o MNI_to_" + T1 + "_nonlin_field", logFile=log)
                            rrun("applywarp --interp=nn --in=" + os.path.join(self.fsl_data_standard_dir, "MNI152_" + T1 + "_2mm_brain_mask") + " --ref=" + T1 + "_biascorr -w MNI_to_" + T1 + "_nonlin_field -o " + T1 + "_biascorr_brain_mask", logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr_brain_mask -fillh " + T1 + "_biascorr_brain_mask", logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr -mas " + T1 + "_biascorr_brain_mask " + T1 + "_biascorr_brain", logFile=log)
                        ## In the future, could check the initial ROI extraction here
                else:
                    if do_bet is True:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.label + " :Performing brain extraction (using BET)")
                        rrun("bet -R " + T1 + "_biascorr " + T1 + "_biascorr_brain -m " + betopts, logFile=log)  ## results sensitive to the f parameter
                    else:
                        rrun("fslmaths " + T1 + "_biascorr " + T1 + "_biascorr_brain", logFile=log)
                        rrun("fslmaths " + T1 + "_biascorr_brain -bin " + T1 + "_biascorr_brain_mask", logFile=log)

            #### TISSUE-TYPE SEGMENTATION
            # required input: " + T1 + "_biascorr " + T1 + "_biascorr_brain " + T1 + "_biascorr_brain_mask
            # output: " + T1 + "_biascorr " + T1 + "_biascorr_brain (modified) " + T1 + "_fast* (as normally output by fast) " + T1 + "_fast_bias (modified)
            if imtest(T1 + "_fast_pve_1") is False or do_overwrite is True:
                if do_seg is True:
                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.label + " :Performing tissue-imgtype segmentation")
                    rrun("fslmaths " + T1 + "_biascorr_brain -mas lesionmaskinv " + T1 + "_biascorr_maskedbrain", logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " " + T1 + "_biascorr_maskedbrain", logFile=log)
                    immv(T1 + "_biascorr", T1 + "_biascorr_init", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_restore " + T1 + "_biascorr_brain", logFile=log)
                    # extrapolate bias field and apply to the whole head image
                    rrun("fslmaths " + T1 + "_biascorr_brain_mask -mas lesionmaskinv " + T1 + "_biascorr_brain_mask2", logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_restore -mas " + T1 + "_biascorr_brain_mask2 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_biascorr_brain_mask2 -o " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_biascorr_brain_mask2 -dilall -add 1 " + T1 + "_fast_bias # alternative to fslsmoothfill", logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_bias " + T1 + "_biascorr", logFile=log)

                    if do_nonlinreg is True:
                        # regenerate the standard space version with the new bias field correction applied
                        rrun("applywarp -i " + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_field -r " + os.path.join(self.fsl_data_standard_dir, "MNI152_" + T1 + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline", logFile=log)

            #### SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION (only done if registration turned on, and segmentation done, and it is a T1 image)
            # required inputs: " + T1 + "_biascorr
            # output: " + T1 + "_vols.txt
            if os.path.isfile(T1 + "_vols.txt") is False or do_overwrite is True:

                if do_reg is True and do_seg is True and T1 == "T1":
                    print(self.label + " :Skull-constrained registration (linear)")

                    rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_bet -s -m " + betopts, logFile=log)
                    rrun("pairreg " + os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain") + " " + T1 + "_biascorr_bet " + os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_skull") + " " + T1 + "_biascorr_bet_skull " + T1 + "2std_skullcon.mat", logFile=log)

                    if use_lesionmask is True:
                        rrun("fslmathslesionmask -max " + T1 + "_fast_pve_2 " + T1 + "_fast_pve_2_plusmask -odt float", logFile=log)
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

            #	#### SUB-CORTICAL STRUCTURE SEGMENTATION (done in subject_t1_first)
            #	# required input: " + T1 + "_biascorr
            #	# output: " + T1 + "_first*
            #	if [ `$FSLDIR/bin/imtest " + T1 + "_subcort_seg` = 0 -o $do_overwrite = yes ]; then
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

            #### CLEANUP
            if do_cleanup is True:
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning up intermediate files"
                rrun("imrm " + T1 + "_biascorr_bet_mask " + T1 + "_biascorr_bet " + T1 + "_biascorr_brain_mask2 " + T1 + "_biascorr_init " + T1 + "_biascorr_maskedbrain " + T1 + "_biascorr_to_std_sub " + T1 + "_fast_bias_idxmask " + T1 + "_fast_bias_init " + T1 + "_fast_bias_vol2 " + T1 + "_fast_bias_vol32 " + T1 + "_fast_totbias " + T1 + "_hpf* " + T1 + "_initfast* " + T1 + "_s20 " + T1 + "_initmask_s20", logFile=log)

            #### STRONG CLEANUP
            if do_strongcleanup is True:
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning all unnecessary files "
                rrun("imrm " + T1 + " " + T1 + "_orig " + T1 + "_fullfov", logFile=log)

            os.chdir(curdir)

        except Exception as e:
            traceback.print_exc()
            os.chdir(curdir)
            log.close()
            print(e)

    def post_anatomical_processing(self, odn="anat", imgtype=1):

        logfile     = os.path.join(self.t1_dir, "mpr_log.txt")
        curdir      = os.getcwd()

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir     = os.path.join(self.t1_dir, odn)
            T1          = "T1";
        elif imgtype == 2:
            anatdir     = os.path.join(self.t2_dir, odn)
            T1          = "T2";
        else:
            print("ERROR: PD input format is not supported")
            return False

        # ==================================================================================================================================================================
        #### move and rename files according to myMRI system
        print("----------------------------------- starting t1_post_processing of subject " + self.label)
        try:
            log = open(logfile, "a")
            print("******************************************************************", file=log)
            print("starting t1_post_processing", file=log)
            print("******************************************************************", file=log)

            os.chdir(anatdir)
    
            run_notexisting_img(self.t1_data + "_orig", "immv " + self.t1_data + " " + self.t1_data + "_orig", logFile=log)
            run_notexisting_img(self.t1_data, "imcp " + T1 + "_biascorr " + self.t1_data, logFile=log)
            run_notexisting_img(self.t1_brain_data, "imcp " + T1 + "_biascorr_brain " + self.t1_brain_data, logFile=log)
            run_notexisting_img(self.t1_brain_data + "_mask", "imcp " + T1 + "_biascorr_brain_mask " + self.t1_brain_data + "_mask", logFile=log)
    
            os.makedirs(self.fast_dir, exist_ok=True)

            mass_images_move("*fast*", self.fast_dir, logFile=log)

            run_notexisting_img(T1 + "_fast_pve_1", "imcp " + os.path.join(self.fast_dir, T1 + "_fast_pve_1 ./"), logFile=log) # this file is tested by subject_t1_processing to skip the fast step. so by copying it back, I allow such skip.
    
            run_notexisting_img(self.t1_segment_csf_path, "fslmaths " + os.path.join(self.fast_dir, T1 + "_fast_seg") + " -thr 1 -uthr 1 " + self.t1_segment_csf_path, logFile=log)
            run_notexisting_img(self.t1_segment_gm_path , "fslmaths " + os.path.join(self.fast_dir, T1 + "_fast_seg") + " -thr 2 -uthr 2 " + self.t1_segment_gm_path, logFile=log)
            run_notexisting_img(self.t1_segment_wm_path , "fslmaths " + os.path.join(self.fast_dir, T1 + "_fast_seg") + " -thr 3 " + self.t1_segment_wm_path, logFile=log)

            run_notexisting_img(self.t1_segment_csf_ero_path, "fslmaths " + os.path.join(self.fast_dir, T1 + "_fast_pve_0 -thr 1 -uthr 1 " + self.t1_segment_csf_ero_path), logFile=log)
            run_notexisting_img(self.t1_segment_wm_bbr_path , "fslmaths " + os.path.join(self.fast_dir, T1 + "_fast_pve_2 -thr 0.5 -bin " + self.t1_segment_wm_bbr_path), logFile=log)
            run_notexisting_img(self.t1_segment_wm_ero_path , "fslmaths " + os.path.join(self.fast_dir, T1 + "_fast_pve_2 -ero " + self.t1_segment_wm_ero_path), logFile=log)

            mass_images_move("*_to_MNI*", self.roi_standard_dir, logFile=log)
            mass_images_move("*_to_T1*", self.roi_t1_dir, logFile=log)

            run_move_notexisting_img(os.path.join(self.roi_t1_dir, "standard2highres_warp"), "immv " + os.path.join(self.roi_t1_dir, "MNI_to_T1_nonlin_field") + " " +  os.path.join(self.roi_t1_dir, "standard2highres_warp"), logFile=log)
            run_move_notexisting_img(os.path.join(self.roi_standard_dir, "highres2standard_warp"), "immv " + os.path.join(self.roi_standard_dir, "T1_to_MNI_nonlin_field") + " " +  os.path.join(self.roi_standard_dir, "highres2standard_warp"), logFile=log)

            # first has been removed from the standard t1_processing pipeline
            # mkdir -p $FIRST_DIR
            # run mv first_results $FIRST_DIR
            # run $FSLDIR/bin/immv ${T1}_subcort_seg $FIRST_DIR

            os.chdir(curdir)

        except Exception as e:
            traceback.print_exc()
            os.chdir(curdir)
            log.close()
            print(e)
            
    def do_first(self, structures="", t1_image="", odn=""):

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

            os.chdir(temp_dir)

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

            os.chdir(curdir)

        except Exception as e:
            traceback.print_exc()
            os.chdir(curdir)
            log.close()
            print(e)

    # FreeSurfer recon-all
    def fs_reconall(self):

        logfile = os.path.join(self.t1_dir, "log.txt")
        
        try:
            log = open(logfile, "a")

            curdir = os.getcwd()
            
            rrun("mri_convert " + self.t1_data + ".nii.gz " + self.t1_data + ".mgz")
            os.system("OLD_SUBJECTS_DIR=$SUBJECTS_DIR")
            os.system("SUBJECTS_DIR=" + self.t1_dir)
    
            rrun("recon-all -subject freesurfer" + self.label + " -i " + self.dti_data + ".mgz -all")
            rrun("mri_convert " + os.path.join(self.t1_dir, "freesurfer" + self.label, "mri", "aparc+aseg.mgz") + " " + os.path.join(self.t1_dir, "freesurfer" +  self.label, "aparc+aseg.nii.gz"))
            rrun("mri_convert " + os.path.join(self.t1_dir, "freesurfer" + self.label, "mri", "aseg.mgz") + " " + os.path.join(self.t1_dir, "freesurfer" +  self.label, "aseg.nii.gz"))
    
            os.system("SUBJECTS_DIR=$OLD_SUBJECTS_DIR")
            os.system("rm " + self.dti_data + ".mgz")
            os.chdir(curdir)

        except Exception as e:
            traceback.print_exc()
            os.chdir(curdir)
            log.close()
            print(e)

    def reslice_image(self, dir):

        if dir == "sag->axial":
            bckfilename = self.t1_image_label + "_sag"
            conversion_str = " -z -x y "
        else:
            print("invalid conversion")
            return

        imcp(self.t1_data, os.path.join(self.t1_dir, bckfilename))          # create backup copy
        rrun("fslswapdim " + self.t1_data + conversion_str + self.t1_data)   # run reslicing

    # ==================================================================================================================================================
    # DIFFUSION
    # ==================================================================================================================================================

    def dti_ec_fit(self):
        pass

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

    def transform_roi(self, regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, std_img="", rois=[]):

        if std_img != "":
            if imtest(std_img) is False:
                print( "ERROR: given standard image file (" + std_img + ") does not exist......exiting")
                return
        else:
            std_img = self.project.globaldata.fsl_standard_mni_2mm

        if mask != "":
            if imtest(mask) is False:
                print( "ERROR: mask image file (" + mask + ") do not exist......exiting")
                return

        if len(rois) == 0:
            print("Input ROI list is empty......exiting")
            return

        #==============================================================================================================
        print("registration_type " + regtype + ", do_linear = " + str(islin))

        has_T2=0
        if imtest(self.t2_data) is True:
            has_T2 = True


        linear_registration_type = {
                             "std2hr"     : self.l_std2hr,
                             "std42hr"    : self.l_std42hr,
                             "epi2hr"     : self.l_epi2hr,
                             "dti2hr"     : self.l_dti2hr,
                             "std2epi"    : self.l_std2epi,
                             "std42epi"   : self.l_std42epi,
                             "hr2epi"     : self.l_hr2epi,
                             "dti2epi"    : self.l_dti2epi,
                             "hr2std"     : self.l_hr2std,
                             "epi2std"    : self.l_epi2std,
                             "dti2std"    : self.l_dti2std,
                             "std2std4"   : self.l_std2std4,
                             "epi2std4"   : self.l_epi2std4,
                             "hr2dti"     : self.l_hr2dti,
                             "epi2dti"    : self.l_epi2dti,
                             "std2dti"    : self.l_std2dti
        }

        non_linear_registration_type = {
                             "std2hr"     : self.nl_std2hr,
                             "std42hr"    : self.nl_std42hr,
                             "epi2hr"     : self.nl_epi2hr,
                             "dti2hr"     : self.nl_dti2hr,
                             "std2epi"    : self.nl_std2epi,
                             "std42epi"   : self.nl_std42epi,
                             "hr2epi"     : self.nl_hr2epi,
                             "dti2epi"    : self.nl_dti2epi,
                             "hr2std"     : self.nl_hr2std,
                             "epi2std"    : self.nl_epi2std,
                             "dti2std"    : self.nl_dti2std,
                             "std2std4"   : self.nl_std2std4,
                             "epi2std4"   : self.nl_epi2std4,
                             "hr2dti"     : self.nl_hr2dti,
                             "epi2dti"    : self.nl_epi2dti,
                             "std2dti"    : self.nl_std2dti,
                             }

        for roi in rois:

            roi_name = os.path.basename(roi)
            print("converting " + roi_name)

            if islin is False:
                # is non linear
                output_roi = non_linear_registration_type[regtype]()
            else:
                output_roi = linear_registration_type[regtype]()

            if thresh > 0:
                output_roi_name     = os.path.basename(output_roi)
                output_input_roi    = os.path.dirname(output_roi)

                rrun("fslmaths " + output_roi + " -thr " + str(thresh) + " -bin " + os.path.join(output_input_roi, "mask_" + output_roi_name))

                v1 = rrun("fslstats " + os.path.join(output_input_roi, "mask_" + output_roi_name) + " -V")[0]

                if v1 == 0:
                    if orf != "":
                        print("subj: " + self.label + ", roi: " + roi_name + " ... is empty, thr: " + str(thresh)) # TODO: print to file


    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def nl_std2hr(self):
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        if [ `$FSLDIR/bin/imtest $input_roi` = 0 ]; then echo "error......input_roi ($input_roi) is missing....exiting"; exit; fi
                      $FSLDIR/bin/applywarp -i $input_roi -r $T1_BRAIN_DATA -o $output_roi --warp=$ROI_DIR/reg_t1/standard2highres_warp;;

    def nl_std42hr)
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard4/$roi
                        fi
                        if [ `$FSLDIR/bin/imtest $input_roi` = 0 ]; then echo "error......input_roi ($input_roi) is missing....exiting"; exit; fi
                        ${FSLDIR}/bin/flirt  -in $input_roi -ref $standard_image -out $ROI_DIR/reg_t1/$roi_name"_standard" -applyisoxfm 2;
                        $FSLDIR/bin/applywarp -i $ROI_DIR/reg_t1/$roi_name"_standard" -r $T1_BRAIN_DATA -o $output_roi --warp=$ROI_DIR/reg_t1/standard2highres_warp;
                        $FSLDIR/bin/imrm $ROI_DIR/reg_t1/$roi_name"_standard";;

    def nl_epi2hr)
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_epi/$roi
                        fi
                        if [ `$FSLDIR/bin/imtest $input_roi` = 0 ]; then echo "error......input_roi ($input_roi) is missing....exiting"; exit; fi
                        $FSLDIR/bin/flirt -in $input_roi -ref $T1_BRAIN_DATA -out $output_roi -applyxfm -init $ROI_DIR/reg_dti/epi2highres.mat -interp trilinear;;

    def nl_dti2hr)
                        output_roi=$ROI_DIR/reg_dti/$roi"_dti"
                        if [ "$path_type" = abs ]; then
                            input_roi=$roi
                        else
                            input_roi=$ROI_DIR/reg_dti/$roi
                        fi
                        if [ `$FSLDIR/bin/imtest $input_roi` = 0 ]; then echo "error......input_roi ($input_roi) is missing....exiting"; exit; fi
                        if [ $HAS_T2 -eq 1 ]; then
                            $FSLDIR/bin/applywarp -i $input_roi -r $T1_BRAIN_DATA -o $output_roi --warp=$ROI_DIR/reg_t1/dti2highres_warp
                        else
                            $FSLDIR/bin/flirt -in $input_roi -ref $T1_BRAIN_DATA -out $output_roi -applyxfm -init $ROI_DIR/reg_t1/dti2highres.mat -interp trilinear
                        fi;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_std2epi)
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $RS_EXAMPLEFUNC -o $output_roi --warp=$ROI_DIR/reg_epi/standard2epi_warp;;

    def nl_std42epi)
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard4/$roi
                        fi
                        if [ `$FSLDIR/bin/imtest $input_roi` = 0 ]; then echo "error......input_roi ($input_roi) is missing....exiting"; exit; fi
                        ${FSLDIR}/bin/flirt  -in $input_roi -ref $standard_image -out $ROI_DIR/reg_epi/$roi_name"_standard" -applyisoxfm 2;
                        $FSLDIR/bin/applywarp -i $ROI_DIR/reg_epi/$roi_name"_standard" -r $RS_EXAMPLEFUNC -o $output_roi --warp=$ROI_DIR/reg_epi/standard2epi_warp;
                        $FSLDIR/bin/imrm $ROI_DIR/reg_epi/$roi_name"_standard";;

    def nl_hr2epi)
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_t1/$roi
                        fi
                        echo "the hr2epi NON linear transformation does not exist.....using the linear one"
                        $FSLDIR/bin/flirt -in $input_roi -ref $RS_EXAMPLEFUNC -out $output_roi -applyxfm -init $ROI_DIR/reg_epi/highres2epi.mat -interp trilinear;;

    def nl_dti2epi)
                        echo "registration type: dti2epi NOT SUPPORTED...exiting";exit;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_hr2std)
                        output_roi=$ROI_DIR/reg_standard/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_t1/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $output_roi --warp=$ROI_DIR/reg_t1/highres2standard_warp;;

    def nl_epi2std)
                        output_roi=$ROI_DIR/reg_standard/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_epi/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $output_roi --warp=$ROI_DIR/reg_standard/epi2standard_warp;;

    def nl_dti2std)
                        output_roi=$ROI_DIR/reg_standard/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_dti/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $output_roi --warp=$ROI_DIR/reg_standard/dti2standard_warp;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_std2std4)
                        output_roi=$ROI_DIR/reg_standard4/$roi_name"_standard4"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        ${FSLDIR}/bin/flirt -in $input_roi -ref $standard_image -out $output_roi -applyisoxfm 4;;

    def nl_epi2std4)
                        output_roi=$ROI_DIR/reg_standard4/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_epi/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $ROI_DIR/reg_standard4/$roi_name"_standard2" --warp=$ROI_DIR/reg_standard/epi2standard_warp;
                        ${FSLDIR}/bin/flirt  -in $ROI_DIR/reg_standard4/$roi_name"_standard2" -ref $standard_image -out $output_roi -applyisoxfm 4
                        $FSLDIR/bin/imrm $ROI_DIR/reg_standard4/$roi_name"_standard2";;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_hr2dti)
                        output_roi=$ROI_DIR/reg_dti/$roi_name"_dti"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_t1/$roi
                        fi
                        if [ $HAS_T2 -eq 1 -a `$FSLDIR/bin/imtest $ROI_DIR/reg_t1/highres2dti_warp` = 1 ]; then
                            $FSLDIR/bin/applywarp -i $input_roi -r $ROI_DIR/reg_dti/nobrain_diff -o $output_roi --warp=$ROI_DIR/reg_t1/highres2dti_warp
                        else
                            echo "did not find the non linear registration from HR 2 DTI, I used a linear one"
                            $FSLDIR/bin/flirt -in $input_roi -ref $ROI_DIR/reg_dti/nobrain_diff -out $output_roi -applyxfm -init $ROI_DIR/reg_dti/highres2dti.mat -interp trilinear
                        fi;;

    def nl_epi2dti)
#								output_roi=$ROI_DIR/reg_dti/$roi_name"_dti"
#								if [ "$path_type" = abs ]; then
#									input_roi=$roi
#								else
#									input_roi=$ROI_DIR/reg_epi/$roi
#								fi
#								$FSLDIR/bin/applywarp -i $input_roi -r $ROI_DIR/reg_dti/nobrain_diff -o $ROI_DIR/reg_standard4/$roi_name"_standard2" --premat $ROI_DIR/reg_t1/epi2highres.mat --warp=$ROI_DIR/reg_standard/highres2standard_warp --postmat $ROI_DIR/reg_dti/standard2dti.mat;
                        echo "registration type: epi2dti NOT SUPPORTED...exiting";exit;;

    def nl_std2dti)
                        output_roi=$ROI_DIR/reg_dti/$roi_name"_dti"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $ROI_DIR/reg_dti/nodif_brain -o $output_roi --warp=$ROI_DIR/reg_dti/standard2dti_warp;;


    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def nl_std2hr)
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                      $FSLDIR/bin/applywarp -i $input_roi -r $T1_BRAIN_DATA -o $ROI_DIR/reg_t1/$roi_name"_highres" --warp=$ROI_DIR/reg_t1/standard2highres_warp;;

    def nl_std42hr)
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard4/$roi
                        fi
                        ${FSLDIR}/bin/flirt  -in $input_roi -ref $standard_image -out $ROI_DIR/reg_t1/$roi_name"_standard" -applyisoxfm 2;
                        $FSLDIR/bin/applywarp -i $ROI_DIR/reg_t1/$roi_name"_standard" -r $T1_BRAIN_DATA -o $ROI_DIR/reg_epi/$roi_name"_highres" --warp=$ROI_DIR/reg_t1/standard2highres_warp;
                        rm $ROI_DIR/reg_t1/$roi"_standard";;

    def nl_epi2hr)
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_epi/$roi
                        fi
                        $FSLDIR/bin/flirt -in $input_roi -ref $T1_BRAIN_DATA -out $ROI_DIR/reg_t1/$roi_name"_highres" -applyxfm -init $ROI_DIR/reg_dti/epi2highres.mat -interp trilinear;;

    def nl_dti2hr)
                        output_roi=$ROI_DIR/reg_t1/$roi_name"_highres"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_dti/$roi
                        fi
                        if [ $HAS_T2 -eq 1 ]; then
                            $FSLDIR/bin/applywarp -i $input_roi -r $T1_BRAIN_DATA -o $ROI_DIR/reg_t1/$roi"_highres" --warp=$ROI_DIR/reg_t1/dti2highres_warp
                        else
                            $FSLDIR/bin/flirt -in $input_roi -ref $T1_BRAIN_DATA -out $ROI_DIR/reg_t1/$roi"_highres" -applyxfm -init $ROI_DIR/reg_dti/dti2highres.mat -interp trilinear
                        fi;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_std2epi)
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        elsegaz
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        ${FSLDIR}/bin/flirt  -in $input_roi -ref $RS_EXAMPLEFUNC -out $output_roi -applyxfm -init $ROI_DIR/reg_epi/standard2epi.mat;;

    def nl_std42epi)
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard4/$roi
                        fi
                        if [ `$FSLDIR/bin/imtest $input_roi` = 0 ]; then echo "error......input_roi ($input_roi) is missing....exiting"; exit; fi
                        ${FSLDIR}/bin/flirt  -in $input_roi -ref $standard_image -out $ROI_DIR/reg_epi/$roi_name"_standard" -applyisoxfm 2;
                        $FSLDIR/bin/applywarp -i $ROI_DIR/reg_epi/$roi_name"_standard" -r $RS_EXAMPLEFUNC -o $ROI_DIR/reg_epi/$roi_name"_epi" --warp=$ROI_DIR/reg_epi/standard2epi_warp;
                        $FSLDIR/bin/imrm $ROI_DIR/reg_epi/$roi_name"_standard";;

    def nl_hr2epi)
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        output_roi=$ROI_DIR/reg_epi/$roi_name"_epi"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_t1/$roi
                        fi
                        $FSLDIR/bin/flirt -in $input_roi -ref $RS_EXAMPLEFUNC -out $output_roi -applyxfm -init $ROI_DIR/reg_epi/highres2epi.mat -interp trilinear;;

    def nl_dti2epi)	echo "registration type: dti2epi NOT SUPPORTED...exiting";exit;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_hr2std)
                        output_roi=$ROI_DIR/reg_standard/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_t1/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $ROI_DIR/reg_standard/$roi_name"_standard" --warp=$ROI_DIR/reg_t1/highres2standard_warp;;

    def nl_epi2std)
                        output_roi=$ROI_DIR/reg_standard/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_epi/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $ROI_DIR/reg_standard/$roi_name"_standard" --warp=$ROI_DIR/reg_standard/epi2standard_warp;;

    def nl_dti2std)
                        output_roi=$ROI_DIR/reg_standard/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_dti/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $standard_image -o $ROI_DIR/reg_standard/$roi_name"_standard" --warp=$ROI_DIR/reg_standard/epi2standard_warp;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_epi2std4)
                        output_roi=$ROI_DIR/reg_standard4/$roi_name"_standard"
                        if [ "$path_type" = abs ]; then
                            input_roi=$roi
                        else
                            input_roi=$ROI_DIR/reg_epi/$roi
                        fi
                        $FSLDIR/bin/flirt -in $input_roi -ref $RS_EXAMPLEFUNC -out $ROI_DIR/reg_standard4/$roi_name"_standard2" -applyxfm -init $ROI_DIR/reg_standard/epi2standard.mat -interp trilinear
                        ${FSLDIR}/bin/flirt  -in $ROI_DIR/reg_standard4/$roi_name"_standard2" -ref $standard_image -out $output_roi -applyisoxfm 4
                        $FSLDIR/bin/imrm $ROI_DIR/reg_standard4/$roi_name"_standard2";;

    def nl_std2std4)
                        output_roi=$ROI_DIR/reg_standard4/$roi_name"_standard"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        ${FSLDIR}/bin/flirt  -in $input_roi -ref $standard_image -out $output_roi -applyisoxfm 4;;

    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def nl_hr2dti)
                        output_roi=$ROI_DIR/reg_dti/$roi_name"_dti"
                        if [ "$path_type" = abs ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_t1/$roi
                        fi
                        if [ $HAS_T2 -eq 1 ]; then
                            $FSLDIR/bin/applywarp -i $input_roi -r $ROI_DIR/reg_dti/nobrain_diff -o $ROI_DIR/reg_dti/$roi_name"_dti" --warp=$ROI_DIR/reg_t1/highres2dti_warp
                        else
                            $FSLDIR/bin/flirt -in $input_roi -ref $ROI_DIR/reg_dti/nobrain_diff -out $ROI_DIR/reg_dti/$roi_name"_dti" -applyxfm -init $ROI_DIR/reg_dti/highres2dti.mat -interp trilinear
                        fi;;

    def nl_epi2dti)
                        echo "registration type: epi2dti NOT SUPPORTED...exiting";exit;;

    def nl_std2dti)
                        output_roi=$ROI_DIR/reg_dti/$roi_name"_dti"
                        if [ "$path_type" = "abs" ]; then
                            input_roi=$roi
                        elif [ "$path_type" == "rel" ]; then
                            input_roi=$SUBJECT_DIR/$roi
                        else
                            input_roi=$ROI_DIR/reg_standard/$roi
                        fi
                        $FSLDIR/bin/applywarp -i $input_roi -r $ROI_DIR/reg_dti/nodif_brain -o $ROI_DIR/reg_dti/$roi_name"_dti" --warp=$ROI_DIR/reg_dti/standard2dti_warp;;

                    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def transform_epi(self, do_bbr=True, std_img_label="standard", std_img="", std_img_head="", std_img_mask_dil="", wmseg=""):
        
        if std_img == "":
            std_img             = self.project.globaldata.fsl_standard_mni_2mm

        if std_img_head == "":
            std_img_head        = self.project.globaldata.fsl_standard_mni_2mm_head

        if std_img_mask_dil == "":
            std_img_mask_dil    = self.project.globaldata.fsl_standard_mni_2mm_mask_dil

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
            std_img = self.project.globaldata.fsl_standard_mni_2mm

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
        #$FSLDIR/bin/convertwarp --ref=$ROI_DIR/reg_dti/nodif_brain --warp1=$ROI_DIR/reg_t1/standard2highres_warp --postmat=$ROI_DIR/reg_dti/highres2dti --out=$ROI_DIR/reg_dti/standard2dti_warp


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
        # [ `$FSLDIR/bin/imtest $ROI_DIR/reg_${std_img_label}/highres2standard` = 0 ] && $FSLDIR/bin/applywarp -i $T1_BRAIN_DATA -r $STD_IMAGE -o $ROI_DIR/reg_${std_img_label}/highres2standard -w $ROI_DIR/reg_${std_img_label}/highres2standard_warp

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # highres <--> standard4
        os.makedirs(os.path.join(self.roi_dir, "reg_"+ std_img_label + "4"), exist_ok=True)

        highres2standard4   = os.path.join(self.roi_dir, "reg_" + std_img_label + "4", "highres2standard")
        standard42highres   = os.path.join(self.roi_t1_dir, std_img_label + "42highres")
        hr2std4_warp        = os.path.join(self.roi_dir, "reg_" + std_img_label + "4", "highres2standard_warp.nii.gz")
        std42hr_warp        = os.path.join(self.roi_t1_dir, std_img_label + "42highres_warp.nii.gz")


        if os.path.isfile(highres2standard4 + ".mat") is False:
            rrun("flirt -in " + self.t1_brain_data + " -ref " + self.project.globaldata.fsl_standard_mni_4mm + " -omat " + highres2standard4 + ".mat")

        if os.path.isfile(standard42highres + ".mat") is False:
            rrun("convert_xfm -omat " + standard42highres + ".mat" + " -inverse " + highres2standard4 + ".mat")

        # if imtest(hr2std4_warp) is False:
        #     rrun("fnirt --in " + self.t1_data + " --aff=" + highres2standard4 + ".mat" + " --cout=" + hr2std4_warp + " --iout=" + highres2standard4 +
        #          " --jout=" + highres2standard4 + "_jac" + " --config=" + os.path.join(self.project.globaldata.global_data_templates, "gray_matter", "T1_2_MNI152_4mm") +
        #          " --ref=" + self.project.globaldata.fsl_standard_mni_4mm + " --refmask=" + self.project.globaldata.fsl_standard_mni_4mm + "_mask_dil" + " --warpres=10,10,10")
        #
        # if imtest(std42hr_warp) is False:
        #     rrun("inwarp -w " + hr2std4_warp + " -o " + std42hr_warp + " -r " + self.t1_brain_data)

        # ==================================================================================================================================================

