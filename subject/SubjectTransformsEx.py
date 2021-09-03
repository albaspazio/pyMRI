import os

from myfsl.utils.run import rrun
from utility.fslfun import runsystem
from utility.images import imtest, imcp, imgname, remove_ext, read_header



# Class contains all the available transformations across different sequences.

# it has 50 properties listing all the transformation
#    - 26 linear
#    - 24 non-linear
#
#    -  4 transformations does not need a property as they involve moving between std & std4 through flirt -applyisoxfm)
#    -  6 non-linear transformation does not exist and code returns their linear transformation
#
# 5 methods to calculate transf relating to t1, rs, fmri, dti and t2 (the latter used to better connect to t1)
# one method to transform a list of images from one space to the other
#       it calls 60 primitives (6 non-linear returns the linear version, 4 involve moving between std & std4)
#   RS    <-----2/4-----> HR <-4/4> STD  <--0/2-> STD4
#    |    <----------> HR <--------------> STD4
#    |
#   FMRI  <----------> HR <---> STD
#   FMRI  <----------> HR <--------------> STD4
#
#   DTI   <----------> HR <---> STD
#   DTI   <--> T2 <--> HR <---> STD
#
class SubjectTransformsEx:

    def __init__(self, subject, _global):
        
        self.subject = subject
        self._global = _global

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO HR (from std, std4, rs, fmri, dti, t2)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.std2hr_warp    = os.path.join(self.subject.roi_t1_dir, "std2hr_warp")
        self.std2hr_mat     = os.path.join(self.subject.roi_t1_dir, "std2hr.mat")

        self.std42hr_warp   = os.path.join(self.subject.roi_t1_dir, "std42hr_warp")
        self.std42hr_mat    = os.path.join(self.subject.roi_t1_dir, "std42hr.mat")

        #self.rs2hr_warp does not exist
        self.rs2hr_mat      = os.path.join(self.subject.roi_t1_dir, "rs2hr.mat")

        #self.fmri2hr_warp does not exist
        self.fmri2hr_mat    = os.path.join(self.subject.roi_t1_dir, "fmri2hr.mat")

        self.dti2hr_warp      = os.path.join(self.subject.roi_t1_dir, "dti2hr_warp")    # when t2 is available
        self.dti2hr_mat       = os.path.join(self.subject.roi_t1_dir, "dti2hr.mat")

        #self.t22hr_warp  does not exist
        self.t22hr_mat      = os.path.join(self.subject.roi_t1_dir, "t22hr.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO RS (from hr, fmri, std, std4)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.std2rs_warp    = os.path.join(self.subject.roi_rs_dir, "std2rs_warp")
        self.std2rs_mat     = os.path.join(self.subject.roi_rs_dir, "std2rs.mat")

        self.std42rs_warp   = os.path.join(self.subject.roi_rs_dir, "std42rs_warp")
        self.std42rs_mat     = os.path.join(self.subject.roi_rs_dir, "std42rs.mat")

        # self.hr2rs_warp does not exist
        self.hr2rs_mat       = os.path.join(self.subject.roi_rs_dir, "hr2rs.mat")

        self.fmri2rs_warp   = os.path.join(self.subject.roi_rs_dir, "fmri2rs_warp") # passing from hr and std
        self.fmri2rs_mat    = os.path.join(self.subject.roi_rs_dir, "fmri2rs.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO FMRI (from std, std4, hr, rs)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.std2fmri_warp     = os.path.join(self.subject.roi_fmri_dir, "std2fmri_warp")
        self.std2fmri_mat       = os.path.join(self.subject.roi_fmri_dir, "std2fmri.mat")

        self.std42fmri_warp    = os.path.join(self.subject.roi_fmri_dir, "std42fmri_warp")
        self.std42fmri_mat     = os.path.join(self.subject.roi_fmri_dir, "std42fmri.mat")

        # self.hr2fmri_warp does not exist
        self.hr2fmri_mat       = os.path.join(self.subject.roi_fmri_dir, "hr2fmri.mat")

        self.rs2fmri_warp    = os.path.join(self.subject.roi_fmri_dir, "rs2fmri_warp")  # passing from hr and std
        self.rs2fmri_mat     = os.path.join(self.subject.roi_fmri_dir, "rs2fmri.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO STD (from std4, hr, rs, fmri, dti, t2)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #self.std42std_warp does not exist
        #self.std42std_mat  does not exist

        self.hr2std_warp    = os.path.join(self.subject.roi_std_dir, "hr2std_warp")
        self.hr2std_mat     = os.path.join(self.subject.roi_std_dir, "hr2std.mat")

        self.rs2std_warp    = os.path.join(self.subject.roi_std_dir, "rs2std_warp")
        self.rs2std_mat     = os.path.join(self.subject.roi_std_dir, "rs2std.mat")

        self.fmri2std_warp  = os.path.join(self.subject.roi_std_dir, "fmri2std_warp")
        self.fmri2std_mat   = os.path.join(self.subject.roi_std_dir, "fmri2std.mat")

        self.dti2std_warp   = os.path.join(self.subject.roi_std_dir, "dti2std_warp")
        self.dti2std_mat    = os.path.join(self.subject.roi_std_dir, "dti2std.mat")

        self.t22std_warp    = os.path.join(self.subject.roi_std_dir, "t22std_warp")
        self.t22std_mat     = os.path.join(self.subject.roi_std_dir, "t22std.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO STD4 (from std, hr, rs, fmri)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #self.std2std4_warp does not exist
        #self.std2std4_mat   does not exist

        self.hr2std4_warp = os.path.join(self.subject.roi_std4_dir, "hr2std4_warp")
        self.hr2std4_mat = os.path.join(self.subject.roi_std4_dir, "hr2std4.mat")

        self.rs2std4_warp   = os.path.join(self.subject.roi_std4_dir, "rs2std4_warp")
        self.rs2std4_mat     = os.path.join(self.subject.roi_std4_dir, "rs2std4.mat")

        self.fmri2std4_warp    = os.path.join(self.subject.roi_std4_dir, "fmri2std4_warp")
        self.fmri2std4_mat     = os.path.join(self.subject.roi_std4_dir, "fmri2std4.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO DTI (from std, hr, t2)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.std2dti_warp     = os.path.join(self.subject.roi_dti_dir, "std2dti_warp")
        self.std2dti_mat      = os.path.join(self.subject.roi_dti_dir, "std2dti.mat")

        self.hr2dti_warp      = os.path.join(self.subject.roi_dti_dir, "hr2dti_warp")
        self.hr2dti_mat       = os.path.join(self.subject.roi_dti_dir, "hr2dti.mat")

        self.t22dti_warp      = os.path.join(self.subject.roi_dti_dir, "t22dti_warp")
        self.t22dti_mat       = os.path.join(self.subject.roi_dti_dir, "t22dti.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO T2 (from std, hr, dti)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.std2t2_warp     = os.path.join(self.subject.roi_t2_dir, "std2t2_warp")
        self.std2t2_mat      = os.path.join(self.subject.roi_t2_dir, "std2t2.mat")

        # self.hr2t2_warp does not exist
        self.hr2t2_mat    = os.path.join(self.subject.roi_t2_dir, "hr2t2.mat")

        self.dti2t2_warp      = os.path.join(self.subject.roi_t2_dir, "dti2t2_warp")
        self.dti2t2_mat       = os.path.join(self.subject.roi_t2_dir, "dti2t2.mat")

        # ------------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------------
        # define all available transformations (30 + 30) 8 non-l, returns the l version
        self.linear_registration_type = {
            "stdTOhr": self.transform_l_std2hr,
            "std4TOhr": self.transform_l_std42hr,
            "rsTOhr": self.transform_l_rs2hr,
            "fmriTOhr": self.transform_l_fmri2hr,
            "dtiTOhr": self.transform_l_dti2hr,
            "t2TOhr": self.transform_l_t22hr,

            "stdTOrs": self.transform_l_std2rs,
            "std4TOrs": self.transform_l_std42rs,
            "hrTOrs": self.transform_l_hr2rs,
            "fmriTOrs": self.transform_l_fmri2rs,

            "stdTOfmri": self.transform_l_std2fmri,
            "std4TOfmri": self.transform_l_std42fmri,
            "hrTOfmri": self.transform_l_hr2fmri,
            "rsTOfmri": self.transform_l_rs2fmri,

            "std4TOstd": self.transform_l_std2std4,
            "hrTOstd": self.transform_l_hr2std,
            "rsTOstd": self.transform_l_rs2std,
            "fmriTOstd": self.transform_l_fmri2std,
            "dtiTOstd": self.transform_l_dti2std,
            "t2TOstd": self.transform_l_t22dti,

            "stdTOstd4": self.transform_l_std2std4,
            "hrTOstd4": self.transform_l_hr2std4,
            "rsTOstd4": self.transform_l_rs2std4,
            "fmriTOstd4": self.transform_l_fmri2std4,

            "stdTOdti": self.transform_l_std2dti,
            "hrTOdti": self.transform_l_hr2dti,
            "t2TOdti": self.transform_l_hr2dti,

            "stdTOt2": self.transform_l_hr2t2,
            "hrTOt2": self.transform_l_hr2t2,
            "dtiTOt2": self.transform_l_dti2t2
        }

        self.non_linear_registration_type = {
            "stdTOhr": self.transform_nl_std2hr,
            "std4TOhr": self.transform_nl_std42hr,
            "rsTOhr": self.transform_nl_rs2hr,
            "fmriTOhr": self.transform_nl_fmri2hr,
            "dtiTOhr": self.transform_nl_dti2hr,
            "t2TOhr": self.transform_nl_t22hr,

            "stdTOrs": self.transform_nl_std2rs,
            "std4TOrs": self.transform_nl_std42rs,
            "hrTOrs": self.transform_nl_hr2rs,
            "fmriTOrs": self.transform_nl_fmri2rs,

            "stdTOfmri": self.transform_nl_std2fmri,
            "std4TOfmri": self.transform_nl_std42fmri,
            "hrTOfmri": self.transform_nl_hr2fmri,
            "rsTOfmri": self.transform_nl_rs2fmri,

            "std4TOstd": self.transform_nl_std2std4,
            "hrTOstd": self.transform_nl_hr2std,
            "rsTOstd": self.transform_nl_rs2std,
            "fmriTOstd": self.transform_nl_fmri2std,
            "dtiTOstd": self.transform_nl_dti2std,
            "t2TOstd": self.transform_nl_t22dti,

            "stdTOstd4": self.transform_nl_std2std4,
            "hrTOstd4": self.transform_nl_hr2std4,
            "rsTOstd4": self.transform_nl_rs2std4,
            "fmriTOstd4": self.transform_nl_fmri2std4,

            "stdTOdti": self.transform_nl_std2dti,
            "hrTOdti": self.transform_nl_hr2dti,
            "t2TOdti": self.transform_nl_hr2dti,

            "stdTOt2": self.transform_nl_hr2t2,
            "hrTOt2": self.transform_nl_hr2t2,
            "dtiTOt2": self.transform_nl_dti2t2
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
    # it creates (8) :  hr2std_mat,  std2hr_mat,  hr2std_warp,  std2hr_warp,            hrhead2std.mat
    #                   hr2std4_mat, std42hr_mat, hr2std4_warp, std42hr_warp,           hrhead2std4.mat
    def transform_mpr(self, logFile=None):

        hrhead2std      = os.path.join(self.subject.roi_std_dir,  "hrhead2" + self.subject.std_img_label)
        hrhead2std4     = os.path.join(self.subject.roi_std4_dir, "hrhead2" + self.subject.std_img_label + "4")

        process_std4 = True

        if imtest(self.subject.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.t1_data) is False:
            print("file T1_DATA: " + self.subject.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        # check template
        if imtest(self.subject.std_img) is False:
            print("ERROR: file std_img: " + self.subject.std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_head_img) is False:
            print("ERROR: file std_head_img: " + self.subject.std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_img_mask_dil) is False:
            print("ERROR: file STD_IMAGE_MASK: " + self.subject.std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std4_img) is False:
            print("WARNING: file std_img: " + self.subject.std4_img + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        if imtest(self.subject.std4_head_img) is False:
            print("WARNING: file std4_img: " + self.subject.std4_img + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        if imtest(self.subject.std4_img_mask_dil) is False:
            print("WARNING: file STD_IMAGE_MASK: " + self.subject.std4_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")
            process_std4 = False

        print(self.subject.label + " :STARTED transform_mpr")

        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + self.subject.std_img_label), exist_ok=True)
        os.makedirs(self.subject.roi_t1_dir, exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # HIGHRES <--------> STANDARD
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => hr2{std}.mat
        if os.path.isfile(self.hr2std_mat) is False:
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + self.subject.std_img + " -omat " + self.hr2std_mat + " -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2{std}.mat
        if os.path.isfile(hrhead2std + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + self.subject.std_img + " -omat " + hrhead2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => {std}2hr.mat
        if os.path.isfile(self.std2hr_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.std2hr_mat + " " + self.hr2std_mat)

        # NON LINEAR
        # => hr2{std}_warp
        if imtest(self.hr2std_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std + ".mat --config=" + self._global.fsl_std_mni_2mm_cnf +
                    " --ref=" + self.subject.std_head_img + " --refmask=" + self.subject.std_img_mask_dil + " --warpres=10,10,10" +
                    " --cout=" + self.hr2std_warp + " --iout=" + self.hr2std_mat)

        # => {std}2hr_warp
        if imtest(self.std2hr_warp) is False:
            rrun("invwarp -r " + self.subject.t1_data + " -w " + self.hr2std_warp + " -o " + self.std2hr_warp)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # HIGHRES <--------> STANDARD4
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if process_std4 is False:
            return

        os.makedirs(self.subject.roi_std4_dir, exist_ok=True)
        # => hr2{std}4.mat
        if os.path.isfile(self.hr2std4_mat) is False:
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + self.subject.std4_img + " -omat " + self.hr2std4_mat + " -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2{std}4.mat
        if os.path.isfile(hrhead2std4 + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + self.subject.std4_head_img + " -omat " + hrhead2std4 + ".mat" + " -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => {std}42hr.mat
        if os.path.isfile(self.std42hr_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.std42hr_mat + " " + self.hr2std4_mat)

        # NON LINEAR
        # => hr2{std}4_warp
        if imtest(self.hr2std4_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std4 + ".mat  --config=" + self._global.fsl_std_mni_4mm_cnf +
                 " --ref=" + self.subject.std4_head_img + " --refmask=" + self.subject.std4_img_mask_dil + " --warpres=10,10,10" + " --cout=" + self.hr2std4_warp)

        # => {std}42hr_warp
        if imtest(self.std42hr_warp) is False:
            rrun("invwarp -r " + self.subject.t1_data + " -w " + self.hr2std4_warp + " -o " + self.std42hr_warp)

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate all the transforms involved in EPI processing.
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # (17/7/21) bbr co-registration fails!!!
    # it creates (10) : example_func, rs2hr_mat , hr2rs_mat , rs2std_mat , std2rs_mat , rs2std4_mat , std42rs_mat
    #                                 rs2std_warp, std2rs_warp, rs2std4_warp, std42rs_warp
    def transform_rs(self, do_bbr=False, wmseg="", logFile=None):

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
        if imtest(self.subject.std_img) is False:
            print("ERROR: file std_img: " + self.subject.std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_head_img) is False:
            print("ERROR: file std_img: " + self.subject.std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_img_mask_dil) is False:
            print("ERROR: file std_img_mask_dil: " + self.subject.std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std4_img) is False:
            print("WARNING: file std4_img: " + self.subject.std4_img + ".nii.gz is not present...skipping STD4 transform")

        if imtest(self.subject.std4_head_img) is False:
            print("WARNING: file std4_head_img: " + self.subject.std4_head_img + ".nii.gz is not present...skipping STD4 transform")

        if imtest(self.subject.std4_img_mask_dil) is False:
            print("WARNING: file std4_img_mask_dil: " + self.subject.std4_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # check or create example function
        exfun = self.subject.epi.get_example_function(logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  EPI <--> HIGHRES (linear, bbr or not)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            rrun("flirt -ref " + self.subject.t1_brain_data + " -in " + exfun + " -dof 6 -omat " + "init_" + self.rs2hr_mat, logFile=logFile)

            if imtest(wmseg) is False:
                print("Running FAST segmentation for subj " + self.subject.label)
                temp_dir = os.path.join(self.subject.roi_t1_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.subject.t1_brain_data), logFile=logFile)
                rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + wmseg, logFile=logFile)
                runsystem("rm -rf " + temp_dir, logFile=logFile)

            if os.path.isfile(self.rs2hr_mat) is False:
                rrun("flirt -ref " + self.subject.t1_brain_data + " -in " + exfun + " -dof 6 -cost bbr -wmseg " + wmseg + " -init " + "init_" + self.rs2hr_mat + " -omat " + self.rs2hr_mat + " -schedule " + os.path.join(self.subject.fsl_dir, "etc", "flirtsch", "bbr.sch"), logFile=logFile)

            runsystem("rm " + "init_" + self.rs2hr_mat, logFile=logFile)
        else:
            # NOT BBR
            if os.path.isfile(self.rs2hr_mat) is False:
                rrun("flirt -in " + exfun + " -ref " + self.subject.t1_brain_data + " -omat " + self.rs2hr_mat + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear", logFile=logFile)

        if os.path.isfile(self.hr2rs_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.hr2rs_mat + " " + self.rs2hr_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => rs2std.mat (as concat)
        if os.path.isfile(self.rs2std_mat) is False:
            rrun("convert_xfm -concat " + self.hr2std_mat + " " + self.rs2hr_mat + " -omat " + self.rs2std_mat, logFile=logFile)

        # => std2rs.mat
        if os.path.exists(self.std2rs_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.std2rs_mat + " " + self.rs2std_mat)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.rs2std_warp) is False:
            rrun("convertwarp --ref=" + self.subject.std_head_img + " --premat=" + self.rs2hr_mat + " --warp1=" + self.hr2std_warp + " --out=" + self.rs2std_warp, logFile=logFile)

        # invwarp: standard -> highres -> epi
        if imtest(self.std2rs_warp) is False:
            rrun("invwarp -r " + exfun + " -w " + self.rs2std_warp + " -o " + self.std2rs_warp, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <-> STANDARD4    (epi2hr + hr2std4_warp)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.rs2std4_warp) is False:
            rrun("convertwarp --ref=" + self.subject.std4_head_img + " --premat=" + self.rs2hr_mat + " --warp1=" + self.hr2std4_warp + " --out=" + self.rs2std4_warp, logFile=logFile)

        # => epi2std4.mat
        if os.path.isfile(self.rs2std4_mat) is False:
            rrun("convert_xfm -concat " + self.hr2std4_mat + " " + self.rs2hr_mat + " -omat " + self.rs2std4_mat, logFile=logFile)

        if imtest(self.std42rs_warp) is False:
            rrun("invwarp -r " + exfun + " -w " + self.rs2std4_warp + " -o " + self.std42rs_warp, logFile=logFile)

        # => std42epi.mat
        if os.path.exists(self.std42rs_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.std42rs_mat + " " + self.rs2std4_mat)

        # ------------------------------------------------------------------------------------------------------
        # various co-registration
        # ------------------------------------------------------------------------------------------------------
        # coregister fast-highres to epi
        if imtest(os.path.join(self.subject.roi_rs_dir, "t1_wm_rs")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_wm") + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + self.hr2rs_mat + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_wm_rs"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_rs_dir, "t1_csf_rs")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_csf") + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + self.hr2rs_mat + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_csf_rs"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_rs_dir, "t1_gm_rs")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_gm") + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + self.hr2rs_mat + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_gm_rs"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_rs_dir, "t1_brain_rs")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, self.subject.t1_brain_data) + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + self.hr2rs_mat + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_brain_rs"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, self.subject.t1_brain_data_mask) + " -ref " + self.subject.rs_examplefunc + " -applyxfm -init " + self.hr2rs_mat + " -out " + os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs"), logFile=logFile)

        # mask & binarize
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_gm_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_gm_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_wm_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_wm_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_csf_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_csf_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_brain_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"), logFile=logFile)

    # it creates (12) : example_func, fmri2hr_mat , hr2fmri_mat , fmri2std_mat , std2fmri_mat , fmri2std4_mat , std42fmri_mat
    #                               fmri2hr_warp, hr2fmri_warp, fmri2std_warp, std2fmri_warp, fmri2std4_warp, std42fmri_warp
    def transform_fmri(self, do_bbr=False, wmseg="", logFile=None):

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
        if imtest(self.subject.std_img) is False:
            print("ERROR: file std_img: " + self.subject.std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_head_img) is False:
            print("ERROR: file std_img: " + self.subject.std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_img_mask_dil) is False:
            print("ERROR: file std_img_mask_dil: " + self.subject.std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std4_img) is False:
            print("WARNING: file std4_img: " + self.subject.std4_img + ".nii.gz is not present...skipping STD4 transform")

        if imtest(self.subject.std4_head_img) is False:
            print("WARNING: file std4_head_img: " + self.subject.std4_head_img + ".nii.gz is not present...skipping STD4 transform")

        if imtest(self.subject.std4_img_mask_dil) is False:
            print("WARNING: file std4_img_mask_dil: " + self.subject.std4_img_mask_dil + ".nii.gz is not present...skipping STD4 transform")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # check or create example function
        exfun = self.subject.epi.get_example_function(seq="fmri", logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  EPI <--> HIGHRES (linear, bbr or not)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            rrun("flirt -ref " + self.subject.t1_brain_data + " -in " + exfun + " -dof 6 -omat " + "init_" + self.fmri2hr_mat, logFile=logFile)

            if imtest(wmseg) is False:
                print("Running FAST segmentation for subj " + self.subject.label)
                temp_dir = os.path.join(self.subject.roi_t1_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.subject.t1_brain_data), logFile=logFile)
                rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + wmseg, logFile=logFile)
                runsystem("rm -rf " + temp_dir, logFile=logFile)

            # => epi2hr.mat
            if os.path.isfile(self.fmri2hr_mat) is False:
                rrun("flirt -ref " + self.subject.t1_brain_data + " -in " + exfun + " -dof 6 -cost bbr -wmseg " + wmseg + " -init " + "init_" + self.fmri2hr_mat + " -omat " + self.fmri2hr_mat + " -schedule " + os.path.join(self.subject.fsl_dir, "etc", "flirtsch", "bbr.sch"), logFile=logFile)

            runsystem("rm " + "init_" + self.fmri2hr_mat, logFile=logFile)
        else:
            # NOT BBR
            if os.path.isfile(self.fmri2hr_mat) is False:
                rrun("flirt -in " + exfun + " -ref " + self.subject.t1_brain_data + " -omat " + self.fmri2hr_mat + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear", logFile=logFile)

        if os.path.isfile(self.hr2fmri_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.hr2fmri_mat + " " + self.fmri2hr_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => fmri2std.mat (as concat)
        if os.path.isfile(self.fmri2std_mat) is False:
            rrun("convert_xfm -concat " + self.hr2std_mat + " " + self.fmri2hr_mat + " -omat " + self.fmri2std_mat, logFile=logFile)

        # => std2fmri.mat
        if os.path.exists(self.std2fmri_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.std2fmri_mat + " " + self.fmri2std_mat)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.fmri2std_warp) is False:
            rrun("convertwarp --ref=" + self.subject.std_head_img + " --premat=" + self.fmri2hr_mat + " --warp1=" + self.hr2std_warp + " --out=" + self.fmri2std_warp, logFile=logFile)

        # invwarp: standard -> highres -> epi
        if imtest(self.std2fmri_warp) is False:
            rrun("invwarp -r " + exfun + " -w " + self.fmri2std_warp + " -o " + self.std2fmri_warp, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <-> STANDARD4    (fmri2hr + hr2std4_warp)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.fmri2std4_warp) is False:
            rrun("convertwarp --ref=" + self.subject.std4_head_img + " --premat=" + self.fmri2hr_mat + " --warp1=" + self.hr2std4_warp + " --out=" + self.fmri2std4_warp, logFile=logFile)

        # => epi2std4.mat
        if os.path.isfile(self.fmri2std4_mat) is False:
            rrun("convert_xfm -concat " + self.hr2std4_mat + " " + self.fmri2hr_mat + " -omat " + self.fmri2std4_mat, logFile=logFile)

        if imtest(self.std42fmri_warp) is False:
            rrun("invwarp -r " + exfun + " -w " + self.fmri2std4_warp + " -o " + self.std42fmri_warp, logFile=logFile)

        # => std42epi.mat
        if os.path.exists(self.std42fmri_mat) is False:
            rrun("convert_xfm -inverse -omat " + self.std42fmri_mat + " " + self.fmri2std4_mat)

        # ------------------------------------------------------------------------------------------------------
        # various co-registration
        # ------------------------------------------------------------------------------------------------------
        # coregister fast-highres to epi
        if imtest(os.path.join(self.subject.roi_fmri_dir, "t1_wm_fmri")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_wm") + " -ref " + self.subject.fmri_examplefunc + " -applyxfm -init " + self.hr2fmri_mat + " -out " + os.path.join(self.subject.roi_fmri_dir, "t1_wm_fmri"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_fmri_dir, "t1_csf_fmri")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_csf") + " -ref " + self.subject.fmri_examplefunc + " -applyxfm -init " + self.hr2fmri_mat + " -out " + os.path.join(self.subject.roi_fmri_dir, "t1_csf_fmri"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_fmri_dir, "t1_gm_fmri")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, "mask_t1_gm") + " -ref " + self.subject.fmri_examplefunc + " -applyxfm -init " + self.hr2fmri_mat + " -out " + os.path.join(self.subject.roi_fmri_dir, "t1_gm_fmri"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_fmri_dir, "t1_brain_fmri")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, self.subject.t1_brain_data) + " -ref " + self.subject.fmri_examplefunc + " -applyxfm -init " + self.hr2fmri_mat + " -out " + os.path.join(self.subject.roi_fmri_dir, "t1_brain_fmri"), logFile=logFile)

        if imtest(os.path.join(self.subject.roi_fmri_dir, "t1_brain_mask_fmri")) is False:
            rrun("flirt -in " + os.path.join(self.subject.roi_t1_dir, self.subject.t1_brain_data_mask) + " -ref " + self.subject.fmri_examplefunc + " -applyxfm -init " + self.hr2fmri_mat + " -out " + os.path.join(self.subject.roi_fmri_dir, "t1_brain_mask_fmri"), logFile=logFile)

        # mask & binarize
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_gm_fmri") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_gm_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_wm_fmri") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_wm_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_csf_fmri") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_csf_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_brain_fmri") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"), logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_brain_mask_fmri") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"), logFile=logFile)

    # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
    # creates  (16) :   dti2hr.mat, hr2dti.mat,     dti2std_warp, std2dti_warp  , dti2std_mat, std2dti_mat
    # and if has_T2 :   dti2t2.mat, t22dti.mat,     dti2t2_warp,  t22dti_warp   , t22hr.mat, hr2t2.mat,     t22std_warp,  std2t2_warp
    #                   dti2hr_warp, hr2dti_warp,
    #                   overwrites dti2std_warp, std2dti_warp
    def transform_dti_t2(self, logFile=None):

        if imtest(self.subject.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.t1_data) is False:
            print("file T1_DATA: " + self.subject.t1_data + ".nii.gz is not present...exiting transforms_mpr")
            return

        # check template
        if imtest(self.subject.std_img) is False:
            print("ERROR: file std_img: " + self.subject.std_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_head_img) is False:
            print("ERROR: file std_img: " + self.subject.std_head_img + ".nii.gz is not present...exiting transforms_mpr")
            return

        if imtest(self.subject.std_img_mask_dil) is False:
            print("ERROR: file std_img_mask_dil: " + self.subject.std_img_mask_dil + ".nii.gz is not present...exiting transforms_mpr")
            return

        print(self.subject.label + ":						STARTED : nonlin nodiff-t1-standard coregistration")
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.subject.dti.get_nodiff()

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <------> HIGHRES (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if os.path.exists(self.dti2hr_mat) is False:
            rrun("flirt -in " + self.subject.dti_nodiff_data + "_brain" + " -ref " + self.subject.t1_brain_data + " -omat " + self.dti2hr_mat +
                " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear", logFile=logFile)

        if os.path.exists(self.dti2hr_mat) is False:
            rrun("convert_xfm -omat " + self.dti2hr_mat + " -inverse " + self.dti2hr_mat, logFile=logFile)

        if self.subject.hasT2 is False:

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if imtest(self.dti2std_warp) is False:
                rrun("convertwarp --ref=" + self.subject.std_head_img + " --premat=" + self.dti2hr_mat + " --warp1=" + self.hr2std_warp + " --out=" + self.dti2std_warp, logFile=logFile)

            if os.path.exists(self.dti2std_mat) is False:
                rrun("convert_xfm -omat " + self.dti2std_mat + " -concat " + self.dti2hr_mat + " " + self.hr2std_mat, logFile=logFile)

            if imtest(self.std2dti_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data  + " -w " + self.dti2std_warp + " -o " + self.std2dti_warp, logFile=logFile)

            if os.path.exists(self.std2dti_mat) is False:
                rrun("convert_xfm -omat " + self.std2dti_mat + " -inverse " + self.dti2std_mat)

        else:
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <--->  T2  linear and non-linear
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 -> dti
            # linear
            if os.path.exists(self.t22dti_mat) is False:
                rrun("flirt -in " + self.subject.t2_brain_data + " -ref " + self.subject.dti_nodiff_brain_data + " -omat " + self.t22dti_mat +
                    " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)
            # non-linear
            if imtest(self.t22dti_warp) is False:
                rrun("fnirt --in=" + self.subject.t2_data + " --ref=" + self.subject.dti_nodiff_data + " --aff=" + self.t22dti_mat + " --cout=" + self.t22dti_warp, logFile=logFile)

            # dti -> t2
            # linear
            if os.path.exists(self.dti2t2_mat) is False:
                rrun("convert_xfm -omat " + self.dti2t2_mat + " -inverse " + self.t22dti_mat,
                     logFile=logFile)
            # non-linear
            if imtest(self.dti2t2_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.t22dti_warp + " -o " + self.dti2t2_warp, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # T2 <------> HIGHRES (linear)
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 -> hr linear
            if os.path.exists(self.t22hr_mat) is False:
                rrun("flirt -in " + self.subject.t2_brain_data + " -ref " + self.subject.t1_brain_data + " -omat " + self.t22hr_mat +
                    " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear",
                    logFile=logFile)

            # hr -> t2 linear
            if os.path.exists(self.hr2t2_mat) is False:
                rrun("convert_xfm -omat " + self.hr2t2_mat + " -inverse " + self.t22hr_mat, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if imtest(self.dti2hr_warp) is False:
                rrun("convertwarp --ref=" + self.subject.t1_data + " --warp1=" + self.dti2t2_warp + " --postmat=" + self.t22hr_mat + " --out=" + self.dti2hr_warp, logFile=logFile)

            if imtest(self.hr2dti_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.dti2hr_warp + " -o " + self.hr2dti_warp, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES -- (non-lin) --> STANDARD
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if imtest(self.t22std_warp) is False:
                rrun("convertwarp --ref=" + self.subject.std_head_img + " --premat=" + self.t22hr_mat +" --warp1=" + self.hr2std_warp + " --out=" + self.dti2std_warp, logFile=logFile)

            if imtest(self.std2t2_warp) is False:
                rrun("invwarp -r " + self.subject.t2_data + " -w " + self.t22std_warp + " -o " + self.std2t2_warp, logFile=logFile)

            # overwrites
            if imtest(self.dti2std_warp) is False:
                rrun("convertwarp --ref=" + self.subject.std_head_img + " --warp1=" + self.dti2t2_warp + " --midmat=" + self.hr2t2_mat + " --warp2=" + self.hr2std_warp + " --out=" + self.dti2std_warp, logFile=logFile)

            if imtest(self.std2dti_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.dti2std_warp + " -o " + self.std2dti_warp, logFile=logFile)

    # it creates (4): rs2fmri_mat , fmri2rs_mat
    #                 rs2fmri_warp, fmri2rs_warp
    def transform_extra(self, logFile=None):

        if self.subject.hasFMRI and self.subject.hasRS:

            if os.path.isfile(self.rs2fmri_mat) is False:
                rrun("convert_xfm -concat " + self.rs2hr_mat + " " + self.hr2fmri_mat + " -omat " + self.rs2fmri_mat, logFile=logFile)

            if os.path.exists(self.fmri2rs_mat) is False:
                rrun("convert_xfm -inverse -omat " + self.fmri2rs_mat + " " + self.rs2fmri_mat)

            # non-linear   rs <--(hr)--> std <--(hr)--> fmri
            if imtest(self.rs2fmri_warp) is False:
                rrun("convertwarp --ref=" + self.subject.fmri_examplefunc + " --warp1=" + self.rs2std_warp + " --warp2=" + self.std2fmri_warp + " --out=" + self.rs2fmri_warp, logFile=logFile)

            if imtest(self.fmri2rs_warp) is False:
                rrun("invwarp -r " + self.subject.fmri_examplefunc + " -w " + self.rs2fmri_warp + " -o " + self.fmri2rs_warp, logFile=logFile)

    # this method takes base images (t1/t1_brain, epi_example_function, dti_nodiff/dti_nodiff_brain) and coregister to all other modalities and standard
    # creates up to 14 folders, 7 for linear and 7 for non linear transformation towards the 7 different space (hr, rs, frmi, dti, t2, std, std4)
    def test_all_coregistration(self, test_dir):

        nldir   = os.path.join(test_dir, "nlin")
        ldir    = os.path.join(test_dir, "lin")

        # --------------------------------------------------------------
        #  FROM HR <--> STD
        #       HR <--> STD4 if hasRS
        # --------------------------------------------------------------
        if self.subject.hasT1 is True:
        #
            nl_t1   = os.path.join(nldir, "hr"); nl_std  = os.path.join(nldir, self.subject.std_img_label); nl_std4 = os.path.join(nldir, self.subject.std_img_label + "4")
            l_t1    = os.path.join(ldir, "hr");   l_std  = os.path.join(ldir, self.subject.std_img_label);  l_std4  = os.path.join(ldir, self.subject.std_img_label + "4")

            os.makedirs(nl_t1, exist_ok=True);os.makedirs(nl_std, exist_ok=True);os.makedirs(nl_std4, exist_ok=True)
            os.makedirs(l_t1, exist_ok=True); os.makedirs(l_std, exist_ok=True); os.makedirs(l_std4, exist_ok=True)

            imcp(self.subject.t1_data,       os.path.join(nl_t1, self.subject.t1_image_label))
            imcp(self.subject.t1_brain_data, os.path.join(l_t1 , self.subject.t1_image_label + "_brain"))

            self.transform_roi("hrTOstd",    pathtype="abs", outdir=nl_std   , islin=False, rois=[self.subject.t1_data])
            self.transform_roi("hrTOstd",    pathtype="abs",  outdir=l_std   , islin=True,  rois=[self.subject.t1_brain_data])

            # self.transform_roi("stdTOhr",    pathtype="abs", outdir=nl_t1   , islin=False, rois=[std_head_img])
            # self.transform_roi("stdTOhr",    pathtype="abs",  outdir=l_t1   , islin=True,  rois=[std_img])

            if self.subject.hasRS is True:  # connect HR with STD4
                pass
                self.transform_roi("hrTOstd4", pathtype="abs", outdir=nl_std4, islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOstd4", pathtype="abs", outdir=l_std4, islin=True, rois=[self.subject.t1_brain_data])

                # self.transform_roi("std4TOhr", pathtype="abs", outdir=nl_t1, islin=False, rois=[std4_head_img])
                # self.transform_roi("std4TOhr", pathtype="abs", outdir=l_t1, islin=True, rois=[std4_img])
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
            self.transform_roi("rsTOhr",    pathtype="abs", outdir=nl_t1   , outname=self.subject.label + "_rs_examplefunc", islin=False,   rois=[exfun])
            self.transform_roi("rsTOhr",    pathtype="abs", outdir=l_t1    , outname=self.subject.label + "_rs_examplefunc", islin=True,    rois=[exfun])

            self.transform_roi("rsTOstd",   pathtype="abs", outdir=nl_std   , outname=self.subject.label + "_rs_examplefunc", islin=False,   rois=[exfun])
            self.transform_roi("rsTOstd",   pathtype="abs", outdir=l_std    , outname=self.subject.label + "_rs_examplefunc", islin=True,    rois=[exfun])
            # self.transform_roi("stdTOrs",   pathtype="abs", outdir=nl_rs   , islin=False,   rois=[std_head_img])
            # self.transform_roi("stdTOrs",   pathtype="abs", outdir=l_rs    , islin=True,    rois=[std_img])

            self.transform_roi("rsTOstd4",  pathtype="abs", outdir=nl_std4   , outname=self.subject.label + "_rs_examplefunc", islin=False,   rois=[exfun])
            self.transform_roi("rsTOstd4",  pathtype="abs", outdir=l_std4    , outname=self.subject.label + "_rs_examplefunc", islin=True,    rois=[exfun])
            # self.transform_roi("std4TOrs",  pathtype="abs", outdir=nl_rs   , islin=False,   rois=[std4_head_img])
            # self.transform_roi("std4TOrs",  pathtype="abs", outdir=l_rs    , islin=True,    rois=[std4_img])

            if self.subject.hasFMRI:    # connect RS with FMRI

                exfun_fmri = self.subject.epi.get_example_function("fmri")

                nl_fmri = os.path.join(nldir, "fmri")
                l_fmri = os.path.join(ldir, "fmri")

                os.makedirs(nl_fmri, exist_ok=True)
                os.makedirs(l_fmri, exist_ok=True)

                self.transform_roi("rsTOfmri", pathtype="abs", outdir=nl_fmri, outname=self.subject.label + "_rs_examplefunc", islin=False, rois=[exfun])
                self.transform_roi("rsTOfmri", pathtype="abs", outdir=l_fmri,  outname=self.subject.label + "_rs_examplefunc", islin=True,  rois=[exfun])

                self.transform_roi("fmriTOrs", pathtype="abs", outdir=nl_rs,   outname=self.subject.label + "_fmri_examplefunc", islin=False, rois=[exfun_fmri])
                self.transform_roi("fmriTOrs", pathtype="abs", outdir=l_rs,    outname=self.subject.label + "_fmri_examplefunc", islin=True,  rois=[exfun_fmri])

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

            imcp(exfun, os.path.join(nl_fmri, self.subject.label + "_example_func"))
            imcp(exfun, os.path.join(l_fmri,  self.subject.label + "_example_func"))

            self.transform_roi("fmriTOhr", pathtype="abs", outdir=nl_t1, outname=self.subject.label + "_fmri_example_func", islin=False,    rois=[exfun])
            self.transform_roi("fmriTOhr", pathtype="abs", outdir=l_t1,  outname=self.subject.label + "_fmri_example_func", islin=True,     rois=[exfun])

            self.transform_roi("hrTOfmri", pathtype="abs", outdir=nl_fmri, islin=False,    rois=[self.subject.t1_brain_data])
            self.transform_roi("hrTOfmri", pathtype="abs", outdir=l_fmri,  islin=True,     rois=[self.subject.t1_data])

            self.transform_roi("fmriTOstd", pathtype="abs", outdir=nl_std, outname=self.subject.label + "_fmri_example_func", islin=False,   rois=[exfun])
            self.transform_roi("fmriTOstd", pathtype="abs", outdir=l_std,  outname=self.subject.label + "_fmri_example_func", islin=True,    rois=[exfun])

            # self.transform_roi("stdTOfmri", pathtype="abs", outdir=nl_fmri, islin=False,  rois=[std_head_img])
            # self.transform_roi("stdTOfmri", pathtype="abs", outdir=l_fmri, islin=True,    rois=[std_img])

            if self.subject.hasRS:

                self.transform_roi("fmriTOstd4", pathtype="abs", outdir=nl_std4, outname=self.subject.label + "_fmri_example_func", islin=False, rois=[exfun])
                self.transform_roi("fmriTOstd4", pathtype="abs", outdir=l_std4, outname=self.subject.label + "_fmri_example_func", islin=True,   rois=[exfun])

                # self.transform_roi("std4TOfmri", pathtype="abs", outdir=nl_fmri, islin=False, rois=[std4_head_img])
                # self.transform_roi("std4TOfmri", pathtype="abs", outdir=l_fmri, islin=True,   rois=[std4_img])

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

            # self.transform_roi("t2TOstd" , pathtype="abs",  outdir=nl_std , islin=False, rois=[self.subject.t2_data])
            # self.transform_roi("t2TOstd" , pathtype="abs",  outdir=l_std  , islin=True,  rois=[self.subject.t2_brain_data])
            #
            # self.transform_roi("stdTOt2" , pathtype="abs",  outdir=nl_t2  , islin=False, rois=[std_head_img])
            # self.transform_roi("stdTOt2" , pathtype="abs",  outdir=l_t2   , islin=True,  rois=[std_img])

        # --------------------------------------------------------------
        #  FROM DTI <--> HR
        #       DTI <--> STD
        #       DTI <--> T2 if hasT2
        # --------------------------------------------------------------
        if self.subject.hasDTI is True:

            nl_dti = os.path.join(nldir, "dti")
            l_dti  = os.path.join(ldir, "dti")

            os.makedirs(nl_dti, exist_ok=True)
            os.makedirs(l_dti,  exist_ok=True)

            imcp(self.subject.dti_nodiff_data,       os.path.join(nl_dti, self.subject.label + "_nodif"))
            imcp(self.subject.dti_nodiff_brain_data, os.path.join(l_dti , self.subject.label + "_nodif_brain"))

            self.transform_roi("hrTOdti"  , pathtype="abs",  outdir=nl_dti , islin=False, rois=[self.subject.t1_data])
            self.transform_roi("hrTOdti"  , pathtype="abs",  outdir=l_dti  , islin=True,  rois=[self.subject.t1_brain_data])
            self.transform_roi("dtiTOhr"  , pathtype="abs",  outdir=nl_t1  , outname=self.subject.label + "_nodif_data", islin=False, rois=[self.subject.dti_nodiff_data])
            self.transform_roi("dtiTOhr"  , pathtype="abs",  outdir=l_t1   , outname=self.subject.label + "_nodif_brain_data", islin=True,  rois=[self.subject.dti_nodiff_brain_data])

            self.transform_roi("dtiTOstd" , pathtype="abs",  outdir=nl_std , outname=self.subject.label + "_nodif_data", islin=False, rois=[self.subject.dti_nodiff_data])
            self.transform_roi("dtiTOstd" , pathtype="abs",  outdir=l_std  , outname=self.subject.label + "_nodif_brain_data", islin=True,  rois=[self.subject.dti_nodiff_brain_data])
            # self.transform_roi("stdTOdti" , pathtype="abs",  outdir=nl_dti , islin=False, rois=[std_head_img])
            # self.transform_roi("stdTOdti" , pathtype="abs",  outdir=l_dti  , islin=True,  rois=[std_img])

            if self.subject.hasT2 is True:
                self.transform_roi("t2TOdti", pathtype="abs", outdir=nl_dti, islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOdti", pathtype="abs", outdir=l_dti, islin=True, rois=[self.subject.t2_brain_data])
                self.transform_roi("dtiTOt2", pathtype="abs", outdir=nl_t2, outname=self.subject.label + "_nodif_data", islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOt2", pathtype="abs", outdir=l_t2, outname=self.subject.label + "_nodif_brain_data", islin=True, rois=[self.subject.dti_nodiff_brain_data])

    # open fsleyes with all sequence coregistered to given seq = [t1, t2, dti, rs, fmri, std, std4]
    def view_space_images(self, seq):

        outdir = os.path.join(self.subject.roi_dir, "check_coregistration", seq)
        os.makedirs(outdir, exist_ok=True)

        if seq == "t1":
            if self.subject.hasFMRI:
                self.transform_roi("fmriTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                self.transform_roi("fmriTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasRS:
                self.transform_roi("rsTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                self.transform_roi("rsTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasDTI:
                self.transform_roi("dtiTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",          islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",       islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2:
                self.transform_roi("t2TOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",      islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin",   islin=True, rois=[self.subject.t2_brain_data])

            imcp(self.subject.t1_brain_data, outdir)

        elif seq == "t2":
            if self.subject.hasFMRI:
                self.transform_roi("fmriTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                self.transform_roi("fmriTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasRS:
                self.transform_roi("rsTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                self.transform_roi("rsTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasDTI:
                self.transform_roi("dtiTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",          islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",       islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT1:
                self.transform_roi("hrTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",      islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",   islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.t2_brain_data, outdir)

        elif seq == "dti":
            if self.subject.hasFMRI:
                self.transform_roi("fmriTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                self.transform_roi("fmriTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasRS:
                self.transform_roi("rsTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                self.transform_roi("rsTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasT2:
                self.transform_roi("t2TOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",    islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin", islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1:
                self.transform_roi("hrTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.dti_nodiff_brain_data, outdir)

        elif seq == "rs":
            if self.subject.hasFMRI:
                self.transform_roi("fmriTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                self.transform_roi("fmriTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasDTI:
                self.transform_roi("dtiTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",      islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",   islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2:
                self.transform_roi("t2TOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",    islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin", islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1:
                self.transform_roi("hrTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.rs_examplefunc, outdir)

        elif seq == "fmri":
            if self.subject.hasRS:
                self.transform_roi("rsTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                self.transform_roi("rsTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasDTI:
                self.transform_roi("dtiTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",    islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin", islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2:
                self.transform_roi("t2TOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",    islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin", islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1:
                self.transform_roi("hrTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.fmri_examplefunc, outdir)

        elif seq == "std":
            if self.subject.hasRS:
                self.transform_roi("rsTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin",    islin=False, rois=[self.subject.rs_examplefunc])
                self.transform_roi("rsTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",       islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasFMRI:
                self.transform_roi("fmriTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                self.transform_roi("fmriTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasDTI:
                self.transform_roi("dtiTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",     islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",  islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2:
                self.transform_roi("t2TOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",     islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin",  islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1:
                self.transform_roi("hrTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.std_img, outdir)

        elif seq == "std4":
            if self.subject.hasRS:
                self.transform_roi("rsTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin",    islin=False, rois=[self.subject.rs_examplefunc])
                self.transform_roi("rsTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",       islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasFMRI:
                self.transform_roi("fmriTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                self.transform_roi("fmriTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasDTI:
                self.transform_roi("dtiTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",     islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",  islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2:
                self.transform_roi("t2TOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",     islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin",  islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1:
                self.transform_roi("hrTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.std4_img, outdir)

        rrun("fsleyes " + outdir + "/*.*", stop_on_error=False)

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
    def transform_roi(self, regtype, pathtype="standard", outdir="", outname="", mask="", orf="", thresh=0, islin=True, rois=[]):

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
        # if islin:
        #     if "std4" in regtype:
        #         std_img = self._global.fsl_std_mni_4mm_brain
        #     else:
        #         std_img = self._global.fsl_std_mni_2mm_brain
        # else:
        #     if "std4" in regtype:
        #         std_img = self._global.fsl_std_mni_4mm_head
        #     else:
        #         std_img = self._global.fsl_std_mni_2mm_head
        #
        # else:
        #
        #     if imtest(stdimg) is False:
        #         print("ERROR: given standard image file (" + stdimg + ") does not exist......exiting")
        #         return
        #
        #     imgdir              = os.path.dirname(stdimg)
        #     std_img_label       = remove_ext(os.path.basename(stdimg))  # "pediatric" with or without brain
        #     std_img_label       = std_img_label.replace("_brain", "")   # "pediatric" (without "_brain")
        #
        #     # check resolution
        #     res = read_header(stdimg, ["dx"])["dx"]
        #     if "std4" in regtype:
        #         if res != "4":
        #             print("ERROR: user pretended to make a transformation toward the std4 space but given template resolution does not match")
        #             return
        #     else:
        #         if "std" in regtype:
        #             if res != "2":
        #                 print("ERROR: user pretended to make a transformation toward the std space but given template resolution does not match")
        #                 return
        #
        #     if islin:
        #         if "std4" in regtype:
        #             std_img = os.path.join(imgdir, std_img_label + "4_brain")       # "pediatric4_brain"
        #         else:
        #             std_img = os.path.join(imgdir, std_img_label + "_brain")        # "pediatric_brain"
        #     else:
        #         if "std4" in regtype:
        #             std_img = os.path.join(imgdir, std_img_label + "4")             # "pediatric4"
        #         else:
        #             std_img = os.path.join(imgdir, std_img_label)                   # "pediatric"

        # ==============================================================================================================
        print("registration_type " + regtype + ", do_linear = " + str(islin))

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
                    input_roi = os.path.join(self.subject.roi_t1_dir, roi_name)
                elif from_space == "rs":
                    input_roi = os.path.join(self.subject.roi_rs_dir, roi_name)
                elif from_space == "fmri":
                    input_roi = os.path.join(self.subject.roi_fmri_dir, roi_name)
                elif from_space == "dti":
                    input_roi = os.path.join(self.subject.roi_dti_dir, roi_name)
                elif from_space == "t2":
                    input_roi = os.path.join(self.subject.roi_t2_dir, roi_name)
                elif from_space == "std":
                    input_roi = os.path.join(self.subject.roi_std_dir, roi_name)
                elif from_space == "std4":
                    input_roi = os.path.join(self.subject.roi_std4_dir, roi_name)

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
                    output_roi = os.path.join(self.subject.roi_t1_dir, name + "_" + to_space)
                elif to_space == "rs":
                    output_roi = os.path.join(self.subject.roi_rs_dir, name + "_" + to_space)
                elif to_space == "fmri":
                    output_roi = os.path.join(self.subject.roi_fmri_dir, name + "_" + to_space)
                elif to_space == "dti":
                    output_roi = os.path.join(self.subject.roi_dti_dir, name + "_" + to_space)
                elif to_space == "t2":
                    output_roi = os.path.join(self.subject.roi_t2_dir, name + "_" + to_space)
                elif to_space == "std":
                    output_roi = os.path.join(self.subject.roi_std_dir, name + "_" + to_space)
                elif to_space == "std4":
                    output_roi = os.path.join(self.subject.roi_std4_dir, name + "_" + to_space)
            else:
                output_roi = os.path.join(outdir, name + "_" + to_space)

            # ----------------------------------------------------------------------------------------------------------
            # TRANSFORM !!!!
            # ----------------------------------------------------------------------------------------------------------
            if islin:
                self.linear_registration_type[regtype](input_roi, output_roi)
            else:
                # is non linear
                self.non_linear_registration_type[regtype](input_roi, output_roi)

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
    def transform_nl_std2hr(self, input_roi, output_roi):

        warp = self.std2hr_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2hr(self, input_roi, output_roi):

        mat = self.std2hr_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_std42hr(self, input_roi, output_roi):

        warp = self.std42hr_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std42hr(self, input_roi, output_roi):

        mat = self.std42hr.mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2hr(self, input_roi, output_roi):

        if imtest(self.std2hr_warp) is False:
            print("ERROR: transformation warp " + self.std2hr_warp + " is missing...exiting transform roi")
            return ""
        if os.path.exists(self.rs2std_mat) is False:
            print("ERROR: transformation matrix " + self.rs2std_mat + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --premat=" + self.rs2std_mat + " --warp=" + self.std2hr_warp)
    def transform_l_rs2hr(self, input_roi, output_roi):

        mat = self.rs2hr_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2hr(self, input_roi, output_roi):

        if imtest(self.std2hr_warp) is False:
            print("ERROR: transformation warp " + self.std2hr_warp + " is missing...exiting transform roi")
            return ""
        if os.path.exists(self.fmri2std_mat) is False:
            print("ERROR: transformation matrix " + self.fmri2std_mat + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --premat=" + self.fmri2std_mat + " --warp=" + self.std2hr_warp)
    def transform_l_fmri2hr(self, input_roi, output_roi):

        mat = self.fmri2hr.mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_dti2hr(self, input_roi, output_roi):

        if self.subject.hasT2 is True:
            if imtest(self.dti2hr_warp) is False:
                print("ERROR: transformation warp " + self.dti2hr_warp + " is missing...exiting transform roi")
                return ""
            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + self.dti2hr_warp)
        else:

            if imtest(self.std2hr_warp) is False:
                print("ERROR: transformation warp " + self.std2hr_warp + " is missing...exiting transform roi")
                return ""
            if os.path.exists(self.dti2std_mat) is False:
                print("ERROR: transformation matrix " + self.dti2std_mat + " is missing...exiting transform roi")
                return ""

            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --premat=" + self.dti2std_mat + " --warp=" + self.std2hr_warp)
    def transform_l_dti2hr(self, input_roi, output_roi):

        if os.path.exists(self.dti2hr_mat) is False:
            print("ERROR: transformation matrix " + self.dti2hr_mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + self.dti2hr_mat + " -interp trilinear")

    def transform_nl_t22hr(self, input_roi, output_roi):
        print("WARNING calling transform_l_t22hr instead of transform_nl_t22hr")
        return self.transform_l_t22hr(input_roi, output_roi)
    def transform_l_t22hr(self, input_roi, output_roi):

        if os.path.exists(self.t22hr_mat) is False:
            print("ERROR: transformation matrix " + self.t22hr_mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + self.t22hr_mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO RS (from hr, fmri, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2rs(self, input_roi, output_roi):

        warp = self.std2rs_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.rs_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2rs(self, input_roi, output_roi):

        mat = self.std2rs_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_std42rs(self, input_roi, output_roi):

        warp = self.std42rs_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.rs_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std42rs(self, input_roi, output_roi):

        mat = self.std42rs.mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_hr2rs(self, input_roi, output_roi):
        print("WARNING: transform_nl_hr2rs calls transform_l_hr2rs ")
        self.transform_l_hr2rs(input_roi, output_roi)
    def transform_l_hr2rs(self, input_roi, output_roi):

        mat  = self.hr2rs_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2rs(self, input_roi, output_roi):

        if imtest(self.fmri2rs_warp) is False:
            print("ERROR: transformation warp " + self.fmri2rs_warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.rs_examplefunc + " -o " + output_roi + " --warp=" + self.fmri2rs_warp)
    def transform_l_fmri2rs(self, input_roi, output_roi):

        mat  = os.path.join(self.subject.roi_rs_dir, "fmri2rs.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO FMRI (from hr, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2fmri(self, input_roi, output_roi):

        warp = self.std2fmri_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2fmri(self, input_roi, output_roi):

        mat = self.std2fmri.mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.roi_fmri_dir + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_std42fmri(self, input_roi, output_roi):

        warp = self.std42fmri_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std42fmri(self, input_roi, output_roi):

        mat = self.std42fmri.mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.fmri_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat)

    def transform_nl_hr2fmri(self, input_roi, output_roi):

        if imtest(self.hr2std_warp) is False:
            print("ERROR: transformation warp " + self.hr2std_warp + " is missing...exiting transform roi")
            return ""
        if os.path.exists(self.std2fmri_mat) is False:
            print("ERROR: transformation warp " + self.std2fmri_mat + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + self.hr2std_warp + " --postmat=" + self.std2fmri_mat)
    def transform_l_hr2fmri(self, input_roi, output_roi):

        mat  = os.path.join(self.subject.roi_fmri_dir, "hr2fmri.mat")
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.fmri_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2fmri(self, input_roi, output_roi):

        warp = self.rs2fmri_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.fmri_examplefunc + " -o " + output_roi + " --warp=" + warp)
    def transform_l_rs2fmri(self, input_roi, output_roi):

        mat  = self.fmri2rs_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.rs_examplefunc + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD (from std4, hr, rs, fmri, dti, t2)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std42std(self, input_roi, output_roi):
        return self.transform_l_std42std(input_roi, output_roi)
    def transform_l_std42std(self, input_roi, output_roi):
        rrun("flirt -in " + input_roi + " -ref " + self.subject.std4_img + " -out " + output_roi + " -applyisoxfm 2")

    def transform_nl_hr2std(self, input_roi, output_roi):

        warp = self.hr2std_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_hr2std(self, input_roi, output_roi):

        mat = self.hr2std_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2std(self, input_roi, output_roi):

        warp = self.rs2std_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_rs2std(self, input_roi, output_roi):

        mat = self.rs2std_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2std(self, input_roi, output_roi):

        warp = self.fmri2std_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_fmri2std(self, input_roi, output_roi):

        mat = self.rs2std_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_dti2std(self, input_roi, output_roi):

        warp = self.dti2std_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_dti2std(self, input_roi, output_roi):

        mat = self.dti2std_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_t22std(self, input_roi, output_roi):

        warp = self.t22std_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_t22std(self, input_roi, output_roi):

        mat = self.t22std_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD4 (from std, hr, rs, fmri)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2std4(self, input_roi, output_roi):
        return self.transform_l_std2std4(input_roi, output_roi)
    def transform_l_std2std4(self, input_roi, output_roi):
        rrun("flirt -in " + input_roi + " -ref " + self.subject.std4_img + " -out " + output_roi + " -applyisoxfm 4")

    def transform_nl_hr2std4(self, input_roi, output_roi):

        warp = self.hr2std4_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""
        rrun("applywarp -i " + input_roi + " -r " + self.subject.std4_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_hr2std4(self, input_roi, output_roi):

        mat = self.hr2std4_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""
        rrun("flirt -in " + input_roi + " -ref " + self.subject.std4_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_rs2std4(self, input_roi, output_roi):

        warp = self.rs2std4_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std4_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_rs2std4(self, input_roi, output_roi):

        mat = self.rs2std4_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std4_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_fmri2std4(self, input_roi, output_roi):

        warp = self.rs2std4_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.std4_head_img + " -o " + output_roi + " --warp=" + warp)
    def transform_l_fmri2std4(self, input_roi, output_roi):

        mat = self.fmri2std4_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.std4_img + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO DTI (from std, hr, t2)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2dti(self, input_roi, output_roi):

        warp = self.std2dti_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nodif_brain") + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2dti(self, input_roi, output_roi):

        mat = self.std2dti_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

        # ==============================================================================================================

    def transform_nl_hr2dti(self, input_roi, output_roi):

        if self.subject.hasT2 is True and imtest(self.hr2dti_warp) is True:
            if imtest(self.hr2dti_warp) is False:
                print("ERROR: transformation warp " + self.hr2dti_warp + " is missing...exiting transform roi")
                return ""

            rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + self.hr2dti_warp)
        else:
            print("did not find the non linear registration from HR 2 DTI, I concat hr---(NL)--->std  with std ---(LIN)---> dti used a linear one")

            if imtest(self.hr2std_warp) is False:
                print("ERROR: transformation warp " + self.hr2std_warp + " is missing...exiting transform roi")
                return ""
            if os.path.exists(self.std2dti_mat) is False:
                print("ERROR: transformation matrix " + self.std2dti_mat + " is missing...exiting transform roi")
                return ""

            rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + self.hr2std_warp + " --postmat=" + self.std2dti_mat)
    def transform_l_hr2dti(self, input_roi, output_roi):

        if os.path.exists(self.hr2dti_mat) is False:
            print("ERROR: transformation matrix " + self.hr2dti_mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + self.hr2dti_mat + " -interp trilinear")

    def transform_nl_t22dti(self, input_roi, output_roi):

        warp = self.t22dti_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_t22dti(self, input_roi, output_roi):

        mat = self.t22dti_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.dti_nodiff_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO T2 (from std, hr, dti)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2t2(self, input_roi, output_roi):

        warp = self.dti2t2_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_brain_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_std2t2(self, input_roi, output_roi):

        mat = self.dti2t2_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return ""

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t2_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_hr2t2(self, input_roi, output_roi):
        print("WARNING calling transform_l_hr2t2 instead of transform_nl_hr2t2")
        return self.transform_l_hr2t2(input_roi, output_roi)
    def transform_l_hr2t2(self, input_roi, output_roi):

        mat = self.hr2t2_mat
        if os.path.exists(mat) is False:
            print("ERROR: transformation matrix " + mat + " is missing...exiting transform roi")
            return

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t2_brain_data + " -out " + output_roi + " -applyxfm -init " + mat + " -interp trilinear")

    def transform_nl_dti2t2(self, input_roi, output_roi):

        warp = self.dti2t2_warp
        if imtest(warp) is False:
            print("ERROR: transformation warp " + warp + " is missing...exiting transform roi")
            return ""

        rrun("applywarp -i " + input_roi + " -r " + self.subject.dti_nodiff_brain_data + " -o " + output_roi + " --warp=" + warp)
    def transform_l_dti2t2(self, input_roi, output_roi):

        mat = self.dti2t2_mat
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

    # def transform_nl_dti2fmri(self, input_roi, output_roi):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")
    #
    # def transform_l_dti2fmri(self, input_roi, output_roi):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")


    # def transform_nl_dti2rs(self, input_roi, output_roi):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")
    #
    # def transform_l_dti2rs(self, input_roi, output_roi):
    #     print("registration type: dti2epi NOT SUPPORTED...exiting")
