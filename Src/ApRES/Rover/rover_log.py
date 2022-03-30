# Log ApRES position data to CSV
# 
#   Auth: J.D. Hawkins
#   Date: 2022-02-23
#
#   Description: Parses a rover log *.txt file, collects 'ApRES:' logging info
#                and outputs each measurment point to a csv file.
#
#   Usage:
#
#       rover_log log_position_to_csv.py /path/to/log.txt /path/to/output.csv
#

import argparse
import datetime
import geopandas
import pandas
import pathlib
import re

class BurstEvent:

    def __init__(self, 
        timestamp=None,
        filename=None, 
        point_name=None, 
        latitude=None, 
        longitude=None, 
        elevation=None, 
        gps_type=0
    ):

        # Validate and assign variables
        if timestamp != None and not isinstance(timestamp, datetime.datetime):
            raise TypeError("timestamp should be of type 'datetime.datetime'.")
        self.timestamp = timestamp

        if filename != None and not isinstance(filename, str):
            raise TypeError("filename should be of type 'str'.")
        self.filename = filename

        if point_name != None and not isinstance(point_name, str):
            raise TypeError("point_no should be of type 'str'.")
        self.point_name = point_name
        
        pos_none_check = [
            latitude == None, 
            longitude == None, 
            elevation == None
        ]

        # Checks we assign all position variables
        if any(pos_none_check) and not all(pos_none_check):
            raise TypeError("Either all lat, long, el values must be assigned or all must be None")

        # Boo repetitive code but oh well...
        if not pos_none_check[0] and not isinstance(latitude, float):
            raise TypeError("latitude should be of type 'float'.")
        if not pos_none_check[1] and not isinstance(longitude, float):
            raise TypeError("longitude should be of type 'float'.")
        if not pos_none_check[2] and not isinstance(elevation, float):
            raise TypeError("elevation should be of type 'float'.") 

        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

        if not isinstance(gps_type, int):
            raise TypeError("gps_type should be of type 'int'.")
        self.gps_type = gps_type

    def __repr__(self):
        return f"BurstEvent({self.filename})" +  \
            f"\n\tLat: {self.latitude}" + \
            f"\n\tLong: {self.longitude}" + \
            f"\n\tElev: {self.elevation}"

class RoverTelemetry:

    def __init__(self, timestamp):

        if not isinstance(timestamp, datetime.datetime):
            raise TypeError("timestamp should be of type 'datetime.datetime'.")
        self.timestamp = timestamp

    @staticmethod
    def from_log_line(timestamp, csv_data):
        # Create new telemetry object
        telemetry = RoverTelemetry(timestamp)#

        # TODO: properly assign all telemetry properties to from CSV string
        csv_split = csv_data.split(",")

        telemetry.latitude = float(csv_split[2])
        telemetry.longitude = float(csv_split[3])
        telemetry.elevation = float(csv_split[4])
        telemetry.gps_type = int(csv_split[16])
        telemetry.battery_voltage = float(csv_split[7])

        return telemetry

class SubZeroLogIterator:

    def __init__(self, path):

        # Try and open log file
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        if not path.is_file():
            raise FileNotFoundError(path)

        # Save path
        self.path = path
        # Initialise with empty file handle
        self.fh = None

    def __enter__(self):
        # Close existing file handle
        if self.fh != None:
            self.fh.close()

        # Open file handle with path
        self.fh = open(self.path, "r")

        return self

    def __exit__(self, exc_type, exc_value, tb):
        # Close file
        self.fh.close()
        if exc_type is not None:
            return False
        return True

    def __iter__(self):
        # Check we have opened the file handle
        if self.fh.closed:
            raise ValueError("Log file handle closed.")
        # If so then let's return to the start of the file 
        self.fh.seek(0)
        return self

    @staticmethod
    def parse_log_line(line): 
        # Strip line into sections with regex
        line_match = re.match(r"([\d\-\:\, ]+) \- (\w+) \- (\w+) \- (.+)", line)
        if line_match == None:
            return None
        else:
            # Strip components from match
            timestamp = datetime.datetime.strptime(
                line_match.group(1), "%Y-%m-%d %H:%M:%S,%f")
            user = line_match.group(2)
            level = line_match.group(3)
            message = line_match.group(4)
            # And return values
            return timestamp, user, level, message

class SubZeroApRESBurstIterator(SubZeroLogIterator):

    def __next__(self):

        # Create default variable for latest event
        last_burst = {}
        last_stage = 0
        current_stage = 0

        line = self.fh.readline()
        # Otherwise, lets try and parse the line
        while len(line) > 0:
            
            # Parse line into log format
            parsed_line =  SubZeroLogIterator.parse_log_line(line)
            
            if parsed_line == None:
                line = self.fh.readline()
                continue

            time, user, level, message = parsed_line

            # Now check if message is an "ApRES:" message
            if message.startswith("ApRES:"):

                if len(last_burst) == 0:
                    # First stage - check for BURSTINFO
                    match = re.match(r"ApRES: BURSTINFO@(.+)", message)
                    if match != None:
                        last_burst["name"] = match.group(1)

                elif len(last_burst) == 1:
                    # Second stage - check for PointName
                    match = re.match(r"ApRES: PointName@(.+)", message)
                    if match != None:
                        last_burst["filename"] = match.group(1)
                    else:
                        print(f"Invalid log.\n\tExpected ApRES: PointName.\n\tGot {message}.")
                        last_burst = {}

                elif len(last_burst) == 2:
                    # Third stage - check for PointInfo
                    match = re.match(r"ApRES: PointInfo@(\d+),(-?[\d\.]+),\[(\-?[\d\.]+), ?(\-?[\d\.]+)\],(\-?[\d\.]+),(\d+)", message)
                    if match != None:
                        # Pull fields from burst
                        last_burst["burst_number"] = int(match.group(1))
                        last_burst["latitude"] = float(match.group(3))
                        last_burst["longitude"] = float(match.group(4))
                        last_burst["elevation"] = float(match.group(5))
                        last_burst["gps_type"] = int(match.group(6))

                        return BurstEvent(
                            time, 
                            last_burst["filename"],
                            last_burst["name"],
                            last_burst["latitude"],
                            last_burst["longitude"],
                            last_burst["elevation"],
                            last_burst["gps_type"]
                        )

                    else:
                        print(f"Invalid log.\n\tExpected ApRES: PointInfo.\n\tGot {message}.")
                        last_burst = {}

            else:
                last_burst = {}

            line = self.fh.readline()

        else:
        # we can't read in anything further
            raise StopIteration

class SubZeroTelemetryIterator(SubZeroLogIterator):

    def __next__(self):
        # Read a file until next TELEMETRY: message
        line = self.fh.readline()
        while len(line) > 0:
            # Read line
            parsed_line = SubZeroLogIterator.parse_log_line(line)
            # skip if format is incorrect
            if parsed_line == None:
                line = self.fh.readline()
                continue
            # and now unpack valid line
            time, user, level, message = parsed_line
            match = re.match(r"RADIO: sent #TELEMETRY,(.+)\$", message)
            if match != None:
                # we have a valid telemetry message
                return RoverTelemetry.from_log_line(time, match.group(1))
            line = self.fh.readline()
        else:
            raise StopIteration
                
def apres_burst_events_to_dataframe(events):

    # Get fields for dataframe
    filename    = [e.filename for e in events]
    timestamp   = [e.timestamp for e in events]
    posixtime   = [e.timestamp.timestamp() for e in events]
    latitude    = [e.latitude for e in events]
    longitude   = [e.longitude for e in events]
    elevation   = [e.elevation for e in events]
    gps_type    = [e.gps_type for e in events]
    
    # Put into dict
    df = pandas.DataFrame(
        {
            "filename" : filename,
            "timestamp" : timestamp,
            "posixtime" : posixtime,
            "latitude" : latitude,
            "longitude" : longitude,
            "elevation" : elevation,
            "gps_type" : gps_type
        }
    )

    # Convert to geodataframe
    df = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(
            df.longitude,
            df.latitude,
            df.elevation
        )
    )

    return df

def telemetry_events_to_dataframe(events):

    timestamp       = [e.timestamp for e in events]
    posixtime       = [e.timestamp.timestamp() for e in events]
    latitude        = [e.latitude for e in events]
    longitude       = [e.longitude for e in events]
    elevation       = [e.elevation for e in events]
    battery_voltage = [e.battery_voltage for e in events]
    gps_type        = [e.gps_type for e in events]

    # Put into dict
    df = pandas.DataFrame(
        {
            "timestamp" : timestamp,
            "posixtime" : posixtime,
            "latitude" : latitude,
            "longitude" : longitude,
            "elevation" : elevation,
            "gps_type" : gps_type,
            "battery_voltage" : battery_voltage
        }
    )

    # Convert to geodataframe
    df = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(
            df.longitude,
            df.latitude,
            df.elevation
        )
    )

    return df
    
def parse_apres_burst_events(path_to_log):

    events = []
    with SubZeroApRESBurstIterator(path_to_log) as rover_log:
        for burst in rover_log:
            events.append(burst)

    return events

def parse_telemetry_events(path_to_log):

    events = []
    with SubZeroTelemetryIterator(path_to_log) as rover_log:
        for telemetry in rover_log:
            events.append(telemetry)
    
    return events

def parse_apres_burst_events_to_dataframe(path_to_log):
    events = parse_apres_burst_events(path_to_log)
    return apres_burst_events_to_dataframe(events)

if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # Parse input arguments:
    parser = argparse.ArgumentParser(description=\
        """Parses a rover logging *.txt file, collects 'ApRES:' logging info
and outputs each measurement point to a csv file.""")

    # Setup arguments
    parser.add_argument("input_path", help="Path to input log *.txt file")
    parser.add_argument("output_path", help="Path to output *.csv file")

    arguments = parser.parse_args()

    # Parse log file
    log_events_list = parse_apres_burst_events(arguments.input_path)

    log_events_frame = apres_burst_events_to_dataframe(log_events_list)

    log_events_frame.to_csv(arguments.output_path, index=False)
