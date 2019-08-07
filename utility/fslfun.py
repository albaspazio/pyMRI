import os
import sys
import ntpath
from shutil import copyfile, move
import glob
import subprocess
import xml.etree.ElementTree as ET

from myfsl.utils.run import rrun

IMAGE_FORMATS = [".nii", ".nii.gz", ".mnc", ".mnc.gz", ".hdr", ".hdr.gz", ".img", ".img.gz", ".mgz"]

#===============================================================================================================================
# manage images
#===============================================================================================================================
# return False if no image exists or True if the image exists
def imtest(image_path):

    if image_path == "":
        return False

    fileparts = mysplittext(image_path)

    if os.path.isfile(fileparts[0] + ".nii") or os.path.isfile(fileparts[0] + ".nii.gz") or os.path.isfile(fileparts[0] + ".mgz"):
        return True

    if os.path.isfile(fileparts[0] + ".mnc") or os.path.isfile(fileparts[0] + ".mnc.gz"):
        return True

    if not os.path.isfile(fileparts[0] + ".hdr") and not os.path.isfile(fileparts[0] + ".hdr.gz"):
        # return 0 here as no header exists and no single image means no image!
        return False

    if not os.path.isfile(fileparts[0] + ".img") and not os.path.isfile(fileparts[0] + ".img.gz"):
        # return 0 here as no img file exists and no single image means no image!
        return False

    # only gets to here if there was a hdr and an img file
    return True


def imcp(src, dest, logFile=None):

    # filename_src, file_extension_src = os.path.splitext(src)
    # filename_dst, file_extension_dst = os.path.splitext(dest)

    fileparts_src = mysplittext(src)
    fileparts_dst = mysplittext(dest)


    ext = ""
    if os.path.isfile(fileparts_src[0] + ".nii"):
        ext = ".nii"
    elif os.path.isfile(fileparts_src[0] + ".nii.gz"):
        ext = ".nii.gz"

    copyfile(fileparts_src[0] + ext, fileparts_dst[0] + ext)

    if logFile is not None:
        print("cp " + fileparts_src[0] + fileparts_src[1] + " " + fileparts_dst[0] + fileparts_dst[1], file=logFile)


def immv(src, dest, logFile=None):

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

    if logFile is not None:
        print("mv " + filename_src + ext + " " + filename_dst + ext, file=logFile)

    return True


def imrm(filelist, logFile=None):

    for file in filelist:
        fileparts = mysplittext(file)

        ext = ""
        if os.path.isfile(fileparts[0] + ".nii"):
            ext = ".nii"
        elif os.path.isfile(fileparts[0] + ".nii.gz"):
            ext = ".nii.gz"
        elif os.path.isfile(fileparts[0] + ".mgz"):
            ext = ".mgz"

        os.remove(fileparts[0] + ext)

        if logFile is not None:
            print("rm " + fileparts[0] + ext, file=logFile)

# extract header in xml format and returns it as a (possibly filtered by list_field) dictionary
def read_header(file, list_field=None):

    res             = rrun("fslhd -x " +  file)
    root            = ET.fromstring(res)
    attribs_dict    = root.attrib

    if list_field is not None:
        fields = dict()
        for f in list_field:
            fields[f] = attribs_dict[f]
        return fields
    else:
        return attribs_dict

# read header and calculate a dimension number hdr["nx"] * hdr["ny"] * hdr["nz"] * hdr["dx"] * hdr["dy"] * hdr["dz"]
def get_image_dimension(file):
    hdr = read_header(file)
    return int(hdr["nx"]) * int(hdr["ny"]) * int(hdr["nz"]) * float(hdr["dx"]) * float(hdr["dy"]) * float(hdr["dz"])


# return basename of given image (useful to return "image" from "image.nii.gz")
def remove_ext(img):
    return mysplittext(img)[0]

#===============================================================================================================================
# utilities
#===============================================================================================================================
# move a series of images defined by wildcard string ( e.g.   *fast*
def mass_images_move(wildcardsource, destdir, logFile=None):

    files = glob.glob(wildcardsource)

    images = []
    for f in files:
        if is_image(f) is True:
            images.append(f)

    for img in images:
        dest_file = os.path.join(destdir, os.path.basename(img))
        move(img, dest_file)
        if logFile is not None:
            print("mv " + img + " " + dest_file, file=logFile)


def is_image(file, img_formats=IMAGE_FORMATS):

    file_extension = mysplittext(file)[1]

    if file_extension in img_formats:
        return True
    else:
        return False


def quick_smooth(inimg, outimg, logFile=None):

    currpath    = os.path.dirname(inimg)
    vol16       = os.path.join(currpath, "vol16")

    rrun("fslmaths " + inimg + " -subsamp2 -subsamp2 -subsamp2 -subsamp2 " + vol16, logFile=logFile)
    rrun("flirt -in " + vol16 + " -ref " + inimg + " -out " + outimg + " -noresampblur -applyxfm -paddingsize 16", logFile=logFile)
    # possibly do a tiny extra smooth to $out here?
    imrm([vol16])

# get the whole extension  (e.g. abc.nii.gz => nii.gz )
def mysplittext(img):

    filepath = ntpath.dirname(img)
    filename = ntpath.basename(img)

    filename, fext = os.path.splitext(filename)

    fullext = fext
    while "." in filename:
        filename, fext = os.path.splitext(filename)
        fullext = fext + fullext

    return [os.path.join(filepath, filename), fullext]


def imgname(img):

    namepath = mysplittext(img)[0]
    return ntpath.basename(namepath)


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
