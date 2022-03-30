% create_file_listing.m
%
%   Description: Traverse and compile list of all *.dat files within folder
%                and append relevant information about ApRES settings and
%                burst types.
%
%   Author: J.D. Hawkins
%   Date:   2022-01-27
%   

% -------------------------------------------------------------------------
%% Script Variables

% DATA_FOLDER
%   specifiies the folder to look for *.dat files in
% DATA_FOLDER = '../../../Untouched/ApRES/HF';
DATA_FOLDER = 'E:/Antarctica2022/Untouched/ApRES/HF';

% RECURSIVE
%   whether to traverse sub-folders within each folder
RECURSIVE = 1; 

% OUTPUT_PATH
%   path to output csv file where data is to be written.
OUTPUT_PATH = '../../../../Doc/ApRES/Rover/HF/apres_files.csv';

% DAT_FIELDS
%   list of ApRES profile variables to write to CSV file
%
%   Name of each csv header is given by the struct field name.  For example
%   with 
%
%       DAT_FIELDS = struct();
%       DAT_FIELDS.filename = []
%       DAT_FILEDS.NAttenuators = []
%
%   the heading of the CSV file would read as:
%
%       filename,NAttenuators
%       ... [ file contents ] ...
%
%   If you want to adjust the name written to the header, you can provide
%   an anonymous function as the value of the struct field which returns
%   the value to be stored in the column, i.e.
%
%       DAT_FIELDS.NChirps = @(prof) prof.ChirpsInBurst;
%
%   will write the value of found in .ChirpsInBurst in the FMCW profile
%   under the heading 'NChirps'.

DAT_FIELDS = struct();
DAT_FIELDS.filename         = @(prof) prof.filename;
DAT_FIELDS.timestamp        = @get_timestamp_from_prof;
DAT_FIELDS.NChirps          = @(prof) prof.ChirpsInBurst;
DAT_FIELDS.NAttenuators     = [];
DAT_FIELDS.SubBurstsInBurst = [];
DAT_FIELDS.RF_Attenuator    = @(prof) join(string(num2str(prof.Attenuator_1(1:prof.NAttenuators)))," ");
DAT_FIELDS.AF_Gain          = @(prof) join(string(num2str(prof.Attenuator_1(1:prof.NAttenuators)))," ");
DAT_FIELDS.fc               = [];
DAT_FIELDS.B                = [];
DAT_FIELDS.T                = [];
DAT_FIELDS.fs               = [];
DAT_FIELDS.Temperature_1    = [];
DAT_FIELDS.Temperature_2    = [];
DAT_FIELDS.BatteryVoltage   = [];

% -------------------------------------------------------------------------
%% Open Output File
fh = fopen(OUTPUT_PATH, 'w+');
% Write header (with combined fields
write_csv_header(fh, DAT_FIELDS)

% try
    
    %% Create and Initialise Path Stack for Recursive Mode
    path_stack = string.empty;
    path_stack(end+1) = DATA_FOLDER;
    
    %% Iterate Over Files
    %   Continue to do this while path_stack is not empty

    while numel(path_stack) > 0
        
        % Pop current path from stack
        c_path = path_stack(end);
        path_stack(end) = [];
    
        % List files in folder
        files = dir(c_path);
        
        % Output to cmdline
        fprintf("Found %d file system objects in directory [%s]%s", numel(files), c_path, newline);
        
        % Iterate over files in folder
        for k = 1:numel(files)
           
            % Get current file
            c_file = files(k);
            
            % Get edge case of . and .. directories
            if any(strcmp(files(k).name, {'.','..'}))
                continue
            end
            
            % If it is a directory then add it to stack
            if files(k).isdir && RECURSIVE
                path_stack(end+1) = fullfile(files(k).folder, files(k).name);
                continue
            end
            
            % Otherwise, if it is a *.dat file then parse and write to
            % output file.
            [~,~,ext] = fileparts(files(k).name);
            if strcmpi(ext, '.dat')
                % Concatenate filename 
                f_name = fullfile(files(k).folder, files(k).name);
                % Write stage to cmdline
                fprintf("Processing [%s] | Path Stack [%d]%s", ...
                    f_name, numel(path_stack), newline)
                % Process file
                process_and_write_dat_info_to_csv(...
                    fullfile(files(k).folder, files(k).name), DAT_FIELDS, fh ...
                );
            end
            
        end
        
    end
   
    fclose(fh);
    
% catch e
%     fclose(fh);
%     rethrow(e)
% end

% -------------------------------------------------------------------------
%% Write Header for CSV File
function write_csv_header(output_handle, dat_fields)

    dat_fieldnames = fields(dat_fields);
    % Write mandatory fields first
    % 
    for k = 1:numel(dat_fieldnames)-1
        fprintf(output_handle, "%s,", dat_fieldnames{k});
    end
    fprintf(output_handle, "%s%s", dat_fieldnames{k+1}, newline);
    
end

% -------------------------------------------------------------------------
%% Process and Log DAT File Info to CSV
function process_and_write_dat_info_to_csv(file_path, dat_fields, output_handle)

    % Get fieldnames
    fieldnames = fields(dat_fields);
    
    % Load profile
    try
        c_prof = fmcw_load(file_path);
    catch
        fprintf("> ERROR reading [%s].  Writing NaN to file.%s", newline);
        fprintf(output_handle, "%s,", file_path);
        for k = 1:numel(fieldnames)
            fprintf(output_handle, "%d,", NaN);
        end
        fprintf(output_handle, "%d%s", NaN, newline);
        return
    end
    
    % Iterate over dat_fields
    for k = 1:numel(fieldnames)
        
        % Get field name
        fieldname = fieldnames{k};
        
        % Check if empty
        if isempty(dat_fields.(fieldname))
            c_val = c_prof.(fieldname);
        elseif isa(dat_fields.(fieldname), 'function_handle')
            func = dat_fields.(fieldname);
            if nargin(func) == 2
                c_val = func(c_prof, file_path);
            else
                c_val = func(c_prof);
            end
        else
            c_val = NaN;
        end
        
        % Check if numeric type and cast to string
        if isnumeric(c_val)
            c_val = num2str(c_val);
        end
        
        % Write to file
        if k == numel(fieldnames)
            fprintf(output_handle, "%s\n", c_val);
        else
            fprintf(output_handle, "%s,", c_val);
        end
        
    end

end

% -------------------------------------------------------------------------
%% Function definitions for file conversion
% Bit of a trick here - to treat path as a special case because it's not
% stored in profile, we pass it as a second argument which should be unused
% most of the time.
function path = get_path_from_prof(~, path)
    return
end

function timestamp = get_timestamp_from_prof(profile)
    timestamp = datestr(...
        datetime(profile.TimeStamp,'ConvertFrom','datenum'), ...
        'YYYY-mm-dd HH:MM:ss' ...
    );
end