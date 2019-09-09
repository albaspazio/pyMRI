import os
import json
import math
from threading import Thread
from inspect import signature

from Subject import Subject

class Project:

    def __init__(self, dir, globaldata, hasT1=True, hasRS=False, hasDTI=False, hasT2=False):

        if not os.path.exists(dir):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.dir                    = dir
        self.label                  = os.path.basename(self.dir)

        self.name                   = os.path.basename(self.dir)
        self.subjects_dir           = os.path.join(self.dir, "subjects")
        self.group_analysis_dir     = os.path.join(self.dir, "group_analysis")
        self.script_dir             = os.path.join(self.dir, "script")

        self.melodic_templates_dir  = os.path.join(self.group_analysis_dir, "melodic", "group_templates")
        self.melodic_dr_dir         = os.path.join(self.group_analysis_dir, "melodic", "dr")

        self.sbfc_dir               = os.path.join(self.group_analysis_dir, "sbfc")
        self.mpr_dir                = os.path.join(self.group_analysis_dir, "mpr")

        self.vbm_dir                = os.path.join(self.mpr_dir, "vbm")

        self.globaldata         = globaldata

        self.subjects               = []
        self.nsubj                  = -1

        self.hasT1                  = hasT1
        self.hasRS                  = hasRS
        self.hasDTI                 = hasDTI
        self.hasT2                  = hasT2

        # load all possible subjects list into self.subjects_lists
        with open(os.path.join(self.script_dir, "subjects_lists.json")) as json_file:
            self.subjects_lists = json.load(json_file)

    # retrieve a specific list of subjects
    def get_list_by_label(self, label):
        for subj in self.subjects_lists["subjects"]:
            if subj["label"] == label:
                return subj["list"]

    def get_subjects(self, list_label, sess_id=1):

        subjects = self.get_list_by_label(list_label)
        subjs = []
        for subj in subjects:
            subjs.append(Subject(subj, sess_id, self))

        return subjs

    # load a list of subjects
    def load_subjects(self, list_label, sess_id=1):

        self.subjects   = self.get_subjects(list_label, sess_id)
        self.nsubj      = len(self.subjects)
        return self.subjects

    # get the list of loaded subjects' label
    def get_subjects_labels(self):
        subjs = []
        for subj in self.subjects:
            subjs.append(subj.label)
        return subjs

    #
    def check_subjects_original_images(self):

        incomplete_subjects = []
        for subj in self.subjects["subjects"]:
            missing = subj.check_images(self.hasT1, self.hasRS, self.hasDTI, self.hasT2)
            if len(missing) > 0:
                incomplete_subjects.append({"label":subj.label, "images":missing})

        return incomplete_subjects

    # get subject with given label
    def get_subject_by_label(self, subj_label):
        for subj in self.subjects:
            if subj.label == subj_label:
                return subj
        return None

    def get_subjects_num(self):
        return len(self.subjects)

    # *kwparams is a list of kwparams. if len(kwparams)=1 & len(subj_labels) > 1 ...pass that same kwparams[0] to all subjects
    # if subj_labels is not given...use the loaded subjects
    def run_subjects_methods(self, method_name, kwparams, subj_labels=None, nthread=1):

        # check subjects
        if subj_labels is None:
            subj_labels = self.get_subjects_labels()
        nsubj       = len(subj_labels)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        # check number of NECESSARY (without a default value) method params
        subj    = self.get_subject_by_label(subj_labels[0])
        method  = eval("subj." + method_name)
        sig     = signature(method)
        nparams = len(sig.parameters)       # parameters that need a value
        for p in sig.parameters:
            if sig.parameters[p].default is not None:
                nparams = nparams - 1       # this param has a default value

        # if no params are given, create a nsubj list of None
        if len(kwparams) is 0:
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


        numblocks   = math.ceil(nprocesses/nthread)     # num of provessing blocks (threads)

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
                    method  = eval("subj." + method_name)
                    process = Thread(target=method, kwargs=processes[bl][s])
                    process.start()
                    threads.append(process)

            for process in threads:
                process.join()

            print("completed block " + str(bl) + " with processes: " + str(subjects[bl]))


    # create a folder where it copies the brain extracted from BET, FreeSurfer and SPM
    def compare_brain_extraction(self, tempdir, list_subj_label=None):

        if list_subj_label is None or list_subj_label == "":

            if len(self.subjects) == 0:
                print("ERROR in compare_brain_extraction: no subjects are loaded and input subjects list label is empty")
                return
            else:
                subjs = self.subjects
        else:
            subjs = self.get_list_by_label(list_subj_label)

        os.makedirs(tempdir,exist_ok=True)

        for subj in subjs:
            subj.mpr_compare_brain_extraction(tempdir)


        # curr_dir = os.getcwd()
        # os.chdir(tempdir)
        # rrun("slicesdir *")
        # os.chdir(curr_dir)

