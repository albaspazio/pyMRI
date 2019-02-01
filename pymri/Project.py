import os
import json
from pymri.Subject import Subject

class Project:

    def __init__(self, dir, globaldata, hasT1=True, hasRS=False, hasDTI=False, hasT2=False):

        self.dir                    = dir
        self.label                  = os.path.basename(self.dir)

        self.name                   = os.path.basename(self.dir)
        self.subjects_dir           = os.path.join(self.dir, "subjects")
        self.group_analysis_dir     = os.path.join(self.dir, "group_analysis")

        self.melodic_templates_dir  = os.path.join(self.group_analysis_dir, "melodic", "group_templates")
        self.melodic_dr_dir         = os.path.join(self.group_analysis_dir, "melodic", "dr")

        self.globaldata         = globaldata

        self.subjects           = []

        self.hasT1              = hasT1
        self.hasRS              = hasRS
        self.hasDTI             = hasDTI
        self.hasT1              = hasT2

        with open(os.path.join(self.dir, "subjects_lists.json")) as json_file:
            self.subjects_lists = json.load(json_file)

    def get_list_by_label(self, label):
        for subj in self.subjects_lists["subjects"]:
            if subj["label"] == label:
                return subj["list"]

    def load_subjects(self, list_label, sess_id=1):
        subjects = self.get_list_by_label(list_label)

        self.subjects = []

        for subj in subjects:
            self.subjects.append(Subject(subj, sess_id, self))

        return self.subjects

    def get_subjects_labels(self):
        subjs = []
        for subj in self.subjects:
            subjs.append(subj.label)
        return subjs

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




