import ntpath
import os
import shutil
import traceback
from shutil import move

import matlab.engine
import numpy

from data import plot_data
from data.SubjectsDataDict import SubjectsDataDict
from group.SPMModels import SPMModels
from group.SPMStatsUtils import SPMStatsUtils
from utility.myfsl.utils.run import rrun
from utility.images.images import imcp, imtest, immv, imrm, remove_ext, filter_volumes, get_image_nvoxels, get_image_mean, mask_image
from data.utilities import list2spm_text_column, get_icv_spm_file
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


class GroupAnalysis:

    def __init__(self, proj):

        self.subjects_list  = None
        self.working_dir    = ""
        self.project        = proj
        self._global        = self.project.globaldata

        self.spm            = SPMModels(proj)

    # ---------------------------------------------------
    #region DATA PREPARATION
    # ====================================================================================================================================================

    # given a subjects list, it creates their template and project all the c1 images to its normalized version
    # create a folder name and its subfolders : subjects (normalized images), flowfields, stats
    # RC1_IMAGES:    {  '/media/data/MRI/projects/ELA/subjects/0202/s1/mpr/rc20202-t1.nii,1'
    #                   '/media/data/MRI/projects/ELA/subjects/0503/s1/mpr/rc20503-t1.nii,1'}
    def create_vbm_spm_template_normalize(self, name, grouplabel_or_subjlist, spm_template_name="spm_dartel_createtemplate_normalize", sess_id=1):

        self.subjects_list = self.project.get_subjects(grouplabel_or_subjlist, sess_id)
        if len(self.subjects_list) == 0:
            print("ERROR in create_vbm_spm_template_normalize, given subjs params is neither a string nor a list")
            return

        self.working_dir = os.path.join(self.project.vbm_dir, name)

        out_batch_job, out_batch_start = self.project.adapt_batch_files(spm_template_name, "mpr")

        # =======================================================
        # START !!!!
        # =======================================================
        # create job file
        T1_darteled_images_1 = "{\r"
        T1_darteled_images_2 = "{\r"
        T1_images_1 = "{\r"

        for subj in self.subjects_list:
            T1_darteled_images_1 = T1_darteled_images_1 + "\'" + os.path.join(subj.t1_spm_dir, "rc1T1_" + subj.label + ".nii") + ",1\'\r"
            T1_darteled_images_2 = T1_darteled_images_2 + "\'" + os.path.join(subj.t1_spm_dir, "rc2T1_" + subj.label + ".nii") + ",1\'\r"
            T1_images_1 = T1_images_1 + "\'" + os.path.join(subj.t1_spm_dir, "c1T1_" + subj.label + ".nii") + "\'\r"

        T1_darteled_images_1 = T1_darteled_images_1 + "\r}"
        T1_darteled_images_2 = T1_darteled_images_2 + "\r}"
        T1_images_1 = T1_images_1 + "\r}"

        sed_inplace(out_batch_job, "<RC1_IMAGES>", T1_darteled_images_1)
        sed_inplace(out_batch_job, "<RC2_IMAGES>", T1_darteled_images_2)
        sed_inplace(out_batch_job, "<C1_IMAGES>", T1_images_1)
        sed_inplace(out_batch_job, "<TEMPLATE_NAME>", name)
        sed_inplace(out_batch_job, "<TEMPLATE_ROOT_DIR>", self.project.vbm_dir)

        call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])
        print("running SPM batch template: " + name)

        affine_trasf_mat = os.path.join(self.subjects_list[0].t1_spm_dir, name + "_6_2mni.mat")
        move(affine_trasf_mat, os.path.join(self.project.vbm_dir, name, "flowfields", name + "_6_2mni.mat"))

    # create a fslvbm folder using spm's vbm output
    def create_fslvbm_from_spm(self, grouplabel_or_subjlist, smw_folder, vbmfsl_folder, sess_id=1):

        self.subjects_list  = self.project.get_subjects(grouplabel_or_subjlist, sess_id)
        if len(self.subjects_list) == 0:
            print("ERROR in create_fslvbm_from_spm, given subjs params is neither a string nor a list")
            return

        stats_dir = os.path.join(vbmfsl_folder, "stats")
        struct_dir = os.path.join(vbmfsl_folder, "struct")

        os.makedirs(stats_dir, exist_ok=True)
        os.makedirs(struct_dir, exist_ok=True)

        for subj in self.subjects_list:
            imcp(os.path.join(smw_folder, "smwc1T1_biascorr_" + subj.label),
                 os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))
            rrun("fslmaths " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label) + " -thr 0.1 " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))

        # create merged image
        cur_dir = os.getcwd()
        os.chdir(stats_dir)

        # trick...since there are nii and nii.gz. by adding ".gz" in the check I consider only the nii
        images = [os.path.join(struct_dir, f) for f in os.listdir(struct_dir) if os.path.isfile(os.path.join(struct_dir, f + ".gz"))]

        rrun("fslmerge -t GM_merg" + " " + " ".join(images))
        rrun("fslmaths GM_merg" + " -Tmean -thr 0.05 -bin GM_mask -odt char")

        shutil.rmtree(struct_dir)


    def tbss_run_fa(self, grouplabel_or_subjlist, odn, prepare=True, proc=True, postreg="S", prestat_thr=0.2, sess_id=1):

        self.subjects_list  = self.project.get_subjects(grouplabel_or_subjlist, sess_id)
        if len(self.subjects_list) == 0:
            print("ERROR in tbss_run_fa, given grouplabel_or_subjlist params is neither a string nor a list")
            return

        root_analysis_folder = os.path.join(self.project.tbss_dir, odn)

        os.makedirs(root_analysis_folder, exist_ok=True)
        os.makedirs(os.path.join(root_analysis_folder, "design"), exist_ok=True)

        # copy DTIFIT IMAGES to MAIN_ANALYSIS_FOLDER
        if prepare is True:

            print("copy subjects' corresponding dtifit_FA images to analysis folder")
            for subj in self.subjects_list:
                src_img = os.path.join(subj.dti_dir, subj.dti_fit_label + "_FA")
                dest_img = os.path.join(root_analysis_folder, subj.dti_fit_label + "_FA")
                imcp(src_img, dest_img)

        if proc is True:
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

        return root_analysis_folder

    # run tbss for other modalities = ["MD", "L1", ....]
    # you first must have done run_tbss_fa
    def tbss_run_alternatives(self, grouplabel_or_subjlist, input_folder, modalities, prepare=True, proc=True, sess_id=1):

        self.subjects_list  = self.project.get_subjects(grouplabel_or_subjlist, sess_id)
        if len(self.subjects_list) == 0:
            print("ERROR in tbss_run_alternatives, given grouplabel_or_subjlist params is neither a string nor a list")
            return

        input_stats = os.path.join(input_folder, "stats")

        # copy DTIFIT IMAGES to MAIN_ANALYSIS_FOLDER
        if prepare is True:

            print("copy subjects' corresponding dtifit_XX images to analysis folder")
            for subj in self.subjects_list:

                for mod in modalities:
                    alternative_folder = os.path.join(input_folder, mod)  # /group_analysis/tbss/population/MD
                    os.makedirs(alternative_folder, exist_ok=True)

                    src_img = os.path.join(subj.dti_dir, subj.dti_fit_label + "_" + mod)
                    dest_img = os.path.join(alternative_folder, subj.dti_fit_label + "_" + mod)
                    imcp(src_img, dest_img)

                    src_img = os.path.join(alternative_folder, subj.dti_fit_label + "_" + mod)
                    dest_img = os.path.join(alternative_folder, subj.dti_fit_label + "_FA")
                    immv(src_img, dest_img)

                    imcp(os.path.join(input_stats, "mean_FA_skeleton_mask_dst"),
                         os.path.join(input_stats, "mean_" + mod + "_skeleton_mask_dst"))
                    imcp(os.path.join(input_stats, "mean_FA_skeleton_mask"),
                         os.path.join(input_stats, "mean_" + mod + "_skeleton_mask"))
                    imcp(os.path.join(input_stats, "mean_FA_skeleton"),
                         os.path.join(input_stats, "mean_" + mod + "_skeleton_mask"))

        if proc is True:
            curr_dir = os.getcwd()
            os.chdir(input_folder)

            for mod in modalities:
                print("preprocessing dtifit_" + mod + " images")
                rrun("tbss_non_FA " + mod)

            os.chdir(curr_dir)


    # read a matrix file (not a classical subjects_data file) and add total ICV as last column
    # here it assumes [integer, integer, integer, integer, integer, float4]
    def add_icv_2_data_matrix(self, grouplabel_or_subjlist, input_data_file=None, sess_id=1):

        if os.path.exists(input_data_file) is False:
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
    def xtract_export_group_data(self, grouplabel_or_subjlist, ofp, tracts=None, values=None, ifn="stats.csv", sess_id=1):

        self.subjects_list  = self.project.get_subjects(grouplabel_or_subjlist, sess_id)
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
    def group_melodic(self, out_dir_name, subjects, tr):

        if os.path.exists(out_dir_name):
            os.removedirs(out_dir_name)

        os.makedirs(out_dir_name)

        subjs           = ""
        bgimages        = ""
        masks           = ""
        missing_data    = ""

        for s in subjects:

            if imtest(s.rs_final_regstd_image) is True and imtest(s.rs_final_regstd_bgimage) and imtest(s.rs_final_regstd_bgimage):
                subjs       = subjs + " " + s.rs_final_regstd_image
                bgimages    = subjs + " " + s.rs_final_regstd_bgimage
                masks       = masks + " " + s.rs_final_regstd_mask
            else:
                missing_data = missing_data + s.label + " "

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

    # ====================================================================================================================================================
    #region TBSS
    # ====================================================================================================================================================
    # run tbss for FA
    # uses the union between template FA_skeleton and xtract's main tracts to clusterize a tbss output
    def tbss_clusterize_results_by_atlas(self, tbss_result_image, out_folder,
                                         log_file="log.txt", tracts_labels=None, tracts_dir=None, thr=0.95):

        try:
            if tracts_labels is None:
                tracts_labels = self._global.dti_xtract_labels

            if tracts_dir is None:
                tracts_dir = self._global.dti_xtract_dir

            log = os.path.join(out_folder, log_file)
            tot_voxels = 0
            classified_tracts = []
            os.makedirs(out_folder, exist_ok=True)

            # ------------------------------------------------
            # threshold tbss input, copy to out_folder, get number of voxels
            name            = os.path.basename(tbss_result_image)
            thr_input       = os.path.join(out_folder, name)
            rrun("fslmaths " + tbss_result_image + " -thr " + str(thr) + " -bin " + thr_input)
            original_voxels = get_image_nvoxels(thr_input)

            out_str = ""
            for tract in tracts_labels:
                tr_img              = os.path.join(tracts_dir, "FMRIB58_FA-skeleton_1mm_" + tract + "_mask")
                tract_tot_voxels    = get_image_nvoxels(tr_img)
                out_img             = os.path.join(out_folder, "sk_" + tract)
                rrun("fslmaths " + thr_input + " -mas " + tr_img + " " + out_img)

                res                 = get_image_nvoxels(out_img)
                if res > 0:
                    tot_voxels = tot_voxels + res
                    out_str = out_str + tract + "\t" + str(res) + " out of " + str(tract_tot_voxels) + " voxels = " + str(round((res * 100) / tract_tot_voxels, 2)) + " %" + "\n"
                    classified_tracts.append(out_img)
                else:
                    imrm(out_img)

            # ------------------------------------------------
            # create unclassified image
            unclass_img = os.path.join(out_folder, "unclass_" + os.path.basename(out_folder))
            cmd_str = "fslmaths " + thr_input
            for img in classified_tracts:
                cmd_str = cmd_str + " -sub " + img + " -bin "
            cmd_str = cmd_str + unclass_img
            rrun(cmd_str)
            unclass_vox = get_image_nvoxels(unclass_img)

            # ------------------------------------------------
            # write log file
            out_str = out_str + "\n" + "\n" + "tot voxels = " + str(tot_voxels) + " out of " + str(original_voxels) + "\n"
            out_str = out_str + "unclassified image has " + str(unclass_vox)
            with open(log, 'w', encoding='utf-8') as f:
                f.write(out_str)

        except Exception as e:
            print(e)

    # clust_res_dir: output folder of tbss's results clustering
    # datas is a tuple of two elements containing the list of values and subj_labels
    # returns tracts_data
    def tbss_summarize_clusterized_folder(self, in_clust_res_dir, datas, data_label, tbss_folder, modality="FA",
                                          subj_img_postfix="_FA_FA_to_target", ofn="scatter_tracts_", doplot=False):

        subjects_images = os.path.join(tbss_folder, modality)  # folder containing tbss subjects' folder of that modality
        results_folder  = os.path.join(tbss_folder, "results")
        os.makedirs(results_folder, exist_ok=True)

        tracts_labels   = []
        # compose header
        str_data = "subj\t" + data_label
        for entry in os.scandir(in_clust_res_dir):
            if not entry.name.startswith('.') and not entry.is_dir():
                if entry.name.startswith("sk_"):
                    lab         = remove_ext(entry.name[3:])
                    tracts_labels.append(lab)
                    str_data    = str_data + "\t" + lab
        str_data = str_data + "\n"

        tracts_data = []
        [tracts_data.append([]) for t in range(len(tracts_labels))]
        nsubj = len(datas[0])
        for i in range(nsubj):
            subj_label      = datas[1][i]
            subj_img        = os.path.join(subjects_images, subj_label + "-dti_fit" + subj_img_postfix)
            subj_img_masked = subj_img + "_masked"
            n_tracts        = 0
            str_data        = str_data + subj_label + "\t" + str(datas[0][i])

            for entry in os.scandir(in_clust_res_dir):
                if not entry.name.startswith('.') and not entry.is_dir():
                    if entry.name.startswith("sk_"):
                        mask_image(subj_img, entry.path, subj_img_masked)
                        val = get_image_mean(subj_img_masked)
                        imrm([subj_img_masked])

                        str_data = str_data + "\t" + str(val)
                        tracts_data[n_tracts].append(val)
                        n_tracts = n_tracts + 1
            str_data = str_data + "\n"

        if doplot is True:
            for t in range(len(tracts_labels)):
                fig_file = os.path.join(results_folder, tracts_labels[t] + "_" + data_label + ".png")
                plot_data.scatter_plot_dataserie(datas[0], tracts_data[t], fig_file)

        res_file = os.path.join(results_folder, ofn + modality + "_" + data_label + ".dat")

        with open(res_file, "w") as f:
            f.write(str_data)

        return tracts_data

    # create a new tbss analysis folder (only stats one), filtering an existing analysis folder
    # vols2keep: 0-based list of indices to keep
    def create_analysis_folder_from_existing(self, src_folder, new_folder, vols2keep, modalities=None):

        if modalities is None:
            modalities = ["FA", "MD", "L1", "L23"]

        # create new folder
        new_stats_folder = os.path.join(new_folder, "stats")
        os.makedirs(new_stats_folder, exist_ok=True)

        for mod in modalities:
            orig_image = os.path.join(src_folder, "stats", "all_" + mod + "_skeletonised")
            dest_image = os.path.join(new_folder, "stats", "all_" + mod + "_skeletonised")

            orig_mean_image = os.path.join(src_folder, "stats", "mean_" + mod + "_skeleton_mask")
            dest_mean_image = os.path.join(new_folder, "stats", "mean_" + mod + "_skeleton_mask")

            filter_volumes(orig_image, vols2keep, dest_image)

            imcp(orig_mean_image, dest_mean_image)

    #endregion