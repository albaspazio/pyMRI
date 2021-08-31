import os

from myfsl.utils.run import rrun
from utility.fslfun import runsystem
from utility.images import imtest, imcp, imgname, remove_ext, read_header


#   RS    <----------> HR <---> STD  <---> STD4
#    |    <----------> HR <--------------> STD4
#    |
#   FMRI  <----------> HR <---> STD
#   FMRI  <----------> HR <--------------> STD4
#
#   DTI   <----------> HR <---> STD
#   DTI   <--> T2 <--> HR <---> STD
#
class SubjectTransforms:

    def __init__(self, subject, _global):
        
        self.subject = subject
        self._global = _global

        # define all available transformations
        self.linear_registration_type = {
            "stdTOstd4": self.transform_l_std2std4,
            "stdTOhr": self.transform_l_std2hr,
            "stdTOrs": self.transform_l_std2rs,
            "stdTOfmri": self.transform_l_std2fmri,
            "stdTOdti": self.transform_l_std2dti,

            "std4TOhr": self.transform_l_std42hr,
            "std4TOrs": self.transform_l_std42rs,
            "std4TOfmri": self.transform_l_std42fmri,

            "hrTOstd": self.transform_l_hr2std,
            "hrTOstd4": self.transform_l_hr2std4,
            "hrTOrs": self.transform_l_hr2rs,
            "hrTOfmri": self.transform_l_hr2fmri,
            "hrTOdti": self.transform_l_hr2dti,
            "hrTOt2": self.transform_l_hr2t2,

            "rsTOstd": self.transform_l_rs2std,
            "rsTOstd4": self.transform_l_rs2std4,
            "rsTOhr": self.transform_l_rs2hr,
            "rsTOfmri": self.transform_l_rs2fmri,

            "fmriTOstd": self.transform_l_fmri2std,
            "fmriTOhr": self.transform_l_fmri2hr,
            "fmriTOstd4": self.transform_l_fmri2std4,
            "fmriTOrs": self.transform_l_fmri2rs,

            "dtiTOstd": self.transform_l_dti2std,
            "dtiTOhr": self.transform_l_dti2hr,
            "dtiTOt2": self.transform_l_dti2t2,

            "t2TOhr": self.transform_l_t22hr,
            "t2TOdti": self.transform_l_t22dti
        }

        self.non_linear_registration_type = {
            "stdTOstd4": self.transform_nl_std2std4,
            "stdTOhr": self.transform_nl_std2hr,
            "stdTOrs": self.transform_nl_std2rs,
            "stdTOfmri": self.transform_nl_std2fmri,
            "stdTOdti": self.transform_nl_std2dti,

            "std4TOhr": self.transform_nl_std42hr,
            "std4TOrs": self.transform_nl_std42rs,
            "std4TOfmri": self.transform_nl_std42fmri,

            "hrTOstd": self.transform_nl_hr2std,
            "hrTOstd4": self.transform_nl_hr2std4,
            "hrTOrs": self.transform_nl_hr2rs,
            "hrTOfmri": self.transform_nl_hr2fmri,
            "hrTOdti": self.transform_nl_hr2dti,
            "hrTOt2": self.transform_nl_hr2t2,

            "rsTOstd": self.transform_nl_rs2std,
            "rsTOstd4": self.transform_nl_rs2std4,
            "rsTOhr": self.transform_nl_rs2hr,
            "rsTOfmri": self.transform_nl_rs2fmri,

            "fmriTOstd": self.transform_nl_fmri2std,
            "fmriTOhr": self.transform_nl_fmri2hr,
            "fmriTOstd4": self.transform_nl_fmri2std4,
            "fmriTOrs": self.transform_nl_fmri2rs,

            "dtiTOstd": self.transform_nl_dti2std,
            "dtiTOhr": self.transform_nl_dti2hr,
            "dtiTOt2": self.transform_nl_dti2t2,

            "t2TOhr": self.transform_nl_t22hr,
            "t2TOdti": self.transform_nl_t22dti
        }
        
    def fnirt(self, ref, ofn="", odp="", refmask="", inimg="t1"):

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
    # it creates:   hr2std.mat, hrhead2std.mat, std2hr.mat, hr2std_warp, std2hr_warp
    #               hr2std4.mat, hrhead2std4.mat, std42hr.mat, hr2std4_warp, std42hr_warp
    def transform_mpr(self, stdimg="", logFile=None):

        if stdimg == "":

            std_img_label       = "std"

            std_img             = self._global.fsl_std_mni_2mm_brain
            std_head_img        = self._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self._global.fsl_std_mni_2mm_brain_mask_dil

            std4_img            = self._global.fsl_std_mni_4mm_brain
            std4_head_img       = self._global.fsl_std_mni_4mm_head
            std4_img_mask_dil   = self._global.fsl_std_mni_4mm_brain_mask_dil
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
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + std_img + " -omat " + hr2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2{std}.mat
        if os.path.isfile(hrhead2std + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + std_head_img + " -omat " + hrhead2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => {std}2hr.mat
        if os.path.isfile(std2hr + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + std2hr + ".mat " + hr2std + ".mat")

        # NON LINEAR
        # => hr2{std}_warp
        if imtest(hr2std_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std + ".mat --config=" + self.subject._global.fsl_std_mni_2mm_cnf +
                    " --ref=" + std_head_img + " --refmask=" + std_img_mask_dil + " --warpres=10,10,10" +
                    " --cout=" + hr2std_warp + " --iout=" + hr2std + " --jout=" + hr2std + "_jac")

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
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + std4_img + " -omat " + hr2std4 + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2{std}4.mat
        if os.path.isfile(hrhead2std4 + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + std4_head_img + " -omat " + hrhead2std4 + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

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
    # it creates    : example_func, epi2hr.mat,
    def transform_epi(self, type='fmri', stdimg="", do_bbr=False, wmseg="", logFile=None):

        if stdimg == "":

            std_img_label       = "std"

            std_img             = self._global.fsl_std_mni_2mm_brain
            std_head_img        = self._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self._global.fsl_std_mni_2mm_brain_mask_dil

            std4_img            = self._global.fsl_std_mni_4mm_brain
            std4_head_img       = self._global.fsl_std_mni_4mm_head
            std4_img_mask_dil   = self._global.fsl_std_mni_4mm_brain_mask_dil
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
        hr2std4         = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4"   , "hr2" + std_img_label + "4")
        hr2std_warp     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label         , "hr2" + std_img_label + "_warp")
        hr2std4_warp    = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4"   , "hr2" + std_img_label + "4_warp")

        if wmseg == "":
            wmseg = self.subject.t1_segment_wm_bbr_path
        else:
            if imtest(wmseg) is False and do_bbr is True:
                print("ERROR: asked to run bbr, but the given wmseg file " + wmseg + ".nii.gz is not present...exiting transforms_mpr")
                return

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

        if imtest(std4_head_img) is False:
            print("WARNING: file std4_head_img: " + std4_head_img + ".nii.gz is not present...skipping STD4 transform")

        if imtest(std4_img_mask_dil) is False:
            print("WARNING: file std4_img_mask_dil: " + std4_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")

        os.makedirs(folder, exist_ok=True)
        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label), exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # check or create example function
        exfun = self.subject.epi.get_example_function(logFile=logFile)

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
            rrun("flirt -ref " + std_img + " -in " + exfun + " -applyxfm -init " + epi2std + ".mat" + " -interp trilinear", logFile=logFile)

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

            # => epi2std4.mat
            if os.path.isfile(epi2std4 + ".mat") is False:
                rrun("convert_xfm -concat " + hr2std4 + ".mat" + " " + epi2hr + ".mat" + " -omat " + epi2std4 + ".mat", logFile=logFile)

            if imtest(std42epi + "_warp") is False:
                rrun("invwarp -r " + exfun + " -w " + epi2std4 + "_warp" + " -o " + std42epi + "_warp", logFile=logFile)

            # => std42epi.mat
            if os.path.exists(std42epi + ".mat") is False:
                rrun("convert_xfm -inverse -omat " + std42epi + ".mat " + epi2std4 + ".mat")

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

    # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
    # creates       :   dti2hr.mat, hr2dti.mat, dti2std_warp, std2dti_warp (dti <-> hr <-> std)
    # and if has_T2 :   t22hr.mat, hr2t2.mat, dti2t2.mat, t22dti.mat, dti2t2_warp, t22dti_warp, dti2hr_warp, hr2dti_warp
    #                   overwrites dti2std_warp, std2dti_warp
    def transform_dti(self, stdimg="", logFile=None):

        if stdimg == "":

            std_img_label       = "std"

            std_img             = self._global.fsl_std_mni_2mm_brain
            std_head_img        = self._global.fsl_std_mni_2mm_head
            std_img_mask_dil    = self._global.fsl_std_mni_2mm_brain_mask_dil

        else:
            imgdir              = os.path.dirname(stdimg)
            std_img_label       = remove_ext(os.path.basename(stdimg))                      # "pediatric"

            std_head_img        = os.path.join(imgdir, std_img_label)                       # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")            # "pediatric_brain"
            std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")   # "pediatric_brain_mask_dil"

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
        self.subject.dti.get_nodiff()

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <------> HIGHRES (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        dti2hr = os.path.join(self.subject.roi_t1_dir, "dti2hr")
        if os.path.exists(dti2hr + ".mat") is False:
            rrun("flirt -in " + self.subject.dti_nodiff_data + "_brain" + " -ref " + self.subject.t1_brain_data + " -omat " + dti2hr + ".mat" +
                " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear", logFile=logFile)

        hr2dti = os.path.join(self.subject.roi_dti_dir, "hr2dti")
        if os.path.exists(hr2dti + ".mat") is False:
            rrun("convert_xfm -omat " + hr2dti + ".mat" + " -inverse " + dti2hr + ".mat", logFile=logFile)

        if self.subject.hasT2 is False:

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            dti2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label)
            hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
            hr2std      = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label)
            if imtest(dti2std + "_warp") is False:
                rrun("convertwarp --ref=" + std_head_img + " --premat=" + dti2hr + ".mat" + " --warp1=" + hr2std_warp + " --out=" + dti2std + "_warp", logFile=logFile)

            if os.path.exists(dti2std + ".mat") is False:
                rrun("convert_xfm -omat " + dti2std + ".mat" + " -concat " + dti2hr + ".mat" + " " + hr2std + ".mat", logFile=logFile)

            std2dti = os.path.join(self.subject.roi_dti_dir, std_img_label + "2dti")
            if imtest(std2dti + "_warp") is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data  + " -w " + dti2std + "_warp" + " -o " + std2dti + "_warp", logFile=logFile)

            if os.path.exists(std2dti + ".mat") is False:
                rrun("convert_xfm -omat " + std2dti + ".mat" + " -inverse " + dti2std + ".mat")

        else:
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <--->  T2  linear and non-linear
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 -> dti
            # linear
            if os.path.exists(self.subject.t22dti_mat) is False:
                rrun("flirt -in " + self.subject.t2_brain_data + " -ref " + self.subject.dti_nodiff_brain_data + " -omat " + self.subject.t22dti_mat +
                    " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)
            # non-linear
            if imtest(self.subject.t22dti_warp) is False:
                rrun("fnirt --in=" + self.subject.t2_data + " --ref=" + self.subject.dti_nodiff_data + " --aff=" + self.subject.t22dti_mat + " --cout=" + self.subject.t22dti_warp, logFile=logFile)

            # dti -> t2
            # linear
            if os.path.exists(self.subject.dti2t2_mat) is False:
                rrun("convert_xfm -omat " + self.subject.dti2t2_mat + " -inverse " + self.subject.t22dti_mat,
                     logFile=logFile)
            # non-linear
            if imtest(self.subject.dti2t2_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.subject.t22dti_warp + " -o " + self.subject.dti2t2_warp, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # T2 <------> HIGHRES (linear)
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 -> hr linear
            if os.path.exists(self.subject.t22hr_mat) is False:
                rrun("flirt -in " + self.subject.t2_brain_data + " -ref " + self.subject.t1_brain_data + " -omat " + self.subject.t22hr_mat +
                    " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear",
                    logFile=logFile)

            # hr -> t2 linear
            if os.path.exists(self.subject.hr2t2_mat) is False:
                rrun("convert_xfm -omat " + self.subject.hr2t2_mat + " -inverse " + self.subject.t22hr_mat, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if imtest(self.subject.dti2hr_warp) is False:
                rrun("convertwarp --ref=" + self.subject.t1_data + " --warp1=" + self.subject.dti2t2_warp + " --postmat=" + self.subject.t22hr_mat + ".mat" + " --out=" + self.subject.dti2hr_warp, logFile=logFile)

            if imtest(self.subject.hr2dti_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.subject.dti2hr_warp + " -o " + self.subject.hr2dti_warp, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES -- (non-lin) --> STANDARD
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            dti2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label)
            hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
            if imtest(dti2std + "_warp") is False:
                rrun("convertwarp --ref=" + std_head_img + " --warp1=" + self.subject.dti2t2_warp + " --midmat=" + self.subject.hr2t2_mat + ".mat" + " --warp2=" + hr2std_warp + " --out=" + dti2std + "_warp", logFile=logFile)

            std2dti = os.path.join(self.subject.roi_dti_dir, std_img_label + "2dti")
            if imtest(std2dti + "_warp") is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + dti2std + "_warp" + " -o " + std2dti + "_warp", logFile=logFile)

    # this method takes base images (t1/t1_brain, epi_example_function, dti_nodiff/dti_nodiff_brain) and coregister to all other modalities and standard
    # creates up to 14 folders, 7 for linear and 7 for non linear transformation towards the 7 different space (hr, rs, frmi, dti, t2, std, std4)
    def test_all_coregistration(self, test_dir, stdimg=""):

        # manage STANDARD image
        if stdimg == "":

            std_img_label       = "std"

            std_img             = self.subject._global.fsl_std_mni_2mm_brain
            std_head_img        = self.subject._global.fsl_std_mni_2mm_head
            # std_img_mask_dil    = self.subject._global.fsl_std_mni_2mm_brain_mask_dil

            std4_img            = self.subject._global.fsl_std_mni_4mm_brain
            std4_head_img       = self.subject._global.fsl_std_mni_4mm_head
            # std4_img_mask_dil   = self.subject._global.fsl_std_mni_4mm_brain_mask_dil
        else:
            imgdir              = os.path.dirname(stdimg)
            std_img_label       = remove_ext(os.path.basename(stdimg))                      # "pediatric"

            std_head_img        = os.path.join(imgdir, std_img_label)                       # "pediatric"
            std_img             = os.path.join(imgdir, std_img_label + "_brain")            # "pediatric_brain"
            # std_img_mask_dil    = os.path.join(imgdir, std_img_label + "_brain_mask_dil")   # "pediatric_brain_mask_dil"

            std4_head_img        = os.path.join(imgdir, std_img_label + "4")                # "pediatric4"
            std4_img             = os.path.join(imgdir, std_img_label + "4_brain")          # "pediatric4_brain"
            # std4_img_mask_dil    = os.path.join(imgdir, std_img_label + "4_brain_mask_dil") # "pediatric4_brain_mask_dil"

        nldir   = os.path.join(test_dir, "nlin")
        ldir    = os.path.join(test_dir, "lin")

        # --------------------------------------------------------------
        #  FROM HR <--> STD
        #       HR <--> STD4 if hasRS
        # --------------------------------------------------------------
        if self.subject.hasT1 is True:
        #
            nl_t1   = os.path.join(nldir, "hr"); nl_std  = os.path.join(nldir, std_img_label); nl_std4 = os.path.join(nldir, std_img_label + "4")
            l_t1    = os.path.join(ldir, "hr");   l_std  = os.path.join(ldir, std_img_label);  l_std4  = os.path.join(ldir, std_img_label + "4")

            os.makedirs(nl_t1, exist_ok=True);os.makedirs(nl_std, exist_ok=True);os.makedirs(nl_std4, exist_ok=True)
            os.makedirs(l_t1, exist_ok=True); os.makedirs(l_std, exist_ok=True); os.makedirs(l_std4, exist_ok=True)

            imcp(self.subject.t1_data,       os.path.join(nl_t1, self.subject.t1_image_label))
            imcp(self.subject.t1_brain_data, os.path.join(l_t1 , self.subject.t1_image_label + "_brain"))

            self.transform_roi("hrTOstd",    pathtype="abs", outdir=nl_std   , islin=False, rois=[self.subject.t1_data])
            self.transform_roi("hrTOstd",    pathtype="abs",  outdir=l_std   , islin=True,  rois=[self.subject.t1_brain_data])

            self.transform_roi("stdTOhr",    pathtype="abs", outdir=nl_t1   , islin=False, rois=[std_head_img])
            self.transform_roi("stdTOhr",    pathtype="abs",  outdir=l_t1   , islin=True,  rois=[std_img])

            if self.subject.hasRS is True:  # connect HR with STD4
                pass
                self.transform_roi("hrTOstd4", pathtype="abs", outdir=nl_std4, islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOstd4", pathtype="abs", outdir=l_std4, islin=True, rois=[self.subject.t1_brain_data])

                self.transform_roi("std4TOhr", pathtype="abs", outdir=nl_t1, islin=False, rois=[std4_head_img])
                self.transform_roi("std4TOhr", pathtype="abs", outdir=l_t1, islin=True, rois=[std4_img])
        else:
            print("ERROR...T1 is missing......exiting")
            return

        # --------------------------------------------------------------
        #  FROM RS <--> HR
        #       RS <--> STD
        #       RS <--> STD4
        #       RS <--> FMRI if hasFMRI
        # --------------------------------------------------------------
        if self.subject.hasRS is True:  # goes to HR, STD and STD4

            nl_rs = os.path.join(nldir, "rs")
            l_rs = os.path.join(ldir, "rs")
            os.makedirs(nl_rs, exist_ok=True)
            os.makedirs(l_rs, exist_ok=True)

            exfun = self.subject.epi.get_example_function("rs")

            imcp(exfun, os.path.join(nl_rs, self.subject.label + "_example_func"))
            imcp(exfun, os.path.join(l_rs,  self.subject.label + "_example_func"))

            self.transform_roi("hrTOrs",    pathtype="abs", outdir=nl_rs   , islin=False,   rois=[self.subject.t1_data])
            self.transform_roi("hrTOrs",    pathtype="abs", outdir=l_rs    , islin=True,    rois=[self.subject.t1_brain_data])
            self.transform_roi("rsTOhr",    pathtype="abs", outdir=nl_t1   , islin=False,   rois=[exfun])
            self.transform_roi("rsTOhr",    pathtype="abs", outdir=l_t1    , islin=True,    rois=[exfun])

            self.transform_roi("rsTOstd",   pathtype="abs", outdir=nl_std   , islin=False,   rois=[exfun])
            self.transform_roi("rsTOstd",   pathtype="abs", outdir=l_std    , islin=True,    rois=[exfun])
            self.transform_roi("stdTOrs",   pathtype="abs", outdir=nl_rs   , islin=False,   rois=[std_head_img])
            self.transform_roi("stdTOrs",   pathtype="abs", outdir=l_rs    , islin=True,    rois=[std_img])

            self.transform_roi("rsTOstd4",  pathtype="abs", outdir=nl_std4   , islin=False,   rois=[exfun])
            self.transform_roi("rsTOstd4",  pathtype="abs", outdir=l_std4    , islin=True,    rois=[exfun])
            self.transform_roi("std4TOrs",  pathtype="abs", outdir=nl_rs   , islin=False,   rois=[std4_head_img])
            self.transform_roi("std4TOrs",  pathtype="abs", outdir=l_rs    , islin=True,    rois=[std4_img])

            if self.subject.hasFMRI:    # connect RS with FMRI

                exfun_fmri = self.subject.epi.get_example_function("fmri")

                nl_fmri = os.path.join(nldir, "fmri")
                l_fmri = os.path.join(ldir, "fmri")

                os.makedirs(nl_fmri, exist_ok=True)
                os.makedirs(l_fmri, exist_ok=True)

                self.transform_roi("rsTOfmri", pathtype="abs", outdir=nl_fmri, islin=False, rois=[exfun])
                self.transform_roi("rsTOfmri", pathtype="abs", outdir=l_fmri, islin=True,   rois=[exfun])

                self.transform_roi("fmriTOrs", pathtype="abs", outdir=nl_rs, islin=False,   rois=[exfun_fmri])
                self.transform_roi("fmriTOrs", pathtype="abs", outdir=l_rs, islin=True,     rois=[exfun_fmri])

        # --------------------------------------------------------------
        #  FROM FMRI <--> HR
        #       FMRI <--> STD
        #       FMRI <--> STD4 if hasRS  (fmri <--> was done previously)
        # --------------------------------------------------------------
        if self.subject.hasFMRI is True:  # goes to HR, STD and STD4, RS

            nl_fmri = os.path.join(nldir, "fmri")
            l_fmri = os.path.join(ldir, "fmri")

            os.makedirs(nl_fmri, exist_ok=True)
            os.makedirs(l_fmri, exist_ok=True)

            exfun = self.subject.epi.get_example_function("fmri")

            imcp(exfun, os.path.join(nl_fmri, "example_func"))
            imcp(exfun, os.path.join(l_fmri, "example_func"))

            self.transform_roi("fmriTOhr", pathtype="abs", outdir=nl_t1, islin=False,   rois=[exfun])
            self.transform_roi("fmriTOhr", pathtype="abs", outdir=l_t1, islin=True,     rois=[exfun])

            self.transform_roi("hrTOfmri", pathtype="abs", outdir=nl_fmri, islin=False,   rois=[self.subject.t1_brain_data])
            self.transform_roi("hrTOfmri", pathtype="abs", outdir=l_fmri, islin=True,     rois=[self.subject.t1_data])

            self.transform_roi("fmriTOstd", pathtype="abs", outdir=nl_std, islin=False,  rois=[exfun])
            self.transform_roi("fmriTOstd", pathtype="abs", outdir=l_std, islin=True,    rois=[exfun])

            self.transform_roi("stdTOfmri", pathtype="abs", outdir=nl_fmri, islin=False,  rois=[std_head_img])
            self.transform_roi("stdTOfmri", pathtype="abs", outdir=l_fmri, islin=True,    rois=[std_img])

            if self.subject.hasRS:

                self.transform_roi("fmriTOstd4", pathtype="abs", outdir=nl_std4, islin=False, rois=[exfun])
                self.transform_roi("fmriTOstd4", pathtype="abs", outdir=l_std4, islin=True,   rois=[exfun])

                self.transform_roi("std4TOfmri", pathtype="abs", outdir=nl_fmri, islin=False, rois=[std4_head_img])
                self.transform_roi("std4TOfmri", pathtype="abs", outdir=l_fmri, islin=True,   rois=[std4_img])

        # --------------------------------------------------------------
        #  FROM T2 <--> HR
        #       T2 <--> STD
        # --------------------------------------------------------------
        if self.subject.hasT2 is True:

            nl_t2   = os.path.join(nldir, "t2")
            l_t2    = os.path.join(ldir, "t2")
            os.makedirs(nl_t2, exist_ok=True)
            os.makedirs(l_t2,  exist_ok=True)

            imcp(self.subject.t2_data,       os.path.join(nl_t2, self.subject.t2_image_label))
            imcp(self.subject.t2_brain_data, os.path.join(l_t2 , self.subject.t2_image_label + "_brain"))

            self.transform_roi("t2TOhr"  , pathtype="abs",  outdir=nl_t1  , islin=False, rois=[self.subject.t2_data])
            self.transform_roi("t2TOhr"  , pathtype="abs",  outdir=l_t1   , islin=True,  rois=[self.subject.t2_brain_data])

            self.transform_roi("hrTOt2"  , pathtype="abs",  outdir=nl_t2  , islin=False, rois=[self.subject.t1_data])
            self.transform_roi("hrTOt2"  , pathtype="abs",  outdir=l_t2   , islin=True,  rois=[self.subject.t1_brain_data])

            self.transform_roi("t2TOstd" , pathtype="abs",  outdir=nl_std , islin=False, rois=[self.subject.t2_data])
            self.transform_roi("t2TOstd" , pathtype="abs",  outdir=l_std  , islin=True,  rois=[self.subject.t2_brain_data])

            self.transform_roi("stdTOt2" , pathtype="abs",  outdir=nl_t2  , islin=False, rois=[std_head_img])
            self.transform_roi("stdTOt2" , pathtype="abs",  outdir=l_t2   , islin=True,  rois=[std_img])

        # --------------------------------------------------------------
        #  FROM DTI <--> HR
        #       DTI <--> STD
        #       DTI <--> T2 if hasT2
        # --------------------------------------------------------------
        if self.subject.hasDTI is True:

            nl_dti = os.path.join(nldir, "dti")
            l_dti  = os.path.join(ldir, "dti")

            os.makedirs(nl_dti, exist_ok=True)
            os.makedirs(l_dti, exist_ok=True)

            imcp(self.subject.dti_nodiff_data,       os.path.join(nl_dti, self.subject.label + "_nodiff"))
            imcp(self.subject.dti_nodiff_brain_data, os.path.join(l_dti , self.subject.label + "_nodiff_brain"))

            self.transform_roi("hrTOdti"  , pathtype="abs",  outdir=nl_dti , islin=False, rois=[self.subject.t1_data])
            self.transform_roi("hrTOdti"  , pathtype="abs",  outdir=l_dti  , islin=True,  rois=[self.subject.t1_brain_data])
            self.transform_roi("dtiTOhr"  , pathtype="abs",  outdir=nl_t1  , islin=False, rois=[self.subject.dti_nodiff_data])
            self.transform_roi("dtiTOhr"  , pathtype="abs",  outdir=l_t1   , islin=True,  rois=[self.subject.dti_nodiff_brain_data])

            self.transform_roi("dtiTOstd" , pathtype="abs",  outdir=nl_std , islin=False, rois=[self.subject.dti_nodiff_data])
            self.transform_roi("dtiTOstd" , pathtype="abs",  outdir=l_std  , islin=True,  rois=[self.subject.dti_nodiff_brain_data])
            self.transform_roi("stdTOdti" , pathtype="abs",  outdir=nl_dti , islin=False, rois=[std_head_img])
            self.transform_roi("stdTOdti" , pathtype="abs",  outdir=l_dti  , islin=True,  rois=[std_img])

    # ==================================================================================================================================================
    # GENERIC ROI TRANSFORMS
    # ==================================================================================================================================================
    # path_type =   "standard"      : a roi name, located in the default folder (subjectXX/s1/roi/reg_YYY/INPUTPATH),
    #	            "rel"			: a path relative to SUBJECT_DIR (subjectXX/s1/INPUTPATH)
    #               "abs"			: a full path (INPUTPATH)
    # outdir    =   ""              : save it into roi/reg_... folders
    #               dir path        : save to outdir
    # std_img                       : can be specified a different templete.
    #                                 it must be in 2x2x2 for std transformation and 4x4x4 for std4 ones. correctness is here checked
    #                                 user must provide (in a same folder) the following images:
    #                                       -> stdimg, stdimg_brain, stdimg_brain_mask_dil
    #                                       -> stdimg4, stdimg4_brain, stdimg4_brain_mask_dil
    # in linear transf, it must be betted (must contain the "_brain" text) in non-linear is must be a full head image.
    def transform_roi(self, regtype, pathtype="standard", outdir="", outname="", mask="", orf="", thresh=0, islin=True, stdimg="", rois=[]):

        # ===========================================================
        # SANITY CHECK
        # ===========================================================
        if outdir != "":
            if os.path.isdir(outdir) is False:
                print("ERROR in transform_roi: given outdir (" + outdir + ") is not a folder.....exiting")
                return

        if mask != "":
            if imtest(mask) is False:
                print("ERROR: mask image file (" + mask + ") do not exist......exiting")
                return

        if len(rois) == 0:
            print("Input ROI list is empty......exiting")
            return

        try:
            bool(self.linear_registration_type[regtype])
        except Exception as e:
            print("ERROR in transform_roi: given regtype (" + regtype + ") is not valid.....exiting")
            return
        # ===========================================================

        from_space  = regtype.split("TO")[0]
        to_space    = regtype.split("TO")[1]

        # ===========================================================
        # CHECK STANDARD IMAGES (4mm_brain, 2mm_brain, 4mm_head, 2mm_head)
        # ===========================================================
        if stdimg == "":
            std_img_label = "std"

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
            std_img_label       = std_img_label.replace("_brain", "")   # "pediatric" (without "_brain")

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
                if "std4" in regtype:
                    std_img = os.path.join(imgdir, std_img_label + "4_brain")       # "pediatric4_brain"
                else:
                    std_img = os.path.join(imgdir, std_img_label + "_brain")        # "pediatric_brain"
            else:
                if "std4" in regtype:
                    std_img = os.path.join(imgdir, std_img_label + "4")             # "pediatric4"
                else:
                    std_img = os.path.join(imgdir, std_img_label)                   # "pediatric"

        # ==============================================================================================================
        print("registration_type " + regtype + ", do_linear = " + str(islin))

        self.subject.has_T2 = 0
        if imtest(self.subject.t2_data) is True:
            self.subject.has_T2 = True

        for roi in rois:

            roi_name = os.path.basename(roi)
            print("converting " + roi_name)

            # ----------------------------------------------------------------------------------------------------------
            # SET INPUT
            # ----------------------------------------------------------------------------------------------------------
            if   pathtype == "abs":
                 input_roi = roi
            elif pathtype == "rel":
                 input_roi = os.path.join(self.subject.dir, roi)
            else:
                # is a roi name
                if from_space   == "hr":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_t1", roi_name)
                elif from_space == "rs":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_rs", roi_name)
                elif from_space == "fmri":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_fmri", roi_name)
                elif from_space == "dti":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_dti", roi_name)
                elif from_space == "t2":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_t2", roi_name)
                elif from_space == "std":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, roi_name)
                elif from_space == "std4":
                    input_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", roi_name)

            if imtest(input_roi) is False:
                print("error......input_roi (" + input_roi + ") is missing....exiting")
                return
            # ----------------------------------------------------------------------------------------------------------
            # SET OUTPUT
            # ----------------------------------------------------------------------------------------------------------
            if outname != "":
                name = outname
            else:
                name = roi_name

            if outdir == "":
                if to_space == "hr":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_t1", name + "_" + to_space)
                elif to_space == "rs":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_rs", name + "_" + to_space)
                elif to_space == "fmri":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_fmri", name + "_" + to_space)
                elif to_space == "dti":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_dti", name + "_" + to_space)
                elif to_space == "t2":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_t2", name + "_" + to_space)
                elif to_space == "std":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, name + "_" + to_space)
                elif to_space == "std4":
                    output_roi = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", name + "_" + to_space)
            else:
                output_roi = os.path.join(outdir, name + "_" + to_space)

            # ----------------------------------------------------------------------------------------------------------
            # TRANSFORM !!!!
            # ----------------------------------------------------------------------------------------------------------
            if islin:
                self.linear_registration_type[regtype](input_roi, output_roi, std_img)
            else:
                # is non linear
                self.non_linear_registration_type[regtype](input_roi, output_roi, std_img)

            # ----------------------------------------------------------------------------------------------------------
            # THRESHOLD
            # ----------------------------------------------------------------------------------------------------------
            if thresh > 0:
                output_roi_name     = os.path.basename(output_roi)
                output_input_roi    = os.path.dirname(output_roi)

                rrun("fslmaths " + output_roi + " -thr " + str(thresh) + " -bin " + os.path.join(output_input_roi, "mask_" + output_roi_name))
                v1 = rrun("fslstats " + os.path.join(output_input_roi, "mask_" + output_roi_name) + " -V")[0]

                if v1 == 0:
                    if orf != "":
                        print("subj: " + self.subject.label + ", roi: " + roi_name + " ... is empty, thr: " + str(thresh))  # TODO: print to file

            return output_roi

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO HR (from rs, fmri, dti, t2, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_std42hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std42hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        rs2std_mat  = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + ".mat")
        std2hr_warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr_warp")

        if imtest(std2hr_warp) is False:
            print("ERROR: transformation warp " + std2hr_warp + " is missing...exiting transform roi")
            return ""
        if os.path.exists(rs2std_mat) is False:
            print("ERROR: transformation matrix " + rs2std_mat + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --premat=" + rs2std_mat + " --warp=" + std2hr_warp )
    def transform_l_rs2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_t1_dir, "rs2hr.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        fmri2std_mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "fmri2" + std_img_label + ".mat")
        std2hr_warp  = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr.mat")

        if imtest(std2hr_warp) is False:
            print("ERROR: transformation warp " + std2hr_warp + " is missing...exiting transform roi")
            return ""
        if os.path.exists(fmri2std_mat) is False:
            print("ERROR: transformation matrix " + fmri2std_mat + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --premat=" + fmri2std_mat + " --warp=" + std2hr_warp )
    def transform_l_fmri2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_t1_dir, "fmri2hr.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_dti2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        if self.subject.has_T2 is True:
            if imtest(self.subject.dti2hr_warp) is False:
                print("ERROR: transformation warp " + self.subject.dti2hr_warp + " is missing...exiting transform roi")
                return ""
            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + self.subject.dti2hr_warp)
        else:

            dti2std_mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label + ".mat")
            std2hr_warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr_warp")

            if imtest(std2hr_warp) is False:
                print("ERROR: transformation warp " + std2hr_warp + " is missing...exiting transform roi")
                return ""
            if os.path.exists(dti2std_mat) is False:
                print("ERROR: transformation matrix " + dti2std_mat + " is missing...exiting transform roi")
                return ""

            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --premat=" + dti2std_mat + " --warp=" + std2hr_warp)
    def transform_l_dti2hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        if os.path.exists(self.subject.dti2hr_mat) is False:
            print("ERROR: transformation matrix " + self.subject.dti2hr_mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.dti2hr_mat + " -interp trilinear")

    def transform_nl_t22hr(self, input_roi, output_roi, std_img, std_img_label="std"):
        print("WARNING calling transform_l_t22hr instead of transform_nl_t22hr")
        return self.transform_l_t22hr(input_roi, output_roi, std_img, std_img_label)
    def transform_l_t22hr(self, input_roi, output_roi, std_img, std_img_label="std"):

        if os.path.exists(self.subject.t22hr_mat) is False:
            print("ERROR: transformation matrix " + self.subject.t22hr_mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.t22hr_mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO RS (from hr, fmri, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_rs_dir, std_img_label + "2rs_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.rs_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_rs_dir, std_img_label + "2rs.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_std42rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_rs_dir, std_img_label + "42rs_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.rs_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std42rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_rs_dir, std_img_label + "42rs.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_hr2rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        print("WARNING: transform_nl_hr2rs calls transform_l_hr2rs ")
        self.transform_l_hr2rs(input_roi, output_roi, std_img, std_img_label)
    def transform_l_hr2rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat  = os.path.join(self.subject.roi_rs_dir, "hr2rs.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        fmri2rs_warp = os.path.join(self.subject.roi_rs_dir, "fmri2rs_warp")
        if imtest(fmri2rs_warp) is False:
            print("ERROR: transformation warp " + fmri2rs_warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.rs_examplefunc + " -o " + output_roi + " --warp=" + fmri2rs_warp)
    def transform_l_fmri2rs(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat  = os.path.join(self.subject.roi_rs_dir, "fmri2rs.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO FMRI (from hr, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_fmri_dir, std_img_label + "2fmri_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_fmri_dir, std_img_label + "2fmri.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.roi_fmri_dir + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_std42fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_fmri_dir, std_img_label + "42fmri_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std42fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_fmri_dir, std_img_label + "42fmri.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.fmri_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_hr2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
        std2fmri_mat  = os.path.join(self.subject.roi_fmri_dir, std_img_label + "2fmri.mat")

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + hr2std_warp + " --postmat=" + std2fmri_mat)
    def transform_l_hr2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat  = os.path.join(self.subject.roi_fmri_dir, "hr2fmri.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.fmri_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = self.subject.rs2fmri_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_rs2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat  = self.subject.fmri2rs_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD (from hr, rs, fmri, dti)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_hr2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + ".mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + "_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_rs2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + ".mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "fmri2" + std_img_label + "_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_fmri2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2" + std_img_label + ".mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_dti2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label + "_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_dti2std(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "dti2" + std_img_label + ".mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD4 (from hr, rs, fmri, std)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2std4(self, input_roi, output_roi, std_img, std_img_label="std"):
        return self.transform_l_std2std4(input_roi, output_roi, std_img, std_img_label)
    def transform_l_std2std4(self, input_roi, output_roi, std_img, std_img_label="std"):
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")

    def transform_nl_rs2std4(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "rs2" + std_img_label + "4_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_rs2std4(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "rs2" + std_img_label + "4.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2std4(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "rs2" + std_img_label + "4_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_fmri2std4(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "fmri2" + std_img_label + "4.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_hr2std4(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2" + std_img_label + "4_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_hr2std4(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2" + std_img_label + "4.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO DTI (from hr, t2, std)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2dti(self, input_roi, output_roi, std_img, std_img_label="std"):

        if self.subject.has_T2 is True and imtest(self.subject.hr2dti_warp) is True:
            if imtest(self.subject.hr2dti_warp) is False:
                print("ERROR: transformation warp " + self.subject.hr2dti_warp + " is missing...exiting transform roi")
                return ""

            rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + self.subject.hr2dti_warp)
        else:
            print("did not find the non linear registration from HR 2 DTI, I concat hr---(NL)--->std  with std ---(LIN)---> dti used a linear one")

            hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2" + std_img_label + "_warp")
            std2dti_mat = os.path.join(self.subject.roi_dti_dir, std_img_label + "2dti.mat")

            if imtest(hr2std_warp) is False:
                print("ERROR: transformation warp " + hr2std_warp + " is missing...exiting transform roi")
                return ""
            if os.path.exists(std2dti_mat) is False:
                print("ERROR: transformation matrix " + std2dti_mat + " is missing...exiting transform roi")
                return ""

            rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + hr2std_warp + " --postmat=" + std2dti_mat)
    def transform_l_hr2dti(self, input_roi, output_roi, std_img, std_img_label="std"):

        if os.path.exists(self.subject.hr2dti_mat) is False:
            print("ERROR: transformation matrix " + self.subject.hr2dti_mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + self.subject.hr2dti_mat + " -interp trilinear")

    def transform_nl_std2dti(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = os.path.join( self.subject.roi_dti_dir, std_img_label + "2dti_warp")
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nodif_brain") + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2dti(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = os.path.join( self.subject.roi_dti_dir, std_img_label + "2dti.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

        # ==============================================================================================================

    def transform_nl_t22dti(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = self.subject.t22dti_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_t22dti(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = self.subject.t22dti_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO T2 (from hr, dti)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2t2(self, input_roi, output_roi, std_img, std_img_label="std"):
        print("WARNING calling transform_l_hr2t2 instead of transform_nl_hr2t2")
        return self.transform_l_hr2t2(input_roi, output_roi, std_img, std_img_label)
    def transform_l_hr2t2(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = self.subject.hr2t2_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t2_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_dti2t2(self, input_roi, output_roi, std_img, std_img_label="std"):

        warp = self.subject.dti2t2_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_brain_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_dti2t2(self, input_roi, output_roi, std_img, std_img_label="std"):

        mat = self.subject.dti2t2_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t2_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # ==============================================================================================================


    # def transform_nl_rs2dti(self, input_roi, output_roi, std_img, epi_label="rs", std_img_label="std"):
    #     print("registration type: epi2dti NOT SUPPORTED...exiting")
    #     return ""
    #
    # def transform_l_rs2dti(self, input_roi, output_roi, std_img, epi_label="rs"):
    #     print("registration type: epi2dti NOT SUPPORTED...exiting")
    #     return ""

    # def transform_nl_fmri2dti(self, input_roi, output_roi, std_img, epi_label="rs", std_img_label="std"):
    #     print("registration type: epi2dti NOT SUPPORTED...exiting")
    #     return ""
    #
    # def transform_l_fmri2dti(self, input_roi, output_roi, std_img, epi_label="rs"):
    #     print("registration type: epi2dti NOT SUPPORTED...exiting")
    #     return ""

    # def transform_nl_dti2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")
    #
    # def transform_l_dti2fmri(self, input_roi, output_roi, std_img, std_img_label="std"):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")


    # def transform_nl_dti2rs(self, input_roi, output_roi, std_img, std_img_label="std"):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")
    #
    # def transform_l_dti2rs(self, input_roi, output_roi, std_img, std_img_label="std"):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")