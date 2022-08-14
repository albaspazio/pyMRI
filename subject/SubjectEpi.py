import os
import sys
from shutil import copyfile, rmtree
from numpy import arange, concatenate, array

from Global import Global
from data.utilities import list2spm_text_column
from group.SPMStatsUtils import SPMStatsUtils
from utility.images.Image import Image, Images
from utility.images.images import add_postfix2name
from utility.images.transform_images import flirt
from utility.myfsl.utils.run import rrun
from utility.matlab import call_matlab_spmbatch, call_matlab_function
from utility.utilities import sed_inplace, compress, copytree, get_filename


class SubjectEpi:

    def __init__(self, subject, _global):
        self.subject = subject
        self._global = _global

    # ==================================================================================================================================================
    # GENERAL (pepolar corr, fsl_feat, aroma, remove_nuisance)
    # ==================================================================================================================================================
    def get_nth_volume(self, in_img, out_img=None, out_mask_img=None, volnum=3, logFile=None):

        if out_mask_img is None:
            out_mask_img = add_postfix2name(in_img, "_mask")

        if out_mask_img is None:
            out_mask_img = add_postfix2name(in_img, "_mask")

        rrun("fslmaths "    + in_img + " " + add_postfix2name(in_img, "_prefiltered_func_data") + " -odt float", logFile=logFile)
        rrun("fslroi "      + add_postfix2name(in_img, "_prefiltered_func_data") + " " + out_img + " " + str(volnum) + " 1", logFile=logFile)
        rrun("bet2 "        + out_img + " " + out_img + " -f 0.3", logFile=logFile)
        rrun("imrm "        + "*prefiltered_func_data*",  logFile=logFile)
        rrun("fslmaths "    + out_img + " -bin " + out_mask_img,  logFile=logFile)  # create example_function mask (a -thr 0.01/0.1 could have been used to further reduce it)

        return out_img

    def get_example_function(self, seq="rs", vol_num=100, logFile=None):

        if seq == "rs":
            exfun   = self.subject.rs_examplefunc
            data    = self.subject.rs_data
            m_exfun = self.subject.rs_examplefunc_mask
        else:
            exfun   = self.subject.fmri_examplefunc
            data    = self.subject.fmri_data
            m_exfun = self.subject.fmri_examplefunc_mask

        if not exfun.exist:
            self.get_nth_volume(data, exfun, m_exfun, vol_num, logFile)

        return Image(exfun)

    def slice_timing(self, TR, num_slices=-1, epi_image=None, TA=-1, acq_scheme=0, ref_slice=-1, slice_timing=None, spm_template_name="subj_spm_fmri_slice_timing_correction"):

        # default params:
        if epi_image is None:
            epi_image = self.subject.fmri_data
        else:
            epi_image = Image(epi_image, must_exist=True, msg="Subject.epi.slice_timing")

        if num_slices == -1:
            pass

        # TA - if not otherwise indicated, it assumes the acquisition is continuous and TA = TR - (TR/num slices)
        if TA == -1:
            TA = TR - (TR / num_slices)

        if ref_slice == -1:
            ref_slice = num_slices // 2 + 1

        if slice_timing is None:
            slice_timing = self.get_slicetiming_params(num_slices, acq_scheme)
        else:
            slice_timing = [str(p) for p in slice_timing]

        # substitute for all the volumes + rest of params
        epi_nvols       = epi_image.get_nvoxels()
        epi_image.check_if_uncompress()

        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume      = epi_image.spmpath + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' + "'"

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)
        sed_inplace(out_batch_job, '<NUM_SLICES>', str(num_slices))
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<TA_VALUE>', str(TA))
        sed_inplace(out_batch_job, '<SLICETIMING_PARAMS>', ' '.join(slice_timing))
        sed_inplace(out_batch_job, '<REF_SLICE>', str(ref_slice))

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

        input_dir   = epi_image.dir    # /a/b/c
        in_label    = epi_image.name   # name

        compress(os.path.join(input_dir, "a" + in_label + ".nii"), os.path.join(input_dir, "a" + in_label + ".nii.gz"), replace=True)
        os.remove(epi_image.spmpath)

    # PERFORM motion correction toward the volume closest to PA sequence and then perform TOPUP CORRECTION
    # - epi_ref_vol/pe_ref_vol =-1 means use the middle volume
    # 1: get number of volumes of epi_PA image in opposite phase-encoding direction and extract middle volume (add "_ref")
    # 2: look for the epi volume closest to epi_pa_ref volume
    # 3: merge the 2 ref volumes into one (add "_ref")
    # 4: run topup using ref, acq params; used_templates: "_topup"
    # 5: do motion correction with the chosen volume [default do it]
    # 6: applytopup --> choose images whose distortion we want to correct
    def topup_correction(self, in_ap_img, in_pa_img, acq_params, ap_ref_vol=-1, pa_ref_vol=-1, config="b02b0.cnf", motion_corr=True, logFile=None):

        #  /a/b/c/name.nii.gz
        in_ap_img       = Image(in_ap_img)
        ap_distorted    = Image(in_ap_img.fpathnoext + "_distorted")
        in_pa_img       = Image(in_pa_img)

        input_dir = in_ap_img.dir    # /a/b/c

        if not ap_distorted.exist:
            in_ap_img.cp(ap_distorted)

        ap_ref          = Image(os.path.join(input_dir, "ap_ref"))
        pa_ref          = Image(os.path.join(input_dir, "pa_ref"))
        ap_pa_ref       = Image(os.path.join(input_dir, "ap_pa_ref"))
        ap_pa_ref_topup = Image(os.path.join(input_dir, "ap_pa_ref_topup"))

        # 1
        if pa_ref_vol == -1:
            nvols_pe = in_pa_img.get_nvoxels()
            central_vol_pa = int(nvols_pe) // 2
        else:
            central_vol_pa = pa_ref_vol

        rrun("fslselectvols -i " + in_pa_img + " -o " + pa_ref + " --vols=" + str(central_vol_pa), logFile=logFile)

        # 2
        if ap_ref_vol == -1:
            closest_vol = self.get_closest_volume(in_ap_img, in_pa_img, pa_ref_vol) - 1 # returns a 1-based volume, so I subtract 1
        else:
            closest_vol = ap_ref_vol

        rrun("fslselectvols -i " + in_ap_img + " -o " + ap_ref + " --vols=" + str(closest_vol), logFile=logFile)

        # 3
        rrun("fslmerge -t " + ap_pa_ref + " " + ap_ref + " " + pa_ref, stop_on_error=False)

        # 4 —assumes merged epi volumes appear in the same order as acqparams.txt (--datain)
        rrun("topup --imain=" + ap_pa_ref + " --datain=" + acq_params + " --config=" + config + " --out=" + ap_pa_ref_topup, logFile=logFile) # + " --iout=" + self.subject.fmri_data + "_PE_ref_topup_corrected")

        img2correct = in_ap_img
        # 5 -motion correction using central_vol (given or that closest to _PA image)
        if motion_corr:
            img2correct = Image(os.path.join(input_dir, "r" + in_ap_img.name))
            self.spm_motion_correction(in_ap_img, ref_vol=closest_vol)   # add r in front of img name
            os.remove(in_ap_img + ".nii")       # remove old with-motion SUBJ-fmri.nii
            os.remove(in_ap_img + ".nii.gz")    # remove old with-motion SUBJ-fmri.nii.gz
            img2correct.compress(in_ap_img + ".nii.gz", replace=True)  # zip rSUBJ-fmri.nii => rSUBJ-fmri.nii.gz

        # 6 —again these must be in the same order as --datain/acqparams.txt // "inindex=" values reference the images-to-correct corresponding row in --datain and --topup
        rrun("applytopup --imain=" + img2correct + " --topup=" + ap_pa_ref_topup + " --datain=" + acq_params + " --inindex=1 --method=jac --interp=spline --out=" + img2correct, logFile=logFile)

        os.system("rm " + input_dir + "/" + "ap_*")
        os.system("rm " + input_dir + "/" + "pa_*")

        print("topup correction of subj: " + self.subject.label + " finished. closest volume is: " + str(closest_vol))
        return closest_vol

    # model can be:  a fullpath, a filename (string) located in project's glm_template_dir
    def fsl_feat(self, epi_label, in_file_name, out_dir_name, model, do_initreg=False, std_image="", tr="", te=""):

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
        TOT_VOL_NUM = epi_image.get_nvoxels()

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
            print("error in epi_aroma for subject: " + self.subject.label + ": you specified an incorrect folder name (" + input_dir + ")......exiting")
            return

        print("running AROMA for subject " + self.subject.label)
        rrun("python2.7 " + self._global.ica_aroma_script + " -feat " + input_dir + " -out " + aroma_dir, logFile=logFile)

        if upsampling > 0:
            os.makedirs(regstd_aroma_dir, exist_ok=True)
            # problems with non linear registration....use linear one.
            copyfile(os.path.join(input_dir, "design.fsf"), os.path.join(aroma_dir, "design.fsf"))
            copytree(os.path.join(input_dir, "reg"), aroma_dir)
            rrun(os.path.join(self._global.fsl_bin, "featregapply") + " " + aroma_dir, logFile=logFile)

            # upsampling of standard
            rrun(os.path.join(self._global.fsl_bin, "flirt") + " -ref " + os.path.join(input_dir, "reg","standard") + " -in " + os.path.join(input_dir, "reg", "standard")
                    + " -out " + os.path.join(regstd_aroma_dir, "standard") + " -applyisoxfm " + str(upsampling), logFile=logFile)
            rrun(os.path.join(self._global.fsl_bin, "flirt") + " -ref " + os.path.join(regstd_aroma_dir, "standard") + " -in " + os.path.join(input_dir, "reg", "highres")
                    + " -out " + os.path.join(regstd_aroma_dir,"bg_image") + " -applyxfm -init " + os.path.join(input_dir, "reg", "highres2standard.mat") + " -interp sinc -datatype float", logFile=logFile)
            rrun(os.path.join(self._global.fsl_bin, "flirt") + " -ref " + os.path.join(regstd_aroma_dir, "standard") + " -in " + os.path.join(aroma_dir, "denoised_func_data_nonaggr")
                    + " -out " + os.path.join(regstd_aroma_dir, "filtered_func_data") + " -applyxfm -init " + os.path.join(input_dir, "reg", "example_func2standard.mat") + " -interp trilinear -datatype float", logFile=logFile)
            rrun(os.path.join(self._global.fsl_bin, "fslmaths") + " " + os.path.join(regstd_aroma_dir, "filtered_func_data") + " -Tstd -bin " + os.path.join(regstd_aroma_dir, "mask") + " -odt char", logFile=logFile)

    def ica_fix(self, epi_label):

        if epi_label == "rs":
            rs_icafix_dir       = self.subject.rs_fix_dir
            regstd_aroma_dir    = self.subject.rs_regstd_aroma_dir

        elif epi_label.startswith("fmri"):
            rs_icafix_dir       = self.subject.fmri_icafix_dir
            regstd_aroma_dir    = self.subject.fmri_regstd_aroma_dir
        else:
            print("ERROR in epi.ica_fix epi_label was not recognized")
            return

    def remove_nuisance(self, in_img_name, out_img_name, epi_label="rs", ospn="", hpfsec=100):

        if epi_label == "rs":
            in_img          = Image(os.path.join(self.subject.rs_dir, in_img_name))
            out_img         = Image(os.path.join(self.subject.rs_dir, out_img_name))
            series_wm       = self.subject.rs_series_wm + ospn + ".txt"
            series_csf      = self.subject.rs_series_csf + ospn + ".txt"
            output_series   = os.path.join(self.subject.rs_series_dir, "nuisance_timeseries" + ospn + ".txt")
        else:
            print('WARNING in remove_nuisance of subject ' + self.subject.label + ". presently, remove nuisance is allowed only for resting state data")
            return

        if not in_img.exist:
            print('ERROR in remove_nuisance of subject ' + self.subject.label + ". input image (" + in_img + ") is missing")
            return

        tr          = in_img.get_epi_tr()
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

        rrun("fslmeants -i " + in_img + " -o " + series_wm + " -m " + self.subject.rs_mask_t1_wmseg4nuis + " --no_bin")
        rrun("fslmeants -i " + in_img + " -o " + series_csf + " -m " + self.subject.rs_mask_t1_csfseg4nuis + " --no_bin")

        if os.path.isfile(series_csf) and os.path.isfile(series_wm):
            os.system("paste " + series_wm + " " + series_csf + " > " + output_series)
            # rrun("paste " + series_wm + " " + series_csf + " > " + output_series) # ISSUE: doesn't work. don't know why

        tempMean = os.path.join(self.subject.rs_dir, "tempMean.nii.gz")
        residual = os.path.join(self.subject.rs_dir, "residual.nii.gz")

        rrun("fslmaths " + in_img + " -Tmean " + tempMean)
        rrun("fsl_glm -i " + in_img + " -d " + output_series + " --demean --out_res=" + residual)

        rrun("fslcpgeom " + in_img + ".nii.gz " + residual)  # solves a bug in fsl_glm which writes TR=1 in residual.
        rrun("fslmaths " + residual + " -bptf " + str(hpf_sigma) + " -1 -add " + tempMean + " " + out_img)

        os.remove(residual)
        os.remove(tempMean)

    def create_regstd(self, postnuisance, feat_preproc_odn="resting", overwrite=False, islin=False, logFile=None):
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

    # ==================================================================================================================================================
    # fMRI
    # ==================================================================================================================================================
    # epi_spm_XXXXX are methods editing and lauching a SPM batch file

    # coregister epi (or a given image) to given volume of given image (usually the epi itself, the pepolar in case of distortion correction process)
    # automatically put an "r" in front of the given file name
    def spm_motion_correction(self, epi2correct, ref_image=None, ref_vol=1,
                              spm_template_name="subj_spm_fmri_realign_estimate_reslice_to_given_vol"):

        epi2correct = Image(epi2correct, must_exist=True, msg="Subject.epi.spm_motion_correction")

        # check if ref image is valid (if not specified, use in_img)
        if ref_image is None:
            ref_image = epi2correct
        else:
            ref_image = Image(ref_image, must_exist=True, msg="Subject.epi.spm_motion_correction")

        # upzip whether zipped
        epi2correct.check_if_uncompress()
        ref_image.check_if_uncompress()

        # 2.1: select the input spm template obtained from batch (we defined it in spm_template_name) + its run file …
        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        # 2.2: create "output spm template" by copying "input spm template" + changing general tags for our specific ones…
        ref_vol = max(ref_vol, 1)
        sed_inplace(out_batch_job, '<REF_IMAGE,refvol>', ref_image + '.nii,' + str(ref_vol))  # <-- i added 1 to ref_volume_pe bc spm counts the volumes from 1, not from 0 as FSL

        # 2.2' …now we want to select all the volumes from the epi file and insert that into the template:
        epi_nvols       = epi2correct.get_nvoxels()
        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume      = "'" + epi2correct.spmpath + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n'

        sed_inplace(out_batch_job, '<TO_ALIGN_IMAGES,1-n_vols>', epi_all_volumes)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    def get_closest_volume(self, in_image, ref_image, ref_volume=-1):
        # will calculate the closest vol from given epi image to ref_image
        # Steps:
        # 0: get epi_pe central volume + unzip so SPM can use it
        # 1: merge all the sessions into one file ("_merged-sessions") + unzip so SPM can use it
        # 2: align all the volumes within merged file to epi_pe central volume (SPM12-Realign:Estimate)
        # 3: calculate the "less motion corrected" volume from the merged file with respect to the epi-pe in terms of rotation around x, y and z axis).

        in_image    = Image(in_image, must_exist=True,  msg="Subject.epi.get_closest_volume")       # TODO: evalute whether this check can be asked to Image (e.g. Image(in_image, must_exist=True)) which raises an exception ,instead of returning
        ref_image   = Image(ref_image, must_exist=True, msg="Subject.epi.get_closest_volume")

        input_dir   = in_image.dir

        # create temp folder, copy there epi and epi_pe, unzip and run mc (then I can simply remove it when ended)
        temp_distorsion_mc  = os.path.join(input_dir, "temp_distorsion_mc")
        os.makedirs(temp_distorsion_mc, exist_ok=True)
        temp_epi            = Image(os.path.join(temp_distorsion_mc, in_image.name))
        temp_epi_ref        = Image(os.path.join(temp_distorsion_mc, in_image.name + "_ref"))

        if not os.path.isfile(temp_epi + ".nii"):
            if os.path.isfile(in_image + ".nii"):
                in_image.cp(temp_epi + ".nii")
            else:
                in_image.unzip(temp_epi + ".nii")

        if not os.path.isfile(temp_epi_ref + ".nii"):
            if os.path.isfile(ref_image + ".nii"):
                ref_image.cp(temp_epi_ref + ".nii")
            else:
                ref_image.unzip(temp_epi_ref + ".nii")

        if ref_volume == -1:
            # 0
            epi_pe_nvols    = ref_image.get_nvoxels()
            ref_volume      = epi_pe_nvols // 2     # 0-based. in spm_motioncorrection get 1-based

        # estimate BUT NOT reslice
        self.spm_motion_correction(temp_epi, temp_epi_ref, ref_volume, spm_template_name="subj_spm_fmri_realign_estimate_to_given_vol")

        # 3: call matlab function that calculates best volume (1-based):
        best_vol = call_matlab_function("least_mov", [self._global.spm_functions_dir], "\"" + os.path.join(temp_distorsion_mc, "rp_" + in_image.name + "_ref" + '.txt' + "\""))[1]
        rmtree(temp_distorsion_mc)

        return int(best_vol)

    def prepare_for_spm(self, in_img, subdirmame="temp_split"):

        raise Exception("ERROR in prepare for spm")
        folder = os.path.dirname(in_img)
        self.subject.epi_split(in_img, subdirmame)
        outdir = os.path.join(folder, subdirmame)
        os.chdir(outdir)
        for f in os.scandir():
            f = Image(f)
            if f.is_image():
                f.unzip(os.path.join(outdir, f.name), replace=True)

    def spm_fmri_preprocessing_motioncorrected(self, epi_image=None, spm_template_name='subj_spm_fmri_preprocessing_noslicetiming_norealign'):

        # default params:
        if epi_image is None:
            epi_image = self.subject.fmri_data_mc
        epi_image = Image(epi_image, must_exist=True, msg="Subject.epi.spm_fmri_preprocessing_motioncorrected")

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        # substitute for all the volumes + rest of params
        epi_nvols   = epi_image.get_nvoxels()
        epi_image.check_if_uncompress()

        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume = epi_image.spmpath + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' + "'"

        mean_image = os.path.join(self.subject.fmri_dir, "mean" + self.subject.fmri_image_label + ".nii")

        sed_inplace(out_batch_job, '<RESLICE_MEANIMAGE>', mean_image)
        sed_inplace(out_batch_job, '<T1_IMAGE>', self.subject.t1_data.spmpath + ',1')
        sed_inplace(out_batch_job, '<SPM_DIR>', self._global.spm_dir)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    def spm_fmri_preprocessing(self, num_slices, TR, TA=0, acq_scheme=0, ref_slice=-1, slice_timing=None,
                               epi_images=None, smooth=6, spm_template_name='subj_spm_fmri_full_preprocessing'):

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

        nsessions = len(valid_images)

        if slice_timing is None:
            slice_timing = self.subject.epi_get_slicetiming_params(num_slices, acq_scheme)

            # TA - if not otherwise indicated, it assumes the acquisition is continuous and TA = TR - (TR/num slices)
            if TA == 0:
                TA = TR - (TR / num_slices)

        else:
            num_slices      = len(slice_timing)
            slice_timing    = [str(p) for p in slice_timing]
            TA              = 0

        # takes central slice as a reference
        if ref_slice == -1:
            ref_slice = num_slices // 2 + 1

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        # substitute for all the volumes + rest of params
        epi_all_volumes = ''
        for img in valid_images:

            epi_nvols       = img.get_nvoxels()
            img.check_if_uncompress()

            epi_all_volumes += '{'
            for i in range(1, epi_nvols + 1):
                epi_volume =  "'" + img.spmpath + ',' + str(i) + "'"
                epi_all_volumes = epi_all_volumes + epi_volume + '\n'

            epi_all_volumes += '}\n'

        # slice-timing sessions
        slice_timing_sessions = ""
        for i in range(nsessions):
            slice_timing_sessions += "matlabbatch{2}.spm.temporal.st.scans{" + str(i+1) + "}(1) = cfg_dep('Realign: Estimate & Reslice: Resliced Images (Sess " + str(i+1) + ")', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('.', 'sess', '()', {" + str(i+1) + "}, '.', 'rfiles'));\n"

        # normalize write
        normalize_write_sessions = ""
        for i in range(nsessions):
            normalize_write_sessions += "matlabbatch{5}.spm.spatial.normalise.write.subj.resample(" + str(i+1) + ") = cfg_dep('Slice Timing: Slice Timing Corr. Images (Sess 1)', substruct('.', 'val', '{}', {2}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('()', {" + str(i+1) + "}, '.', 'files'));\n"

        mean_image = os.path.join(self.subject.fmri_dir, "mean" + self.subject.fmri_image_label + ".nii")

        if not self.subject.t1_data.uexist:
            self.subject.t1_data.unzip(replace=False)

        smooth_schema = "[" + str(smooth) + " " + str(smooth) + " " + str(smooth) + "]"

        sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)
        sed_inplace(out_batch_job, '<SLICE_TIMING_SESSIONS>', slice_timing_sessions)
        sed_inplace(out_batch_job, '<NORMALIZE_WRITE_SESSIONS>', normalize_write_sessions)

        sed_inplace(out_batch_job, '<NUM_SLICES>', str(num_slices))
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<TA_VALUE>', str(TA))
        sed_inplace(out_batch_job, '<SLICETIMING_PARAMS>', ' '.join(slice_timing))
        sed_inplace(out_batch_job, '<REF_SLICE>', str(ref_slice))
        sed_inplace(out_batch_job, '<RESLICE_MEANIMAGE>', mean_image)
        sed_inplace(out_batch_job, '<T1_IMAGE>', self.subject.t1_data + '.nii,1')
        sed_inplace(out_batch_job, '<SPM_DIR>', self._global.spm_dir)
        sed_inplace(out_batch_job, '<SMOOTH_SCHEMA>', smooth_schema)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    # conditions_lists[{"name", "onsets", "duration"}, ....]
    def spm_fmri_1st_level_analysis(self, analysis_name, TR, num_slices, conditions_lists, events_unit="secs",
                                    spm_template_name='subj_spm_fmri_stats_1st_level', rp_filename=""):

        # default params:
        stats_dir = os.path.join(self.subject.fmri_dir, "stats", analysis_name)
        os.makedirs(stats_dir, exist_ok=True)

        ref_slice = num_slices // 2 + 1

        if rp_filename == "":
            rp_filename = os.path.join(self.subject.fmri_dir, "rp_" + self.subject.fmri_image_label + ".txt")

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        # substitute for all the volumes
        epi_nvols       = self.subject.fmri_data.get_nvoxels()
        epi_path        = Image(os.path.join(self.subject.fmri_dir, "swar" + self.subject.fmri_image_label))
        epi_all_volumes = ""
        for i in range(1, epi_nvols + 1):
            epi_volume = "'" + epi_path.spmpath + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n'  # + "'"

        sed_inplace(out_batch_job, '<SPM_DIR>', stats_dir)
        sed_inplace(out_batch_job, '<EVENTS_UNIT>', events_unit)
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<MICROTIME_RES>', str(num_slices))
        sed_inplace(out_batch_job, '<MICROTIME_ONSET>', str(ref_slice))
        sed_inplace(out_batch_job, '<SMOOTHED_VOLS>', epi_all_volumes)
        sed_inplace(out_batch_job, '<MOTION_PARAMS>', rp_filename)

        SPMStatsUtils.spm_replace_fmri_subj_stats_conditions_string(out_batch_job, conditions_lists)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])
        # eng = matlab.engine.start_matlab()
        # print("running SPM batch template: " + out_batch_start)  # , file=log)
        # eval("eng." + os.path.basename(os.path.splitext(out_batch_start)[0]) + "(nargout=0)")
        # eng.quit()


    # sessions x conditions_lists[{"name", "onsets", "duration"}, ....]
    def spm_fmri_1st_level_multisessions_custom_analysis(self, analysis_name, input_images, TR, num_slices, conditions_lists, events_unit="secs",
                                                  spm_template_name='subj_spm_fmri_stats_1st_level', rp_filenames=None):

        nsessions = len(input_images)

        # unzip whether necessary
        for img in input_images:
            Image(img).check_if_uncompress()

        # default params:
        stats_dir = os.path.join(self.subject.fmri_dir, "stats", analysis_name)
        os.makedirs(stats_dir, exist_ok=True)

        ref_slice = num_slices // 2 + 1

        # if rp_filename == "":
        #     rp_filename = os.path.join(self.subject.fmri_dir, "rp_" + self.subject.fmri_image_label + ".txt")

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "fmri", postfix=self.subject.label)

        sed_inplace(out_batch_job, '<SPM_DIR>', stats_dir)
        sed_inplace(out_batch_job, '<EVENTS_UNIT>', events_unit)
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<MICROTIME_RES>', str(num_slices))
        sed_inplace(out_batch_job, '<MICROTIME_ONSET>', str(ref_slice))

        for s in range(nsessions):

            image = Image(input_images[s])

            # substitute for all the volumes
            epi_nvols       = image.get_nvoxels()
            epi_all_volumes = ""
            for i in range(1, epi_nvols + 1):
                epi_volume = "'" + image.spmpath + ',' + str(i) + "'"
                epi_all_volumes = epi_all_volumes + epi_volume + '\n'  # + "'"

            sed_inplace(out_batch_job, '<VOLS'+ str(s+1) + '>', epi_all_volumes)
            sed_inplace(out_batch_job, '<MOTION_PARAMS'+ str(s+1) + '>', rp_filenames[s])

        sed_inplace(out_batch_job, '<COND11_ONSETS>', list2spm_text_column(conditions_lists[0][0][:]))
        sed_inplace(out_batch_job, '<COND12_ONSETS>', list2spm_text_column(conditions_lists[0][1][:]))

        sed_inplace(out_batch_job, '<COND21_ONSETS>', list2spm_text_column(conditions_lists[1][0][:]))
        sed_inplace(out_batch_job, '<COND22_ONSETS>', list2spm_text_column(conditions_lists[1][1][:]))

        sed_inplace(out_batch_job, '<COND31_ONSETS>', list2spm_text_column(conditions_lists[2][0][:]))
        sed_inplace(out_batch_job, '<COND32_ONSETS>', list2spm_text_column(conditions_lists[2][1][:]))

        sed_inplace(out_batch_job, '<COND41_ONSETS>', list2spm_text_column(conditions_lists[3][0][:]))

        sed_inplace(out_batch_job, '<COND51_ONSETS>', list2spm_text_column(conditions_lists[4][0][:]))

        # SPMStatsUtils.spm_replace_fmri_subj_stats_conditions_string(out_batch_job, conditions_lists)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])

    # ===============================================================================
    # FRAMEWORK (copy data across relevant folders, clean up)
    # ===============================================================================
    def cleanup(self, lvl=Global.CLEANUP_LVL_MIN):

        os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_preprocess_image_label))
        os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_aroma_image_label))
        os.removedirs(os.path.join(self.subject.rs_dir, "resting.feat"))
        os.removedirs(self.subject.rs_aroma_dir)

        if lvl == Global.CLEANUP_LVL_MED:
            # copy melodic report i
            os.makedirs(self.subject.rs_melic_dir)
            rrun("mv " + self.subject.rs_default_mel_dir + "/filtered_func_data_ica.ica/report" + " " + self.subject.rs_melic_dir)

            rrun("rm -rf " + self.subject.rs_default_mel_dir)
            os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_nuisance_melodic_image_label))

        elif lvl == Global.CLEANUP_LVL_HI:

            os.removedirs(self.subject.rs_melic_dir)

            rrun("rm -rf " + self.subject.rs_default_mel_dir)
            os.remove(os.path.join(self.subject.rs_dir, self.subject.rs_post_nuisance_melodic_image_label))

    # take a preproc step in the individual space (epi), convert to std4 and copy to resting/reg_std folder
    def adopt_rs_preproc_step(self, step_label, outsuffix=""):

        in_img = os.path.join(self.subject.rs_dir, step_label)
        self.subject.transform.transform_roi("epiTOstd4", "abs", rois=[in_img])  # add _std4 to roi name)
        in_img4 = Image(os.path.join(self.subject.roi_std4_dir, step_label + "_std4"))
        in_img4.mv(self.subject.rs_final_regstd_image + outsuffix)

    # take the reg_standard output of feat/melodic, convert to std4 and copy to resting/reg_std folder
    def adopt_rs_preproc_folderoutput(self, proc_folder):

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

    def reg_copy_feat(self, epi_label, std_image=""):

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

    # ===============================================================================
    # SBFC
    # ===============================================================================
    def sbfc_1multiroi_feat(self):
        pass

    def sbfc_several_1roi_feat(self):
        pass

    def coregister_epis(self, ref, target, trgpostfix="_ref", img2transform=None, ref_vol=3):

        trg_dir     = os.path.dirname(target)
        trg_name    = os.path.basename(target)
        omat        = os.path.join(trg_dir, "temp_trg2ref")
        owarp       = os.path.join(trg_dir, "temp_trg2ref_warp")
        otrg        = add_postfix2name(target, trgpostfix)
        otrg_lin    = add_postfix2name(target, trgpostfix + "_lin")

        single_ref_vol = add_postfix2name(ref,      "_sv")
        single_trg_vol = add_postfix2name(target,   "_sv")
        ref_mask       = add_postfix2name(ref,      "_sv_mask")

        if img2transform is None:
            cout = " "                          # don't want to use warp for further coreg, only interested in trg coreg
        else:
            cout = " --cout=" + owarp + " "     # want to use warp for further coregs

        self.get_nth_volume(ref,    single_ref_vol, ref_mask, volnum=ref_vol, logFile=None)     # it creates ref_mask
        self.get_nth_volume(target, single_trg_vol, out_mask_img=None, volnum=ref_vol, logFile=None)

        rrun("flirt  -in "  + single_trg_vol + "  -ref " + single_ref_vol + "  -omat " + omat + " -out " + otrg_lin)
        rrun("fnirt --in="  + single_trg_vol + " --ref=" + single_ref_vol + " --aff="  + omat + " --refmask=" + ref_mask + cout + " --iout=" + otrg)

        if img2transform is not None:
            for img in img2transform:
                ref_name = os.path.basename(ref)
                oimg     = add_postfix2name(img, trgpostfix)
                rrun("applywarp -i " + img + " -w " + owarp + " -r " + single_ref_vol + " -o " + oimg + " --interp=spline")

        return owarp

    def normalize(self, inimg=None, logFile=None):

        if inimg is None:
            inimg = Image(inimg, must_exist=True, msg="Error in epi.normalize of subj: " + self.subject.label )
        elif inimg == "rs":
            inimg = self.subject.rs_data
        elif inimg == "fmri":
            inimg = self.subject.fmri_data

        iname       = inimg.name
        params      = " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear"
        omat        = os.path.join(os.path.dirname(inimg), iname + "2hr.mat")
        epi_sv      = os.path.join(os.path.dirname(inimg), iname + "_sv")
        owarp       = os.path.join(os.path.dirname(inimg), iname + "2std_warp")
        norm_input  = os.path.join(os.path.dirname(inimg), iname +  "_norm")
        self.get_nth_volume(inimg, epi_sv, None, 0, logFile)
        flirt(omat, epi_sv, self.subject.t1_brain_data, params, logFile=logFile)

        if self.subject.transform.hr2std_warp.exist:
            rrun("convertwarp --ref=" + self.subject.std_img + " --premat=" + omat + " --warp1=" + self.subject.transform.hr2std_warp + " --out=" + owarp, logFile=logFile)
            rrun("applywarp -i " + inimg + " -r " + self.subject.std_img + " -o " + norm_input + " --warp=" + owarp, logFile=logFile)






    # ===============================================================================
