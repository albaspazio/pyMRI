import os

from Global import Global
from Project import Project

from utility.import_data_file import *


if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "601"
    try:
        globaldata = Global(fsl_code)
    except Exception as e:
        print(e)
        exit()

    # ======================================================================================================================
    # HEADER
    # ======================================================================================================================
    proj_dir    = "/data/MRI/projects/T15"
    project     = Project(proj_dir, globaldata)
    SESS_ID     = 1
    num_cpu     = 1
    group_label = "all"
    subjects    = project.load_subjects(group_label, SESS_ID)

    datafile    = os.path.join(project.script_dir, "data.dat")  # is a tab limited data matrix with a header in the first row
    #==================================================================================================================
    # test getting filtered data columns
    data        = tabbed_file_with_header2dict_list(datafile)
    age         = get_dict_column(data, "age")
    age         = get_filtered_dict_column(data, "age", "subj", project.get_list_by_label("test"))
    age         = get_filtered_dict_column(data, "age", "cat_dist", ['0'])
    str         = list2spm_text_column(age)

    # create a convenient dictionary with each (unique) subject label as key and a dictionary of scores as value
    data1       = tabbed_file_with_header2subj_dic(datafile)
    matrix      = get_filtered_subj_dict_columns(data1, ["group", "age"], project.get_list_by_label("single"))







