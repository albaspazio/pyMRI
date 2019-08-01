import os
import shutil

from shutil import copyfile, move
from pymri.fsl.utils.run import rrun
from pymri.utility.fslfun import imcp
from pymri.utility.utilities import sed_inplace
import matlab.engine
import numpy


class GroupAnalysis:

    def __init__(self, proj):
        self.project        = proj


    # given a subjects list, it creates their template and project all the c1 images to its normalized version
    # create a folder name and its subfolders : subjects (normalized images), flowfields, stats
    def create_vbm_spm_template_normalize(self, name, subjs, sess_id=1, spm_template="spm_dartel_createtemplate_normalize_template_job.m"):

        self.subjects_list  = subjs
        self.working_dir    = os.path.join(self.project.vbm_dir, name)

        IN_TEMPLATE_DIR = os.path.join(self.project.script_dir, "mpr", "spm", "templates")
        OUT_BATCH_DIR   = os.path.join(self.project.script_dir, "mpr", "spm", "batch")

        template_batch_start    = os.path.join(IN_TEMPLATE_DIR, "spm_job_start.m")
        template_batch_job  = os.path.join(IN_TEMPLATE_DIR, spm_template)

        output_batch_start  = os.path.join(OUT_BATCH_DIR, "create_dartel_template_" + name + "_start.m")
        output_batch_job    = os.path.join(OUT_BATCH_DIR, "create_dartel_template_" + name + "_job.m")

        os.makedirs(OUT_BATCH_DIR, exist_ok=True)
        #=======================================================
        # START !!!!
        #=======================================================

        # RC1_IMAGES:
        # {
        #'/media/data/MRI/projects/ELA/subjects/0202/s1/mpr/rc20202-t1.nii,1'
        # '/media/data/MRI/projects/ELA/subjects/0503/s1/mpr/rc20503-t1.nii,1'
        # }

        # create job file
        T1_darteled_images_1="{\r"
        T1_darteled_images_2="{\r"
        T1_images_1="{\r"

        for subj in self.subjects_list:

            T1_darteled_images_1  = T1_darteled_images_1 + "\'" + os.path.join(subj.t1_spm_dir, "rc1T1_biascorr_" + subj.label + ".nii") + ",1\'\r"
            T1_darteled_images_2  = T1_darteled_images_2 + "\'" + os.path.join(subj.t1_spm_dir, "rc2T1_biascorr_" + subj.label + ".nii") + ",1\'\r"
            T1_images_1           = T1_images_1 + "\'"          + os.path.join(subj.t1_spm_dir, "c1T1_biascorr_" + subj.label + ".nii") + "\'\r"

        T1_darteled_images_1    = T1_darteled_images_1 + "\r}"
        T1_darteled_images_2    = T1_darteled_images_2 + "\r}"
        T1_images_1             = T1_images_1 + "\r}"


        copyfile(template_batch_job, output_batch_job)
        sed_inplace(output_batch_job, "<RC1_IMAGES>", T1_darteled_images_1)
        sed_inplace(output_batch_job, "<RC2_IMAGES>", T1_darteled_images_2)
        sed_inplace(output_batch_job, "<C1_IMAGES>",  T1_images_1)
        sed_inplace(output_batch_job, "<TEMPLATE_NAME>", name)
        sed_inplace(output_batch_job, "<TEMPLATE_ROOT_DIR>", self.project.vbm_dir)

        copyfile(template_batch_start, output_batch_start)
        sed_inplace(output_batch_start, "X", "1")
        sed_inplace(output_batch_start, "JOB_LIST", "\'" + output_batch_job + "\'")

        eng = matlab.engine.start_matlab()
        print("running SPM batch template: " + name)
        eval("eng." + os.path.basename(os.path.splitext(output_batch_start)[0]) + "(nargout=0)")
        eng.quit()

        affine_trasf_mat = os.path.join(self.subjects_list[0].t1_spm_dir, name + "_6_2mni.mat")
        move(affine_trasf_mat, os.path.join(self.project.vbm_dir, name, "flowfields", name + "_6_2mni.mat"))


    def create_vbm_spm_stats(self, name, subjs, input_data_file, sess_id=1, spm_template="spm_dartel_createtemplate_normalize_template_job.m"):
        pass

    def create_fslvbm_from_spm(self, subjs, smw_folder, vbmfsl_folder):

        stats_dir = os.path.join(vbmfsl_folder, "stats")
        struct_dir = os.path.join(vbmfsl_folder, "struct")

        os.makedirs(stats_dir,  exist_ok="True")
        os.makedirs(struct_dir, exist_ok="True")

        for subj in subjs:
            imcp(os.path.join(smw_folder, "smwc1T1_biascorr_" + subj.label), os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))
            rrun("fslmaths " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label) + " -thr 0.1 " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))

        # create merged image
        cur_dir = os.getcwd()
        os.chdir(stats_dir)

        # trick...since there are nii and nii.gz. by adding ".gz" in the check I consider only the nii
        images = [os.path.join(struct_dir, f) for f in os.listdir(struct_dir) if os.path.isfile(os.path.join(struct_dir, f + ".gz"))]

        rrun("fslmerge -t GM_merg" + " " + " ".join(images))
        rrun("fslmaths GM_merg" + " -Tmean -thr 0.05 -bin GM_mask -odt char")

        shutil.rmtree(struct_dir)

    # read a matrix file and add total ICV as last column
    # here it assumes [integer, integer, integer, integer, integer, float4]
    def add_icv_2_data_matrix(self, subjs, input_data_file):

        nsubj       = len(subjs)
        data_file   = numpy.loadtxt(input_data_file)
        ndata       = len(data_file)

        icv_scores  = numpy.zeros((ndata, 1))

        if nsubj != ndata:
            print("ERROR in create_vbm_spm_stats. number of given subjects does not correspond to data number")
            return

        cnt = 0
        for subj in subjs:
            icv_file = os.path.join(subj.t1_spm_dir, "icv_" + subj.label + ".dat")

            with open(icv_file) as fp:
                line = fp.readline()
                line = fp.readline().rstrip()
                values = line.split(',')

            icv_scores[cnt,0] = round(float(values[1]) + float(values[2]) + float(values[3]), 4)
            cnt = cnt + 1

        b = numpy.hstack((data_file, icv_scores))
        numpy.savetxt(input_data_file, b, ['%1.0f', '%1.0f', '%5.0f', '%5.0f', '%5.0f', '%2.4f'], '\t')






