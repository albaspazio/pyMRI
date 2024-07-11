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
from data.SubjectsData import SubjectsData
from data.utilities import FilterValues
from subject.Subject import Subject
from data.SubjectSDList import SubjectSDList
from utility.exceptions import SubjectListException
from utility.images.Image import Image
from utility.fileutilities import sed_inplace, remove_ext


class Project:

    def __init__(self, folder:str, globaldata:Global, data:str|SubjectsData="data.xlsx"):
        """
        Initialize a Project instance.

        Parameters
        ----------
        folder : str
            The path to the project folder.
        globaldata : Global
            The global data instance.
        data : str | SubjectsData, optional
            The path to the data file, by default "data.dat" or a SubjectsData instance.
        """
        if not os.path.exists(folder):
            raise Exception("PROJECT_DIR not defined.....exiting")

        self.dir        = folder
        self.label      = os.path.basename(self.dir)
        self.name       = os.path.basename(self.dir)

        self.subjects_dir       = os.path.join(self.dir, "subjects")
        self.group_analysis_dir = os.path.join(self.dir, "group_analysis")
        self.script_dir         = os.path.join(globaldata.project_scripts_dir, self.name)

        self.glm_template_dir   = os.path.join(self.script_dir, "glm", "templates")
        self.group_glm_dir     = os.path.join(self.group_analysis_dir, "glm_models")

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


        self.subjects_lists_file    = os.path.join(self.script_dir, "subjects_lists.json")

        self.globaldata             = globaldata

        self.subjects:list[Subject] = []
        self.subjects_labels    = []
        self.nsubj              = 0

        # load all available subjects list into self.subjects_lists
        with open(self.subjects_lists_file) as json_file:
            subjects            = json.load(json_file)
            self.subjects_lists = subjects["subjects"]

        # load subjects data if possible
        self.data_file = ""
        self.data:SubjectsData = SubjectsData()

        self.load_data(data)

    # if must_exist=true:   loads in self.subjects, a list of subjects instances associated to a valid grouplabel or a subjlabels list
    # if must_exist=false:  only create
    # returns this list
    def load_subjects(self, group_or_subjlabels:str|List[str], sess_id:int=1, must_exist:bool=True) -> List[Subject]:
        """
        Load subjects based on a group label or a list of subject labels.

        Parameters
        ----------
        group_or_subjlabels : str or list
            The group label or a list of subject labels.
        sess_id : int, optional
            The session ID, by default 1.
        must_exist : bool, optional
            If True, raise an exception if the group or any of the subjects do not exist, by default True.

        Returns
        -------
        List[Subject]
            The list of loaded subjects.

        Raises
        ------
        SubjectListException
            If the group or any of the subjects do not exist and `must_exist` is True.
        """
        try:
            subjects           = self.get_subjects(group_or_subjlabels, sess_id, must_exist)

        except SubjectListException as e:
            raise SubjectListException("load_subjects", e.param)  # send whether the group label was not present
                                                                        # or one of the subjects was not valid
        if must_exist:
            self.subjects           = subjects
            self.subjects_labels    = [subj.label for subj in self.subjects]
            self.nsubj              = len(self.subjects)

        return subjects

    # get a deepcopy of subject with given label
    def get_subject(self, subj_label:str, sess:int=1, must_exist:bool=True) -> Subject:
        """
        Get a subject instance with the given subject label.

        Parameters
        ----------
        subj_label : str
            The subject label.
        sess : int, optional
            The session ID, by default 1.
        must_exist : bool, optional
            If True, raise an exception if the subject does not exist, by default True.

        Returns
        -------
        Subject
            The subject instance.

        Raises
        ------
        SubjectListException
            If the subject does not exist and `must_exist` is True.
        """
        if must_exist:
            for subj in self.subjects:
                if subj.label == subj_label:
                    if subj.sessid == sess:
                        return deepcopy(subj)
                    else:
                        return subj.set_properties(sess, rollback=True)  # it returns a deepcopy of requested session
            raise Exception("Error in Project.get_subject: given subject (" + subj_label + " does not exist")
        else:
            return Subject(subj_label, self, sess)

    # ==================================================================================================================
    # region GET SUBJECTS' LABELS or INSTANCES
    # ==================================================================================================================
    # IN:   GROUP_LABEL | SUBLABELS LIST
    # OUT:  [VALID SUBJECT INSTANCES LIST]
    def get_subjects(self, group_or_subjlabels:str|List[str]=None, sess_id:int=1, must_exist:bool=True, select_conds:List[FilterValues]=None) -> List[Subject]:
        """
        Load subjects based on a group label or a list of subject labels.

        Parameters
        ----------
        group_or_subjlabels : str or list, optional
            The group label or a list of subject labels. If None, all subjects are loaded.
        sess_id : int, optional
            The session ID, by default 1.
        must_exist : bool, optional
            If True, raise an exception if the group or any of the subjects do not exist, by default True.
        select_conds : List[FilterValues], optional
            A list of FilterValues to filter the subjects based on their properties.

        Returns
        -------
        List[Subject]
            The list of loaded subjects.

        Raises
        ------
        SubjectListException
            If the group or any of the subjects do not exist and `must_exist` is True.
        """
        valid_subj_labels = self.get_subjects_labels(group_or_subjlabels, sess_id, must_exist)

        if select_conds is not None:
            valid_subj_labels = self.data.select_subjlist(valid_subj_labels, [sess_id], select_conds)

        return [Subject(subj_lab, self, sess_id) for subj_lab in valid_subj_labels]

    # IN:   GROUP_LABEL | SUBLABELS LIST | SUBJINSTANCES LIST
    # OUT:  [VALID SUBLABELS LIST]
    def get_subjects_labels(self, grlab_subjlabs_subjs:str|List[str]|List[Subject]=None, sess_id=1, must_exist:bool=True) -> List[str]:
        """
        Get a list of subject labels based on a group label or a list of subject labels.

        Parameters
        ----------
        grlab_subjlabs_subjs : (str or List[str] or List[Subject]), optional.
           The group label or a list of subjects' label/instances. If None, all subjects are loaded.
        sess_id : int, optional
            The session ID, by default 1.
        must_exist : bool, optional
            If True, raise an exception if the group or any of the subjects do not exist, by default True.

        Returns
        -------
        List[str]
            The list of subject labels.

        Raises
        ------
        SubjectListException
            If the group or any of the subjects do not exist and `must_exist` is True.
        """
        if grlab_subjlabs_subjs is None:
            if len(self.subjects_labels) == 0:
                raise SubjectListException("get_subjects_labels", "given grlab_subjlabs_subjs is None and no group is loaded")
            else:
                return self.subjects_labels         # if != 0, a list of validated subjects exist

        elif isinstance(grlab_subjlabs_subjs, str):  # must be a group_label and have its associated subjects list
            return self.__get_valid_subjlabels_from_group(grlab_subjlabs_subjs, sess_id, must_exist)

        elif isinstance(grlab_subjlabs_subjs, list):
            if isinstance(grlab_subjlabs_subjs[0], str) is True:
                # list of subjects' names
                if must_exist:
                    self.__assert_valid_subjlabels(grlab_subjlabs_subjs, sess_id)
                return grlab_subjlabs_subjs   # [string]

            elif isinstance(grlab_subjlabs_subjs[0], Subject):
                return [subj.label for subj in grlab_subjlabs_subjs]
            else:
                raise SubjectListException("get_subjects_labels", "the given grlab_subjlabs_subjs param is not a string list, first value is: " + str(grlab_subjlabs_subjs[0]))
        else:
            raise SubjectListException("get_subjects_labels", "the given grlab_subjlabs_subjs param is not a valid param (None, string  or string list), is: " + str(grlab_subjlabs_subjs))
    # endregion

    # =========================================================================
    # region PRIVATE VALIDATION ROUTINES
    # =========================================================================

    # must_exist=True   -> check list is valid and whether all subjects belonging to the given group_label are valid
    # must_exist=False  -> if list if present, returns its associated subjects' labels without verifying their validity
    # IN:   GROUP_LAB
    # OUT:  [VALID SUBJLABELS LIST] or SubjectListException
    def __get_valid_subjlabels_from_group(self, group_label:str, sess_id=1, must_exist:bool=True) -> List[str]:
        """
        Get a list of subject labels based on a group label or a list of subject labels.

        Parameters
        ----------
        group_label : str
            The group label.
        sess_id : int, optional
            The session ID, by default 1.
        must_exist : bool, optional
            If True, raise an exception if the group or any of the subjects do not exist, by default True.

        Returns
        -------
        List[str]
            The list of subject labels.

        Raises
        ------
        SubjectListException
            If the group or any of the subjects do not exist and `must_exist` is True.
        """
        for grp in self.subjects_lists:
            if grp["label"] == group_label:
                if must_exist:
                    self.__assert_valid_subjlabels(grp["list"], sess_id)
                return grp["list"]
        raise SubjectListException("__get_valid_subjlabels_from_group", "given group_label (" + group_label + ") does not exist in subjects_lists")

    # check whether all subjects listed in subjects are valid
    # returns given list if all valid
    # IN:   SUBJLABELS LIST
    # OUT:  [VALID SUBJLABELS LIST] or SubjectListException
    def __assert_valid_subjlabels(self, subj_labels:List[str], sess_id: int = 1):
        """
        Check if all subjects in the given list exist.

        Parameters:
        subj_labels (List[str]): List of subject labels.
        sess_id (int, optional): Session ID.

        Raises:
        SubjectListException: If a subject does not exist.
        """
        for lab in subj_labels:
            if not Subject(lab, self, sess_id).exist():
                raise SubjectListException("__get_valid_subjlabels", "given subject (" + lab + ") does not exist in file system")

    #endregion

    # ==================================================================================================================
    #region M R I

    # CHECK/PREPARE IMAGES
    def check_subjects_original_images(self):
        """
        Check if all subjects have all the necessary images.

        Returns:
        A list of dictionaries, where each dictionary represents a subject and its missing images.
        """
        incomplete_subjects = []
        for subj in self.subjects:
            missing = subj.check_images(self.hasT1, self.hasRS, self.hasDTI, self.hasT2)
            if len(missing) > 0:
                incomplete_subjects.append({"label": subj.label, "images": missing})

        return incomplete_subjects

    def hasSeq(self, seq_type, group_or_subjlabels:str|List[str]=None, sess_id:int=1, images_labels:List[str]=None):
        """
        Check if all subjects have the given sequence.

        Args:
        seq_type (str): The sequence type, e.g., "T1w", "T2w", "FLAIR", etc.
        group_or_subjlabels (str or list, optional): The group label or a list of subject labels. If None, all subjects are checked.
        sess_id (int, optional): The session ID, by default 1.
        images_labels (list, optional): A list of image labels to check, by default None (all images).

        Returns:
        A string with the subjects not ready.
        """
        invalid_subjs = ""
        valid_subjs = self.get_subjects(group_or_subjlabels, sess_id)
        for subj in valid_subjs:
            if not subj.hasSeq(seq_type, images_labels):
                invalid_subjs = invalid_subjs + subj.label + "\n"

        if len(invalid_subjs) > 0:
            print("ERROR.... the following subjects does not have the given sequence " + seq_type + " :\n" + invalid_subjs)
        else:
            print("OK....... " + seq_type + " analysis can be run")

        return invalid_subjs

    # check whether all subjects defined by given group_or_subjlabels have the necessary files to perform given analysis
    # allowed analysis are: vbm_fsl, vbm_spm, ct, tbss, bedpost, xtract_single, xtract_group, melodic, sbfc, fmri
    # returns a string with the subjects not ready
    def can_run_analysis(self, analysis_type, analysis_params:str|List[str]=None, group_or_subjlabels:str|List[str]=None, sess_id=1):
        """
        Check if all subjects have the necessary files to perform the given analysis.

        Args:
        analysis_type (str): The analysis type, e.g., "vbm_fsl", "vbm_spm", etc.
        analysis_params (str|List[str], optional): The analysis parameters, if any.
        group_or_subjlabels (str or list, optional): The group label or a list of subject labels. If None, all subjects are checked.
        sess_id (int, optional): The session ID, by default 1.

        Returns:
        A string with the subjects not ready.
        """
        invalid_subjs = ""
        valid_subjs = self.get_subjects(group_or_subjlabels, sess_id)
        for subj in valid_subjs:
            if not subj.can_run_analysis(analysis_type, analysis_params):
                invalid_subjs = invalid_subjs + subj.label + "\n"

        if len(invalid_subjs) > 0:
            print("ERROR.... the following subjects prevent the completion of the " + analysis_type + " analysis:\n" + invalid_subjs)
        else:
            print("OK....... " + analysis_type + " analysis can be run")

        return invalid_subjs

    def check_all_coregistration(self, outdir:str, subjs_labels:List[str]=None, _from:str=None, _to:str=None, fmri_labels:List[str]=None, num_cpu:int=1, overwrite:bool=False):
        """
        Check/Prepare coregistration for all subjects.

        Args:
        outdir (str): The output directory.
        subjs_labels (list, optional): A list of subject labels. If None, all subjects are used.
        _from (list, optional): A list of image types to coregister from. If None, ["hr", "rs", "fmri", "dti", "t2", "std", "std4"] is used.
        _to (list, optional): A list of image types to coregister to. If None, ["hr", "rs", "fmri", "dti", "t2", "std", "std4"] is used.
        fmri_labels (list, optional): A list of FMRIBank labels to use for coregistration.
        num_cpu (int, optional): The number of cores to use, by default 1.
        overwrite (bool, optional): If True, overwrite existing coregistration results, by default False.

        Returns:
        None.
        """
        if subjs_labels is None:
            subjs_labels = self.get_subjects_labels()

        if _from is None:
            _from = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        if _to is None:
            _to = ["hr", "rs", "fmri", "dti", "t2", "std", "std4"]

        self.run_subjects_methods("transform", "test_all_coregistration", [{"test_dir":outdir, "_from":_from, "_to":_to, "fmri_labels":fmri_labels, "overwrite":overwrite}], ncore=num_cpu, group_or_subjlabels=subjs_labels)

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
    def compare_brain_extraction(self, outdir:str, subj_labels:List[str]=None, num_cpu=1):
        """
        Check/Prepare coregistration for all subjects.

        Args:
            outdir (str): The output directory.
            subj_labels (list, optional): A list of subject labels. If None, all subjects are used.
            num_cpu (int, optional): The number of cores to use, by default 1.

        Returns:
            None.
        """
        if subj_labels is None or subj_labels == "":

            if len(self.subjects) == 0:
                print("ERROR in compare_brain_extraction: no subjects are loaded and input subjects list label is empty")
                return
            else:
                subjs = self.subjects
        else:
            subjs = self.get_subjects_labels(subj_labels)

        os.makedirs(outdir, exist_ok=True)

        self.run_subjects_methods("mpr", "compare_brain_extraction", [{"tempdir":outdir}], ncore=num_cpu, group_or_subjlabels=subj_labels)

        # for subj in subjs:
        #     self.get_subjects([subj])[0].compare_brain_extraction(outdir)

        olddir = os.getcwd()
        os.chdir(outdir)
        os.system("slicesdir ./*.nii.gz")
        os.chdir(olddir)

    # prepare_mpr_for_setorigin1 and prepare_mpr_for_setorigin2 are to be used in conjunction
    # the former make a backup and unzip the original file,
    # the latter zip and clean up
    def prepare_mpr_for_setorigin1(self, group_label:str, sess_id:int=1, replaceOrig:bool=False, overwrite:bool=False):
        """
        Prepare MPR data for setorigin.

        Parameters:
        group_label (str): The group label.
        sess_id (int, optional): The session ID, by default 1.
        replaceOrig (bool, optional): If True, replace the original data with the temporary data, by default False.
        overwrite (bool, optional): If True, overwrite existing temporary data, by default False.

        Returns:
        None.
        """
        subjects = self.load_subjects(group_label, sess_id)

        for subj in subjects:
            if not replaceOrig:
                subj.t1_data.cp(subj.t1_data + "_old_origin")

            niifile = Image(str(os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")))

            if niifile.uexist and not overwrite:
                print("skipping prepare_mpr_for_setorigin1 for subj " + subj.label)
                continue

            subj.t1_data.cpath.unzip(niifile, replace=True)
            print("unzipped " + subj.label + " mri")

    def prepare_mpr_for_setorigin2(self, group_label:str, sess_id:int=1):
        """
        Prepare MPR data for setorigin.

        Parameters:
        group_label (str): The group label.
        sess_id (int, optional): The session ID, by default 1.

        Returns:
        None.
        """
        subjects = self.load_subjects(group_label, sess_id)
        for subj in subjects:
            niifile = Image(str(os.path.join(subj.t1_dir, subj.t1_image_label + "_temp.nii")))
            subj.t1_data.cpath.rm()
            niifile.compress(subj.t1_data.cpath)
            niifile.rm()
            print("zipped " + subj.label + " mri")
    #endregion

    # ==================================================================================================================
    #region D A T A

    # load a data_file if exist
    def load_data(self, data:str|SubjectsData) -> SubjectsData:
        """
        Load data into the project.

        Args:
            data (str|SubjectsData): The path to the data file or a SubjectsData instance.

        Returns:
            SubjectsData: The loaded data file.

        Raises:
            TypeError: if given data is neither a string nor a SubjectsData instance.
        """
        if isinstance(data, str):
            data_file = ""
            if os.path.exists(data):
                data_file = data
            elif os.path.isfile(os.path.join(self.script_dir, data)):
                data_file = os.path.join(self.script_dir, data)

            if data_file != "":
                d = SubjectsData(data_file)
                if d.num > 0:
                    self.data       = d
                    self.data_file  = data_file
        elif isinstance(data, SubjectsData):
            self.data       = data
        else:
            raise TypeError("ERROR in Project.load_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

        return self.data

    # validate data dictionary. if param is none -> takes it from self.data
    #                           otherwise try to load it
    def validate_data(self, data:str|SubjectsData=None) -> SubjectsData:
        """
        Load a data file into the project.

        Args:
            data (SubjectsData or str, optional): The data to load. If None, and the project's data is already loaded, it is returned. If None and the project's data is not loaded, an exception is raised. If a string, the string is interpreted as a path to a data file to load.

        Returns:
            SubjectsData: The loaded data.

        Raises:
            Exception: If the given data is neither a SubjectsData instance nor a string path to a data file.
        """
        if data is None:
            if self.data.num > 0:
                return self.data
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is None and project's data is not loaded")
        else:
            if isinstance(data, SubjectsData):
                return data
            elif isinstance(data, str):
                if os.path.exists(data):
                    return SubjectsData(data)
                else:
                    raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is a string that does not point to a valid file to load")
            else:
                raise Exception("ERROR in Project.validate_data: given data param (" + str(data) + ") is neither a SubjectsData nor a string")

    # returns a matrix (values x subjects) containing values of the requested columns of given subjects
    # user can also pass a datafile path or a custom subj_dictionary
    def get_subjects_values_by_cols(self, grlab_subjlabs_subjs:str|List[str]|List[Subject], columns_list:List[str], data:str|SubjectsData=None, sort:bool=False,
                                    demean_flags:List[bool]=None, sess_id:str=None, must_exist:bool=False) -> List[List[Any]]:
        """
        Returns a matrix (values x subjects) containing values of the requested columns of given subjects.

        Parameters:

        - grlab_subjlabs_subjs (str or List[str] or List[Subject]): The group label or a list of subjects' label/instances.
        - columns_list (list): A list of column labels.
        - data (SubjectsData or str, optional): The data to use. If None, the project's data is used. If a string, the string is interpreted as a path to a data file to load.
        - sort (bool, optional): If True, sort the output by subject.
        - demean_flags (list, optional): A list of demeaning flags. If None, no demeaning is performed.
        - sess_id (int or None, optional): The session ID.
        - must_exist (bool, optional): If True, raise an exception if a subject does not exist.

        Returns:
        list: A list of values.

        Raises:
        Exception: If the given data is neither a SubjectsData instance nor a string path to a data file.
        """
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs, sess_id, must_exist=must_exist)
        valid_data  = self.validate_data(data)

        if sess_id is not None:
            sessions = [sess_id for s in subj_labels]     # 1-fill
        else:
            sessions = None

        subjsSD_list:SubjectSDList = valid_data.filter_subjects(subj_labels, sessions)

        if valid_data is not None:
            return valid_data.get_subjects_values_by_cols(subjsSD_list, columns_list, demean_flags=demean_flags)
        else:
            return []

    # - [values]
    # - [labels]
    # user can also pass a datafile path or a custom subj_dictionary
    def get_filtered_column(self, grlab_subjlabs_subjs:str|List[str]|List[Subject], column, data=None, sort:bool=False, sess_id=1, select_conds:List[FilterValues]=None) -> Tuple[list, List[str]]:
        """
        Returns a list of values and a list of labels for a given column, filtered by given conditions.

        Parameters:
        grlab_subjlabs_subjs (str or List[str] or List[Subject]): The group label or a list of subjects' label/instances.
        column (str): The column label.
        data (SubjectsData or str, optional): The data to use. If None, the project's data is used. If a string, the string is interpreted as a path to a data file to load.
        sort (bool, optional): If True, sort the output by subject.
        sess_id (int, optional): The session ID.
        select_conds (list, optional): A list of filter conditions.

        Returns:
        tuple: A tuple containing a list of values and a list of labels.

        Raises:
        Exception: If the given data is neither a SubjectsData instance nor a string path to a data file.
        """
        subj_labels = self.get_subjects_labels(grlab_subjlabs_subjs, sess_id)
        valid_data  = self.validate_data(data)

        sessions = [sess_id for s in subj_labels]     # sess_id-fill
        subjsSD_list:SubjectSDList = valid_data.filter_subjects(subj_labels, sessions, conditions=select_conds)

        if valid_data is None:
            raise Exception("Error in Project.get_filtered_column: valid_data is None")
        else:
            return valid_data.get_filtered_column(subjsSD_list, column, sort=sort)

    def add_data_column(self, colname: str, subjects: SubjectSDList, values):
        """
        Adds a new column to the data.

        Args:
            colname (str): The name of the column.
            subjects (SubjectSDList): The subjects to add the column to.
            values (list): The values of the column for each subject.

        Returns:
            None.
        """
        self.data.add_column(colname, values, subjects)

    # added data_file in order to add v
    def add_icv_to_data(self, grlab_subjlabs_subjs:str|List[str]|List[Subject]=None, updatefile:bool=False, df=None, sess_id=1):
        """
        Add the intracranial volume (ICV) to the data.

        Parameters:
        grlab_subjlabs_subjs (str or List[str] or List[Subject]): The group label or a list of subjects' label/instances. If None, all subjects are used.
        updatefile (bool, optional): If True, update the data file, by default False.
        df (SubjectsData, optional): The data to use. If None, the project's data is used.
        sess_id (int, optional): The session ID.

        Returns:
        None.
        """
        if grlab_subjlabs_subjs is None:
            grlab_subjlabs_subjs = self.get_subjects_labels()
        else:
            grlab_subjlabs_subjs = self.get_subjects_labels(grlab_subjlabs_subjs)

        icvs = self.get_subjects_icv(grlab_subjlabs_subjs, sess_id)

        subjsids = self.data.filter_subjects(grlab_subjlabs_subjs, [sess_id])
        self.data.add_column("icv", icvs, subjsids, df)

    #endregion

    # ==================================================================================================================
    # region ACCESSORY

    def get_subjects_icv(self, grlab_subjlabs_subjs:str|List[str]|List[Subject], sess_id:int=1):
        """
        Returns the intracranial volume (ICV) for a given group of subjects.

        Args:
            grlab_subjlabs_subjs (str or List[str] or List[Subject]): The group label or a list of subjects' label/instances.
            sess_id (int, optional): The session ID.

        Returns:
            List[float]: A list of ICV scores.
        """
        if isinstance(grlab_subjlabs_subjs[0], Subject):  # so caller does not have to set also the sess_id, is a xprojects parameter
            subjects_list:List[Subject] = grlab_subjlabs_subjs
        else:
            subjects_list = self.get_subjects(grlab_subjlabs_subjs, sess_id)

        icv_scores = []
        for subj in subjects_list:
            with open(subj.t1_spm_icv_file) as fp:
                fp.readline()
                line    = fp.readline().rstrip()
                values  = line.split(',')

            icv_scores.append(round(float(values[1]) + float(values[2]) + float(values[3]), 4))
        return icv_scores

    def create_lists(self, group_label=None):

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

        # remove auto lists
        subjects_lists = [d for d in subjects_lists if d.get("label") not in ["auto_t1", "auto_ct", "auto_dti", "auto_rs"]]
        subjects_lists = subjects_lists + lists

        subjects["subjects"] = subjects_lists

        with open(self.subjects_lists_file, mode="w") as json_file:
            json.dump(subjects, json_file, indent=4)

    #endregion ==================================================================================================================

    # ==================================================================================================================
    #region BATCHING
    # returns out_batch_job, created from zero
    def create_batch_files(self, out_batch_name, seq):
        """
        Creates the SPM batch files for a given sequence.

        Args:
            out_batch_name (str): The name of the output batch file.
            seq (str): The sequence name.

        Returns:
            Tuple[str, str]: A tuple containing the path to the output batch file and the path to the start batch file.
        """
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
    def adapt_batch_files(self, templfile_noext, seq, prefix:str="", postfix:str=""):
        """
        Creates adapted SPM batch files for a given sequence.

        Args:
            templfile_noext (str): The name of the SPM batch template file, without the extension.
            seq (str): The sequence name.
            prefix (str, optional): A prefix to add to the batch file names, by default "".
            postfix (str, optional): A postfix to add to the batch file names, by default "".

        Returns:
            Tuple[str, str]: A tuple containing the paths to the adapted output batch file and the adapted start batch file.
        """
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
    #endregion

    # ==================================================================================================================
    # region MULTICORE PROCESSING
    # *kwparams is a list of kwparams. if len(kwparams)=1 & len(subjects) > 1 ...pass that same kwparams[0] to all subjects
    # if subjects is not given...use the loaded subjects
    def run_subjects_methods(self, method_type, method_name, kwparams, ncore=1, group_or_subjlabels=None, sess_id=1, must_exist:bool=True):
        """
        Runs a method on a list of subjects.

        Args:
            method_type (str): The type of method to run. Can be an empty string, "mpr", "epi", "dti", or "transform".
            method_name (str): The name of the method to run.
            kwparams (List): A list of keyword arguments to pass to the method. If there is only one argument, it can be passed as a single element list.
            ncore (int, optional): The number of cores to use for parallel processing. Defaults to 1.
            group_or_subjlabels (Union[str, List], optional): The group or list of subject labels to run the method on. If None, all subjects are used. Defaults to None.
            sess_id (int, optional): The session ID. Defaults to 1.
            must_exist (bool, optional): If True, raise an exception if a subject does not exist. Defaults to True.

        Returns:
            None.

        Raises:
            Exception: If the method type is not one of the allowed values, or if the number of keyword arguments does not match the number of subjects.
        """
        if method_type not in ("", "mpr", "epi", "dti", "transform"):
            raise Exception("Invalid method type: " + method_type + " Method type must be an empty string, 'mpr', 'epi', 'dti', or 'transform'.")

        print("run_subjects_methods: validating given subjects")
        valid_subjlabels    = self.get_subjects_labels(group_or_subjlabels, sess_id, must_exist)
        nsubj               = len(valid_subjlabels)
        if nsubj == 0:
            print("ERROR in run_subjects_methods: subject list is empty")
            return

        # check number of NECESSARY (without a default value) method params
        subj = self.get_subject(valid_subjlabels[0], sess_id, must_exist)    # subj appear unused, but is instead used in the eval()
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

                subj = self.get_subject(subjects[bl][s], sess_id, must_exist)

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

    #endregion
    # ==================================================================================================================
