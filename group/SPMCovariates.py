from __future__ import annotations

from typing import Union, List, Optional, Any

from Project import Project
from data.SubjectsData import SubjectsData
from data.utilities import list2spm_text_column
from group.spm_utilities import Covariate, Regressor
from subject.Subject import Subject
from myutility.fileutilities import sed_inplace


# class used to replace covariates strings in SPM batch
class SPMCovariates:
    """
    This class contains functions related to the addition of covariates to SPM batch files.
    """

    @staticmethod
    def spm_replace_stats_add_covariates(project: Project, out_batch_job: str, groups_instances:List[List[Subject]], covs:List[Regressor],
                                        batch_id: int = 1, cov_interaction:List[int]=None, data:str|SubjectsData=None, centering: bool = False) -> None:
        """
        This function adds covariates to an SPM batch file.

        Args:
            project: The project object.
            out_batch_job: The path to the SPM batch file.
            groups_instances: List[List[Subject]], where each inner list represents a group.
            covs: A list of covariates.
            batch_id: The ID of the batch job.
            cov_interaction: A list of interactions between covariates and factors.
            data: The name of the data file.
            centering: A boolean indicating whether to center the covariates.
        """
        # -------------------------------------------------------------------------------------------------------------
        if covs is None:
            sed_inplace(out_batch_job, "<COV_STRING>", "matlabbatch{1}.spm.stats.factorial_design.cov = struct('c', {}, 'cname', {}, 'iCFI', {}, 'iCC', {});")
            return
        else:
            if not isinstance(covs, list):
                raise Exception("ERROR in spm_replace_stats_add_simplecovariates, regressors (" + str(covs) + ") is not a list....returning")

        ncov = len(covs)
        if cov_interaction is None:
            # general case when no interaction is specified
            if len(groups_instances) == 1:
                # one group, no interaction
                cov_interaction = [1 for _ in covs]
            else:
                # if covariates : they interact with first factor (group)
                # if nuisance   : no interaction
                cov_interaction = []
                for c in covs:
                    if isinstance(c, Covariate):
                        cov_interaction.append(2)
                    else:
                        cov_interaction.append(1)

        cint = len(cov_interaction)
        if ncov != cint:
            print("ERROR: spm_replace_stats_add_simplecovariates. number of covariates and their interaction differs")
            return

        # -------------------------------------------------------------------------------------------------------------
        if ncov == 1:
            SPMCovariates.spm_replace_stats_add_1cov_manygroups(out_batch_job, groups_instances, project, covs[0],
                                                                batch_id, cov_interaction, data)
        else:
            if centering:
                icc = 1
            else:
                icc = 5

            cov_string  = ""
            for cov_id in range(ncov):
                cov = []
                cov_name    = covs[cov_id].name
                for subjs in groups_instances:
                    cov = cov + project.get_filtered_column(subjs, cov_name, data=data)[0]
                str_cov = "\n" + list2spm_text_column(cov)  # ends with a "\n"

                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").c = "
                cov_string = cov_string + "[" + str_cov + "];\n"
                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").cname = '" + cov_name + "';\n"
                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").iCFI = " + str(cov_interaction[cov_id]) + ";\n"
                cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov(" + str(cov_id + 1) + ").iCC = " + str(icc) + ";\n"

            sed_inplace(out_batch_job,"<COV_STRING>", cov_string)

    @staticmethod
    def spm_replace_stats_add_1cov_manygroups(out_batch_job: str, groups_labels: List[List[Any]], project: Project,
                                              cov:str|Covariate, batch_id: int = 1, cov_interaction:List[int]=None, data:str|SubjectsData=None, centering:bool=False) -> None:
        """
        This function adds a single covariate to an SPM batch file, where the covariate is defined across multiple groups.

        Args:
            out_batch_job: The path to the SPM batch file.
            groups_labels: A list of lists of subjects, where each inner list represents a group.
            project: The project object.
            cov: The covariate.
            batch_id: The ID of the batch job.
            cov_interaction: A list of interactions between covariate and factors.
            data: str | SubjectsData.
            centering: A boolean indicating whether to center the covariate.
        """
        if centering:
            icc = 1
        else:
            icc = 5

        cov_values = []
        for grp in groups_labels:
            cov_values = cov_values + project.get_filtered_column(grp, cov.name, data=data)[0]
        str_cov = "\n" + list2spm_text_column(cov_values)  # ends with a "\n"

        cov_string =              "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.c = "
        cov_string = cov_string + "[" + str_cov + "];\n"
        cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.cname = '" + cov.name + "';\n"
        cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.iCFI = " + str(cov_interaction[0]) + ";\n"
        cov_string = cov_string + "matlabbatch{" + str(batch_id) + "}.spm.stats.factorial_design.cov.iCC = " + str(icc) + ";\n"
        sed_inplace(out_batch_job, "<COV_STRING>", cov_string)
