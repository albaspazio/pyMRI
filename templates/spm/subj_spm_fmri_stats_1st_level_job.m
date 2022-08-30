%-----------------------------------------------------------------------
% Job saved on 10-Sep-2019 15:00:40 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.stats.fmri_spec.dir = {'<SPM_DIR>'};
matlabbatch{1}.spm.stats.fmri_spec.timing.units = '<EVENTS_UNIT>';
matlabbatch{1}.spm.stats.fmri_spec.timing.RT = <TR_VALUE>;
matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = <MICROTIME_RES>;
matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = <MICROTIME_ONSET>;
matlabbatch{1}.spm.stats.fmri_spec.sess.scans = {<SMOOTHED_VOLS>};
<CONDITION_STRING>
matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {'<MOTION_PARAMS>'};
matlabbatch{1}.spm.stats.fmri_spec.sess.hpf = 128;
matlabbatch{1}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
matlabbatch{1}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];
matlabbatch{1}.spm.stats.fmri_spec.volt = 1;
matlabbatch{1}.spm.stats.fmri_spec.global = 'None';
matlabbatch{1}.spm.stats.fmri_spec.mthresh = 0.8;
matlabbatch{1}.spm.stats.fmri_spec.mask = {''};
matlabbatch{1}.spm.stats.fmri_spec.cvi = 'AR(1)';

matlabbatch{2}.spm.stats.fmri_est.spmmat(1) = cfg_dep('fMRI model specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{2}.spm.stats.fmri_est.write_residuals = 0;
matlabbatch{2}.spm.stats.fmri_est.method.Classical = 1;

<CONTRASTS>

<RESULTS_REPORT>
