% Process start stop basal survey
%
%   Auth: J.D. Hawkins
%   Date: 2022-03-01
%
clear all

PROJECT_ROOT = "../../../../..";
DATA_ROOT = fullfile(PROJECT_ROOT, "Raw/ApRES/Rover/HF/StartStop");
PROC_ROOT = fullfile(PROJECT_ROOT, "Proc/ApRES/Rover/HF");

apres_db = sqlite(fullfile(PROJECT_ROOT, 'Doc/ApRES/Rover/HF/StartStop.db'));

query = ['SELECT ' ...
    'measurements.measurement_id, ' ...
    'measurements.path, ' ...
    'measurements.filename, ' ...
    'measurements.timestamp, ' ...
    'IFNULL(measurements.tags, ""), ' ...
    'measurements.latitude, ' ...
    'measurements.longitude, ' ...
    'measurements.elevation ' ...
    'FROM measurements ' ...
    'WHERE measurements.tags LIKE ''%gps_type%'' ' ...
    'ORDER BY measurements.timestamp;'];

TBL_MEAS_ID = 1;
TBL_PATH = 2;
TBL_FNAME = 3;
TBL_TS = 4;
TBL_TAGS = 5;
TBL_LAT = 6;
TBL_LON = 7;
TBL_EL = 8;

data = fetch(apres_db, query);

% catalogue_path = fullfile(PROC_ROOT, "stop_start_rtk.csv");

% catalogue = readtable(catalogue_path);

%% Determine Mean Position for Survey
% mean_pos = [
%     mean(catalogue.latitude),
%     mean(catalogue.longitude),
%     mean(catalogue.elevation)
% ];
pos = cell2mat(data(:, [TBL_LAT TBL_LON TBL_EL]));

mean_pos = mean(pos);

%% Now calculate ENU positions
xyz = lla2enu(...
    [pos(:,1), pos(:,2), pos(:,3)],...
    mean_pos, ...
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
text = fileread([mfilename '.m']);
save_data = struct();
save_data.coordinate_origin = mean_pos;
save_data.source = text;
save_data.time_start = datetime;
save_data.time_interpolated = zeros(1, size(data,1));

log = ApRESProcessor.Log.instance();
log.echo = true;

for k = 1:size(data,1)

    if contains(data{k, TBL_TAGS}, 'bad_chirps')
        ApRESProcessor.Log.write(sprintf(...
            "Skipping %s [bad_chirps]", data{k, TBL_FNAME}));
        continue
    end
    
    ApRESProcessor.Log.write(sprintf(...
        "Processing %s", data{k, TBL_FNAME}));

    profile = fmcw.load(char(fullfile(DATA_ROOT, data{k, TBL_FNAME})));
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
    fprintf("Done %d/%d\n", k, size(data,1))

    save_data.image = img;
    save(save_path, '-struct', 'save_data')

end

time_stop = datetime;

save_data.time_stop = time_stop;
save_data.image = img;

save(save_path, '-struct', 'save_data')