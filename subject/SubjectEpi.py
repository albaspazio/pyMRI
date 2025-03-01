import os
import sys
from shutil import copyfile, rmtree

from numpy import arange, concatenate, array

from Global import Global
from data.utilities import list2spm_text_column
from group.SPMContrasts import SPMContrasts
from group.SPMResults import SPMResults
from group.SPMStatsUtils import SPMStatsUtils
from group.spm_utilities import SubjCondition
from myutility.fileutilities import sed_inplace, copytree, get_filename
from myutility.images.Image import Image
from myutility.images.Images import Images
from myutility.images.transform_images import flirt
from myutility.images.utilities import mid_0based
from myutility.list import is_list_of
from myutility.matlab import call_matlab_spmbatch, call_matlab_function
from myutility.myfsl.utils.run import rrun


class SubjectEpi:
    """
    This class provides methods for resting state and functional MRI preprocessing.
    """

    def __init__(self, subject:'Subject', _global:Global):
        """
        Initialize the SubjectEpi class.

        Args:
            subject (Subject): The subject object.
            _global (Global): The global object.
        """
        self.subject:'Subject' = subject
        self._global:Global  = _global

    def get_example_function(self, seq:str="rs", vol_num=None, fmri_labels=None, overwrite=False, logFile=None):
        """
        Get the example function for a given sequence.

        Args:
            seq (str, optional): The sequence type (rs or fmri). Defaults to "rs".
            vol_num (int, optional): The volume number. Defaults to None.
            fmri_labels (list, optional): The list of labels for the functional images. Defaults to None.
            overwrite (bool, optional): Whether to overwrite the existing example function. Defaults to False.
            logFile (str, optional): The log file. Defaults to None.

        Returns:
            Image: The example function.
        """
        if seq == "rs":
            data    = self.subject.rs_data
            exfun   = self.subject.rs_examplefunc
            m_exfun = self.subject.rs_examplefunc_mask
        elif seq == "fmri":

            if fmri_labels is None:
                data    = self.subject.fmri_data
            else:
                data = os.path.join(self.subject.fmri_dir, self.subject.label + fmri_labels[0])   # I assume other sessions are co-registered to first one
            exfun   = self.subject.fmri_examplefunc
            m_exfun = self.subject.fmri_examplefunc_mask
        else:
            data    = Image(seq, must_exist=True, msg="Error in SubjectEpi.get_example_function, given sequence does not exist")
            exfun   = data.add_postfix2name("_example_func")
            m_exfun = data.add_postfix2name("_example_func_mask")

        if vol_num is None:
            vol_num = round(data.nvols/2)

        if not exfun.exist or overwrite:
            data.get_nth_volume(exfun, m_exfun, vol_num, logFile)

        return exfun    # is an Image

    # ==================================================================================================================================================
    #region PREPROCESSING (slice timing, topup_correction, remove_nuisance, fsl_feat, aroma)
    # ==================================================================================================================================================
    def slice_timing(self, fmri_params, epi_image=None, output_prefix:str="a", spm_template_name:str="subj_spm_fmri_slice_timing_correction"):
        """
        Perform slice timing correction.

        Args:
            fmri_params (FMRIPARAMS): The FMRIPARAMS object.
            epi_image (Image, optional): The EPI image. Defaults to None.
            output_prefix (str, optional): The output prefix. Defaults to "a".
            spm_template_name (str, optional): The SPM template name. Defaults to "subj_spm_fmri_slice_timing_correction".

        Returns:
            None: None.
        """
        num_slices      = fmri_params.num_slices
        TR              = fmri_params.tr
        TA              = fmri_params.ta
        acq_scheme      = fmri_params.acq_scheme
        st_ref          = fmri_params.st_ref
        slice_timing    = fmri_params.slice_timing

        # default params:
        if epi_image is None:
            epi_image = self.subject.fmri_data
        else:
            epi_image = Image(epi_image, must_exist=True, msg="Subject.epi.slice_timing")

        if num_slices == -1:
            num_slices = epi_image.nslices

        # TA - if not otherwise indicated, it assumes the acquisition is continuous and TA = TR - (TR/num slices)
        if TA == 0:
            TA = TR - (TR / num_slices)

        if slice_timing is None:
            slice_timing = self.get_slicetiming_params(num_slices, acq_scheme)
        else:
            slice_timing = [str(p) for p in slice_timing]

        # substitute for all the volumes + rest of params
        epi_image.check_if_uncompress()
        epi_nvols = epi_image.upath.nvols

        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume      = epi_image.upath + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' + "'"

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)
        sed_inplace(out_batch_job, '<NUM_SLICES>', str(num_slices))
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<TA_VALUE>', str(TA))
        sed_inplace(out_batch_job, '<SLICETIMING_PARAMS>', ' '.join(slice_timing))
        sed_inplace(out_batch_job, '<REF_SLICE>', str(st_ref))

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

        input_dir   = epi_image.dir    # /a/b/c
        in_label    = epi_image.name   # name

        time_corrected_image = Image(os.path.join(input_dir, output_prefix + in_label + ".nii"))
        time_corrected_image.compress(replace=True)

        epi_image.upath.rm()

    # PERFORM motion correction toward the AP volume (of the first image) closest to PA sequence and then perform TOPUP CORRECTION
    # - epi_ref_vol/pe_ref_vol =-1 means use the middle volume
    # 1: get number of volumes of epi_PA image in opposite phase-encoding direction and extract middle volume (add "_ref")
    # 2: look for the AP epi volume closest to epi_pa_ref volume
    # 3: merge the 2 ref volumes into one (add "_ref")
    # 4: run topup using ref, acq params; used_templates: "_topup"
    # 5 motion correction using closest_vol to PA (or given one) [fmri do it, rs default not]
    # 6: applytopup --> choose images whose distortion we want to correct
    # returns 0-based volume
    def topup_corrections(self, in_ap_images:Images, in_pa_img:Image, acq_params, ap_ref_vol=-1, pa_ref_vol=-1, config:str="b02b0.cnf", motion_corr:bool=True, cleanup:bool=True, logFile=None):
        """
        Perform topup distortion correction on the given AP and PA images.

        Args:
            in_ap_images (str or list of str): path to the AP image or list of paths to AP images.
            in_pa_img (str): path to the PA image.
            acq_params (str): path to the acquisition parameters file.
            ap_ref_vol (int, optional): index of the reference AP volume. If -1, the closest volume will be used. Defaults to -1.
            pa_ref_vol (int, optional): index of the reference PA volume. If -1, the middle volume will be used. Defaults to -1.
            config (str, optional): path to the topup config file. Defaults to "b02b0.cnf".
            motion_corr (bool, optional): whether to perform motion correction. Defaults to True.
            cleanup (bool, optional): whether to cleanup temporary files. Defaults to True.
            logFile (str, optional): path to the log file. Defaults to None.

        Returns:
            list: list of indices of the volumes with the least distortion.

        Raises:
            Exception: if multiple images are given but motion correction is not performed.

        """
        closest_vols = []
        #  /a/b/c/name.nii.gz
        in_ap_images    = Images(in_ap_images)

        if len(in_ap_images) > 1 and not motion_corr:
            raise Exception("Error in topup_corrections, when multiple images have to be corrected, realignment must be performed, correct and re-run")

        ap_distorted    = Images()
        for img in in_ap_images:
            ap_distorted.append(Image(img).add_postfix2name("_distorted"))

        # in_ap_img       = in_ap_images[0]
        # in_pa_img       = Image(in_pa_img)

        input_dir       = in_ap_images[0].dir    # /a/b/c
        ap_ref          = Image(os.path.join(input_dir, "ap_ref"))
        pa_ref          = Image(os.path.join(input_dir, "pa_ref"))
        ap_pa_ref       = Image(os.path.join(input_dir, "ap_pa_ref"))
        ap_pa_ref_topup = Image(os.path.join(input_dir, "ap_pa_ref_topup"))

        # 1: get number of volumes of epi_PA image in opposite phase-encoding direction and extract middle volume (add "_ref")
        if pa_ref_vol == -1:
            nvols_pe        = in_pa_img.nvols
            central_vol_pa  = mid_0based(nvols_pe)  # odd values:   returns the middle volume in a zero-based context,      3//2 -> 1 which is the middle volume in 0,(1),2 context
        else:                                       # even values:  returns second middle volume in a zero-based context,   4//2 -> 2, 0,1,(2),3
            central_vol_pa = pa_ref_vol
        rrun(f"fslselectvols -i {in_pa_img} -o {pa_ref} --vols={central_vol_pa}", logFile=logFile)

        for in_ap_img in in_ap_images:

            # 2: look for the AP volume closest to epi_pa_ref volume
            if ap_ref_vol == -1:
                closest_vol = self.get_closest_volume(in_ap_img, in_pa_img, pa_ref_vol) # returns a 0-based volume
            else:
                closest_vol = ap_ref_vol
            closest_vols.append(closest_vol)
            rrun(f"fslselectvols -i {in_ap_img} -o {ap_ref} --vols={closest_vol}", logFile=logFile)

            # merge the 2 ref volumes into one (add "_ref")
            rrun(f"fslmerge -t {ap_pa_ref} {ap_ref} {pa_ref}", stop_on_error=False)

            # 4 run topup using ref, acq params; used_templates: "_topup". assumes merged epi volumes appear in the same order as acqparams.txt (--datain)
            rrun(f"topup --imain={ap_pa_ref} --datain={acq_params} --config={config} --out={ap_pa_ref_topup}", logFile=logFile) # + " --iout=" + self.subject.fmri_data + "_PE_ref_topup_corrected")

            # 5 realign all volumes of all images to the closest_vol to PA (or given one)
            if motion_corr:
                self.spm_motion_correction([in_ap_img], ref_vol=closest_vol, reslice=True)   # add r in front of images' names, closest_vol is 0-based

                in_ap_img.upath.rm()    # remove old with-motion SUBJ-fmri.nii
                in_ap_img.cpath.rm()    # remove old with-motion SUBJ-fmri.nii.gz
                Image(os.path.join(input_dir, "r" + in_ap_img.name)).compress(in_ap_img, replace=True)  # zip rSUBJ-fmri.nii => SUBJ-fmri.nii.gz

            # 6 applytopup to input images , these must be in the same order as --datain/acqparams.txt // "inindex=" values reference the images-to-correct corresponding row in --datain and --topup
            rrun(f"applytopup --imain={in_ap_img} --topup={ap_pa_ref_topup} --datain={acq_params} --inindex=1 --method=jac --interp=spline --out={in_ap_img}", logFile=logFile)

        # clean up?
        if cleanup:
            os.system(f"rm {input_dir}/ap_*")
            os.system(f"rm {input_dir}/pa_*")
            os.system(f"rm {input_dir}/*mat")

        print("topup correction of subj: " + self.subject.label + " finished. closest volume is: " + str(closest_vol))
        return closest_vols

    # coregister given images to given volume of given image (usually the epi itself or pepolar in case of distortion correction process)
    # automatically put an out_prefix="r" in front of the given file name if reslice=True
    # ref_vol MUST BE 0-BASED
    # the first volume of the first session is the reference volume.
    # if ref_vol belongs to the input image (ref_image=None):   put that volume first and the remaining in the list (skipping the ref_vol)
    # if ref_vol belongs to ref_image:                          put that vol first and all the input images then
    def spm_motion_correction(self, images2correct, ref_image=None, ref_vol=0, reslice:bool=True, out_prefix="r", whichreslice=None):
        """
        Perform motion correction on the given images.

        Args:
            images2correct (Image or list of Image): the images to correct.
            ref_image (Image, optional): the reference image. If not given, the first image in the list will be used. Defaults to None.
            ref_vol (int, optional): the reference volume. If not given, the middle volume will be used. Defaults to 0.
            reslice (bool, optional): whether to reslice the corrected images. Defaults to True.
            out_prefix (str, optional): the output prefix. Defaults to "r".
            whichreslice (str, optional): the whichreslice parameter for SPM. Defaults to None.

        Raises:
            Exception: if the given whichreslice is not valid.

        Returns:
            None: None.
        """
        if whichreslice is None:
            whichreslice = "[2 1]"
        else:
            if whichreslice != "[2 1]" and whichreslice != "[2 0]" and whichreslice != "[1 0]":
                raise Exception("Error in spm_motion_correction, given whichreslice (" + whichreslice + ") is not valid")

        if reslice is True:
            spm_template_name = "subj_spm_fmri_realign_estimate_reslice_to_given_vol"
        else:
            spm_template_name = "subj_spm_fmri_realign_estimate_to_given_vol"

        ref_vol += 1    # SPM wants it 1-based

        images2correct = Images(images2correct, must_exist=True, msg="Subject.epi.spm_motion_correction")
        images2correct.check_if_uncompress()

        # check if ref image is valid (if not specified, use in_img)
        if ref_image is None:
            ref_volume = "'" + images2correct[0].upath + ',' + str(ref_vol) + "'\n"
            skip_ref = True
        else:
            ref_image  = Image(ref_image, must_exist=True, msg="Subject.epi.spm_motion_correction")
            ref_image.check_if_uncompress()

            ref_volume = "'" + ref_image.upath + ',' + str(ref_vol) + "'\n"
            skip_ref = False

        out_batch_job, out_batch_start  = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        # first session, starting with ref_vol
        epi_all_volumes                 = '{\n'
        epi_all_volumes                += ref_volume      # reference volume must be inserted as first volume

        first_image                     = Image(images2correct.pop(0))
        epi_nvols                       = first_image.upath.nvols
        for i in range(1, epi_nvols + 1):
            if i == ref_vol and skip_ref:
                continue    # skip ref_vol if it belongs to the input image
            epi_all_volumes += ("'" + first_image.upath + ',' + str(i) + "'\n")

        epi_all_volumes                += '}\n'

        # all other sessions
        for img in images2correct:
            epi_nvols = img.upath.nvols
            img.check_if_uncompress()

            epi_all_volumes += '{'
            for i in range(1, epi_nvols + 1):
                epi_all_volumes += ("'" + img.upath + ',' + str(i) + "'\n")
            epi_all_volumes += '}\n'

        sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)
        sed_inplace(out_batch_job, '<IMG_PREFIX>', out_prefix)
        sed_inplace(out_batch_job, '<WHICH>', whichreslice)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    # calculate the in_image 0-based volume closest to ref_image (by estimating the realignment without performing it)
    def get_closest_volume(self, in_image, ref_image, ref_volume=-1):
        """
        Calculates the index of the volume in the input image that is closest to the reference image,
        based on the estimated motion correction.

        Args:
            in_image: The input image.
            ref_image: The reference image.
            ref_volume: The index of the reference volume. If not specified, the middle volume will be used.

        Returns:
            The index of the closest volume.

        """
        # will calculate the closest vol from given epi image to ref_image
        # Steps:
        # 0: get epi_pe central volume + unzip so SPM can use it
        # 1: merge all the sessions into one file ("_merged-sessions") + unzip so SPM can use it
        # 2: align all the volumes within merged file to epi_pe central volume (SPM12-Realign:Estimate)
        # 3: calculate the "less motion corrected" volume from the merged file with respect to the epi-pe in terms of rotation around x, y and z axis).

        in_image    = Image(in_image,  must_exist=True, msg="Subject.epi.get_closest_volume")
        ref_image   = Image(ref_image, must_exist=True, msg="Subject.epi.get_closest_volume")

        input_dir   = in_image.dir

        # create temp folder, copy there epi and epi_pe, unzip and run mc (then I can simply remove it when ended)
        temp_distorsion_mc  = os.path.join(input_dir, "temp_distorsion_mc")
        os.makedirs(temp_distorsion_mc, exist_ok=True)
        temp_epi            = Image(os.path.join(temp_distorsion_mc, in_image.name))
        temp_epi_ref        = Image(os.path.join(temp_distorsion_mc, in_image.name + "_ref"))

        if not temp_epi.uexist:
            if in_image.uexist:
                in_image.cp(temp_epi.upath)
            else:
                in_image.unzip(temp_epi.upath, replace=False)

        if not temp_epi_ref.uexist:
            if ref_image.uexist:
                ref_image.cp(temp_epi_ref.upath)
            else:
                ref_image.unzip(temp_epi_ref.upath, replace=False)

        if ref_volume == -1:
            ref_volume = mid_0based(ref_image.upath.nvols)    # odd values:   returns the middle volume in a zero-based context       3//2 -> 1 which is the middle volume in 0,(1),2 context
                                                            # even values:  returns second middle volume in a zero-based context    4//2 -> 2, 0,1,(2),3
        # estimate BUT NOT reslice
        self.spm_motion_correction([temp_epi], temp_epi_ref, ref_volume, reslice=False)

        # 3: call matlab function that calculates best volume (1-based):
        best_vol = call_matlab_function("least_mov", [self._global.spm_functions_dir], "\"" + os.path.join(temp_distorsion_mc, "rp_" + in_image.name + "_ref" + '.txt' + "\""))[1]
        rmtree(temp_distorsion_mc)

        return int(best_vol) - 1    # 0-based volume

    def remove_nuisance(self, in_img_name, out_img_name, epi_label="rs", ospn:str="", hpfsec=100):
        """
        Remove nuisance signals from resting state fMRI data.

        Args:
            in_img_name (str): the name of the input image.
            out_img_name (str): the name of the output image.
            epi_label (str, optional): the type of EPI data. Defaults to "rs".
            ospn (str, optional): the output suffix for the nuisance regressors. Defaults to "".
            hpfsec (int, optional): the number of seconds of high-pass filtering. Defaults to 100.

        Raises:
            Exception: if the given epi_label is not "rs".

        Returns:
            None: None.
        """
        if epi_label == "rs":
            in_img          = Image(os.path.join(self.subject.rs_dir, in_img_name), must_exist=True, msg="ERROR in remove_nuisance of subject " + self.subject.label + " input image is missing")
            out_img         = Image(os.path.join(self.subject.rs_dir, out_img_name))
            series_wm       = self.subject.rs_series_wm + ospn + ".txt"
            series_csf      = self.subject.rs_series_csf + ospn + ".txt"
            output_series   = os.path.join(self.subject.rs_series_dir, "nuisance_timeseries" + ospn + ".txt")
        else:
            print('WARNING in remove_nuisance of subject ' + self.subject.label + ". presently, remove nuisance is allowed only for resting state data")
            return

        tr          = in_img.TR
        hpf_sigma   = hpfsec / (2 * tr)
        print("execute_subject_resting_nuisance of " + self.subject.label)

        os.makedirs(self.subject.sbfc_dir, exist_ok=True)
        os.makedirs(self.subject.rs_series_dir, exist_ok=True)

        print(self.subject.label + ": coregister fast-highres to epi")

        if not self.subject.rs_mask_t1_wmseg4nuis.exist:
            # regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, std_img="", rois=[]):
            self.subject.transform.transform_roi("hrTOrs", "abs", rois=[self.subject.t1_segment_wm_ero_path])

        if not self.subject.rs_mask_t1_csfseg4nuis.exist:
            # regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, std_img="", rois=[]):
            self.subject.transform.transform_roi("hrTOrs", "abs", rois=[self.subject.t1_segment_csf_ero_path])

        rrun(f"fslmeants -i {in_img} -o {series_wm} -m {self.subject.rs_mask_t1_wmseg4nuis} --no_bin")
        rrun(f"fslmeants -i {in_img} -o {series_csf} -m {self.subject.rs_mask_t1_csfseg4nuis} --no_bin")

        if os.path.isfile(series_csf) and os.path.isfile(series_wm):
            os.system(f"paste {series_wm} {series_csf} > {output_series}")
            # rrun("paste " + series_wm + " " + series_csf + " > " + output_series) # ISSUE: doesn't work. don't know why

        tempMean = Image(os.path.join(self.subject.rs_dir, "tempMean.nii.gz"))
        residual = Image(os.path.join(self.subject.rs_dir, "residual.nii.gz"))

        rrun(f"fslmaths {in_img} -Tmean {tempMean}")
        rrun(f"fsl_glm -i {in_img} -d {output_series} --demean --out_res={residual}")

        rrun(f"fslcpgeom {in_img}.nii.gz {residual}")  # solves a bug in fsl_glm which writes TR=1 in residual.
        rrun(f"fslmaths {residual} -bptf {hpf_sigma} -1 -add {tempMean} {out_img}")

        residual.rm()
        tempMean.rm()

    def spm_fmri_preprocessing(self, fmri_params, epi_images=None, spm_template_name='subj_spm_fmri_full_preprocessing', smoothprefix="s", clean=False, can_skip_input=False, do_overwrite=False):
        """
        Perform SPM fMRI preprocessing on the subject's EPI data.

        Args:
            fmri_params (FMRIParams): the fMRI parameters.
            epi_images (list, optional): the list of EPI images. If not specified, the subject's EPI image will be used.
            spm_template_name (str, optional): the SPM template name. Defaults to "subj_spm_fmri_full_preprocessing".
            smoothprefix (str, optional): the prefix for the smoothed images. Defaults to "s".
            clean (bool, optional): whether to clean the temporary files. Defaults to False.
            can_skip_input (bool, optional): whether to skip input images that are missing. Defaults to False.
            do_overwrite (bool, optional): whether to overwrite existing files. Defaults to False.

        Raises:
            Exception: if the given epi_images are not valid.

        Returns:
            None: None.
        """
        # add sessions
        valid_images = Images()
        if epi_images is None:
            valid_images.append(self.subject.fmri_data)
        else:
            for img in epi_images:
                img = Image(img)
                if img.exist:
                    valid_images.append(img)
                else:
                    if can_skip_input:
                        print("WARNING in subj: " + self.subject.label + ", given image (" + img + " is missing...skipping this image")
                    else:
                        raise Exception("Error in spm_fmri_preprocessing, one of the input image (" + img + ") is missing")

        nsessions = len(valid_images)

        if not valid_images.exist:
            raise Exception("Error in spm_fmri_preprocessing")

        swar_images = valid_images.add_prefix2name("swar")
        swa_images  = valid_images.add_prefix2name("swa")

        if (swar_images.exist or swa_images.exist) and not do_overwrite:
            print("Skipping spm_fmri_preprocessing of subject " + self.subject.label + ", swar images already exist")
            return

        num_slices  = fmri_params.nslices
        TR          = fmri_params.tr
        TA          = fmri_params.ta
        acq_scheme  = fmri_params.acq_scheme
        st_ref      = fmri_params.st_ref
        smooth      = fmri_params.smooth
        slice_timing = fmri_params.slice_timing

        if slice_timing is None:
            slice_timing = self.get_slicetiming_params(num_slices, acq_scheme)

            # TA - if not otherwise indicated, it assumes the acquisition is continuous and TA = TR - (TR/num slices)
            if TA == 0:
                TA = TR - (TR / num_slices)
        else:
            num_slices      = len(slice_timing)
            slice_timing    = [str(p) for p in slice_timing]
            TA              = 0

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        mean_image = valid_images[0].add_prefix2name("mean")
        mean_image.check_if_uncompress()

        temp_t1_dir = os.path.join(self.subject.t1_dir, "temp")
        os.makedirs(temp_t1_dir, exist_ok=True)
        temp_t1     = Image(os.path.join(temp_t1_dir, "t1"))
        self.subject.t1_data.unzip(dest=temp_t1, replace=False)

        smooth_schema = "[" + str(smooth) + " " + str(smooth) + " " + str(smooth) + "]"

        if spm_template_name == "subj_spm_fmri_full_preprocessing" or spm_template_name == "subj_spm_fmri_full_preprocessing_mni":

            # substitute for all the volumes + rest of params
            epi_all_volumes = ''
            for img in valid_images:

                img.check_if_uncompress()
                epi_nvols = img.upath.nvols

                epi_all_volumes += '{'
                for i in range(1, epi_nvols + 1):
                    epi_volume = "'" + img.upath + ',' + str(i) + "'"
                    epi_all_volumes += (epi_volume + '\n')
                epi_all_volumes += '}\n'
            sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)

            # slice-timing sessions
            slice_timing_sessions = ""
            for i in range(nsessions):
                slice_timing_sessions += "matlabbatch{2}.spm.temporal.st.scans{" + str(i + 1) + "}(1) = cfg_dep('Realign: Estimate & Reslice: Resliced Images (Sess " + str(i + 1) + ")', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('.', 'sess', '()', {" + str(i + 1) + "}, '.', 'rfiles'));\n"

            # normalize write
            normalize_write_sessions = ""
            for i in range(nsessions):
                normalize_write_sessions += "matlabbatch{5}.spm.spatial.normalise.write.subj.resample(" + str(i + 1) + ") = cfg_dep('Slice Timing: Slice Timing Corr. Images (Sess " + str(i + 1) + ")', substruct('.', 'val', '{}', {2}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('()', {" + str(i + 1) + "}, '.', 'files'));\n"

        elif spm_template_name == "subj_spm_fmri_preprocessing_norealign" or spm_template_name == "subj_spm_fmri_preprocessing_norealign_mni":

            # input images are realigned images to be slice-timing processed
            slice_timing_sessions = "matlabbatch{1}.spm.temporal.st.scans = {\n"
            for i in range(nsessions):
                epi_session_volumes     = '{\n'
                img                     = valid_images[i]
                img.check_if_uncompress()
                epi_nvols               = img.upath.nvols

                for v in range(1, epi_nvols + 1):
                    epi_session_volumes += ("'" + img.upath + ',' + str(v) + "'\n")
                epi_session_volumes += '}\n'

                slice_timing_sessions += epi_session_volumes

            slice_timing_sessions += "};"

            # normalize write
            normalize_write_sessions = ""
            for i in range(nsessions):
                normalize_write_sessions += "matlabbatch{4}.spm.spatial.normalise.write.subj.resample(" + str(i + 1) + ") = cfg_dep('Slice Timing: Slice Timing Corr. Images (Sess " + str(i + 1) + ")', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('()', {" + str(i + 1) + "}, '.', 'files'));\n"

        else:
            os.removedirs(temp_t1_dir)
            raise Exception("Error in SubjectEpi.spm_fmri_preprocessing...unrecognized template")

        sed_inplace(out_batch_job, '<SLICE_TIMING_SESSIONS>',       slice_timing_sessions)
        sed_inplace(out_batch_job, '<NORMALIZE_WRITE_SESSIONS>',    normalize_write_sessions)

        sed_inplace(out_batch_job, '<NUM_SLICES>',  str(num_slices))
        sed_inplace(out_batch_job, '<TR_VALUE>',    str(TR))
        sed_inplace(out_batch_job, '<TA_VALUE>',    str(TA))
        sed_inplace(out_batch_job, '<SLICETIMING_PARAMS>', ' '.join(slice_timing))
        sed_inplace(out_batch_job, '<REF_SLICE>', str(st_ref))
        sed_inplace(out_batch_job, '<RESLICE_MEANIMAGE>', mean_image.upath + ',1')
        sed_inplace(out_batch_job, '<T1_IMAGE>', temp_t1.upath + ',1')
        sed_inplace(out_batch_job, '<SPM_DIR>', self._global.spm_dir)
        sed_inplace(out_batch_job, '<SMOOTH_SCHEMA>', smooth_schema)
        sed_inplace(out_batch_job, '<SMOOTH_PREFIX>', smoothprefix)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

        rmtree(temp_t1_dir, ignore_errors=True)  # remove T1 temp dir with spm segmentation (for coregistration)

        for img in valid_images:
            img.upath.rm()

        if clean:
            for img in valid_images:
                img.add_prefix2name("r").rm()
                img.add_prefix2name("a").rm()
                img.add_prefix2name("ar").rm()
                img.add_prefix2name("war").rm()
                img.add_prefix2name("wa").rm()

    def spm_smooth(self, epi_images=None, smooth=6, smoothprefix="s", spm_template_name='subj_spm_smooth', logFile=None):
        """
        Smooths the input EPI images using SPM.

        Args:
            epi_images (list, optional): The list of EPI images to smooth. If not specified, the subject's EPI image will be used.
            smooth (int, optional): The smoothing kernel size. Defaults to 6.
            smoothprefix (str, optional): The prefix for the smoothed images. Defaults to "s".
            spm_template_name (str, optional): The SPM template name. Defaults to "subj_spm_smooth".
            logFile (str, optional): The log file. Defaults to None.

        Raises:
            Exception: If the given epi_images are not valid.

        Returns:
            None: None.
        """
        valid_images = Images()
        if epi_images is None:
            valid_images.append(self.subject.fmri_data)
        else:
            for img in epi_images:
                img = Image(img)
                if img.exist:
                    valid_images.append(img)
                else:
                    print("WARNING in subj: " + self.subject.label + ", given image (" + img + " is missing...skipping this image")

        for img in valid_images:

            out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

            img.check_if_uncompress()
            epi_nvols = img.upath.nvols

            epi_volumes = ""
            for v in range(1, epi_nvols + 1):
                epi_volumes += ("'" + img.upath + ',' + str(v) + "'\n")

            smooth_schema = "[" + str(smooth) + " " + str(smooth) + " " + str(smooth) + "]"
            sed_inplace(out_batch_job, '<IMAGE>', epi_volumes)
            sed_inplace(out_batch_job, '<SMOOTH_SCHEMA>', smooth_schema)
            sed_inplace(out_batch_job, '<SMOOTH_PREFIX>', smoothprefix)
            call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    #endregion

    # ==================================================================================================================================================
    #region fMRI analysis
    # ==================================================================================================================================================
    # conditions_lists[{"name", "onsets", "duration"}, ....]
    def spm_fmri_1st_level_analysis(self, analysis_name, input_images, fmri_params, conditions_lists, contrasts=None, res_report=None, rp_filenames=None,
                                                         spm_template_name="subj_spm_fmri_stats_1st_level"):
        """
        Perform first-level analysis of fMRI data.

        Args:
            analysis_name (str): the name of the analysis.
            input_images (list): the list of input EPI images.
            fmri_params (FMRIParams): the fMRI parameters.
            conditions_lists (list): the list of conditions. Each element in the list is a list of conditions for a specific session.
            contrasts (list, optional): the list of contrasts. Defaults to None.
            res_report (str, optional): the name of the results report. Defaults to None.
            rp_filenames (list, optional): the list of regressors filenames. Defaults to None.
            spm_template_name (str, optional): the SPM template name. Defaults to "subj_spm_fmri_stats_1st_level".

        Raises:
            Exception: if the given input_images or conditions_lists are not valid.

        Returns:
            None: None.
        """
        if input_images is None:
            input_images = Images([self.subject.fmri_data])
        else:
            input_images = Images(input_images, must_exist=True, msg="Error in spm_fmri_1st_level_analysis. input images")
        input_images.check_if_uncompress()  # unzip whether necessary
        nsessions = len(input_images)

        if not is_list_of(conditions_lists[0], SubjCondition):
            raise Exception("Error in SubjectEpi.spm_fmri_1st_level_analysis, condition_list is not valid")

        # default params:
        stats_dir = os.path.join(self.subject.fmri_dir, "stats", analysis_name)
        spmpath   = os.path.join(stats_dir, "SPM.mat")
        os.makedirs(stats_dir, exist_ok=True)

        TR          = fmri_params.tr
        time_bins   = fmri_params.time_bins
        events_unit = fmri_params.events_unit
        time_onset  = fmri_params.time_onset
        hrf_deriv   = fmri_params.hrf_deriv

        if hrf_deriv:
            str_hrf_deriv = "[1 0]"
        else:
            str_hrf_deriv = "[0 0]"

        if rp_filenames is None:
            rp_filenames = [os.path.join(self.subject.fmri_dir, "rp_" + self.subject.fmri_image_label + ".txt")]

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        sed_inplace(out_batch_job, '<SPM_DIR>', stats_dir)
        sed_inplace(out_batch_job, '<EVENTS_UNIT>', events_unit)
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<MICROTIME_RES>', str(time_bins))
        sed_inplace(out_batch_job, '<MICROTIME_ONSET>', str(time_onset))
        sed_inplace(out_batch_job, '<HRF_DERIV>', str_hrf_deriv)

        conditions_str = ""
        if nsessions == 1:

            # images
            fmri_data = input_images[0]
            fmri_data.check_if_uncompress()
            epi_nvols = fmri_data.upath.nvols

            if epi_nvols == 0:
                raise Exception("Error in SubjectEpi.spm_fmri_1st_level_analysis: input images have zero volumes. e.g. when nii and nii.gz are both present or image is corrupted")
            conditions_str += "matlabbatch{1}.spm.stats.fmri_spec.sess.scans = {\n"
            for i in range(1, epi_nvols + 1):
                conditions_str += ("'" + fmri_data.upath + ',' + str(i) + "'\n")
            conditions_str += "};\n"

            # conditions
            conditions_str += (SPMStatsUtils.spm_get_fmri_subj_stats_conditions_string_1session(conditions_lists[0]) + ";\n")

            conditions_str +=  "matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};\n"
            conditions_str +=  "matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});\n"
            conditions_str += ("matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {'" + rp_filenames[0] + "'};\n")
            conditions_str += ("matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = " + str(fmri_params.hpf) + ";\n")

        else:
            for im,fmri_data in enumerate(input_images):

                fmri_data.check_if_uncompress()
                epi_nvols       = fmri_data.upath.nvols
                conditions_str += "matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(im+1) + ").scans = {\n"
                for i in range(1, epi_nvols + 1):
                    conditions_str += ("'" + fmri_data.upath + ',' + str(i) + "'\n")
                conditions_str += "};\n"

                # conditions
                conditions_str += (SPMStatsUtils.spm_get_fmri_subj_stats_conditions_string_ithsession(conditions_lists[im], im+1) + ";\n")

                conditions_str +=  "matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(im+1) + ").multi = {''};\n"
                conditions_str +=  "matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(im+1) + ").regress = struct('name', {}, 'val', {});\n"
                conditions_str += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(im+1) + ").multi_reg = {'" + rp_filenames[im] + "'};\n")
                conditions_str += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(im+1) + ").hpf = " + str(fmri_params.hpf) + ";\n")

        sed_inplace(out_batch_job, '<SESSIONS_CONDITIONS>', conditions_str)

        if contrasts is None:
            sed_inplace(out_batch_job, '<CONTRASTS>', "")
            sed_inplace(out_batch_job, '<RESULTS_REPORT>', "")
        else:
            if not isinstance(contrasts, list):
                raise Exception("Error in SubjectEpi.spm_fmri_1st_level_multisessions_custom_analysis, given contrasts")

            SPMContrasts.replace_1stlevel_contrasts(out_batch_job, spmpath, contrasts)
            str_res_rep     = SPMResults.get_1stlevel_results_report(res_report)

            sed_inplace(out_batch_job, '<RESULTS_REPORT>', str_res_rep)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    # sessions x conditions_lists[{"name", "onsets", "duration"}, ....]
    def spm_fmri_1st_level_multisessions_custom_analysis(self, analysis_name, input_images, fmri_params, conditions_lists, contrasts=None, res_report=None, rp_filenames=None,
                                                         spm_template_name="subj_spm_fmri_stats_1st_level"):
        """
        Perform first-level analysis of fMRI data with multiple sessions.

        Args:
            analysis_name (str): the name of the analysis.
            input_images (list): the list of input EPI images.
            fmri_params (FMRIParams): the fMRI parameters.
            conditions_lists (list): the list of conditions. Each element in the list is a list of conditions for a specific session.
            contrasts (list, optional): the list of contrasts. Defaults to None.
            res_report (str, optional): the name of the results report. Defaults to None.
            rp_filenames (list, optional): the list of regressors filenames. Defaults to None.
            spm_template_name (str, optional): the SPM template name. Defaults to "subj_spm_fmri_stats_1st_level".

        Raises:
            Exception: if the given input_images or conditions_lists are not valid.

        Returns:
            None: None.
        """
        if input_images is None:
            input_images = Images([self.subject.fmri_data])
        else:
            input_images = Images(input_images)
        input_images.check_if_uncompress()  # unzip whether necessary
        nsessions = len(input_images)

        # default params:
        stats_dir = os.path.join(self.subject.fmri_dir, "stats", analysis_name)
        spmpath   = os.path.join(stats_dir, "SPM.mat")
        os.makedirs(stats_dir, exist_ok=True)

        TR          = fmri_params.tr
        time_bins   = fmri_params.time_bins
        events_unit = fmri_params.events_unit
        time_onset  = fmri_params.time_onset


        if rp_filenames is None:
            rp_filename = os.path.join(self.subject.fmri_dir, "rp_" + self.subject.fmri_image_label + ".txt")

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        sed_inplace(out_batch_job, '<SPM_DIR>',         stats_dir)
        sed_inplace(out_batch_job, '<EVENTS_UNIT>',     events_unit)
        sed_inplace(out_batch_job, '<TR_VALUE>',        str(TR))
        sed_inplace(out_batch_job, '<MICROTIME_RES>',   str(time_bins))
        sed_inplace(out_batch_job, '<MICROTIME_ONSET>', str(time_onset))

        for s in range(nsessions):

            image = Image(input_images[s])

            # substitute for all the volumes
            epi_nvols       = image.upath.nvols
            epi_all_volumes = ""
            for i in range(1, epi_nvols + 1):
                epi_volume       = "'" + image.upath + ',' + str(i) + "'"
                epi_all_volumes += (epi_volume + '\n')  # + "'"

            sed_inplace(out_batch_job, '<VOLS'+ str(s+1) + '>', epi_all_volumes)
            sed_inplace(out_batch_job, '<MOTION_PARAMS'+ str(s+1) + '>', rp_filenames[s])

        sed_inplace(out_batch_job, '<COND11_ONSETS>', list2spm_text_column(conditions_lists[0][0][:]))
        sed_inplace(out_batch_job, '<COND12_ONSETS>', list2spm_text_column(conditions_lists[0][1][:]))
        sed_inplace(out_batch_job, '<COND13_ONSETS>', list2spm_text_column(conditions_lists[0][2][:]))

        sed_inplace(out_batch_job, '<COND21_ONSETS>', list2spm_text_column(conditions_lists[1][0][:]))
        sed_inplace(out_batch_job, '<COND22_ONSETS>', list2spm_text_column(conditions_lists[1][1][:]))
        sed_inplace(out_batch_job, '<COND23_ONSETS>', list2spm_text_column(conditions_lists[1][2][:]))

        if contrasts is None:
            sed_inplace(out_batch_job, '<CONTRASTS>'     , "")
            sed_inplace(out_batch_job, '<RESULTS_REPORT>', "")
        else:
            if not isinstance(contrasts, list):
                raise Exception("Error in SubjectEpi.spm_fmri_1st_level_multisessions_custom_analysis, given contrasts")

            SPMContrasts.replace_1stlevel_contrasts(out_batch_job, spmpath, contrasts)
            str_res_rep     = SPMResults.get_1stlevel_results_report(res_report)

            sed_inplace(out_batch_job, '<RESULTS_REPORT>', str_res_rep)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])
    #endregion

    # ===============================================================================
    #region SBFC
    # ==================================================================================================================================================
    def sbfc_1multiroi_feat(self):
        pass

    # -i input_ffd_name -f denoised_folder_postfix_name -o output_postfixname_series_and_folder or $0 subj_label proj_dir -p full_input_image_path -o output_postfixname_series_and_folder"
    # rois can be indicated as a list of full paths or names (and rel_in_roi_dir must be not None and equal to a path relative to subj folder)
    def sbfc_several_1roi_feat(self, rois_list, in_model="sbfc_feat_1roi", rel_in_roi_dir=None, ser_pfname:str="", epi_label="rs", in_file_name=None, std_image=None, tr=None, te=None):

        if std_image is None:
            std_image = self._global.fsl_std_mni_2mm_brain

        # define & validate input epi image
        if in_file_name is None:
            if epi_label == "rs":
                in_file_name    = self.subject.rs_post_nuisance_melodic_image_label
                epi_dir         = self.subject.rs_dir
            else:
                in_file_name    = self.subject.fmri_image_label
                epi_dir         = self.subject.fmri_dir
        else:
            if epi_label == "rs":
                epi_dir         = self.subject.rs_dir
            else:
                epi_dir         = self.subject.fmri_dir

        in_image    = os.path.join(epi_dir, in_file_name)
        in_image    = Image(in_image, must_exist=True, msg="Error in sbfc_several_1roi_feat, given input image " + in_image + ", does not exist...exiting")
        tot_vol_num = in_image.nvols

        for roi_name in rois_list:

            # compose & validate input roi path
            if rel_in_roi_dir is None:
                roi = roi_name
            else:
                roi = os.path.join(self.subject.dir, rel_in_roi_dir, roi_name)
            roi = Image(roi, must_exist=True, msg="Error in sbfc_several_1roi_feat, given roi " + roi_name + ", does not exist...exiting")

            # extract roi time-serie
            output_serie    = os.path.join(self.subject.rs_series_dir, f"{roi_name}_ts{ser_pfname}.txt")
            rrun(f"fslmeants -i {in_image} -o {output_serie} -m {roi}")    # <<<<<<<<<<<<<<<<<<--------------------

            # create output model dir and file
            in_model_path   = os.path.join(self.subject.project.glm_template_dir, in_model)
            out_model_path  = os.path.join(self.subject.sbfc_dir, "feat_roi_" + in_model + "_" + roi_name + ser_pfname)
            os.makedirs(os.path.join(epi_dir, "model"), exist_ok=True)
            copyfile(in_model_path + ".fsf", out_model_path + ".fsf")

            output_dir      = os.path.join(self.subject.sbfc_feat_dir, "feat_" + roi_name + ser_pfname)

            # FEAT fsf -------------------------------------------------------------------------------------------------------------------------
            with open(out_model_path + ".fsf", "a") as text_file:
                # original_stdout = sys.stdout
                # sys.stdout = text_file  # Change the standard output to the file we created.

                print("", file=text_file)
                print("################################################################", file=text_file)
                print("# overriding parameters", file=text_file)
                print("################################################################", file=text_file)

                print("set fmri(npts) " + str(tot_vol_num), file=text_file)
                print("set feat_files(1) " + in_image, file=text_file)
                print("set highres_files(1) " + self.subject.t1_brain_data, file=text_file)

                # if self.subject.wb_brain_data.is_image() and do_initreg:
                #     print("set fmri(reginitial_highres_yn) 1", file=text_file)
                #     print("set initial_highres_files(1) " + self.subject.wb_brain_data, file=text_file)
                # else:
                print("set fmri(reginitial_highres_yn) 0", file=text_file)

                print("set fmri(outputdir) " + output_dir, file=text_file)
                print("set fmri(regstandard) " + std_image, file=text_file)
                print("set fmri(custom1) " + output_serie, file=text_file)

                if tr is not None:
                    print("set fmri(tr) " + str(tr), file=text_file)

                if te is not None:
                    print("set fmri(te) " + str(te), file=text_file)

                print("subj: " + self.subject.label + ", starting ROI FEAT: " + roi_name)

            rrun(os.path.join(self._global.fsl_bin, "feat") + " " + out_model_path + ".fsf")  # execute  FEAT
            rrun(os.path.join(self._global.fsl_bin, "featregapply") + " " + output_dir + ".feat")


    # endregion

    # ==================================================================================================================================================
    # region ACCESSORY
    # ==================================================================================================================================================
    # model can be:  a fullpath, a filename (string) located in project's glm_template_dir
    def fsl_feat(self, epi_label, in_file_name, out_dir_name, model, do_initreg=False, std_image:str="", tr:str="", te:str=""):
        """
        Runs FSL FEAT on the given input file.

        Args:
            epi_label (str): The label of the EPI image.
            in_file_name (str): The name of the input EPI image.
            out_dir_name (str): The name of the output directory.
            model (str): The name of the FEAT model.
            do_initreg (bool, optional): Whether to perform initial registration. Defaults to False.
            std_image (str, optional): The name of the standard image. Defaults to "".
            tr (str, optional): The repetition time. Defaults to "".
            te (str, optional): The echo time. Defaults to "".

        Raises:
            Exception: If the given model is not found.

        Returns:
            None: None.
        """
        if epi_label.startswith("fmri"):
            epi_dir = self.subject.fmri_dir
        else:
            epi_dir = self.subject.rs_dir

        out_dir     = os.path.join(epi_dir, out_dir_name)
        epi_image   = Image(os.path.join(epi_dir, in_file_name))

        # default params:
        if not epi_image.exist:
            print("Error in subj: " + self.subject.label + " epi_feat")
            return

        if std_image == "":
            std_image = os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm_brain")

        if not os.path.isfile(model + ".fsf"):

            model = os.path.join(self.subject.project.glm_template_dir, model + ".fsf")
            if not os.path.isfile(model + ".fsf"):
                print("Error in subj: " + self.subject.label + " epi_feat :  model " + model + ".fsf is missing")
                return

        modellabel = get_filename(model)

        # -----------------------------------------------------
        print(self.subject.label + ": FEAT with model: " + model)
        TOT_VOL_NUM = epi_image.nvols

        os.makedirs(os.path.join(epi_dir, "model"), exist_ok=True)

        OUTPUT_FEAT_FSF = os.path.join(epi_dir, "model", modellabel)
        copyfile(model + ".fsf", OUTPUT_FEAT_FSF + ".fsf")

        # FEAT fsf -------------------------------------------------------------------------------------------------------------------------
        with open(OUTPUT_FEAT_FSF + ".fsf", "a") as text_file:
            original_stdout = sys.stdout
            sys.stdout      = text_file  # Change the standard output to the file we created.

            print("", file=text_file)
            print("################################################################", file=text_file)
            print("# overriding parameters", file=text_file)
            print("################################################################", file=text_file)

            print("set fmri(npts) " + str(TOT_VOL_NUM), file=text_file)
            print("set feat_files(1) " + epi_image, file=text_file)
            print("set highres_files(1) " + self.subject.t1_brain_data, file=text_file)

            if self.subject.wb_brain_data.is_image() and do_initreg:
                print("set fmri(reginitial_highres_yn) 1", file=text_file)
                print("set initial_highres_files(1) " + self.subject.wb_brain_data, file=text_file)
            else:
                print("set fmri(reginitial_highres_yn) 0", file=text_file)

            print("set fmri(outputdir) " + out_dir, file=text_file)
            print("set fmri(regstandard) " + std_image, file=text_file)

            if tr != "":
                print("set fmri(tr) " + str(tr), file=text_file)

            if te != "":
                print("set fmri(te) " + str(te), file=text_file)

            sys.stdout = original_stdout  # Reset the standard output to its original value

            # --------------------------------------------------------------------------------------------------------------------------------------
        rrun(os.path.join(self._global.fsl_bin, "feat") + " " + OUTPUT_FEAT_FSF + ".fsf")  # execute  FEAT

    # perform aroma on feat folder data, create reg folder and copy precalculated coregistrations
    def aroma_feat(self, epi_label, input_dir, mc, aff, warp, upsampling=0, logFile=None):
        """
        Runs AROMA on the given input directory.

        Args:
            epi_label (str): The label of the EPI image.
            input_dir (str): The name of the input directory.
            mc (str): The motion correction option.
            aff (str): The affine transformation file.
            warp (str): The warp file.
            upsampling (int, optional): The upsampling factor. Defaults to 0.
            logFile (str, optional): The name of the log file. Defaults to None.

        Raises:
            Exception: If the given epi_label is not recognized.

        Returns:
            None: None.
        """
        if epi_label == "rs":
            aroma_dir           = self.subject.rs_aroma_dir
            regstd_aroma_dir    = self.subject.rs_regstd_aroma_dir

        elif epi_label.startswith("fmri"):
            aroma_dir           = self.subject.fmri_aroma_dir
            regstd_aroma_dir    = self.subject.fmri_regstd_aroma_dir
        else:
            print("ERROR in epi.aroma epi_label was not recognized")
            return

        warp = Image(warp)

        # option_string = ""
        # if mc != "":
        #     option_string = " -mc " + mc + " "

        input_reg = os.path.join(input_dir, "reg")
        os.makedirs(input_reg, exist_ok=True)
        warp.cp(os.path.join(input_reg, "highres2standard_warp"), logFile=logFile)
        copyfile(aff, os.path.join(input_reg, "example_func2highres.mat"))

        # CHECK FILE EXISTENCE #.feat
        if not os.path.isdir(input_dir):
            print(f"error in epi_aroma for subject: {self.subject.label} : you specified an incorrect folder name ({input_dir})......exiting")
            return

        print("running AROMA for subject " + self.subject.label)
        rrun(f"python2.7 {self._global.ica_aroma_script} -feat {input_dir} -out {aroma_dir}", logFile=logFile)

        if upsampling > 0:
            os.makedirs(regstd_aroma_dir, exist_ok=True)
            # problems with non linear registration....use linear one.
            copyfile(os.path.join(input_dir, "design.fsf"), os.path.join(aroma_dir, "design.fsf"))
            copytree(os.path.join(input_dir, "reg"), aroma_dir)
            rrun(os.path.join(self._global.fsl_bin, "featregapply") + " " + aroma_dir, logFile=logFile)

            # upsampling of standard
            rrun(f"{os.path.join(self._global.fsl_bin, 'flirt')} -ref {os.path.join(input_dir, 'reg', 'standard')} -in {os.path.join(input_dir, 'reg', 'standard')} -out {os.path.join(regstd_aroma_dir, 'standard')} -applyisoxfm {upsampling}", logFile=logFile)
            rrun(f"{os.path.join(self._global.fsl_bin, 'flirt')} -ref {os.path.join(regstd_aroma_dir, 'standard')} -in {os.path.join(input_dir, 'reg', 'highres')} -out {os.path.join(regstd_aroma_dir, 'bg_image')} -applyxfm -init {os.path.join(input_dir, 'reg', 'highres2standard.mat')} -interp sinc -datatype float", logFile=logFile)
            rrun(f"{os.path.join(self._global.fsl_bin, 'flirt')} -ref {os.path.join(regstd_aroma_dir, 'standard')} -in {os.path.join(aroma_dir, 'denoised_func_data_nonaggr')} -out {os.path.join(regstd_aroma_dir, 'filtered_func_data')} -applyxfm -init {os.path.join(input_dir, 'reg', 'example_func2standard.mat')} -interp trilinear -datatype float", logFile=logFile)
            rrun(f"{os.path.join(self._global.fsl_bin, 'fslmaths')} {os.path.join(regstd_aroma_dir, 'filtered_func_data')} -Tstd -bin {os.path.join(regstd_aroma_dir, 'mask')} -odt char", logFile=logFile)

    def ica_fix(self, epi_label):
        """
        Runs ICA-FIX on the given EPI image.

        Args:
            epi_label (str): The label of the EPI image.

        Raises:
            Exception: If the given epi_label is not recognized.

        Returns:
            None: None.
        """
        if epi_label == "rs":
            rs_icafix_dir       = self.subject.rs_fix_dir
            regstd_aroma_dir    = self.subject.rs_regstd_aroma_dir

        elif epi_label.startswith("fmri"):
            rs_icafix_dir       = self.subject.fmri_icafix_dir
            regstd_aroma_dir    = self.subject.fmri_regstd_aroma_dir
        else:
            print("ERROR in epi.ica_fix epi_label was not recognized")
            return

    def create_regstd(self, postnuisance, feat_preproc_odn="resting", overwrite:bool=False, islin=False, logFile=None):
        """
        Creates the standard space template for the resting state data.

        Args:
            postnuisance (str): The name of the post-nuisance image.
            feat_preproc_odn (str, optional): The name of the FEAT preprocessing output directory. Defaults to "resting".
            overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
            islin (bool, optional): Whether to use linear or nonlinear registration. Defaults to False.
            logFile (str, optional): The name of the log file. Defaults to None.

        Raises:
            Exception: If the given post-nuisance image is not found.

        Returns:
            None: None.
        """
        # mask from preproc feat
        mask = os.path.join(self.subject.rs_dir, feat_preproc_odn + ".feat", "mask")
        if not Image(self.subject.rs_final_regstd_mask + "_mask") or overwrite:
            self.subject.transform.transform_roi("rsTOstd4", "abs", islin=islin, rois=[mask])
            Image(os.path.join(self.subject.roi_std4_dir, "mask_std4")).cp(self.subject.rs_final_regstd_mask + "_mask", logFile=logFile)

        # mask from example_function (the one used to calculate all the co-registrations)
        if not self.subject.rs_final_regstd_mask.exist or overwrite:
            self.subject.transform.transform_roi("rsTOstd4", "abs", islin=islin, rois=[self.subject.rs_examplefunc_mask])
            Image(os.path.join(self.subject.roi_std4_dir, "mask_example_func_std4")).cp(self.subject.rs_final_regstd_mask, logFile=logFile)

        # brain
        if not self.subject.rs_final_regstd_bgimage.exist or overwrite:
            self.subject.transform.transform_roi("hrTOstd4", "abs", islin=islin, rois=[self.subject.t1_brain_data])
            Image(os.path.join(self.subject.roi_std4_dir, self.subject.t1_image_label + "_brain_std4")).cp(self.subject.rs_final_regstd_bgimage, logFile=logFile)

        # functional data
        if not self.subject.rs_final_regstd_image.exist or overwrite:
            self.subject.transform.transform_roi("rsTOstd4", "abs", islin=islin, rois=[postnuisance])
            Image(os.path.join(self.subject.roi_std4_dir, self.subject.rs_post_nuisance_image_label + "_std4")).mv(self.subject.rs_final_regstd_image, logFile=logFile)

    @staticmethod
    def get_slicetiming_params(nslices, scheme=1, params=None):
        """
        Returns the slice timing parameters for FSL FEAT.

        Args:
            nslices (int): The number of slices.
            scheme (int, optional): The slice timing scheme. Defaults to 1.
            params (array, optional): The slice timing parameters. Defaults to None.

        Returns:
            array: The slice timing parameters.
        """
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

        str_params = [str(p) for p in params]
        return str_params

    def prepare_for_spm(self, in_img, subdirmame="temp_split"):
        """
        This function presently doesn't do anything

        Raises:
            Exception if called

        """
        raise Exception("ERROR in prepare for spm")
        folder = os.path.dirname(in_img)
        self.subject.epi_split(in_img, subdirmame)
        outdir = os.path.join(folder, subdirmame)
        os.chdir(outdir)
        for f in os.scandir():
            f = Image(f)
            if f.is_image():
                f.unzip(os.path.join(outdir, f.name), replace=True)

    # ===============================================================================
    # FRAMEWORK (copy data across relevant folders, clean up)
    # ===============================================================================
    def cleanup(self, lvl=Global.CLEANUP_LVL_MIN):
        """
        Cleans up the resting state data for the given subject.

        Args:
            lvl (int, optional): The level of cleanup. Defaults to Global.CLEANUP_LVL_MIN.

        Raises:
            Exception: If the given subject is not recognized.

        Returns:
            None: None.
        """
        os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_preprocess_image_label))
        os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_aroma_image_label))
        os.removedirs(os.path.join(self.subject.rs_dir, "resting.feat"))
        os.removedirs(self.subject.rs_aroma_dir)

        if lvl == Global.CLEANUP_LVL_MED:
            # copy melodic report i
            os.makedirs(self.subject.rs_melic_dir)
            rrun(f"mv {os.path.join(self.subject.rs_default_mel_dir, 'filtered_func_data_ica.ica', 'report')} {self.subject.rs_melic_dir}")

            rrun(f"rm -rf {self.subject.rs_default_mel_dir}")
            os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_nuisance_melodic_image_label))

        elif lvl == Global.CLEANUP_LVL_HI:

            os.removedirs(self.subject.rs_melic_dir)

            rrun(f"rm -rf {self.subject.rs_default_mel_dir}")
            os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_nuisance_melodic_image_label))

    # take a preproc step in the individual space (epi), convert to std4 and copy to resting/reg_std folder
    def adopt_rs_preproc_step(self, step_label, outsuffix:str=""):
        """
        Copies the given preprocessed step from the individual space to the standard space and adds the given suffix to the filename.

        Args:
            step_label (str): The label of the preprocessed step.
            outsuffix (str, optional): The suffix to add to the filename. Defaults to "".

        Returns:
            None: None.
        """
        in_img = os.path.join(self.subject.rs_dir, step_label)
        self.subject.transform.transform_roi("epiTOstd4", "abs", rois=[in_img])  # add _std4 to roi name)
        in_img4 = Image(os.path.join(self.subject.roi_std4_dir, step_label + "_std4"))
        in_img4.mv(self.subject.rs_final_regstd_image + outsuffix)

    # take the reg_standard output of feat/melodic, convert to std4 and copy to resting/reg_std folder
    def adopt_rs_preproc_folderoutput(self, proc_folder):
        """
        Copies the filtered_func_data, mask, and bg_image from the given FEAT reg_standard folder to the standard space and replaces the corresponding files in the resting state folder.

        Args:
            proc_folder (str): The path to the FEAT reg_standard folder.

        Returns:
            None: None.
        """
        in_img      = os.path.join(proc_folder, "reg_standard", "filtered_func_data")
        in_mask     = os.path.join(proc_folder, "reg_standard", "mask")
        in_bgimage  = os.path.join(proc_folder, "reg_standard", "bg_image")

        self.subject.transform.transform_roi("stdTOstd4", "abs", rois=[in_img, in_mask, in_bgimage])

        in_img4     = Image(os.path.join(self.subject.roi_std4_dir, "filtered_func_data_std4"))
        in_mask4    = Image(os.path.join(self.subject.roi_std4_dir, "mask_std4"))
        in_bgimage4 = Image(os.path.join(self.subject.roi_std4_dir, "bg_image_std4"))

        in_img4.mv(self.subject.rs_final_regstd_image)
        in_mask4.cp(self.subject.rs_final_regstd_mask)
        in_bgimage4.cp(self.subject.rs_final_regstd_bgimage)

    def reg_copy_feat(self, epi_label, std_image:str=""):
        """
        Copies the necessary files from a FEAT preprocessing directory to the standard space.

        Args:
            epi_label (str): The label of the EPI image.
            std_image (str, optional): The path to the standard space image. Defaults to "".

        Raises:
            Exception: If the given epi_label is not recognized.

        Returns:
            None: None.
        """
        if epi_label == "rs":
            epi_image       = self.subject.rs_data
            epi_dir         = self.subject.rs_dir
            out_dir         = os.path.join(epi_dir, "resting.feat")
            exfun           = self.subject.rs_examplefunc
            reg_dir         = self.subject.roi_rs_dir

            std2epi_warp    = self.subject.std2rs_warp
            epi2std_warp    = self.subject.rs2std_warp

            std2epi_mat     = self.subject.std2rs_mat
            epi2std_mat     = self.subject.rs2std_mat

            epi2hr_mat      = self.subject.rs2hr_mat
            hr2epi_mat      = self.subject.hr2rs_mat

        elif epi_label.startswith("fmri"):
            epi_image       = os.path.join(self.subject.fmri_dir, self.subject.label + "-" + epi_label)
            epi_dir         = self.subject.fmri_dir
            out_dir         = os.path.join(epi_dir, epi_label + ".feat")
            exfun           = self.subject.fmri_examplefunc
            reg_dir         = self.subject.roi_fmri_dir

            std2epi_warp    = self.subject.std2fmri_warp
            epi2std_warp    = self.subject.fmri2std_warp

            std2epi_mat     = self.subject.std2fmri_mat
            epi2std_mat     = self.subject.fmri2std_mat

            epi2hr_mat      = self.subject.fmri2hr_mat
            hr2epi_mat      = self.subject.hr2fmri_mat
        else:
            raise Exception("Error in reg_copy_feat...given epi_label (" + epi_label + " is not valid")

        if std_image == "":
            std_image = Image(os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm_brain"))
        else:
            std_image = Image(std_image, must_exist=True, msg="epi_reg_copy_feat of subject " + self.subject.label + " given std_img is not present")

        Image(os.path.join(out_dir, "reg", "example_func")).cp(exfun)

        copyfile(os.path.join(out_dir, "reg", "example_func2highres.mat"), epi2hr_mat)
        copyfile(os.path.join(out_dir, "reg", "highres2example_func.mat"), hr2epi_mat)

        copyfile(os.path.join(out_dir, "reg", "standard2highres.mat"), self.subject.std2hr_mat)
        copyfile(os.path.join(out_dir, "reg", "highres2standard.mat"), self.subject.hr2std_mat)

        copyfile(os.path.join(out_dir, "reg", "standard2example_func.mat"), std2epi_mat)
        copyfile(os.path.join(out_dir, "reg", "example_func2standard.mat"), epi2std_mat)

        # copy/create warps
        Image(os.path.join(out_dir, "reg", "highres2standard_warp")).cp_notexisting(self.subject.hr2std_warp)

        if not self.subject.std2hr_warp.exist:
            rrun(os.path.join(self._global.fsl_bin, "invwarp") + " -w " + self.subject.hr2std_warp + " -o " + self.subject.std2hr_warp + " -r " + self.subject.t1_brain_data)

        # epi -> highres -> standard
        if not epi2std_warp.exist:
            rrun(os.path.join(self._global.fsl_bin, "convertwarp") + " --ref=" + std_image + " --premat=" + epi2hr_mat + " --warp1=" + self.subject.hr2std_warp + " --out=" + epi2std_warp)

        # invwarp: standard -> highres -> epi
        if not std2epi_warp.exist:
            rrun(os.path.join(self._global.fsl_bin, "invwarp") + " -w " + epi2std_warp + " -o " + std2epi_warp + " -r " + exfun)

    @staticmethod
    def coregister_epis(ref, target, trgpostfix="_ref", img2transform=None, ref_vol=3):
        """
        Coregisters two EPI images.

        Args:
            ref (Image): The reference image.
            target (Image): The target image.
            trgpostfix (str, optional): The postfix to add to the target image. Defaults to "_ref".
            img2transform (list, optional): A list of images to transform. Defaults to None.
            ref_vol (int, optional): The reference volume. Defaults to 3.

        Returns:
            str: The path to the output warp file.
        """
        target      = Image(target)
        ref         = Image(ref)

        omat        = os.path.join(target.dir, "temp_trg2ref")
        owarp       = os.path.join(target.dir, "temp_trg2ref_warp")
        otrg        = target.add_postfix2name(trgpostfix)
        otrg_lin    = target.add_postfix2name(trgpostfix + "_lin")

        single_ref_vol = ref.add_postfix2name("_sv")
        single_trg_vol = target.add_postfix2name("_sv")

        ref_mask       = ref.add_postfix2name("_sv_mask")
        trg_mask       = target.add_postfix2name("_sv_mask")

        if img2transform is None:
            cout = ""                          # don't want to use warp for further coreg, only interested in trg coreg
        else:
            cout = "--cout=" + owarp + " "     # want to use warp for further coregs

        ref.get_nth_volume(single_ref_vol, ref_mask, volnum=ref_vol, logFile=None)     # it creates ref_mask
        target.get_nth_volume(single_trg_vol, trg_mask, volnum=ref_vol, logFile=None)  # it creates trg_mask

        rrun(f"flirt  -in {single_trg_vol} -ref {single_ref_vol} -omat {omat} -out {otrg_lin}")
        rrun(f"fnirt --in={single_trg_vol} --ref={single_ref_vol} --aff={omat} --refmask={ref_mask} {cout} --iout={otrg}")

        if img2transform is not None:
            for img in img2transform:
                oimg = Image(img).add_postfix2name(trgpostfix)
                rrun(f"applywarp -i {img} -w {owarp} -r {single_ref_vol} -o {oimg} --interp=spline")

        ref_mask.rm()
        trg_mask.rm()
        return owarp

    def normalize(self, inimg=None, logFile=None):
        """
        Normalizes an EPI image.

        Args:
            inimg (Image, optional): The EPI image to normalize. If None, the default EPI image for the subject is used. If "rs", the resting state EPI image is used. If "fmri", the functional MRI EPI image is used. Defaults to None.
            logFile (str, optional): The name of the log file. Defaults to None.

        Returns:
            Image: The normalized EPI image.

        Raises:
            Exception: If the given inimg is not recognized.

        """
        if inimg is None:
            inimg = Image(inimg, must_exist=True, msg="Error in epi.normalize of subj: " + self.subject.label )
        elif inimg == "rs":
            inimg = self.subject.rs_data
        elif inimg == "fmri":
            inimg = self.subject.fmri_data

        iname       = inimg.name
        params      = " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear"
        omat        = os.path.join(os.path.dirname(inimg), iname + "2hr.mat")
        epi_sv      = Image(os.path.join(os.path.dirname(inimg), iname + "_sv"))
        owarp       = os.path.join(os.path.dirname(inimg), iname + "2std_warp")
        norm_input  = os.path.join(os.path.dirname(inimg), iname +  "_norm")
        inimg.get_nth_volume(epi_sv, None, 0, logFile)
        flirt(omat, epi_sv, self.subject.t1_brain_data, params, logFile=logFile)

        if self.subject.transform.hr2std_warp.exist:
            rrun(f"convertwarp --ref={self.subject.std_img} --premat={omat} --warp1={self.subject.transform.hr2std_warp} --out={owarp}", logFile=logFile)
            rrun(f"applywarp -i {inimg} -r {self.subject.std_img} -o {norm_input} --warp={owarp}", logFile=logFile)

        epi_sv.rm()

    #endregion
    # ==================================================================================================================================================
