# process_cable_lengths.py
#
#   Auth: J.D. Hawkins
#   Date: 2022-03-30
#
#   Process cable lengths used for the cApRES setup to verify timing
#   differences for post-processing.

import matplotlib.pyplot as plt
import numpy as np
import pathlib
import pandas as pd
import skrf as rf

# Load antenna 1 and 2 data
DATA_ROOT = pathlib.Path("Raw/VNA/CableLength")
PROC_ROOT = pathlib.Path("Proc/VNA/CableLength")
CSV_OUT = PROC_ROOT / "OWTT.csv"
PNG_OUT = PROC_ROOT / "OWTT.png"

cables = {
    "Blue/Earth" : DATA_ROOT / "blue-earth-s21-14h18.s2p",
    "Double Earth" : DATA_ROOT / "double-earth-s21-14h23.s2p",
    "Yellow" : DATA_ROOT / "yellow-cable-s21-14h13.s2p"
}

ucl_blue = (0, 151/255, 169/255)
ucl_orange = (234/255, 118/255, 0)
ucl_green = (181/255, 189/255, 0)
ucl_red = (213/255, 0, 50/255)

line_colors = (ucl_blue, ucl_green, ucl_orange)

def owtt_power_vectors_from_s21(network_obj):

    # Extract frequency and S21
    freq = network_obj.f
    s21 = network_obj.s[:,1,0]

    # Determine bandwidth from frequency sweep
    bandwidth = np.max(freq) - np.min(freq)
    time_resolution = 1 / (bandwidth)

    time_vector = np.linspace(
        0, time_resolution * (len(freq) - 1), len(freq)
    )

    power_vector = np.fft.ifft(s21)

    return [time_vector, power_vector]

def calc_fine_owtt(owtt_vector, complex_power, network):

    fc = np.mean(network.f)
    i = np.argmax(complex_power)
    owtt_fine = np.angle(complex_power[i]) / (2*np.pi*fc)

    return owtt_vector[i] - owtt_fine, i



# Creaete SParameter/Network Objects
networks = dict()
for cable in cables:
    networks[cable] = rf.Network(cables[cable])

fig, ax = plt.subplots(2, 1, figsize=(7.5,4), dpi=300)

# Count networks
ntwk_id = 0
cable_owtt = []

for cable in networks:
    # Get corresponding network
    network = networks[cable]

    # Plot S21
    ax[0].plot(network.f/1e6, 20*np.log10(np.abs(network.s[:,1,0])), color=line_colors[ntwk_id], label=cable)
    ax[0].set_xlim([np.min(network.f/1e6), np.max(network.f/1e6)])
    
    [owtt, pwr] = owtt_power_vectors_from_s21(network)
    fine_owtt, i = calc_fine_owtt(owtt, pwr, network)
    # Plot one-way travel time/power
    ax[1].plot(owtt/1e-9, 20*np.log10(np.abs(pwr)), color=line_colors[ntwk_id], label=cable)
    ax[1].plot(fine_owtt/1e-9, 20*np.log10(np.abs(pwr[i])), 'x', color=line_colors[ntwk_id])

    cable_owtt.append(fine_owtt)

    print(f"Cable {cable} OWTT: {fine_owtt/1e-9:7.3f} ns")
    ntwk_id += 1

# Configure axes
ax[0].set_xlabel('Frequency (MHz)')
ax[0].set_ylabel('S_21 (dB)')
ax[0].legend()
ax[0].set_ylim([-6, 0])

ax[1].set_xlabel('One-Way Travel Time (ns)')
ax[1].set_ylabel('S_21 (dB)')
ax[1].set_xlim([0,100])

# Create dataframe and save
df = pd.DataFrame(data={"cable_id": cables.keys() , "owtt":cable_owtt})
df.to_csv(CSV_OUT, index=False)

# Save figure
fig.savefig(PNG_OUT)
