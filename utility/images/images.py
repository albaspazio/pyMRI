import collections
import glob
import json
import os
from shutil import move

from utility.images.Image import Image
from utility.myfsl.utils.run import rrun

IMAGE_FORMATS = [".nii.gz", ".img.gz", ".mnc.gz", ".hdr.gz", ".hdr", ".mnc", ".img", ".nii", ".mgz", ".gii"]


# ===============================================================================================================================
# FOLDERS, NAME, EXTENSIONS,
# ===============================================================================================================================

# return [path/filename_noext, ext with point]
def img_split_ext(img, img_formats=IMAGE_FORMATS):
    fullext = ""
    for imgext in img_formats:
        if img.endswith(imgext):
            fullext = imgext  # [1:]
            break
    filename = img.replace(fullext, '')
    return [filename, fullext]


def add_postfix2name(img, postfix):
    filename, fullext = img_split_ext(img)  # ext contains the dot
    return filename + postfix + fullext


def add_prefix2name(img, prefix):
    filepath, fullext   = img_split_ext(img)  # ext contains the dot
    path                = os.path.dirname(filepath)
    filename            = os.path.basename(filepath)
    return os.path.join(path, prefix + filename + fullext)


# move a series of images defined by wildcard string ( e.g.   *fast*
def mass_images_move(wildcardsource, destdir, logFile=None):
    files = glob.glob(wildcardsource)

    images = []
    for f in files:
        f = Image(f)
        if f.is_image():
            if f.exist:
                images.append(f)

    for img in images:
        dest_file = os.path.join(destdir, os.path.basename(img))
        move(img, dest_file)
        if logFile is not None:
            print("mv " + img + " " + dest_file, file=logFile)

def immerge(out_img, premerge_labels=None):
    seq_string = " "

    if premerge_labels is None:
        seq_string = "./*"
    elif isinstance(premerge_labels, str):
        seq_string = premerge_labels + "*"
    elif isinstance(premerge_labels, collections.Sequence):
        for seq in premerge_labels:
            seq_string = seq_string + out_img + "_" + seq + " "
    else:
        print("Error in immerge, given premerge_labels is not in a correct format")
        return

    os.system("fslmerge -t " + out_img + " " + seq_string)
    # rrun("fslmerge -t " + out_img + " " + seq_string)


# divide the tbss mean skeleton in images according to a given atlas file (where each volume is specific tract)
# needs that atlas has its own json file
# and save to "mean_skeleton" subfolder of atlas folder
def mask_tbss_skeleton_volumes_atlas(skel_templ, atlas_img, atlas_json):

    atlas_dir = os.path.dirname(atlas_img)

    out_dir = os.path.join(atlas_dir, "mean_skeleton")
    os.makedirs(out_dir, exist_ok=True)

    with open(atlas_json) as json_file:
        datas = json.load(json_file)

    temp_name = os.path.basename(skel_templ)

    cnt = 1
    for roi in datas["data"]:
        tempmask  = Image(os.path.join(out_dir, roi["lab"] + "_mask"))
        finalmask = os.path.join(out_dir, temp_name + "_" + roi["lab"] + "_mask")

        rrun("fslmaths " + atlas_img + " -thr " + str(cnt) + " -uthr " + str(cnt) + " -bin " + tempmask)
        rrun("fslmaths " + skel_templ + " -mas " + tempmask + " -bin " + finalmask)

        tempmask.rm()
        cnt = cnt + 1


# divide the tbss mean skeleton in images according to a given atlas folder
# each file is a specific tract and its name define its label, no need for a json file
# and save to "mean_skeleton" subfolder of atlas folder
def mask_tbss_skeleton_folder_atlas(skel_templ, atlas_dir, thr=0.95):
    out_dir = os.path.join(atlas_dir, "mean_skeleton")
    os.makedirs(out_dir, exist_ok=True)

    temp_name = os.path.basename(skel_templ)

    files = glob.glob(atlas_dir + "/*")

    for f in files:
        f = Image(f)

        if not f.exist:
            continue

        tempmask    = Image(os.path.join(out_dir, f.name + "_mask"))
        finalmask   = os.path.join(out_dir, temp_name + "_" + f.name + "_mask")

        rrun("fslmaths " + f + " -thr " + str(thr) + " -bin " + tempmask)
        rrun("fslmaths " + skel_templ + " -mas " + tempmask + " -bin " + finalmask)

        tempmask.rm()





