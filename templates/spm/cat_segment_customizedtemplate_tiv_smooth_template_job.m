%-----------------------------------------------------------------------
% Job saved on 31-Jul-2019 15:02:02 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.tools.cat.estwrite.data = {'<T1_IMAGE>,1'};
matlabbatch{1}.spm.tools.cat.estwrite.nproc = <N_PROC>;
matlabbatch{1}.spm.tools.cat.estwrite.opts.tpm = {'<TEMPLATE_SEGMENTATION>,1'};
matlabbatch{1}.spm.tools.cat.estwrite.opts.affreg = 'mni';
matlabbatch{1}.spm.tools.cat.estwrite.opts.biasstr = 0.5;
matlabbatch{1}.spm.tools.cat.estwrite.opts.accstr = 0.5;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.APP = 1070;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.LASstr = 0.5;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.gcutstr = 2;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.registration.dartel.darteltpm = {'<TEMPLATE_COREGISTRATION>,1'};
matlabbatch{1}.spm.tools.cat.estwrite.extopts.vox = 1.5;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.restypes.fixed = [1 0.1];
matlabbatch{1}.spm.tools.cat.estwrite.output.surface = <CALC_SURFACES>;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.neuromorphometrics = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.lpba40 = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.cobra = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.hammers = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.dartel = 2;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.dartel = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.labelnative = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.bias.warped = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.jacobianwarped = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.warps = [0 0];
matlabbatch{2}.spm.tools.cat.tools.calcvol.data_xml(1) = cfg_dep('CAT12: Segmentation: CAT Report', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','catreport', '()',{':'}));
matlabbatch{2}.spm.tools.cat.tools.calcvol.calcvol_TIV = 1;
matlabbatch{2}.spm.tools.cat.tools.calcvol.calcvol_name = '<TIV_FILE>';
matlabbatch{3}.spm.spatial.smooth.data(1) = cfg_dep('CAT12: Segmentation: mwp1 Image', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','tiss', '()',{1}, '.','mwp', '()',{':'}));
matlabbatch{3}.spm.spatial.smooth.data(2) = cfg_dep('CAT12: Segmentation: mwp2 Image', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','tiss', '()',{2}, '.','mwp', '()',{':'}));
matlabbatch{3}.spm.spatial.smooth.fwhm = [8 8 8];
matlabbatch{3}.spm.spatial.smooth.dtype = 0;
matlabbatch{3}.spm.spatial.smooth.im = 0;
matlabbatch{3}.spm.spatial.smooth.prefix = 's';
