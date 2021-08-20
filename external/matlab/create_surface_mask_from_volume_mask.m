% extract coordinates of all voxels contained in the given mask
function create_surface_mask_from_volume_mask(ref_surface, vmask, out_surf)

    dist = 5;   % distance

    % get coordinates of mask's voxels
    xyzCoordinates  = extract_coordinates_from_mask(vmask);
    ncoord          = length(xyzCoordinates);

    surf            = gifti(ref_surface);
    nvertex         = length(surf.cdata);

    % create another gifti image with zeros
    mask_surf       = gifti(ref_surface);
    mask_surf.cdata = zeros(nvertex,1);
    dispstat('','init')
    for v=1:nvertex
        for r=1:ncoord
            d = sqrt(sum((xyzCoordinates(:,r) - surf.vertices(v,:)') .^ 2));
            if(d < dist)    
                mask_surf.cdata(v) = 1;
                disp("added vertex " + v)
                break
            end
        end
    end
    save(mask_surf, out_surf, 'Base64Binary');
end