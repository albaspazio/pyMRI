from utility import fsl_switcher
import os

if __name__ == "__main__":

    fslswitch = fsl_switcher()

    res = fslswitch.activate_fsl_version("600")

    print(res)
    print(os.system("echo $FSLDIR"))

