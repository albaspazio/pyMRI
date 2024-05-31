import os

from utility.images.Image import Image
from utility.myfsl.utils.run import rrun


# ======================================================================================================================
# LINEAR
# ======================================================================================================================
def flirt(omat, inimg, ref,
          params:str="-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear",
          logFile=None):
    """
    Runs FLIRT to calculate the optimal linear transformation between an input image and a reference image.

    Args:
        omat (str): path to the output transformation matrix
        inimg (str): path to the input image
        ref (str): path to the reference image
        params (str, optional): FLIRT parameters. Defaults to "-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear".
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input image or reference image is not valid

    Returns:
        None

    """
    inimg   = Image(inimg, must_exist=True, msg="ERROR in flirt: input image is not valid")
    ref     = Image(ref, must_exist=True, msg="ERROR in flirt: ref image is not valid")

    outdir  = os.path.dirname(omat)
    if not os.path.isdir(outdir):
        raise Exception("ERROR in flirt, output dir (" + outdir + ") does not exist")

    rrun("flirt -in " + inimg + " -ref " + ref + " -omat " + omat + " " + params, logFile=logFile)


def check_flirt(omat, inimg, ref, params="-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear",
                overwrite=False, logFile=None):
    """
    Check if the output transformation matrix exists, and if not, run FLIRT to create it.

    Args:
        omat (str): path to the output transformation matrix
        inimg (str): path to the input image
        ref (str): path to the reference image
        params (str, optional): FLIRT parameters. Defaults to "-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear".
        overwrite (bool, optional): whether to overwrite the output transformation matrix if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input image or reference image is not valid

    Returns:
        None

    """
    if not os.path.exists(omat) or overwrite:
        inimg   = Image(inimg, must_exist=True, msg="ERROR in flirt: input image is not valid")
        ref     = Image(ref, must_exist=True, msg="ERROR in flirt: ref image is not valid")

        outdir  = os.path.dirname(omat)
        if not os.path.isdir(outdir):
            raise Exception("ERROR in flirt, output dir (" + outdir + ") does not exist")

        rrun("flirt -in " + inimg + " -ref " + ref + " -omat " + omat + " " + params, logFile=logFile)


def check_invert_mat(omat: str, imat: str, overwrite: bool = False, logFile: str = None) -> None:
    """
    Check if the output transformation matrix exists, and if not, invert an input transformation matrix.

    Args:
        omat (str): path to the output transformation matrix
        imat (str): path to the input transformation matrix
        overwrite (bool, optional): whether to overwrite the output transformation matrix if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input transformation matrix does not exist

    Returns:
        None

    """
    if not os.path.exists(omat) or overwrite:
        if not os.path.exists(imat):
            raise Exception("ERROR in check_invert_mat, input mat (" + imat + ") does not exist")
        else:
            outdir = os.path.dirname(omat)
            if not os.path.isdir(outdir):
                raise Exception("ERROR in flirt, output dir (" + outdir + ") does not exist")

            rrun("convert_xfm -inverse -omat " + omat + " " + imat, logFile=logFile)


def check_concat_mat(omat, imat1, imat2, overwrite=False, logFile=None):
    """
    Check if the output transformation matrix exists, and if not, concatenate two input transformation matrices.

    Args:
        omat (str): path to the output transformation matrix
        imat1 (str): path to the first input transformation matrix
        imat2 (str): path to the second input transformation matrix
        overwrite (bool, optional): whether to overwrite the output transformation matrix if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input transformation matrices do not exist

    Returns:
        None

    """
    if not os.path.exists(omat) or overwrite:
        if not os.path.exists(imat1) or not os.path.exists(imat2):
            raise Exception("ERROR in check_concat_mat, input mat1 (" + imat1 + ") or input mat2 (" + imat2 + ") does not exist")
        else:
            outdir = os.path.dirname(omat)
            if not os.path.isdir(outdir):
                raise Exception("ERROR in flirt, output dir (" + outdir + ") does not exist")

            rrun("convert_xfm -omat " + omat + " -concat " + imat1 + " " + imat2, logFile=logFile)


def check_apply_mat(oimg, iimg, mat, ref, overwrite=False, logFile=None):
    """
    Check if the output image exists, and if not, apply a transformation matrix to an input image.

    Args:
        oimg (str): path to the output image
        iimg (str): path to the input image
        mat (str): path to the transformation matrix
        ref (str): path to the reference image
        overwrite (bool, optional): whether to overwrite the output image if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input image, transformation matrix, or reference image does not exist

    Returns:
        None

    """
    if not Image(oimg).exist or overwrite:
        if not Image(iimg).exist or not os.path.exists(mat):
            raise Exception("ERROR in chech_apply_mat, input inmage (" + iimg + ") or mat (" + mat + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("flirt -in " + iimg + " -ref " + ref + " -applyxfm -init " + mat + " -out " + oimg, logFile=logFile)


# ======================================================================================================================
# NON LINEAR
# ======================================================================================================================
def check_invert_warp(owarp, iwarp, ref, overwrite=False, logFile=None):
    """
    Check if the output warp file exists, and if not, invert a warp file.

    Args:
        owarp (str): path to the output warp file
        iwarp (str): path to the input warp file
        ref (str): path to the reference image
        overwrite (bool, optional): whether to overwrite the output warp file if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input warp file or reference image does not exist

    Returns:
        None

    """
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp).exist or not Image(ref).exist:
            raise Exception("ERROR in check_invert_warp, input warp (" + iwarp + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("invwarp -r " + ref + " -w " + iwarp + " -o " + owarp, logFile=logFile)


# initial warp + midmat + final warp
def check_convert_warp_wmw(owarp, iwarp1, mat, iwarp2, ref, overwrite=False, logFile=None):
    """
    Check if the output warp file exists, and if not, convert a warp file using a pre-defined transformation matrix.

    Args:
        owarp (str): path to the output warp file
        iwarp1 (str): path to the input warp file
        iwarp2 (str): path to the input warp file
        ref (str): path to the reference image
        overwrite (bool, optional): whether to overwrite the output warp file if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input warp file, pre-defined transformation matrix, or reference image does not exist

    Returns:
        None

    """
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp1).exist or not Image(iwarp2).exist or not os.path.exists(mat) or not Image(ref).exist:
            raise Exception("ERROR in check_convert_warp_wmw, input warp1 (" + iwarp1 + ") or input warp2 (" + iwarp2 + ") or mid mat (" + mat + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --warp1=" + iwarp1 + " --midmat=" + mat + " --warp2=" + iwarp2 + " --out=" + owarp, logFile=logFile)


# initial warp + final warp
def check_convert_warp_ww(owarp: str, iwarp1: str, iwarp2: str, ref: str, overwrite: bool = False, logFile: str = None) -> None:
    """
    Check if the output warp file exists, and if not, convert a warp file using a pre-defined transformation matrix.

    Args:
        owarp (str): path to the output warp file
        iwarp1 (str): path to the input warp file
        iwarp2 (str): path to the input warp file
        ref (str): path to the reference image
        overwrite (bool, optional): whether to overwrite the output warp file if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input warp file, pre-defined transformation matrix, or reference image does not exist

    Returns:
        None

    """
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp1).exist or not Image(iwarp2).exist or not Image(ref).exist:
            raise Exception("ERROR in check_convert_warp_wmw, input warp1 (" + iwarp1 + ") or input warp2 (" + iwarp2 + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --warp1=" + iwarp1 + " --warp2=" + iwarp2 + " --out=" + owarp, logFile=logFile)


# initial mat + warp
def check_convert_warp_mw(owarp, premat, iwarp, ref, overwrite=False, logFile=None):
    """
    Check if the output warp file exists, and if not, convert a warp file using a pre-defined transformation matrix.

    Args:
        owarp (str): path to the output warp file
        premat (str): path to the pre-defined transformation matrix
        iwarp (str): path to the input warp file
        ref (str): path to the reference image
        overwrite (bool, optional): whether to overwrite the output warp file if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input warp file, pre-defined transformation matrix, or reference image does not exist

    Returns:
        None

    """
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp).exist or not os.path.exists(premat) or not Image(ref).exist:
            raise Exception("ERROR in check_convert_warp_mw, input warp (" + iwarp + ") or pre mat (" + premat + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --premat=" + premat + " --warp1=" + iwarp + " --out=" + owarp, logFile=logFile)


def check_apply_warp(oimg, iimg, warp, ref, overwrite=False, logFile=None):
    """
    Check if the output image exists, and if not, apply a warp to an input image.

    Args:
        oimg (str): path to the output image
        iimg (str): path to the input image
        warp (str): path to the warp file
        ref (str): path to the reference image
        overwrite (bool, optional): whether to overwrite the output image if it already exists. Defaults to False.
        logFile (str, optional): path to the log file. Defaults to None.

    Raises:
        Exception: if the input image, warp, or reference image does not exist

    Returns:
        None

    """
    if not Image(oimg).exist or overwrite:
        if not Image(iimg).exist or not Image(warp).exist or not Image(ref).exist:
            raise Exception("ERROR in check_apply_warp, input image (" + iimg + ") or warp (" + warp + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("applywarp -i " + iimg + " -r " + ref + " -o " + oimg + " --warp=" + warp, logFile=logFile)

# ======================================================================================================================
