import shutil
import traceback
import zipfile

from DataProject import DataProject
from Global import Global
from data.DataDict import DataDict
from data.utilities import *
from utility.exceptions import SubjectListException
from utility.fileutilities import remove_ext, read_keys_values_from_file

if __name__ == "__main__":

    def get_SubjectDataDict(indir, valid_columns=None):

        subjs_data_dict = SubjectsDataDict()
        for f in os.listdir(indir):
            if f.endswith(".csv"):

                filename_noext  = remove_ext(f)

                data_file       = os.path.join(indir, filename_noext + ".csv")
                subjs_data      = SubjectsDataDict(filepath=data_file, validcols=valid_columns, tonum=True, delimiter=";")
                name, values    = subjs_data.mypop()              # works since each file contains only one subject

                subjs_data_dict.add({filename_noext:values})

        return subjs_data_dict

    def get_SubjectDataDict_zipped(indir, valid_columns=None):

        subjs_data_dict = SubjectsDataDict()
        for f in os.listdir(indir):
            if f.endswith(".zip"):
                temp_dir = os.path.join(indir, "temp")
                os.makedirs(temp_dir, exist_ok=True)

                file_name       = os.path.join(indir, f)  # get full path of files
                filename_noext  = remove_ext(f)

                zip_ref         = zipfile.ZipFile(file_name)    # create zipfile object
                zip_ref.extractall(temp_dir)                    # extract file to dir
                zip_ref.close()                                 # close file

                data_file       = os.path.join(temp_dir, filename_noext + ".csv")
                subjs_data      = SubjectsDataDict(filepath=data_file, validcols=valid_columns, tonum=True, delimiter=";")
                name, values    = subjs_data.pop()              # works since each file contains only one subject

                subjs_data_dict.add({filename_noext:values})

        return subjs_data_dict

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
        datafile            = os.path.join(project.script_dir, "data.dat")  # is a tab limited data matrix with a header in the first row
        assoc_file          = os.path.join(project.script_dir, "association_file.dat")
        assoc_labels_ceres  = read_keys_values_from_file(assoc_file)  # returns dict with key(ceres filename) / value (actual subj label)

        valid_columns       = [    "Patient ID", "Sex", "Age", "ICV cm3",
                             "Cerebellum mean cortical thickness", "Cerebellum right cortical thickness", "Cerebellum left cortical thickness", "Cerebellum cortical thickness asymmetry",
                             "I-II mean cortical thickness", "I-II right cortical thickness", "I-II left cortical thickness", "I-II cortical thickness asymmetry",
                             "III mean cortical thickness", "III right cortical thickness", "III left cortical thickness",  "III cortical thickness asymmetry",
                             "IV mean cortical thickness", "IV right cortical thickness", "IV left cortical thickness", "IV cortical thickness asymmetry",
                             "V mean cortical thickness", "V right cortical thickness", "V left cortical thickness", "V cortical thickness asymmetry",
                             "VI mean cortical thickness", "VI right cortical thickness", "VI left cortical thickness", "VI cortical thickness asymmetry",
                             "Crus I mean cortical thickness", "Crus I right cortical thickness", "Crus I left cortical thickness", "Crus I cortical thickness asymmetry",
                             "Crus II mean cortical thickness", "Crus II right cortical thickness", "Crus II left cortical thickness", "Crus II cortical thickness asymmetry",
                             "VIIB mean cortical thickness", "VIIB right cortical thickness", "VIIB left cortical thickness", "VIIB cortical thickness asymmetry",
                             "VIIIA mean cortical thickness", "VIIIA right cortical thickness", "VIIIA left cortical thickness", "VIIIA cortical thickness asymmetry",
                             "VIIIB mean cortical thickness", "VIIIB right cortical thickness", "VIIIB left cortical thickness", "VIIIB cortical thickness asymmetry",
                             "IX mean cortical thickness", "IX right cortical thickness", "IX left cortical thickness", "IX cortical thickness asymmetry",
                             "X mean cortical thickness", "X right cortical thickness", "X left cortical thickness", "X cortical thickness asymmetry",
                            "Cerebellum grey matter %", "Cerebellum right grey matter %", "Cerebellum left grey matter %", "Cerebellum grey matter asymmetry",
                            "I-II grey matter %", "I-II right grey matter %", "I-II left grey matter %", "I-II grey matter asymmetry",
                            "III grey matter %", "III right grey matter %", "III left grey matter %", "III grey matter asymmetry", "IV grey matter %", "IV right grey matter %", "IV left grey matter %", "IV grey matter asymmetry",
                            "V grey matter %", "V right grey matter %", "V left grey matter %", "V grey matter asymmetry",
                            "VI grey matter %", "VI right grey matter %", "VI left grey matter %", "VI grey matter asymmetry",
                            "Crus I grey matter %", "Crus I right grey matter %", "Crus I left grey matter %", "Crus I grey matter asymmetry",
                            "Crus II grey matter %", "Crus II right grey matter %", "Crus II left grey matter %", "Crus II grey matter asymmetry",
                            "VIIB grey matter %", "VIIB right grey matter %", "VIIB left grey matter %", "VIIB grey matter asymmetry",
                            "VIIIA grey matter %", "VIIIA right grey matter %", "VIIIA left grey matter %", "VIIIA grey matter asymmetry",
                            "VIIIB grey matter %", "VIIIB right grey matter %", "VIIIB left grey matter %", "VIIIB grey matter asymmetry",
                            "IX grey matter %", "IX right grey matter %", "IX left grey matter %", "IX grey matter asymmetry",
                            "X grey matter %", "X right grey matter %", "X left grey matter %", "X grey matter asymmetry"]

        valid_columns_short = [    "Patient ID", "Sex", "Age", "ICV cm3",
                             "Cerebellum mean cortical thickness",
                             "I-II mean cortical thickness",
                             "III mean cortical thickness",
                             "IV mean cortical thickness",
                             "V mean cortical thickness",
                             "VI mean cortical thickness",
                             "Crus I mean cortical thickness",
                             "Crus II mean cortical thickness",
                             "VIIB mean cortical thickness",
                             "VIIIA mean cortical thickness",
                             "VIIIB mean cortical thickness",
                             "IX mean cortical thickness",
                             "X mean cortical thickness",
                            "Cerebellum grey matter %",
                            "I-II grey matter %",
                            "III grey matter %",
                            "IV grey matter %",
                            "V grey matter %",
                            "VI grey matter %",
                            "Crus I grey matter %",
                            "Crus II grey matter %",
                            "VIIB grey matter %",
                            "VIIIA grey matter %",
                            "VIIIB grey matter %",
                            "IX grey matter %",
                            "X grey matter %"]

        out_valid_columns   = ["subj", "gender", "age", "icv",
                             "cer_ct", "cer_r_ct", "cer_l_ct", "cer_ct as",
                             "I_II_ct", "I_II_r_ct", "I_II_l_ct", "I_II_ct_as",
                             "III_ct", "III_r_ct", "III_l_ct",  "III_ct_as",
                             "IV_ct", "IV_r_ct", "IV_l_ct", "IV_ct_as",
                             "V_ct", "V_r_ct", "V_l_ct", "V_ct_as",
                             "VI_ct", "VI_r_ct", "VI_l_ct", "VI_ct_as",
                             "crus_I_ct", "crus_I_r_ct", "crus_I_l_ct", "crus_I_ct_as",
                             "crus_II_ct", "crus_II_r_ct", "crus_II_l_ct", "crus_II_ct_as",
                             "VIIB_ct", "VIIB_r_ct", "VIIB_l_ct", "VIIB_ct_as",
                             "VIIIA_ct", "VIIIA_r_ct", "VIIIA_l_ct", "VIIIA_ct_as",
                               "VIIIB_ct", "VIIIB_r_ct", "VIIIB_l_ct", "VIIIB_ct_as",
                               "IX_ct", "IX_r_ct", "IX_l_ct", "IX_ct_as",
                               "X_ct", "X_r_ct", "X_l_ct", "X_ct_as",
                               "cer_gm_perc", "cer_r_gm_perc", "cer_l_gm_perc", "cer_gm_as",
                               "I_II_gm_perc", "I_II_r_gm_perc", "I_II_l_gm_perc", "I_II_gm_as",
                               "III_gm_perc", "III_r_gm_perc", "III_l_gm_perc", "III_gm_as",
                               "IV_gm_perc", "IV_r_gm_perc", "IV_l_gm_perc", "IV_gm_as",
                               "V_gm_perc", "V_r_gm_perc", "V_l_gm_perc", "V_gm_as",
                               "VI_gm_perc", "VI_r_gm_perc", "VI_l_gm_perc", "VI_gm_as",
                               "crus_I_gm_perc", "crus_I_r_gm_perc", "crus_I_l_gm_perc", "crus_I_gm_as",
                               "crus_II_gm_perc", "crus_II_r_gm_perc", "crus_II_l_gm_perc", "crus_II_gm_as",
                               "VIIB_gm_perc", "VIIB_r_gm_perc", "VIIB_l_gm_perc", "gm_as",
                               "VIIIA_gm_perc", "VIIIA_r_gm_perc", "VIIIA_l_gm_perc", "VIIIA_gm_as",
                               "VIIIB_gm_perc", "VIIIB_r_gm_perc", "VIIIB_l_gm_perc", "VIIIB_gm_as",
                               "IX_gm_perc", "IX_r_gm_perc", "IX_l_gm_perc", "IX_gm_as",
                               "X_gm_perc", "X_r_gm_perc", "X_l_gm_perc", "X_l_as"]

        out_valid_columns_shorts = ["subj", "gender", "age", "icv",
                             "cer_ct",
                             "I_II_ct",
                             "III_ct",
                             "IV_ct",
                             "V_ct",
                             "VI_ct",
                             "crus_I_ct",
                             "crus_II_ct",
                             "VIIB_ct",
                             "VIIIA_ct",
                             "VIIIB_ct",
                             "IX_ct",
                             "X_ct",
                             "cer_gm_perc",
                             "I_II_gm_perc",
                             "III_gm_perc",
                             "IV_gm_perc",
                             "V_gm_perc",
                             "VI_gm_perc",
                             "crus_I_gm_perc",
                             "crus_II_gm_perc",
                             "VIIB_gm_perc",
                             "VIIIA_gm_perc",
                             "VIIIB_gm_perc",
                             "IX_gm_perc",
                             "X_gm_perc"]

        output_file     = os.path.join(project.stats_input, "ceres_short_15t.dat")

        # parse a folder (eventually takes each zip and unzip it), read the csv file, extract the second row, fill it in a dictionary
        # return a SubjectsDataDict, each value is a dictionary of values
        subjects_data = get_SubjectDataDict(project.input_data_dir, valid_columns=valid_columns_short)

        subjects_data.rename_subjects(assoc_labels_ceres)

        # subjects_data.add_column("hamd", ["1", "2"], [1,2])
        # valid_columns.append("hamd")
        # out_valid_columns.append("hamd")

        subjects_data.save_data(output_file, incolnames=valid_columns_short[1:len(valid_columns_short)], outcolnames=out_valid_columns_shorts[1:len(out_valid_columns_shorts)])

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()