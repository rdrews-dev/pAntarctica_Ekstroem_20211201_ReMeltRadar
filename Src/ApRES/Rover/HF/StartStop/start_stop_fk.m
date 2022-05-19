% Process start stop basal survey
%
%   Auth: J.D. Hawkins
%   Date: 2022-03-01
%
clear all

PROJECT_ROOT = "../../../../..";
DATA_ROOT = fullfile(PROJECT_ROOT, "Raw/ApRES/Rover/HF/StartStop");
PROC_ROOT = fullfile(PROJECT_ROOT, "Proc/ApRES/Rover/HF");

catalogue_path = fullfile(PROC_ROOT, "StopStart", "start_stop_rtk.csv");

catalogue = readtable(catalogue_path);

%% Determine Mean Position for Survey
% mean_pos = [
%     mean(catalogue.latitude),
%     mean(catalogue.longitude),
%     mean(catalogue.elevation)
% ];
% 
% %% Now calculate ENU positions
% xyz = lla2enu(...
%     [catalogue.latitude, catalogue.longitude, catalogue.elevation],...
%     mean_pos.', ...
%     'ellipsoid');

addpath(fullfile(PROJECT_ROOT, 'Src/RTKGPS/ApRES/Rover/HF'));

[x,y,z] = interp_hf_rover_rtkdata(datetime(catalogue.timestamp));
xyz = [x y z];

fmcw = ApRESProcessor.FMCWProcessor(3e7, 2e7, 2);

raw_image = [];

for k = 1:height(catalogue)
    
    fname = char(fullfile(DATA_ROOT, catalogue.filename(k)))

    if ~exist(fname, 'file')
        continue
    end

    profile = fmcw.load(fname);

    if isempty(raw_image)
        raw_image = profile.voltageSignal;
    else
        raw_image(:,end+1) = profile.voltageSignal;
    end
    
    range = xyz(k,3) - profile.rangeTime*physconst('lightspeed')/(2*sqrt(3.2));
    
    range_lim = range > -900;
    
    subplot(1,2,1)
    imagesc(xyz(k,2) + [-0.5 0.5], range(range_lim), 20*log10(abs(profile.rangeProfile(range_lim))));
    hold on
    xlim([min(xyz(:,2)) max(xyz(:,2))])
    subplot(1,2,2)
    imagesc(xyz(k,2) + [-0.5 0.5], range(range_lim), (angle(profile.rangeProfile(range_lim))));
    hold on
    xlim([min(xyz(:,2)) max(xyz(:,2))])
    drawnow
    
end

set(gca,'ydir','normal')