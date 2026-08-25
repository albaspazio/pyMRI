import os
from project.GlobalMRI import GlobalMRI
from project.ProjectMRI import ProjectMRI
from myutility.images.Image import Image

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = GlobalMRI(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        # NOTE: Update this path to your actual project directory
        proj_dir = os.path.join(os.path.dirname(__file__), "..", "..", "projects", "test")
        project = ProjectMRI(proj_dir, globaldata)
        SESS_ID = 1
        num_cpu = 1

        # Example image path - adjust based on your actual data structure
        image_path = os.path.join(proj_dir, "subjects", "S001", "s1", "mpr", "S001-t11")
        image = Image(image_path, True)

        print(f"Image name: {image.name}")


    except Exception as e:
        print("Error in test: " + str(e))
        exit()


