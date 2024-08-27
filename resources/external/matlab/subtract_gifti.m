% call stats estimate for surfaces

function subtract_gifti(left_surf, right_surf, res_surf)

    s_l = gifti(left_surf);
    s_r = gifti(right_surf);
    s_diff = gifti(left_surf);

    s_diff.cdata = s_l.cdata - s_r.cdata;
    save(s_diff, res_surf, 'Base64Binary');
