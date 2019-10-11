import gzip
import re, shutil, tempfile


def gunzip(src, dest):

    fp = open(dest, "wb")
    with gzip.open(src, "rb") as f:
        bindata = f.read()
    fp.write(bindata)
    fp.close()

def compress(src, dest):

    fp = open(src, "rb")
    with gzip.open(dest, "wb") as f:
        f.write(fp.read())
    fp.close()


def write_text_file(path, text):
    with open(path, "w") as f:
        f.write(text)


def sed_inplace(filename, pattern, repl):
    '''
    Perform the pure-Python equivalent of in-place `sed` substitution: e.g.,
    `sed -i -e 's/'${pattern}'/'${repl}' "${filename}"`.
    '''
    # For efficiency, precompile the passed regular expression.
    pattern_compiled = re.compile(pattern)

    # For portability, NamedTemporaryFile() defaults to mode "w+b" (i.e., binary
    # writing with updating). This is usually a good thing. In this case,
    # however, binary writing imposes non-trivial encoding constraints trivially
    # resolved by switching to text writing. Let's do that.
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        with open(filename) as src_file:
            for line in src_file:
                tmp_file.write(pattern_compiled.sub(repl, line))

    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    shutil.copystat(filename, tmp_file.name)
    shutil.move(tmp_file.name, filename)

# get the sorting schema of a list(e.g [2,3,1,4,5] => [2,0,1,3,4]
def argsort(seq):
    #http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    #by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)

# apply the given permutation to a list
def reorder_list(list, neworder):
    return  [list[i] for i in neworder]

# transform properly a string containing a Int/Float/String
def typeUnknown(s):
    try:
        ns = float(s)
        if ns == round(ns):
            return int(s)
        else:
            return ns
    except ValueError:
        return s