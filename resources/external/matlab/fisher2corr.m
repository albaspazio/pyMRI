function r = fisher2corr(r_fisher)
    r = (exp(2 * r_fisher) - 1) ./ (exp(2 * r_fisher) + 1);
end