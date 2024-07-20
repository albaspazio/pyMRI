import traceback

from DataProject import DataProject
from Global import Global
from data.BayesDB import BayesDB
from data.BayesImporter import BayesImporter
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
        proj_name           = "test"
        final_bayes_db_file = os.path.join("/data/MRI/pymri_projects_scripts", "final_BAYES-PSIC.xlsx")        # input

        project             = DataProject(proj_name, globaldata, data=final_bayes_db_file)
        bayes_db_file       = os.path.join(project.input_data_dir, "BAYES-PSIC_sessions.xlsx")        # input

        # subjects         = ["Arduino Gabriele", "Juan Kratzer", "Corsini Giovanni", "Levo Margherita", "Esposito Davide", "Priarone Ambra", "Bugliani Michele", "Risso Francesco ", "Cammalleri Michela", "Bruni Manuela", "Biggio Monica", "Nazzaro Roberto", "Barreto Cristina", "Vignone Severino", "Trabucco Alice", "Priolo Mario", "Bohlarova Darya", "Macchiavello Massimo", "Inuggi Alberto", "Iurilli Marisa", "Codou Fall", "Ghermakovsky Dumitru", "Gnaneswran Bavidran", "Pantalla Marco", "Cuccureddu Paolo", "Testa Emanuele ", "Tardito Samuele", "Espanet Giovanni", "Cevasco Maria Pia", "Bozomoala Elena Simona", "Bebeci Iridjon", "Galatini Matteo", "Cremonesi Vincenza", "Favilla Luca", "Lechiara Alessio", "Radi Ergesta", "Luciani Mariangela", "Longo Lucia ", "Sepe Francesco", "Rouissi Nejiba", "Paolini Giulio", "Pederzolli Daniela", "Repetto Marcello", "Colucci Laura", "Ubilla Julian", "Rzgar Saleh Sharif", "De noia Chiara", "Velo Alice", "Marino Margherita", "Marozzi Valentina", "Isola Fabrizio", "Da Conceicao Simona", "Bode Juxhin", "Dordolo Paola", "Paba Stefano", "Fornai Mattia", "D'Urso Agata", "Serrapica Ciro", "Cresta Sandra", "Ottonello Luca", "Serpetta Filippo ", "Marinescu Alexandro Marian", "Pullè Alberto", "Cacciatore Cinzia", "Cevasco Gina", "Sterlini Emilio", "Bacikova Lucia", "Ragni Maurizio", "Luminoso Thomas", "Meriggi Olga", "Lyakh Ruslan", "Oberti Alessandro", "Marsiglia Elisabetta", "Tasselli Rosanna", "De Lisi Giuseppe", "Roncarolo Giovanni", "Sgambato Gianluca", "Dotti Vilma", "Clavierez Cruz Sebastian", "Escelsior Andrea", "Versaggi Silvio", "Vai Eleonora", "Cattedra Simone", "Baldanzi Christian", "Esposito Natashia", "Milanti Leonardo", "Minasi Riccardo", "Pitone Giuseppe", "Ferrari Allegra", "Tergolina Camilla", "De Longis Simona", "Campodonico Alessandra", "Pepe Michele", "Bovio Anna", "Magnanini Camilla", "Firenze Stefano", "Orecchia Maria Luisa", "Russo Antonio", "Virga Brian", "Massa Sabrina", "Valerio Luca", "Gandini Alessio", "Marenco Giacomo", "Bruzzone Stefano", "Sartoris Giulia", "Villa veronica", "Gatto Marco", "Zerbi Laura", "Almondo Chiara", "Daturi Gabriele", "Pialorsi Simone", "Meinero Matteo", "Sapia Gabriele", "Iozzia Giorgia", "Chiara Cappello", "Sassarini Paolo", "Mecca Elisa", "Noli Simone", "Vigilanti Luca", "Barbera Maurizio", "Pio Stefano", "Lanino Edoardo", "Zanardi Sabrina", "Pukli Marta", "Briasco Giancarla", "Ravizza Massimiliano", "Cucalon Micheal", "Calcagno Dorotea", "Loi Andrea", "Cavazza Angela", "Rubino Davide", "Parodi Marco", "De Paoli Giampiero", "Talimani Luca", "Scevola Pamela Angela", "Lumetti Flavio", "Torres Paola Andrea", "Cristaldi Damiano", "Puglisi Luca", "Serpetto Filippo", "Ivaldi Federico", "Zerbetto Roberto", "Bode Juxhin", "Vacca Enrica"]

        columns2copy        = ["SA", "CLINIC",
                               "AASP", "ASI", "CCAS", "HAM", "MATRICS", "MEQ", "MW", "BISA", "PANSS",
                               "PAS", "PSQI", "SANS", "SAPS", "SPQ", "STQ", "TATE", "TEMPS", "TLC", "YMRS", "ZTPI"]
        # ======================================================================================================================
        # START !!!
        # ======================================================================================================================
        # read ALL bayes db
        bayes_db        = BayesDB(bayes_db_file)

        # ============================================================================================================
        #region URAS thesis
        subjects         = ["Arduino Gabriele", "Juan Kratzer", "Corsini Giovanni", "Levo Margherita", "Esposito Davide", "Priarone Ambra", "Bugliani Michele", "Risso Francesco ", "Cammalleri Michela", "Bruni Manuela", "Biggio Monica", "Nazzaro Roberto", "Barreto Cristina", "Vignone Severino", "Trabucco Alice", "Priolo Mario", "Bohlarova Darya", "Macchiavello Massimo", "Inuggi Alberto", "Iurilli Marisa", "Codou Fall", "Ghermakovsky Dumitru", "Gnaneswran Bavidran", "Pantalla Marco", "Cuccureddu Paolo", "Testa Emanuele ", "Tardito Samuele", "Espanet Giovanni", "Cevasco Maria Pia", "Bozomoala Elena Simona", "Bebeci Iridjon", "Galatini Matteo", "Cremonesi Vincenza", "Favilla Luca", "Lechiara Alessio", "Radi Ergesta", "Luciani Mariangela", "Longo Lucia ", "Sepe Francesco", "Rouissi Nejiba", "Paolini Giulio", "Pederzolli Daniela", "Repetto Marcello", "Colucci Laura", "Ubilla Julian", "Rzgar Saleh Sharif", "De noia Chiara", "Velo Alice", "Marino Margherita", "Marozzi Valentina", "Isola Fabrizio", "Da Conceicao Simona", "Bode Juxhin", "Dordolo Paola", "Paba Stefano", "Fornai Mattia", "D'Urso Agata", "Serrapica Ciro", "Cresta Sandra", "Ottonello Luca", "Serpetta Filippo ", "Marinescu Alexandro Marian", "Pullè Alberto", "Cacciatore Cinzia", "Cevasco Gina", "Sterlini Emilio", "Bacikova Lucia", "Ragni Maurizio", "Luminoso Thomas", "Meriggi Olga", "Lyakh Ruslan", "Oberti Alessandro", "Marsiglia Elisabetta", "Tasselli Rosanna", "De Lisi Giuseppe", "Roncarolo Giovanni", "Sgambato Gianluca", "Dotti Vilma", "Clavierez Cruz Sebastian", "Escelsior Andrea", "Versaggi Silvio", "Vai Eleonora", "Cattedra Simone", "Baldanzi Christian", "Esposito Natashia", "Milanti Leonardo", "Minasi Riccardo", "Pitone Giuseppe", "Ferrari Allegra", "Tergolina Camilla", "De Longis Simona", "Campodonico Alessandra", "Pepe Michele", "Bovio Anna", "Magnanini Camilla", "Firenze Stefano", "Orecchia Maria Luisa", "Russo Antonio", "Virga Brian", "Massa Sabrina", "Valerio Luca", "Gandini Alessio", "Marenco Giacomo", "Bruzzone Stefano", "Sartoris Giulia", "Villa veronica", "Gatto Marco", "Zerbi Laura", "Almondo Chiara", "Daturi Gabriele", "Pialorsi Simone", "Meinero Matteo", "Sapia Gabriele", "Iozzia Giorgia", "Cappello Chiara", "Sassarini Paolo", "Mecca Elisa", "Noli Simone", "Vigilanti Luca", "Barbera Maurizio", "Pio Stefano", "Lanino Edoardo", "Zanardi Sabrina", "Pukli Marta", "Briasco Giancarla", "Ravizza Massimiliano", "Cucalon Micheal", "Calcagno Dorotea", "Loi Andrea", "Cavazza Angela", "Rubino Davide", "Parodi Marco", "De Paoli Giampiero", "Talimani Luca", "Scevola Pamela Angela", "Lumetti Flavio", "Torres Paola Andrea", "Cristaldi Damiano", "Puglisi Luca"]
        out_uras_subset     = os.path.join(project.stats_input, "uras_db.xlsx")
        bayes_uras_data   = {"Sangue"   :["immfen_code"],
                             "main"     :["group", "Eta", "sesso"],
                             "Clinica"  :["Pregressi_Episodi", "PolaritàPrimoEpisodio", "disdur"]}
        bayes_db.save_df(out_uras_subset, subjects, bayes_uras_data)
        #endregion

        # ============================================================================================================
        # region SOME USEFUL LISTS

        # SUBJECTS WITH BLOOD SAMPLES
        bloodsubj_labels    = bayes_db.bloodlabels()[0] # 6 list of subjects with blood samples (total, th, tr, nk, mono, bi)

        # ============================================================================================================
        # SUBJECTS WITH MRI
        mrisubj_labels      = bayes_db.mrilabels()[0] # 4 list of subjects with mri (all, td, bd, sz)
        # endregion

        # ============================================================================================================
        #region CREATE BAYES DB:SUBJECTS WITH MRI & NK

        out_nk_mri_subset   = os.path.join(project.stats_input, "nk_mri_db.xlsx")   # set output file
        nk_mri_subjects     = bayes_db.sheets["BLOOD"].filter_subjects(mrisubj_labels, conditions=[FilterValues("NK", "==", 1)])
        nk_mri_labels       = nk_mri_subjects.labels


        # define which columns insert into the excel
        nk_mri_shcol   = {"main"     : ["mri_code", "group", "age", "gender"],
                          "CLINIC"  : ["disdur"],
                          "BLOOD"   : ["immfen_code", "CD56_BR_CD16_NEG_DIM", "CD56_DIM_CD16_BR", "CD56_DIM_CD16_DIM_NEG", "CD56_NEG_CD16_BR", "FS0", "FS1", "FS2", "FS3", "FS4", "FS5", "FS6", "FS7", "FS8", "FS9", "FS10", "FS11"],
                          "ASI"      : ["ASI_TOT"],
                          "HAM"  : ["HAM_DTOT", "HAM_ATOT"],
                          "PANSS"    : ["PANSS_TOT_P", "PANSS_TOT_N", "PANSS_TOT_G", "PANSS_TOT"],
                          "SANS"     : ["SANS_TOT"],
                          "SAPS"     : ["SAPS_TOT"],
                          "TLC"      : ["TLC_TOT"],
                          "YMRS"     : ["YMRS_TOT"],
                          }

        # extract df and save to file
        nk_mri_df        = bayes_db.select_df(nk_mri_subjects, nk_mri_shcol)
        nk_mri_df.to_excel(out_nk_mri_subset, index=False)
        #endregion

        # ============================================================================================================
        # region add a columns to each sheet
        new_bayes_db_file   = os.path.join(project.input_data_dir, "BAYES-PSIC_test.xlsx")
        new_db              = bayes_db.add_column("test", [1], None, 1)
        new_db.save_excel(new_bayes_db_file)
        #endregion

        # ============================================================================================================
        # region add second session partial data
        new_bayes_db_file   = os.path.join(project.input_data_dir, "new_subjects_2nd_session.xlsx")
        new_bayes_db        = BayesDB(new_bayes_db_file, calc_flags=False)
        final_db            = bayes_db.add_new_subjects(new_bayes_db, copy_previous_sess=columns2copy)
        final_db.save(final_bayes_db_file)
        #endregion

        # ============================================================================================================
        #region read an etero and add to db
        input_etero = os.path.join(project.input_data_dir, "ABC_etero.xlsx")
        etero_db = BayesImporter(input_etero)

        etero_bayes = etero_db.export_bayes()
        final_db    = bayes_db.add_new_subjects(etero_bayes)
        #endregion

        a=1

    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()
