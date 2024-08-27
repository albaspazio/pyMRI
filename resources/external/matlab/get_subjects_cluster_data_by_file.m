function [vertexes_id, clusters_value, vertexmeans] = get_subjects_cluster_data_by_file(subjects, cluster, subjects_dir)

    n_subjects  = length(subjects);

    % get list of vertex to explore
    ref             = gifti(cluster);
    vertexes_id     = find(ref.cdata>0);
    n_vertex        = length(vertexes_id);

    clusters_value = zeros(n_subjects, n_vertex);


    for s=1:n_subjects

        filename    = subjects_dir + '/' + subjects{s} + '/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_' + subjects{s} + '.gii';
        g           = gifti(cellstr(filename));

        clusters_value(s,:) = g.cdata(vertexes_id);
    end

    vertexmeans = mean(clusters_value,1);


