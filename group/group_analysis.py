import os
from utility.images.Image import Image


# this function assumes that user put the melodic rois of interest in the roi4_folder of a specific subfolder of the given project (where between-groups analyses are done, usually the patient folder)
# subjects instances are given already divided by groups, in order to launch the corresponding project.run_subjects_methods
# the script coregisters each roi into a 2mm rs individual space
def convert_melodic_rois_to_individual(project, templ_name, popul_name, rois_list, arr_subjs_insts, thr=0.1, report_file="transform_report", num_cpu=1, mni_2mm_brain=None):

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

        # rrun("flirt -in " + input_roi + " -ref " + mni_2mm_brain + " -out " + output_roi + " -applyisoxfm 2")      # ${FSLDIR}/bin/flirt -in $roi_folder4/$roi -ref $ref_img -out $roi_folder2/$roi -applyisoxfm

        for subjs_insts in arr_subjs_insts:
            proj = subjs_insts[0].project

            # "$subjects_list" $PROJ_DIR -nlin -ipathtype abs -refabs $ref_img -transfrel $transformation -refrel $refrel -maskrel $maskrel -opath $output_rel_path -orf $report_file -fullrep "${arr_rois_paths[@]}"
            # regtype, pathtype="standard", outdir="", outname="", mask="", orf="", thresh=0, islin=True, rois=None):
            proj.run_subjects_methods("transform", "transform_roi", [{"regtype": "std4TOrs", "pathtype": "abs", "islin": False, "orf": report_file, "thresh": thr, "rois": [roi]}], ncore=num_cpu, group_or_subjlabels=subjs_insts)
