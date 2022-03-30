# process_rover_telemetry.py
#
#   Auth: J.D. Hawkins
#   Date: 2022-03-30
#
#   Description: Iterate through SubZero log files and strip telemetry data
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
    "Raw/ApRES/Rover/Log/46_SubZeroDrive_01092022_155344.txt",
]

events = None

for file in files:
    # Load measurement events from file
    new_events = rover_log.parse_telemetry_events(file)
    # then either save in first instance, or append to existing results
    if not isinstance(events, list):
        events = new_events
    else:
        events.extend(new_events)

    print(f"Recorded {len(new_events)} new events of {len(events)} total.")

# Create data frame
frame = rover_log.telemetry_events_to_dataframe(events)
# and write to file
frame.to_csv("Proc/ApRES/Rover/HF/Kinematic/kinematic_rover_rtk.csv", index=False)