%-----------------------------------------------------------------------
% Job saved on 20-Aug-2019 11:21:34 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.stats.con.spmmat = {'<SPM_MAT>'};
matlabbatch{1}.spm.stats.con.consess{1}.tcon.name = '<C1_NAME>';
matlabbatch{1}.spm.stats.con.consess{1}.tcon.weights = [1 -1];
matlabbatch{1}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
matlabbatch{1}.spm.stats.con.consess{2}.tcon.name = '<C2_NAME>';
matlabbatch{1}.spm.stats.con.consess{2}.tcon.weights = [-1 1];
matlabbatch{1}.spm.stats.con.consess{2}.tcon.sessrep = 'none';
matlabbatch{1}.spm.stats.con.delete = 1;
matlabbatch{2}.spm.stats.results.spmmat(1) = cfg_dep('Contrast Manager: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{2}.spm.stats.results.conspec.titlestr = '';
matlabbatch{2}.spm.stats.results.conspec.contrasts = Inf;
matlabbatch{2}.spm.stats.results.conspec.threshdesc = '<MULT_CORR>';
matlabbatch{2}.spm.stats.results.conspec.thresh = <PVALUE>;
matlabbatch{2}.spm.stats.results.conspec.extent = <CLUSTER_EXTEND>;
matlabbatch{2}.spm.stats.results.conspec.conjunction = 1;
matlabbatch{2}.spm.stats.results.conspec.mask.none = 1;
matlabbatch{2}.spm.stats.results.units = 1;
matlabbatch{2}.spm.stats.results.export{1}.csv = true;
matlabbatch{2}.spm.stats.results.export{2}.jpg = true;