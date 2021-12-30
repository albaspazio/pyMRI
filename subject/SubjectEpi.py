import os
import sys
from shutil import copyfile, rmtree

from numpy import arange, concatenate, array

from Global import Global
from group.Stats import Stats
from myfsl.utils.run import rrun
from utility.images import imtest, imcp, is_image, remove_ext, imcp_notexisting, immv
from utility.matlab import call_matlab_spmbatch, call_matlab_function
from utility.utilities import sed_inplace, gunzip, compress, copytree, get_filename


class SubjectEpi:

    def __init__(self, subject, _global):
        self.subject = subject
        self._global = _global

    # ==================================================================================================================================================
    # GENERAL (pepolar corr, fsl_feat, aroma, remove_nuisance)
    # ==================================================================================================================================================

    def get_example_function(self, seq="rs", logFile=None):

        if seq == "rs":
            exfun = self.subject.rs_examplefunc
            data = self.subject.rs_data
            m_exfun = self.subject.rs_examplefunc_mask
        else:
            exfun = self.subject.fmri_examplefunc
            data = self.subject.fmri_data
            m_exfun = self.subject.fmri_examplefunc_mask

        if imtest(exfun) is False:
            rrun("fslmaths " + data + " " + data + "_prefiltered_func_data" + " -odt float", logFile=logFile)
            rrun("fslroi " + data + "_prefiltered_func_data" + " " + exfun + " 100 1", logFile=logFile)
            rrun("bet2 " + exfun + " " + exfun + " -f 0.3", logFile=logFile)

            rrun("imrm " + data + "prefiltered_func_data*", logFile=logFile)

            rrun("fslmaths " + exfun + " -bin " + m_exfun, logFile=logFile)  # create example_function mask (a -thr 0.01/0.1 could have been used to further reduce it)

        return exfun

    # assumes opposite PE direction sequence is called label-epi_PA and acquisition parameters
    # - epi_ref_vol/pe_ref_vol =-1 means use the middle volume
    # 1: get number of volumes of epi_PA image in opposite phase-encoding direction and extract middle volume (add "_ref")
    # 2: look for the epi volume closest to epi_pa_ref volume
    # 3: merge the 2 ref volumes into one (add "_ref")
    # 4: run topup using ref, acq params; used_templates: "_topup"
    # 5: (optionally) do motion correction with the chosen volume
    # 6: applytopup --> choose images whose distortion we want to correct
    def topup_correction(self, in_ap_img, in_pa_img, acq_params, ap_ref_vol=-1, pa_ref_vol=-1, config="b02b0.cnf", motion_corr=False, logFile=None):

        #  /a/b/c/name.ext
        input_dir   = os.path.dirname(in_ap_img)    # /a/b/c
        in_ap_img   = remove_ext(in_ap_img)         # /a/b/c/name
        in_ap_label = os.path.basename(in_ap_img)   # name

        if imtest(in_ap_img + "_distorted") is False:
            imcp(in_ap_img, in_ap_img + "_distorted")  # this will refer to a file with all the sessions merged <--------!!

        ap_ref          = os.path.join(input_dir, "ap_ref")
        pa_ref          = os.path.join(input_dir, "pa_ref")
        ap_pa_ref       = os.path.join(input_dir, "ap_pa_ref")
        ap_pa_ref_topup = os.path.join(input_dir, "ap_pa_ref_topup")

        # 1
        if pa_ref_vol == -1:
            nvols_pe = rrun("fslnvols " + in_pa_img + '.nii.gz')
            central_vol_pa = int(nvols_pe) // 2
        else:
            central_vol_pa = pa_ref_vol

        rrun("fslselectvols -i " + in_pa_img + " -o " + pa_ref + " --vols=" + str(central_vol_pa), logFile=logFile)

        # 2
        if ap_ref_vol == -1:
            central_vol = self.get_closest_volume(in_ap_img, in_pa_img, pa_ref_vol) - 1 # returns a 1-based volume, so I subtract 1
        else:
            central_vol = ap_ref_vol

        rrun("fslselectvols -i " + in_ap_img + " -o " + ap_ref + " --vols=" + str(central_vol), logFile=logFile)

        # 3
        rrun("fslmerge -t " + ap_pa_ref + " " + ap_ref + " " + pa_ref)

        # 4 —assumes merged epi volumes appear in the same order as acqparams.txt (--datain)
        rrun("topup --imain=" + ap_pa_ref + " --datain=" + acq_params + " --config=" + config + " --out=" + ap_pa_ref_topup, logFile=logFile) # + " --iout=" + self.subject.fmri_data + "_PE_ref_topup_corrected")

        img2correct = in_ap_img
        # 5 -motion correction using central_vol
        if motion_corr is True:
            r_in_ap_img = os.path.join(input_dir, "r" + in_ap_label)
            self.spm_motioncorrection(in_ap_img, ref_vol=central_vol)
            os.remove(in_ap_img + ".nii")  # remove old with-motion SUBJ-fmri.nii
            os.remove(in_ap_img + ".nii.gz")  # remove old with-motion SUBJ-fmri.nii.gz
            compress(r_in_ap_img + ".nii", r_in_ap_img + ".nii.gz", replace=True)  # zip rSUBJ-fmri.nii => rSUBJ-fmri.nii.gz
            img2correct = r_in_ap_img

        # 6 —again these must be in the same order as --datain/acqparams.txt // "inindex=" values reference the images-to-correct corresponding row in --datain and --topup
        rrun("applytopup --imain=" + in_ap_img + " --topup=" + ap_pa_ref_topup + " --datain=" + acq_params + " --inindex=1 --method=jac --interp=spline --out=" + in_ap_img, logFile=logFile)

        os.system("rm " + input_dir + "/" + "ap_*")
        os.system("rm " + input_dir + "/" + "pa_*")

    # model can be:  a fullpath, a filename (string) located in project's glm_template_dir
    def fsl_feat(self, epi_label, in_file_name, out_dir_name, model, do_initreg=False, std_image="", tr="", te=""):

        if epi_label == "rs":
            epi_dir = self.subject.rs_dir
        elif epi_label.startswith("fmri"):
            epi_dir = self.subject.fmri_dir

        out_dir = os.path.join(epi_dir, out_dir_name)
        epi_image = os.path.join(epi_dir, in_file_name)

        # default params:
        if imtest(epi_image) is False:
            print("Error in subj: " + self.subject.label + " epi_feat")
            return

        if std_image == "":
            std_image = os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm_brain")

        if os.path.isfile(model + ".fsf") is False:

            model = os.path.join(self.subject.project.glm_template_dir, model + ".fsf")
            if os.path.isfile(model + ".fsf") is False:
                print("Error in subj: " + self.subject.label + " epi_feat :  model " + model + ".fsf is missing")
                return

        modellabel = get_filename(model)

        # -----------------------------------------------------
        print(self.subject.label + ": FEAT with model: " + model)
        TOT_VOL_NUM = int(rrun("fslnvols " + epi_image))

        os.makedirs(os.path.join(epi_dir, "model"), exist_ok=True)

        OUTPUT_FEAT_FSF = os.path.join(epi_dir, "model", modellabel)
        copyfile(model + ".fsf", OUTPUT_FEAT_FSF + ".fsf")

        # FEAT fsf -------------------------------------------------------------------------------------------------------------------------
        with open(OUTPUT_FEAT_FSF + ".fsf", "a") as text_file:
            original_stdout = sys.stdout
            sys.stdout = text_file  # Change the standard output to the file we created.

            print("", file=text_file)
            print("################################################################", file=text_file)
            print("# overriding parameters", file=text_file)
            print("################################################################", file=text_file)

            print("set fmri(npts) " + str(TOT_VOL_NUM), file=text_file)
            print("set feat_files(1) " + epi_image, file=text_file)
            print("set highres_files(1) " + self.subject.t1_brain_data, file=text_file)

            if is_image(self.subject.wb_brain_data) and do_initreg is True:
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
    def aroma_feat(self, epi_label, input_dir, mc="", aff="", warp="", ofn="ica_aroma", upsampling=0, logFile=None):

        if epi_label == "rs":
            aroma_dir           = self.subject.rs_aroma_dir
            regstd_aroma_dir    = self.subject.rs_regstd_aroma_dir

        elif epi_label.startswith("fmri"):
            aroma_dir           = self.subject.fmri_aroma_dir
            regstd_aroma_dir    = self.subject.fmri_regstd_aroma_dir
        else:
            print("ERROR in epi.aroma epi_label was not recognized")
            return

        option_string = ""
        if mc != "":
            option_string = " -mc " + mc + " "

        input_reg = os.path.join(input_dir, "reg")
        os.makedirs(input_reg, exist_ok=True)
        imcp(warp, os.path.join(input_reg, "highres2standard_warp"), logFile=logFile)
        copyfile(aff, os.path.join(input_reg, "example_func2highres.mat"))

        # CHECK FILE EXISTENCE #.feat
        if os.path.isdir(input_dir) is False:
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
            rs_icafix_dir       = self.subject.rs_icafix_dir
            regstd_aroma_dir    = self.subject.rs_regstd_aroma_dir

        elif epi_label.startswith("fmri"):
            rs_icafix_dir       = self.subject.fmri_icafix_dir
            regstd_aroma_dir    = self.subject.fmri_regstd_aroma_dir
        else:
            print("ERROR in epi.ica_fix epi_label was not recognized")
            return



    def remove_nuisance(self, in_img_name, out_img_name, epi_label="rs", ospn="", hpfsec=100):

        if epi_label == "rs":
            in_img = os.path.join(self.subject.rs_dir, in_img_name)
            out_img = os.path.join(self.subject.rs_dir, out_img_name)
            series_wm = self.subject.rs_series_wm + ospn + ".txt"
            series_csf = self.subject.rs_series_csf + ospn + ".txt"
            output_series = os.path.join(self.subject.rs_series_dir, "nuisance_timeseries" + ospn + ".txt")

        if imtest(in_img) is False:
            print(
                'ERROR in epi_resting_nuisance of subject ' + self.subject.label + ". input image (" + in_img + ") is missing")
            return

        tr = float(rrun('fslval ' + in_img + ' pixdim4'))
        hpf_sigma = hpfsec / (2 * tr)
        print("execute_subject_resting_nuisance of " + self.subject.label)

        os.makedirs(self.subject.sbfc_dir, exist_ok=True)
        os.makedirs(self.subject.rs_series_dir, exist_ok=True)

        print(self.subject.label + ": coregister fast-highres to epi")

        if imtest(self.subject.rs_mask_t1_wmseg4nuis) is False:
            # regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, std_img="", rois=[]):
            self.subject.transform.transform_roi("hrTOrs", "abs", rois=[self.subject.t1_segment_wm_ero_path])

        if imtest(self.subject.rs_mask_t1_csfseg4nuis) is False:
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

    def get_slicetiming_params(self, nslices, scheme=1, params=None):

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
    def spm_motioncorrection(self, epi2correct, ref_image=None, ref_vol=1,
                             spm_template_name="spm_fmri_realign_estimate_reslice_to_given_vol"):

        # check if input image is valid, upzip whether zipped
        if imtest(epi2correct) is False:
            print("Error in epi.spm_motioncorrection, given epi2correct (" + epi2correct + ") is not valid....exiting")
            return
        if os.path.isfile(epi2correct + ".nii.gz") and not os.path.isfile(epi2correct + ".nii"):
            gunzip(epi2correct + ".nii.gz", epi2correct + ".nii")

        # check if ref image is valid (if not specified, use in_img), upzip whether zipped
        if ref_image is None:
            ref_image = epi2correct
        else:
            if imtest(ref_image) is False:
                print("Error in epi.spm_motioncorrection, given ref_img (" + ref_image + ") is not valid....exiting")
                return

        if os.path.isfile(ref_image + ".nii.gz") and not os.path.isfile(ref_image + ".nii"):
            gunzip(ref_image + ".nii.gz", ref_image + ".nii")


        # 2.1: select the input spm template obtained from batch (we defined it in spm_template_name) + its run file …
        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "fmri", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
        in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + '_job.m')

        # 2.1' … and establish location of output spm template + output run file:
        out_batch_job = os.path.join(out_batch_dir, spm_template_name + self.subject.label + '_job.m')
        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + self.subject.label + '.m')

        os.makedirs(out_batch_dir, exist_ok=True)

        # 2.2: create "output spm template" by copying "input spm template" + changing general tags for our specific ones…
        ref_vol = max(ref_vol, 1)
        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, '<REF_IMAGE,refvol>', ref_image + '.nii,' + str(ref_vol))  # <-- i added 1 to ref_volume_pe bc spm counts the volumes from 1, not from 0 as FSL

        # 2.2' …now we want to select all the volumes from the epi file and insert that into the template:
        epi_nvols       = int(rrun('fslnvols ' + epi2correct + '.nii'))
        epi_path_name   = epi2correct + '.nii'
        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume      = "'" + epi_path_name + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n'

        sed_inplace(out_batch_job, '<TO_ALIGN_IMAGES,1-n_vols>', epi_all_volumes)

        # 2.3: run job --> create "output run spm template" by analogue process + call matlab and run it:
        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, 'X', '1')
        sed_inplace(out_batch_start, 'JOB_LIST', "\'" + out_batch_job + "\'")
        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir], endengine=False)

    def get_closest_volume(self, in_image, ref_image, ref_volume=-1):
        # will calculate the closest vol from given epi image to ref_image
        # Steps:
        # 0: get epi_pe central volume + unzip so SPM can use it
        # 1: merge all the sessions into one file ("_merged-sessions") + unzip so SPM can use it
        # 2: align all the volumes within merged file to epi_pe central volume (SPM12-Realign:Estimate)
        # 3: calculate the "less motion corrected" volume from the merged file with respect to the epi-pe in terms of rotation around x, y and z axis).

        # check if input image is valid
        if imtest(in_image) is False:
            print("Error in get_closest_volumen, given in_image (" + in_image + ") is not valid....exiting")
            return

        # check if ref image is valid
        if imtest(ref_image) is False:
            print("Error in epi.get_closest_volumen, given ref_image (" + ref_image + ") is not valid....exiting")
            return

        #  /a/b/c/name.ext
        input_dir   = os.path.dirname(in_image)    # /a/b/c
        in_image    = remove_ext(in_image)         # /a/b/c/name
        in_label    = os.path.basename(in_image)   # name

        # create temp folder, copy there epi and epi_pe, unzip and run mc (then I can simply remove it when ended)
        temp_distorsion_mc  = os.path.join(input_dir, "temp_distorsion_mc")
        os.makedirs(temp_distorsion_mc, exist_ok=True)
        temp_epi            = os.path.join(temp_distorsion_mc, in_label)
        temp_epi_ref        = os.path.join(temp_distorsion_mc, in_label + "_ref")

        if not os.path.isfile(temp_epi + ".nii"):
            gunzip(in_image + ".nii.gz", temp_epi + ".nii")

        if not os.path.isfile(temp_epi_ref + ".nii"):
            gunzip(ref_image + ".nii.gz", temp_epi_ref + ".nii")

        if ref_volume == -1:
            # 0
            epi_pe_nvols    = int(rrun('fslnvols ' + ref_image + '.nii.gz'))
            ref_volume      = epi_pe_nvols // 2     # 0-based. in spm_motioncorrection get 1-based

        self.spm_motioncorrection(temp_epi, temp_epi_ref, ref_volume, spm_template_name="spm_fmri_realign_estimate_to_given_vol")

        # 3: call matlab function that calculates best volume (1-based):
        best_vol = call_matlab_function("least_mov", [self._global.spm_functions_dir], "\"" + os.path.join(temp_distorsion_mc, "rp_" + in_label + "_ref" + '.txt' + "\""))[1]
        rmtree(temp_distorsion_mc)

        return int(best_vol)

    def prepare_for_spm(self, in_img, subdirmame="temp_split"):

        folder = os.path.dirname(in_img)

        self.subject.epi_split(in_img, subdirmame)
        outdir = os.path.join(folder, subdirmame)
        os.chdir(outdir)
        for f in os.scandir():
            if f.is_file():
                gunzip(f.name, os.path.join(outdir, remove_ext(f.name) + ".nii"), replace=True)

    def spm_fmri_preprocessing_motioncorrected(self, num_slices, TR, TA=-1, acq_scheme=0, ref_slice=-1,
                                               slice_timing=None):
        self.subject.epi_spm_fmri_preprocessing(num_slices, TR, TA, acq_scheme, ref_slice, slice_timing,
                                                epi_image=self.subject.fmri_data_mc,
                                                spm_template_name='spm_fmri_preprocessing_norealign')

    def spm_fmri_preprocessing(self, num_slices, TR, TA=-1, acq_scheme=0, ref_slice=-1, slice_timing=None,
                               epi_image=None, spm_template_name='spm_fmri_preprocessing'):

        # default params:
        if epi_image is None:
            epi_image = self.subject.fmri_data
        else:
            if imtest(epi_image) is False:
                print("Error in subj: " + self.subject.label + " epi_spm_fmri_preprocessing")
                return

        # TA - if not otherwise indicated, it assumes the acquisition is continuous and TA = TR - (TR/num slices)
        if TA == -1:
            TA = TR - (TR / num_slices)

        # takes central slice as a reference
        if ref_slice == -1:
            ref_slice = num_slices // 2 + 1

        #
        if slice_timing is None:
            slice_timing = self.subject.epi_get_slicetiming_params(num_slices, acq_scheme)
        else:
            slice_timing = [str(p) for p in slice_timing]

        # set dirs
        in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + '_job.m')
        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        spm_script_dir = os.path.join(self.subject.project.script_dir, "fmri", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        out_batch_job = os.path.join(out_batch_dir, spm_template_name + self.subject.label + '_job.m')
        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + self.subject.label + '.m')

        # substitute for all the volumes + rest of params
        epi_nvols = int(rrun('fslnvols ' + epi_image + '.nii.gz'))
        epi_path_name = epi_image + '.nii'

        gunzip(epi_image + '.nii.gz', epi_path_name, replace=False)

        epi_all_volumes = ''
        for i in range(1, epi_nvols + 1):
            epi_volume = epi_path_name + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n' + "'"

        mean_image = os.path.join(self.subject.fmri_dir, "mean" + self.subject.fmri_image_label + ".nii")

        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, '<FMRI_IMAGES>', epi_all_volumes)
        sed_inplace(out_batch_job, '<NUM_SLICES>', str(num_slices))
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<TA_VALUE>', str(TA))
        sed_inplace(out_batch_job, '<SLICETIMING_PARAMS>', ' '.join(slice_timing))
        sed_inplace(out_batch_job, '<REF_SLICE>', str(ref_slice))
        sed_inplace(out_batch_job, '<RESLICE_MEANIMAGE>', mean_image)
        sed_inplace(out_batch_job, '<T1_IMAGE>', self.subject.t1_data + '.nii,1')
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
    def spm_fmri_1st_level_analysis(self, analysis_name, TR, num_slices, conditions_lists, events_unit="secs",
                                    spm_template_name='spm_fmri_stats_1st_level', rp_filemame=""):

        # default params:
        stats_dir = os.path.join(self.subject.fmri_dir, "stats", analysis_name)
        os.makedirs(stats_dir, exist_ok=True)

        ref_slice = num_slices // 2 + 1

        if rp_filemame == "":
            rp_filemame = os.path.join(self.subject.fmri_dir, "rp_" + self.subject.fmri_image_label + ".txt")

        # set dirs
        in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + '_job.m')
        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        spm_script_dir = os.path.join(self.subject.project.script_dir, "fmri", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        out_batch_job = os.path.join(out_batch_dir, spm_template_name + self.subject.label + '_job.m')
        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + self.subject.label + '.m')

        # substitute for all the volumes
        epi_nvols = int(rrun('fslnvols ' + self.subject.fmri_data + '.nii.gz'))
        epi_path_name = os.path.join(self.subject.fmri_dir, "swar" + self.subject.fmri_image_label + '.nii')
        epi_all_volumes = ""
        for i in range(1, epi_nvols + 1):
            epi_volume = "'" + epi_path_name + ',' + str(i) + "'"
            epi_all_volumes = epi_all_volumes + epi_volume + '\n'  # + "'"

        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, '<SPM_DIR>', stats_dir)
        sed_inplace(out_batch_job, '<EVENTS_UNIT>', events_unit)
        sed_inplace(out_batch_job, '<TR_VALUE>', str(TR))
        sed_inplace(out_batch_job, '<MICROTIME_RES>', str(num_slices))
        sed_inplace(out_batch_job, '<MICROTIME_ONSET>', str(ref_slice))
        sed_inplace(out_batch_job, '<SMOOTHED_VOLS>', epi_all_volumes)
        sed_inplace(out_batch_job, '<MOTION_PARAMS>', rp_filemame)

        Stats.spm_fmri_subj_stats_replace_conditions_string(out_batch_job, conditions_lists)

        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, 'X', '1')
        sed_inplace(out_batch_start, 'JOB_LIST', "\'" + out_batch_job + "\'")

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir])
        # eng = matlab.engine.start_matlab()
        # print("running SPM batch template: " + out_batch_start)  # , file=log)
        # eval("eng." + os.path.basename(os.path.splitext(out_batch_start)[0]) + "(nargout=0)")
        # eng.quit()

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
            rrun(
                "mv " + self.subject.rs_default_mel_dir + "/filtered_func_data_ica.ica/report" + " " + self.subject.rs_melic_dir)

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
        in_img4 = os.path.join(self.subject.roi_std4_dir, step_label + "_std4")
        immv(in_img4, self.subject.rs_final_regstd_image + outsuffix)

    # take the reg_standard output of feat/melodic, convert to std4 and copy to resting/reg_std folder
    def adopt_rs_preproc_folderoutput(self, proc_folder):

        in_img = os.path.join(proc_folder, "reg_standard", "filtered_func_data")
        in_mask = os.path.join(proc_folder, "reg_standard", "mask")
        in_bgimage = os.path.join(proc_folder, "reg_standard", "bg_image")

        self.subject.transform.transform_roi("stdTOstd4", "abs", rois=[in_img, in_mask, in_bgimage])

        in_img4 = os.path.join(self.subject.roi_std4_dir, "filtered_func_data_std4")
        in_mask4 = os.path.join(self.subject.roi_std4_dir, "mask_std4")
        in_bgimage4 = os.path.join(self.subject.roi_std4_dir, "bg_image_std4")

        immv(in_img4, self.subject.rs_final_regstd_image)
        imcp(in_mask4, self.subject.rs_final_regstd_mask)
        imcp(in_bgimage4, self.subject.rs_final_regstd_bgimage)

    def reg_copy_feat(self, epi_label, std_image=""):

        if epi_label == "rs":
            epi_image = self.subject.rs_data
            epi_dir = self.subject.rs_dir
            out_dir = os.path.join(epi_dir, "resting.feat")
            exfun = self.subject.rs_examplefunc
            reg_dir = self.subject.roi_rs_dir

            std2epi_warp = self.subject.std2rs_warp
            epi2std_warp = self.subject.rs2std_warp

            std2epi_mat = self.subject.std2rs_mat
            epi2std_mat = self.subject.rs2std_mat

            epi2hr_mat = self.subject.rs2hr_mat
            hr2epi_mat = self.subject.hr2rs_mat

        elif epi_label.startswith("fmri"):
            epi_image = os.path.join(self.subject.fmri_dir, self.subject.label + "-" + epi_label)
            epi_dir = self.subject.fmri_dir
            out_dir = os.path.join(epi_dir, epi_label + ".feat")
            exfun = self.subject.fmri_examplefunc
            reg_dir = self.subject.roi_fmri_dir

            std2epi_warp = self.subject.std2fmri_warp
            epi2std_warp = self.subject.fmri2std_warp

            std2epi_mat = self.subject.std2fmri_mat
            epi2std_mat = self.subject.fmri2std_mat

            epi2hr_mat = self.subject.fmri2hr_mat
            hr2epi_mat = self.subject.hr2fmri_mat

        if std_image == "":
            std_image = os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm_brain")
        else:
            if imtest(std_image) is False:
                print("epi_reg_copy_feat of subject " + self.subject.label + " given std_img is not present")
                return

        imcp(os.path.join(out_dir, "reg", "example_func"), exfun)

        copyfile(os.path.join(out_dir, "reg", "example_func2highres.mat"), epi2hr_mat)
        copyfile(os.path.join(out_dir, "reg", "highres2example_func.mat"), hr2epi_mat)

        copyfile(os.path.join(out_dir, "reg", "standard2highres.mat"), self.subject.std2hr_mat)
        copyfile(os.path.join(out_dir, "reg", "highres2standard.mat"), self.subject.hr2std_mat)

        copyfile(os.path.join(out_dir, "reg", "standard2example_func.mat"), std2epi_mat)
        copyfile(os.path.join(out_dir, "reg", "example_func2standard.mat"), epi2std_mat)

        # copy/create warps
        imcp_notexisting(os.path.join(out_dir, "reg", "highres2standard_warp"), self.subject.hr2std_warp)

        if imtest(self.subject.std2hr_warp) is False:
            rrun(os.path.join(self._global.fsl_bin,
                              "invwarp") + " -w " + self.subject.hr2std_warp + " -o " + self.subject.std2hr_warp + " -r " + self.subject.t1_brain_data)

        # epi -> highres -> standard
        if imtest(epi2std_warp) is False:
            rrun(os.path.join(self._global.fsl_bin,
                              "convertwarp") + " --ref=" + std_image + " --premat=" + epi2hr_mat + " --warp1=" + self.subject.hr2std_warp + " --out=" + epi2std_warp)

        # invwarp: standard -> highres -> epi
        if imtest(std2epi_warp) is False:
            rrun(os.path.join(self._global.fsl_bin,
                              "invwarp") + " -w " + epi2std_warp + " -o " + std2epi_warp + " -r " + exfun)

    # ===============================================================================
    # SBFC
    # ===============================================================================
    def sbfc_1multiroi_feat(self):
        pass

    def sbfc_several_1roi_feat(self):
        pass
    # ===============================================================================
