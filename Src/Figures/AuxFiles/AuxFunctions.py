#------------------------------------------------------
#Script reading the GP2 files from PulseEkko
#   RDrews (2022-01-13)
#------------------------------------------------------
import pynmea2
import csv


def dm(x):
    degrees = int(x) // 100
    minutes = x - 100*degrees
    return degrees, minutes

def decimal_degrees(degrees, minutes):
    return degrees + minutes/60 

def GetLatLonFromGP2(PathToGP2File):
     #Return latitude and longitude in decimal degrees from PulseEkko's GP2 files.
    trace = []
    lgpgga = []
    it = -1
    lat=[]
    lon=[]
    with open(PathToGP2File, newline='') as csvfile:
        lread = csv.reader(csvfile, delimiter=',')
        for row in lread:
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