import csv

from utility.utilities import sed_inplace
from utility import import_data_file


class Stats:

    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_stats_add_1cov_manygroups(out_batch_job, groups_labels, project, cov_name, cov_interaction=1, datafile=None):

        cov = []
        for grp in groups_labels:
            cov = cov + project.get_filtered_column(cov_name, grp, datafile)[0]
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

    # parse a series of spm-output csv files and report info of those voxels/cluster associated to the given cluster
    #set    set cluster         cluster         cluster cluster peak            peak            peak    peak    peak
    #p      c   p(FWE - corr)   p(FDR - corr)   equivk  p(unc)  p(FWE - corr)   p(FDR - corr)   T       equivZ  p(unc) x  y  z {mm}
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
                    clusters.append(Cluster(curr_cluster, float(data_row[2]), float(data_row[3]), int(data_row[4]), float(data_row[5]),
                                            Peak(float(data_row[6]),float(data_row[7]),float(data_row[8]),float(data_row[9]),float(data_row[10]),
                                                 int(data_row[11]),int(data_row[12]),int(data_row[13]))))
                else:
                    clusters[curr_cluster].add_peak(Peak(float(data_row[6]),float(data_row[7]),float(data_row[8]),float(data_row[9]),float(data_row[10]),
                                                 int(data_row[11]),int(data_row[12]),int(data_row[13])))


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
