import os

from myfsl.utils.run import rrun
from utility.images import imtest


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


    def bedpostx_gpu(self):
        pass


    def conn_matrix(self, atlas_path="freesurfer", nroi=0):
        pass


    def autoptx_tractography(self):
        pass

    