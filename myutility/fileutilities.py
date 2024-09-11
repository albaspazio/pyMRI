"""
This module provides various utility functions for manipulating files and directories.

The functions provided in this module are:

extractall_zip: Extracts the contents of a ZIP archive to a directory.
gunzip: Decompresses a GZIP file.
compress: Compresses a file into a GZIP file.
write_text_file: Writes text to a file.
append_text_file: Appends text to a file.
sed_inplace: Performs a search-and-replace operation on a file in-place.
get_filename: Returns the filename without the extension.
get_dirname: Returns the directory name of a given path.
remove_ext: Removes the extension from a filename.
copytree: Copies a directory tree.
read_list_from_file: Reads a file and returns a list of strings.
read_keys_values_from_file: Reads a file with key-value pairs and returns a dictionary.
"""

import gzip
import os
import re
import shutil
import tempfile
import zipfile


def extractall_zip(src, dest, replace:bool=True):
    """
    Extracts the contents of a ZIP archive to a directory.

    Args:
        src (str): The path to the ZIP archive.
        dest (str): The directory to extract the contents to.
        replace (bool, optional): If True, replaces the contents of the destination directory if it already exists. Defaults to True.

    Raises:
        FileNotFoundError: If the source file does not exist.
        IsADirectoryError: If the destination is a file.

    Returns:
        None

    """
    if not os.path.exists(src):
        raise FileNotFoundError("Source file does not exist: {}".format(src))

    if os.path.isdir(dest):
        if os.path.isfile(dest):
            raise IsADirectoryError("Destination is a file: {}".format(dest))
    else:
        os.makedirs(dest, exist_ok=True)

    print("start unzipping " + src)
    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dest)
    print("finished unzipping " + src)


def gunzip(src, dest, replace=False):
    """
    Decompresses a GZIP file.

    Args:
        src (str): The path to the GZIP file.
        dest (str): The path to the destination file.
        replace (bool, optional): If True, replaces the destination file if it already exists. Defaults to False.

    Raises:
        FileNotFoundError: If the source file does not exist.

    Returns:
        None

    """
    if not os.path.exists(src):
        raise FileNotFoundError("Source file does not exist: {}".format(src))

    fp = open(dest, "wb")
    with gzip.open(src, "rb") as f:
        bindata = f.read()
    fp.write(bindata)
    fp.close()

    if replace:
        os.remove(src)


def compress(src, dest, replace=False):
    """
    Compresses a file into a GZIP file.

    Args:
        src (str): The path to the file to compress.
        dest (str): The path to the destination GZIP file.
        replace (bool, optional): If True, replaces the destination file if it already exists. Defaults to False.

    Raises:
        FileNotFoundError: If the source file does not exist.

    Returns:
        None

    """
    if not os.path.exists(src):
        raise FileNotFoundError("Source file does not exist: {}".format(src))

    fp = open(src, "rb")
    with gzip.open(dest, "wb") as f:
        f.write(fp.read())
    fp.close()

    if replace:
        os.remove(src)


def write_text_file(path, text, replace:bool=True):
    """
    Writes text to a file.

    Args:
        path (str): The path to the file.
        text (str): The text to write to the file.
        replace (bool, optional): If True, replaces the destination file if it already exists. Defaults to True

    Raises:
        FileNotFoundError: If the destination file exists and replace is False.

    Returns:
        None
    """
    if os.path.exists(path) and not replace:
        raise FileExistsError("Destination file exists: {}".format(path))

    with open(path, "w") as f:
        f.write(text)


def append_text_file(path, text):
    """
    Appends text to a file.

    Args:
        path (str): The path to the file.
        text (str): The text to append to the file.

    Raises:
        FileNotFoundError: If the destination file does not exist.

    Returns:
        None

    """
    if not os.path.exists(path):
        raise FileNotFoundError("Destination file does not exist: {}".format(path))

    with open(path, "a") as f:
        f.write(text)


def sed_inplace(filename, pattern, repl, must_exist=False):
    """
    Performs a search-and-replace operation on a file in-place.

    Args:
        filename (str): The path to the file.
        pattern (str): The regular expression pattern to search for.
        repl (str): The replacement string.
        must_exist (bool, optional): If True, raises an exception if the file does not exist. Defaults to False.

    Raises:
        FileNotFoundError: If the file does not exist and must_exist is True.

    Returns:
        None

    """
    if not os.path.exists(filename):
        if must_exist:
            raise FileNotFoundError("File does not exist: {}".format(filename))
        else:
            print("File does not exist: {}".format(filename))
            return

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


def get_filename(fullpath):
    """
    Returns the filename without the extension.

    Args:
        fullpath (str): The full path to the file.

    Returns:
        str: The filename without the extension.

    """
    return os.path.splitext(os.path.basename(fullpath))[0]


# return   /a/b/c/d/e.f  -> d
def get_dirname(fullpath: str) -> str:
    """
    Returns the directory name of a given path.

    Args:
        fullpath (str): The full path to the file.

    Returns:
        str: The directory name.

    """
    if os.path.isdir(fullpath):
        return os.path.basename(fullpath)
    else:
        return os.path.basename(os.path.dirname(fullpath))


def remove_ext(filepath: str) -> str:
    """
    Removes the extension from a filename.

    Args:
        filepath (str): The path to the file.

    Returns:
        str: The filename without the extension.

    """
    return os.path.splitext(filepath)[0]


def copytree(src: str, dst: str, symlinks: bool = False, ignore=None):
    """
    Copies a directory tree.

    Args:
        src (str): The path to the source directory.
        dst (str): The path to the destination directory.
        symlinks (bool, optional): If True, symlinks are followed. Defaults to False.
        ignore (callable, optional): A callable that takes the source path of each file or directory, and returns a boolean value indicating whether the path should be ignored. Defaults to None.

    Raises:
        FileExistsError: If the destination directory already exists and is not an empty directory.
        IsADirectoryError: If the source path is not a directory.

    Returns:
        None

    """
    if not os.path.isdir(src):
        raise IsADirectoryError("Source path is not a directory: {}".format(src))

    if os.path.exists(dst):
        if not os.path.isdir(dst):
            raise FileExistsError("Destination exists and is not a directory: {}".format(dst))
        if os.listdir(dst):
            raise FileExistsError("Destination directory is not empty: {}".format(dst))

    os.makedirs(dst, exist_ok=True)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def read_list_from_file(srcfile: str) -> list:
    """
    Reads a file and returns a list of strings.

    Args:
        srcfile (str): The path to the file.

    Returns:
        list: A list of strings.

    """
    with open(srcfile, 'r') as f:
        _str = f.readlines()

    for s in range(len(_str)):
        _str[s] = _str[s].strip()
    return _str


def read_keys_values_from_file(srcfile: str, separator: str = "\t", mustbeunique: bool = True) -> dict:
    """
    Reads a file with key-value pairs and returns a dictionary.

    Args:
        srcfile (str): The path to the file.
        separator (str, optional): The separator between the key and value. Defaults to "\t".
        mustbeunique (bool, optional): If True, raises an exception if the keys are not unique. Defaults to True.

    Returns:
        dict: A dictionary with the key-value pairs.

    Raises:
        ValueError: If the file does not exist or cannot be read.

    """
    if not os.path.exists(srcfile):
        raise ValueError("File does not exist: {}".format(srcfile))

    try:
        with open(srcfile, 'r') as f:
            _str = f.readlines()
    except:
        raise ValueError("Failed to read file: {}".format(srcfile))

    res = {}
    for s in range(len(_str)):
        _str[s] = _str[s].strip()
        arr = _str[s].split(separator)
        try:
            if bool(res[arr[0]]) and mustbeunique:
                raise ValueError("Duplicate key: {}".format(arr[0]))
            res[arr[0]] = arr[1]
        except:
            try:
                res[arr[0]] = arr[1]
            except:
                pass
    return res
