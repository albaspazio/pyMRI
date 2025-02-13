import glob
import json
import os
from shutil import move

from myutility.images.Image import Image
from myutility.myfsl.utils.run import rrun
from myutility.utilities import fillnumber2fourdigits


# ===============================================================================================================================
# FOLDERS, NAME, EXTENSIONS,
# ===============================================================================================================================
# move a series of images defined by wildcard string ( e.g.   *fast*
def mass_images_move(wildcardsource: str, destdir: str, logFile=None) -> None:
    """
    move a series of images defined by wildcard string ( e.g.   *fast*
    Args:
        wildcardsource (str): a string containing a wildcard pattern to match files
        destdir (str): the destination directory
        logFile (optional, default=None): a file-like object to write log messages to
    Returns:
        None
    """
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
            print(f"mv {img} {dest_file}", file=logFile)


def mask_tbss_skeleton_volumes_atlas(skel_templ: str, atlas_img: str, atlas_json: str) -> None:
    """
    divide the tbss mean skeleton in images according to a given atlas file (where each volume is specific tract)
    needs that atlas has its own json file
    and save to "mean_skeleton" subfolder of atlas folder
    Args:
        skel_templ (str): the path to the mean skeleton template
        atlas_img (str): the path to the atlas image
        atlas_json (str): the path to the atlas json file
    Returns:
        None
    """
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

        rrun(f"fslmaths {atlas_img} -thr {cnt} -uthr {cnt} -bin {tempmask}")
        rrun(f"fslmaths {skel_templ} -mas {tempmask} -bin {finalmask}")

        tempmask.rm()
        cnt = cnt + 1


def mask_tbss_skeleton_folder_atlas(skel_templ: str, atlas_dir: str, thr: float = 0.95) -> None:
    """
    divide the tbss mean skeleton in images according to a given atlas folder
    each file is a specific tract and its name define its label, no need for a json file
    and save to "mean_skeleton" subfolder of atlas folder
    Args:
        skel_templ (str): the path to the mean skeleton template
        atlas_dir (str): the path to the atlas folder
        thr (float, optional): the threshold value for binarizing the atlas images. Defaults to 0.95.
    Returns:
        None
    """
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

        rrun(f"fslmaths {f} -thr {thr} -bin {tempmask}")
        rrun(f"fslmaths {skel_templ} -mas {tempmask} -bin {finalmask}")

        tempmask.rm()


def mid_0based(nvol: int) -> int:
    """
    Return the index of the middle volume (zero-based)
    Args:
        nvol (int): the number of volumes
    Returns:
        int: the index of the middle volume
    """
    if (nvol % 2) == 0:     # even      0,1,2,3 -> 2
        return nvol//2
    else:                   # odd       0,1,2   -> 1
        return nvol//2


def mid_1based(nvol: int) -> int:
    """
    Return the index of the middle volume (one-based)
    Args:
        nvol (int): the number of volumes
    Returns:
        int: the index of the middle volume
    """
    if (nvol % 2) == 0:     # even      1,2,3,4 -> 3
        return nvol//2 + 1
    else:                   # odd       1,2,3   -> 2
        return nvol//2 + 1


def remove_volumes_from_4D(inimg: str, vols2rem0based: list, outname: str) -> None:
    """
    Remove a list of i-th volumes (zero-based) from a 4D image and save a new image
    Args:
        inimg (str): the path to the input 4D image
        vols2rem0based (list): a list of indices of volumes to remove (zero-based)
        outname (str): the path to the output image
    Returns:
        None
    """
    inimg = Image(inimg)
    indir = inimg.dir
    temp_dir = os.path.join(indir, "TEMPXXXX")
    os.makedirs(temp_dir, exist_ok=True)

    tempimg = inimg.cp(temp_dir)

    curr_dir = os.getcwd()
    os.chdir(temp_dir)

    rrun(f"fslsplit {tempimg} TEMP")

    for v in vols2rem0based:
        Image(os.path.join(temp_dir, "TEMP" + fillnumber2fourdigits(v))).rm()

    # join remaining volumes
    rrun(f"fslmerge -t {outname} TEMP*")

    os.chdir(curr_dir)