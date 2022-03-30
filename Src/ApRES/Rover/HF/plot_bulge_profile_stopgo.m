%% Check for interference in the ApRES data from the rover RTK GPS
%   
%   For data collected by JH and RE at Bulge Location (Ekstrom)
%
%   REQUIRES:
%   -   KWN/CS fmcw_load and fmcw_nbursts scripts

% data_folder = '../data/2021-12-07/Unattended_withRTKtest_DIR2021-12-06-1116';
% data_folder = '../data/2022-01-07-hf-apres-bulge-profile';
ROOT = '../../../../';
data_folder = fullfile(ROOT, 'Raw/ApRES/Rover/HF/StartStop');

if ~exist(data_folder,'dir')
    error("Couldn't find the folder %s\nHas the data been downloaded?", data_folder)
end

% Get bursts in folder
bursts = dir([data_folder, '/*.dat']);

% Get number of files
Nfiles = numel(bursts);

data = [];
time = zeros(1, Nfiles);

for k = 1:Nfiles
    prof = fmcw_load(fullfile(bursts(k).folder, bursts(k).name));
    [rc,~,sc,~] = fmcw_range(prof, 2, 1500);
    time(k) = prof.TimeStamp;
    if isempty(data)
        data = mean(sc);
    else
        data(end+1,:) = mean(sc);
    end
%     subplot(1,2,1)
    imagesc(20*log10(abs(data)).')
%     sound((mean(prof.vif,1)-mean(prof.vif,'all'))/1.25, 80e3)
%     pause(0.5)
    
%     subplot(1,2,2)
%     plot(mean(prof.vif,1).' + k, 1:40000, 'k')

    title(bursts(k).name)
    drawnow
end

[time, sidx] = sort(time);
data = data(sidx,:);

%%
% Min Max Range
minr = find(rc >= 760,1);
maxr = find(rc >= 830,1);
maxpower = zeros(1, Nfiles);

for k = 1:Nfiles
    [mv,mi] = max(20*log10(abs(data(k,minr:maxr))));
    maxpower(k) = mv;
end

figure(1)
plot(1:Nfiles, maxpower)

figure(2)
%%
subplot(1,2,1)
imagesc(1:Nfiles, rc, 20*log10(abs(data)).');
% imagesc(1:Nfiles, rc, 20*log10(abs(data)).' - maxpower);
colorbar
colormap bone
caxis([-100 0])
xlabel('Profile Index')
ylabel('Depth (m)')
title('Power')

subplot(1,2,2)
p_coeff = 0.25;
power_norm = abs(data).^p_coeff ./ max(abs(data).^(abs(data).^0.5).^p_coeff, [], 'all');
imagesc(1:Nfiles, rc, -(angle(data)).', 'AlphaData', power_norm.');
colorbar
colormap(subplot(1,2,2),'hsv')
xlabel('Profile Index')
ylabel('Depth (m)')
title('Phase (Power Transparency)')