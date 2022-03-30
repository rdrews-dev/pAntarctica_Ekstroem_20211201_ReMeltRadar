# process_start_stop_pos.py
#
#   Auth: J.D. Hawkins
#   Date: 2022-02-23
#
#   Description: Iterate through SubZero log files and strip ApRES measurment
#                filenames and position data.
# 
#   Requires: rover_apres_log, geopandas, pandas
# 
import os
import pathlib 
import sys

# Add parent directory to current file path to use rover_log
__file__path__ = pathlib.Path(os.path.realpath(__file__))
sys.path.insert(0, str(__file__path__.parent.parent.parent))

import rover_log

# List files with relevant HF ApRES positional data
files = [
    "Raw/ApRES/Rover/Log/37_SubZeroDrive_01072022_172020.txt",
    "Raw/ApRES/Rover/Log/38_SubZeroDrive_01072022_173626.txt",
    "Raw/ApRES/Rover/Log/39_SubZeroDrive_01072022_180050.txt",
    "Raw/ApRES/Rover/Log/40_SubZeroDrive_01082022_113357.txt",
    "Raw/ApRES/Rover/Log/41_SubZeroDrive_01082022_122855.txt",
    "Raw/ApRES/Rover/Log/42_SubZeroDrive_01082022_123903.txt",
    "Raw/ApRES/Rover/Log/43_SubZeroDrive_01082022_124002.txt",
    "Raw/ApRES/Rover/Log/44_SubZeroDrive_01082022_181526.txt",
    "Raw/ApRES/Rover/Log/45_SubZeroDrive_01082022_182519.txt"
]

events = None

for file in files:
    # Load measurement events from file
    new_events = rover_log.parse_apres_burst_events(file)
    # then either save in first instance, or append to existing results
    if not isinstance(events, list):
        events = new_events
    else:
        events.extend(new_events)

    print(f"Recorded {len(new_events)} new events of {len(events)} total.")

# Create data frame
frame = rover_log.apres_burst_events_to_dataframe(events)
# and write to file
frame.to_csv("Proc/ApRES/Rover/HF/StartStop/start_stop_rtk.csv", index=False)