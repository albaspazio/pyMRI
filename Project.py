import os
import json
import math
from threading import Thread
from inspect import signature
from copy import deepcopy

from myfsl.utils.run import rrun
from subject.Subject import Subject
from utility.SubjectsDataDict import SubjectsDataDict
from utility.images import imcp, imrm
from utility.utilities import gunzip, compress
from utility import import_data_file


class Project:

    def __init__(self, folder, globaldata, data="data.dat"):

        if not os.path.exists(folder):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.dir                    = folder
        self.label                  = os.path.basename(self.dir)

        self.name                   = os.path.basename(self.dir)
        self.subjects_dir           = os.path.join(self.dir, "subjects")
        self.group_analysis_dir     = os.path.join(self.dir, "group_analysis")
        self.script_dir             = os.path.join(self.dir, "script")

        self.glm_template_dir       = os.path.join(self.script_dir, "glm", "templates")

        self.melodic_templates_dir  = os.path.join(self.group_analysis_dir, "resting", "group_templates")
        self.melodic_dr_dir         = os.path.join(self.group_analysis_dir, "resting", "dr")

        self.sbfc_dir               = os.path.join(self.group_analysis_dir, "sbfc")
        self.mpr_dir                = os.path.join(self.group_analysis_dir, "mpr")

        self.vbm_dir                = os.path.join(self.mpr_dir, "vbm")

        self.tbss_dir               = os.path.join(self.group_analysis_dir, "tbss")

        self._global                = globaldata

        self.subjects               = []
        self.nsubj                  = -1

        self.hasT1                  = False
        self.hasRS                  = False
        self.hasDTI                 = False
        self.hasT2                  = False

        # load all available subjects list into self.subjects_lists
        with open(os.path.join(self.script_dir, "subjects_lists.json")) as json_file:
            self.subjects_lists = json.load(json_file)

        self.data_file  = ""
        self.data       = {}
        # load data file if exist
        if os.path.exists(data):
            self.data_file = data
        elif os.path.exists(os.path.join(self.script_dir, data)):
            self.data_file = os.path.join(self.script_dir, data)

        if self.data_file != "":
            self.data = SubjectsDataDict(self.data_file)    # import_data_file.tabbed_file_with_header2subj_dic(self.data_file)

    # ==================================================================================================================
    # GET SUBJECTS' INSTANCES
    # ==================================================================================================================
    # loads a list of subjects instances in self.subjects
    # returns this list
    def load_subjects(self, group_label, sess_id=1):

        self.subjects = self.get_subjects(group_label, sess_id)
        self.nsubj = len(self.subjects)
        return self.subjects

    # returns a list of subjects instances
    def get_subjects(self, group_label, sess_id=1):

        subjects = self.get_subjects_labels(group_label)
        subjs = []
        for subj in subjects:
            subjs.append(Subject(subj, sess_id, self))
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
                    return subj.set_file_system(sess, rollback=True)    # it returns a deepcopy of requested session
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
                incomplete_subjects.append({"label":subj.label, "images":missing})

        return incomplete_subjects

    def test_all_coregistration(self, subjects, outdir, num_cpu=1):

        kwparams = []
        for p in range(len(subjects)):
            kwparams.append({"outdir":outdir})
        self.run_subjects_methods("transform", "test_all_coregistration", kwparams, self.get_subjects_labels(), nthread=num_cpu)


        # rrun("slicesdir " + )

    # create a folder where it copies the brain extracted from BET, FreeSurfer and SPM
    def compare_brain_extraction(self, tempdir, list_subj_label=None):

        if list_subj_label is None or list_subj_label == "":

            if len(self.subjects) == 0:
                print("ERROR in compare_brain_extraction: no subjects are loaded and input subjects list label is empty")
                return
            else:
                subjs = self.subjects
        else:
            subjs = self.get_subjects_labels(list_subj_label)

        os.makedirs(tempdir, exist_ok=True)

        for subj in subjs:
            subj.compare_brain_extraction(tempdir)

    # prepare_mpr_for_setorigin1 and prepare_mpr_for_setorigin2 are to be used in conjunction
    # the former make a backup and unzip the original file,
    # the latter zip and clean up
    def prepare_mpr_for_setorigin1(self, group_label, sess_id=1, replaceOrig=False):
        subjects    = self.load_subjects(group_label, sess_id)
        for subj in subjects:

            if replaceOrig is False:
                imcp(subj.t1_data, subj.t1_data + "_old_origin")

            niifile = os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")
            gunzip(subj.t1_data + ".nii.gz", niifile)
            print("unzipped " + subj.label + " mri")

    def prepare_mpr_for_setorigin2(self, group_label, sess_id=1):

        subjects    = self.load_subjects(group_label, sess_id)
        for subj in subjects:

            niifile = os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")
            imrm([subj.t1_data + ".nii.gz"])
            compress(niifile, subj.t1_data + ".nii.gz")
            imrm([niifile])
            print("zipped " + subj.label + " mri")

    # works with already converted and renames images
    # - subj.t1_data
    # - t1_cat_dir
    def mpr_setorigin(self, group_label, sess_id=1, replaceOrig=False):
        subjects    = self.load_subjects(group_label, sess_id)
        for subj in subjects:

            if replaceOrig is False:
                imcp(subj.t1_data, subj.t1_data + "_old_origin")

            niifile = os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")
            gunzip(subj.t1_data + ".nii.gz", niifile)

            # call_matlab_function_noret("spm_display_image", [self._global.spm_functions_dir], "\'" + niifile + "\'", endengine=False)
            input("press any key to continue")

            imrm([subj.t1_data + ".nii.gz"])
            compress(niifile, subj.t1_data + ".nii.gz")
            imrm([niifile])

    # ==================================================================================================================
    # GET SUBJECTS DATA
    # ==================================================================================================================
    # returns a matrix (values x subjects) containing values of the requested columns of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_columns(self, columns_list, subjects_label, sort=False, data=None):

        subj_list   = self.get_subjects_labels(subjects_label)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_columns(columns_list, subj_list, sort)
        else:
            return None

    # returns a tuple with two vectors[nsubj] (filtered by subj labels) of the requested column
    # - [values]
    # - [labels]
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column(self, column, subjects_label, sort=False, data=None):

        subj_list   = self.get_subjects_labels(subjects_label)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column(column, subj_list, sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column_by_value(self, column, value, operation="=", subjects_label=None, sort=False, data=None):

        subj_list   = self.get_subjects_labels(subjects_label)
        valid_data  = self.validate_data(data)
        if valid_data is not None:
            return valid_data.get_filtered_column_by_value(column, value, "=", subj_list, sort)
        else:
            return None

    # returns a vector (nsubj) containing values of the requested column of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    # def get_filtered_column_by_value(self, column, value, operation="=", subjects_label=None, data=None):
    def get_filtered_subj_dict_column_within_values(self, column, value1, value2, operation="<>", subjects_label=None, sort=False, data=None):

        subj_list   = self.get_subjects_labels(subjects_label)
        valid_data  = self.validate_data(data)
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
                print("ERROR in get_filtered_columns: given data param (" + str(data) + ") is neither a dict nor a string")
                return None
        else:
            if isinstance(data, SubjectsDataDict):
                return data
            elif isinstance(data, str):
                if os.path.exists(data) is True:
                    return SubjectsDataDict(data)   #import_data_file.tabbed_file_with_header2subj_dic(data)
                else:
                    print("ERROR in get_filtered_columns: given data param (" + str(data) + ") is string that does not point to a valid file to load")
                    return None
            else:
                print("ERROR in get_filtered_columns: given data param (" + str(data) + ") is neither a dict nor a string")
                return None

    # ==================================================================================================================
    # MULTICORE PROCESSING
    # ==================================================================================================================
    # *kwparams is a list of kwparams. if len(kwparams)=1 & len(subj_labels) > 1 ...pass that same kwparams[0] to all subjects
    # if subj_labels is not given...use the loaded subjects
    def run_subjects_methods(self, method_type, method_name, kwparams, subj_labels=None, nthread=1):

        # check subjects
        if subj_labels is None:
            subj_labels = self.get_loaded_subjects_labels()
        nsubj       = len(subj_labels)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        # check number of NECESSARY (without a default value) method params
        subj    = self.get_subject_by_label(subj_labels[0])

        if method_type == "":
            method = eval("subj." + method_name)
        else:
            method = eval("subj." + method_type + "." + method_name)

        sig     = signature(method)
        nparams = len(sig.parameters)       # parameters that need a value
        for p in sig.parameters:
            if sig.parameters[p].default is not None:
                nparams = nparams - 1       # this param has a default value

        # if no params are given, create a nsubj list of None
        if len(kwparams) == 0:
            if nparams > 0:
                print("ERROR in run_subjects_methods: given params list is empty, while method needs " + str(nparams) + " params" )
                return
            else:
                kwparams = [None] * nsubj

        nprocesses  = len(kwparams)

        if nsubj > 1 and nprocesses == 1:
            kwparams    = [kwparams[0]] * nsubj        # duplicate the first kwparams up to given subj number
            nprocesses  = nsubj
        else:
            if nprocesses != nsubj:
                print("ERROR in run_subject_method: given params list length differs from subjects list")
                return
        # here nparams is surely == nsubj

        numblocks   = math.ceil(nprocesses/nthread)     # num of processing blocks (threads)

        subjects    = []
        processes   = []

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
            if proc4block == nthread:
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
