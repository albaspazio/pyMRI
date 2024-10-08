import traceback

from DataProject import DataProject
from Global import Global
from data.importer.VolBrainImporter import VolBrainImporter
from data.utilities import *
from myutility.exceptions import SubjectListException

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
        proj_dir = "/data/MRI/pymri_projects_scripts/volbrain"
        project             = DataProject(proj_dir)

        # input
        csv_folder          = os.path.join(project.input_data_dir, "3T")

        # output
        output_file         = os.path.join(project.output_data_dir, "ceres_short_3t.xlsx")

        # ======================================================================================================================
        # START !!!
        # ======================================================================================================================
        # parse folder, create structure, save it to excel
        VolBrainImporter(csv_folder, output_file)

        # parse folder, return structure
        ceres_importer  = VolBrainImporter(csv_folder)
        subjs_data      = ceres_importer.subs_data

        # .... edit df .....

        subjs_data.save_data(output_file)

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()
