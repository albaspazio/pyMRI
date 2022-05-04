import ntpath
import os
import traceback

from group.SPMResults import SPMResults
from group.SPMStatsUtils import StatsParams
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace


class SPMContrasts:

    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def batchrun_spm_stats_2samplesttest_contrasts_results(project, _global, spmmat, c1_name="A>B", c2_name="B>A",
                                                           spm_template_name="spm_stats_2samplesttest_contrasts_results",
                                                           stats_params=None, runit=True):
        try:
            if stats_params is None:
                stats_params = StatsParams()

            # create template files
            out_batch_job, out_batch_start = project.adapt_batch_files(spm_template_name, "mpr")

            sed_inplace(out_batch_job, "<SPM_MAT>"          , spmmat)
            sed_inplace(out_batch_job, "<STATS_DIR>"        , ntpath.dirname(spmmat))
            sed_inplace(out_batch_job, "<C1_NAME>"          , c1_name)
            sed_inplace(out_batch_job, "<C2_NAME>"          , c2_name)
            sed_inplace(out_batch_job, "<MULT_CORR>"        , stats_params.mult_corr)
            sed_inplace(out_batch_job, "<PVALUE>"           , str(stats_params.pvalue))
            sed_inplace(out_batch_job, "<CLUSTER_EXTEND>"   , str(stats_params.cluster_extend))

            SPMResults.runbatch_cat_results_trasformation_string(out_batch_job, 3, stats_params.mult_corr, stats_params.pvalue, stats_params.cluster_extend)

            if runit is True:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])

        except Exception as e:
            traceback.print_exc()
            print(e)

    # calculate contrasts and report their results on a given, already estimated, SPM.mat
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def batchrun_cat_stats_1group_multregr_contrasts_results(project, _global, spmmat, cov_names,
                                                             spm_template_name="cat_stats_contrasts_results",
                                                             stats_params=None, runit=True):
        try:
            if stats_params is None:
                stats_params = StatsParams()

            # create template files
            out_batch_job, out_batch_start = project.adapt_batch_files(spm_template_name, "mpr")

            sed_inplace(out_batch_job, "<SPM_MAT>"  , spmmat)
            sed_inplace(out_batch_job, "<STATS_DIR>", ntpath.dirname(spmmat))

            SPMContrasts.replace_1group_multregr_contrasts(out_batch_job, cov_names, tool="cat")

            sed_inplace(out_batch_job, "<MULT_CORR>"        , stats_params.mult_corr)
            sed_inplace(out_batch_job, "<PVALUE>"           , str(stats_params.pvalue))
            sed_inplace(out_batch_job, "<CLUSTER_EXTEND>"   , str(stats_params.cluster_extend))

            call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])

        except Exception as e:
            traceback.print_exc()
            print(e)

    # run a prebuilt batch file in a non-standard location, which only need to set the stat folder and SPM.mat path
    @staticmethod
    def batchrun_spm_stats_predefined_contrasts_results(project, _global, statsdir, spm_template_full_path_noext, eng=None, runit=True):
        try:
            # create template files
            out_batch_job, out_batch_start = project.adapt_batch_files(spm_template_full_path_noext, "mpr")

            spm_mat_path = os.path.join(statsdir, "SPM.mat")

            sed_inplace(out_batch_job, "<SPM_MAT>", spm_mat_path)
            sed_inplace(out_batch_job, "<STATS_DIR>", statsdir)

            if runit is True:
                if eng is None:
                    call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])  # open a new session and then end it
                else:
                    call_matlab_spmbatch(out_batch_start, endengine=False)  # I assume that the caller will end the matlab session and def dir have been already specified

        except Exception as e:
            traceback.print_exc()
            print(e)

    # create multregr contrasts for spm and cat
    @staticmethod
    def replace_1group_multregr_contrasts(out_batch_job, cov_names, tool="spm", batch_id=1):

        if tool == "spm":
            con_str = "spm.stats.stools.con.consess"
        else:
            con_str = "spm.tools.cat.stools.con.consess"

        contr_str = ""

        ncov = len(cov_names)
        for cov_id in range(ncov):
            cov_name = cov_names[cov_id]

            # define weight
            weight_str_pos = "0"
            weight_str_neg = "0"
            for wp in range(cov_id):
                weight_str_pos = weight_str_pos + " 0"
                weight_str_neg = weight_str_neg + " 0"
            weight_str_pos = weight_str_pos + " 1"
            weight_str_neg = weight_str_neg + " -1"

            contr_str = contr_str + "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1) - 1) + "}.tcon.name = \'" + cov_name + " pos\';\n"
            contr_str = contr_str + "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1) - 1) + "}.tcon.weights = [" + weight_str_pos + "];\n"
            contr_str = contr_str + "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1) - 1) + "}.tcon.sessrep = 'none';\n"

            contr_str = contr_str + "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1)) + "}.tcon.name = \'" + cov_name + " neg\';\n"
            contr_str = contr_str + "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1)) + "}.tcon.weights = [" + weight_str_neg + "];\n"
            contr_str = contr_str + "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1)) + "}.tcon.sessrep = 'none';\n"

        sed_inplace(out_batch_job, "<CONTRASTS>", contr_str)
