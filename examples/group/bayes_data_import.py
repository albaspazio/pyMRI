import shutil
import traceback
import zipfile

from DataProject import DataProject
from Global import Global
from data.BayesDB import BayesDB
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
        proj_name           = "test"
        project             = DataProject(proj_name, globaldata)

        bayes_db_file       = os.path.join(project.input_data_dir, "BAYES-PSIC_299.xlsx")        # input


        # ======================================================================================================================
        # START !!!
        # ======================================================================================================================
        # read ALL bayes db
        bayes_db            = BayesDB(bayes_db_file)

        # check is_equal works
        # bayes_db2           = BayesDB(bayes_db_file)
        # bayes_db.is_equal(bayes_db2)

        # ===========================================================================================================
        #region create a new excel after removing some subjects
        # remove 4 subjects and save a new multisheets xls file
        newbayes_db         = bayes_db.remove_subjects(["Finessi Claudio", "Garbarino Marco", "Matta Michela", "Possemato Gianna"])
        newbayes_db_file    = os.path.join(project.input_data_dir, "BAYES-PSIC_295.xlsx")
        newbayes_db.save_excel(newbayes_db_file, sort=["subj"])

        # endregion

        # ============================================================================================================
        #region     GET USEFUL SUBJECTS' LISTS
        # SUBJECTS WITH MRI
        # mrisubj_labels      = bayes_db.mrilabels()[0] # 4 list of subjects with mri (all, td, bd, sz)

        # ============================================================================================================
        # SUBJECTS WITH BLOOD SAMPLES
        # bloodsubj_labels    = bayes_db.bloodlabels()[0] # 6 list of subjects with blood samples (total, th, tr, nk, mono, bi)

        # ============================================================================================================
        # SUBJECTS WITH MRI & BLOOD

        # out_blood_mri_subset = os.path.join(project.stats_input, "blood_mri_db.xlsx")   # set output file
        # bloodmrisubj_labels  = bayes_db.bloodlabels(mrisubj_labels)[0]                  # select, among those having MRI, those having also the blood
        #endregion

        # ============================================================================================================
        # region EXPORT DF TO FILE
        # define which sheets' columns insert into the excel
        # blood_mri_shcol   = {"main"     : ["group", "Eta", "sesso"],
        #                      "clinica"  : ["Durata_di_malattia"],
        #                      "sangue"   : ["CODICE", "blood", "T_HELP", "T_REG", "NK", "MONO", "B"]}
        # blood_mri_df        = bayes_db.select_df(bloodmrisubj_labels, blood_mri_shcol)
        # blood_mri_df.to_excel(out_blood_mri_subset, index=False)
        #endregion

        # ============================================================================================================
        #region     EXPORT BISECTION DATA
        # bisection_shcol   = {"main"     : ["group", "age", "gender"],
        #                      "clinica"  : ["Durata_di_malattia"],
        #                      "OA"       : ["pse_v", "sd_v", "pse_f", "sd_f", "pse_pa", "sd_pa"],
        #                      "PANS"     : ["*"],
        #                      "SANS"     : ["*"],
        #                      "SAPS"     : ["*"],
        #                      "MW S-D"   : ["*"],
        #                      "TATE"     : ["*"],
        #                      "TLC"      : ["*"]
        #                     }
        #
        # bisection_db_file   = os.path.join(project.script_dir, "bisection_db.xlsx")
        # bisection_subj_list = bayes_db.bisection_labels()[0]
        # bisection_df        = bayes_db.select_df(bisection_subj_list, bisection_shcol)
        # bisection_df.to_excel(bisection_db_file, index=False)

        #endregion

        # ============================================================================================================
        # region ADD SUBJECTS from another excel that may contain non complete data (subjects' labels list in each sheet may be different)

        newsubj_file    = os.path.join(project.input_data_dir, "new_subjects_bolz.xlsx")
        newsubj_db      = BayesDB(newsubj_file, can_different_subjs=True)

        newsubj_file2   = os.path.join(project.input_data_dir, "new_subjects_hsm.xlsx")
        newsubj_db2     = BayesDB(newsubj_file2, can_different_subjs=True)

        newbayes_db     = newbayes_db.add_new_subjects(newsubj_db, True)
        newbayes_db     = newbayes_db.add_new_subjects(newsubj_db2, True)

        newbayes_db_file327  = os.path.join(project.input_data_dir, "BAYES-PSIC.xlsx")

        newbayes_db.save_excel(newbayes_db_file327, sort=["subj"])
        #endregion


        a=1

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()
