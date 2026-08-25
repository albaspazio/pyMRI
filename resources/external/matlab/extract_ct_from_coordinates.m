function values = extract_ct_from_coordinates(subjs_files, coords_mni, radius_mm, cat_template_folder)

    if nargin < 4
        cat_template_folder = '/data/CODE/MATLAB/toolboxes/spm12/toolbox/cat12/templates_surfaces_32k';
    end
    
    % Template surfaces (MNI-like space)
    lh_surf = gifti(fullfile(cat_template_folder, 'lh.central.Template_T1.gii'));
    rh_surf = gifti(fullfile(cat_template_folder, 'rh.central.Template_T1.gii'));
    
    vertices = [lh_surf.vertices; rh_surf.vertices];  % Combine hemispheres
    
    n_coords   = size(coords_mni, 1);
    n_vertices = size(vertices, 1);
    
    % ----- LOAD SUBJECT FILES -----
    nSubjects = size(subjs_files, 2);
    
    % Output matrix: rows = subjects, columns = MNI coordinates
    values = zeros(nSubjects, n_coords);
    
    % ----- MAIN LOOP -----
    for c = 1:n_coords
        coord = coords_mni(c, :);
        
        % Compute distances from this coordinate to all vertices
        dists = sqrt(sum((vertices - coord).^2, 2));
        
        % Find all vertices within the radius
        roi_indices = find(dists <= radius_mm);
        
        fprintf('Coordinate %d: %d vertices found within %.1f mm\n', c, numel(roi_indices), radius_mm);
        
        % Loop through subjects and extract mean CT in ROI
        for s = 1:nSubjects
            G = gifti(subjs_files{1,s});
            ct_data = G.cdata;
            roi_vals = ct_data(roi_indices);
            values(s, c) = mean(roi_vals, 'omitnan');
        end
    end
end
