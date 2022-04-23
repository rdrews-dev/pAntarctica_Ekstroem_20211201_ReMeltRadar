# We get annoying warnings about backends that are safe to ignore
import warnings
warnings.filterwarnings("ignore")
# Standard Python Libraries
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# Impdar’s loading function
from impdar.lib import load
from impdar.lib.plot import plot_traces, plot_radargram, plot_spectrogram

#matplotlib.use('tkagg')

# Load the Pulse EKKO data. Uznip the GPZ file before.
# This works for data from shielded anteann, 10, 14, 17
#dat = load.load("pe",["Lauswiesen_Timelapse/Lineset/line2.dt1"])[0]
#dat = load.load("pe",["3GL50MHz3/Lineset/line4.dt1"])[0]

## 1
## 6: poor bed bed maybe at t 300 and 13.5
## 7: bed jagged between 12.2 and 13.4 rough base
## 8: bed jagged between 11.5 and 12.75 rough base
## 9: bed jagged between 11.5 and 12.5 rough base
## 10: bed jagged between 11.5 and 12.5 rough base
## 11: Bulge and then flat.!!!! + 20
## 12: c ApRES position
## 13: c ApRES position

#------------------------------------------------------
# Define locations of external files and folders
#------------------------------------------------------
# Core Directory
CoreDirectory='/Users/rdrews/esd/data/rdrews/data_large/Data_Antarctica/2021_RemeltRadar/Raw/Raw_PE/'
LinesetDirectory='20220104_GL_FL_50_MHz_along_567/20220104_GL_FL_50_MHz_along_5/Lineset/'
LinesetDirectory='20220106_FG_EIS_12/20220106_FG_EIS_1/Lineset/'
print(f"{CoreDirectory}{LinesetDirectory}/line3.dt1")
dat = load.load("pe",[f"{CoreDirectory}{LinesetDirectory}/line3.dt1"])[0]


#dat2 = load.load("pe",["../../../tmp/pulseEKKO/1GLFL50MHZ/Lineset/line10.dt1"])[0]
#dat.crop(0.,dimension="pretrig",rezero=True)
from impdar.lib.gpslib import interp
#dat.vertical_band_pass(100,500)
#dat.lowpass(100)
dat.vertical_band_pass(10,75)
dat.agc(100,100)
[im, xd, yd, x_range, clims] = plot_radargram(dat,x_range=(0, -1), y_range=(0, -1),return_plotinfo="True")
plt.show()
print(clims)
