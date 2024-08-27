% This example prompts the user to select one subject functional series
% (one resting state session) and one anatomical volume, and performs all 
% standard SPM preprocessing steps (realignment,coregistration,
% normalization,smoothing, etc.) and connectivity analyses using all default atlas ROIs

function conn_batch_create_project(inputmat, projpath, subjects, tr, varargin)
    
    projname = 'conn_proj.mat';
    display  = true;
    sess_id  = 1;
    simulate = true;
    for par=1:2:length(varargin)
        switch varargin{par}
            case {'sess_id', 'projname', 'display', 'simulate'}
                
                if isempty(varargin{par+1})
                    continue;
                else
                    assign(varargin{par}, varargin{par+1});
                end
        end
    end

%     load(inputmat);


    nsubj                   = length(subjects);
    CONN_x.name             = "col";
    CONN_x.filename          = fullfile(projpath, projname);
    CONN_x.Setup.nsubjects   = nsubj;

    for s=1:nsubj

        subj_label    = subjects{s};
        subj_sess_dir = fullfile(projpath, "subjects", subj_label, strcat('s',num2str(sess_id)));
        t1            = fullfile(subj_sess_dir, 'mpr', strcat(subj_label, '-t1.nii'));
        rs            = fullfile(subj_sess_dir, 'rs', strcat(subj_label, '-rs.nii'));

        if ~simulate
            assert( isfile(t1), strcat('anatomical image of subj: ', subj_label, ' does not exist...exiting'));
            assert( isfile(rs), strcat('resting state image of subj: ', subj_label, ' does not exist...exiting'));
        end

        CONN_x.Setup.structurals{s}    = t1;
        CONN_x.Setup.functionals{s}{1} = rs;

        CONN_x.Setup.conditions.onsets{1}{s}{1}=0; 
        CONN_x.Setup.conditions.durations{1}{s}{1}=inf;        

    end

    CONN_x.Setup.RT=tr;
    CONN_x.Setup.rois.names={'atlas'};
    CONN_x.Setup.rois.files{1}=fullfile(fileparts(which('conn')),'rois','atlas.nii');
    CONN_x.Setup.conditions.names={'rest'};       
%     CONN_x.Setup.voxelresolution=1;                          % default 2mm isotropic voxels analysis space
%     CONN_x.Setup.preprocessing.steps={}; % user-ask 
    CONN_x.Setup.isnew=1;
    CONN_x.Setup.done=0;
    %% CONN Denoising
%     CONN_x.Denoising.filter=[0.01, 0.1];          % frequency filter (band-pass values, in Hz)
%     CONN_x.Denoising.done=1;
    %% CONN Analysis


%     CONN_x.Setup.outputfiles=[0,1,0,0,0,0];                  % creates d*.nii denoised output files
%     CONN_x.Setup.analyses=[1,2];                             % seed-to-voxel and ROI-to-ROI pipelines
%     CONN_x.Setup.overwrite='Yes';                            
%     CONN_x.Setup.done=1;

%     CONN_x.Setup.preprocessing.steps={'structural_segment','functional_art','functional_smooth'};  % Run additional preprocessing steps: segmentation,ART,smoothing
%     CONN_x.Setup.preprocessing.fwhm=6;                       % smoothing fwhm (mm)

%     CONN_x.Analysis.analysis_number=1;       % Sequential number identifying each set of independent first-level analyses
%     CONN_x.Analysis.measure=1;               % connectivity measure used {1 = 'correlation (bivariate)', 2 = 'correlation (semipartial)', 3 = 'regression (bivariate)', 4 = 'regression (multivariate)';
%     CONN_x.Analysis.weight=2;                % within-condition weight used {1 = 'none', 2 = 'hrf', 3 = 'hanning';
%     CONN_x.Analysis.sources={};              % (defaults to all ROIs)
%     CONN_x.Analysis.done=1;
    
     save(CONN_x.filename, "CONN_x",'-mat');
    conn_batch(CONN_x);
    
    if display
        %% CONN Display
        % launches conn gui to explore results
        conn
        conn('load',fullfile(pwd,'conn_singlesubject01.mat'));
        conn gui_results
    end

end