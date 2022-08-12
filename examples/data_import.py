from Global import Global
from Project import Project

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
        group_label = "all_46_seq1"
        subjects = project.load_subjects(group_label, SESS_ID)

        datafile = os.path.join(project.script_dir, "data.dat")  # is a tab limited data matrix with a header in the first row
        # ==================================================================================================================
        # test getting filtered data columns
        data = SubjectsDataDict(datafile)

        age             = data.get_column("age")
        age_subj_subset = data.get_filtered_column("age", project.get_subjects_labels("test"))  # extract age from a subset of loaded subjects
        cat_dist        = data.get_filtered_column_by_value("cat_dist", 0)
        age_withinvalues= data.get_filtered_column_within_values("age", 1800, 2500)
        age_str = data.get_column_str("age")
        print(age_str)

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        print(e)
        exit()


