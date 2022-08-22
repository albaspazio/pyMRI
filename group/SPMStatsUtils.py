import os
# import ssl    # it was needed, can't remember when

from Global import Global
from data.SubjectsDataDict import SubjectsDataDict
from data.utilities import list2spm_text_column
from utility.exceptions import DataFileException
from utility.images.Image import Image
from utility.matlab import call_matlab_function_noret, call_matlab_spmbatch
from utility.utilities import sed_inplace, remove_ext


class SPMStatsUtils:

    # create spm fmri 1st level contrasts onsets
    # conditions is a dictionary list with field: [name, onsets, duration]
    @staticmethod
    def spm_replace_fmri_subj_stats_conditions_string(out_batch_job, conditions):

        conditions_string = ""
        for c in range(1, len(conditions) + 1):
            onsets = list2spm_text_column(conditions[c - 1]["onsets"])  # ends with a "\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").name = \'" + conditions[c - 1]["name"] + "\';" + "\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").onset = [" + onsets + "];\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").tmod = 0;\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").duration = " + str(conditions[c - 1]["duration"]) + ";\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").pmod = struct('name', {}, 'param', {}, 'poly', {});\n"
            conditions_string = conditions_string + "matlabbatch{1}.spm.stats.fmri_spec.sess.cond(" + str(c) + ").orth = 1;\n"

        sed_inplace(out_batch_job, "<CONDITION_STRING>", conditions_string)

    # ---------------------------------------------------
    #region compose images string

    # group_instances is a list of subjects' instances
    # image_description: {"type": ct | dartel | vbm, "folder": root path for dartel}
    @staticmethod
    def compose_images_string_1GROUP_MULTREGR(group_instances, out_batch_job, img_description):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_1W: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if not os.path.isdir(img_description["folder"]):
                print("ERROR in compose_images_string_1W: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        cells_images = "\r"

        img = ""
        for subj in group_instances:
            if img_type == "ct":
                img = eval("subj.t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_1GROUP_MULTREGR")
            cells_images = cells_images + "\'" + img + "\'\r"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    @staticmethod
    def compose_images_string_1W(groups_instances, out_batch_job, img_description):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_1W: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if not os.path.isdir(img_description["folder"]):
                print("ERROR in compose_images_string_1W: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        cells_images = ""
        gr = 0
        for subjs in groups_instances:
            gr              = gr + 1
            cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.anova.icell(" + str(gr) + ").scans = "

            img             = ""
            grp1_images     = "{\n"
            for subj in subjs:

                if img_type == "ct":
                    img = eval("subj.t1_cat_resampled_surface")
                elif img_type == "dartel":
                    img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_1W")

                grp1_images = grp1_images + "\'" + img + "\'\n"
            grp1_images = grp1_images + "\n};"

            cells_images = cells_images + grp1_images + "\n"

        sed_inplace(out_batch_job, "<GROUP_IMAGES>", cells_images)

    @staticmethod
    def compose_images_string_2W(factors, out_batch_job, img_description):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_2W: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if not os.path.isdir(img_description["folder"]):
                print("ERROR in compose_images_string_2W: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        factors_labels  = factors["labels"]
        cells           = factors["cells"]

        # nfactors = len(factors_labels)
        nlevels = [len(cells), len(cells[0])]  # nlevels for each factor

        # checks
        # if nfactors != len(cells):
        #     print("Error: num of factors labels (" + str(nfactors) + ") differs from cells content (" + str(len(cells)) + ")")
        #     return

        cells_images = ""
        ncell = 0
        for f1 in range(0, nlevels[0]):
            for f2 in range(0, nlevels[1]):
                ncell           = ncell + 1
                cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(ncell) + ").levels = [" + str(f1 + 1) + "\n" + str(f2 + 1) + "];\n"
                cells_images    = cells_images + "matlabbatch{1}.spm.stats.factorial_design.des.fd.icell(" + str(ncell) + ").scans = {\n"

                subjs           = cells[f1][f2]
                img             = ""
                for subj in subjs:

                    if img_type == "ct":
                        img = eval("subj.t1_cat_resampled_surface")
                    elif img_type == "dartel":
                        img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

                    img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_2W")

                    cells_images = cells_images + "'" + img + "'\n"
                cells_images = cells_images + "};"

        sed_inplace(out_batch_job, "<FACTOR1_NAME>",    factors_labels[0])
        sed_inplace(out_batch_job, "<FACTOR1_NLEV>",    str(nlevels[0]))
        sed_inplace(out_batch_job, "<FACTOR2_NAME>",    factors_labels[1])
        sed_inplace(out_batch_job, "<FACTOR2_NLEV>",    str(nlevels[1]))
        sed_inplace(out_batch_job, "<FACTORS_CELLS>",   cells_images)

    @staticmethod
    def compose_images_string_2sTT(groups_instances, out_batch_job, img_description):

        img_type = img_description["type"]
        if img_type != "ct" and img_type != "dartel": # and img_type != "vbm":
            print("ERROR in compose_images_string_2sTT: given img_description[type] (" + img_type + ") is not valid")
            return

        img_folder  = ""
        if img_type == "dartel":
            if not os.path.isdir(img_description["folder"]):
                print("ERROR in compose_images_string_2sTT: given img_description[folder] (" + img_description["folder"] + ") is not valid a valid folder")
                return
            else:
                img_folder = img_description["folder"]

        subjs1      = groups_instances[0]
        subjs2      = groups_instances[1]

        grp1_images = "{\n"
        img         = ""
        for subj in subjs1:

            if img_type == "ct":
                img = eval("subj.t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_2sTT")

            grp1_images = grp1_images + "\'" + img + "\'\n"
        grp1_images = grp1_images + "\n}"

        grp2_images = "{\n"
        for subj in subjs2:

            if img_type == "ct":
                img = eval("subj.t1_cat_resampled_surface")
            elif img_type == "dartel":
                img = os.path.join(img_folder, "smwc1T1_" + subj.label + ".nii")

            img = Image(img, must_exist=True, msg="SPMStatsUtils.compose_images_string_2sTT")

            grp2_images = grp2_images + "\'" + img + "\'\n"
        grp2_images = grp2_images + "\n}"

        # set job file
        sed_inplace(out_batch_job, "<GROUP1_IMAGES>", grp1_images)
        sed_inplace(out_batch_job, "<GROUP2_IMAGES>", grp2_images)
    #endregion

    # ---------------------------------------------------------------------------
    #region explicit masking

    @staticmethod
    def spm_replace_explicit_mask(_global, out_batch_job, expl_mask=None, athresh=0.2, idstep=1):

        if expl_mask is None:
            masking =   "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.tm.tm_none = 1;\n" \
                        "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.im = 1;\n" \
                        "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.em = {''};"
        else:
            if expl_mask == "icv":
                mask = _global.spm_icv_mask + ",1"
            else:
                expl_mask = Image(expl_mask, must_exist=True, msg="SPMStatsUtils.spm_replace_explicit_mask")
                mask = expl_mask + ",1"

            masking = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.tm.tma.athresh = " + str(athresh) + ";\n" \
                      "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.im = 1;\n" \
                      "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.masking.em = {'" + mask + "'};"

        sed_inplace(out_batch_job, "<FACTDES_MASKING>", masking)

    #endregion

    # ---------------------------------------------------------------------------
    #region global calculation

    # method can be: subj_icv, subj_tiv, "" (no correction) or a column name of the given data_file
    @staticmethod
    def spm_replace_global_calculation(project, out_batch_job, method="", groups_instances=None, data_file=None, idstep=1):

        no_corr_str     = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalc.g_omit = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.glonorm = 1;"
        user_corr_str1  = "matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalc.g_user.global_uval = [\n"
        user_corr_str2  = "];\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.gmsca.gmsca_no = 1;\n matlabbatch{" + str(idstep) + "}.spm.stats.factorial_design.globalm.glonorm = 2;"
        gc_str          = ""

        slabels         = []
        for subjs in groups_instances:
            slabels = slabels + project.get_subjects_labels(subjs)

        if method == "subj_icv":  # read icv file from each subject/mpr/spm folder

            if project.data.exist_filled_column("icv", slabels):
                str_icvs = list2spm_text_column(project.get_filtered_column("icv", slabels)[0])
                # raise DataFileException("spm_replace_global_calculation", "given data_file does not contain the column icv")
            else:
                icvs = []
                for subjs in groups_instances:
                    icvs = icvs + project.get_subjects_icv(subjs)
                str_icvs = list2spm_text_column(icvs)
            gc_str = user_corr_str1 + str_icvs + user_corr_str2
        elif method == "subj_tiv":  # read tiv file from each subject/mpr/cat folder
            # if not project.data.exist_filled_column("tiv", slabels):
            #

            gc_str = no_corr_str
        elif method == "":  # don't correct
            gc_str = no_corr_str

        elif isinstance(method, str) and data_file is not None:  # must be a column in the given data_file list of

            if not os.path.exists(data_file):
                raise DataFileException("spm_replace_global_calculation", "given data_file does not exist")
            data = SubjectsDataDict(data_file)

            if not data.exist_filled_column(method, slabels):
                raise DataFileException("spm_replace_global_calculation", "given data_file does not contain a valid value of column " + method + " for all subjects")

            str_icvs = list2spm_text_column(data.get_filtered_column(method, slabels)[0])
            gc_str = user_corr_str1 + str_icvs + user_corr_str2  # list2spm_text_column ends with a "\n"

        sed_inplace(out_batch_job, "<FACTDES_GLOBAL>", gc_str)
    #endregion

    # ---------------------------------------------------------------------------
    #region CHECK REVIEW ESTIMATE

    @staticmethod
    def spm_get_cat_check(idstep=2):

        return  "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.spmmat(1) = cfg_dep(\'Factorial design specification: SPM.mat File\', substruct(\'.\', 'val', '{}', {1}, \'.\', \'val\', '{}', {1}, \'.\', \'val\', \'{}\', {1}), substruct(\'.\', \'spmmat\'));\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.use_unsmoothed_data = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.adjust_data = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.outdir = {\'\'};\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.fname = \'CATcheckdesign_\';\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.save = 0;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.tools.cat.tools.check_SPM.check_SPM_ortho = 1;\n"

    @staticmethod
    def spm_get_review_model(idstep=2):

        return  "matlabbatch{" + str(idstep) + "}.spm.stats.review.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));\n" \
                "matlabbatch{" + str(idstep) + "}.spm.stats.review.display.matrix = 1;\n" \
                "matlabbatch{" + str(idstep) + "}.spm.stats.review.print = 'ps';\n"

    @staticmethod
    def get_spm_model_estimate(isSurf=False, idstep=3):

        if isSurf:
            return "matlabbatch{" + str(idstep) + "}.spm.tools.cat.stools.SPM.spmmat = cfg_dep('Factorial design specification: SPM.mat File', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('.', 'spmmat'));"
        else:
            return "matlabbatch{" + str(idstep) + "}.spm.stats.fmri_est.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.', 'val', '{}', {1}, '.', 'val', '{}', {1}, '.', 'val', '{}', {1}), substruct('.', 'spmmat'));\n \
                    matlabbatch{" + str(idstep) + "}.spm.stats.fmri_est.write_residuals = 0;\n \
                    matlabbatch{" + str(idstep) + "}.spm.stats.fmri_est.method.Classical = 1;\n"

    #endregion

    # ---------------------------------------------------------------------------
    #region OTHER

    # create a gifti image with ones in correspondence of each vmask voxel
    @staticmethod
    def batchrun_spm_surface_mask_from_volume_mask(vmask, ref_surf, out_surf, matlab_paths): #, distance=8):

        Image(vmask, must_exist=True, msg="SPMStatsUtils.batchrun_spm_surface_mask_from_volume_mask vmask")
        Image(ref_surf, must_exist=True, msg="SPMStatsUtils.batchrun_spm_surface_mask_from_volume_mask ref_surf")
        call_matlab_function_noret('create_surface_mask_from_volume_mask', matlab_paths, "'" + vmask + "','" + ref_surf + "','" + out_surf + "'")

    @staticmethod
    def batchrun_cat_surface_smooth(project, _global, subj_instances, sfilt=12, spm_template_name="cat_surf_smooth", nproc=1, eng=None, runit=True):

        # create template files
        out_batch_job, out_batch_start = project.adapt_batch_files(spm_template_name, "mpr")

        str_images="\n"
        for subj in subj_instances:
            lhimage = "'" + subj.t1_cat_lh_surface + "'"
            str_images = str_images + lhimage + "\n"

        sed_inplace(out_batch_job, "<LH_IMAGES>", str_images)
        sed_inplace(out_batch_job, "<SPFILT>", str(sfilt))
        sed_inplace(out_batch_job, "<N_PROC>", str(nproc))

        if runit:
            if eng is None:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir])
            else:
                call_matlab_spmbatch(out_batch_start, [_global.spm_functions_dir, _global.spm_dir], eng=eng, endengine=False)
    #endregion


class ResultsParams:
    def __init__(self, multcorr="FWE", pvalue=0.05, clustext=0):
        self.mult_corr      = multcorr
        self.pvalue         = pvalue
        self.cluster_extend = clustext


class CatConvResultsParams:
    def __init__(self, multcorr="FWE", pvalue=0.05, clustext="none"):
        self.mult_corr      = multcorr
        self.pvalue         = pvalue    # "FWE" | "FDR" | "none"
        self.cluster_extend = clustext  # "none" | "en_corr" | "en_nocorr"


class PostModel:
    def __init__(self, templ_name, regressors, contr_names=None, res_params=None, res_conv_params=None, isSpm=True):

        if contr_names is None:
            contr_names = []

        templ_name = remove_ext(templ_name)

        # check if template name is valid according to the specification applied in Project.adapt_batch_files
        # it can be a full path (without extension) of an existing file, or a file name present in pymri/templates/spm (without "_job.m)
        if not os.path.exists(templ_name + ".m"):
            if not os.path.exists(os.path.join(Global.get_spm_template_dir(), templ_name + "_job.m")):
                raise Exception("given post_model template name (" + templ_name + ") is not valid")

        self.template_name = templ_name

        self.contrast_names = contr_names   # list of strings
        self.regressors     = regressors    # list of subtypes of Regressors
        self.isSpm          = isSpm

        if res_params is None:
            self.results_params = ResultsParams()   # standard (FWE, 0.05, 0)
        else:
            self.results_params = res_params  # of type (CatConv)ResultsParams

        # if res_conv_params is None, do not create a default value, means I don't want to convert results
        if not isSpm and bool(res_conv_params):
            self.results_conv_params = res_conv_params


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

    def __init__(self, _id, pfwe, pfdr, k, punc, firstpeak):
        self.id     = _id
        self.pfwe   = pfwe
        self.pfdr   = pfdr
        self.k      = k
        self.punc   = punc
        self.peaks  = []
        self.peaks.append(firstpeak)

    def add_peak(self, peak):
        self.peaks.append(peak)


class Regressor:
    def __init__(self, name, isNuisance):
        self.name       = name
        self.isNuisance = isNuisance


class Covariate(Regressor):
    def __init__(self, name):
        super().__init__(name, False)


class Nuisance(Regressor):
    def __init__(self, name):
        super().__init__(name, True)


class FmriProcParams:
    def __init__(self, tr, nsl, sl_tim, ref_sl=-1, acq_sch=0, ta=0, smooth=6):
        self.tr             = tr
        self.nslices        = nsl
        self.slice_timing   = sl_tim
        self.ref_slice      = ref_sl
        self.acq_scheme     = acq_sch
        self.ta             = ta
        self.smooth         = smooth
