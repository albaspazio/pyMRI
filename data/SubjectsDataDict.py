import csv
import os

from utility.exceptions import DataFileException
from utility.utilities import argsort, reorder_list, string2num, write_text_file, listToString


# =====================================================================================
# DATA EXTRACTION FROM A "SUBJ" DICTIONARY
# =====================================================================================
# assumes that the first column represents subjects' labels (it will act as dictionary's key).
# creates a dictionary with subj label as key and data columns as a dictionary
# returns   { "label1":{"col1", ..., "colN"}, "label2":{"col1", ..., "colN"}, .....}

class SubjectsDataDict:

    def __init__(self, filepath=""):

        self.data       = {}
        self.labels     = []
        self.filepath   = filepath

        if filepath != "":
            self.load(filepath)
        self.num        = len(self.data)
        self.header     = self.get_header()

    # =====================================================================================
    # DATA EXTRACTION FROM A "SUBJ" DICTIONARY {"a_subj_label":{"a":..., "b":...., }}
    # =====================================================================================

    # assumes that the first column represents subjects' labels (it will act as dictionary's key).
    # creates a dictionary with subj label as key and data columns as a dictionary  {subjlabel:{"a":..., "b":..., }}
    # tonum defines whether checking string(ed) type and convert to int/float
    # filepath CANNOT be empty
    def load(self, filepath, tonum=True):

        self.data = {}
        if os.path.exists(filepath) is False:
            raise DataFileException("SubjectsDataDict.load", "given filepath param (" + filepath + ") is not a file")

        with open(filepath, "r") as f:
            reader = csv.reader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if reader.line_num == 1:
                    header = row
                else:
                    if len(row) == 0:
                        break

                    data_row = {}
                    cnt = 0
                    for elem in row:
                        if cnt == 0:
                            subj_lab = elem
                        else:
                            casted_elem             = string2num(elem)
                            data_row[header[cnt]]   = casted_elem
                        cnt = cnt + 1
                    self.data[subj_lab] = data_row
                    self.labels.append(subj_lab)

            self.num        = len(self.data)
            self.filepath   = filepath
            return self.data

    # return a list of values from a given column
    def get_column(self, colname):
        return [self.data[d][colname] for d in self.data]

    def get_column_str(self, colname, ndecimals=3):
        return self.__to_str(self.get_column(colname), ndecimals)

    # returns two vectors filtered by [subj labels]
    # - [values]
    # - [labels]
    def get_filtered_column(self, colname, subj_labels=None, sort=False):

        if subj_labels is None:
            subj_labels = self.labels

        res = []
        lab = []
        for subj in subj_labels:
            try:
                colvalue = string2num(self.data[subj][colname])
                res.append(colvalue)
                lab.append(subj)
            except KeyError:
                raise DataFileException("SubjectsDataDict.get_filtered_column", "data of given subject (" + subj + ") is not present in the loaded data")

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    def get_filtered_column_str(self, colname, ndecimals=3):
        res, lab = self.get_filtered_column(colname)
        res_str = self.__to_str(res, ndecimals)
        return res_str, lab

    # returns a filtered matrix [subj x colnames]
    def get_filtered_columns(self, colnames, subj_labels=None, sort=-1):

        if subj_labels is None:
            subj_labels = self.labels

        res = []
        lab = []

        for subj in subj_labels:
            try:
                subj_dic = self.data[subj]
                subj_row = []
                for colname in colnames:
                    subj_row.append(subj_dic[colname])
                res.append(subj_row)
                lab.append(subj)

            except KeyError:
                raise DataFileException("SubjectsDataDict.get_filtered_columns", "data of given subject (" + subj + ") is not present in the loaded data")

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    # TODO:
    # def get_filtered_columns_str(self, colnames, subj_labels=None, sort=-1, ndecimals=3):
    #     res, lab = self.get_filtered_columns(colnames, subj_labels, sort)
    #     res_str = self.__to_str(res, ndecimals)
    #     return res_str, lab

    # returns two vectors filtered by [subj labels] & value
    # - [values]
    # - [labels]
    def get_filtered_column_by_value(self, colname, value, operation="=", subj_labels=None, sort=False):

        if subj_labels is None:
            subj_labels = self.labels

        res = []
        lab = []
        for subj in subj_labels:
            try:
                colvalue = string2num(self.data[subj][colname])
                if operation == "=" or operation == "==":
                    if colvalue == value:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == ">":
                    if colvalue > value:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == ">=":
                    if colvalue >= value:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == "<":
                    if colvalue < value:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == "<=":
                    if colvalue <= value:
                        res.append(colvalue)
                        lab.append(subj)

            except KeyError:
                raise DataFileException("SubjectsDataDict.get_filtered_column_by_value", "data of given subject (" + subj + ") is not present in the loaded data")

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    def get_filtered_column_by_value_str(self, colname, value, operation, subj_labels=None, sort=False, ndecimals=3):
        res, lab = self.get_filtered_column_by_value(colname, value, operation, subj_labels, sort)
        res_str = self.__to_str(res, ndecimals)
        return res_str, lab

    # returns two vectors filtered by [subj labels] & whether value is within value1/2
    # - [values]
    # - [labels]
    def get_filtered_column_within_values(self, colname, value1, value2, operation="<>", subj_labels=None, sort=False):

        if subj_labels is None:
            subj_labels = self.labels

        res = []
        lab = []
        for subj in subj_labels:
            try:
                colvalue = string2num(self.data[subj][colname])
                if operation == "<>":
                    if value2 > colvalue > value1:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == "<=>":
                    if value2 >= colvalue > value1:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == "<=>=":
                    if value2 >= colvalue >= value1:
                        res.append(colvalue)
                        lab.append(subj)
                elif operation == "<>=":
                    if value2 > colvalue >= value1:
                        res.append(colvalue)
                        lab.append(subj)

            except KeyError:
                raise DataFileException("SubjectsDataDict.get_filtered_column_within_values", "data of given subject (" + subj + ") is not present in the loaded data")

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    def get_filtered_column_within_values_str(self, colname, value1, value2, operation="<>", subj_labels=None, sort=False, ndecimals=3):
        res, lab = self.get_filtered_column_within_values(colname, value1, value2, operation, subj_labels, sort)
        res_str = self.__to_str(res, ndecimals)
        return res_str, lab

    def add_column(self, col_label, values, saveit=True):
        nv = len(values)
        if nv != self.num:
            print("ERROR in SubjectsDataDict.add")

        cnt = 0
        for slab in self.data:
            self.data[slab][col_label] = values[cnt]
            cnt = cnt + 1

        self.header = self.get_header()

        if saveit is True:
            self.save_data()


    def get_header(self):
        self.header = ["subj"]
        for row in self.data:
            for field in self.data[row]:
                self.header.append(field)
            break
        return self.header

    def exist_column(self, colname):
        return colname in self.header

    def exist_filled_column(self, colname, subj_labels=None):

        if colname in self.header is False:
            return False

        if subj_labels is None:
            labs = self.labels
        else:
            labs = subj_labels

        for lab in labs:
            elem = self.data[lab][colname]
            if len(str(elem)) == 0:
                return False

        return True

    # TODO: fix data save
    def save_data(self, data_file=None):

        if data_file is None:
            data_file = self.filepath

        txt = listToString(self.header) + "\n"
        for row in self.data:
            r = ""
            for field in row:
                r = field + "\t"
            r = r.rstrip('\t') + "\n"
        txt = txt + r
        write_text_file(data_file, txt)

    # =====================================================================================
    # get a data list and return a \n separated string, suitable for spm template files
    def __to_str(self, datalist, ndecimals=3):
        datastr = ""

        for r in datalist:
            rr = str(round(r*ndecimals*10)/(ndecimals*10))
            datastr = datastr + rr + "\n"
        return datastr
    # =====================================================================================
