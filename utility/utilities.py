import gzip
import os
import re
import shutil
import tempfile
import zipfile


def is_list_of(_list, _type, checkall=False):
    if isinstance(_list, list):
        if not checkall:
            if isinstance(_list[0], _type):
                return True
        else:
            for i in _list:
                if not isinstance(i, _type):
                    return False
            return True
    return False


def extractall_zip(src, dest, replace=True):

    if os.path.exists(dest):
        if replace:
            os.removedirs(dest)
        else:
            return
    os.makedirs(dest, exist_ok=True)

    print("start unzipping " + src)
    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dest)
    print("finished unzipping " + src)


def gunzip(src, dest, replace=False):
    fp = open(dest, "wb")
    with gzip.open(src, "rb") as f:
        bindata = f.read()
    fp.write(bindata)
    fp.close()

    if replace:
        os.remove(src)


def compress(src, dest, replace=False):
    fp = open(src, "rb")
    with gzip.open(dest, "wb") as f:
        f.write(fp.read())
    fp.close()

    if replace:
        os.remove(src)


def write_text_file(path, text):
    with open(path, "w") as f:
        f.write(text)


def append_text_file(path, text):
    with open(path, "a") as f:
        f.write(text)


def sed_inplace(filename, pattern, repl, must_exist=False):
    """
    Perform the pure-Python equivalent of in-place `sed` substitution: e.g.,
    `sed -i -e 's/'${pattern}'/'${repl}' "${filename}"`.
    """
    # For efficiency, precompile the passed regular expression.
    pattern_compiled = re.compile(pattern)

    # For portability, NamedTemporaryFile() defaults to mode "w+b" (i.e., binary
    # writing with updating). This is usually a good thing. In this case,
    # however, binary writing imposes non-trivial encoding constraints trivially
    # resolved by switching to text writing. Let's do that.
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            with open(filename) as src_file:
                for line in src_file:
                    tmp_file.write(pattern_compiled.sub(repl, line))
    except FileNotFoundError:
        if must_exist is True:
            raise Exception("file " + filename + " not found")
        else:
            print("file " + filename + " not found, skipping!!")
            return




    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    shutil.copystat(filename, tmp_file.name)
    shutil.move(tmp_file.name, filename)


# get the sorting schema of a list(e.g [2,3,1,4,5] => [2,0,1,3,4]
def argsort(seq):
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)


# apply the given permutation to a list
def reorder_list(_list, neworder):
    return [_list[i] for i in neworder]


def get_filename(fullpath):
    return os.path.splitext(os.path.basename(fullpath))[0]


def remove_ext(filepath):
    return os.path.splitext(filepath)[0]


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


# read a file where each line is a string and returns them as list (pruning the '\n')
def read_list_from_file(srcfile):
    with open(srcfile, 'r') as f:
        _str = f.readlines()

    for s in range(len(_str)):
        _str[s] = _str[s].strip()
    return _str


def fillnumber2fourdigits(num):

    if num > 9999:
        print("Error in fillnumber2fourdigits, given number is > 9999")
        return

    if num < 10:
        str_num = "000" + str(num)
    elif 9 < num < 100:
        str_num = "00" + str(num)
    elif 99 < num < 1000:
        str_num = "0" + str(num)
    else:
        str_num = str(num)

    return str_num


# if is a string => cast to int or float (when appropriate) or keep it string
# if not         => don't do anything, return input param unchanged
def string2num(string):
    try:
        if not isinstance(string, str):
            return string

        fl_string = float(string)
        if round(fl_string) == fl_string:
            return int(fl_string)
        else:
            return fl_string
    except ValueError:
        return string


def listToString(_list, separator='\t'):

    _str = ""
    # traverse the list and concatenate to String variable
    for element in _list:
        _str += (str(element) + separator)

    return _str