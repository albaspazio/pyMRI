%-----------------------------------------------------------------------
% Job saved on 12-Aug-2019 16:41:10 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.stats.factorial_design.dir = {'<STATS_DIR>'};

matlabbatch{1}.spm.stats.factorial_design.des.t2.scans1 = <GROUP1_IMAGES>;


matlabbatch{1}.spm.stats.factorial_design.des.t2.scans2 = <GROUP2_IMAGES>;

matlabbatch{1}.spm.stats.factorial_design.des.t2.dept = 0;
matlabbatch{1}.spm.stats.factorial_design.des.t2.variance = 1;
matlabbatch{1}.spm.stats.factorial_design.des.t2.gmsca = 0;
matlabbatch{1}.spm.stats.factorial_design.des.t2.ancova = 0;





<COV_STRING>
matlabbatch{1}.spm.stats.factorial_design.multi_cov = struct('files', {}, 'iCFI', {}, 'iCC', {});
<FACTDES_MASKING>
<FACTDES_GLOBAL>
matlabbatch{2}.spm.stats.review.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{2}.spm.stats.review.display.matrix = 1;
matlabbatch{2}.spm.stats.review.print = 'ps';
matlabbatch{3}.spm.tools.cat.tools.check_SPM.spmmat(1) = cfg_dep('Factorial design specification: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{3}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.use_unsmoothed_data = 1;
matlabbatch{3}.spm.tools.cat.tools.check_SPM.check_SPM_cov.do_check_cov.adjust_data = 1;
matlabbatch{3}.spm.tools.cat.tools.check_SPM.check_SPM_ortho = 1;
<MODEL_ESTIMATE>
matlabbatch{5}.spm.stats.con.spmmat(1) = cfg_dep('Model estimation: SPM.mat File', substruct('.','val', '{}',{3}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{5}.spm.stats.con.consess{1}.tcon.name = '<C1_NAME>';
matlabbatch{5}.spm.stats.con.consess{1}.tcon.weights = [1 -1];
matlabbatch{5}.spm.stats.con.consess{1}.tcon.sessrep = 'none';
matlabbatch{5}.spm.stats.con.consess{2}.tcon.name = '<C2_NAME>';
matlabbatch{5}.spm.stats.con.consess{2}.tcon.weights = [-1 1];
matlabbatch{5}.spm.stats.con.consess{2}.tcon.sessrep = 'none';
matlabbatch{5}.spm.stats.con.delete = 0;
matlabbatch{6}.spm.stats.results.spmmat(1) = cfg_dep('Contrast Manager: SPM.mat File', substruct('.','val', '{}',{4}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{6}.spm.stats.results.conspec.titlestr = '';
matlabbatch{6}.spm.stats.results.conspec.contrasts = Inf;
matlabbatch{6}.spm.stats.results.conspec.threshdesc = '<MULT_CORR>';
matlabbatch{6}.spm.stats.results.conspec.thresh = <PVALUE>;
matlabbatch{6}.spm.stats.results.conspec.extent = <CLUSTER_EXTEND>;
matlabbatch{6}.spm.stats.results.conspec.conjunction = 1;
matlabbatch{6}.spm.stats.results.conspec.mask.none = 1;
matlabbatch{6}.spm.stats.results.units = 1;
matlabbatch{6}.spm.stats.results.export{1}.csv = true;
matlabbatch{6}.spm.stats.results.export{2}.jpg = true;