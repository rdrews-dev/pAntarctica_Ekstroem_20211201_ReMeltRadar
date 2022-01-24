# Data Management Routines for ReMeltRadar Data Folders
#
#   Auth: JD Hawkins
#   Date: 2022-01-13
#
#   Change Log:
#   ---------------------------------------------------------------------------
#   2022-01-24: Add markdown report generation and update backend to ensure 
#               files are correctly marked as missing or catalogued.
#   2022-01-13: Created.
#
#   

import argparse
import csv
import datetime
import logging
import os
import pathlib

PROJECT_NAME = "ReMeltRadar"
VERSION = "0.0.1"
LOG_LEVEL = logging.DEBUG

class FileRecord:

    FIELDS = [
        "filename",
        "size",
        "owner",
        "date_added",
        "comment"
    ]

    def __init__(self, path=None):

        if isinstance(path, str):
            path = pathlib.Path(path)

        # Assign None to all field values
        for field in self.FIELDS:
            setattr(self, field, None)
        # Set catalogued to false - assumed we haven't logged the file
        self.catalogued = False

        # Check whether we're looking at a real 
        if not isinstance(path, pathlib.Path) and path != None:
            raise Exception("path should be of type 'str' or 'pathlib.Path'.")
        elif path != None:  
            self.path = path
            # Pick filename from path
            self.filename = self.path.parts[-1]
            # Check path exists
            if path.exists():
                self.date_added = datetime.datetime.utcfromtimestamp(self.path.stat().st_mtime)
                try:
                    self.owner = self.path.owner()
                except NotImplementedError:
                    self.owner = ""
                self.size = self.path.stat().st_size
                self.comment = ""


    def exists(self):
        if self.path == None:
            return False
        else:
            return self.path.is_file()

    def __eq__(self, other_file):
        # Behaviour for equal is that True is returned if filename and size match
        if isinstance(other_file, FileRecord):
            return (
                    self.filename == other_file.filename
                and self.size == other_file.size
            )
        else:
            TypeError("comparison must be made with another FileRecord object")

    def __ne__(self, other_file):
        return not self.__eq__(other_file)

    def __lt__(self, other_file):
        if isinstance(other_file, FileRecord):
            return (
                    self.filename == other_file.filename
                and self.size < other_file.size
            )
        else:
            TypeError("comparison must be made with another FileRecord object")

    def __gt__(self, other_file):
        if isinstance(other_file, FileRecord):
            return (
                    self.filename == other_file.filename
                and self.size > other_file.size
            )
        else:
            TypeError("comparison must be made with another FileRecord object")

class Catalogue:

    def __init__(self, path, logger_name=__file__):
        # Assign empty variables
        self.path = path
        self.files = []
        self.catalogues = []

        # Assign logger name
        self.__logger_name = logger_name
        
        # Validate filename
        if path.parts[-1].lower() != "catalogue.csv":
            if path.is_dir():
                self.path = path / "catalogue.csv"
            else:
                raise ValueError("Catalogue files should be named 'catalogue.csv'.")
        
        # Load records from file
        self.read_from_csv()

    def __contains__(self, item):
        # Iterate over files and if matched, return true, otherwise return False
        for file in self.files:
            if item.filename == file.filename:
                return True
        return False

    def read_from_csv(self):
        # Create logger instance
        logger = logging.getLogger(self.__logger_name)
        # Check catalogue file exists
        if not self.path.is_file():
            logger.error(f"File {self.path} does not exist.")
            return

        # Open file
        with open(self.path, 'r') as cat_file:
            # Create CSV reader
            cat_reader = csv.reader(cat_file)
            header = cat_reader.__next__()
            header_map = {}
            #Store column index
            col_index = 0
            # Check each header and validate
            for header_name in header:
                # If valid store in map
                if header_name in FileRecord.FIELDS:
                    header_map[col_index] = header_name
                # otherwise error
                else:
                    raise ValueError(f"Invalid header name {header_name} in {self.path}.")
                col_index += 1
            # Now read rows of CSV file
            for row in cat_reader:
                file_record = self.file_record_from_csv(row, header_map)
                if not file_record in self:
                    self.files.append(file_record)
                else:
                    logger.warning(f"File {file_record.path} already found in catalogue {self.path}")

    def file_record_from_csv(self, row, header_map):
        # Assume that the directory for the catalogue is the parent directory
        file_record = FileRecord()
        # Iterate over values
        for k in range(len(row)):
            setattr(file_record, header_map[k], row[k])
        # Assign path to file record from catalogue
        file_record.path = self.path.parent / file_record.filename
        file_record.catalogued = True
        # Return instance of object
        return file_record

    def read_from_file_system(self, subfolders=False):
        # Assign loggers
        logger = logging.getLogger(self.__logger_name)
        # Read existing files
        for file in os.listdir(self.path.parent):
            file_path = self.path.parent / file
            logger.debug(f"Looking at {file_path}")
            if file_path.is_file():
                if file_path.parts[-1].lower() != "catalogue.csv":
                    logger.debug(f"Adding reference to file {file_path}")
                    file_record = FileRecord(file_path)
                    if not file_record in self:
                        file_record.catalogued = False
                        self.files.append(file_record)
                        logger.info(f"Added {file_record.path} to catalogue")
                    else:
                        file_record.catalogued = True
                        logger.warning(f"File {file_record.path} already found in catalogue {self.path}")
            elif file_path.is_dir() and subfolders:
                logger.debug(f"Going into subfolder {file_path}")
                # Create new sub catalogue
                sub_catalogue = Catalogue(file_path / "catalogue.csv", logger_name=self.__logger_name)
                # Read contents from catalogue
                sub_catalogue.read_from_file_system(subfolders=subfolders)
                # Add to top level list
                self.catalogues.append(sub_catalogue)

    def get_non_existent_files(self):
        # Create empty array to store file records
        non_existent_files = []
        # Iterate over files and fine those that do not exist
        for file in self.files:
            if not file.exists():
                non_existent_files.append(file)
        # Append to array
        return non_existent_files

    def get_non_catalogued_files(self):
        # Create empty array to store file records
        non_catalogued_files = []
        for file in self.files:
            if not file.catalogued:
                non_catalogued_files.append(file)
        # Append to array
        return non_catalogued_files

    def write(self):
        pass

def arg_validate_date(datestr):
    # Parse object to datetime - should raise value error if invalid
    dt = datetime.datetime.strptime(datestr, "%Y%m%d")
    return datestr

def populate_stack_from_catalogue(stack, path):
    
    # Load catalogue
    catalogue = Catalogue(path)
    
    # Now append all files to stack
    for fname in catalogue.filename:
        stack[fname] = 1

    return catalogue

def traverse(start_path, subfolders=False, logger_name=__file__):

    # Create a directory stack to store catalogue/directory locations
    dir_stack = []
    cat_stack = []
    # Create an empty stack for files to be appended to
    # file_stack = []
    # # Create an empty stack for missing catalogue files to be appended to
    # missing_stack = []
    # # Log missing catalogues
    # missing_cat = []

    # # Add root to dir_stack 
    # dir_stack.append(Catalogue(start_path))
    
    # # Start logger
    logger = logging.getLogger(logger_name);

    logger.info(f"Opening top-level catalogue at path {start_path}")
    
    # Create top-level catalogue
    top_cat = Catalogue(start_path, logger_name=logger_name)

    if subfolders:
        logger.info(f"Reading file system and subfolders within {start_path}")
    else:
        logger.info(f"Reading top-level directory only within {start_path}")
    
    # Read file-system from top-level directory
    top_cat.read_from_file_system(subfolders)
    
    return top_cat

def do_report(args):
    
    # Check report name
    report_name = "data_report.md"
    if args.name == None:
        # Select default name
        report_name = pathlib.Path(__file__).parent.parent / "Log" / \
        datetime.datetime.strftime(
            datetime.datetime.now(),
            "data_report_%Y%m%d_%H%M%S.md"
        )
    else:
        report_name = pathlib.Path(__file__).parent.parent / "Log" / args.name

    # Create logger
    logger = logging.getLogger("data_report");
    # Determine filename
    log_file = pathlib.Path(__file__).parent.parent / "Log" / "data_report.log"

    # Bit of a problem here if we try to make lots of reports simultaneously
    # so watch out...
    log_format = logging.Formatter("[%(asctime)s] %(levelname)8s :: %(message)s")
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setFormatter(log_format)
    # Assign handler
    logger.addHandler(log_file_handler)
    # and set level to INFO - this means we can keep debug messages if we like
    logger.setLevel(LOG_LEVEL)

    inc_subfolders = "N"
    if args.subfolders:
        inc_subfolders = "Y"

    logger.info("-" * 80)
    logger.info(f"DATA REPORT FOR PROJECT: {PROJECT_NAME}")
    logger.info("-" * 80)
    logger.info(f"I am about to write a data report for {args.path}")
    logger.info(f"You have given me the following options:")
    logger.info(f"\tInclude Subfolders? [{inc_subfolders}]")
    logger.info("")
    logger.info("-- START TEST --")
    logger.info("")

    # Get catalogue of files
    cat = traverse(args.path, subfolders=args.subfolders, logger_name="data_report")

    missing_files = []
    missing_catalogue = []
    missing_cat_entries = []

    # Iterate over catalogues
    cat_stack = [cat]
    while len(cat_stack) > 0:
        # Get current catalogue
        c_cat = cat_stack.pop()
        # Append catalogues within current catalogue if they exist
        for new_cat in c_cat.catalogues:
            cat_stack.append(new_cat)
        
        # With current catalogue, get catalogue files that do not exist
        if not c_cat.path.is_file():
            missing_catalogue.append(c_cat)

        # then get data files that don't exist
        for file in c_cat.get_non_existent_files():
            missing_files.append(file)

        # then get catalogue entries that do not exist (i.e. found a file but not cat entry)
        for file in c_cat.get_non_catalogued_files():
            missing_cat_entries.append(file)

    logger.info("")
    logger.info("-- END TEST -- ")
    logger.info("")
    logger.info("-- START REPORT --")
    logger.info("")

    # Print remaining files
    if len(missing_cat_entries) > 0:
        logger.warning(f"The following {len(missing_cat_entries)} files were found in the file system but not recorded in the catalogues:")
        for file in missing_cat_entries:
            logger.info(f"\t{file.path}")
    
    logger.info("")

    # Print missing files
    if len(missing_files) > 0:
        logger.warning(f"The following {len(missing_files)} files were found in the catalogues but not recorded in the file system:")
        for file in missing_files:
            logger.info(f"\t{file.path}")

    with open(report_name, 'w') as fh:

        # Get datetime as string
        timestring = datetime.datetime.strftime(datetime.datetime.now(),"%Y/%m/%d %H:%M:%S")
        # Write report title
        fh.writelines([
            f"# Data Report ({report_name.parts[-1]})\n\n",
            f"## Report Info\n\n",
            f"- Version `{VERSION}`\n",
            f"- Path `{args.path}`\n",
            f"- Subfolders `{inc_subfolders}`\n",
            f"- Generated `{timestring}`\n\n",
            "-"*80 + "\n\n"
            f"## Report Summary\n\n", 
            f"- Missing catalogues: `{len(missing_catalogue)}`\n",
            f"- Missing files: `{len(missing_files) + len(missing_cat_entries)}`\n",
            f"  - of which on file system but not catalogued   : `{len(missing_cat_entries)}`\n",
            f"  - of which in catalogue but not on file system : `{len(missing_files)}`\n",
            "\n", 
            "-"*80 + "\n\n",
            f"## Report Details\n\n"
        ])

        fh.write("### Missing Catalogues\n\n")
        fh.write("These files should be available on the Git repository.\n")
        fh.write("Have you pulled from the main branch recently?\n\n")
        fh.write("```text\n")
        for cat in missing_catalogue:
            fh.write(f"{cat.path}\n")
        fh.write("```\n\n")

        fh.write("### Missing Files on System\n\n")
        fh.write("These files are present in the `catalogue.csv` files that were found but not on your file system.\n")
        fh.write("You will need to download these files separately and request from colleagues.\n\n")
        fh.write("```text\n")
        for file in missing_files:
            fh.write(f"{file.path}\n")
        fh.write("```\n\n")

        fh.write("### Missing Files in Catalogue\n\n")
        fh.write("These files are present on your file system but not in `catalogue.csv` for the folder that contains them.\n")
        fh.write("If these files should be shared data then you need to update `catalogue.csv` manually or automatically\n")
        fh.write(f"using the `bin/data.py -u {args.path}` command.\n")
        fh.write("If the file does not need to be shared you can ignore the warning.\n\n")
        fh.write("```text\n")
        for file in missing_cat_entries:
            fh.write(f"{file.path}\n")
        fh.write("```\n")

    logger.info("")
    logger.info("-- END REPORT --")
    logger.info("-" * 80)

def create_catalogue(path):
    # Assign logger
    logger = logging.getLogger("data_update")    
    with open(path, 'w') as fh:
            # Iterate over fields in FileRecord
            for field in FileRecord.FIELDS[0:-1]:
                fh.write(f"{field},")
            fh.write(f"{FileRecord().FIELDS[-1]}\n")
            logger.info(f"Finished writing header to {path}")

def do_update(args):

    # Create logger
    logger = logging.getLogger("data_update");
    # Determine filename
    log_file = pathlib.Path(__file__).parent.parent / "Log" / "data_update.log"

    # Bit of a problem here if we try to make lots of reports simultaneously
    # so watch out...
    log_format = logging.Formatter("[%(asctime)s] %(levelname)8s :: %(message)s")
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setFormatter(log_format)
    # Assign handler
    logger.addHandler(log_file_handler)
    # and set level to INFO - this means we can keep debug messages if we like
    logger.setLevel(LOG_LEVEL)

    inc_subfolders = "N"
    if args.subfolders:
        inc_subfolders = "Y"

    logger.info("-" * 80)
    logger.info(f"DATA UPDATE FOR PROJECT: {PROJECT_NAME}")
    logger.info("-" * 80)
    logger.info(f"I am about to write a data update for {args.path}")
    logger.info(f"You have given me the following options:")
    logger.info(f"\tInclude Subfolders? [{inc_subfolders}]")
    logger.info(f"\tOwner [{args.owner}]")
    logger.info(f"\tDate [{args.date}]")
    logger.info(f"\tComment [{args.comment}]")
    logger.info("")
    logger.info("-- START TEST --")
    logger.info("")

    exist_in_cat, exist_in_fs, missing_cat = traverse(args.path, subfolders=args.subfolders, logger="data_update")

    # We're only interested in missing_cat and exist_in_fs
    
    # Create catalogues
    for cat_path in missing_cat:
        logger.info(f"Creating new file at {cat_path}")
        create_catalogue(cat_path)

    # Now iterate over missing files
    for file in exist_in_fs:
        # Get path to catalogue
        cat_path = file.path.parent / "catalogue.csv"
        # Create catalogue if it doesn't exist
        if not cat_path.is_file():
            logger.warning(f"Somehow we have missed the catalogue at {cat_path}")
            create_catalogue(cat_path)
        # Otherwise we'll open the file and write our record
        with open(cat_path, 'a') as fh:
            cat_obj = Catalogue(cat_path, header_only=True)
            # Now iterate over fields in header map
            n_fields = len(cat_obj.header_map)
            # Check owner exists
            if not file.owner:
                if args.owner != None:
                    file.owner = args.owner
                else:
                    try:
                        file.owner = file.path.owner()
                    except:
                        logger.warning("Could not find owner of file - are you running on Windows?")
            # Check comment exists
            if not file.comment:
                if args.comment != None:
                    file.comment = args.comment

            # Date added 
            if args.date:
                file.date_added = datetime.datetime.strptime(args.date, "%Y%m%d") 

            file.size = file.path.stat().st_size

            for idx in range(n_fields-1):
                fh.write(f"{getattr(file,cat_obj.header_map[idx])},")
            # Increment 
            idx = idx + 1
            fh.write(f"{getattr(file,cat_obj.header_map[idx])}\n")
        

    logger.info("-"*80)
    logger.info("Finished update")
    logger.info("-"*80)


if __name__ == "__main__":

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Manage ReMeltRadar Data Catalogues.  If no action specified, action defaults to update."
    )
    parser.add_argument("-u", "--update", help="Update catalogue.csv", action="store_true")
    parser.add_argument("-s", "--subfolders", help="Include subfolders in operation", action="store_true")
    parser.add_argument("-r", "--report", help="Generate missing file report", action="store_true")
    parser.add_argument("path", help="Path to folder from project root (i.e. /Raw/Folder/SubFolder)")
    parser.add_argument("-n", "--name", help="Path for where report should be written", default=None, required=False)
    parser.add_argument("-o", "--owner", help="Owner to be used when updating catalogue.csv", type=ascii)
    parser.add_argument("-d", "--date", help="Date to be used when updating catalogue.csv [YYYYMMDD]",type=arg_validate_date)
    parser.add_argument("-c", "--comment", help="Comment to be used when updating catalogue.csv",type=ascii)
    args = parser.parse_args()

    # Path should be a comment argument in both cases so we can reparse it
    # into a pathlib.Path object here
    args.path = pathlib.Path(args.path)

    # Check if path exists
    if not args.path.exists():
        # We can check whether the path is relative to the project root
        # (which we determine relative to the bin/data.py location)
        root = pathlib.Path(__file__).parent.parent
        rel_path = root / args.path
        # Check whether new relative path exists
        if not rel_path.exists():
            exit(f"Could not find {args.path} on filesystem.  Is the name typed correctly?")
        else:
            args.path = rel_path

    # Check if path is folder
    if args.path.is_file():
        exit(f"The path {args.path} points to a file not a folder. path should point to a folder only.")

    # Check what action we should take and default to update
    if args.report:
        do_report(args)
    else:
        do_update(args)