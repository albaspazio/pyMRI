import os
import shutil
from math import ceil
from random import randrange
from shutil import move
import subprocess

import numpy

from Project import Project
from group.FSLModels import FSLModels
from group.SPMModels import SPMModels
from utility.exceptions import NotExistingImageException
from utility.fileutilities import get_dirname, write_text_file
from utility.fileutilities import sed_inplace
from utility.images.Image import Image
from utility.matlab import call_matlab_spmbatch
from utility.myfsl.utils.run import rrun
from utility.utilities import listToString


class GroupAnalysis:

    def __init__(self, proj:Project):

        self.subjects_list  = None
        self.working_dir    = ""
        self.project        = proj
        self._global        = self.project.globaldata

        self.spm            = SPMModels(proj)

    # does the following checks:
    # - input 4D image and mask, input fsf file exists.
    # - number of volumes (subjects) of input image coincides with number of points into the model
    # can split contrasts in different processes
    def start_tbss_randomize(self, pop_dir_name, dti_image_type, analysis_name, corr_string, models_dir_name="", delay=20, numcpu=1, perm=5000, ignore_errors=False, runit=True):

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
                    # p.wait()
                    rrun("sleep " + str(delay))
                    return p
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
                    con_txt = contrast_file.get_subset_text(conids_x_cpu[idcpu])
                    con_file = os.path.join(final_dir, random_folders[idcpu], analysis_name + "_x_" + corr_string + ".con")
                    write_text_file(con_file, con_txt)

                    mat_file = os.path.join(final_dir, random_folders[idcpu], analysis_name + "_x_" + corr_string + ".mat")
                    shutil.copyfile(model_mat, mat_file)

                    if runit:

                        try:
                            print("RANDOMIZE STARTED: model: " + model_noext + " on " + input_image)
                            p = subprocess.Popen(["randomise","-i", input_image, "-m", input_mask, "-o", os.path.join(final_dir, random_folders[idcpu], out_image_name), "-d", mat_file, "-t", con_file, "-n", str(perm), "--T2", "-V"])
                            subprocesses.append(p)
                            rrun("sleep " + str(delay))
                        except Exception as e:
                            print(e)

                for process in subprocesses:
                    process.wait()

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
    #region DATA PREPARATION
    # ====================================================================================================================================================

    # given a subjects list, it creates their template and project all the c1 images to its normalized version
    # create a folder name and its subfolders : subjects (normalized images), flowfields, stats
    # RC1_IMAGES:    {  '/media/data/MRI/projects/ELA/subjects/0202/s1/mpr/rc20202-t1.nii,1'
    #                   '/media/data/MRI/projects/ELA/subjects/0503/s1/mpr/rc20503-t1.nii,1'}
    def create_vbm_spm_template_normalize(self, name, subjects_list, spm_template_name="group_spm_dartel_createtemplate_normalize"):

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
    def create_fslvbm_from_spm(self, subjects_list, smw_folder, vbmfsl_folder):

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
            rrun("fslmaths " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label) + " -thr 0.1 " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))

        # create merged image
        # cur_dir = os.getcwd()
        os.chdir(stats_dir)

        # trick...since there are nii and nii.gz. by adding ".gz" in the check I consider only the nii
        images = [os.path.join(struct_dir, f) for f in os.listdir(struct_dir) if os.path.isfile(os.path.join(struct_dir, f + ".gz"))]

        rrun("fslmerge -t GM_merg" + " " + " ".join(images))
        rrun("fslmaths GM_merg" + " -Tmean -thr 0.05 -bin GM_mask -odt char")

        shutil.rmtree(struct_dir)

    def tbss_run_fa(self, subjects_list, odn, prepare=True, proc=True, postreg="S", prestat_thr=0.2, cleanup=True):

        self.subjects_list  = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in tbss_run_fa, given grouplabel_or_subjlist params is neither a string nor a list")
            return

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
            rrun("tbss_3_postreg -" + postreg)
            rrun("tbss_4_prestats " + str(prestat_thr))

            os.chdir(curr_dir)

        if cleanup:
            # shutil.rmtree(os.path.join(root_analysis_folder, "FA"))
            shutil.rmtree(os.path.join(root_analysis_folder, "origdata"))
            shutil.rmtree(os.path.join(root_analysis_folder, "design"))

        return root_analysis_folder

    # run tbss for other modalities = ["MD", "L1", ....]
    # you first must have done run_tbss_fa
    def tbss_run_alternatives(self, subjects_list, input_folder, modalities, prepare=True, proc=True, cleanup=True):

        self.subjects_list  = subjects_list
        if len(self.subjects_list) == 0:
            print("ERROR in tbss_run_alternatives, given grouplabel_or_subjlist params is neither a string nor a list")
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
                rrun("tbss_non_FA " + mod)

            os.chdir(curr_dir)

        if cleanup:
            # shutil.rmtree(os.path.join(input_folder, "FA")) #
            shutil.rmtree(os.path.join(input_folder, "L1"))
            shutil.rmtree(os.path.join(input_folder, "L23"))
            shutil.rmtree(os.path.join(input_folder, "MD"))

    # read a matrix file (not a classical subjects_data file) and add total ICV as last column
    # here it assumes [integer, integer, integer, integer, integer, float4]
    def add_icv_2_data_matrix(self, grouplabel_or_subjlist, input_data_file=None, sess_id=1):

        if not os.path.exists(input_data_file):
            print("ERROR in add_icv_2_data_matrix, given data_file does not exist")
            return

        subjects    = self.project.get_subjects_labels(grouplabel_or_subjlist)
        icvs        = self.project.get_subjects_icv(grouplabel_or_subjlist, sess_id)

        nsubj       = len(subjects)
        ndata       = len(icvs)
        if nsubj != ndata:
            print("ERROR in create_vbm_spm_stats. number of given subjects does not correspond to data number")
            return

        b = numpy.hstack((input_data_file, icvs))
        numpy.savetxt(input_data_file, b, ['%1.0f', '%1.0f', '%5.0f', '%5.0f', '%5.0f', '%2.4f'], '\t')

    # read xtract's stats.csv file of each subject in the given list and create a tabbed file (ofp) with given values/tract
    # calls the subject routine
    def xtract_export_group_data(self, subjects_list, ofp, tracts=None, values=None, ifn="stats.csv"):

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

    # endregion =================================================================================================================================================

    # ---------------------------------------------------
    #region MELODIC
    @staticmethod
    def group_melodic(out_dir_name, subjects_list, tr):

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

        rrun("fslmerge -t " + os.path.join(out_dir_name, "bg_image") + " " + bgimages)

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
    def group_sbfc(grouplabel_or_subjlist, firstlvl_fn, regressors, input_fsf, odp, ofn="mult_cov", data_file=None,
                                               create_model=True, group_mean_contrasts=1, cov_mean_contrasts=2, compare_covs=False, ofn_postfix=""):
        pass

    #endregion

    # ---------------------------------------------------
    # region TBSS
    # ====================================================================================================================================================
    # run tbss for FA
    # uses the union between template FA_skeleton and xtract's main tracts to clusterize a tbss output
    def tbss_clusterize_results_by_atlas(self, tbss_result_image, out_folder, log_file="overlap.txt", tracts_labels=None, tracts_dir=None, thr=0.95):

        try:
            if tracts_labels is None:
                tracts_labels   = self._global.dti_xtract_labels

            if tracts_dir is None:
                tracts_dir      = self._global.dti_xtract_dir

            log                 = os.path.join(out_folder, log_file)
            tot_voxels          = 0
            classified_tracts   = []
            os.makedirs(out_folder, exist_ok=True)

            # ----------------------------------------------------------------------------------------------------------
            # threshold tbss input, copy to out_folder, get number of voxels
            name            = os.path.basename(tbss_result_image)
            thr_input       = Image(os.path.join(out_folder, name))
            rrun("fslmaths " + tbss_result_image + " -thr " + str(thr) + " -bin " + thr_input)
            original_voxels = thr_input.get_nvoxels()

            out_str = ""
            for tract in tracts_labels:
                tr_img              = Image(os.path.join(tracts_dir, "FMRIB58_FA-skeleton_1mm_" + tract + "_mask"))
                tract_tot_voxels    = tr_img.get_nvoxels()
                out_img             = Image(os.path.join(out_folder, "sk_" + tract))
                rrun("fslmaths " + thr_input + " -mas " + tr_img + " " + out_img)

                res                 = out_img.get_nvoxels()
                if res > 0:
                    classified_tracts.append(out_img)
                else:
                    out_img.rm()

                tot_voxels = tot_voxels + res
                out_str = out_str + tract + "\t" + str(res) + " out of " + str(tract_tot_voxels) + " voxels = " + str(round((res * 100) / tract_tot_voxels, 2)) + " %" + "\n"

            # ------------------------------------------------
            # create unclassified image
            unclass_img = Image(os.path.join(out_folder, "unclass_" + os.path.basename(out_folder)))
            cmd_str = "fslmaths " + thr_input
            for img in classified_tracts:
                cmd_str = cmd_str + " -sub " + img + " -bin "
            cmd_str = cmd_str + unclass_img
            rrun(cmd_str)
            unclass_vox = unclass_img.get_nvoxels()

            # ----------------------------------------------------------------------------------------------------------
            # write log file
            out_str = out_str + "\n" + "\n" + "tot voxels = " + str(tot_voxels) + " out of " + str(original_voxels) + "\n"
            out_str = out_str + "unclassified image has " + str(unclass_vox)
            with open(log, 'w', encoding='utf-8') as f:
                f.write(out_str)

        except Exception as e:
            print(e)

    # clust_res_dir: output folder of tbss's results clustering
    # datas is a tuple of two elements containing a matrix of values and subjects
    # returns tracts_data
    @staticmethod
    def tbss_summarize_clusterized_folder(in_clust_res_dir, datas, data_labels, tbss_folder, modality="FA",
                                          subj_img_postfix="_FA_FA_to_target", ofn="scatter_tracts_") -> tuple:

        ndata       = len(data_labels)
        whatdata    = datas[0][0]
        if isinstance(whatdata, list):
            if len(whatdata) != ndata:
                print("ERROR in tbss_summarize_clusterized_folder: number of data columns differ from labels....exiting")
                return
        else:
            if ndata != 1:
                print("ERROR in tbss_summarize_clusterized_folder: more than one labels for one column data....exiting")
                return

        out_folder      = os.path.join(tbss_folder, "results")
        ifn             = get_dirname(in_clust_res_dir)
        subjects_images = os.path.join(tbss_folder, modality)  # folder containing tbss subjects' folder of that modality

        if modality == "FA":
            subj_img_postfix = "_FA_FA_to_target"
        else:
            subj_img_postfix = "_FA_to_target_" + modality

        tracts_labels = []

        # compose header
        str_data = "subj"
        for lab in data_labels:
            str_data = str_data + "\t" + lab

        for entry in os.scandir(in_clust_res_dir):
            if not entry.name.startswith('.') and not entry.is_dir():
                if entry.name.startswith("sk_"):
                    lab         = Image(entry.name[3:]).fpathnoext
                    tracts_labels.append(lab)
                    str_data    = str_data + "\t" + lab
        str_data = str_data + "\n"

        tracts_data = []
        [tracts_data.append([]) for _ in range(len(tracts_labels))]
        nsubj = len(datas[0])
        for i in range(nsubj):
            subj_label      = datas[1][i]
            in_img          = os.path.join(subjects_images, subj_label + "-dti_fit" + subj_img_postfix)
            subj_img        = Image(in_img, must_exist=True, msg="Error in tbss_summarize_clusterized_folder, subj image (" + in_img + "_masked" + ") is missing...exiting")
            subj_img_masked = Image(subj_img + "_masked")
            n_tracts        = 0
            str_data        = str_data + subj_label
            for id,lab in enumerate(data_labels):
                str_data = str_data + "\t" + str(datas[0][i][id])

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

    # create a new tbss analysis folder (only stats one), filtering an existing analysis folder
    # vols2keep: 0-based list of indices to keep
    @staticmethod
    def create_analysis_folder_from_existing(src_folder, new_folder, vols2keep, modalities=None):

        if modalities is None:
            modalities = ["FA", "MD", "L1", "L23"]

        # create new folder
        new_stats_folder = os.path.join(new_folder, "stats")
        os.makedirs(new_stats_folder, exist_ok=True)

        for mod in modalities:
            orig_image      = Image(os.path.join(src_folder, "stats", "all_" + mod + "_skeletonised"), must_exist=True, msg="GroupAnalysis.create_analysis_folder_from_existing")
            dest_image      = os.path.join(new_folder, "stats", "all_" + mod + "_skeletonised")

            orig_mean_image = Image(os.path.join(src_folder, "stats", "mean_" + mod + "_skeleton_mask"), must_exist=True, msg="GroupAnalysis.create_analysis_folder_from_existing")
            dest_mean_image = os.path.join(new_folder, "stats", "mean_" + mod + "_skeleton_mask")

            orig_image.filter_volumes(vols2keep, dest_image)

            orig_mean_image.cp(dest_mean_image)

    #endregion

    # ====================================================================================================
