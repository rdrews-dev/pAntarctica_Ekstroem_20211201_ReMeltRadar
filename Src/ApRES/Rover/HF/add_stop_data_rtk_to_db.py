#!/usr/bin/python3
#
#   Auth: J.D. Hawkins
#   Date: 2022-03-15
#
#   Descriptions copies across RTK position information to StopStart.db
#
#   Requires: geopandas, sqlite3

import pandas
import pathlib
import re
import SQL.catalogue_data

# Path to database from project root
DB_PATH = "Doc/ApRES/Rover/HF/StartStop.db"
# Path to CSV file containing positional information
CSV_PATH = "Proc/ApRES/Rover/HF/start_stop_rtk.csv"

# Load database
database = SQL.catalogue_data.ApRESDatabase(DB_PATH, create=False)

# Read RTK data
rtk = pandas.read_csv(CSV_PATH)

# Now iterate over dataframe
for _, rtk_entry in rtk.iterrows():

    # Use filename to find corresponding row in DB
    fname = rtk_entry.filename
    cur = database.get_cursor()
    cur.execute("SELECT `measurement_id`, `tags` FROM `measurements` WHERE `filename` = (?)",(fname,))
    row = cur.fetchone()

    if row == None:
        print(f"Could not find {fname} in database.")
        continue

    # Create now GPS string
    new_gps_string = "gps_type={:d}".format(rtk_entry.gps_type)
    new_tags = new_gps_string

    # Check whether we have any (comma separated) tags
    if row[1] != None:
        # If we do, then look for a gps_type=? tag
        m = re.search(r"(?:gps_type)|(?:GPS_TYPE)=(\d+)", row[1])
        # Check if not none
        if m != None:
            new_tags = row[0:m.span[0]] + new_gps_string + row[m.span[1]:]
        else:
            new_tags = row[1] + "," + new_gps_string

    print(f"Updating record #{row[0]} ({fname})")
    cur.execute(
        "UPDATE `measurements` " +
        "SET `latitude` = (?), " + 
        "`longitude` = (?), " +
        "`elevation` = (?), " + 
        "`tags` = (?) " + 
        "WHERE `measurement_id` = (?);", 
        (
            rtk_entry.latitude,
            rtk_entry.longitude,
            rtk_entry.elevation,
            new_tags,
            row[0]
        )
    )

database.get_connection().commit()
