import csv
import os

# =====================================================================================
# DATA EXTRACTION FROM A PLAIN DICTIONARY
# =====================================================================================
# returns       [ {"subj":..., "col1":..., "col2":... }, {"subj":..., "col1":..., "col2":... }, ....]
from utility.exceptions import DataFileException
from utility.utilities import string2num, listToString, write_text_file


class DataDict:
    def __init__(self, filepath="", tonum=True, delimiter='\t'):

        self.data       = {}
        self.filepath   = filepath

        if filepath != "":
            self.load(filepath, tonum, delimiter)

    @property
    def header(self):
        return self.get_header()

    @property
    def num(self):
        return len(self.data)

    def load(self, filepath, tonum=True, delimiter='\t'):

        self.data = []
        if not os.path.exists(filepath):
            raise DataFileException("DataDict.load", "given filepath param (" + filepath + ") is not a file")

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
                        if tonum:
                            casted_elem = string2num(elem)
                        else:
                            casted_elem = elem
                        data_row[header[cnt]] = casted_elem
                        cnt = cnt + 1
                    self.data.append(data_row)

            return self.data

    def get_header(self):
        header = []
        for field in self.data[0]:
            header.append(field)
        return header

    # return a list of values from a given column
    def get_dict_column(self, colname):
        return [d[colname] for d in self.data]

    def get_filtered_dict_column(self, colname, filt_col="", filt=None):
        if filt_col != "":
            res = []
            if filt is not None and isinstance(filt, list):
                for d in self.data:
                    if d[filt_col] in filt:
                        res.append(d[colname])
                return res
            else:
                print("Error in get_filtered_dict_column")
        else:
            return self.get_dict_column(colname)

    def get_values(self, valid_columns):
        datas = []
        for row in self.data:
            values = []
            for col in valid_columns:
                values.append(string2num(row[col]))
            datas.append(values)

        return datas

    def save_data(self, data_file=None):

        if data_file is None:
            data_file = self.filepath

        txt = listToString(self.header) + "\n"
        r = ""
        for row in self.data:
            r = ""
            for field in row:
                r = field + "\t"
            r = r.rstrip('\t') + "\n"
        txt = txt + r
        write_text_file(data_file, txt)
