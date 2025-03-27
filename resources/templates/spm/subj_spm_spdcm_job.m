%-----------------------------------------------------------------------
% Job saved on 21-Mar-2025 10:58:43 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7771)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.stats.fmri_spec.dir = {<DCM_PREPROC_DIR>};
matlabbatch{1}.spm.stats.fmri_spec.timing.units = 'scans';
matlabbatch{1}.spm.stats.fmri_spec.timing.RT = <TR_VALUE>;
matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t = <FMRI_T>;
matlabbatch{1}.spm.stats.fmri_spec.timing.fmri_t0 = <FMRI_T0>;
%%
matlabbatch{1}.spm.stats.fmri_spec.sess.scans = <FMRI_IMAGES>;
%%
matlabbatch{1}.spm.stats.fmri_spec.sess.cond = struct('name', {}, 'onset', {}, 'duration', {}, 'tmod', {}, 'pmod', {}, 'orth', {});
matlabbatch{1}.spm.stats.fmri_spec.sess.multi = {''};
matlabbatch{1}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
matlabbatch{1}.spm.stats.fmri_spec.sess.multi_reg = {''};
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

matlabbatch{3}.spm.util.voi.spmmat(1) = cfg_dep('Model estimation: SPM.mat File', substruct('.','val', '{}',{2}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{3}.spm.util.voi.adjust = NaN;
matlabbatch{3}.spm.util.voi.session = 1;
matlabbatch{3}.spm.util.voi.name = 'CSF';
matlabbatch{3}.spm.util.voi.roi{1}.sphere.centre = <CSF_COORD>;
matlabbatch{3}.spm.util.voi.roi{1}.sphere.radius = 6;
matlabbatch{3}.spm.util.voi.roi{1}.sphere.move.fixed = 1;
matlabbatch{3}.spm.util.voi.roi{2}.mask.image = {<MASK_IMAGE>};
matlabbatch{3}.spm.util.voi.roi{2}.mask.threshold = 0.5;
matlabbatch{3}.spm.util.voi.expression = 'i1&i2';

matlabbatch{4}.spm.util.voi.spmmat(1) = cfg_dep('Model estimation: SPM.mat File', substruct('.','val', '{}',{2}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{4}.spm.util.voi.adjust = NaN;
matlabbatch{4}.spm.util.voi.session = 1;
matlabbatch{4}.spm.util.voi.name = 'WM';
matlabbatch{4}.spm.util.voi.roi{1}.sphere.centre = <WM_COORD>;
matlabbatch{4}.spm.util.voi.roi{1}.sphere.radius = 6;
matlabbatch{4}.spm.util.voi.roi{1}.sphere.move.fixed = 1;
matlabbatch{4}.spm.util.voi.roi{2}.mask.image = {<MASK_IMAGE>};
matlabbatch{4}.spm.util.voi.roi{2}.mask.threshold = 0.5;
matlabbatch{4}.spm.util.voi.expression = 'i1&i2';

matlabbatch{5}.spm.stats.fmri_spec.dir = {<DCM_DIR>};
matlabbatch{5}.spm.stats.fmri_spec.timing.units = 'scans';
matlabbatch{5}.spm.stats.fmri_spec.timing.RT = <TR_VALUE>;
matlabbatch{5}.spm.stats.fmri_spec.timing.fmri_t = <FMRI_T>;
matlabbatch{5}.spm.stats.fmri_spec.timing.fmri_t0 = <FMRI_T0>;
%%
matlabbatch{5}.spm.stats.fmri_spec.sess.scans = <FMRI_IMAGES>;
%%
matlabbatch{5}.spm.stats.fmri_spec.sess.cond = struct('name', {}, 'onset', {}, 'duration', {}, 'tmod', {}, 'pmod', {}, 'orth', {});
matlabbatch{5}.spm.stats.fmri_spec.sess.multi = {''};
matlabbatch{5}.spm.stats.fmri_spec.sess.regress = struct('name', {}, 'val', {});
matlabbatch{5}.spm.stats.fmri_spec.sess.multi_reg = <NUISANCE_FILES>;
matlabbatch{5}.spm.stats.fmri_spec.sess.hpf = 128;
matlabbatch{5}.spm.stats.fmri_spec.fact = struct('name', {}, 'levels', {});
matlabbatch{5}.spm.stats.fmri_spec.bases.hrf.derivs = [0 0];
matlabbatch{5}.spm.stats.fmri_spec.volt = 1;
matlabbatch{5}.spm.stats.fmri_spec.global = 'None';
matlabbatch{5}.spm.stats.fmri_spec.mthresh = 0.8;
matlabbatch{5}.spm.stats.fmri_spec.mask = {''};
matlabbatch{5}.spm.stats.fmri_spec.cvi = 'AR(1)';

matlabbatch{6}.spm.stats.fmri_est.spmmat(1) = cfg_dep('fMRI model specification: SPM.mat File', substruct('.','val', '{}',{5}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{6}.spm.stats.fmri_est.write_residuals = 0;
matlabbatch{6}.spm.stats.fmri_est.method.Classical = 1;

<ROIS_IMAGES>
