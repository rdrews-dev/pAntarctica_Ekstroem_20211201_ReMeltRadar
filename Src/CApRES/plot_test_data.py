import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pathlib
import pyapres 

ucl_blue = (0, 151/255, 169/255)
ucl_orange = (234/255, 118/255, 0)
ucl_green = (181/255, 189/255, 0)
ucl_red = (213/255, 0, 50/255)

line_colors = (ucl_blue, ucl_orange, ucl_green, ucl_red)

DATA_PATH = pathlib.Path("Raw/CApRES/2022-01-10-capres-sd-copy")
FILE_PATH = DATA_PATH / "Survey_2022-01-10_184911_txcor.dat"

FIG_PATH = pathlib.Path("Doc/Tex/Figures/CApRES/test_burst_2022-01-10_184911.png")

labels = ["HH", "HV", "VH", "VV"]

burst = pyapres.read(FILE_PATH)[0]
burst.load()

n_ant = burst.number_of_rx() * burst.number_of_tx()
chirp_avg = np.zeros((n_ant, np.size(burst.chirp_voltage,1)))
for k in range(n_ant):
    for m in range(burst.NSubBursts):
        print(k + m*n_ant)
        chirp_avg[k,:] = chirp_avg[k,:] + burst.chirp_voltage[k + m*n_ant,:]
    chirp_avg[k,:] = chirp_avg[k,:] / burst.NSubBursts
print("-" * 80)

fig, axs = plt.subplots(2)

for idx in range(np.size(chirp_avg,0)):
    axs[0].plot(burst.chirp_time(), chirp_avg[idx,:], label=labels[idx], color=line_colors[idx])
axs[0].set_xlabel("Time (s)")
axs[0].set_ylabel("Voltage (V)")
axs[0].set_ylim([0, 2.5])
axs[0].set_xlim([0, 1])
axs[0].set_title(f"Deramped Signal") #T: {result[11]}, F: {result[12]/1e6}-{result[13]/1e6} MHz, RF: {result[9]}, AF:{result[10]}")

# Get range profile
power = pyapres.RangeProfile.calculate_from_chirp([], chirp_avg, burst.fmcw_parameters, pad_factor=2)
range_vec = 3e8 / (4 * (2e8) * np.sqrt(3.18)) * np.arange(0,np.size(power,1))

# # Check whether base is visible
# base_visible = result[5]
# if base_visible:
#     base_range = result[6:8]
#     axs[1].add_patch(
#         mpatches.Rectangle(
#             # left bottom
#             (base_range[0], -120),
#             # width height
#             base_range[1] - base_range[0], 120,
#             facecolor="gray",
#             alpha=0.25
#         )
#     )

for idx in range(np.size(chirp_avg,0)):
    axs[1].plot(range_vec, 20*np.log10(np.abs(power[idx,:])), label=labels[idx], color=line_colors[idx])
axs[1].set_ylabel("Power (dBV)")
axs[1].set_xlabel("Range (m, e_r=3.18)")
axs[1].set_title("Range-Power")
axs[1].set_xlim([0, 1500])
axs[1].set_ylim([-130, 0])
axs[1].legend(loc="upper right")

fig.subplots_adjust(hspace=0.75)
fig.set_size_inches(7.5,4)
if ~FIG_PATH.parent.is_dir():
    FIG_PATH.parent.mkdir()
fig.savefig(FIG_PATH)