import json
import math
import ntpath
import os
import shutil
from copy import deepcopy
from inspect import signature
from shutil import copyfile
from threading import Thread

from data.SubjectsDataDict import SubjectsDataDict
from subject.Subject import Subject
from utility.exceptions import SubjectListException
from utility.images.Image import Image
from utility.fileutilities import sed_inplace, remove_ext


class Project:

    def __init__(self, folder, globaldata, data="data.dat"):

        if not os.path.exists(folder):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.dir        = folder
        self.label      = os.path.basename(self.dir)
        self.name       = os.path.basename(self.dir)

        self.subjects_dir       = os.path.join(self.dir, "subjects")
        self.group_analysis_dir = os.path.join(self.dir, "group_analysis")
        self.script_dir         = os.path.join(globaldata.project_scripts_dir, self.name)

        self.glm_template_dir = os.path.join(self.script_dir, "glm", "templates")

        self.resting_dir            = os.path.join(self.group_analysis_dir, "rs")
        self.mpr_dir                = os.path.join(self.group_analysis_dir, "mpr")

        self.melodic_templates_dir  = os.path.join(self.resting_dir, "melodic", "group_templates")
        self.melodic_dr_dir         = os.path.join(self.resting_dir, "melodic", "dr")
        self.sbfc_dir               = os.path.join(self.resting_dir, "sbfc")

        self.fmri_dir               = os.path.join(self.group_analysis_dir, "fmri")

        self.vbm_dir                = os.path.join(self.mpr_dir, "vbm")
        self.ct_dir                 = os.path.join(self.mpr_dir, "ct")

        self.tbss_dir               = os.path.join(self.group_analysis_dir, "tbss")

        self.topup_rs_params        = os.path.join(self.script_dir, "topup_acqpar_rs.txt")
        self.topup_rs2_params       = os.path.join(self.script_dir, "topup_acqpar_rs2.txt")

        self.topup_fmri_params      = os.path.join(self.script_dir, "topup_acqpar_fmri.txt")
        self.topup_fmri2_params     = os.path.join(self.script_dir, "topup_acqpar_fmri2.txt")

        self.topup_dti_params       = os.path.join(self.script_dir, "topup_acqpar_dti.txt")
        self.eddy_dti_json          = os.path.join(self.script_dir, "dti_ap.json")
        self.eddy_index             = os.path.join(self.script_dir, "eddy_index.txt")

        self.globaldata             = globaldata

        self.subjects           = []
        self.subjects_labels    = []
        self.nsubj              = 0

        self.hasT1  = False
        self.hasRS  = False
        self.hasDTI = False
        self.hasT2  = False

        # load all available subjects list into self.subjects_lists
        with open(os.path.join(self.script_dir, "subjects_lists.json")) as json_file:
            subjects            = json.load(json_file)
            self.subjects_lists = subjects["subjects"]

        # load subjects data if possible
        self.data_file = ""
        self.data = SubjectsDataDict()

        self.load_data(data)

    # load a data_file if exist
    def load_data(self, data_file):

        df = ""
        if os.path.exists(data_file):
            df = data_file
        elif os.path.exists(os.path.join(self.script_dir, data_file)):
            df = os.path.join(self.script_dir, data_file)

        if df != "":
            d = SubjectsDataDict(df)
            if d.num > 0:
                self.data       = d
                self.data_file  = df

        return self.data

    # if must_exist=true:   loads in self.subjects, a list of subjects instances associated to a valid grouplabel or a subjlabels list
    # if must_exist=false:  only create
    # returns this list
    def load_subjects(self, group_label, sess_id=1, must_exist=True):

        try:
            subjects           = self.get_subjects(group_label, sess_id, must_exist)

        except SubjectListException as e:
            raise SubjectListException("load_subjects", e.param)    # send whether the group label was not present
                                                                    # or one of the subjects was not valid
        if must_exist:
            self.subjects           = subjects
            self.subjects_labels    = [subj.label for subj in self.subjects]
            self.nsubj              = len(self.subjects)

        return subjects

    # get a deepcopy of subject with given label
    def get_subject_by_label(self, subj_label, sess=1, must_exist=True):

        if must_exist:
            for subj in self.subjects:
                if subj.label == subj_label:
                    if subj.sessid == sess:
                        return deepcopy(subj)
                    else:
                        return subj.set_properties(sess, rollback=True)  # it returns a deepcopy of requested session
            return None
        else:
            return Subject(subj_label, self, sess)

    # ==================================================================================================================
    # region GET SUBJECTS' LABELS or INSTANCES
    # ==================================================================================================================
    # IN:   GROUP_LABEL | SUBLABELS LIST
    # OUT:  [VALID SUBJECT INSTANCES LIST]
    def get_subjects(self, group_or_subjlabels, sess_id=1, must_exist=True):
        valid_subj_labels = self.get_subjects_labels(group_or_subjlabels, sess_id, must_exist)
        return self.__get_subjects_from_labels(valid_subj_labels, sess_id, must_exist)

    # IN:   GROUP_LABEL | SUBLABELS LIST | SUBJINSTANCES LIST
    # OUT:  [VALID SUBLABELS LIST]
    def get_subjects_labels(self, grouplabel_or_subjlist=None, sess_id=1, must_exist=True):

        if grouplabel_or_subjlist is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("get_subjects_labels", "given grouplabel_or_subjlist is None and no group is loaded")
            else:
                return self.subjects_labels         # if != 0, a list of validated subjects exist

        elif isinstance(grouplabel_or_subjlist, str):  # must be a group_label and have its associated subjects list
            return self.__get_valid_subjlabels_from_group(grouplabel_or_subjlist, sess_id, must_exist)

        elif isinstance(grouplabel_or_subjlist, list):
            if isinstance(grouplabel_or_subjlist[0], str) is True:
                # list of subjects' names
                if must_exist:
                    return self.__get_valid_subjlabels(grouplabel_or_subjlist, sess_id)
                else:
                    return grouplabel_or_subjlist   # [string]

            elif isinstance(grouplabel_or_subjlist[0], Subject):
                return [subj.label for subj in grouplabel_or_subjlist]
            else:
                raise SubjectListException("get_subjects_labels", "the given grouplabel_or_subjlist param is not a string list, first value is: " + str(grouplabel_or_subjlist[0]))
        else:
            raise SubjectListException("get_subjects_labels", "the given grouplabel_or_subjlist param is not a valid param (None, string  or string list), is: " + str(grouplabel_or_subjlist))

    # endregion

    # =========================================================================
    # region PRIVATE VALIDATION ROUTINES
    # =========================================================================

    # must_exist=True   -> check list is valid and whether all subjects belonging to the given group_label are valid
    # must_exist=False  -> if list if present, returns its associated subjects' labels without verifying their validity
    # IN:   GROUP_LAB
    # OUT:  [VALID SUBJLABELS LIST] or SubjectListException
    def __get_valid_subjlabels_from_group(self, group_label, sess_id=1, must_exist=True):
        for grp in self.subjects_lists:
            if grp["label"] == group_label:
                if must_exist:
                    return self.__get_valid_subjlabels(grp["list"], sess_id)
                else:
                    return grp["list"]
        raise SubjectListException("__get_valid_subjlabels_from_group", "given group_label (" + group_label + ") does not exist in subjects_lists")

    # check whether all subjects listed in subj_labels are valid
    # returns given list if all valid
    # IN:   SUBJLABELS LIST
    # OUT:  [VALID SUBJLABELS LIST] or SubjectListException
    def __get_valid_subjlabels(self, subj_labels, sess_id=1):
        for lab in subj_labels:
            if not Subject(lab, self, sess_id).exist():
                raise SubjectListException("__get_valid_subjlabels", "given subject (" + lab + ") does not exist in file system")
        return subj_labels

    # create and returns a list of valid subjects instances given a subjlabels list
    # IN:   SUBJLABELS LIST
    # OUT:  VALID SUBJS INSTANCES
    def __get_subjects_from_labels(self, subj_labels, sess_id=1, must_exist=True):
        if must_exist:
            subj_labels = self.__get_valid_subjlabels(subj_labels)
        return [Subject(subj_lab, self, sess_id) for subj_lab in subj_labels]

    #endregion

    # ==================================================================================================================
    #region CHECK/PREPARE IMAGES
    # ==================================================================================================================
    def check_subjects_original_images(self):

        incomplete_subjects = []
        for subj in self.subjects:
            missing = subj.check_images(self.hasT1, self.hasRS, self.hasDTI, self.hasT2)
            if len(missing) > 0:
                incomplete_subjects.append({"label": subj.label, "images": missing})

        return incomplete_subjects

    # check whether all subjects defined by given group_or_subjlabels have the necessary files to perform given analysis
    # allowed analysis are: vbm_fsl, vbm_spm, ct, tbss, bedpost, xtract_single, xtract_group, melodic, sbfc, fmri
    # returns a string with the subjects not ready
    def can_run_analysis(self, analysis_type, analysis_params=None, group_or_subjlabels=None, sess_id=1):

        invalid_subjs = ""
        valid_subjs = self.get_subjects(group_or_subjlabels, sess_id)
        for subj in valid_subjs:
            if not subj.can_run_analysis(analysis_type, analysis_params):
                invalid_subjs = invalid_subjs + subj.label + ", "

        if len(invalid_subjs) > 0:
            print("ERROR.... the following subjects prevent the completion of the " + analysis_type + " analysis: " + invalid_subjs)
        else:
            print("OK....... " + analysis_type + " analysis can be run")

        return invalid_subjs

    def check_all_coregistration(self, outdir, subjs_labels=None, _from=None, _to=None, num_cpu=1, overwrite=False):

        if subjs_labels is None:
            subjs_labels = self.get_subjects_labels()

        if _from is None:
            _from = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        if _to is None:
            _to = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        self.run_subjects_methods("transform", "test_all_coregistration", [{"test_dir":outdir, "_from":_from, "_to":_to, "overwrite":overwrite}], ncore=num_cpu, group_or_subjlabels=subjs_labels)

        if "hr" in _to:
            l_t1 = os.path.join(outdir, "lin", "hr");            nl_t1 = os.path.join(outdir, "nlin", "hr")
            sd_l_t1 = os.path.join(outdir, "slicesdir", "lin_hr");      os.makedirs(sd_l_t1, exist_ok=True)
            sd_nl_t1 = os.path.join(outdir, "slicesdir", "nlin_hr");    os.makedirs(sd_nl_t1, exist_ok=True)
            os.chdir(l_t1);     os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(l_t1, "slicesdir"), sd_l_t1)
            os.chdir(nl_t1);    os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(nl_t1, "slicesdir"), sd_nl_t1)

        if "dti" in _to:
            l_dti = os.path.join(outdir, "lin", "dti");     nl_dti = os.path.join(outdir, "nlin", "dti")
            sd_l_dti = os.path.join(outdir, "slicesdir", "lin_dti");    os.makedirs(sd_l_dti, exist_ok=True)
            sd_nl_dti = os.path.join(outdir, "slicesdir", "nlin_dti");  os.makedirs(sd_nl_dti, exist_ok=True)
            os.chdir(l_dti);    os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(l_dti, "slicesdir"), sd_l_dti)
            os.chdir(nl_dti);   os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(nl_dti, "slicesdir"), sd_nl_dti)

        if "rs" in _to:
            l_rs = os.path.join(outdir, "lin", "rs");   nl_rs = os.path.join(outdir, "nlin", "rs")
            sd_l_rs = os.path.join(outdir, "slicesdir", "lin_rs");      os.makedirs(sd_l_rs, exist_ok=True)
            sd_nl_rs = os.path.join(outdir, "slicesdir", "nlin_rs");    os.makedirs(sd_nl_rs, exist_ok=True)
            os.chdir(l_rs);     os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(l_rs, "slicesdir"), sd_l_rs)
            os.chdir(nl_rs);    os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(nl_rs, "slicesdir"), sd_nl_rs)

        if "std" in _to:
            l_std = os.path.join(outdir, "lin", "std");     nl_std = os.path.join(outdir, "nlin", "std")
            sd_l_std = os.path.join(outdir, "slicesdir", "lin_std");    os.makedirs(sd_l_std, exist_ok=True)
            sd_nl_std = os.path.join(outdir, "slicesdir", "nlin_std");  os.makedirs(sd_nl_std, exist_ok=True)
            os.chdir(l_std);    os.system("slicesdir -p " + self.globaldata.fsl_std_mni_2mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(l_std, "slicesdir"), sd_l_std)
            os.chdir(nl_std);   os.system("slicesdir -p " + self.globaldata.fsl_std_mni_2mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(nl_std, "slicesdir"), sd_nl_std)

        if "std4" in _to:
            l_std4 = os.path.join(outdir, "lin", "std4");       nl_std4 = os.path.join(outdir, "nlin", "std4")
            sd_l_std4 = os.path.join(outdir, "slicesdir", "lin_std4");  os.makedirs(sd_l_std4, exist_ok=True)
            sd_nl_std4 = os.path.join(outdir, "slicesdir", "nlin_std4");os.makedirs(sd_nl_std4, exist_ok=True)
            os.chdir(l_std4);   os.system("slicesdir -p " + self.globaldata.fsl_std_mni_4mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(l_std4, "slicesdir"), sd_l_std4)
            os.chdir(nl_std4);  os.system("slicesdir -p " + self.globaldata.fsl_std_mni_4mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(nl_std4, "slicesdir"), sd_nl_std4)

        if "t2" in _to:
            l_t2 = os.path.join(outdir, "lin", "t2");       nl_t2 = os.path.join(outdir, "nlin", "t2")
            sd_l_t2 = os.path.join(outdir, "slicesdir", "lin_t2");      os.makedirs(sd_l_t2, exist_ok=True)
            sd_nl_t2 = os.path.join(outdir, "slicesdir", "nlin_t2");    os.makedirs(sd_nl_t2, exist_ok=True)
            os.chdir(l_t2);     os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(l_t2, "slicesdir"), sd_l_t2)
            os.chdir(nl_t2);    os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(nl_t2, "slicesdir"), sd_nl_t2)

    # create a folder where it copies the brain extracted from BET, FreeSurfer and SPM
    def compare_brain_extraction(self, outdir, list_subj_label=None, num_cpu=1):

        if list_subj_label is None or list_subj_label == "":

            if len(self.subjects) == 0:
                print("ERROR in compare_brain_extraction: no subjects are loaded and input subjects list label is empty")
                return
            else:
                subjs = self.subjects
        else:
            subjs = self.get_subjects_labels(list_subj_label)

        os.makedirs(outdir, exist_ok=True)

        self.run_subjects_methods("mpr", "compare_brain_extraction", [{"tempdir":outdir}], ncore=num_cpu, group_or_subjlabels=list_subj_label)

        for subj in subjs:
            subj.compare_brain_extraction(outdir)

        olddir = os.getcwd()
        os.chdir(outdir)
        os.system("slicesdir ./*.nii.gz")
        os.chdir(olddir)

    # prepare_mpr_for_setorigin1 and prepare_mpr_for_setorigin2 are to be used in conjunction
    # the former make a backup and unzip the original file,
    # the latter zip and clean up
    def prepare_mpr_for_setorigin1(self, group_label, sess_id=1, replaceOrig=False, overwrite=False):
        subjects = self.load_subjects(group_label, sess_id)

        for subj in subjects:
            if not replaceOrig:
                subj.t1_data.cp(subj.t1_data + "_old_origin")

            niifile = Image(os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii"))

            if niifile.uexist and not overwrite:
                print("skipping prepare_mpr_for_setorigin1 for subj " + subj.label)
                continue

            subj.t1_data.cpath.unzip(niifile, replace=True)
            print("unzipped " + subj.label + " mri")

    def prepare_mpr_for_setorigin2(self, group_label, sess_id=1):

        subjects = self.load_subjects(group_label, sess_id)
        for subj in subjects:
            niifile = Image(os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii"))
            subj.t1_data.cpath.rm()
            niifile.compress(subj.t1_data.cpath)
            niifile.rm()
            print("zipped " + subj.label + " mri")
    #endregion

    # ==================================================================================================================
    #region GET SUBJECTS DATA
    # ==================================================================================================================
    # returns a matrix (values x subjects) containing values of the requested columns of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_columns(self, columns_list, grouplabel_or_subjlist, data=None, sort=False, sess_id=1):

        subj_list  = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_columns(columns_list, subj_list, sort=sort)
        else:
            return None

    # returns a tuple with two vectors[nsubj] (filtered by subj labels) of the requested column
    # - [values]
    # - [labels]
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column(self, column, grouplabel_or_subjlist, data=None, sort=False, sess_id=1):

        subj_list   = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column(column, subj_list, sort=sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column_by_value(self, column, value, operation="=", grouplabel_or_subjlist=None, data=None, sort=False, sess_id=1):

        subj_list   = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_by_value(column, value, operation, subj_list, sort=sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    # def get_filtered_column_by_value(self, column, value, operation="=", subjects_label=None, data=None):
    def get_filtered_subj_dict_column_within_values(self, column, value1, value2, operation="<>", grouplabel_or_subjlist=None,
                                                    data=None, sort=False, sess_id=1):

        subj_list   = self.get_subjects_labels(grouplabel_or_subjlist, sess_id)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_within_values(column, value1, value2, operation, subj_list, sort=sort)
        else:
            return None

    # validate data dictionary. if param is none -> takes it from self.data
    #                           otherwise try to load it
    def validate_data(self, data=None) -> SubjectsDataDict:

        if data is None:
            if bool(self.data):
                return self.data
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is None and project's data is not loaded")
        else:
            if isinstance(data, SubjectsDataDict):
                return data
            elif isinstance(data, str):
                if os.path.exists(data):
                    return SubjectsDataDict(data)
                else:
                    raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is a string that does not point to a valid file to load")
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is neither a SubjectsDataDict nor a string")

    def add_icv_to_data(self, grouplabel_or_subjlist=None, updatefile=False, sess_id=1):

        if grouplabel_or_subjlist is None:
            grouplabel_or_subjlist = self.get_subjects_labels()
        else:
            grouplabel_or_subjlist = self.get_subjects_labels(grouplabel_or_subjlist)

        icvs = self.get_subjects_icv(grouplabel_or_subjlist, sess_id)

        self.data.add_column("icv", grouplabel_or_subjlist, icvs, updatefile)

    def get_subjects_icv(self, grouplabel_or_subjlist, sess_id=1):

        if isinstance(grouplabel_or_subjlist[0], Subject):  # so caller does not have to set also the sess_id, is a xprojects parameter
            subjects_list = grouplabel_or_subjlist
        else:
            subjects_list = self.get_subjects(grouplabel_or_subjlist, sess_id)

        icv_scores = []
        for subj in subjects_list:
            with open(subj.t1_spm_icv_file) as fp:
                fp.readline()
                line    = fp.readline().rstrip()
                values  = line.split(',')

            icv_scores.append(round(float(values[1]) + float(values[2]) + float(values[3]), 4))
        return icv_scores

    def add_data_column(self, colname, labels, values, updatefile=False):
        self.data.add_column(colname, labels, values, updatefile)

    #endregion ==================================================================================================================

    # ==================================================================================================================
    # GROUP ANALYSIS ACCESSORY
    # ==================================================================================================================
    # returns out_batch_job, created from zero
    def create_batch_files(self, out_batch_name, seq):

        out_batch_dir = os.path.join(self.script_dir, seq, "spm", "batch")
        os.makedirs(out_batch_dir, exist_ok=True)

        in_batch_start = os.path.join(self.globaldata.spm_templates_dir, "spm_job_start.m")

        out_batch_start = os.path.join(out_batch_dir, "create_" + out_batch_name + "_start.m")
        out_batch_job   = os.path.join(out_batch_dir, "create_" + out_batch_name + ".m")

        # create empty file
        open(out_batch_job, 'w', encoding='utf-8').close()

        # set start file
        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, "X", "1")
        sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

        return out_batch_job, out_batch_start

    # returns out_batch_job, taken from an existing spm batch template
    def adapt_batch_files(self, templfile_noext, seq, prefix="", postfix=""):

        if prefix != "":
            prefix = prefix + "_"

        if postfix != "":
            postfix =  "_" + postfix

        # force input template to be without ext
        templfile_noext     = remove_ext(templfile_noext)
        input_batch_name    = ntpath.basename(templfile_noext)

        out_batch_dir       = os.path.join(self.script_dir, seq, "spm", "batch")
        os.makedirs(out_batch_dir, exist_ok=True)

        in_batch_start = os.path.join(self.globaldata.spm_templates_dir, "spm_job_start.m")

        if os.path.exists(templfile_noext + ".m"):
            in_batch_job = templfile_noext + ".m"
        else:
            in_batch_job = os.path.join(self.globaldata.spm_templates_dir, templfile_noext + "_job.m")

        out_batch_start = os.path.join(out_batch_dir, prefix + "create_" + input_batch_name + postfix + "_start.m")
        out_batch_job   = os.path.join(out_batch_dir, prefix + "create_" + input_batch_name + postfix + ".m")

        # set job file
        copyfile(in_batch_job, out_batch_job)

        # set start file
        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, "X", "1")
        sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

        return out_batch_job, out_batch_start

    # ==================================================================================================================
    # MULTICORE PROCESSING
    # ==================================================================================================================
    # *kwparams is a list of kwparams. if len(kwparams)=1 & len(subj_labels) > 1 ...pass that same kwparams[0] to all subjects
    # if subj_labels is not given...use the loaded subjects
    def run_subjects_methods(self, method_type, method_name, kwparams, ncore=1, group_or_subjlabels=None, sess_id=1, must_exist=True):

        if method_type != "" and method_type != "mpr" and method_type != "dti" and method_type != "epi" and method_type != "transform":
            print("ERROR in run_subjects_methods: the method type does not correspond to any of the allowed values (\"\", mpr, epi, dti, transform")
            return

        print("run_subjects_methods: validating given subjects")
        valid_subjlabels    = self.get_subjects_labels(group_or_subjlabels, sess_id, must_exist)
        nsubj               = len(valid_subjlabels)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        # check number of NECESSARY (without a default value) method params
        subj = self.get_subject_by_label(valid_subjlabels[0], sess_id, must_exist)    # subj appear unused, but is instead used in the eval()
        if method_type == "":
            method = eval("subj." + method_name)
        else:
            method = eval("subj." + method_type + "." + method_name)
        sig     = signature(method)
        nparams = len(sig.parameters)  # parameters that need a value
        for p in sig.parameters:
            if sig.parameters[p].default is not None:
                nparams = nparams - 1  # this param has a default value

        # if no params are given, create a nsubj list of None
        if len(kwparams) == 0:
            # if nparams > 0:
            #     print("ERROR in run_subjects_methods: given params list is empty, while method needs " + str(nparams) + " params")
            #     return
            # else:
            kwparams = [None] * nsubj

        nprocesses = len(kwparams)

        if nsubj > 1 and nprocesses == 1:
            kwparams = [kwparams[0]] * nsubj  # duplicate the first kwparams up to given subj number
            nprocesses = nsubj
        else:
            if nprocesses != nsubj:
                print("ERROR in run_subject_method: given params list length differs from subjects list")
                return
        # here nparams is surely == nsubj

        numblocks = math.ceil(nprocesses / ncore)  # num of processing blocks (threads)

        subjects = []
        processes = []

        for p in range(numblocks):
            subjects.append([])
            processes.append([])

        proc4block = 0
        curr_block = 0

        # divide nprocesses across numblocks
        for proc in range(nprocesses):
            processes[curr_block].append(kwparams[proc])
            subjects[curr_block].append(valid_subjlabels[proc])

            proc4block = proc4block + 1
            if proc4block == ncore:
                curr_block = curr_block + 1
                proc4block = 0

        for bl in range(numblocks):
            threads = []

            for s in range(len(subjects[bl])):

                subj = self.get_subject_by_label(subjects[bl][s], sess_id, must_exist)

                if subj is not None:

                    if method_type == "":
                        method = eval("subj." + method_name)
                    else:
                        method = eval("subj." + method_type + "." + method_name)

                    try:
                        process = Thread(target=method, kwargs=processes[bl][s])
                        process.start()
                        threads.append(process)
                    except Exception as e:
                        print(e)

            for process in threads:
                process.join()

            print("completed block " + str(bl) + " with processes: " + str(subjects[bl]))

    # ==================================================================================================================
