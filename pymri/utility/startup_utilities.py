import os
from pymri.utility import FslSwitcher


def init(globalscriptdir, projectdir, fsl_ver):

    if not os.path.exists(globalscriptdir):
        print("GLOBAL_SCRIPT_DIR not defined.....exiting")
        return False

    if not os.path.exists(projectdir):
        print("PROJECT_DIR not defined.....exiting")
        return False

    fslswitch = FslSwitcher()
    res = fslswitch.activate_fsl_version(fsl_ver)

    return True
