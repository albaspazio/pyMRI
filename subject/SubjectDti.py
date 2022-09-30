import csv
import os
import shutil
from shutil import copyfile

from utility.images.Image import Image
from utility.myfsl.utils.run import rrun
from utility.utilities import write_text_file


class SubjectDti:

    def __init__(self, subject, _global):
        self.subject = subject
        self._global = _global

    # ==================================================================================================================================================
    # DIFFUSION
    # ==================================================================================================================================================
    def get_nodiff(self, logFile=None):

        if not self.subject.dti_nodiff_data.exist:
            rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)

        if not self.subject.dti_nodiff_brain_data.exist:
            rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

    # eddy correction when PA sequence is not available
    def eddy_correct(self, overwrite=False, logFile=None):

        if self.subject.dti_data.exist:
            print("WARNING in dti eddy_correct of subject: " + self.subject.label + ",dti image is missing...skipping subject")
            return

        rrun("fslroi " + self.subject.dti_data + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)
        rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        if not self.subject.dti_ec_data.exist or overwrite:
            print("starting eddy_correct on " + self.subject.label)
            rrun("eddy_correct " + self.subject.dti_data + " " + self.subject.dti_ec_data + " 0", logFile=logFile)

            os.system("bash fdt_rotate_bvecs " + self.subject.dti_bvec + " " + self.subject.dti_rotated_bvec + " " + self.subject.dti_ec_data + ".ecclog")

    # perform eddy correction, finally writes  .._ec.nii.gz &  .._-dti_rotated.bvec
    def eddy(self, exe_ver="eddy_openmp", acq_params=None, config="b02b0_1.cnf", estmove=True, slice2vol=6, rep_out="both", json=None, logFile=None):

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
            raise Exception("ERROR in eddy of subject: " + self.subject.label + ", acq_params file does not exist, exiting.....")

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
            str_estmove = " --estimate_move_by_susceptibility"
        else:
            str_estmove = ""

        if json == "":
            str_json = ""
        else:
            str_json = " --json=" + json

        if rep_out == "":
            str_rep_out = ""
        else:
            str_rep_out = " --repol --ol_type=" + rep_out

        if slice2vol == 0:
            str_slice2vol = ""
        else:
            str_slice2vol = " --mporder=" + str(slice2vol) + " "

        # -----------------------------------------------------------------
        # check whether requested eddy version exist
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
        rrun("fslroi " + self.subject.dti_data + " " + a2p_bo + " 0 1", logFile=logFile)
        rrun("fslroi " + self.subject.dti_pa_data + " " + p2a_bo + " 0 1", logFile=logFile)
        rrun("fslmerge -t " + a2p_p2a_bo + " " + a2p_bo + " " + p2a_bo, stop_on_error=False)

        rrun("topup --imain=" + a2p_p2a_bo + " --datain=" + acq_params + " --config=" + config + " --out=" +  topup_results  + " --iout=" +  hifi_b0, logFile=logFile)

        rrun("fslmaths " + hifi_b0 + " -Tmean " + hifi_b0, logFile=logFile)
        rrun("bet " + hifi_b0 + " " + hifi_b0 + "_brain -m", logFile=logFile)

        nvols_dti = self.subject.dti_data.getnvol()
        indx=""
        for i in range(0, nvols_dti):
            indx=indx + "1 "
        write_text_file(index_file, indx)

        rrun(exe_ver + " --imain=" +  self.subject.dti_data + " --mask=" + hifi_b0 + "_brain_mask --acqp=" + acq_params + " --index=" + index_file + " --bvecs=" + self.subject.dti_bvec + " --bvals=" + self.subject.dti_bval +
                       " --topup=" + topup_results + " --out=" + eddy_corrected_data + str_estmove + str_slice2vol + str_json + str_rep_out, logFile=logFile)

        os.rename(self.subject.dti_eddyrotated_bvec, self.subject.dti_rotated_bvec)

        os.system("rm " + self.subject.dti_dir + "/" + "ap_*")
        os.system("rm " + self.subject.dti_dir + "/" + "pa_*")
        os.system("rm " + self.subject.dti_dir + "/" + "hifi_*")

    # use_ec = True: eddycorrect, False: eddy
    def fit(self, logFile=None):

        if not self.subject.dti_data.exist:
            print("WARNING in dti fit of subject: " + self.subject.label + ",dti image is missing...skipping subject")
            return

        if not os.path.exists(self.subject.dti_rotated_bvec):
            print("ERROR in dti fit of subject: " + self.subject.label + ",rotated bvec file is not available..did you run either eddy_correct or eddy?...skipping subject")
            return

        rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)
        rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        if not self.subject.dti_fit_data.exist:
            print("starting DTI fit on " + self.subject.label)
            rrun("dtifit --sse -k " + self.subject.dti_ec_data + " -o " + self.subject.dti_fit_data + " -m " + self.subject.dti_nodiff_brainmask_data + " -r " + self.subject.dti_rotated_bvec + " -b " + self.subject.dti_bval, logFile=logFile)

        if not Image(self.subject.dti_ec_data + "_L23").exist:
            rrun("fslmaths " + self.subject.dti_fit_data + "_L2" + " -add " + self.subject.dti_fit_data + "_L3" + " -div 2 " + self.subject.dti_fit_data + "_L23", logFile=logFile)

    def bedpostx(self, out_dir_name="bedpostx", use_gpu=False, logFile=None):

        bp_dir      = os.path.join(self.subject.dti_dir, out_dir_name)
        bp_out_dir  = os.path.join(self.subject.dti_dir, out_dir_name + ".bedpostX")

        os.makedirs(bp_dir, exist_ok=True)

        if not self.subject.dti_ec_data.exist:
            print("WARNING in bedpostx: ec data of subject " + self.subject.label + " is missing.....skipping subject")
            return

        print("STARTING bedpostx on subject " + self.subject.label)

        self.subject.dti_ec_data.cp(os.path.join(bp_dir, "data"), logFile=logFile)
        self.subject.dti_nodiff_brainmask_data.cp(os.path.join(bp_dir, "nodif_brain_mask"), logFile=logFile)
        copyfile(self.subject.dti_bval, os.path.join(bp_dir, "bvals"))
        copyfile(self.subject.dti_rotated_bvec, os.path.join(bp_dir, "bvecs"))

        res = rrun("bedpostx_datacheck " + bp_dir, logFile=logFile)

        # if res > 0:
        #     print("ERROR in bedpostx (" +  bp_dir + " ....exiting")
        #     return

        if use_gpu:
            rrun("bedpostx_gpu " + bp_dir + " -n 3 -w 1 -b 1000", logFile=logFile)
        else:
            rrun("bedpostx " + bp_dir + " -n 3 -w 1 -b 1000", logFile=logFile)

        if not Image(os.path.join(bp_out_dir, self.subject.dti_bedpostx_mean_S0_label)).exist:
            shutil.move(bp_out_dir, os.path.join(self.subject.dti_dir, out_dir_name))
            os.removedirs(bp_dir)

        else:
            print("ERROR in bedpostx_gpu....something went wrong in bedpostx")
            return

    def probtrackx(self):
        pass

    def xtract(self, outdir_name="xtract", bedpostx_dirname="bedpostx", refspace="native", use_gpu=False, species="HUMAN", logFile=None):

        bp_dir  = os.path.join(self.subject.dti_dir, bedpostx_dirname)
        out_dir = os.path.join(self.subject.dti_dir, outdir_name)

        if refspace == "native":
            refspace_str = " -native -stdwarp " + self.subject.transform.std2dti_warp + " " + self.subject.transform.dti2std_warp + " "
        else:
            # TODO: split refspace by space, check if the two elements are valid files
            refspace_str = " -ref " + refspace + " "

        gpu_str = ""
        if use_gpu:
            gpu_str = " -gpu "

        print("STARTING xtract on subject " + self.subject.label)
        rrun("xtract -bpx " + bp_dir + " -out " + out_dir + gpu_str + refspace_str + " -species " + species, stop_on_error=False, logFile=logFile)

        self.xtract_check(out_dir)
        return out_dir

    def xtract_check(self, in_dir="xtract"):

        if in_dir == "xtract":
            in_dir = os.path.join(self.subject.dti_dir, in_dir)
        else:
            if not os.path.isdir(in_dir):
                print("ERROR in xtract_check: given folder (" + in_dir + ") is missing....exiting")
                return

        all_ok = True
        tracts = self._global.dti_xtract_labels
        for tract in tracts:
            if not Image(os.path.join(in_dir, "tracts", tract, "densityNorm")).exist:
                print("WARNING: in xtract. SUBJ " + self.subject.label + ", tract " + tract + " is missing")
                all_ok = False
        if all_ok:
            print("  ============>  check_xtracts of SUBJ " + self.subject.label + ", is ok!")

    def xtract_viewer(self, xtract_dir="xtract", structures="", species="HUMAN"):

        xdir = os.path.join(self.subject.dti_dir, xtract_dir)

        if structures != "":
            structures = " -str " + structures + " "

        rrun("xtract_viewer -dir " + xdir + " -species " + species + "" + structures)

    def xtract_stats(self, xtract_dir="xtract", refspace="native", meas="vol,prob,length,FA,MD,L1", structures="", logFile=None):

        xdir = os.path.join(self.subject.dti_dir, xtract_dir)

        if refspace == "native":
            rspace = " -w native "
        elif refspace == "":
            print("ERROR in xtract_stats: refspace param is empty.....exiting")
            return
        else:
            refspace = Image(refspace, must_exist=True, msg="SubjectDti.xtract_stats given refspace param is not a transform image")
            rspace = " -w " + refspace + " "

        root_dir = " -d " + os.path.join(self.subject.dti_dir, self.subject.dti_fit_label + "_") + " "

        if structures != "":
            structures = " -str " + structures + " "

        rrun("xtract_stats " + " -xtract " + xdir + rspace + root_dir + " -meas " + meas + "" + structures, logFile=logFile)

    # read its own xtract_stats output file and return a dictionary = { "tractX":{"val1":XX,"val2":YY, ...}, .. }
    def xtract_read_file(self, tracts=None, values=None, ifn="stats.csv"):

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

    def conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass
