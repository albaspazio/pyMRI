function remove_vars_from_mat(mat_file)
    load(mat_file);

    save(mat_file, "connectivity")
