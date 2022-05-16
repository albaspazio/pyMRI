from utility.utilities import sed_inplace


class SPMContrasts:

    # create multregr contrasts for spm and cat
    @staticmethod
    def replace_1group_multregr_contrasts(out_batch_job, post_model, batch_id=1):

        if post_model.isSpm is True:
            con_str = "spm.stats.stools.con.consess"
        else:
            con_str = "spm.tools.cat.stools.con.consess"

        contr_str = ""

        nregr   = len(post_model.regressors)
        cov_id  = 0
        for regr_id in range(nregr):
            regressor = post_model.regressors[regr_id]

            if regressor.isNuisance is False:
                cov_name = regressor.name

                # weights follows regr_id (regressors column positions), contrast id follow cov_id (number of covariates)
                weight_str_pos = "0"
                weight_str_neg = "0"
                for wp in range(regr_id):
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

                cov_id += 1

        if contr_str == "":
            raise Exception("ERROR in replace_1group_multregr_contrasts, no covariates were specified")

        sed_inplace(out_batch_job, "<CONTRASTS>", contr_str)
