import csv
import os


# =====================================================================================
# DATA EXTRACTION FROM A PLAIN DICTIONARY
# =====================================================================================
# returns       [ {"subj":..., "col1":..., "col2":... }, {"subj":..., "col1":..., "col2":... }, ....]

class DataDict:
    def __init__(self, filepath=""):

        self.data       = {}
        self.labels     = []
        self.filepath   = filepath

        if filepath != "":
            self.load(filepath)
        self.num    = len(self.data)

    def load(self, filepath):

        self.data = []
        if not os.path.exists(filepath):
            print("ERROR in SubjectsDataDict.load, given filepath param (" + filepath + ") is not a file")
            return self.data

        with open(filepath, "r") as f:
            reader = csv.reader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if reader.line_num == 1:
                    header = row
                else:
                    data_row = {}
                    cnt = 0
                    for elem in row:
                        data_row[header[cnt]] = elem
                        cnt = cnt + 1
                    self.data.append(data_row)

            return self.data

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

