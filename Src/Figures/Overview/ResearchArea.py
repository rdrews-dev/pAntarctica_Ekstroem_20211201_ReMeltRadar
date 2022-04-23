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

def PlotFieldData(lregion,lprojection):
    #------------------------------------------------------
    # Define locations of external files and folders
    #------------------------------------------------------
    # Core Directory
    CoreDirectory='/Users/rdrews/esd/data/rdrews/data_large/Data_Antarctica/2021_RemeltRadar/'
    # Background grid
    BackgroundImage = "/Users/rdrews/Desktop/ReMeltRadar/QGis/ClippedBackgroundRasters/RoiRadarsat_EPSG4326.tif"
    # Grounding line used: Simplified makes it faster.
    GLFile = "/Users/rdrews/Desktop/QGis/Quantarctica3/Glaciology/ASAID/ASAID_GroundingLine_Continent.shp"
    #GLFile = "/Users/rdrews/Desktop/QGis/Quantarctica3/Glaciology/ASAID/ASAID_GroundingLine_Simplified.shp"
    # Location of PulseEkko RAW Folders
    PERawFolder=f'{CoreDirectory}Raw/Raw_PE/'
    # Location of intermediate folder to speed up the reading of the lon-lat coordinates
    PEProcFolder=f'{CoreDirectory}Proc/PulseEkko/LonLatFiles/'
    # SPM Locations
    SPMLocations='/Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/ScienceProfiles/GpxExport/OutputBasecamp/AllSPMPoints.GPX'
  
    #------------------------------------------------------
    try:
        fig.grdimage(
            grid=BackgroundImage,
            cmap="haxby",
            projection=lprojection,
            frame=False,
            region=lregion
        )
    except:
        print(f"Ups. Something went wrong when inserting the background image. Most likely {BackgroundImage} does not exist.")
    #------------------------------------------------------
    # Plot grounding line shp file
    #------------------------------------------------------
    try:
        gdf = gpd.read_file(filename=GLFile)
        gdf = gdf.to_crs(epsg=4326)
        fig.plot(data=gdf,projection=lprojection,region=lregion,label="GroundingLine")
    except:
        print(f"Ups. Something went wrong when inserting the grounding line. Most likely {GLFile} does not exist.")

    #------------------------------------------------------
    # Plot locations of PulseEkko radar profiles 
    #------------------------------------------------------
    ## 250 MHz measured in parallel to the traverse from NM towards the grounding line
    lfileid = '20220101_Kotta1_250MHz_central_flow/'
    lcolor = 'blue'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c", pen=lcolor,projection=lprojection,region=lregion)
    lfileid = '20220101_Kotta2_250MHz_central_flow/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c", color=lcolor, pen=lcolor,label="250MHz+S0.09c",projection=lprojection,region=lregion)

    ## 50 MHz mapping of the grounding zone region
    lcolor = 'steelblue'
    lfileid = '20220102_GL_FL_50_MHz_along_1/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c", pen=lcolor,projection=lprojection,region=lregion)
    lfileid = '20220103_GL_FL_50_MHz_along_234/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c",  pen=lcolor,projection=lprojection,region=lregion)
    lfileid = '20220104_GL_FL_50_MHz_along_567/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c",  pen=lcolor,projection=lprojection,region=lregion)
    lfileid = '20220105_GL_FL_50_MHz_across_12345/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c",  pen=lcolor,projection=lprojection,region=lregion)
    ## not quite sure what this one was about. It doubles a line.
    lfileid = '20220108_50MHz_aroundSPM23/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c", color="white", pen=lcolor,projection=lprojection,region=lregion)

    ## 50 MHz fine grid
    lcolor = 'cadetblue'
    lfileid = '20220106_FG_EIS_12/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c",  pen=lcolor,projection=lprojection,region=lregion)
    lfileid = '20220108_FG_across_EIS/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c",  pen=lcolor,projection=lprojection,region=lregion)


    ## 50 MHz grounding zone back to NM
    lfileid = '20220110_50MHz_along_flow_long123/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c", pen=lcolor,projection=lprojection,region=lregion)
    lfileid = '20220112_50MHz_along_flow_long45/'
    (llat,llon) = GetLonLatFromGP2FilesInFolder(f'{PERawFolder}{lfileid}',f'{PEProcFolder}{lfileid[:-1]}.pickle')
    fig.plot(x=llon[::200], y=llat[::200], style="c0.025c", color=lcolor, pen=lcolor,label="50MHz+S0.09c",projection=lprojection,region=lregion)

    #------------------------------------------------------
    # Plot locations of SPM measurements.
    # At the moment those are planned, not the measured locs.
    #------------------------------------------------------
    try:
        gdf = gpd.read_file(filename=SPMLocations)
        fig.plot(data=gdf,style="c0.09c", color="purple", pen='purple',label="SPM",projection=lprojection,region=lregion)
    except:
        print(f"Ups. Something went wrong when inserting the SPM locations. Most likely {SPMLocations} does not exist.")

    #------------------------------------------------------
    # Plot point locations
    #------------------------------------------------------
    #Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/cApRES/cApRES.txt
    fig.plot(x=-8.432945419999999, y=-71.616032783333338, style="i0.2c", color="red",pen="red",label="cApRES",projection=lprojection,region=lregion)
    #/Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/BaseStation/BaseStation.txt
    fig.plot(x=-8.41588, y=-71.61375, style="i0.2c",color="blue", pen="blue",label="BaseStation",projection=lprojection,region=lregion)
    #/Users/rdrews/Desktop/QGis/Quantarctica3/MyDataFolder/FieldSeason_Antr21_22/Coordinates/CAMP/
    fig.plot(x=-8.593387484254789, y=-71.724807328156288,style="i0.2c",color="green", pen="green",label="Camp",projection=lprojection,region=lregion)

    fig.legend(projection=lprojection,region=lregion,position="JBR+jBR+o0.2c", box="+gwhite+p1p",timestamp=False)

   


if __name__ == "__main__":
    #------------------------------------------------------
    # General settings defining the plot
    #------------------------------------------------------
    # Projection
    UsedProjection = "M10c" ## set LJ = "-Js163.5/-90/-71/1:150000" (?)
    # Region of interest for Ekström Ice Shelf in lon lat
    UsedRegion = [-10, -7, -71.8,-70.5]
    # Region zoomed into grounding line
    UsedZoom = [-8.8, -8.2, -71.8,-71.55]
    # Location of Output Image for Tex File
    OutputImage=f'../../../Doc/Tex/Figures/Overview.png'
    #------------------------------------------------------

    
    fig = pygmt.Figure()
    with fig.subplot(
        nrows=1,
        ncols=2,
        figsize=("18c", "6c"),
        autolabel=False,
        frame=["af", "WSne"],
        margins=["2.5c", "0.0c"],
    #    title="My Subplot Heading",
    ):
        
        PlotFieldData(UsedRegion,UsedProjection)
        fig.basemap(region=UsedRegion, projection=UsedProjection, panel=[0, 0],timestamp=True,map_scale="jBL+w15k+o0.5c/0.5c+f+lkm")
        fig.basemap(region=UsedZoom, projection=UsedProjection, panel=[0, 1])
        PlotFieldData(UsedZoom,UsedProjection)
        
    fig.savefig(OutputImage, transparent=False, crop=True, anti_alias=True, show=False)
    #fig.show()