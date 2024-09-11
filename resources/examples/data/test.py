import traceback
import pandas as pd

from DataProject import DataProject
from Global import Global
from data.utilities import *
from myutility.exceptions import SubjectListException
from data.SubjectsData import SubjectsData
from data.SubjectSDList import SubjectSDList

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
        bayes_db_file       = os.path.join("/data/MRI/pymri_projects_scripts", "BAYES-PSIC_sessions.xlsx")        # input

        project             = DataProject(proj_name, globaldata, data=bayes_db_file)

        subjects         = ["Arduino Gabriele", "Juan Kratzer", "Corsini Giovanni", "Levo Margherita", "Esposito Davide", "Priarone Ambra", "Bugliani Michele", "Risso Francesco ", "Cammalleri Michela", "Bruni Manuela", "Biggio Monica", "Nazzaro Roberto", "Barreto Cristina", "Vignone Severino", "Trabucco Alice", "Priolo Mario", "Bohlarova Darya", "Macchiavello Massimo", "Inuggi Alberto", "Iurilli Marisa", "Codou Fall", "Ghermakovsky Dumitru", "Gnaneswran Bavidran", "Pantalla Marco", "Cuccureddu Paolo", "Testa Emanuele ", "Tardito Samuele", "Espanet Giovanni", "Cevasco Maria Pia", "Bozomoala Elena Simona", "Bebeci Iridjon", "Galatini Matteo", "Cremonesi Vincenza", "Favilla Luca", "Lechiara Alessio", "Radi Ergesta", "Luciani Mariangela", "Longo Lucia ", "Sepe Francesco", "Rouissi Nejiba", "Paolini Giulio", "Pederzolli Daniela", "Repetto Marcello", "Colucci Laura", "Ubilla Julian", "Rzgar Saleh Sharif", "De noia Chiara", "Velo Alice", "Marino Margherita", "Marozzi Valentina", "Isola Fabrizio", "Da Conceicao Simona", "Bode Juxhin", "Dordolo Paola", "Paba Stefano", "Fornai Mattia", "D'Urso Agata", "Serrapica Ciro", "Cresta Sandra", "Ottonello Luca", "Serpetta Filippo ", "Marinescu Alexandro Marian", "Pullè Alberto", "Cacciatore Cinzia", "Cevasco Gina", "Sterlini Emilio", "Bacikova Lucia", "Ragni Maurizio", "Luminoso Thomas", "Meriggi Olga", "Lyakh Ruslan", "Oberti Alessandro", "Marsiglia Elisabetta", "Tasselli Rosanna", "De Lisi Giuseppe", "Roncarolo Giovanni", "Sgambato Gianluca", "Dotti Vilma", "Clavierez Cruz Sebastian", "Escelsior Andrea", "Versaggi Silvio", "Vai Eleonora", "Cattedra Simone", "Baldanzi Christian", "Esposito Natashia", "Milanti Leonardo", "Minasi Riccardo", "Pitone Giuseppe", "Ferrari Allegra", "Tergolina Camilla", "De Longis Simona", "Campodonico Alessandra", "Pepe Michele", "Bovio Anna", "Magnanini Camilla", "Firenze Stefano", "Orecchia Maria Luisa", "Russo Antonio", "Virga Brian", "Massa Sabrina", "Valerio Luca", "Gandini Alessio", "Marenco Giacomo", "Bruzzone Stefano", "Sartoris Giulia", "Villa veronica", "Gatto Marco", "Zerbi Laura", "Almondo Chiara", "Daturi Gabriele", "Pialorsi Simone", "Meinero Matteo", "Sapia Gabriele", "Iozzia Giorgia", "Chiara Cappello", "Sassarini Paolo", "Mecca Elisa", "Noli Simone", "Vigilanti Luca", "Barbera Maurizio", "Pio Stefano", "Lanino Edoardo", "Zanardi Sabrina", "Pukli Marta", "Briasco Giancarla", "Ravizza Massimiliano", "Cucalon Micheal", "Calcagno Dorotea", "Loi Andrea", "Cavazza Angela", "Rubino Davide", "Parodi Marco", "De Paoli Giampiero", "Talimani Luca", "Scevola Pamela Angela", "Lumetti Flavio", "Torres Paola Andrea", "Cristaldi Damiano", "Puglisi Luca", "Serpetto Filippo", "Ivaldi Federico", "Zerbetto Roberto", "Bode Juxhin", "Vacca Enrica"]
        some_subjects    = ["Arduino Gabriele", "Juan Kratzer", "Corsini Giovanni", "Levo Margherita"]

        xls = pd.ExcelFile(bayes_db_file)

        df = pd.read_excel(xls, "main")
        sd = SubjectsData(df)

        # subjs = SubjectSDList(sd.subjects)
        # new_subjs = subjs.filter(sd, [FilterValues("age", "<", 50)])

        some_subjs              = sd.select_subs_labels(some_subjects)
        some_sess1_subjs        = sd.select_subs_labels(some_subjects, [1])
        some_male_sess1_subjs   = sd.select_subs_labels(some_subjects, [1], [FilterValues("gender", "=", 1 )])
        some_female_sess1_subjs = sd.select_subs_labels(some_subjects, [1], [FilterValues("gender", "=", 2 )])

        a=1



    except SubjectListException as e:
        print(e)
        exit()
    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()
