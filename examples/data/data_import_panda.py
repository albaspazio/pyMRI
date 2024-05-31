from Global import Global
from Project import Project
from data.SubjectsData import SubjectsData

from data.utilities import *
from utility.exceptions import SubjectListException

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = Global(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        proj_dir = "/data/MRI/projects/test"
        project = Project(proj_dir, globaldata)
        SESS_ID = 1
        num_cpu = 1
        group_label = "all"
        subjects = project.load_subjects(group_label, SESS_ID, must_exist=False)

        test_labels = project.get_subjects_labels("test", must_exist=False)
        valid_cols  = ["age", "FS0"]
        datafile = os.path.join(project.script_dir, "data.xlsx")  # is a tab limited data matrix with a header in the first row
        # datafile = os.path.join(project.script_dir, "data.dat")  # is a tab limited data matrix with a header in the first row
        # ==================================================================================================================
        # test getting filtered data columns
        data = SubjectsData(data=datafile)

        # extract data
        age              = data.get_subjects_column(colname="age")
        select_df        = data.select_df(test_labels, valid_cols)  # DATAFRAME
        select_data      = data.get_subjects_values_by_cols(test_labels, valid_cols)  # MATRIX[cols,subjs] list of subjects' columns values
        select_dicts     = data.get_subjects(test_labels, valid_cols)  # List[dict]

        male_ages       = data.get_filtered_column(colname="age", select_conds=[FilterValues("gender", "==", 1)])
        ages_betweenages= data.get_filtered_column(colname="age", select_conds=[FilterValues("age", "<>", 30, 60)])
        age_str         = data.get_subjects_column_str(colname="age")
        a=1
        # cat_dist        = data.get_filtered_column_by_value("age", 26)
        # age_withinvalues= data.get_filtered_column_within_values("age", 30, 60)
        # age_str = data.get_column_str("age")
        # print(age_str)

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        print(e)
        exit()


