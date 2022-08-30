from utility.utilities import sed_inplace


class SPMContrasts:


    # first level fmri contrasts
    # contrasts is a list of dictionaries with the following field:  name, weights, sessrep
    @staticmethod
    def spm_get_1stlevel_contrasts(spmmath, contrasts, deleteexisting=True, idstep=4):

        constrasts_str = "matlabbatch{" + str(idstep) + "}.spm.stats.con.spmmat = {'" + spmmath + "'};\n"

        for num, con in enumerate(contrasts):
            constrasts_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.con.consess{" + str(num+1) + "}.tcon.name = '" + con.name + "';\n")
            constrasts_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.con.consess{" + str(num+1) + "}.tcon.weights = " + con.weights + ";\n")
            constrasts_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.con.consess{" + str(num+1) + "}.tcon.sessrep = '" + con.sessrep + "';\n")

        if deleteexisting:
            constrasts_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.con.delete = 1;\n")
        else:
            constrasts_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.con.delete = 0;\n")

        return constrasts_str



    # create multregr contrasts for spm and cat
    @staticmethod
    def replace_1group_multregr_contrasts(out_batch_job, post_model, batch_id=1):

        if post_model.isSpm:
            con_str = "spm.stats.con.consess"
        else:
            con_str = "spm.tools.cat.stools.con.consess"

        contr_str = ""

        nregr   = len(post_model.regressors)
        cov_id  = 0
        for regr_id in range(nregr):
            regressor = post_model.regressors[regr_id]

            if not regressor.isNuisance:
                cov_name = regressor.name

                # weights follows regr_id (regressors column positions), contrast id follow cov_id (number of covariates)
                weight_str_pos = "0"
                weight_str_neg = "0"
                for wp in range(regr_id):
                    weight_str_pos = weight_str_pos + " 0"
                    weight_str_neg = weight_str_neg + " 0"
                weight_str_pos = weight_str_pos + " 1"
                weight_str_neg = weight_str_neg + " -1"

                contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1) - 1) + "}.tcon.name = \'" + cov_name + " pos\';\n"
                contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1) - 1) + "}.tcon.weights = [" + weight_str_pos + "];\n"
                contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1) - 1) + "}.tcon.sessrep = 'none';\n"

                contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1)) + "}.tcon.name = \'" + cov_name + " neg\';\n"
                contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1)) + "}.tcon.weights = [" + weight_str_neg + "];\n"
                contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{" + str(2 * (cov_id + 1)) + "}.tcon.sessrep = 'none';\n"

                cov_id += 1

        if contr_str == "":
            raise Exception("ERROR in replace_1group_multregr_contrasts, no covariates were specified")

        sed_inplace(out_batch_job, "<CONTRASTS>", contr_str)


    # create 1W anova contrasts for spm and cat
    # post_model.contrast_names contains levels' names
    # manage up to 4 levels
    @staticmethod
    def replace_1WAnova_contrasts(out_batch_job, post_model, batch_id=1):

        if post_model.isSpm:
            con_str = "spm.stats.con.consess"
        else:
            con_str = "spm.tools.cat.stools.con.consess"

        contr_str = ""

        contr_str += "matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{1}.fcon.name = 'ANOVA';"

        # create F-contrast
        nlevels = len(post_model.contrast_names)
        if nlevels > 4:
            print("ERROR in replace_1WAnova_contrasts, no more than 4 levels are managed...exiting")
            return

        elif nlevels == 3:
            contr_str += "matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{1}.fcon.weights = [1 -1 0"
            contr_str += "                                                                            0 1 -1]"
        elif nlevels == 4:
            contr_str += "matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{1}.fcon.weights = [1 -1 0 0"
            contr_str += "                                                                            0 1 -1 0]"
            contr_str += "                                                                            0 0 1 -1]"

        contr_str += "matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{1}.fcon.sessrep = 'none';"

        # create pair-wise T-contrasts
        if nlevels == 3:
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{2}.tcon.name = \'" + post_model.contrast_names[0] + " > " + post_model.contrast_names[1] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{2}.tcon.weights = [1 -1 0];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{2}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{3}.tcon.name = \'" + post_model.contrast_names[1] + " > " + post_model.contrast_names[0] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{3}.tcon.weights = [-1 1 0];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{3}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{4}.tcon.name = \'" + post_model.contrast_names[0] + " > " + post_model.contrast_names[2] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{4}.tcon.weights = [1 0 -1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{4}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{5}.tcon.name = \'" + post_model.contrast_names[2] + " > " + post_model.contrast_names[0] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{5}.tcon.weights = [-1 0 1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{5}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{6}.tcon.name = \'" + post_model.contrast_names[1] + " > " + post_model.contrast_names[2] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{6}.tcon.weights = [0 1 -1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{6}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{7}.tcon.name = \'" + post_model.contrast_names[2] + " > " + post_model.contrast_names[1] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{7}.tcon.weights = [0 -1 1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{7}.tcon.sessrep = 'none';\n"

        else:

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{8}.tcon.name = \'" + post_model.contrast_names[0] + " > " + post_model.contrast_names[3] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{8}.tcon.weights = [1 0 0 -1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{8}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{9}.tcon.name = \'" + post_model.contrast_names[3] + " > " + post_model.contrast_names[0] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{9}.tcon.weights = [-1 0 0 1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{9}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{10}.tcon.name = \'" + post_model.contrast_names[1] + " > " + post_model.contrast_names[3] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{10}.tcon.weights = [0 1 0 -1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{10}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{11}.tcon.name = \'" + post_model.contrast_names[3] + " > " + post_model.contrast_names[1] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{11}.tcon.weights = [0 -1 0 1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{11}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{12}.tcon.name = \'" + post_model.contrast_names[2] + " > " + post_model.contrast_names[3] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{12}.tcon.weights = [0 0 1 -1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{12}.tcon.sessrep = 'none';\n"

            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{13}.tcon.name = \'" + post_model.contrast_names[3] + " > " + post_model.contrast_names[2] + "\';\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{13}.tcon.weights = [0 0 -1 1];\n"
            contr_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{13}.tcon.sessrep = 'none';\n"


        sed_inplace(out_batch_job, "<CONTRASTS>", contr_str)
