#!/usr/bin/python3
#
#   Setup project folders for ReMeltRadar data, documentation and processing.
#
#   Auth: J Hawkins
#   Date: 2022-01-12
#
#   Defines a top-level directory structure and then copies a folder hierarchy
#   to each folder so that data is organised by 
#   
#       ./[top_level]/[instrument]/[method]/[...]
#
#   Change Log
#   ---------------------------------------------------------------------------
#   2022-01-13: Updated setup.py to copy .gitignore files for different folders
#   2022-01-12: Create file.
#
#
#   Top-level directories are
#
#       ------------+---------------+-----------------------------------------
#       Untouched   | Read Only     | No changes to data at all 
#       ------------+---------------+-----------------------------------------
#       Raw         | Read Only     | Modify filenames etc. for clarity
#       ------------+---------------+-----------------------------------------
#       Proc        | Read/Write    | Processed datasets derived from scripts
#                   |               | in Src
#       ------------+---------------+-----------------------------------------
#       Src         | Write/Execute | Executable scripts for processing data
#       ------------+---------------+-----------------------------------------
#       Doc         | Read/Write    | Documentation and description of data
#                   |               | collection and processing approaches 
#       ------------+---------------+-----------------------------------------
#       QGis        | Read/Write    | GIS data (doesn't have copied folders)
#       ------------+---------------+-----------------------------------------
#
#   i.e. for raw PulseEKKO data collected in along flow on the 12/01/2022 the
#   file path would be
#       
#       ./Raw/PulseEKKO/AlongFlow_20220112.gfz
#
#   Overview of path structure within each top-level folder is  
#
#       /ApRES
#       |
#       |---/Rover
#       |   |---/HF
#       |   |---/VHF
#       |   |
#       |   /SPM
#       |   |---/SPM_A
#       |   |---/SPM_X
#       |   |---/SPM_X2
#       |   |---/SPM_X3
#       |   |---/SPM_X4
#       |
#       /CApRES
#       |
#       /PulseEKKO
#       |
#       /RTKGPS

##############################################################################
# Project Variables
##############################################################################
PROJECT_NAME = "ReMeltRadar21"
PROJECT_ROOT = "./"
LOG_NAME = "Log/setup.log"

##############################################################################
# Define Folder Structure
#   "folder_name" : True/False for copying sub_folder structure
##############################################################################
top_level_directories = {
    "Raw" : True,
    "Proc" : True,
    "Src" : True,
    "Doc" : True,
    "QGis" : False,
    "Untouched" : True
}

# Sub-level shared folders
sub_folders = {
    "VNA" : {
        "HFAntenna" : {},
        "CableLength" : {}
    },
    "ApRES" : {
        "Rover" : {
            "HF" : {},
            "VHF" : {}
        }, 
        "SPM" : {
            "SPM_A" : {},
            "SPM_X" : {},
            "SPM_X2" : {},
            "SPM_X3" : {},
            "SPM_X4" : {}
        }
    },
    "CApRES" : {},
    "PulseEKKO" : {},
    "RTKGPS" : {}
}

##############################################################################
# Imports
#   (Come after definition of folder structure for clarity)
##############################################################################
from abc import abstractmethod
import pathlib
import shutil
import logging

##############################################################################
# Main Routine
##############################################################################
def create_subfolder_structure(root, folder_structure):
    
    logger = logging.getLogger(__name__)

    # Check folder_structure is dictionary
    if not isinstance(folder_structure, dict):
        logger.error("folder_structure must be of type 'dict'");
        raise ValueError("folder_structure must be of type 'dict'")

    # Iterate over folder_structure
    for key in folder_structure:
        
        # Create current path
        c_path = root / key;
        if not c_path.exists():
            logger.info(f"Creating {c_path}")
            c_path.mkdir()
        else:
            logger.warning(f"{c_path} already exists.")

        # Create subfolders
        sub_folders = folder_structure[key]
        if isinstance(sub_folders, dict):
            create_subfolder_structure(c_path, sub_folders)
        else:
            logger.warning(f"Argument given in {c_path} is not a dict. Skipping.")

def create_file_structure(root, top_level, copy_folder):

    logger = logging.getLogger(__name__)
    
    # Start by creating top_level directories if they don't exist
    for dir_name in top_level:
        # Get current top level path 
        tl_path = root / pathlib.Path(dir_name)
        
        # Check whether path exists
        logger.info(f"Checking if {tl_path} exists...")
        if not tl_path.exists():
            logger.info(f"Creating {tl_path}")
            tl_path.mkdir()
        else:
            logger.warning(f"{tl_path} already exists")
        
        # Create subfolder structure
        if top_level[dir_name]:
            create_subfolder_structure(tl_path, copy_folder)


##############################################################################
# Command Line Routine
##############################################################################
if __name__ == "__main__":

    # Set logging name
    log_path = pathlib.Path(LOG_NAME)
    
    # Check logging directory exists
    if not log_path.exists():
        if len(log_path.parents) > 0:
            log_path.parents[0].mkdir(parents=True)

    # Get logging instance
    logger = logging.getLogger(__name__)

    # Create file handle for logger
    file = logging.FileHandler(log_path)
    console = logging.StreamHandler()

    # Set format for logger
    logger_format = logging.Formatter('[%(asctime)s] %(levelname)s :: %(message)s')
    file.setFormatter(logger_format)
    console.setFormatter(logger_format)

    # Add file handler to logger
    logger.addHandler(file)
    logger.addHandler(console)
    # and set level to warning
    logger.setLevel(logging.INFO) 

    # Parse root path
    root_path = pathlib.Path(PROJECT_ROOT)
    logger.info(f"Create directory structure for {PROJECT_NAME} in {root_path}...")

    # Create file structure
    create_file_structure(root_path, top_level_directories, sub_folders)

    # Check .gitignore exists
    setup_path = root_path / "Setup"
    if not (root_path / ".gitignore").is_file():
        logger.warning(f"Could not find a .gitignore file in the {root_path} directory. I'll copy one now.")
        shutil.copyfile(setup_path / ".gitignore", root_path / ".gitignore");

    # Check Src/.gitignore exists
    src_path = root_path / "Src"
    if not (src_path / ".gitignore").is_file():
        logger.warning(f"Could not find a .gitignore file in {src_path}. I'll copy one now.")
        shutil.copyfile(setup_path / "Src/.gitignore", root_path / "Src/.gitignore");
    
    # Check Src/.gitignore exists
    doc_path = root_path / "Doc"
    if not (doc_path / ".gitignore").is_file():
        logger.warning(f"Could not find a .gitignore file in {src_path}. I'll copy one now.")
        shutil.copyfile(setup_path / "Doc/.gitignore", root_path / "Doc/.gitignore");

    