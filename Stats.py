import csv
import ntpath

from utility.images import imtest
from utility.utilities import sed_inplace
from utility import import_data_file
from utility.matlab import call_matlab_function_noret

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


    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    @staticmethod
    def spm_stats_add_manycov_1group(out_batch_job, group_label, project, cov_names, cov_interaction=None, datafile=None):

        cov_string = ""
        ncov = len(cov_names)

        if cov_interaction is None:
            cov_interaction = [1 for i in range(ncov)]

        cint = len(cov_interaction)
        if ncov != cint:
            print("ERROR: spm_stats_add_manycov_1group. number of covariates and their interaction differs")
            return



        for cov_id in range(ncov):
            cov_name = cov_names[cov_id]
            cov = project.get_filtered_column(cov_names[cov_id], group_label, data=datafile)[0]
            str_cov = "\n" + import_data_file.list2spm_text_column(cov) # ends with a "\n"

            cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov(" + str(cov_id+1) + ").c = "
            cov_string = cov_string + "[" + str_cov + "];\n"
            cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov(" + str(cov_id+1) + ").cname = '" + cov_name + "';\n"
            cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov(" + str(cov_id+1) + ").iCFI = " + str(cov_interaction[cov_id]) + ";\n"
            cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov(" + str(cov_id+1) + ").iCC = 1;\n"

        sed_inplace(out_batch_job, "<COV_STRING>", cov_string)

    # get cov values from many groups and concat them into a single vector
    # interaction=1 : no interaction, otherwise specify factors (1-based + 1, e.g. first factor = 2)
    # @staticmethod
    # def spm_stats_add_manycov_manygroups(out_batch_job, groups_labels, project, cov_names, cov_interaction=1, datafile=None):
    #
    #     cov = []
    #     for grp in groups_labels:
    #         cov = cov + project.get_filtered_column(cov_name, grp, datafile)[0]
    #     str_cov = "\n" + import_data_file.list2spm_text_column(cov) # ends with a "\n"
    #
    #     cov_string = "matlabbatch{1}.spm.stats.factorial_design.cov.c = "
    #     cov_string = cov_string + "[" + str_cov + "];\n"
    #     cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.cname = '" + cov_name + "';\n"
    #     cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.iCFI = " + str(cov_interaction) + ";\n"
    #     cov_string = cov_string + "matlabbatch{1}.spm.stats.factorial_design.cov.iCC = 1;"
    #     sed_inplace(out_batch_job,"<COV_STRING>", cov_string)

    @staticmethod
    def spm_stats_replace_conditions_string(out_batch_job, conditions):

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

    @staticmethod
    def cat_replace_1group_multregr_contrasts(out_batch_job, cov_names):
        contr_str = ""

        ncov = len(cov_names)
        for cov_id in range(ncov):
            cov_name = cov_names[cov_id]

            # define weight
            weight_str_pos = "0"
            weight_str_neg = "0"
            for wp in range(cov_id):
                weight_str_pos = weight_str_pos + " 0"
                weight_str_neg = weight_str_neg + " 0"
            weight_str_pos = weight_str_pos + " 1"
            weight_str_neg = weight_str_neg + " -1"

            contr_str = contr_str + "matlabbatch{1}.spm.tools.cat.stools.con.consess{" + str(2*(cov_id + 1) - 1) + "}.tcon.name = \'" + cov_name + " pos\';\n"
            contr_str = contr_str + "matlabbatch{1}.spm.tools.cat.stools.con.consess{" + str(2*(cov_id + 1) - 1) + "}.tcon.weights = [" + weight_str_pos + "];\n"
            contr_str = contr_str + "matlabbatch{1}.spm.tools.cat.stools.con.consess{" + str(2*(cov_id + 1) - 1) + "}.tcon.sessrep = 'none';\n"

            contr_str = contr_str + "matlabbatch{1}.spm.tools.cat.stools.con.consess{" + str(2*(cov_id + 1)) + "}.tcon.name = \'" + cov_name + " neg\';\n"
            contr_str = contr_str + "matlabbatch{1}.spm.tools.cat.stools.con.consess{" + str(2*(cov_id + 1)) + "}.tcon.weights = [" + weight_str_neg + "];\n"
            contr_str = contr_str + "matlabbatch{1}.spm.tools.cat.stools.con.consess{" + str(2*(cov_id + 1)) + "}.tcon.sessrep = 'none';\n"

        sed_inplace(out_batch_job, "<CONTRASTS>", contr_str)

    @staticmethod
    def spm_replace_1group_multregr_contrasts(out_batch_job, cov_names):
        contr_str = ""

        ncov = len(cov_names)
        for cov_id in range(ncov):
            cov_name = cov_names[cov_id]

            # define weight
            weight_str_pos = "0"
            weight_str_neg = "0"
            for wp in range(cov_id):
                weight_str_pos = weight_str_pos + " 0"
                weight_str_neg = weight_str_neg + " 0"
            weight_str_pos = weight_str_pos + " 1"
            weight_str_neg = weight_str_neg + " -1"

            contr_str = contr_str + "matlabbatch{1}.spm.stats.stools.con.consess{" + str(2*(cov_id + 1) - 1) + "}.tcon.name = \'" + cov_name + " pos\';\n"
            contr_str = contr_str + "matlabbatch{1}.spm.stats.stools.con.consess{" + str(2*(cov_id + 1) - 1) + "}.tcon.weights = [" + weight_str_pos + "];\n"
            contr_str = contr_str + "matlabbatch{1}.spm.stats.stools.con.consess{" + str(2*(cov_id + 1) - 1) + "}.tcon.sessrep = 'none';\n"

            contr_str = contr_str + "matlabbatch{1}.spm.stats.stools.con.consess{" + str(2*(cov_id + 1)) + "}.tcon.name = \'" + cov_name + " neg\';\n"
            contr_str = contr_str + "matlabbatch{1}.spm.stats.stools.con.consess{" + str(2*(cov_id + 1)) + "}.tcon.weights = [" + weight_str_neg + "];\n"
            contr_str = contr_str + "matlabbatch{1}.spm.stats.stools.con.consess{" + str(2*(cov_id + 1)) + "}.tcon.sessrep = 'none';\n"

        sed_inplace(out_batch_job, "<CONTRASTS>", contr_str)


    # replace CAT results trasformation string
    # mult_corr = "FWE" | "FDR" | "none"
    # cluster_extend = "none" | "en_corr" | "en_nocorr"
    @staticmethod
    def cat_replace_trasformation_string(out_batch_job, cmd_id=3, mult_corr="FWE", pvalue=0.05, cluster_extend="none"):

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
            print("warning in cat_replace_trasformation_string...unrecognized cluster_extend in Tsurf transf")
            sed_inplace(out_batch_job, "<CAT_T_CONV_CLUSTER>", "matlabbatch{" + str(cmd_id) + "}.spm.tools.cat.tools.T2x_surf.conversion.cluster.none = 1;")

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

    # create a gifti image with ones in correspondence of each vmask voxel
    @staticmethod
    def spm_stats_replace_conditions_string(vmask, ref_surf, out_surf, matlab_paths, distance=8):

        if imtest(vmask) is False:
            print("Error in create_surface_mask_from_volume_mask: input vmask does not exist")
            return

        if imtest(ref_surf) is False:
            print("Error in create_surface_mask_from_volume_mask: input ref_surf does not exist")
            return

        call_matlab_function_noret('create_surface_mask_from_volume_mask', matlab_paths, "'" + vmask + "','" + ref_surf + "','" + out_surf + "'")


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
