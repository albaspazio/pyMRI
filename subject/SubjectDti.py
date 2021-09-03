import csv
import os
import shutil
from shutil import copyfile

from myfsl.utils.run import rrun
from utility.images import imtest, imcp


class SubjectDti:

    def __init__(self, subject, _global):
        self.subject = subject
        self._global = _global


    # ==================================================================================================================================================
    # DIFFUSION
    # ==================================================================================================================================================
    def get_nodiff(self, logFile=None):

        if imtest(self.subject.dti_nodiff_data) is False:
            rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)

        if imtest(self.subject.dti_nodiff_brain_data) is False:
            rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

    def ec_fit(self, logFile=None):

        if imtest(self.subject.dti_data) is False:
            return

        rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1", logFile=logFile)
        rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3", logFile=logFile)  # also creates dti_nodiff_brain_mask_data

        if imtest(self.subject.dti_ec_data) is False:
            print("starting eddy_correct on " + self.subject.label)
            rrun("eddy_correct " + self.subject.dti_data + " " + self.subject.dti_ec_data + " 0", logFile=logFile)

        if os.path.exists(self.subject.dti_rotated_bvec) is False:
            os.system("bash fdt_rotate_bvecs " + self.subject.dti_bvec + " " + self.subject.dti_rotated_bvec + " " + self.subject.dti_ec_data + ".ecclog")
            # rrun("fdt_rotate_bvecs " + self.subject.dti_bvec + " " + self.subject.dti_rotated_bvec + " " + self.subject.dti_ec_data + ".ecclog", logFile=logFile)

        if imtest(self.subject.dti_fit_data) is False:
            print("starting DTI fit on " + self.subject.label)
            rrun("dtifit --sse -k " + self.subject.dti_ec_data + " -o " + self.subject.dti_fit_data + " -m " + self.subject.dti_nodiff_brainmask_data + " -r " + self.subject.dti_rotated_bvec + " -b " + self.subject.dti_bval, logFile=logFile)

        if imtest(self.subject.dti_ec_data + "_L23") is False:
            rrun("fslmaths " + self.subject.dti_fit_data + "_L2" + " -add " + self.subject.dti_fit_data + "_L3" + " -div 2 " + self.subject.dti_fit_data + "_L23", logFile=logFile)

    def probtrackx(self):
        pass

    def bedpostx(self, out_dir_name="bedpostx", use_gpu=False, logFile=None):

        bp_dir      = os.path.join(self.subject.dti_dir, out_dir_name)
        bp_out_dir  = os.path.join(self.subject.dti_dir, out_dir_name + ".bedpostX")

        os.makedirs(bp_dir, exist_ok=True)

        imcp(self.subject.dti_ec_data, os.path.join(bp_dir, "data"), logFile=logFile)
        imcp(self.subject.dti_nodiff_brainmask_data, os.path.join(bp_dir, "nodif_brain_mask"), logFile=logFile)
        copyfile(self.subject.dti_bval, os.path.join(bp_dir, "bvals"))
        copyfile(self.subject.dti_rotated_bvec, os.path.join(bp_dir, "bvecs"))

        res = rrun("bedpostx_datacheck " + bp_dir, logFile=logFile)

        # if res > 0:
        #     print("ERROR in bedpostx (" +  bp_dir + " ....exiting")
        #     return

        if use_gpu is True:
            rrun("bedpostx_gpu " + bp_dir + " -n 3 -w 1 -b 1000", logFile=logFile)
        else:
            rrun("bedpostx " + bp_dir + " -n 3 -w 1 -b 1000", logFile=logFile)

        # if imtest(os.path.join(bp_out_dir, self.subject.dti_bedpostx_mean_S0_label)):
        #     shutil.move(bp_out_dir, os.path.join(self.subject.dti_dir, out_dir_name))
        #     os.removedirs(bp_dir)

        # else:
        #     print("ERROR in bedpostx_gpu....something went wrong in bedpostx")
        #     return

    def xtract(self, outdir_name="xtract", bedpostx_dirname="bedpostx", refspace="native", use_gpu=False, species="HUMAN", logFile=None):

        bp_dir      = os.path.join(self.subject.dti_dir, bedpostx_dirname)
        out_dir     = os.path.join(self.subject.dti_dir, outdir_name)

        refspace_str = " -native "
        if refspace != "native":
            # TODO: split refspace by space, check if the two elements are valid files
            refspace_str = " -ref " + refspace + " "

        gpu_str = ""
        if use_gpu is True:
            gpu_str = " -gpu "

        rrun("xtract -bpx " + bp_dir + " -out " + out_dir + " -stdwarp " + self.subject.std2dti_warp + " " + self.subject.dti2std_warp + gpu_str + refspace_str + " -species " + species, stop_on_error=False, logFile=logFile)

        self.xtract_check(out_dir)
        return out_dir


    def xtract_check(self, in_dir="xtract"):

        if in_dir == "xtract":
            in_dir = os.path.join(self.subject.dti_dir, in_dir)
        else:
            if os.path.isdir(in_dir) is False:
                print("ERROR in xtract_check: given folder (" + in_dir + ") is missing....exiting")
                return

        all_ok = True
        tracts = self._global.dti_xtract_labels
        for tract in tracts:
            if imtest(os.path.join(in_dir, "tracts", tract, "densityNorm")) is False:
                print("WARNING: in xtract. SUBJ " + self.subject.label + ", tract " + tract + " is missing")
                all_ok = False
        if all_ok is True:
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
            if imtest(refspace) is False:
                print("ERROR in xtract_stats: given refspace param is not a transform image.....exiting")
                return
            else:
                rspace = " -w " + refspace + " "

        root_dir = " -d " + os.path.join(self.subject.dti_dir, self.subject.dti_fit_label + "_") + " "

        if structures != "":
            structures = " -str " + structures + " "

        rrun("xtract_stats " + " -xtract " + xdir + rspace + root_dir + " -meas " + meas + "" + structures, logFile=logFile)

    # read its own xtract_stats output file and return a dictionary = { "tractX":{"val1":XX,"val2":YY, ...}, .. }
    def xtract_read_file(self, tracts=None, values=None, ifn="stats.csv", logFile=None):

        if len(tracts) is None:
            tracts  = self._global.dti_xtract_labels

        if values is None:
            values  = ["mean_FA", "mean_MD"]

        inputfile   = os.path.join(self.subject.dti_xtract_dir, ifn)
        datas       = {}

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

        str = self.subject.label + "\t"
        for tract in datas:
            for v in values:
                str = str + datas[tract][v] + "\t"

        return str, datas

    def conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass

