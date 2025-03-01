import csv
import os
from shutil import copyfile
from typing import List

from Global import Global
from myutility.SubjectTracts import SubjectTracts
from myutility.fileutilities import write_text_file, read_value_from_file
from myutility.images.Image import Image
from myutility.myfsl.utils.run import rrun
from myutility.images.Images import Images
from myutility.Tract import Tract

class SubjectDti:
    """
    This class contains methods for diffusion tensor imaging (DTI) processing.

    Args:
        subject (Subject): The subject object.
        _global (Global): The global object.

    """
    def __init__(self, subject:'Subject', _global:Global):
        self.subject:'Subject'    = subject
        self._global:Global     = _global

    # ==================================================================================================================================================
    # DIFFUSION
    # ==================================================================================================================================================
    def get_nodiff(self, logFile=None):
        """
        This function extracts the non-diffusion-weighted (b0) image from the DTI data.

        Args:
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            None.
        """
        if not self.subject.dti_nodiff_data.exist:
            rrun(f"fslroi {os.path.join(self.subject.dti_data)} {self.subject.dti_nodiff_data} 0 1", logFile=logFile)

        if not self.subject.dti_nodiff_brain_data.exist:
            rrun(f"bet {self.subject.dti_nodiff_data} {self.subject.dti_nodiff_brain_data} -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

    # eddy correction when PA sequence is not available
    def eddy_correct(self, overwrite:bool=False, logFile=None):
        """
        This function performs eddy correction on the DTI data.

        Args:
            overwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            None.
        """
        if self.subject.dti_data.exist:
            print("WARNING in dti eddy_correct of subject: " + self.subject.label + ",dti image is missing...skipping subject")
            return

        rrun(f"fslroi {self.subject.dti_data} {self.subject.dti_nodiff_data} 0 1", logFile=logFile)
        rrun(f"bet {self.subject.dti_nodiff_data} {self.subject.dti_nodiff_brain_data} -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        if not self.subject.dti_ec_data.exist or overwrite:
            print("starting eddy_correct on " + self.subject.label)
            rrun(f"eddy_correct {self.subject.dti_data} {self.subject.dti_ec_data} 0", logFile=logFile)

            os.system(f"bash fdt_rotate_bvecs {self.subject.dti_bvec} {self.subject.dti_rotated_bvec} {self.subject.dti_ec_data}.ecclog")

    # perform eddy correction, finally writes  .._ec.nii.gz &  .._-dti_rotated.bvec
    def eddy(self, exe_ver:str="eddy_openmp", acq_params=None, config:str="b02b0_1.cnf", estmove=True, slice2vol=6, rep_out:str="both", json=None, logFile=None):
        """
        This function performs eddy correction on the DTI data.

        Args:
            exe_ver (str, optional): The eddy executable version. Defaults to "eddy_openmp".
            acq_params (str, optional): The topup acqparams file path. Defaults to None.
            config (str, optional): The eddy config file path. Defaults to "b02b0_1.cnf".
            estmove (bool, optional): Whether to estimate movement by susceptibility. Defaults to True.
            slice2vol (int, optional): The eddy mporder value. Defaults to 6.
            rep_out (str, optional): The eddy repol output type. Defaults to "both".
            json (str, optional): The eddy json file path. Defaults to None.
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            None.
        """
        if not self.subject.dti_data.exist:
            print("WARNING in dti eddy of subject: " + self.subject.label + ",dti image is missing...skipping subject")
            return      # in normal usage, welcome script, self.hasDTI has been checked, this is used for single call

        if acq_params is None:
            acq_params = self.subject.project.topup_dti_params

        if json is None:
            json = self.subject.project.eddy_dti_json

        if not (rep_out == "both" or rep_out == "gw" or rep_out == "sw" or rep_out == ""):
            print("ERROR in eddy of subject: " + self.subject.label + ", rep_out (" + str(rep_out) + ") param must be one of the following: sw,gw,both,'', exiting.....")
            return

        if not os.path.exists(acq_params):
            raise Exception("ERROR in eddy of subject: " + self.subject.label + ", topup_acqparams file does not exist, exiting.....")

        if not os.path.exists(json):
            if (rep_out == "both" or rep_out == "gw" or rep_out == "sw") or slice2vol > 0:
                raise Exception("ERROR in eddy of subject: " + self.subject.label + ", json file does not exist and repol type was set or mporder > 0 , exiting.....")

        if not os.path.exists(self.subject.project.eddy_index):
            raise Exception("ERROR in eddy of subject: " + self.subject.label + ", eddy_index file does not exist, exiting.....")

        if not self.subject.dti_pa_data.exist:
            raise Exception("ERROR in eddy, PA sequence is not available, cannot do eddy")

        # ----------------------------------------------------------------
        # parameters
        # ----------------------------------------------------------------
        if estmove:
            str_estmove = "--estimate_move_by_susceptibility"
        else:
            str_estmove = ""

        if json == "":
            str_json = ""
        else:
            str_json = "--json=" + json

        if rep_out == "":
            str_rep_out = ""
        else:
            str_rep_out = "--repol --ol_type=" + rep_out

        if slice2vol == 0:
            str_slice2vol = ""
        else:
            str_slice2vol = "--mporder=" + str(slice2vol) + " "

        # -----------------------------------------------------------------
        # check whether requested eddy version exist (to use cuda versions of other FSL releases, I can pass also a full file path)
        if not os.path.isfile(exe_ver):
            exe_ver = os.path.join(self.subject._global.fsl_dir, "bin", exe_ver)

        if not os.path.exists(exe_ver):
            print("ERROR in eddy of subject: " + self.subject.label + ", eddy exe version (" + exe_ver + ") does not exist, exiting.....")
            return

        # NO NEED ANYMORE....using b02b0_1.cnf : check whether images number are all even, correct it
        # nslices = int(rrun("fslval " + self.subject.dti_data + " dim3"))      # if (nslices % 2) != 0:       #     remove_slices(self.subject.dti_data, 1)     # removes first axial slice
        # nslices = int(rrun("fslval " + self.subject.dti_pa_data + " dim3"))   # if (nslices % 2) != 0:        #     remove_slices(self.subject.dti_pa_data, 1)     # removes first axial slice

        a2p_bo              = Image(os.path.join(self.subject.dti_dir, "a2p_b0"))
        p2a_bo              = Image(os.path.join(self.subject.dti_dir, "p2a_b0"))
        a2p_p2a_bo          = Image(os.path.join(self.subject.dti_dir, "a2p_p2a_b0"))
        hifi_b0             = Image(os.path.join(self.subject.dti_dir, "hifi_b0"))
        eddy_corrected_data = Image(os.path.join(self.subject.dti_dir, self.subject.dti_ec_image_label))

        index_file          = os.path.join(self.subject.dti_dir, "index_file.txt")
        topup_results       = os.path.join(self.subject.dti_dir, "topup_results")

        # create an image with the 2 b0s with opposite directions
        rrun(f"fslroi {self.subject.dti_data} {a2p_bo} 0 1", logFile=logFile)
        rrun(f"fslroi {self.subject.dti_pa_data} {p2a_bo} 0 1", logFile=logFile)
        rrun(f"fslmerge -t {a2p_p2a_bo} {a2p_bo} {p2a_bo}", stop_on_error=False)

        if not Image(os.path.join(self.subject.dti_dir, "topup_results_fieldcoef.nii.gz")).exist:
            rrun(f"topup --imain={a2p_p2a_bo} --datain={acq_params} --config={config} --out={topup_results} --iout={hifi_b0}", logFile=logFile)

        rrun(f"fslmaths {hifi_b0} -Tmean {hifi_b0}", logFile=logFile)
        rrun(f"bet {hifi_b0} {hifi_b0}_brain -m", logFile=logFile)

        nvols_dti = self.subject.dti_data.nvols
        indx=""
        for i in range(0, nvols_dti):
            indx=indx + "1 "
        write_text_file(index_file, indx)

        # TEMPORARY OVERRIDE ------ TODO: fix it one day !!
        # if "cuda" in exe_ver:
        #     exe_ver = "/usr/local/fsl-6.0.5/bin/eddy_cuda10.2"

        rrun(f"{exe_ver} --imain={self.subject.dti_data} --mask={hifi_b0}_brain_mask --acqp={acq_params} --index={index_file} --bvecs={self.subject.dti_bvec} --bvals={self.subject.dti_bval} --topup={topup_results} --out={eddy_corrected_data} {str_estmove} {str_slice2vol} {str_json} {str_rep_out}", logFile=logFile)

        os.rename(self.subject.dti_eddyrotated_bvec, self.subject.dti_rotated_bvec)

        os.system(f"rm {self.subject.dti_dir}/a2p_*")
        os.system(f"rm {self.subject.dti_dir}/p2a_*")
        os.system(f"rm {self.subject.dti_dir}/hifi_*")

    # use_ec = True: eddycorrect, False: eddy
    def fit(self, logFile=None):
        """
        This function performs DTI fitting.

        Args:
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            None.

        Raises:
            IOError: If the diffusion tensor image is missing.
            IOError: If the rotated b-vector file is missing.

        """
        if not self.subject.dti_data.exist:
            print("WARNING in dti fit of subject: " + self.subject.label + ",dti image is missing...skipping subject")
            return

        if not os.path.exists(self.subject.dti_rotated_bvec):
            print("ERROR in dti fit of subject: " + self.subject.label + ",rotated bvec file is not available..did you run either eddy_correct or eddy?...skipping subject")
            return

        rrun(f"fslroi {os.path.join(self.subject.dti_data)} {self.subject.dti_nodiff_data} 0 1", logFile=logFile)
        rrun(f"bet {self.subject.dti_nodiff_data} {self.subject.dti_nodiff_brain_data} -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        if not self.subject.dti_fit_data.exist:
            print("starting DTI fit on " + self.subject.label)
            rrun(f"dtifit --sse -k {self.subject.dti_ec_data} -o {self.subject.dti_fit_data} -m {self.subject.dti_nodiff_brainmask_data} -r {self.subject.dti_rotated_bvec} -b {self.subject.dti_bval}", logFile=logFile)

        if not Image(self.subject.dti_ec_data + "_L23").exist:
            rrun(f"fslmaths {self.subject.dti_fit_data}_L2 -add {self.subject.dti_fit_data}_L3 -div 2 {self.subject.dti_fit_data}_L23", logFile=logFile)

    def bedpostx(self, bedpostx_dirname:str|None="bedpostx", use_gpu:bool=False, logFile=None):
        """
        This function performs bedpostx.

        Args:
            out_dir_name (str, optional): The output directory name. Defaults to "bedpostx".
            use_gpu (bool, optional): Whether to use GPU. Defaults to False.
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            None.

        Raises:
            IOError: If the eddy-corrected diffusion tensor image is missing.

        """

        if bedpostx_dirname is None:
            bp_dir      = self.subject.dti_bedpostX_dir
            bp_out_dir  = bp_dir + ".bedpostX"
        else:
            bp_dir      = os.path.join(self.subject.dti_dir, bedpostx_dirname)
            bp_out_dir  = os.path.join(self.subject.dti_dir, bedpostx_dirname + ".bedpostX")

        os.makedirs(bp_dir, exist_ok=True)

        if not self.subject.dti_ec_data.exist:
            print("WARNING in bedpostx: ec data of subject " + self.subject.label + " is missing.....skipping subject")
            return

        print("STARTING bedpostx on subject " + self.subject.label)

        self.subject.dti_ec_data.cp(os.path.join(bp_dir, "data"), logFile=logFile)
        self.subject.dti_nodiff_brainmask_data.cp(os.path.join(bp_dir, "nodif_brain_mask"), logFile=logFile)
        copyfile(self.subject.dti_bval, os.path.join(bp_dir, "bvals"))
        copyfile(self.subject.dti_rotated_bvec, os.path.join(bp_dir, "bvecs"))

        res = rrun(f"bedpostx_datacheck {bp_dir}", logFile=logFile)

        # if res > 0:
        #     print("ERROR in bedpostx (" +  bp_dir + " ....exiting")
        #     return

        if use_gpu:
            rrun(os.path.join(self._global.fsl_dir, "bin", "bedpostx_gpu") + " " + bp_dir + " -n 3 -w 1 -b 1000", logFile=logFile)
        else:
            rrun(f"bedpostx {bp_dir} -n 3 -w 1 -b 1000", logFile=logFile)

        if Image(os.path.join(bp_out_dir, self.subject.dti_bedpostx_mean_S0_label)).exist:
            os.rename(bp_dir, os.path.join(self.subject.dti_dir, "bedpostx_"))
            os.rename(bp_out_dir, bp_dir)
        else:
            print("ERROR in bedpostx_gpu....something went wrong in bedpostx")
            return

    def probtrackx(self, out_dir_name:str, out_tractofile_name:str,
                   seed:str|List[str]|List[int], # list of images or point coordinates
                   avoid:str|None=None,
                   wayp:List[str]|None=None,
                   stop:str|None = None,
                   bedpost_dirname:str|None=None, pd:bool=False, use_gpu:bool=False, nsamples:int=5000,
                   default_pbt_params:str = " -V 1 --loopcheck --forcedir --opd --ompl",
                   other_pbt_params:str = " --sampvox=1 --randfib=1 --onewaycondition"):

        if use_gpu is True:
            cmd_str = "probtrackx2_gpu "
        else:
            cmd_str = "probtrackx2 "

        if bedpost_dirname is None:
            bp_dir = self.subject.dti_bedpostX_dir
        else:
            bp_dir = os.path.join(self.subject.dti_dir, bedpost_dirname)

        out_dir = os.path.join(self.subject.dti_probtrackx_dir, out_dir_name)

        os.makedirs(out_dir, exist_ok=True)

        # EXTRA PARAMS ---------------------------------------------------------------------------
        param_str = " --nsamples=" + str(nsamples) + other_pbt_params

        if pd is True:
            params_str = param_str + " --pd "

        # SEED ---------------------------------------------------------------------------
        seed_file = os.path.join(out_dir, "seed_file_" + out_tractofile_name + ".txt")
        if isinstance(seed , str):
            seed_str = "-x " + seed
        elif isinstance(seed, list):
            if isinstance(seed[0], str):
                with open(seed_file, "w") as f:
                    str_seed = ""
                    for s in seed:
                        str_seed = f"{str_seed}{s}\n"
                    f.write(str_seed)
                seed_str = "-x " + seed_file
            elif isinstance(seed[0], int):
                with open(seed_file, "w") as f:
                    str_seed = f"{seed[0]},{seed[1]},{seed[2]}"
                    f.write(str_seed)
                seed_str = f"-x {seed_file} --simple"
            else:
                print("Seed parameters is a list but not of the expected types....exiting")
                return
        else:
            print("Seed parameters type is not recognized....exiting")
            return

        # WAYPOINTS ---------------------------------------------------------------------------
        if len(wayp) > 0:
            wp_file = os.path.join(out_dir, "wp_file_" + out_tractofile_name + ".txt")
            with open(wp_file, "w") as f:
                str_wp = ""
                for wp in wayp:
                    str_wp = str_wp + wp + "\n"
                f.write(str_wp)
            wp_str = "--waypoints=" + wp_file
        else:
            wp_str = ""

        # STOP & AVOID ---------------------------------------------------------------------------
        if stop is not None:
            stop_mask = Image(stop, must_exist=True, msg="Stop mask is not valid")
            stop_str = "--stop=" + stop_mask
        else:
            stop_str = ""

        if avoid is not None:
            avoid_mask = Image(avoid, must_exist=True, msg="Avoid mask is not valid")
            avoid_str = "--avoid=" + avoid_mask
        else:
            avoid_str = ""

        # START ---------------------------------------------------------------------------
        print(f"STARTING probtrackx {out_dir_name} | {out_tractofile_name} on subject {self.subject.label}")
        rrun(f"{cmd_str} -o {out_tractofile_name} --dir={out_dir} -s {os.path.join(bp_dir, 'merged')} -m {os.path.join(self.subject.roi_dti_dir, 'nodif_brain_mask')} {param_str} {wp_str} {seed_str} {stop_str} {avoid_str} {param_str} {default_pbt_params}")

        waytotal = read_value_from_file(os.path.join(out_dir, "waytotal"))

        rrun(f"fslmaths {os.path.join(out_dir, out_tractofile_name)} -div {waytotal} {os.path.join(out_dir, out_tractofile_name + 'Norm')}")

        os.rename(os.path.join(out_dir, "waytotal"), os.path.join(out_dir, "waytotal_" + out_tractofile_name))

        print(f"FINISHED probtrackx {out_dir_name} on subject {self.subject.label}")

    def get_tbss_metric_from_masks(self, masks:List[str], meas:List[str]|None=None, must_exist:bool=True) -> SubjectTracts:

        masks = Images(masks, must_exist=must_exist, msg="get_tbss_metric_from_masks: one or more Input masks images are not valid")

        if meas is None:
            meas = ["FA","MD","L1","L23"]

        tracts:SubjectTracts = SubjectTracts(self.subject.label)
        for mask in masks:
            tract = Tract(mask)
            for m in meas:
                meas_image = Image(os.path.join(self.subject.dti_dir, self.subject.dti_fit_label + "_" + m))
                val = float(rrun("fslstats " + meas_image + " -m -k " + mask).strip())
                tract.set_metric(m, val)

            tracts.append(tract)

        return tracts

    def xtract(self, xtractdir_name:str|None=None, bedpostx_dirname:str|None=None, refspace="native", use_gpu:bool=False, species="HUMAN", logFile=None):
        """
        This function performs xtract.

        Args:
            outdir_name (str, optional): The output directory name. Defaults to "xtract".
            bedpostx_dirname (str, optional): The bedpostx directory name. Defaults to "bedpostx".
            refspace (str, optional): The reference space. Defaults to "native".
            use_gpu (bool, optional): Whether to use GPU. Defaults to False.
            species (str, optional): The species. Defaults to "HUMAN".
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            str: The output directory path.

        """

        if xtractdir_name is None:
            xtractdir_name = "xtract"
            out_dir = self.subject.dti_xtract_dir
        else:
            out_dir = os.path.join(self.subject.dti_dir, xtractdir_name)

        if bedpostx_dirname is None:
            bp_dir = self.subject.dti_bedpostX_dir
        else:
            bp_dir = os.path.join(self.subject.dti_dir, bedpostx_dirname)

        if refspace == "native":
            refspace_str = "-native -stdwarp " + self.subject.transform.std2dti_warp + " " + self.subject.transform.dti2std_warp + " "
        else:
            # TODO: split refspace by space, check if the two elements are valid files
            refspace_str = "-ref " + refspace + " "

        gpu_str = ""
        if use_gpu:
            gpu_str = "-gpu "

        print("STARTING xtract on subject " + self.subject.label)
        rrun(f"xtract -bpx {bp_dir} -out {out_dir} {gpu_str} {refspace_str} -species {species}", stop_on_error=False, logFile=logFile)

        self.xtract_check(xtractdir_name)
        return out_dir

    def xtract_check(self, xtractdir_name:str|None=None):
        """
        This function checks the xtract output.

        Args:
            in_dir (str, optional): The input directory path. Defaults to "xtract".

        Returns:
            None.

        """
        if xtractdir_name is None:
            xtractdir_name = "xtract"
            in_dir = self.subject.dti_xtract_dir
        else:
            in_dir = os.path.join(self.subject.dti_dir, xtractdir_name)

        all_ok = True
        tracts = self._global.dti_xtract_labels
        for tract in tracts:
            if not Image(os.path.join(in_dir, "tracts", tract, "densityNorm")).exist:
                print("WARNING: in xtract. SUBJ " + self.subject.label + ", tract " + tract + " is missing")
                all_ok = False
        if all_ok:
            print("  ============>  check_xtracts of SUBJ " + self.subject.label + ", is ok!")

    def xtract_viewer(self, xtractdir_name:str|None=None, structures:str="", species="HUMAN"):
        """
        This function launches the xtract viewer.

        Args:
            xtract_dir (str, optional): The xtract directory path. Defaults to "xtract".
            structures (str, optional): The structures. Defaults to "".
            species (str, optional): The species. Defaults to "HUMAN".

        Returns:
            None.

        """
        if xtractdir_name is None:
            xtractdir_name = "xtract"
            xdir = self.subject.dti_xtract_dir
        else:
            xdir = os.path.join(self.subject.dti_dir, xtractdir_name)

        if structures != "":
            structures = " -str " + structures + " "

        rrun(f"xtract_viewer -dir {xdir} -species {species} {structures}")

    def xtract_stats(self, xtractdir_name:str|None=None, refspace="native", meas="vol,prob,length,FA,MD,L1,L23", structures:str="", logFile=None):
        """
        This function performs xtract_stats.

        Args:
            xtract_dir (str, optional): The xtract directory path. Defaults to "xtract".
            refspace (str, optional): The reference space. Defaults to "native".
            meas (str, optional): The measurements. Defaults to "vol,prob,length,FA,MD,L1".
            structures (str, optional): The structures. Defaults to "".
            logFile (str, optional): The log file path. Defaults to None.

        Returns:
            None.

        Raises:
            IOError: If refspace is empty.
            IOError: If refspace is not a valid transform image.

        """
        if xtractdir_name is None:
            in_dir = self.subject.dti_xtract_dir
        else:
            in_dir = os.path.join(self.subject.dti_dir, xtractdir_name)

        if refspace == "native":
            rspace = "-w native "
        elif refspace == "":
            raise IOError("SubjectDti.xtract_stats given refspace param is empty")

        else:
            refspace = Image(refspace, must_exist=True, msg="SubjectDti.xtract_stats given refspace param is not a transform image")
            rspace = "-w " + refspace + " "

        root_dir = f" -d {os.path.join(self.subject.dti_dir, self.subject.dti_fit_label + '_')} "

        if structures != "":
            structures = f"-str {structures} "

        rrun(f"xtract_stats -xtract {in_dir} {rspace} {root_dir} -meas {meas} {structures}", logFile=logFile)

    # read its own xtract_stats output file and return a dictionary = { "tractX":{"val1":XX,"val2":YY, ...}, .. }
    def xtract_read_file(self, tracts=None, values=None, ifn="stats.csv"):
        """
        This function reads the xtract_stats output file and returns a dictionary of tract values.

        Args:
            tracts (list, optional): The tracts to extract. If None, all tracts are extracted. Defaults to None.
            values (list, optional): The values to extract. If None, only mean FA and MD are extracted. Defaults to None.
            ifn (str, optional): The input file name. Defaults to "stats.csv".

        Returns:
            dict: A dictionary of tract values.

        """
        if len(tracts) is None:
            tracts = self._global.dti_xtract_labels

        if values is None:
            values = ["mean_FA", "mean_MD"]

        inputfile = os.path.join(self.subject.dti_xtract_dir, ifn)
        datas = {}

        with open(inputfile, "r") as f:
            reader = csv.reader(f, dialect='excel', delimiter=',')
            for row in reader:
                if reader.line_num == 1:
                    header = row
                else:
                    data_row = {}
                    cnt = 0
                    for elem in row:
                        if cnt == 0:

                            if elem in tracts:
                                tract_lab = elem
                            else:
                                break
                        else:
                            hdr = header[cnt].strip()
                            for v in values:
                                if v in hdr:
                                    data_row[v] = elem

                        cnt = cnt + 1

                    if bool(data_row):
                        datas[tract_lab] = data_row

        _str = self.subject.label + "\t"
        for tract in datas:
            for v in values:
                _str += datas[tract][v] + "\t"

        return _str, datas

    def xtract_blueprint(self, outdir_name:str|None=None, bedpostx_dirname:str|None=None, res:int = 3, use_gpu:bool=False):

        if outdir_name is None:
            out_dir = self.subject.dti_xtract_dir
        else:
            out_dir = os.path.join(self.subject.dti_dir, outdir_name)

        if bedpostx_dirname is None:
            bp_dir = self.subject.dti_bedpostX_dir
        else:
            bp_dir = os.path.join(self.subject.dti_dir, bedpostx_dirname)

        gpu_str = ""
        if use_gpu:
            gpu_str = " -gpu "

        lwhitegii = "lwhite"
        rwhitegii = "rwhite"

        rrun(f"xtract_blueprint -bpx {self.subject.dti_bedpostX_dir} -out {self.subject.dti_blueprint_dir} -xtract {self.subject.dti_xtract_dir} -seeds {lwhitegii} ,{rwhitegii} -warps {self.subject.std_img} {self.subject.transform.std2dti_warp} {self.subject.transform.dti2std_warp} -nsamples 50 -res {res} {gpu_str}")

    def conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass

    # region DSI-STUDIO
    def convert2dsi(self, type: str = "original", error_if_absent:bool=False) -> None:
        """
        This function converts the DTI data to DSI Studio format.
        Args:
            type (str, optional): The type of data to convert. Can be "original" or "ec" (eddy corrected). Defaults to "original".
            error_if_absent (bool, optional): Whether to raise an error if the input image does not exist. Defaults to False.
        Returns:
            None.
        Raises:
            IOError: If the input image does not exist and error_if_absent is True.
        """
        if type == "original":
            inputimg    = self.subject.dti_data
            bvec        = self.subject.dti_bvec
        else:
            inputimg    = self.subject.dti_ec_data
            bvec        = self.subject.dti_rotated_bvec

        bval = self.subject.dti_bval

        if not inputimg.exist:
            if error_if_absent:
                raise IOError("SubjectDti.convert2dsi given input image does not exist")
            else:
                print("SubjectDti.convert2dsi given input image (" + inputimg + ") does not exist...skipping conversion")
                return

        rrun(f"dsi_studio --action=src --source={inputimg}.nii.gz --bval={bval} --bvec={bvec} --output={os.path.join(self.subject.dti_dsi_dir, self.subject.dti_image_label)}")

    def dsi_recon(self, in_img:Image=None, method:str="GQI", param0:float=1.25, connectometry:int=1, output:str=None, thread_count:int=1):
        """
        This function performs DSI Studio reconstruction.
        Args:
            in_img (Image, optional): The input image. If None, the DSI Studio data is used. Defaults to None.
            method (str, optional): The reconstruction method. Can be "GQI" or "QSDR". Defaults to "GQI".
            param0 (float, optional): The parameter 0 value. Only used for GQI. Defaults to 1.25.
            connectometry (int, optional): The connectometry value. Only used for QSDR. Defaults to 1.
            output (str, optional): The output file path. If None, no output file is created. Defaults to None.
            thread_count (int, optional): The thread count. Only used for GPU acceleration. Defaults to 1.
        Returns:
            None.
        Raises:
            IOError: If the input image does not exist.
        """
        rec_method = "1"
        if method == "GQI":
            rec_method = "4"
        elif method == "QSDR":
            rec_method = "7"
        else:
            raise Exception("SubjectDti.dsi_recon given method param is not valid")

        if in_img is None:
            in_img = self.subject.dti_dsi_data

        if  output is None:
            output_str = ""
        else:
            output_str = "--output=" + output

        if not in_img.exist:
            raise IOError("SubjectDti.dsi_recon given input image does not exist: " + in_img)

        rrun(f"dsi_studio --action=rec --source={in_img} --method={rec_method} --param0={param0} --record_odf={connectometry} {output_str} --thread_count={thread_count}")

    def dsi_connectivity(self, fib_file=None, fib_type:str=".src.gz.odf.gqi.1.25", threshold:int=0.001, fib_cnt:int=1000000, conn_atlas:str="Brainnectome", conn_values:str="count,qa,trk"):
        """
        This function performs DSI Studio connectivity analysis.
        Args:
            fib_file (str, optional): The input fiber file. If None, the DSI Studio data is used. Defaults to None.
            threshold (int, optional): The connectivity threshold. Defaults to 0.001.
            fib_cnt (int, optional): The maximum number of fibers. Defaults to 1000000.
            conn_atlas (str, optional): The connectivity atlas. Defaults to "HCP-MMP".
            conn_values (str, optional): The connectivity values. Defaults to "count,qa,trk".
        Returns:
            None.
        Raises:
            IOError: If the input fiber file does not exist.
        """
        if fib_file is None:
            fib_file = Image(os.path.join(self.subject.dti_dsi_dir, self.subject.dti_image_label + fib_type + ".fib.gz"))


        if not os.path.exists(fib_file):
            raise IOError("SubjectDti.dsi_connectivity given input fiber file does not exist: " + fib_file)

        rrun(f"dsi_studio --action=trk --source={fib_file} --fiber_count={fib_cnt} --connectivity_threshold={threshold} --output=no_file --connectivity={conn_atlas} --connectivity_value={conn_values}")


    # endregion