import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import pathlib 

# Define colour fields
ucl_blue = (0, 151/255, 169/255)
ucl_orange = (234/255, 118/255, 0)
ucl_green = (181/255, 189/255, 0)
ucl_red = (213/255, 0, 50/255)

MARKER_SIZE=0.5

ROOT_PATH = pathlib.Path(".")
DB_PATH = ROOT_PATH / pathlib.Path("Doc/ApRES/Rover/HF/StartStop.db")

FIG_PATH = ROOT_PATH / "Doc/ApRES/Rover/HF/StartStop"

df = pd.read_csv("Proc/RTKGPS/ApRES/Rover/HF/rtk_processed.csv")

# Convert first column to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create day indices
day_7 = df.timestamp.dt.day == 7
day_8 = df.timestamp.dt.day == 8

day_7_min = datetime.datetime(2022, 1, 7, 18, 15, 00)
day_7_max = datetime.datetime(2022, 1, 7, 19, 30, 00)

day_8_min = datetime.datetime(2022, 1, 8, 12, 30, 00)
day_8_max = datetime.datetime(2022, 1, 8, 17, 45, 00)

day_ratio = (day_7_max -day_7_min).seconds / \
    (day_8_max - day_8_min).seconds

# Highlight active areas 
ACTIVE_AREAS = [
    [datetime.datetime(2022, 1, 7, 18, 24, 29), datetime.datetime(2022, 1, 7, 19, 23, 50)],
    [datetime.datetime(2022, 1, 8, 12, 45, 00), datetime.datetime(2022, 1, 8, 13, 43, 53)],
    [datetime.datetime(2022, 1, 8, 13, 47, 25), datetime.datetime(2022, 1, 8, 14, 44, 36)],
    [datetime.datetime(2022, 1, 8, 14, 47, 55), datetime.datetime(2022, 1, 8, 15, 43, 35)],
    [datetime.datetime(2022, 1, 8, 16, 23, 54), datetime.datetime(2022, 1, 8, 16, 50, 57)],
    [datetime.datetime(2022, 1, 8, 17, 16, 00), datetime.datetime(2022, 1, 8, 17, 31,  9)]
]

def highlight_active_areas(ax, areas):
    for area in areas:
        ax.axvspan(area[0], area[1], color=[0.5, 0.5, 0.5], alpha=0.1)

# Create figure
fig, ax = plt.subplots(3,2, 
    figsize=(7.5,4), 
    dpi=300,  
    gridspec_kw={"width_ratios" : [day_ratio, 1]}, 
    sharex='col', 
    sharey='row'
)

# Plot Polarstereogrpahic X
ax[0][0].plot(
    df[day_7].timestamp, df[day_7].basestation_psx, '.', color=ucl_blue,
    markersize=MARKER_SIZE
)
ax[0][0].plot(
    df[day_7].timestamp, df[day_7].rover_psx, '.', color=ucl_red,
    markersize=MARKER_SIZE
)
ax[0][0].set_ylabel('PSX (m)')
highlight_active_areas(ax[0][0], ACTIVE_AREAS)

ax[0][1].plot(
    df[day_8].timestamp, df[day_8].basestation_psx, '.', color=ucl_blue,
    markersize=MARKER_SIZE
)
ax[0][1].plot(
    df[day_8].timestamp, df[day_8].rover_psx, '.', color=ucl_red,
    markersize=MARKER_SIZE
)
highlight_active_areas(ax[0][1], ACTIVE_AREAS)

# Plot Polarstereogrpahic X
ax[1][0].plot(
    df[day_7].timestamp, df[day_7].basestation_psy, '.', color=ucl_blue,
    markersize=MARKER_SIZE
)
ax[1][0].plot(
    df[day_7].timestamp, df[day_7].rover_psy, '.', color=ucl_red,
    markersize=MARKER_SIZE
)
ax[1][0].set_ylabel('PSY (m)')
highlight_active_areas(ax[1][0], ACTIVE_AREAS)

ax[1][1].plot(
    df[day_8].timestamp, df[day_8].basestation_psy, '.', color=ucl_blue,
    markersize=MARKER_SIZE
)
ax[1][1].plot(
    df[day_8].timestamp, df[day_8].rover_psy, '.', color=ucl_red,
    markersize=MARKER_SIZE
)
highlight_active_areas(ax[1][1], ACTIVE_AREAS)

# Plot Polarstereogrpahic X
ax[2][0].plot(
    df[day_7].timestamp, df[day_7].basestation_el, '.', color=ucl_blue,
    markersize=MARKER_SIZE
)
ax[2][0].plot(
    df[day_7].timestamp, df[day_7].rover_el, '.', color=ucl_red,
    markersize=MARKER_SIZE
)
ax[2][0].set_ylabel('El. (m)')
highlight_active_areas(ax[2][0], ACTIVE_AREAS)

ax[2][1].plot(
    df[day_8].timestamp, df[day_8].basestation_el, '.', color=ucl_blue,
    markersize=MARKER_SIZE, label="Base Station"
)
ax[2][1].plot(
    df[day_8].timestamp, df[day_8].rover_el, '.', color=ucl_red,
    markersize=MARKER_SIZE, label="Rover"
)
ax[2][1].legend(markerscale=4)
highlight_active_areas(ax[2][1], ACTIVE_AREAS)

ax[2][1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax[2][1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
ax[2][1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
ax[2][1].set_xlabel("Time of Day")
ax[2][1].set_xlim([day_8_min, day_8_max])

ax[2][0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax[2][0].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
ax[2][0].xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
ax[2][0].set_xlabel("Time of Day")
ax[2][0].set_xlim([day_7_min, day_7_max])

ax[0][0].set_title('2022-01-07')
ax[0][1].set_title('2022-01-08')

for a in ax:
    try:
        a.label_outer()
    except:
        pass

fig.tight_layout()
fig.savefig(FIG_PATH / "StartStopRTKPositions.png")


# Create figure
fig, ax = plt.subplots(3,2, 
    figsize=(7.5,4), 
    dpi=300,  
    gridspec_kw={"width_ratios" : [day_ratio, 1]}, 
    sharex='col', 
    sharey='row'
)

# Plot Polarstereogrpahic X
ax[0][0].plot(
    df[day_7].timestamp, df[day_7].rover_x, '.', color=ucl_orange,
    markersize=MARKER_SIZE
)
ax[0][0].set_ylabel('Rover X (m)')
highlight_active_areas(ax[0][0], ACTIVE_AREAS)

ax[0][1].plot(
    df[day_8].timestamp, df[day_8].rover_x, '.', color=ucl_orange,
    markersize=MARKER_SIZE
)
highlight_active_areas(ax[0][1], ACTIVE_AREAS)

# Plot Polarstereogrpahic X
ax[1][0].plot(
    df[day_7].timestamp, df[day_7].rover_y, '.', color=ucl_orange,
    markersize=MARKER_SIZE
)
ax[1][0].set_ylabel('Rover Y (m)')
highlight_active_areas(ax[1][0], ACTIVE_AREAS)

ax[1][1].plot(
    df[day_8].timestamp, df[day_8].rover_y, '.', color=ucl_orange,
    markersize=MARKER_SIZE
)
highlight_active_areas(ax[1][1], ACTIVE_AREAS)

# Plot Polarstereogrpahic X
ax[2][0].plot(
    df[day_7].timestamp, df[day_7].rover_z, '.', color=ucl_orange,
    markersize=MARKER_SIZE
)
ax[2][0].set_ylabel('Rover Z (m)')
highlight_active_areas(ax[2][0], ACTIVE_AREAS)

ax[2][1].plot(
    df[day_8].timestamp, df[day_8].rover_z, '.', color=ucl_orange,
    markersize=MARKER_SIZE
)
highlight_active_areas(ax[2][1], ACTIVE_AREAS)

ax[2][1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax[2][1].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
ax[2][1].xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
ax[2][1].set_xlabel("Time of Day")
ax[2][1].set_xlim([day_8_min, day_8_max])

ax[2][0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax[2][0].xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
ax[2][0].xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
ax[2][0].set_xlabel("Time of Day")
ax[2][0].set_xlim([day_7_min, day_7_max])

ax[0][0].set_title('2022-01-07')
ax[0][1].set_title('2022-01-08')

for a in ax:
    try:
        a.label_outer()
    except:
        pass

fig.tight_layout()
fig.savefig(FIG_PATH / "StartStopRoverPositions.png")