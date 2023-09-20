def is_list_of(_list, _type, checkall=True):
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


# get the sorting schema of a list(e.g [2,3,1,4,5] => [2,0,1,3,4]
def argsort(seq):
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)


# apply the given permutation to a list
def reorder_list(_list, neworder):
    return [_list[i] for i in neworder]


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
# if not         => return input just rounding if requested
def string2num(string, ndecim=-1):
    try:
        if isinstance(string, float):
            if ndecim == -1:
                return string
            else:
                return float("{:." + str(ndecim) + "f}".format(str(string)))

        elif isinstance(string, int):
            return string

        elif isinstance(string, str):
            # is a string, check what really contains
            fl_string = float(string)
            if round(fl_string) == fl_string:
                return int(fl_string)
            else:
                # is float
                if ndecim == -1:
                    return fl_string
                else:
                    return float("{:." + str(ndecim) + "f}".format(fl_string))      # round
    except ValueError:
        return string


def listToString(_list, separator='\t'):

    _str = ""
    # traverse the list and concatenate to String variable
    for element in _list:
        _str += (str(element) + separator)

    return _str


# extract i-th column from a list of list
def get_col_from_listmatrix(matrix, zerocolid):

    ncols = len(matrix[0])

    if zerocolid >= ncols:
        print("Error in get_col_from_listmatrix, given colid (" + str(zerocolid) + ") is higher than available columns")
        return

    return [ r[zerocolid] for r in matrix ]

