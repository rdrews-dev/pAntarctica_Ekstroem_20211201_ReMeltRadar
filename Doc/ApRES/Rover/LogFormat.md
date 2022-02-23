# Notes on Logging format for SubZero Rover
All lines begin the a timestamp, user and logging level in the following format:

```
YYYY-mm-dd HH:MM:SS,SSS - [user] - [log level] - [logging message]
```

where `lineno` indicates the line number in the logfile, `SSS` is the first 3 significant figures of the milliseconds at the logging timestamp.  The `log level` can be one of a number of values

| Level       | Numeric value   |
|-------------|-----------------|
| CRITICAL    | 50              |
| ERROR       | 40              |
| WARNING     | 30              |
| INFO        | 20              |
| DEBUG       | 10              |
| NOTSET      | 0               |

More info can be found in the `logging` module documentation [here](https://docs.python.org/3/library/logging.html).

## ApRES Bursts in RTK/SAR Mode
An example of the sections of the rover log that relate to ApRES measurements is given below:

```
2022-01-08 13:32:28,448 - root - INFO - ApRES: Burst done
2022-01-08 13:32:28,449 - root - INFO - >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
2022-01-08 13:32:28,450 - root - INFO - ApRES: BURSTINFO@Point148
2022-01-08 13:32:28,452 - root - INFO - ApRES: PointName@148_SubZero__133219.50_T1HR1H.dat
2022-01-08 13:32:28,452 - root - INFO - ApRES: PointInfo@148,133219.50,[-71.6137581, -8.4172455],99.75,4
2022-01-08 13:32:28,453 - root - INFO - <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
```

Breaking this down there are three key lines in the log file:

- `ApRES: BURSTINFO`: measurement point number, resets on restart of rover PC.

- `ApRES: PointName`: name of file at measurement point 

- `ApRES: PointInfo`: telemetric or positioning information corresponding to measurement point.

### `BURSTINFO`
The format of the `BURSTINFO` message is:

```
BURSTINFO@Point name
```

### `PointName`
The format of the `PointName` message is:
```
PointName@filename
```

where filename corresponds to the name of the saved `*.dat` file.

### `PointInfo`
The format of the `PointInfo` message is:
```
PointInfo@Burst number,[Latitude,Longitude],Altitude,GPS Quality
```

where
- **Burst number** is an integer identifier, which resets whenever the rover is restarted.

- **Latitude** is the WGS84 latitude in decimal format.

- **Longitude** is the WGS84 longitude in decimal format.

- **Altitude** is the WGS84 altitude in decimal format.

- **GPS Quality** is an integer indicating the type of GPS connection used (4 = RTK GPS).