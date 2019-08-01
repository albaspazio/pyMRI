import os
import subprocess
from pymri.fsl.utils.run import rrun

class FslSwitcher:

    dir = ""
    fsl_ver = ""

    def activate_fsl_version(self, argument):
        """Dispatch method"""
        method_name = 'ver_' + str(argument)
        method = getattr(self, method_name, lambda: self.unknown_version())        # Get the method from 'self'. Default to a lambda.
        method()         # Call the method as we return it
        self.send_cmd()

    def ver_509(self):
        self.dir = "/usr/local/fsl-5.0.9"
        self.fsl_ver = "5.0.9"
        return self.fsl_ver

    def ver_600(self):
        self.dir = "/usr/local/fsl-6.0"
        self.fsl_ver = "6.0.0"
        return self.fsl_ver

    def ver_601(self):
        self.dir = "/usr/local/fsl-6.0.1"
        self.fsl_ver = "6.0.1"
        return self.fsl_ver

    def ver_511(self):
        self.dir = "/usr/local/fsl-5.0.11"
        self.fsl_ver = "5.0.11"
        return self.fsl_ver

    def unknown_version(self):
        return "Unknown Parameters. presently, only version 5.0.9, 5.0.11 and 6 (6.0.0) are installed"

    def send_cmd(self):
        # os.environ['PATH']      ="%s/bin:${PATH}" % self.dir
        # os.environ['FSL_VER']   ="%s" % self.fsl_ver
        # os.environ['FSLDIR']    ="%s" % self.dir

        os.system("PATH=%s/bin:${PATH}" % self.dir)
        os.system("FSL_VER=%s" % self.fsl_ver)
        os.system("FSLDIR=%s" % self.dir)
        os.system("export PATH FSL_VER FSLDIR")
        os.system(". %s/etc/fslconf/fsl.sh" % self.dir)

        # rrun(". %s/etc/fslconf/fsl.sh" % self.dir)
        # process = subprocess.run(["bash", "%s/etc/fslconf/fsl.sh" % self.dir], stdin=subprocess.PIPE)
        # process.wait()  # Wait for process to complete.
