import csv
from utility.utilities import sed_inplace


class SPMResults:

    # ======================================================================================================================================================
    # replace CAT results trasformation string
    # mult_corr = "FWE" | "FDR" | "none"
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def cat_replace_results_trasformation_string(out_batch_job, cmd_id=3, mult_corr="FWE", pvalue=0.05, cluster_extend="none"):

        if mult_corr == "FWE":
            sed_inplace(out_batch_job, "<CAT_T_CONV_THRESHOLD>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fwe.thresh05 = " + str(pvalue) + ";")
        elif mult_corr == "FDR":
            sed_inplace(out_batch_job, "<CAT_T_CONV_THRESHOLD>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fdr.thresh05 = " + str(pvalue) + ";")
        elif mult_corr == "none":
            sed_inplace(out_batch_job, "<CAT_T_CONV_THRESHOLD>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.uncorr.thresh001 = " + str(pvalue) + ";")
        else:
            sed_inplace(out_batch_job, "<CAT_T_CONV_THRESHOLD>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.threshdesc.fwe.thresh05 = " + str(pvalue) + ";")

        if cluster_extend == "none":
            sed_inplace(out_batch_job, "<CAT_T_CONV_CLUSTER>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;")
        elif mult_corr == "en_corr":
            sed_inplace(out_batch_job, "<CAT_T_CONV_CLUSTER>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.En.noniso = 1;")
        elif mult_corr == "en_nocorr":
            sed_inplace(out_batch_job, "<CAT_T_CONV_CLUSTER>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.En.noniso = 0;")
        else:
            print("warning in cat_replace_results_trasformation_string...unrecognized cluster_extend in Tsurf transf")
            sed_inplace(out_batch_job, "<CAT_T_CONV_CLUSTER>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;")

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
        self.pfwe = pfwe
        self.pfdr = pfdr
        self.t = t
        self.zscore = zscore
        self.punc = punc
        self.x = x
        self.y = y
        self.z = z


class Cluster:

    def __init__(self, id, pfwe, pfdr, k, punc, firstpeak):
        self.id = id
        self.pfwe = pfwe
        self.pfdr = pfdr
        self.k = k
        self.punc = punc
        self.peaks = []
        self.peaks.append(firstpeak)

    def add_peak(self, peak):
        self.peaks.append(peak)
