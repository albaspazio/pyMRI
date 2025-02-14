import os
from shutil import move

from myutility.exceptions import NotExistingImageException
from myutility.images.Image import Image


class Images(list):
    """
    A class for managing a list of images.

    Args:
        value (list, optional): A list of image paths. If not provided, an empty list is created.
        must_exist (bool, optional): If True, the existence of each image is checked before adding it to the list.
        msg (str, optional): A message to be displayed if the image does not exist and must_exist is True.
    """

    def __new__(cls, value=None, must_exist:bool=False, msg:str=""):
        return super(Images, cls).__new__(cls, value)

    def __init__(self, value=None, must_exist=False, msg:str=""):
        super().__init__()
        if value is None:
            value = []
        if isinstance(value, str):
            value = [value]

        missing_images = []
        for v in value:
            try:
                self.append(Image(v, must_exist, msg))
            except NotExistingImageException as e:
                missing_images.append(e.image)

        if len(missing_images) > 0:
            raise NotExistingImageException(msg, str(missing_images))


    @property
    def exist(self):
        """
        Returns True if all images in the list exist, False otherwise.
        """
        for img in self:
            if not Image(img).exist:
                return False
        return True

    def rm(self, logFile=None):
        """
        Removes all images in the list.

        Args:
            logFile (file, optional): A file object to which the removal process is logged.
        """
        for img in self:
            Image(img).rm(logFile)

    def cp(self, dest, error_src_not_exist:bool=True, logFile=None):
        """
        Copies all images in the list to the destination directory.

        Args:
            dest (Images): A list of destination image paths.
            error_src_not_exist (bool, optional): If True, an exception is raised if an image does not exist in the source list.
            logFile (file, optional): A file object to which the copying process is logged.

        Raises:
            Exception: If the destination is not an Images instance.
            Exception: If the length of the source and destination lists differ.
        """
        if not isinstance(dest, Images):
            raise Exception("Error in Images.cp, given dest is not an Images instance")

        if len(self) != len(dest):
            raise Exception("Error in Images.cp, given dest lenght differs from source length")

        for _id, img in enumerate(self):
            Image(img).cp(dest[_id], error_src_not_exist, logFile)

    def mv(self, dest, error_src_not_exist=False, logFile=None):
        """
        Moves all images in the list to the destination directory.

        Args:
            dest (Images): A list of destination image paths.
            error_src_not_exist (bool, optional): If True, an exception is raised if an image does not exist in the source list.
            logFile (file, optional): A file object to which the moving process is logged.

        Raises:
            Exception: If the destination is not an Images instance.
            Exception: If the length of the source and destination lists differ.
        """
        if not isinstance(dest, Images):
            raise Exception("Error in Images.mv, given dest is not an Images instance")

        if len(self) != len(dest):
            raise Exception("Error in Images.mv, given dest lenght differs from source length")

        for _id, img in enumerate(self):
            Image(img).mv(dest[_id], error_src_not_exist, logFile)

    # def append(self, __object) -> None:
    #     self.append(Image(__object))

    # move a series of images defined by wildcard string ( e.g.   *fast*
    def move(self, destdir, logFile=None):
        """
        Moves all images in the list to a destination directory.

        Args:
            destdir (str): The destination directory.
            logFile (file, optional): A file object to which the moving process is logged.
        """
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
        """
        Checks if all images in the list are compressed and, if not, uncompresses them.

        Args:
            replace (bool, optional): If True, the original image is replaced by the uncompressed version.
        """
        for img in self:
            Image(img).check_if_uncompress(replace)

    def add_postfix2name(self, postfix):
        """
        Adds a postfix to the filename of all images in the list.

        Args:
            postfix (str): The postfix to be added.

        Returns:
            Images: A new Images instance with the postfixed filenames.
        """
        ret = Images()
        for img in self:
            ret.append(Image(img).add_postfix2name(postfix))
        return ret

    def add_prefix2name(self, prefix):
        """
        Adds a prefix to the filename of all images in the list.

        Args:
            prefix (str): The prefix to be added.

        Returns:
            Images: A new Images instance with the prefixed filenames.
        """
        ret = Images()
        for img in self:
            ret.append(Image(img).add_prefix2name(prefix))
        return ret
