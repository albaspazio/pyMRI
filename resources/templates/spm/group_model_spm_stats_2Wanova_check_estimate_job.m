%-----------------------------------------------------------------------
% Job saved on 16-Sep-2019 09:47:12 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.stats.factorial_design.dir = {'<STATS_DIR>'};
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(1).name = '<FACTOR1_NAME>';
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(1).levels = <FACTOR1_NLEV>;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(1).dept = 0;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(1).variance = 1;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(1).gmsca = 0;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(1).ancova = 0;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(2).name = '<FACTOR2_NAME>';
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(2).levels = <FACTOR2_NLEV>;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(2).dept = 0;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(2).variance = 1;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(2).gmsca = 0;
matlabbatch{1}.spm.stats.factorial_design.des.fd.fact(2).ancova = 0;
<FACTORS_CELLS>
matlabbatch{1}.spm.stats.factorial_design.des.fd.contrasts = 1;

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

