import inspect
import os


# user must set:
# - spm_dir
# - cat version

class Global:

    def __init__(self, globalscriptdir):

        # --------------------------------------------------------------------------------------------------------
        # USER DEPENDENT
        # --------------------------------------------------------------------------------------------------------
        self.spm_dir                        = "/data/matlab_toolbox/spm12"
        self.cat_version                    = "cat12"
        # --------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------

        filename                            = inspect.getframeinfo(inspect.currentframe()).filename
        self.framework_dir                  = os.path.dirname(os.path.abspath(filename))

        self.templates_dir                  = os.path.join(self.framework_dir, "templates")
        self.spm_templates_dir              = os.path.join(self.framework_dir, "templates", "spm")
        self.spm_functions_dir              = os.path.join(self.framework_dir, "matlab")

        self.global_script_dir              = globalscriptdir
        self.global_data_templates          = os.path.join(self.global_script_dir, "data_templates")
        self.global_utility_script          = os.path.join(self.global_script_dir, "utility")

        self.ica_aroma_script_dir           = os.path.join(self.global_script_dir, "external_tools", "ica_aroma", "ica_aroma.py")
        self.autoptx_script_dir             = os.path.join(self.global_script_dir, "external_tools", "autoPtx_0_1_1")
        self.trackvis_bin                   = os.path.join(globalscriptdir, "external_tools", "dtk")

        self.fsl_dir                        = os.getenv('FSLDIR')

        if self.fsl_dir is None:
            print("FSLDIR is undefined")
            return

        self.cat_dartel_template            = os.path.join(self.spm_dir,"toolbox", self.cat_version, "templates_1.50mm", "Template_1_IXI555_MNI152.nii")
        self.spm_tissue_map                 = os.path.join(self.spm_dir, "tpm", "TPM.nii")

        self.fsl_bin                        = os.path.join(self.fsl_dir, "bin")
        self.fsl_data_standard_dir          = os.path.join(self.fsl_dir, "data", "standard")
        self.fsl_standard_mni_2mm_head      = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm")
        self.fsl_standard_mni_2mm           = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain")
        self.fsl_standard_mni_2mm_mask      = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain_mask")
        self.fsl_standard_mni_2mm_mask_dil  = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_2mm_brain_mask_dil")
        self.fsl_standard_mni_4mm           = os.path.join(self.fsl_data_standard_dir, "MNI152_T1_4mm_brain")

        self.fsl_standard_mni_2mm_cnf       = os.path.join(self.fsl_dir, "etc", "flirtsch", "T1_2_MNI152_2mm.cnf")

        self.standard_aal_atlas_2mm         = os.path.join(self.global_data_templates, "mpr", "aal_262_standard")

        self.vtk_transpose_file             = os.path.join(self.global_utility_script, "transpose_dti32.awk")

