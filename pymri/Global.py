import os


class Global:

    def __init__(self, globalscriptdir):

        self.global_script_dir  = globalscriptdir
        self.global_data_templates = os.path.join(self.global_script_dir, "data_templates")
        self.global_utility_script = os.path.join(self.global_script_dir, "utility")

        self.ica_aroma_script_dir = os.path.join(self.global_script_dir, "external_tools", "ica_aroma", "ica_aroma.py")
        self.autoptx_script_dir = os.path.join(self.global_script_dir, "external_tools", "autoPtx_0_1_1")
        self.trackvis_bin = "/media/data/MRI/scripts/external_tools/dtk"

        self.fsl_dir = os.getenv('FSLDIR')
        self.fsl_bin = os.path.join(self.fsl_dir, "bin")
        self.fsl_data_standard = os.path.join(self.fsl_dir, "data", "standard")
        self.fsl_standard_mni_2mm = os.path.join(self.fsl_data_standard, "MNI152_T1_2mm_brain")
        self.fsl_standard_mni_2mm_mask = os.path.join(self.fsl_data_standard, "MNI152_T1_2mm_brain_mask")
        self.fsl_standard_mni_4mm = os.path.join(self.fsl_data_standard, "MNI152_T1_4mm_brain")

        self.standard_aal_atlas_2mm = os.path.join(self.global_data_templates, "mpr", "aal_262_standard")

        self.vtk_transpose_file = os.path.join(self.global_utility_script, "transpose_dti32.awk")
