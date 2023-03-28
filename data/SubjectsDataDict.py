import csv
import os
from collections import Counter

from typing import List

from data.utilities import demean_serie
from utility.exceptions import DataFileException
from utility.utilities import argsort, reorder_list, string2num, listToString
from utility.fileutilities import write_text_file


# =====================================================================================
# DATA EXTRACTION FROM A "SUBJ" DICTIONARY
# =====================================================================================
# assumes that the first column represents subjects' labels (it will act as dictionary's key).
# creates a dictionary with subj label as key and a dictionary of data columns as  value
# returns   { "label1":{"col1", ..., "colN"}, "label2":{"col1", ..., "colN"}, .....}

class SubjectsDataDict(dict):

    def __new__(cls, filepath="", validcols=None, tonum=True, delimiter='\t'):
        return super(SubjectsDataDict, cls).__new__(cls, None)

    def __init__(self, filepath="", validcols=None, tonum=True, delimiter='\t'):

        super().__init__()
        self.filepath = filepath

        if filepath != "":
            self.load(filepath, tonum, delimiter)
            if validcols is not None:
                self.filter_columns(validcols)

    @property
    def header(self) -> list:
        return self.get_header()

    @property
    def labels(self) -> list:
        return list(self.keys())

    @property
    def num(self) -> int:
        return len(self)

    # =====================================================================================
    # DATA EXTRACTION FROM A "SUBJ" DICTIONARY {"a_subj_label":{"a":..., "b":...., }}
    # =====================================================================================

    # assumes that the first column represents subjects' labels (it will act as dictionary's key).
    # creates a dictionary with key = subj label and values = dictionary of data columns   => {subjlabel:{"a":..., "b":..., }}
    # validcols=[list of column to include]
    # tonum defines whether checking string(ed) type and convert to int/float
    # filepath CANNOT be empty
    def load(self, filepath, tonum=True, delimiter='\t') -> dict:

        if not os.path.exists(filepath):
            raise DataFileException("SubjectsDataDict.load", "given filepath param (" + filepath + ") is not a file")

        with open(filepath, "r") as f:
            reader = csv.reader(f, dialect='excel', delimiter=delimiter)
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
                            if tonum:
                                casted_elem = string2num(elem)
                            else:
                                casted_elem = elem
                            data_row[header[cnt]] = casted_elem
                        cnt = cnt + 1

                    self[subj_lab] = data_row

            return self

    # add new subjects
    def add(self, newsubjs, can_overwrite=False, can_add_incomplete=False):

        if not isinstance(newsubjs, dict):
            raise Exception("Error in SubjectsDataDict.add, given newsubjs is not a dictionary")

        names = list(newsubjs.keys())
        nsubjs = len(names)
        if nsubjs == 0:
            raise Exception("Error in SubjectsDataDict.add, given newsubjs is an empty dictionary")

        elems = list(list(newsubjs.values())[0].keys())
        elems.insert(0, "subj")

        for name in names:
            if self.exist_subject(name) and not can_overwrite:
                raise Exception("Error in SubjectsDataDict.add, you are trying to overwrite existing subject " + name)

        if len(self.header) > 0:
            if Counter(elems) != Counter(self.header) and not can_add_incomplete:
                raise Exception("Error in SubjectsDataDict.add, given newsubj does not contain the same elements")

        self.update(newsubjs)

    def filter_columns(self, validcols):
        for subj in self:
            sub_values = {}
            for col in self[subj]:
                if col in validcols:
                    sub_values[col] = self[subj][col]
            self[subj] = sub_values

    def exist_subject(self, subj_name) -> bool:
        try:
            return bool(self[subj_name])
        except:
            return False

    def get_subject(self, subj_lab) -> dict:
        return self[subj_lab]

    def mypop(self, k=None) -> tuple:
        if k is None:
            return self.popitem()
        else:
            try:
                v = self.pop(k)
                return k, v
            except:
                return ()

    def get_subjects_list(self, subj_names=None) -> list:

        if subj_names is None:
            subj_names = self.labels

        try:
            return [self[subj_lab] for subj_lab in subj_names]
        except Exception as e:
            return []

    def get_subset(self, subj_names=None) -> dict:

        if subj_names is None:
            return self
        sdict = {}
        for k, v in self.items():
            if k in subj_names:
                sdict[k] = v
        return sdict

    # return a list of subjects values
    def get_subjects_filtered_columns(self, colnames, subj_names=None):

        if subj_names is None:
            subj_names = self.labels

        try:
            res = {}
            for subj_lab in subj_names:
                data_row = {}
                subj = self[subj_lab]
                for col in colnames:
                    data_row[col] = subj[col]
                res[subj_lab] = data_row
            return res

        except Exception as e:
            return []

    # return a list of values from a given column
    def get_column(self, colname):
        return [self[d][colname] for d in self]

    def get_column_str(self, colname, ndecimals=3):
        return self.__to_str(self.get_column(colname), ndecimals)

    # returns two vectors filtered by [subj labels]
    # - [values]
    # - [labels]
    def get_filtered_column(self, colname, subj_labels=None, sort=False, demean=False, ndecim=4):

        if subj_labels is None:
            subj_labels = self.labels

        res = []
        lab = []
        for subj in subj_labels:
            try:
                colvalue = string2num(self[subj][colname])
                res.append(colvalue)
                lab.append(subj)
            except KeyError:
                raise DataFileException("SubjectsDataDict.get_filtered_column", "data of given subject (" + subj + ") is not present in the loaded data")

        if demean:
            res = demean_serie(res, ndecim)

        if sort:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    def get_filtered_column_str(self, colname, ndecimals=3):
        res, lab = self.get_filtered_column(colname)
        res_str = self.__to_str(res, ndecimals)
        return res_str, lab

    # returns a filtered matrix [subj x colnames]
    def get_filtered_columns(self, colnames, subj_labels=None, sort=False, demean_flags=None, ndecim=4):

        if subj_labels is None:
            subj_labels = self.labels

        subj_values = []
        subj_lab = []

        try:
            # create nsubj * ncols array
            for subj in subj_labels:
                subj_dic = self[subj]
                subj_row = []
                for colname in colnames:
                    subj_row.append(subj_dic[colname])
                subj_values.append(subj_row)
                subj_lab.append(subj)

            if demean_flags is not None:
                if len(colnames) != len(demean_flags):
                    msg = "Error in get_filtered_columns...lenght of colnames is different from demean_flags"
                    raise Exception(msg)
                else:
                    # demean requested columns
                    for idcol, dem_col in enumerate(demean_flags):
                        if dem_col:
                            # calculate demeaned serie
                            vals = []
                            for subj_row in subj_values:
                                vals.append(subj_row[idcol])

                            vals = demean_serie(vals, ndecim)
                            # substitute demenead serie
                            for idsubj, subjvalues in enumerate(subj_values):
                                subj_values[idsubj][idcol] = vals[idsubj]


        except KeyError:
            raise DataFileException("SubjectsDataDict.get_filtered_columns", "data of given subject (" + subj + ") is not present in the loaded data")

        if sort:
            sort_schema = argsort(subj_values)
            subj_values.sort()
            subj_lab = reorder_list(subj_lab, sort_schema)

        return subj_values, subj_lab

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
                colvalue = string2num(self[subj][colname])
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

        if sort:
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
                colvalue = string2num(self[subj][colname])
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

        if sort:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    def get_filtered_column_within_values_str(self, colname, value1, value2, operation="<>", subj_labels=None, sort=False, ndecimals=3):
        res, lab = self.get_filtered_column_within_values(colname, value1, value2, operation, subj_labels, sort)
        res_str = self.__to_str(res, ndecimals)
        return res_str, lab

    def add_column(self, col_label, labels, values, saveit=False):

        nv = len(values)
        nl = len(labels)
        if nv != self.num or nl != self.num:
            print("ERROR in SubjectsDataDict.add")

        cnt = 0
        for subj in labels:
            self[subj][col_label] = values[cnt]
            cnt = cnt + 1

        if saveit:
            self.save_data()

    def get_header(self):

        if len(self) == 0:
            return []

        header = ["subj"]
        for row in self:
            for field in self[row]:
                header.append(field)
            break
        return header

    def validate_covs(self, covs):

        header = self.get_header()  # get_header_of_tabbed_file(data_file)

        # if all(elem in header for elem in regressors) is False:  if I don't want to understand which cov is absent
        missing_covs = ""
        for cov in covs:
            if not cov.name in header:
                missing_covs = missing_covs + cov.name + ", "

        if len(missing_covs) > 0:
            raise DataFileException("validate_covs",
                                    "the following header are NOT present in the given datafile: " + missing_covs)
        return header

    def exist_column(self, colname):
        return colname in self.header

    def exist_filled_column(self, colname, subj_labels=None):

        if colname not in self.header:
            return False

        if subj_labels is None:
            labs = self.labels
        else:
            labs = subj_labels

        for lab in labs:
            elem = self[lab][colname]
            if len(str(elem)) == 0:
                return False

        return True

    # assoc_dict is a dictionary where key is current name and value is the new one
    def rename_subjects(self, assoc_dict):
        for i, (k, v) in enumerate(assoc_dict.items()):
            tup = self.mypop(k)
            if tup:
                self[v] = tup[1]

    # save some columns of a subset of the subjects in given file
    def save_data(self, data_file=None, subj_labels=None, incolnames=None, outcolnames=None, separator="\t"):

        if data_file is None:
            data_file = self.filepath

        if incolnames is None:
            incolnames = self.header[1:len(self.header)]

        if outcolnames is None:
            outcolnames = self.header[1:len(self.header)]

        if subj_labels is None:
            data = self
        else:
            data = self.get_subset(subj_labels)

        txt = "subj" + separator + listToString(outcolnames, separator) + "\n"
        r = ""
        for subj in data:
            r += (subj + separator)
            for col in incolnames:
                try:
                    value = str(data[subj][col])
                except:
                    value = ""
                r += value + separator
            r = r.rstrip(separator) + "\n"
        txt += r
        write_text_file(data_file, txt)

    # =====================================================================================
    # get a data list and return a \n separated string, suitable for spm template files
    @staticmethod
    def __to_str(datalist, ndecimals=3):
        datastr = ""

        for r in datalist:
            rr = str(round(r * ndecimals * 10) / (ndecimals * 10))
            datastr = datastr + rr + "\n"
        return datastr
    # =====================================================================================
