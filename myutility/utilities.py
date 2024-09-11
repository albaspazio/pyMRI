from __future__ import annotations

import numpy as np


# get the sorting schema of a list(e.g [2,3,1,4,5] => [2,0,1,3,4]


def fillnumber2fourdigits(num:int|float) -> str:
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


def fillnumber2threedigits(num:int|float) -> str:
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


# extract i-th column from a list of list


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

