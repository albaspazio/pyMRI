import inspect
import os
from utility import fsl_switcher, import_data_file


class Global:

    def __init__(self, fsl_ver, ignore_warnings=True):

        fslswitch = fsl_switcher.FslSwitcher()
        print(fslswitch.activate_fsl_version(fsl_ver))

        self.ignore_warnings                = ignore_warnings
        # --------------------------------------------------------------------------------------------------------
        # determine framework folder
        filename                            = inspect.getframeinfo(inspect.currentframe()).filename
        self.framework_dir                  = os.path.dirname(os.path.abspath(filename))
        # --------------------------------------------------------------------------------------------------------
        # READ local.settings and fill corresponding variables
        local_settings = os.path.join(self.framework_dir, "local.settings")

        # check its presence
        if os.path.isfile(local_settings) is False:
            raise Exception("ERROR. the file \"local.settings\" must be present in the framework root folder (" + self.framework_dir + ")\n" +
                            "copy and rename the file " + os.path.join(self.framework_dir, "examples", "local.settings") + " there and modify its content according to your local settings")

        local_settings_data = import_data_file.read_varlist_file(local_settings)

        self.spm_dir                        = local_settings_data["spm_dir"]
        self.cat_version                    = local_settings_data["cat_version"]
        self.marsbar                        = local_settings_data["marsbar"]
        self.global_data_templates          = local_settings_data["global_data_templates"]
        self.ica_aroma_script               = local_settings_data["ica_aroma_script"]
        self.trackvis_bin                   = local_settings_data["trackvis_bin"]
        self.autoptx_script_dir             = local_settings_data["autoptx_script_dir"]

        self.cat_foldername                 = self.cat_version.split('.')[0]

        self.check_paths()
        # --------------------------------------------------------------------------------------------------------

        self.data_templates_dir             = os.path.join(self.framework_dir, "templates")
        self.spm_templates_dir              = os.path.join(self.framework_dir, "templates", "spm")
        self.spm_functions_dir              = os.path.join(self.framework_dir, "external", "matlab")
        self.ica_aroma_script               = os.path.join(self.framework_dir, "external", "ica_aroma", "ICA_AROMA.py")

        self.fsl_dir                        = os.getenv('FSLDIR')
        if self.fsl_dir is None:
            print("FSLDIR is undefined")
            return

        if self.cat_version.startswith("cat12.7"):
            # cat 12.7
            self.cat_dartel_template        = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_1.50mm", "Template_1_IXI555_MNI152.nii")
            self.cat_template_name          = "cat27_segment_customizedtemplate_tiv_smooth"
        else:
            # cat 12.8
            self.cat_dartel_template        = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_1_Dartel.nii")
            self.cat_shooting_template      = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_0_GS.nii")
            self.cat_template_name          = "cat28_segment_shooting_tiv_smooth"

        self.spm_tissue_map                 = os.path.join(self.spm_dir, "tpm", "TPM.nii")

        self.fsl_bin                        = os.path.join(self.fsl_dir, "bin")
        self.fsl_data_std_dir               = os.path.join(self.fsl_dir, "data", "standard")
        self.fsl_std_mni_2mm_head           = os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm")
        self.fsl_std_mni_2mm_brain          = os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain")
        self.fsl_std_mni_2mm_brain_mask     = os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask")
        self.fsl_std_mni_2mm_brain_mask_dil = os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask_dil")
        self.fsl_std_mni_2mm_cnf            = os.path.join(self.fsl_dir, "etc", "flirtsch", "T1_2_MNI152_2mm.cnf")

        # useful for melodic analysis
        self.fsl_std_mni_4mm_head           = os.path.join(self.framework_dir, "templates", "images", "MNI152_T1_4mm")
        self.fsl_std_mni_4mm_brain          = os.path.join(self.framework_dir, "templates", "images", "MNI152_T1_4mm_brain")
        self.fsl_std_mni_4mm_brain_mask     = os.path.join(self.framework_dir, "templates", "images", "MNI152_T1_4mm_brain_mask")
        self.fsl_std_mni_4mm_brain_mask_dil = os.path.join(self.framework_dir, "templates", "images", "MNI152_T1_4mm_brain_mask_dil")
        self.fsl_std_mni_4mm_cnf            = os.path.join(self.framework_dir, "templates", "images", "T1_2_MNI152_4mm.cnf")

        self.std_aal_atlas_2mm         = os.path.join(self.global_data_templates, "mpr", "aal_262_standard")

    def check_paths(self):

        if len(self.spm_dir) > 0:
            if os.path.isdir(self.spm_dir) is False:
                raise Exception("Error: SPM is not present")
        else:
            if not self.ignore_warnings:
                print("Warning: SPM has not been specified")

        if len(self.cat_version) > 0:
            if os.path.isdir(os.path.join(self.spm_dir, "toolbox", self.cat_foldername)) is False:
                raise Exception("Error: CAT is not present")
        else:
            if not self.ignore_warnings:
                print("Warning: CAT has not been specified")

        if len(self.ica_aroma_script) > 0:
            if os.path.isfile(self.ica_aroma_script) is False:
                raise Exception("Error: ICA-AROMA script is not present")
        else:
            if not self.ignore_warnings:
                print("Warning: ICA-AROMA has not been specified")

        # accessory elements. do not warn if they are not specified
        # if len(self.global_data_templates) > 0:
        #     if os.path.isdir(self.global_data_templates) is False:
        #         raise Exception("Error: DATA TEMPLATES folder is not present")
        #
        # if len(self.trackvis_bin) > 0:
        #     if os.path.isdir(self.trackvis_bin) is False:
        #         raise Exception("Error: TRACKVIS BIN folder is not present")
        #
        # if len(self.autoptx_script_dir) > 0:
        #     if os.path.isdir(self.autoptx_script_dir) is False:
        #         raise Exception("Error: DATA AUTOPTX folder is not present")
        #
        # if len(self.marsbar) > 0:
        #     if os.path.isdir(os.path.join(self.spm_dir, "toolbox", "marsbar")) is False:
        #         self.marsbar_dir        = ""
        #         self.marsbar_spm_dir    = ""
        #         raise Exception("Error: marsbar is not present")
        #     else:
        #         self.marsbar_dir        = os.path.join(self.spm_dir, "toolbox", "marsbar")
        #         self.marsbar_spm_dir    = os.path.join(self.spm_dir, "toolbox", "marsbar", "spm5")

