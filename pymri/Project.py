import os
import json
import math
from threading import Thread

from pymri.Subject import Subject

class Project:

    def __init__(self, dir, globaldata, hasT1=True, hasRS=False, hasDTI=False, hasT2=False):

        self.dir                    = dir
        self.label                  = os.path.basename(self.dir)

        self.name                   = os.path.basename(self.dir)
        self.subjects_dir           = os.path.join(self.dir, "subjects")
        self.group_analysis_dir     = os.path.join(self.dir, "group_analysis")
        self.script_dir             = os.path.join(self.dir, "script")

        self.melodic_templates_dir  = os.path.join(self.group_analysis_dir, "melodic", "group_templates")
        self.melodic_dr_dir         = os.path.join(self.group_analysis_dir, "melodic", "dr")

        self.sbfc_dir               = os.path.join(self.group_analysis_dir, "sbfc")

        self.globaldata         = globaldata

        self.subjects               = []
        self.nsubj                  = -1

        self.hasT1                  = hasT1
        self.hasRS                  = hasRS
        self.hasDTI                 = hasDTI
        self.hasT1                  = hasT2

        # load all possible subjects list into self.subjects_lists
        with open(os.path.join(self.dir, "subjects_lists.json")) as json_file:
            self.subjects_lists = json.load(json_file)

    # retrieve a specific list of subjects
    def get_list_by_label(self, label):
        for subj in self.subjects_lists["subjects"]:
            if subj["label"] == label:
                return subj["list"]

    # load a list of subjects
    def load_subjects(self, list_label, sess_id=1):

        subjects = self.get_list_by_label(list_label)

        self.subjects = []
        for subj in subjects:
            self.subjects.append(Subject(subj, sess_id, self))

        self.nsubj = len(self.subjects)
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

    def anatomical_processing(self, subjects_list_label=None, numthread=1):

        if subjects_list_label is not None:
            self.load_subjects(subjects_list_label)

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

        if subj_labels is None:
            subj_labels = self.get_subjects_labels()

        nsubj       = len(subj_labels)
        nprocesses  = len(kwparams)

        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        if nsubj > 1 and nprocesses == 1:
            kwparams = [kwparams[0]] * nsubj        # duplicate the first kwparams up to given subj number
        else:
            if len(kwparams) != nsubj:
                print("ERROR in run_subject_method: given params list length differs from subjects list")
                return

        numblocks = math.ceil(nprocesses/nthread)

        subjects    = []
        processes   = []

        for p in range(numblocks):
            subjects.append([])
            processes.append([])

        proc4block = 0
        curr_block = 0
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
                    process = Thread(target=method, kwargs=kwparams[s])
                    process.start()
                    threads.append(process)

            for process in threads:
                process.join()

            print("completed block " + str(bl) + " with processes: " + str(subjects[bl]))




