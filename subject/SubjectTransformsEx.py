import os

from myfsl.utils.run import rrun
from utility.fslfun import runsystem
from utility.images import imtest, imcp

# Class contains all the available transformations across different sequences.
#
# there can be 60 transformation among t1, t2, dti, rs, fmri, std, std4
# I created only 50 properties because
#    -  4 transformations does not need a property as they involve moving between std & std4 through flirt -applyisoxfm)
#    -  6 non-linear transformation (hr-rs, hr-fmri, hr-t2) never exist and code returns their linear transformation (non linear hr-dti can exist if t2 is available)
#
# the 50 properties manage
#    - 26 linear
#    - 24 non-linear
# transformation
#
# There exist 5 methods to calculate transf relating to t1, rs, fmri, dti+t2 and an extra to connect rs & fmri (the latter used to better connect to t1)
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
from utility.transform_images import check_concat_mat, check_invert_mat, check_convert_warp_mw, check_invert_warp, \
    check_flirt, check_apply_mat, check_convert_warp_wmw, check_convert_warp_ww, check_apply_warp


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

        self.dti2hr_warp    = os.path.join(self.subject.roi_t1_dir, "dti2hr_warp")    # when t2 is available
        self.dti2hr_mat     = os.path.join(self.subject.roi_t1_dir, "dti2hr.mat")     # TODO: decide whether using direct or through-T2
        self.dtihead2hr_mat = os.path.join(self.subject.roi_t1_dir, "dtihead2hr.mat")     #

        #self.t22hr_warp  does not exist
        self.t22hr_mat      = os.path.join(self.subject.roi_t1_dir, "t22hr.mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # TO RS (from hr, fmri, std, std4)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.std2rs_warp    = os.path.join(self.subject.roi_rs_dir, "std2rs_warp")
        self.std2rs_mat     = os.path.join(self.subject.roi_rs_dir, "std2rs.mat")

        self.std42rs_warp   = os.path.join(self.subject.roi_rs_dir, "std42rs_warp")
        self.std42rs_mat    = os.path.join(self.subject.roi_rs_dir, "std42rs.mat")

        # self.hr2rs_warp does not exist
        self.hr2rs_mat      = os.path.join(self.subject.roi_rs_dir, "hr2rs.mat")

        self.fmri2rs_warp   = os.path.join(self.subject.roi_rs_dir, "fmri2rs_warp") # passing from hr and std
        self.fmri2rs_mat    = os.path.join(self.subject.roi_rs_dir, "fmri2rs.mat")  # TODO: decide whether using direct or through-hr

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
        self.rs2fmri_mat     = os.path.join(self.subject.roi_fmri_dir, "rs2fmri.mat")   # TODO: decide whether using direct or through-hr

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

        self.hr2dti_warp      = os.path.join(self.subject.roi_dti_dir, "hr2dti_warp")   # if hasT2
        self.hr2dti_mat       = os.path.join(self.subject.roi_dti_dir, "hr2dti.mat")    # TODO: decide whether using direct or through-T2

        self.t22dti_warp      = os.path.join(self.subject.roi_dti_dir, "t22dti_warp")
        self.t22dti_mat       = os.path.join(self.subject.roi_dti_dir, "t22dti.mat")
        self.t2head2dti_mat   = os.path.join(self.subject.roi_dti_dir, "t2head2dti.mat")     #

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

            "hrTOstd": self.transform_l_hr2std,
            "rsTOstd": self.transform_l_rs2std,
            "fmriTOstd": self.transform_l_fmri2std,
            "dtiTOstd": self.transform_l_dti2std,
            "t2TOstd": self.transform_l_t22dti,

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

            "hrTOstd": self.transform_nl_hr2std,
            "rsTOstd": self.transform_nl_rs2std,
            "fmriTOstd": self.transform_nl_fmri2std,
            "dtiTOstd": self.transform_nl_dti2std,
            "t2TOstd": self.transform_nl_t22dti,

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

    # ==================================================================================================================================================
    # MAIN SEQUENCES TRANSFORMS
    # ==================================================================================================================================================

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate all the transforms involved in MPR processing.
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # it creates (8) :  hr2std_mat,  std2hr_mat,  hr2std_warp,  std2hr_warp,            hrhead2std.mat
    #                   hr2std4_mat, std42hr_mat, hr2std4_warp, std42hr_warp,           hrhead2std4.mat
    def transform_mpr(self, logFile=None):

        hrhead2std      = os.path.join(self.subject.roi_std_dir,  "hrhead2" + self.subject.std_img_label + ".mat")
        hrhead2std4     = os.path.join(self.subject.roi_std4_dir, "hrhead2" + self.subject.std_img_label + "4.mat")

        check = self.subject.check_template()
        if check[0] != "":
            return
        else:
            process_std4 = check[1]

        print(self.subject.label + " :STARTED transform_mpr")

        os.makedirs(self.subject.roi_std_dir, exist_ok=True)
        os.makedirs(self.subject.roi_t1_dir, exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # HIGHRES <--------> STANDARD
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => hr2{std}.mat
        check_flirt(self.hr2std_mat, self.subject.t1_brain_data, self.subject.std_img, logFile=logFile)

        # => hrhead2{std}.mat
        check_flirt(hrhead2std, self.subject.t1_data, self.subject.std_img, logFile=logFile)

        # # => {std}2hr.mat
        check_invert_mat(self.std2hr_mat, self.hr2std_mat, logFile=logFile)

        # NON LINEAR
        # => hr2{std}_warp
        if imtest(self.hr2std_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std + " --config=" + self._global.fsl_std_mni_2mm_cnf +
                    " --ref=" + self.subject.std_head_img + " --refmask=" + self.subject.std_img_mask_dil + " --warpres=10,10,10" +
                    " --cout=" + self.hr2std_warp + " --iout=" + self.hr2std_mat, logFile=logFile)

        # => {std}2hr_warp
        check_invert_warp(self.std2hr_warp, self.hr2std_warp, self.subject.t1_data, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # HIGHRES <--------> STANDARD4
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if process_std4 is False:
            return

        os.makedirs(self.subject.roi_std4_dir, exist_ok=True)
        # => hr2{std}4.mat
        check_flirt(self.hr2std4_mat, self.subject.t1_brain_data, self.subject.std4_img, logFile=logFile)

        # => hrhead2{std}4.mat
        check_flirt(hrhead2std4, self.subject.t1_data, self.subject.std4_head_img, logFile=logFile)

        # => {std}42hr.mat
        check_invert_mat(self.std42hr_mat, self.hr2std4_mat, logFile=logFile)

        # NON LINEAR
        # => hr2{std}4_warp
        if imtest(self.hr2std4_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std4 + " --config=" + self._global.fsl_std_mni_4mm_cnf +
                 " --ref=" + self.subject.std4_head_img + " --refmask=" + self.subject.std4_img_mask_dil + " --warpres=10,10,10" + " --cout=" + self.hr2std4_warp)

        # => {std}42hr_warp
        check_invert_warp(self.std42hr_warp, self.hr2std4_warp, self.subject.t1_data, logFile=logFile)

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

        check = self.subject.check_template()
        if check[0] != "":
            return
        else:
            process_std4 = check[1]

        print(self.subject.label + " :STARTED transform_rs")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # check or create example function
        exfun = self.subject.epi.get_example_function(logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  RS <--> HIGHRES (linear, bbr or not)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            check_flirt("init_" + self.rs2hr_mat, exfun, self.subject.t1_brain_data, params="-dof 6", logFile=logFile)

            if imtest(wmseg) is False:
                print("Running FAST segmentation for subj " + self.subject.label)
                temp_dir = os.path.join(self.subject.roi_t1_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.subject.t1_brain_data), logFile=logFile)
                rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + wmseg, logFile=logFile)
                runsystem("rm -rf " + temp_dir, logFile=logFile)

            check_flirt(self.rs2hr_mat, exfun, self.subject.t1_brain_data, params=" -dof 6 -cost bbr -wmseg " + wmseg + " -init " + "init_" + self.rs2hr_mat + " -schedule " + os.path.join(self.subject.fsl_dir, "etc", "flirtsch", "bbr.sch"), logFile=logFile)

            runsystem("rm " + "init_" + self.rs2hr_mat, logFile=logFile)
        else:   # NOT BBR
            check_flirt(self.rs2hr_mat, exfun, self.subject.t1_brain_data, params=" -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear", logFile=logFile)

        check_invert_mat(self.hr2rs_mat, self.rs2hr_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # RS <--> STANDARD (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => rs2std.mat
        check_concat_mat(self.rs2std_mat, self.rs2hr_mat, self.hr2std_mat, logFile=logFile)

        # => std2rs.mat
        check_invert_mat(self.std2rs_mat, self.rs2std_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # RS <--> STANDARD (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => rs2std_warp
        check_convert_warp_mw(self.rs2std_warp, self.rs2hr_mat, self.hr2std_warp, self.subject.std_head_img, logFile=logFile)

        # => std2rs_warp
        check_invert_warp(self.std2rs_warp, self.rs2std_warp, self.subject.rs_examplefunc, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # RS <-> STANDARD4 (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => rs2std4.mat
        check_concat_mat(self.rs2std4_mat, self.rs2hr_mat, self.hr2std4_mat, logFile=logFile)

        # => std42rs.mat
        check_invert_mat(self.std42rs_mat, self.rs2std4_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # RS <-> STANDARD4 (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => rs2std4_warp
        check_convert_warp_mw(self.rs2std4_warp, self.rs2hr_mat, self.hr2std4_warp, self.subject.std4_head_img, logFile=logFile)

        # => std42rs_warp
        check_invert_warp(self.std42rs_warp, self.rs2std4_warp, exfun, logFile=logFile)

        # ------------------------------------------------------------------------------------------------------
        # various co-registration
        # ------------------------------------------------------------------------------------------------------
        # coregister fast-highres to rs
        check_apply_mat(os.path.join(self.subject.roi_rs_dir, "t1_wm_rs"),          os.path.join(self.subject.roi_t1_dir, "mask_t1_wm"),    self.hr2rs_mat, self.subject.rs_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_rs_dir, "t1_csf_rs"),         os.path.join(self.subject.roi_t1_dir, "mask_t1_csf"),   self.hr2rs_mat, self.subject.rs_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_rs_dir, "t1_gm_rs"),          os.path.join(self.subject.roi_t1_dir, "mask_t1_gm"),    self.hr2rs_mat, self.subject.rs_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_rs_dir, "t1_brain_rs"),       self.subject.t1_brain_data,                             self.hr2rs_mat, self.subject.rs_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs"),  self.subject.t1_brain_data_mask,                        self.hr2rs_mat, self.subject.rs_examplefunc, logFile=logFile)

        # mask & binarize
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_gm_rs")         + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_gm_rs"),      logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_wm_rs")         + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_wm_rs"),      logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_csf_rs")        + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_csf_rs"),     logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_brain_rs")      + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"),   logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_rs_dir, "t1_brain_mask_rs") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_rs_dir, "mask_t1_brain_rs"),   logFile=logFile)

    # it creates (10) : example_func, fmri2hr_mat , hr2fmri_mat , fmri2std_mat , std2fmri_mat , fmri2std4_mat , std42fmri_mat
    #                                                             fmri2std_warp, std2fmri_warp, fmri2std4_warp, std42fmri_warp
    def transform_fmri(self, do_bbr=False, wmseg="", logFile=None):

        if wmseg == "":
            wmseg = self.subject.t1_segment_wm_bbr_path
        else:
            if imtest(wmseg) is False and do_bbr is True:
                print("ERROR: asked to run bbr, but the given wmseg file " + wmseg + ".nii.gz is not present...exiting transforms_mpr")
                return

        check = self.subject.check_template()
        if check[0] != "":
            return
        else:
            process_std4 = check[1]

        print(self.subject.label + " :STARTED transform_fmri")
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # check or create example function
        exfun = self.subject.epi.get_example_function(logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  fmri <--> HIGHRES (linear, bbr or not)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            check_flirt("init_" + self.fmri2hr_mat, exfun, self.subject.t1_brain_data, params="-dof 6", logFile=logFile)

            if imtest(wmseg) is False:
                print("Running FAST segmentation for subj " + self.subject.label)
                temp_dir = os.path.join(self.subject.roi_t1_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.subject.t1_brain_data), logFile=logFile)
                rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + wmseg, logFile=logFile)
                runsystem("rm -rf " + temp_dir, logFile=logFile)

            check_flirt(self.fmri2hr_mat, exfun, self.subject.t1_brain_data, params=" -dof 6 -cost bbr -wmseg " + wmseg + " -init " + "init_" + self.fmri2hr_mat + " -schedule " + os.path.join(self.subject.fsl_dir, "etc", "flirtsch", "bbr.sch"), logFile=logFile)

            runsystem("rm " + "init_" + self.fmri2hr_mat, logFile=logFile)
        else:   # NOT BBR
            check_flirt(self.fmri2hr_mat, exfun, self.subject.t1_brain_data, params=" -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear", logFile=logFile)

        check_invert_mat(self.hr2fmri_mat, self.fmri2hr_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # fmri <--> STANDARD (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => fmri2std.mat
        check_concat_mat(self.fmri2std_mat, self.fmri2hr_mat, self.hr2std_mat, logFile=logFile)

        # => std2fmri.mat
        check_invert_mat(self.std2fmri_mat, self.fmri2std_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # fmri <--> STANDARD (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => fmri2std_warp
        check_convert_warp_mw(self.fmri2std_warp, self.fmri2hr_mat, self.hr2std_warp, self.subject.std_head_img, logFile=logFile)

        # => std2fmri_warp
        check_invert_warp(self.std2fmri_warp, self.fmri2std_warp, self.subject.fmri_examplefunc, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # fmri <-> STANDARD4 (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => fmri2std4.mat
        check_concat_mat(self.fmri2std4_mat, self.fmri2hr_mat, self.hr2std4_mat, logFile=logFile)

        # => std42fmri.mat
        check_invert_mat(self.std42fmri_mat, self.fmri2std4_mat, logFile=logFile)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # fmri <-> STANDARD4 (non linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => fmri2std4_warp
        check_convert_warp_mw(self.fmri2std4_warp, self.fmri2hr_mat, self.hr2std4_warp, self.subject.std4_head_img, logFile=logFile)

        # => std42fmri_warp
        check_invert_warp(self.std42fmri_warp, self.fmri2std4_warp, exfun, logFile=logFile)

        # ------------------------------------------------------------------------------------------------------
        # various co-registration
        # ------------------------------------------------------------------------------------------------------
        # coregister fast-highres to fmri
        check_apply_mat(os.path.join(self.subject.roi_fmri_dir, "t1_wm_fmri"),          os.path.join(self.subject.roi_t1_dir, "mask_t1_wm"),    self.hr2fmri_mat, self.subject.fmri_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_fmri_dir, "t1_csf_fmri"),         os.path.join(self.subject.roi_t1_dir, "mask_t1_csf"),   self.hr2fmri_mat, self.subject.fmri_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_fmri_dir, "t1_gm_fmri"),          os.path.join(self.subject.roi_t1_dir, "mask_t1_gm"),    self.hr2fmri_mat, self.subject.fmri_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_fmri_dir, "t1_brain_fmri"),       self.subject.t1_brain_data,                             self.hr2fmri_mat, self.subject.fmri_examplefunc, logFile=logFile)
        check_apply_mat(os.path.join(self.subject.roi_fmri_dir, "t1_brain_mask_fmri"),  self.subject.t1_brain_data_mask,                        self.hr2fmri_mat, self.subject.fmri_examplefunc, logFile=logFile)

        # mask & binarize
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_gm_fmri")         + " -thr 0.2 -bin " + os.path.join(self.subject.roi_fmri_dir, "mask_t1_gm_fmri"),      logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_wm_fmri")         + " -thr 0.2 -bin " + os.path.join(self.subject.roi_fmri_dir, "mask_t1_wm_fmri"),      logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_csf_fmri")        + " -thr 0.2 -bin " + os.path.join(self.subject.roi_fmri_dir, "mask_t1_csf_fmri"),     logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_brain_fmri")      + " -thr 0.2 -bin " + os.path.join(self.subject.roi_fmri_dir, "mask_t1_brain_fmri"),   logFile=logFile)
        rrun("fslmaths " + os.path.join(self.subject.roi_fmri_dir, "t1_brain_mask_fmri") + " -thr 0.2 -bin " + os.path.join(self.subject.roi_fmri_dir, "mask_t1_brain_fmri"),   logFile=logFile)

    # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
    # creates  (18) :   dti2hr.mat, hr2dti.mat,     dti2std_warp, std2dti_warp  , dti2std_mat, std2dti_mat
    # and if has_T2 :   dti2t2.mat, t22dti.mat,     dti2t2_warp,  t22dti_warp   , t22hr.mat, hr2t2.mat,     t22std_warp,  std2t2_warp
    #                   dti2hr_warp, hr2dti_warp,
    #                   overwrites dti2std_warp, std2dti_warp
    def transform_dti_t2(self, logFile=None):

        check = self.subject.check_template()
        if check[0] != "":
            return

        if self.subject.hasT2 is True:
            print(self.subject.label + " :STARTED transform_dti_t2: (DTI--T2--HR--STD coregistration)")
        else:
            print(self.subject.label + " :STARTED transform_dti_t2 (DTI--HR--STD coregistration)")
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        self.subject.dti.get_nodiff()

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # DTI <------> HIGHRES (linear)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        check_flirt(self.dti2hr_mat,     self.subject.dti_nodiff_brain_data, self.subject.t1_brain_data, "-bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear", logFile=logFile)
        check_flirt(self.dtihead2hr_mat, self.subject.dti_nodiff_data,       self.subject.t1_brain_data, "-bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear", logFile=logFile)

        check_invert_mat(self.hr2dti_mat, self.dti2hr_mat, logFile=logFile)

        if self.subject.hasT2 is False:

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (lin) -- HIGHRES -- (non-lin) --> STANDARD
            # -------------------------------------------------------------------------, ------------------------------------------------------------------------------------------------------------------
            # dti --> std
            check_convert_warp_mw(self.dti2std_warp, self.dtihead2hr_mat, self.hr2std_warp, self.subject.std_head_img, logFile=logFile)
            check_concat_mat(self.dti2std_mat, self.dti2hr_mat, self.hr2std_mat, logFile=logFile)

            # std --> dti
            check_invert_warp(self.std2dti_warp, self.dti2std_warp, self.subject.dti_nodiff_data, logFile=logFile)
            check_invert_mat(self.std2dti_mat, self.dti2std_mat, logFile=logFile)

        else:
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <--->  T2  linear and non-linear
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 -> dti
            # linear
            check_flirt(self.t22dti_mat,     self.subject.t2_brain_data,    self.subject.dti_nodiff_brain_data, " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)
            check_flirt(self.t2head2dti_mat, self.subject.t2_data,          self.subject.dti_nodiff_data,       " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)

            # non-linear
            if imtest(self.t22dti_warp) is False:
                rrun("fnirt --in=" + self.subject.t2_data + " --ref=" + self.subject.dti_nodiff_data + " --aff=" + self.t2head2dti_mat + " --cout=" + self.t22dti_warp, logFile=logFile)

            # dti -> t2
            # linear
            check_invert_mat(self.dti2t2_mat, self.t22dti_mat, logFile=logFile)

            # non-linear
            check_invert_warp(self.dti2t2_warp, self.t22dti_warp, self.subject.dti_nodiff_data, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # T2 <------> HIGHRES (linear)
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 -> hr linear
            check_flirt(self.t22hr_mat, self.subject.t2_brain_data, self.subject.t1_brain_data, " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12 -interp trilinear", logFile=logFile)

            # hr -> t2 linear
            check_invert_mat(self.hr2t2_mat, self.t22hr_mat, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            if imtest(self.dti2hr_warp) is False:
                rrun("convertwarp --ref=" + self.subject.t1_data + " --warp1=" + self.dti2t2_warp + " --postmat=" + self.t22hr_mat + " --out=" + self.dti2hr_warp, logFile=logFile)

            if imtest(self.hr2dti_warp) is False:
                rrun("invwarp -r " + self.subject.dti_nodiff_data + " -w " + self.dti2hr_warp + " -o " + self.hr2dti_warp, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # T2 <------> STD
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # t2 --> std
            check_convert_warp_mw(self.t22std_warp, self.t22hr_mat, self.hr2std_warp, self.subject.std_head_img, logFile=logFile)
            check_concat_mat(self.t22std_mat, self.t22hr_mat, self.hr2std_mat, logFile=logFile)

            # std --> t2
            check_invert_warp(self.std2t2_warp, self.t22std_warp, self.subject.t2_data, logFile=logFile)
            check_invert_mat(self.std2t2_mat, self.t22std_mat, logFile=logFile)

            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DTI <-- (non-lin) -- t2 -- (lin) -- HIGHRES -- (non-lin) --> STANDARD
            # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # dti --> std
            check_convert_warp_wmw(self.dti2std_warp, self.dti2t2_warp, self.t22hr_mat, self.hr2std_warp, self.subject.std_head_img, logFile=logFile)
            check_concat_mat(self.dti2std_mat, self.dti2hr_mat, self.hr2std_mat, logFile=logFile)

            # std --> dti
            check_invert_warp(self.std2dti_warp, self.dti2std_warp, self.subject.dti_nodiff_data, logFile=logFile)
            check_invert_mat(self.std2dti_mat, self.dti2std_mat, logFile=logFile)

    # it creates (4): rs2fmri_mat , fmri2rs_mat
    #                 rs2fmri_warp, fmri2rs_warp
    def transform_extra(self, logFile=None):

        if self.subject.hasFMRI and self.subject.hasRS:

            check_concat_mat(self.rs2fmri_mat, self.rs2hr_mat, self.hr2fmri_mat, logFile=logFile)
            check_invert_mat(self.fmri2rs_mat, self.rs2fmri_mat, logFile=logFile)

            # non-linear   rs <--(hr)--> std <--(hr)--> fmri
            check_convert_warp_ww(self.rs2fmri_warp, self.rs2std_warp, self.std2fmri_warp, self.subject.fmri_examplefunc, logFile=logFile)
            check_invert_warp(self.fmri2rs_warp, self.rs2fmri_warp, self.subject.fmri_examplefunc, logFile=logFile)

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
            if regtype == "std2std4":
                rrun("flirt -in " + input_roi + " -ref " + self.subject.std4_img + " -out " + output_roi + " -applyisoxfm 4")
            elif regtype == "std42std":
                rrun("flirt -in " + input_roi + " -ref " + self.subject.std_img  + " -out " + output_roi + " -applyisoxfm 2")
            else:
                if islin:
                    mat, ref = self.linear_registration_type[regtype]()
                    check_apply_mat(output_roi, input_roi, mat, ref, overwrite=True)
                else:
                    # is non linear (actually, when non linear reg exist, it can be linear)
                    warp, ref = self.non_linear_registration_type[regtype]()
                    if imtest(warp) is False:
                        check_apply_mat(output_roi, input_roi, warp, ref, overwrite=True)
                    else:
                        check_apply_warp(output_roi, input_roi, warp, ref, overwrite=True)
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


    # ==================================================================================================================
    # the following methods return the mat/warp of the given transformation and the reference image
    # ==================================================================================================================

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO HR (from rs, fmri, dti, t2, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2hr(self):
        return self.std2hr_warp, self.subject.t1_data
    def transform_l_std2hr(self):
        return self.std2hr_mat, self.subject.t1_brain_data

    def transform_nl_std42hr(self):
        return self.std42hr_warp, self.subject.t1_data
    def transform_l_std42hr(self):
        return self.std42hr.mat, self.subject.t1_brain_data

    def transform_nl_rs2hr(self):
        print("WARNING calling transform_l_rs2hr instead of transform_nl_rs2hr")
        return self.transform_l_rs2hr()
    def transform_l_rs2hr(self):
        return self.rs2hr_mat, self.subject.t1_brain_data

    def transform_nl_fmri2hr(self):
        print("WARNING calling transform_l_fmri2hr instead of transform_nl_fmri2hr")
        return self.transform_l_fmri2hr()
    def transform_l_fmri2hr(self):
        return self.fmri2hr.mat, self.subject.t1_brain_data

    def transform_nl_dti2hr(self):
        if self.subject.hasT2 is True:
            return self.dti2hr_warp, self.subject.t1_data
        else:
            print("WARNING calling transform_l_dti2hr instead of transform_nl_dti2hr")
            return transform_l_dti2hr(self)
    def transform_l_dti2hr(self):
        return self.dti2hr_mat, self.subject.t1_brain_data

    def transform_nl_t22hr(self):
        print("WARNING calling transform_l_t22hr instead of transform_nl_t22hr")
        return self.transform_l_t22hr()
    def transform_l_t22hr(self):
        return self.t22hr_mat, self.subject.t1_brain_data

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO RS (from hr, fmri, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2rs(self):
        return self.std2rs_warp, self.subject.rs_examplefunc
    def transform_l_std2rs(self):
        return self.std2rs_mat, self.subject.rs_examplefunc

    def transform_nl_std42rs(self):
        return self.std42rs_warp, self.subject.rs_examplefunc
    def transform_l_std42rs(self):
        return self.std42rs.mat, self.subject.rs_examplefunc

    def transform_nl_hr2rs(self):
        print("WARNING: transform_nl_hr2rs calls transform_l_hr2rs ")
        return self.transform_l_hr2rs()
    def transform_l_hr2rs(self):
        return self.hr2rs_mat, self.subject.rs_examplefunc

    def transform_nl_fmri2rs(self):
        return self.fmri2rs_warp, self.subject.rs_examplefunc
    def transform_l_fmri2rs(self):
        return self.rs2fmri_mat, self.subject.rs_examplefunc

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO FMRI (from hr, std, std4)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2fmri(self):
        return self.std2fmri_warp, self.subject.fmri_examplefunc
    def transform_l_std2fmri(self):
        return self.std2fmri.mat, self.subject.roi_fmri_dir

    def transform_nl_std42fmri(self):
        return self.std42fmri_warp, self.subject.fmri_examplefunc
    def transform_l_std42fmri(self):
        return self.std42fmri.mat, self.subject.fmri_examplefunc

    def transform_nl_hr2fmri(self):
        return transform_l_hr2fmri()
    def transform_l_hr2fmri(self):
        return self.hr2fmri_mat, self.subject.fmri_examplefunc

    def transform_nl_rs2fmri(self):
        return self.rs2fmri_warp, self.subject.fmri_examplefunc
    def transform_l_rs2fmri(self):
        return self.fmri2rs_mat, self.subject.rs_examplefunc

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD (from std4, hr, rs, fmri, dti, t2)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2std(self):
        return self.hr2std_warp, self.subject.std_img
    def transform_l_hr2std(self):
        return self.hr2std_mat, self.subject.std_img

    def transform_nl_rs2std(self):
        return self.rs2std_warp, self.subject.std_head_img
    def transform_l_rs2std(self):
        return self.rs2std_mat, self.subject.std_img

    def transform_nl_fmri2std(self):
        return self.fmri2std_warp, self.subject.std_head_img
    def transform_l_fmri2std(self):
        return self.rs2std_mat, self.subject.std_img

    def transform_nl_dti2std(self):
        return self.dti2std_warp, self.subject.std_head_img
    def transform_l_dti2std(self):
        return self.dti2std_mat, self.subject.std_img

    def transform_nl_t22std(self):
        return self.t22std_warp, self.subject.std_head_img
    def transform_l_t22std(self):
        return self.t22std_mat, self.subject.std_img

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD4 (from std, hr, rs, fmri)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_hr2std4(self):
        return self.hr2std4_warp, self.subject.std4_head_img
    def transform_l_hr2std4(self):
        return self.hr2std4_mat, self.subject.std4_img

    def transform_nl_rs2std4(self):
        return self.rs2std4_warp, self.subject.std4_head_img
    def transform_l_rs2std4(self):
        return self.rs2std4_mat, self.subject.std4_img

    def transform_nl_fmri2std4(self):
        return self.rs2std4_warp, self.subject.std4_head_img
    def transform_l_fmri2std4(self):
        return self.fmri2std4_mat, self.subject.std4_img

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO DTI (from std, hr, t2)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2dti(self):
        return self.std2dti_warp, self.subject.dti_nodiff_data
    def transform_l_std2dti(self):
        return self.std2dti_mat, self.subject.dti_nodiff_brain_data

        # ==============================================================================================================

    def transform_nl_hr2dti(self):
        if self.subject.hasT2 is True and imtest(self.hr2dti_warp) is True:
            return self.hr2dti_warp, self.subject.dti_nodiff_data
        else:
            print("did not find the non linear registration from HR 2 DTI, I concat hr---(NL)--->std  with std ---(LIN)---> dti used a linear one")
            return transform_l_hr2dti()
    def transform_l_hr2dti(self):
        return self.hr2dti_mat, self.subject.dti_nodiff_brain_data

    def transform_nl_t22dti(self):
        return self.t22dti_warp, self.subject.dti_nodiff_data
    def transform_l_t22dti(self):
        return self.t22dti_mat, self.subject.dti_nodiff_brain_data

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO T2 (from std, hr, dti)
    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def transform_nl_std2t2(self):
        return self.dti2t2_warp, self.subject.dti_nodiff_brain_data
    def transform_l_std2t2(self):
        return self.dti2t2_mat, self.subject.t2_brain_data

    def transform_nl_hr2t2(self):
        print("WARNING calling transform_l_hr2t2 instead of transform_nl_hr2t2")
        return self.transform_l_hr2t2()
    def transform_l_hr2t2(self):
        return self.hr2t2_mat, self.subject.t2_brain_data

    def transform_nl_dti2t2(self):
        return self.dti2t2_warp, self.subject.dti_nodiff_brain_data
    def transform_l_dti2t2(self):
        return self.dti2t2_mat, self.subject.t2_brain_data

    # ==============================================================================================================
    # methods to check coregistration of multiple images
    # ==============================================================================================================
    # this method takes base images (t1/t1_brain, epi_example_function, dti_nodiff/dti_nodiff_brain, t2/t2_brain) and coregister to all other modalities and standard
    # creates up to 14 folders, 7 for linear and 7 for non linear transformation towards the 7 different space (hr, rs, frmi, dti, t2, std, std4)
    # user can select from which seq to which seq create the transforms
    def test_all_coregistration(self, test_dir, _from=None, _to=None, extended=False):

        if _from is None:
            _from = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        if _to is None:
            _to = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]


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

            if "hr" in _from and "std" in _to:
                self.transform_roi("hrTOstd",    pathtype="abs", outdir=nl_std   , islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOstd",    pathtype="abs",  outdir=l_std   , islin=True,  rois=[self.subject.t1_brain_data])

            if extended is True and "std" in _from and "hr" in _to:
                self.transform_roi("stdTOhr",    pathtype="abs", outdir=nl_t1   , islin=False, rois=[self.subject.std_head_img])
                self.transform_roi("stdTOhr",    pathtype="abs",  outdir=l_t1   , islin=True,  rois=[self.subject.std_img])

            if self.subject.hasRS is True:  # connect HR with STD4

                if "hr" in _from and "std4" in _to:
                    self.transform_roi("hrTOstd4", pathtype="abs", outdir=nl_std4, islin=False, rois=[self.subject.t1_data])
                    self.transform_roi("hrTOstd4", pathtype="abs", outdir=l_std4, islin=True, rois=[self.subject.t1_brain_data])

                if extended is True and "std4" in _from and "hr" in _to:
                    self.transform_roi("std4TOhr", pathtype="abs", outdir=nl_t1, islin=False, rois=[self.subject.std4_head_img])
                    self.transform_roi("std4TOhr", pathtype="abs", outdir=l_t1, islin=True, rois=[self.subject.std4_img])
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

            if "hr" in _from and "rs" in _to:
                self.transform_roi("hrTOrs",    pathtype="abs", outdir=nl_rs   , islin=False,   rois=[self.subject.t1_data])
                self.transform_roi("hrTOrs",    pathtype="abs", outdir=l_rs    , islin=True,    rois=[self.subject.t1_brain_data])

            if "rs" in _from and "hr" in _to:
                self.transform_roi("rsTOhr",    pathtype="abs", outdir=nl_t1   , outname=self.subject.label + "_rs_examplefunc", islin=False,   rois=[exfun])
                self.transform_roi("rsTOhr",    pathtype="abs", outdir=l_t1    , outname=self.subject.label + "_rs_examplefunc", islin=True,    rois=[exfun])

            if "rs" in _from and "std" in _to:
                self.transform_roi("rsTOstd",   pathtype="abs", outdir=nl_std   , outname=self.subject.label + "_rs_examplefunc", islin=False,   rois=[exfun])
                self.transform_roi("rsTOstd",   pathtype="abs", outdir=l_std    , outname=self.subject.label + "_rs_examplefunc", islin=True,    rois=[exfun])

            if extended is True and "std" in _from and "rs" in _to:
                self.transform_roi("stdTOrs",   pathtype="abs", outdir=nl_rs   , islin=False,   rois=[self.subject.std_head_img])
                self.transform_roi("stdTOrs",   pathtype="abs", outdir=l_rs    , islin=True,    rois=[self.subject.std_img])

            if "rs" in _from and "std4" in _to:
                self.transform_roi("rsTOstd4",  pathtype="abs", outdir=nl_std4   , outname=self.subject.label + "_rs_examplefunc", islin=False,   rois=[exfun])
                self.transform_roi("rsTOstd4",  pathtype="abs", outdir=l_std4    , outname=self.subject.label + "_rs_examplefunc", islin=True,    rois=[exfun])

            if extended is True and "std4" in _from and "rs" in _to:
                self.transform_roi("std4TOrs",  pathtype="abs", outdir=nl_rs   , islin=False,   rois=[self.subject.std4_head_img])
                self.transform_roi("std4TOrs",  pathtype="abs", outdir=l_rs    , islin=True,    rois=[self.subject.std4_img])

            if self.subject.hasFMRI:    # connect RS with FMRI

                exfun_fmri = self.subject.epi.get_example_function("fmri")

                nl_fmri = os.path.join(nldir, "fmri")
                l_fmri = os.path.join(ldir, "fmri")

                os.makedirs(nl_fmri, exist_ok=True)
                os.makedirs(l_fmri, exist_ok=True)

                if "rs" in _from and "fmri" in _to:
                    self.transform_roi("rsTOfmri", pathtype="abs", outdir=nl_fmri, outname=self.subject.label + "_rs_examplefunc", islin=False, rois=[exfun])
                    self.transform_roi("rsTOfmri", pathtype="abs", outdir=l_fmri,  outname=self.subject.label + "_rs_examplefunc", islin=True,  rois=[exfun])

                if "fmri" in _from and "rs" in _to:
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

            if "fmri" in _from and "hr" in _to:
                self.transform_roi("fmriTOhr", pathtype="abs", outdir=nl_t1, outname=self.subject.label + "_fmri_example_func", islin=False,    rois=[exfun])
                self.transform_roi("fmriTOhr", pathtype="abs", outdir=l_t1,  outname=self.subject.label + "_fmri_example_func", islin=True,     rois=[exfun])

            if "hr" in _from and "fmri" in _to:
                self.transform_roi("hrTOfmri", pathtype="abs", outdir=nl_fmri, islin=False,    rois=[self.subject.t1_brain_data])
                self.transform_roi("hrTOfmri", pathtype="abs", outdir=l_fmri,  islin=True,     rois=[self.subject.t1_data])

            if "fmri" in _from and "std" in _to:
                self.transform_roi("fmriTOstd", pathtype="abs", outdir=nl_std, outname=self.subject.label + "_fmri_example_func", islin=False,   rois=[exfun])
                self.transform_roi("fmriTOstd", pathtype="abs", outdir=l_std,  outname=self.subject.label + "_fmri_example_func", islin=True,    rois=[exfun])

            if extended is True and "std" in _from and "fmri" in _to:
                self.transform_roi("stdTOfmri", pathtype="abs", outdir=nl_fmri, islin=False,  rois=[self.subject.std_head_img])
                self.transform_roi("stdTOfmri", pathtype="abs", outdir=l_fmri, islin=True,    rois=[self.subject.std_img])

            if self.subject.hasRS:

                if "fmri" in _from and "std4" in _to:
                    self.transform_roi("fmriTOstd4", pathtype="abs", outdir=nl_std4, outname=self.subject.label + "_fmri_example_func", islin=False, rois=[exfun])
                    self.transform_roi("fmriTOstd4", pathtype="abs", outdir=l_std4, outname=self.subject.label + "_fmri_example_func", islin=True,   rois=[exfun])

                if extended is True and "std4" in _from and "fmri" in _to:
                    self.transform_roi("std4TOfmri", pathtype="abs", outdir=nl_fmri, islin=False, rois=[self.subject.std4_head_img])
                    self.transform_roi("std4TOfmri", pathtype="abs", outdir=l_fmri, islin=True,   rois=[self.subject.std4_img])

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

            if "t2" in _from and "hr" in _to:
                self.transform_roi("t2TOhr"  , pathtype="abs",  outdir=nl_t1  , islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOhr"  , pathtype="abs",  outdir=l_t1   , islin=True,  rois=[self.subject.t2_brain_data])

            if "hr" in _from and "t2" in _to:
                self.transform_roi("hrTOt2"  , pathtype="abs",  outdir=nl_t2  , islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOt2"  , pathtype="abs",  outdir=l_t2   , islin=True,  rois=[self.subject.t1_brain_data])

            if "t2" in _from and "std" in _to:
                self.transform_roi("t2TOstd" , pathtype="abs",  outdir=nl_std , islin=False, rois=[self.subject.t2_data])
                self.transform_roi("t2TOstd" , pathtype="abs",  outdir=l_std  , islin=True,  rois=[self.subject.t2_brain_data])

            if extended is True and "std" in _from and "t2" in _to:
                self.transform_roi("stdTOt2" , pathtype="abs",  outdir=nl_t2  , islin=False, rois=[self.subject.std_head_img])
                self.transform_roi("stdTOt2" , pathtype="abs",  outdir=l_t2   , islin=True,  rois=[self.subject.std_img])

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

            if "hr" in _from and "dti" in _to:
                self.transform_roi("hrTOdti"  , pathtype="abs",  outdir=nl_dti , islin=False, rois=[self.subject.t1_data])
                self.transform_roi("hrTOdti"  , pathtype="abs",  outdir=l_dti  , islin=True,  rois=[self.subject.t1_brain_data])

            if "dti" in _from and "hr" in _to:
                self.transform_roi("dtiTOhr"  , pathtype="abs",  outdir=nl_t1  , outname=self.subject.label + "_nodif_data", islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOhr"  , pathtype="abs",  outdir=l_t1   , outname=self.subject.label + "_nodif_brain_data", islin=True,  rois=[self.subject.dti_nodiff_brain_data])

            if "dti" in _from and "std" in _to:
                self.transform_roi("dtiTOstd" , pathtype="abs",  outdir=nl_std , outname=self.subject.label + "_nodif_data", islin=False, rois=[self.subject.dti_nodiff_data])
                self.transform_roi("dtiTOstd" , pathtype="abs",  outdir=l_std  , outname=self.subject.label + "_nodif_brain_data", islin=True,  rois=[self.subject.dti_nodiff_brain_data])

            if extended is True and "std" in _from and "dti" in _to:
                self.transform_roi("stdTOdti" , pathtype="abs",  outdir=nl_dti , islin=False, rois=[self.subject.std_head_img])
                self.transform_roi("stdTOdti" , pathtype="abs",  outdir=l_dti  , islin=True,  rois=[self.subject.std_img])

            if self.subject.hasT2 is True:

                if "t2" in _from and "dti" in _to:
                    self.transform_roi("t2TOdti", pathtype="abs", outdir=nl_dti, islin=False, rois=[self.subject.t2_data])
                    self.transform_roi("t2TOdti", pathtype="abs", outdir=l_dti, islin=True, rois=[self.subject.t2_brain_data])

                if "dti" in _from and "t2" in _to:
                    self.transform_roi("dtiTOt2", pathtype="abs", outdir=nl_t2, outname=self.subject.label + "_nodif_data", islin=False, rois=[self.subject.dti_nodiff_data])
                    self.transform_roi("dtiTOt2", pathtype="abs", outdir=l_t2, outname=self.subject.label + "_nodif_brain_data", islin=True, rois=[self.subject.dti_nodiff_brain_data])

    # open fsleyes with a sequences list coregistered to one given seq = [t1, t2, dti, rs, fmri, std, std4]
    def view_space_images(self, seq, _from=None):

        outdir = os.path.join(self.subject.roi_dir, "check_coregistration", seq)
        os.makedirs(outdir, exist_ok=True)

        if seq == "t1":
            if self.subject.hasFMRI and "fmri" in _from:

                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_nonlin" + "_hr")) is False:
                    self.transform_roi("fmriTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_lin" + "_hr")) is False:
                        self.transform_roi("fmriTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasRS and "rs" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_nonlin" + "_hr")) is False:
                    self.transform_roi("rsTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_lin" + "_hr")) is False:
                    self.transform_roi("rsTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasDTI and "dti" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_nonlin" + "_hr")) is False:
                    self.transform_roi("dtiTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",          islin=False, rois=[self.subject.dti_nodiff_data])
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_brain_lin" + "_hr")) is False:
                    self.transform_roi("dtiTOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",       islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2 and "t2" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t2_nonlin" + "_hr")) is False:
                    self.transform_roi("t2TOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",      islin=False, rois=[self.subject.t2_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t2_brain_lin" + "_hr")) is False:
                    self.transform_roi("t2TOhr", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin",   islin=True, rois=[self.subject.t2_brain_data])

            imcp(self.subject.t1_brain_data, outdir)

        elif seq == "t2":
            if self.subject.hasFMRI and "fmri" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_nonlin" + "_t2")) is False:
                    self.transform_roi("fmriTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_lin" + "_t2")) is False:
                    self.transform_roi("fmriTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasRS and "rs" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_nonlin" + "_t2")) is False:
                    self.transform_roi("rsTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_lin" + "_t2")) is False:
                    self.transform_roi("rsTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasDTI and "dti" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_nonlin" + "_t2")) is False:
                    self.transform_roi("dtiTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",          islin=False, rois=[self.subject.dti_nodiff_data])
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_brain_lin" + "_t2")) is False:
                    self.transform_roi("dtiTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",       islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT1 and "t1" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t1_nonlin" + "_t2")) is False:
                    self.transform_roi("hrTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",      islin=False, rois=[self.subject.t1_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t1_brain_lin" + "_t2")) is False:
                    self.transform_roi("hrTOt2", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",   islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.t2_brain_data, outdir)

        elif seq == "dti":
            if self.subject.hasFMRI and "fmri" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_nonlin" + "_dti")) is False:
                    self.transform_roi("fmriTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_lin" + "_dti")) is False:
                    self.transform_roi("fmriTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasRS and "rs" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_nonlin" + "_dti")) is False:
                    self.transform_roi("rsTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_lin" + "_dti")) is False:
                    self.transform_roi("rsTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasT2 and "t2" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t2_nonlin" + "_dti")) is False:
                    self.transform_roi("t2TOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",    islin=False, rois=[self.subject.t2_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t2_brain_lin" + "_dti")) is False:
                    self.transform_roi("t2TOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin", islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1 and "t1" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t1_nonlin" + "_dti")) is False:
                    self.transform_roi("hrTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t1_brain_lin" + "_dti")) is False:
                    self.transform_roi("hrTOdti", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.dti_nodiff_brain_data, outdir)

        elif seq == "rs":
            if self.subject.hasFMRI and "fmri" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_nonlin" + "_rs")) is False:
                    self.transform_roi("fmriTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_lin" + "_rs")) is False:
                    self.transform_roi("fmriTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasDTI and "dti" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_nonlin" + "_rs")) is False:
                    self.transform_roi("dtiTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",      islin=False, rois=[self.subject.dti_nodiff_data])
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_brain_lin" + "_rs")) is False:
                    self.transform_roi("dtiTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",   islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2 and "t2" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t2_nonlin" + "_rs")) is False:
                    self.transform_roi("t2TOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",    islin=False, rois=[self.subject.t2_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t2_brain_lin" + "_rs")) is False:
                    self.transform_roi("t2TOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin", islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1 and "t1" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t1_nonlin" + "_rs")) is False:
                    self.transform_roi("hrTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t1_brain_lin" + "_rs")) is False:
                    self.transform_roi("hrTOrs", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.rs_examplefunc, outdir)

        elif seq == "fmri":
            if self.subject.hasRS and "rs" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_nonlin" + "_fmri")) is False:
                    self.transform_roi("rsTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin", islin=False, rois=[self.subject.rs_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_lin" + "_fmri")) is False:
                    self.transform_roi("rsTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",    islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasDTI and "dti" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_nonlin" + "_fmri")) is False:
                    self.transform_roi("dtiTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",    islin=False, rois=[self.subject.dti_nodiff_data])
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_brain_lin" + "_fmri")) is False:
                    self.transform_roi("dtiTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin", islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2 and "t2" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t2_nonlin" + "_fmri")) is False:
                    self.transform_roi("t2TOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",    islin=False, rois=[self.subject.t2_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t2_brain_lin" + "_fmri")) is False:
                    self.transform_roi("t2TOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin", islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1 and "t1" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t1_nonlin" + "_fmri")) is False:
                    self.transform_roi("hrTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t1_brain_lin" + "_fmri")) is False:
                    self.transform_roi("hrTOfmri", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.fmri_examplefunc, outdir)

        elif seq == "std":
            if self.subject.hasRS and "rs" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_nonlin" + "_std")) is False:
                    self.transform_roi("rsTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin",    islin=False, rois=[self.subject.rs_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_lin" + "_std")) is False:
                    self.transform_roi("rsTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",       islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasFMRI and "fmri" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_nonlin" + "_std")) is False:
                    self.transform_roi("fmriTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_lin" + "_std")) is False:
                    self.transform_roi("fmriTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasDTI and "dti" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_nonlin" + "_std")) is False:
                    self.transform_roi("dtiTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",     islin=False, rois=[self.subject.dti_nodiff_data])
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_brain_lin" + "_std")) is False:
                    self.transform_roi("dtiTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",  islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2 and "t2" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t2_nonlin" + "_std")) is False:
                    self.transform_roi("t2TOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",     islin=False, rois=[self.subject.t2_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t2_brain_lin" + "_std")) is False:
                    self.transform_roi("t2TOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin",  islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1 and "t1" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t1_nonlin" + "_std")) is False:
                    self.transform_roi("hrTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t1_brain_lin" + "_std")) is False:
                    self.transform_roi("hrTOstd", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.std_img, outdir)

        elif seq == "std4":
            if self.subject.hasRS and "rs" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_nonlin" + "_std4")) is False:
                    self.transform_roi("rsTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_nonlin",    islin=False, rois=[self.subject.rs_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_rs_example_func_lin" + "_std4")) is False:
                    self.transform_roi("rsTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_rs_example_func_lin",       islin=True, rois=[self.subject.rs_examplefunc])

            if self.subject.hasFMRI and "fmri" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_nonlin" + "_std4")) is False:
                    self.transform_roi("fmriTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_nonlin", islin=False, rois=[self.subject.fmri_examplefunc])
                if imtest(os.path.join(outdir, self.subject.label + "_fmri_example_func_lin" + "_std4")) is False:
                    self.transform_roi("fmriTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_fmri_example_func_lin",    islin=True, rois=[self.subject.fmri_examplefunc])

            if self.subject.hasDTI and "dti" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_nonlin" + "_std4")) is False:
                    self.transform_roi("dtiTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_nonlin",     islin=False, rois=[self.subject.dti_nodiff_data])
                if imtest(os.path.join(outdir, self.subject.label + "_nodif_brain_lin" + "_std4")) is False:
                    self.transform_roi("dtiTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_nodif_brain_lin",  islin=True, rois=[self.subject.dti_nodiff_brain_data])

            if self.subject.hasT2 and "t2" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t2_nonlin" + "_std4")) is False:
                    self.transform_roi("t2TOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_nonlin",     islin=False, rois=[self.subject.t2_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t2_brain_lin" + "_std4")) is False:
                    self.transform_roi("t2TOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t2_brain_lin",  islin=True, rois=[self.subject.t2_brain_data])

            if self.subject.hasT1 and "t1" in _from:
                if imtest(os.path.join(outdir, self.subject.label + "_t1_nonlin" + "_std4")) is False:
                    self.transform_roi("hrTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_nonlin",     islin=False, rois=[self.subject.t1_data])
                if imtest(os.path.join(outdir, self.subject.label + "_t1_brain_lin" + "_std4")) is False:
                    self.transform_roi("hrTOstd4", pathtype="abs", outdir=outdir, outname=self.subject.label + "_t1_brain_lin",  islin=True, rois=[self.subject.t1_brain_data])

            imcp(self.subject.std4_img, outdir)

        os.system("fsleyes " + outdir + "/*.* &")

    # ==============================================================================================================
