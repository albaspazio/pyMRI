function best_vol = least_mov(path)

    parameters      = dlmread(path)
    parameters_abs  = abs(parameters)
    volumes         = [0:size(parameters_abs,1)-1].'
    vols_parameters = [volumes parameters_abs]
    best_vol        = 1
    least_sum       = sum(vols_parameters(2,5:7))

    for vol = 1:vols_parameters(end,1)
        total_mov_sum = sum(vols_parameters(vol+1,5:7))
        if total_mov_sum < least_sum
            best_vol    = vol
            least_sum   = total_mov_sum
        end
    end
    fprintf ('The best volume is %i. \n',best_vol)
end

