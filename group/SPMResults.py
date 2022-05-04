import csv
import os

from group.SPMStatsUtils import StatsParams, CatConvStatsParams
from utility.matlab import call_matlab_spmbatch
from utility.utilities import sed_inplace, fillnumber2fourdigits, write_text_file


class SPMResults:

    # ======================================================================================================================================================
    # replace CAT results trasformation string
    # mult_corr = "FWE" | "FDR" | "none"
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def runbatch_cat_results_trasformation_string(project, _global, statsdir, ncontrasts, cmd_id=1, cat_conv_stats_params=None, runit=True):

        if cat_conv_stats_params is None:
            cat_conv_stats_params = CatConvStatsParams()

        mult_corr   = cat_conv_stats_params.mult_corr
        pvalue      = cat_conv_stats_params.pvalue
        cl_ext      = cat_conv_stats_params.cluster_extend

        str_images = "matlabbatch{"+ str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.data_T2x = {"
        for con in range(1,ncontrasts+1):
            str_images += ("'" + os.path.join(statsdir, "spmT_" + fillnumber2fourdigits(con) + ".gii") +"'\n")
        str_images += "}\n"
        str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.sel = 2;\n"

        if mult_corr == "FWE":
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fwe.thresh05 = " + str(pvalue) + ";"
        elif mult_corr == "FDR":
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fdr.thresh05 = " + str(pvalue) + ";"
        elif mult_corr == "none":
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.uncorr.thresh001 = " + str(pvalue) + ";"
        else:
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fwe.thresh05 = " + str(pvalue) + ";"

        str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.inverse = 0;"

        if cl_ext == "none":
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;"
        elif mult_corr == "en_corr":
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.En.noniso = 1;"
        elif mult_corr == "en_nocorr":
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.En.noniso = 0;"
        else:
            print("warning in runbatch_cat_results_trasformation_string...unrecognized cluster_extend in Tsurf transf")
            str_images += "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;"

        out_batch_job, out_batch_start = project.adapt_batch_files("cat_results_trasformation", "mpr")

        write_text_file(out_batch_job, str_images)

        if runit is True:
            call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])


    # parse a series of spm-output csv files and report info of those voxels/cluster associated to the given cluster
    # set    set cluster         cluster         cluster cluster peak            peak            peak    peak    peak
    # p      c   p(FWE - corr)   p(FDR - corr)   equivk  p(unc)  p(FWE - corr)   p(FDR - corr)   T       equivZ  p(unc) x  y  z {mm}
    @staticmethod
    def extract_clusters_info(res_csv_file, ref_clusters, distance=8):

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

class Peak:

    def __init__(self, pfwe, pfdr, t, zscore, punc, x, y, z):
        self.pfwe   = pfwe
        self.pfdr   = pfdr
        self.t      = t
        self.zscore = zscore
        self.punc   = punc
        self.x      = x
        self.y      = y
        self.z      = z


class Cluster:

    def __init__(self, id, pfwe, pfdr, k, punc, firstpeak):
        self.id     = id
        self.pfwe   = pfwe
        self.pfdr   = pfdr
        self.k      = k
        self.punc   = punc
        self.peaks  = []
        self.peaks.append(firstpeak)

    def add_peak(self, peak):
        self.peaks.append(peak)
