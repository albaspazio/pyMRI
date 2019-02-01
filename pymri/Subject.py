import os

from pymri.utility.fslfun import imtest, immv, imcp, quick_smooth, run, runpipe, run_notexisting_img, run_move_notexisting_img, remove_ext, mass_images_move

from pymri.fsl.utils.run import rrun
# from fsl.utils import run
# from fsl.scripts import immv
import datetime
import traceback

# from nipype.interfaces.fsl import 

class Subject:

    def __init__(self, label, sessid, project):

        self.label              = label
        self.sessid             = sessid

        self.fsl_dir            = project.globaldata.fsl_dir
        self.fsl_bin            = project.globaldata.fsl_bin
        self.fsl_data_standard  = project.globaldata.fsl_data_standard

        self.project_subjects_dir = project.subjects_dir

        self.dir                = os.path.join(project.subjects_dir, self.label, "s" + str(self.sessid))
        self.roi_dir            = os.path.join(self.dir, "roi")

        self.t1_image_label     = self.label + "-t1"
        self.t1_dir             = os.path.join(self.dir, "mpr")
        self.t1_data            = os.path.join(self.t1_dir, self.t1_image_label)
        self.t1_brain_data      = os.path.join(self.t1_dir, self.t1_image_label + "_brain")
        self.t1_brain_data_mask = os.path.join(self.t1_dir, self.t1_image_label + "_brain_mask")
        
        self.fast_dir           = os.path.join(self.t1_dir, "fast")
        self.first_dir          = os.path.join(self.t1_dir, "first")
        self.sienax_dir         = os.path.join(self.t1_dir, "sienax")

        #if [ ! -d $SUBJECT_DIR]; then print( "ERROR: subject dir ($SUBJECT_DIR) not present !!!.....exiting"; exit; fi
        
        self.t1_segment_gm_path         = os.path.join(self.roi_dir, "reg_t1", "mask_t1_gm")
        self.t1_segment_wm_path         = os.path.join(self.roi_dir, "reg_t1", "mask_t1_wm")
        self.t1_segment_csf_path        = os.path.join(self.roi_dir, "reg_t1", "mask_t1_csf")
        self.t1_segment_wm_bbr_path     = os.path.join(self.roi_dir, "reg_t1", "wmseg4bbr")
        self.t1_segment_wm_ero_path     = os.path.join(self.roi_dir, "reg_t1", "mask_t1_wmseg4Nuisance")
        self.t1_segment_csf_ero_path    = os.path.join(self.roi_dir, "reg_t1", "mask_t1_csfseg4Nuisance")

        self.dti_image_label            = self.label + "- dti"
        self.dti_EC_image_label         = self.label + "-dti_ec"
        self.dti_ROTATED_bvec           = self.label + "-dti_rotated.bvec"
        
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
        self.rs_examplefunc             = os.path.join(self.roi_dir, "reg_epi", "example_func")

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

        self.rs_regstd_dir = os.path.join(self.rs_dir, "resting.ica", "reg_standard")
        self.rs_regstd_image = os.path.join(self.rs_regstd_dir, "filtered_func_data")
        self.rs_regstd_denoise_dir = os.path.join(self.rs_dir, "resting.ica", "reg_standard_denoised")
        self.rs_regstd_denoise_image = os.path.join(self.rs_regstd_denoise_dir, "filtered_func_data")

        self.rs_aroma_dir = os.path.join(self.rs_dir, "ica_aroma")
        self.rs_aroma_image = os.path.join(self.rs_aroma_dir, "denoised_func_data_nonaggr")
        self.rs_regstd_aroma_dir = os.path.join(self.rs_aroma_dir, "reg_standard")
        self.rs_regstd_aroma_image = os.path.join(self.rs_regstd_aroma_dir, "filtered_func_data")

        self.mc_params_dir = os.path.join(self.rs_dir, self.rs_image_label + ".ica", "mc")
        self.mc_abs_displ = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_abs_mean.rms")
        self.mc_rel_displ = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_rel_mean.rms")

        self.de_dir = os.path.join(self.dir, "t2")
        self.de_image_label = "de"
        self.de_data = os.path.join(self.de_dir, self.de_image_label)
        self.de_brain_data = os.path.join(self.de_dir, self.de_image_label + "_brain")

        self.t2_dir = self.de_dir
        self.t2_image_label = "t2"
        self.t2_data = os.path.join(self.t2_dir, self.t2_image_label)
        self.t2_brain_data = os.path.join(self.t2_dir, self.t2_image_label + "_brain")

        self.wb_dir = os.path.join(self.dir, "wb")
        self.wb_image_label = self.label + "-wb_epi"
        self.wb_data = os.path.join(self.wb_dir, self.wb_image_label)
        self.wb_brain_data = os.path.join(self.wb_dir, self.wb_image_label + "_brain")


    def create_file_system(self):

        os.makedirs(os.path.join(self.dir, "mpr"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "epi"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "dti"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "t2"), exist_ok = True)

        os.makedirs(os.path.join(self.dir, "roi", "reg_t1"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "roi", "reg_standard"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "roi", "reg_dti"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "roi", "reg_epi"), exist_ok = True)
        os.makedirs(os.path.join(self.dir, "roi", "reg_t2"), exist_ok = True)

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
                        strongbias = True, do_biasrestore = True,
                        do_reorient = True, do_crop = True,
                        do_bet = True, betfparam = 0.5,
                        do_reg = True, do_nonlinreg = True,
                        do_seg = True, do_subcortseg = True,
                        do_skipflirtsearch = False,
                        do_cleanup = True, do_strongcleanup = False, do_overwrite = False,
                        use_lesionmask = False, lesionmask = "",
                        do_fs=False,
                        do_first=False, first_struct="", first_odn="",
                        do_epirm2vol=0, do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="resting",
                        feat_preproc_model="singlesubj_feat_preproc", do_featinitreg=False,
                        do_melodic=True, mel_odn="resting",mel_preproc_model="singlesubj_melodic" , do_melinitreg=False,
                        do_dtifit=True, do_bedx=True, do_bedx_cuda=False, do_autoptx_tract=False):


        #feat_preproc_model=$PROJ_SCRIPT_DIR / glm / templates / singlesubj_feat_preproc):

        # Usage()
        # {
        # echo "usage: $0 SUBJ_LABEL PROJ_DIR -sienax \"-B -f 0.3\" -firststructs L_Thal,R_Thal -mel resting -dtifit -bedx bedpostx"
        # echo "-----t1 processing				"
        # echo "  	-noanat)							"
        # echo "  	-nobias)							"
        # echo "  	-weakbias)						"
        # echo "  	-sienax)							"
        # echo "  	-firststructs) 				"
        # echo "  	-firstodn) 						"
        # echo "  	-firstlreg2odn) 			"
        # echo "  	-firstnlreg2odn) 			"
        # echo "-----epi preprocessing		"
        # echo "-----melodic processing	  "
        # echo "-----dti processing 			"
        # }


        HAS_T2=0
        # ==================================================================================
        # PROCESSING
        # ==================================================================================
        BET_PARAM_STRING="-SNB -f 0.2"
        BET_F_VALUE_T2="0.5"
        MELODIC_MODEL="$PROJ_SCRIPT_DIR/glm/templates/singlesubj_melodic"
        MELODIC_OUTPUT_DIR="resting"
        MELODIC_DO_INIT_REG=0
        FEAT_PREPROC_MODEL="$PROJ_SCRIPT_DIR/glm/templates/singlesubj_feat_preproc"
        FEAT_PREPROC_OUTPUT_DIR_NAME="resting"
        BEDPOST_OUTDIR_NAME="bedpostx"
        STRUCT_CONN_ATLAS_PATH="freesurfer"	  		# default value, otherwise specify path to image
        STRUCT_CONN_ATLAS_NROI=0
        # standard steps
        DO_ANAT_PROC=1
        DO_FEAT_PREPROC=1
        DO_ICA_AROMA=1
        DO_NUISANCE=1

        # to be chosen
        DO_SIENAX=0
        DO_FIRST=0
        DO_MELODIC=0
        DO_DTIFIT=0
        DO_AUTOPTX_TRACT=0
        DO_BEDPOST=0
        DO_BEDPOST_CUDA=0
        DO_FREESURFER_RECON=0
        DO_STRUCT_CONN=0

        # more params
        DO_FEAT_PREPROC_INIT_REG=0 # valid also for melodic
        DO_BIAS_TYPE=2	# 0: no bias, 1: weak bias, 2:full bias
        HPF_SEC=100
        STANDARD_IMAGE="$FSL_DATA_STANDARD/MNI152_T1_2mm_brain"

        # declare -i DO_RMVOL_TO_NUM=0  # indicate how many volumes must have the final EPI image
        #
        #
        # while [ ! -z "$1" ]
        # do
        #   case "$1" in
        #
        #     # t1 preprocessing
        #         -skipanat)				DO_ANAT_PROC=0;;
        #         -nobias)				DO_BIAS_TYPE=0;;		# see subject_t1_processing.sh
        #         -weakbias)				DO_BIAS_TYPE=1;;
        #         -sienax)				DO_SIENAX=1
        #                                 BET_PARAM_STRING="-B -f 0.20"; shift;;
        #         -first) 				DO_FIRST=1;;
        #         -firststructs)			DO_FIRST=1
        #                                 FIRST_STRUCTURES="-structs $2"; shift;;
        #         -firstodn) 				DO_FIRST=1
        #                                 FIRST_OUTPUT_DIR_NAME="-odn $2"; shift;;
        #         -freesurfer)			DO_FREESURFER_RECON=1; shift;;
        #         -stdimg) 				STANDARD_IMAGE=$2; shift;;
        #
        #         # epi preprocessing
        #         -epirm2vol)				DO_RMVOL_TO_NUM=$2;	shift;;
        #         -skiparoma) 			DO_ICA_AROMA=0;;
        #         -skipnuisance)			DO_NUISANCE=0;;
        #         -skippreproc)			DO_FEAT_PREPROC=0;;
        #         -hpfsec)				HPF_SEC=$2; shift;;
        #         -featpreprocodn)		DO_FEAT_PREPROC=1;
        #                                 FEAT_PREPROC_OUTPUT_DIR_NAME=$2; shift;;
        #         -featpreprocmodel)		DO_FEAT_PREPROC=1
        #                                 FEAT_PREPROC_MODEL=$2; shift;;
        #         -featinitreg) 			DO_FEAT_PREPROC_INIT_REG=1;;  # valid also for melodic
        #
        #         # melodic
        #         -mel)					DO_MELODIC=1;;
        #         -melodn)				DO_MELODIC=1
        #                                 MELODIC_OUTPUT_DIR=$2; shift;;
        #         -melmodel)				DO_MELODIC=1
        #                                 MELODIC_MODEL=$2; shift;;
        #         # dti
        #         -bedx)					DO_BEDPOST=1; shift;;
        #         -bedxodn)				DO_BEDPOST=1
        #                                 BEDPOST_OUTDIR_NAME=$2; shift;;
        #         -bedxcuda)				DO_BEDPOST_CUDA=1; shift;;
        #         -bedxcudaodn)			DO_BEDPOST_CUDA=1
        #                                 BEDPOST_OUTDIR_NAME=$2; shift;;
        #         -dtifit)				DO_DTIFIT=1;;
        #         -autoptx_tract)			DO_AUTOPTX_TRACT=1;;
        #         -structconn)			DO_STRUCT_CONN=1;
        #                                 STRUCT_CONN_ATLAS_PATH=$2; shift;;
        #
        #         -structconn_nroi)		STRUCT_CONN_ATLAS_NROI=$2; shift;;
        #
        #         *)  					echo "ERROR: unrecognized input parameter($1)";
        #                                 exit;;
        #     esac
        #     shift
        # done
        #
        # fsl_anat_elem=""
        # if [ $DO_FIRST -eq 0 ]; then		fsl_anat_elem=`echo "$fsl_anat_elem --nosubcortseg"`;fi
        #
        # if [ $DO_BIAS_TYPE -eq 0 ]; then fsl_anat_elem=`echo "$fsl_anat_elem --nobias"`;
        # elif [ $DO_BIAS_TYPE -eq 1 ]; then fsl_anat_elem=`echo "$fsl_anat_elem --weakbias"`;
        # fi
        # #==============================================================================================================================================================
        # #  T1 data
        # #==============================================================================================================================================================
        # if [ -d "$T1_DIR" ]; then
        #     mkdir -p $ROI_DIR/reg_t1
        #     mkdir -p $ROI_DIR/reg_standard
        #     mkdir -p $FAST_DIR
        #
        #     if [ $DO_ANAT_PROC -eq 1 ]; then
        #         . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_t1_processing.sh $SUBJ_NAME $PROJ_DIR $fsl_anat_elem
        #         . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_t1_post_processing.sh $SUBJ_NAME $PROJ_DIR
        #     fi
        #
        #     if [ $DO_SIENAX -eq 1 ]; then
        #       echo "===========>>>> $SUBJ_NAME: sienax with $BET_PARAM_STRING"
        #         $FSLDIR/bin/sienax $T1_DATA -B "$BET_PARAM_STRING" -r
        #         rm $SIENAX_DIR/I.nii*
        #     fi
        #
        #     . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_transforms_calculate_t1.sh $SUBJ_NAME $PROJ_DIR
        #
        #   if [ $DO_FIRST -eq 1 ]; then
        #     if [ ! -f $FIRST_DIR/$T1_IMAGE_LABEL"_"all_none_origsegs.nii.gz -a ! -f $FIRST_DIR/$T1_IMAGE_LABEL"_"all_fast_origsegs.nii.gz ];	then
        #         . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_t1_first.sh $SUBJ_NAME $PROJ_DIR $FIRST_STRUCTURES $FIRST_OUTPUT_DIR_NAME $FIRST_OUTPUT_REG_DIR_NAME
        #         fi
        #     fi
        #
        #     if [ $DO_FREESURFER_RECON -eq 1 ]; then
        #         . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_t1_freesurfer_reconall.sh $SUBJ_NAME $PROJ_DIR
        #     fi
        # fi
        #
        # #==============================================================================================================================================================
        # # WB data
        # #==============================================================================================================================================================
        # if [ -d "$WB_DIR" ]; then
        #   if [ `$FSLDIR/bin/imtest $WB_DATA` = 1 ]; then
        #     if [ `$FSLDIR/bin/imtest $WB_BRAIN_DATA` = 0 ]; then
        #         echo "===========>>>> $SUBJ_NAME: bet on WB"
        #         $FSLDIR/bin/bet $WB_DATA $WB_BRAIN_DATA -f $BET_F_VALUE_T2 -g 0 -m
        #     fi
        #   fi
        # fi
        #
        # #==============================================================================================================================================================
        # # RS data
        # #==============================================================================================================================================================
        # if [ -d "$RS_DIR" ]; then
        #
        #     mkdir -p $ROI_DIR/reg_epi
        #   if [ 1 = 0 ];  then
        #         echo "===========>>>> rs image $RS_DATA.nii.gz is missing...continuing"
        #     else
        #         LOGFILE=$RS_DIR/log_epi_processing.txt
        #
        #         run mkdir -p $PROJ_GROUP_ANALYSIS_DIR/melodic/dr
        #         run mkdir -p $PROJ_GROUP_ANALYSIS_DIR/melodic/group_templates
        #         run mkdir -p $RS_DIR/reg_standard
        #
        #         if [ $DO_RMVOL_TO_NUM -gt 0 ]; then
        #             # check if I have to remove the first (TOT_VOL-DO_RMVOL_TO_NUM) volumes
        #             declare -i TOT_VOL_NUM=`fslnvols $RS_DATA`
        #             declare -i vol2remove=$TOT_VOL_NUM-$DO_RMVOL_TO_NUM
        #             if [ $vol2remove -gt 0 ]; then
        #                 run mv $RS_DATA.nii.gz $RS_DATA"_fullvol".nii.gz
        #                 run $FSLDIR/bin/fslroi $RS_DATA"_fullvol" $RS_DATA $vol2remove $TOT_VOL_NUM
        #             fi
        #         fi
        #
        #         # FEAT PRE PROCESSING
        #         if [ `$FSLDIR/bin/imtest $RS_DIR/$RS_POST_PREPROCESS_IMAGE_LABEL` = 0 ]; then
        #             if [ ! -f $FEAT_PREPROC_MODEL.fsf ]; then
        #                 echo "===========>>>> FEAT_PREPROC template file ($SUBJ_NAME $PROJ_DIR $FEAT_PREPROC_MODEL.fsf) is missing...skipping feat preprocessing"
        #             else
        #                 if [ ! -d $RS_DIR/$FEAT_PREPROC_OUTPUT_DIR_NAME.feat ]; then
        #                     run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_feat.sh $SUBJ_NAME $PROJ_DIR -model $FEAT_PREPROC_MODEL -odn $FEAT_PREPROC_OUTPUT_DIR_NAME.feat -stdimg $STANDARD_IMAGE -initreg $DO_FEAT_PREPROC_INIT_REG
        #                     run $FSLDIR/bin/imcp $RS_DIR/$FEAT_PREPROC_OUTPUT_DIR_NAME.feat/filtered_func_data $RS_DIR/$RS_POST_PREPROCESS_IMAGE_LABEL
        #                 fi
        #             fi
        #         fi
        #
        #         # do AROMA processing
        #         if [ $DO_ICA_AROMA -eq 1 -a `$FSLDIR/bin/imtest $RS_DIR/$RS_POST_AROMA_IMAGE_LABEL` = 0 ]; then
        #             run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_aroma.sh $SUBJ_NAME $PROJ_DIR -idn $FEAT_PREPROC_OUTPUT_DIR_NAME.feat  # do not register to standard
        #             run $FSLDIR/bin/imcp $RS_AROMA_IMAGE $RS_DIR/$RS_POST_AROMA_IMAGE_LABEL
        #         fi
        #
        #         # do nuisance removal (WM, CSF & highpass temporal filtering)....create the following file: $RS_IMAGE_LABEL"_preproc_aroma_nuisance"
        #         if [ $DO_NUISANCE -eq 1 -a `$FSLDIR/bin/imtest $RS_DIR/$RS_POST_NUISANCE_IMAGE_LABEL` = 0 ]; then
        #             run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_resting_nuisance.sh $SUBJ_NAME $PROJ_DIR -hpfsec $HPF_SEC -ifn $RS_POST_AROMA_IMAGE_LABEL
        #             run . $GLOBAL_SCRIPT_DIR/process_subject/subject_transforms_roi.sh $SUBJ_NAME $PROJ_DIR -thresh 0 -regtype epi2std4 -pathtype abs $RS_DIR/$RS_POST_NUISANCE_IMAGE_LABEL
        #             $FSLDIR/bin/immv $ROI_DIR/reg_standard4/$RS_POST_NUISANCE_STANDARD_IMAGE_LABEL $RS_FINAL_REGSTD_IMAGE
        #         fi
        #
        #         run $FSLDIR/bin/imcp $RS_DIR/$FEAT_PREPROC_OUTPUT_DIR_NAME.feat/reg_standard/bg_image $RS_FINAL_REGSTD_DIR/bg_image
        #         run $FSLDIR/bin/imcp $RS_DIR/$FEAT_PREPROC_OUTPUT_DIR_NAME.feat/reg_standard/mask $RS_FINAL_REGSTD_DIR/mask
        #
        #
        #         # NOW reg_standard contains a denoised file with its mask and background image. nevertheless, we also do a melodic to check the output,
        #         # doing another MC and HPF results seems to improve...although they should not...something that should be investigated....
        #
        #
        #         # MELODIC
        #         if [ ! -d $RS_DIR/$MELODIC_OUTPUT_DIR.ica -a $DO_MELODIC -eq 1 ]; then
        #             if [ ! -f $MELODIC_MODEL.fsf ];
        #             then
        #                 echo "===========>>>> melodic template file ($SUBJ_NAME $PROJ_DIR $MELODIC_MODEL.fsf) is missing...skipping 1st level melodic"
        #             else
        #                 if [ ! -d $RS_DIR/$MELODIC_OUTPUT_DIR.ica ]; then
        #                     run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_feat.sh $SUBJ_NAME $PROJ_DIR -model $MELODIC_MODEL -odn $MELODIC_OUTPUT_DIR.ica -stdimg $STANDARD_IMAGE -initreg $DO_FEAT_PREPROC_INIT_REG -ifn $RS_POST_NUISANCE_IMAGE_LABEL
        #                     if [ `$FSLDIR/bin/imtest $RS_DIR/$MELODIC_OUTPUT_DIR.ica/reg_standard/filtered_func_data` = 1 ]; then
        #                         run $FSLDIR/bin/imcp $RS_DIR/$MELODIC_OUTPUT_DIR.ica/reg_standard/filtered_func_data $RS_FINAL_REGSTD_DIR/${RS_POST_NUISANCE_MELODIC_IMAGE_LABEL}_$MELODIC_OUTPUT_DIR
        #                     fi
        #                 fi
        #             fi
        #         fi
        #
        #
        #         # calculate the remaining transformations   .....3/4/2017 si blocca qui...devo commentarlo per andare avanti !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #         run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_transforms_calculate_epi.sh $SUBJ_NAME $PROJ_DIR
        #
        #         # coregister fast-highres to epi
        #         echo "$SUBJ_NAME: coregister fast-highres to epi"
        #         [ ! -f $ROI_DIR/reg_epi/t1_wm_epi.nii.gz ] && $FSLDIR/bin/flirt -in $ROI_DIR/reg_t1/mask_t1_wm.nii.gz -ref $ROI_DIR/reg_epi/example_func -applyxfm -init $ROI_DIR/reg_epi/highres2epi.mat -out $ROI_DIR/reg_epi/t1_wm_epi.nii.gz
        #         [ ! -f $ROI_DIR/reg_epi/t1_csf_epi.nii.gz ] && $FSLDIR/bin/flirt -in $ROI_DIR/reg_t1/mask_t1_csf.nii.gz -ref $ROI_DIR/reg_epi/example_func -applyxfm -init $ROI_DIR/reg_epi/highres2epi.mat -out $ROI_DIR/reg_epi/t1_csf_epi.nii.gz
        #         [ ! -f $ROI_DIR/reg_epi/t1_gm_epi.nii.gz ] && $FSLDIR/bin/flirt -in $ROI_DIR/reg_t1/mask_t1_gm.nii.gz -ref $ROI_DIR/reg_epi/example_func -applyxfm -init $ROI_DIR/reg_epi/highres2epi.mat -out $ROI_DIR/reg_epi/t1_gm_epi.nii.gz
        #         [ ! -f $ROI_DIR/reg_epi/t1_brain_epi.nii.gz ] && $FSLDIR/bin/flirt -in $T1_BRAIN_DATA.nii.gz -ref $ROI_DIR/reg_epi/example_func -applyxfm -init $ROI_DIR/reg_epi/highres2epi.mat -out $ROI_DIR/reg_epi/t1_brain_epi.nii.gz
        #
        #         # mask & binarize
        #         $FSLDIR/bin/fslmaths $ROI_DIR/reg_epi/t1_gm_epi.nii.gz -thr 0.2 -bin $ROI_DIR/reg_epi/mask_t1_gm_epi.nii.gz
        #         $FSLDIR/bin/fslmaths $ROI_DIR/reg_epi/t1_wm_epi.nii.gz -thr 0.2 -bin $ROI_DIR/reg_epi/mask_t1_wm_epi.nii.gz
        #         $FSLDIR/bin/fslmaths $ROI_DIR/reg_epi/t1_csf_epi.nii.gz -thr 0.2 -bin $ROI_DIR/reg_epi/mask_t1_csf_epi.nii.gz
        #         $FSLDIR/bin/fslmaths $ROI_DIR/reg_epi/t1_brain_epi.nii.gz -thr 0.2 -bin $ROI_DIR/reg_epi/mask_t1_brain_epi.nii.gz
        #
        #   fi
        # fi
        #
        # #==============================================================================================================================================================
        # # T2 data
        # #==============================================================================================================================================================
        # if [ -d "$DE_DIR" ]; then
        #   if [ `$FSLDIR/bin/imtest $T2_DATA` = 1 ]; then
        #     HAS_T2=1
        #         mkdir -p $ROI_DIR/reg_t2
        #     if [ `$FSLDIR/bin/imtest $T2_BRAIN_DATA` = 0 ]; then
        #         echo "$SUBJ_NAME: bet on t2"
        #         $FSLDIR/bin/bet $T2_DATA $T2_BRAIN_DATA -f $BET_F_VALUE_T2 -g 0.2 -m
        #     fi
        #   fi
        # fi
        #
        # #==============================================================================================================================================================
        # # DTI data
        # #==============================================================================================================================================================
        # if [ -d "$DTI_DIR" ]; then
        #   if [ "$(ls -A $DTI_DIR)" ]; then
        #     if [ `$FSLDIR/bin/imtest $DTI_DIR/$DTI_FIT_LABEL"_FA"` = 0 -a $DO_DTIFIT -eq 1 ]; then
        #             echo "===========>>>> $SUBJ_NAME: dtifit"
        #             LOGFILE=$DTI_DIR/log_dti_processing.txt
        #
        #             run .	$GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_ec_fit.sh $SUBJ_NAME $PROJ_DIR
        #         run $FSLDIR/bin/fslmaths $DTI_DIR/$DTI_FIT_LABEL"_L2" -add $DTI_DIR/$DTI_FIT_LABEL"_L3" -div 2 $DTI_DIR/$DTI_FIT_LABEL"_L23"
        #             run .	$GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_autoPtx_preproc.sh $SUBJ_NAME $PROJ_DIR
        #     fi
        #     run mkdir -p $ROI_DIR/reg_dti
        #
        #     if [ $HAS_T2 -eq 1 ]; then 	run .	$GLOBAL_SUBJECT_SCRIPT_DIR/subject_transforms_calculate_dti_t2.sh $SUBJ_NAME $PROJ_DIR;
        #     else
        #         run .	$GLOBAL_SUBJECT_SCRIPT_DIR/subject_transforms_calculate_dti.sh $SUBJ_NAME $PROJ_DIR;
        #     fi
        #
        #     if [ ! -f $DTI_DIR/$BEDPOST_OUTDIR_NAME/mean_S0samples.nii.gz ]; then
        #             [ -f $DTI_DIR/$DTI_ROTATED_BVEC.gz ] && gunzip $DTI_DIR/$DTI_ROTATED_BVEC.gz
        #       [ -f $DTI_DIR/$DTI_BVAL.gz ] && gunzip $DTI_DIR/$DTI_BVAL.gz
        #
        #       if [ $DO_BEDPOST -eq 1 ]; then
        #             run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_bedpostx.sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME
        #           fi
        #
        #       if [ $DO_BEDPOST_CUDA -eq 1 ]; then
        #             run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_bedpostx_CUDA.sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME
        #           fi
        #         fi
        #
        #         if [ $DO_AUTOPTX_TRACT -eq 1 ]; then
        #             if [ ! -f $DTI_DIR/$BEDPOST_OUTDIR_NAME/mean_S0samples.nii.gz ]; then
        #                 echo "subj $SUBJ_NAME ,you requested the autoPtx tractorgraphy, but bedpostx was not performed.....skipping"
        #             else
        #                 . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_autoPtx_tractography.sh $SUBJ_NAME $PROJ_DIR
        #             fi
        #         fi
        #
        #         if [ $DO_STRUCT_CONN -eq 1 -a ! -f $TV_MATRICES_DIR/fa_AM.mat ]; then
        #             . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_conn_matrix.sh $SUBJ_NAME $PROJ_DIR
        #         fi
        #
        #
        #   fi
        # fi

        pass

    # ==================================================================================================================================================
    # ANATOMICAL
    # ==================================================================================================================================================
    # pre-processing:
    def anatomical_processing(self,
                        odn="anat", imgtype=1, smooth=10,
                        strongbias=True, do_biasrestore=True,
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
                if do_biasrestore is True:
                    if strongbias is True:
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

                        rrun("flirt -interp spline -dof 12 -in " + T1 + "_biascorr -ref " + os.path.join(self.fsl_data_standard, "MNI152_" + T1 + "_2mm") + " -dof 12 -omat " + T1 + "_to_MNI_lin.mat -out " + T1 + "_to_MNI_lin " + flirtargs, logFile=log)

                        if do_nonlinreg is True:
                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print( "Registering to standard space (non-linear)")
                            refmask = "MNI152_" + T1 + "_2mm_brain_mask_dil1"

                            rrun("fslmaths " + os.path.join(self.fsl_data_standard, "MNI152_" + T1 + "_2mm_brain_mask") + " -fillh -dilF " + refmask, logFile=log)
                            rrun("fnirt --in=" + T1 + "_biascorr --ref=" + os.path.join(self.fsl_data_standard, "MNI152_" + T1 + "_2mm") + " --fout=" + T1 + "_to_MNI_nonlin_field --jout=" + T1 + "_to_MNI_nonlin_jac --iout=" + T1 + "_to_MNI_nonlin --logout=" + T1 + "_to_MNI_nonlin.txt --cout=" + T1 + "_to_MNI_nonlin_coeff --config=" + os.path.join(self.fsl_dir, "etc", "flirtsch", T1 + "_2_MNI152_2mm.cnf") + " --aff=" + T1 + "_to_MNI_lin.mat --refmask=" + refmask + " " + fnirtargs, logFile=log)

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.label + " :Performing brain extraction (using FNIRT)")
                            rrun("invwarp --ref=" + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_coeff -o MNI_to_" + T1 + "_nonlin_field", logFile=log)
                            rrun("applywarp --interp=nn --in=" + os.path.join(self.fsl_data_standard, "MNI152_" + T1 + "_2mm_brain_mask") + " --ref=" + T1 + "_biascorr -w MNI_to_" + T1 + "_nonlin_field -o " + T1 + "_biascorr_brain_mask", logFile=log)
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
                        rrun("applywarp -i " + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_field -r " + os.path.join(self.fsl_data_standard, "MNI152_" + T1 + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline", logFile=log)

            #### SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION (only done if registration turned on, and segmentation done, and it is a T1 image)
            # required inputs: " + T1 + "_biascorr
            # output: " + T1 + "_vols.txt
            if os.path.isfile(T1 + "_vols.txt") is False or do_overwrite is True:

                if do_reg is True and do_seg is True and T1 == "T1":
                    print(self.label + " :Skull-constrained registration (linear)")

                    rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_bet -s -m " + betopts, logFile=log)
                    rrun("pairreg " + os.path.join(self.fsl_data_standard, "MNI152_T1_2mm_brain") + " " + T1 + "_biascorr_bet " + os.path.join(self.fsl_data_standard, "MNI152_T1_2mm_skull") + " " + T1 + "_biascorr_bet_skull " + T1 + "2std_skullcon.mat", logFile=log)

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
            inputimage  = self.t1_data
            anatdir     = os.path.join(self.t1_dir, odn)
            T1          = "T1";
        elif imgtype == 2:
            inputimage  = self.t2_data
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

            mass_images_move("*_to_MNI*", os.path.join(self.roi_dir, "reg_standard"), logFile=log)
            mass_images_move("*_to_T1*", os.path.join(self.roi_dir, "reg_t1"), logFile=log)

            run_move_notexisting_img(os.path.join(self.roi_dir, "reg_t1", "standard2highres_warp"), "immv " + os.path.join(self.roi_dir, "reg_t1", "MNI_to_T1_nonlin_field") + " " +  os.path.join(self.roi_dir, "reg_t1", "standard2highres_warp"), logFile=log)
            run_move_notexisting_img(os.path.join(self.roi_dir, "reg_standard", "highres2standard_warp"), "immv " + os.path.join(self.roi_dir, "reg_standard", "T1_to_MNI_nonlin_field") + " " +  os.path.join(self.roi_dir, "reg_standard", "highres2standard_warp"), logFile=log)

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

        output_roi_dir  = os.path.join(self.roi_dir, "reg_t1", odn)
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

    def dti_conn_matrix(self):
        pass

    # ==================================================================================================================================================
    # FUNCTIONAL
    # ==================================================================================================================================================

    def epi_resting_nuisance(self):
        pass

    def epi_feat(self):
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

    def transforms_mpr(self, stdimg="", stdimgmask="", stdimglabel=""):
        pass

        STD_IMAGE_LABEL = "standard"
        STD_IMAGE       = os.path.join(self.fsl_data_standard, "MNI152_T1_2mm_brain")
        STD_IMAGE_MASK  = os.path.join(self.fsl_data_standard, "MNI152_T1_2mm_brain_mask_dil")

        if imtest(STD_IMAGE) is False:
            print("file STD_IMAGE: " + STD_IMAGE + ".nii.gz is not present...skipping reg_nonlin_epi_t1_standard.sh")
            return

        if imtest(STD_IMAGE_MASK) is False:
            print("file STD_IMAGE_MASK: " + STD_IMAGE_MASK + ".nii.gz is not present...skipping reg_nonlin_epi_t1_standard.sh")
            return

        if imtest(self.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.t1_brain_data + ".nii.gz is not present...skipping reg_nonlin_epi_t1_standard.sh")
            return

        print( self.label + " :STARTED : nonlin t1-standard coregistration")

        # highres <--> standard

        os.makedirs(os.path.join(self.roi_dir, "reg_" + STD_IMAGE_LABEL), exist_ok=True)
        os.makedirs(os.path.join(self.roi_dir, "reg_" + STD_IMAGE_LABEL + "4"), exist_ok=True)
        os.makedirs(os.path.join(self.roi_dir, "reg_t1"), exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # ---- HIGHRES <--------> STANDARD
        # => highres2standard.mat
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

