"""
This module provides functions for reading and writing data in various formats.

The functions provided in this module can be categorized as follows:

1. File I/O: Functions for reading and writing data to and from files.
2. Data manipulation: Functions for manipulating data, such as sorting, filtering, and aggregating data.
3. Mathematical and statistical functions: Functions for performing mathematical and statistical operations on data.
4. Utility functions: Functions that provide general-purpose utilities, such as string manipulation, file searching, and data validation.

The functions in this module are designed to be flexible and can be easily customized to meet the specific needs of different applications.

"""

import csv
import os
from statistics import mean
from typing import Dict, List, Any

from utility.fileutilities import write_text_file
# read file as:   lab1=val1\nlab2=val2\n....etc
from utility.utilities import listToString

# =====================================================================================
# ACCESSORY
# =====================================================================================
# read files like:
# var1=value1
# varN=valueN


def read_varlist_file(filepath: str, comment_char: str = "#") -> Dict[str, str]:
    """
    Read a file containing variable-value pairs.

    Args:
        filepath (str): Path to the file.
        comment_char (str, optional): Character used to indicate a comment line. Defaults to "#".

    Returns:
        Dict[str, str]: A dictionary containing the variables and their values.

    Raises:
        IOError: If the file does not exist.

    """
    data: Dict[str, str] = {}
    if not os.path.exists(filepath):
        raise IOError(f"File {filepath} does not exist.")

    with open(filepath, "r") as f:

        lines = f.readlines()
        for line in lines:

            if line[0] == comment_char:
                continue
            values = line.rstrip().split("=")  # also remove trailing characters
            data[values[0]] = values[1]
    return data


# get a data list and return a \n separated string
def list2spm_text_column(datalist: List[Any]) -> str:
    """
    Convert a list of data into a SPM-formatted text column. numbers separated by \n without trailing square brackets

    Args:
        datalist (List[Any]): A list of data.

    Returns:
        str: A SPM-formatted text column.

    """
    datastr = ""

    for r in datalist:
        datastr += (str(r) + "\n")

    # remove starting [ and ending ] brackets if present.
    datastr = datastr.replace("[", "")
    datastr = datastr.replace("]", "")
    return datastr


# read a csv with header and returns a list of rows
def read_csv(data_file: str, delimiter: str = ",") -> List[Dict[str, str]]:
    """
    Read a CSV file and return a list of dictionaries, where each dictionary represents a row.

    Args:
        data_file (str): Path to the CSV file.
        delimiter (str, optional): Delimiter used in the CSV file. Defaults to ",".

    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary represents a row in the CSV file.

    Raises:
        IOError: If the file does not exist.

    """
    data: List[Dict[str, str]] = []
    if not os.path.exists(data_file):
        raise IOError(f"File {data_file} does not exist.")

    with open(data_file) as f:
        file_data = csv.reader(f, delimiter=delimiter)
        headers = next(file_data)
        for i in file_data:
            data.append(dict(zip(headers, i)))
    return data


# write a separated text file
def write_lists(outfile: str, header: List[str], data: List[List[Any]], separator: str = "\t"):
    """
    Write a list of data to a text file, with each column separated by a separator.

    Args:
        outfile (str): Path to the output file.
        header (List[str]): A list of column headers.
        data (List[List[Any]]): A list of data, where each element in the list represents a row.
        separator (str, optional): Separator used to separate columns. Defaults to "\t".

    Raises:
        ValueError: If the number of elements in the header list and the data list do not match.

    """
    nelem = len(data[0])
    if len(header) != nelem:
        raise ValueError(f"Error in write_lists. number of header's and data's elements differs")

    for d in data:
        if len(d) != nelem:
            raise ValueError(f"Error in write_lists. number of data's elements differs")

    txt = listToString(header) + "\n"
    r = ""
    for row in data:
        for field in row:
            r += (str(field) + separator)
        r = r.rstrip(separator) + "\n"
    txt += r
    write_text_file(outfile, txt)


# read the output file of fslmeants, create subjlabel and value columns
def process_results(filepath: str, subjs_list: List[str], outname: str, dataprecision: str = ".3f") -> List[str]:
    """
    Read the output file of FSL MEANTS and create subject label and value columns.

    Args:
        filepath (str): Path to the MEANTS output file.
        subjs_list (List[str]): A list of subject labels.
        outname (str): Path to the output file.
        dataprecision (str, optional): Number of decimal places to use for formatting the values. Defaults to ".3f".

    Returns:
        List[str]: A list of strings, where each string represents a line of the output file.

    Raises:
        IOError: If the input file does not exist.

    """
    list_str: List[str] = []
    if not os.path.exists(filepath):
        raise IOError(f"File {filepath} does not exist.")

    with open(filepath) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    nsubj = len(content)

    for i in range(nsubj):
        list_str.append(subjs_list[i] + "\t" + format(float(content[i]), dataprecision))

    row = "\n".join(list_str)
    with open(outname, "w") as fout:
        fout.write(row)

    return list_str


# read file, split in two columns (1-56 & 57-112), add a third column with the difference.
def process_results2tp(fname: str, subjs_list: List[str], outname: str, dataprecision: str = ".3f") -> List[str]:
    """
    Read a file and split it into two columns (1-56 & 57-112), add a third column with the difference.

    Args:
        fname (str): Path to the input file.
        subjs_list (List[str]): A list of subject labels.
        outname (str): Path to the output file.
        dataprecision (str, optional): Number of decimal places to use for formatting the values. Defaults to ".3f".

    Returns:
        List[str]: A list of strings, where each string represents a line of the output file.

    Raises:
        IOError: If the input file does not exist.

    """
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    nsubj = len(content)

    list_str = []
    for i in range(int(nsubj / 2)):
        list_str.append(subjs_list[i] + "\t" + format(float(content[i]), dataprecision) + "\t" + format(
            float(content[i + int(nsubj / 2)]), dataprecision) + "\t" + format(
            float(content[i + int(nsubj / 2)]) - float(content[i]), dataprecision))

    row = "\n".join(list_str)
    with open(outname, "w") as fout:
        fout.write(row)

    return list_str


# read the three values within ICV-SPM file and return their sum
def get_icv_spm_file(filepath: str) -> float:
    """
    Reads the ICV-SPM file and returns the ICV.

    Args:
        filepath (str): Path to the ICV-SPM file.

    Returns:
        float: The ICV value.

    Raises:
        IOError: If the file does not exist.

    """
    if not os.path.exists(filepath):
        raise IOError(f"File {filepath} does not exist.")

    with open(filepath, "r") as f:
        content = f.readlines()

    secondline = str(content[1].strip())
    values = secondline.split(",")

    return float(values[1]) + float(values[2]) + float(values[3])


def get_file_header(filepath: str, delimiter: str = '\t') -> List[str]:
    """
    Reads the first line of a file and returns the values as a list.

    Args:
        filepath (str): Path to the file.
        delimiter (str, optional): Delimiter used in the file. Defaults to '\t'.

    Returns:
        List[str]: A list of values from the first line of the file.

    Raises:
        IOError: If the file does not exist.

    """
    if not os.path.exists(filepath):
        raise IOError(f"File {filepath} does not exist.")

    with open(filepath, "r") as f:
        reader = csv.reader(f, dialect='excel', delimiter=delimiter)
        for row in reader:
            if reader.line_num == 1:
                return row
    return []


def demean_serie(serie: list, ndecim: int = 4) -> list:
    """
    This function takes a list of numbers as input and returns a list of the demeaned values.

    Parameters:
    serie (list): input list of numbers
    ndecim (int): number of decimal places to round the demeaned values to (default: 4)

    Returns:
    list: list of demeaned values
    """
    m = mean(serie)
    return [round(v - m, ndecim) for v in serie]


class FilterValues:

    def __init__(self, colname:str, operation:str, par1, par2=None):

        self.colname= colname
        self.op     = operation
        self.par1   = par1
        self.par2   = par2

    def isValid(self, value:Any):
        """
        Check if a value is valid according to the filter conditions.

        Parameters
        ----------
        value : any
            The value to be checked.

        Returns
        -------
        bool
            True if the value is valid, False otherwise.

        """
        if self.op == "=" or self.op == "==":
            return value == self.par1
        elif self.op == "!=":
            return value != self.par1
        elif self.op == ">":
            return value > self.par1
        elif self.op == ">=":
            return value >= self.par1
        elif self.op == "<":
            return value < self.par1
        elif self.op == "<=":
            return value <= self.par1
        elif self.op == "<>":
            return self.par2 > value > self.par1
        elif self.op == "<=>":
            return self.par2 >= value >= self.par1
        elif self.op == "exist":
            if str(value) == "" or str(value).lower() == "na" or str(value).lower() == "nan":
                return False
            else:
                return True
        elif self.op == "noexist":
            if str(value) == "" or str(value).lower() == "na" or str(value).lower() == "nan":
                return True
            else:
                return False

    def areValid(self, values:List[Any]):
        """
        Check if a list of values is valid according to the filter conditions.

        Parameters
        ----------
        values : list
            The list of values to be checked.

        Returns
        -------
        list
            A list containing the filtered values that are valid and the corresponding validity status (True or False).

        """
        res = []
        valid = []
        if self.op == "=" or self.op == "==":
            if values == self.par1:
                res.append(values)
                valid.append(True)
            else:
                valid.append(False)
        elif self.op == ">":
            if values > self.par1:
                res.append(values)
        elif self.op == ">=":
            if values >= self.par1:
                res.append(values)
                valid.append(True)
            else:
                valid.append(False)
        elif self.op == "<":
            if values < self.par1:
                res.append(values)
                valid.append(True)
            else:
                valid.append(False)
        elif self.op == "<=":
            if values <= self.par1:
                res.append(values)
                valid.append(True)
            else:
                valid.append(False)
        elif self.op == "<>":
            if self.par2 > values > self.par1:
                res.append(values)
                valid.append(True)
            else:
                valid.append(False)
        elif self.op == "<=>":
            if self.par2 >= values >= self.par1:
                res.append(values)
                valid.append(True)
            else:
                valid.append(False)
        return res, valid
