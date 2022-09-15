import ntpath
import os
import shutil
from shutil import move, copyfile
import xml.etree.ElementTree as ET
import collections

# https://stackoverflow.com/questions/30045106/python-how-to-extend-str-and-overload-its-constructor
from utility.exceptions import NotExistingImageException
from utility.myfsl.utils.run import rrun
from utility.utilities import compress, gunzip, fillnumber2fourdigits


class Image(str):

    IMAGE_FORMATS = [".nii.gz", ".img.gz", ".mnc.gz", ".hdr.gz", ".hdr", ".mnc", ".img", ".nii", ".mgz", ".gii"]

    def __new__(cls, value, must_exist=False, msg=""):
        return super(Image, cls).__new__(cls, value)

    def __init__(self, value, must_exist=False, msg=""):

        if value != "":
            parts = self.imgparts()

            self.dir        = parts[0]
            self.name       = parts[1]      # name NO EXTENSION !!!!!!
            self.ext        = parts[2]
            self.fpathnoext = os.path.join(self.dir, self.name)
            self.is_dir     = os.path.isdir(self)

            if must_exist and not self.exist:
                raise NotExistingImageException(msg, self)
            return

        if msg == "":
            msg = "Given Image path is empty"

        raise NotExistingImageException(msg, self)

    @property
    def exist(self):
        return self.imtest()

    @property
    def uexist(self):
        return self.uimtest()

    @property
    def cexist(self):
        return self.cimtest()

    @property
    def upath(self):
        return Image(self.fpathnoext + ".nii")

    @property
    def cpath(self):
        return Image(self.fpathnoext + ".nii.gz")

    @property
    def nslices(self):
        return self.getnslices()

    @property
    def nvols(self):
        return self.getnvol()

    @property
    def TR(self):
        return self.get_tr()

    # ===============================================================================================================================
    # FOLDERS, NAME, EXTENSIONS,
    # ===============================================================================================================================
    # get the whole extension  (e.g. abc.nii.gz => nii.gz )
    # return [path/filename_noext, ext]
    def split_ext(self, img_formats=None):

        if img_formats is None:
            img_formats = self.IMAGE_FORMATS
        fullext = ""
        for imgext in img_formats:
            if self.endswith(imgext):
                fullext = imgext  # [1:]
                break
        filename = self.replace(fullext, '')
        return [filename, fullext]

    # suitable for images (with double extension e.g.: /a/b/c/name.nii.gz)
    # return [folder, filename, ext]
    def imgparts(self):
        if os.path.isdir(self):
            return [self, "", ""]

        parts = self.split_ext()
        return [ntpath.dirname(parts[0]), ntpath.basename(parts[0]), parts[1]]

    # return imgname_noext
    def imgname(self):
        namepath = self.split_ext()[0]
        return ntpath.basename(namepath)

    def imgdir(self):
        namepath = self.split_ext()[0]
        return ntpath.dirname(namepath)

    # return basename of given image (useful to return "image" from "image.nii.gz")
    def remove_image_ext(self):
        return self.split_ext()[0]

    # ===========================================================================================================
    # EXIST, COPY, REMOVE, MOVE, MASS MOVE
    # ===========================================================================================================

    # return False if neither compressed nor uncompressed images exist or True if either compressed or uncompressed image exists
    def imtest(self):
        # if self == "":
        #     return False

        if os.path.isfile(self.upath) or os.path.isfile(self.cpath) or os.path.isfile(self.fpathnoext + ".mgz"):
            return True

        if os.path.isfile(self.fpathnoext + ".mnc") or os.path.isfile(self.fpathnoext + ".mnc.gz"):
            return True

        if os.path.isfile(self.fpathnoext + ".gii"):
            return True

        if not os.path.isfile(self.fpathnoext + ".hdr") and not os.path.isfile(self.fpathnoext + ".hdr.gz"):
            # return 0 here as no header exists and no single image means no image!
            return False

        if not os.path.isfile(self.fpathnoext + ".img") and not os.path.isfile(self.fpathnoext + ".img.gz"):
            # return 0 here as no img file exists and no single image means no image!
            return False

        # only gets to here if there was a hdr and an img file
        return True

    # return False if compressed image does not exist or True if compressed image exists
    def cimtest(self):
        # if self == "":
        #     return False

        if os.path.isfile(self.cpath):
            return True

        if os.path.isfile(self.fpathnoext + ".mnc.gz"):
            return True

        if os.path.isfile(self.fpathnoext + ".gii"):
            return True

        if not os.path.isfile(self.fpathnoext + ".hdr.gz"):
            # return 0 here as no header exists and no single image means no image!
            return False

        if not os.path.isfile(self.fpathnoext + ".img.gz"):
            # return 0 here as no img file exists and no single image means no image!
            return False

        # only gets to here if there was a hdr and an img file
        return True

    # return False if uncompressed image does not exist or True if uncompressed image exists
    def uimtest(self):
        # if self == "":
        #     return False

        if os.path.isfile(self.upath):
            return True

        if os.path.isfile(self.fpathnoext + ".mnc"):
            return True

        if os.path.isfile(self.fpathnoext + ".gii"):
            return True

        if not os.path.isfile(self.fpathnoext + ".hdr"):
            # return 0 here as no header exists and no single image means no image!
            return False

        if not os.path.isfile(self.fpathnoext + ".img"):
            # return 0 here as no img file exists and no single image means no image!
            return False

        # only gets to here if there was a hdr and an img file
        return True

    def cp(self, dest, error_src_not_exist=True, logFile=None):

        if not self.exist:
            if error_src_not_exist:
                print("ERROR in cp. src image (" + self + ") does not exist")
                return
            else:
                print("WARNING in cp. src image (" + self + ") does not exist, skip copy and continue")

        ext = ""
        if os.path.isfile(self.upath):
            ext = ".nii"
        elif os.path.isfile(self.cpath):
            ext = ".nii.gz"

        dest            = Image(dest)
        fileparts_dst   = dest.split_ext()

        if dest.is_dir:
            fileparts_dst[0] = os.path.join(dest, self.name)  # dest dir + source filename
        else:
            fileparts_dst[0] = dest.fpathnoext

        dest_ext = fileparts_dst[1]
        if dest_ext == "":
            dest_ext = ext

        copyfile(self.fpathnoext + ext, fileparts_dst[0] + dest_ext)

        if logFile is not None:
            print("cp " + self.fpathnoext + ext + " " + fileparts_dst[0] + dest_ext, file=logFile)

    def cp_notexisting(self, dest, error_src_not_exist=False, logFile=None):

        if not self.exist and error_src_not_exist:
            raise NotExistingImageException("Image.cp_notexisting", self)

        dest = Image(dest)

        if not dest.exist:
            self.cp(dest, logFile)

    def mv(self, dest, error_src_not_exist=False, logFile=None):

        if not self.exist:
            if error_src_not_exist:
                print("ERROR in mv. src image (" + self + ") does not exist")
                return
            else:
                print("WARNING in mv. src image (" + self + ") does not exist, skip copy and continue")

        ext = ""
        if os.path.isfile(self.upath):
            ext = ".nii"
        elif os.path.isfile(self.cpath):
            ext = ".nii.gz"
        elif os.path.isfile(self.fpathnoext + ".gii"):
            ext = ".gii"

        if ext == "":
            return False

        dest = Image(dest)
        move(self.fpathnoext + ext, dest.fpathnoext + ext)

        if logFile is not None:
            print("mv " + self.fpathnoext + ext + " " + dest.fpathnoext + ext, file=logFile)

        return True

    def rm(self, logFile=None):

        if not self.exist:
            return 
        
        if self.ext == "":
            # delete all the existing ones
            if os.path.isfile(self.upath):
                os.remove(self.upath)
                
            if os.path.isfile(self.cpath):
                os.remove(self.cpath)

            if os.path.isfile(self.fpathnoext + ".mgz"):
                os.remove(self.fpathnoext + ".mgz")

            if os.path.isfile(self.fpathnoext + ".gii"):
                os.remove(self.fpathnoext + ".gii")

        else:
            # delete only the version with the given extension
            os.remove(self.fpathnoext + self.ext)

        if logFile is not None:
            print("rm " + self.fpathnoext, file=logFile)

    # ===============================================================================================================================
    # utilities
    # ===============================================================================================================================
    def getnvol(self):
        return int(rrun("fslnvols " + self).split('\n')[0])

    def get_nvoxels(self):
        return int(rrun("fslstats " + self + " -V").strip().split(" ")[0])

    def getnslices(self):
        return int(rrun("fslval " + self + " dim3"))

    def get_image_volume(self):
        return int(rrun("fslstats " + self + " -V").strip().split(" ")[1])

    def get_image_mean(self):
        return float(rrun("fslstats " + self + " -M").strip())

    def mask_image(self, mask, out):
        rrun("fslmaths " + self + " -mas " + mask + " " + out)

    def imsplit(self, templabel=None, subdirmame=""):

        if templabel is None:
            label = self.name
        else:
            label = templabel

        currdir = os.getcwd()
        outdir = os.path.join(self.dir, subdirmame)
        os.makedirs(outdir, exist_ok=True)
        os.chdir(outdir)
        rrun('fslsplit ' + self + " " + label + " -t")
        os.chdir(currdir)
        return outdir,  label

    def quick_smooth(self, outimg=None, logFile=None):

        if outimg is None:
            outimg = self

        currpath    = os.path.dirname(self)
        vol16       = Image(os.path.join(currpath, "vol16"))

        rrun("fslmaths " + self + " -subsamp2 -subsamp2 -subsamp2 -subsamp2 " + vol16, logFile=logFile)
        rrun("flirt -in " + vol16 + " -ref " + self + " -out " + outimg + " -noresampblur -applyxfm -paddingsize 16", logFile=logFile)
        # possibly do a tiny extra smooth to $out here?
        vol16.rm()

    # TODO: patched to deal with X dots + .nii.gz...fix it definitively !!
    def is_image(self, img_formats=None):

        if img_formats is None:
            img_formats = self.IMAGE_FORMATS

        temp = Image(self)
        # preserve only the last two dots (those relating to ".nii.gz")
        num_dot = temp.count(".")
        if num_dot > 2:
            temp = Image(temp.replace(".", "", num_dot - 2))
        file_extension = temp.split_ext(img_formats)[1]

        if file_extension in img_formats:
            return True
        else:
            return False

    def get_head_from_brain(self, checkexist=True):
        if not self.exist:
            err = "Error in get_head_from_brain: given img is not an image"
            print(err)
            raise Exception(err)

        str_ = str(self)

        headimg = Image(str_.replace("_brain", ""))
        if not headimg.exist and checkexist:
            err = "Error in get_head_from_brain: head image is not present"
            print(err)
            raise Exception(err)
        else:
            return headimg

    # read header and calculate a dimension number hdr["nx"] * hdr["ny"] * hdr["nz"] * hdr["dx"] * hdr["dy"] * hdr["dz"]
    def get_image_dimension(self):
        hdr = self.read_header()
        return int(hdr["nx"]) * int(hdr["ny"]) * int(hdr["nz"]) * float(hdr["dx"]) * float(hdr["dy"]) * float(hdr["dz"])

    def get_tr(self):
        return float(rrun('fslval ' + self + ' pixdim4'))

    # extract header in xml format and returns it as a (possibly filtered by list_field) dictionary
    def read_header(self, list_field=None):

        res             = rrun("fslhd -x " + self)
        root            = ET.fromstring(res)
        attribs_dict    = root.attrib

        if list_field is not None:
            fields = dict()
            for f in list_field:
                fields[f] = attribs_dict[f]
            return fields
        else:
            return attribs_dict

    # remove numslice2remove up and down (fslroi wants, for each dimension, first slice to keep and number of slices to keep)
    def remove_slices(self, numslice2remove=1, whichslices2remove="updown", remove_dimension="axial"):

        nslices = int(rrun("fslval " + self + " dim3"))
        if remove_dimension == "axial":
            if whichslices2remove == "updown":
                dim_str = " 0 -1 0 -1 " + str(numslice2remove) + " " + str(nslices - 2*numslice2remove)
            else:
                print("ERROR in remove_slices, presently it removes only in the axial (z) dimension") # TODO
                return
                # dim_str = " 0 -1 0 -1 " + "0 " + str(numslice2remove) + " " + str(nslices - 2 * numslice2remove)
        else:
            print("ERROR in remove_slices, presently it removes only in the axial (z) dimension")
            return

        self.cp(self.fpathnoext + "_full")
        rrun('fslroi ' + self + " " + self + dim_str)

    def compress(self, dest=None, replace=True):
        if dest is None:
            udest   = self.cpath
        else:
            udest = Image(dest).cpath

        compress(self.upath, udest, replace)

    # unzip file to a given path, preserving (by default) the original nii.gz
    def unzip(self, dest=None, replace=False):

        if dest is None:
            udest   = self.upath
        else:
            udest   = Image(dest).upath
        gunzip(self.cpath, udest, replace)

    # check whether nii does not exist but nii.gz does => create the nii copy preserving (by default) the nii.gz one
    def check_if_uncompress(self, replace=False):
        if not self.uexist and self.cexist:
            self.unzip(replace=replace)

    # preserve given volumes
    def filter_volumes(self, vols2keep, filtered_image):

        outdir, outprefix = self.imsplit("temp_")
        nvols = self.getnvol()

        tempdir = os.path.join(outdir, "tempXXXX")
        os.makedirs(tempdir, exist_ok=True)

        for i in range(0, nvols):
            if i in vols2keep:
                strnum = fillnumber2fourdigits(i)
                Image(os.path.join(outdir, "temp_" + strnum)).mv(os.path.join(tempdir, "temp_" + strnum))

        currdir = os.getcwd()

        os.chdir(tempdir)
        immerge(filtered_image)

        shutil.rmtree(tempdir)
        os.chdir(currdir)
        os.system("rm " + os.path.join(outdir, "temp_*"))

    def get_nth_volume(self, out_img=None, out_mask_img=None, volnum=3, logFile=None):

        if out_mask_img is None:
            out_mask_img = self.add_postfix2name("_mask")

        prefilt_func_data = Image(self.add_postfix2name("_prefiltered_func_data"))

        rrun("fslmaths "    + self.fpathnoext + " " + prefilt_func_data + " -odt float", logFile=logFile)
        rrun("fslroi "      + prefilt_func_data + " " + out_img + " " + str(volnum) + " 1", logFile=logFile)
        rrun("bet2 "        + out_img + " " + out_img + " -f 0.3", logFile=logFile)
        rrun("fslmaths "    + out_img + " -bin " + out_mask_img,  logFile=logFile)  # create example_function mask (a -thr 0.01/0.1 could have been used to further reduce it)
        prefilt_func_data.rm(logFile=logFile)

        return out_img

    def add_postfix2name(self, postfix):
        return Image(self.fpathnoext + postfix + self.ext)

    def add_prefix2name(self, prefix):
        return Image(os.path.join(self.dir, prefix + self.name + self.ext))


class Images(list):

    def __new__(cls, value=None, must_exist=False, msg=""):
        return super(Images, cls).__new__(cls, value)

    # def __new__(cls, value=None, must_exist=False, msg=""):
    #     ivalues = []
    #     if value is not None:
    #         for v in value:
    #             ivalues.append(Image(v, must_exist, msg))
    #
    #     return super(Images, cls).__new__(cls, ivalues)

    def __init__(self, value=None, must_exist=False, msg=""):
        super().__init__()
        if value is None:
            value = []
        for v in value:
            self.append(Image(v, must_exist, msg))

    def rm(self, logFile=None):

        for file in self:
            Image(file).rm(logFile)

    # def append(self, __object) -> None:
    #     self.append(Image(__object))

    # move a series of images defined by wildcard string ( e.g.   *fast*
    def move(self, destdir, logFile=None):

        images = []
        for f in self:
            f = Image(f)
            if f.is_image():
                if f.exist:
                    images.append(f)

        for img in images:
            dest_file = os.path.join(destdir, os.path.basename(img))
            move(img, dest_file)
            if logFile is not None:
                print("mv " + img + " " + dest_file, file=logFile)

    def check_if_uncompress(self, replace=False):
        for img in self:
            Image(img).check_if_uncompress(replace)

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
