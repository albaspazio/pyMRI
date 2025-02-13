function create_dsi_matrix_from_files(input_dir, nnodes, fish2r)
    files = dir(input_dir);
    nsubj = length(files) - 2; % remove . and ..
    conn_mat = zeros(nnodes, nnodes, nsubj);
    s=0;
    for f=1:length(files)
        if ~files(f).isdir
            s=s+1;
            load(fullfile(input_dir, files(f).name));

            if fish2r == 1
                connectivity = arrayfun(@fisher2corr, connectivity);
            end
            conn_mat(:,:, s) = connectivity;
        end
    end
    save(fullfile(input_dir, "matrices.mat"), "conn_mat")
end