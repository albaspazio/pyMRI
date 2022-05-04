from data.utilities import list2spm_text_column
from utility.utilities import sed_inplace

# class used to replace covariates strings in SPM batch
class SPMCovariates:

    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_replace_stats_add_covariates(project, out_batch_job, groups_labels, cov_names=None, batch_id=1, cov_interaction=None, datafile=None):

        if cov_names is None:
            sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")
            return
        else:
            if isinstance(cov_names, list) is False:
                raise Exception("ERROR in spm_replace_stats_add_covariates, cov_names (" + str(cov_names) + ") is not a list....returning")

        ncov = len(cov_names)
        if cov_interaction is None:
            cov_interaction = [1 for i in range(ncov)]

        cint = len(cov_interaction)
        if ncov != cint:
            print("ERROR: spm_replace_stats_add_covariates. number of covariates and their interaction differs")
            return

        if len(groups_labels) > 1 and ncov == 1:
            SPMCovariates.spm_replace_stats_add_1cov_manygroups(out_batch_job, groups_labels, project, cov_names[0], batch_id, cov_interaction, datafile)

        elif len(groups_labels) == 1 and ncov > 1:
            SPMCovariates.spm_replace_stats_add_manycov_1group(out_batch_job, groups_labels[0], project, cov_names, batch_id, cov_interaction, datafile)

        else:
            cov_string  = ""
            cov         = []
            for cov_id in range(ncov):
                cov_name    = cov_names[cov_id]
                for grp_name in groups_labels:
                    cov = cov + project.get_filtered_column(cov_name, grp_name, datafile)[0]
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

    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_replace_stats_add_manycov_1group(out_batch_job, group_label, project, cov_names, batch_id=1, cov_interaction=None, datafile=None):

        cov_string = ""
        ncov = len(cov_names)

        for cov_id in range(ncov):
            cov_name    = cov_names[cov_id]
            cov         = project.get_filtered_column(cov_names[cov_id], group_label, data=datafile)[0]
            str_cov     = "\n" + list2spm_text_column(cov)  # ends with a "\n"

            cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").c = "
            cov_string = cov_string + "[" + str_cov + "];\n"
            cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").cname = '" + cov_name + "';\n"
            cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").iCFI = " + str(cov_interaction[cov_id]) + ";\n"
            cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").iCC = 1;\n"

        sed_inplace(out_batch_job, "<COV_STRING>", cov_string)
