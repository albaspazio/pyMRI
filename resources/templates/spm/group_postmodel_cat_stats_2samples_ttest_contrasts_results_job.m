%-----------------------------------------------------------------------
% Job saved on 20-Aug-2019 11:21:34 by cfg_util (rev $Rev: 7345 $)
% spm SPM - SPM12 (7487)
% cfg_basicio BasicIO - Unknown
%-----------------------------------------------------------------------
matlabbatch{1}.spm.tools.cat.stools.con.spmmat = {'<SPM_MAT>'};
matlabbatch{1}.spm.tools.cat.stools.con.consess{1}.tcon.name = '<C1_NAME>';
matlabbatch{1}.spm.tools.cat.stools.con.consess{1}.tcon.weights = [1 -1];
matlabbatch{1}.spm.tools.cat.stools.con.consess{1}.tcon.sessrep = 'none';
matlabbatch{1}.spm.tools.cat.stools.con.consess{2}.tcon.name = '<C2_NAME>';
matlabbatch{1}.spm.tools.cat.stools.con.consess{2}.tcon.weights = [-1 1];
matlabbatch{1}.spm.tools.cat.stools.con.consess{2}.tcon.sessrep = 'none';
matlabbatch{1}.spm.tools.cat.stools.con.delete = 1;
matlabbatch{2}.spm.tools.cat.stools.results.spmmat(1) = cfg_dep('Contrast Manager: SPM.mat File', substruct('.','val', '{}',{1}, '.','val', '{}',{1}, '.','val', '{}',{1}), substruct('.','spmmat'));
matlabbatch{2}.spm.tools.cat.stools.results.conspec.titlestr = '';
matlabbatch{2}.spm.tools.cat.stools.results.conspec.contrasts = Inf;
matlabbatch{2}.spm.tools.cat.stools.results.conspec.threshdesc = '<MULT_CORR>';
matlabbatch{2}.spm.tools.cat.stools.results.conspec.thresh = <PVALUE>;
matlabbatch{2}.spm.tools.cat.stools.results.conspec.extent = <CLUSTER_EXTEND>;
matlabbatch{2}.spm.tools.cat.stools.results.conspec.conjunction = 1;
matlabbatch{2}.spm.tools.cat.stools.results.conspec.mask.none = 1;
matlabbatch{2}.spm.tools.cat.stools.results.units = 1;
matlabbatch{2}.spm.tools.cat.stools.results.export{1}.csv = true;
matlabbatch{2}.spm.tools.cat.stools.results.export{2}.jpg = true;

%matlabbatch{3}.spm.tools.cat.tools.T2x_surf.data_T2x = {
%                                                        '<STATS_DIR>/spmT_0001.gii'
%                                                        '<STATS_DIR>/spmT_0002.gii'
%                                                        };
%matlabbatch{3}.spm.tools.cat.tools.T2x_surf.conversion.sel = 2;
%<CAT_T_CONV_THRESHOLD>
%matlabbatch{3}.spm.tools.cat.tools.T2x_surf.conversion.inverse = 0;
%<CAT_T_CONV_CLUSTER>
