import ntpath
import os
import shutil
import traceback
from shutil import copyfile, move

import matlab.engine
import numpy

from group.Stats import Stats
from myfsl.utils.run import rrun
from utility import import_data_file, plot_data
from utility.images import imcp, imtest, immv, imrm, remove_ext
from utility.import_data_file import get_header_of_tabbed_file, get_icv_spm_file
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


class GroupAnalysis:

    def __init__(self, proj):
        self.project = proj
        self._global = self.project._global

    # ====================================================================================================================================================
    # DATA PREPARATION
    # ====================================================================================================================================================

    # given a subjects list, it creates their template and project all the c1 images to its normalized version
    # create a folder name and its subfolders : subjects (normalized images), flowfields, stats
    # RC1_IMAGES:    {  '/media/data/MRI/projects/ELA/subjects/0202/s1/mpr/rc20202-t1.nii,1'
    #                   '/media/data/MRI/projects/ELA/subjects/0503/s1/mpr/rc20503-t1.nii,1'}
    def create_vbm_spm_template_normalize(self, name, subjs, sess_id=1,
                                          spm_template_name="spm_dartel_createtemplate_normalize"):

        self.subjects_list = subjs
        self.working_dir = os.path.join(self.project.vbm_dir, name)

        # set dirs
        spm_script_dir = os.path.join(self.project.script_dir, "mpr", "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
        in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")

        out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + ".m")
        out_batch_job = os.path.join(out_batch_dir, spm_template_name + "_job.m")

        os.makedirs(out_batch_dir, exist_ok=True)
        # =======================================================
        # START !!!!
        # =======================================================
        # create job file
        T1_darteled_images_1 = "{\r"
        T1_darteled_images_2 = "{\r"
        T1_images_1 = "{\r"

        for subj in self.subjects_list:
            T1_darteled_images_1 = T1_darteled_images_1 + "\'" + os.path.join(subj.t1_spm_dir,
                                                                              "rc1T1_" + subj.label + ".nii") + ",1\'\r"
            T1_darteled_images_2 = T1_darteled_images_2 + "\'" + os.path.join(subj.t1_spm_dir,
                                                                              "rc2T1_" + subj.label + ".nii") + ",1\'\r"
            T1_images_1 = T1_images_1 + "\'" + os.path.join(subj.t1_spm_dir, "c1T1_" + subj.label + ".nii") + "\'\r"

        T1_darteled_images_1 = T1_darteled_images_1 + "\r}"
        T1_darteled_images_2 = T1_darteled_images_2 + "\r}"
        T1_images_1 = T1_images_1 + "\r}"

        copyfile(in_batch_job, out_batch_job)
        sed_inplace(out_batch_job, "<RC1_IMAGES>", T1_darteled_images_1)
        sed_inplace(out_batch_job, "<RC2_IMAGES>", T1_darteled_images_2)
        sed_inplace(out_batch_job, "<C1_IMAGES>", T1_images_1)
        sed_inplace(out_batch_job, "<TEMPLATE_NAME>", name)
        sed_inplace(out_batch_job, "<TEMPLATE_ROOT_DIR>", self.project.vbm_dir)

        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, "X", "1")
        sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

        eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])
        # eng = matlab.engine.start_matlab()
        print("running SPM batch template: " + name)
        # eval("eng." + os.path.basename(os.path.splitext(out_batch_start)[0]) + "(nargout=0)")
        # eng.quit()

        affine_trasf_mat = os.path.join(self.subjects_list[0].t1_spm_dir, name + "_6_2mni.mat")
        move(affine_trasf_mat, os.path.join(self.project.vbm_dir, name, "flowfields", name + "_6_2mni.mat"))

    # create a fslvbm folder using spm's vbm output
    def create_fslvbm_from_spm(self, subjs, smw_folder, vbmfsl_folder):

        stats_dir = os.path.join(vbmfsl_folder, "stats")
        struct_dir = os.path.join(vbmfsl_folder, "struct")

        os.makedirs(stats_dir, exist_ok="True")
        os.makedirs(struct_dir, exist_ok="True")

        for subj in subjs:
            imcp(os.path.join(smw_folder, "smwc1T1_biascorr_" + subj.label),
                 os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label))
            rrun("fslmaths " + os.path.join(struct_dir, "smwc1T1_biascorr_" + subj.label) + " -thr 0.1 " + os.path.join(
                struct_dir, "smwc1T1_biascorr_" + subj.label))

        # create merged image
        cur_dir = os.getcwd()
        os.chdir(stats_dir)

        # trick...since there are nii and nii.gz. by adding ".gz" in the check I consider only the nii
        images = [os.path.join(struct_dir, f) for f in os.listdir(struct_dir) if
                  os.path.isfile(os.path.join(struct_dir, f + ".gz"))]

        rrun("fslmerge -t GM_merg" + " " + " ".join(images))
        rrun("fslmaths GM_merg" + " -Tmean -thr 0.05 -bin GM_mask -odt char")

        shutil.rmtree(struct_dir)

    # read a matrix file and add total ICV as last column
    # here it assumes [integer, integer, integer, integer, integer, float4]
    def add_icv_2_data_matrix(self, subjs, input_data_file):

        nsubj = len(subjs)
        data_file = numpy.loadtxt(input_data_file)
        ndata = len(data_file)

        icv_scores = numpy.zeros((ndata, 1))

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

            icv_scores[cnt, 0] = round(float(values[1]) + float(values[2]) + float(values[3]), 4)
            cnt = cnt + 1

        b = numpy.hstack((data_file, icv_scores))
        numpy.savetxt(input_data_file, b, ['%1.0f', '%1.0f', '%5.0f', '%5.0f', '%5.0f', '%2.4f'], '\t')

    # read xtract's stats.csv file of each subject in the given list and create a tabbed file (ofp) with given values/tract
    # calls the subject routine
    def xtract_export_group_data(self, subjs, ofp, tracts=None, values=None, ifn="stats.csv"):

        if tracts is None:
            tracts = self._global.dti_xtract_labels

        if values is None:
            values = ["mean_FA", "mean_MD"]

        file_str = "subj\t"
        for tr in tracts:
            for v in values:
                file_str = file_str + tr + "_" + v + "\t"
        file_str = file_str + "\n"

        for subj in subjs:
            file_str = file_str + subj.dti.xtract_read_file(tracts, values, ifn)[0] + "\n"

        with open(ofp, 'w', encoding='utf-8') as f:
            f.write(file_str)

    # ---------------------------------------------------
    # STATS - VBM
    # ---------------------------------------------------

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>, <ITV_SCORES>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def create_spm_vbm_dartel_stats_factdes_1Wanova(self, darteldir, groups_labels, cov_name, cov_interaction=1,
                                                    data_file=None, glob_calc="subj_icv", cov_interactions=None,
                                                    expl_mask="icv", sess_id=1,
                                                    spm_template_name="spm_vbm_stats_1Wanova_design_estimate"):

        try:
            # ---------------------------------------------------------------------------
            # sanity check
            # ---------------------------------------------------------------------------
            if data_file is not None:
                if os.path.exists(data_file) is False:
                    print("ERROR in create_spm_vbm_dartel_stats_factdes_1Wanova, given data_file (" + str(
                        data_file) + ") does not exist......exiting")
                    return

                header = get_header_of_tabbed_file(data_file)

                if cov_name in header is False:
                    print(
                        "ERROR in create_spm_vbm_dartel_stats_factdes_1Wanova, the given data_file does not contain all requested covariates")
                    return

            # ---------------------------------------------------------------------------
            # create template files
            # ---------------------------------------------------------------------------
            out_batch_job, out_batch_start = self.create_batch_files(spm_template_name, "mpr")

            # ---------------------------------------------------------------------------
            # stats dir
            # ---------------------------------------------------------------------------
            statsdir = os.path.join(darteldir, "stats")
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # ---------------------------------------------------------------------------
            # compose images string
            # ---------------------------------------------------------------------------
            cells_images = ""
            cnt = 0
            for grp in groups_labels:
                cnt = cnt + 1
                cells_images = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(" + str(
                    cnt) + ").scans = "

                subjs = self.project.get_subjects(grp, sess_id)

                grp1_images = "{\n"
                for subj in subjs:
                    grp1_images = grp1_images + "\'" + subj.t1_cat_resampled_surface + "\'\n"
                grp1_images = grp1_images + "\n};"

                cells_images = cells_images + grp1_images + "\n"
            sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

            # ---------------------------------------------------------------------------
            # global calculation
            # ---------------------------------------------------------------------------
            no_corr_str = "matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = 1;\n matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 1;"
            user_corr_str1 = "matlabbatch{1}.spm.stats.factorial_design.globalc.g_user.global_uval = [\n"
            user_corr_str2 = "];\n matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 2;"
            gc_str = ""

            if glob_calc == "subj_icv":  # read icv file from each subject/mpr/spm folder

                icv = ""
                for grp in groups_labels:
                    for subj in self.project.get_subjects(grp):
                        icv = icv + str(get_icv_spm_file(subj.t1_spm_icv_file)) + "\n"
                gc_str = user_corr_str1 + icv + user_corr_str2

            elif glob_calc == "subj_tiv":  # read tiv file from each subject/mpr/cat folder
                gc_str = no_corr_str
            elif glob_calc == "":  # don't correct
                gc_str = no_corr_str
            elif isinstance(glob_calc,
                            str) is True and data_file is not None:  # must be a column in the given data_file list of

                icvs = []
                for grp in groups_labels:
                    icvs = icvs + self.project.get_filtered_column(glob_calc, self.project.get_subjects_labels(grp))
                gc_str = user_corr_str1 + import_data_file.list2spm_text_column(
                    icvs) + user_corr_str2  # list2spm_text_column ends with a "\n"

            sed_inplace(out_batch_job, "<GLOBAL_SCORES>", gc_str)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if cov_name != "":
                Stats.spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, self.project, cov_name,
                                                    cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>",
                            "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # ---------------------------------------------------------------------------
            # explicit mask
            # ---------------------------------------------------------------------------
            if expl_mask == "icv":
                sed_inplace(out_batch_job, "<EXPL_MASK>", self._global.spm_icv_mask + ",1")

            elif expl_mask == "":
                sed_inplace(out_batch_job, "<EXPL_MASK>", "")
            else:
                if imtest(expl_mask) is False:
                    print(
                        "ERROR in create_spm_vbm_dartel_stats_factdes_1Wanova, given explicit mask is not present....exiting")
                    return
                sed_inplace(out_batch_job, "<EXPL_MASK>", expl_mask + ",1")

            # ---------------------------------------------------------------------------
            # call matlab
            # ---------------------------------------------------------------------------
            eng = matlab.engine.start_matlab()
            print("running SPM batch template: " + statsdir)
            eval("eng." + os.path.basename(os.path.splitext(out_batch_start)[0]) + "(nargout=0)")
            eng.quit()

        except Exception as e:
            traceback.print_exc()
            print(e)

    def create_spm_vbm_dartel_stats_factdes_multregr(self, darteldir, grp_label, cov_names,
                                                     data_file=None, glob_calc="subj_icv", cov_interactions=None,
                                                     expl_mask="icv", sess_id=1,
                                                     spm_template_name="spm_vbm_stats_multregr_design_estimate",
                                                     spm_contrasts_template_name="",
                                                     mult_corr="FWE", pvalue=0.05, cluster_extend=0):
        try:
            # ---------------------------------------------------------------------------
            # sanity check
            # ---------------------------------------------------------------------------
            if data_file is not None:
                if os.path.exists(data_file) is False:
                    print("ERROR in create_spm_vbm_dartel_stats_factdes_multregr, given data_file (" + str(
                        data_file) + ") does not exist......exiting")
                    return

                header = get_header_of_tabbed_file(data_file)

                if all(elem in header for elem in cov_names) is False:
                    print(
                        "ERROR in create_spm_vbm_dartel_stats_factdes_multregr, the given data_file does not contain all requested covariates")
                    return

            # ---------------------------------------------------------------------------
            # create template files
            # ---------------------------------------------------------------------------
            out_batch_job, out_batch_start = self.create_batch_files(spm_template_name, "mpr")

            # ---------------------------------------------------------------------------
            # stats dir
            # ---------------------------------------------------------------------------
            statsdir = os.path.join(darteldir, "stats")
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # ---------------------------------------------------------------------------
            # compose images string
            # ---------------------------------------------------------------------------
            subjs_dir = os.path.join(darteldir, "subjects")
            cells_images = "\r"
            subjs = self.project.get_subjects(grp_label, sess_id)

            for subj in subjs:
                img = os.path.join(subjs_dir, "smwc1T1_" + subj.label + ".nii")
                cells_images = cells_images + "\'" + img + "\'\r"

            sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

            # ---------------------------------------------------------------------------
            # global calculation
            # ---------------------------------------------------------------------------
            no_corr_str = "matlabbatch{1}.spm.stats.factorial_design.globalc.g_omit = 1;\n matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 1;"
            user_corr_str1 = "matlabbatch{1}.spm.stats.factorial_design.globalc.g_user.global_uval = [\n"
            user_corr_str2 = "];\n matlabbatch{1}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{1}.spm.stats.factorial_design.globalm.glonorm = 2;"

            if glob_calc == "subj_icv":  # read icv file from each subject/mpr/spm folder
                icv = ""
                for subj in self.project.get_subjects(grp_label):
                    icv = icv + str(get_icv_spm_file(subj.t1_spm_icv_file)) + "\n"
                gc_str = user_corr_str1 + icv + user_corr_str2
            elif glob_calc == "subj_tiv":  # read tiv file from each subject/mpr/cat folder
                gc_str = no_corr_str
            elif glob_calc == "":  # don't correct
                gc_str = no_corr_str
            elif isinstance(glob_calc,
                            str) is True and data_file is not None:  # must be a column in the given data_file list of
                icv = self.project.get_filtered_column(glob_calc, self.project.get_subjects_labels(grp_label))
                gc_str = user_corr_str1 + import_data_file.list2spm_text_column(
                    icv) + user_corr_str2  # list2spm_text_column ends with a "\n"

            sed_inplace(out_batch_job, "<GLOBAL_SCORES>", gc_str)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if len(cov_names) > 0:
                Stats.spm_stats_add_manycov_1group(out_batch_job, grp_label, self.project, cov_names, cov_interactions,
                                                   data_file)
            else:
                print("ERROR : No covariates in a multiple regression")
                return ""

            # ---------------------------------------------------------------------------
            # explicit mask
            # ---------------------------------------------------------------------------
            if expl_mask == "icv":
                sed_inplace(out_batch_job, "<EXPL_MASK>", self._global.spm_icv_mask + ",1")

            elif expl_mask == "":
                sed_inplace(out_batch_job, "<EXPL_MASK>", "")
            else:
                if imtest(expl_mask) is False:
                    print(
                        "ERROR in create_spm_vbm_dartel_stats_factdes_1Wanova, given explicit mask is not present....exiting")
                    return
                sed_inplace(out_batch_job, "<EXPL_MASK>", expl_mask + ",1")

            # ---------------------------------------------------------------------------
            # call matlab
            # ---------------------------------------------------------------------------
            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir],
                                       endengine=False)

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                self.create_spm_stats_predefined_contrasts_results(statsdir, spm_contrasts_template_name, eng)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # ---------------------------------------------------
    # STATS - SURFACES THICKNESS (CAT12)
    # ---------------------------------------------------

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <GROUPS_IMAGES> must be something like :
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(1).scans = {  'xxx'
    #                                                                               'yyy'
    #                                                                            };
    #       matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(2).scans = {'<UNDEFINED>'};
    def create_cat_thickness_stats_factdes_1Wanova(self, statsdir, groups_labels, cov_name, cov_interaction=1,
                                                   data_file=None, sess_id=1,
                                                   spm_template_name="cat_thickness_stats_1Wanova_onlydesign",
                                                   spm_contrasts_template_name=""):

        try:

            # ---------------------------------------------------------------------------
            # create template files
            # ---------------------------------------------------------------------------
            out_batch_job, out_batch_start = self.create_batch_files(spm_template_name, "mpr")

            # ---------------------------------------------------------------------------
            #
            # ---------------------------------------------------------------------------
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # ---------------------------------------------------------------------------
            # compose images string
            # ---------------------------------------------------------------------------
            cells_images = ""
            cnt = 0
            for grp in groups_labels:
                cnt = cnt + 1
                cells_images = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(" + str(
                    cnt) + ").scans = "

                subjs = self.project.get_subjects(grp, sess_id)

                grp1_images = "{\r"
                for subj in subjs:
                    grp1_images = grp1_images + "\'" + subj.t1_cat_resampled_surface + "\'\r"
                grp1_images = grp1_images + "\r};"

                cells_images = cells_images + grp1_images + "\r"
            sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if cov_name != "":
                Stats.spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, self.project, cov_name,
                                                    cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>",
                            "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # ---------------------------------------------------------------------------
            #
            # ---------------------------------------------------------------------------

            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir],
                                       endengine=False)

            # ---------------------------------------------------------------------------
            # estimate surface model in cat 12.6
            # ---------------------------------------------------------------------------
            if self._global.cat_version == "cat12.6":
                # model estimate
                print("estimating surface model")
                eng.pymri_cat_surfaces_stat_spm(statsdir, nargout=0)

            # ---------------------------------------------------------------------------
            # check whether running a given contrasts batch. script must only modify SPM.mat file
            # ---------------------------------------------------------------------------
            if spm_contrasts_template_name != "":
                self.create_spm_stats_predefined_contrasts_results(statsdir, spm_contrasts_template_name, eng)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUPS_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # <FACTORS_CELLS> must be something like :
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).levels = [1
    #                                                          1];
    # matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(1).scans = {
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_T15_C_001.gii'
    #     '/data/MRI/projects/T15/subjects/T15_C_001/s1/mpr/anat/cat_proc/surf/rh.sphere.T1_T15_C_001.gii'
    # };
    # cells is [factor][level][subjects_label]
    def create_cat_thickness_stats_factdes_2Wanova(self, statsdir, factors_labels, cells, cov_name="",
                                                   cov_interaction=1, data_file=None, sess_id=1,
                                                   spm_template_name="cat_thickness_stats_2Wanova_onlydesign"):

        try:
            # ---------------------------------------------------------------------------
            # create template files
            # ---------------------------------------------------------------------------
            out_batch_job, out_batch_start = self.create_batch_files(spm_template_name, "mpr")

            # ---------------------------------------------------------------------------
            # stats dir
            # ---------------------------------------------------------------------------
            os.makedirs(statsdir, exist_ok=True)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # ---------------------------------------------------------------------------
            # compose cells string
            # ---------------------------------------------------------------------------
            nfactors = len(factors_labels)
            nlevels = [len(cells), len(cells[0])]  # nlevels for each factor

            # checks
            # if nfactors != len(cells):
            #     print("Error: num of factors labels (" + str(nfactors) + ") differs from cells content (" + str(len(cells)) + ")")
            #     return

            groups_labels = []  # will host the subjects labels for covariate specification
            cells_images = ""
            ncell = 0
            for f1 in range(0, nlevels[0]):
                for f2 in range(0, nlevels[1]):
                    ncell = ncell + 1
                    cells_images = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(
                        ncell) + ").levels = [" + str(f1 + 1) + "\n" + str(f2 + 1) + "];\n"
                    cells_images = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(
                        ncell) + ").scans = {\n"

                    subjs = self.project.get_subjects(cells[f1][f2], sess_id)
                    for subj in subjs:
                        cells_images = cells_images + "'" + subj.t1_cat_resampled_surface + "'\n"
                    cells_images = cells_images + "};"

            sed_inplace(out_batch_job, "<FACTOR1_NAME>", factors_labels[0])
            sed_inplace(out_batch_job, "<FACTOR1_NLEV>", str(nlevels[0]))
            sed_inplace(out_batch_job, "<FACTOR2_NAME>", factors_labels[1])
            sed_inplace(out_batch_job, "<FACTOR2_NLEV>", str(nlevels[1]))
            sed_inplace(out_batch_job, "<FACTORS_CELLS>", cells_images)

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            # ---------------------------------------------------------------------------
            if cov_name != "":
                Stats.spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, self.project, cov_name,
                                                    cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>",
                            "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # ---------------------------------------------------------------------------
            #
            # ---------------------------------------------------------------------------
            print("running SPM batch template: " + statsdir)
            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir],
                                       endengine=False)

            # ---------------------------------------------------------------------------
            # estimate surface model in cat 12.6
            # ---------------------------------------------------------------------------
            if self._global.cat_version == "cat12.6":
                # model estimate
                print("estimating surface model")
                eng.pymri_cat_surfaces_stat_spm(statsdir, nargout=0)

            # ---------------------------------------------------------------------------
            eng.quit()
            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)

    # params to replace: <STATS_DIR>, <GROUP1_IMAGES>, <GROUP2_IMAGES>, <COV1_LIST>, <COV1_NAME>
    # GROUPx_IMAGES are :  'mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_XXXXXXXXXX.gii,1'
    def create_cat_thickness_stats_factdes_2samplesttest(self, statsdir, grp1_label, grp2_label, cov_name="",
                                                         cov_interaction=1, data_file=None, sess_id=1,
                                                         spm_template_name="cat_thickness_stats_2samples_ttest_onlydesign",
                                                         mult_corr="FWE", pvalue=0.05, cluster_extend=0,
                                                         grp_labels=["g1", "g2"]):

        try:
            os.makedirs(statsdir, exist_ok=True)
            # set dirs
            spm_script_dir = os.path.join(self.project.script_dir, "mpr", "spm")
            out_batch_dir = os.path.join(spm_script_dir, "batch")

            in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
            in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")

            out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + ".m")
            out_batch_job = os.path.join(out_batch_dir, spm_template_name + "_job.m")

            # get subjects lists
            if isinstance(grp1_label, str):
                grp_labels[0] = grp1_label
            if isinstance(grp2_label, str):
                grp_labels[1] = grp2_label

            subjs1 = self.project.get_subjects(grp1_label, sess_id)
            subjs2 = self.project.get_subjects(grp2_label, sess_id)

            # compose images string
            grp1_images = "{\r"
            for subj in subjs1:
                grp1_images = grp1_images + "\'" + subj.t1_cat_resampled_surface + "\'\r"
            grp1_images = grp1_images + "\r}"

            grp2_images = "{\r"
            for subj in subjs2:
                grp2_images = grp2_images + "\'" + subj.t1_cat_resampled_surface + "\'\r"
            grp2_images = grp2_images + "\r}"

            # set job file
            copyfile(in_batch_job, out_batch_job)
            sed_inplace(out_batch_job, "<GROUP1_IMAGES>", grp1_images)
            sed_inplace(out_batch_job, "<GROUP2_IMAGES>", grp2_images)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # check whether adding a covariate
            if cov_name != "":
                Stats.spm_stats_add_1cov_manygroups(out_batch_job, [grp1_label, grp2_label], self.project, cov_name,
                                                    cov_interaction, data_file)
            else:
                sed_inplace(out_batch_job, "<COV_STRING>",
                            "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")

            # set start file
            copyfile(in_batch_start, out_batch_start)
            sed_inplace(out_batch_start, "X", "1")
            sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir],
                                       endengine=False)

            # model estimate
            print("estimating surface model")
            eng.pymri_cat_surfaces_stat_spm(statsdir, nargout=0)
            eng.quit()

            self.create_spm_stats_2samplesttest_contrasts_results(os.path.join(statsdir, "SPM.mat"),
                                                                  grp_labels[0] + " > " + grp_labels[1],
                                                                  grp_labels[1] + " > " + grp_labels[0],
                                                                  "spm_stats_2samplesttest_contrasts_results",
                                                                  mult_corr, pvalue, cluster_extend)

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    #
    def create_cat_thickness_stats_1group_multregr(self, statsdir, grp_label, cov_names, anal_name,
                                                   cov_interactions=None, data_file=None, sess_id=1,
                                                   spm_template_name="cat_thickness_stats_1group_multiregr_check_estimate",
                                                   spm_contrasts_template_name="", mult_corr="FWE", pvalue=0.05,
                                                   cluster_extend=0):
        try:
            os.makedirs(statsdir, exist_ok=True)
            # set dirs
            spm_script_dir = os.path.join(self.project.script_dir, "mpr", "spm")
            out_batch_dir = os.path.join(spm_script_dir, "batch")

            in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
            in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")

            out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + "_" + anal_name + ".m")
            out_batch_job = os.path.join(out_batch_dir, spm_template_name + "_" + anal_name + "_job.m")

            # set job file
            copyfile(in_batch_job, out_batch_job)

            # set start file
            copyfile(in_batch_start, out_batch_start)
            sed_inplace(out_batch_start, "X", "1")
            sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

            # ---------------------------------------------------------------------------
            # compose images string
            cells_images = "\r"
            subjs = self.project.get_subjects(grp_label, sess_id)

            for subj in subjs:
                cells_images = cells_images + "\'" + subj.t1_cat_resampled_surface + "\'\r"

            # ---------------------------------------------------------------------------
            # check whether adding a covariate
            if len(cov_names) > 0:
                Stats.spm_stats_add_manycov_1group(out_batch_job, grp_label, self.project, cov_names, cov_interactions,
                                                   data_file)
            else:
                print("ERROR : No covariates in a multiple regression")
                return ""

            sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            eng = call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir],
                                       endengine=False)

            if self._global.cat_version == "cat12.6":
                # model estimate
                print("estimating surface model")
                eng.pymri_cat_surfaces_stat_spm(statsdir, nargout=0)

            # check whether running a given contrasts batch. script must only modify SPM.mat file
            if spm_contrasts_template_name != "":
                self.create_spm_stats_predefined_contrasts_results(statsdir, spm_contrasts_template_name, eng)

            eng.quit()

            return os.path.join(statsdir, "SPM.mat")

        except Exception as e:
            traceback.print_exc()
            print(e)
            return ""

    # ---------------------------------------------------
    # STATS - GENERAL
    # ---------------------------------------------------

    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    def create_spm_stats_2samplesttest_contrasts_results(self, spmmat, c1_name="A>B", c2_name="B>A",
                                                         spm_template_name="spm_stats_2samplesttest_contrasts_results",
                                                         mult_corr="FWE", pvalue=0.05, cluster_extend="none"):

        try:
            # set dirs
            spm_script_dir = os.path.join(self.project.script_dir, "mpr", "spm")
            out_batch_dir = os.path.join(spm_script_dir, "batch")

            in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
            in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")

            out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + ".m")
            out_batch_job = os.path.join(out_batch_dir, spm_template_name + "_job.m")

            # set job file
            copyfile(in_batch_job, out_batch_job)
            sed_inplace(out_batch_job, "<SPM_MAT>", spmmat)
            sed_inplace(out_batch_job, "<STATS_DIR>", ntpath.dirname(spmmat))
            sed_inplace(out_batch_job, "<C1_NAME>", c1_name)
            sed_inplace(out_batch_job, "<C2_NAME>", c2_name)
            sed_inplace(out_batch_job, "<MULT_CORR>", mult_corr)
            sed_inplace(out_batch_job, "<PVALUE>", str(pvalue))
            sed_inplace(out_batch_job, "<CLUSTER_EXTEND>", str(cluster_extend))

            Stats.cat_replace_results_trasformation_string(out_batch_job, 3, mult_corr, pvalue, cluster_extend)

            # set start file
            copyfile(in_batch_start, out_batch_start)
            sed_inplace(out_batch_start, "X", "1")
            sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

            call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

        except Exception as e:
            traceback.print_exc()
            print(e)

    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    def create_cat_stats_1group_multregr_contrasts_results(self, spmmat, cov_names,
                                                           spm_template_name="cat_stats_contrasts_results",
                                                           mult_corr="FWE", pvalue=0.05, cluster_extend="none"):

        try:
            # set dirs
            spm_script_dir = os.path.join(self.project.script_dir, "mpr", "spm")
            out_batch_dir = os.path.join(spm_script_dir, "batch")

            in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
            in_batch_job = os.path.join(self._global.spm_templates_dir, spm_template_name + "_job.m")

            out_batch_start = os.path.join(out_batch_dir, "start_" + spm_template_name + ".m")
            out_batch_job = os.path.join(out_batch_dir, spm_template_name + "_job.m")

            # set job file
            copyfile(in_batch_job, out_batch_job)
            sed_inplace(out_batch_job, "<SPM_MAT>", spmmat)
            sed_inplace(out_batch_job, "<STATS_DIR>", ntpath.dirname(spmmat))

            Stats.replace_1group_multregr_contrasts(out_batch_job, cov_names, tool="cat")

            sed_inplace(out_batch_job, "<MULT_CORR>", mult_corr)
            sed_inplace(out_batch_job, "<PVALUE>", str(pvalue))
            sed_inplace(out_batch_job, "<CLUSTER_EXTEND>", str(cluster_extend))

            # set start file
            copyfile(in_batch_start, out_batch_start)
            sed_inplace(out_batch_start, "X", "1")
            sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

            call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir, self._global.spm_dir])

        except Exception as e:
            traceback.print_exc()
            print(e)

    # run a prebuilt batch file in a non-standard location, which only need to set the stat folder and SPM.mat path
    def create_spm_stats_predefined_contrasts_results(self, statsdir, spm_template_full_path_noext, eng=None):

        try:

            spm_mat_path = os.path.join(statsdir, "SPM.mat")
            input_batch_name = ntpath.basename(spm_template_full_path_noext)

            # set dirs
            spm_script_dir = os.path.join(self.project.script_dir, "mpr", "spm")
            out_batch_dir = os.path.join(spm_script_dir, "batch")

            in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")
            in_batch_job = spm_template_full_path_noext + ".m"

            out_batch_start = os.path.join(out_batch_dir, "create_" + input_batch_name + "_start.m")
            out_batch_job = os.path.join(out_batch_dir, "create_" + input_batch_name + ".m")

            # set job file
            copyfile(in_batch_job, out_batch_job)
            sed_inplace(out_batch_job, "<SPM_MAT>", spm_mat_path)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            # set start file
            copyfile(in_batch_start, out_batch_start)
            sed_inplace(out_batch_start, "X", "1")
            sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

            if eng is None:
                call_matlab_spmbatch(out_batch_start, [self._global.spm_functions_dir,
                                                       self._global.spm_dir])  # open a new session and then end it
            else:
                call_matlab_spmbatch(out_batch_start,
                                     endengine=False)  # I assume that the caller will end the matlab session and def dir have been already specified

        except Exception as e:
            traceback.print_exc()
            print(e)

    # returns out_batch_job
    def create_batch_files(self, templfile_noext, seq):

        input_batch_name = ntpath.basename(templfile_noext)

        # set dirs
        spm_script_dir = os.path.join(self.project.script_dir, seq, "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        if os.path.exists(templfile_noext) is True:
            in_batch_job = templfile_noext
        else:
            in_batch_job = os.path.join(self._global.spm_templates_dir, templfile_noext + "_job.m")

        out_batch_start = os.path.join(out_batch_dir, "create_" + input_batch_name + "_start.m")
        out_batch_job = os.path.join(out_batch_dir, "create_" + input_batch_name + ".m")

        # set job file
        copyfile(in_batch_job, out_batch_job)

        # set start file
        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, "X", "1")
        sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

        return out_batch_job, out_batch_start

    # ---------------------------------------------------
    def group_melodic(self, out_dir_name, subjects, tr):

        if os.path.exists(out_dir_name):
            os.removedirs(out_dir_name)

        os.makedirs(out_dir_name)

        subjs = ""
        bg_images = ""
        masks = ""

        missing_data = ""

        for s in subjects:

            if imtest(s.rs_final_regstd_image) is True and imtest(s.rs_final_regstd_bgimage) and imtest(
                    s.rs_final_regstd_bgimage):
                subjs = subjs + " " + s.rs_final_regstd_image
                bgimages = subjs + " " + s.rs_final_regstd_bgimage
                masks = masks + " " + s.rs_final_regstd_mask
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

    # ====================================================================================================================================================
    # TBSS
    # ====================================================================================================================================================
    # run tbss for FA
    def tbss_run_fa(self, group_label, odn, sessid=1, prepare=True, proc=True, postreg="S", prestat_thr=0.2):

        root_analysis_folder = os.path.join(self.project.tbss_dir, odn)

        os.makedirs(root_analysis_folder, exist_ok=True)
        os.makedirs(os.path.join(root_analysis_folder, "design"), exist_ok=True)

        # copy DTIFIT IMAGES to MAIN_ANALYSIS_FOLDER
        if prepare is True:

            print("copy subjects' corresponding dtifit_FA images to analysis folder")
            subjects = self.project.get_subjects(group_label, sessid)
            for subj in subjects:
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
    def tbss_run_alternatives(self, group_label, input_folder, modalities, sessid=1, prepare=True, proc=True):

        input_stats = os.path.join(input_folder, "stats")

        # copy DTIFIT IMAGES to MAIN_ANALYSIS_FOLDER
        if prepare is True:

            print("copy subjects' corresponding dtifit_XX images to analysis folder")
            subjects = self.project.get_subjects(group_label, sessid)
            for subj in subjects:

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

    # uses the union between template FA_skeleton and xtract's main tracts to clusterize a tbss output
    def tbss_clusterize_results_by_atlas(self, tbss_result_image, tracts_labels, tracts_dir, out_folder,
                                         log_file="log.txt", thr=0.95):

        try:
            log = os.path.join(out_folder, log_file)
            tot_voxels = 0
            classified_tracts = []
            os.makedirs(out_folder, exist_ok=True)

            # ------------------------------------------------
            # threshold tbss input, copy to out_folder, get number of voxels
            name = os.path.basename(tbss_result_image)
            thr_input = os.path.join(out_folder, name)
            rrun("fslmaths " + tbss_result_image + " -thr " + str(thr) + " -bin " + thr_input)
            original_voxels = rrun("fslstats " + thr_input + " -V").strip().split(" ")[0]

            out_str = ""
            for tract in tracts_labels:
                tr_img = os.path.join(tracts_dir, "FMRIB58_FA-skeleton_1mm_" + tract + "_mask")

                tract_tot_voxels = int(rrun("fslstats " + tr_img + " -V").strip().split(" ")[0])

                out_img = os.path.join(out_folder, "sk_" + tract)
                rrun("fslmaths " + thr_input + " -mas " + tr_img + " " + out_img)

                res = rrun("fslstats " + out_img + " -V").strip().split(" ")[0]
                if int(res) > 0:
                    tot_voxels = tot_voxels + int(res)
                    out_str = out_str + tract + "\t" + res + " out of " + str(tract_tot_voxels) + " voxels = " + str(
                        round((int(res) * 100) / tract_tot_voxels, 2)) + " %" + "\n"
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
            unclass_vox = rrun("fslstats " + unclass_img + " -V").strip().split(" ")[0]

            # ------------------------------------------------
            # write log file
            out_str = out_str + "\n" + "\n" + "tot voxels = " + str(tot_voxels) + " out of " + str(
                original_voxels) + "\n"
            out_str = out_str + "unclassified image has " + str(unclass_vox)
            with open(log, 'w', encoding='utf-8') as f:
                f.write(out_str)

        except Exception as e:
            e

    # clust_res_dir: output folder of tbss's results clustering
    # datas is a tuple of two elements containing the list of values and subj_labels
    def tbss_plot_clusterized_folder(self, in_clust_res_dir, datas, data_label, tbss_folder, modality="FA",
                                     subj_img_postfix="_FA_FA_to_target", ofn="res_"):

        subjects_images = os.path.join(tbss_folder,
                                       modality)  # folder containing tbss subjects' folder of that modality
        results_folder = os.path.join(tbss_folder, "results")
        os.makedirs(results_folder, exist_ok=True)

        tracts_labels = []
        # compose header
        str_data = "subj\t" + data_label
        for entry in os.scandir(in_clust_res_dir):
            if not entry.name.startswith('.') and not entry.is_dir():
                if entry.name.startswith("sk_"):
                    lab = remove_ext(entry.name[3:])
                    tracts_labels.append(lab)
                    str_data = str_data + "\t" + lab
        str_data = str_data + "\n"

        tracts_data = []
        [tracts_data.append([]) for t in range(len(tracts_labels))]
        nsubj = len(datas[0])
        for i in range(nsubj):
            subj_label = datas[1][i]
            subj_img = os.path.join(subjects_images, subj_label + "-dti_fit" + subj_img_postfix)
            subj_img_masked = subj_img + "_masked"
            n_tracts = 0
            str_data = str_data + subj_label + "\t" + str(datas[0][i])

            for entry in os.scandir(in_clust_res_dir):
                if not entry.name.startswith('.') and not entry.is_dir():
                    if entry.name.startswith("sk_"):
                        rrun("fslmaths " + subj_img + " -mas " + entry.path + " " + subj_img_masked)
                        val = float(rrun("fslstats " + subj_img_masked + " -M").strip())
                        imrm([subj_img_masked])

                        str_data = str_data + "\t" + str(val)
                        tracts_data[n_tracts].append(val)
                        n_tracts = n_tracts + 1
            str_data = str_data + "\n"

        for t in range(len(tracts_labels)):
            fig_file = os.path.join(results_folder, tracts_labels[t] + "_" + data_label + ".png")
            plot_data.scatter_plot_dataserie(datas[0], tracts_data[t], fig_file)

        res_file = os.path.join(results_folder, "scatter_tracts_" + modality + "_" + data_label + ".dat")

        with open(res_file, "w") as f:
            f.write(str_data)
