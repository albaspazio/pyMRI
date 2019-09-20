from utility.utilities import sed_inplace
from utility import import_data_file


class Stats:

    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, project, cov_name, cov_interaction=1, datafile=None):

        cov = []
        for grp in groups_labels:
            cov = cov + project.get_filtered_column(cov_name, grp, datafile)
        str_cov = "\n" + import_data_file.list2spm_text_column(cov) # ends with a "\n"

        cov_string = "matlabbatch{1}.spm.stats.factorial_design.cov.c = "
        cov_string = cov_string + "[" + str_cov + "];\n"
        cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.cname = '" + cov_name + "';\n"
        cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.iCFI = " + str(cov_interaction) + ";\n"
        cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.iCC = 1;"
        sed_inplace(out_batch_job,"<COV_STRING>", cov_string)


    @staticmethod
    def spm_stats_add_conditions(out_batch_job, conditions):

        conditions_string = ""
        for c in range(1, len(conditions)+1):
            onsets = import_data_file.list2spm_text_column(conditions[c-1]["onsets"])  # ends with a "\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond("+ str(c) + ").name = \'" + conditions[c-1]["name"] + "\';" + "\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond("+ str(c) + ").onset = [" + onsets + "];\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond("+ str(c) + ").tmod = 0;\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond("+ str(c) + ").duration = " + str(conditions[c-1]["duration"]) + ";\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond("+ str(c) + ").pmod = struct('name', {}, 'param', {}, 'poly', {});\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond("+ str(c) + ").orth = 1;\n"

        sed_inplace(out_batch_job,"<CONDITION_STRING>", conditions_string)

