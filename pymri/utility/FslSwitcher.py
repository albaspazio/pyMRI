import os


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

    def ver_511(self):
        self.dir = "/usr/local/fsl-5.0.11"
        self.fsl_ver = "5.0.11"
        return self.fsl_ver

    def unknown_version(self):
        return "Unknown Parameters. presently, only version 5.0.9, 5.0.11 and 6 (6.0.0) are installed"

    def send_cmd(self):
        os.system("PATH=%s/bin:${PATH}" % self.dir)
        os.system("FSL_VER=%s" % self.fsl_ver)
        os.system("FSLDIR=%s" % self.dir)
        os.system("export FSLDIR PATH FSL_VER")
        os.system(". %s/etc/fslconf/fsl.sh" % self.dir)
