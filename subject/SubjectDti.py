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

    def ec_fit(self):

        if imtest(self.subject.dti_data) is False:
            return

        rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1")
        rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3")  # also creates dti_nodiff_brain_mask_data

        if imtest(self.subject.dti_ec_data) is False:
            print("starting eddy_correct on " + self.subject.label)
            rrun("eddy_correct " + self.subject.dti_data + " " + self.subject.dti_ec_data + " 0")

        if os.path.exists(self.subject.dti_rotated_bvec) is False:
            rrun("fdt_rotate_bvecs " + self.subject.dti_bvec + " " + self.subject.dti_rotated_bvec + " " + self.subject.dti_ec_data + ".ecclog")

        if imtest(self.subject.dti_fit_data) is False:
            print("starting DTI fit on " + self.subject.label)
            rrun("dtifit --sse -k " + self.subject.dti_ec_data + " -o " + self.subject.dti_fit_data + " -m " + self.subject.dti_nodiff_brainmask_data + " -r " + self.subject.dti_rotated_bvec + " -b " + self.subject.dti_bval)

        if imtest(self.subject.dti_ec_data + "_L23") is False:
            rrun("fslmaths " + self.subject.dti_fit_data + "_L2" + " -add " + self.subject.dti_fit_data + "_L3" + " -div 2 " + self.subject.dti_fit_data + "_L23")

    def probtrackx(self):
        pass

    def bedpostx(self, out_dir_name="bedpostx", use_gpu=False):

        bp_dir      = os.path.join(self.subject.dti_dir, out_dir_name)
        bp_out_dir  = os.path.join(self.subject.dti_dir, out_dir_name + ".bedpostX")

        os.makedirs(bp_dir, exist_ok=True)

        imcp(self.subject.dti_ec_data, os.path.join(bp_dir, "data"))
        imcp(self.subject.dti_nodiff_brainmask_data, os.path.join(bp_dir, "nodif_brain_mask"))
        copyfile(self.subject.dti_bval, os.path.join(bp_dir, "bvals"))
        copyfile(self.subject.dti_rotated_bvec, os.path.join(bp_dir, "bvecs"))

        res = rrun("bedpostx_datacheck " + bp_dir)

        # if res > 0:
        #     print("ERROR in bedpostx (" +  bp_dir + " ....exiting")
        #     return

        if use_gpu is True:
            rrun("bedpostx_gpu " + bp_dir + " -n 3 -w 1 -b 1000")
        else:
            rrun("bedpostx " + bp_dir + " -n 3 -w 1 -b 1000")

        # if imtest(os.path.join(bp_out_dir, self.subject.dti_bedpostx_mean_S0_label)):
        #     shutil.move(bp_out_dir, os.path.join(self.subject.dti_dir, out_dir_name))
        #     os.removedirs(bp_dir)

        # else:
        #     print("ERROR in bedpostx_gpu....something went wrong in bedpostx")
        #     return

    def xtract(self, outdir_name="xtract", bedpostx_dirname="bedpostx", refspace="native", use_gpu=False, species="HUMAN"):

        bp_dir      = os.path.join(self.subject.dti_dir, bedpostx_dirname)
        out_dir     = os.path.join(self.subject.dti_dir, outdir_name)

        refspace_str = " -native "
        if refspace != "native":
            # TODO: split refspace by space, check if the two elements are valid files
            refspace_str = " -ref " + refspace + " "

        gpu_str = ""
        if use_gpu is True:
            gpu_str = " -gpu "

        rrun("xtract -bpx " + bp_dir + " -out " + out_dir + " -stdwarp " + self.subject.std2dti_warp + " " + self.subject.dti2std_warp + gpu_str + refspace_str + " -species " + species)

    def xtract_viewer(self, xtract_dir, structures="", species="HUMAN"):

        if structures != "":
            structures = " -str " + structures + " "

        rrun("xtract_viewer -dir " + xtract_dir + " -species " + species + "" + structures)

    def xtract_stats(self, xtract_dir, meas="vol,prob,length,FA,MD", structures=""):

        if structures != "":
            structures = " -str " + structures + " "

        rrun("xtract_stats " + " -xtract " + xtract_dir + " -meas " + meas + "" + structures)

    def conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass



    