%-----------------------------------------------------------------------
% used by SubjectEpi.get_closest_volume
%-----------------------------------------------------------------------
%%
matlabbatch{1}.spm.spatial.realign.estimate.data = {
                                                    {
'<REF_IMAGE,refvol>'
<TO_ALIGN_IMAGES,1-n_vols>
                                                    }
                                                   };
%%
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.quality = 0.9;
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.sep = 4;
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.fwhm = 5;
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.rtm = 0;
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.interp = 2;
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.wrap = [0 0 0];
matlabbatch{1}.spm.spatial.realign.estimate.eoptions.weight = '';
