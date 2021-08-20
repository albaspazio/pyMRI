import csv
from utility.utilities import argsort, reorder_list, typeUnknown


class SubjectsDict:

    def __init__(self, filepath=""):

        self.data = {}
        self.num = len(self.data)
        self.labels = []

        if filepath != "":
            self.load(filepath)

    # =====================================================================================
    # DATA EXTRACTION FROM A "SUBJ" DICTIONARY {"a_subj_label":{"a":..., "b":...., }}
    # =====================================================================================

    # assumes that the first column represents subjects' labels (it will act as dictionary's key).
    # creates a dictionary with subj label as key and data columns as a dictionary  {subjlabel:{"a":..., "b":..., }}
    def load(self, filepath):

        self.data = {}
        with open(filepath, "r") as f:
            reader = csv.reader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if reader.line_num == 1:
                    header = row
                else:
                    data_row = {}
                    cnt=0
                    for elem in row:
                        if cnt == 0:
                            subj_lab = elem
                        else:
                            data_row[header[cnt]] = elem
                        cnt = cnt+1
                    self.data[subj_lab] = data_row
                    self.labels.append(subj_lab)

            self.num = len(self.data)
            return self.data

    # works with a "subj" dict
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
                print("Error in get_filtered_subj_dict_column: given subject (" + subj + ") is not present in the given list...returning.....")
                return

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    # works with a "subj" dict
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
                colvalue = typeUnknown(self.data[subj][colname])
                res.append(colvalue)
                lab.append(subj)
            except KeyError:
                print("Error in get_filtered_subj_dict_column: given subject (" + subj + ") is not present in the given list...returning.....")
                return

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    # works with a "subj" dict
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
                colvalue = typeUnknown(self.data[subj][colname])
                if operation == "=" or operation == "==" :
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
                print("Error in get_filtered_subj_dict_column: given subject (" + subj + ") is not present in the given list...returning.....")
                return

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    # works with a "subj" dict
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
                colvalue = typeUnknown(self.data[subj][colname])
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
                print("Error in get_filtered_column: given subject (" + subj + ") is not present in the given list...returning.....")
                return

        if sort is True:
            sort_schema = argsort(res)
            res.sort()
            lab = reorder_list(lab, sort_schema)

        return res, lab

    # =====================================================================================
