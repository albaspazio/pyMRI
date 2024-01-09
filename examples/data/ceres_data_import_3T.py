import shutil
import traceback
import zipfile

from DataProject import DataProject
from Global import Global
from data.MSHDB import MSHDB
from data.SubjectsData import SubjectsData
from data.CeresImporter import CeresImporter
from data.utilities import *
from utility.exceptions import SubjectListException
from utility.fileutilities import remove_ext, read_keys_values_from_file

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
        proj_name           = "ceres"
        project             = DataProject(proj_name, globaldata)

        # input
        csv_folder          = os.path.join(project.input_data_dir, "3T")

        # output
        output_file         = os.path.join(project.stats_input, "ceres_short_3t.xlsx")

        # ======================================================================================================================
        # START !!!
        # ======================================================================================================================
        # parse folder, create structure, save it to excel
        CeresImporter(csv_folder, output_file)

        # parse folder, return structure
        ceres_importer  = CeresImporter(csv_folder)
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
