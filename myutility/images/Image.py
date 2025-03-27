from __future__ import annotations

import collections
import ntpath
import os
import shutil
import xml.etree.ElementTree as ET
from shutil import move, copyfile
from typing import Optional, List

# https://stackoverflow.com/questions/30045106/python-how-to-extend-str-and-overload-its-constructor
from myutility.exceptions import NotExistingImageException
from myutility.fileutilities import compress, gunzip
from myutility.myfsl.utils.run import rrun
from myutility.utilities import fillnumber2fourdigits


class Image(str):
    """
    A class to handle neuroimaging files.

    Attributes:
        dir (str): The directory where the image is located.
        name (str): The name of the image without the extension.
        ext (str): The extension of the image.
        fpathnoext (str): The full path of the image without the extension.
        is_dir (bool): Whether the path points to a directory or a file.

    """

    IMAGE_FORMATS = [".nii.gz", ".img.gz", ".mnc.gz", ".hdr.gz", ".hdr", ".mnc", ".img", ".nii", ".mgz", ".gii", ".src.gz"]

    def __new__(cls, value, must_exist=False, msg:str=""):
        return super(Image, cls).__new__(cls, value)

    def __init__(self, value:str, must_exist=False, msg:str="Given Image path is empty"):
        """
        Initialize the Image object.

        Args:
            value (str): The path to the image.
            must_exist (bool, optional): Whether the image must exist. Defaults to False.
            msg (str, optional): The error message to be raised if the image does not exist. Defaults to "Given Image path is empty".

        Raises:
            NotExistingImageException: If the image does not exist and must_exist is True.

        """
        if value != "":
            parts = self.imgparts()

            self.dir = parts[0]
            self.name = parts[1]  # name NO EXTENSION !!!!!!
            self.ext = parts[2]
            self.fpathnoext = str(os.path.join(self.dir, self.name))
            self.is_dir = os.path.isdir(self)

            if must_exist and not self.exist:
                raise NotExistingImageException(msg, self)
            return

        raise NotExistingImageException(msg, self)

    @property
    def exist(self) -> bool:
        """
        Check if the image exists.
        return False if neither compressed nor uncompressed images exist or True if either compressed or uncompressed image exists

        Returns:
            bool: Whether the image exists.
        """
        # if self == "":
        #     return False

        if os.path.isfile(self.upath) or os.path.isfile(self.cpath) or os.path.isfile(self.spath) or os.path.isfile(self.fpathnoext + ".mgz"):
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

    @property
    def uexist(self) -> bool:
        """
        Check if the uncompressed image exists.

        Returns:
            bool: Whether the uncompressed image exists.
        """
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

    @property
    def cexist(self) -> bool:
        """
        Check if the compressed image exists.

        Returns:
            bool: Whether the compressed image exists.
        """
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

    @property
    def gexist(self) -> bool:
        """
        Check if the compressed image exists.

        Returns:
            bool: Whether the compressed image exists.

        """
        return os.path.isfile(self.fpathnoext + ".gii")

    @property
    def upath(self) -> 'Image':
        """
        Get the path to the uncompressed image.

        Returns:
            Image: The uncompressed image.

        """
        return Image(str(self.fpathnoext + ".nii"))

    @property
    def cpath(self) -> 'Image':
        """
        Get the path to the compressed image.

        Returns:
            Image: The compressed image.

        """
        return Image(self.fpathnoext + ".nii.gz")

    @property
    def gpath(self) -> 'Image':
        """
        Get the path to the surface image.

        Returns:
            Image: The surface image.

        """
        return Image(self.fpathnoext + ".gii")

    @property
    def spath(self) -> 'Image':
        """
        Get the path to DSI-studio dti image.

        Returns:
            Image: The dti image.

        """
        return Image(self.fpathnoext + ".src.gz")

    @property
    def nslices(self) -> int:
        """
        Get the number of slices in the image.

        Returns:
            int: The number of slices.

        """
        return int(rrun(f"fslval {self} dim3"))

    @property
    def nvols(self) -> int:
        """
        Get the number of volumes in the image.

        Returns:
            int: The number of volumes.

        """
        return int(rrun(f"fslnvols {self}").split('\n')[0])

    @property
    def nvoxels(self) -> int:
        """
        Get the number of voxels in the image.
        Returns:
            int: The number of voxels.
        """
        return int(rrun(f"fslstats {self} -V").strip().split(" ")[0])

    @property
    def TR(self) -> float:
        """
        Get the repetition time of the image.

        Returns:
            float: The repetition time.

        """
        return float(rrun(f"fslval {self} pixdim4"))

    # ===============================================================================================================================
    # FOLDERS, NAME, EXTENSIONS,
    # ===============================================================================================================================
    # get the whole extension  (e.g. abc.nii.gz => nii.gz )
    # return [path/filename_noext, ext]
    def split_ext(self, img_formats=None) -> List[str]:
        """
        Split the extension from the filename.

        Args:
            img_formats (list, optional): The allowed image formats. Defaults to None, which uses the class attribute IMAGE_FORMATS.

        Returns:
            list: A list containing the filename and extension.

        """
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
    def imgparts(self) -> List[str]:
        """
        Split the path to the image into its components: directory, filename, and extension.

        Returns:
            list: A list containing the directory, filename, and extension.

        """
        if os.path.isdir(self):
            return [self, "", ""]

        parts = self.split_ext()
        return [ntpath.dirname(parts[0]), ntpath.basename(parts[0]), parts[1]]

    def imgdir(self) -> str:
        namepath = self.split_ext()[0]
        return ntpath.dirname(namepath)

    # return basename of given image (useful to return "image" from "image.nii.gz")
    def remove_image_ext(self) -> str:
        return self.split_ext()[0]

    # ===========================================================================================================
    # COPY, REMOVE, MOVE, MASS MOVE
    # ===========================================================================================================
    def cp(self, dest:str, error_src_not_exist:bool=True, logFile=None) -> 'Image':
        """
        Copy the image to a destination.

        Args:
            dest (Image): The destination image.
            error_src_not_exist (bool, optional): Whether to raise an exception if the source image does not exist. Defaults to True.
            logFile (object, optional): The log file object. Defaults to None.

        Returns:
            str: The path to the copied image.

        Raises:
            NotExistingImageException: If the source image does not exist and error_src_not_exist is True.

        """
        if not self.exist:
            if error_src_not_exist:
                print("ERROR in cp. src image (" + self + ") does not exist")
                return ""
            else:
                print("WARNING in cp. src image (" + self + ") does not exist, skip copy and continue")

        ext = ""
        if os.path.isfile(self.upath):
            ext = ".nii"
        elif os.path.isfile(self.cpath):
            ext = ".nii.gz"
        elif os.path.isfile(self.gpath):
            ext = ".gii"

        dest = Image(dest)
        fileparts_dst = dest.split_ext()

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

        return Image(fileparts_dst[0] + dest_ext)

    def cp_notexisting(self, dest:str|'Image', error_src_not_exist=False, logFile=None) -> 'Image':
        """
        Copy the image to a destination.

        Args:
            dest (Image): The destination image.
            error_src_not_exist (bool, optional): Whether to raise an exception if the source image does not exist. Defaults to True.
            logFile (object, optional): The log file object. Defaults to None.

        Returns:
            str: The path to the copied image.

        Raises:
            NotExistingImageException: If the source image does not exist and error_src_not_exist is True.
        """
        if not self.exist:
            if error_src_not_exist:
                raise NotExistingImageException("Image.cp_notexisting", self)
            else:
                print(f"WARNING in cp_notexisting. src image ({self}) does not exist, skip copy and continue")

        dest = Image(dest)

        if not dest.exist:
            return self.cp(dest, logFile)
        else:
            return dest

    def mv(self, dest:'Image', error_src_not_exist: bool = False, logFile=None) -> 'Image':
        """
        Move the image to a destination.

        Args:
            dest (Image): The destination image.
            error_src_not_exist (bool, optional): Whether to raise an exception if the source image does not exist. Defaults to False.
            logFile (object, optional): The log file object. Defaults to None.

        Returns:
            bool: Whether the move operation succeeded.

        Raises:
            NotExistingImageException: If the source image does not exist and error_src_not_exist is True.

        """
        if not self.exist:
            if error_src_not_exist:
                print("ERROR in mv. src image (" + self + ") does not exist")
                return
            else:
                print("WARNING in mv. src image (" + self + ") does not exist, skip rename and continue")

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

        return Image(dest.fpathnoext + ext)

    def rm(self, logFile=None):
        """
        Remove the image.

        Args:
            logFile (object, optional): The log file object. Defaults to None.
        """
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
    def get_image_volume(self) -> int:
        """
        Get the volume of the image.

        Returns:
            int: The volume of the image.

        """
        return int(rrun(f"fslstats {self} -V").strip().split(" ")[1])

    def get_image_mean(self, includezeros:bool=False) -> float:
        """
        Get the mean of the image.

        Returns:
            float: The mean of the image.

        """
        if includezeros:
            str_mean = " -m"
        else:
            str_mean = " -M"
        return float(rrun(f"fslstats {self} {str_mean}").strip())

    def mask_image(self, mask:str|'Image', out:str|'Image') -> 'Image':
        """
        Mask an image with a mask.

        Args:
            mask (Image): The mask image.
            out (Image): The output image.

        """
        mask = Image(mask, must_exist=True)

        rrun(f"fslmaths {self} -mas {mask} {out}")

    def get_mask_mean(self, mask:str, includezeros:bool=False) -> float:

        mask = Image(mask, must_exist=True, msg="Given mask in get_mask_mean is not valid")
        if includezeros:
            str_mean = " -m"
        else:
            str_mean = " -M"

        return float(rrun(f"fslstats {self} -k {mask} {str_mean}").strip())

    def imsplit(self, templabel=None, subdirmame:str="") -> tuple[str, str]:
        """
        Split an image into multiple volumes.

        Args:
            templabel (str, optional): The temporary label for the volumes. If None, the filename will be used. Defaults to None.
            subdirmame (str, optional): The name of the sub-directory to store the volumes in. Defaults to "".

        Returns:
            tuple: A tuple containing the path to the output directory and the temporary label.

        """
        if templabel is None:
            label = self.name
        else:
            label = templabel

        currdir = os.getcwd()
        outdir  = os.path.join(self.dir, subdirmame)
        os.makedirs(outdir, exist_ok=True)
        os.chdir(outdir)
        rrun(f"fslsplit {self} {label} -t")
        os.chdir(currdir)
        return outdir, label

    def thr(self, thr:float, out_img:Image|None=None) -> 'Image':

        if out_img is None:
            out_img = self
        else:
            out_img = Image(out_img)

        rrun(f"fslmaths {self} -thr {thr} {out_img}")

        return out_img

    def bin(self, out_img:Image|None=None) -> 'Image':
        if out_img is None:
            out_img = self
        else:
            out_img = Image(out_img)
        rrun(f"fslmaths {self} -bin {out_img}")

        return out_img

    def quick_smooth(self, out_img=None, logFile=None) -> 'Image':
        """
        Perform a quick smoothing of the image using FSL.

        Args:
            outimg (Image, optional): The output image. If None, the input image will be used. Defaults to None.
            logFile (object, optional): The log file object. Defaults to None.

        Returns:
            Image: The smoothed image.

        """
        if out_img is None:
            out_img = self
        else:
            out_img = Image(out_img)

        currpath    = os.path.dirname(self)
        vol16       = Image(os.path.join(currpath, "vol16"))

        rrun(f"fslmaths {self} -subsamp2 -subsamp2 -subsamp2 -subsamp2 {vol16}", logFile=logFile)
        rrun(f"flirt -in {vol16} -ref {self} -out {out_img} -noresampblur -applyxfm -paddingsize 16", logFile=logFile)
        # possibly do a tiny extra smooth to $out here?
        vol16.rm()

        return out_img

    # TODO: patched to deal with X dots + .nii.gz...fix it definitively !!
    def is_image(self, img_formats=None) -> bool:
        """
        Check if the image is an image.

        Args:
            img_formats (list, optional): The allowed image formats. Defaults to None, which uses the class attribute IMAGE_FORMATS.

        Returns:
            bool: Whether the image is an image.

        """
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

    def get_head_from_brain(self, checkexist:bool=True) -> 'Image':
        """
        Get the head image from the brain image.

        Args:
            checkexist (bool, optional): Whether to check if the head image exists. Defaults to True.

        Raises:
            Exception: If the given image is not an image or the head image does not exist and checkexist is True.

        Returns:
            Image: The head image.

        """
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
    def get_image_dimension(self) -> int:
        """
        Get the dimension of the image.

        Returns:
            int: The dimension of the image.

        """
        hdr = self.read_header()
        return int(hdr["nx"]) * int(hdr["ny"]) * int(hdr["nz"]) * float(hdr["dx"]) * float(hdr["dy"]) * float(hdr["dz"])

    # extract header in xml format and returns it as a (possibly filtered by list_field) dictionary
    def read_header(self, list_field=None) -> dict:
        """
        Extract the header from an image and return it as a dictionary.

        Args:
            list_field (list): A list of fields to extract from the header. If None, all fields will be extracted.

        Returns:
            dict: A dictionary containing the header fields.

        """
        res = rrun(f"fslhd -x {self}")
        root = ET.fromstring(res)
        attribs_dict = root.attrib

        if list_field is not None:
            fields = dict()
            for f in list_field:
                fields[f] = attribs_dict[f]
            return fields
        else:
            return attribs_dict

    # remove numslice2remove up and down (fslroi wants, for each dimension, first slice to keep and number of slices to keep)
    def remove_slices(self, numslice2remove=1, whichslices2remove:str="updown", remove_dimension="axial") -> 'Image':
        """
        Remove slices from an image.

        Args:
            numslice2remove (int): The number of slices to remove.
            whichslices2remove (str): Whether to remove the first or last slices. Can be "updown" or "firstlast".
            remove_dimension (str): The dimension to remove slices from. Can be "axial" or "sagittal".

        Returns:
            None

        Raises:
            ValueError: If the given remove_dimension is not "axial" or "sagittal".

        """
        nslices = int(rrun(f"fslval {self} dim3"))
        if remove_dimension == "axial":
            if whichslices2remove == "updown":
                dim_str = "0 -1 0 -1 " + str(numslice2remove) + " " + str(nslices - 2*numslice2remove)
            else:
                raise ValueError("ERROR in remove_slices, presently it removes only in the axial (z) dimension")
        else:
            raise ValueError("ERROR in remove_slices, presently it removes only in the axial (z) dimension")

        self.cp(self.fpathnoext + "_full")
        rrun(f"fslroi {self} {self} {dim_str}")

        return self

    def compress(self, dest=None, replace:bool=True) -> 'Image':
        """
        Compress the image to a compressed format.

        Args:
            dest (Image, optional): The destination image. If None, the compressed image will be stored in the same directory as the uncompressed image and will have a .nii.gz extension.
            replace (bool, optional): Whether to replace the existing compressed image. Defaults to True.

        Returns:
            Image: The compressed image.

        """
        if dest is None:
            udest = self.cpath
        else:
            udest = Image(dest).cpath

        compress(self.upath, udest, replace)
        return udest

    # unzip file to a given path, preserving (by default) the original nii.gz
    def unzip(self, dest: 'Image'|None = None, replace: bool = False) -> 'Image':
        """
        Unzip the image to a given path, preserving (by default) the original nii.gz

        Args:
            dest (Image, optional): The destination image. If None, the uncompressed image will be stored in the same directory as the compressed image and will have a .nii extension.
            replace (bool, optional): Whether to replace the existing uncompressed image. Defaults to False.

        Returns:
            None
        """
        if dest is None:
            udest = self.upath
        else:
            udest = Image(dest).upath

        if udest.exist and replace is False:
            return udest

        gunzip(self.cpath, udest, replace)

        return udest

    # check whether nii does not exist but nii.gz does => create the nii copy preserving (by default) the nii.gz one
    def check_if_uncompress(self, replace=False):
        """
        Check whether the uncompressed nii does not exist but the compressed nii.gz does, and if so, unzip the image to the original location, preserving (by default) the original nii.gz.

        Args:
            replace (bool, optional): Whether to replace the existing uncompressed image. Defaults to False.

        Returns:
            None
        """
        if not self.uexist and self.cexist:
            self.unzip(dest=self, replace=replace)

    # preserve given volumes
    def filter_volumes(self, vols2keep:List[int], filtered_image:'Image') -> 'Image':
        """
        create a new 4D image (filtered_image) preserving the volumes of self specified in vols2keep.

        Args:
            vols2keep (list): A 0-based list of volumes to keep.
            filtered_image (Image): The output filtered image.

        Returns:
            None

        """
        tempdir, outprefix  = self.imsplit("temp_", "tempXXX") # split image in the subfolder tempXXX
        nvols               = self.nvols

        outdir              = filtered_image.dir
        outtempdir          = os.path.join(outdir, "tempXXX")
        os.makedirs(outtempdir, exist_ok=True)

        for i in range(0, nvols):
            if i in vols2keep:
                strnum = fillnumber2fourdigits(i)
                Image(os.path.join(tempdir, outprefix + strnum)).mv(Image(os.path.join(outtempdir, outprefix + strnum)))

        currdir = os.getcwd()
        os.chdir(outtempdir)
        Image.immerge(filtered_image)

        shutil.rmtree(tempdir)
        shutil.rmtree(outtempdir)
        os.chdir(currdir)

        return filtered_image
        # os.system("rm " + os.path.join(outdir, "temp_*"))

    def get_nth_volume(self, out_img:str|Image, out_mask_img=None, volnum=3, logFile=None) -> 'Image':
        """
        Get the nth volume of the image.

        Args:
            out_img (Image, optional): The output image. If None, a temporary image will be created.
            out_mask_img (Image, optional): The output mask image. If None, a temporary image will be created.
            volnum (int): The volume number.
            logFile (object, optional): The log file object.

        Returns:
            Image: The nth volume.

        """
        if out_img == "":
            raise Exception("Error in Image.get_nth_volume: output image is empty")
        # TODO: check whether out_img folder exists

        if out_mask_img is None:
            out_mask_img = self.add_postfix2name("_mask")

        prefilt_func_data = Image(self.add_postfix2name("_prefiltered_func_data"))

        rrun(f"fslmaths {self.fpathnoext} {prefilt_func_data} -odt float", logFile=logFile)
        rrun(f"fslroi {prefilt_func_data} {out_img} {volnum} 1", logFile=logFile)
        rrun(f"bet2 {out_img} {out_img} -f 0.3", logFile=logFile)
        rrun(f"fslmaths {out_img} -bin {out_mask_img}",  logFile=logFile)  # create example_function mask (a -thr 0.01/0.1 could have been used to further reduce it)
        prefilt_func_data.rm(logFile=logFile)

        return Image(out_img)

    def add_postfix2name(self, postfix: str) -> 'Image':
        """
        Adds a postfix to the filename of an image.

        Args:
            postfix (str): The postfix to add to the filename.

        Returns:
            Image: The image with the added postfix.
        """
        return Image(self.fpathnoext + postfix + self.ext)

    def add_prefix2name(self, prefix: str) -> 'Image':
        """
        Adds a prefix to the filename of an image.

        Args:
            prefix (str): The prefix to add to the filename.

        Returns:
            Image: The image with the added prefix.
        """
        return Image(os.path.join(self.dir, prefix + self.name + self.ext))

    @staticmethod
    def immerge(out_img: str, premerge_labels=None) -> 'Image':
        """
        Merge a set of images into a single image.

        Args:
            out_img (str): The path to the output image.
            premerge_labels (list, str, optional): A list of labels or a single label to use as prefixes for the input images. If None, all images in the current directory will be used.

        Returns:
            None

        Raises:
            ValueError: If the given premerge_labels is not in a supported format.

        """
        seq_string = " "

        if premerge_labels is None:
            seq_string = "./*"
        elif isinstance(premerge_labels, str):
            seq_string = premerge_labels + "*"
        elif isinstance(premerge_labels, collections.Sequence):
            for seq in premerge_labels:
                seq_string = seq_string + out_img + "_" + seq + " "
        else:
            raise ValueError("Error in immerge, given premerge_labels is not in a correct format")

        os.system(f"fslmerge -t {out_img} {seq_string}")

        return Image(out_img)

    def get_spm_volumes_list(self) -> str:
        """
        explode a 4d volumes in a list of images,vol:    { 'image,1'
                                                           'image,n' }
        ready for spm batch file

        Returns:
            str: list of images r
        """
        epi_nvols = self.upath.nvols
        epi_all_volumes = ''
        epi_all_volumes += '{\n'
        for i in range(1, epi_nvols + 1):
            epi_volume = "'" + self.upath + ',' + str(i) + "'"
            epi_all_volumes += (epi_volume + '\n')
        epi_all_volumes += '}\n'

        return epi_all_volumes


