from data.utilities import list2spm_text_column
from utility.utilities import sed_inplace

# class used to replace covariates strings in SPM batch
class SPMCovariates:

    # SIMPLE covariation. does not manage group x covariate. For each covariate, it concatenates the values from many groups (if present) into a single vector.
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_replace_stats_add_simplecovariates(project, out_batch_job, groups_instances, cov_names=None, batch_id=1, cov_interaction=None, datafile=None):

        if cov_names is None:
            sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")
            return
        else:
            if isinstance(cov_names, list) is False:
                raise Exception("ERROR in spm_replace_stats_add_simplecovariates, cov_names (" + str(cov_names) + ") is not a list....returning")

        ncov = len(cov_names)
        if cov_interaction is None:
            cov_interaction = [1 for i in range(ncov)]

        cint = len(cov_interaction)
        if ncov != cint:
            print("ERROR: spm_replace_stats_add_simplecovariates. number of covariates and their interaction differs")
            return

        if ncov == 1:
            SPMCovariates.spm_replace_stats_add_1cov_manygroups(out_batch_job, groups_instances, project, cov_names[0], batch_id, cov_interaction, datafile)
        else:
            cov_string  = ""
            for cov_id in range(ncov):
                cov = []
                cov_name    = cov_names[cov_id]
                for subjs in groups_instances:
                    cov = cov + project.get_filtered_column(cov_name, subjs, datafile)[0]
                str_cov = "\n" + list2spm_text_column(cov)  # ends with a "\n"

                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").c = "
                cov_string = cov_string + "[" + str_cov + "];\n"
                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").cname = '" + cov_name + "';\n"
                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").iCFI = " + str(cov_interaction[cov_id]) + ";\n"
                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").iCC = 1;\n"

            sed_inplace(out_batch_job,"<COV_STRING>", cov_string)

    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_replace_stats_add_1cov_manygroups(out_batch_job, groups_labels, project, cov_name, batch_id=1, cov_interaction=None, datafile=None):

        cov = []
        for grp in groups_labels:
            cov = cov + project.get_filtered_column(cov_name, grp, datafile)[0]
        str_cov = "\n" + list2spm_text_column(cov)  # ends with a "\n"

        cov_string =              "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.c = "
        cov_string = cov_string + "[" + str_cov + "];\n"
        cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.cname = '" + cov_name + "';\n"
        cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.iCFI = " + str(cov_interaction[0]) + ";\n"
        cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.iCC = 1;"
        sed_inplace(out_batch_job, "<COV_STRING>", cov_string)
