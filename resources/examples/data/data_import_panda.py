from DataProject import DataProject
from data.SubjectsData import SubjectsData

from data.utilities import *
from myutility.exceptions import SubjectListException

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    try:

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        script_dir  = os.path.dirname(__file__)
        project     = DataProject(script_dir, "data.xlsx")
        SESS_ID     = 1
        num_cpu     = 1
        group_label = "all"
        # subjects = project.load_subjects(group_label, SESS_ID, must_exist=False)

        test_labels = project.get_subjects_labels("test")
        valid_cols  = ["age", "FS0"]
        # datafile = os.path.join(project.script_dir, "data.xlsx")  # is a tab limited data matrix with a header in the first row
        # datafile = os.path.join(project.script_dir, "data.dat")  # is a tab limited data matrix with a header in the first row
        # ==================================================================================================================
        # test getting filtered data columns
        data = SubjectsData(data=os.path.join(script_dir, "data.xlsx"))

        # SubjectsData has only one method (filter_subjects) that accept subj_labels, sessions and conditions.
        test_sids       = project.data.filter_subjects(test_labels)

        # with the returned SIDList user can call all its methods
        age             = data.get_subjects_column(colname="age")
        select_df       = data.select_df(test_sids, valid_cols)  # DATAFRAME
        select_data     = data.get_subjects_values_by_cols(test_sids, valid_cols)[0]  # MATRIX[cols,subjs] list of subjects' columns values
        select_dicts    = data.get_sids_dict(test_sids, valid_cols)  # List[dict]

        males           = data.filter_subjects(conditions=[FilterValues("gender", "==", 1)])
        male_ages       = data.get_subjects_column(males, colname="age")

        adults          = data.filter_subjects(conditions=[FilterValues("age", "<>", 18, 60)])
        ages_adults     = data.get_subjects_column(adults, colname="age")

        # DataProject has methods that accept subj_labels, sessions and conditions
        ages_adults2        = project.get_filtered_column("test", "age", select_conds=[FilterValues("age", "<>", 18, 60)])
        ages_gender_adults  = project.get_subjects_values_by_cols("test", ["age", "gender"], select_conds=[FilterValues("age", "<>", 18, 60)])


        age_str         = data.get_subjects_column_str(colname="age")

        a=1

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        print(e)
        exit()


