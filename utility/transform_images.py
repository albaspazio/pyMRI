import os

from myfsl.utils.run import rrun
from utility.images import imtest


# ======================================================================================================================
# LINEAR
# ======================================================================================================================
def flirt(omat, inimg, ref,
          params="-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear",
          logFile=None):
    if imtest(inimg) is False:
        print("ERROR in flirt: input image (" + inimg + ") is not valid....exiting")
        return

    if imtest(ref) is False:
        print("ERROR in flirt: ref image (" + ref + ") is not valid....exiting")
        return

    outdir = os.path.dirname(omat)
    if os.path.isdir(outdir) is False:
        print("ERROR in flirt, output dir (" + outdir + ") does not exist")

    rrun("flirt -in " + inimg + " -ref " + ref + " -omat " + omat + " " + params, logFile=logFile)


def check_flirt(omat, inimg, ref,
                params="-cost corratio -dof 12 -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -interp trilinear",
                logFile=None):
    if os.path.exists(omat) is False:
        flirt(omat, inimg, ref, params, logFile=logFile)


def check_invert_mat(omat, imat, logFile=None):
    if os.path.exists(omat) is False:
        if os.path.exists(imat) is False:
            raise Exception("ERROR in check_invert_mat, input mat (" + imat + ") does not exist")
        else:
            rrun("convert_xfm -inverse -omat " + omat + " " + imat, logFile=logFile)


def check_concat_mat(omat, imat1, imat2, logFile=None):
    if os.path.exists(omat) is False:
        if os.path.exists(imat1) is False or os.path.exists(imat2) is False:
            raise Exception(
                "ERROR in check_concat_mat, input mat1 (" + imat1 + ") or input mat2 (" + imat2 + ") does not exist")
        else:
            rrun("convert_xfm -omat " + omat + " -concat " + imat1 + " " + imat2, logFile=logFile)


def check_apply_mat(oimg, iimg, mat, ref, overwrite=False, logFile=None):
    if overwrite is True or imtest(oimg) is False:
        if imtest(iimg) is False or os.path.exists(mat) is False:
            raise Exception(
                "ERROR in chech_apply_mat, input inmage (" + iimg + ") or mat (" + mat + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("flirt -in " + iimg + " -ref " + ref + " -applyxfm -init " + mat + " -out " + oimg, logFile=logFile)


# ======================================================================================================================
# NON LINEAR
# ======================================================================================================================
def check_invert_warp(owarp, iwarp, ref, logFile=None):
    if imtest(owarp) is False:
        if imtest(iwarp) is False or imtest(ref) is False:
            raise Exception(
                "ERROR in check_invert_warp, input warp (" + iwarp + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("invwarp -r " + ref + " -w " + iwarp + " -o " + owarp, logFile=logFile)


# initial warp + midmat + final warp
def check_convert_warp_wmw(owarp, iwarp1, mat, iwarp2, ref, logFile=None):
    if imtest(owarp) is False:
        if imtest(iwarp1) is False or imtest(iwarp2) is False or os.path.exists(mat) is False or imtest(ref) is False:
            raise Exception(
                "ERROR in check_convert_warp_wmw, input warp1 (" + iwarp1 + ") or input warp2 (" + iwarp2 + ") or mid mat (" + mat + ") or ref (" + ref + ") does not exist")
        else:
            rrun(
                "convertwarp --ref=" + ref + " --warp1=" + iwarp1 + " --midmat=" + mat + " --warp2=" + iwarp2 + " --out=" + owarp,
                logFile=logFile)


# initial warp + final warp
def check_convert_warp_ww(owarp, iwarp1, iwarp2, ref, logFile=None):
    if imtest(owarp) is False:
        if imtest(iwarp1) is False or imtest(iwarp2) is False or imtest(ref) is False:
            raise Exception(
                "ERROR in check_convert_warp_wmw, input warp1 (" + iwarp1 + ") or input warp2 (" + iwarp2 + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --warp1=" + iwarp1 + " --warp2=" + iwarp2 + " --out=" + owarp,
                 logFile=logFile)


# initial mat + warp
def check_convert_warp_mw(owarp, premat, iwarp, ref, logFile=None):
    if imtest(owarp) is False:
        if imtest(iwarp) is False or os.path.exists(premat) is False or imtest(ref) is False:
            raise Exception(
                "ERROR in chech_convert_warp_mw, input warp (" + iwarp + ") or pre mat (" + premat + ") or ref (" + ref + ") does not exist")
        else:
            rrun("convertwarp --ref=" + ref + " --premat=" + premat + " --warp1=" + iwarp + " --out=" + owarp,
                 logFile=logFile)


def check_apply_warp(oimg, iimg, warp, ref, overwrite=False, logFile=None):
    if overwrite is True or imtest(oimg) is False or imtest(ref) is False:
        if imtest(iimg) is False or imtest(warp) is False:
            raise Exception(
                "ERROR in check_apply_warp, input image (" + iimg + ") or warp (" + warp + ") or ref img (" + ref + ") does not exist")
        else:
            rrun("applywarp -i " + iimg + " -r " + ref + " -o " + oimg + " --warp=" + warp, logFile=None)

# ======================================================================================================================
