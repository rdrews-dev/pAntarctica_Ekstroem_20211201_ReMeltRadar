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
mean_pos = [
    mean(catalogue.latitude),
    mean(catalogue.longitude),
    mean(catalogue.elevation)
];

%% Now calculate ENU positions
xyz = lla2enu(...
    [catalogue.latitude, catalogue.longitude, catalogue.elevation],...
    mean_pos.', ...
    'ellipsoid');

% Get least squares positions to determine image plane
a = [xyz(:,1) ones(length(xyz),1)] \ xyz(:,2);

imgU = [1;a(1);0] / sqrt(1+a(1)^2);
imgV = [0;0;-1];
imgOrigin = ApRESProcessor.PositionENU([min(xyz(:,1));min(xyz(:,1))*a(1)+a(2);0]);
imgRes = 4;
imgSize = round([sqrt((max(xyz(:,1))-min(xyz(:,1))).^2 + (max(xyz(:,2))-min(xyz(:,2))).^2)/imgRes(1), 900/4]);

imgPlaneObj = ApRESProcessor.Imaging.ImagePlane(imgSize, imgU, imgV, imgRes, imgRes, imgOrigin);
img = ApRESProcessor.Imaging.ImagePlane(imgSize, imgU, imgV, imgRes, imgRes, imgOrigin);

velModel = ApRESProcessor.Imaging.ConstantVelocityModel(3.2);
int = ApRESProcessor.Imaging.InterpolatorBeamPattern(velModel, @(x) cos(x).^4 .* cos(x/3));
int.windowSize = 3;

fmcw = ApRESProcessor.FMCWProcessor(3e7, 2e7, 2);

time_start = datetime;

save_path = fullfile(PROC_ROOT, strcat("StopStart/interp_", datestr(datetime, "yyyymmdd_HHMMss"), ".mat"));
text = fileread(mfilename);
save_data = struct();
save_data.coordinate_origin = mean_pos;
save_data.source = text;
save_data.time_start;
save_data.tiem_interpolated = zeros(1, height(catalogue));

for k = 1:height(catalogue)
    
    profile = fmcw.load(char(fullfile(DATA_ROOT, catalogue.filename(k))));
    % assign positions
    profile.position = xyz(k,:);
    profile.rxPosition = xyz(k,:);
    profile.txPosition = xyz(k,:);
    
    tic
    int.interpolate(imgPlaneObj, profile, 2);
    save_data.time_interpolated(k) = toc;
    img.data = img.data + imgPlaneObj.data;

    img.draw(gca, @(x) 20*log10(abs(x)));
    drawnow
    fprintf("Done %d/%d\n", k, height(catalogue))

    save_data.image = img;
    save(save_path, '-struct', 'save_data')

end

time_stop = datetime;

save_data.time_stop = time_stop;
save_data.image = img;

save(save_path, '-struct', 'save_data')