function spm_display_image(image)

    matlabbatch{1}.spm.util.disp.data = {image};
    spm_jobman('run', matlabbatch)