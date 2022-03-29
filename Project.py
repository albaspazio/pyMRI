import json
import math
import os
import shutil
import ntpath

from copy import deepcopy
from inspect import signature
from threading import Thread
from shutil import copyfile

from subject.Subject import Subject
from utility.SubjectsDataDict import SubjectsDataDict
from utility.images import imcp, imrm
from utility.utilities import gunzip, compress, sed_inplace


class Project:

    def __init__(self, folder, globaldata, data="data.dat"):

        if not os.path.exists(folder):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.dir        = folder
        self.label      = os.path.basename(self.dir)
        self.name       = os.path.basename(self.dir)

        self.subjects_dir       = os.path.join(self.dir, "subjects")
        self.group_analysis_dir = os.path.join(self.dir, "group_analysis")
        self.script_dir         = os.path.join(self.dir, "script")

        self.glm_template_dir = os.path.join(self.script_dir, "glm", "templates")

        self.resting_dir            = os.path.join(self.group_analysis_dir, "resting")
        self.mpr_dir                = os.path.join(self.group_analysis_dir, "mpr")

        self.melodic_templates_dir  = os.path.join(self.resting_dir, "group_templates")
        self.melodic_dr_dir         = os.path.join(self.resting_dir, "dr")
        self.sbfc_dir               = os.path.join(self.resting_dir, "sbfc")

        self.vbm_dir                = os.path.join(self.mpr_dir, "vbm")
        self.ct_dir                 = os.path.join(self.mpr_dir, "ct")

        self.tbss_dir = os.path.join(self.group_analysis_dir, "tbss")

        self.topup_dti_params       = os.path.join(self.script_dir, "topup_acqpar_dti.txt")
        self.topup_rs_params        = os.path.join(self.script_dir, "topup_acqpar_rs.txt")
        self.topup_fmri_params      = os.path.join(self.script_dir, "topup_acqpar_fmri.txt")
        self.eddy_index             = os.path.join(self.script_dir, "eddy_index.txt")

        self._global = globaldata

        self.subjects = []
        self.nsubj = -1

        self.hasT1 = False
        self.hasRS = False
        self.hasDTI = False
        self.hasT2 = False

        # load all available subjects list into self.subjects_lists
        with open(os.path.join(self.script_dir, "subjects_lists.json")) as json_file:
            self.subjects_lists = json.load(json_file)

        self.data_file = ""
        self.data = {}
        # load data file if exist
        if os.path.exists(data):
            self.data_file = data
        elif os.path.exists(os.path.join(self.script_dir, data)):
            self.data_file = os.path.join(self.script_dir, data)

        if self.data_file != "":
            self.data = SubjectsDataDict(self.data_file)

    # ==================================================================================================================
    # GET SUBJECTS' INSTANCES
    # ==================================================================================================================
    # loads a list of subjects instances in self.subjects
    # returns this list
    def load_subjects(self, group_label, sess_id=1):

        self.subjects = self.get_subjects(group_label, sess_id)
        self.nsubj = len(self.subjects)
        return self.subjects

    # create and returns a list of subjects instances
    def get_subjects(self, group_label, sess_id=1):

        subjects = self.get_subjects_labels(group_label)
        subjs = []
        for subj_lab in subjects:
            subjs.append(Subject(subj_lab, sess_id, self))
        return subjs

    # ==================================================================================================================
    # GET SUBJECTS' LABELS
    # ==================================================================================================================
    # retrieve a specific list of subjects' labels
    def get_subjects_labels(self, group_label=None):
        try:
            if group_label is None:
                return self.get_loaded_subjects_labels()
            else:
                if isinstance(group_label, list):
                    return group_label
                else:
                    for grp in self.subjects_lists["subjects"]:
                        if grp["label"] == group_label:
                            return grp["list"]

        except Exception as e:
            print("Error in get_subjectlabels")
            return []

    # get the list of loaded subjects' labels
    def get_loaded_subjects_labels(self):
        subjs = []
        for subj in self.subjects:
            subjs.append(subj.label)
        return subjs

    # ---------------------------------------------------------
    # get a deepcopy of subject with given label
    def get_subject_by_label(self, subj_label, sess=1):

        for subj in self.subjects:
            if subj.label == subj_label:
                if subj.sessid == sess:
                    return deepcopy(subj)
                else:
                    return subj.set_properties(sess, rollback=True)  # it returns a deepcopy of requested session
        return None

    def get_subjects_num(self):
        return len(self.subjects)

    # ==================================================================================================================
    # CHECK/PREPARE IMAGES
    # ==================================================================================================================
    def check_subjects_original_images(self):

        incomplete_subjects = []
        for subj in self.subjects["subjects"]:
            missing = subj.check_images(self.hasT1, self.hasRS, self.hasDTI, self.hasT2)
            if len(missing) > 0:
                incomplete_subjects.append({"label": subj.label, "images": missing})

        return incomplete_subjects

    def check_all_coregistration(self, outdir, subjs_labels=None, _from=None, _to=None, num_cpu=1, overwrite=False):

        if subjs_labels is None:
            subjs_labels = self.get_subjects_labels()

        if _from is None:
            _from = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        if _to is None:
            _to = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        self.run_subjects_methods("transform", "test_all_coregistration", [{"test_dir":outdir, "_from":_from, "_to":_to, "overwrite":overwrite}], subjs_labels, ncore=num_cpu)

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
            os.chdir(l_std);    os.system("slicesdir -p " + self._global.fsl_std_mni_2mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(l_std, "slicesdir"), sd_l_std)
            os.chdir(nl_std);   os.system("slicesdir -p " + self._global.fsl_std_mni_2mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(nl_std, "slicesdir"), sd_nl_std)

        if "std4" in _to:
            l_std4 = os.path.join(outdir, "lin", "std4");       nl_std4 = os.path.join(outdir, "nlin", "std4")
            sd_l_std4 = os.path.join(outdir, "slicesdir", "lin_std4");  os.makedirs(sd_l_std4, exist_ok=True)
            sd_nl_std4 = os.path.join(outdir, "slicesdir", "nlin_std4");os.makedirs(sd_nl_std4, exist_ok=True)
            os.chdir(l_std4);   os.system("slicesdir -p " + self._global.fsl_std_mni_4mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(l_std4, "slicesdir"), sd_l_std4)
            os.chdir(nl_std4);  os.system("slicesdir -p " + self._global.fsl_std_mni_4mm_brain + " ./*.nii.gz");  shutil.move(os.path.join(nl_std4, "slicesdir"), sd_nl_std4)

        if "t2" in _to:
            l_t2 = os.path.join(outdir, "lin", "t2");       nl_t2 = os.path.join(outdir, "nlin", "t2")
            sd_l_t2 = os.path.join(outdir, "slicesdir", "lin_t2");      os.makedirs(sd_l_t2, exist_ok=True)
            sd_nl_t2 = os.path.join(outdir, "slicesdir", "nlin_t2");    os.makedirs(sd_nl_t2, exist_ok=True)
            os.chdir(l_t2);     os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(l_t2, "slicesdir"), sd_l_t2)
            os.chdir(nl_t2);    os.system("slicesdir ./*.nii.gz");  shutil.move(os.path.join(nl_t2, "slicesdir"), sd_nl_t2)

    # create a folder where it copies the brain extracted from BET, FreeSurfer and SPM
    def compare_brain_extraction(self, outdir, list_subj_label=None):

        if list_subj_label is None or list_subj_label == "":

            if len(self.subjects) == 0:
                print("ERROR in compare_brain_extraction: no subjects are loaded and input subjects list label is empty")
                return
            else:
                subjs = self.subjects
        else:
            subjs = self.get_subjects_labels(list_subj_label)

        os.makedirs(outdir, exist_ok=True)

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

            if replaceOrig is False:
                imcp(subj.t1_data, subj.t1_data + "_old_origin")

            niifile = os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")

            if os.path.exists(niifile) is True and overwrite is False:
                print("skipping prepare_mpr_for_setorigin1 for subj " + subj.label)
                continue

            gunzip(subj.t1_data + ".nii.gz", niifile)
            print("unzipped " + subj.label + " mri")

    def prepare_mpr_for_setorigin2(self, group_label, sess_id=1):

        subjects = self.load_subjects(group_label, sess_id)
        for subj in subjects:
            niifile = os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")
            imrm([subj.t1_data + ".nii.gz"])
            compress(niifile, subj.t1_data + ".nii.gz")
            imrm([niifile])
            print("zipped " + subj.label + " mri")

    # ==================================================================================================================
    # GET SUBJECTS DATA
    # ==================================================================================================================
    # returns a matrix (values x subjects) containing values of the requested columns of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_columns(self, columns_list, subjects_label, sort=False, data=None):

        subj_list = self.get_subjects_labels(subjects_label)
        valid_data = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_columns(columns_list, subj_list, sort)
        else:
            return None

    # returns a tuple with two vectors[nsubj] (filtered by subj labels) of the requested column
    # - [values]
    # - [labels]
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column(self, column, subjects_label, sort=False, data=None):

        subj_list = self.get_subjects_labels(subjects_label)
        valid_data = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column(column, subj_list, sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column_by_value(self, column, value, operation="=", subjects_label=None, sort=False, data=None):

        subj_list = self.get_subjects_labels(subjects_label)
        valid_data = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_by_value(column, value, "=", subj_list, sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    # def get_filtered_column_by_value(self, column, value, operation="=", subjects_label=None, data=None):
    def get_filtered_subj_dict_column_within_values(self, column, value1, value2, operation="<>", subjects_label=None,
                                                    sort=False, data=None):

        subj_list = self.get_subjects_labels(subjects_label)
        valid_data = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_within_values(column, value1, value2, operation, subj_list, sort)
        else:
            return None

    # validate data dictionary. if param is none -> takes it from self.data
    #                           otherwise try to load it
    def validate_data(self, data=None):

        if data is None:
            if bool(self.data):
                return self.data
            else:
                print("ERROR in get_filtered_columns: given data param (" + str(
                    data) + ") is neither a dict nor a string")
                return None
        else:
            if isinstance(data, SubjectsDataDict):
                return data
            elif isinstance(data, str):
                if os.path.exists(data) is True:
                    return SubjectsDataDict(data)
                else:
                    print("ERROR in get_filtered_columns: given data param (" + str(
                        data) + ") is string that does not point to a valid file to load")
                    return None
            else:
                print("ERROR in get_filtered_columns: given data param (" + str(
                    data) + ") is neither a dict nor a string")
                return None

    # returns out_batch_job
    def create_batch_files(self, templfile_noext, seq, prefix=""):

        if prefix != "":
            prefix = prefix + "_"

        input_batch_name = ntpath.basename(templfile_noext)

        # set dirs
        spm_script_dir = os.path.join(self.script_dir, seq, "spm")
        out_batch_dir = os.path.join(spm_script_dir, "batch")

        os.makedirs(out_batch_dir, exist_ok=True)

        in_batch_start = os.path.join(self._global.spm_templates_dir, "spm_job_start.m")

        if os.path.exists(templfile_noext) is True:
            in_batch_job = templfile_noext
        else:
            in_batch_job = os.path.join(self._global.spm_templates_dir, templfile_noext + "_job.m")

        out_batch_start = os.path.join(out_batch_dir, prefix + "create_" + input_batch_name + "_start.m")
        out_batch_job = os.path.join(out_batch_dir, prefix + "create_" + input_batch_name + ".m")

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
    def run_subjects_methods(self, method_type, method_name, kwparams, ncore=1, subj_labels=None):

        if method_type != "" and method_type != "mpr" and method_type != "dti" and method_type != "epi" and method_type != "transform":
            print("ERROR in run_subjects_methods: the method type does not correspond to any of the allowed values (\"\", mpr, epi, dti, transform")
            return

        # check subjects
        if subj_labels is None:
            subj_labels = self.get_loaded_subjects_labels()
        else:
            if isinstance(subj_labels, list) is False:
                print("ERROR in run_subjects_methods: the given subj_labels param is not a list")
                return
            else:
                if isinstance(subj_labels[0], str) is False:
                    print("ERROR in run_subjects_methods: the given subj_labels param is not a string list, first value is: " + str(subj_labels[0]))
                    return

        nsubj = len(subj_labels)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        # check number of NECESSARY (without a default value) method params
        subj = self.get_subject_by_label(subj_labels[0])    # subj appear unused, but is instead used in the eval()
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
            subjects[curr_block].append(subj_labels[proc])

            proc4block = proc4block + 1
            if proc4block == ncore:
                curr_block = curr_block + 1
                proc4block = 0

        for bl in range(numblocks):
            threads = []

            for s in range(len(subjects[bl])):

                subj = self.get_subject_by_label(subjects[bl][s])

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
