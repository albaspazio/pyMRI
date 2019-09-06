import sys
import os
import subprocess
from myfsl.utils.run import rrun
from utility.manage_images import imtest

#===============================================================================================================================
# some run functions
#===============================================================================================================================
# run plain os.system command
def runsystem(cmd, logFile=None):
    os.system(cmd)
    if logFile is not None:
        print(cmd, file=logFile)


# run plain os.system command whether the given image is not present
def run_move_notexisting_img(img, cmd, logFile=None, is_fsl=True):
    if not imtest(img):
        runsystem(cmd, logFile)


# run command whether the given image is not present
def run_notexisting_img(img, cmd, logFile=None):
    if not imtest(img):
        rrun(cmd, logFile=logFile)


#===============================================================================================================================
# DEPRECATED run bash commands, i use the rrun function (modified version of the fsl's run function
#===============================================================================================================================
# run fsl (default) or generic command and return exception
def run(cmd, logFile=None, is_fsl=True):

    if is_fsl is True:
        fsl_bin = os.path.join(os.getenv('FSLDIR'), "bin")
        cmdstr = os.path.join(fsl_bin, cmd)
    else:
        cmdstr = cmd

    try:
        retcode = subprocess.check_call(cmdstr, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode, file=sys.stderr)

        if logFile is not None:
            print(cmdstr, file=logFile)

    except subprocess.CalledProcessError as e:

        if e.output is not None:
            errors = e.output.decode('ascii').split('\n')
            errstring = "ERROR in run with cmd: " + cmdstr + ", errors: " + "\n" + "\n".join(errors)
        else:
            errstring = "ERROR in run with cmd: " + cmdstr

        if logFile is not None:
            print(errstring, file=logFile)
        raise Exception(errstring)
#
# run a fsl (default) or generic pipe command
def runpipe(cmd, logFile=None, is_fsl=True):
    try:
        cmdstr = ""
        if is_fsl is True:
            fsl_bin = os.path.join(os.getenv('FSLDIR'), "bin")
            cmdstr = os.path.join(fsl_bin, cmd)
        else:
            cmdstr = cmd

        p = subprocess.Popen(cmdstr, shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if logFile is not None:
            print(cmd, file=logFile)

        return p.stdout.readlines(-1)

    except subprocess.CalledProcessError as e:
        errors = e.output.decode('ascii').split('\n')
        errstring = "ERROR in runpipe with cmd: " + cmdstr + ", errors: " + "\n" + "\n".join(errors)
        if logFile is not None:
            print(errstring, file=logFile)
        raise Exception(errstring)


# run fsl (default) or generic command and return cmd values (typically fslstats)
# def runreturn(cmd, params, logFile=None, is_fsl=True):
#
#     if is_fsl is True:
#         fsl_bin = os.path.join(os.getenv('FSLDIR'), "bin")
#         cmdstr = os.path.join(fsl_bin, cmd)
#     else:
#         cmdstr = cmd
#
#     inputlist = [cmdstr]
#     for i in params:
#         inputlist.append(str(i))
#     fullcmdstr = " ".join(inputlist)
#
#     try:
#         bytesret = subprocess.check_output(inputlist, stderr=subprocess.STDOUT)
#         if logFile is not None:
#             print(fullcmdstr, file=logFile)
#         strret = bytesret.decode('ascii')
#         return strret.split(" ")
#
#     except subprocess.CalledProcessError as e:
#         errors = e.output.decode('ascii').split('\n')
#         errstring = "ERROR in runreturn with cmd: " + fullcmdstr + ", errors: " + "\n" + "\n".join(errors)
#         if logFile is not None:
#             print(errstring, file=logFile)
#         raise Exception(errstring)
#
