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
% pos = cell2mat(data(:, [TBL_LAT TBL_LON TBL_EL]));
% 
% mean_pos = mean(pos);

%% Now calculate ENU positions
% xyz = lla2enu(...
%     [pos(:,1), pos(:,2), pos(:,3)],...
%     mean_pos, ...
%     'ellipsoid');
addpath(fullfile(PROJECT_ROOT, 'Src/RTKGPS/ApRES/Rover/HF'));

[x,y,z] = interp_hf_rover_rtkdata(datetime(data(:, TBL_TS)));
xyz = [x y z];

% Get least squares positions to determine image plane
a = [xyz(:,1) ones(length(xyz),1)] \ xyz(:,2);

imgU = [1;a(1);0] / sqrt(1+a(1)^2);
imgV = [0;0;-1];
imgOrigin = ApRESProcessor.PositionENU([min(xyz(:,1));min(xyz(:,1))*a(1)+a(2);0]);
imgRes = 4;
imgSize = round([sqrt((max(xyz(:,1))-min(xyz(:,1))).^2 + (max(xyz(:,2))-min(xyz(:,2))).^2)/imgRes(1), 900/4]);

imgPlaneObj = ApRESProcessor.Imaging.ImagePlane(imgSize, imgU, imgV, imgRes, imgRes, imgOrigin);
img = ApRESProcessor.Imaging.ImagePlane(imgSize, imgU, imgV, imgRes, imgRes, imgOrigin);

velModel = ApRESProcessor.Imaging.ConstantVelocityModel(3.15, ...
    50, 0.8, 10, 0.8);
int = ApRESProcessor.Imaging.InterpolatorBeamPattern(velModel, @(x) cos(x).^4 .* cos(x/3));
int.windowSize = 3;


time_start = datetime;

save_path = fullfile(PROC_ROOT, strcat("StopStart/interp_", datestr(datetime, "yyyymmdd_HHMMss"), ".mat"));
text = fileread([mfilename '.m']);
save_data = struct();
save_data.coordinate_origin = [0,0,0];
save_data.source = text;
save_data.time_start = datetime;
save_data.time_interpolated = zeros(1, size(data,1));

log = ApRESProcessor.Log.instance();
log.echo = true;

pool = gcp;
nWorkers = pool.NumWorkers;
valid_profiles = find(~contains(data(:, TBL_TAGS), 'bad_chirps'));
nProfiles = numel(valid_profiles);

save_data.valid_profiles = valid_profiles;
save_data.n_workers = nWorkers;

img_data = zeros(size(img.data));
sumTime = 0;

processed = 0;

%%
while processed < nProfiles

    tic

    futureIdx = processed + 1 : processed + nWorkers;
    futureIdx(futureIdx > nProfiles) = [];

    evalFutures(1:numel(futureIdx)) = parallel.FevalFuture;
    for k = 1:numel(futureIdx)

%         if contains(data{profIdx(m,k), TBL_TAGS}, 'bad_chirps')
%             ApRESProcessor.Log.write(sprintf(...
%                 "Skipping %s [bad_chirps]", data{profIdx(m,k), TBL_FNAME}));
%             continue
%         end

        ApRESProcessor.Log.write(sprintf(...
            "Processing %s", data{valid_profiles(futureIdx(k)), TBL_FNAME}));

        filename = char(fullfile(DATA_ROOT, data{valid_profiles(futureIdx(k)), TBL_FNAME}));
        % assign positions
        position = xyz(valid_profiles(futureIdx(k)),:);
                
        evalFutures(k) = parfeval(...
            @interpolateProfile, 1, filename, position, velModel, imgSize, imgU, imgV, imgRes, imgRes, imgOrigin);

    end

%     wait(evalFutures);
    
    for k = 1:numel(futureIdx)

        processed = processed + 1;
        [~, v] = fetchNext(evalFutures);
        img_data = img_data + v;
        
    end

    lastTime = toc;
    sumTime = sumTime + lastTime;
    timeRemAvg = (nProfiles - processed) * sumTime / processed;
    timeRemLast = (nProfiles - processed) * lastTime;
    
    timeStrMin = secondsToHoursMinsSeconds(min([timeRemAvg timeRemLast]));
    timeStrMax = secondsToHoursMinsSeconds(max([timeRemAvg timeRemLast]));
    
    disp(strcat("Remaining approximately between ",timeStrMin," and ", timeStrMax));

    img.data = img_data;
    
%     tic
%     int.interpolate(imgPlaneObj, profile, 2);
    save_data.time_interpolated(valid_profiles(futureIdx)) = lastTime;
%     img.data = img.data + imgPlaneObj.data;

    img.draw(gca, @(x) 20*log10(abs(x)));
    view(48, 1)
    axis equal
    drawnow
    fprintf("Done %d/%d in %f s / %f s\n", processed, nProfiles,...
        save_data.time_interpolated(k), sum(save_data.time_interpolated));

    save_data.image = img;
    save(save_path, '-struct', 'save_data')

    clear evalFunc

end

time_stop = datetime;

save_data.time_stop = time_stop;
save_data.image = img;

save(save_path, '-struct', 'save_data')

function [data] = interpolateProfile(filename, position, velModel, imgSize, imgU, imgV, imgResU, imgResV, imgOrigin)

    fmcw = ApRESProcessor.FMCWProcessor(3e7, 2e7, 2);
    profile = fmcw.load(filename);
    % assign positions
    profile.position = position;
    profile.rxPosition = position - imgU.' * 10;
    profile.txPosition = position - imgU.' * 50;

    plane = ApRESProcessor.Imaging.ImagePlane(imgSize, imgU, imgV, imgResU, imgResV, imgOrigin);
%     int = ApRESProcessor.Imaging.InterpolatorBeamPattern(velModel);
    int = ApRESProcessor.Imaging.InterpolatorBeamPattern(velModel, @(x) cos(x).^4 .* cos(x/3));
    int.monostaticApproximation = false;
    int.interpolate(plane, profile);
    data = plane.data;
    clear plane
    
end

function [str] = secondsToHoursMinsSeconds(time)

    s = mod(time , 60);
    time = time - s;
    m = mod(time / 60, 60);
    time = time - m * 60;
    h = floor(time / 60 / 60);
    
    str = sprintf("%ih %im %2.0fs", h, m, s);
    
end
 