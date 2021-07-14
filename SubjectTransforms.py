import os

from myfsl.utils.run import rrun
from utility.fslfun import runsystem
from utility.images import imtest, imrm, imcp, imgname, get_head_from_brain


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
    # TRANSFORMS
    # ==================================================================================================================================================
    # path_type =   "standard"      : a roi name, located in the default folder (subjectXX/s1/roi/reg_YYY/INPUTPATH),
    #	            "rel"			: a path relative to SUBJECT_DIR (subjectXX/s1/INPUTPATH)
    #               "abs"			: a full path (INPUTPATH)
    def transform_roi(self, regtype, pathtype="standard", mask="", orf="", thresh=0.2, islin=True, std_img="", rois=[]):

        if std_img != "":
            if imtest(std_img) is False:
                print("ERROR: given standard image file (" + std_img + ") does not exist......exiting")
                return
        else:
            std_img = self._global.fsl_std_mni_2mm_brain

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
    # TO HR

    def transform_nl_std2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_t1_dir, "std2hr_warp"))

    def transform_l_std2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + os.path.join(self.subject.roi_t1_dir, roi_name + "_hr") + " --warp=" + os.path.join(self.subject.roi_t1_dir, "std2hr_warp"))

    def transform_nl_std42hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std4_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(self.subject.roi_t1_dir, roi_name + "_std") + " -applyisoxfm 2")
        rrun("applywarp -i " + os.path.join(self.subject.roi_t1_dir, roi_name + "_std") + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_t1_dir, "std2hr_warp"))
        imrm(os.path.join(self.subject.roi_t1_dir, roi_name + "_std"))

    def transform_l_std42hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std4_dir, roi)

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(self.subject.roi_t1_dir, roi_name + "_std") + " -applyisoxfm 2")
        rrun("applywarp -i " + os.path.join(self.subject.roi_t1_dir, roi_name + "_std") + " -r " + self.subject.t1_data + " -o " + os.path.join(self.subject.roi_epi_dir, roi_name + "_hr") + " --warp=" + os.path.join(self.subject.roi_t1_dir, "std2hr_warp"))
        imrm(os.path.join(self.subject.roi_t1_dir, roi + "_std"))

    def transform_nl_epi2hr(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            epi2hr_warp = os.path.join(self.subject.roi_t1_dir, "rs2hr_warp")
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            epi2hr_warp = os.path.join(self.subject.roi_t1_dir, "fmri2hr_warp")

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + epi2hr_warp)

    def transform_l_epi2hr(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            epi2hr_mat = os.path.join(self.subject.roi_t1_dir, "rs2hr.mat")
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            epi2hr_mat = os.path.join(self.subject.roi_t1_dir, "fmri2hr.mat")

        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + os.path.join(self.subject.roi_t1_dir, roi_name + "_hr") + " -applyxfm -init " + epi2hr_mat + " -interp trilinear")

    def transform_nl_dti2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_dti_dir, roi + "_dti")
        if path_type == "abs":
            input_roi = roi
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")
        if self.subject.has_T2 is True:
            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_t1_dir, "dti2hr_warp"))
        else:
            rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.subject.roi_t1_dir, "dti2hr.mat") + " -interp trilinear")

    def transform_l_dti2hr(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_t1_dir, roi_name + "_hr")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)

        if self.subject.has_T2 is True:
            rrun("applywarp -i " + input_roi + " -r " + self.subject.t1_data + " -o " + os.path.join(self.subject.roi_t1_dir, roi + "_hr") + " --warp=" + os.path.join(self.subject.roi_t1_dir, "dti2hr_warp"))
        else:
            rrun("flirt -in " + input_roi + " -ref " + self.subject.t1_brain_data + " -out " + os.path.join(self.subject.roi_t1_dir, roi + "_hr") + " -applyxfm -init " + os.path.join(self.subject.roi_dti_dir, "dti2hr.mat") + " -interp trilinear")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO EPI

    def transform_nl_std2epi(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            std2epi_warp= os.path.join(roi_epi_dir, "std2rs_warp")

        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            std2epi_warp= os.path.join(roi_epi_dir, "std2fmri_warp")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("applywarp -i " + input_roi + " -r " + examplefunc + " -o " + output_roi + " --warp=" + std2epi_warp)

    def transform_l_std2epi(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            std2epi_mat = os.path.join(roi_epi_dir, "std2rs.mat")

        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            std2epi_mat = os.path.join(roi_epi_dir, "std2fmri.mat")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + examplefunc + " -out " + output_roi + " -applyxfm -init " + std2epi_mat)

    def transform_nl_std42epi(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            hr2epi_warp = os.path.join(roi_epi_dir, "std2rs_warp")
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            hr2epi_warp = os.path.join(roi_epi_dir, "std2fmri_warp")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_std4_dir, "roi")

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(roi_epi_dir, roi_name + "_std") + " -applyisoxfm 2")
        rrun("applywarp -i " + os.path.join(roi_epi_dir, roi_name + "_std") + " -r " + examplefunc + " -o " + output_roi + " --warp=" + hr2epi_warp)
        imrm(os.path.join(roi_epi_dir, roi_name + "_std"))

    def transform_l_std42epi(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            hr2epi_warp = os.path.join(roi_epi_dir, "std2rs_warp")
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            hr2epi_warp = os.path.join(roi_epi_dir, "std2fmri_warp")

        output_roi = os.path.join(roi_epi_dir, roi_name + "_epi")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_std4_dir, "roi")

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + os.path.join(roi_epi_dir, roi_name + "_std") + " -applyisoxfm 2")
        rrun("applywarp -i " + os.path.join(roi_epi_dir, roi_name + "_std") + " -r " + examplefunc + " -o " + os.path.join(roi_epi_dir, roi_name + "_epi") + " --warp=" + hr2epi_warp)
        imrm(os.path.join(roi_epi_dir, roi_name + "_std"))


    def transform_nl_hr2epi(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            hr2epi_mat  = os.path.join(roi_epi_dir, "hr2epi.mat")
        elif epi_label.startsWith("fmri"):
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

        print("the hr2epi NON linear transformation does not exist.....using the linear one")
        rrun("flirt -in " + input_roi + " -ref " + examplefunc + " -out " + output_roi + " -applyxfm -init " + hr2epi_mat + " -interp trilinear")


    def transform_l_hr2epi(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            hr2epi_mat  = os.path.join(roi_epi_dir, "hr2rs.mat")
        elif epi_label.startsWith("fmri"):
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

        rrun("flirt -in " + input_roi + " -ref " + examplefunc + " -out " + output_roi + " -applyxfm -init " + hr2epi_mat + " -interp trilinear")

    def transform_nl_dti2epi(self, path_type, roi_name, roi, std_img):
        print("registration type: dti2epi NOT SUPPORTED...exiting")

    def transform_l_dti2epi(self, path_type, roi_name, roi, std_img):
        print("registration type: dti2epi NOT SUPPORTED...exiting")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD

    def transform_nl_hr2std(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_std_dir, roi_name + "_std")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)


        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_t1_dir, "hr2std_warp"))

    def transform_l_hr2std(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_std_dir, roi_name + "_std")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.subject.roi_std_dir, roi_name + "_std") + " --warp=" + os.path.join(self.subject.roi_t1_dir, "hr2std_warp"))

    def transform_nl_epi2std(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        output_roi = os.path.join(self.subject.roi_std_dir, roi_name + "_std")

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_std_dir, "epi2std_warp"))

    def transform_l_epi2std(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc

        output_roi = os.path.join(self.subject.roi_std_dir, roi_name + "_std")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.subject.roi_std_dir, roi_name + "_std") + " --warp=" + os.path.join(self.subject.roi_std_dir, "epi2std_warp"))

    def transform_nl_dti2std(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_std_dir, roi_name + "_std")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_std_dir, "dti2std_warp"))

    def transform_l_dti2std(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_std_dir, roi_name + "_std")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_dti_dir, roi)

        rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.subject.roi_std_dir, roi_name + "_std") + " --warp=" + os.path.join(self.subject.roi_std_dir, "epi2std_warp"))

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO STD4

    def transform_nl_std2std4(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_std4_dir, roi_name + "_std4")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")

    def transform_l_epi2std4(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
            epi2std_mat = os.path.join(self.subject.roi_std_dir, "rs2std.mat")
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc
            epi2std_mat = os.path.join(self.subject.roi_std_dir, "fmri2std.mat")

        output_roi = os.path.join(self.subject.roi_std4_dir, roi_name + "_std4")

        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(roi_epi_dir, roi)

        if imtest(input_roi) is False:
            print("error......input_roi (" + input_roi + ") is missing....exiting")

        rrun("flirt -in " + input_roi + " -ref " + examplefunc + " -out " + os.path.join(self.subject.roi_std4_dir, roi_name + "_std2") + " -applyxfm -init " + epi2std_mat + " -interp trilinear")
        rrun("flirt -in " + os.path.join(self.subject.roi_std4_dir, roi_name + "_std2") + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")
        imrm([os.path.join(self.subject.roi_std4_dir, roi_name + "_std2")])

    def transform_nl_epi2std4(self, path_type, roi_name, roi, std_img, epi_label="rs"):

        if epi_label == "rs":
            roi_epi_dir = self.subject.roi_rs_dir
            examplefunc = self.subject.rs_examplefunc
        elif epi_label.startsWith("fmri"):
            roi_epi_dir = self.subject.roi_fmri_dir
            examplefunc = self.subject.fmri_examplefunc

        output_roi = os.path.join(self.subject.roi_std4_dir, roi_name + "_std")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = os.path.join(self.subject.dir, roi)
        else:
            input_roi = os.path.join(self.subject.roi_epi_dir, roi)

        try:
            std_img = get_head_from_brain(std_img)

            rrun("applywarp -i " + input_roi + " -r " + std_img + " -o " + os.path.join(self.subject.roi_std4_dir, roi_name) + "_std2" + " --warp=" + os.path.join(self.subject.roi_std_dir, "epi2std_warp"))
            # rrun("flirt -in " + os.path.join(self.subject.roi_std4_dir, roi_name + "_std2") + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")
            # imrm(os.path.join(self.subject.roi_std4_dir, roi_name + "_std2"))
        except Exception as e:
            raise e


    def transform_l_std2std4(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_std4_dir, roi_name + "_std4")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        rrun("flirt -in " + input_roi + " -ref " + std_img + " -out " + output_roi + " -applyisoxfm 4")

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # TO DTI

    def transform_nl_hr2dti(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)

        if self.subject.has_T2 is True and imtest(os.path.join(self.subject.roi_t1_dir, "hr2dti_warp")) is True:
            rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nobrain_diff") + " -o " + output_roi + " --warp=" + os.path.join(self.subject.roi_t1_dir, "hr2dti_warp"))
        else:
            print("did not find the non linear registration from HR 2 DTI, I used a linear one")
            rrun("flirt -in " + input_roi + " -ref " + os.path.join(self.subject.roi_dti_dir, "nobrain_diff") + " -out " + output_roi + " -applyxfm -init " + os.path.join(self.subject.roi_dti_dir, "hr2dti.mat") + " -interp trilinear")

    def transform_l_hr2dti(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_t1_dir, roi)

        if self.subject.has_T2 is True:
            rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nobrain_diff") + " -o " + os.path.join(self.subject.roi_dti_dir, roi_name + "_dti") + " --warp=" + os.path.join(self.subject.roi_t1_dir, "hr2dti_warp"))
        else:
            rrun("flirt -in " + input_roi + " -ref " + os.path.join(self.subject.roi_dti_dir, "nobrain_diff") + " -out " + os.path.join(self.subject.roi_dti_dir, roi_name + "_dti") + " -applyxfm -init " + os.path.join(self.subject.roi_dti_dir, "hr2dti.mat") + " -interp trilinear")

    def transform_nl_epi2dti(self, path_type, roi_name, roi, std_img, epi_label="rs"):
        # output_roi=os.path.join(self.subject.roi_dti_dir,roi_name + "_dti"
        # if [ "$path_type" = abs ]; then
        #     input_roi=roi
        # else:
        #     input_roi=os.path.join(self.subject.roi_epi_dir, roi
        # fi
        # rrun("applywarp -i " + input_roi -r os.path.join(self.subject.roi_dti_dir, nobrain_diff -o os.path.join(self.subject.roi_std4_dir, roi_name + "_std2" --premat os.path.join(self.subject.roi_t1_dir,epi2hr.mat --warp=os.path.join(self.subject.roi_std_dir, hr2std_warp --postmat os.path.join(self.subject.roi_dti_dir, std2dti.mat;
        print("registration type: epi2dti NOT SUPPORTED...exiting")

    def transform_l_epi2dti(self, path_type, roi_name, roi, std_img, epi_label="rs"):
        print("registration type: epi2dti NOT SUPPORTED...exiting")

    def transform_nl_std2dti(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nodif_brain") + " -o " + output_roi + " --warp=" + os.path.join( self.subject.roi_dti_dir, "std2dti_warp"))

    def transform_l_std2dti(self, path_type, roi_name, roi, std_img):
        output_roi = os.path.join(self.subject.roi_dti_dir, roi_name + "_dti")
        if path_type == "abs":
            input_roi = roi
        elif path_type == "rel":
            input_roi = self.subject.roi_dir
        else:
            input_roi = os.path.join(self.subject.roi_std_dir, "roi")

        rrun("applywarp -i " + input_roi + " -r " + os.path.join(self.subject.roi_dti_dir, "nodif_brain") + " -o " + os.path.join(self.subject.roi_dti_dir, roi_name + "_dti") + " --warp=" + os.path.join(self.subject.roi_dti_dir, "std2dti_warp"))

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def transform_mpr(self, std_img="", std_img_mask_dil="", std_img_label="std"):

        if std_img == "":
            std_img         = os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm_brain")
            std_head_img    = os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm")

        if std_img_mask_dil == "":
            std_img_mask_dil        = os.path.join(self.subject.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask_dil")

        if imtest(std_img) is False:
            print("file std_img: " + std_img + ".nii.gz is not present...skipping transforms_mpr")
            return

        if imtest(std_img_mask_dil) is False:
            print("file STD_IMAGE_MASK: " + std_img_mask_dil + ".nii.gz is not present...skipping transforms_mpr")
            return

        if imtest(self.subject.t1_brain_data) is False:
            print("file T1_BRAIN_DATA: " + self.subject.t1_brain_data + ".nii.gz is not present...skipping transforms_mpr")
            return

        print(self.subject.label + " :STARTED : nonlin t1-standard coregistration")

        # hr <--> std

        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label), exist_ok=True)
        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4"), exist_ok=True)
        os.makedirs(self.subject.roi_t1_dir, exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # ---- HIGHRES <--------> STANDARD
        # => hr2std.mat
        hr2std = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2std")
        if os.path.isfile(hr2std + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + std_img + " -out " + hr2std + " -omat " + hr2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # => hrhead2std.mat
        hrhead2std = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hrhead2std")
        if os.path.isfile(hrhead2std + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + std_head_img + " -out " + hrhead2std + " -omat " + hr2std + ".mat -cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        # # => std2hr.mat
        std2hr = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr")
        if os.path.isfile(std2hr + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + std2hr + ".mat " + hr2std + ".mat")

        # NON LINEAR
        # => hr2std_warp
        hr2std_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2std_warp")
        if imtest(hr2std_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff= " + hrhead2std + ".mat --cout=" + hr2std_warp + " --iout=" + hr2std + " --jout=" + os.path.join(self.subject.roi_t1_dir, "hr2hr_jac") + " --config=T1_2_MNI152_2mm --ref=" + std_head_img + " --refmask=" + std_img_mask_dil + "--warpres=10,10,10")

        # => std2hr_warp
        std_warp2hr = os.path.join(self.subject.roi_t1_dir, std_img_label + "2hr_warp")
        if imtest(std_warp2hr) is False:
            rrun("invwarp -r " + self.subject.t1_data + " -w " + hr2std_warp + " -o " + std_warp2hr)

        ## => hr2${std_img_label}.nii.gz
        # [ `$FSLDIR/bin/imtest $ROI_DIR/reg_${std_img_label}/hr2std` = 0 ] && rrun("applywarp -i " + T1_BRAIN_DATA -r $STD_IMAGE -o $ROI_DIR/reg_${std_img_label}/hr2std -w $ROI_DIR/reg_${std_img_label}/hr2std_warp

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # hr <--> std4
        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4"), exist_ok=True)

        hrhead2std4 = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hrhead2std")
        hr2std4 = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2std")

        std42hr = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr")
        hr2std4_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2std_warp.nii.gz")
        std42hr_warp = os.path.join(self.subject.roi_t1_dir, std_img_label + "42hr_warp.nii.gz")

        if os.path.isfile(hr2std4 + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_brain_data + " -ref " + self._global.fsl_std_mni_4mm_brain + " -omat " + hr2std4 + ".mat")

        if os.path.isfile(hrhead2std4 + ".mat") is False:
            rrun("flirt -in " + self.subject.t1_data + " -ref " + self._global.fsl_std_mni_4mm_head + " -omat " + hrhead2std4 + ".mat")

        if os.path.isfile(std42hr + ".mat") is False:
            rrun("convert_xfm -omat " + std42hr + ".mat" + " -inverse " + hr2std4 + ".mat")

        if imtest(hr2std4_warp) is False:
            rrun("fnirt --in=" + self.subject.t1_data + " --aff=" + hrhead2std4 + ".mat" + " --cout=" + hr2std4_warp + " --iout=" + hr2std4 +
                 " --jout=" + hr2std4 + "_jac" + " --config=" + self._global.fsl_std_mni_4mm_brain_conf +
                 " --ref=" + self._global.fsl_std_mni_4mm_head + " --refmask=" + self._global.fsl_std_mni_4mm_brain_mask_dil + " --warpres=10,10,10")

        if imtest(std42hr_warp) is False:
            rrun("invwarp -w " + hr2std4_warp + " -o " + std42hr_warp + " -r " + self.subject.t1_data)


    def transform_epi(self, type='fmri', do_bbr=True, std_img_label="std", std_img="", std_img_head="", std_img_mask_dil="", wmseg=""):

        if type == 'fmri':
            data        = self.subject.fmri_data
            folder      = self.subject.fmri_dir
            label       = self.subject.fmri_image_label
            examplefunc = self.subject.fmri_examplefunc
            roi_dir     = self.subject.roi_fmri_dir
            epi2hr      = os.path.join(self.subject.roi_t1_dir, "fmri2hr")
            hr2epi_mat  = self.subject.hr2fmri_mat
            epi2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "fmri2std")
            std2epi     = os.path.join(self.subject.roi_fmri_dir, std_img_label + "2fmri")

        else:
            data        = self.subject.rs_data
            folder      = self.subject.rs_dir
            label       = self.subject.rs_image_label
            examplefunc = self.subject.rs_examplefunc
            roi_dir     = self.subject.roi_rs_dir
            epi2hr      = os.path.join(self.subject.roi_t1_dir, "rs2hr")
            hr2epi_mat  = self.subject.hr2rs_mat
            epi2std     = os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "rs2std")
            std2epi     = os.path.join(self.subject.roi_rs_dir, std_img_label + "2rs")
            mask_std4   = self.subject.rs_final_regstd_mask


        if std_img == "":
            std_img = self._global.fsl_std_mni_2mm_brain

        if std_img_head == "":
            std_img_head = self._global.fsl_std_mni_2mm_head

        if std_img_mask_dil == "":
            std_img_mask_dil = self._global.fsl_std_mni_2mm_brain_mask_dil

        if wmseg == "":
            wmseg = self.subject.t1_segment_wm_bbr_path

        os.makedirs(folder, exist_ok=True)
        os.makedirs(os.path.join(self.subject.roi_dir, "reg_" + std_img_label), exist_ok=True)

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if imtest(self.subject.t1_brain_data) is False:
            print("returning from transform_epi....t1_brain_data (" + self.subject.t1_brain_data + ") is missing")
            return

        if imtest(std_img) is False:
            ("returning from transform_epi....standard image (" + std_img + ") is missing")

        if imtest(examplefunc) is False:
            rrun("fslmaths " + data + " " + os.path.join(folder, "prefiltered_func_data") + " -odt float")
            rrun("fslroi " + os.path.join(folder, "prefiltered_func_data") + " " + examplefunc + " 100 1")
            rrun("bet2 " + examplefunc + " " + examplefunc + " -f 0.3")

            rrun("imrm " + os.path.join(folder, "prefiltered_func_data*"))

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #  EPI <--> HIGHRES
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if do_bbr is True:
            # BBR (taken from $FSLDIR/bin/epi_reg.sh)
            rrun("flirt -ref " + self.subject.t1_brain_data + " -in " + examplefunc + " -dof 6 -omat " + epi2hr + "_init.mat")

            if imtest(self.subject.t1_segment_wm_bbr_path) is False:
                print("Running FAST segmentation for subj " + self.subject.label)
                temp_dir = os.path.join(self.subject.roi_t1_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                rrun("fast -o " + os.path.join(temp_dir, "temp_" + self.subject.t1_brain_data))
                rrun("fslmaths " + os.path.join(temp_dir, "temp_pve_2") + " -thr 0.5 -bin " + self.subject.t1_segment_wm_bbr_path)
                runsystem("rm -rf " + temp_dir)

            # => epi2hr.mat
            if os.path.isfile(epi2hr + ".mat") is False:
                rrun("flirt -ref " + self.subject.t1_data + " -in " + examplefunc + " -dof 6 -cost bbr -wmseg " + self.subject.t1_segment_wm_bbr_path + " -init " + epi2hr + "_init.mat" + " -omat " + epi2hr + ".mat" + " -out " + epi2hr + " -schedule " + os.path.join(self.subject.fsl_dir, "etc", "flirtsch", "bbr.sch"))

            # => epi2hr.nii.gz
            if imtest(epi2hr) is False:
                rrun("applywarp -i " + examplefunc + " -r " + self.subject.t1_data + " -o " + epi2hr + " --premat=" + epi2hr + ".mat" + " --interp=spline")

            runsystem("rm " + epi2hr + "_init.mat")
        else:
            # NOT BBR
            if os.path.isfile(epi2hr + ".mat") is False:
                rrun("flirt -in " + examplefunc + " -ref " + self.subject.t1_brain_data + " -out " + epi2hr + " -omat " + epi2hr + ".mat" + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")

        if os.path.isfile(hr2epi_mat) is False:
            rrun("convert_xfm -inverse -omat " + hr2epi_mat + " " + epi2hr + ".mat")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # EPI <--> STANDARD
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # => epi2std.mat (as concat)
        if os.path.isfile(epi2std + ".mat") is False:
            rrun("convert_xfm -omat " + epi2std + ".mat" + " -concat " + os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2std.mat") + " " + epi2hr + ".mat")

        # => std2epi.mat
        if os.path.exists(std2epi + ".mat") is False:
            rrun("convert_xfm -inverse -omat " + std2epi + ".mat " + epi2std + ".mat")

        # => $ROI_DIR/reg_${std_img_label}/epi2std.nii.gz
        if imtest(epi2std) is False:
            rrun("flirt -ref " + std_img + " -in " + examplefunc + " -out " + epi2std + " -applyxfm -init " + epi2std + ".mat" + " -interp trilinear")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # epi -> highres -> standard
        if imtest(epi2std + "_warp") is False:
            rrun("convertwarp --ref=" + std_img_head + " --premat=" + epi2hr + ".mat" + " --warp1=" + os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2std_warp") + " --out=" + epi2std + "_warp")

        # invwarp: standard -> highres -> epi
        if imtest(std2epi + "_warp") is False:
            rrun("invwarp -r " + examplefunc + " -w " + os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "epi2std_warp") + " -o " + std2epi + "_warp")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # epi <-> standard4    (epi2hr + hr2std4_warp)
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        if type == "rs":
            hr2std4_warp = os.path.join(self.subject.roi_dir, "reg_" + std_img_label + "4", "hr2std_warp.nii.gz")
            if imtest(self.subject.rs2std4_warp) is False:
                rrun("convertwarp --refvol=" + self._global.fsl_std_mni_4mm_head + " --premat=" + epi2hr + ".mat" + " --warp1=" + hr2std4_warp + " --out=" + self.subject.rs2std4_warp)

            if imtest(self.subject.std42rs_warp) is False:
                rrun("invwarp -r " + examplefunc + " -w " + self.subject.rs2std4_warp + " -o " + self.subject.std42rs_warp)

            # self.subject.t1_brain_data_mask + " -o " + self.subject.rs_final_regstd_mask + "_std2" + " -r " + refvol + " -w " + os.path.join(self.subject.roi_dir, "reg_" + std_img_label, "hr2std_warp"))



    def transform_dti_t2(self):
        pass

    def transform_dti(self, std_img=""):

        if std_img == "":
            std_img = self._global.fsl_std_mni_2mm_brain

        if imtest(self.subject.t1_brain_data) is False:
            print("T1_BRAIN_DATA (" + self.subject.t1_brain_data + ") is missing....exiting")
            return

        if imtest(std_img) is False:
            print("standard image (" + std_img + ") is missing....exiting")
            return

        print(self.subject.label + ":						STARTED : nonlin nodiff-t1-standard coregistration")
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        roi_no_dif = os.path.join(self.subject.roi_dti_dir, "nodif")
        no_dif = os.path.join(self.subject.dti_dir, "nodif")
        if imtest(roi_no_dif + "_brain") is False:
            if imtest(no_dif + "_brain") is False:
                rrun("fslroi " + self.subject.dti_data + " " + no_dif + " 0 1")
                rrun("bet " + no_dif + " " + no_dif + "_brain -m -f 0.3")

            imcp(no_dif + "_brain", roi_no_dif + "_brain")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # dti -> highres
        dti2hr = os.path.join(self.subject.roi_t1_dir, "dti2hr")
        if os.path.exist(dti2hr + ".mat") is False:
            rrun("flirt -in " + no_dif + "_brain" + " -ref " + self.subject.t1_brain_data + " -out " + dti2hr + " -omat " + dti2hr + ".mat" +
                " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 7 -interp trilinear")

        if imtest(dti2hr + "_warp") is False:
            rrun("fnirt --in=" + roi_no_dif + "_brain" + " --ref=" + self.subject.t1_brain_data + " --aff=" + dti2hr + ".mat" + " --cout=" + dti2hr + "_warp" + " --iout=" + roi_no_dif + "_brain2hr_nl" + " -v &>" + dti2hr + "_nl.txt")

        # highres -> dti
        hr2dti = os.path.join(self.subject.roi_dti_dir, "hr2dti")
        if os.path.exist(hr2dti + ".mat") is False:
            rrun("convert_xfm -omat " + hr2dti + ".mat" + " -inverse " + dti2hr + ".mat")

        if imtest(hr2dti + "_warp") is False:
            rrun("invwarp -r " + roi_no_dif + "_brain" + " -w " + dti2hr + "_warp" + " -o " + hr2dti + "_warp")

        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # dti -> highres -> standard
        dti2std = os.path.join(self.subject.roi_std_dir, "dti2std")
        if imtest(dti2std + "_warp") is False:
            rrun("convertwarp --ref=" + std_img + " --warp1=" + os.path.join(self.subject.roi_t1_dir, "dti2hr_warp") + " --warp2=" + os.path.join(self.subject.roi_std_dir, "hr2std_warp") + " --out=" + dti2std + "_warp")

        # standard -> highres -> dti
        std2dti = os.path.join(self.subject.roi_dti_dir, "std2dti")
        if imtest(std2dti + "_warp") is False:
            rrun("invwarp -r " + roi_no_dif + "_brain" + " -w " + dti2std + "_warp" + " -o " + std2dti + "_warp")

        # 2: concat: standard -> highres -> dti
        # $FSLDIR/bin/convertwarp --ref=os.path.join(self.subject.roi_dti_dir, nodif_brain --warp1=os.path.join(self.subject.roi_t1_dir,standard2hr_warp --postmat=os.path.join(self.subject.roi_dti_dir, hr2dti --out=os.path.join(self.subject.roi_dti_dir, standard2dti_warp

    # ==================================================================================================================================================

