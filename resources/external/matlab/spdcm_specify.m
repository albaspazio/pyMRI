%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% specify DCM
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function dcm_specify(dcm_dir_path, name, outname, roi_list, te, a_matrix)

    clear DCM

    dcm_folder      = fullfile(dcm_dir_path, name);
    dcm_output_file = fullfile(dcm_folder, "DCM_" + outname);

    load(fullfile(dcm_folder,'SPM.mat'));
    
    for r = 1:length(roi_list)
        load(fullfile(dcm_folder, roi_list{r}) ,'xY');
        DCM.xY(r) = xY;
    end
    
    DCM.n = length(DCM.xY);      % number of regions
    DCM.v = length(DCM.xY(1).u); % number of time points
    
    DCM.Y.dt  = SPM.xY.RT;
    DCM.Y.X0  = DCM.xY(1).X0;

    for i = 1:DCM.n
        DCM.Y.y(:,i)  = DCM.xY(i).u;
        DCM.Y.name{i} = DCM.xY(i).name;
    end
    
    DCM.Y.Q    = spm_Ce(ones(1, DCM.n)*DCM.v);
    
    DCM.U.idx  = 0;
    DCM.U.name = {'RS'}; 
    DCM.U.u    = ones(1, DCM.v);
    
    DCM.delays = repmat(SPM.xY.RT/2, DCM.n,1);
    DCM.TE     = te;
    
    DCM.options.nonlinear  = 0;
    DCM.options.two_state  = 0;
    DCM.options.stochastic = 0;
    DCM.options.centre     = 0;
    DCM.options.nograph    = 0;
    
    DCM.options.induced    = 1;

    if nargin < 6
        DCM.a = ones(length(roi_list));
    else
        DCM.a = a_matrix;
    end
    
    DCM.b = zeros(length(roi_list));
    DCM.c = zeros(length(roi_list),1);
    DCM.d = [];
    
    save(dcm_output_file, 'DCM');
    
    % ESTIMATION
    %--------------------------------------------------------------------------
    DCM_DMN = spm_dcm_fmri_csd(dcm_output_file);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
