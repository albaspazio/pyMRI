%-----------------------------------------------------------------------
% Job saved on 15-Sep-2019 15:00:13 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.tools.cat.tools.long.subj.mov = {
                                                    <T1_IMAGES>};
matlabbatch{1}.spm.tools.cat.tools.long.nproc = <N_PROC>;
matlabbatch{1}.spm.tools.cat.tools.long.opts.tpm = {'<TEMPLATE_SEGMENTATION>,1'};
matlabbatch{1}.spm.tools.cat.tools.long.opts.affreg = 'mni';
matlabbatch{1}.spm.tools.cat.tools.long.opts.biasstr = 0.5;
matlabbatch{1}.spm.tools.cat.tools.long.opts.accstr = 0.5;
matlabbatch{1}.spm.tools.cat.tools.long.extopts.APP = 1070;
matlabbatch{1}.spm.tools.cat.tools.long.extopts.LASstr = 0.5;
matlabbatch{1}.spm.tools.cat.tools.long.extopts.gcutstr = 2;
matlabbatch{1}.spm.tools.cat.tools.long.extopts.registration.dartel.darteltpm = {'<TEMPLATE_COREGISTRATION>,1'};
matlabbatch{1}.spm.tools.cat.tools.long.extopts.vox = 1.5;
matlabbatch{1}.spm.tools.cat.tools.long.extopts.restypes.fixed = [1 0.1];
matlabbatch{1}.spm.tools.cat.tools.long.output.surface = <CALC_SURFACES>;
matlabbatch{1}.spm.tools.cat.tools.long.ROImenu.atlases.neuromorphometrics = 1;
matlabbatch{1}.spm.tools.cat.tools.long.ROImenu.atlases.lpba40 = 0;
matlabbatch{1}.spm.tools.cat.tools.long.ROImenu.atlases.cobra = 0;
matlabbatch{1}.spm.tools.cat.tools.long.ROImenu.atlases.hammers = 0;
matlabbatch{1}.spm.tools.cat.tools.long.modulate = 1;
matlabbatch{1}.spm.tools.cat.tools.long.dartel = 0;
matlabbatch{2}.spm.spatial.smooth.data(1) = cfg_dep('Segment longitudinal data: Segmented longitudinal data (Subj 1)', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','sess', '()',{1}, '.','files'));
matlabbatch{2}.spm.spatial.smooth.fwhm = [8 8 8];
matlabbatch{2}.spm.spatial.smooth.dtype = 0;
matlabbatch{2}.spm.spatial.smooth.im = 0;
matlabbatch{2}.spm.spatial.smooth.prefix = 's';
<SURF_RESAMPLE>
<ICV_CALCULATION>
