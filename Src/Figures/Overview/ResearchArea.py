#------------------------------------------------------
#Script locating profile and measurement locations
#   RDrews (2022-01-13)
#------------------------------------------------------
#Requires: pygmt, geopandas, pynmea2
#   conda create --name pygmt --channel conda-forge pygmt
#   conda activate pygmt
#   conda install --channel conda-forge geopandas
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
import geopandas as gpd
import sys
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
os.chdir(scriptPath)
sys.path.insert(1, '../AuxFiles/')
from AuxFunctions import *

#------------------------------------------------------
# Define locations of external files and folders
#------------------------------------------------------
# Background grid
BackgroundImage = "/Users/rdrews/Desktop/ReMeltRadar/QGis/ClippedBackgroundRasters/RoiRadarsat_EPSG4326.tif"
# Grounding line used
GLFile = "/Users/rdrews/Desktop/QGis/Quantarctica3/Glaciology/ASAID/ASAID_GroundingLine_Simplified.shp"
#------------------------------------------------------

#------------------------------------------------------
# General settings defining the plot
#------------------------------------------------------
# Projection
lprojection = "M10c" ## set LJ = "-Js163.5/-90/-71/1:150000" (?)
# Region of interest for Ekström Ice Shelf in lon lat
lregion = [-10, -7, -71.8,-70.5]
#------------------------------------------------------

#------------------------------------------------------
# Baseline Figure
#------------------------------------------------------
fig = pygmt.Figure()
fig.basemap(region=lregion, 
            projection=lprojection, 
            frame=["af", '+t"ReMeltRadar 21/22"'])

try:
    fig.grdimage(
        grid=BackgroundImage,
        cmap="haxby",
        projection=lprojection,
        frame=True,
    )
except:
    print(f"Ups. Something went wrong when inserting the background image. Most likely {BackgroundImage} does not exist.")
#------------------------------------------------------
# Plot grounding line shp file
#------------------------------------------------------
try:
    gdf = gpd.read_file(filename=GLFile)
    gdf = gdf.to_crs(epsg=4326)
    fig.plot(data=gdf)
except:
    print(f"Ups. Something went wrong when inserting the grounding line. Most likely {GLFile} does not exist.")

#------------------------------------------------------
# Plot locations of PulseEkko radar profiles 
#------------------------------------------------------
lfile = '/Users/rdrews/Desktop/tmp/pulseEKKO/line4.gp2'
(lon,lat) = GetLatLonFromGP2(lfile)
fig.plot(x=lon[::100], y=lat[::100], style="c0.05c", color="white", pen="black",label="PulseEkko")

#------------------------------------------------------
# Plot point locations
#------------------------------------------------------
#Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/cApRES/cApRES.txt
fig.plot(x=-8.432945419999999, y=-71.616032783333338, style="c0.1t", color="white", pen="red",label="cApRES")
#/Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/BaseStation/BaseStation.txt
fig.plot(x=-8.41588, y=-71.61375, style="c0.1t", color="white", pen="blue",label="BaseStation")
#/Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/CAMP/
fig.plot(x=-8.593387484254789, y=-71.724807328156288,style="c0.1t", color="white", pen="green",label="Camp" )



#------------------------------------------------------
# Adding a legend for all labelled lines
#------------------------------------------------------
fig.legend()

fig.show()