import os

from utility.myfsl import fsl_switcher
from utility.myfsl.fsl_switcher import FslSwitcher

if __name__ == "__main__":
    fslswitch = FslSwitcher()

    res = fslswitch.activate_fsl_version("600")

    print(res)
    print(os.system("echo $FSLDIR"))
