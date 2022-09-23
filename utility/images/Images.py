import os
from shutil import move

from utility.images.Image import Image


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
        if isinstance(value, str):
            value = [value]
        for v in value:
            self.append(Image(v, must_exist, msg))

    @property
    def exist(self):
        for img in self:
            if not Image(img).exist:
                return False
        return True

    def rm(self, logFile=None):
        for img in self:
            Image(img).rm(logFile)

    def cp(self, dest, error_src_not_exist=True, logFile=None):

        if not isinstance(dest, Images):
            raise Exception("Error in Images.cp, given dest is not an Images instance")

        if len(self) != len(dest):
            raise Exception("Error in Images.cp, given dest lenght differs from source length")

        for _id, img in enumerate(self):
            Image(img).cp(dest[_id], error_src_not_exist, logFile)

    def mv(self, dest, error_src_not_exist=False, logFile=None):

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

    def add_postfix2name(self, postfix):
        ret = Images()
        for img in self:
            ret.append(Image(img).add_postfix2name(postfix))
        return ret

    def add_prefix2name(self, prefix):
        ret = Images()
        for img in self:
            ret.append(Image(img).add_prefix2name(prefix))
        return ret
