import glob
import os
import shutil
import traceback
from copy import deepcopy
from shutil import move, rmtree

from utility.images.Image import Image
from utility.images.Images import Images
from utility.myfsl.utils.run import rrun
from subject.SubjectDti import SubjectDti
from subject.SubjectEpi import SubjectEpi
from subject.SubjectMpr import SubjectMpr
from subject.SubjectTransforms import SubjectTransforms
from utility.myfsl.fslfun import runsystem
from utility.fileutilities import extractall_zip, sed_inplace


class Subject:
    TYPE_T1 = 1
    TYPE_RS = 2
    TYPE_FMRI = 3
    TYPE_DTI = 4
    TYPE_DTI_B0 = 5     # does not have bval/bvec
    TYPE_T2 = 6

    def __init__(self, label, project, sessid=1, stdimg=""):

        self.label  = label
        self.sessid = sessid

        self.project = project
        self._global = project.globaldata

        self.fsl_dir            = self._global.fsl_dir
        self.fsl_bin            = self._global.fsl_bin
        self.fsl_data_std_dir   = self._global.fsl_data_std_dir

        self.project_subjects_dir = project.subjects_dir

        self.DCM2NII_IMAGE_FORMATS = [".nii", ".nii.gz", ".hdr", ".hdr.gz", ".img", ".img.gz"]

        self.set_templates(stdimg)
        self.set_properties(self.sessid)

        self.transform  = SubjectTransforms(self, self._global)
        self.mpr        = SubjectMpr(self, self._global)
        self.dti        = SubjectDti(self, self._global)
        self.epi        = SubjectEpi(self, self._global)

    @property
    def hasT1(self):
        return self.t1_data.exist

    @property
    def hasRS(self):
        return self.rs_data.exist

    @property
    def hasDTI(self):
        return self.dti_data.exist

    @property
    def hasT2(self):
        return self.t2_data.exist

    def hasFMRI(self, images=None):
        if images is None:
            return self.fmri_data.exist
        else:
            return Images(images).exist

    @property
    def hasWB(self):
        return self.wb_data.exist

    def get_properties(self, sess):
        return self.set_properties(sess, True)

    # this method has 2 usages:
    # 1) DEFAULT : to create filesystem names at startup    => returns : self  (DOUBT !! alternatively may always return a deepcopy)
    # 2) to get a copy with names of another session        => returns : deepcopy(self)
    def set_properties(self, sess, rollback=False):

        self.dir            = os.path.join(self.project.subjects_dir, self.label, "s" + str(sess))

        self.roi_dir        = os.path.join(self.dir, "roi")
        self.roi_t1_dir     = os.path.join(self.roi_dir, "reg_t1")
        self.roi_rs_dir     = os.path.join(self.roi_dir, "reg_rs")
        self.roi_fmri_dir   = os.path.join(self.roi_dir, "reg_fmri")
        self.roi_dti_dir    = os.path.join(self.roi_dir, "reg_dti")
        self.roi_t2_dir     = os.path.join(self.roi_dir, "reg_t2")

        self.roi_std_dir    = os.path.join(self.roi_dir, "reg_" + self.std_img_label)
        self.roi_std4_dir   = os.path.join(self.roi_dir, "reg_" + self.std_img_label + "4")

        # ------------------------------------------------------------------------------------------------------------------------
        # T1/MPR
        # ------------------------------------------------------------------------------------------------------------------------
        self.t1_image_label = self.label + "-t1"

        self.t1_dir         = os.path.join(self.dir, "mpr")
        self.t1_anat_dir    = os.path.join(self.t1_dir, "anat")
        self.fast_dir       = os.path.join(self.t1_dir, "fast")
        self.first_dir      = os.path.join(self.t1_dir, "first")
        self.sienax_dir     = os.path.join(self.t1_dir, "sienax")
        self.t1_fs_dir      = os.path.join(self.t1_dir, "freesurfer")
        self.t1_fs_mri_dir  = os.path.join(self.t1_fs_dir, "mri")
        self.t1_spm_dir     = os.path.join(self.t1_dir, "spm")
        self.t1_cat_dir     = os.path.join(self.t1_dir, "cat")

        self.t1_data                = Image(os.path.join(self.t1_dir, self.t1_image_label))
        self.t1_brain_data          = Image(os.path.join(self.t1_dir, self.t1_image_label + "_brain"))
        self.t1_brain_data_mask     = Image(os.path.join(self.t1_dir, self.t1_image_label + "_brain_mask"))
        self.t1_fs_brainmask_data   = Image(os.path.join(self.t1_fs_dir, "mri", "brainmask"))
        self.t1_fs_data             = Image(os.path.join(self.t1_fs_dir, "mri", "T1"))  # T1 coronal [1x1x1] after conform
        self.t1_fs_aparc_aseg       = Image(os.path.join(self.t1_fs_dir, "mri", "aparc+aseg.mgz"))  # output of freesurfer

        self.first_all_none_origsegs = Image(os.path.join(self.first_dir, self.t1_image_label + "_all_none_origsegs"))
        self.first_all_fast_origsegs = Image(os.path.join(self.first_dir, self.t1_image_label + "_all_fast_origsegs"))

        self.t1_segment_gm_path         = Image(os.path.join(self.roi_t1_dir, "mask_t1_gm"))
        self.t1_segment_wm_path         = Image(os.path.join(self.roi_t1_dir, "mask_t1_wm"))
        self.t1_segment_csf_path        = Image(os.path.join(self.roi_t1_dir, "mask_t1_csf"))
        self.t1_segment_wm_bbr_path     = Image(os.path.join(self.roi_t1_dir, "wmseg4bbr"))
        self.t1_segment_wm_ero_path     = Image(os.path.join(self.roi_t1_dir, "mask_t1_wmseg4Nuisance"))
        self.t1_segment_csf_ero_path    = Image(os.path.join(self.roi_t1_dir, "mask_t1_csfseg4Nuisance"))

        self.t1_cat_surface_dir         = os.path.join(self.t1_cat_dir, "surf")
        self.t1_cat_surface_resamplefilt= self._global.cat_smooth_surf
        self.t1_cat_lh_surface          = Image(os.path.join(self.t1_cat_surface_dir, "lh.thickness.T1_" + self.label))
        self.t1_cat_resampled_surface   = Image(os.path.join(self.t1_cat_surface_dir, "s" + str(self.t1_cat_surface_resamplefilt) + ".mesh.thickness.resampled_32k.T1_" + self.label + ".gii"))
        self.t1_cat_resampled_surface_longitudinal = Image(os.path.join(self.t1_cat_surface_dir, "s" + str(self.t1_cat_surface_resamplefilt) + ".mesh.thickness.resampled_32k.rT1_" + self.label + ".gii"))

        self.t1_dartel_c1               = Image(os.path.join(self.t1_spm_dir, "c1T1_" + self.label))
        self.t1_dartel_rc1              = Image(os.path.join(self.t1_spm_dir, "rc1T1_" + self.label))
        self.t1_dartel_rc2              = Image(os.path.join(self.t1_spm_dir, "rc2T1_" + self.label))

        self.t1_spm_icv_file = os.path.join(self.t1_spm_dir, "icv_" + self.label + ".dat")

        # ------------------------------------------------------------------------------------------------------------------------
        # DTI
        # ------------------------------------------------------------------------------------------------------------------------
        self.dti_image_label    = self.label + "-dti"
        self.dti_ec_image_label = self.dti_image_label + "_ec"
        self.dti_fit_label      = self.dti_image_label + "_fit"

        self.dti_dir            = os.path.join(self.dir, "dti")
        self.bedpost_X_dir      = os.path.join(self.dti_dir, "bedpostx")
        self.probtrackx_dir     = os.path.join(self.dti_dir, "probtrackx")
        self.trackvis_dir       = os.path.join(self.dti_dir, "trackvis")
        self.tv_matrices_dir    = os.path.join(self.dti_dir, "tv_matrices")
        self.dti_xtract_dir     = os.path.join(self.dti_dir, "xtract")

        self.dti_bval           = os.path.join(self.dti_dir, self.label + "-dti.bval")
        self.dti_bvec           = os.path.join(self.dti_dir, self.label + "-dti.bvec")
        self.dti_rotated_bvec   = os.path.join(self.dti_dir, self.label + "-dti_rotated.bvec")
        self.dti_eddyrotated_bvec = os.path.join(self.dti_dir, self.label + "-dti_ec.eddy_rotated_bvecs")

        self.dti_data           = Image(os.path.join(self.dti_dir, self.dti_image_label))
        self.dti_pa_data        = Image(os.path.join(self.dti_dir, self.dti_image_label + "_PA"))
        self.dti_ec_data        = Image(os.path.join(self.dti_dir, self.dti_ec_image_label))
        self.dti_fit_data       = Image(os.path.join(self.dti_dir, self.dti_fit_label))

        self.dti_nodiff_data            = Image(os.path.join(self.roi_dti_dir, "nodif"))
        self.dti_nodiff_brain_data      = Image(os.path.join(self.roi_dti_dir, "nodif_brain"))
        self.dti_nodiff_brainmask_data  = Image(os.path.join(self.roi_dti_dir, "nodif_brain_mask"))

        self.dti_fit_FA                 = Image(os.path.join(self.dti_dir, self.dti_fit_label + "_FA"))
        self.dti_fit_MD                 = Image(os.path.join(self.dti_dir, self.dti_fit_label + "_MD"))
        self.dti_fit_L1                 = Image(os.path.join(self.dti_dir, self.dti_fit_label + "_L1"))
        self.dti_fit_L23                = Image(os.path.join(self.dti_dir, self.dti_fit_label + "_L23"))

        self.dti_bedpostx_mean_S0_label = "mean_S0samples"

        self.trackvis_transposed_bvecs = "bvec_vert.txt"

        # ------------------------------------------------------------------------------------------------------------------------
        # RS
        # ------------------------------------------------------------------------------------------------------------------------
        self.rs_image_label = self.label + "-rs"

        self.rs_dir         = os.path.join(self.dir, "resting")
        self.rs_data        = Image(os.path.join(self.rs_dir, self.rs_image_label))
        self.rs_data_dist   = Image(os.path.join(self.rs_dir, self.rs_image_label + "_distorted"))
        self.rs_pa_data     = Image(os.path.join(self.rs_dir, self.rs_image_label + "_PA"))
        self.rs_pa_data2    = Image(os.path.join(self.rs_dir, self.rs_image_label + "_PA2"))

        self.sbfc_dir           = os.path.join(self.rs_dir, "sbfc")
        self.rs_series_dir      = os.path.join(self.sbfc_dir, "series")
        self.rs_melic_dir       = os.path.join(self.rs_dir, "melic")
        self.rs_default_mel_dir = os.path.join(self.rs_dir, "postmel.ica")

        self.rs_examplefunc         = Image(os.path.join(self.roi_rs_dir, "example_func"))
        self.rs_examplefunc_mask    = Image(os.path.join(self.roi_rs_dir, "mask_example_func"))

        self.rs_series_csf          = os.path.join(self.rs_series_dir, "csf_ts")
        self.rs_series_wm           = os.path.join(self.rs_series_dir, "wm_ts")

        self.rs_final_regstd_dir    = os.path.join(self.rs_dir, "reg_" + self.std_img_label)

        self.rs_final_regstd_image      = Image(os.path.join(self.rs_final_regstd_dir, "filtered_func_data"))  # image after first preprocessing, aroma and nuisance regression.
        self.rs_final_regstd_mask       = Image(os.path.join(self.rs_final_regstd_dir, "mask"))  # image after first preprocessing, aroma and nuisance regression.
        self.rs_final_regstd_bgimage    = Image(os.path.join(self.rs_final_regstd_dir, "bg_image"))  # image after first preprocessing, aroma and nuisance regression.

        self.rs_post_preprocess_image_label         = self.rs_image_label + "_preproc"
        self.rs_post_aroma_image_label              = self.rs_image_label + "_preproc_aroma"
        self.rs_post_nuisance_image_label           = self.rs_image_label + "_preproc_aroma_nuisance"
        self.rs_post_nuisance_melodic_image_label   = self.rs_image_label + "_preproc_aroma_nuisance_melodic"

        self.rs_aroma_dir           = os.path.join(self.rs_dir, "ica_aroma")
        self.rs_fix_dir             = os.path.join(self.rs_dir, "fix")
        self.rs_aroma_image         = Image(os.path.join(self.rs_aroma_dir, "denoised_func_data_nonaggr"))
        self.rs_regstd_aroma_dir    = os.path.join(self.rs_aroma_dir, "reg_standard")
        self.rs_regstd_aroma_image  = Image(os.path.join(self.rs_regstd_aroma_dir, "filtered_func_data"))

        self.rs_mask_t1_wmseg4nuis  = Image(os.path.join(self.roi_dir, "reg_rs", "mask_t1_wmseg4Nuisance_rs"))
        self.rs_mask_t1_csfseg4nuis = Image(os.path.join(self.roi_dir, "reg_rs", "mask_t1_csfseg4Nuisance_rs"))

        # self.rs_post_nuisance_std4_image_label          = self.rs_image_label + "_preproc_aroma_nuisance_std4"
        # self.rs_post_nuisance_melodic_std4_image_label  = self.rs_image_label + "_preproc_aroma_nuisance_melodic_std4"
        # self.rs_regstd_dir              = os.path.join(self.rs_dir, "resting.ica", "reg_std")
        # self.rs_regstd_image            = os.path.join(self.rs_regstd_dir, "filtered_func_data")
        # self.rs_regstd_denoise_dir      = os.path.join(self.rs_dir, "resting.ica", "reg_std_denoised")
        # self.rs_regstd_denoise_image    = os.path.join(self.rs_regstd_denoise_dir, "filtered_func_data")

        # self.mc_params_dir  = os.path.join(self.rs_dir, self.rs_image_label + ".ica", "mc")
        # self.mc_abs_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_abs_mean.rms")
        # self.mc_rel_displ   = os.path.join(self.mc_params_dir, "prefiltered_func_data_mcf_rel_mean.rms")

        # ------------------------------------------------------------------------------------------------------------------------
        # fMRI
        # ------------------------------------------------------------------------------------------------------------------------
        self.fmri_image_label = self.label + "-fmri"

        self.fmri_dir       = os.path.join(self.dir, "fmri")
        self.fmri_data      = Image(os.path.join(self.fmri_dir, self.fmri_image_label))
        self.fmri_pa_data   = Image(os.path.join(self.fmri_dir, self.fmri_image_label + "_PA"))
        self.fmri_pa_data2  = Image(os.path.join(self.fmri_dir, self.fmri_image_label + "_PA2"))

        self.fmri_data_mc           = Image(os.path.join(self.fmri_dir, "ra" + self.fmri_image_label))   # assumes motion correction after slice timings

        self.fmri_examplefunc       = Image(os.path.join(self.roi_fmri_dir, "example_func"))
        self.fmri_examplefunc_mask  = Image(os.path.join(self.roi_fmri_dir, "mask_example_func"))

        self.fmri_aroma_dir             = os.path.join(self.fmri_dir, "ica_aroma")
        self.fmri_icafix_dir            = os.path.join(self.fmri_dir, "ica_fix")
        self.fmri_aroma_image           = Image(os.path.join(self.fmri_aroma_dir, "denoised_func_data_nonaggr"))
        self.fmri_regstd_aroma_dir      = os.path.join(self.fmri_aroma_dir, "reg_standard")
        self.fmri_regstd_aroma_image    = Image(os.path.join(self.fmri_regstd_aroma_dir, "filtered_func_data"))

        # ------------------------------------------------------------------------------------------------------------------------
        # WB
        # ------------------------------------------------------------------------------------------------------------------------
        self.wb_image_label = self.label + "-wb_epi"

        self.wb_dir         = os.path.join(self.dir, "wb")
        self.wb_data        = Image(os.path.join(self.wb_dir, self.wb_image_label))
        self.wb_brain_data  = Image(os.path.join(self.wb_dir, self.wb_image_label + "_brain"))

        # ------------------------------------------------------------------------------------------------------------------------
        # T2
        # ------------------------------------------------------------------------------------------------------------------------
        self.t2_image_label = self.label + "-t2"

        self.t2_dir         = os.path.join(self.dir, "t2")
        self.t2_data        = Image(os.path.join(self.t2_dir, self.t2_image_label))
        self.t2_brain_data  = Image(os.path.join(self.t2_dir, self.t2_image_label + "_brain"))

        # ------------------------------------------------------------------------------------------------------------------------
        # DE
        # ------------------------------------------------------------------------------------------------------------------------
        self.de_image_label = self.label + "-de"
        self.de_dir         = os.path.join(self.dir, "de")
        self.de_data        = Image(os.path.join(self.de_dir, self.de_image_label))
        self.de_brain_data  = Image(os.path.join(self.de_dir, self.de_image_label + "_brain"))

        # ------------------------------------------------------------------------------------------------------------------------
        self_copy = deepcopy(self)
        if rollback:
            self.set_properties(self.sessid, False)
            return self_copy
        else:
            self.sessid = sess
            return self

    def set_templates(self, stdimg=""):

        if stdimg == "":

            self.std_img_label = "std"

            self.std_img            = Image(self._global.fsl_std_mni_2mm_brain)
            self.std_head_img       = Image(self._global.fsl_std_mni_2mm_head)
            self.std_img_mask_dil   = Image(self._global.fsl_std_mni_2mm_brain_mask_dil)

            self.std4_img           = Image(self._global.fsl_std_mni_4mm_brain)
            self.std4_head_img      = Image(self._global.fsl_std_mni_4mm_head)
            self.std4_img_mask_dil  = Image(self._global.fsl_std_mni_4mm_brain_mask_dil)
        else:

            # assumes to receive the full path of standard head. e.g. "/.../.../.../pediatric.nii.gz"
            self.std_head_img       = Image(stdimg)

            if not self.std_head_img.exist:
                raise Exception("given standard image does not exist")

            imgdir              = self.std_head_img.dir
            self.std_img_label  = self.std_head_img.name

            self.std_img            = Image(os.path.join(imgdir, self.std_img_label + "_brain"))  # "pediatric_brain"
            self.std_img_mask_dil   = Image(os.path.join(imgdir, self.std_img_label + "_brain_mask_dil"))  # "pediatric_brain_mask_dil"

            self.std4_head_img      = Image(os.path.join(imgdir, self.std_img_label + "4"))  # "pediatric4"
            self.std4_img           = Image(os.path.join(imgdir, self.std_img_label + "4_brain"))  # "pediatric4_brain"
            self.std4_img_mask_dil  = Image(os.path.join(imgdir, self.std_img_label + "4_brain_mask_dil")) # "pediatric4_brain_mask_dil"

            if not self.std_img.exist or not self.std4_head_img.exist or not self.std4_img.exist:
                raise Exception("Error in set_templates")

            # check resolution
            res1 = self.std4_head_img.read_header(["dx"])["dx"]
            res2 = self.std4_img.read_header(["dx"])["dx"]
            if res1 != "4" or res2 != "4":
                raise Exception("Error in set_templates. given custom 4mm template have a different resolution")

    # ==================================================================================================
    # GENERAL
    # ==================================================================================================
    def exist(self):
        return os.path.exists(self.dir)

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

    def rename(self, new_label, session_id=1):

        for path, subdirs, files in os.walk(self.dir):
            for name in files:
                if self.label in name:
                    file_path = os.path.join(path, name)
                    new_name = os.path.join(path, name.replace(self.label, new_label))
                    os.rename(file_path, new_name)

        # rename special file
        # in sXX.mesh.thickness.resampled_32K.....gii, it loads the corresponding .dat, change such reference)
        new_t1_cat_resampled_surface = Image(os.path.join(self.t1_cat_surface_dir, "s" + str(self.t1_cat_surface_resamplefilt) + ".mesh.thickness.resampled_32k.T1_" + new_label + ".gii"))
        sed_inplace(new_t1_cat_resampled_surface, self.label, new_label)

        os.makedirs(os.path.join(self.project.dir, "subjects", new_label))
        os.rename(self.dir, os.path.join(self.project.dir, "subjects", new_label, "s" + str(session_id)))
        rmtree(os.path.join(self.project.dir, "subjects", self.label))

    def check_images(self, t1=False, rs=False, dti=False, t2=False, fmri=None):

        missing_images = []

        if t1:
            if not self.t1_data.exist:
                missing_images.append("t1")

        if rs:
            if not self.rs_data.exist:
                missing_images.append("rs")

        if fmri is not None:

            for s in fmri:
                fmri_img = Image(os.path.join(self.fmri_dir, self.label + s))
                if not fmri_img.exist:
                    missing_images.append(fmri_img)

        if dti:
            if not self.dti_data.exist:
                missing_images.append("dti")

        if t2:
            if not self.t2_data.exist:
                missing_images.append("t2")

        if len(missing_images) > 0:
            missing_images.insert(0, "---------------------------------------------------------------> " + self.label)

        print(missing_images)

        return missing_images

    def check_template(self):

        can_process_std4 = True
        missing_images = ""

        if not self.t1_brain_data.exist:
            print("file T1_BRAIN_DATA: " + self.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            missing_images = missing_images + "T1_BRAIN_DATA: " + self.t1_brain_data + " "

        if not self.t1_data.exist:
            print("file T1_DATA: " + self.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            missing_images = missing_images + "T1_DATA: " + self.t1_data + " "

        # check template
        if not self.std_img.exist:
            print("ERROR: file std_img: " + self.std_img + ".nii.gz is not present...exiting transforms_mpr")
            missing_images = missing_images + "T1_DATA: " + self.t1_data + " "

        if not self.std_head_img.exist:
            print("ERROR: file std_img: " + self.std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            missing_images = missing_images + "T1_DATA: " + self.t1_data + " "

        if not self.std_img_mask_dil.exist:
            print(
                "ERROR: file std_img_mask_dil: " + self.std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            missing_images = missing_images + "T1_DATA: " + self.t1_data + " "

        if not self.std4_img.exist:
            print("WARNING: file std4_img: " + self.std4_img + ".nii.gz is not present...skipping STD4 transform")
            can_process_std4 = False

        if not self.std4_head_img.exist:
            print(
                "WARNING: file std4_head_img: " + self.std4_head_img + ".nii.gz is not present...skipping STD4 transform")
            can_process_std4 = False

        if not self.std4_img_mask_dil.exist:
            print(
                "WARNING: file std4_img_mask_dil: " + self.std4_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")
            can_process_std4 = False

        return missing_images, can_process_std4

    def reslice_image(self, direction):

        if direction == "sag->axial":
            bckfilename = self.t1_image_label + "_sag"
            conversion_str = " -z -x y "
        else:
            print("invalid conversion")
            return

        bckfilepath = Image(os.path.join(self.t1_dir, bckfilename))
        if bckfilepath.exist:
            return

        self.t1_data.cp(bckfilepath)  # create backup copy
        rrun("fslswapdim " + self.t1_data + conversion_str + self.t1_data)  # run reslicing

    # ==================================================================================================================================================
    # WELCOME
    # ==================================================================================================================================================
    def wellcome(self, do_overwrite=False,
                 do_fslanat=True, odn="anat", imgtype=1, smooth=10,
                 biascorr_type=SubjectMpr.BIAS_TYPE_STRONG,
                 do_reorient=True, do_crop=True,
                 do_bet=True, betfparam=None,
                 do_sienax=False, bet_sienax_param_string="-SNB -f 0.2",
                 do_reg=True, do_nonlinreg=True, do_seg=True,
                 do_spm_seg=False, spm_seg_templ="", spm_seg_over_bet=False,
                 do_cat_seg=False, cat_use_dartel=False, do_cat_surf=True, cat_smooth_surf=None,
                 do_cat_seg_long=False, cat_long_sessions=None,
                 do_cleanup=True, do_strongcleanup=False,
                 use_lesionmask=False, lesionmask="lesionmask",
                 do_freesurfer=False, do_complete_fs=False, fs_seg_over_bet=False,
                 do_first=False, first_struct="", first_odn="",

                 do_susc_corr=False,

                 do_rs=True, do_epirm2vol=0, rs_pa_data=None,
                 do_aroma=True, do_nuisance=True, hpfsec=100, feat_preproc_odn="resting", feat_preproc_model="singlesubj_feat_preproc_noreg_melodic",
                 do_featinitreg=False, do_melodic=True, mel_odn="postmel", mel_preproc_model="singlesubj_melodic_noreg", do_melinitreg=False, replace_std_filtfun=True,

                 do_fmri=True, fmri_params=None, fmri_images=None, fmri_pa_data=None,

                 do_dtifit=True, do_pa_eddy=False, do_eddy_gpu=False, do_bedx=False, do_bedx_gpu=False, bedpost_odn="bedpostx",
                 do_xtract=False, xtract_odn="xtract", xtract_refspace="native", xtract_gpu=False, xtract_meas="vol,prob,length,FA,MD,L1,L23",
                 do_struct_conn=False, struct_conn_atlas_path="freesurfer", struct_conn_atlas_nroi=0):

        if cat_long_sessions is None:
            cat_long_sessions = [1]

        if betfparam is None:
            betfparam = [0.5]

        BET_F_VALUE_T2      = "0.5"
        feat_preproc_model  = os.path.join(self.project.script_dir, "glm", "templates", feat_preproc_model)
        melodic_model       = os.path.join(self.project.script_dir, "glm", "templates", mel_preproc_model)

        # ==============================================================================================================================================================
        #  T1 data
        # ==============================================================================================================================================================
        if self.hasT1:

            os.makedirs(self.roi_t1_dir, exist_ok=True)
            os.makedirs(self.roi_std_dir, exist_ok=True)
            os.makedirs(self.fast_dir, exist_ok=True)

            if do_fslanat:
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

                if do_spm_seg:
                    self.mpr.spm_segment(
                        odn=odn,
                        do_bet_overwrite=spm_seg_over_bet,
                        do_overwrite=do_overwrite,
                        seg_templ=spm_seg_templ,
                        spm_template_name="subj_spm_segment_tissuevolume")

                if do_cat_seg:
                    self.mpr.cat_segment(
                        odn=odn,
                        do_overwrite=do_overwrite,
                        spm_template_name=self._global.cat_template_name,
                        use_dartel=cat_use_dartel,
                        calc_surfaces=do_cat_surf,
                        smooth_surf=cat_smooth_surf)

                if do_cat_seg_long:
                    self.mpr.cat_segment_longitudinal(
                        cat_long_sessions,
                        do_overwrite=do_overwrite,
                        spm_template_name=self._global.cat_template_name,
                        use_dartel=cat_use_dartel,
                        calc_surfaces=do_cat_surf,
                        smooth_surf=cat_smooth_surf)

                if do_freesurfer:
                    if do_complete_fs:
                        fs_step = "-all"
                    else:
                        fs_step = "-autorecon1"
                    self.mpr.fs_reconall(step=fs_step, do_overwrite=do_overwrite)

                    if fs_seg_over_bet:
                        self.mpr.use_fs_brainmask()

                self.mpr.postbet(
                    odn=odn, imgtype=imgtype, smooth=smooth,
                    betfparam=betfparam,
                    do_reg=do_reg, do_nonlinreg=do_nonlinreg,
                    do_seg=do_seg,
                    do_cleanup=do_cleanup, do_strongcleanup=do_strongcleanup, do_overwrite=do_overwrite,
                    use_lesionmask=use_lesionmask, lesionmask=lesionmask)

                self.mpr.finalize(odn=odn)
                self.transform.transform_mpr()

            if do_sienax:
                print(self.label + " : sienax with " + bet_sienax_param_string)
                rrun("sienax " + self.t1_data + " -B " + bet_sienax_param_string + " -r")

            if do_first:
                if not self.first_all_fast_origsegs.exist and not self.first_all_none_origsegs.exist:
                    self.mpr.first(first_struct, odn=first_odn)

        # ==============================================================================================================================================================
        # WB data
        # ==============================================================================================================================================================
        if self.hasWB:
            if self.wb_data.exist:
                if not self.wb_brain_data.exist:
                    print(self.label + " : bet on WB")
                    rrun("bet " + self.wb_data + " " + self.wb_brain_data + " -f " + BET_F_VALUE_T2 + " -g 0 -m")

        # ==============================================================================================================================================================
        # RS data
        # ==============================================================================================================================================================
        # preprocessing step considered valid (filtered_func_data, bg_image and mask)
        # is stored in resting/reg_std with a resolution of 4mm to be used for melodic group analysis
        while self.hasRS:
            os.makedirs(self.roi_rs_dir, exist_ok=True)

            if do_rs:
                log_file = os.path.join(self.rs_dir, "log_rs_processing.txt")
                log = open(log_file, "a")

                os.makedirs(os.path.join(self.project.group_analysis_dir, "resting", "dr"), exist_ok=True)
                os.makedirs(os.path.join(self.project.group_analysis_dir, "resting", "group_templates"), exist_ok=True)
                os.makedirs(self.rs_final_regstd_dir, exist_ok=True)

                # ------------------------------------------------------------------------------------------------------
                # remove first volumes ?
                # ------------------------------------------------------------------------------------------------------
                if do_epirm2vol > 0:
                    # check if I have to remove the first (TOT_VOL-DO_RMVOL_TO_NUM) volumes
                    tot_vol_num = int(rrun("fslnvols " + self.rs_data, logFile=log).split('\n')[0])

                    vol2remove = tot_vol_num - do_epirm2vol

                    if vol2remove > 0:
                        try:
                            self.rs_data.mv(self.rs_data.fpathnoext + "_fullvol", logFile=log)
                            rrun("fslroi " + self.rs_data + "_fullvol " + self.rs_data + " " + str(vol2remove) + " -1", logFile=log)
                        except Exception as e:
                            print("UNRECOVERABLE ERROR: " + str(e))
                            Image(self.rs_data.fpathnoext + "_fullvol").mv(self.rs_data, logFile=log)
                            break

                # ------------------------------------------------------------------------------------------------------
                # susceptibility correction ?
                # ------------------------------------------------------------------------------------------------------
                if do_susc_corr:        # want to correct
                    ap_distorted = self.rs_data.add_postfix2name("_distorted")

                    if rs_pa_data is None:
                        rs_pa_data = self.rs_pa_data
                    rs_pa_data = Image(rs_pa_data)  # don't want an exception, create without must_exist and then simply break if does not exist
                    if not rs_pa_data.exist:
                        print("Error in welcome...user want to correct for susceptibility but PA image does not exist...skip rs processing...continue other")
                        break

                    if ap_distorted.exist and self.rs_data.exist and not do_overwrite:
                        pass    # already done and I don't want to re-do it
                    else:
                        if ap_distorted.exist:              # already done  ==> rollback changes
                            self.rs_data.rm(logFile=log)
                            ap_distorted.cp(self.rs_data, logFile=log)
                        else:        # never done ==> create backup copy
                            self.rs_data.cp(ap_distorted, logFile=log)

                        try:
                            self.epi.topup_corrections([self.rs_data], rs_pa_data, self.project.topup_rs_params, motion_corr=False, logFile=log)
                        except Exception as e:
                            print("UNRECOVERABLE ERROR: " + str(e))
                            ap_distorted.mv(self.rs_data, logFile=log)
                            break

                # ------------------------------------------------------------------------------------------------------
                # FEAT PRE PROCESSING  (hp filt, mcflirt, spatial smoothing, melodic exploration, NO REG)
                # ------------------------------------------------------------------------------------------------------
                preproc_img         = Image(os.path.join(self.rs_dir, self.rs_post_preprocess_image_label))  # output image of first preproc resting.featfeat
                filtfuncdata        = Image(os.path.join(self.rs_dir, feat_preproc_odn + ".feat", "filtered_func_data"))
                preproc_feat_dir    = os.path.join(self.rs_dir, feat_preproc_odn + ".feat")  # /s1/resting/resting.feat
                if not preproc_img.exist:
                    if not os.path.isfile(feat_preproc_model + ".fsf"):
                        print("===========>>>> FEAT_PREPROC template file (" + self.label + " " + feat_preproc_model + ".fsf) is missing...skipping feat preprocessing")
                    else:
                        if os.path.isdir(preproc_feat_dir):
                            rmtree(preproc_feat_dir, ignore_errors=True)

                        self.epi.fsl_feat("rs", self.rs_image_label, "resting.feat", feat_preproc_model, do_initreg=do_featinitreg, std_image=self.std_img)
                        filtfuncdata.cp(preproc_img, logFile=log)

                # calculate all trasformations once (I do it here after MCFLIRT acted on images)
                self.transform.transform_rs(overwrite=do_overwrite, logFile=log)  # create self.subject.rs_examplefunc, epi2std/str2epi.nii.gz,  epi2std/std2epi_warp

                # ------------------------------------------------------------------------------------------------------
                # AROMA processing
                # ------------------------------------------------------------------------------------------------------
                preproc_aroma_img           = Image(os.path.join(self.rs_dir, self.rs_post_aroma_image_label))  # output image of aroma processing
                preproc_feat_dir_mc         = os.path.join(preproc_feat_dir, "mc", "prefiltered_func_data_mcf.par")
                # preproc_feat_dir_melodic    = os.path.join(preproc_feat_dir, "filtered_func_data.ica")
                # aff                         = self.transform.rs2hr_mat

                try:
                    if do_aroma:
                        if not preproc_aroma_img.exist:
                            if os.path.isdir(self.rs_aroma_dir):
                                rmtree(self.rs_aroma_dir, ignore_errors=True)

                            self.epi.aroma_feat("rs", preproc_feat_dir, preproc_feat_dir_mc, self.transform.rs2hr_mat, self.transform.hr2std_warp)
                            self.rs_aroma_image.cp(os.path.join(self.rs_dir, self.rs_post_aroma_image_label), logFile=log)
                    else:
                        preproc_img.cp(preproc_aroma_img, logFile=log)

                except Exception as e:
                    print("UNRECOVERABLE ERROR: " + str(e))
                    break

                # ------------------------------------------------------------------------------------------------------
                # do nuisance removal (WM, CSF & highpass temporal filtering)....create the following file: $RS_IMAGE_LABEL"_preproc_aroma_nuisance"
                # ------------------------------------------------------------------------------------------------------
                postnuisance = Image(os.path.join(self.rs_dir, self.rs_post_nuisance_image_label))
                if do_nuisance:
                    if not postnuisance.exist:
                        self.epi.remove_nuisance(self.rs_post_aroma_image_label, self.rs_post_nuisance_image_label, hpfsec=hpfsec)
                else:
                    preproc_aroma_img.cp(postnuisance)

                # ------------------------------------------------------------------------------------------------------
                # MELODIC (ONLY new melodic exploration, NO : reg, hpf, smooth) .....doing another MC and HPF results seemed to improve...although they should not...something that should be investigated....
                # ------------------------------------------------------------------------------------------------------
                mel_out_dir = os.path.join(self.rs_dir, mel_odn + ".ica")
                postmel_img = Image(os.path.join(self.rs_dir, self.rs_post_nuisance_melodic_image_label))

                if not postmel_img.exist and do_melodic:
                    if not os.path.isfile(melodic_model + ".fsf"):
                        print("===========>>>> resting template file (" + self.label + " " + melodic_model + ".fsf) is missing...skipping 1st level rs")
                    else:
                        if os.path.isdir(mel_out_dir):
                            rmtree(mel_out_dir, ignore_errors=True)

                        self.epi.fsl_feat("rs", self.rs_post_nuisance_image_label, mel_odn + ".ica", melodic_model,
                                          do_initreg=do_melinitreg,
                                          std_image=self.std_img)  # run . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_epi_feat.sh $SUBJ_NAME $PROJ_DIR -model $MELODIC_MODEL -odn $MELODIC_OUTPUT_DIR.ica -std_img $STANDARD_IMAGE -initreg $DO_FEAT_PREPROC_INIT_REG -ifn $RS_POST_NUISANCE_IMAGE_LABEL
                        Image(os.path.join(mel_out_dir, "filtered_func_data")).cp(postmel_img, logFile=log)

                # ------------------------------------------------------------------------------------------------------
                # CREATE STANDARD 4MM IMAGES FOR MELODIC
                # ------------------------------------------------------------------------------------------------------
                if replace_std_filtfun:
                    self.epi.create_regstd(postnuisance, feat_preproc_odn, do_overwrite, log)

                log.close()

            break

        # ==============================================================================================================================================================
        # FMRI DATA
        # ==============================================================================================================================================================
        while self.hasFMRI(fmri_images) and do_fmri:

            # sanity checks
            if fmri_params is None:
                raise Exception("Error in Subject.wellcome of subj " + self.label)

            if fmri_images is None:
                fmri_images = Images([self.fmri_data])
            else:
                fmri_images = Images(fmri_images)

            if not fmri_images.exist:
                print("Error in welcome...user want to perform fmri analysis but fmri image(s) does not exist...skip fmri processing...continue other")
                break

            log_file    = os.path.join(self.fmri_dir, "log_fmri_processing.txt")
            log         = open(log_file, "a")

            # ------------------------------------------------------------------------------------------------------
            # if susceptibility correction is selected. it performs topup correction after motion correction (realignment).
            # ------------------------------------------------------------------------------------------------------
            if do_susc_corr:        # want to correct
                ap_distorted = fmri_images.add_postfix2name("_distorted")

                if fmri_pa_data is None:
                    fmri_pa_data = self.fmri_pa_data
                fmri_pa_data = Image(fmri_pa_data)  # don't want an exception, create without must_exist and then simply break if does not exist
                if not fmri_pa_data.exist:
                    print("Error in welcome...user want to correct for susceptibility but PA image does not exist...skip fmri processing...continue other")
                    break

                if ap_distorted.exist and fmri_images.exist and not do_overwrite:
                    pass  # already done and I don't want to re-do it
                else:
                    if ap_distorted.exist:          # already done  ==> rollback changes
                        fmri_images.rm(logFile=log)
                        ap_distorted.cp(fmri_images, logFile=log)
                    else:                           # never done ==> create backup copy
                        fmri_images.cp(ap_distorted, logFile=log)

                    try:
                        self.epi.topup_corrections(fmri_images, fmri_pa_data, self.project.topup_fmri_params, motion_corr=True, logFile=log)
                    except Exception as e:
                        print("UNRECOVERABLE ERROR: " + str(e))
                        ap_distorted.mv(fmri_images, logFile=log)
                        break

                self.epi.spm_fmri_preprocessing(fmri_params, fmri_images, "subj_spm_fmri_preprocessing_norealign", do_overwrite=do_overwrite)

            else:
                self.epi.spm_fmri_preprocessing(fmri_params, fmri_images, "subj_spm_fmri_full_preprocessing", do_overwrite=do_overwrite)

            self.transform.transform_fmri(fmri_images, logFile=log)  # create self.subject.fmri_examplefunc, epi2std/str2epi.nii.gz,  epi2std/std2epi_warp
            break

        # ==============================================================================================================================================================
        # T2 data
        # ==============================================================================================================================================================
        if self.hasT2:

            os.makedirs(os.path.join(self.roi_dir, "reg_t2"), exist_ok=True)

            if not self.t2_brain_data:
                print(self.label + " : bet on t2")
                rrun("bet " + self.t2_data + " " + self.t2_brain_data + " -f " + BET_F_VALUE_T2 + " -g 0.2 -m")

        # ==============================================================================================================================================================
        # DTI data
        # ==============================================================================================================================================================
        while self.hasDTI:

            log_file = os.path.join(self.dti_dir, "log_dti_processing.txt")
            log = open(log_file, "a")

            self.dti.get_nodiff()  # create nodif & nodif_brain in roi/reg_dti

            if not self.dti_fit_FA.exist and do_dtifit:
                print("===========>>>> " + self.label + " : dtifit")

                if not do_pa_eddy:
                    self.dti.eddy_correct(do_overwrite, log)
                else:
                    if do_eddy_gpu:
                        self.dti.eddy(exe_ver=self._global.eddy_gpu_exe_name, logFile=log)
                    else:
                        self.dti.eddy(exe_ver="eddy_openmp", logFile=log)

                self.dti.fit(log)

                # create L23 image
                rrun("fslmaths " + os.path.join(self.dti_dir, self.dti_fit_label) + "_L2 -add " + os.path.join(self.dti_dir, self.dti_fit_label + "_L3") + " -div 2 " + os.path.join(self.dti_dir,self.dti_fit_label + "_L23"),logFile=log)

            os.makedirs(self.roi_dti_dir, exist_ok=True)

            self.transform.transform_dti_t2()

            if os.path.isfile(os.path.join(self.dti_dir, self.dti_rotated_bvec + ".gz")):
                runsystem("gunzip " + os.path.join(self.dti_dir, self.dti_rotated_bvec + ".gz"), logFile=log)

            if do_bedx:
                self.dti.bedpostx(bedpost_odn, use_gpu=do_bedx_gpu)  # .sh $SUBJ_NAME $PROJ_DIR $BEDPOST_OUTDIR_NAME

            if do_xtract:
                if not Image(os.path.join(self.dti_dir, bedpost_odn, "mean_S0samples")).exist:
                    print("subj " + self.label + " ,you requested the xtract tractorgraphy, but bedpostx was not performed.....skipping")
                else:
                    self.dti.xtract(xtract_odn, bedpost_odn, xtract_refspace, xtract_gpu)
                    self.dti.xtract_stats(xtract_odn, xtract_refspace, xtract_meas)

            if do_struct_conn and not os.path.isfile(os.path.join(self.tv_matrices_dir, "fa_AM.mat")):
                self.dti.conn_matrix(struct_conn_atlas_path, struct_conn_atlas_nroi)  # . $GLOBAL_SUBJECT_SCRIPT_DIR/subject_dti_conn_matrix.sh $SUBJ_NAME $PROJ_DIR

            log.close()
            break

        # ==============================================================================================================================================================
        # EXTRA
        # ==============================================================================================================================================================
        try:
            self.transform.transform_extra()
        except Exception:
            if do_fmri and do_rs:       # because the method check for the presence of both images and raises an error if other stuff is missing
                print("Error in Subject.welcome: transform_extra could not be completed")

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

    def renameNifti(self, extpath, associations, options="-z o -f %f_%p_%t_%s_%d ", cleanup=0, convert=True, rename=True):

        try:
            if "." in extpath:
                print("ERROR : input path " + str(extpath) + " cannot contain dots !!!")
                return

            if convert:
                rrun("dcm2niix " + options + extpath)  # it returns :. usefs coXXXXXX, oXXXXXXX and XXXXXXX images

            if not rename:
                return

            files = glob.glob(os.path.join(extpath, "*"))

            converted_images = []
            original_images = []

            for f in files:
                f = Image(f)
                if f.endswith("dcm"):
                    continue

                if f.is_image(self.DCM2NII_IMAGE_FORMATS):
                    converted_images.append(f)
                else:
                    original_images.append(f)

            for img in converted_images:

                fullext     = img.ext
                name_noext  = img.name
                name        = name_noext + fullext

                for ass in associations:

                    if ass['contains'] in name:
                        if ass['type'] == self.TYPE_T1:
                            dest_file = os.path.join(self.t1_dir, self.label + ass['postfix'] + fullext)
                        elif ass['type'] == self.TYPE_T2:
                            dest_file = os.path.join(self.t2_dir, self.label + ass['postfix'] + fullext)
                        elif ass['type'] == self.TYPE_RS:
                            dest_file = os.path.join(self.rs_dir, self.label + ass['postfix'] + fullext)
                        elif ass['type'] == self.TYPE_DTI:
                            dest_file = os.path.join(self.dti_dir, self.label + ass['postfix'] + fullext)
                            os.rename(os.path.join(extpath, name_noext + '.bval'), os.path.join(self.dti_dir, self.label + ass['postfix'] + '.bval'))
                            os.rename(os.path.join(extpath, name_noext + '.bvec'), os.path.join(self.dti_dir, self.label + ass['postfix'] + '.bvec'))
                        elif ass['type'] == self.TYPE_DTI_B0:
                            dest_file = os.path.join(self.dti_dir, self.label + ass['postfix'] + fullext)
                        elif ass['type'] == self.TYPE_FMRI:
                            dest_file = os.path.join(self.fmri_dir, self.label + ass['postfix'] + fullext)
                        else:
                            continue

                        img.mv(dest_file)

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
                f = Image(f)
                if f.is_image(self.DCM2NII_IMAGE_FORMATS):
                    converted_images.append(f)
                else:
                    original_images.append(f)

            for img in converted_images:

                if img.name.startswith("co"):
                    dest_file = os.path.join(self.t1_dir, "co-" + self.t1_image_label + img.ext)
                    # os.rename(img, dest_file)
                    os.remove(img)
                elif img.name.startswith("o"):
                    dest_file = os.path.join(self.t1_dir, "o-" + self.t1_image_label + img.ext)
                    # os.rename(img, dest_file)
                    os.remove(img)
                else:
                    dest_file = os.path.join(self.t1_dir, self.t1_image_label + img.ext)
                    move(img, dest_file)

            if cleanup == 1:
                for img in original_images:
                    os.remove(img)
            elif cleanup == 2:
                os.rmdir(extpath)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def mri_merger(self, input_files, outputname, dimension="-t", typ='fmri'):

        if typ == 'fmri':
            folder = self.fmri_dir
        else:
            folder = self.rs_dir

        cur_dir = os.path.curdir
        os.chdir(folder)

        rrun("fslmerge " + dimension + " " + outputname + " " + " ".join(input_files))
        os.chdir(cur_dir)

    def unzip_data(self, src_zip, dest_dir, replace=True):
        extractall_zip(src_zip, dest_dir, replace)
        pass

    def copy_final_data(self, dest_proj, t1=True, t1_surf=True, vbmspm=True, rs=True, fmri=None, dti=True, sess_id=1):

        subj_in_dest_project = Subject(self.label, dest_proj, sess_id)
        subj_in_dest_project.create_file_system()

        if t1:
            self.t1_data.cp_notexisting(subj_in_dest_project.t1_data)
            self.t1_brain_data.cp_notexisting(subj_in_dest_project.t1_brain_data)
            self.t1_brain_data_mask.cp_notexisting(subj_in_dest_project.t1_brain_data_mask)

        if t1_surf:
            os.makedirs(subj_in_dest_project.t1_cat_surface_dir, exist_ok=True)

            self.t1_cat_resampled_surface.gpath.cp_notexisting(subj_in_dest_project.t1_cat_resampled_surface.gpath)
            shutil.copyfile(self.t1_cat_resampled_surface.fpathnoext + ".dat", subj_in_dest_project.t1_cat_resampled_surface.fpathnoext + ".dat")

        if vbmspm:
            os.makedirs(subj_in_dest_project.t1_spm_dir, exist_ok=True)

            shutil.copyfile(self.t1_spm_icv_file, subj_in_dest_project.t1_spm_icv_file)

            self.t1_dartel_c1.cp_notexisting(subj_in_dest_project.t1_dartel_c1)
            self.t1_dartel_rc1.cp_notexisting(subj_in_dest_project.t1_dartel_rc1)
            self.t1_dartel_rc2.cp_notexisting(subj_in_dest_project.t1_dartel_rc2)

        if dti:
            self.dti_fit_FA.cp_notexisting(subj_in_dest_project.dti_fit_FA)
            self.dti_fit_MD.cp_notexisting(subj_in_dest_project.dti_fit_MD)
            self.dti_fit_L1.cp_notexisting(subj_in_dest_project.dti_fit_L1)
            self.dti_fit_L23.cp_notexisting(subj_in_dest_project.dti_fit_L23)

        if fmri is not None:

            if not isinstance(fmri, list):
                print("Error in copy_final_data")
                return

            for img in fmri:

                # Image(img).copy
                pass

        if rs:
            os.system("cp -r " + self.rs_final_regstd_dir + " " + subj_in_dest_project.rs_final_regstd_dir)

        os.system("cp -r " + self.roi_dir + " " + subj_in_dest_project.roi_dir)





    # ==================================================================================================================================================
    def can_run_analysis(self, analysis_type, analysis_params=None):

        # T1
        if analysis_type == "vbm_spm":
            return Image(os.path.join(self.t1_spm_dir, "rc1T1_" + self.label + ".nii")).exist and \
                   Image(os.path.join(self.t1_spm_dir, "rc2T1_" + self.label + ".nii")).exist and \
                   Image(os.path.join(self.t1_spm_dir, "c1T1_" + self.label + ".nii")).exist

        # elif analysis_type == "vbm_fsl":
        elif analysis_type == "ct":
            return self.t1_cat_resampled_surface.exist
        # DTI
        elif analysis_type == "tbss":
            if analysis_params is None:
                analysis_params = ["FA", "MD", "L1", "L23"]

            for ap in analysis_params:
                src_img = Image(os.path.join(self.dti_dir, self.dti_fit_label + "_" + ap))
                if not src_img.exist:
                    return False
            return True

        elif analysis_type == "bedpost":
            src_img = Image(os.path.join(self.dti_dir, self.dti_ec_image_label))
            return src_img.exist and os.path.exists(self.dti_rotated_bvec)

        elif analysis_type == "xtract_single":
            if analysis_params is None:
                analysis_params = "bedpostx"

            return Image(os.path.join(self.dti_dir, analysis_params, self.dti_bedpostx_mean_S0_label)).exist

        elif analysis_type == "xtract_group":
            if analysis_params is None:
                analysis_params = "xtract"

            rootdir = os.path.join(self.dti_dir, analysis_params, "tracts")
            for tract in self._global.dti_xtract_labels:
                if tract == "cc":
                    continue
                if not os.path.exists(os.path.join(rootdir, tract)):
                    return False

            return True

        # RESTING
        elif analysis_type == "melodic":
            return self.rs_final_regstd_image.exist and self.rs_final_regstd_mask.exist and self.rs_final_regstd_bgimage.exist

        elif analysis_type == "sbfc":
            src_imgA = Image(os.path.join(self.rs_dir, self.rs_post_nuisance_image_label))
            src_imgB = Image(os.path.join(self.rs_dir, self.rs_post_nuisance_melodic_image_label))
            return src_imgA.exist or src_imgB.exist

        # elif analysis_type == "fmri":

