# Data Management Routines for ReMeltRadar Data Folders
#
#   Auth: JD Hawkins
#   Date: 2022-01-13
#
#   Change Log:
#   ---------------------------------------------------------------------------
#   2022-13-01: Created.
#
#   

import argparse
import csv
import datetime
import logging
from msilib.schema import File
import os
import pathlib

class FileRecord:

    FIELDS = [
        "filename",
        "size",
        "owner",
        "date_added",
        "comment"
    ]

    def __init__(self):
        # Assign None to all field values
        for field in self.FIELDS:
            setattr(self, field, None)

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
        
    @staticmethod
    def from_csv_row(header, values):

        # Check header and values are same length
        if len(header) != len(values):
            raise ValueError("header and values must have the same number of elements.")

        # Create new record
        new_file = FileRecord()

        # Iterate over fields
        for k in range(len(values)):
            setattr(new_file,header[k],values[k])

        return new_file

    @staticmethod
    def from_path(path):

        # Cast to pathlib.Path object if we haven't already been passed one
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path);

        # Check file exists
        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            raise ValueError("path must point to a file-like object.")

        file_record = FileRecord()

        # Now load fields
        file_record.filename = path.parts[-1]
        file_record.date_added = datetime.datetime.utcfromtimestamp(path.stat().st_mtime)
        try:
            file_record.owner = path.owner()
        except NotImplementedError:
            file_record.owner = ""
        file_record.size = path.stat().st_size
        file_record.comment = ""

class Catalogue:

    def __init__(self, path):
        
        # Initialise variables
        self.files = []
        self.path = path

        # Load catalogue from CSV
        if path.is_file():
            logger = logging.getLogger("data_report")
            logger.debug(f"Path {path} exists, loading from CSV.")
            self.load_from_csv(path)

    def load_from_csv(self, path):

        # Check whether catalogue.csv file path exists
        if not path.is_file():
            # Try to find catalogue.csv
            path = path / "catalogue.csv";
            if not path.is_file():
                raise FileNotFoundError(path)

        with open(path, 'r') as cat_file:
            cat_reader = csv.reader(cat_file)
            
            # Read first line and test for header
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
                    raise ValueError(f"Invalid header name {header_name} in {path}.")
                col_index += 1

            # Now when we read from files we can use the header_map to 
            # select the correct column to read from
            for row in cat_reader:
                # Read file from row
                self.files.append(FileRecord.from_csv_row(header_map, row))


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

def do_report(args):

    # Create logger
    logger = logging.getLogger("data_report");
    # Determine filename
    log_file = pathlib.Path(__file__).parent.parent / "Log" / \
        datetime.datetime.strftime(
            datetime.datetime.now(),
            "data_report_%Y%m%d_%H%M%S.log"
        )

    # Bit of a problem here if we try to make lots of reports simultaneously
    # so watch out...
    log_format = logging.Formatter("[%(asctime)s] %(levelname)s :: %(message)s")
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setFormatter(log_format)
    # Assign handler
    logger.addHandler(log_file_handler)
    # and set level to INFO - this means we can keep debug messages if we like
    logger.setLevel(logging.DEBUG)

    # Create a directory stack to store catalogue/directory locations
    dir_stack = []
    # Create an empty stack for files to be appended to
    file_stack = []
    # Create an empty stack for missing catalogue files to be appended to
    missing_stack = []

    # Add root to dir_stack 
    dir_stack.append(Catalogue(args.path))
    
    # Variable to track maximum file path
    max_file_path = 0

    inc_subfolders = "N"
    if args.subfolders:
        inc_subfolders = "Y"

    logger.info(f"I am about to write a data report for {args.path}")
    logger.info(f"You have given me the following options:")
    logger.info(f"\tInclude Subfolders? [{inc_subfolders}]")
    logger.info("")
    logger.info("-- START TEST --")
    logger.info("")

    # Now iterate over dir_stack until empty
    while len(dir_stack) > 0:
        
        # Get last element of the stack
        catalogue = dir_stack.pop()

        logger.info(f"Reading {catalogue.path}")

        # Read the catalogue to know what files we should expect to see
        logger.debug(f"I am aware of {len(catalogue.files)} files in {catalogue.path}")

        # Now read files in the current directory
        for file in os.listdir(catalogue.path.parent):
            f_path = catalogue.path / file
            if not f_path.is_file() and args.subfolders:
                # Must be a subfolder - so if we are using subfolders then
                # add it to the directory stack
                dir_stack.append(Catalogue(f_path / "catalogue.csv"))
            elif f_path.is_file() and file.lower() != "catalogue.csv":
                # Append file to file stack
                file_stack.append(FileRecord.from_path(f_path))
                if len(str(f_path)) > max_file_path:
                    max_file_path = len(str(f_path))

        logger.debug("File stack")
        logger.debug("----------")
        for file in file_stack:
            logger.debug(file)
        logger.debug("----------")

        # Now iterate through the catalogue
        for file in catalogue.files:
            f_path = catalogue.path / file.filename
            logger.debug(f"Searching for {f_path}")
            if f_path in file_stack:
                file_stack.pop(file_stack.index(f_path))
            else:
                missing_stack.append(file)
                if len(str(f_path)) > max_file_path:
                    max_file_path = len(str(f_path))

    logger.info("")
    logger.info("-- END TEST -- ")
    logger.info("")
    logger.info("-- START RESULTS --")
    logger.info("")

    # Print remaining files
    if len(file_stack) > 0:
        logger.warning(f"The following {len(file_stack)} files were found in the file system but not recorded in the catalogues:")
        for file in file_stack:
            logger.info(f"\t{file}")
    
    logger.info("")

    # Print missing files
    if len(missing_stack) > 0:
        logger.warning(f"The following {len(missing_stack)} files were found in the catalogues but not recorded in the file system:")
        for file in missing_stack:
            logger.info(f"\t{file}")

    logger.info("")
    logger.info("-- END REPORT --")
    logger.info("")


def do_update(args):
    print("Doing update - yay")

if __name__ == "__main__":

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Manage ReMeltRadar Data Catalogues.  If no action specified, action defaults to update."
    )
    parser.add_argument("-u", "--update", help="Update catalogue.csv", action="store_true")
    parser.add_argument("-s", "--subfolders", help="Include subfolders in operation", action="store_true")
    parser.add_argument("-r", "--report", help="Generate missing file report", action="store_true")
    parser.add_argument("path", help="Path to folder from project root (i.e. /Raw/Folder/SubFolder)")
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