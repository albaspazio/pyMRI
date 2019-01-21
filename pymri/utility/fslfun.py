import os
from shutil import copyfile, move
import subprocess
import sys
import glob


IMAGE_FORMATS = [".nii", ".nii.gz", ".mnc", ".mnc.gz", ".hdr", ".hdr.gz", ".img", ".img.gz"]

# return False if no image exists or True if the image exists
def imtest(image_path):

    if image_path == "":
        return False

    filename, file_extension = remove_ext(image_path)

    if os.path.isfile(filename + ".nii") or os.path.isfile(filename + ".nii.gz"):
        return True

    if os.path.isfile(filename + ".mnc") or os.path.isfile(filename + ".mnc.gz"):
        return True

    if not os.path.isfile(filename + ".hdr") and not os.path.isfile(filename + ".hdr.gz"):
        # return 0 here as no header exists and no single image means no image!
        return False

    if not os.path.isfile(filename + ".img") and not os.path.isfile(filename + ".img.gz"):
        # return 0 here as no img file exists and no single image means no image!
        return False

    # only gets to here if there was a hdr and an img file
    return True

def imcp(src, dest, log=None):

    filename_src, file_extension_src = os.path.splitext(src)
    filename_dst, file_extension_dst = os.path.splitext(dest)

    if os.path.isfile(filename_src + ".nii"):
        ext = ".nii"
    elif os.path.isfile(filename_src + ".nii.gz"):
        ext = ".nii.gz"

    copyfile(filename_src + ext, filename_dst + ext)

    if log is not None:
        print("cp " + filename_src + ext + " " + filename_dst + ext, file=log)

def immv(src, dest, log=None):

    filename_src, file_extension_src = os.path.splitext(src)
    filename_dst, file_extension_dst = os.path.splitext(dest)

    ext = ""
    if os.path.isfile(filename_src + ".nii"):
        ext = ".nii"
    elif os.path.isfile(filename_src + ".nii.gz"):
        ext = ".nii.gz"

    if ext == "":
        return False

    move(filename_src + ext, filename_dst + ext)

    if log is not None:
        print("mv " + filename_src + ext + " " + filename_dst + ext, file=log)

    return True

def imrm(filelist, log=None):

    for file in filelist:
        filename_src, file_extension_src = os.path.splitext(file)

        if os.path.isfile(filename_src + ".nii"):
            ext = ".nii"
        elif os.path.isfile(filename_src + ".nii.gz"):
            ext = ".nii.gz"

        os.remove(filename_src + ext)

        if log is not None:
            print("rm " + filename_src + ext, file=log)

def run(cmd, log=None):

    fsl_bin = os.path.join(os.getenv('FSLDIR'), "bin")
    cmdstr = os.path.join(fsl_bin, cmd)

    try:
        retcode = subprocess.check_call(cmdstr, shell=True)
        if retcode < 0:
            print("Child was terminated by signal", -retcode, file=sys.stderr)

        if log is not None:
            print(cmdstr, file=log)

    except subprocess.CalledProcessError as e:

        if e.output is not None:
            errors = e.output.decode('ascii').split('\n')
            errstring = "ERROR in run with cmd: " + cmdstr + ", errors: " + "\n" + "\n".join(errors)
        else:
            errstring = "ERROR in run with cmd: " + cmdstr

        if log is not None:
            print(errstring, file=log)
        raise Exception(errstring)

# used for mv command that returns error if no valid files exist
def runsystem(cmd, log=None):
    os.system(cmd)
    if log is not None:
        print(cmd, file=log)

# run command whether the given file is not present
def run_move_notexisting_img(img, cmd, log=None):
    if not imtest(img):
        runsystem(cmd, log)

# run command whether the given file is not present
def run_notexisting_img(img, cmd, log=None):
    if not imtest(img):
        run(cmd, log)

# run a pipe command
def runpipe(cmd, log=None):
    try:
        p = subprocess.Popen(cmd, shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if log is not None:
            print(cmd, file=log)

        return p.stdout.readlines(-1)

    except subprocess.CalledProcessError as e:
        errors = e.output.decode('ascii').split('\n')
        errstring = "ERROR in runpipe with cmd: " + cmd + ", errors: " + "\n" + "\n".join(errors)
        if log is not None:
            print(errstring, file=log)
        raise Exception(errstring)

# return cmd values (typically fslstats)
def runreturn(cmd, params, log=None):

    fsl_bin = os.path.join(os.getenv('FSLDIR'), "bin")
    cmdstr = os.path.join(fsl_bin, cmd)

    inputlist = [cmdstr]
    for i in params:
        inputlist.append(str(i))
    fullcmdstr = " ".join(inputlist)

    try:
        bytesret = subprocess.check_output(inputlist, stderr=subprocess.STDOUT)
        if log is not None:
            print(fullcmdstr, file=log)
        strret = bytesret.decode('ascii')
        return strret.split(" ")

    except subprocess.CalledProcessError as e:
        errors = e.output.decode('ascii').split('\n')
        errstring = "ERROR in runreturn with cmd: " + fullcmdstr + ", errors: " + "\n" + "\n".join(errors)
        if log is not None:
            print(errstring, file=log)
        raise Exception(errstring)

# move a series of images defined by wildcard string ( e.g.   *fast*
def mass_images_move(wildcardsource, destdir, log=None):

    files = glob.glob(wildcardsource)

    images = []
    for f in files:
        if is_image(f) is True:
            images.append(f)

    for img in images:
        dest_file = os.path.join(destdir, os.path.basename(img))
        move(img, dest_file)
        if log is not None:
            print("mv " + img + " " + dest_file, file=log)


def is_image(file):

    _, file_extension = remove_ext(file)

    if file_extension in IMAGE_FORMATS:
        return True
    else:
        return False


def quick_smooth(inimg, outimg, log):

  run("fslmaths " + inimg + " -subsamp2 -subsamp2 -subsamp2 -subsamp2 vol16", log)
  run("flirt -in vol16 -ref " + inimg + " -out " + outimg + " -noresampblur -applyxfm -paddingsize 16", log)
  # possibly do a tiny extra smooth to $out here?
  imrm(["vol16"])

def remove_ext(img):

    filename, fext = os.path.splitext(img)
    fullext = fext
    while "." in filename:
        filename, fext = os.path.splitext(filename)
        fullext = fext + fullext

    return filename, fullext