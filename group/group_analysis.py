import os
from typing import List

from Project import Project
from subject.Subject import Subject
from myutility.images.Image import Image
from myutility.images.Images import Images
from myutility.myfsl.utils.run import rrun


# this function assumes that user put the melodic rois of interest in the roi4_folder of a specific subfolder of the given project (where between-groups analyses are done, usually the patient folder)
# subjects instances are given already divided by groups, in order to launch the corresponding project.run_subjects_methods
# the script coregisters each roi into a 2mm rs individual space
def convert_melodic_rois_to_individual(project:Project, templ_name:str, popul_name:str, rois_list:List[str], arr_subjs_insts:List[List[Subject]], thr:int=0.1, report_file:str="transform_report", num_cpu:int=1, mni_2mm_brain:Image=None):

    """
    This function converts melodic ROIs from 4mm to 2mm in individual space.

    Args:
        project (Project): The project object.
        templ_name (str): The template name.
        popul_name (str): The population name.
        rois_list (List[str]): The list of ROIs.
        arr_subjs_insts (List[List[SubjectInstance]]): The list of subject instances.
        thr (float, optional): The threshold value. Defaults to 0.1.
        report_file (str, optional): The report file name. Defaults to "transform_report".
        num_cpu (int, optional): The number of CPUs. Defaults to 1.
        mni_2mm_brain (Image, optional): The MNI 2mm brain image. Defaults to None.

    Raises:
        Exception: If the given ROI does not exist.

    """
    if mni_2mm_brain is None:
        mni_2mm_brain = project.globaldata.fsl_std_mni_2mm_brain
    else:
        mni_2mm_brain = Image(mni_2mm_brain, must_exist=True, msg="given Standard Images is not present")

    dr_results = os.path.join(project.melodic_dr_dir, templ_name, popul_name, "results")
    roi4_folder = os.path.join(dr_results, "standard4")
    roi2_folder = os.path.join(dr_results, "standard2")

    for roi in rois_list:

        if not Image(os.path.join(roi4_folder, roi)).exist:
            raise Exception("Error in convert_melodic_rois_to_individual, roi " + roi + " does not exist in " + roi4_folder)

    os.makedirs(roi2_folder, exist_ok=True)

    report_file = os.path.join(dr_results, report_file + "_" + str(thr) + ".txt")
    with open(report_file, "w") as text_file:
        print("# transformations report of melodic rois located in:", file=text_file)
        print("# " + dr_results + " with thr=" + str(thr), file=text_file)

    # echo "move rois from 4 => 2 mm"
    for roi in rois_list:
        input_roi = Image(os.path.join(roi4_folder, roi))
        output_roi = Image(os.path.join(roi2_folder, roi))

        # rrun(f"flirt -in {input_roi} -ref {mni_2mm_brain} -out {output_roi} -applyisoxfm 2")      # ${FSLDIR}/bin/flirt -in $roi_folder4/$roi -ref $ref_img -out $roi_folder2/$roi -applyisoxfm

        for subjs_insts in arr_subjs_insts:
            proj = subjs_insts[0].project

            # "$subjects_list" $PROJ_DIR -nlin -ipathtype abs -refabs $ref_img -transfrel $transformation -refrel $refrel -maskrel $maskrel -opath $output_rel_path -orf $report_file -fullrep "${arr_rois_paths[@]}"
            # regtype, pathtype="standard", outdir="", outname="", mask="", orf="", thresh=0, islin=True, rois=None):
            proj.run_subjects_methods("transform", "transform_roi", [{"regtype": "std4TOrs", "pathtype": "abs", "islin": False, "orf": report_file, "thresh": thr, "rois": [roi]}], ncore=num_cpu, group_or_subjlabels=subjs_insts)


# this function deal with tbss results.
# project:  project where group analysis are done
# rois:     list of normalized Image to investigate (extract mean individual metrics)
# subjects: list of subjects instances
# metric:   measures to analyze. values are: FA,MD,AD,RD

def extract_meanvalue_from_tbssresults(project:Project, rois:Images, subjects:List[Subject], metric:str="FA"):

    """
    This function takes

    Args:
        project (Project): The project object.
        rois (List[Image]): The list of normalized Image to investigate (extract mean individual metrics)
        subjects (List[Subject]): The list of subjects instances
        metric (str, optional): The measures to analyze. Defaults to "FA".

    Returns:
        List[List[float]]: The mean values of the given metric in each ROI.

    Raises:
        Exception: If the given metric is not valid.

    """
    # sanity checks
    if metric not in ["FA", "MD", "AD", "RD"]:
        print("Error in extract_meanvalue_from_tbssresults, given metric (" + str(metric) + ") is not valid")
        return

    if not rois.exist:
        print("Error in extract_meanvalue_from_tbssresults, one or more roi image is not valid (" + str(rois) + ")")
        return

    # ----------------------------------------------------------------------
    if metric == "FA":
        subj_img_postfix = "_FA_FA_to_target"
    else:
        subj_img_postfix = "_FA_to_target_" + metric

    for roi in rois:
        rrun(f"fslmaths {roi} -thr 0.95 -bin {roi.split_ext()[0]}_mask")
    out_folder = os.path.join(project.tbss_dir, "results_sp_sts_htc_fmrib58")

    results = []
    for roi in tbssmap:
        roi_mask_img = os.path.join(roi_root_dir, roi + "_mask")
        roi_row = []

        for subj in subjects:
            subj_img = os.path.join(subjects_images, subj.dti_fit_label + subj_img_postfix)
            subj_img_masked = os.path.join(subjects_images, subj.dti_fit_label + subj_img_postfix + "_masked")

            rrun(f"fslmaths {subj_img} -mas {roi_mask_img} {subj_img_masked}")
            val = float(rrun(f"fslstats  {subj_img_masked} -M").strip())
            imrm([subj_img_masked])
            roi_row.append(val)

        results.append(roi_row)


# takes melodic RSN's labels created with fsleyes, parse it and
# - extract valid and non-valid IC and returns them as lists
# - writes in bash melodic templates (for dual regression): str_pruning_ic_id, str_arr_IC_labels, arr_IC_labels, arr_pruning_ic_id fields
# - writes in matlab melodic templates (for fslnets):
#           templates(1)=struct('name', 'controls59', 'imagepath' , '/data/MRI/pymri/templates/images/MNI152_T1_4mm_brain', 'rsn_labels', [], 'good_nodes', []);
#           templates(1).rsn_labels={'aDMN','LAT_OCCIP','pDMN','RATN','FP','PRIM_VIS','LATN','FP2','pTemp','pSM','EXEC','SM','BG','BFP','CEREB','SM2','aTemp','LAT_OCCIP2','SAL','LAT_OCCIP3','X','SAL2'};
#           templates(1).good_nodes=[1 2 3 5 6 7 8 9 11 12 13 14 15 16 17 20 23 24 27 29 34 47];
def parse_melodic_labels(ilabels:str, ibashtempl:str="", ifslnetstempl:str="", fslnetstemplname:str="", t1_4mm_brain:str="", templnum:int=1):

    with open(ilabels, "r") as f:
        _str = f.readlines()
    _str.pop(0)
    _str.pop()

    rsns = []
    noises = []

    # calculate rsn and noise components
    for s in _str:
        _a = s.split(",")       # 4, Signal, False
        a = [s.strip() for s in _a]
        a[0] = int(a[0])-1

        if a[2] == "False":
            rsns.append(a[0])
        else:
            noises.append(a[0])

    # write bash melodic templates
    if not os.path.exists(ibashtempl):
        print("ibashtempl " + ibashtempl + " is missing. won't write it")
    else:
        with open(ibashtempl, "a") as f:

            # id are 0-based
            txt = "str_pruning_ic_id=(\""
            for rsn in rsns:
                txt = txt + str(rsn) + ","
            txt = txt[:-1] + "\")\n"

            txt = txt + "declare -a arr_pruning_ic_id=("
            for rsn in rsns:
                txt = txt + str(rsn) + " "
            txt = txt[:-1] + ")\n"

            # labels are 1-based
            txt = txt + "str_arr_IC_labels=(\""
            for rsn in rsns:
                txt = txt + str(rsn) + ","
            txt = txt[:-1] + "\")\n"

            txt = txt + "declare -a arr_IC_labels=("
            for rsn in rsns:
                txt = txt + str(rsn) + " "
            txt = txt[:-1] + ")\n"

            f.write(txt)
            # str_pruning_ic_id=("0,1,2,3,4,5,7,8,9,13,14,16,19,21,23,25,30,31,33,34,37,38,40,51")  # valid RSN: you must set their id values removing 1: if in the html is the 6th RSN, you must write 5!!!!!!
            # str_arr_IC_labels=("V1,R_ATN,pDMN,FRPOLE,LAT_VIS,L_ATN,aDMN,B_FR_PAR,B_TEMP,SM,LAT_VIS2,OCCIP,SM_BG,B_FP,CEREB,BG_INS,EXEC,CEREB2,MSF,R_SM,AUDIO,POST_TEMP,XX_FR_OFC,L_SM")
            # declare -a arr_IC_labels=(V1 R_ATN pDMN FRPOLE LAT_VIS L_ATN aDMN B_FR_PAR B_TEMP SM LAT_VIS2 OCCIP SM_BG B_FP CEREB BG_INS EXEC CEREB2 MSF R_SM AUDIO POST_TEMP XX_FR_OFC L_SM)
            # declare -a arr_pruning_ic_id=(0 1 2 3 4 5 7 8 9 13 14 16 19 21 23 25 30 31 33 34 37 38 40 51)

    # write fslnets matlab melodic templates
    if not os.path.exists(ifslnetstempl):
        print("ifslnetstempl " + ifslnetstempl + " is missing. won't write it")
    else:
        with open(ifslnetstempl, "a") as f:

            txt = "templates(" + str(templnum) + ") = struct('name', '" + fslnetstemplname + "', 'imagepath', '" + t1_4mm_brain + "', 'rsn_labels', [], 'good_nodes', []);\n"

            txt = txt + "templates(" + str(templnum) + ").rsn_labels = {"
            for rsn in rsns:
                txt = txt + "'" + str(rsn + 1) + "',"
            txt = txt[:-1] + "};\n"

            txt = txt + "templates(" + str(templnum) + ").good_nodes = ["
            for rsn in rsns:
                txt = txt + str(rsn + 1) + " "
            txt = txt[:-1] + "];\n"

            f.write(txt)

            # templates(1) = struct('name', 'controls59', 'imagepath', '/data/MRI/pymri/templates/images/MNI152_T1_4mm_brain', 'rsn_labels', [], 'good_nodes', []);
            # templates(1).rsn_labels = {'aDMN', 'LAT_OCCIP', 'pDMN', 'RATN', 'FP', 'PRIM_VIS', 'LATN', 'FP2', 'pTemp', 'pSM', 'EXEC', 'SM', 'BG', 'BFP', 'CEREB', 'SM2', 'aTemp', 'LAT_OCCIP2', 'SAL', 'LAT_OCCIP3', 'X', 'SAL2'};
            # templates(1).good_nodes = [1 2 3 5 6 7 8 9 11 12 13 14 15 16 17 20 23 24 27 29 34 47];
    return rsns, noises


