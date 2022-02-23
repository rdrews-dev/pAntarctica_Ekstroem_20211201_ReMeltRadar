import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pathlib
import pyapres 
import re
import SQL.catalogue_data as apresdb

ucl_blue = (0, 151/255, 169/255)
ucl_orange = (234/255, 118/255, 0)
ucl_green = (181/255, 189/255, 0)
ucl_red = (213/255, 0, 50/255)

line_colors = (ucl_blue, ucl_orange, ucl_green, ucl_red)

ROOT_PATH = pathlib.Path("/mnt/storage/JH_PhD/ReMeltRadar")
DB_PATH = ROOT_PATH / pathlib.Path("Doc/ApRES/Rover/HF/Testing.db")

FIG_PATH = ROOT_PATH / "Doc/ApRES/Rover/HF/Testing/figures"

db_man = apresdb.ApRESDatabase(DB_PATH)
cursor = db_man.get_cursor()

cursor.execute("""
SELECT 
    `measurements`.`measurement_id`,
    `measurements`.`filename`,
    `measurements`.`path`,
    `measurements`.`location`,
    `measurements`.`comments`,
    `measurements`.`base_visible`,
    `measurements`.`base_range_min`,
    `measurements`.`base_range_max`,
    `measurements`.`timestamp`,
    `apres_metadata`.`af_gain`,
    `apres_metadata`.`rf_attenuator`,
    `apres_metadata`.`period`,
    `apres_metadata`.`f_lower`,
    `apres_metadata`.`f_upper`,
    `apres_metadata`.`n_attenuators`,
    `apres_metadata`.`n_chirps`,
    `apres_metadata`.`n_subbursts`,
    `apres_metadata`.`power_code`,
    `apres_metadata`.`battery_voltage`,
    `apres_metadata`.`temperature_1`,
    `apres_metadata`.`temperature_2`
FROM `measurements`
INNER JOIN `apres_metadata`
ON `measurements`.`measurement_id`=`apres_metadata`.`measurement_id`
WHERE `measurements`.`valid` = 1
ORDER BY `measurements`.`timestamp`
""")

with open(f"{ROOT_PATH}/Doc/ApRES/Rover/HF/Testing/file_doc.tex", "w+") as fh:
        
    for result in cursor.fetchall():


        print(f"Print loading {result[1]}...")
        burst = pyapres.read(ROOT_PATH / result[2])
        burst.load()

        fig_name = f"{FIG_PATH}/{result[1]}.png"
        
        if False: #pathlib.Path(fig_name).exists():
            print(f"Skipping creating figure for {fig_name}")
        else:

            n_att = burst.nAttenuators
            chirp_avg = np.zeros((n_att, np.size(burst.chirp_voltage,1)))
            for k in range(n_att):
                for m in range(burst.NSubBursts):
                    print(k + m*n_att)
                    chirp_avg[k,:] = chirp_avg[k,:] + burst.chirp_voltage[k + m*n_att,:]
                chirp_avg[k,:] = chirp_avg[k,:] / burst.NSubBursts
            print("-" * 80)

            fig, axs = plt.subplots(2)

            for idx in range(np.size(chirp_avg,0)):
                axs[0].plot(burst.chirp_time(), chirp_avg[idx,:], label=f"Attn {idx+1}", color=line_colors[idx])
            axs[0].set_xlabel("Time (s)")
            axs[0].set_ylabel("Voltage (V)")
            axs[0].set_ylim([0, 2.5])
            axs[0].set_xlim([0, result[11]])
            axs[0].set_title(f"Deramped Signal") #T: {result[11]}, F: {result[12]/1e6}-{result[13]/1e6} MHz, RF: {result[9]}, AF:{result[10]}")
            axs[0].legend(loc="lower right")

            # Get range profile
            power = pyapres.RangeProfile.calculate_from_chirp([], chirp_avg, burst.fmcw_parameters, pad_factor=2)
            range_vec = 3e8 / (4 * (result[13] - result[12]) * np.sqrt(3.18)) * np.arange(0,np.size(power,1))
            
            # Check whether base is visible
            base_visible = result[5]
            if base_visible:
                base_range = result[6:8]
                axs[1].add_patch(
                    mpatches.Rectangle(
                        # left bottom
                        (base_range[0], -120),
                        # width height
                        base_range[1] - base_range[0], 120,
                        facecolor="gray",
                        alpha=0.25
                    )
                )

            for idx in range(np.size(chirp_avg,0)):
                axs[1].plot(range_vec, 20*np.log10(np.abs(power[idx,:])), label=f"Attn {idx+1}", color=line_colors[idx])
            axs[1].set_ylabel("Power (dBV)")
            axs[1].set_xlabel("Range (m, e_r=3.18)")
            axs[1].set_title("Range-Power")
            axs[1].set_xlim([0, 1500])
            axs[1].set_ylim([-120, 0])

            fig.subplots_adjust(hspace=0.75)
            fig.set_size_inches(8,4)
            fig.savefig(fig_name)

        fh.write(re.sub(
            r"([\_\#\$])",
            r"\\\g<1>",
            ("\\apresdoc{{{filename:s}}}" + \
            "{{{location:s}}}" + \
            "{{{comments:s}}}" + \
            "{{{timestamp:s}}}" + \
            "{{{af_gain:s}}}" + \
            "{{{rf_attenuator:s}}}" + \
            "{{{period:.3f}}}" + \
            "{{{f_lower:.3f}}}" + \
            "{{{f_upper:.3f}}}" + \
            "{{{n_attenuators:d}}}" + \
            "{{{n_chirps:d}}}" + \
            "{{{n_subbursts:d}}}" + \
            "{{{power_code:d}}}" + \
            "{{{battery_voltage:.3f}}}\r\n" ).format(
                filename=result[1],
                location=result[3],
                comments=result[4],
                timestamp=result[8],
                af_gain=result[9],
                rf_attenuator=result[10],
                period=result[11],
                f_lower=result[12],
                f_upper=result[13],
                n_attenuators=result[14],
                n_chirps=result[15],
                n_subbursts=result[16],
                power_code=result[17],
                battery_voltage=result[18]
            )))

