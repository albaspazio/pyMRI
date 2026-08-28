from __future__ import annotations

import json
import math
import ntpath
import os
import shutil
from inspect import signature
from shutil import copyfile
from threading import Thread
from typing import List

from data.SID import SID
from data.SubjectsData import SubjectsData
from myutility.exceptions import DataFileException, SubjectExistException
from myutility.fileutilities import sed_inplace, remove_ext
from myutility.images.Image import Image
from project.GlobalMRI import GlobalMRI
from subject.Subject import Subject
from subject.SubjectMRI import SubjectMRI
from subject.SubjectsList import SubjectsList
from .Project import Project


class ProjectMRI(Project):

    def __init__(self, folder: str, globaldata: 'GlobalMRI', data: str | SubjectsData = "data.xlsx", must_exist: bool = False, isBids: bool = False, bidsDerivatives: str | None = None):
        """
        Initialize an ProjectMRI instance.

        Parameters
        ----------
        folder : str
            The path to the project folder.
        globaldata : GlobalMRI
            The MRI global configuration instance (MUST be GlobalMRI, not generic Global).
        data : str | SubjectsData, optional
            The path to the data file or a SubjectsData instance.
        must_exist : bool, optional
            If True, emit UserWarning for subjects not present in filesystem.
            Default: False.
        isBids : bool, optional
            If True, filesystem follows BIDS standard (sub-XX/ses-YY/anat/, etc.).
            If False, uses legacy format (subjects/XX/sYY/mpr/, etc.).
            Default: False (legacy format for backward compatibility).
        bidsDerivatives : str | None, optional
            Path to derivatives directory. Only used if isBids=True.
            If None, assumes derivatives are at {folder}/../derivatives (sibling of raw).
            If a path is provided, uses that path as root for derivatives.
            Example: folder="/projects/myproject/raw", bidsDerivatives=None
                     → derivatives will be at "/projects/myproject/derivatives"
                     OR: bidsDerivatives="/data/derivs" → derivatives will be at "/data/derivs"
            Default: None.
        """
        if not os.path.exists(folder):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.globaldata = globaldata
        self.isBids = isBids
        
        # Resolve bidsDerivatives path
        if self.isBids and bidsDerivatives is None:
            # Default: derivatives at same level as raw (sibling folder)
            # If folder = "/projects/myproject/raw" → derivatives = "/projects/myproject/derivatives"
            parent_dir = os.path.dirname(folder)
            self.bidsDerivatives = os.path.join(parent_dir, "derivatives")
        else:
            self.bidsDerivatives = bidsDerivatives

        self.dir        = folder
        self.label      = os.path.basename(self.dir)
        self.name       = os.path.basename(self.dir)

        self.subjects_dir       = os.path.join(self.dir, "subjects")
        self.group_analysis_dir = os.path.join(self.dir, "group_analysis")
        self.script_dir         = os.path.join(globaldata.project_scripts_dir, self.name)

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
        
        # validate filesystem if requested
        if must_exist:
            self._validate_mri_filesystem()

    # ==================================================================================================================
    # region PROPERTIES

    @property
    def existing_subjects(self) -> SubjectsList:
        
        subjects = SubjectsList()
        subj_labels = [f for f in os.listdir(self.subjects_dir) if os.path.isdir(os.path.join(self.subjects_dir, f))]
        for slab in subj_labels:
            search_folder = os.path.join(self.subjects_dir, slab)
            sessions = [int(f[1:]) for f in os.listdir(search_folder) if os.path.isdir(os.path.join(search_folder, f))]
            for sess in sessions:
                subjects.append(Subject(slab, self, sess))
        return subjects


    # endregion

    # ==================================================================================================================
    # region LOAD / GET SUBJECTS

    def load_subjects(self, group_or_subjlabels: str | List[str], sess_ids: List[int]|None = None, must_exist: bool = True) -> SubjectsList:
        """
        DEPRECATED: Use get_subjects() instead. This method will be removed in a future version.
        
        This method is deprecated because subjects are now auto-loaded at project init
        via _build_subjects(). Use get_subjects() for the modern pattern.
        
        Modern patterns:
        - Single-project analysis: project.run_subjects_methods(..., subjects=project.get_subjects("group"))
        - Cross-project analysis: Manually build SubjectsList from multiple projects via .extend()
        - All subjects: project.run_subjects_methods(...) without subjects param (uses project.subjects)

        Parameters
        ----------
        group_or_subjlabels : str or list
            Group label or list of subject labels.
        sess_ids : List[int], optional
            Session IDs to retrieve.
        must_exist : bool, optional
            If True, raises on missing subjects. Default: True.
        
        Returns
        -------
        SubjectsList
            List of subjects matching the criteria.
        """
        import warnings
        warnings.warn(
            "load_subjects() is deprecated. Use get_subjects() instead.",
            DeprecationWarning, stacklevel=2
        )
        
        return self.get_subjects(group_or_subjlabels, sess_ids, must_exist)

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
                raise SubjectExistException("ProjectMRI.get_subject_available_sessions: given subj " + subj_lab + " does not have any session")
            else:
                return []

    #override
    def _create_subject(self, sid:SID) -> Subject:
        """
        Factory override: create SubjectMRI with sid immediately assigned.

        Inherited by parent _build_subjects(), so all subject creation goes through here.
        Follows the same contract as Project._create_subject(): sid is assigned immediately.

        Parameters
        ----------
        sid : SID
            Subject SID got from SubjectsData

        Returns
        -------
        Subject (actually SubjectMRI)
            A new SubjectMRI instance with sid assigned.
        
        Raises
        ------
        DataFileException
            If (label, sess_id) not found in self.data.
        """
        subj = SubjectMRI(sid.label, self, sid.session, isBids=self.isBids, bidsDerivatives=self.bidsDerivatives)
        subj.sid = sid  # Raises DataFileException if not found
        return subj

    def get_subject(self, subjlabel: str, sess_id: int = 1, must_exist: bool = False) -> SubjectMRI:
        """
        Get a single subject as SubjectMRI (type-safe override of Project.get_subject).

        Returns SubjectMRI instead of generic Subject for better IDE type checking.
        At runtime, all subjects in ProjectMRI are SubjectMRI anyway; this just makes
        the type explicit for the type checker.

        Parameters
        ----------
        subjlabel : str
            Subject label.
        sess_id : int, optional
            Session ID. Default: 1.
        must_exist : bool, optional
            If True, raises on missing subject. Default: False.

        Returns
        -------
        SubjectMRI
            A single SubjectMRI instance.

        Examples
        --------
        >>> subj = project.get_subject("0001", sess_id=1)
        >>> subj.dti.eddy(...)  # Type checker now knows subj is SubjectMRI
        """
        return super().get_subject(subjlabel, sess_id, must_exist)  # type: ignore

    def _validate_mri_filesystem(self) -> None:
        """
        Validate that all subjects in self.subjects have directory on filesystem.
        
        For BIDS projects, also validates the presence of dataset_description.json in the raw root.
        
        Emits UserWarning for subjects without directory. Non-blocking: init
        completes even if warnings are emitted.
        """
        import warnings
        import os
        
        missing = []
        for subj in self.subjects:
            if not subj.exist:
                missing.append(subj.label)
        
        if missing:
            warnings.warn(
                f"ProjectMRI: {len(missing)} soggetti mancano nel filesystem: {sorted(set(missing))}",
                UserWarning, stacklevel=2
            )
        
        # For BIDS projects, validate dataset_description.json exists
        if self.isBids:
            dataset_desc_path = os.path.join(self.dir, "dataset_description.json")
            if not os.path.exists(dataset_desc_path):
                warnings.warn(
                    f"ProjectMRI BIDS: dataset_description.json non trovato in {self.dir}. "
                    "Il progetto potrebbe non essere BIDS-compliant.",
                    UserWarning, stacklevel=2
                )



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

    def hasSeq(self, seq_type, subjects: SubjectsList|None = None, images_labels: List[str]|None = None):
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

    def can_run_analysis(self, analysis_type, analysis_params: str | List[str]|None = None, subjects: SubjectsList|None = None):
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

    def check_all_coregistration(self, outdir: str, subjects: SubjectsList|None = None, _from: List[str]|None = None, _to: List[str]|None = None, fmri_labels: List[str]|None = None, num_cpu: int = 1, overwrite: bool = False):
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

    def compare_brain_extraction(self, outdir: str, subjects: SubjectsList|None = None, num_cpu=1):
        subjects = self.validate_subjects(subjects)
        os.makedirs(outdir, exist_ok=True)
        self.run_subjects_methods("mpr", "compare_brain_extraction", [{"tempdir": outdir}], ncore=num_cpu, subjects=subjects)
        olddir = os.getcwd()
        os.chdir(outdir)
        os.system("slicesdir ./*.nii.gz")
        os.chdir(olddir)

    def prepare_mpr_for_setorigin1(self, subjects: SubjectsList|None = None, replaceOrig: bool = False, overwrite: bool = False):
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

    def prepare_mpr_for_setorigin2(self, subjects: SubjectsList|None = None):
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

    def add_icv_to_data(self, subjects: SubjectsList|None = None, updatefile: bool = False, df=None):
        subjects = self.validate_subjects(subjects)
        icvs = self.get_subjects_icv(subjects)
        self.data.add_column("icv", icvs, self.subjects2sids(subjects), df)

    def get_subjects_icv(self, subjects: SubjectsList) -> List[float]:
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
            raise DataFileException("Error in ProjectMRI.get_subjects_icv: icv files of some subject/session are missing", str(missing_files))
        return icv_scores

    def create_subjects_lists(self, group_label=None):
        if group_label is None:
            subjs = self.subjects
        else:
            subjs = self.get_subjects(group_label)

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

    #endregion

    # ==================================================================================================================
    # region MULTICORE PROCESSING
    # *kwparams is a list of kwparams. if len(kwparams)=1 & len(subjects) > 1 ...pass that same kwparams[0] to all subjects
    # if subjects is not given...use the loaded subjects
    def run_subjects_methods(self, method_type, method_name, kwparams, ncore=1, subjects: SubjectsList|None = None, must_exist: bool = True):
        """
        Runs a method on a list of subjects.

        Args:
            method_type (str): The type of method to run. Can be an empty string, "mpr", "epi", "dti", or "transform".
            method_name (str): The name of the method to run.
            kwparams (List): A list of keyword arguments to pass to the method. If there is only one argument, it can be passed as a single element list.
            ncore (int, optional): The number of cores to use for parallel processing. Defaults to 1.
            subjects (SubjectsList, optional): list of Subject instances to run the method on. If None, all subjects are used. Defaults to None.
            must_exist (bool, optional): If True, raise an exception if a subject does not exist. Defaults to True.

        Returns:
            None.

        Raises:
            Exception: If the method type is not one of the allowed values, or if the number of keyword arguments does not match the number of subjects.
        """
        subjects = self.validate_subjects(subjects)

        if method_type not in ("", "mpr", "epi", "dti", "transform"):
            raise Exception("Invalid method type: " + method_type + " Method type must be an empty string, 'mpr', 'epi', 'dti', or 'transform'.")
        print("run_subjects_methods: validating given subjects")

        nsubj = len(subjects)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        # check number of NECESSARY (without a default value) method params
        subj = subjects[0]
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
            kwparams = [None] * nsubj

        nprocesses = len(kwparams)

        if nsubj > 1 and nprocesses == 1:
            kwparams   = [kwparams[0]] * nsubj # duplicate the first kwparams up to given subj number
            nprocesses = nsubj
        else:
            if nprocesses != nsubj:
                print("ERROR in run_subject_method: given params list length differs from subjects list")
                return
        # here nparams is surely == nsubj

        numblocks = math.ceil(nprocesses / ncore)  # num of processing blocks (threads)

        subjs: List[List[SubjectMRI]] = []
        processes = []

        for p in range(numblocks):
            subjs.append([])
            processes.append([])

        proc4block = 0
        curr_block = 0

        # divide nprocesses across numblocks
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

    #endregion

    # ==================================================================================================================
