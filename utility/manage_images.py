import ntpath
import os
import glob
from shutil import copyfile, move
import xml.etree.ElementTree as ET

from myfsl.utils.run import rrun

IMAGE_FORMATS = [".nii.gz", ".img.gz", ".mnc.gz", ".hdr.gz", ".hdr", ".mnc", ".img", ".nii", ".mgz"]
#===============================================================================================================================
# FOLDERS, NAME, EXTENSIONS,
#===============================================================================================================================


# get the whole extension  (e.g. abc.nii.gz => nii.gz )
def img_split_ext(img, img_formats=IMAGE_FORMATS):

    fullext = ""
    for imgext in img_formats:
        if img.endswith(imgext):
            fullext = imgext #[1:]
            break
    filename = img.replace(fullext, '')
    return [filename, fullext]


def imgparts(img):

    if os.path.isdir(img):
        return [img, "", ""]

    parts = img_split_ext(img)
    return [ntpath.dirname(parts[0]), ntpath.basename(parts[0]), parts[1]]


def imgname(img):

    namepath = img_split_ext(img)[0]
    return ntpath.basename(namepath)


def imgdir(img):

    namepath = img_split_ext(img)[0]
    return ntpath.dirname(namepath)


# return basename of given image (useful to return "image" from "image.nii.gz")
def remove_ext(img):
    return img_split_ext(img)[0]

# ===========================================================================================================
# EXIST, COPY, REMOVE, MOVE, MASS MOVE
# ===========================================================================================================

# return False if no image exists or True if the image exists
def imtest(image_path):

    if image_path == "":
        return False

    fileparts = img_split_ext(image_path)

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

    fileparts_src = img_split_ext(src)
    fileparts_dst = img_split_ext(dest)

    if os.path.isdir(dest) is True:
        fileparts_dst[0] = os.path.join(dest, imgname(fileparts_src[0]))    # dest dir + source filename
    else:
        fileparts_dst = img_split_ext(dest)

    ext = ""
    if os.path.isfile(fileparts_src[0] + ".nii"):
        ext = ".nii"
    elif os.path.isfile(fileparts_src[0] + ".nii.gz"):
        ext = ".nii.gz"

    dest_ext = fileparts_dst[1]
    if dest_ext == "":
        dest_ext = ext

    copyfile(fileparts_src[0] + ext, fileparts_dst[0] + dest_ext)

    if logFile is not None:
        print("cp " + fileparts_src[0] + ext + " " + fileparts_dst[0] + dest_ext, file=logFile)


def imcp_notexisting(src, dest, logFile=None):

    if imtest(dest) is False:
        imcp(src, dest, logFile)


def imrm(filelist, logFile=None):

    for file in filelist:
        fileparts = img_split_ext(file)

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

#===============================================================================================================================
# utilities
#===============================================================================================================================


def quick_smooth(inimg, outimg, logFile=None):

    currpath    = os.path.dirname(inimg)
    vol16       = os.path.join(currpath, "vol16")

    rrun("fslmaths " + inimg + " -subsamp2 -subsamp2 -subsamp2 -subsamp2 " + vol16, logFile=logFile)
    rrun("flirt -in " + vol16 + " -ref " + inimg + " -out " + outimg + " -noresampblur -applyxfm -paddingsize 16", logFile=logFile)
    # possibly do a tiny extra smooth to $out here?
    imrm([vol16])


# TODO: patched to deal with X dots + .nii.gz...fix it definitively !!
def is_image(file, img_formats=IMAGE_FORMATS):

    # preserve only the last two dots (those relating to ".nii.gz")
    num_dot = file.count(".")
    if num_dot > 2:
        file = file.replace(".", "", num_dot-2)
    file_extension = img_split_ext(file, img_formats)[1]

    if file_extension in img_formats:
        return True
    else:
        return False


# read header and calculate a dimension number hdr["nx"] * hdr["ny"] * hdr["nz"] * hdr["dx"] * hdr["dy"] * hdr["dz"]
def get_image_dimension(file):
    hdr = read_header(file)
    return int(hdr["nx"]) * int(hdr["ny"]) * int(hdr["nz"]) * float(hdr["dx"]) * float(hdr["dy"]) * float(hdr["dz"])


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

