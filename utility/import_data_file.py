import csv

def read_tabbed_file_with_header(filepath):

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
        datastr = datastr + r + "\n"
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


