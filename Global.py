import inspect
import os

from data.utilities import read_varlist_file
from myutility.images.Image import Image
from myutility.myfsl import fsl_switcher


class Global:

    CLEANUP_LVL_MIN = 0
    CLEANUP_LVL_MED = 1
    CLEANUP_LVL_HI  = 1

    def __init__(self, fsl_ver:str, full_check:bool=True, ignore_warnings:bool=True):
        """
        Initialize the Global class.

        Args:
            fsl_ver (str): The version of FSL to use.
            ignore_warnings (bool, optional): Whether to ignore warnings. Defaults to True.

        Raises:
            Exception: If the local.settings file is not present.
        """

        self.ignore_warnings = ignore_warnings

        # --------------------------------------------------------------------------------------------------------
        # determine framework folder
        filename            = inspect.getframeinfo(inspect.currentframe()).filename
        self.framework_dir  = os.path.dirname(os.path.abspath(filename))

        # --------------------------------------------------------------------------------------------------------
        # READ local.settings and fill corresponding variables
        local_settings      = os.path.join(self.framework_dir, "local.settings")

        # check its presence
        if not os.path.isfile(local_settings):
            raise Exception(
                "ERROR. the file \"local.settings\" must be present in the framework root folder (" + self.framework_dir + ")\n" +
                "copy and rename the file " + os.path.join(self.framework_dir, "examples", "local.settings") + " there and modify its content according to your local settings")

        local_settings_data         = read_varlist_file(local_settings)

        self.project_scripts_dir    = local_settings_data["project_scripts_dir"]
        self.spm_dir                = local_settings_data["spm_dir"]
        self.cat_version            = local_settings_data["cat_version"]
        self.marsbar                = local_settings_data["marsbar"]
        self.melodic_data_templates = local_settings_data["melodic_data_templates"]
        self.global_data_templates  = local_settings_data["global_data_templates"]
        self.ica_aroma_script       = local_settings_data["ica_aroma_script"]
        self.trackvis_bin           = local_settings_data["trackvis_bin"]
        self.autoptx_script_dir     = local_settings_data["autoptx_script_dir"]
        self.eddy_gpu_exe_name      = local_settings_data["eddy_gpu_exe_name"]
        self.def_dsi_rec            = local_settings_data["def_dsi_rec"]
        self.def_dsi_conntempl      = local_settings_data["def_dsi_conntempl"]
        self.local_schemas          = local_settings_data["local_schemas"]

        self.cat_foldername         = self.cat_version.split('.')[0]
        self.cat_dir                = os.path.join(self.spm_dir, "toolbox", self.cat_foldername)

        # mandatory check
        if len(self.project_scripts_dir) > 0:
            if os.path.isdir(self.project_scripts_dir) is False:
                raise Exception("Error: Scripts folder is not present")
        else:
            raise Exception("Error: Scripts folder (e.g. /data/MRI/projects/SCRIPT) is not specified")

        # --------------------------------------------------------------------------------------------------------

        self.data_templates_dir     = os.path.join(self.framework_dir, "resources", "templates")
        self.spm_templates_dir      = os.path.join(self.framework_dir, "resources", "templates", "spm")
        self.spm_functions_dir      = os.path.join(self.framework_dir, "resources", "external", "matlab")
        self.ica_aroma_script       = os.path.join(self.framework_dir, "resources", "external", "ica_aroma", "ICA_AROMA.py")

        # ==============================================================================================================
        # MRI SECTION
        # ==============================================================================================================
        fslswitch = fsl_switcher.FslSwitcher()
        print(fslswitch.activate_fsl_version(fsl_ver))

        self.fsl_dir = os.getenv('FSLDIR')
        if self.fsl_dir is None:
            print("WARNING: FSLDIR is undefined")

        if full_check is True:
            self.check_paths()

        if self.cat_version.startswith("cat12.7"):
            # cat 12.7
            self.cat_dartel_template        = Image(os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_1.50mm", "Template_1_IXI555_MNI152.nii"), must_exist=True, msg="CAT Dartel template not present")
            self.cat_template_name          = "cat27_segment_customizedtemplate_tiv_smooth"
        else:
            # cat 12.8
            self.cat_dartel_template        = Image(os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_1_Dartel.nii"), must_exist=True, msg="CAT Dartel template not present")
            self.cat_shooting_template      = Image(os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_0_GS.nii"), must_exist=True, msg="CAT Dartel template not present")
            self.cat_template_name          = "cat28_segment_shooting_tiv_smooth"
            self.cat_dartel_template        = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_1_Dartel.nii")
            self.cat_shooting_template      = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_0_GS.nii")
            self.cat_template_name          = "subj_cat28_segment_shooting_tiv_smooth"
        self.cat_smooth_surf                = 12
        self.cat_smooth_gyrif               = 20

        self.spm_tissue_map                 = Image(os.path.join(self.spm_dir, "tpm", "TPM.nii"), must_exist=True, msg="SPM's Standard Images not present")
        self.spm_icv_mask                   = Image(os.path.join(self.spm_dir, "tpm", "mask_ICV.nii"), must_exist=True, msg="SPM's Standard Images not present")

        self.fsl_bin                        = os.path.join(self.fsl_dir, "bin")
        self.fsl_data_std_dir               = os.path.join(self.fsl_dir, "data", "standard")
        self.fsl_std_mni_2mm_head           = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_brain          = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_brain_mask     = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_brain_mask_dil = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask_dil"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_cnf            = os.path.join(self.fsl_dir, "etc", "flirtsch", "T1_2_MNI152_2mm.cnf")

        # useful for melodic analysis
        self.fsl_std_mni_4mm_head           = Image(os.path.join(self.framework_dir, "resources","templates", "images", "MNI152_T1_4mm"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_brain          = Image(os.path.join(self.framework_dir, "resources","templates", "images", "MNI152_T1_4mm_brain"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_brain_mask     = Image(os.path.join(self.framework_dir, "resources","templates", "images", "MNI152_T1_4mm_brain_mask"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_brain_mask_dil = Image(os.path.join(self.framework_dir, "resources","templates", "images", "MNI152_T1_4mm_brain_mask_dil"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_cnf            = os.path.join(self.framework_dir, "resources","templates", "images", "T1_2_MNI152_4mm.cnf")

        self.fsl_std_mean_skeleton          = Image(os.path.join(self.fsl_data_std_dir, "FMRIB58_FA-skeleton_1mm"), must_exist=True, msg="FSL's Standard Images not present")

        self.std_aal_atlas_2mm              = os.path.join(self.global_data_templates, "mpr", "aal_262_standard")

        self.dti_xtract_labels              = ["af_l", "af_r", "ar_l", "ar_r", "atr_l", "atr_r", "cbd_l", "cbd_r", "cbp_l", "cbp_r",
                                              "cbt_l", "cbt_r", "cst_l", "cst_r", "fa_l", "fa_r", "fma", "fmi", "fx_l", "fx_r",
                                              "ilf_l", "ilf_r", "ifo_l", "ifo_r", "mcp", "mdlf_l", "mdlf_r", "or_l", "or_r",
                                              "str_l", "str_r", "slf1_l", "slf1_r", "slf2_l", "slf2_r", "slf3_l", "slf3_r", "ac",
                                              "uf_l", "uf_r", "vof_l", "vof_r", "cc"]
        self.dti_xtract_dir                 = os.path.join(self.framework_dir, "resources", "templates", "images", "xtract", "mean_skeleton")

    @staticmethod
    def get_spm_template_dir():
        """Get the path to the SPM templates directory.

        Returns:
            str: The path to the SPM templates directory.
        """
        filename            = inspect.getframeinfo(inspect.currentframe()).filename
        return os.path.join(os.path.dirname(os.path.abspath(filename)), "resources", "templates", "spm")

    def check_paths(self):
        """
        Check the presence of important folders and files.

        Raises:
            Exception: If any of the required folders or files are not present.

        Args:
            self (Global): The Global object.
        """


        if len(self.spm_dir) > 0:
            if not os.path.isdir(self.spm_dir):
                raise Exception("Error: SPM is not present")
        else:
            if not self.ignore_warnings:
                print("Warning: SPM has not been specified")

        if len(self.cat_version) > 0:
            if not os.path.isdir(self.cat_dir):
                raise Exception("Error: CAT is not present")
        else:
            if not self.ignore_warnings:
                print("Warning: CAT has not been specified")

        if len(self.ica_aroma_script) > 0:
            if not os.path.isfile(self.ica_aroma_script):
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
