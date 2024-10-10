import os
import traceback

from Global import Global
from Project import Project
from subject.Subject import Subject
from myutility.images.Image import Image
from group.spm_utilities import SubjResultsParam, TContrast, FContrast, SubjCondition, FmriProcParams
from numpy import sort, asarray

if __name__ == "__main__":

    # ======================================================================================================================
    # check global data and external toolboxes
    # ======================================================================================================================
    fsl_code = "604"
    try:
        globaldata = Global(fsl_code)

        # ======================================================================================================================
        # HEADER
        # ======================================================================================================================
        subjproj_dir    = "/data/MRI/projects/3T"
        subjproject     = Project(subjproj_dir, globaldata)

        proj_dir        = "/data/MRI/projects/temporal_bisection"
        project         = Project(proj_dir, globaldata)

        SESS_ID         = 1
        num_cpu         = 2

        TR              = 0.72
        num_slices      = 72
        time_bins       = 9     # 72/8
        slice_timing    = [310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5, 310.0, 0, 387.5, 77.5, 465.0, 155.0, 542.5, 232.5, 622.5]
        st_refslice     = 310
        hrf_derivatives = True
        fmri_params         = FmriProcParams(TR, num_slices, slice_timing, st_refslice, time_bins, hrf_deriv=True)
        fmri_params_noderiv = FmriProcParams(TR, num_slices, slice_timing, st_refslice, time_bins, hrf_deriv=False)

        hpf_er          = 100
        hpf_bl          = 100
        stim_duration   = 0

        contrasts_tempbis_er            = [ TContrast("bis",  "[1]")]
        contrasts_tempbis_bl            = [ TContrast("task",  "[1 0 0 0]"), TContrast("rest",  "[0 0 1 0]"), TContrast("task > rest",  "[1 0 -1 0]"), TContrast("rest > task",  "[-1 0 1 0]")]
        contrasts_tempbis_bl_noderiv    = [ TContrast("task",  "[1 0]"), TContrast("rest",  "[0 1]"), TContrast("task > rest",  "[1 -1]"), TContrast("rest > task",  "[-1 1]")]
        contrasts_tempbis_er_ctrl       = [ TContrast("task",  "[1 0 0 0]"), TContrast("rest",  "[0 0 1 0]"), TContrast("task > rest",  "[1 0 -1 0]"), TContrast("rest > task",  "[-1 0 1 0]")]

        # result_report     = SubjResultsParam(multcorr="none", pvalue=0.001, clustext=10, sessrep="none")
        result_report     = SubjResultsParam(multcorr="FWE", pvalue=0.05, clustext=10, sessrep="none")

        # ======================================================================================================================
        # PROCESSING
        # ======================================================================================================================
        def run_1stlevel_analysis(eng, proj:Project, subjects:list[Subject], cond_labels, hpf, block_dur, log_dirname, img_type, anal_name, fmri_par, contrasts, num_cpu):

            subjproj:Project = subjects[0].project
            slabels = []
            fmri_par.hpf    = hpf
            images_type     = img_type

            kwparams = []
            for s in subjects:
                slabels.append(s.label)
                rp_filenames = []
                input_images = []
                sessions_cond = []

                onset_file = os.path.join(proj.script_dir, "fmri", "logs", log_dirname, s.label + "-fmri" + ".mat")
                if os.path.exists(onset_file):
                    conditions = eng.load(onset_file)
                else:
                    print("onset file of subject " + s.label + " is not present....skipping subjects")
                    continue

                session = []
                for cond in cond_labels:

                    if block_dur is None:
                        session.append(SubjCondition(cond, sort(conditions["task_onsets"][cond]["onsets"][:]._data), asarray(conditions["task_onsets"][cond]["durations"][:]._data)))
                    else:
                        session.append(SubjCondition(cond, sort(conditions["task_onsets"][cond]["onsets"][:]._data), block_dur))
                sessions_cond.append(session)

                input_images.append(os.path.join(s.fmri_dir, img_type + s.label + "-fmri.nii"))
                rp_filenames.append(os.path.join(s.fmri_dir, "rp_" + s.label + "-fmri.txt"))

                kwparams.append({"analysis_name": anal_name, "fmri_params": fmri_par, "contrasts": contrasts, "res_report": result_report,
                                 "input_images": input_images, "conditions_lists": sessions_cond, "rp_filenames": rp_filenames})

            subjproj.load_subjects(slabels)
            subjproj.run_subjects_methods("epi", "spm_fmri_1st_level_analysis", kwparams, ncore=num_cpu)

        # ======================================================================================================================
        group_label     = "tempbis_er_with_ctrl"
        subjects        = subjproject.load_subjects(group_label, [SESS_ID])
        log_dirname     = "temp_bis_er_with_ctrl"
        subjproject.can_run_analysis("fmri")

        # kwparams = []
        # for s in subjects:
        #     kwparams.append({"fmri_params":fmri_params, "spm_template_name":"subj_spm_fmri_full_preprocessing"})
        # subjproject.run_subjects_methods("epi", "spm_fmri_preprocessing", kwparams, ncore=num_cpu)

        # def transform_roi(self, regtype, pathtype="standard", outdir="", outname="", mask="", orf="", thresh=0, islin=True, rois=None):
        # kwparams = []
        # for s in subjects:
            # kwparams.append({"regtype":"fmriTOstd", "pathtype":"abs", "outdir":s.fmri_dir, "islin":False, "rois":[Image(s.fmri_data).add_prefix2name("a")]})
        # project.run_subjects_methods("transform", "transform_roi", kwparams, ncore=num_cpu)

        # ---------------------------------------------------------------------------------------------------------------------
        import matlab.engine
        eng = matlab.engine.start_matlab()
        # ---------------------------------------------------------------------------------------------------------------------
        images_type     = "swar"

        # EVENT RELATED, hpf=100, stim_dur=0
        # run_1stlevel_analysis(eng, project, "tempbis_er" , ["tempbis_er"], hpf_er, stim_duration, images_type, "tempbis_er_swa", fmri_params, contrasts_tempbis_er, num_cpu)
        run_1stlevel_analysis(eng, project, [subjproject.get_subject_session("1041"), subjproject.get_subject_session("1043")], ["task", "rest"], hpf_er, stim_duration, log_dirname, images_type, "tempbis_er_ctrl_swar", fmri_params, contrasts_tempbis_er_ctrl, num_cpu)

        # BLOCK DESIGN, hpf=100, stim_dur=0
        # run_1stlevel_analysis(eng, project, "tempbis_blocks", ["task", "rest"], hpf_bl, None, images_type, "tempbis_bl_swa", fmri_params, contrasts_tempbis_bl, num_cpu)
        # run_1stlevel_analysis(eng, project, "tempbis_blocks", ["task", "rest"], hpf_bl, None, images_type, "tempbis_bl_swa_noderiv", fmri_params_noderiv, contrasts_tempbis_bl_noderiv, num_cpu)

    except Exception as e:
        traceback.print_exc()
        print(e)
        exit()

