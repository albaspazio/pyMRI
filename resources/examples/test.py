from Global import Global
from Project import Project

from myutility.images.Image import Image

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

        image = Image("/data/MRI/projects/test/subjects/S001/s1/mpr/S001-t11", True)

        print(image.name)


    except Exception as e:
        print("Error in test: " + str(e))
        exit()


