import os

from myfsl.utils.run import rrun
from utility.manage_images import imtest


class SubjectDti:

    def __init__(self, subject, _global):
        self.subject = subject
        self._global = _global
        

    # ==================================================================================================================================================
    # DIFFUSION
    # ==================================================================================================================================================

    def ec_fit(self):

        if os.path.exist(self.subject.dti_data) is False:
            return

        rrun("fslroi " + os.path.join(self.subject.dti_data) + " " + self.subject.dti_nodiff_data + " 0 1")
        rrun("bet " + self.subject.dti_nodiff_data + " " + self.subject.dti_nodiff_brain_data + " -m -f 0.3")  # also creates dti_nodiff_brain_mask_data

        if imtest(self.subject.dti_ec_image) is False:
            print("starting eddy_correct on " + self.subject.label)
            rrun("eddy_correct " + self.subject.dti_data + " " + self.subject.dti_ec_image + " 0")

        if os.path.exist(self.subject.dti_rotated_bvec) is False:
            rrun("fdt_rotate_bvecs " + self.subject.dti_bvec + " " + self.subject.dti_rotated_bvec + " " + self.subject.dti_data + ".ecclog")

        if imtest(self.subject.dti_fit_data) is False:
            print("starting DTI fit on " + self.subject.label)
            rrun(
                "dtifit --sse -k " + self.subject.dti_ec_data + " -o " + self.subject.dti_fit_data + " -m " + self.subject.dti_nodiff_brainmask_data + " -r " + self.subject.dti_rotated_bvec + " -b " + self.subject.dti_bval)


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

    