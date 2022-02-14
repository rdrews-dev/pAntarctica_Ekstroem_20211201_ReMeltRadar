#------------------------------------------------------
#Script reading the GP2 files from PulseEkko
#   RDrews (2022-01-13)
#------------------------------------------------------
import pynmea2
import csv
import os
from os.path import exists
import pickle


def dm(x):
    degrees = int(x) // 100
    minutes = x - 100*degrees
    return degrees, minutes

def decimal_degrees(degrees, minutes):
    return degrees + minutes/60 

def skip_last(iterator):
    prev = next(iterator)
    for item in iterator:
        yield prev
        prev = item

def GetLatLonFromGP2(PathToGP2File):
     #Return latitude and longitude in decimal degrees from PulseEkko's GP2 files.
    trace = [];lgpgga = [];it = -1;lat=[];lon=[]
    with open(PathToGP2File, newline='') as csvfile:
        lread = csv.reader(csvfile, delimiter=',')
        for row in skip_last(lread):
            it = it +1
            #Skip header
            if it>5:
                trace.append(row[0])
                lgpgga.append(row[4])
                msg = pynmea2.parse(row[4])
                if msg.lat_dir == 'S':
                    lat.append(-decimal_degrees(*dm(float(msg.lat))))
                else:
                    lat.append(decimal_degrees(*dm(float(msg.lat))))
                if msg.lon_dir == 'W':
                    lon.append(-decimal_degrees(*dm(float(msg.lon))))
                else:
                    lon.append(decimal_degrees(*dm(float(msg.lon))))
    return (lon, lat)

def GetLonLatFromGP2FilesInFolder(folder,picklefile):
    if exists(picklefile):
        print(f'Loading {picklefile} from previous run.')
        with open(picklefile, 'rb') as f:
            glat,  glon = pickle.load(f)
    else:
        matches=[];glat = [];glon = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                if filename.endswith('gp2'):
                    matches.append(os.path.join(root, filename))
        if len(matches)>0: 
            for lfile in matches:
                if os.stat(lfile).st_size > 0:
                    print(f'Reading: {lfile}.')
                    (lon,lat) = GetLatLonFromGP2(lfile)
                    print(f'Found {len(lon)} points.')
                    glat.extend(lat)
                    glon.extend(lon)
                else:
                    print(f'Empty file: {lfile}.')
        else:
            print(f'No GP2 files in: {folder}.')
        with open(picklefile, 'wb') as f:
            print(f'Writing {picklefile} to speed this for the next run.')
            pickle.dump([glat, glon], f)

    return (glat,glon)