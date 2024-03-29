import os
# import ssl    # it was needed, can't remember when

from data.SubjectsDataDict import SubjectsDataDict
from data.utilities import list2spm_text_column
from group.spm_utilities import SubjCondition
from utility.exceptions import DataFileException
from utility.images.Image import Image
from utility.matlab import call_matlab_function_noret, call_matlab_spmbatch
from utility.utilities import is_list_of
from utility.fileutilities import sed_inplace


class SPMStatsUtils:

    # conditions is a list of SubjCondition(name, onsets, duration)
    @staticmethod
    def spm_get_fmri_subj_stats_conditions_string_1session(conditions):

        if not is_list_of(conditions, SubjCondition):
            raise Exception("Error in SPMStatsUtils.spm_get_fmri_subj_stats_conditions_string_1session, conditions list is not valid")

        conditions_string = ""
        for c in range(1, len(conditions) + 1):
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").name = \'" + conditions[c - 1].name + "\';" + "\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").onset = [" + conditions[c - 1].onsets + "];\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").tmod = 0;\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").duration = " + conditions[c - 1].duration + ";\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").pmod = struct('name', {}, 'param', {}, 'poly', {});\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").orth = " + conditions[c - 1].orth + ";\n")

        return conditions_string

    @staticmethod
    def spm_get_fmri_subj_stats_conditions_string_ithsession(conditions, sessid):

        if not is_list_of(conditions, SubjCondition):
            raise Exception("Error in SPMStatsUtils.spm_get_fmri_subj_stats_conditions_string_1session, conditions list is not valid")

        conditions_string = ""
        for c in range(1, len(conditions) + 1):
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(sessid) + ").cond(" + str(c) + ").name = \'" + conditions[c - 1].name + "\';" + "\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(sessid) + ").cond(" + str(c) + ").onset = [" + conditions[c - 1].onsets + "];\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(sessid) + ").cond(" + str(c) + ").tmod = 0;\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(sessid) + ").cond(" + str(c) + ").duration = " + conditions[c - 1].duration + ";\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(sessid) + ").cond(" + str(c) + ").pmod = struct('name', {}, 'param', {}, 'poly', {});\n")
            conditions_string += ("matlabbatch{1}.spm.stats.fmri_spec.sess(" + str(sessid) + ").cond(" + str(c) + ").orth = " + conditions[c - 1].orth + ";\n")

        return conditions_string

    # ---------------------------------------------------
    #region compose images string

    # group_instances is a list of subjects' instances
    # image_description: {"type": ct | dartel | vbm, "folder": root path for dartel}
    @staticmethod
    def compose_images_string_1GROUP_MULTREGR(group_instances, out_batch_job, grp_input_imgs):

        img_type    = grp_input_imgs.type
        img_folder  = grp_input_imgs.folder

        cells_images = "\r"

        img = ""
        for subj in group_instances:
            if img_type == "ct":
                img = subj.t1_cat_resampled_surface
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_1GROUP_MULTREGR")
            cells_images = cells_images + "\'" + img + "\'\r"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    @staticmethod
    def compose_images_string_1W(groups_instances, out_batch_job, grp_input_imgs):

        img_type    = grp_input_imgs.type
        img_folder  = grp_input_imgs.folder

        cells_images = ""
        gr = 0
        for subjs in groups_instances:
            gr              = gr + 1
            cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(" + str(gr) + ").scans = "

            img             = ""
            grp1_images     = "{\n"
            for subj in subjs:

                if img_type == "ct":
                    img = subj.t1_cat_resampled_surface
                elif img_type == "dartel":
                    img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_1W")

                grp1_images = grp1_images + "\'" + img + "\'\n"
            grp1_images = grp1_images + "\n};"

            cells_images = cells_images + grp1_images + "\n"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    @staticmethod
    def compose_images_string_2W(factors, out_batch_job, grp_input_imgs):

        img_type    = grp_input_imgs.type
        img_folder  = grp_input_imgs.folder

        factors_labels  = factors["labels"]
        cells           = factors["cells"]

        # nfactors = len(factors_labels)
        nlevels = [len(cells), len(cells[0])]  # nlevels for each factor

        # checks
        # if nfactors != len(cells):
        #     print("Error: num of factors labels (" + str(nfactors) + ") differs from cells content (" + str(len(cells)) + ")")
        #     return

        cells_images = ""
        ncell = 0
        for f1 in range(0, nlevels[0]):
            for f2 in range(0, nlevels[1]):
                ncell           = ncell + 1
                cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(ncell) + ").levels = [" + str(f1 + 1) + "\n" + str(f2 + 1) + "];\n"
                cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(ncell) + ").scans = {\n"

                subjs           = cells[f1][f2]
                img             = ""
                for subj in subjs:

                    if img_type == "ct":
                        img = eval("subj.t1_cat_resampled_surface")
                    elif img_type == "dartel":
                        img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                    img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_2W")

                    cells_images = cells_images + "'" + img + "'\n"
                cells_images = cells_images + "};"

        sed_inplace(out_batch_job, "<FACTOR1_NAME>",    factors_labels[0])
        sed_inplace(out_batch_job, "<FACTOR1_NLEV>",    str(nlevels[0]))
        sed_inplace(out_batch_job, "<FACTOR2_NAME>",    factors_labels[1])
        sed_inplace(out_batch_job, "<FACTOR2_NLEV>",    str(nlevels[1]))
        sed_inplace(out_batch_job, "<FACTORS_CELLS>",   cells_images)

    @staticmethod
    def compose_images_string_2sTT(groups_instances, out_batch_job, grp_input_imgs):

        img_type    = grp_input_imgs.type
        img_folder  = grp_input_imgs.folder

        subjs1      = groups_instances[0]
        subjs2      = groups_instances[1]

        grp1_images = "{\n"
        img         = ""
        for subj in subjs1:

            if img_type == "ct":
                img = subj.t1_cat_resampled_surface
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")
            elif img_type == "fmri":
                img = os.path.join(subj.fmri_dir, "stats", img_folder, grp_input_imgs.name + ".nii")

            img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_2sTT")

            grp1_images = grp1_images + "\'" + img + "\'\n"
        grp1_images = grp1_images + "\n}"

        grp2_images = "{\n"
        for subj in subjs2:

            if img_type == "ct":
                img = subj.t1_cat_resampled_surface
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")
            elif img_type == "fmri":
                img = os.path.join(subj.fmri_dir, "stats", img_folder, grp_input_imgs.name + ".nii")

            img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_2sTT")

            grp2_images = grp2_images + "\'" + img + "\'\n"
        grp2_images = grp2_images + "\n}"

        # set job file
        sed_inplace(out_batch_job, "<GROUP1_IMAGES>", grp1_images)
        sed_inplace(out_batch_job, "<GROUP2_IMAGES>", grp2_images)
    #endregion

    # ---------------------------------------------------------------------------
    #region explicit masking

    @staticmethod
    def spm_replace_explicit_mask(_global, out_batch_job, expl_mask=None, athresh=0.2, idstep=1):

        if expl_mask is None:
            masking =   "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.tm.tm_none = 1;\n" \
                        "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.im = 1;\n" \
                        "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.em = {''};"
        else:
            if expl_mask == "icv":
                mask = _global.spm_icv_mask + ",1"
            else:
                expl_mask = Image(expl_mask, must_exist=True, msg="SPMStatsUtils.spm_replace_explicit_mask")
                mask = expl_mask + ",1"

            masking = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.tm.tma.athresh = " + str(athresh) + ";\n" \
                      "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.im = 1;\n" \
                      "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.em = {'" + mask + "'};"

        sed_inplace(out_batch_job, "<FACTDES_MASKING>", masking)

    #endregion

    # ---------------------------------------------------------------------------
    #region global calculation

    # method can be: subj_icv, subj_tiv, "" (no correction) or a column name of the given data_file
    # when analysing subjects from different groups, we must avoid validating data.
    # Thus get_filtered_column must receive a Subject instances list, not a labels list  (16/1/2023)
    @staticmethod
    def spm_replace_global_calculation(project, out_batch_job, method="", groups_instances=None, data_file=None, idstep=1):

        no_corr_str     = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalc.g_omit = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.glonorm = 1;"
        user_corr_str1  = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalc.g_user.global_uval = [\n"
        user_corr_str2  = "];\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.glonorm = 2;"
        gc_str          = ""

        slabels         = []
        subjs_instances = []
        for subjs in groups_instances:
            slabels         = slabels + project.get_subjects_labels(subjs)
            subjs_instances = subjs_instances + subjs

        if method == "subj_icv":  # read icv file from each subject/mpr/spm folder

            if project.data.exist_filled_column("icv", slabels):
                str_icvs = list2spm_text_column(project.get_filtered_column("icv", subjs_instances)[0])
                # raise DataFileException("spm_replace_global_calculation", "given data_file does not contain the column icv")
            else:
                icvs = []
                for subjs in groups_instances:
                    icvs = icvs + project.get_subjects_icv(subjs)
                str_icvs = list2spm_text_column(icvs)
            gc_str = user_corr_str1 + str_icvs + user_corr_str2
        elif method == "subj_tiv":  # read tiv file from each subject/mpr/cat folder
            # if not project.data.exist_filled_column("tiv", slabels):
            #

            gc_str = no_corr_str
        elif method == "":  # don't correct
            gc_str = no_corr_str

        elif isinstance(method, str) and data_file is not None:  # must be a column in the given data_file list of

            if not os.path.exists(data_file):
                raise DataFileException("spm_replace_global_calculation", "given data_file does not exist")
            data = SubjectsDataDict(data_file)

            if not data.exist_filled_column(method, slabels):
                raise DataFileException("spm_replace_global_calculation", "given data_file does not contain a valid value of column " + method + " for all subjects")

            str_icvs = list2spm_text_column(data.get_filtered_column(method, slabels)[0])
            gc_str = user_corr_str1 + str_icvs + user_corr_str2  # list2spm_text_column ends with a "\n"

        sed_inplace(out_batch_job, "<FACTDES_GLOBAL>", gc_str)
    #endregion

    # ---------------------------------------------------------------------------
    #region CHECK REVIEW ESTIMATE

    @staticmethod
    def spm_get_cat_check(idstep=2):

        return  "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.spmmat(1) = cfg_dep(\'Factorial design specification: SPM.mat File\', substruct(\'.\', 'val', '{}', {1}, \'.\', \'val\', '{}', {1}, \'.\', \'val\', \'{}\', {1}), substruct(\'.\', \'spmmat\'));\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.use_unsmoothed_data = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.adjust_data = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.outdir = {\'\'};\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.fname = \'CATcheckdesign_\';\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.save = 0;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_ortho = 1;\n"

    @staticmethod
    def spm_get_review_model(idstep=2):

        return  "matlabbatch{" + str(idstep) + "}.spm.stats.review.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));\n" \
                "matlabbatch{" + str(idstep) + "}.spm.stats.review.display.matrix = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.stats.review.print = 'ps';\n"

    @staticmethod
    def get_spm_model_estimate(isSurf=False, idstep=3):

        if isSurf:
            return "matlabbatch{" + str(idstep) + "}.spm.tools.cat.stools.SPM.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));"
        else:
            return "matlabbatch{" + str(idstep) + "}.spm.stats.fmri_est.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('.', 'spmmat'));\n \
                    matlabbatch{" + str(idstep) + "}.spm.stats.fmri_est.write_residuals = 0;\n \
                    matlabbatch{" + str(idstep) + "}.spm.stats.fmri_est.method.Classical = 1;\n"

    #endregion

    # ---------------------------------------------------------------------------
    #region OTHER

    # create a gifti image with ones in correspondence of each vmask voxel
    @staticmethod
    def batchrun_spm_surface_mask_from_volume_mask(vmask, ref_surf, out_surf, matlab_paths): #, distance=8):

        Image(vmask, must_exist=True, msg="SPMStatsUtils.batchrun_spm_surface_mask_from_volume_mask vmask")
        Image(ref_surf, must_exist=True, msg="SPMStatsUtils.batchrun_spm_surface_mask_from_volume_mask ref_surf")
        call_matlab_function_noret('create_surface_mask_from_volume_mask', matlab_paths, "'" + vmask + "','" + ref_surf + "','" + out_surf + "'")

    @staticmethod
    def batchrun_cat_surface_smooth(project, _global, subj_instances, sfilt=12, spm_template_name="subjs_cat_surf_smooth", nproc=1, eng=None, runit=True):

        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(spm_template_name, "mpr")

        str_images="\n"
        for subj in subj_instances:
            lhimage = "'" + subj.t1_cat_lh_surface + "'"
            str_images = str_images + lhimage + "\n"

        sed_inplace(out_batch_job, "<LH_IMAGES>", str_images)
        sed_inplace(out_batch_job, "<SPFILT>", str(sfilt))
        sed_inplace(out_batch_job, "<N_PROC>", str(nproc))

        if runit:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])
            else:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir], eng=eng, endengine=False)
    #endregion
