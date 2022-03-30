function prof = fmcw_bandlimit(prof, flow, fupp)

    % Frequencies
    freq_vector = linspace(prof.f0, prof.f1, numel(prof.t));

    if flow >= fupp
        error('fupp must be > than flow');
    end

    % Limits
    f0_idx = find(freq_vector >= flow, 1);
    f1_idx = find(freq_vector >= fupp, 1);

    if isempty(f0_idx)
        f0_idx = 1;
    end

    if isempty(f1_idx)
        f1_idx = numel(freq_vector);
    end

    freq_idx = f0_idx:f1_idx;
    freq_vector = freq_vector(freq_idx);
    prof.T = prof.t(f1_idx) - prof.t(f0_idx);
    prof.t = prof.t(freq_idx) - prof.t(f0_idx);
    prof.B = freq_vector(end) - freq_vector(1);
    prof.fc = (freq_vector(end) + freq_vector(1))/2;
    prof.vif = prof.vif(:, freq_idx);
    prof.f0 = freq_vector(1);
    prof.f1 = freq_vector(end);

    fprintf("New frequency range from %.2f MHz to %.2f MHz\n", ...
        prof.f0/1e6, prof.f1/1e6);

end