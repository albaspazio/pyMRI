function [clusters_value, vertexmeans] = get_subjects_cluster_data_by_ids(subjects, cluster_ids, subjects_dir)

    n_subjects      = length(subjects);
    n_vertex        = length(cluster_ids);

    clusters_value  = zeros(n_subjects, n_vertex);


    for s=1:n_subjects

        filename    = subjects_dir + '/' + subjects{s} + '/s1/mpr/anat/cat_proc/surf/s15.mesh.thickness.resampled_32k.T1_' + subjects{s} + '.gii';
        g           = gifti(cellstr(filename));

        clusters_value(s,:) = g.cdata(cluster_ids);
    end

    vertexmeans = mean(clusters_value,1);






