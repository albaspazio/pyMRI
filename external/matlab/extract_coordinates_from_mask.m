% extract coordinates of all voxels contained in the given mask
% needs marsbar package
function xyzCoordinates = extract_coordinates_from_mask(vmask)

    [filepath,name,ext] = fileparts(vmask);
    roipath             = my_mars_img2rois(vmask, filepath, 'rois','c');
    sphereInfo          = maroi(roipath);
    volumeInfo          = spm_vol(vmask);
    xyzCoordinates      = realpts(sphereInfo,volumeInfo);


    