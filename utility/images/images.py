import glob
import json
import os
from shutil import move

from utility.images.Image import Image
from utility.myfsl.utils.run import rrun

# ===============================================================================================================================
# FOLDERS, NAME, EXTENSIONS,
# ===============================================================================================================================
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


def mid_0based(nvol):

    if (nvol % 2) == 0:     # even      0,1,2,3 -> 2
        return nvol//2
    else:                   # odd       0,1,2   -> 1
        return nvol//2


def mid_1based(nvol):

    if (nvol % 2) == 0:     # even      1,2,3,4 -> 3
        return nvol//2 + 1
    else:                   # odd       1,2,3   -> 2
        return nvol//2 + 1



