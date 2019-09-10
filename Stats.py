from utility.utilities import sed_inplace
from utility import import_data_file


class Stats:

    @staticmethod
    def spm_stats_add_1cov_manygroups(datafile, out_batch_job, groups_labels, cov_name, project):

        # get cov values
        data = import_data_file.read_tabbed_file_with_header(datafile)

        cov = []
        for grp in groups_labels:
            cov = cov + import_data_file.get_filtered_dict_column(data, "age", "subj", project.get_list_by_label(grp))
        str_cov = "\n" + import_data_file.list2spm_text_column(cov) # ends with a "\n"

        cov_string = "matlabbatch{1}.spm.stats.factorial_design.cov.c = "
        cov_string = cov_string + "[" + str_cov + "];\n"
        cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.cname = '" + cov_name + "';\n"
        cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.iCFI = 1;\nmatlabbatch{1}.spm.stats.factorial_design.cov.iCC = 1;"

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

