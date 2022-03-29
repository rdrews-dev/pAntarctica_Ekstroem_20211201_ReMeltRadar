function [x, y, z, bs_psx, bs_psy, bs_el, rv_psx, rv_psy, rv_el, t] = ...
    interp_hf_rover_rtkdata(t_rov)

PROJECT_ROOT = "../../../../..";
DATA_ROOT = fullfile(PROJECT_ROOT, "Raw/RTKGPS/ApRES/Rover/HF");

% Load base station data
base_day7 = load_rtk_from_csrs_csv(fullfile(...
    DATA_ROOT, "Base/20220107/5936R24614202201071548A.csv"));

base_day8 = load_rtk_from_csrs_csv(fullfile(...
    DATA_ROOT, "Base/20220108/5936R24614202201081130A.csv"));

rover_day7 = load_rtk_from_csrs_csv(fullfile(...
    DATA_ROOT, "Rover/20220107/5930R24506202201071555A.csv"));

rover_day8 = load_rtk_from_csrs_csv(fullfile(...
    DATA_ROOT, "Rover/20220108/5930R24506202201081133A.csv"));

%% Combine day 7 and day 8 components for base and rover
% Sampling Time
dt = 0.2;

% Find first and last time in day 7 sets and round to nearest second
%   ceil for first_time, floor for last_time
day_7_time = vertcat(base_day7.timestamp,rover_day8.timestamp);
first_time = dateshift(min(day_7_time), 'start', 'second');
last_time = dateshift(max(day_7_time), 'start', 'second') - seconds(1);
t_day7 = first_time : seconds(dt) : last_time;

% Iterpolate latitude values
bx = interp1(base_day7.timestamp, base_day7.lat, t_day7);
rx = interp1(rover_day7.timestamp, rover_day7.lat, t_day7);

% Mask timestamps to those where base and rover measurements are both
% available
t_day7 = t_day7(~isnan(bx) & ~isnan(rx));

% Do same for day 8...
day_8_time = vertcat(base_day8.timestamp, rover_day8.timestamp);
first_time = dateshift(min(day_8_time), 'start', 'second');
last_time = dateshift(max(day_8_time), 'start', 'second') - seconds(1);
t_day8 = first_time : seconds(dt) : last_time;

bx = interp1(base_day8.timestamp, base_day8.lat, t_day8);
rx = interp1(rover_day8.timestamp, rover_day8.lat, t_day8);

t_day8 = t_day8(~isnan(bx) & ~isnan(rx));

%% Interpolate day 7 and day 8
base_7_int = interpolate_rtk_struct(base_day7, t_day7);
rover_7_int = interpolate_rtk_struct(rover_day7, t_day7);
base_8_int = interpolate_rtk_struct(base_day8, t_day8);
rover_8_int = interpolate_rtk_struct(rover_day8, t_day8);

%% Fit tidal components 
% Aslak Grinsted (2022). Tidal fitting toolbox 
%   (https://www.mathworks.com/matlabcentral/fileexchange/19099-tidal-fitting-toolbox),
%   MATLAB Central File Exchange.
%   Retrieved March 29, 2022.

% Create datenum vector for base
bs_dn = [datenum(t_day7) datenum(t_day8)];
min_dn = min(bs_dn);
bs_dn_norm = bs_dn - min_dn;

% Create elevation vector for base
bs_el = [base_7_int.el base_8_int.el];

fprintf("Fitting tidal constituents...\n")
% Fit tidal model
bs_tidalfit = tidalfit([bs_dn_norm.' bs_el.']);

fprintf("\n    Name :   Speed  Period     Amp   Phase\n")
fprintf("------------------------------------------\n")
% List components
[~,sidx] = sort(vertcat(bs_tidalfit.amp), 'descend');

for k = 1:numel(bs_tidalfit)
    if ~isnan(bs_tidalfit(sidx(k)).amp)
        fprintf("%8s : %7.3f %7.3f %7.3f %7.3f\n", ...
            bs_tidalfit(sidx(k)).name, ...
            bs_tidalfit(sidx(k)).speed, ...
            bs_tidalfit(sidx(k)).period, ...
            bs_tidalfit(sidx(k)).amp, ...
            bs_tidalfit(sidx(k)).phase)
    end
end
fprintf("\n")

% Remove tidal components
bs_tide = tidalval(bs_tidalfit, bs_dn_norm);
bs_el_detide = bs_el - bs_tide;

% Remove linear trend
bs_el_detide_linfit = polyval(polyfit(bs_dn_norm, bs_el_detide, 1), bs_dn_norm);
bs_el_detide_linfit = bs_el_detide_linfit - bs_el_detide_linfit(1);

bs_el_detrend = bs_el_detide - bs_el_detide_linfit;

%% Calculate Relative Offsets
t = [t_day7 t_day8];

bs_psy = [base_7_int.psy base_8_int.psy];
bs_psx = [base_7_int.psx base_8_int.psx];
bs_el = [base_7_int.el base_8_int.el];

rv_psy = [rover_7_int.psy rover_8_int.psy];
rv_psx = [rover_7_int.psx rover_8_int.psx];
rv_el = [rover_7_int.el rover_8_int.el];

%% Calculate Interpolated Positions
if nargin ~= 1
    t_rov = t;
end

x = interp1(t, rv_psx - bs_psx, t_rov);
y = interp1(t, rv_psy - bs_psy, t_rov);
z = interp1(t, rv_el - bs_el, t_rov);