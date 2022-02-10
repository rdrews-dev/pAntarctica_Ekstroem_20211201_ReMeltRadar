% List files stored in the Testing.db database, iterate through and plot
% results.  Store comments and location data back in database.
%
%   Auth: J.D. Hawkins
   

% Create database connection
apres_db = sqlite('../../../../Doc/ApRES/Rover/HF/Testing.db');

query = ['SELECT ' ... 
    'measurements.measurement_id, ' ...
    'measurements.path, ' ...
    'measurements.filename, ' ...
    'measurements.timestamp [ts], ' ...
    'measurements.valid, ' ...
    'IFNULL(measurements.location,""), ' ...
    'IFNULL(measurements.comments,""), ', ...
    'apres_metadata.n_attenuators, ' ...
    'apres_metadata.n_chirps, ' ...
    'apres_metadata.n_subbursts, ' ...
    'apres_metadata.af_gain, ' ...
    'apres_metadata.rf_attenuator, ' ...
    'apres_metadata.f_lower, ' ...
    'apres_metadata.f_upper, ' ...
    'apres_metadata.period, ' ...
    'apres_metadata.battery_voltage, ' ...
    'apres_metadata.power_code ' ...
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

COMMENT_LENGTH = 16;

data = fetch(apres_db, query);

%% Create list of filenames and truncated comments
n_rows = size(data,1);
file_list = cell(n_rows, 1);
for row = 1:n_rows
    comment = data{row, TBL_COMMENTS};
    if strlength(comment) > COMMENT_LENGTH
        comment = strcat(comment(1:COMMENT_LENGTH), '...');
    elseif strlength(comment) == 0
        comment = '[EMPTY]';
    end
    file_list{row} = sprintf("%s - %s", ...
        data{row, TBL_FILENAME}, ...
        comment);
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
    plot(prof.t, prof.vif.')
    title(sprintf("Time [%s] RF [%s] AF [%s] Chirp [%.3fs, %.2f-%.2f MHz] Power Code [%d] Battery Voltage [%.3f V]", ...
        data{row, TBL_TIMESTAMP}, ...
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
    title(sprintf("File: %s", data{row,TBL_FILENAME}), 'Interpreter', 'none')

    annotations = {
        data{row, TBL_LOCATION},
        data{row, TBL_COMMENTS}
    };

    if isempty(annotations{1})
        if strcmp(questdlg(...
            "No location found - copy previous?",...
            "Missing Location","Yes","No","Yes"), "Yes")
            annotations{1} = last_annotations{1};
        end
    end

    if isempty(annotations{2})
        if strcmp(questdlg(...
            "No comment found - copy previous?",...
            "Missing Comment","Yes","No","Yes"), "Yes")
            annotations{2} = last_annotations{2};
        end
    end

    annotations = inputdlg(...
        ["Location:", "Comments:"], ...
        sprintf("Annotate %d/%d - %s", ...
            row, ...
            n_rows, ...
            data{row,TBL_FILENAME}), ...
        [3 80], ...
        annotations);

    last_annotations = annotations;

    if numel(annotations) == 0
        fprintf("Quitting...%s", newline)
        break
    end

    query = ['UPDATE `measurements` ' ...
        sprintf('SET `location` = ''%s'', `comments` = ''%s''', ...
            escape_sql_string(annotations{1}), ...
            escape_sql_string(annotations{2})) ...
        sprintf('WHERE `measurement_id` = ''%s''', ...
            escape_sql_string(num2str(data{row, 1}))) ...
            ';'];

%     fprintf(query)

    exec(apres_db, query)

end

close(apres_db)