import os

from myfsl.utils.run import rrun
from utility.fslfun import runsystem
from utility.images import imtest, imgname, remove_ext, read_header


class SubjectTransforms:
    
    def __init__(self, subject, _global):
        
        self.subject = subject
        self._global = _global
        
    def fnirt(self, ref, ofn="", odp="", refmask="", inimg="t1_brain"):

        if inimg == "t1_brain":
            img = self.subject.t1_brain_data
        elif inimg == "t1":
            img = self.subject.t1_data
        elif inimg == "t2_brain":
            img = self.subject.t2_brain_data
        elif inimg == "t2":
            img = self.subject.t2_brain
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
            REF_STRING = " --refmask=" + refmask

        rrun("flirt -in " + img + " -ref " + ref + " -omat " + os.path.join(odp, ofn + ".mat") + " -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")
        rrun("fnirt --iout= " + os.path.join(odp, ofn) + " --in=" + inimg + " --aff=" + os.path.join(odp, ofn + ".mat") + " --ref=" + ref + REF_STRING)

    # ==================================================================================================================================================
    # MAIN SEQUENCES TRANSFORMS
    # ==================================================================================================================================================

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate all the transforms involved in MPR processing.
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # you can work with the default MNI template or a custom one.
    # In the latter case, user must provide (in a same folder) the following images:
    #  -> stdimg, stdimg_brain, stdimg_brain_mask_dil
    #  -> stdimg4, stdimg4_brain, stdimg4_brain_mask_dil
    def transform_mpr(self, stdimg="", logFile=None):

        if stdimg == "":

            std_img_label       = "std"

            std_img             = self.subject._global.fsl_std_mni_2mm_brain
            std_head_img        = self.subject._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self.subject._global.fsl_std_mni_2mm_brain_mask_dil

            std4_img            = self.subject._global.fsl_std_mni_4mm_brain
            std4_head_img       = self.subject._global.fsl_std_mni_4mm_head
            std4_img_mask_dil   = self.subject._global.fsl_std_mni_4mm_brain_mask_dil
        else:
            imgdir              = os.path.dirname(stdimg)
            std_img_label       = remove_ext(os.path.basename(stdimg))                      # "pediatric"

            std_head_img        = os.path.join(imgdir, std_img_label)                       # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")            # "pediatric_brain"
            std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")   # "pediatric_brain_mask_dil"

            std4_head_img        = os.path.join(imgdir, std_img_label + "4")                # "pediatric4"
            std4_img             = os.path.join(imgdir, std_img_label + "4_brain")          # "pediatric4_brain"
            std4_img_mask_dil    = os.path.join(imgdir, std_img_label + "4_brain_mask_dil") # "pediatric4_brain_mask_dil"

        hr2std          = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label)
        hrhead2std      = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hrhead2" + std_img_label)
        std2hr          = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr")
        hr2std_warp     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
        std2hr_warp     = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr_warp")

        hr2std4         = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2" + std_img_label + "4")
        hrhead2std4     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hrhead2" + std_img_label + "4")
        std42hr         = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr")
        hr2std4_warp    = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2" + std_img_label + "4_warp")
        std42hr_warp    = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr_warp")

        process_std4 = True

        if imtest(self.subject.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.t1_data) is False:
            print("file T1_DATA: " + self.subject.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        # check template
        if imtest(std_img) is False:
            print("ERROR: file std_img: " + std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_head_img) is False:
            print("ERROR: file std4_img: " + std4_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_img_mask_dil) is False:
            print("ERROR: file STD_IMAGE_MASK: " + std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std4_img) is False:
            print("WARNING: file std_img: " + std_img + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        if imtest(std4_head_img) is False:
            print("WARNING: file std4_img: " + std4_img + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        if imtest(std4_img_mask_dil) is False:
            print("WARNING: file STD_IMAGE_MASK: " + std_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        print(self.subject.label + " :STARTED transform_mpr")

        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label), exist_ok=True)
        os.makedirs(self.subject.roi_t1_dir, exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # HIGHRES <--------> STANDARD (there could be different standard (e.g. group template) so I don't use default Subject properties
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => hr2{std}.mat
        if os.path.isfile(hr2std + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + std_img + " -out " + hr2std + " -omat " + hr2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2{std}.mat
        if os.path.isfile(hrhead2std + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + std_head_img + " -out " + hrhead2std + " -omat " + hrhead2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => {std}2hr.mat
        if os.path.isfile(std2hr + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + std2hr + ".mat " + hr2std + ".mat")

        # NON LINEAR
        # => hr2{std}_warp
        if imtest(hr2std_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std + ".mat --config=" + self.subject._global.self.fsl_std_mni_2mm_cnf +
                    " --ref=" + std_head_img + " --refmask=" + std_img_mask_dil + " --warpres=10,10,10" +
                    "--cout=" + hr2std_warp + " --iout=" + hr2std + " --jout=" + hr2std + "_jac")

        # => {std}2hr_warp
        if imtest(std2hr_warp) is False:
            rrun("invwarp -r " + self.subject.t1_data + " -w " + hr2std_warp + " -o " + std2hr_warp)

        ## => hr2{std}.nii.gz
        if imtest(hr2std) is False:
            rrun("applywarp -i " + self.subject.t1_data + " -r " + std_img + " -o " + hr2std + " -w " + hr2std_warp)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # HIGHRES <--------> STANDARD4
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if process_std4 is False:
            return

        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4"), exist_ok=True)
        # => hr2{std}4.mat
        if os.path.isfile(hr2std4 + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + std4_img + " -out " + hr2std4 + " -omat " + hr2std4 + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2{std}4.mat
        if os.path.isfile(hrhead2std4 + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + std4_head_img + " -out " + hrhead2std4 + " -omat " + hrhead2std4 + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => {std}42hr.mat
        if os.path.isfile(std42hr + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + std42hr + ".mat " + hr2std4 + ".mat")

        # NON LINEAR
        # => hr2{std}4_warp
        if imtest(hr2std4_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std4 + ".mat  --config=" + self._global.fsl_std_mni_4mm_cnf +
                 " --ref=" + std4_head_img + " --refmask=" + std4_img_mask_dil + " --warpres=10,10,10" +
                 " --cout=" + hr2std4_warp + " --iout=" + hr2std4 + " --jout=" + hr2std4 + "_jac" )

        # => {std}42hr_warp
        if imtest(std42hr_warp) is False:
            rrun("invwarp -r " + self.subject.t1_data + " -w " + hr2std4_warp + " -o " + std42hr_warp)

        ## => hr2{std}4.nii.gz
        if imtest(hr2std4) is False:
            rrun("applywarp -i " + self.subject.t1_data + " -r " + std4_img + " -o " + hr2std4 + " -w " + hr2std4_warp)


    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate all the transforms involved in EPI processing.
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # (17/7/21) bbr co-registration fails!!!
    # you can work with the default MNI template or a custom one.
    # In the latter case, user must provide (in a same folder) the following images:
    #  -> stdimg, stdimg_brain, stdimg_brain_mask_dil
    #  -> stdimg4, stdimg4_brain, stdimg4_brain_mask_dil
    def transform_epi(self, type='fmri', stdimg="", do_bbr=False, wmseg="", logFile=None):

        if stdimg == "":

            std_img_label       = "std"

            std_img             = self.subject._global.fsl_std_mni_2mm_brain
            std_head_img        = self.subject._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self.subject._global.fsl_std_mni_2mm_brain_mask_dil

            std4_img            = self.subject._global.fsl_std_mni_4mm_brain
            std4_head_img       = self.subject._global.fsl_std_mni_4mm_head
            std4_img_mask_dil   = self.subject._global.fsl_std_mni_4mm_brain_mask_dil
        else:
            imgdir              = os.path.dirname(stdimg)
            std_img_label       = remove_ext(os.path.basename(stdimg))                      # "pediatric"

            std_head_img        = os.path.join(imgdir, std_img_label)                       # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")            # "pediatric_brain"
            std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")   # "pediatric_brain_mask_dil"

            std4_head_img        = os.path.join(imgdir, std_img_label + "4")                # "pediatric4"
            std4_img             = os.path.join(imgdir, std_img_label + "4_brain")          # "pediatric4_brain"
            std4_img_mask_dil    = os.path.join(imgdir, std_img_label + "4_brain_mask_dil") # "pediatric4_brain_mask_dil"

        if type == 'fmri':
            data        = self.subject.fmri_data
            folder      = self.subject.fmri_dir
            exfun       = self.subject.fmri_examplefunc
            m_exfun     = self.subject.fmri_examplefunc_mask
            epi2hr      = os.path.join(self.subject.roi_t1_dir, "fmri2hr")
            hr2epi_mat  = self.subject.hr2fmri_mat
            epi2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "fmri2" + std_img_label)
            std2epi     = os.path.join(self.subject.roi_fmri_dir, std_img_label + "2fmri")
            epi2std4    = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "fmri2" + std_img_label + "4")
            std42epi    = os.path.join(self.subject.roi_fmri_dir, std_img_label + "42fmri")

        else:
            data        = os.path.join(self.subject.rs_dir, self.subject.rs_post_preprocess_image_label)
            folder      = self.subject.rs_dir
            exfun       = self.subject.rs_examplefunc
            m_exfun     = self.subject.rs_examplefunc_mask
            epi2hr      = os.path.join(self.subject.roi_t1_dir, "rs2hr")
            hr2epi_mat  = self.subject.hr2rs_mat
            epi2std     = os.path.join(self.subject.roi_dir     , "reg_" + std_img_label, "rs2" + std_img_label)
            std2epi     = os.path.join(self.subject.roi_rs_dir  , std_img_label + "2rs")
            epi2std4    = os.path.join(self.subject.roi_dir     , "reg_" + std_img_label + "4", "rs2" + std_img_label + "4")
            std42epi    = os.path.join(self.subject.roi_rs_dir  , std_img_label + "42rs")

        hr2std          = os.path.join(self.subject.roi_dir, "reg_" + std_img_label         , "hr2" + std_img_label)
        hr2std_warp     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label         , "hr2" + std_img_label + "_warp")
        hr2std4_warp    = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4"   , "hr2" + std_img_label + "4_warp")

        if wmseg == "":
            wmseg = self.subject.t1_segment_wm_bbr_path
        else:
            if imtest(wmseg) is False and do_bbr is True:
                print("ERROR: asked to run bbr, but the given wmseg file " + wmseg + ".nii.gz is not present...exiting transforms_mpr")
                return
        process_std4 = True

        if imtest(self.subject.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.t1_data) is False:
            print("file T1_DATA: " + self.subject.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        # check template
        if imtest(std_img) is False:
            print("ERROR: file std_img: " + std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_head_img) is False:
            print("ERROR: file std_img: " + std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_img_mask_dil) is False:
            print("ERROR: file std_img_mask_dil: " + std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std4_img) is False:
            print("WARNING: file std4_img: " + std4_img + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        if imtest(std4_head_img) is False:
            print("WARNING: file std4_head_img: " + std4_head_img + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        if imtest(std4_img_mask_dil) is False:
            print("WARNING: file std4_img_mask_dil: " + std4_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        os.makedirs(folder, exist_ok=True)
        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label), exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # create example function
        if imtest(exfun) is False:
            rrun("fslmaths " + data + " " + os.path.join(folder, "prefiltered_func_data") + " -odt float", logFile=logFile)
            rrun("fslroi " + os.path.join(folder, "prefiltered_func_data") + " " + exfun + " 100 1", logFile=logFile)
            rrun("bet2 " + exfun + " " + exfun + " -f 0.3", logFile=logFile)

            rrun("imrm " + os.path.join(folder, "prefiltered_func_data*"), logFile=logFile)

            rrun("fslmaths " + exfun + " -bin " + m_exfun, logFile=logFile)      # create example_function mask (a -thr 0.01/0.1 could have been used to further reduce it)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  EPI <--> HIGHRES (linear, bbr or not)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            rrun("flirt -ref " + self.subject.t1_brain_data + " -in " + exfun + " -dof 6 -omat " + epi2hr + "_init.mat", logFile=logFile)

            if imtest(wmseg) is False:
                print("Running FAST segmentation for subj " + self.subject.label)
                temp_dir = os.path.join(self.subject.roi_t1_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.subject.t1_brain_data), logFile=logFile)
                rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + wmseg, logFile=logFile)
                runsystem("rm -rf " + temp_dir, logFile=logFile)

            # => epi2hr.mat
            if os.path.isfile(epi2hr + ".mat") is False:
                rrun("flirt -ref " + self.subject.t1_data + " -in " + exfun + " -dof 6 -cost bbr -wmseg " + wmseg + " -init " + epi2hr + "_init.mat" + " -omat " + epi2hr + ".mat" + " -out " + epi2hr + " -schedule " + os.path.join(self.subject.fsl_dir, "etc", "flirtsch", "bbr.sch"), logFile=logFile)

            # => epi2hr.nii.gz
            if imtest(epi2hr) is False:
                rrun("applywarp -i " + exfun + " -r " + self.subject.t1_data + " -o " + epi2hr + " --premat=" + epi2hr + ".mat" + " --interp=spline", logFile=logFile)

            runsystem("rm " + epi2hr + "_init.mat", logFile=logFile)
        else:
            # NOT BBR
            if os.path.isfile(epi2hr + ".mat") is False:
                rrun("flirt -in " + exfun + " -ref " + self.subject.t1_brain_data + " -out " + epi2hr + " -omat " + epi2hr + ".mat" + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear", logFile=logFile)

        if os.path.isfile(hr2epi_mat) is False:
            rrun("convert_xfm -inverse -omat " + hr2epi_mat + " " + epi2hr + ".mat", logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => epi2std.mat (as concat)
        if os.path.isfile(epi2std + ".mat") is False:
            rrun("convert_xfm -concat " + hr2std + ".mat" + " " + epi2hr + ".mat" + " -omat " + epi2std + ".mat", logFile=logFile)

        # => std2epi.mat
        if os.path.exists(std2epi + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + std2epi + ".mat " + epi2std + ".mat")

        # => $ROI_DIR/reg_${std_img_label}/rs(fmri)2std.nii.gz
        if imtest(epi2std) is False:
            rrun("flirt -ref " + std_img + " -in " + exfun + " -out " + epi2std + " -applyxfm -init " + epi2std + ".mat" + " -interp trilinear", logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(epi2std + "_warp") is False:
            rrun("convertwarp --ref=" + std_head_img + " --premat=" + epi2hr + ".mat" + " --warp1=" + hr2std_warp + " --out=" + epi2std + "_warp", logFile=logFile)

        # invwarp: standard -> highres -> epi
        if imtest(std2epi + "_warp") is False:
            rrun("invwarp -r " + exfun + " -w " + epi2std + "_warp" + " -o " + std2epi + "_warp", logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <-> STANDARD4    (epi2hr + hr2std4_warp)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if type == "rs":
            if imtest(epi2std4 + "_warp") is False:
                rrun("convertwarp --ref=" + std4_head_img + " --premat=" + epi2hr + ".mat" + " --warp1=" + hr2std4_warp + " --out=" + epi2std4 + "_warp", logFile=logFile)

            if imtest(std42epi + "_warp") is False:
                rrun("invwarp -r " + exfun + " -w " + epi2std4 + "_warp" + " -o " + std42epi + "_warp", logFile=logFile)

            # ------------------------------------------------------------------------------------------------------
            # various co-registration
            # ------------------------------------------------------------------------------------------------------
            # coregister fast-highres to epi
            if imtest(os.path.join(self.subject.roi_rs_dir, "t1_wm_rs")) is False:
                rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_wm") + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + os.path.join(self.subject.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_wm_rs"), logFile=logFile)

            if imtest(os.path.join(self.subject.roi_rs_dir, "t1_csf_rs")) is False:
                rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_csf") + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + os.path.join(self.subject.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_csf_rs"), logFile=logFile)

            if imtest(os.path.join(self.subject.roi_rs_dir, "t1_gm_rs")) is False:
                rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_gm") + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + os.path.join(self.subject.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_gm_rs"), logFile=logFile)

            if imtest(os.path.join(self.subject.roi_rs_dir, "t1_brain_rs")) is False:
                rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, self.subject.t1_brain_data) + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + os.path.join(self.subject.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_brain_rs"), logFile=logFile)

            if imtest(os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs")) is False:
                rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, self.subject.t1_brain_data_mask) + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + os.path.join(self.subject.roi_rs_dir, "hr2rs.mat") + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs"), logFile=logFile)

            # mask & binarize
            rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_gm_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_gm_rs"), logFile=logFile)
            rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_wm_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_wm_rs"), logFile=logFile)
            rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_csf_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_csf_rs"), logFile=logFile)
            rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_brain_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"), logFile=logFile)
            rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"), logFile=logFile)

    # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES -- (non-lin) --> STANDARD
    def transform_dti_t2(self, stdimg="", logFile=None):

        if stdimg == "":

            std_img_label = "std"

            std_img             = self.subject._global.fsl_std_mni_2mm_brain
            std_head_img        = self.subject._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self.subject._global.fsl_std_mni_2mm_brain_mask_dil

        else:
            imgdir = os.path.dirname(stdimg)
            std_img_label = remove_ext(os.path.basename(stdimg))  # "pediatric"

            std_head_img        = os.path.join(imgdir, std_img_label)  # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")  # "pediatric_brain"
            std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")  # "pediatric_brain_mask_dil"

        if imtest(self.subject.t1_brain_data) is False:
            print(
                "file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.t1_data) is False:
            print("file T1_DATA: " + self.subject.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        # check template
        if imtest(std_img) is False:
            print("ERROR: file std_img: " + std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_head_img) is False:
            print("ERROR: file std_img: " + std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_img_mask_dil) is False:
            print(
                "ERROR: file std_img_mask_dil: " + std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        print(self.subject.label + ":						STARTED : nonlin nodiff-t1-standard coregistration")
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.subject.dti_nodiff_data) is False:
            rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)
        if imtest(self.subject.dti_nodiff_brain_data) is False:
            rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # T2 <------> HIGHRES (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # t2 -> hr linear
        t22hr = os.path.join(self.subject.roi_t1_dir, "t22hr")
        if os.path.exists(t22hr + ".mat") is False:
            rrun("flirt -in " + self.subject.t2_brain_data + " -ref " + self.subject.t1_brain_data + " -out " + t22hr + " -omat " + t22hr + ".mat" +
                " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)

        # hr -> t2 linear
        hr2t2 = os.path.join(self.subject.roi_t2_dir, "hr2t2")
        if os.path.exists(hr2t2 + ".mat") is False:
            rrun("convert_xfm -omat " + hr2t2 + ".mat" + " -inverse " + t22hr + ".mat", logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <--->  T2 non linear
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # dti -> t2 linear
        if os.path.exists(self.subject.dti2t2_mat) is False:
            rrun("flirt -in " + self.subject.t2_brain_data + " -ref " + self.subject.dti_nodiff_brain_data + " -omat " + self.subject.dti2t2_mat +
                " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)

        # t2 -> dti linear
        if os.path.exists(self.subject.t22dti_mat) is False:
            rrun("convert_xfm -omat " + self.subject.t22dti_mat + " -inverse " + self.subject.dti2t2_mat, logFile=logFile)

        # dti -> t2 non linear
        if imtest(self.subject.dti2t2_warp) is False:
            rrun("fnirt --in=" + self.subject.t2_data + " --ref=" + self.subject.t2_data + " --aff=" + self.subject.dti2t2_mat + " --cout=" + self.subject.dti2t2_warp, logFile=logFile)

        # t2 -> dti non linear
        if imtest(self.subject.t22dti_warp) is False:
            rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.subject.dti2t2_warp + " -o " + self.subject.t22dti_warp, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.subject.dti2hr_warp) is False:
            rrun("convertwarp --ref=" + self.subject.t1_data + " --warp1=" + self.subject.dti2t2_warp + " --postmat=" + t22hr + ".mat" + " --out=" + self.subject.dti2hr_warp, logFile=logFile)

        if imtest(self.subject.hr2dti_warp) is False:
            rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.subject.dti2hr_warp + " -o " + self.subject.hr2dti_warp, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES -- (non-lin) --> STANDARD
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        dti2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label)
        hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
        if imtest(dti2std + "_warp") is False:
            rrun("convertwarp --ref=" + std_head_img + " --warp1=" + self.subject.dti2t2_warp + " --midmat=" + t22hr + ".mat" + " --warp2=" + hr2std_warp + " --out=" + dti2std + "_warp",logFile=logFile)

        std2dti = os.path.join(self.subject.roi_dti_dir, std_img_label + "2dti")
        if imtest(std2dti + "_warp") is False:
            rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + dti2std + "_warp" + " -o " + std2dti + "_warp", logFile=logFile)

    # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
    def transform_dti(self, stdimg="", logFile=None):

        if stdimg == "":

            std_img_label       = "std"

            std_img             = self.subject._global.fsl_std_mni_2mm_brain
            std_head_img        = self.subject._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self.subject._global.fsl_std_mni_2mm_brain_mask_dil

            std4_img            = self.subject._global.fsl_std_mni_4mm_brain
            std4_head_img       = self.subject._global.fsl_std_mni_4mm_head
            std4_img_mask_dil   = self.subject._global.fsl_std_mni_4mm_brain_mask_dil
        else:
            imgdir              = os.path.dirname(stdimg)
            std_img_label       = remove_ext(os.path.basename(stdimg))                      # "pediatric"

            std_head_img        = os.path.join(imgdir, std_img_label)                       # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")            # "pediatric_brain"
            std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")   # "pediatric_brain_mask_dil"

            std4_head_img        = os.path.join(imgdir, std_img_label + "4")                # "pediatric4"
            std4_img             = os.path.join(imgdir, std_img_label + "4_brain")          # "pediatric4_brain"
            std4_img_mask_dil    = os.path.join(imgdir, std_img_label + "4_brain_mask_dil") # "pediatric4_brain_mask_dil"

        if imtest(self.subject.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.t1_data) is False:
            print("file T1_DATA: " + self.subject.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        # check template
        if imtest(std_img) is False:
            print("ERROR: file std_img: " + std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_head_img) is False:
            print("ERROR: file std_img: " + std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(std_img_mask_dil) is False:
            print("ERROR: file std_img_mask_dil: " + std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        print(self.subject.label + ":						STARTED : nonlin nodiff-t1-standard coregistration")
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.subject.dti_nodiff_data) is False:
            rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)
        if imtest(self.subject.dti_nodiff_brain_data) is False:
            rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <------> HIGHRES (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        dti2hr = os.path.join(self.subject.roi_t1_dir, "dti2hr")
        if os.path.exists(dti2hr + ".mat") is False:
            rrun("flirt -in " + self.subject.dti_nodiff_data + "_brain" + " -ref " + self.subject.t1_brain_data + " -out " + dti2hr + " -omat " + dti2hr + ".mat" +
                " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear", logFile=logFile)

        hr2dti = os.path.join(self.subject.roi_dti_dir, "hr2dti")
        if os.path.exists(hr2dti + ".mat") is False:
            rrun("convert_xfm -omat " + hr2dti + ".mat" + " -inverse " + dti2hr + ".mat", logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        dti2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label)
        hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
        if imtest(dti2std + "_warp") is False:
            rrun("convertwarp --ref=" + std_head_img + " --premat=" + dti2hr + ".mat" + " --warp1=" + hr2std_warp + " --out=" + dti2std + "_warp", logFile=logFile)

        std2dti = os.path.join(self.subject.roi_dti_dir, std_img_label + "2dti")
        if imtest(std2dti + "_warp") is False:
            rrun("invwarp -r " + self.subject.dti_nodiff_data  + " -w " + dti2std + "_warp" + " -o " + std2dti + "_warp", logFile=logFile)

    # this method takes base images (t1, epi_example_function, dti_no_diff) and coregister to all other modalities and standard
    def test_all_coregistration(self):

        #t1
        in_img = self.subject.t1_brain_data

        t12std_nl = os.path.join(self.subject.roi_std_dir, "t12std_nl")
        t12std_l = os.path.join(self.subject.roi_std_dir, "t12std_l")

        t12rs_nl = os.path.join(self.subject.roi_std_dir, "t12std_nl")
        t12rs_l = os.path.join(self.subject.roi_std_dir, "t12std_l")

        t12dti_nl = os.path.join(self.subject.roi_std_dir, "t12std_nl")
        t12dti_l = os.path.join(self.subject.roi_std_dir, "t12std_l")

        self.transform_roi("hr2std", islin=False, rois=[in_img])


    # ==================================================================================================================================================
    # GENERIC ROI TRANSFORMS
    # ==================================================================================================================================================
    # path_type =   "standard"      : a roi name, located in the default folder (subjectXX/s1/roi/reg_YYY/INPUTPATH),
    #	            "rel"			: a path relative to SUBJECT_DIR (subjectXX/s1/INPUTPATH)
    #               "abs"			: a full path (INPUTPATH)
    # std_img correctness check is up to the caller. it must be in 2x2x2 for std transformation and 4x4x4 for std4 ones.
    # it must be betted (and must contain the "_brain" text for linear and full head for non-linear.
    def transform_roi(self, regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, stdimg="", rois=[]):

        if stdimg == "":
            std_img_label       = "std"

            if islin:
                if "std4" in regtype:
                    std_img = self._global.fsl_std_mni_4mm_brain
                else:
                    std_img = self._global.fsl_std_mni_2mm_brain
            else:
                if "std4" in regtype:
                    std_img = self._global.fsl_std_mni_4mm_head
                else:
                    std_img = self._global.fsl_std_mni_2mm_head

        else:

            if imtest(stdimg) is False:
                print("ERROR: given standard image file (" + stdimg + ") does not exist......exiting")
                return

            imgdir              = os.path.dirname(stdimg)
            std_img_label       = remove_ext(os.path.basename(stdimg))  # "pediatric" with or without brain
            std_img_label       = std_img_label.replace("_brain", "")   # "pediatric"

            # check resolution
            res = read_header(stdimg, ["dx"])["dx"]
            if "std4" in regtype:
                if res != "4":
                    print("ERROR: user pretended to make a transformation toward the std4 space but given template resolution does not match")
                    return
            else:
                if "std" in regtype:
                    if res != "2":
                        print("ERROR: user pretended to make a transformation toward the std space but given template resolution does not match")
                        return

            if islin:
                if "_brain" not in regtype:
                    print("ERROR: in a linear registration, user must provide a _brain image")
                    return

            std_head_img        = os.path.join(imgdir, std_img_label)                       # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")            # "pediatric_brain"
            std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")   # "pediatric_brain_mask_dil"

            std4_head_img        = os.path.join(imgdir, std_img_label + "4")                # "pediatric4"
            std4_img             = os.path.join(imgdir, std_img_label + "4_brain")          # "pediatric4_brain"
            std4_img_mask_dil    = os.path.join(imgdir, std_img_label + "4_brain_mask_dil") # "pediatric4_brain_mask_dil"

        if mask != "":
            if imtest(mask) is False:
                print("ERROR: mask image file (" + mask + ") do not exist......exiting")
                return

        if len(rois) == 0:
            print("Input ROI list is empty......exiting")
            return

        # ==============================================================================================================
        print("registration_type " + regtype + ", do_linear = " + str(islin))

        self.subject.has_T2 = 0
        if imtest(self.subject.t2_data) is True:
            self.subject.has_T2 = True

        linear_registration_type = {
            "std2hr": self.transform_l_std2hr,
            "std42hr": self.transform_l_std42hr,
            "epi2hr": self.transform_l_epi2hr,
            "dti2hr": self.transform_l_dti2hr,
            "std2epi": self.transform_l_std2epi,
            "std42epi": self.transform_l_std42epi,
            "hr2epi": self.transform_l_hr2epi,
            "dti2epi": self.transform_l_dti2epi,
            "hr2std": self.transform_l_hr2std,
            "hr2std4": self.transform_l_hr2std4,
            "epi2std": self.transform_l_epi2std,
            "dti2std": self.transform_l_dti2std,
            "std2std4": self.transform_l_std2std4,
            "epi2std4": self.transform_l_epi2std4,
            "hr2dti": self.transform_l_hr2dti,
            "epi2dti": self.transform_l_epi2dti,
            "std2dti": self.transform_l_std2dti
        }

        non_linear_registration_type = {
            "std2hr": self.transform_nl_std2hr,
            "std42hr": self.transform_nl_std42hr,
            "epi2hr": self.transform_nl_epi2hr,
            "dti2hr": self.transform_nl_dti2hr,
            "std2epi": self.transform_nl_std2epi,
            "std42epi": self.transform_nl_std42epi,
            "hr2epi": self.transform_nl_hr2epi,
            "dti2epi": self.transform_nl_dti2epi,
            "hr2std": self.transform_nl_hr2std,
            "hr2std4": self.transform_nl_hr2std4,
            "epi2std": self.transform_nl_epi2std,
            "dti2std": self.transform_nl_dti2std,
            "std2std4": self.transform_nl_std2std4,
            "epi2std4": self.transform_nl_epi2std4,
            "hr2dti": self.transform_nl_hr2dti,
            "epi2dti": self.transform_nl_epi2dti,
            "std2dti": self.transform_nl_std2dti,
        }

        for roi in rois:

            roi_name = os.path.basename(roi)
            print("converting " + roi_name)

            if islin:
                output_roi = linear_registration_type[regtype](pathtype, roi_name, roi, std_img)
            else:
                # is non linear
                output_roi = non_linear_registration_type[regtype](pathtype, roi_name, roi, std_img)

            if thresh > 0:
                output_roi_name     = os.path.basename(output_roi)
                output_input_roi    = os.path.dirname(output_roi)

                rrun("fslmaths " + output_roi + " -thr " + str(thresh) + " -bin " + os.path.join(output_input_roi, "mask_" + output_roi_name))
                v1 = rrun("fslstats " + os.path.join(output_input_roi, "mask_" + output_roi_name) + " -V")[0]

                if v1 == 0:
                    if orf != "":
                        print("subj: " + self.subject.label + ", roi: " + roi_name + " ... is empty, thr: " + str(thresh))  # TODO: print to file

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO HR (from epi, dti, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2hr(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
            return

        warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    def transform_l_std2hr(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
            return

        mat = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    def transform_nl_std42hr(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    def transform_l_std42hr(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        mat = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    def transform_nl_epi2hr(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            epi2hr_warp = os.path.join(self.subject.roi_t1_dir, "rs2hr_warp")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            epi2hr_warp = os.path.join(self.subject.roi_t1_dir, "fmri2hr_warp")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if imtest(epi2hr_warp) is False:
            print("ERROR: transformation warp " + epi2hr_warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + epi2hr_warp)
        return output_roi

    def transform_l_epi2hr(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            epi2hr_mat = os.path.join(self.subject.roi_t1_dir, "rs2hr.mat")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            epi2hr_mat = os.path.join(self.subject.roi_t1_dir, "fmri2hr.mat")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(epi2hr_mat) is False:
            print("ERROR: transformation matrix " + epi2hr_mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + epi2hr_mat + " -interp trilinear")
        return output_roi

    def transform_nl_dti2hr(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if self.subject.has_T2 is True:
            if imtest(self.subject.dti2hr_warp) is False:
                print("ERROR: transformation warp " + self.subject.dti2hr_warp + " is missing...exiting transform roi")
                return ""
            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + self.subject.dti2hr_warp)
        else:
            if os.path.exists(self.subject.dti2hr_mat) is False:
                print("ERROR: transformation matrix " + self.subject.dti2hr_mat + " is missing...exiting transform roi")
                return ""
            rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.dti2hr_mat + " -interp trilinear")
        return output_roi

    def transform_l_dti2hr(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(self.subject.dti2hr_mat) is False:
            print("ERROR: transformation matrix " + self.subject.dti2hr_mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.dti2hr_mat + " -interp trilinear")
        return output_roi

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO EPI (from hr, dti, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2epi(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            std2epi_warp= os.path.join(roi_epi_dir, std_img_label + "2rs_warp")

        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            std2epi_warp= os.path.join(roi_epi_dir, std_img_label + "2fmri_warp")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if imtest(std2epi_warp) is False:
            print("ERROR: transformation warp " + std2epi_warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + examplefunc + " -o " + output_roi + " --warp=" + std2epi_warp)
        return output_roi

    def transform_l_std2epi(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            std2epi_mat = os.path.join(roi_epi_dir, std_img_label + "2rs.mat")

        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            std2epi_mat = os.path.join(roi_epi_dir, std_img_label + "2fmri.mat")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(std2epi_mat) is False:
            print("ERROR: transformation matrix " + std2epi_mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + examplefunc + " -out " + output_roi + " -applyxfm -init " + std2epi_mat)
        return output_roi

    def transform_nl_std42epi(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            std42epi_warp = os.path.join(roi_epi_dir, std_img_label + "42rs_warp")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            std42epi_warp = os.path.join(roi_epi_dir, std_img_label + "42fmri_warp")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if imtest(std42epi_warp) is False:
            print("ERROR: transformation warp " + std42epi_warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + examplefunc + " -o " + output_roi + " --warp=" + std42epi_warp)
        return output_roi

    def transform_l_std42epi(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            std42epi_mat = os.path.join(roi_epi_dir, std_img_label + "42rs.mat")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            std42epi_mat = os.path.join(roi_epi_dir, std_img_label + "42fmri.mat")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(std42epi_mat) is False:
            print("ERROR: transformation matrix " + std42epi_mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + std42epi_mat)
        return output_roi

    def transform_nl_hr2epi(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        print("the hr2epi NON linear transformation does not exist.....using the linear one")
        return self.transform_l_hr2epi(path_type, roi_name, roi, std_img, epi_label, std_img_label)

    def transform_l_hr2epi(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            hr2epi_mat  = os.path.join(roi_epi_dir, "hr2rs.mat")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            hr2epi_mat  = os.path.join(roi_epi_dir, "hr2fmri.mat")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(hr2epi_mat) is False:
            print("ERROR: transformation matrix " + hr2epi_mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + examplefunc + " -out " + output_roi + " -applyxfm -init " + hr2epi_mat + " -interp trilinear")
        return output_roi

    def transform_nl_dti2epi(self, path_type, roi_name, roi, std_img, std_img_label="std"):
        print("registration type: dti2epi NOT SUPPORTED...exiting")

    def transform_l_dti2epi(self, path_type, roi_name, roi, std_img, std_img_label="std"):
        print("registration type: dti2epi NOT SUPPORTED...exiting")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD (from hr, epi, dti)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2std(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name + "_std")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    def transform_l_hr2std(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name + "_std")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + ".mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    def transform_nl_epi2std(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name + "_std")

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            warp        = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + "_warp")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            warp        = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "fmri2" + std_img_label + "_warp")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    def transform_l_epi2std(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name + "_std")

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            mat         = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + ".mat")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            mat         = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + ".mat")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    def transform_nl_dti2std(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name + "_std")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label + "_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)

    def transform_l_dti2std(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name + "_std")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label + ".mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD4 (from hr, epi, std)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_l_std2std4(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", roi_name + "_std4")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")
        return output_roi

    def transform_nl_std2std4(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        return self.transform_l_std2std4(path_type, roi_name, roi, std_img, std_img_label)

    def transform_l_epi2std4(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", roi_name + "_std4")

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            mat         = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "rs2" + std_img_label + "4.mat")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            mat         = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "fmri2" + std_img_label + "4.mat")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    def transform_nl_epi2std4(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", roi_name + "_std4")

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            warp        = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "rs2" + std_img_label + "4_warp")
        elif epi_label.startswith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            warp        = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "rs2" + std_img_label + "4_warp")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_epi_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
            return

        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    def transform_l_hr2std4(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", roi_name + "_std4")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2" + std_img_label + "4.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

    def transform_nl_hr2std4(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", roi_name + "_std4")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2" + std_img_label + "4_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO DTI (from hr, epi, std)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2dti(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if self.subject.has_T2 is True and imtest(self.subject.hr2dti_warp) is True:
            if imtest(self.subject.hr2dti_warp) is False:
                print("ERROR: transformation warp " + self.subject.hr2dti_warp + " is missing...exiting transform roi")
                return ""
            rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + self.subject.hr2dti_warp)
        else:
            print("did not find the non linear registration from HR 2 DTI, I used a linear one")
            if os.path.exists(self.subject.hr2dti_mat) is False:
                print("ERROR: transformation matrix " + self.subject.hr2dti_mat + " is missing...exiting transform roi")
                return ""
            rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.hr2dti_mat + " -interp trilinear")
        return output_roi

    def transform_l_hr2dti(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        if os.path.exists(self.subject.hr2dti_mat) is False:
            print("ERROR: transformation matrix " + self.subject.hr2dti_mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.hr2dti_mat + " -interp trilinear")
        return output_roi

    def transform_nl_epi2dti(self, path_type, roi_name, roi, std_img, epi_label="rs", std_img_label="std"):
        print("registration type: epi2dti NOT SUPPORTED...exiting")
        return ""

    def transform_l_epi2dti(self, path_type, roi_name, roi, std_img, epi_label="rs"):
        print("registration type: epi2dti NOT SUPPORTED...exiting")
        return ""

    def transform_nl_std2dti(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        warp = os.path.join( self.subject.roi_dti_dir, std_img_label + "2dti_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nodif_brain") + " -o " + output_roi + " --warp=" + warp)
        return output_roi

    def transform_l_std2dti(self, path_type, roi_name, roi, std_img, std_img_label="std"):

        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "roi")
        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
            return ""

        mat = os.path.join( self.subject.roi_dti_dir, std_img_label + "2dti.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")
        return output_roi

        # ==============================================================================================================

