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
DATA_FOLDER = 'D:/JH_PhD/ReMeltRadar/Raw/ApRES/Rover/HF/Testing';

% ROOT_FOLDER
%   specifies the root folder to make a relative file path from
%   there should be no trailing /
ROOT_FOLDER = 'D:/JH_PhD/ReMeltRadar';

% RECURSIVE
%   whether to traverse sub-folders within each folder
RECURSIVE = 0; 

% OUTPUT_PATH
%   path to output csv file where data is to be written.
OUTPUT_PATH = '../../../../Doc/ApRES/Rover/HF/Files/Testing.tex';

% -------------------------------------------------------------------------
%% Open Output File
fh = fopen(OUTPUT_PATH, 'wt+');
% % Write header (with combined fields
% write_csv_header(fh, DAT_FIELDS)

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
            process_and_write_dat_info_to_tex(...
                fullfile(files(k).folder, files(k).name), fh, ROOT_FOLDER ...
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
%% Process and Log DAT File Info to CSV
function process_and_write_dat_info_to_tex(file_path, output_handle, root_folder)
    
    % Load profile
    try
        c_prof = fmcw_load(file_path);
    catch
        fprintf(">>> ERROR reading [%s].  Writing NaN to file.%s", newline);
%         fprintf(output_handle, "%s,", file_path);
%         for k = 1:numel(fieldnames)
%             fprintf(output_handle, "%d,", NaN);
%         end
%         fprintf(output_handle, "%d%s", NaN, newline);
        return
    end
    
    [dir_name, file_name, file_ext] = fileparts(file_path);
    
    % Try and find root
    f_root = strfind(strrep(dir_name,'\','/'), root_folder);
    if ~isempty(f_root)
        folder_path = dir_name(f_root + strlength(root_folder):end);
    else
        folder_path = dir_name;
    end
    
    if isempty(folder_path)
        folder_path = '';
    end
    
    folder_path = strrep(folder_path, '\', '/');
    file_name = strcat(file_name, file_ext);
    
    format_string = ['\\hfaprestable\n',  ...
        '%% Folder\n',  ...
        '{%s}%%\n',  ...
        '%% Filename\n',  ...
        '{%s}%%\n',  ...
        '%% Subbursts\n',  ...
        '{%d}{%d}{%s}{%s}{%.3f}{%.3f}{%.3f}%%\n',  ...
        '%% Location\n',  ...
        '{%s (%2.7f, %2.7f)}%%\n',  ...
        '%% Comments\n',  ...
        '{%s}%%\n',  ...
        '%% Label\n',  ...
        '{%s}%%\n\n'];
    
    tex_sanitize = @(txt) regexprep(txt, '([\\\_\^])', '\\$0');
    
    fprintf(output_handle,...
        format_string, ...
        tex_sanitize(folder_path), tex_sanitize(file_name), ...
        c_prof.SubBurstsInBurst, c_prof.NAttenuators, ...
        join(string(num2str(c_prof.Attenuator_1(1:c_prof.NAttenuators))),","), ...
        join(string(num2str(c_prof.Attenuator_2(1:c_prof.NAttenuators))),","), ...
        c_prof.f0/1e6, c_prof.f1/1e6, c_prof.T, "", c_prof.lat, c_prof.long, "", "" ...
    );

%     
%     % Iterate over dat_fields
%     for k = 1:numel(fieldnames)
%         
%         % Get field name
%         fieldname = fieldnames{k};
%         
%         % Check if empty
%         if isempty(dat_fields.(fieldname))
%             c_val = c_prof.(fieldname);
%         elseif isa(dat_fields.(fieldname), 'function_handle')
%             func = dat_fields.(fieldname);
%             if nargin(func) == 2
%                 c_val = func(c_prof, file_path);
%             else
%                 c_val = func(c_prof);
%             end
%         else
%             c_val = NaN;
%         end
%         
%         % Check if numeric type and cast to string
%         if isnumeric(c_val)
%             c_val = num2str(c_val);
%         end
%         
%         % Write to file
%         if k == numel(fieldnames)
%             fprintf(output_handle, "%s\n", c_val);
%         else
%             fprintf(output_handle, "%s,", c_val);
%         end
%         
%     end

end

function timestamp = get_timestamp_from_prof(profile)
    timestamp = datestr(...
        datetime(profile.TimeStamp,'ConvertFrom','datenum'), ...
        'YYYY-mm-dd HH:MM:ss' ...
    );
end