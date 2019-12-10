% returns list of vertexes > 0
function vertexes_id = get_cluster_ids(cluster)

    % get list of vertex to explore
    ref             = gifti(cluster);
    vertexes_id     = find(ref.cdata>0);





