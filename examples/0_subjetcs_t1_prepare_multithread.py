from threading import Thread
# from Queue import Queue

from pymri.Global import Global
from pymri.Project import Project
from pymri.utility import startup_utilities
from pymri.Subject import Subject

if __name__ == "__main__":

    # ======================================================================================================================
    global_script_dir = "/data/MRI/scripts"
    proj_dir = "/data/MRI/projects/T15"
    fsl_code = "600"

    if not startup_utilities.init(global_script_dir, proj_dir, fsl_code):
        print("Error")
        exit()

    globaldata = Global(global_script_dir)

    # ======================================================================================================================
    # SUBJECTS
    # ======================================================================================================================

    project = Project(proj_dir, globaldata, hasT1=True)
    SESS_ID = 1

    # subject = Subject("T15_N_001", 1, project)
    # subject.create_file_system()

    project.load_subjects("test", SESS_ID)

    # ======================================================================================================================
    # PROCESSING
    # ======================================================================================================================
    paths = ["/data/MRI/projects/T15/subjects/T15_N_001/s1/mpr", "/data/MRI/projects/T15/subjects/T15_N_002/s1/mpr"]

    kwpaths = [{"extpath":"/data/MRI/projects/T15/subjects/T15_N_001/s1/mpr"},
               {"extpath":"/data/MRI/projects/T15/subjects/T15_N_002/s1/mpr"}]

    project.run_subject_methods("mpr2nifti", kwpaths)


    # methods manual threads
    # trg = eval("subject.mpr2nifti")
    # threads = []
    # # In this case 'urls' is a list of urls to be crawled.
    # for ii in range(len(paths)):
    #     # We start one thread per url present.
    #     process = Thread(target=trg, args=[paths[ii], 0])
    #     process.start()
    #     threads.append(process)
    #
    # # We now pause execution on the main thread by 'joining' all of our started threads. This ensures that each has finished processing.
    # for process in threads:
    #     process.join()


    # methods queue
    # q = Queue(maxsize=0)
    # # Use many threads (50 max, or one for each url)
    # num_threads = min(2, len(paths))
    #
    # for i in range(len(paths)):
    #     # need the index and the url in each queue item.
    #     q.put((i, paths[i]))

    # subject.mpr2nifti("/data/MRI/projects/T15/subjects/T15_N_001/s1/mpr", 1)


    subject.reslice_image("sag->axial")
    subject.anatomical_processing(do_cleanup=False)
    subject.post_anatomical_processing()
    # subject.do_first("L_Amyg,R_Amyg", odn="first")
    subject.do_first()

    num_cpu = 1

