import warnings
warnings.filterwarnings("ignore")
# Standard Python Libraries
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import sys
#sys.path.append('./ImpDAR/')
sys.path.append('./impdar/')

from lib import load

CoreDirectory='/esd/esd01/data/rdrews/data_large/Data_Antarctica/2021_RemeltRadar/Raw/Raw_PE/'
LinesetDirectory='20220104_GL_FL_50_MHz_along_567/20220104_GL_FL_50_MHz_along_5/Lineset/'
print(f"{CoreDirectory}{LinesetDirectory}/line3.dt1")
dat = load.load("pe",[f"{CoreDirectory}{LinesetDirectory}/line3.dt1"])[0]




print('Test.')
