import inspect
import os
from typing import Any


class Global:
    """
    Base Global configuration class for generic framework operations.
    
    This class provides safe configuration access without requiring MRI-specific
    tools or dependencies. It establishes a base contract for all Global implementations.
    
    Attributes:
        framework_dir (str): The absolute path to the PyMRI framework root directory.
        project_scripts_dir (str): The absolute path to external project scripts directory.
        ignore_warnings (bool): Whether to suppress non-critical warnings.
    
    The safe property access pattern (_safe_get_setting) enables graceful handling of
    missing configuration properties, making this class suitable for both MRI and
    non-MRI projects.
    """

    CLEANUP_LVL_MIN = 0
    CLEANUP_LVL_MED = 1
    CLEANUP_LVL_HI = 1

    def __init__(self, ignore_warnings: bool = True):
        """
        Initialize the base Global configuration.
        
        This initialization does not require local.settings to exist or any MRI
        tools to be configured. It establishes only framework-level paths.
        
        Args:
            ignore_warnings (bool, optional): Whether to suppress non-critical warnings. 
                Defaults to True.
        """
        self.ignore_warnings = ignore_warnings

        # Determine framework folder
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.framework_dir = os.path.dirname(os.path.abspath(filename))

        # Initialize project scripts directory (will be set by subclasses or configuration)
        self.project_scripts_dir = ""

    def _safe_get_setting(self, data_dict: dict, key: str, default: Any = None) -> Any:
        """
        Safely read a configuration setting from a dictionary.
        
        This method provides graceful property access without crashing if a key
        is missing. If the key is not present in the dictionary, the default value
        is returned instead.
        
        Args:
            data_dict (dict): The configuration dictionary to read from.
            key (str): The key to look up in the dictionary.
            default (Any, optional): The default value to return if the key is missing. 
                Defaults to None.
        
        Returns:
            Any: The value from the dictionary, or the default if the key is missing.
        
        Examples:
            >>> config = {"spm_dir": "/opt/spm12"}
            >>> value = self._safe_get_setting(config, "spm_dir", "")
            >>> value
            '/opt/spm12'
            >>> missing = self._safe_get_setting(config, "fsl_dir", "")
            >>> missing
            ''
        """
        return data_dict.get(key, default)

    @staticmethod
    def get_spm_template_dir() -> str:
        """
        Get the path to the SPM templates directory.
        
        This is a framework-level utility that can be used without instantiating
        a Global object.
        
        Returns:
            str: The absolute path to the SPM templates directory.
        """
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        return os.path.join(os.path.dirname(os.path.abspath(filename)), "../resources", "templates", "spm")
