import csv

from data.utilities import list2spm_text_column, get_icv_spm_file
from utility.images.images import imtest
from utility.matlab import call_matlab_function_noret
from utility.utilities import sed_inplace


class SPMStatsUtils:

    # create spm fmri 1st level contrasts onsets
    # conditions is a dictionary list with field: [name, onsets, duration]
    @staticmethod
    def spm_fmri_subj_stats_replace_conditions_string(out_batch_job, conditions):

        conditions_string = ""
        for c in range(1, len(conditions) + 1):
            onsets = list2spm_text_column(conditions[c - 1]["onsets"])  # ends with a "\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").name = \'" + conditions[c - 1]["name"] + "\';" + "\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").onset = [" + onsets + "];\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").tmod = 0;\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").duration = " + str(conditions[c - 1]["duration"]) + ";\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").pmod = struct('name', {}, 'param', {}, 'poly', {});\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").orth = 1;\n"

        sed_inplace(out_batch_job, "<CONDITION_STRING>", conditions_string)

    # ---------------------------------------------------------------------------
    # explicit masking
    # ---------------------------------------------------------------------------
    @staticmethod
    def explicit_mask(_global, out_batch_job, expl_mask=None, athresh=0.2, idstep=1 ):

        if expl_mask is None:
            masking =   "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.tm.tm_none = 1;\n" \
                        "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.im = 1;\n" \
                        "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.em = {''};"
        else:
            if expl_mask == "icv":
                mask = _global.spm_icv_mask + ",1"
            else:
                if imtest(expl_mask) is False:
                    raise Exception("ERROR in explicit_mask, given explicit mask does not exist")
                mask = expl_mask + ",1"

            masking = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.tm.tma.athresh = " + str(athresh) + ";\n" \
                      "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.im = 1;\n" \
                      "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.em = {'" + mask + "'};"

        sed_inplace(out_batch_job, "<FACTDES_MASKING>", masking)

    # ---------------------------------------------------------------------------
    # global calculation
    # ---------------------------------------------------------------------------
    @staticmethod
    def global_calculation(project, out_batch_job, method="", groups_labels=None, data_file=None, idstep=1):

        no_corr_str     = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalc.g_omit = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.glonorm = 1;"
        user_corr_str1  = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalc.g_user.global_uval = [\n"
        user_corr_str2  = "];\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.glonorm = 2;"
        gc_str = ""

        if method == "subj_icv":  # read icv file from each subject/mpr/spm folder
            icv = ""
            for grp in groups_labels:
                for subj in project.get_subjects(grp):
                    icv = icv + str(get_icv_spm_file(subj.t1_spm_icv_file)) + "\n"
            gc_str = user_corr_str1 + icv + user_corr_str2
        elif method == "subj_tiv":  # read tiv file from each subject/mpr/cat folder
            gc_str = no_corr_str
        elif method == "":  # don't correct
            gc_str = no_corr_str
        elif isinstance(method, str) is True and data_file is not None:  # must be a column in the given data_file list of
            icvs = []
            for grp in groups_labels:
                icvs = icvs + project.get_filtered_column(method, project.get_subjects_labels(grp))
            gc_str = user_corr_str1 + list2spm_text_column(icvs) + user_corr_str2  # list2spm_text_column ends with a "\n"

        sed_inplace(out_batch_job, "<FACTDES_GLOBAL>", gc_str)

    #======================================================================================================================================================
    #region CHECK REVIEW
    @staticmethod
    def spm_get_cat_check(out_batch_job, idstep=2):

        return  "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.spmmat(1) = cfg_dep(\'Factorial design specification: SPM.mat File\', substruct(\'.\', 'val', '{}', {1}, \'.\', \'val\', '{}', {1}, \'.\', \'val\', \'{}\', {1}), substruct(\'.\', \'spmmat\'));\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.use_unsmoothed_data = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.adjust_data = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.outdir = {\'\'};\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.fname = \'CATcheckdesign_\';\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.save = 0;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_ortho = 1;\n"

    @staticmethod
    def spm_get_review_model(out_batch_job, string, idstep=2):

        return  "matlabbatch{2}.spm.stats.review.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));\n" \
                "matlabbatch{2}.spm.stats.review.display.matrix = 1;\n" \
                "matlabbatch{2}.spm.stats.review.print = 'ps';\n"

    #endregion

    #======================================================================================================================================================
    # create a gifti image with ones in correspondence of each vmask voxel
    @staticmethod
    def spm_create_surface_mask_from_volume_mask(vmask, ref_surf, out_surf, matlab_paths, distance=8):

        if imtest(vmask) is False:
            print("Error in create_surface_mask_from_volume_mask: input vmask does not exist")
            return

        if imtest(ref_surf) is False:
            print("Error in create_surface_mask_from_volume_mask: input ref_surf does not exist")
            return

        call_matlab_function_noret('create_surface_mask_from_volume_mask', matlab_paths,"'" + vmask + "','" + ref_surf + "','" + out_surf + "'")

