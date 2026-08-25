import os

from project.Global import Global
from data.utilities import read_varlist_file
from myutility.images.Image import Image
from myutility.myfsl import fsl_switcher


class MRIGlobal(Global):
    """
    MRI-specific global configuration class extending the base Global.
    
    This class reads MRI tool configuration from local.settings safely, using the
    _safe_get_setting() method to handle missing properties gracefully. All MRI
    dependencies (FSL, SPM, CAT) are initialized in this class, not in the base.
    
    Attributes (from local.settings):
        spm_dir (str): Path to SPM installation
        cat_version (str): CAT toolbox version (e.g., "cat12.8")
        marsbar (str): MARSbar extension path
        melodic_data_templates (str): MELODIC templates directory
        global_data_templates (str): Global data templates directory
        ica_aroma_script (str): ICA-AROMA script path
        trackvis_bin (str): TrackVis binary path
        autoptx_script_dir (str): AutoPtX script directory
        eddy_gpu_exe_name (str): GPU-accelerated eddy executable name
        def_dsi_rec (str): Default DSI reconstruction
        def_dsi_conntempl (str): Default DSI connectivity template
        local_schemas (str): Local schemas directory
    
    Derived attributes (computed from local.settings):
        cat_dir (str): Full path to CAT toolbox directory
        cat_foldername (str): CAT folder name (e.g., "cat12" from version "cat12.8")
        cat_template_surfaces_32k (str): CAT 32k template surfaces path
        cat_dartel_template (Image): CAT Dartel template image
        cat_shooting_template (Image): CAT shooting template image
        cat_template_name (str): CAT template name for segmentation
        cat_smooth_surf (int): Surface smoothing kernel for CAT
        cat_smooth_gyrif (int): Gyrification smoothing kernel for CAT
        
        fsl_dir (str): FSL installation directory
        fsl_bin (str): FSL bin directory
        fsl_data_std_dir (str): FSL standard images directory
        fsl_std_mni_2mm_head (Image): 2mm MNI head template
        fsl_std_mni_2mm_brain (Image): 2mm MNI brain template
        fsl_std_mni_2mm_brain_mask (Image): 2mm brain mask
        fsl_std_mni_2mm_brain_mask_dil (Image): 2mm brain mask dilated
        fsl_std_mni_2mm_cnf (str): 2mm flirt configuration
        fsl_std_mni_4mm_* (Image): 4mm MNI standard images
        fsl_std_mean_skeleton (Image): Mean skeleton for TBSS
        
        spm_templates_dir (str): SPM templates directory
        spm_functions_dir (str): SPM Matlab functions directory
        spm_tissue_map (Image): SPM tissue probability map
        spm_icv_mask (Image): SPM ICV mask image
        
        dti_xtract_labels (List[str]): XTRACT white matter tract labels
        dti_xtract_dir (str): XTRACT templates directory
        
        std_aal_atlas_2mm (str): AAL atlas 2mm path
    """

    def __init__(self, fsl_ver: str, full_check: bool = True, ignore_warnings: bool = True):
        """
        Initialize MRI-specific global configuration.
        
        Reads local.settings from the framework directory using safe property access.
        All MRI-specific properties are initialized with defaults if missing from
        local.settings. Filesystem validation can be controlled via full_check.
        
        Args:
            fsl_ver (str): The FSL version to activate (e.g., "6.0", "5.0.11").
            full_check (bool, optional): Whether to validate that MRI tool directories
                exist on the filesystem. Defaults to True.
            ignore_warnings (bool, optional): Whether to suppress non-critical warnings
                about missing optional MRI tools. Defaults to True.
        
        Raises:
            Exception: If local.settings file is not found in the framework directory.
        """
        super().__init__(ignore_warnings=ignore_warnings)

        # --------------------------------------------------------------------------------------------------------
        # READ local.settings and fill corresponding variables
        local_settings = os.path.join(self.framework_dir, "local.settings")

        # check its presence
        if not os.path.isfile(local_settings):
            raise Exception(
                "ERROR. the file \"local.settings\" must be present in the framework root folder (" + self.framework_dir + ")\n" +
                "copy and rename the file " + os.path.join(self.framework_dir, "examples", "../local.settings") + " there and modify its content according to your local settings")

        local_settings_data = read_varlist_file(local_settings)

        # Initialize all local.settings properties safely (with defaults if missing)
        self.project_scripts_dir    = self._safe_get_setting(local_settings_data, "project_scripts_dir", "")
        self.spm_dir                = self._safe_get_setting(local_settings_data, "spm_dir", "")
        self.cat_version            = self._safe_get_setting(local_settings_data, "cat_version", "")
        self.marsbar                = self._safe_get_setting(local_settings_data, "marsbar", "")
        self.melodic_data_templates = self._safe_get_setting(local_settings_data, "melodic_data_templates", "")
        self.global_data_templates  = self._safe_get_setting(local_settings_data, "global_data_templates", "")
        self.ica_aroma_script       = self._safe_get_setting(local_settings_data, "ica_aroma_script", "")
        self.trackvis_bin           = self._safe_get_setting(local_settings_data, "trackvis_bin", "")
        self.autoptx_script_dir     = self._safe_get_setting(local_settings_data, "autoptx_script_dir", "")
        self.eddy_gpu_exe_name      = self._safe_get_setting(local_settings_data, "eddy_gpu_exe_name", "")
        self.def_dsi_rec            = self._safe_get_setting(local_settings_data, "def_dsi_rec", "")
        self.def_dsi_conntempl      = self._safe_get_setting(local_settings_data, "def_dsi_conntempl", "")
        self.local_schemas          = self._safe_get_setting(local_settings_data, "local_schemas", "")

        # Derive CAT paths
        self.cat_foldername         = self.cat_version.split('.')[0] if self.cat_version else ""
        self.cat_dir                = os.path.join(self.spm_dir, "toolbox", self.cat_foldername) if self.spm_dir else ""
        self.cat_template_surfaces_32k = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_surfaces_32k") if self.spm_dir else ""

        # mandatory check on scripts folder
        if len(self.project_scripts_dir) > 0:
            if not os.path.isdir(self.project_scripts_dir):
                raise Exception("Error: Scripts folder is not present")
        else:
            raise Exception("Error: Scripts folder (e.g. /data/MRI/projects/SCRIPT) is not specified")

        # --------------------------------------------------------------------------------------------------------
        # Framework-level template directories (always available)
        self.data_templates_dir = os.path.join(self.framework_dir, "resources", "templates")
        self.spm_templates_dir  = os.path.join(self.framework_dir, "resources", "templates", "spm")
        self.spm_functions_dir  = os.path.join(self.framework_dir, "resources", "external", "matlab")
        self.ica_aroma_script   = os.path.join(self.framework_dir, "resources", "external", "ica_aroma", "ICA_AROMA.py")

        # ==============================================================================================================
        # MRI SECTION - Activate FSL and initialize MRI tools
        # ==============================================================================================================
        fslswitch = fsl_switcher.FslSwitcher()
        print(fslswitch.activate_fsl_version(fsl_ver))

        self.fsl_dir = os.getenv('FSLDIR')
        if self.fsl_dir is None:
            print("WARNING: FSLDIR is undefined")

        if full_check is True:
            self.check_paths()

        # ========================================================
        # CAT Templates (version-specific)
        # ========================================================
        if self.cat_version.startswith("cat12.7"):
            # cat 12.7
            self.cat_dartel_template = Image(os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_1.50mm", "Template_1_IXI555_MNI152.nii"), must_exist=True, msg="CAT Dartel template not present")
            self.cat_template_name = "cat27_segment_customizedtemplate_tiv_smooth"
        else:
            # cat 12.8
            self.cat_dartel_template = Image(os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_1_Dartel.nii"), must_exist=True, msg="CAT Dartel template not present")
            self.cat_shooting_template = Image(os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_0_GS.nii"), must_exist=True, msg="CAT Dartel template not present")
            self.cat_template_name = "cat28_segment_shooting_tiv_smooth"
            self.cat_dartel_template = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_1_Dartel.nii")
            self.cat_shooting_template = os.path.join(self.spm_dir, "toolbox", self.cat_foldername, "templates_MNI152NLin2009cAsym", "Template_0_GS.nii")
            self.cat_template_name = "subj_cat28_segment_shooting_tiv_smooth"
        self.cat_smooth_surf = 12
        self.cat_smooth_gyrif = 20

        # ========================================================
        # SPM Standard Tissue Probability Map and ICV Mask
        # ========================================================
        self.spm_tissue_map = Image(os.path.join(self.spm_dir, "tpm", "TPM.nii"), must_exist=True, msg="SPM's Standard Images not present")
        self.spm_icv_mask   = Image(os.path.join(self.spm_dir, "tpm", "mask_ICV.nii"), must_exist=True, msg="SPM's Standard Images not present")

        # ========================================================
        # FSL Standard Images (2mm resolution)
        # ========================================================
        self.fsl_bin                        = os.path.join(self.fsl_dir, "bin") if self.fsl_dir else ""
        self.fsl_data_std_dir               = os.path.join(self.fsl_dir, "data", "standard") if self.fsl_dir else ""
        self.fsl_std_mni_2mm_head           = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_brain          = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_brain_mask     = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_brain_mask_dil = Image(os.path.join(self.fsl_data_std_dir, "MNI152_T1_2mm_brain_mask_dil"), must_exist=True, msg="FSL's Standard Images not present")
        self.fsl_std_mni_2mm_cnf            = os.path.join(self.fsl_dir, "etc", "flirtsch", "T1_2_MNI152_2mm.cnf") if self.fsl_dir else ""

        # ========================================================
        # FSL Standard Images (4mm resolution)
        # ========================================================
        # useful for melodic analysis
        self.fsl_std_mni_4mm_head           = Image(os.path.join(self.framework_dir, "resources", "templates", "images", "MNI152_T1_4mm"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_brain          = Image(os.path.join(self.framework_dir, "resources", "templates", "images", "MNI152_T1_4mm_brain"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_brain_mask     = Image(os.path.join(self.framework_dir, "resources", "templates", "images", "MNI152_T1_4mm_brain_mask"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_brain_mask_dil = Image(os.path.join(self.framework_dir, "resources", "templates", "images", "MNI152_T1_4mm_brain_mask_dil"), must_exist=True, msg="pyMRI 4mm Standard Images not present")
        self.fsl_std_mni_4mm_cnf            = os.path.join(self.framework_dir, "resources", "templates", "images", "T1_2_MNI152_4mm.cnf")

        # ========================================================
        # FSL Additional Standard Images
        # ========================================================
        self.fsl_std_mean_skeleton = Image(os.path.join(self.fsl_data_std_dir, "FMRIB58_FA-skeleton_1mm"), must_exist=True, msg="FSL's Standard Images not present")

        # ========================================================
        # Atlases and XTRACT
        # ========================================================
        self.std_aal_atlas_2mm = os.path.join(self.global_data_templates, "mpr", "aal_262_standard") if self.global_data_templates else ""

        self.dti_xtract_labels = ["af_l", "af_r", "ar_l", "ar_r", "atr_l", "atr_r", "cbd_l", "cbd_r", "cbp_l", "cbp_r",
                                  "cbt_l", "cbt_r", "cst_l", "cst_r", "fa_l", "fa_r", "fma", "fmi", "fx_l", "fx_r",
                                  "ilf_l", "ilf_r", "ifo_l", "ifo_r", "mcp", "mdlf_l", "mdlf_r", "or_l", "or_r",
                                  "str_l", "str_r", "slf1_l", "slf1_r", "slf2_l", "slf2_r", "slf3_l", "slf3_r", "ac",
                                  "uf_l", "uf_r", "vof_l", "vof_r", "cc"]
        self.dti_xtract_dir = os.path.join(self.framework_dir, "resources", "templates", "images", "xtract", "mean_skeleton")

    def check_paths(self):
        """
        Check the presence of important MRI tool folders and files.
        
        This method validates that required MRI tools are installed and accessible.
        If ignore_warnings is False, warnings are printed for missing optional tools.
        
        Raises:
            Exception: If any of the required MRI tools are not present.
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
