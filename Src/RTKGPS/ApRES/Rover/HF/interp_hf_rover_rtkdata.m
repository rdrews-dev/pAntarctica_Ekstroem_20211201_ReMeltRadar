function [x, y, z, bs_psx, bs_psy, bs_el, rv_psx, rv_psy, rv_el, bs_psx0, bs_psy0, bs_el0, t] = ...
    interp_hf_rover_rtkdata(t_rov)
%%
%
%   Assume that the base station is fixed at position B_0 on the ice shelf,
%   which is the modulated in the horizontal direction by the ice flow F
%   and the tidal motion of the ice shelf (assumed to be fixed in the
%   vertical direction) T_v.  Then there is also an error component
%   introduced by the GPS such that the recorded position is given by
%
%       B(t) = B_0 + F*t + T_v(t) + B_e(t)
%
%   Then similarly, the rover position, relative to the ice shelf can be
%   described as R_0(t) because it is mobile.  It is subject to the same
%   flow and tidal modulation with time (assuming that these parameters are
%   constant across the distance of the profile).
%
%       R(t) = R_0(t) + F*t + T_v(t) + R_e(t)
%
%   From the ITS_LIVE dataset we can approximate the estimated flow
%   velocity across the spatial extent of the profile.  This can then be
%   subtracted from B(t) to give
%
%       B(t) - Fe*t = B_0 + (F-Fe)*t + T_v(t) + B_e(t)
%
%   The Tidal Fitting Toolbox is then used to the estimate the vertical
%   tidal motion from B(t) - Fe*t
%
%       B(t) - Fe*t - T_ve(t) = B_0 + (F-Fe)*t + (T_v(t)-T_ve(t)) + B_e(t)
%
%   Therefore provided that F-Fe and T_v(t) - T_ve(t) are sufficiently
%   small, the derived solution gives
%
%       B(t) - Fe*t - T_ve(t) = B_0 + B_e(t)
%
%   Assuming that the error B_e(t) is distributed normally over a
%   sufficient duration of time then B_0 can be estimated.
%
%   To find the rover position, relying on the assumtion that T_v(t) and F
%   are locally invariant, then
%
%       R(t) - Fe*t - T_ve(t) = R_0(t) + (F-Fe)*t + (T_v(t)-T_ve(t)) +
%                               R_e(t)
%
%   As before, assuming that F-Fe and T(t)-T_ve(t) are sufficiently small
%   then
%
%       R(t) - Fe*t - T_ve(t) = R_0(t) + R_e(t)
%
%   And then the estimate of B_0 can be used to find the relative position
%   of the rover to the base station thus:
%
%       R(t) - Fe*t - T_ve(t) - B_0 = R_0(t) + R_e(t) + B_0
%

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

%% Calculate Relative Offsets
t = [t_day7 t_day8];

bs_psy = [base_7_int.psy base_8_int.psy];
bs_psx = [base_7_int.psx base_8_int.psx];
bs_el = [base_7_int.el base_8_int.el];

rv_psy = [rover_7_int.psy rover_8_int.psy];
rv_psx = [rover_7_int.psx rover_8_int.psx];
rv_el = [rover_7_int.el rover_8_int.el];

%% Fit ITS_LIVE ice flow
%
%   This assumes that the interpolated value of vx and vy are constant over
%   the length of the profile however this may not generally be the case.
t_years = years(t - t(1));

% vx = mean(itslive_interp('vx', bs_psx, bs_psy));
% vy = mean(itslive_interp('vy', bs_psx, bs_psy));
% 
% dx_flow = cumtrapz(t_years, vx*ones(size(t)));
% dy_flow = cumtrapz(t_years, vy*ones(size(t)));

pfit_x = polyfit(t_years, bs_psx, 1);
pfit_y = polyfit(t_years, bs_psy, 1);

vx_est = pfit_x(1);
vy_est = pfit_y(1);

fprintf("Estimating (x,y) velocities...\n");
fprintf("vx: %7.3f m/yr\n", vx_est);
fprintf("vy: %7.3f m/yr\n", vy_est);
fprintf(" v: %7.3f m/yr\n", vecnorm([vx_est vy_est]));

dx_flow = cumtrapz(t_years, vx_est*ones(size(t)));
dy_flow = cumtrapz(t_years, vy_est*ones(size(t)));

bs_psx0 = mean(bs_psx - dx_flow); %polyval(pfit_x, t_years));
bs_psy0 = mean(bs_psy - dy_flow); %polyval(pfit_y, t_years));

fprintf("\nBase Station Estimated Position:\n")
fprintf("bs_psx0: %f m\n", bs_psx0);
fprintf("bs_psx0: %f m\n", bs_psy0);

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

%% Remove linear trend
bs_el_detide_linfit = polyval(polyfit(bs_dn_norm, bs_el_detide, 1), bs_dn_norm);
bs_el_detide_linfit = bs_el_detide_linfit - bs_el_detide_linfit(1);

bs_el_detrend = bs_el_detide - bs_el_detide_linfit;
bs_el0 = mean(bs_el_detrend);

%% Calculate Interpolated Positions
if nargin ~= 1
    t_rov = t;
end

x = interp1(t, rv_psx - bs_psx0 - dx_flow, t_rov);
y = interp1(t, rv_psy - bs_psy0 - dy_flow, t_rov);
z = interp1(t, rv_el - bs_el0 - bs_tide - bs_el_detide_linfit, t_rov);
