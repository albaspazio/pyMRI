from Global import Global
from Project import Project
from data.SubjectsDataDict import SubjectsDataDict

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

        datafile = os.path.join(project.script_dir, "data.dat")  # is a tab limited data matrix with a header in the first row
        # ==================================================================================================================
        # test getting filtered data columns
        data = SubjectsDataDict(filepath=datafile)

        age              = data.get_column("age")
        age_subj_subset  = data.get_filtered_columns_by_subjects(["age", "FS0"], project.get_subjects_labels("all", must_exist=False))  # extract age from a subset of loaded subjects
        age_subj_subset2 = data.get_filtered_columns_by_values(["age", "FS0"],   project.get_subjects_labels("all", must_exist=False))  # extract age from a subset of loaded subjects

        cat_dist        = data.get_filtered_column_by_value("age", 26)
        age_withinvalues= data.get_filtered_column_within_values("age", 30, 60)
        age_str = data.get_column_str("age")
        print(age_str)

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        print(e)
        exit()


