import numpy as np

def is_list_of(_list, _type, checkall:bool=True):
    """
    Checks if a given variable is a list of a specific type.

    Parameters
    ----------
    _list: variable
        The variable to be checked.
    _type: type
        The type that the elements of the list should be.
    checkall: bool, optional
        If set to True (default), all elements of the list must be of type _type.
        If set to False, only the first element of the list is checked.

    Returns
    -------
    bool
        True if the variable is a list of the specified type, False otherwise.

    """
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
    """
    Returns the indices that would sort a list in ascending order.

    Parameters
    ----------
    seq: list
        The list for which the sorting indices are to be returned.

    Returns
    -------
    list
        A list of indices that, when applied to the original list, would sort it
        in ascending order.

    """
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)


# apply the given permutation to a list
def reorder_list(_list, neworder):
    """
    Reorders a list according to a given permutation.

    Parameters
    ----------
    _list: list
        The list to be reordered.
    neworder: list
        A list of indices that specifies the new order of the elements in the list.

    Returns
    -------
    list
        The reordered list.

    """
    return [_list[i] for i in neworder]


def fillnumber2fourdigits(num):
    """
    Adds leading zeros to a number so that it has four digits.

    Parameters
    ----------
    num: int or float
        The number to be formatted.

    Returns
    -------
    str
        The number formatted with leading zeros, as a string.

    Raises
    ------
    ValueError
        If the input number is greater than 9999.

    """
    if num > 9999:
        raise ValueError("Error in fillnumber2fourdigits, given number is > 9999")

    if num < 10:
        str_num = "000" + str(num)
    elif 9 < num < 100:
        str_num = "00" + str(num)
    elif 99 < num < 1000:
        str_num = "0" + str(num)
    else:
        str_num = str(num)

    return str_num


def fillnumber2threedigits(num):
    """
    Adds leading zeros to a number so that it has three digits.

    Parameters
    ----------
    num: int or float
        The number to be formatted.

    Returns
    -------
    str
        The number formatted with leading zeros, as a string.

    Raises
    ------
    ValueError
        If the input number is greater than 999.

    """
    if num > 999:
        raise ValueError("Error in fillnumber2threedigits, given number is > 999")

    if num < 10:
        str_num = "00" + str(num)
    elif 9 < num < 100:
        str_num = "0" + str(num)
    else:
        str_num = str(num)

    return str_num


# if is a string => cast to int or float (when appropriate) or keep it string
# if not         => return input just rounding if requested
def string2num(string, ndecim=-1):
    """
    Attempts to convert a string to a number, with optional decimal precision.

    Parameters
    ----------
    string: str
        The string to be converted.
    ndecim: int, optional
        The number of decimal places to use (default is -1, which means no decimal
        precision is applied).

    Returns
    -------
    Union[int, float, str]
        The converted number, or the original string if the conversion failed.

    """
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
                    return float("{:." + str(ndecim) + "f}".format(fl_string))  # round
    except ValueError:
        return string


def listToString(_list, separator='\t'):
    """
    Converts a list of values to a string, with each value separated by a separator.

    Parameters
    ----------
    _list: list
        The list of values to be converted to a string.
    separator: str, optional
        The separator to use between values (default is a tab character).

    Returns
    -------
    str
        The list values separated by the specified separator.

    """
    _str = _list[0]
    # traverse the list and concatenate to String variable
    for i in range(1, len(_list)):
        _str += separator + str(_list[i])

    return _str


# extract i-th column from a list of list
def get_col_from_listmatrix(matrix, zerocolid):
    """
    Extracts a column from a list of lists.

    Parameters
    ----------
    matrix: list of list
        The list of lists from which the column is to be extracted.
    zerocolid: int
        The index of the column to be extracted (zero-based).

    Returns
    -------
    list
        The values of the specified column.

    Raises
    ------
    ValueError
        If the specified column index is out of range.

    """
    ncols = len(matrix[0])

    if zerocolid >= ncols:
        raise ValueError("Error in get_col_from_listmatrix, given colid "
                         "({}) is higher than available columns".format(zerocolid))

    return [r[zerocolid] for r in matrix]


def remove_items_from_list(origlist, list2remove):
    """
    Removes items from a list that are also present in another list.

    Parameters
    ----------
    origlist: list
        The original list.
    list2remove: list
        The list of items to be removed.

    Returns
    -------
    list
        The list with the specified items removed.

    """
    res = []
    for orig_list in origlist:
        if orig_list not in list2remove:
            res.append(orig_list)
    return res


class Processes(list):
    """
    A list-like object that can be used to manage a collection of processes.

    Parameters
    ----------
    procs : list, optional
        A list of processes to be added to the collection.

    Methods
    -------
    wait()
        Waits for all processes in the collection to complete.
    """
    def __new__(cls, procs=None):
        return super(Processes, cls).__new__(cls, procs)

    def __init__(self, procs=None):
        super().__init__()
        if procs is None:
            procs = []
        for pr in procs:
            self.append(pr)

    def wait(self):
        for pr in self:
            pr.wait()


def fisher_to_correlation(r_fisher):
    return (np.exp(2 * r_fisher) - 1) / (np.exp(2 * r_fisher) + 1)

