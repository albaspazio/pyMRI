import os

from utility.images.Image import Image
from utility.myfsl.utils.run import rrun

# ======================================================================================================================
# LINEAR
# ======================================================================================================================
def flirt(omat, inimg, ref,
          params="-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear",
          logFile=None):
    if not Image(inimg).exist:
        print("ERROR in flirt: input image (" + inimg + ") is not valid....exiting")
        return

    if not Image(ref).exist:
        print("ERROR in flirt: ref image (" + ref + ") is not valid....exiting")
        return

    outdir = os.path.dirname(omat)
    if not os.path.isdir(outdir):
        print("ERROR in flirt, output dir (" + outdir + ") does not exist")

    rrun("flirt -in " + inimg + " -ref " + ref + " -omat " + omat + " " + params, logFile=logFile)


def check_flirt(omat, inimg, ref,
                params="-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear",
                overwrite=False, logFile=None):
    if not os.path.exists(omat) or overwrite:
        flirt(omat, inimg, ref, params, logFile=logFile)


def check_invert_mat(omat, imat, overwrite=False, logFile=None):
    if not os.path.exists(omat) or overwrite:
        if not os.path.exists(imat):
            raise Exception("ERROR in check_invert_mat, input mat (" + imat + ") does not exist")
        else:
            rrun("convert_xfm -inverse -omat " + omat + " " + imat, logFile=logFile)


def check_concat_mat(omat, imat1, imat2, overwrite=False, logFile=None):
    if not os.path.exists(omat) or overwrite:
        if not os.path.exists(imat1) or not os.path.exists(imat2):
            raise Exception("ERROR in check_concat_mat, input mat1 (" + imat1 + ") or input mat2 (" + imat2 + ") does not exist")
        else:
            rrun("convert_xfm -omat " + omat + " -concat " + imat1 + " " + imat2, logFile=logFile)


def check_apply_mat(oimg, iimg, mat, ref, overwrite=False, logFile=None):
    if not Image(oimg).exist or overwrite:
        if not Image(iimg).exist or not os.path.exists(mat):
            raise Exception("ERROR in chech_apply_mat, input inmage (" + iimg + ") or mat (" + mat + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("flirt -in " + iimg + " -ref " + ref + " -applyxfm -init " + mat + " -out " + oimg, logFile=logFile)


# ======================================================================================================================
# NON LINEAR
# ======================================================================================================================
def check_invert_warp(owarp, iwarp, ref, overwrite=False, logFile=None):
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp).exist or not Image(ref).exist:
            raise Exception("ERROR in check_invert_warp, input warp (" + iwarp + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("invwarp -r " + ref + " -w " + iwarp + " -o " + owarp, logFile=logFile)


# initial warp + midmat + final warp
def check_convert_warp_wmw(owarp, iwarp1, mat, iwarp2, ref, overwrite=False, logFile=None):
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp1).exist or not Image(iwarp2).exist or not os.path.exists(mat) or not Image(ref).exist:
            raise Exception("ERROR in check_convert_warp_wmw, input warp1 (" + iwarp1 + ") or input warp2 (" + iwarp2 + ") or mid mat (" + mat + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --warp1=" + iwarp1 + " --midmat=" + mat + " --warp2=" + iwarp2 + " --out=" + owarp, logFile=logFile)


# initial warp + final warp
def check_convert_warp_ww(owarp, iwarp1, iwarp2, ref, overwrite=False, logFile=None):
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp1).exist or not Image(iwarp2).exist or not Image(ref).exist:
            raise Exception("ERROR in check_convert_warp_wmw, input warp1 (" + iwarp1 + ") or input warp2 (" + iwarp2 + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --warp1=" + iwarp1 + " --warp2=" + iwarp2 + " --out=" + owarp, logFile=logFile)


# initial mat + warp
def check_convert_warp_mw(owarp, premat, iwarp, ref, overwrite=False, logFile=None):
    if not Image(owarp).exist or overwrite:
        if not Image(iwarp).exist or not os.path.exists(premat) or not Image(ref).exist:
            raise Exception("ERROR in chech_convert_warp_mw, input warp (" + iwarp + ") or pre mat (" + premat + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --premat=" + premat + " --warp1=" + iwarp + " --out=" + owarp, logFile=logFile)


def check_apply_warp(oimg, iimg, warp, ref, overwrite=False, logFile=None):
    if not Image(oimg).exist or overwrite:
        if not Image(iimg).exist or not Image(warp).exist or not Image(ref).exist:
            raise Exception("ERROR in check_apply_warp, input image (" + iimg + ") or warp (" + warp + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("applywarp -i " + iimg + " -r " + ref + " -o " + oimg + " --warp=" + warp, logFile=logFile)

# ======================================================================================================================
