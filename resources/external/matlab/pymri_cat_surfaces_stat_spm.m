% call stats estimate for surfaces

function pymri_cat_surfaces_stat_spm(file_path)

    load(fullfile(file_path,'SPM.mat'));
    SPM.swd  = file_path; 
    cat_stat_spm(SPM);