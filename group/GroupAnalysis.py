from __future__ import annotations

import os
import shutil
from math import ceil
from random import randrange
from shutil import move
import subprocess
from typing import List
import numpy
import pandas

from Global import Global
from Project import Project
from subject.Subject import Subject
from models.FSLModels import FSLModels
from group.SPMModels import SPMModels
from myutility.exceptions import NotExistingImageException
from myutility.fileutilities import get_dirname, write_text_file
from myutility.fileutilities import sed_inplace
from myutility.images.Image import Image
from myutility.matlab import call_matlab_spmbatch
from myutility.myfsl.utils.run import rrun
from myutility.utilities import fillnumber2threedigits
from myutility.list import listToString, first_contained_in_second
from myutility.matlab import call_matlab_function_noret

class GroupAnalysis:
    """
    This class provides methods for group analysis of MRI data.
    """
    def __init__(self, proj:Project):
        """
        Initialize the GroupAnalysis class.

        Args:
            proj (Project): The Project object that contains the data and analysis settings.
        """
        self.subjects_list      = None
        self.working_dir        = ""
        self.project:Project    = proj
        self._global:Global     = self.project.globaldata

        self.spm:SPMModels      = SPMModels(proj)

    def start_tbss_randomize(self, pop_dir_name:str, dti_image_type:str, analysis_name:str, corr_string:str, models_dir_name:str="", delay:int=20, numcpu:int=1, perm:int=5000, ignore_errors:bool=False, runit:bool=True):
        """
        Start a TBSS randomization analysis.

        can split contrasts in different processes. if one process is used -> is not blocking, if more than one process is used -> waits for all of them.

        does the following checks:

        - input 4D image and mask, input fsf file exists.
        - number of volumes (subjects) of input image coincides with number of points into the model
        Args:
            pop_dir_name (str): The name of the population directory.
            dti_image_type (str): The DTI image type (e.g., FA).
            analysis_name (str): The name of the analysis.
            corr_string (str): The correlation string.
            models_dir_name (str, optional): The name of the directory containing the GLM models.
            delay (int, optional): The number of seconds to wait between each analysis.
            numcpu (int, optional): The number of CPUs to use for the analysis.
            perm (int, optional): The number of permutations to use for the analysis.
            ignore_errors (bool, optional): Whether to ignore errors or raise exceptions.
            runit (bool, optional): Whether to actually run the analysis or just return a subprocess.

        Returns:
            subprocess.Popen: A subprocess object if runit is True, otherwise None.
        """
        try:
            main_analysis_folder    = os.path.join(self.project.tbss_dir, pop_dir_name)     # /data/MRI/projects/past_controls/group_analysis/tbss/controls57
            out_stats_folder        = os.path.join(main_analysis_folder, "stats")           # /data/MRI/projects/past_controls/group_analysis/tbss/controls57/stats

            # /data/MRI/projects/past_controls/group_analysis/tbss/controls57/stats/all_FA_skeletonised --- mean_FA_skeleton_mask
            input_image     = Image(os.path.join(out_stats_folder, "all_" + dti_image_type + "_skeletonised"), must_exist=True, msg="skeletonised image not present")
            input_mask      = Image(os.path.join(out_stats_folder, "mean_" + dti_image_type + "_skeleton_mask"), must_exist=True, msg="skeleton mask image not present")
            out_image_name  = "tbss_" + dti_image_type + "_" + analysis_name + "_x_" + corr_string  # tbss_FA_groups&factors_x_age
            final_dir       = os.path.join(out_stats_folder, dti_image_type, corr_string)   # /data/MRI/projects/past_controls/group_analysis/tbss/population/stats/FA/age_gender

            os.makedirs(final_dir, exist_ok=True)

            model_noext = os.path.join(self.project.group_glm_dir, models_dir_name, analysis_name + "_x_" + corr_string) # /data/MRI/projects/past_controls/group_analysis/glm_models/XXX/groups&factors_x_nuisances
            model_con   = model_noext + ".con"
            model_mat   = model_noext + ".mat"

            if not os.path.exists(model_con) or not os.path.exists(model_con):
                raise Exception("model files are missing: "+ model_con + " | " + model_mat + "...analysis aborted")

            nvols   = input_image.nvols
            npoints = FSLModels.get_numpoints_from_fsl_model(model_mat)

            if nvols != npoints:
                raise Exception("number of data points in input image (" + input_image + ") and given model (" + model_noext + ") does not coincide...analysis aborted")

            if numcpu == 1:
                if runit:
                    print("RANDOMIZE STARTED: model: " + model_noext + " on " + input_image)
                    p = subprocess.Popen(["randomise", "-i", input_image, "-m", input_mask, "-o", os.path.join(final_dir, out_image_name), "-d", model_noext + ".mat", "-t", model_noext + ".con", "-n", str(perm), "--T2", "-V"])
                    rrun(f"sleep {delay}")
                    return p
                else:
                    print("model: " + model_noext + " on " + input_image + " is ok")
                    return
            else:
                contrast_file   = FSLModels.read_fsl_contrasts_file(model_con)
                numcpu          = min(contrast_file.ncontrasts, numcpu)

                # create a temp directory for each splitted analysis

                random_folders = [ "temp_" + out_image_name + "_" + str(i) + "_" + str(randrange(10000, 100000)) for i in range(numcpu)]

                for rf in random_folders:
                    os.makedirs(os.path.join(final_dir, rf), exist_ok=True)

                # assign contrasts id to each available cpu
                conids_x_cpu    = []
                contrasts       = contrast_file.matrix.copy()

                ncpu = numcpu               # 3cpu, 4 contr
                con_id = 0
                for c in range(numcpu):
                    ratio = ceil(len(contrasts) * 1.0 / ncpu)
                    cpu_conids = []
                    for cc in range(ratio):
                        cpu_conids.append(con_id)
                        contrasts.pop(0)
                        con_id += 1
                    ncpu -= 1
                    conids_x_cpu.append(cpu_conids)

                # create the numcpu mat / con files & start randomize
                subprocesses = []
                for idcpu in range(numcpu):
                    con_txt  = contrast_file.get_subset_text(conids_x_cpu[idcpu])
                    con_file = os.path.join(final_dir, random_folders[idcpu], analysis_name + "_x_" + corr_string + ".con")
                    write_text_file(con_file, con_txt)

                    mat_file = os.path.join(final_dir, random_folders[idcpu], analysis_name + "_x_" + corr_string + ".mat")
                    shutil.copyfile(model_mat, mat_file)

                    if runit:

                        try:
                            print("RANDOMIZE STARTED: model: " + model_noext + " on " + input_image)
                            p = subprocess.Popen(["randomise","-i", input_image, "-m", input_mask, "-o", os.path.join(final_dir, random_folders[idcpu], out_image_name), "-d", mat_file, "-t", con_file, "-n", str(perm), "--T2", "-V"])
                            subprocesses.append(p)
                            rrun(f"sleep {delay}")
                        except Exception as e:
                            print(e)
                    else:
                        print("model: " + model_noext + " on " + input_image + " is ok")
                        return
                for process in subprocesses:
                    process.wait()

                # move all the temp files to the final directory
                for f in range(numcpu):
                    temp_folder     = os.path.join(final_dir, random_folders[f])
                    num_contrasts   = len(conids_x_cpu[f])
                    for c in range(num_contrasts):
                        shutil.move(os.path.join(temp_folder, out_image_name + "_tfce_corrp_tstat" + str(c+1) + ".nii.gz"), os.path.join(final_dir, out_image_name + "_tfce_corrp_tstat" + str(conids_x_cpu[f][c]+1) + ".nii.gz"))
                        shutil.move(os.path.join(temp_folder, out_image_name + "_tstat" + str(c+1) + ".nii.gz")           , os.path.join(final_dir, out_image_name + "_tstat" + str(conids_x_cpu[f][c]+1) + ".nii.gz"))

                print("completed randomize: model: " + model_noext + " on " + input_image)

        except NotExistingImageException as e:
            msg = e.msg + " (" + e.image.fpathnoext + ")"
            if ignore_errors:
                print(msg)
                return
            else:
                raise Exception(msg)
        except Exception as e:
            msg = "Error in start_randomize: " + str(e)
            if ignore_errors:
                print(msg)
                return
            else:
                raise Exception(msg)

    # ---------------------------------------------------
    # region DATA PREPARATION
    # ====================================================================================================================================================

    # given a subjects list, it creates their template and project all the c1 images to its normalized version
    # create a folder name and its subfolders : subjects (normalized images), flowfields, stats
    # RC1_IMAGES:    {  '/media/data/MRI/projects/ELA/subjects/0202/s1/mpr/rc20202-t1.nii,1'
    #                   '/media/data/MRI/projects/ELA/subjects/0503/s1/mpr/rc20503-t1.nii,1'}
    def create_vbm_spm_template_normalize(self, name:str, subjects_list:List[Subject], spm_template_name:str="group_spm_dartel_createtemplate_normalize"):
        """
        Create a VBM SPM template for normalization.

        Args:
            name (str): The name of the template.
            subjects_list (list): A list of Subject objects.
            spm_template_name (str, optional): The name of the SPM template. Defaults to "group_spm_dartel_createtemplate_normalize".

        Returns:
            str: The path to the created template.
        """
        self.subjects_list = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in create_vbm_spm_template_normalize, given subjs params is neither a string nor a list")
            return

        self.working_dir = os.path.join(self.project.vbm_dir, name)

        out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr", "vbmtemplnorm_" + name)

        # =======================================================
        # START !!!!
        # =======================================================
        # create job file
        T1_darteled_images_1    = "{\r"
        T1_darteled_images_2    = "{\r"
        T1_images_1             = "{\r"

        for subj in self.subjects_list:
            T1_darteled_images_1    = T1_darteled_images_1 + "\'" + subj.t1_dartel_rc1.upath + ",1\'\r"
            T1_darteled_images_2    = T1_darteled_images_2 + "\'" + subj.t1_dartel_rc2.upath + ",1\'\r"
            T1_images_1             = T1_images_1 + "\'" + subj.t1_dartel_c1.upath + "\'\r"

        T1_darteled_images_1    = T1_darteled_images_1 + "\r}"
        T1_darteled_images_2    = T1_darteled_images_2 + "\r}"
        T1_images_1             = T1_images_1 + "\r}"

        sed_inplace(out_batch_job, "<RC1_IMAGES>", T1_darteled_images_1)
        sed_inplace(out_batch_job, "<RC2_IMAGES>", T1_darteled_images_2)
        sed_inplace(out_batch_job, "<C1_IMAGES>" , T1_images_1)
        sed_inplace(out_batch_job, "<TEMPLATE_NAME>", name)
        sed_inplace(out_batch_job, "<TEMPLATE_ROOT_DIR>", self.project.vbm_dir)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])
        print("running SPM batch template: " + name)

        affine_trasf_mat = os.path.join(self.subjects_list[0].t1_spm_dir, name + "_6_2mni.mat")
        move(affine_trasf_mat, os.path.join(self.project.vbm_dir, name, "flowfields", name + "_6_2mni.mat"))

        return self.working_dir

    # create a fslvbm folder using spm's vbm output
    def create_fslvbm_from_spm(self, subjects_list:List[Subject], smw_folder:str, vbmfsl_folder:str):
        """
        Create an FSL VBM folder from an SPM VBM folder.

        Args:
            subjects_list (List[Subject]): A list of Subject objects.
            smw_folder (str): The path to the SPM VBM folder.
            vbmfsl_folder (str): The path to the FSL VBM folder.

        Returns:
            None
        """
        self.subjects_list  = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in create_fslvbm_from_spm, given subjs params is neither a string nor a list")
            return

        stats_dir = os.path.join(vbmfsl_folder, "stats")
        struct_dir = os.path.join(vbmfsl_folder, "struct")

        os.makedirs(stats_dir, exist_ok=True)
        os.makedirs(struct_dir, exist_ok=True)

        for subj in self.subjects_list:
            Image(os.path.join(smw_folder, "smwc1T1_biascorr_" + subj.label)).cp(os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))
            rrun(f"fslmaths {os.path.join(struct_dir, 'smwc1T1_biascorr_' + subj.label)} -thr 0.1 {os.path.join(struct_dir, 'smwc1T1_biascorr_' + subj.label)}")

        # create merged image
        # cur_dir = os.getcwd()
        os.chdir(stats_dir)

        # trick...since there are nii and nii.gz. by adding ".gz" in the check I consider only the nii
        images = [os.path.join(struct_dir, f) for f in os.listdir(struct_dir) if os.path.isfile(os.path.join(struct_dir, f + ".gz"))]

        rrun(f"fslmerge -t GM_merg {' '.join(images)}")
        rrun("fslmaths GM_merg -Tmean -thr 0.05 -bin GM_mask -odt char")

        shutil.rmtree(struct_dir)

    def tbss_run_fa(self, subjects_list:List[Subject], odn:str, prepare:bool=True, proc:bool=True, postreg:str="S", prestat_thr:float=0.2, cleanup:bool=True):
        """
        Run a TBSS analysis on the given subjects list for the given output directory name.

        Args:
            subjects_list (List[Subject]): The list of Subject objects to analyze.
            odn (str): The name of the output directory.
            prepare (bool, optional): Whether to prepare the analysis by copying the necessary files. Defaults to True.
            proc (bool, optional): Whether to process the analysis. Defaults to True.
            postreg (str, optional): The post-registration method. Defaults to "S".
            prestat_thr (float, optional): The threshold for pre-statistics. Defaults to 0.2.
            cleanup (bool, optional): Whether to cleanup the analysis directory after running. Defaults to True.

        Returns:
            str: The path to the root analysis folder.
        """
        self.subjects_list  = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in tbss_run_fa, given grlab_subjlabs_subjs params is neither a string nor a list")
            return
        else:
            print("Starting tbss_run with " + str(len(self.subjects_list)) + " subjects")

        root_analysis_folder = os.path.join(self.project.tbss_dir, odn)

        os.makedirs(root_analysis_folder, exist_ok=True)
        os.makedirs(os.path.join(root_analysis_folder, "design"), exist_ok=True)

        # copy DTIFIT IMAGES to MAIN_ANALYSIS_FOLDER
        if prepare:

            print("copy subjects' corresponding dtifit_FA images to analysis folder")
            for subj in self.subjects_list:
                src_img     = Image(os.path.join(subj.dti_dir, subj.dti_fit_label + "_FA"))
                dest_img    = os.path.join(root_analysis_folder, subj.dti_fit_label + "_FA")
                src_img.cp(dest_img)

        if proc:
            curr_dir = os.getcwd()
            os.chdir(root_analysis_folder)

            print("preprocessing dtifit_FA images")
            rrun("tbss_1_preproc *.nii.gz")
            print("co-registrating images to MNI template")
            rrun("tbss_2_reg -T")
            print("postreg")
            rrun(f"tbss_3_postreg -{postreg}")
            rrun(f"tbss_4_prestats {prestat_thr}")

            os.chdir(curr_dir)

        if cleanup:
            # shutil.rmtree(os.path.join(root_analysis_folder, "FA"))
            shutil.rmtree(os.path.join(root_analysis_folder, "origdata"))
            shutil.rmtree(os.path.join(root_analysis_folder, "design"))

        return root_analysis_folder

    # run tbss for other modalities = ["MD", "L1", ....]
    # you first must have done run_tbss_fa
    def tbss_run_alternatives(self, subjects_list:List[Subject], input_folder:str, modalities:List[str], prepare:bool=True, proc:bool=True, cleanup:bool=True):
        """
        Runs a TBSS analysis on the given subjects list for the given output directory name for the given modalities.

        Args:
            subjects_list (List[Subject]): The list of Subject objects to analyze.
            input_folder (str): The path to the root analysis folder.
            modalities (List[str]): The list of modalities to analyze.
            prepare (bool, optional): Whether to prepare the analysis by copying the necessary files. Defaults to True.
            proc (bool, optional): Whether to process the analysis. Defaults to True.
            cleanup (bool, optional): Whether to cleanup the analysis directory after running. Defaults to True.

        Returns:
            None
        """
        self.subjects_list  = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in tbss_run_alternatives, given grlab_subjlabs_subjs params is neither a string nor a list")
            return

        input_stats = os.path.join(input_folder, "stats")

        # copy DTIFIT IMAGES to MAIN_ANALYSIS_FOLDER
        if prepare:

            print("copy subjects' corresponding dtifit_XX images to analysis folder")
            for subj in self.subjects_list:

                for mod in modalities:
                    alternative_folder = os.path.join(input_folder, mod)  # /group_analysis/tbss/population/MD
                    os.makedirs(alternative_folder, exist_ok=True)

                    src_img     = Image(os.path.join(subj.dti_dir, subj.dti_fit_label + "_" + mod), must_exist=True, msg="GroupAnalysis.tbss_run_alternatives")
                    dest_img    = os.path.join(alternative_folder, subj.dti_fit_label + "_" + mod)
                    src_img.cp(dest_img)

                    src_img     = Image(os.path.join(alternative_folder, subj.dti_fit_label + "_" + mod), must_exist=True, msg="GroupAnalysis.tbss_run_alternatives")
                    dest_img    = os.path.join(alternative_folder, subj.dti_fit_label + "_FA")
                    src_img.mv(dest_img)

                    Image(os.path.join(input_stats, "mean_FA_skeleton_mask_dst")).cp(os.path.join(input_stats, "mean_" + mod + "_skeleton_mask_dst"))
                    Image(os.path.join(input_stats, "mean_FA_skeleton_mask")).cp(os.path.join(input_stats, "mean_" + mod + "_skeleton_mask"))
                    Image(os.path.join(input_stats, "mean_FA_skeleton")).cp(os.path.join(input_stats, "mean_" + mod + "_skeleton_mask"))

        if proc:
            curr_dir = os.getcwd()
            os.chdir(input_folder)

            for mod in modalities:
                print("preprocessing dtifit_" + mod + " images")
                rrun(f"tbss_non_FA {mod}")

            os.chdir(curr_dir)

        if cleanup:
            # shutil.rmtree(os.path.join(input_folder, "FA")) #
            shutil.rmtree(os.path.join(input_folder, "L1"))
            shutil.rmtree(os.path.join(input_folder, "L23"))
            shutil.rmtree(os.path.join(input_folder, "MD"))

    # read a matrix file (not a classical subjects_data file) and add total ICV as last column
    # here it assumes [integer, integer, integer, integer, integer, float4]
    def add_icv_2_data_matrix(self, subjects:List[Subject], input_data_file:str=None):
        """
        Add the intracranial volume (ICV) to a data matrix.

        Args:
            subjects:List[Subject]: The group label or a list of subjects' label/instances.
            input_data_file (str, optional): The input data file. If not given, the project's default data file will be used.

        Returns:
            None
        """
        if not os.path.exists(input_data_file):
            print("ERROR in add_icv_2_data_matrix, given data_file does not exist")
            return

        icvs        = self.project.get_subjects_icv(subjects)

        nsubj       = len(subjects)
        ndata       = len(icvs)
        if nsubj != ndata:
            print("ERROR in create_vbm_spm_stats. number of given subjects does not correspond to data number")
            return

        b = numpy.hstack((input_data_file, icvs))
        numpy.savetxt(input_data_file, b, ['%1.0f', '%1.0f', '%5.0f', '%5.0f', '%5.0f', '%2.4f'], '\t')

    # read xtract's stats.csv file of each subject in the given list and create a tabbed file (ofp) with given values/tract
    # calls the subject routine
    def xtract_export_group_data(self, subjects_list:List[Subject], ofp:str, tracts:List[str]=None, values:List[str]=None, ifn:str="stats.csv"):
        """
        Export Xtract results for a group of subjects to a tab-separated file.

        Args:
            subjects_list (list): A list of Subject objects.
            ofp (str): The path to the output file.
            tracts (list, optional): A list of tractography labels. Defaults to None, which uses the default tractography labels defined in the project settings.
            values (list, optional): A list of values to export. Defaults to None, which exports the default values defined in the project settings.
            ifn (str, optional): The name of the input file. Defaults to "stats.csv".

        Returns:
            None
        """
        self.subjects_list  = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in xtract_export_group_data, given subjs params is neither a string nor a list")
            return

        if tracts is None:
            tracts = self._global.dti_xtract_labels

        if values is None:
            values = ["mean_FA", "mean_MD"]

        file_str = "subj\t"
        for tr in tracts:
            for v in values:
                file_str = file_str + tr + "_" + v + "\t"
        file_str = file_str + "\n"

        for subj in self.subjects_list:
            file_str = file_str + subj.dti.xtract_read_file(tracts, values, ifn)[0] + "\n"

        with open(ofp, 'w', encoding='utf-8') as f:
            f.write(file_str)

    def prepare_structconn_groupanalysis_dsi2nbs(self, subjects_list:List[Subject], ofp:str, nnodes:int, fisher2r:bool=False, input_postfix:str|None=None):
        """
        Prepare a group structural connectivity analysis for the given subjects list.
        Args:
            subjects_list (List[Subject]): The list of Subject objects to analyze.
            ofp (str): The path to the output file.
            input_postfix (str, optional): The postfix of the input files. Defaults to "-dti.src.gz.odf.gqi.1.25.fib.gz.tt.gz.bn274.count.pass.connectivity.mat".
        Raises:
            ValueError: If the output directory already exists.
        Returns:
            None
        This function prepares a group connectivity analysis for the given subjects list.
        It creates a directory for the output files and then iterates through the subjects in the list, copying their input matrices to the output directory.
        Finally, it calls a Matlab function to create a connectivity matrix from the input files.

        Note: This function assumes that the input matrices are in a specific format and that the Matlab function will be able to process them correctly.
        It also assumes that the output directory does not already exist, as it will raise a ValueError if it does.
        """

        if input_postfix is None:
            input_postfix =  "-dti.src.gz." + self._global.def_dsi_rec + ".fib.gz.tt.gz." + self._global.def_dsi_conntempl + ".count.pass.connectivity.mat"

        # if os.path.exists(ofp):
        #     os.removedirs(ofp)

        matrices_dir = os.path.join(ofp, "matrices")
        if not os.path.exists(ofp):
            os.makedirs(ofp)
        if not os.path.exists(matrices_dir):
            os.makedirs(matrices_dir)

        eng = None
        for subj in subjects_list:
            imat = os.path.join(subj.dti_dsi_dir, subj.label + input_postfix)
            omat = os.path.join(matrices_dir, subj.label + "_s" + str(subj.sessid) + ".mat")
            if os.path.exists(imat):
                shutil.copy(imat, omat)
            else:
                raise IOError("ERROR in prepare_nbs_group_conn_analysis, input mat of subject " + subj.label + " (sess " + str(subj.sessid) + ") does not exist")

            # eng = call_matlab_function_noret("remove_vars_from_mat", [self._global.spm_functions_dir], "'" + omat + "'", endengine=False, eng=eng)
        eng = call_matlab_function_noret("create_dsi_matrix_from_files", [self._global.spm_functions_dir], "'" + matrices_dir + "'" + ", " + str(nnodes) + ", 0", endengine=False, eng=eng)

    def prepare_funcconn_groupanalysis_conn2nbs(self, subjects_list:List[Subject], infp:str, ofp:str, nnodes:int, fisher2r:bool=True, input_prefix:str= "resultsROI_Subject", input_postfix:str= "_Condition001"):
        """
        Prepare a group functional connectivity analysis for the given subjects list.
        Args:
            subjects_list (List[Subject]): The list of Subject objects to analyze.
            ofp (str): The path to the output file.
            input_postfix (str, optional): The postfix of the input files. Defaults to "-dti.src.gz.odf.gqi.1.25.fib.gz.tt.gz.Brainnectome.count.pass.connectivity.mat".
        Raises:
            ValueError: If the output directory already exists.
        Returns:
            None
        This function prepares a group connectivity analysis for the given subjects list.
        It creates a directory for the output files and then iterates through the subjects in the list, copying their input matrices to the output directory.
        Finally, it calls a Matlab function to create a connectivity matrix from the input files.

        Note: This function assumes that the input matrices are in a specific format and that the Matlab function will be able to process them correctly.
        It also assumes that the output directory does not already exist, as it will raise a ValueError if it does.
        """

        # if os.path.exists(ofp):
        #     os.removedirs(ofp)

        matrices_dir = os.path.join(ofp, "matrices")
        if not os.path.exists(ofp):
            os.makedirs(ofp)
        if not os.path.exists(matrices_dir):
            os.makedirs(matrices_dir)

        eng = None
        for i in range(len(subjects_list)):
            zerofillednum = fillnumber2threedigits(i+1)
            imat = os.path.join(infp, input_prefix + zerofillednum + input_postfix + ".mat")
            omat = os.path.join(matrices_dir, input_prefix + zerofillednum + input_postfix + ".mat")
            if os.path.exists(imat):
                shutil.copy(imat, omat)
            else:
                raise IOError("ERROR in prepare_funcconn_groupanalysis_conn2nbs, input mat of subject " + str(i) + " does not exist")

        eng = call_matlab_function_noret("create_conn_matrix_from_files", [self._global.spm_functions_dir], "'" + matrices_dir + "'" + ", " + str(nnodes) + ", 1", endengine=False, eng=eng)


    # endregion =================================================================================================================================================

    # ---------------------------------------------------
    #region MELODIC
    @staticmethod
    def group_melodic(out_dir_name:str, subjects_list:List[Subject], tr):
        """
        Runs group melodic on the given subjects list.

        Args:
            out_dir_name (str): The path to the output directory.
            subjects_list (List[Subject]): The list of Subject objects to analyze.
            tr (float): The repetition time.

        Raises:
            ValueError: If the output directory already exists.

        Returns:
            None
        """
        if os.path.exists(out_dir_name):
            os.removedirs(out_dir_name)

        os.makedirs(out_dir_name)

        subjs           = ""
        bgimages        = ""
        masks           = ""
        missing_data    = ""

        for subj in subjects_list:

            if subj.rs_final_regstd_image.exist and subj.rs_final_regstd_bgimage.exist and subj.rs_final_regstd_bgimage.exist:
                subjs       = subjs + " " + subj.rs_final_regstd_image
                bgimages    = subjs + " " + subj.rs_final_regstd_bgimage
                masks       = masks + " " + subj.rs_final_regstd_mask
            else:
                missing_data = missing_data + subj.label + " "

        if len(missing_data) > 0:
            print("group melodic failed. the following subjects does not have all the needed images:")
            print(missing_data)
            return

        print("creating merged background image")

        rrun(f"fslmerge -t {os.path.join(out_dir_name, 'bg_image')} {bgimages}")

        # echo "merging background image"
        # $FSLDIR/bin/fslmerge -t $OUTPUT_DIR/bg_image $bglist
        # $FSLDIR/bin/fslmaths $OUTPUT_DIR/bg_image -inm 1000 -Tmean $OUTPUT_DIR/bg_image -odt float
        # echo "merging mask image"
        # $FSLDIR/bin/fslmerge -t $OUTPUT_DIR/mask $masklist
        #
        # echo "start group melodic !!"
        # $FSLDIR/bin/melodic -i $filelist -o $OUTPUT_DIR -v --nobet --bgthreshold=10 --tr=$TR_VALUE --report --guireport=$OUTPUT_DIR/report.html --bgimage=$OUTPUT_DIR/bg_image -d 0 --mmthresh=0.5 --Ostats -a concat
        #
        # echo "creating template description file"
        # template_file=$GLOBAL_SCRIPT_DIR/melodic_templates/$template_name.sh
        #
        # echo "template_name=$template_name" > $template_file
        # echo "TEMPLATE_MELODIC_IC=$OUTPUT_DIR/melodic_IC.nii.gz" >> $template_file
        # echo "TEMPLATE_MASK_IMAGE=$OUTPUT_DIR/mask.nii.gz" >> $template_file
        # echo "TEMPLATE_BG_IMAGE=$OUTPUT_DIR/bg_image.nii.gz" >> $template_file
        # echo "TEMPLATE_STATS_FOLDER=$OUTPUT_DIR/stats" >> $template_file
        # echo "TEMPLATE_MASK_FOLDER=$OUTPUT_DIR/stats" >> $template_file
        # echo "str_pruning_ic_id=() # valid RSN: you must set their id values removing 1: if in the html is the 6th RSN, you must write 5!!!!!!" >> $template_file
        # echo "str_arr_IC_labels=()" >> $template_file
        # echo "declare -a arr_IC_labels=()" >> $template_file
        # echo "declare -a arr_pruning_ic_id=()" >> $template_file
        #
        pass

    #endregion

    # ---------------------------------------------------
    #region SBFC
    @staticmethod
    def group_sbfc(grlab_subjlabs_subjs, firstlvl_fn, regressors, input_fsf, odp, ofn:str="mult_cov", data_file=None,
                   create_model:bool=True, group_mean_contrasts=1, cov_mean_contrasts=2, compare_covs:bool=False, ofn_postfix:str=""):
        pass

    #endregion

    # ---------------------------------------------------
    # region TBSS / xtrack / probtrack
    # ====================================================================================================================================================
    # run tbss for FA
    # uses the union between template FA_skeleton and xtract's main tracts to clusterize a tbss output
    def tbss_clusterize_results_by_atlas(self, tbss_result_image:str, out_folder:str, log_file:str="overlap.txt", tracts_labels:List[str]=None, tracts_dir:str=None, thr:float=0.95):
        """
        This function clusters the TBSS results by atlases.

        Args:
            tbss_result_image (str): The path to the TBSS result image.
            out_folder (str): The path to the output folder.
            log_file (str, optional): The name of the log file. Defaults to "overlap.txt".
            tracts_labels (List[str], optional): The list of tractography labels. Defaults to None, which uses the default tractography labels defined in the project settings.
            tracts_dir (str, optional): The path to the tractography directory. Defaults to None, which uses the default tractography directory defined in the project settings.
            thr (float, optional): The threshold value. Defaults to 0.95.

        Raises:
            Exception: If the output folder already exists.

        Returns:
            None
        """
        try:
            if tracts_labels is None:
                tracts_labels   = self._global.dti_xtract_labels

            if tracts_dir is None:
                tracts_dir      = self._global.dti_xtract_dir

            log                 = os.path.join(out_folder, log_file)
            os.makedirs(out_folder, exist_ok=True)

            tot_voxels          = 0     # tot voxels in whole tbss result image
            ntotvox_x_tract     = []    # total number of voxels in each tract
            nsignvox_x_tract    = []    # total number of significant voxels in each tract
            classified_tracts   = []    # list of tracts where significant voxels are > 0
            tbss_result_image = Image(tbss_result_image, must_exist=True, msg="Error in tbss_clusterize_results_by_atlas. TBSS result image (" + tbss_result_image + ") does not exist")

            # ----------------------------------------------------------------------------------------------------------
            # threshold tbss input, copy to out_folder, get number of voxels
            name            = tbss_result_image.name
            thr_input       = Image(os.path.join(out_folder, name))
            rrun(f"fslmaths {tbss_result_image} -thr {thr} -bin {thr_input}")
            original_voxels = thr_input.nvoxels

            for tract in tracts_labels:
                tr_img              = Image(os.path.join(tracts_dir, "FMRIB58_FA-skeleton_1mm_" + tract + "_mask"))
                ntotvox_x_tract.append(tr_img.nvoxels)
                out_img             = Image(os.path.join(out_folder, "sk_" + tract))
                rrun(f"fslmaths {thr_input} -mas {tr_img} {out_img}")

                res = out_img.nvoxels
                nsignvox_x_tract.append(res)
                if res > 0:
                    classified_tracts.append(out_img)
                else:
                    out_img.rm()

                tot_voxels = tot_voxels + res

            out_str = "tract\tsignvx\ttotvx\ttr_perc\ttot_perc\n"
            for id, tract in enumerate(tracts_labels):
                    out_str = f"{out_str}{tract}\t{nsignvox_x_tract[id]}\t{ntotvox_x_tract[id]}\t{round((nsignvox_x_tract[id] * 100) / ntotvox_x_tract[id], 2)}\t{round((nsignvox_x_tract[id] * 100) / tot_voxels, 2)}\n"

            # ------------------------------------------------
            # create unclassified image
            unclass_img = Image(os.path.join(out_folder, "unclass_" + os.path.basename(out_folder)))
            cmd_str = "fslmaths " + thr_input
            for img in classified_tracts:
                cmd_str = f"{cmd_str} -sub {img} -bin "
            cmd_str = cmd_str + unclass_img
            rrun(cmd_str)
            unclass_vox = unclass_img.nvoxels

            # ----------------------------------------------------------------------------------------------------------
            # write log file
            out_str = f"{out_str}\ntot_rec_voxels\ttot_voxels\tperc\n"
            out_str = f"{out_str}{tot_voxels}\t{original_voxels}\t{round((tot_voxels * 100) / original_voxels, 2)}\n"
            out_str = f"{out_str}unclassified image has {unclass_vox} voxels"
            with open(log, 'w', encoding='utf-8') as f:
                f.write(out_str)

        except Exception as e:
            print(e)

    # clust_res_dir: output folder of tbss's results clustering
    # datas is a pandas.DataFrame with the same number of rows as the subjects contained in subj_labels and a varying number of columns
    # sessions are flattened. tbss output folder divide subjects by labels only, thus session is eventually appended to the subject labels
    # returns tracts_data
    @staticmethod
    def tbss_summarize_clusterized_folder(subj_labels:List[str], in_clust_res_dir, tbss_folder, modality:str="FA", subj_img_postfix="_FA_FA_to_target",
                                          data:pandas.DataFrame=None, ofn="scatter_tracts_") -> tuple:
        """
        This function takes the output of a TBSS clustering and possibly a DataFrame and extract dti metrics values within these fraction of tracts
        summarizes the results in a tab-separated file.

        Args:
            subj_labels (List[str]) : The list of subject labels.
            in_clust_res_dir (str)  : The path to the TBSS clustering results folder.
            tbss_folder (str)       : The root path to the TBSS analysis folder.
            modality (str, optional): The metric to extract. Defaults to "FA".
            subj_img_postfix (str, optional): The postfix of the subject images. Defaults to "_FA_FA_to_target".
            data (pandas.DataFrame) : A dataframe containing a set of subject rows and data columns.
            ofn (str, optional)     : The name of the output file. Defaults to "scatter_tracts_".

        Returns:
            tuple: A tuple containing the path to the output file and the tracts data.

        Raises:
            Exception: If the input data is not valid.

        """
        # check that data contains values of all subects included in subj_labels
        subjs_in_data = data["subj"].tolist()
        if not first_contained_in_second(subj_labels, subjs_in_data):
            raise Exception("ERROR in tbss_summarize_clusterized_folder: at least one of subj_labels is not included in data....exiting")

        out_folder      = os.path.join(tbss_folder, "results")
        ifn             = get_dirname(in_clust_res_dir)
        subjects_images = os.path.join(tbss_folder, "FA")  # by default, subjects' data are in the FA folder

        if modality == "FA":
            subj_img_postfix = "_FA_FA_to_target"
        else:
            subj_img_postfix = "_FA_to_target_" + modality

        tracts_labels = []

        # compose header
        if data is None:
            str_data    = "subj"
            data_labels = []
        else:
            str_data = "\t".join(data.columns.to_list())
            data_labels = data.columns.to_list()
            data_labels.pop(0)

        for entry in os.scandir(in_clust_res_dir):
            if not entry.name.startswith('.') and not entry.is_dir():
                if entry.name.startswith("sk_"):
                    lab         = Image(entry.name[3:]).fpathnoext
                    tracts_labels.append(lab)
                    str_data    = str_data + "\t" + lab
        str_data = str_data + "\n"

        tracts_data = []
        [tracts_data.append([]) for _ in range(len(tracts_labels))]


        nsubj = len(subj_labels)
        for id,subj_label in enumerate(subj_labels):
            in_img          = os.path.join(subjects_images, subj_label + "-dti_fit" + subj_img_postfix)
            subj_img        = Image(in_img, must_exist=True, msg="Error in tbss_summarize_clusterized_folder, subj image (" + in_img + "_masked" + ") is missing...exiting")
            subj_img_masked = Image(subj_img + "_masked")
            n_tracts        = 0
            str_data        = str_data + subj_label
            for id,lab in enumerate(data_labels):
                str_data = str_data + "\t" + str(data.loc[data['subj'] == subj_label, lab].values[0])

            for entry in os.scandir(in_clust_res_dir):
                if not entry.name.startswith('.') and not entry.is_dir():
                    if entry.name.startswith("sk_"):
                        subj_img.mask_image(entry.path, subj_img_masked)
                        val = subj_img_masked.get_image_mean()
                        subj_img_masked.rm()

                        str_data = str_data + "\t" + str(val)
                        tracts_data[n_tracts].append(val)
                        n_tracts = n_tracts + 1
            str_data = str_data + "\n"

        res_file = os.path.join(out_folder, ofn + ifn + "_" + listToString(data_labels, separator='_') + ".dat")

        with open(res_file, "w") as f:
            f.write(str_data)

        return res_file

    # create a new tbss analysis folder (only stats one), filtering an existing analysis folder (specifying what to keep)
    # vols2keep: 0-based list of indices to keep
    @staticmethod
    def create_analysis_folder_from_existing_keep(src_folder, new_folder, vols2keep, modalities=None):
        """
        Creates a new analysis folder from an existing one, by copying the necessary files and keeping the given volumes.

        Args:
            src_folder (str): The path to the existing analysis folder.
            new_folder (str): The path to the new analysis folder.
            vols2keep (List[int]): A list of volume indices to keep.
            modalities (Optional[List[str]]): A list of modalities to copy. If not specified, all modalities will be copied.

        Returns:
            None
        """
        if modalities is None:
            modalities = ["FA", "MD", "L1", "L23"]

        # create new folder
        new_stats_folder = os.path.join(new_folder, "stats")
        os.makedirs(new_stats_folder, exist_ok=True)

        for mod in modalities:
            orig_image      = Image(os.path.join(src_folder, "stats", "all_" + mod + "_skeletonised"), must_exist=True, msg="GroupAnalysis.create_analysis_folder_from_existing_keep")
            dest_image      = Image(os.path.join(new_stats_folder, "all_" + mod + "_skeletonised"))

            orig_mean_image = Image(os.path.join(src_folder, "stats", "mean_" + mod + "_skeleton_mask"), must_exist=True, msg="GroupAnalysis.create_analysis_folder_from_existing_keep")
            dest_mean_image = Image(os.path.join(new_stats_folder, "mean_" + mod + "_skeleton_mask"))

            orig_image.filter_volumes(vols2keep, dest_image)

            orig_mean_image.cp(dest_mean_image)

    # create a new tbss analysis folder (only stats one), filtering an existing analysis folder (specifying what to remove)
    # vols2remove: 0-based list of indices to remove
    @staticmethod
    def create_analysis_folder_from_existing_remove(src_folder:str, new_folder:str, vols2remove:List[int], modalities:List[str] | None=None):
        """
        Creates a new analysis folder from an existing one, by copying the necessary files and removing the given volumes.

        Args:
            src_folder (str): The path to the existing analysis folder.
            new_folder (str): The path to the new analysis folder.
            vols2remove (List[int]): A list of volume indices to remove.
            modalities (Optional[List[str]]): A list of modalities to copy. If not specified, all modalities will be copied.

        Returns:
            None
        """
        if modalities is None:
            modalities = ["FA", "MD", "L1", "L23"]

        # get number of subjects (assumes all modalities contains the same number of volumes)
        orig_image = Image(os.path.join(src_folder, "stats", "all_" + modalities[0] + "_skeletonised"), must_exist=True, msg="GroupAnalysis.create_analysis_folder_from_existing_keep")

        nvols = orig_image.nvols
        all_ids = [i for i in range(nvols)]
        for i in vols2remove:
            all_ids.remove(i)

        GroupAnalysis.create_analysis_folder_from_existing_keep(src_folder, new_folder, all_ids, modalities)

    @staticmethod
    def xtract_group_qc(self, subjects:List[Subject], out_dir:str, xtractdir_name:str|None=None, thr:float=0.001, n_std:int=2):

        xtracts_file = os.path.join(out_dir, "xtracts_file.txt")
        os.makedirs(out_dir, exist_ok=True)
        with open(xtracts_file, "w") as f:
            str_xtr = ""
            for subj in subjects:
                if xtractdir_name is None:
                    xtrdir = subj.dti_xtract_dir
                else:
                    xtrdir = os.path.join(subj.dti_dir, xtractdir_name)
                str_xtr = f"{str_xtr}{xtrdir}\n"
            f.write(str_xtr)

        rrun(f"xtract_qc -subject_list {xtracts_file} -out {out_dir} -thr {thr} -n_std {n_std}")
    #endregion

    # # takes N individual tracts for each subject in the list, create a merged tract (union) names as the subject, project to template and display in a single fsleyes
    # def show_group_probtracks(self, subjects:List[Subject], tracts_names:List[str], tracts_dir_name:str):
    #     tracts_list = ""
    #
    #     ntracts = len(tracts_names)
    #     for s in subjects:
    #
    #         first_tract = os.path.join(s.dti_probtrackx_dir, tracts_dir_name, track_names[0])
    #         merged_str = "fslmaths " + first_tract
    #         for n in range(1, ntracts):
    #             nth_tract = os.path.join(s.dti_probtrackx_dir, tracts_dir_name, track_names[n])
    #             merged_str = merged_str + " -add " + nth_tract
    #         merged_str = merged_str + s.label + tracts
    #
    #
    #         # ---------------------------------------------------

    def extract_values_from_image(self, ):

        """
        given a group analysis result image
        """
        pass
    # ====================================================================================================
