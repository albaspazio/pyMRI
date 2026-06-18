from __future__ import annotations

import json
import math
import ntpath
import os
import shutil
from copy import deepcopy
from inspect import signature
from shutil import copyfile
from threading import Thread

from typing import List, Tuple, Any

from Global import Global
from .Project import Project
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from myutility.list import is_list_of
from subject.Subject import Subject
from data.SIDList import SIDList
from myutility.exceptions import SubjectListException, DataFileException, SubjectExistException
from myutility.images.Image import Image
from myutility.fileutilities import sed_inplace, remove_ext


class MRIProject(Project):

    subjects: List[Subject] = []

    def __init__(self, folder: str, globaldata: Global, data: str | SubjectsData = "data.xlsx"):
        """
        Initialize an MRIProject instance.

        Parameters
        ----------
        folder : str
            The path to the project folder.
        globaldata : Global
            The global data instance.
        data : str | SubjectsData, optional
            The path to the data file or a SubjectsData instance.
        """
        if not os.path.exists(folder):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.globaldata = globaldata

        # MRI-specific filesystem layout
        self.subjects_dir       = os.path.join(folder, "subjects")
        self.group_analysis_dir = os.path.join(folder, "group_analysis")
        self.script_dir         = os.path.join(globaldata.project_scripts_dir, os.path.basename(folder))

        self.glm_template_dir   = os.path.join(self.script_dir, "glm", "templates")
        self.group_glm_dir      = os.path.join(self.group_analysis_dir, "glm_models")

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

        self.hasT1  = False
        self.hasRS  = False
        self.hasDTI = False
        self.hasT2  = False

        # subjects_lists.json lives in script_dir for MRI projects (outside the project folder)
        # set it before super().__init__ reads it
        self.subjects_lists_file = os.path.join(self.script_dir, "subjects_lists.json")
        # data file is searched in script_dir for MRI projects
        self._data_search_dir = self.script_dir

        super().__init__(folder, data)

    # ==================================================================================================================
    # region PROPERTIES

    @property
    def existing_subjects(self) -> List[Subject]:
        subjects = []
        subj_labels = [f for f in os.listdir(self.subjects_dir) if os.path.isdir(os.path.join(self.subjects_dir, f))]
        for slab in subj_labels:
            search_folder = os.path.join(self.subjects_dir, slab)
            sessions = [int(f[1:]) for f in os.listdir(search_folder) if os.path.isdir(os.path.join(search_folder, f))]
            for sess in sessions:
                subjects.append(Subject(slab, self, sess))
        return subjects

    @property
    def subjects_labels(self) -> List[str]:
        if len(self.subjects) > 0:
            return list(set([subj.label for subj in self.subjects]))
        else:
            return []

    @property
    def nsubj(self) -> int:
        return len(self.subjects)

    # endregion

    # ==================================================================================================================
    # region LOAD / GET SUBJECTS

    def load_subjects(self, group_or_subjlabels: str | List[str], sess_ids: List[int] = None, must_exist: bool = True) -> List[Subject]:
        """
        Create and optionally store a list of Subject based on a group label or subject labels.

        Parameters
        ----------
        group_or_subjlabels : str or list
        sess_ids : List[int], optional
        must_exist : bool, optional
            If True, stores result in self.subjects and raises on missing subjects.
        """
        try:
            subjects = self.get_subjects(group_or_subjlabels, sess_ids, must_exist)
        except SubjectListException as e:
            raise SubjectListException("Error in MRIProject.load_subjects", e.param)

        if must_exist:
            self.subjects = subjects

        return subjects

    def get_subject_session(self, subj_label: str, sess: int = 1, must_exist: bool = True) -> Subject:
        """
        Get an independent Subject instance for the given label/session.
        """
        if must_exist:
            for subj in self.subjects:
                if subj.label == subj_label:
                    if subj.sessid == sess:
                        return deepcopy(subj)
                    else:
                        return subj.set_properties(sess, rollback=True)
            raise SubjectExistException("Error in MRIProject.get_subject: given subject (" + subj_label + " does not exist")
        else:
            return Subject(subj_label, self, sess)

    def get_subject_available_sessions(self, subj_lab: str, error_if_empty: bool = True) -> List[int]:
        """
        Returns the list of available sessions for a given subject.
        """
        search_folder = os.path.join(self.subjects_dir, subj_lab)
        sessions = [int(f[1:]) for f in os.listdir(search_folder) if os.path.isdir(os.path.join(search_folder, f))]

        if len(sessions) > 0:
            return sessions
        else:
            if error_if_empty:
                raise SubjectExistException("MRIProject.get_subject_available_sessions: given subj " + subj_lab + " does not have any session")
            else:
                return []

    def get_subjects(self, group_or_subjlabels: str | List[str] = None, sess_ids: List[int] = None, must_exist: bool = False) -> List[Subject]:
        """
        Returns subjects based on a group label or a list of subject labels.
        """
        subj_labels = self.get_subjects_labels(group_or_subjlabels)

        subjects = []
        for subj_lab in subj_labels:
            if sess_ids is None:
                sessions = self.get_subject_available_sessions(subj_lab)
            else:
                sessions = sess_ids

            for sess_id in sessions:
                subj = Subject(subj_lab, self, sess_id)
                if not subj.exist and must_exist is True:
                    raise SubjectExistException("Error in MRIProject.get_subjects: requested subject (" + subj_lab + " | " + str(sess_id) + " ) does not exist")
                elif subj.exist or (subj.exist is False and must_exist is False):
                    subjects.append(subj)
        return subjects

    def get_subject(self, subjlabel: str, sess_id: int = 1, must_exist: bool = False) -> Subject:
        return self.get_subjects([subjlabel], [sess_id], must_exist)[0]

    def get_subjects_labels(self, grlab_subjlabs_subjs: str | List[str] | List[Subject] = None) -> List[str]:
        """
        Extends base get_subjects_labels to also accept a List[Subject].
        """
        if isinstance(grlab_subjlabs_subjs, list) and len(grlab_subjlabs_subjs) > 0 and isinstance(grlab_subjlabs_subjs[0], Subject):
            return [subj.label for subj in grlab_subjlabs_subjs]
        return super().get_subjects_labels(grlab_subjlabs_subjs)

    # endregion

    # ==================================================================================================================
    # region SID <-> Subject bridges

    def subjects2sids(self, subjects: List[Subject] = None) -> SIDList:
        """
        Returns a SIDList corresponding to the given list of subjects.
        """
        subjects = self.validate_subjects(subjects)
        sids = [self.data.get_sid(subj.label, subj.sessid) for subj in subjects]
        return SIDList(sids)

    def sids2subjects(self, sids: SIDList = None) -> List[Subject]:
        """
        Returns a list of Subject instances corresponding to the given SIDList.
        """
        return [Subject(sid.label, self, sid.session) for sid in sids]

    # endregion

    # ==================================================================================================================
    # region VALIDATION

    def are_subjects_valid(self, subjects: List[Subject]) -> bool:
        for subj in subjects:
            if not subj.exist:
                return False
        return True

    def validate_subjects(self, subjs: List[Subject] = None) -> List[Subject]:
        if subjs is None:
            if self.nsubj > 0:
                return self.subjects
            else:
                raise SubjectExistException("ERROR in MRIProject.validate_subjects: given subjs param (" + str(subjs) + ") is None and project's subjects is empty")
        else:
            if is_list_of(subjs, Subject) and len(subjs) > 0:
                return subjs
            else:
                raise SubjectExistException("ERROR in MRIProject.validate_subjects: given subjs param (" + str(subjs) + ") is not a Subject list or is empty")

    # endregion

    # ==================================================================================================================
    # region DATA (override query methods to accept List[Subject])

    def get_subjects_values_by_cols(self, grlab_subjlabs_subjs: str | List[str] | List[Subject], columns_list: List[str],
                                    sess_ids: List[int] = None, select_conds: List[FilterValues] = None,
                                    data: str | SubjectsData = None, demean_flags: List[bool] | bool | None = None,
                                    ndecim: int = 4) -> Tuple[List[List[Any]], List[str], List[int]]:
        valid_data = self.validate_data(data)

        if not is_list_of(grlab_subjlabs_subjs, Subject):
            subjects = self.get_subjects(grlab_subjlabs_subjs, sess_ids)
        else:
            subjects = self.validate_subjects(grlab_subjlabs_subjs)

        sids: SIDList = valid_data.filter_sids(select_conds, sids=self.subjects2sids(subjects))

        return valid_data.get_subjects_values_by_cols(sids, columns_list, demean_flags=demean_flags, ndecim=ndecim), sids.labels, sids.sessions

    def get_filtered_column(self, grlab_subjlabs_subjs: str | List[str] | List[Subject], column,
                            sess_ids: List[int] = None, select_conds: List[FilterValues] = None,
                            data: str | SubjectsData = None, sort: bool = False,
                            demean_flag: bool = False, ndecim: int = 4) -> Tuple[list, List[str], List[int]]:
        valid_data = self.validate_data(data)

        if not is_list_of(grlab_subjlabs_subjs, Subject):
            subjects = self.get_subjects(grlab_subjlabs_subjs, sess_ids)
        else:
            subjects = self.validate_subjects(grlab_subjlabs_subjs)

        sids: SIDList = valid_data.filter_sids(select_conds, sids=self.subjects2sids(subjects))

        return valid_data.get_subjects_column(sids, column, sort=sort, demean=demean_flag, ndecim=ndecim), sids.labels, sids.sessions

    # endregion

    # ==================================================================================================================
    # region MRI CHECKS

    def check_subjects_original_images(self):
        incomplete_subjects = []
        for subj in self.subjects:
            missing = subj.check_images(self.hasT1, self.hasRS, self.hasDTI, self.hasT2)
            if len(missing) > 0:
                incomplete_subjects.append({"label": subj.label, "images": missing})
        return incomplete_subjects

    def hasSeq(self, seq_type, subjects: List[Subject] = None, images_labels: List[str] = None):
        subjects        = self.validate_subjects(subjects)
        invalid_subjs   = ""
        for subj in subjects:
            if not subj.hasSeq(seq_type, images_labels):
                invalid_subjs = invalid_subjs + subj.label + "\n"

        if len(invalid_subjs) > 0:
            print("ERROR.... the following subjects does not have the given sequence " + seq_type + " :\n" + invalid_subjs)
        else:
            print("OK....... " + seq_type + " analysis can be run")

        return invalid_subjs

    def can_run_analysis(self, analysis_type, analysis_params: str | List[str] = None, subjects: List[Subject] = None):
        subjects        = self.validate_subjects(subjects)
        invalid_subjs   = ""
        for subj in subjects:
            if not subj.can_run_analysis(analysis_type, analysis_params):
                invalid_subjs = invalid_subjs + subj.label + "\n"

        if len(invalid_subjs) > 0:
            print("ERROR.... the following subjects prevent the completion of the " + analysis_type + " analysis:\n" + invalid_subjs)
        else:
            print("OK....... " + analysis_type + " analysis can be run")

        return invalid_subjs

    def _process_slicesdir(self, outdir: str, image_label: str, slicesdir_args: str = ""):
        """
        Helper to process slicesdir for lin/nlin coregistration directories.

        Args:
            outdir: Base output directory
            image_label: Image type (e.g., 'hr', 'dti', 'rs', 't2', 'std', 'std4')
            slicesdir_args: Optional arguments for slicesdir command (e.g., "-p /path/to/brain")
        """
        l_dir = os.path.join(outdir, "lin", image_label)
        nl_dir = os.path.join(outdir, "nlin", image_label)
        sd_l_dir = os.path.join(outdir, "slicesdir", f"lin_{image_label}")
        sd_nl_dir = os.path.join(outdir, "slicesdir", f"nlin_{image_label}")

        os.makedirs(sd_l_dir, exist_ok=True)
        os.makedirs(sd_nl_dir, exist_ok=True)

        olddir = os.getcwd()
        try:
            for src_dir, sd_dir in [(l_dir, sd_l_dir), (nl_dir, sd_nl_dir)]:
                os.chdir(src_dir)
                os.system(f"slicesdir {slicesdir_args} ./*.nii.gz")
                shutil.move(os.path.join(src_dir, "slicesdir"), sd_dir)
        finally:
            os.chdir(olddir)

    def check_all_coregistration(self, outdir: str, subjects: List[Subject] = None, _from: List[str] = None, _to: List[str] = None, fmri_labels: List[str] = None, num_cpu: int = 1, overwrite: bool = False):
        subjects = self.validate_subjects(subjects)

        if _from is None:
            _from = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]
        if _to is None:
            _to = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        self.run_subjects_methods("transform", "test_all_coregistration", [{"test_dir": outdir, "_from": _from, "_to": _to, "fmri_labels": fmri_labels, "overwrite": overwrite}], ncore=num_cpu, subjects=subjects)

        # Process slicesdir for each image type
        for img_type in _to:
            if img_type == "std":
                self._process_slicesdir(outdir, img_type, f"-p {self.globaldata.fsl_std_mni_2mm_brain}")
            elif img_type == "std4":
                self._process_slicesdir(outdir, img_type, f"-p {self.globaldata.fsl_std_mni_4mm_brain}")
            else:
                self._process_slicesdir(outdir, img_type)

    def compare_brain_extraction(self, outdir: str, subjects: List[Subject] = None, num_cpu=1):
        subjects = self.validate_subjects(subjects)
        os.makedirs(outdir, exist_ok=True)
        self.run_subjects_methods("mpr", "compare_brain_extraction", [{"tempdir": outdir}], ncore=num_cpu, subjs=subjects)
        olddir = os.getcwd()
        os.chdir(outdir)
        os.system("slicesdir ./*.nii.gz")
        os.chdir(olddir)

    def prepare_mpr_for_setorigin1(self, subjects: List[Subject] = None, replaceOrig: bool = False, overwrite: bool = False):
        subjects = self.validate_subjects(subjects)
        for subj in subjects:
            if not replaceOrig:
                subj.t1_data.cp(subj.t1_data + "_old_origin")

            niifile = Image(str(os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")))

            if niifile.uexist and not overwrite:
                print("skipping prepare_mpr_for_setorigin1 for subj " + subj.label)
                continue

            subj.t1_data.cpath.unzip(niifile, replace=True)
            print("unzipped " + subj.label + " mri")

    def prepare_mpr_for_setorigin2(self, subjects: List[Subject] = None):
        subjects = self.validate_subjects(subjects)
        for subj in subjects:
            niifile = Image(str(os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")))
            subj.t1_data.cpath.rm()
            niifile.compress(subj.t1_data.cpath)
            niifile.rm()
            print("zipped " + subj.label + " mri")

    # endregion

    # ==================================================================================================================
    # region ACCESSORY

    def add_icv_to_data(self, subjects: List[Subject] = None, updatefile: bool = False, df=None):
        subjects = self.validate_subjects(subjects)
        icvs = self.get_subjects_icv(subjects)
        self.data.add_column("icv", icvs, self.subjects2sids(subjects), df)

    def get_subjects_icv(self, subjects: List[Subject]) -> List[float]:
        subjects        = self.validate_subjects(subjects)
        icv_scores      = []
        missing_files   = []
        for subj in subjects:
            try:
                with open(subj.t1_spm_icv_file) as fp:
                    fp.readline()
                    line    = fp.readline().rstrip()
                    values  = line.split(',')
                    icv_scores.append(round(float(values[1]) + float(values[2]) + float(values[3]), 4))
            except OSError:
                missing_files.append(subj.t1_spm_icv_file)

        if len(missing_files) > 0:
            raise DataFileException("Error in MRIProject.get_subjects_icv: icv files of some subject/session are missing", str(missing_files))
        return icv_scores

    def create_subjects_lists(self, group_label=None):
        if group_label is None:
            subjs = self.subjects
        else:
            subjs = self.load_subjects(group_label)

        lists = [{"label": "auto_t1", "list": []}, {"label": "auto_ct", "list": []}, {"label": "auto_dti", "list": []}, {"label": "auto_rs", "list": []}]

        for s in subjs:
            if s.hasT1:
                lists[0]["list"].append(s.label)
            if s.hasCT:
                lists[1]["list"].append(s.label)
            if s.hasDTI:
                lists[2]["list"].append(s.label)
            if s.hasRS:
                lists[3]["list"].append(s.label)

        with open(self.subjects_lists_file, mode="r") as json_file:
            subjects        = json.load(json_file)
            subjects_lists  = subjects["subjects"]

        subjects_lists = [d for d in subjects_lists if d.get("label") not in ["auto_t1", "auto_ct", "auto_dti", "auto_rs"]]
        subjects_lists = subjects_lists + lists
        subjects["subjects"] = subjects_lists

        with open(self.subjects_lists_file, mode="w") as json_file:
            json.dump(subjects, json_file, indent=4)

    # endregion

    # ==================================================================================================================
    # region BATCHING

    def create_batch_files(self, out_batch_name, seq):
        out_batch_dir = os.path.join(self.script_dir, seq, "spm", "batch")
        os.makedirs(out_batch_dir, exist_ok=True)

        in_batch_start  = os.path.join(self.globaldata.spm_templates_dir, "spm_job_start.m")
        out_batch_start = os.path.join(out_batch_dir, "create_" + out_batch_name + "_start.m")
        out_batch_job   = os.path.join(out_batch_dir, "create_" + out_batch_name + ".m")

        open(out_batch_job, 'w', encoding='utf-8').close()

        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, "X", "1")
        sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

        return out_batch_job, out_batch_start

    def adapt_batch_files(self, templfile_noext, seq, prefix: str = "", postfix: str = ""):
        if prefix != "":
            prefix = prefix + "_"
        if postfix != "":
            postfix = "_" + postfix

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

        copyfile(in_batch_job, out_batch_job)
        copyfile(in_batch_start, out_batch_start)
        sed_inplace(out_batch_start, "X", "1")
        sed_inplace(out_batch_start, "JOB_LIST", "\'" + out_batch_job + "\'")

        return out_batch_job, out_batch_start

    # endregion

    # ==================================================================================================================
    # region MULTICORE PROCESSING

    def run_subjects_methods(self, method_type, method_name, kwparams, ncore=1, subjects: List[Subject] = None, must_exist: bool = True):
        subjects = self.validate_subjects(subjects)

        if method_type not in ("", "mpr", "epi", "dti", "transform"):
            raise Exception("Invalid method type: " + method_type + " Method type must be an empty string, 'mpr', 'epi', 'dti', or 'transform'.")
        print("run_subjects_methods: validating given subjects")

        nsubj = len(subjects)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        subj = subjects[0]
        if method_type == "":
            method = eval("subj." + method_name)
        else:
            method = eval("subj." + method_type + "." + method_name)
        sig     = signature(method)
        nparams = len(sig.parameters)
        for p in sig.parameters:
            if sig.parameters[p].default is not None:
                nparams = nparams - 1

        if len(kwparams) == 0:
            kwparams = [None] * nsubj

        nprocesses = len(kwparams)

        if nsubj > 1 and nprocesses == 1:
            kwparams   = [kwparams[0]] * nsubj
            nprocesses = nsubj
        else:
            if nprocesses != nsubj:
                print("ERROR in run_subject_method: given params list length differs from subjects list")
                return

        numblocks = math.ceil(nprocesses / ncore)

        subjs: List[List[Subject]] = []
        processes = []

        for p in range(numblocks):
            subjs.append([])
            processes.append([])

        proc4block = 0
        curr_block = 0

        for proc in range(nprocesses):
            processes[curr_block].append(kwparams[proc])
            subjs[curr_block].append(subjects[proc])

            proc4block = proc4block + 1
            if proc4block == ncore:
                curr_block = curr_block + 1
                proc4block = 0

        for bl in range(numblocks):
            threads = []
            subj_labels = []
            for s in range(len(subjs[bl])):
                subj = subjs[bl][s]
                subj_labels.append(subj.label)
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

            print("completed block " + str(bl) + " with processes: " + str(subj_labels))

    # endregion
