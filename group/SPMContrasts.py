from typing import List

from group.PostModel import PostModel
from group.spm_utilities import Contrast, TContrast, Regressor
from myutility.list import is_list_of
from myutility.fileutilities import sed_inplace


class SPMContrasts:
    """
    This class contains functions for writing SPM contrasts.

    """
    # -------------------------------------------------------------------------------------------
    # first level fmri contrasts
    # -------------------------------------------------------------------------------------------

    # contrasts is a list of dictionaries with the following field:  name, weights, sessrep
    @staticmethod
    def replace_1stlevel_contrasts(out_batch_job:str, spmmath:str, contrasts:List[Regressor], deleteexisting:bool=True, batch_id:int=4):
        """
        This function creates the 1st level contrasts in the batch job file.

        Parameters
        ----------
        out_batch_job : str
            The path to the batch job file.
        spmmath : str
            The path to the SPM mat file.
        contrasts : list
            A list of contrasts.
        deleteexisting : bool, optional
            A flag indicating whether to delete existing contrasts. The default is True.
        batch_id : int, optional
            The ID of the Matlab batch. The default is 4.

        Returns
        -------
        constrasts_str : str
            The Matlab code for setting the 1st level contrasts.

        """
        if not is_list_of(contrasts, Contrast):
            raise Exception("Error in spm_get_1stlevel_contrasts, given contrasts list is not of type Contrast")

        constrasts_str = "matlabbatch{" + str(batch_id) + "}.spm.stats.con.spmmat = {'" + spmmath + "'};\n"

        for num, con in enumerate(contrasts):
            if isinstance(con, TContrast):
                con_type = "tcon"
            else:
                con_type = "fcon"

            constrasts_str += ("matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{" + str(num + 1) + "}." + con_type + ".name = '" + con.name + "';\n")
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{" + str(num + 1) + "}." + con_type + ".weights = " + con.weights + ";\n")
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}.spm.stats.con.consess{" + str(num + 1) + "}." + con_type + ".sessrep = '" + con.sessrep + "';\n")

        if deleteexisting:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}.spm.stats.con.delete = 1;\n")
        else:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}.spm.stats.con.delete = 0;\n")

        sed_inplace(out_batch_job, "<CONTRASTS>", constrasts_str)

        return constrasts_str

    # -------------------------------------------------------------------------------------------
    # region second level fmri contrasts
    # -------------------------------------------------------------------------------------------
    @staticmethod
    def replace_contrasts(out_batch_job:str, spmmath:str, post_model:PostModel, deleteexisting:bool=True, batch_id:int=1):
        """
        This function creates the standard (as-is) contrasts in the batch job file.

        Parameters
        ----------
        out_batch_job : str
            The path to the batch job file.
        spmmath : str
            The path to the SPM mat file.
        post_model : PostModel
            The post-model object.
        deleteexisting : bool, optional
            A flag indicating whether to delete existing contrasts. The default is True.
        batch_id : int, optional
            The ID of the Matlab batch. The default is 1.

        Returns
        -------
        constrasts_str : str
            The Matlab code for setting the contrasts.

        """
        if post_model.isSpm:
            con_str = "spm.stats.con"
        else:
            con_str = "spm.tools.cat.stools.con"

        if not is_list_of(post_model.contrasts, Contrast):
            raise Exception("Error in replace_contrasts, given contrasts list is not of type Contrast")

        constrasts_str = "matlabbatch{" + str(batch_id) + "}." + con_str + ".spmmat = {'" + spmmath + "'};\n"

        for num, con in enumerate(post_model.contrasts):

            if isinstance(con, TContrast):
                con_type = "tcon"
            else:
                con_type = "fcon"

            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(num + 1) + "}." + con_type + ".name = '" + con.name + "';\n")
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(num + 1) + "}." + con_type + ".weights = " + con.weights + ";\n")
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(num + 1) + "}." + con_type + ".sessrep = '" + con.sessrep + "';\n")

        if deleteexisting:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".delete = 1;\n")
        else:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".delete = 0;\n")

        sed_inplace(out_batch_job, "<CONTRASTS>", constrasts_str)

        return constrasts_str

    @staticmethod
    def replace_1group_multregr_contrasts(out_batch_job:str, spmmath:str, post_model:PostModel, deleteexisting:bool=True, batch_id:int=1):
        """
        This function creates the multiple regression contrasts in the batch job file.
        post_model does not contain a Contrast list, names and weights are derived from regressors

        Parameters
        ----------
        out_batch_job : str
            The path to the batch job file.
        spmmath : str
            The path to the SPM mat file.
        post_model : PostModel
            The post-model object.
        deleteexisting : bool, optional
            A flag indicating whether to delete existing contrasts. The default is True.
        batch_id : int, optional
            The ID of the Matlab batch. The default is 1.

        Returns
        -------
        constrasts_str : str
            The Matlab code for setting the contrasts.
        """
        if post_model.isSpm:
            con_str = "spm.stats.con"
        else:
            con_str = "spm.tools.cat.stools.con"

        constrasts_str = "matlabbatch{" + str(batch_id) + "}." + con_str + ".spmmat = {'" + spmmath + "'};\n"

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

                constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(2 * (cov_id + 1) - 1) + "}.tcon.name = \'" + cov_name + " pos\';\n"
                constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(2 * (cov_id + 1) - 1) + "}.tcon.weights = [" + weight_str_pos + "];\n"
                constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(2 * (cov_id + 1) - 1) + "}.tcon.sessrep = 'none';\n"

                constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(2 * (cov_id + 1)) + "}.tcon.name = \'" + cov_name + " neg\';\n"
                constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(2 * (cov_id + 1)) + "}.tcon.weights = [" + weight_str_neg + "];\n"
                constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{" + str(2 * (cov_id + 1)) + "}.tcon.sessrep = 'none';\n"

                cov_id += 1

        if deleteexisting:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".delete = 1;\n")
        else:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".delete = 0;\n")

        if constrasts_str == "":
            raise Exception("ERROR in replace_1group_multregr_contrasts, no covariates were specified")

        sed_inplace(out_batch_job, "<CONTRASTS>", constrasts_str)
        
        return constrasts_str

    @staticmethod
    def replace_1WAnova_contrasts(out_batch_job:str, spmmath:str, post_model:PostModel, deleteexisting:bool=True, batch_id:int=1):
        """
        This function creates the 1-way ANOVA contrasts in the batch job file.
        post_model.contrast_names contains levels' names, manages only 3 or 4 levels
        Parameters
        ----------
        out_batch_job : str
            The path to the batch job file.
        spmmath : str
            The path to the SPM mat file.
        post_model : PostModel
            The post-model object.
        deleteexisting : bool, optional
            A flag indicating whether to delete existing contrasts. The default is True.
        batch_id : int, optional
            The ID of the Matlab batch. The default is 1.

        Returns
        -------
        constrasts_str : str
            The Matlab code for setting the contrasts.
        """
        if not is_list_of(post_model.contrasts, Contrast):
            raise Exception("Error in replace_1WAnova_contrasts, given contrasts list is not of type Contrast")

        if post_model.isSpm:
            con_str = "spm.stats.con"
        else:
            con_str = "spm.tools.cat.stools.con"

        constrasts_str = "matlabbatch{" + str(batch_id) + "}." + con_str + ".spmmat = {'" + spmmath + "'};\n"

        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + "{1}.fcon.name = 'ANOVA';"

        # create F-contrast
        nlevels = len(post_model.contrasts)
        if nlevels == 3:
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{1}.fcon.weights = [1 -1 0"
            constrasts_str += "                                                                              0 1 -1]"
        elif nlevels == 4:
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{1}.fcon.weights = [1 -1 0 0"
            constrasts_str += "                                                                            0 1 -1 0]"
            constrasts_str += "                                                                            0 0 1 -1]"
        else:
            print("ERROR in replace_1WAnova_contrasts, only 3 or 4 levels are managed, given levels are = " + str(nlevels) + " ...exiting")
            return

        constrasts_str     += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{1}.fcon.sessrep = 'none';"

        # create pair-wise T-contrasts
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{2}.tcon.name = \'" + post_model.contrasts[0].name + " > " + post_model.contrasts[1].name + "\';\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{2}.tcon.weights = [1 -1 0];\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{2}.tcon.sessrep = 'none';\n"

        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{3}.tcon.name = \'" + post_model.contrasts[1].name + " > " + post_model.contrasts[0].name + "\';\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{3}.tcon.weights = [-1 1 0];\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{3}.tcon.sessrep = 'none';\n"

        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{4}.tcon.name = \'" + post_model.contrasts[0].name + " > " + post_model.contrasts[2].name + "\';\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{4}.tcon.weights = [1 0 -1];\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{4}.tcon.sessrep = 'none';\n"

        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{5}.tcon.name = \'" + post_model.contrasts[2].name + " > " + post_model.contrasts[0].name + "\';\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{5}.tcon.weights = [-1 0 1];\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{5}.tcon.sessrep = 'none';\n"

        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{6}.tcon.name = \'" + post_model.contrasts[1].name + " > " + post_model.contrasts[2].name + "\';\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{6}.tcon.weights = [0 1 -1];\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{6}.tcon.sessrep = 'none';\n"

        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{7}.tcon.name = \'" + post_model.contrasts[2].name + " > " + post_model.contrasts[1].name + "\';\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{7}.tcon.weights = [0 -1 1];\n"
        constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{7}.tcon.sessrep = 'none';\n"

        if nlevels == 4:

            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{8}.tcon.name = \'" + post_model.contrasts[0].name + " > " + post_model.contrasts[3].name + "\';\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{8}.tcon.weights = [1 0 0 -1];\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{8}.tcon.sessrep = 'none';\n"

            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess.consess{9}.tcon.name = \'" + post_model.contrasts[3].name + " > " + post_model.contrasts[0].name + "\';\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{9}.tcon.weights = [-1 0 0 1];\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{9}.tcon.sessrep = 'none';\n"

            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{10}.tcon.name = \'" + post_model.contrasts[1].name + " > " + post_model.contrasts[3].name + "\';\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{10}.tcon.weights = [0 1 0 -1];\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{10}.tcon.sessrep = 'none';\n"

            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{11}.tcon.name = \'" + post_model.contrasts[3].name + " > " + post_model.contrasts[1].name + "\';\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{11}.tcon.weights = [0 -1 0 1];\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{11}.tcon.sessrep = 'none';\n"

            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{12}.tcon.name = \'" + post_model.contrasts[2].name + " > " + post_model.contrasts[3].name + "\';\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{12}.tcon.weights = [0 0 1 -1];\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{12}.tcon.sessrep = 'none';\n"

            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{13}.tcon.name = \'" + post_model.contrasts[3].name + " > " + post_model.contrasts[2].name + "\';\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{13}.tcon.weights = [0 0 -1 1];\n"
            constrasts_str += "matlabbatch{" + str(batch_id) + "}." + con_str + ".consess{13}.tcon.sessrep = 'none';\n"

        if deleteexisting:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".delete = 1;\n")
        else:
            constrasts_str += ("matlabbatch{" + str(batch_id) + "}." + con_str + ".delete = 0;\n")

        sed_inplace(out_batch_job, "<CONTRASTS>", constrasts_str)

        return constrasts_str

    # endregion