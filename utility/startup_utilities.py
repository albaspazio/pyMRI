import os
from utility import fsl_switcher


def init(globalscriptdir, projectdir, fsl_ver):

    if not os.path.exists(globalscriptdir):
        print("GLOBAL_SCRIPT_DIR not defined.....exiting")
        return False

    if not os.path.exists(projectdir):
        print("PROJECT_DIR not defined.....exiting")
        return False

    fslswitch = fsl_switcher.FslSwitcher()
    res = fslswitch.activate_fsl_version(fsl_ver)

    return True
