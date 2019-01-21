from pymri.utility import FslSwitcher
import os

if __name__ == "__main__":

    fslswitch = FslSwitcher()

    res = fslswitch.activate_fsl_version("600")

    print(res)
    print(os.system("echo $FSLDIR"))

