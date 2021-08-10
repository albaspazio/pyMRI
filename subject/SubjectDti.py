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

    def bedpostx(self):
        pass

    def bedpostx_gpu(self, out_dir_name="bedpostx_gpu", stdimg=""):

        bp_dir      = os.path.join(self.subject.dti_dir, out_dir_name)
        bp_out_dir  = os.path.join(self.subject.dti_dir, out_dir_name + ".bedpostX")

        os.makedirs(bp_dir, exist_ok=True)

        imcp(self.subject.dti_ec_data, os.path.join(bp_dir, "data"))
        imcp(self.subject.dti_nodiff_brainmask_data, os.path.join(bp_dir, "nodif_brain_mask"))
        copyfile(self.subject.dti_bval, os.path.join(bp_dir, "bvals"))
        copyfile(self.subject.dti_rotated_bvec, os.path.join(bp_dir, "bvecs"))

        res = rrun("bedpostx_datacheck " + bp_dir)

        # if res > 0:
        #     print("ERROR in bedpostx_gpu (" +  bp_dir + " ....exiting")
        #     return

        rrun("bedpostx_gpu " + bp_dir + " -n 3 -w 1 -b 1000")

        if imtest(os.path.join(bp_out_dir, self.subject.dti_bedpostx_mean_S0_label)):
            shutil.move(bp_out_dir, os.path.join(self.subject.dti_dir, out_dir_name))
            os.removedirs(bp_dir)

        else:
            print("ERROR in bedpostx_gpu....something went wrong in bedpostx")
            return


    def xtract(self, outdir_name="xtract", bedpostx_dir="bedpostx", species="HUMAN", use_gpu=False):

        bp_dir      = os.path.join(self.subject.dti_dir, bedpostx_dir)
        out_dir     = os.path.join(self.subject.dti_dir, outdir_name)

        rrun("xtract -bpx " + bp_dir + " -out " + out_dir + " -stdwarp " + self.subject.std2dti_warp + " " + self.subject.dti2std_warp + " -species " + species )




    def conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass



    