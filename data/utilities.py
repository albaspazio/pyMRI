import csv
import os


# =====================================================================================
# ACCESSORY
# =====================================================================================

# read files like:
# var1=value1
# varN=valueN
from data.SubjectsDataDict import SubjectsDataDict
from utility.exceptions import DataFileException

# read file as:   lab1=val1\nlab2=val2\n....etc
from utility.utilities import listToString
from utility.fileutilities import write_text_file


def read_varlist_file(filepath, comment_char="#"):
    data = {}
    if not os.path.exists(filepath):
        print("ERROR in read_varlist_file, given filepath param (" + filepath + ") is not a file")
        return data

    with open(filepath, "r") as f:

        lines = f.readlines()
        for line in lines:

            if line[0] == comment_char:
                continue
            values = line.rstrip().split("=")  # also remove trailing characters
            data[values[0]] = values[1]
    return data


# get a data list and return a \n separated string
def list2spm_text_column(datalist):
    datastr = ""

    for r in datalist:
        datastr += (str(r) + "\n")
    return datastr


# read a csv with header and returns a list of rows
def read_csv(data_file, delimiter=","):
    data = []
    with open(data_file) as f:
        file_data = csv.reader(f, delimiter=delimiter)
        headers = next(file_data)
        for i in file_data:
            data.append(dict(zip(headers, i)))
    return data


# write a separated text file
def write_lists(outfile, header, data, separator="\t"):

    nelem = len(data[0])
    if len(header) != nelem:
        raise Exception("Error in write_lists. number of header's and data's elements differs")

    for d in data:
        if len(d) != nelem:
            raise Exception("Error in write_lists. number of data's elements differs")

    txt = listToString(header) + "\n"
    r = ""
    for row in data:
        for field in row:
            r += (str(field) + separator)
        r = r.rstrip(separator) + "\n"
    txt += r
    write_text_file(outfile, txt)


# read the output file of fslmeants, create subjlabel and value columns
def process_results(filepath, subjs_list, outname, dataprecision='.3f'):
    list_str = []
    if not os.path.exists(filepath):
        print("ERROR in process_results, given filepath param (" + filepath + ") is not a file")
        return list_str

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
def process_results2tp(fname, subjs_list, outname, dataprecision=".3f"):
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
def get_icv_spm_file(filepath):
    with open(filepath) as f:
        content = f.readlines()

    secondline = str(content[1].strip())
    values = secondline.split(",")

    return float(values[1]) + float(values[2]) + float(values[3])


def get_file_header(filepath, delimiter='\t'):
    if not os.path.exists(filepath):
        print("ERROR in get_file_header, given filepath param (" + filepath + ") is not a file")
        return []

    with open(filepath, "r") as f:
        reader = csv.reader(f, dialect='excel', delimiter=delimiter)
        for row in reader:
            if reader.line_num == 1:
                return row
    return []


# ---------------------------------------------------------------------------
# validate data
# ---------------------------------------------------------------------------
def validate_datafile_with_covs(data_file=None, covs=None):

    if covs is None:
        covs = []

    header = []
    if data_file is not None:
        if not os.path.exists(data_file):
            raise DataFileException("validate_datafile_with_covs", "given data_file (" + str(data_file) + ") does not exist")

        header = SubjectsDataDict(data_file).get_header()  # get_header_of_tabbed_file(data_file)

        # if all(elem in header for elem in regressors) is False:  if I don't want to understand which cov is absent
        missing_covs = ""
        for cov in covs:
            if not cov.name in header:
                missing_covs = missing_covs + cov.name + ", "

        if len(missing_covs) > 0:
            raise DataFileException("validate_datafile_with_covs", "the following header are NOT present in the given datafile: " + missing_covs)

    return header


def validate_data_with_covs(data=None, covs=None):

    if covs is None:
        covs = []

    if bool(data):
        if isinstance(data, SubjectsDataDict):
            header = data.get_header()  # get_header_of_tabbed_file(data_file)

            # if all(elem in header for elem in regressors) is False:  if I don't want to understand which cov is absent
            missing_covs = ""
            for cov in covs:
                if not cov.name in header:
                    missing_covs = missing_covs + cov.name + ", "

            if len(missing_covs) > 0:
                raise DataFileException("validate_data_with_covs", "the following header are NOT present in the given datafile: " + missing_covs)

            return header

    raise DataFileException("validate_data_with_covs", "given data (" + str(data) + ") is not valid")

