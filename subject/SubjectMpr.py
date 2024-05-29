import datetime
import os
import traceback

from Global import Global
from utility.images.Image import Image
from utility.images.Images import Images
from utility.images.images import mass_images_move
from utility.matlab import call_matlab_spmbatch, call_matlab_function_noret
from utility.myfsl.fslfun import run
from utility.myfsl.fslfun import run_notexisting_img, runpipe, run_move_notexisting_img
from utility.myfsl.utils.run import rrun
from utility.fileutilities import sed_inplace, write_text_file


# ==================================================================================================================================================
# ANATOMICAL
# ==================================================================================================================================================

class SubjectMpr:
    """
    This class contains methods for pre-processing and post-processing of MPR images.
    """
    BIAS_TYPE_NO = 0
    BIAS_TYPE_WEAK = 1
    BIAS_TYPE_STRONG = 2

    def __init__(self, subject:'Subject', _global:Global):
        """
        Initialize the SubjectMpr class.

        Args:
            subject (Subject): The subject object.
            _global (Global): The global object.
        """
        self.subject:'Subject' = subject
        self._global:Global  = _global

    # pre-processing:
    #   FIXING NEGATIVE RANGE
    #   REORIENTATION 2 STANDARD
    #   AUTOMATIC CROPPING
    #   LESION MASK
    #   BIAS FIELD CORRECTION
    #  creates lesionmask, lesionmaskinv
    def prebet(self,
               odn="anat", imgtype=1, smooth=10,
               biascorr_type=BIAS_TYPE_STRONG,
               do_reorient:bool=True, do_crop:bool=True,
               do_bet:bool=True,
               do_overwrite:bool=False,
               use_lesionmask:bool=False, lesionmask:str=""
               ):
        """
         Perform pre-processing steps on the MPR images.

         Args:
             odn (str, optional): The output directory name. Defaults to "anat".
             imgtype (int, optional): The image type. Defaults to 1.
             smooth (int, optional): The smoothing kernel size. Defaults to 10.
             biascorr_type (int, optional): The type of bias correction. Defaults to BIAS_TYPE_STRONG.
             do_reorient (bool, optional): Whether to reorient the image. Defaults to True.
             do_crop (bool, optional): Whether to crop the image. Defaults to True.
             do_bet (bool, optional): Whether to perform brain extraction. Defaults to True.
             do_overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
             use_lesionmask (bool, optional): Whether to use an external lesion mask. Defaults to False.
             lesionmask (str, optional): The path to the lesion mask. Defaults to "lesionmask".

         Returns:
             bool: Whether the pre-processing was successful.
         """
        niter = 5
        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage  = self.subject.t1_data
            anatdir     = os.path.join(self.subject.t1_dir, odn)
            T1          = "T1"
        elif imgtype == 2:
            inputimage  = self.subject.t2_data
            anatdir     = os.path.join(self.subject.t2_dir, odn)
            T1          = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        inputimage = Image(inputimage, must_exist=True, msg="SubjectMpr.prebet input anatomical image is missing")

        # check given lesionmask presence, otherwise exit
        if use_lesionmask:
            lesionmask = Image(lesionmask, must_exist=True, msg="SubjectMpr.prebet given Lesion mask is missing")

        # I CAN START PROCESSING !
        try:

            # create processing dir (if non-existent)
            os.makedirs(anatdir, exist_ok=True)
            T1 = Image(os.path.join(anatdir, T1))  # T1 is now an absolute path

            # init or append log file
            if os.path.isfile(logfile):
                with open(logfile, "a") as text_file:
                    print("# ******************************************************************", file=text_file)
                    print("# updating directory", file=text_file)
                    print(" ", file=text_file)
            else:
                with open(logfile, "w") as text_file:
                    # some initial reporting for the log file
                    print("# Script invoked from directory = " + os.getcwd(), file=text_file)
                    print("# Output directory " + anatdir, file=text_file)
                    print("# Input image is " + inputimage, file=text_file)
                    print(" " + anatdir, file=text_file)

            log = open(logfile, "a")

            # copy original image to anat dir
            rrun("fslmaths " + inputimage + " " + T1, logFile=log)

            # cp lesionmask to anat dir then (even it does not exist) update variable lesionmask=os.path.join(anatdir, "lesionmask")
            if use_lesionmask:
                # I previously verified that it exists
                rrun("fslmaths " + lesionmask + " " + os.path.join(anatdir, "lesionmask"), logFile=log)

            # they are created
            lesionmask      = Image(os.path.join(anatdir, "lesionmask"))
            lesionmaskinv   = Image(lesionmask + "inv")

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
                    rrun("fslmaths " + T1 + " -sub " + str(minval) + " -mas zeromask " + T1 + " -odt float", logFile=log)

            #### REORIENTATION 2 STANDARD
            # required input: " + T1 + "
            # output: " + T1 + " (modified) [ and " + T1 + "_orig and .mat ]
            if not os.path.isfile(T1 + "_orig2std.mat") or do_overwrite:
                if do_reorient:
                    print("# " + self.subject.label + " :Reorienting to standard orientation")
                    rrun("fslmaths " + T1 + " " + T1 + "_orig", logFile=log)
                    # os.system("fslreorient2std " + T1 + " > " + T1 + "_orig2std.mat")
                    run("fslreorient2std " + T1 + " > " + T1 + "_orig2std.mat", logFile=log)
                    rrun("convert_xfm -omat " + T1 + "_std2orig.mat -inverse " + T1 + "_orig2std.mat", logFile=log)
                    rrun("fslmaths " + T1 + " " + T1 + "_orig", logFile=log)

            #### AUTOMATIC CROPPING
            # required input: " + T1 + "
            # output: " + T1 + " (modified) [ and " + T1 + "_fullfov plus various .mats ]
            fullfov = Image(T1 + "_fullfov")
            if not fullfov.exist or do_overwrite:
                if do_crop:
                    print("# " + self.subject.label + " :Automatically cropping the image")
                    T1.mv(fullfov)
                    run(os.path.join(os.path.join(os.getenv('FSLDIR'), "bin"), "robustfov -i " + fullfov + " -r " + T1 + " -m " + T1 + "_roi2nonroi.mat | grep [0-9] | tail -1 > " + T1 + "_roi.log"), logFile=log)
                    # combine this mat file and the one above (if generated)
                    if do_reorient:
                        rrun("convert_xfm -omat " + T1 + "_nonroi2roi.mat -inverse " + T1 + "_roi2nonroi.mat", logFile=log)
                        rrun("convert_xfm -omat " + T1 + "_orig2roi.mat -concat " + T1 + "_nonroi2roi.mat " + T1 + "_orig2std.mat", logFile=log)
                        rrun("convert_xfm -omat " + T1 + "_roi2orig.mat -inverse " + T1 + "_orig2roi.mat", logFile=log)

            ### LESION MASK
            # if I set use_lesionmask: I already verified that the external lesionmask exist and I copied to anat folder and renamed as "lesionmask"
            transform = ""
            if not lesionmask.exist or do_overwrite:
                # make appropriate (reoreinted and cropped) lesion mask (or a default blank mask to simplify the code later on)
                if use_lesionmask:
                    if not os.path.isfile(T1 + "_orig2std.mat"):
                        transform = T1 + "_orig2std.mat"
                    if not os.path.isfile(T1 + "_orig2roi.mat"):
                        transform = T1 + "_orig2roi.mat"
                    if transform != "":
                        rrun("fslmaths " + lesionmask + " " + lesionmask + "_orig", logFile=log)
                        rrun("flirt -in " + lesionmask + "_orig" + " -ref " + T1 + " -applyxfm -interp nearestneighbour -init " + transform + " -out " + lesionmask, logFile=log)
                else:
                    rrun("fslmaths " + T1 + " -mul 0 " + lesionmask, logFile=log)

                rrun("fslmaths " + lesionmask + " -bin " + lesionmask, logFile=log)
                rrun("fslmaths " + lesionmask + " -binv " + lesionmaskinv, logFile=log)

            #### BIAS FIELD CORRECTION (main work, although also refined later on if segmentation is run)
            # required input: " + T1 + "
            # output: " + T1 + "_biascorr  [ other intermediates to be cleaned up ]
            T1_biascorr = Image(T1 + "_biascorr")
            if not T1_biascorr.exist or do_overwrite:
                if biascorr_type > self.BIAS_TYPE_NO:
                    if biascorr_type == self.BIAS_TYPE_STRONG:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print("# " + self.subject.label + " :Estimating and removing field (stage 1 -large-scale fields)")
                        # for the first step (very gross bias field) don't worry about the lesionmask
                        # the following is a replacement for : run $FSLDIR/bin/fslmaths " + T1 + " -s 20 " + T1 + "_s20
                        T1.quick_smooth(T1 + "_s20", logFile=log)
                        rrun("fslmaths " + T1 + " -div " + T1 + "_s20 " + T1 + "_hpf", logFile=log)

                        if do_bet:
                            # get a rough brain mask - it can be *VERY* rough (i.e. missing huge portions of the brain or including non-brain, but non-background) - use -f 0.1 to err on being over inclusive
                            rrun("bet " + T1 + "_hpf " + T1 + "_hpf_brain -m -f 0.1", logFile=log)
                        else:
                            rrun("fslmaths " + T1 + "_hpf " + T1 + "_hpf_brain", logFile=log)
                            rrun("fslmaths " + T1 + "_hpf_brain -bin " + T1 + "_hpf_brain_mask", logFile=log)

                        T1_hpf_bm  = Image(T1 + "_hpf_brain_mask")
                        rrun("fslmaths " + T1 + "_hpf_brain_mask -mas " + lesionmaskinv + " " + T1 + "_hpf_brain_mask", logFile=log)
                        # get a smoothed version without the edge effects
                        T1_hpf_s20 = Image(T1 + "_hpf_s20")

                        rrun("fslmaths " + T1 + " -mas " + T1_hpf_bm + " " + T1_hpf_s20, logFile=log)
                        T1_hpf_s20.quick_smooth(logFile=log)
                        T1_hpf_bm.quick_smooth(T1 + "_initmask_s20", logFile=log)

                        rrun("fslmaths " + T1_hpf_s20 + " -div " + T1 + "_initmask_s20 -mas " + T1_hpf_bm + " " + T1 + "_hpf2_s20", logFile=log)
                        rrun("fslmaths " + T1 + " -mas " + T1_hpf_bm + " -div " + T1 + "_hpf2_s20 " + T1 + "_hpf2_brain", logFile=log)
                        # make sure the overall scaling doesn't change (equate medians)
                        med0 = rrun("fslstats " + T1 + " -k " + T1_hpf_bm + " -P 50", logFile=log)
                        med1 = rrun("fslstats " + T1 + " -k " + T1 + "_hpf2_brain -k " + T1_hpf_bm + " -P 50", logFile=log)
                        rrun("fslmaths " + T1 + "_hpf2_brain -div " + str(med1) + " -mul " + med0 + " " + T1 + "_hpf2_brain", logFile=log)

                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print("# " + self.subject.label + " :Estimating and removing bias field (stage 2 - detailed fields)")
                        rrun("fslmaths " + T1 + "_hpf2_brain -mas " + lesionmaskinv + " " + T1 + "_hpf2_maskedbrain", logFile=log)
                        rrun("fast -o " + T1 + "_initfast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_hpf2_maskedbrain", logFile=log)
                        rrun("fslmaths " + T1 + "_initfast_restore -mas " + lesionmaskinv + " " + T1 + "_initfast_maskedrestore", logFile=log)
                        rrun("fast -o " + T1 + "_initfast2 -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_initfast_maskedrestore", logFile=log)
                        rrun("fslmaths " + T1_hpf_bm + " " + T1 + "_initfast2_brain_mask", logFile=log)
                    else:
                        # weak bias
                        if do_bet:
                            # get a rough brain mask - it can be *VERY* rough (i.e. missing huge portions of the brain or including non-brain, but non-background) - use -f 0.1 to err on being over inclusive
                            rrun("bet " + T1 + " " + T1 + "_initfast2_brain -m -f 0.1", logFile=log)
                        else:
                            rrun("fslmaths " + T1 + " " + T1 + "_initfast2_brain", logFile=log)
                            rrun("fslmaths " + T1 + "_initfast2_brain -bin " + T1 + "_initfast2_brain_mask", logFile=log)

                        rrun("fslmaths " + T1 + "_initfast2_brain " + T1 + "_initfast2_restore", logFile=log)

                    # redo fast again to try and improve bias field
                    rrun("fslmaths " + T1 + "_initfast2_restore -mas " + lesionmaskinv + " " + T1 + "_initfast2_maskedrestore", logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " --nopve --fixed=0 -v " + T1 + "_initfast2_maskedrestore", logFile=log)
                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.subject.label + " :Extrapolating bias field from central region")
                    # use the latest fast output
                    rrun("fslmaths " + T1 + " -div " + T1 + "_fast_restore -mas " + T1 + "_initfast2_brain_mask " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslmaths " + T1 + "_initfast2_brain_mask -ero -ero -ero -ero -mas " + lesionmaskinv + " " + T1 + "_initfast2_brain_mask2", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_initfast2_brain_mask2 -o " + T1 + "_fast_bias", logFile=log)
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
            do_bet:bool=True, betfparam=None, bettypeparam="-R",
            do_reg:bool=True, do_nonlinreg:bool=True,
            do_skipflirtsearch:bool=False,
            do_overwrite:bool=False,
            use_lesionmask:bool=False, lesionmask="lesionmask"
            ):
        """
        Perform brain extraction on the MPR images.

        Args:
            odn (str, optional): The output directory name. Defaults to "anat".
            imgtype (int, optional): The image type. Defaults to 1.
            do_bet (bool, optional): Whether to perform brain extraction. Defaults to True.
            betfparam (list, optional): The list of BET f parameters. Defaults to None.
            bettypeparam (str, optional): The BET transformation type. Defaults to "-R".
            do_reg (bool, optional): Whether to perform registration. Defaults to True.
            do_nonlinreg (bool, optional): Whether to perform non-linear registration. Defaults to True.
            do_skipflirtsearch (bool, optional): Whether to skip FLIRT search. Defaults to False.
            do_overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
            use_lesionmask (bool, optional): Whether to use an external lesion mask. Defaults to False.
            lesionmask (str, optional): The path to the lesion mask. Defaults to "lesionmask".

        Returns:
            bool: Whether the brain extraction was successful.
        """
        if betfparam is None:
            betfparam = []
        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")
        curdir = os.getcwd()

        # check anatomical image imgtype
        if imgtype != 1:
            if do_nonlinreg:
                print("ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
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

        inputimage = Image(inputimage, must_exist=True, msg="SubjectMpr.bet input anatomical image is missing")

        T1              = Image(os.path.join(anatdir, T1))  # T1 is now an absolute path
        lesionmask      = Image(os.path.join(anatdir, lesionmask))
        lesionmaskinv   = Image(os.path.join(anatdir, lesionmask + "inv"))

        # check given lesionmask presence, otherwise exit
        if use_lesionmask and not lesionmask.exist:
            print("ERROR: given Lesion mask is missing....exiting")
            return False

        if len(betfparam) == 0:
            list_bet_fparams = [0.5]
        else:
            list_bet_fparams = betfparam

        # I CAN START PROCESSING !
        try:
            # create some params strings
            if do_skipflirtsearch:
                flirtargs = " -nosearch"
            else:
                flirtargs = " "

            if use_lesionmask:
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
            T1_biascorr_brain = Image(T1 + "_biascorr_brain")
            if not T1_biascorr_brain.exist or do_overwrite:
                if do_reg:
                    if not do_bet:
                        print(self.subject.label + " :Skipping registration, as it requires a non-brain-extracted input image")
                    else:
                        print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        print(self.subject.label + " :Registering to standard space (linear)")

                        if use_lesionmask:
                            flirtargs = flirtargs + " -inweight " + lesionmaskinv

                        rrun("flirt -interp spline -dof 12 -in " + T1 + "_biascorr -ref " + os.path.join(self.subject.fsl_data_std_dir,"MNI152_T1_2mm") + " -dof 12 -omat " + T1 + "_to_MNI_lin.mat -out " + T1 + "_to_MNI_lin " + flirtargs, logFile=log)

                        if do_nonlinreg:
                            # nnlin co-reg T1 to standard
                            # inv warp of T1standard_mask => mask T1.
                            # mask T1 with above img
                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print("Registering to standard space (non-linear)")
                            refmask = os.path.join(anatdir, "MNI152_T1_2mm_brain_mask_dil1")

                            rrun("fslmaths " + self._global.fsl_std_mni_2mm_brain_mask + " -fillh -dilF " + refmask, logFile=log)
                            rrun("fnirt --in=" + T1 + "_biascorr --ref=" + self._global.fsl_std_mni_2mm_head + " --aff=" + T1 + "_to_MNI_lin.mat --refmask=" + refmask +
                                " --fout=" + T1 + "_to_MNI_nonlin_field --jout=" + T1 + "_to_MNI_nonlin_jac --iout=" + T1 + "_to_MNI_nonlin --logout=" + T1 + "_to_MNI_nonlin.txt --cout=" + T1 + "_to_MNI_nonlin_coeff --config=" + self._global.fsl_std_mni_2mm_cnf + " " + fnirtargs, logFile=log)

                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.subject.label + " :Performing brain extraction (using FNIRT)")
                            rrun("invwarp --ref=" + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_coeff -o " + os.path.join(anatdir, "MNI_to_T1_nonlin_field"), logFile=log)
                            rrun("applywarp --interp=nn --in=" + self._global.fsl_std_mni_2mm_brain_mask + " --ref=" + T1 + "_biascorr -w " + os.path.join(anatdir, "MNI_to_T1_nonlin_field") + " -o " + T1 + "_biascorr_brain_mask", logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr_brain_mask -fillh " + T1 + "_biascorr_brain_mask", logFile=log)
                            rrun("fslmaths " + T1 + "_biascorr -mas " + T1 + "_biascorr_brain_mask " + T1 + "_biascorr_brain", logFile=log)
                            ## In the future, could check the initial ROI extraction here
                        else:
                            fp = ""
                            for i in range(len(list_bet_fparams)):
                                betopts = bettypeparam + " -f " + str(list_bet_fparams[i])
                                fp = "_" + str(list_bet_fparams[i]).replace(".", "")
                                print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                print(self.subject.label + " :Performing brain extraction (using BET)")
                                rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_brain" + fp + " -m " + betopts, logFile=log)  ## results sensitive to the f parameter

                            Image(T1 + "_biascorr_brain" + fp).cp(T1_biascorr_brain)
                            Image(T1 + "_biascorr_brain" + fp + "_mask").cp(T1 + "_biascorr_brain_mask")
                else:
                    # do_reg=False
                    if do_bet:
                        fp = ""
                        for i in range(len(list_bet_fparams)):
                            betopts = bettypeparam + " -f " + str(list_bet_fparams[i])
                            fp = "_" + str(list_bet_fparams[i]).replace(".", "")
                            print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            print(self.subject.label + " :Performing brain extraction (using BET)")
                            rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_brain" + fp + " -m " + betopts, logFile=log)  ## results sensitive to the f parameter

                        Image(T1 + "_biascorr_brain" + fp).cp(T1 + "_biascorr_brain")
                        Image(T1 + "_biascorr_brain" + fp + "_mask").cp(T1 + "_biascorr_brain_mask")
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
                    odn:str="anat", imgtype:int=1,
                    do_overwrite:bool=False,
                    do_bet_overwrite:bool=False,
                    add_bet_mask:bool=False,
                    set_origin:bool=False,
                    seg_templ:str="",
                    spm_template_name:str="subj_spm_segment_tissuevolume"
                    ):
        """
        Perform segmentation using SPM.

        Args:
            odn (str, optional): The output directory name. Defaults to "anat".
            imgtype (int, optional): The image type. Defaults to 1.
            do_overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
            do_bet_overwrite (bool, optional): Whether to overwrite existing brain extraction files. Defaults to False.
            add_bet_mask (bool, optional): Whether to add the BET mask to the SPM mask. Defaults to False.
            set_origin (bool, optional): Whether to set the origin of the NIfTI image. Defaults to False.
            seg_templ (str, optional): The path to the segmentation template. Defaults to "".
            spm_template_name (str, optional): The name of the SPM template. Defaults to "subj_spm_segment_tissuevolume".

        Returns:
            bool: Whether the segmentation was successful.
        """
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

        srcinputimage       = Image(os.path.join(anatdir, T1 + "_biascorr"))
        inputimage          = Image(os.path.join(self.subject.t1_spm_dir, T1 + "_" + self.subject.label))

        brain_mask          = Image(os.path.join(self.subject.t1_spm_dir, "brain_mask.nii.gz"))
        skullstripped_mask  = Image(os.path.join(self.subject.t1_spm_dir, "skullstripped_mask.nii.gz"))

        icv_file            = os.path.join(self.subject.t1_spm_dir, "icv_" + self.subject.label + ".dat")

        # check whether skipping
        if brain_mask.exist and not do_overwrite:
            return
        try:

            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(self.subject.t1_spm_dir, exist_ok=True)

            srcinputimage.unzip(inputimage.upath)

            # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
            if set_origin:
                input("press keyboard when finished setting the origin for subj " + self.subject.label + " :")

            if seg_templ == "":
                seg_templ = os.path.join(self._global.spm_dir, "tpm", "TPM.nii")

            seg_templ = Image(seg_templ, must_exist=True, msg="SubjectMPR.spm_segment given template tissue")

            out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "mpr", postfix=self.subject.label)

            sed_inplace(out_batch_job, "<T1_IMAGE>", inputimage.upath)
            sed_inplace(out_batch_job, "<ICV_FILE>", icv_file)
            sed_inplace(out_batch_job, '<SPM_DIR>', self._global.spm_dir)
            sed_inplace(out_batch_job, '<TEMPLATE_TISSUES>', seg_templ)

            call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir], log)

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
            rrun("fslmaths " + srcinputimage.cpath + " -mas " + brain_mask + " -bin " + brain_mask)
            rrun("fslmaths " + srcinputimage.cpath + " -mas " + skullstripped_mask + " -bin " + skullstripped_mask)

            if add_bet_mask:
                T1_biascorr_brain_mask = Image(os.path.join(self.subject.t1_anat_dir, "T1_biascorr_brain_mask"))
                if T1_biascorr_brain_mask.exist:
                    rrun("fslmaths " + brain_mask + " -add " + T1_biascorr_brain_mask + " -bin " + brain_mask)
                elif self.subject.t1_brain_data_mask.exist:
                    rrun("fslmaths " + brain_mask + " -add " + self.subject.t1_brain_data_mask + " " + brain_mask)
                else:
                    print("warning in spm_segment: no other bet mask to add to spm one")

            if do_bet_overwrite:
                # copy SPM mask and use it to mask T1_biascorr
                brain_mask.cp(self.subject.t1_brain_data_mask, logFile=log)
                rrun("fslmaths " + inputimage + " -mas " + brain_mask + " " + self.subject.t1_brain_data, logFile=log)

            Image(inputimage.upath).rm()
            log.close()

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def spm_segment_check(self, check_dartel:bool=True):
        """
        Check the SPM segmentation results for the given subject.

        Args:
            check_dartel (bool, optional): Whether to check the Dartel results. Defaults to True.

        Returns:
            bool: Whether the SPM segmentation results are valid.
        """
        icv_file = os.path.join(self.subject.t1_spm_dir, "icv_" + self.subject.label + ".dat")

        if not os.path.exists(icv_file):
            print("Error in cat_segment_check of subj " + self.subject.label + ", ICV_FILE is missing")
            return False

        if os.path.getsize(icv_file) == 0:
            print("Error in spm_segment_check of subj " + self.subject.label + ", ICV_FILE is empty")
            return False

        c1file = Image(os.path.join(self.subject.t1_spm_dir, "c1T1_" + self.subject.label + ".nii"))
        if not c1file.exist:
            print("Error in spm_segment_check of subj " + self.subject.label + ", C1 File is missing")
            return False

        if check_dartel:
            rc1file = Image(os.path.join(self.subject.t1_spm_dir, "rc1T1_" + self.subject.label + ".nii"))
            if not rc1file.exist:
                print("Error in spm_segment_check of subj " + self.subject.label + ", RC1 File is missing")
                return False

        return True

    # segment T1 with CAT and create  WM+GM mask (CSF is not created)
    # add_bet_mask params is used to correct the presence of holes (only partially filled) in the WM+GM mask.
    # assuming the bet produced a smaller mask in outer part of the gray matter, I add also the bet mask
    # if requested: replace label-t1_brain and label-t1_brain_mask (produced by BET)
    def cat_segment(self,
                    odn:str="anat", imgtype:int=1,
                    do_overwrite:bool=False,
                    set_origin:bool=False,
                    seg_templ:str="",
                    coreg_templ:str="",
                    calc_surfaces:bool=True,
                    num_proc=1,
                    use_existing_nii:bool=True,
                    use_dartel:bool=True,
                    smooth_surf:int=None,
                    extract_extra:bool=True,
                    atlases=None,
                    do_cleanup=Global.CLEANUP_LVL_MED,
                    spm_template_name="cat27_segment_customizedtemplate_tiv_smooth"):

        #y_T1 = Image(os.path.join(self.subject.t1_cat_dir, "mri", "y_T1_" + self.subject.label))
        if Image(self.subject.t1_cat_resampled_surface).cexist and not do_overwrite:
            print(self.subject.label + ": skipping cat_segment, already done")
            return

        if smooth_surf is None:
            smooth_surf = self.subject.t1_cat_surface_resamplefilt

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

        seg_templ = Image(seg_templ, must_exist=True, msg="SubjectMpr.cat_segment segmentation template is not present")

        if coreg_templ == "":
            if use_dartel:
                coreg_templ = self._global.cat_dartel_template
            else:
                coreg_templ = self._global.cat_shooting_template

        coreg_templ = Image(coreg_templ, must_exist=True, msg="SubjectMpr.cat_segment coreg template is not present")

        if atlases is None:
            atlases = ["aparc_HCP_MMP1", "aparc_DK40", "aparc_a2009s"]

        str_atlases = ""
        for atl in atlases:
            str_atlases += "'" + os.path.join(self._global.cat_dir, "atlases_surfaces", "lh." + atl + ".freesurfer.annot") + "'\n"

        srcinputimage   = Image(os.path.join(anatdir, T1 + "_biascorr"))
        inputimage      = Image(os.path.join(self.subject.t1_cat_dir, T1 + "_" + self.subject.label))

        icv_file        = os.path.join(self.subject.t1_cat_dir, "tiv_" + self.subject.label + ".txt")
        brain_mask      = Image(os.path.join(self.subject.t1_cat_dir, "brain_mask.nii.gz"))

        # check whether skipping
        if brain_mask.exist and not do_overwrite:
            return
        try:

            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            os.makedirs(self.subject.t1_cat_dir, exist_ok=True)

            # I may want to process with cat after having previously processed without having set image's origin.
            # thus I may have created a nii version in the cat_proc folder , with the origin properly set
            # unzip nii.gz -> nii in cat folder only if nii is absent or I want to overwrite it.
            if use_existing_nii and not srcinputimage.cpath:
                print("Error in subj: " + self.subject.label + ", method: cat_segment, given image in cat folder is absent")
            else:

                if srcinputimage.cexist:
                    srcinputimage.unzip(inputimage)
                else:
                    print("Error in subj: " + self.subject.label + ", method: cat_segment, biascorr image is absent")

            # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
            if set_origin:
                input("press keyboard when finished setting the origin for subj " + self.subject.label + " :")

            if calc_surfaces is True:
                str_surf = "1"
            else:
                str_surf = "0"

            out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "mpr", postfix=self.subject.label)

            sed_inplace(out_batch_job, "<T1_IMAGE>", inputimage + ".nii")
            sed_inplace(out_batch_job, "<TEMPLATE_SEGMENTATION>", seg_templ)
            sed_inplace(out_batch_job, "<TEMPLATE_COREGISTRATION>", coreg_templ)
            sed_inplace(out_batch_job, "<CALC_SURFACES>", str_surf)
            sed_inplace(out_batch_job, "<TIV_FILE>", icv_file)
            sed_inplace(out_batch_job, "<N_PROC>", str(num_proc))

            resample_string = ""
            if calc_surfaces:
                # resample_string += "matlabbatch{4}.spm.tools.cat.stools.surfresamp.sample{1}.data_surf(1) = cfg_dep('CAT12: Segmentation: Left Thickness', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('()', {1}, '.', 'lhthickness', '()', {':'}));\n"
                resample_string += "matlabbatch{4}.spm.tools.cat.stools.surfresamp.data_surf(1) = cfg_dep('CAT12: Segmentation: Left Thickness',substruct('.', 'val', '{}', {1}, '.', 'val','{}', {1}, '.', 'val', '{}', {1},'.', 'val', '{}', {1}),substruct('()', {1}, '.', 'lhthickness','()', {':'}));\n"
                resample_string += "matlabbatch{4}.spm.tools.cat.stools.surfresamp.merge_hemi = 1;\n"
                resample_string += "matlabbatch{4}.spm.tools.cat.stools.surfresamp.mesh32k = 1;\n"
                resample_string += "matlabbatch{4}.spm.tools.cat.stools.surfresamp.fwhm_surf = " + str(smooth_surf) + ";\n"
                resample_string += "matlabbatch{4}.spm.tools.cat.stools.surfresamp.nproc = " + str(num_proc) + ";\n"
                resample_string += ""
                resample_string += "matlabbatch{5}.spm.tools.cat.stools.surf2roi.cdata = {\n{'" + self.subject.t1_cat_lh_surface + "'}\n};\n"
                resample_string += "matlabbatch{5}.spm.tools.cat.stools.surf2roi.rdata = {\n" + str_atlases + "};\n"

            sed_inplace(out_batch_job, "<SURF_POSTPROCESS>", resample_string)

            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], log, endengine=False)

            if extract_extra is True:
                self.cat_surf_extrameasure(eng=eng)

            if not use_existing_nii:
                inputimage.upath.rm()

            if do_cleanup == Global.CLEANUP_LVL_MED:
                os.system("rm -rf " + os.path.join(self.subject.t1_cat_dir, "mri"))

            log.close()

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def cat_segment_check(self, calc_surfaces:bool=True):
        icv_file = os.path.join(self.subject.t1_cat_dir, "tiv_" + self.subject.label + ".txt")

        if not os.path.exists(icv_file):
            print("Error in cat_segment_check of subj " + self.subject.label + ", ICV_FILE is missing")
            return False

        if os.path.getsize(icv_file) == 0:
            print("Error in cat_segment_check of subj " + self.subject.label + ", ICV_FILE is empty")
            return False

        if not os.path.exists(os.path.join(self.subject.t1_cat_dir, "report", "cat_T1_" + self.subject.label + ".xml")):
            print("Error in cat_segment_check of subj " + self.subject.label + ", CAT REPORT is missing")
            return False

        if calc_surfaces:

            if not os.path.exists(os.path.join(self.subject.t1_cat_surface_dir, "lh.thickness.T1_" + self.subject.label)):
                print("Error in cat_segment_check of subj " + self.subject.label + ", lh thickness is missing")
                return False

            if not os.path.exists(self.subject.t1_cat_resampled_surface):
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
                                 do_overwrite:bool=False,
                                 set_origin:bool=False,
                                 seg_templ:str="",
                                 coreg_templ:str="",
                                 calc_surfaces:bool=True,
                                 num_proc=1,
                                 use_dartel:bool=False,
                                 smooth_surf=None,
                                 use_existing_nii:bool=True,
                                 do_cleanup=Global.CLEANUP_LVL_MED,
                                 spm_template_name="cat_segment_longitudinal_customizedtemplate_tiv_smooth"):

        current_session = self.subject.sessid
        # define placeholder variables for input dir and image name

        if seg_templ == "":
            seg_templ = self._global.spm_tissue_map
        seg_templ = Image(seg_templ, must_exist=True, msg="SubjectMpr.cat_segment_longitudinal segmentation template ")

        if coreg_templ == "":
            if use_dartel:
                coreg_templ = self._global.cat_dartel_template
            else:
                coreg_templ = self._global.cat_shooting_template
        coreg_templ = Image(coreg_templ, must_exist=True, msg="SubjectMpr.cat_segment_longitudinal coreg template ")

        if smooth_surf is None:
            smooth_surf = self.subject.t1_cat_surface_resamplefilt

        try:

            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

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

                srcinputimage   = Image(os.path.join(anatdir, T1 + "_biascorr"))
                inputimage      = Image(os.path.join(subj.t1_cat_dir, T1 + "_" + subj.label))
                brain_mask      = Image(os.path.join(subj.t1_cat_dir, "brain_mask.nii.gz"))

                # check whether skipping
                if brain_mask.exist and not do_overwrite:
                    return

                os.makedirs(subj.t1_cat_dir, exist_ok=True)

                # I may want to process with cat after having previously processed without having set image's origin.
                # thus I may have created a nii version in the cat_proc folder, with the origin properly set
                # unzip T1_biascorr.nii.gz -> nii in cat folder only if nii is absent or I want to overwrite it.
                if not use_existing_nii:
                    if srcinputimage.cexist:
                        srcinputimage.unzip(inputimage)
                    else:
                        print("Error in subj: " + self.subject.label + ", method: cat_segment, biascorr image is absent")
                else:
                    if not inputimage.uexist:
                        print("Error in subj: " + self.subject.label + ", method: cat_segment, given image in cat folder is absent")

                # here I may stop script to allow resetting the nii origin. sometimes is necessary to perform the segmentation
                if set_origin:
                    input("press keyboard when finished setting the origin for subj " + subj.label + " :")

                images_string = images_string + "'" + inputimage.upath + ",1'\n"
                images_list.append(inputimage.upath)

            if calc_surfaces:
                str_surf = "1"
            else:
                str_surf = "0"

            out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "mpr", postfix=self.subject.label)

            sed_inplace(out_batch_job, "<T1_IMAGES>", images_string)
            sed_inplace(out_batch_job, "<TEMPLATE_SEGMENTATION>", seg_templ)
            sed_inplace(out_batch_job, "<TEMPLATE_COREGISTRATION>", coreg_templ)
            sed_inplace(out_batch_job, "<CALC_SURFACES>", str_surf)
            sed_inplace(out_batch_job, "<N_PROC>", str(num_proc))

            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], log, endengine=False)

            if calc_surfaces:
                for sess in sessions:
                    self.cat_surf_resample(sess, num_proc, isLong=True, smooth_surf=smooth_surf, endengine=False, eng=eng)

            for sess in sessions:
                self.cat_tiv_calculation(sess, isLong=True, endengine=False, eng=eng)

            if not use_existing_nii:
                Images([images_list]).rm()

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

    def cat_segment_longitudinal_check(self, sessions, calc_surfaces:bool=True):

        err = ""

        for sess in sessions:

            subj = self.subject.get_properties(sess)

            icv_file = os.path.join(subj.t1_cat_dir, "tiv_r_" + subj.label + ".txt")
            report_file = os.path.join(subj.t1_cat_dir, "report", "cat_rT1_" + subj.label + ".xml")

            if not os.path.exists(report_file):
                err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", CAT REPORT is missing" + "\n"

            if not os.path.exists(icv_file):
                err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", ICV_FILE is missing" + "\n"
            else:
                if os.path.getsize(icv_file) == 0:
                    err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", ICV_FILE is empty" + "\n"

            if calc_surfaces:

                if not os.path.exists(os.path.join(subj.t1_cat_surface_dir, "lh.thickness.rT1_" + subj.label)):
                    err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", lh thickness is missing" + "\n"

                if not os.path.exists(subj.t1_cat_resampled_surface_longitudinal):
                    err = err + "Error in cat_segment_check of subj " + subj.label + ", session: " + str(sess) + ", RESAMPLED SURFACE is missing" + "\n"

        if err != "":
            print(err)

        return err

    def cat_surf_resample(self, session=1, num_proc=1, isLong=False, mesh32k=1, smooth_surf=None, endengine:bool=True, eng=None):

        if smooth_surf is None:
            smooth_surf = self.subject.t1_cat_surface_resamplefilt

        spm_template_name = "subjs_cat_surf_resample"

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "mpr", postfix=self.subject.label)
        subj = self.subject.get_properties(session)

        surf_prefix = "T1"
        if isLong:
            surf_prefix = "rT1"
        surface = os.path.join(subj.t1_cat_dir, "surf", "lh.thickness." + surf_prefix + "_" + subj.label)

        resample_string = ""
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.data_surf = {'" + surface + "'};\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.merge_hemi = 1;\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.mesh32k = " + str(mesh32k) + ";\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.fwhm_surf = " + str(smooth_surf) + ";\n"
        resample_string = resample_string + "matlabbatch{1}.spm.tools.cat.stools.surfresamp.nproc = " + str(num_proc) + ";\n"

        write_text_file(out_batch_job, resample_string)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine, eng=eng)

    def cat_surf_extrameasure(self, session=1, num_proc=1, inlhcentral_surf=None, endengine:bool=True, eng=None):

        if inlhcentral_surf is None:
            inlhcentral_surf = self.subject.t1_cat_lhcentral_image

        spm_template_name = "subj_cat_surf_folding_sulcdepth_resamplesmooth"

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "mpr", postfix=self.subject.label)
        subj = self.subject.get_properties(session)

        sed_inplace(out_batch_job, "<LH_CENTRAL>", inlhcentral_surf)
        sed_inplace(out_batch_job, "<N_PROC>", str(num_proc))

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine, eng=eng)

    def cat_tiv_calculation(self, session=1, isLong:bool=False, endengine:bool=True, eng=None):

        spm_template_name = "mpr_cat_tiv_calculation"

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files(spm_template_name, "mpr", postfix=self.subject.label)

        subj = self.subject.get_properties(session)

        prefix      = "cat_T1_"
        prefix_tiv  = "tiv_"
        if isLong is True:
            prefix = "cat_rT1_"
            prefix_tiv = "tiv_r_"

        report_file = os.path.join(subj.t1_cat_dir, "report", prefix + subj.label + ".xml")
        tiv_file    = os.path.join(subj.t1_cat_dir, prefix_tiv + subj.label + ".txt")

        tiv_string = ""
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.data_xml = {'" + report_file + "'};\n"
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.calcvol_TIV = 1;\n"
        tiv_string = tiv_string + "matlabbatch{1}.spm.tools.cat.tools.calcvol.calcvol_name = '" + tiv_file + "';\n"

        write_text_file(out_batch_job, tiv_string)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir], endengine=endengine, eng=eng)

    def cat_extract_roi_based_surface(self, atlases=None):

        if atlases is None:
            atlases = ["aparc_HCP_MMP1", "aparc_DK40", "aparc_a2009s"]

        _atlases = ""
        for atlas in atlases:
            _atlases = _atlases + "\'" + os.path.join(self._global.cat_dir, "atlases_surfaces", "lh." + atlas + ".freesurfer.annot") + "\'" + "\n"

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files("cat_extract_roi_based_surface", "mpr", postfix=self.subject.label)

        left_thick_img = os.path.join(self.subject.t1_cat_surface_dir, "lh.thickness.T1_" + self.subject.label)
        if not os.path.exists(left_thick_img):
            print("ERROR in cat_extract_roi_based_surface of subj " + self.subject.label + ", missing left thickness surface")
            return

        sed_inplace(out_batch_job, "<LH_TCK_IMAGES>", "\'" + left_thick_img + "\'")
        sed_inplace(out_batch_job, "<ATLASES>", _atlases)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

    def spm_tissue_volumes(self, spm_template_name="spm_icv_template", endengine=False, eng=None):

        seg_mat = os.path.join(self.subject.t1_spm_dir, "T1_biascorr_" + self.subject.label + "_seg8.mat")
        icv_file = os.path.join(self.subject.t1_spm_dir, "icv_" + self.subject.label + ".dat")

        out_batch_job, out_batch_start = self.subject.project.adapt_batch_files("cat_extract_roi_based_surface", "mpr", self.subject.label)

        sed_inplace(out_batch_job, "<SEG_MAT>", seg_mat)
        sed_inplace(out_batch_job, "<ICV_FILE>", icv_file)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir], endengine=endengine, eng=eng)

    def surf_resampled_longitudinal_diff(self, sessions, outdir:str="", matlab_func="subtract_gifti"):

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

        call_matlab_function_noret(matlab_func, [self._global.spm_functions_dir], "\"" + surfaces[1] + "\",  \"" + surfaces[0] + "\", \"" + res_surf + "\"")

    # ==================================================================================================================
    #   TISSUE-TYPE SEGMENTATION
    #   SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION
    def postbet(self,
                odn="anat", imgtype=1, smooth=10,
                betfparam=0.5,
                do_reg:bool=True, do_nonlinreg:bool=True,
                do_seg:bool=True,
                do_overwrite:bool=False,
                use_lesionmask:bool=False, lesionmask="lesionmask"):
        niter = 5
        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

        # check anatomical image imgtype
        if imgtype != 1:
            if do_nonlinreg:
                print("ERROR: Cannot do non-linear registration with non-T1 images, please re-run with do_nonlinreg=False")
                return False

        # define placeholder variables for input dir and image name
        if imgtype == 1:
            inputimage  = self.subject.t1_data
            anatdir     = os.path.join(self.subject.t1_dir, odn)
            T1          = "T1"
            T1_label    = "T1"

        elif imgtype == 2:
            inputimage  = self.subject.t2_data
            anatdir     = os.path.join(self.subject.t2_dir, odn)
            T1          = "T2"
            T1_label    = "T2"
        else:
            print("ERROR: PD input format is not supported")
            return False

        T1              = Image(os.path.join(anatdir, T1))  # T1 is now an absolute path
        inputimage      = Image(inputimage, must_exist=True, msg="SubjectMpr.postbet input image")

        # check given lesionmask presence, otherwise exit
        lesionmask      = Image(os.path.join(anatdir, lesionmask), must_exist=True, msg="SubjectMpr.postbet lesion mask")
        lesionmaskinv   = Image(os.path.join(anatdir, lesionmask + "inv"), must_exist=True, msg="SubjectMpr.postbet lesion mask inv")

        # I CAN START PROCESSING !
        try:

            betopts = "-f " + str(betfparam[0])

            # create processing dir (if non-existent) and cd to it
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

            if (not Image(T1 + "_fast_pve_1").exist and not Image(os.path.join(self.subject.fast_dir, "T1_fast_pve_1")).exist) or do_overwrite:
                if do_seg:

                    print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    print(self.subject.label + " :Performing tissue-imgtype segmentation")
                    rrun("fslmaths " + T1 + "_biascorr_brain" + " -mas " + lesionmaskinv + " " + T1 + "_biascorr_maskedbrain", logFile=log)
                    rrun("fast -o " + T1 + "_fast -l " + str(smooth) + " -b -B -t " + str(imgtype) + " --iter=" + str(niter) + " " + T1 + "_biascorr_maskedbrain", logFile=log)
                    Image(T1 + "_biascorr").mv(T1 + "_biascorr_init", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_restore " + T1 + "_biascorr_brain", logFile=log)  # overwrite brain

                    # extrapolate bias field and apply to the whole head image
                    rrun("fslmaths " + T1 + "_biascorr_brain_mask -mas " + lesionmaskinv + " " + T1 + "_biascorr_brain_mask2", logFile=log)
                    # rrun("fslmaths " + self.t1_brain_data_mask + " -mas " + lesionmaskinv + " " + T1 + "_biascorr_brain_mask2",logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_restore -mas " + T1 + "_biascorr_brain_mask2 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -sub 1 " + T1 + "_fast_totbias", logFile=log)
                    rrun("fslsmoothfill -i " + T1 + "_fast_totbias -m " + T1 + "_biascorr_brain_mask2 -o " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_bias -add 1 " + T1 + "_fast_bias", logFile=log)
                    rrun("fslmaths " + T1 + "_fast_totbias -add 1 " + T1 + "_fast_totbias", logFile=log)
                    # run $FSLDIR/bin/fslmaths " + T1 + "_fast_totbias -sub 1 -mas " + T1 + "_biascorr_brain_mask2 -dilall -add 1 " + T1 + "_fast_bias # alternative to fslsmoothfill", logFile=log)
                    rrun("fslmaths " + T1 + "_biascorr_init -div " + T1 + "_fast_bias " + T1 + "_biascorr", logFile=log)  # overwrite full image

                    Image(T1 + "_biascorr_brain").cp(self.subject.t1_brain_data)
                    Image(T1 + "_biascorr").cp(self.subject.t1_data)

                    if do_nonlinreg:

                        # regenerate the standard space version with the new bias field correction applied
                        if Image(T1 + "_to_MNI_nonlin_field").exist:
                            rrun("applywarp -i " + T1 + "_biascorr -w " + T1 + "_to_MNI_nonlin_field -r " + os.path.join(self.subject.fsl_data_std_dir,"MNI152_" + T1_label + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline", logFile=log)
                        else:
                            if Image(os.path.join(self.subject.roi_std_dir, "hr2std_warp")).exist:
                                rrun("applywarp -i " + T1 + "_biascorr -w " + os.path.join(self.subject.roi_std_dir, "hr2std_warp") + " -r " + os.path.join(self.subject.fsl_data_std_dir,"MNI152_" + T1_label + "_2mm") + " -o " + T1 + "_to_MNI_nonlin --interp=spline", logFile=log)
                            else:
                                print("WARNING in postbet: either " + T1 + "_to_MNI_nonlin_field" + " or " + os.path.join(self.subject.roi_std_dir, "hr2std_warp") + " is missing")

            #### SKULL-CONSTRAINED BRAIN VOLUME ESTIMATION (only done if registration turned on, and segmentation done, and it is a T1 image)
            # required inputs: " + T1 + "_biascorr
            # output: " + T1 + "_vols.txt
            if not os.path.isfile(T1 + "_vols.txt") or do_overwrite:

                if do_reg and do_seg and T1_label == "T1":
                    print(self.subject.label + " :Skull-constrained registration (linear)")

                    rrun("bet " + T1 + "_biascorr " + T1 + "_biascorr_bet -s -m " + betopts, logFile=log)
                    rrun("pairreg " + os.path.join(self.subject.fsl_data_std_dir,"MNI152_T1_2mm_brain") + " " + T1 + "_biascorr_bet " + os.path.join(self.subject.fsl_data_std_dir,"MNI152_T1_2mm_skull") + " " + T1 + "_biascorr_bet_skull " + T1 + "2std_skullcon.mat", logFile=log)

                    if use_lesionmask:
                        rrun("fslmaths " + lesionmask + " -max " + T1 + "_fast_pve_2 " + T1 + "_fast_pve_2_plusmask -odt float",logFile=log)
                        # ${FSLDIR}/bin/fslmaths lesionmask -bin -mul 3 -max " + T1 + "_fast_seg " + T1 + "_fast_seg_plusmask -odt int

                    vscale  = float(runpipe("avscale " + T1 + "2std_skullcon.mat | grep Determinant | awk '{ print $3 }'",logFile=log)[0].decode("utf-8").split("\n")[0])
                    ugrey   = float(runpipe("fslstats " + T1 + "_fast_pve_1 -m -v | awk '{ print $1 * $3 }'", logFile=log)[0].decode("utf-8").split("\n")[0])
                    uwhite  = float(runpipe("fslstats " + T1 + "_fast_pve_2 -m -v | awk '{ print $1 * $3 }'", logFile=log)[0].decode("utf-8").split("\n")[0])

                    ngrey   = ugrey * vscale
                    nwhite  = uwhite * vscale
                    ubrain  = ugrey + uwhite
                    nbrain  = ngrey + nwhite

                    with open(T1 + "_vols.txt", "w") as file_vol:
                        print("Scaling factor from " + T1 + " to MNI (using skull-constrained linear registration) = " + str(vscale), file=file_vol)
                        print("Brain volume in mm^3 (native/original space) = " + str(ubrain), file=file_vol)
                        print("Brain volume in mm^3 (normalised to MNI) = " + str(nbrain), file=file_vol)

        except Exception as e:
            traceback.print_exc()
            print(e)

    def finalize(self, odn="anat", imgtype=1, do_cleanup=Global.CLEANUP_LVL_MED):

        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

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

            if do_cleanup == Global.CLEANUP_LVL_MIN:         #### CLEANUP
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning up intermediate files"
                rrun("imrm " + T1 + "_biascorr_bet_mask " + T1 + "_biascorr_bet " + T1 + "_biascorr_brain_mask2 " + T1 + "_biascorr_init " + T1 + "_biascorr_maskedbrain " + T1 + "_biascorr_to_std_sub " + T1 + "_fast_bias_idxmask " + T1 + "_fast_bias_init " + T1 + "_fast_bias_vol2 " + T1 + "_fast_bias_vol32 " + T1 + "_fast_totbias " + T1 + "_hpf* " + T1 + "_initfast* " + T1 + "_s20 " + T1 + "_initmask_s20", logFile=log)

            if do_cleanup == Global.CLEANUP_LVL_MED:    #### STRONG CLEANUP
                #  print("Current date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) print( "$SUBJ_NAME :Cleaning all unnecessary files "
                Images([T1, T1 + "_orig", T1 + "_fullfov"]).rm(log)
                if os.path.exists(self.subject.t1_cat_mri_dir):
                    os.system("rm -rf " + self.subject.t1_cat_mri_dir)

            if do_cleanup == Global.CLEANUP_LVL_HI:       #### TOTAL CLEANUP
                os.system("rm -rf " + self.subject.t1_anat_dir)

        except Exception as e:
            traceback.print_exc()
            log.close()
            print(e)

    def first(self, structures:str="", t1_image:str="", odn:str=""):

        logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

        # init params
        if t1_image == "":
            t1_image = self.subject.t1_brain_data

        t1_image = Image(t1_image)

        if structures != "":
            structs = "-s " + structures
            list_structs = structures.split(",")
        else:
            list_structs = []
            structs = ""

        output_roi_dir  = os.path.join(self.subject.roi_t1_dir, odn)
        temp_dir        = os.path.join(self.subject.first_dir, "temp")

        try:
            os.makedirs(self.subject.first_dir, exist_ok=True)
            os.makedirs(output_roi_dir, exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)

            # os.chdir(temp_dir)

            log = open(logfile, "a")

            print("******************************************************************", file=log)
            print("starting FIRST processing", file=log)
            print("******************************************************************", file=log)

            print(self.subject.label + ": FIRST (of " + t1_image.name + " " + structs + " " + odn + ")")

            image_label_path = os.path.join(self.subject.first_dir, t1_image.name)

            rrun("first_flirt " + t1_image + " " + image_label_path + "_to_std_sub", logFile=log)
            rrun("run_first_all -i " + t1_image + " - o " + image_label_path + " -d -a " + image_label_path + "_to_std_sub.mat -b " + structs, logFile=log)

            for struct in list_structs:
                Image(image_label_path + "-" + struct + "_first.nii.gz").mv(os.path.join(output_roi_dir, "mask_" + struct + "_hr.nii.gz"), logFile=log)

        except Exception as e:
            traceback.print_exc()
            print(e)

    # FreeSurfer recon-all
    def fs_reconall(self, step="-all", do_overwrite=False, backtransfparams=" RL PA IS ", numcpu=1):

        # check whether skipping
        if step == "-all" and self.subject.t1_fs_aparc_aseg.exist and not do_overwrite:
            return

        if step == "-autorecon1" and Image(os.path.join(self.subject.t1_dir, "freesurfer", "mri", "brainmask.mgz")).exist and not do_overwrite:
            return

        try:
            logfile = os.path.join(self.subject.t1_dir, "mpr_log.txt")

            with open(logfile, "a") as text_file:
                print("******************************************************************", file=text_file)
                print("updating directory", file=text_file)
                print(" ", file=text_file)

            log = open(logfile, "a")

            rrun("mri_convert " + self.subject.t1_data + ".nii.gz " + self.subject.t1_data + ".mgz", logFile=log)

            try:
                os.environ['OLD_SUBJECTS_DIR'] = os.environ['SUBJECTS_DIR']
            except Exception:
                pass

            os.environ['SUBJECTS_DIR'] = self.subject.t1_dir

            rrun("recon-all -subject freesurfer" + " -i " + self.subject.t1_data + ".mgz " + step + " -threads " + str(numcpu), logFile=log)

            t1_fs_data_orig = self.subject.t1_fs_data.add_postfix2name("_orig")

            # calculate linear trasf to move coronal-conformed T1 back to original reference (specified by backtransfparams)
            # I convert T1.mgz => nii.gz, then I swapdim to axial and coregister to t1_data
            rrun("mri_convert " + self.subject.t1_fs_data + ".mgz " + self.subject.t1_fs_data.cpath)
            rrun("fslswapdim " + self.subject.t1_fs_data.cpath + backtransfparams + t1_fs_data_orig.cpath)
            rrun("flirt -in " + t1_fs_data_orig.cpath + " -ref " + self.subject.t1_data + " -omat " + os.path.join(self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -cost corratio -dof 6 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear")
            Images([self.subject.t1_fs_data.cpath, t1_fs_data_orig.cpath])

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
    def use_fs_brainmask(self, backtransfparams=" RL PA IS ", erosiontype=" -kernel boxv 5 ", is_interactive:bool=True, do_clean:bool=True):

        t1_fs_brainmask_data_orig       = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig")
        t1_fs_brainmask_data_orig_ero   = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero")

        # convert fs brainmask to nii.gz => move to the same orientation as working image (usually axial) => erode it
        rrun("mri_convert " + self.subject.t1_fs_brainmask_data + ".mgz " + self.subject.t1_fs_brainmask_data.cpath)
        rrun("fslswapdim " + self.subject.t1_fs_brainmask_data.cpath + backtransfparams + t1_fs_brainmask_data_orig.cpath)

        if erosiontype != "":
            rrun("fslmaths " + t1_fs_brainmask_data_orig.cpath + erosiontype + " -ero " + t1_fs_brainmask_data_orig_ero.cpath)
        else:
            t1_fs_brainmask_data_orig.cpath.cp(t1_fs_brainmask_data_orig_ero.cpath)

        if is_interactive:
            rrun("fsleyes " + self.subject.t1_data + " " + self.subject.t1_brain_data + " " + t1_fs_brainmask_data_orig_ero.cpath, stop_on_error=False)

            do_substitute = input("do you want to substitute bet image with this one? press y or n\n : ")

            if do_substitute == "y":
                self.use_fs_brainmask_exec(do_clean)

        else:
            self.use_fs_brainmask_exec(do_clean)

        if do_clean:
            Images([self.subject.t1_fs_brainmask_data.cpath,
                    t1_fs_brainmask_data_orig.cpath,
                    t1_fs_brainmask_data_orig_ero.cpath]).rm()

    def use_fs_brainmask_exec(self, add_previous:bool=False, do_clean:bool=True):

        t1_fs_brainmask_data_orig_ero       = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero")
        t1_fs_brainmask_data_orig_ero_mask  = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero_mask")
        t1_fs_brainmask_data_orig_ero_in_t1 = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero_in_t1")

        # I may have manually edited self.t1_fs_brainmask + "_orig_ero.nii.gz"
        # although is at the same reference as working image, it still has to be co-registered
        # 1) I move this orig brainmask to the same space as t1 and t1_brain, applying the coronalconformed->original transformation to eroded brainmask_orig
        rrun("flirt -in " + t1_fs_brainmask_data_orig_ero + " -ref " + self.subject.t1_data + " -out " + t1_fs_brainmask_data_orig_ero_in_t1 + " -applyxfm -init " + os.path.join(self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

        if add_previous:
            # => I create its mask (with holes) and add to the bet's one (assumed as smaller but without holes)
            rrun("fslmaths " + t1_fs_brainmask_data_orig_ero_in_t1 + " -bin -add " + self.subject.t1_brain_data_mask + " -bin " + t1_fs_brainmask_data_orig_ero_mask)
        else:
            # => just fill holes
            rrun("fslmaths " + t1_fs_brainmask_data_orig_ero_in_t1 + " -bin -fillh " + t1_fs_brainmask_data_orig_ero_mask)

        t1_fs_brainmask_data_orig_ero_mask.cp(self.subject.t1_brain_data_mask)  # substitute bet mask with this one
        rrun("fslmaths " + self.subject.t1_data + " -mas " + self.subject.t1_brain_data_mask + " " + self.subject.t1_brain_data)

        if do_clean:
            t1_fs_brainmask_data_orig_ero_in_t1.cpath.rm()

    # check whether substituting bet brain with the one created by SPM-segment.
    # since the SPM GM+WM mask contains holes within the image. I create a mask with the latter and the bet mask (which must be coregistered since fs ones are coronal)
    def use_spm_brainmask(self, backtransfparams=" RL PA IS ", erosiontype=" -kernel boxv 5 ", is_interactive:bool=True, do_clean:bool=True):

        t1_fs_brainmask_data_orig           = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig")
        t1_fs_brainmask_data_orig_ero       = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero")

        # convert fs brainmask to nii.gz => move to the same orientation as working image (usually axial) => erode it
        rrun("mri_convert " + self.subject.t1_fs_brainmask_data + ".mgz " + self.subject.t1_fs_brainmask_data.cpath)
        rrun("fslswapdim " + self.subject.t1_fs_brainmask_data.cpath + backtransfparams + t1_fs_brainmask_data_orig.cpath)
        rrun("fslmaths " + t1_fs_brainmask_data_orig.cpath + erosiontype + " -ero " + t1_fs_brainmask_data_orig_ero.cpath)

        if is_interactive is True:
            rrun("fsleyes " + self.subject.t1_data + " " + self.subject.t1_brain_data + " " + t1_fs_brainmask_data_orig_ero.cpath)

            do_substitute = input("do you want to substitute bet image with this one? press y or n\n : ")

            if do_substitute == "y":
                self.use_spm_brainmask_exec(do_clean)

        else:
            self.use_spm_brainmask_exec(do_clean)

        if do_clean:
            Images([self.subject.t1_fs_brainmask_data.cpath,
                    t1_fs_brainmask_data_orig.cpath,
                    t1_fs_brainmask_data_orig_ero.cpath]).rm()

    def use_spm_brainmask_exec(self, do_clean:bool=True):

        t1_fs_brainmask_data_orig_ero       = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero")
        t1_fs_brainmask_data_orig_ero_mask  = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero_mask")
        t1_fs_brainmask_data_orig_ero_in_t1 = self.subject.t1_fs_brainmask_data.add_postfix2name("_orig_ero_in_t1")

        # I may have manually edited self.t1_fs_brainmask + "_orig_ero.nii.gz"
        # although is at the same reference as working image, it still has to be co-registered
        # 1) I move this orig brainmask to the same space as t1 and t1_brain, applying the coronalconformed->original transformation to eroded brainmask_orig
        rrun("flirt -in " + t1_fs_brainmask_data_orig_ero + " -ref " + self.subject.t1_data + " -out " + t1_fs_brainmask_data_orig_ero_in_t1 + " -applyxfm -init " + os.path.join(
                self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

        # => I create its mask (with holes) and add to the bet's one (assumed as smaller but without holes)
        rrun("fslmaths " + t1_fs_brainmask_data_orig_ero_in_t1 + " -bin -add " + self.subject.t1_brain_data_mask + " -bin " + t1_fs_brainmask_data_orig_ero_mask)

        t1_fs_brainmask_data_orig_ero_mask.cp(self.subject.t1_brain_data_mask)  # substitute bet mask with this one
        rrun("fslmaths " + self.subject.t1_data + " -mas " + t1_fs_brainmask_data_orig_ero_mask + " " + self.subject.t1_brain_data)

        if do_clean:
            t1_fs_brainmask_data_orig_ero_in_t1.rm()

    # copy bet, spm and fs extracted brain to given directory
    def compare_brain_extraction(self, tempdir, backtransfparams=" RL PA IS "):

        # bet
        Image(os.path.join(self.subject.t1_anat_dir, "T1_biascorr_brain")).cp(os.path.join(tempdir, self.subject.label + "_bet.nii.gz"))

        # spm (assuming bet mask is smaller than spm's one and the latter contains holes...I make their union to mask the t1
        brain_mask = Image(os.path.join(self.subject.t1_spm_dir, "brain_mask"))
        if brain_mask.exist:
            temp_bet_spm_mask = Image(os.path.join(tempdir, self.subject.label + "_bet_spm_mask"))
            rrun("fslmaths " + brain_mask + " -add " + self.subject.t1_brain_data_mask + " " + temp_bet_spm_mask)
            rrun("fslmaths " + self.subject.t1_data + " -mas " + temp_bet_spm_mask + " " + os.path.join(tempdir, self.subject.label + "_spm"))
            temp_bet_spm_mask.rm()
        else:
            print("subject " + self.subject.label + " spm mask is not present")

        # freesurfer
        fsmask = Image(os.path.join(self.subject.t1_dir, "freesurfer", "mri", "brainmask"))
        temp_brain_mask = Image(os.path.join(tempdir, self.subject.label + "_brainmask.nii.gz"))
        if fsmask.exist:
            rrun("mri_convert " + fsmask + ".mgz " + temp_brain_mask.cpath)

            rrun("fslswapdim " + temp_brain_mask.cpath + backtransfparams + temp_brain_mask.cpath)
            rrun("flirt -in " + temp_brain_mask.cpath + " -ref " + self.subject.t1_data + " -out " + temp_brain_mask.cpath + " -applyxfm -init " + os.path.join(self.subject.t1_fs_mri_dir, "fscor2t1.mat") + " -interp trilinear")

            # rrun("fslmaths " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz") + " -bin " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz"))
            # rrun("fslmaths " + os.path.join(betdir, "T1_biascorr_brain") + " -mas " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz") + " " + os.path.join(tempdir, subj.label + "_brainmask.nii.gz"))
        else:
            print("subject " + self.subject.label + " freesurfer's brainmask is not present")

    def cleanup(self, lvl=Global.CLEANUP_LVL_MIN):

        os.removedirs(self.subject.t1_anat_dir)

        if lvl == Global.CLEANUP_LVL_HI:

            os.removedirs(self.subject.first_dir)
            os.removedirs(self.subject.fast_dir)
            rrun("mv " + self.subject.t1_cat_surface_dir + " " + self.subject.t1_dir)
