% List files stored in the Testing.db database, iterate through and plot
% results.  Store comments and location data back in database.
%
%   Auth: J.D. Hawkins
   

% Create database connection
apres_db = sqlite('../../../../Doc/ApRES/Rover/HF/StartStop.db');

query = ['SELECT ' ... 
    'measurements.measurement_id, ' ...
    'measurements.path, ' ...
    'measurements.filename, ' ...
    'measurements.timestamp [ts], ' ...
    'measurements.valid, ' ... ...
    'IFNULL(measurements.location,""), ' ...
    'IFNULL(measurements.comments,""), ' ...
    'apres_metadata.n_attenuators, ' ...
    'apres_metadata.n_chirps, ' ...
    'apres_metadata.n_subbursts, ' ...
    'apres_metadata.af_gain, ' ...
    'apres_metadata.rf_attenuator, ' ...
    'apres_metadata.f_lower, ' ...
    'apres_metadata.f_upper, ' ...
    'apres_metadata.period, ' ...
    'apres_metadata.battery_voltage, ' ...
    'apres_metadata.power_code, ' ...
    'IFNULL(measurements.tags,"") ' ...
    'FROM `measurements`' ...
    'JOIN `apres_metadata`' ...
    'ON measurements.measurement_id = apres_metadata.measurement_id ' ...
    'ORDER BY ts'];

TBL_MEAS_ID = 1;
TBL_PATH = 2;
TBL_FILENAME = 3;
TBL_TIMESTAMP = 4;
TBL_VALID = 5;
TBL_LOCATION = 6;
TBL_COMMENTS = 7;
TBL_N_ATTN = 8;
TBL_N_CHIRPS = 9;
TBL_N_SUBBURSTS = 10;
TBL_AF_GAIN = 11;
TBL_RF_ATTN = 12;
TBL_F_LOWER = 13;
TBL_F_UPPER = 14;
TBL_PERIOD = 15;
TBL_BATT_VOLT = 16;
TBL_POWER_CODE = 17;
TBL_TAGS = 18;

COMMENT_LENGTH = 16;

data = fetch(apres_db, query);

%% Create list of filenames and truncated comments
n_rows = size(data,1);
file_list = cell(n_rows, 1);
fid_format_number = num2str(ceil(log10(n_rows)));
for row = 1:n_rows
    bad_chirps = '-';
    if contains(data{row, TBL_TAGS},"bad_chirps")
        bad_chirps = 'X';
    end
    file_list{row} = sprintf(['[%' fid_format_number 'd, %s] %s'], ...
        row, ...
        bad_chirps, ...
        data{row, TBL_FILENAME});
end

row_start = listdlg("ListString", file_list, "ListSize", [400 512], "SelectionMode", "single");

last_annotations = {
    char.empty, 
    char.empty
};

if row_start > 1
    last_annotations = {
        data{row_start-1, TBL_LOCATION},
        data{row_start-1, TBL_COMMENTS}
    };
end

%% Now iterate over the each row
for row = row_start:n_rows

    fprintf("Loading measurment_id %d at %s [Valid: %d]%s", ...
        data{row,TBL_MEAS_ID}, ...
        data{row,TBL_PATH}, ...
        data{row,TBL_VALID}, newline)

    if ~data{row,TBL_VALID} 
        fprintf("Skipping, data invalid.%s", newline)
        continue
    end

    path_to_data = fullfile('../../../..',data{row,TBL_PATH});
    
    prof = fmcw_load(path_to_data);
    subplot(2,1,1)
    hold off
    fill([0 0 1 1], [0 0.1 0.1 0], 'r', 'FaceAlpha', 0.1, 'EdgeAlpha', 0)
    hold on
    fill([0 0 1 1], [2.4 2.5 2.5 2.4], 'r', 'FaceAlpha', 0.1, 'EdgeAlpha', 0)
    plot(prof.t, prof.vif.')
    
    all_clips = all(any(prof.vif > 2.4 | prof.vif < 0.1, 2));
    some_clips = any(prof.vif > 2.4 | prof.vif < 0.1, 'all');
    if all_clips
        clips = 'All Clips';
    elseif some_clips
        clips = 'Some Clips';
    else
        clips = 'No Clips';
    end
    
    title(sprintf("Time [%s] Clip [%s] RF [%s] AF [%s] Chirp [%.3fs, %.2f-%.2f MHz] Power Code [%d] Battery Voltage [%.3f V]", ...
        data{row, TBL_TIMESTAMP}, ...
        clips, ...
        data{row, TBL_RF_ATTN}, ...
        data{row, TBL_AF_GAIN}, ...
        data{row, TBL_PERIOD}, ...
        data{row, TBL_F_LOWER}/1e6, ...
        data{row, TBL_F_UPPER}/1e6, ...
        data{row, TBL_POWER_CODE}, ...
        data{row, TBL_BATT_VOLT}));

    subplot(2,1,2)
    [rc, ~, sc, ~] = fmcw_range(prof, 2, 1500);
    hold off
    for n_at = 1:prof.NAttenuators
        plot(rc, 20*log10(abs(sc(n_at:prof.NAttenuators:end,:))),'Color',[0.75 0.75 0.75])
        hold on
    end
    for n_at = 1:prof.NAttenuators
        plot(rc, 20*log10(abs(mean(sc(n_at:prof.NAttenuators:end,:),1))), 'r')
    end

    % Load tags
    tags = data{row, TBL_TAGS};
    
    title(sprintf("File: %s,  Tags: %s", data{row,TBL_FILENAME}, tags), 'Interpreter', 'none')
    xticks(0:50:1500);
    ylim([-140 0])
    grid on

    drawnow

%     if some_clips
%         uiwait(warndlg('Some clipping found.', 'Clipping Warning'));
%     end

    if all_clips && ~contains(tags, 'clipping_all')
        if isempty(tags) || strlength(tags) == 0
            tags = 'clipping_all';
        else
            tags = strcat(tags, ',', 'clipping_all');
        end
    elseif some_clips && ~contains(tags, 'clipping_some')
        if isempty(tags) || strlength(tags) == 0
            tags = 'clipping_some';
        else
            tags = strcat(tags, ',', 'clipping_some');
        end
    end

%     bad_chirps = questdlg("Are there bad chirps within the burst?", ...
%         "Bad Chirps", "No");
% 
%     if strcmp(bad_chirps, "Cancel")
%         break;
%     elseif strcmp(bad_chirps, "Yes")
%         % Check whether we already have a bad chirps tag
%         if contains(tags, "bad_chirps")
%             fprintf("Already found bad_chirps tag allocated to this record.\n");
%         else
%             if isempty(tags) || strlength(tags) == 0
%                 tags = "bad_chirps";
%             else
%                 tags = strcat(tags, ',', "bad_chirps");
%             end
%             fprintf("Updated tag string: %s\n", tags);
%         end
% 
%     end

    query = ['UPDATE `measurements` ' ...
        sprintf('SET `tags` = ''%s'' ', escape_sql_string(tags)) ...
        sprintf('WHERE `measurement_id` = ''%s'';', ...
        escape_sql_string(num2str(data{row, 1})))];

    exec(apres_db, query);

%     uiwait(warndlg("Move to next file?", "Next File"))

end

close(apres_db)