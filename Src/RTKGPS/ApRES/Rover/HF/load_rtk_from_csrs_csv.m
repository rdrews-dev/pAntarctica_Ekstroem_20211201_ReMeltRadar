function [lat, lon, el, dt] = load_rtk_from_csrs_csv(path)

    rtk_data = readtable(path);

    lat = rtk_data.latitude_decimal_degree;
    lon = rtk_data.longitude_decimal_degree;
    el = rtk_data.ellipsoidal_height_m;

    dec_hour = rtk_data.decimal_hour;
    int_hour = floor(dec_hour);
    min = (dec_hour - int_hour) * 60;
    int_min = floor(min);
    sec = (min - int_min) * 60;

    % Process datetime
    dt = datetime(rtk_data.year, 1, 1);
    dt = dt ...
         + days(rtk_data.day_of_year - 1) ...
         + hours(int_hour) ...
         + minutes(int_min) ...
         + seconds(sec);

    if nargout == 1
        prev_lat = lat;
        lat = struct();
        lat.lat = prev_lat;
        lat.lon = lon;
        lat.el = el;
        lat.timestamp = dt;
        lat.posixtime = posixtime(dt);

        if exist('ll2ps', 'file')
            [lat.psx, lat.psy] = ll2ps(lat.lat, lat.lon);
        end

    end

end