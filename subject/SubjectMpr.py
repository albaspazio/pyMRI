import datetime
import os
import traceback
from shutil import copyfile

from Global import Global
from myfsl.utils.run import rrun
from utility.fslfun import run, run_notexisting_img, runpipe, run_move_notexisting_img
from utility.images import imtest, immv, mass_images_move, imrm, imcp, quick_smooth, remove_ext
from utility.matlab import call_matlab_spmbatch, call_matlab_function_noret
from utility.utilities import sed_inplace, gunzip, write_text_file


# ==================================================================================================================================================
# ANATOMICAL
# ==================================================================================================================================================

class SubjectMpr:
    BIAS_TYPE_NO = 0
    BIAS_TYPE_WEAK = 1
    BIAS_TYPE_STRONG = 2

    def __init__(self, subject, _global):
        self.subject = subject
        self._global = _global

    # pre-processing:
    #   FIXING NEGATIVE RANGE
    #   REORIENTATION 2 STANDARD
    #   AUTOMATIC CROPPING
    #   LESION MASK
    #   BIAS FIELD CORRECTION
    def prebet(self,
               odn="anat", imgtype=1, smooth=10,
               biascorr_type=BIAS_TYPE_STRONG,
               do_reorient=True, do_crop=True,
               do_bet=True,
               do_overwrite=False,
               use_lesionmask=False, lesionmask=""
               ):
        niter = 5
        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage = self.subject.t1_data
            anatdir = os.path.join(self.subject.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            inputimage = self.subject.t2_data
            anatdir = os.path.join(self.subject.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        # check original image presence, otherwise exit
        if imtest(inputimage) is False:
            print("ERROR: (" + self.subject.label + ") input anatomical image is missing....exiting")
            return False

        # check given lesionmask presence, otherwise exit
        if use_lesionmask is True and imtest(lesionmask) is False:
            print("ERROR: (" + self.subject.label + ") given Lesion mask is missing....exiting")
            return False

        # I CAN START PROCESSING !
        try:

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            # os.chdir(anatdir)
            T1 = os.path.join(anatdir, T1)  # T1 is now an absolute path

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
            # if imtest(T1) is False:
            rrun("fslmaths " + inputimage + " " + T1, logFile=log)

            # cp lesionmask to anat dir then (even it does not exist) update variable lesionmask=os.path.join(anatdir, "lesionmask")
            if use_lesionmask is True:
                # I previously verified that it exists
                rrun("fslmaths", [lesionmask, os.path.join(anatdir, "lesionmask")])
                lesionmask = os.path.join(anatdir, "lesionmask")
                with open(logfile, "a") as text_file:
                    text_file.write("copied lesion mask " + lesionmask)
            else:
                lesionmask = os.path.join(anatdir, "lesionmask")

            lesionmaskinv = lesionmask + "inv"

            # ==================================================================================================================================================================
            # now the real work
            # ==================================================================================================================================================================

            #### FIXING NEGATIVE RANGE
            # required input: " + T1 + "
            # output: " + T1 + "

            minval = float(rrun("fslstats " + T1 + " -p " + str(0), logFile=log))
            maxval = float(rrun("fslstats " + T1 + " -p " + str(100), logFile=log))

            if minval < 0:
                if maxval > 0:
                    # if there are just some negative values among the positive ones then reset zero to the min value
                    rrun("fslmaths " + T1 + " -sub " + str(minval) + T1 + " -odt float", logFile=log)
                else:
                    rrun("fslmaths " + T1 + " -bin -binv zeromask", logFile=log)
                    rrun("fslmaths " + T1 + " -sub " + str(minval) + " -mas zeromask " + T1 + " -odt float",
                         logFile=log)

            #### REORIENTATION 2 STANDARD
            # required input: " + T1 + "
            # output: " + T1 + " (modified) [ and " + T1 + "_orig and .mat ]
            if not os.path.isfile(T1 + "_orig2std.mat") or do_overwrite is True:
                if do_reorient is True:
                    print(self.subject.label + " :Reorienting to standard orientation")
                    rrun("fslmaths " + T1 + " " + T1 + "_orig", logFile=log)
                    # os.system("fslreorient2std " + T1 + " > " + T1 + "_orig2std.mat")
                    run("fslreorient2std " + T1 + " > " + T1 + "_orig2std.mat", logFile=log)
                    rrun("convert_xfm -omat " + T1 + "_std2orig.mat -inverse " + T1 + "_orig2std.mat", logFile=log)
                    rrun("fslmaths " + T1 + " " + T1 + "_orig", logFile=log)

            #### AUTOMATIC CROPPING
            # required input: " + T1 + "
            # output: " + T1 + " (modified) [ and " + T1 + "_fullfov plus various .mats ]

            if imtest(T1 + "_fullfov") is False or do_overwrite is True:
                if do_crop is True:
                    print(self.subject.label + " :Automatically cropping the image")
                    immv(T1, T1 + "_fullfov")
                    run(os.path.join(os.path.join(os.getenv('FSLDIR'), "bin"),
                                     "robustfov -i " + T1 + "_fullfov -r " + T1 + " -m " + T1 + "_roi2nonroi.mat | grep [0-9] | tail -1 > " + T1 + "_roi.log"),
                        logFile=log)
                    # combine this mat file and the one above (if generated)
                    if do_reorient is True:
                        rrun("convert_xfm -omat " + T1 + "_nonroi2roi.mat -inverse " + T1 + "_roi2nonroi.mat",
                             logFile=log)
                        rrun(
                            "convert_xfm -omat " + T1 + "_orig2roi.mat -concat " + T1 + "_nonroi2roi.mat " + T1 + "_orig2std.mat",
                            logFile=log)
                        rrun("convert_xfm -omat " + T1 + "_roi2orig.mat -inverse " + T1 + "_orig2roi.mat", logFile=log)

            ### LESION MASK
            # if I set use_lesionmask: I already verified that the external lesionmask exist and I copied to anat folder and renamed as "lesionmask"
            transform = ""
            if imtest(lesionmask) is False or do_overwrite is True:
                # make appropriate (reoreinted and cropped) lesion mask (or a default blank mask to simplify the code later on)
                if use_lesionmask is True:
                    if not os.path.isfile(T1 + "_orig2std.mat"):
                        transform = T1 + "_orig2std.mat"
                    if not os.path.isfile(T1 + "_orig2roi.mat"):
                        transform = T1 + "_orig2roi.mat"
                    if transform != "":
                        rrun("fslmaths " + lesionmask + " " + lesionmask + "_orig", logFile=log)
                        rrun(
                            "flirt -in " + lesionmask + "_orig" + " -ref " + T1 + " -applyxfm -interp nearestneighbour -init " + transform + " -out " + lesionmask,
                            logFile=log)
                else:
                    rrun("fslmaths " + T1 + " -mul 0 " + lesionmask, logFile=log)

                rrun("fslmaths " + lesionmask + " -bin " + lesionmask, logFile=log)
                rrun("fslmaths " + lesionmask + " -binv " + lesionmaskinv, logFile=log)

            #### BIAS FIELD CORRECTION (main work, although also refined later on if segmentation is run)
            # required input: " + T1 + "
            # output: " + T1 + "_biascorr  [ other intermediates to be cleaned up ]
            if imtest(T1 + "_biascorr") is False or do_overwrite is True:
                if biascorr_type > self.BIAS_TYPE_NO:
                    if biascorr_type == self.BIAS_TYPE_STRONG:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.subject.label + " :Estimating and removing field (stage 1 -large-scale fields)")
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

                        rrun("fslmaths " + T1 + "_hpf_brain_mask -mas " + lesionmaskinv + " " + T1 + "_hpf_brain_mask",
                             logFile=log)
                        # get a smoothed version without the edge effects
                        rrun("fslmaths " + T1 + " -mas " + T1 + "_hpf_brain_mask " + T1 + "_hpf_s20", logFile=log)
                        quick_smooth(T1 + "_hpf_s20", T1 + "_hpf_s20", logFile=log)
                        quick_smooth(T1 + "_hpf_brain_mask", T1 + "_initmask_s20", logFile=log)
                        rrun(
                            "fslmaths " + T1 + "_hpf_s20 -div " + T1 + "_initmask_s20 -mas " + T1 + "_hpf_brain_mask " + T1 + "_hpf2_s20",
                            logFile=log)
                        rrun(
                            "fslmaths " + T1 + " -mas " + T1 + "_hpf_brain_mask -div " + T1 + "_hpf2_s20 " + T1 + "_hpf2_brain",
                            logFile=log)
                        # make sure the overall scaling doesn't change (equate medians)
                        med0 = rrun("fslstats " + T1 + " -k " + T1 + "_hpf_brain_mask -P 50", logFile=log)
                        med1 = rrun("fslstats " + T1 + " -k " + T1 + "_hpf2_brain -k " + T1 + "_hpf_brain_mask -P 50",
                                    logFile=log)
                        rrun("fslmaths " + T1 + "_hpf2_brain -div " + str(
                            med1) + " -mul " + med0 + " " + T1 + "_hpf2_brain", logFile=log)

                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.subject.label + " :Estimating and removing bias field (stage 2 - detailed fields)")
                        rrun("fslmaths " + T1 + "_hpf2_brain -mas " + lesionmaskinv + " " + T1 + "_hpf2_maskedbrain",
                             logFile=log)
                        rrun("fast -o " + T1 + "_initfast -l " + str(smooth) + " -b -B -t " + str(
                            imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_hpf2_maskedbrain",
                             logFile=log)
                        rrun(
                            "fslmaths " + T1 + "_initfast_restore -mas " + lesionmaskinv + " " + T1 + "_initfast_maskedrestore",
                            logFile=log)
                        rrun("fast -o " + T1 + "_initfast2 -l " + str(smooth) + " -b -B -t " + str(
                            imgtype) + " --iter=" + str(
                            niter) + " --nopve --fixed=0 -v " + T1 + "_initfast_maskedrestore", logFile=log)
                        rrun("fslmaths " + T1 + "_hpf_brain_mask " + T1 + "_initfast2_brain_mask", logFile=log)
                    else:
                        # weak bias
                        if do_bet is True:
                            # get a rough brain mask - it can be *VERY* rough (i.e. missing huge portions of the brain or including non-brain, but non-background) - use -f 0.1 to err on being over inclusive
                            rrun("bet " + T1 + " " + T1 + "_initfast2_brain -m -f 0.1", logFile=log)
                        else:
                            rrun("fslmaths " + T1 + " " + T1 + "_initfast2_brain", logFile=log)
                            rrun("fslmaths " + T1 + "_initfast2_brain -bin " + T1 + "_initfast2_brain_mask",
                                 logFile=log)

                        rrun("fslmaths " + T1 + "_initfast2_brain " + T1 + "_initfast2_restore", logFile=log)

                    # redo fast again to try and improve bias field
                    rrun(
                        "fslmaths " + T1 + "_initfast2_restore -mas " + lesionmaskinv + " " + T1 + "_initfast2_maskedrestore",
                        logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(
                        niter) + " --nopve --fixed=0 -v " + T1 + "_initfast2_maskedrestore", logFile=log)
                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.subject.label + " :Extrapolating bias field from central region")
                    # use the latest fast output
                    rrun(
                        "fslmaths " + T1 + " -div " + T1 + "_fast_restore -mas " + T1 + "_initfast2_brain_mask " + T1 + "_fast_totbias",
                        logFile=log)
                    rrun(
                        "fslmaths " + T1 + "_initfast2_brain_mask -ero -ero -ero -ero -mas " + lesionmaskinv + " " + T1 + "_initfast2_brain_mask2",
                        logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun(
                        "fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_initfast2_brain_mask2 -o " + T1 + "_fast_bias",
                        logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_initfast2_brain_mask -dilall -add 1 " + T1 + "_fast_bias  # alternative to fslsmoothfill
                    rrun("fslmaths " + T1 + " -div " + T1 + "_fast_bias " + T1 + "_biascorr", logFile=log)
                else:
                    rrun("fslmaths " + T1 + " " + T1 + "_biascorr", logFile=log)
            log.close()

        except Exception as e:
            traceback.print_exc()
            print(self.subject.label + "  " + os.getcwd())
            log.close()
            print(e)

    def bet(self,
            odn="anat", imgtype=1,
            do_bet=True, betfparam=[], bettypeparam="-R",
            do_reg=True, do_nonlinreg=True,
            do_skipflirtsearch=False,
            do_overwrite=False,
            use_lesionmask=False, lesionmask="lesionmask"
            ):

        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # check anatomical image imgtype
        if imgtype != 1:
            if do_nonlinreg is True:
                print(
                    "ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
                return False

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage = self.subject.t1_data
            anatdir = os.path.join(self.subject.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            inputimage = self.subject.t2_data
            anatdir = os.path.join(self.subject.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1 = os.path.join(anatdir, T1)  # T1 is now an absolute path
        lesionmask = os.path.join(anatdir, lesionmask)
        lesionmaskinv = os.path.join(anatdir, lesionmask + "inv")

        # check original image presence, otherwise exit
        if imtest(inputimage) is False:
            print("ERROR: input anatomical image is missing....exiting")
            return False

        # check given lesionmask presence, otherwise exit
        if use_lesionmask is True and imtest(lesionmask) is False:
            print("ERROR: given Lesion mask is missing....exiting")
            return False

        if len(betfparam) == 0:
            list_bet_fparams = [0.5]
        else:
            list_bet_fparams = betfparam

        # I CAN START PROCESSING !
        try:
            # create some params strings
            if do_skipflirtsearch is True:
                flirtargs = " -nosearch"
            else:
                flirtargs = " "

            if use_lesionmask is True:
                fnirtargs = " --inmask=" + lesionmaskinv
            else:
                fnirtargs = " "

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            # os.chdir(anatdir)

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

            #### REGISTRATION AND BRAIN EXTRACTION
            # required input: " + T1 + "_biascorr
            # output: " + T1 + "_biascorr_brain " + T1 + "_biascorr_brain_mask " + T1 + "_to_MNI_lin " + T1 + "_to_MNI [plus transforms, inverse transforms, jacobians, etc.]
            if imtest(T1 + "_biascorr_brain") is False or do_overwrite is True:
                if do_reg is True:
                    if do_bet is False:
                        print(
                            self.subject.label + " :Skipping registration, as it requires a non-brain-extracted input image")
                    else:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.subject.label + " :Registering to standard space (linear)")

                        if use_lesionmask is True:
                            flirtargs = flirtargs + " -inweight " + lesionmaskinv

                        rrun("flirt -interp spline -dof 12 -in " + T1 + "_biascorr -ref " + os.path.join(
                            self.subject.fsl_data_std_dir,
                            "MNI152_T1_2mm") + " -dof 12 -omat " + T1 + "_to_MNI_lin.mat -out " + T1 + "_to_MNI_lin " + flirtargs,
                             logFile=log)

                        if do_nonlinreg is True:
                            # nnlin co-reg T1 to standard
                            # inv warp of T1standard_mask => mask T1.
                            # mask T1 with above img
                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print("Registering to standard space (non-linear)")
                            refmask = os.path.join(anatdir, "MNI152_T1_2mm_brain_mask_dil1")

                            rrun("fslmaths " + self._global.fsl_std_mni_2mm_brain_mask + " -fillh -dilF " + refmask,
                                 logFile=log)
                            rrun(
                                "fnirt --in=" + T1 + "_biascorr --ref=" + self._global.fsl_std_mni_2mm_head + " --aff=" + T1 + "_to_MNI_lin.mat --refmask=" + refmask +
                                " --fout=" + T1 + "_to_MNI_nonlin_field --jout=" + T1 + "_to_MNI_nonlin_jac --iout=" + T1 + "_to_MNI_nonlin --logout=" + T1 + "_to_MNI_nonlin.txt --cout=" + T1 + "_to_MNI_nonlin_coeff --config=" + self._global.fsl_std_mni_2mm_cnf + " " + fnirtargs,
                                logFile=log)

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.subject.label + " :Performing brain extraction (using FNIRT)")
                            rrun(
                                "invwarp --ref=" + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_coeff -o " + os.path.join(
                                    anatdir, "MNI_to_T1_nonlin_field"), logFile=log)
                            rrun(
                                "applywarp --interp=nn --in=" + self._global.fsl_std_mni_2mm_brain_mask + " --ref=" + T1 + "_biascorr -w " + os.path.join(
                                    anatdir, "MNI_to_T1_nonlin_field") + " -o " + T1 + "_biascorr_brain_mask",
                                logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr_brain_mask -fillh " + T1 + "_biascorr_brain_mask",
                                 logFile=log)
                            rrun(
                                "fslmaths " + T1 + "_biascorr -mas " + T1 + "_biascorr_brain_mask " + T1 + "_biascorr_brain",
                                logFile=log)
                            ## In the future, could check the initial ROI extraction here
                        else:
                            for i in range(len(list_bet_fparams)):
                                betopts = bettypeparam + " -f " + str(list_bet_fparams[i])
                                fp = "_" + str(list_bet_fparams[i]).replace(".", "")
                                print(
                                    "Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                print(self.subject.label + " :Performing brain extraction (using BET)")
                                rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_brain" + fp + " -m " + betopts,
                                     logFile=log)  ## results sensitive to the f parameter

                            imcp(T1 + "_biascorr_brain" + fp, T1 + "_biascorr_brain")
                            imcp(T1 + "_biascorr_brain" + fp + "_mask", T1 + "_biascorr_brain_mask")
                else:
                    if do_bet is True:

                        for i in range(len(list_bet_fparams)):
                            betopts = bettypeparam + " -f " + str(list_bet_fparams[i])

                            fp = "_" + str(list_bet_fparams[i]).replace(".", "")

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.subject.label + " :Performing brain extraction (using BET)")
                            rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_brain" + fp + " -m " + betopts,
                                 logFile=log)  ## results sensitive to the f parameter

                        imcp(T1 + "_biascorr_brain" + fp, T1 + "_biascorr_brain")
                        imcp(T1 + "_biascorr_brain" + fp + "_mask", T1 + "_biascorr_brain_mask")
                    else:
                        rrun("fslmaths " + T1 + "_biascorr " + T1 + "_biascorr_brain", logFile=log)
                        rrun("fslmaths " + T1 + "_biascorr_brain -bin " + T1 + "_biascorr_brain_mask", logFile=log)
            log.close()



        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    # segment T1 with SPM and create  WM+GM and WM+GM+CSF masks
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    # if requested: replace brainmask (produced by FreeSurfer)  BUGGED !!! ignore it
    def spm_segment(self,
                    odn="anat", imgtype=1,
                    do_overwrite=False,
                    do_bet_overwrite=False,
                    add_bet_mask=False,
                    set_origin=False,
                    seg_templ="",
                    spm_template_name="spm_segment_tissuevolume"
                    ):

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir = os.path.join(self.subject.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            anatdir = os.path.join(self.subject.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        srcinputimage = os.path.join(anatdir, T1 + "_biascorr")
        inputimage = os.path.join(self.subject.t1_spm_dir, T1 + "_" + self.subject.label)

        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")
        in_script_template = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template = os.path.join(out_batch_dir, self.subject.label + "_" + spm_template_name + "_job.m")
        output_start = os.path.join(out_batch_dir, "start_" + self.subject.label + "_" + spm_template_name + ".m")

        brain_mask = os.path.join(self.subject.t1_spm_dir, "brain_mask.nii.gz")
        skullstripped_mask = os.path.join(self.subject.t1_spm_dir, "skullstripped_mask.nii.gz")

        icv_file = os.path.join(self.subject.t1_spm_dir, "icv_" + self.subject.label + ".dat")

        # check whether skipping
        if imtest(brain_mask) is True and do_overwrite is False:
            return
        try:

            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(out_batch_dir, exist_ok=True)
            os.makedirs(self.subject.t1_spm_dir, exist_ok=True)

            gunzip(srcinputimage + ".nii.gz", inputimage + ".nii")

            # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
            if set_origin is True:
                input("press keyboard when finished setting the origin for subj " + self.subject.label + " :")

            if seg_templ == "":
                seg_templ = os.path.join(self._global.spm_dir, "tpm", "TPM.nii")
            else:
                if imtest(seg_templ) is False:
                    print("Error in spm_segment: given tissues template image (" + seg_templ + ") does not exist")

            copyfile(in_script_template, output_template)
            copyfile(in_script_start, output_start)

            sed_inplace(output_template, "<T1_IMAGE>", inputimage + ".nii")
            sed_inplace(output_template, "<ICV_FILE>", icv_file)
            sed_inplace(output_template, '<SPM_DIR>', self._global.spm_dir)
            sed_inplace(output_template, '<TEMPLATE_TISSUES>', seg_templ)

            sed_inplace(output_start, "X", "1")
            sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

            call_matlab_spmbatch(output_start, [self._global.spm_functions_dir], log)

            # create brainmask (WM+GM) and skullstrippedmask (WM+GM+CSF)
            c1img = os.path.join(self.subject.t1_spm_dir, "c1T1_" + self.subject.label + ".nii")
            c2img = os.path.join(self.subject.t1_spm_dir, "c2T1_" + self.subject.label + ".nii")
            c3img = os.path.join(self.subject.t1_spm_dir, "c3T1_" + self.subject.label + ".nii")

            rrun("fslmaths " + c1img + " -add " + c2img + " -thr 0.1 -fillh " + brain_mask, logFile=log)
            rrun("fslmaths " + c1img + " -add " + c2img + " -add " + c3img + " -thr 0.1 -bin " + skullstripped_mask, logFile=log)

            # this codes have two aims:
            # 1) it resets like in the original image the dt header parameters that spm set to 0.
            #    otherwise it fails some operations like fnirt as it sees the mask and the brain data of different dimensions
            # 2) changing image origin in spm, changes how fsleyes display the image. while, masking in this ways, everything goes right
            rrun("fslmaths " + srcinputimage + ".nii.gz" + " -mas " + brain_mask + " -bin " + brain_mask)
            rrun("fslmaths " + srcinputimage + ".nii.gz" + " -mas " + skullstripped_mask + " -bin " + skullstripped_mask)

            if add_bet_mask is True:

                if imtest(os.path.join(self.subject.t1_anat_dir, "T1_biascorr_brain_mask")) is True:
                    rrun("fslmaths " + brain_mask + " -add " + os.path.join(self.subject.t1_anat_dir, "T1_biascorr_brain_mask") + " -bin " + brain_mask)
                elif imtest(self.subject.t1_brain_data_mask) is True:
                    rrun("fslmaths " + brain_mask + " -add " + self.subject.t1_brain_data_mask + " " + brain_mask)
                else:
                    print("warning in spm_segment: no other bet mask to add to spm one")

            if do_bet_overwrite is True:
                # copy SPM mask and use it to mask T1_biascorr
                imcp(brain_mask, self.subject.t1_brain_data_mask, logFile=log)
                rrun("fslmaths " + inputimage + " -mas " + brain_mask + " " + self.subject.t1_brain_data, logFile=log)

            imrm([inputimage + ".nii"])
            # if do_fs_overwrite is True:
            #
            #     fs_brain_mask       = os.path.join(self.t1_fs_dir, "brainmask.mgz")
            #     fs_brain_mask_fsl   = os.path.join(self.t1_fs_dir, "brainmask.nii.gz")
            #     fs_t1               = os.path.join(self.t1_fs_dir, "T1.mgz")
            #     fs_t1_fsl           = os.path.join(self.t1_fs_dir, "T1.nii.gz")
            #
            #     if not imtest(fs_t1):
            #         print("anatomical_processing_spm_segment was called with freesurfer replace, but fs has not been run")
            #         return
            #
            #     imcp(fs_brain_mask, os.path.join(self.t1_fs_dir, "brainmask_orig.mgz"), logFile=log)    # backup original brainmask
            #     rrun("mri_convert " + fs_t1 + " " + fs_t1_fsl, logFile=log)                          # convert t1.mgz
            #
            #     rrun("fslmaths " + fs_t1_fsl + " -mas " + brain_mask + " " + fs_brain_mask_fsl, logFile=log) # mask T1 with SPM brain_mask
            #     rrun("mri_convert " + fs_brain_mask_fsl + " " + fs_brain_mask, logFile=log)                  # convert brainmask back to mgz
            #
            #     imrm(fs_t1_fsl, logFile=log)
            #     imrm(fs_brain_mask_fsl, logFile=log)

            log.close()

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def spm_segment_check(self, check_dartel=True):
        icv_file = os.path.join(self.subject.t1_spm_dir, "icv_" + self.subject.label + ".dat")

        if os.path.exists(icv_file) is False:
            print("Error in cat_segment_check of subj " + self.subject.label + ", ICV_FILE is missing")
            return False

        if os.path.getsize(icv_file) == 0:
            print("Error in spm_segment_check of subj " + self.subject.label + ", ICV_FILE is empty")
            return False

        c1file = os.path.join(self.subject.t1_spm_dir, "c1T1_" + self.subject.label + ".nii")
        if imtest(c1file) is False:
            print("Error in spm_segment_check of subj " + self.subject.label + ", C1 File is missing")
            return False

        if check_dartel is True:
            rc1file = os.path.join(self.subject.t1_spm_dir, "rc1T1_" + self.subject.label + ".nii")
            if imtest(rc1file) is False:
                print("Error in spm_segment_check of subj " + self.subject.label + ", RC1 File is missing")
                return False

        return True

    # segment T1 with CAT and create  WM+GM mask (CSF is not created)
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    def cat_segment(self,
                    odn="anat", imgtype=1,
                    do_overwrite=False,
                    do_bet_overwrite=False,
                    add_bet_mask=True,
                    set_origin=False,
                    seg_templ="",
                    coreg_templ="",
                    calc_surfaces=0,
                    num_proc=1,
                    use_existing_nii=True,
                    use_dartel=True,
                    spm_template_name="cat27_segment_customizedtemplate_tiv_smooth"
                    ):

        if imtest(os.path.join(self.subject.t1_cat_dir, "mri",
                               "y_T1_" + self.subject.label)) is True and do_overwrite is False:
            print(self.subject.label + ": skipping cat_segment, already done")
            return

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir = os.path.join(self.subject.t1_dir, odn)
            T1 = "T1"
        elif imgtype == 2:
            anatdir = os.path.join(self.subject.t2_dir, odn)
            T1 = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        if seg_templ == "":
            seg_templ = self._global.spm_tissue_map
        else:
            if imtest(seg_templ) is False:
                print("ERROR in cat_segment: given template segmentation is not present")
                return

        if coreg_templ == "":
            if use_dartel is True:
                coreg_templ = self._global.cat_dartel_template
            else:
                coreg_templ = self._global.cat_shooting_template
        else:
            if imtest(coreg_templ) is False:
                print("ERROR in cat_segment: given template coregistration is not present")
                return

        srcinputimage = os.path.join(anatdir, T1 + "_biascorr")
        inputimage = os.path.join(self.subject.t1_cat_dir, T1 + "_" + self.subject.label)

        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")
        in_script_template = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template = os.path.join(out_batch_dir, self.subject.label + "_" + spm_template_name + "_job.m")
        output_start = os.path.join(out_batch_dir, "start_" + self.subject.label + "_" + spm_template_name + ".m")

        brain_mask = os.path.join(self.subject.t1_cat_dir, "brain_mask.nii.gz")

        icv_file = os.path.join(self.subject.t1_cat_dir, "tiv_" + self.subject.label + ".txt")

        # check whether skipping
        if imtest(brain_mask) is True and do_overwrite is False:
            return
        try:

            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(out_batch_dir, exist_ok=True)
            os.makedirs(self.subject.t1_cat_dir, exist_ok=True)

            # I may want to process with cat after having previously processed without having set image's origin.
            # thus I may have created a nii version in the cat_proc folder , with the origin properly set
            # unzip nii.gz -> nii in cat folder only if nii is absent or I want to overwrite it.
            if use_existing_nii is True and os.path.exists(srcinputimage + ".nii.gz") is False:
                print(
                    "Error in subj: " + self.subject.label + ", method: cat_segment, given image in cat folder is absent")
            else:

                if os.path.exists(srcinputimage + ".nii.gz") is True:
                    gunzip(srcinputimage + ".nii.gz", inputimage + ".nii")
                else:
                    print("Error in subj: " + self.subject.label + ", method: cat_segment, biascorr image is absent")

            # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
            if set_origin is True:
                input("press keyboard when finished setting the origin for subj " + self.subject.label + " :")

            copyfile(in_script_template, output_template)
            copyfile(in_script_start, output_start)

            sed_inplace(output_template, "<T1_IMAGE>", inputimage + ".nii")
            sed_inplace(output_template, "<TEMPLATE_SEGMENTATION>", seg_templ)
            sed_inplace(output_template, "<TEMPLATE_COREGISTRATION>", coreg_templ)
            sed_inplace(output_template, "<CALC_SURFACES>", str(calc_surfaces))
            sed_inplace(output_template, "<TIV_FILE>", icv_file)
            sed_inplace(output_template, "<N_PROC>", str(num_proc))

            resample_string = ""
            if calc_surfaces == 1:
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.data_surf(1) = cfg_dep('CAT12: Segmentation: Left Thickness',substruct('.', 'val', '{}', {1}, '.', 'val','{}', {1}, '.', 'val', '{}', {1},'.', 'val', '{}', {1}),substruct('()', {1}, '.', 'lhthickness','()', {':'}));\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.merge_hemi = 1;\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.mesh32k = 1;\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.fwhm_surf = 15;\n"
                resample_string = resample_string + "matlabbatch{4}.spm.tools.cat.stools.surfresamp.nproc = " + str(
                    num_proc) + ";\n"

            sed_inplace(output_template, "<SURF_RESAMPLE>", resample_string)

            sed_inplace(output_start, "X", "1")
            sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

            call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], log)

            if use_existing_nii is False:
                imrm([inputimage + ".nii"])

            log.close()

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def cat_segment_check(self, calc_surfaces=True):
        icv_file = os.path.join(self.subject.t1_cat_dir, "tiv_" + self.subject.label + ".txt")

        if os.path.exists(icv_file) is False:
            print("Error in cat_segment_check of subj " + self.subject.label + ", ICV_FILE is missing")
            return False

        if os.path.getsize(icv_file) == 0:
            print("Error in cat_segment_check of subj " + self.subject.label + ", ICV_FILE is empty")
            return False

        if os.path.exists(
                os.path.join(self.subject.t1_cat_dir, "report", "cat_T1_" + self.subject.label + ".xml")) is False:
            print("Error in cat_segment_check of subj " + self.subject.label + ", CAT REPORT is missing")
            return False

        if calc_surfaces is True:

            if os.path.exists(
                    os.path.join(self.subject.t1_cat_surface_dir, "lh.thickness.T1_" + self.subject.label)) is False:
                print("Error in cat_segment_check of subj " + self.subject.label + ", lh thickness is missing")
                return False

            if os.path.exists(self.subject.t1_cat_resampled_surface) is False:
                print("Error in cat_segment_check of subj " + self.subject.label + ", RESAMPLED SURFACE is missing")
                return False

        return True

    # longitudinal segment T1 with CAT and create  WM+GM mask (CSF is not created)
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    def cat_segment_longitudinal(self,
                                 sessions,
                                 odn="anat", imgtype=1,
                                 do_overwrite=False,
                                 do_bet_overwrite=False,
                                 add_bet_mask=True,
                                 set_origin=False,
                                 seg_templ="",
                                 coreg_templ="",
                                 calc_surfaces=0,
                                 num_proc=1,
                                 use_existing_nii=True,
                                 spm_template_name="cat_segment_longitudinal_customizedtemplate_tiv_smooth"
                                 ):

        current_session = self.subject.sessid
        # define placeholder variables for input dir and image name

        if seg_templ == "":
            seg_templ = self._global.spm_tissue_map
        else:
            if imtest(seg_templ) is False:
                print("ERROR in cat_segment: given template segmentation is not present")
                return

        if coreg_templ == "":
            coreg_templ = self._global.cat_dartel_template
        else:
            if imtest(coreg_templ) is False:
                print("ERROR in cat_segment: given template coregistration is not present")
                return

        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")
        in_script_template = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template = os.path.join(out_batch_dir, self.subject.label + "_" + spm_template_name + "_job.m")
        output_start = os.path.join(out_batch_dir, "start_" + self.subject.label + "_" + spm_template_name + ".m")

        copyfile(in_script_template, output_template)
        copyfile(in_script_start, output_start)

        try:

            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(out_batch_dir, exist_ok=True)

            images_string = ""
            images_list = []

            # create images list
            for sess in sessions:

                subj = self.subject.get_properties(sess)

                if imgtype == 1:
                    anatdir = os.path.join(subj.t1_dir, odn)
                    T1 = "T1"
                elif imgtype == 2:
                    anatdir = os.path.join(subj.t2_dir, odn)
                    T1 = "T2"
                else:
                    print("ERROR: PD input format is not supported")
                    return False

                srcinputimage = os.path.join(anatdir, T1 + "_biascorr")
                inputimage = os.path.join(subj.t1_cat_dir, T1 + "_" + subj.label)
                brain_mask = os.path.join(subj.t1_cat_dir, "brain_mask.nii.gz")

                # check whether skipping
                if imtest(brain_mask) is True and do_overwrite is False:
                    return

                os.makedirs(subj.t1_cat_dir, exist_ok=True)

                # I may want to process with cat after having previously processed without having set image's origin.
                # thus I may have created a nii version in the cat_proc folder , with the origin properly set
                # unzip T1_biascorr.nii.gz -> nii in cat folder only if nii is absent or I want to overwrite it.
                if use_existing_nii is False:
                    if os.path.exists(srcinputimage + ".nii.gz") is True:
                        gunzip(srcinputimage + ".nii.gz", inputimage + ".nii")
                    else:
                        print(
                            "Error in subj: " + self.subject.label + ", method: cat_segment, biascorr image is absent")
                else:
                    if os.path.exists(inputimage + ".nii") is False:
                        print(
                            "Error in subj: " + self.subject.label + ", method: cat_segment, given image in cat folder is absent")

                # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
                if set_origin is True:
                    input("press keyboard when finished setting the origin for subj " + subj.label + " :")

                images_string = images_string + "'" + inputimage + ".nii,1'\n"
                images_list.append(inputimage + ".nii")

            sed_inplace(output_template, "<T1_IMAGES>", images_string)
            sed_inplace(output_template, "<TEMPLATE_SEGMENTATION>", seg_templ)
            sed_inplace(output_template, "<TEMPLATE_COREGISTRATION>", coreg_templ)
            sed_inplace(output_template, "<CALC_SURFACES>", str(calc_surfaces))
            sed_inplace(output_template, "<N_PROC>", str(num_proc))

            sed_inplace(output_start, "X", "1")
            sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

            eng = call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], log,
                                       endengine=False)

            if calc_surfaces == 1:
                for sess in sessions:
                    self.surf_resample(sess, num_proc, isLong=True, endengine=False, eng=eng)

            for sess in sessions:
                self.cat_tiv_calculation(sess, isLong=True, endengine=False, eng=eng)

            if use_existing_nii is False:
                imrm([images_list])

            eng.quit()
            log.close()

            self.subject.sessid = current_session

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    # the above scripts often fails after having correctly segmented the image and calculated the lh.thickness.rT1_XXXX image
    def cat_surfaces_complete_longitudinal(self, sessions, num_proc=1):

        try:
            for sess in sessions:
                self.cat_surf_resample(sess, num_proc, isLong=True, endengine=False)

            for sess in sessions:
                self.cat_tiv_calculation(sess, isLong=True)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def cat_segment_longitudinal_check(self, sessions, calc_surfaces=0):

        err = ""

        for sess in sessions:

            subj = self.subject.get_properties(sess)

            icv_file = os.path.join(subj.t1_cat_dir, "tiv_r_" + subj.label + ".txt")
            report_file = os.path.join(subj.t1_cat_dir, "report", "cat_rT1_" + subj.label + ".xml")

            if os.path.exists(report_file) is False:
                err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(
                    sess) + ", CAT REPORT is missing" + "\n"

            if os.path.exists(icv_file) is False:
                err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(
                    sess) + ", ICV_FILE is missing" + "\n"
            else:
                if os.path.getsize(icv_file) == 0:
                    err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(
                        sess) + ", ICV_FILE is empty" + "\n"

            if calc_surfaces > 0:

                if os.path.exists(os.path.join(subj.t1_cat_surface_dir, "lh.thickness.rT1_" + subj.label)) is False:
                    err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(
                        sess) + ", lh thickness is missing" + "\n"

                if os.path.exists(subj.t1_cat_resampled_surface_longitudinal) is False:
                    err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(
                        sess) + ", RESAMPLED SURFACE is missing" + "\n"

        if err != "":
            print(err)

        return err

    def cat_surf_resample(self, session=1, num_proc=1, isLong=False, mesh32k=1, endengine=True, eng=None):

        spm_template_name = "mpr_cat_surf_resample"
        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")
        in_script_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template = os.path.join(out_batch_dir, self.subject.label + "_" + spm_template_name + "_job.m")
        output_start = os.path.join(out_batch_dir, "start_" + self.subject.label + "_" + spm_template_name + ".m")

        copyfile(in_script_start, output_start)

        subj = self.subject.get_properties(session)

        surf_prefix = "T1"
        if isLong is True:
            surf_prefix = "rT1"
        surface = os.path.join(subj.t1_cat_dir, "surf", "lh.thickness." + surf_prefix + "_" + subj.label)

        resample_string = ""
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.data_surf = {'" + surface + "'};\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.merge_hemi = 1;\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.mesh32k = " + str(
            mesh32k) + ";\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.fwhm_surf = 15;\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.nproc = " + str(
            num_proc) + ";\n"

        write_text_file(output_template, resample_string)
        sed_inplace(output_start, "X", "1")
        sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

        call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine,
                             eng=eng)

    def cat_tiv_calculation(self, session=1, isLong=False, endengine=True, eng=None):

        spm_template_name = "mpr_cat_tiv_calculation"
        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")
        in_script_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template = os.path.join(out_batch_dir, self.subject.label + "_" + spm_template_name + "_job.m")
        output_start = os.path.join(out_batch_dir, "start_" + self.subject.label + "_" + spm_template_name + ".m")

        copyfile(in_script_start, output_start)

        subj = self.subject.get_properties(session)

        prefix = "cat_T1_"
        prefix_tiv = "tiv_"
        if isLong is True:
            prefix = "cat_rT1_"
            prefix_tiv = "tiv_r_"

        report_file = os.path.join(subj.t1_cat_dir, "report", prefix + subj.label + ".xml")
        tiv_file = os.path.join(subj.t1_cat_dir, prefix_tiv + subj.label + ".txt")

        tiv_string = ""
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.data_xml = {'" + report_file + "'};\n"
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.calcvol_TIV = 1;\n"
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.calcvol_name = '" + tiv_file + "';\n"

        write_text_file(output_template, tiv_string)
        sed_inplace(output_start, "X", "1")
        sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

        call_matlab_spmbatch(output_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine,
                             eng=eng)

    def cat_extract_roi_based_surface(self, atlases=None):

        if atlases is None:
            atlases = ["aparc_HCP_MMP1", "aparc_DK40", "aparc_a2009s"]

        _atlases = ""
        for atlas in atlases:
            _atlases = _atlases + "\'" + os.path.join(self._global.cat_dir, "atlases_surfaces", "lh." + atlas + ".freesurfer.annot") + "\'" + "\n"

        out_batch_job, out_batch_start = self.subject.project.create_batch_files("cat_extract_roi_based_surface", "mpr", self.subject.label)

        left_thick_img = os.path.join(self.subject.t1_cat_surface_dir, "lh.thickness.T1_" + self.subject.label)
        if os.path.exists(left_thick_img) is False:
            print("ERROR in cat_extract_roi_based_surface of subj " + self.subject.label + ", missing left thickness surface")
            return

        sed_inplace(out_batch_job, "<LH_TCK_IMAGES>", "\'" + left_thick_img + "\'")
        sed_inplace(out_batch_job, "<ATLASES>", _atlases)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

    def spm_tissue_volumes(self, spm_template_name="spm_icv_template", endengine=True, eng=None):

        seg_mat = os.path.join(self.subject.t1_spm_dir, "T1_biascorr_" + self.subject.label + "_seg8.mat")
        icv_file = os.path.join(self.subject.t1_spm_dir, "icv_" + self.subject.label + ".dat")

        # set dirs
        spm_script_dir = os.path.join(self.subject.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")
        in_script_template = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")
        in_script_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        output_template = os.path.join(out_batch_dir, self.subject.label + "_" + spm_template_name + "_job.m")
        output_start = os.path.join(out_batch_dir, "start_" + self.subject.label + "_" + spm_template_name + ".m")

        copyfile(in_script_template, output_template)
        copyfile(in_script_start, output_start)

        sed_inplace(output_template, "<SEG_MAT>", seg_mat)
        sed_inplace(output_template, "<ICV_FILE>", icv_file)
        sed_inplace(output_start, "X", "1")
        sed_inplace(output_start, "JOB_LIST", "\'" + output_template + "\'")

        call_matlab_spmbatch(output_start, [self._global.spm_functions_dir], endengine=False, eng=eng)

    def surf_resampled_longitudinal_diff(self, sessions, outdir="", matlab_func="subtract_gifti"):

        if len(sessions) != 2:
            print("Error in surf_resampled_longitudinal_diff...given sessions are not 2")
            return

        if outdir == "":
            outdir = self.subject.t1_cat_surface_dir

        out_str = ""
        surfaces = []
        for sess in sessions:
            subj = self.subject.get_properties(sess)
            out_str = out_str + str(sess) + "_"
            surfaces.append(subj.t1_cat_resampled_surface_longitudinal)

        res_surf = os.path.join(outdir, "surf_resampled_sess_" + out_str + self.subject.label + ".gii")

        call_matlab_function_noret(matlab_func, [self._global.spm_functions_dir],
                                   "\"" + surfaces[1] + "\",  \"" + surfaces[0] + "\", \"" + res_surf + "\"")

    # ==================================================================================================================
    #   TISSUE-TYPE SEGMENTATION
    #   SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION
    def postbet(self,
                odn="anat", imgtype=1, smooth=10,
                betfparam=0.5,
                do_reg=True, do_nonlinreg=True,
                do_seg=True,
                do_cleanup=True, do_strongcleanup=False, do_overwrite=False,
                use_lesionmask=False, lesionmask="lesionmask"
                ):
        niter = 5
        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # check anatomical image imgtype
        if imgtype != 1:
            if do_nonlinreg is True:
                print(
                    "ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
                return False

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage = self.subject.t1_data
            anatdir = os.path.join(self.subject.t1_dir, odn)
            T1 = "T1"
            T1_label = "T1"
        elif imgtype == 2:
            inputimage = self.subject.t2_data
            anatdir = os.path.join(self.subject.t2_dir, odn)
            T1 = "T2"
            T1_label = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1 = os.path.join(anatdir, T1)  # T1 is now an absolute path
        lesionmask = os.path.join(anatdir, lesionmask)
        lesionmaskinv = os.path.join(anatdir, lesionmask + "inv")

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

            betopts = "-f " + str(betfparam[0])

            # create processing dir (if non existent) and cd to it
            os.makedirs(anatdir, exist_ok=True)
            # os.chdir(anatdir)

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

            #### TISSUE-TYPE SEGMENTATION (uses the t1_brain whichever created, not necessarly the bet one.)
            # required input: T1_biascorr + label-t1_brain + label-t1_brain_mask
            # output:  T1_biascorr (modified) + T1_biascorr_brain (modified) + T1_fast* (as normally output by fast) + T1_fast_bias (modified)
            if (imtest(T1 + "_fast_pve_1") is False and imtest(
                    os.path.join(self.subject.fast_dir, "T1_fast_pve_1")) is False) or do_overwrite is True:
                if do_seg is True:

                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.subject.label + " :Performing tissue-imgtype segmentation")
                    rrun(
                        "fslmaths " + T1 + "_biascorr_brain" + " -mas " + lesionmaskinv + " " + T1 + "_biascorr_maskedbrain",
                        logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(
                        niter) + " " + T1 + "_biascorr_maskedbrain", logFile=log)
                    immv(T1 + "_biascorr", T1 + "_biascorr_init", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_restore " + T1 + "_biascorr_brain", logFile=log)  # overwrite brain

                    # extrapolate bias field and apply to the whole head image
                    rrun(
                        "fslmaths " + T1 + "_biascorr_brain_mask -mas " + lesionmaskinv + " " + T1 + "_biascorr_brain_mask2",
                        logFile=log)
                    # rrun("fslmaths " + self.t1_brain_data_mask + " -mas " + lesionmaskinv + " " + T1 + "_biascorr_brain_mask2",logFile=log)
                    rrun(
                        "fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_restore -mas " + T1 + "_biascorr_brain_mask2 " + T1 + "_fast_totbias",
                        logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun(
                        "fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_biascorr_brain_mask2 -o " + T1 + "_fast_bias",
                        logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_biascorr_brain_mask2 -dilall -add 1 " + T1 + "_fast_bias # alternative to fslsmoothfill", logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_bias " + T1 + "_biascorr",
                         logFile=log)  # overwrite full image

                    imcp(T1 + "_biascorr_brain", self.subject.t1_brain_data)
                    imcp(T1 + "_biascorr", self.subject.t1_data)

                    if do_nonlinreg is True:

                        # regenerate the standard space version with the new bias field correction applied
                        if imtest(T1 + "_to_MNI_nonlin_field") is True:
                            rrun(
                                "applywarp -i " + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_field -r " + os.path.join(
                                    self.subject.fsl_data_std_dir,
                                    "MNI152_" + T1_label + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline",
                                logFile=log)
                        else:
                            if imtest(os.path.join(self.subject.roi_std_dir, "hr2std_warp")) is True:
                                rrun("applywarp -i " + T1 + "_biascorr -w " + os.path.join(self.subject.roi_std_dir,
                                                                                           "hr2std_warp") + " -r " + os.path.join(
                                    self.subject.fsl_data_std_dir,
                                    "MNI152_" + T1_label + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline",
                                     logFile=log)
                            else:
                                print(
                                    "WARNING in postbet: either " + T1 + "_to_MNI_nonlin_field" + " or " + os.path.join(
                                        self.subject.roi_std_dir, "hr2std_warp") + " is missing")

            #### SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION (only done if registration turned on, and segmentation done, and it is a T1 image)
            # required inputs: " + T1 + "_biascorr
            # output: " + T1 + "_vols.txt
            if os.path.isfile(T1 + "_vols.txt") is False or do_overwrite is True:

                if do_reg is True and do_seg is True and T1_label == "T1":
                    print(self.subject.label + " :Skull-constrained registration (linear)")

                    rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_bet -s -m " + betopts, logFile=log)
                    rrun("pairreg " + os.path.join(self.subject.fsl_data_std_dir,
                                                   "MNI152_T1_2mm_brain") + " " + T1 + "_biascorr_bet " + os.path.join(
                        self.subject.fsl_data_std_dir,
                        "MNI152_T1_2mm_skull") + " " + T1 + "_biascorr_bet_skull " + T1 + "2std_skullcon.mat",
                         logFile=log)

                    if use_lesionmask is True:
                        rrun(
                            "fslmaths " + lesionmask + " -max " + T1 + "_fast_pve_2 " + T1 + "_fast_pve_2_plusmask -odt float",
                            logFile=log)
                        # ${FSLDIR}/bin/fslmaths lesionmask -bin -mul 3 -max " + T1 + "_fast_seg " + T1 + "_fast_seg_plusmask -odt int

                    vscale = float(
                        runpipe("avscale " + T1 + "2std_skullcon.mat | grep Determinant | awk '{ print $3 }'",
                                logFile=log)[0].decode("utf-8").split("\n")[0])
                    ugrey = float(
                        runpipe("fslstats " + T1 + "_fast_pve_1 -m -v | awk '{ print $1 * $3 }'", logFile=log)[
                            0].decode("utf-8").split("\n")[0])
                    uwhite = float(
                        runpipe("fslstats " + T1 + "_fast_pve_2 -m -v | awk '{ print $1 * $3 }'", logFile=log)[
                            0].decode("utf-8").split("\n")[0])

                    ngrey = ugrey * vscale
                    nwhite = uwhite * vscale
                    ubrain = ugrey + uwhite
                    nbrain = ngrey + nwhite

                    with open(T1 + "_vols.txt", "w") as file_vol:
                        print(
                            "Scaling factor from " + T1 + " to MNI (using skull-constrained linear registration) = " + str(
                                vscale), file=file_vol)
                        print("Brain volume in mm^3 (native/original space) = " + str(ubrain), file=file_vol)
                        print("Brain volume in mm^3 (normalised to MNI) = " + str(nbrain), file=file_vol)

            #### CLEANUP
            if do_cleanup is True:
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning up intermediate files"
                rrun(
                    "imrm " + T1 + "_biascorr_bet_mask " + T1 + "_biascorr_bet " + T1 + "_biascorr_brain_mask2 " + T1 + "_biascorr_init " + T1 + "_biascorr_maskedbrain " + T1 + "_biascorr_to_std_sub " + T1 + "_fast_bias_idxmask " + T1 + "_fast_bias_init " + T1 + "_fast_bias_vol2 " + T1 + "_fast_bias_vol32 " + T1 + "_fast_totbias " + T1 + "_hpf* " + T1 + "_initfast* " + T1 + "_s20 " + T1 + "_initmask_s20",
                    logFile=log)

            #### STRONG CLEANUP
            if do_strongcleanup is True:
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning all unnecessary files "
                rrun("imrm " + T1 + " " + T1 + "_orig " + T1 + "_fullfov", logFile=log)

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def finalize(self, odn="anat", imgtype=1):

        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            anatdir = os.path.join(self.subject.t1_dir, odn)
            T1 = "T1"
            T1_label = "T1"
        elif imgtype == 2:
            anatdir = os.path.join(self.subject.t2_dir, odn)
            T1 = "T2"
            T1_label = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1 = os.path.join(anatdir, T1)  # T1 is now an absolute path
        # ==================================================================================================================================================================
        #### move and rename files according to myMRI system
        print("----------------------------------- starting t1_post_processing of subject " + self.subject.label)
        try:
            log = open(logfile, "a")
            print("******************************************************************", file=log)
            print("starting t1_post_processing", file=log)
            print("******************************************************************", file=log)

            run_notexisting_img(self.subject.t1_data + "_orig", "immv " + self.subject.t1_data + " " + self.subject.t1_data + "_orig", logFile=log)
            run_notexisting_img(self.subject.t1_data, "imcp " + T1 + "_biascorr " + self.subject.t1_data, logFile=log)
            run_notexisting_img(self.subject.t1_brain_data, "imcp " + T1 + "_biascorr_brain " + self.subject.t1_brain_data, logFile=log)
            run_notexisting_img(self.subject.t1_brain_data + "_mask", "imcp " + T1 + "_biascorr_brain_mask " + self.subject.t1_brain_data + "_mask", logFile=log)

            os.makedirs(self.subject.fast_dir, exist_ok=True)

            mass_images_move(os.path.join(anatdir, "*fast*"), self.subject.fast_dir, logFile=log)

            run_notexisting_img(T1 + "_fast_pve_1", "imcp " + os.path.join(self.subject.fast_dir, T1_label + "_fast_pve_1 " + anatdir), logFile=log)  # this file is tested by subject_t1_processing to skip the fast step. so by copying it back, I allow such skip.

            run_notexisting_img(self.subject.t1_segment_csf_path, "fslmaths " + os.path.join(self.subject.fast_dir, T1_label + "_fast_seg") + " -thr 1 -uthr 1 " + self.subject.t1_segment_csf_path, logFile=log)
            run_notexisting_img(self.subject.t1_segment_gm_path, "fslmaths " + os.path.join(self.subject.fast_dir, T1_label + "_fast_seg") + " -thr 2 -uthr 2 " + self.subject.t1_segment_gm_path, logFile=log)
            run_notexisting_img(self.subject.t1_segment_wm_path, "fslmaths " + os.path.join(self.subject.fast_dir, T1_label + "_fast_seg") + " -thr 3 " + self.subject.t1_segment_wm_path, logFile=log)

            run_notexisting_img(self.subject.t1_segment_csf_ero_path, "fslmaths " + os.path.join(self.subject.fast_dir, T1_label + "_fast_pve_0 -thr 1 -uthr 1 " + self.subject.t1_segment_csf_ero_path), logFile=log)
            run_notexisting_img(self.subject.t1_segment_wm_bbr_path, "fslmaths " + os.path.join(self.subject.fast_dir, T1_label + "_fast_pve_2 -thr 0.5 -bin " + self.subject.t1_segment_wm_bbr_path), logFile=log)
            run_notexisting_img(self.subject.t1_segment_wm_ero_path, "fslmaths " + os.path.join(self.subject.fast_dir, T1_label + "_fast_pve_2 -ero " + self.subject.t1_segment_wm_ero_path), logFile=log)

            mass_images_move(os.path.join(anatdir, "*_to_MNI*"), self.subject.roi_std_dir, logFile=log)
            mass_images_move(os.path.join(anatdir, "*_to_T1*"), self.subject.roi_t1_dir, logFile=log)

            run_move_notexisting_img(os.path.join(self.subject.roi_t1_dir, "std2hr_warp"), "immv " + os.path.join(self.subject.roi_t1_dir, "MNI_to_T1_nonlin_field") + " " + os.path.join(self.subject.roi_t1_dir, "std2hr_warp"), logFile=log)
            run_move_notexisting_img(os.path.join(self.subject.roi_std_dir, "hr2std_warp"), "immv " + os.path.join(self.subject.roi_std_dir, "T1_to_MNI_nonlin_field") + " " + os.path.join(self.subject.roi_std_dir, "hr2std_warp"), logFile=log)

            # first has been removed from the standard t1_processing pipeline
            # mkdir -p $FIRST_DIR
            # run mv first_results $FIRST_DIR
            # run $FSLDIR/bin/immv ${T1}_subcort_seg $FIRST_DIR

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def first(self, structures="", t1_image="", odn=""):

        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # init params
        if t1_image == "":
            t1_image = self.subject.t1_brain_data

        if structures != "":
            structs = "-s " + structures
            list_structs = structures.split(",")
        else:
            list_structs = []
            structs = ""

        output_roi_dir = os.path.join(self.subject.roi_t1_dir, odn)
        temp_dir = os.path.join(self.subject.first_dir, "temp")

        filename = remove_ext(t1_image)
        t1_image_label = os.path.basename(filename)

        try:
            os.makedirs(self.subject.first_dir, exist_ok=True)
            os.makedirs(output_roi_dir, exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)

            # os.chdir(temp_dir)

            log = open(logfile, "a")

            print("******************************************************************", file=log)
            print("starting FIRST processing", file=log)
            print("******************************************************************", file=log)

            print(self.subject.label + ": FIRST (of " + t1_image_label + " " + structs + " " + odn + ")")

            image_label_path = os.path.join(self.subject.first_dir, t1_image_label)

            rrun("first_flirt " + t1_image + " " + image_label_path + "_to_std_sub", logFile=log)
            rrun(
                "run_first_all -i " + t1_image + " - o " + image_label_path + " -d -a " + image_label_path + "_to_std_sub.mat -b " + structs,
                logFile=log)

            for struct in list_structs:
                immv(image_label_path + "-" + struct + "_first.nii.gz",
                     os.path.join(output_roi_dir, "mask_" + struct + "_hr.nii.gz"), logFile=log)

            #	#### SUB-CORTICAL STRUCTURE SEGMENTATION (done in subject_t1_first)
            #	# required input: " + T1 + "_biascorr
            #	# output: " + T1 + "_first*
            #	if imtest( " + T1 + "_subcort_seg` = 0 -o $do_overwrite = yes ]; then
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

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    # FreeSurfer recon-all
    def fs_reconall(self, step="-all", do_overwrite=False, backtransfparams=" RL PA IS ", numcpu=1):

        # check whether skipping
        if step == "-all" and imtest(os.path.join(self.subject.t1_dir, "freesurfer", "aparc+aseg.nii.gz")) is True and do_overwrite is False:
            return

        if step == "-autorecon1" and imtest(os.path.join(self.subject.t1_dir, "freesurfer", "mri", "brainmask.mgz")) is True and do_overwrite is False:
            return

        try:
            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            curdir = os.getcwd()

            rrun("mri_convert " + self.subject.t1_data + ".nii.gz " + self.subject.t1_data + ".mgz", logFile=log)

            try:
                os.environ['OLD_SUBJECTS_DIR'] = os.environ['SUBJECTS_DIR']
            except Exception as e:
                pass

            os.environ['SUBJECTS_DIR'] = self.subject.t1_dir

            rrun("recon-all -subject freesurfer" + " -i " + self.subject.t1_data + ".mgz " + step + " -threads " + str(numcpu), logFile=log)

            # calculate linear trasf to move coronal-conformed T1 back to original reference (specified by backtransfparams)
            # I convert T1.mgz => nii.gz, then I swapdim to axial and coregister to t1_data
            rrun("mri_convert " + self.subject.t1_fs_data + ".mgz " + self.subject.t1_fs_data + ".nii.gz")
            rrun("fslswapdim " + self.subject.t1_fs_data + ".nii.gz" + backtransfparams + self.subject.t1_fs_data + "_orig.nii.gz")
            rrun("flirt -in " + self.subject.t1_fs_data + "_orig.nii.gz" + " -ref " + self.subject.t1_data + " -omat " + os.path.join(self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")
            imrm([self.subject.t1_fs_data + ".nii.gz", self.subject.t1_fs_data + "_orig.nii.gz"])

            if step == "-all":
                rrun("mri_convert " + os.path.join(self.subject.t1_dir, "freesurfer", "mri", "aparc+aseg.mgz") + " " + os.path.join(self.subject.t1_dir, "freesurfer", "aparc+aseg.nii.gz"), logFile=log)
                rrun("mri_convert " + os.path.join(self.subject.t1_dir, "freesurfer", "mri", "aseg.mgz") + " " + os.path.join(self.subject.t1_dir, "freesurfer", "aseg.nii.gz"), logFile=log)
                os.system("rm " + self.subject.dti_data + ".mgz")

            os.environ['SUBJECTS_DIR'] = os.environ['OLD_SUBJECTS_DIR']

        except Exception as e:
            traceback.print_exc()
            # log.close()
            print(e)

    # check whether substituting bet brain with the one created by freesurfer.
    # fs mask is usually bigger then fsl/spm brain, so may need some erosion
    # since the latter op create holes within the image. I create a mask with the latter and the bet mask (which must be coregistered since fs ones are coronal)
    def use_fs_brainmask(self, backtransfparams=" RL PA IS ", erosiontype=" -kernel boxv 5 ", is_interactive=True, do_clean=True):

        # convert fs brainmask to nii.gz => move to the same orientation as working image (usually axial) => erode it
        rrun("mri_convert " + self.subject.t1_fs_brainmask_data + ".mgz " + self.subject.t1_fs_brainmask_data + ".nii.gz")
        rrun("fslswapdim " + self.subject.t1_fs_brainmask_data + ".nii.gz" + backtransfparams + self.subject.t1_fs_brainmask_data + "_orig.nii.gz")

        if erosiontype != "":
            rrun("fslmaths " + self.subject.t1_fs_brainmask_data + "_orig.nii.gz" + erosiontype + " -ero " + self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz")
        else:
            imcp(self.subject.t1_fs_brainmask_data + "_orig.nii.gz", self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz")

        if is_interactive is True:
            rrun("fsleyes " + self.subject.t1_data + " " + self.subject.t1_brain_data + " " + self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz", stop_on_error=False)

            do_substitute = input("do you want to substitute bet image with this one? press y or n\n : ")

            if do_substitute == "y":
                self.use_fs_brainmask_exec(do_clean)

        else:
            self.use_fs_brainmask_exec(do_clean)

        if do_clean is True:
            imrm([self.subject.t1_fs_brainmask_data + ".nii.gz",
                  self.subject.t1_fs_brainmask_data + "_orig.nii.gz",
                  self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz"])

    def use_fs_brainmask_exec(self, add_previous=False, do_clean=True):

        # I may have manually edited self.t1_fs_brainmask + "_orig_ero.nii.gz"
        # although is at the same reference as working image, it still have to be co-registered
        # 1) I move this orig brainmask to the same space as t1 and t1_brain, applying the coronalconformed->original transformation to eroded brainmask_orig
        rrun("flirt -in " + self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz" + " -ref " + self.subject.t1_data + " -out " + self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -applyxfm -init " + os.path.join(self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

        if add_previous is True:
            # => I create its mask (with holes) and add to the bet's one (assumed as smaller but without holes)
            rrun("fslmaths " + self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -bin -add " + self.subject.t1_brain_data_mask + " -bin " + self.subject.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz")
        else:
            # => just fill holes
            rrun("fslmaths " + self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -fillh -bin " + self.subject.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz")

        imcp(self.subject.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz", self.subject.t1_brain_data_mask)  # substitute bet mask with this one
        rrun("fslmaths " + self.subject.t1_data + " -mas " + self.subject.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz" + " " + self.subject.t1_brain_data)

        if do_clean is True:
            imrm([self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz"])

    # check whether substituting bet brain with the one created by SPM-segment.
    # since the SPM GM+WM mask contains holes within the image. I create a mask with the latter and the bet mask (which must be coregistered since fs ones are coronal)
    def use_spm_brainmask(self, backtransfparams=" RL PA IS ", erosiontype=" -kernel boxv 5 ", is_interactive=True,
                          do_clean=True):

        # convert fs brainmask to nii.gz => move to the same orientation as working image (usually axial) => erode it
        rrun(
            "mri_convert " + self.subject.t1_fs_brainmask_data + ".mgz " + self.subject.t1_fs_brainmask_data + ".nii.gz")
        rrun(
            "fslswapdim " + self.subject.t1_fs_brainmask_data + ".nii.gz" + backtransfparams + self.subject.t1_fs_brainmask_data + "_orig.nii.gz")
        rrun(
            "fslmaths " + self.subject.t1_fs_brainmask_data + "_orig.nii.gz" + erosiontype + " -ero " + self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz")

        if is_interactive is True:
            rrun(
                "fsleyes " + self.subject.t1_data + " " + self.subject.t1_brain_data + " " + self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz")

            do_substitute = input("do you want to substitute bet image with this one? press y or n\n : ")

            if do_substitute == "y":
                self.use_spm_brainmask_exec(do_clean)

        else:
            self.use_spm_brainmask_exec(do_clean)

        if do_clean is True:
            imrm([self.subject.t1_fs_brainmask_data + ".nii.gz", self.subject.t1_fs_brainmask_data + "_orig.nii.gz",
                  self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz"])

    def use_spm_brainmask_exec(self, do_clean=True):

        # I may have manually edited self.t1_fs_brainmask + "_orig_ero.nii.gz"
        # although is at the same reference as working image, it still have to be co-registered
        # 1) I move this orig brainmask to the same space as t1 and t1_brain, applying the coronalconformed->original transformation to eroded brainmask_orig
        rrun(
            "flirt -in " + self.subject.t1_fs_brainmask_data + "_orig_ero.nii.gz" + " -ref " + self.subject.t1_data + " -out " + self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -applyxfm -init " + os.path.join(
                self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

        # => I create its mask (with holes) and add to the bet's one (assumed as smaller but without holes)
        rrun(
            "fslmaths " + self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz" + " -bin -add " + self.subject.t1_brain_data_mask + " -bin " + self.subject.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz")

        imcp(self.subject.t1_fs_brainmask_data + "_axial_ero_mask.nii.gz",
             self.subject.t1_brain_data_mask)  # substitute bet mask with this one
        rrun(
            "fslmaths " + self.subject.t1_data + " -mas " + self.subject.t1_fs_brainmask_data + "_orig_ero_mask.nii.gz" + " " + self.subject.t1_brain_data)

        if do_clean is True:
            imrm([self.subject.t1_fs_brainmask_data + "_orig_ero_in_t1.nii.gz"])

    # copy bet, spm and fs extracted brain to given directory
    def compare_brain_extraction(self, tempdir, backtransfparams=" RL PA IS "):

        # bet
        imcp(os.path.join(self.subject.t1_anat_dir, "T1_biascorr_brain"),
             os.path.join(tempdir, self.subject.label + "_bet.nii.gz"))

        # spm (assuming bet mask is smaller than spm's one and the latter contains holes...I make their union to mask the t1
        if imtest(os.path.join(self.subject.t1_spm_dir, "brain_mask")) is True:
            rrun("fslmaths " + os.path.join(self.subject.t1_spm_dir,
                                            "brain_mask") + " -add " + self.subject.t1_brain_data_mask + " " + os.path.join(
                tempdir, self.subject.label + "_bet_spm_mask"))
            rrun("fslmaths " + self.subject.t1_data + " -mas " + os.path.join(tempdir,
                                                                              self.subject.label + "_bet_spm_mask") + " " + os.path.join(
                tempdir, self.subject.label + "_spm"))
            imrm([os.path.join(tempdir, self.subject.label + "_bet_spm_mask")])
        else:
            print("subject " + self.subject.label + " spm mask is not present")

        # freesurfer
        fsmask = os.path.join(self.subject.t1_dir, "freesurfer", "mri", "brainmask")
        if imtest(fsmask) is True:
            rrun("mri_convert " + fsmask + ".mgz " + os.path.join(tempdir, self.subject.label + "_brainmask.nii.gz"))

            rrun("fslswapdim " + os.path.join(tempdir,
                                              self.subject.label + "_brainmask.nii.gz") + backtransfparams + os.path.join(
                tempdir, self.subject.label + "_brainmask.nii.gz"))
            rrun("flirt -in " + os.path.join(tempdir,
                                             self.subject.label + "_brainmask.nii.gz") + " -ref " + self.subject.t1_data + " -out " + os.path.join(
                tempdir, self.subject.label + "_brainmask.nii.gz") + " -applyxfm -init " + os.path.join(
                self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

            # rrun("fslmaths " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz") + " -bin " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz"))
            # rrun("fslmaths " + os.path.join(betdir, "T1_biascorr_brain") + " -mas " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz") + " " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz"))
        else:
            print("subject " + self.subject.label + " freesurfer's brainmask is not present")

    def cleanup(self, lvl=Global.CLEANUP_LVL_MIN):

        os.removedirs(self.subject.t1_anat_dir)

        if lvl == Global.CLEANUP_LVL_MED:
            pass
        elif lvl == Global.CLEANUP_LVL_HI:

            os.removedirs(self.subject.first_dir)
            os.removedirs(self.subject.fast_dir)
            rrun("mv " + self.subject.t1_cat_surface_dir + " " + self.subject.t1_dir)
