import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
import pandas
import pathlib
import pyproj
import sys

# Add upper path
__file__path__ = pathlib.Path(os.path.realpath(__file__))
sys.path.insert(0, str(__file__path__.parent.parent))

import SQL.catalogue_data as apresdb

# Define colour fields
ucl_blue = (0, 151/255, 169/255)
ucl_orange = (234/255, 118/255, 0)
ucl_green = (181/255, 189/255, 0)
ucl_red = (213/255, 0, 50/255)

MARKER_SIZE = 1

line_colors = (ucl_blue, ucl_orange, ucl_green, ucl_red)

# Define paths
ROOT_PATH = pathlib.Path(".")
DB_PATH = ROOT_PATH / pathlib.Path("Doc/ApRES/Rover/HF/StartStop.db")

FIG_PATH = ROOT_PATH / "Doc/ApRES/Rover/HF/StartStop"

db_man = apresdb.ApRESDatabase(DB_PATH)

cursor = db_man.get_cursor()
cursor.execute("SELECT " 
    "`measurement_id`, "
    "`timestamp`, "
    "`tags`, "
    "`latitude`, "
    "`longitude`, "
    "`elevation` "
    "FROM `measurements` WHERE "
    "`latitude` IS NOT NULL AND "
    "`longitude` IS NOT NULL AND "
    "`elevation` IS NOT NULL ORDER BY `timestamp`;")

results = pandas.DataFrame(cursor.fetchall())
results = results.rename(columns={
    0 : "measurement_id", 
    1 : "timestamp",
    2 : "tags",
    3 : "latitude",
    4 : "longitude",
    5 : "elevation"
})

results["timestamp"] = pandas.to_datetime(results["timestamp"])

# Extract GPS type to column
results["gps_type"] = results.tags.str.extract(r'gps_type=(\d+)')
results["gps_type"] = pandas.to_numeric(results["gps_type"])

ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')

x0, y0, z0 = pyproj.transform(
    lla,
    ecef,
    -8.41588,
    -71.61375,
    90,
    radians=False
)
z0 = 98

x, y, z = pyproj.transform(
    lla, 
    ecef, 
    results.longitude,
    results.latitude, 
    results.elevation, 
    radians=False
)

day_7 = results.timestamp.dt.day == 7
day_8 = results.timestamp.dt.day == 8

minx = np.min(x - x0)
miny = np.min(y - y0)
minz = np.min(results.elevation - z0)

maxx = np.max(x - x0)
maxy = np.max(y - y0)
maxz = np.max(results.elevation - z0)

# Calculate time ratio for axis
day_ratio = (max(results[day_7].timestamp) - min(results[day_7].timestamp)).seconds / \
    (max(results[day_8].timestamp) - min(results[day_8].timestamp)).seconds

fig, ax = plt.subplots(3,2, figsize=(7.5,4), dpi=300,  gridspec_kw={"width_ratios" : [day_ratio, 1]}, sharex='col', sharey='row')

ax[0][0].plot(results.timestamp[day_7 & (results.gps_type == 4)], x[day_7 & (results.gps_type == 4)] - x0, '.', color=ucl_blue, markersize=MARKER_SIZE)
ax[0][0].plot(results.timestamp[day_7 & (results.gps_type == 2)], x[day_7 & (results.gps_type == 2)] - x0, '.', color=ucl_orange, markersize=MARKER_SIZE)
ax[0][0].plot(results.timestamp[day_7 & (results.gps_type == 1)], x[day_7 & (results.gps_type == 1)] - x0, '.', color=ucl_red, markersize=MARKER_SIZE)
ax[0][0].grid()
ax[0][0].set_ylim([minx, maxx])
ax[0][0].set_ylabel("Easting (m)")

ax[1][0].plot(results.timestamp[day_7 & (results.gps_type == 4)], y[day_7 & (results.gps_type == 4)] - y0, '.', color=ucl_blue, markersize=MARKER_SIZE)
ax[1][0].plot(results.timestamp[day_7 & (results.gps_type == 2)], y[day_7 & (results.gps_type == 2)] - y0, '.', color=ucl_orange, markersize=MARKER_SIZE)
ax[1][0].plot(results.timestamp[day_7 & (results.gps_type == 1)], y[day_7 & (results.gps_type == 1)] - y0, '.', color=ucl_red, markersize=MARKER_SIZE)
ax[1][0].grid()
ax[1][0].set_ylim([miny, maxy])
ax[1][0].set_ylabel("Northing (m)")

ax[2][0].plot(results.timestamp[day_7 & (results.gps_type == 4)], results.elevation[day_7 & (results.gps_type == 4)] - z0, '.', color=ucl_blue, markersize=MARKER_SIZE)
ax[2][0].plot(results.timestamp[day_7 & (results.gps_type == 2)], results.elevation[day_7 & (results.gps_type == 2)] - z0, '.', color=ucl_orange, markersize=MARKER_SIZE)
ax[2][0].plot(results.timestamp[day_7 & (results.gps_type == 1)], results.elevation[day_7 & (results.gps_type == 1)] - z0, '.', color=ucl_orange, markersize=MARKER_SIZE)
ax[2][0].grid()
ax[2][0].set_ylim([minz, maxz])
ax[2][0].set_ylabel("Up (m)")

ax[0][1].plot(results.timestamp[day_8 & (results.gps_type == 4)], x[day_8 & (results.gps_type == 4)] - x0, '.', color=ucl_blue, markersize=MARKER_SIZE)
ax[0][1].plot(results.timestamp[day_8 & (results.gps_type == 2)], x[day_8 & (results.gps_type == 2)] - x0, '.', color=ucl_orange, markersize=MARKER_SIZE)
ax[0][1].plot(results.timestamp[day_8 & (results.gps_type == 1)], x[day_8 & (results.gps_type == 1)] - x0, '.', color=ucl_red, markersize=MARKER_SIZE)
ax[0][1].grid()
ax[0][1].set_ylim([minx, maxx])

ax[1][1].plot(results.timestamp[day_8 & (results.gps_type == 4)], y[day_8 & (results.gps_type == 4)] - y0, '.', color=ucl_blue, markersize=MARKER_SIZE, label="gps_type=4")
ax[1][1].plot(results.timestamp[day_8 & (results.gps_type == 2)], y[day_8 & (results.gps_type == 2)] - y0, '.', color=ucl_orange, markersize=MARKER_SIZE, label="gps_type=2")
ax[1][1].plot(results.timestamp[day_8 & (results.gps_type == 1)], y[day_8 & (results.gps_type == 1)] - y0, '.', color=ucl_red, markersize=MARKER_SIZE, label="gps_type=1")
ax[1][1].grid()
ax[1][1].set_ylim([miny, maxy])
ax[1][1].legend(loc=4, fontsize=8)

# Define legend

ax[2][1].plot(results.timestamp[day_8 & (results.gps_type == 4)], results.elevation[day_8 & (results.gps_type == 4)] - z0, '.', color=ucl_blue, markersize=MARKER_SIZE)
ax[2][1].plot(results.timestamp[day_8 & (results.gps_type == 2)], results.elevation[day_8 & (results.gps_type == 2)] - z0, '.', color=ucl_orange, markersize=MARKER_SIZE)
ax[2][1].plot(results.timestamp[day_8 & (results.gps_type == 1)], results.elevation[day_8 & (results.gps_type == 1)] - z0, '.', color=ucl_red, markersize=MARKER_SIZE)
ax[2][1].grid()
ax[2][1].set_ylim([minz, maxz])

# Get only the month to show in the x-axis:
ax[2][1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax[2][1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
ax[2][1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
ax[2][1].set_xlabel("Time of Day")
ax[2][1].set_xlim(
    [datetime.datetime(2022, 1, 8, 12, 30, 00), \
     datetime.datetime(2022, 1, 8, 17, 45, 00)]
)

ax[2][0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax[2][0].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
ax[2][0].xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
ax[2][0].set_xlabel("Time of Day")
ax[2][0].set_xlim(
    [datetime.datetime(2022, 1, 7, 18, 15, 00), \
     datetime.datetime(2022, 1, 7, 19, 30, 00)]
)

ax[0][0].set_title('2022-01-07')
ax[0][1].set_title('2022-01-08')

for a in ax:
    try:
        a.label_outer()
    except:
        pass

fig.tight_layout()
fig.savefig(FIG_PATH / "StartStopRawPositions.png")

# plt.show()
print()