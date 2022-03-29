% Process start stop basal survey
%
%   Auth: J.D. Hawkins
%   Date: 2022-03-01
%
clear all

PROJECT_ROOT = "../../../../..";
DATA_ROOT = fullfile(PROJECT_ROOT, "Raw/ApRES/Rover/HF/StartStop");
PROC_ROOT = fullfile(PROJECT_ROOT, "Proc/ApRES/Rover/HF");

catalogue_path = fullfile(PROC_ROOT, "stop_start_rtk.csv");

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

[x,y,z] = interp_hf_rover_rtkdata(datetime(data(:, TBL_TS)));
xyz = [x y z];

fmcw = ApRESProcessor.FMCWProcessor(3e7, 2e7, 2);

for k = 1:height(catalogue)
    
    profile = fmcw.load(char(fullfile(DATA_ROOT, catalogue.filename(k))));
    
    range = xyz(k,3) - profile.rangeTime*physconst('lightspeed')/(2*sqrt(3.2));
    
    range_lim = range > -900;
    
    subplot(1,2,1)
    imagesc(xyz(k,1), range(range_lim), 20*log10(abs(profile.rangeProfile(range_lim))));
    hold on
    
end

set(gca,'ydir','normal')