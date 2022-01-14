#------------------------------------------------------
#Script locating profile and measurement locations
#   RDrews (2022-01-13)
#------------------------------------------------------
#Requires: pygmt
#   conda create --name pygmt --channel conda-forge pygmt
#   conda activate pygmt
#   To activate in in Visual Studio Code: cmd+shift+P and choose pygmt environment
#   pip install pynmea2
#Region of Interest for Ekström Ice Shelf:
# -70.5 -71.8 -10 - 7 
#Background Layers:
#   gdalwarp -t_srs EPSG:4326 -s_srs EPSG:3031 -te -10 -71.8 -7 -70.5 <PathToRadarsatMosaic>/RADARSAT_Mosaic.jp2 <PathToGit>/QGis/ClippedBackgroundRasters/RoiRadarsat_EPSG4326.tif
#   RoiRadarsat_EPSG4326.tif 
#------------------------------------------------------



import pygmt 
import os
import pynmea2
import numpy as np
import sys
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
os.chdir(scriptPath)
sys.path.insert(1, '../AuxFiles/')
from AuxFunctions import *
#------------------------------------------------------
# General settings defining the plot
#------------------------------------------------------
# Projection
lprojection = "M10c" ## set LJ = "-Js163.5/-90/-71/1:150000" (?)
# Background grid
bgrid = "/Users/rdrews/Desktop/ReMeltRadar/QGis/ClippedBackgroundRasters/RoiRadarsat_EPSG4326.tif"
# Grounding line used
lgl = "/Users/rdrews/Desktop/QGis/Quantarctica3/Glaciology/ASAID/ASAID_GroundingLine_Simplified.shp"
# Region of interest for Ekström Ice Shelf in lon lat
lregion = [-10, -7, -71.8,-70.5]
#------------------------------------------------------


#------------------------------------------------------
# Baseline Figure
#------------------------------------------------------
fig = pygmt.Figure()
fig.basemap(region=lregion, 
            projection=lprojection, 
            frame=["a", '+t"ReMeltRadar 21/22"'])
#fig.basemap(region=lregion, projection=lprojection, frame='a')
fig.coast(region=lregion, shorelines=True)
fig.grdimage(
    grid=bgrid,
    cmap="haxby",
    projection=lprojection,
    frame=True,
)

#------------------------------------------------------
# Plot locations of PulseEkko radar profiles 
#------------------------------------------------------
lfile = '/Users/rdrews/Desktop/tmp/pulseEKKO/line4.gp2'
(lon,lat) = GetLatLonFromGP2(lfile)

fig.plot(x=lon[::100], y=lat[::100], style="c0.05c", color="white", pen="black")
fig.show()