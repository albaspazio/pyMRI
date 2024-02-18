import csv
import os

from Global import Global
from Project import Project
from group.spm_utilities import CatConvResultsParams, Peak, Cluster, ResultsParams
from utility.matlab import call_matlab_spmbatch
from utility.utilities import fillnumber2fourdigits
from utility.fileutilities import write_text_file


class SPMResults:
    """
    This class provides static methods for managing SPM results.
    """

    @staticmethod
    def get_1stlevel_results_report(result_report:ResultsParams, idstep:int=5):

        """
        This function generates a MATLAB code snippet for reporting 1st-level results.

        Args:
            result_report (ResultsParams): The SPM results object.
            idstep (int, optional): The ID of the MATLAB batch step. Defaults to 5.

        Returns:
            str: The MATLAB code snippet.
        """
        multcorr= result_report.mult_corr
        pvalue  = result_report.pvalue
        extent  = result_report.cluster_extend

        res_rep_str =  ("matlabbatch{" + str(idstep) + "}.spm.stats.results.spmmat(1) = cfg_dep('Contrast Manager: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.titlestr = '';\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.contrasts = Inf;\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.threshdesc = '" + multcorr + "';\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.thresh = " + str(pvalue) + ";\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.extent = " + str(extent) + ";\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.conjunction = 1;\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.conspec.mask.none = 1;\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.units = 1;\n")
        res_rep_str += ("matlabbatch{" + str(idstep) + "}.spm.stats.results.export{1}.jpg = true;\n")

        return res_rep_str

    # ======================================================================================================================================================
    # replace CAT results trasformation string
    # mult_corr = "FWE" | "FDR" | "none"
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def runbatch_cat_results_trasformation(project:Project, _global:Global, statsdir:str, ncontrasts:int, analysis_name:str,
                                           cmd_id:int=1, cat_conv_stats_params:CatConvResultsParams=None, eng=None, runit:bool=True):

        """
        This function generates a MATLAB code snippet for performing CAT results transformation.

        Args:
            project (spm.Project): The SPM project object.
            _global (spm.Global): The SPM global object.
            statsdir (str): The directory containing SPM results.
            ncontrasts (int): The number of contrasts in the analysis.
            analysis_name (str): The name of the analysis.
            cmd_id (int, optional): The ID of the MATLAB batch step. Defaults to 1.
            cat_conv_stats_params (CatConvResultsParams, optional): The CAT conversion parameters. Defaults to None.
            eng (spm.MatlabEngine, optional): The MATLAB engine object. Defaults to None.
            runit (bool, optional): A flag indicating whether to run the code. Defaults to True.

        Returns:
            None: If runit is False, returns None. Otherwise, returns the output of the MATLAB engine.
        """

        if cat_conv_stats_params is None:
            cat_conv_stats_params = CatConvResultsParams()

        mult_corr   = cat_conv_stats_params.mult_corr
        pvalue      = cat_conv_stats_params.pvalue
        cl_ext      = cat_conv_stats_params.cluster_extend

        str_images = "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.data_T2x = {"
        for con in range(1, ncontrasts+1):
            str_images += ("'" + os.path.join(statsdir, "spmT_" + fillnumber2fourdigits(con) + ".gii") + "'\n")
        str_images += "}\n"
        str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.sel = 2;\n"
        str_images += SPMResults.get_threshold_string_cat_results_trasformation(mult_corr, pvalue, cmd_id)
        str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.inverse = 0;"
        str_images += SPMResults.get_clustext_string_cat_results_trasformation(cl_ext, cmd_id)

        out_batch_job, out_batch_start = project.create_batch_files("cat_" + analysis_name + "_results_trasformation", "mpr")

        write_text_file(out_batch_job, str_images)

        if runit:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])
            else:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir], eng=eng)
        os.remove(out_batch_start)

    @staticmethod
    def get_threshold_string_cat_results_trasformation(mult_corr:str, pvalue:float, cmd_id:int=1):

        """
        This function generates a MATLAB code snippet for performing CAT results transformation.

        Args:
            mult_corr (str): The type of multiple comparison correction to be applied.
                Can be "FWE", "FDR", or "none".
            pvalue (float): The p-value threshold for multiple comparison correction.
            cmd_id (int, optional): The ID of the MATLAB batch step. Defaults to 1.

        Returns:
            str: The MATLAB code snippet.
        """

        res = ""
        if mult_corr == "FWE":
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fwe.thresh05 = " + str(pvalue) + ";"
        elif mult_corr == "FDR":
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fdr.thresh05 = " + str(pvalue) + ";"
        elif mult_corr == "none":
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.uncorr.thresh001 = " + str(pvalue) + ";"
        else:
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fwe.thresh05 = " + str(pvalue) + ";"

        return res

    @staticmethod
    def get_clustext_string_cat_results_trasformation(cl_ext:str, cmd_id:int=1):

        """
        This function generates a MATLAB code snippet for performing CAT results transformation.

        Args:
            cl_ext (str): The type of cluster extension to be applied.
                Can be "none", "en_corr", or "en_nocorr".
            cmd_id (int, optional): The ID of the MATLAB batch step. Defaults to 1.

        Returns:
            str: The MATLAB code snippet.
        """

        res = ""
        if cl_ext == "none":
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;"
        elif cl_ext == "en_corr":
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.En.noniso = 1;"
        elif cl_ext == "en_nocorr":
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.En.noniso = 0;"
        else:
            print("warning in runbatch_cat_results_trasformation...unrecognized cluster_extend in Tsurf transf")
            res += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;"

        return res

    # parse a series of spm-output csv files and report info of those voxels/cluster associated to the given cluster
    # set    set cluster         cluster         cluster cluster peak            peak            peak    peak    peak
    # p      c   p(FWE - corr)   p(FDR - corr)   equivk  p(unc)  p(FWE - corr)   p(FDR - corr)   T       equivZ  p(unc) x  y  z {mm}
    @staticmethod
    def extract_clusters_info(res_csv_file:str): #, ref_clusters, distance=8):

        """
        This function extracts information from a SPM results CSV file about the clusters and peaks.

        Args:
            res_csv_file (str): The path to the SPM results CSV file.

        Returns:
            list: A list of Cluster objects, where each Cluster object represents a cluster of voxels and contains information about the peaks within the cluster.
        """
        
        curr_cluster = -1
        clusters = []
        with open(res_csv_file, "r") as f:
            reader = csv.reader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if reader.line_num < 3:
                    continue
                data_row = row[0].split(",")
                if reader.line_num == 3:
                    num_clusters = int(data_row[1])

                if data_row[2] != "":
                    curr_cluster = curr_cluster + 1
                    clusters.append(Cluster(curr_cluster, float(data_row[2]), float(data_row[3]), int(data_row[4]), float(data_row[5]), Peak(float(data_row[6]), float(data_row[7]), float(data_row[8]), float(data_row[9]), float(data_row[10]), int(data_row[11]), int(data_row[12]), int(data_row[13]))))
                else:
                    clusters[curr_cluster].add_peak(Peak(float(data_row[6]), float(data_row[7]), float(data_row[8]), float(data_row[9]), float(data_row[10]), int(data_row[11]), int(data_row[12]), int(data_row[13])))

        return clusters


