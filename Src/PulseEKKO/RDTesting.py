import warnings
warnings.filterwarnings("ignore")
# Standard Python Libraries
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import sys
import os
from os.path import exists
from natsort import natsorted
#sys.path.append('./ImpDAR/')
sys.path.append('./impdar/')

from lib import load
from lib.plot import plot_radargram, plot_traces
from lib.process import concat
##########################################################################
# Tipps und Tricks
# 1/ Reading Files the date in the *hd must be in mm/dd/yyyy spontaneously this is save otherwise.
#       find . -type f -name "*.hd" -exec sed -i.bak 's/2022-Jan-02/01\/02\/2022/g' {} +
# changes this manually.
# 2/ If only a few traces are in line, then horizontal stacking fails. Remove those lines.
##########################################################################

def FindFiletypeInDirectory(Directory, Filetype):
    lpath=[]
    for root, dirs, files in os.walk(Directory):
        for file in files:
            if file.endswith(Filetype):
                lpath.append(os.path.join(root, file))
    print(f'Found {len(lpath)} files of type {Filetype}.')
    return natsorted(lpath)

def StandardProc(PathToDt1):
    HorizontalSpacing=10.0
    AntennaSeperation=2.0
    PreTrigger=1190
    print(f'Loading {PathToDt1}')
    ldat = load.load("pe",[PathToDt1])[0]
    ldat.crop(PreTrigger,dimension='snum', top_or_bottom='top')
    ldat.constant_space(HorizontalSpacing)
    ldat.vertical_band_pass(20,75)
    ldat.agc(100,100)
    ldat.nmo(AntennaSeperation)
    return ldat

def ConnectLineSets(LinesetDirectory):
    lpath = FindFiletypeInDirectory(LinesetDirectory,'.dt1')
    print(lpath)
    if len(lpath)>1:
        lldat = StandardProc(lpath[0])
        lpath.pop(0)
    for dt1 in lpath:
         print(dt1)
         llldat = StandardProc(dt1)
         lldat = concat([lldat, llldat])[0]
    return lldat





#CoreDirectory='/Users/rdrews/esd/data/rdrews/data_large/Data_Antarctica/2021_RemeltRadar/Raw/Raw_PE/'

CoreDirectory='/Users/rdrews/Desktop/tmp/Raw_PE/'

# LinesetDirectory='20220102_GL_FL_50_MHz_along_1/Lineset'
# datm = ConnectLineSets(f'{CoreDirectory}{LinesetDirectory}/')

if exists('../../Proc/PulseEKKO/SampleProfile.mat'):
    print('Loading file from previous step.')
    datm = load.load('mat','../../Proc/PulseEKKO/SampleProfile.mat')[0]
else:
    LinesetDirectory='20220102_GL_FL_50_MHz_along_1/Lineset/'
    Sur0 = ConnectLineSets(f'{CoreDirectory}{LinesetDirectory}/')
    # LinesetDirectory='20220110_50MHz_along_flow_long1/Lineset/'
    # Sur1 = ConnectLineSets(f'{CoreDirectory}{LinesetDirectory}/')
    # LinesetDirectory='20220110_50MHz_along_flow_long2/Lineset/'
    # Sur2 = ConnectLineSets(f'{CoreDirectory}{LinesetDirectory}/')
    # LinesetDirectory='20220110_50MHz_along_flow_long3/Lineset/'
    # Sur3 = ConnectLineSets(f'{CoreDirectory}{LinesetDirectory}/')

    datm = concat([Sur0])[0]
    #datm = concat([Sur0,Sur1, Sur2, Sur3])[0]
    datm.save('../../Proc/PulseEKKO/SampleProfile.mat')


font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 22}
matplotlib.rc('font', **font)

[im, xd, yd, x_range, clims] = plot_radargram(datm,x_range=(0, 3000), y_range=(0, 10000),return_plotinfo="True",xdat='dist',ydat='dual')
# plt.text(0,-5,'A')
# plt.text(54,-5,'A\'')
plt.savefig('../../Doc/Tex/Figures/PulseEkko/PE.png', bbox_inches='tight')
plt.show()



# dir(dat)



# print('Test.')
