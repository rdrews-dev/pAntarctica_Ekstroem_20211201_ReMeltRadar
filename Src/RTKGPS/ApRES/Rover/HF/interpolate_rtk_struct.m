function [rtk_int] = interpolate_rtk_struct(rtk, t)

    rtk_int = struct();
    rtk_int.lat = interp1(rtk.timestamp, rtk.lat, t);
    rtk_int.lon = interp1(rtk.timestamp, rtk.lon, t);
    rtk_int.el = interp1(rtk.timestamp, rtk.el, t);
    rtk_int.posixtime = posixtime(t);

    if isfield(rtk, "psx")
        [rtk_int.psx, rtk_int.psy] = ll2ps(rtk_int.lat, rtk_int.lon);
    end

    rtk_int.timestamp = t;

end

