% Check for duplicate ApRES files and ensure data integrity then cleanup
% 
% Auth: J.D. Hawkins

clear all;

% Create DB connection
apres_db = sqlite('../../../../Doc/ApRES/Rover/HF/Testing.db');

% Now we select results from the `measurements` table
query = [
    'SELECT `measurement_id`, `filename`, `path`, `timestamp` ' ...
    'FROM `measurements`'
];

% Get results
results = fetch(apres_db, query);

filenames = vertcat(results(:, 2));
data_check = zeros(size(filenames));
to_remove = zeros(size(filenames));

% Know that names are those that begin with "Survey_" so iterate through
% for these:
for row = 1:size(results,1)

    c_file = filenames{row};
    % If it doesn't begin with Survey_, skip
    if ~contains(c_file, "Survey_")
        data_check(row) = -1;
        continue;
    end

    fprintf("Looking at %s%s", c_file, newline);

    % Otherwise, now we loop through and find the file with corresponding
    % timestamp in filename
    for row2 = 1:size(results,1)
        % If we're reading the current row, skip
        if row2 == row; continue; end
        % Otherwise check if the filenames match
        m_file = filenames{row2};
        if strcmp(c_file(8:end), m_file)
            fprintf("> Matching file: %s%s", m_file, newline);
            % Load each file
            prof_1 = fmcw_load(fullfile('../../../..',results{row, 3}));
            prof_2 = fmcw_load(fullfile('../../../..',results{row2, 3}));
            % Check timestamp
            fprintf("> Timestamp 1: %f [%s]%s", prof_1.TimeStamp, c_file, newline);
            fprintf("> Timestamp 2: %f [%s]%s", prof_2.TimeStamp, m_file, newline);
            fprintf(">     Delta T: %f %s", prof_1.TimeStamp - prof_2.TimeStamp, newline);
            % Check data integrity
            data_integrity = all(abs(prof_1.v - prof_2.v) < eps);
            data_check(row) = data_integrity;
            fprintf(">  Data Check: %d %s", data_integrity, newline);
            fprintf(newline);

            % If the data is the same, let's remove the Survey_ record
            if data_integrity
                to_remove(row) = 1;
            end

        end
    end
end

fprintf("-------------------------------------------------%s", newline)
fprintf("No. files with data integrity issues: %d %s", ...
    sum(data_check == 0), newline)
fprintf("Duplicate files                     : %d %s", ...
    sum(to_remove), newline);
fprintf(newline);

fprintf("-------------------------------------------------%s", newline)
fprintf("Removing files with duplicated contents%s", newline)
for row = 1:numel(to_remove)
    if to_remove(row)
        fprintf("> Removing record (%d) [%s]%s", results{row,1}, filenames{row}, newline);
        exec(apres_db, sprintf("DELETE FROM `measurements` WHERE `measurement_id` = %d", results{row,1}));
        exec(apres_db, sprintf("DELETE FROM `apres_metadata` WHERE `measurement_id` = %d", results{row,1}));
    end
end

close(apres_db);

