import csv

def read_varlist_file(filepath, comment_char="#"):
    data = {}
    with open(filepath, "r") as f:
        
        lines = f.readlines()
        for line in lines:
            
            if line[0] == comment_char:
                continue
            values = line.rstrip().split("=")   # also remove trailing characters
            data[values[0]] = values[1]
    return data

# =====================================================================================
# DATA EXTRACTION FROM A PLAIN DICTIONARY [{"a":..., "b":...., }]
# =====================================================================================
# returns a list of filtered
def tabbed_file_with_header2dict_list(filepath):
    data = []
    with open(filepath, "r") as f:
        reader = csv.reader(f, dialect='excel', delimiter='\t')
        for row in reader:
            if reader.line_num == 1:
                header = row
            else:
                data_row = {}
                cnt=0
                for elem in row:
                    data_row[header[cnt]] = elem
                    cnt = cnt+1
                data.append(data_row)

        return data

# =====================================================================================
# DATA EXTRACTION FROM A "SUBJ" DICTIONARY {"a_subj_label":{"a":..., "b":...., }}
# =====================================================================================

# assumes that the first column represents subjects' labels (it will act as dictionary's key).
# creates a dictionary with subj label as key and data columns as a dictionary  {subjlabel:{"a":..., "b":..., }}
def tabbed_file_with_header2subj_dic(filepath):

    data = {}
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
                        if elem == "T15_P_134":
                            a=1
                    else:
                        data_row[header[cnt]] = elem
                    cnt = cnt+1
                data[subj_lab] = data_row
        return data

# works with a "subj" dict
# returns a filtered matrix [subj x colnames]
def get_filtered_subj_dict_columns(dic, colnames, subj_labels):

    res = []
    for subj in subj_labels:
        try:
            subj_dic = dic[subj]
            subj_row = []
            for colname in colnames:
                subj_row.append(subj_dic[colname])
            res.append(subj_row)
        except KeyError:
            print("Error in get_filtered_subj_dict_column: given subject (" + subj + ") is not present in the given list...returning.....")
            return
    return res

# works with a "subj" dict
# returns a filtered vector [nsubj]
def get_filtered_subj_dict_column(dic, colname, subj_labels):

    res = []
    for subj in subj_labels:
        try:
            subj_dic = dic[subj]
            res.append(subj_dic[colname])
        except KeyError:
            print("Error in get_filtered_subj_dict_column: given subject (" + subj + ") is not present in the given list...returning.....")
            return
    return res

# =====================================================================================
# =====================================================================================
# return a list of values from a given column
def get_dict_column(dic, colname):
    return [d[colname] for d in dic]

def get_filtered_dict_column(dic, colname, filt_col="", filter=None):

    if filt_col != "":
        res = []
        if filter is not None and isinstance(filter, list):
            for d in dic:
                if d[filt_col] in filter:
                    res.append(d[colname])
            return res
        else:
            print("Error in get_filtered_dict_column")
    else:
        return get_dict_column(dic, colname)

# get a data list and return a \n separated string
def list2spm_text_column(datalist):
    datastr = ""

    for r in datalist:
        datastr = datastr + str(r) + "\n"
    return datastr


# read file, create subjlabel and value columns
def process_results(fname, subjs_list, outname, dataprecision='.3f'):
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    nsubj = len(content)

    list_str = []
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
        list_str.append(subjs_list[i] + "\t" + format(float(content[i]), dataprecision) + "\t" + format(float(content[i + int(nsubj / 2)]), dataprecision) + "\t" + format(float(content[i + int(nsubj / 2)]) - float(content[i]), dataprecision))

    row = "\n".join(list_str)
    with open(outname, "w") as fout:
        fout.write(row)

    return list_str

    #     content = f.readlines()
    #     # you may also want to remove whitespace characters like `\n` at the end of each line
    # content = [x.strip() for x in content]
    # nlines = len(content)
    #
    # header = content[0]


