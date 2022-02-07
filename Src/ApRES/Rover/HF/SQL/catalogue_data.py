from os import pathsep

import datetime
import os
import pathlib
import pyapres
import sqlite3

DB_ROOT = "./Doc/ApRES/Rover/HF"
DB_NAME = "Testing.db"

SEARCH_PATH = "./Raw/ApRES/Rover/HF/Testing"

class ApRESDatabase:

    def __init__(self, path, create=False):
        
        # Check path argument is correct
        if not isinstance(path, pathlib.Path):
            # case to pathlib.Path
            path = pathlib.Path(path)

        if not path.exists() and not create:
            raise FileNotFoundError(f"{path} not found.  If you want to create an object try with create=True parameter.")

        # Assign path to object
        self.path = path
        self.db_con = None

        # Try and get connection to database
        try:
            self.get_connection(create)
        except UninitializedDatabaseError:
            # if not possible then initialise database
            # if create option has been passed:
                if create:
                    self.init_tables()
        
    def get_connection(self, create=False):
        
        if self.db_con == None:
            
            # Check database path exists
            if self.path == None:
                raise ValueError(f"No path assigned to locate database file")
            
            if not self.path.exists() and not create:
                raise FileNotFoundError(f"{self.path} not found.  If you want to create an object try with create=True parameter.")

            # Connect to database
            self.db_con = sqlite3.connect(self.path)
            # Check if database is valid
            self.validate()

        # Return sqlite3 connection object
        return self.db_con

    def get_cursor(self):
        connection = self.get_connection()
        return connection.cursor()

    def is_valid(self):
        # Try and validate the database, if we get an exception then
        # it's not valid.
        try:
            self.validate()
        except UninitializedDatabaseError:
            return False
        return True

    def validate(self):

        # Get cursor instance
        cursor = self.get_cursor()

        # TODO Probably ought to move this definition to be a class member
        tables = {'measurements', 'data', 'apres_metadata'}
        
        # Iterate over tables and check it exists within the database
        for table in tables:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=(?);",
                (table,)
            )
            if len(cursor.fetchall()) == 0:
                raise UninitializedDatabaseError(self.path)

    # ------------------------------------------------------------------------
    # TABLE INITIALISATION ROUTINES 

    def init_tables(self):
        # Create measurements table
        self.init_table_measurements()
        self.init_table_apres_metadata()
        self.init_table_data()

    def init_table_measurements(self):
        cursor = self.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `measurements` (
                measurement_id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                name TEXT,
                timestamp TEXT UNIQUE NOT NULL
                    CONSTRAINT valid_timestamp CHECK(timestamp IS strftime('%Y-%m-%d %H:%M:%f', timestamp)),
                valid INTEGER NOT NULL DEFAULT 0,
                location TEXT,
                comments TEXT,
                latitude REAL,
                longitude REAL,
                elevation REAL
            );
        ''')
    
    def init_table_apres_metadata(self):
        cursor = self.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `apres_metadata` (
                id INTEGER PRIMARY KEY,
                burst_id INTEGER NOT NULL,
                measurement_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL
                    CONSTRAINT valid_timestamp CHECK(timestamp IS strftime('%Y-%m-%d %H:%M:%f', timestamp)),
                n_attenuators INTEGER NOT NULL 
                    CONSTRAINT valid_n_attenuators CHECK (n_attenuators > 0 AND n_attenuators < 5),
                n_chirps INTEGER NOT NULL 
                    CONSTRAINT valid_n_chirps CHECK (n_chirps > 0),
                n_subbursts INTEGER NOT NULL 
                    CONSTRAINT valid_n_subbursts CHECK (n_subbursts > 0), 
                period REAL NOT NULL 
                    CONSTRAINT valid_period CHECK (period > 0),
                f_lower REAL NOT NULL 
                    CONSTRAINT valid_f_lower CHECK (f_lower > 0),
                f_upper REAL NOT NULL 
                    CONSTRAINT valid_f_upper CHECK (f_upper > 0),
                af_gain TEXT NOT NULL,
                rf_attenuator TEXT NOT NULL,
                f_sampling REAL NOT NULL,
                tx_antenna TEXT NOT NULL,
                rx_antenna TEXT NOT NULL,
                power_code INTEGER,
                battery_voltage REAL,
                temperature_1 REAL,
                temperature_2 REAL,
                rmb_issue TEXT,
                vab_issue TEXT,
                venom_issue TEXT,
                software_issue TEXT,
                UNIQUE (id, burst_id)
            ) 
        ''')

    def init_table_data(self):
        cursor = self.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `data` (
                data_id INTEGER PRIMARY KEY,
                measurement_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                timestamp TEXT ASC NOT NULL
                    CONSTRAINT valid_timestamp CHECK(timestamp IS strftime('%Y-%m-%d %H:%M:%f', timestamp)),
                processing_steps TEXT
            )
        ''')

    # ------------------------------------------------------------------------
    # END OF CLASS 
    # ------------------------------------------------------------------------
    
class ApRESDatabaseManager:
    
    def add_dat_file(self, 
        # Require arguments 
        #   filename and timestamp are derived from file
        db, path,
        # Measurement arguments
        name=None,
        location=None,
        comments=None,
        # Positional info 
        latitude=None, longitude=None, elevation=None,
    ):

        # Steps to add data file to database
        #   1. verify file exists and path is valid
        #   2. read file to check it is an ApRES *.dat file
        #       - YES then proceed to step 3.
        #       - NO then error
        #   3. check number of bursts within file
        #   4. begin transaction
        #   5. read first burst and create entry within 'measurements'
        #   6. for all bursts in file:
        #       a.  create entry in 'apres_metadata' using valid
        #           measurement_id
        #   7. commit transaction

        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        if not isinstance(db, ApRESDatabase):
            raise TypeError("database argument should be of type ApRESDatabase.")

        if not db.is_valid():
            raise ValueError(f"database at {db.path} is not valid ApRESDatabase.")

        if not path.is_file():
            raise ValueError(\
                f"File at path {path} does not exist or is not a file.")

        # Try and load burst
        bursts = pyapres.read(path, skip_burst=False)

        # Calculate number of bursts
        n_bursts = len(bursts)
        print(f"Found {n_bursts} in file at {path}")

        meas_dict = \
            ApRESDatabaseManager.measurements_dict_from_pyapres_burst(bursts[0])

        # Begin transaction and create entry within 'measurements'
        cursor = db.get_cursor()

        try:
            cursor.execute("""
                BEGIN TRANSACTION;
                """)
            cursor.execute("""
                INSERT INTO `measurements`
                (`filename`,
                `path`,
                `name`,
                `timestamp`,
                `valid`,
                `location`,
                `comments`,
                `latitude`,
                `longitude`,
                `elevation`)
                VALUES
                (?,?,?,?,?,?,?,?,?,?);
                """,
                # Measurement ID
                (
                    path.parts[-1],
                    str(pathlib.Path(path)),
                    name,
                    meas_dict['timestamp'],
                    meas_dict['valid'],
                    location,
                    comments,
                    meas_dict['latitude'],
                    meas_dict['longitude'],
                    meas_dict['elevation']
                )
            )
        except sqlite3.IntegrityError:
            cursor.execute("ROLLBACK;")
            print(f"Error reading {path}, skipping")
            return

        # Now we need to get the measurement ID
        cursor.execute("""SELECT last_insert_rowid();""")
        meas_id = cursor.fetchone()
        if len(meas_id) > 0:
            print(f"Found measurement_id {meas_id}")
            meas_id = meas_id[0]
        else:
            raise Exception("Could not find inserted measurement row. Quitting.")

        # Now iterate over each burst
        burst_count = 1
        valid = True # assume valid and then and on each burst
        for burst in bursts:

            valid = valid and burst.valid
            burst_metadata = self.get_burst_metadata(burst_count, meas_id, burst)

            try:
                cursor.execute(
                    """
                    INSERT INTO `apres_metadata`
                    (
                    `id`,
                    `burst_id`,
                    `measurement_id`,
                    `timestamp`,
                    `n_attenuators`,
                    `n_chirps`,
                    `n_subbursts`,
                    `period`,
                    `f_lower`,
                    `f_upper`,
                    `af_gain`,
                    `rf_attenuator`,
                    `f_sampling`,
                    `tx_antenna`,
                    `rx_antenna`,
                    `power_code`,
                    `battery_voltage`,
                    `temperature_1`,
                    `temperature_2`,
                    `rmb_issue`,
                    `vab_issue`,
                    `venom_issue`,
                    `software_issue`
                    ) 
                    VALUES
                    (
                    NULL, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?, 
                    ?
                    )
                    """,
                    burst_metadata
                )
            except sqlite3.IntegrityError:
                valid = False

            burst_count += 1

        cursor.execute("""
            UPDATE `measurements`
            SET `valid` = ? 
            WHERE `measurement_id` = ?;
        """,
            (valid, meas_id))
        
        cursor.execute("COMMIT;")
        db.get_connection().commit()

    @staticmethod
    def get_burst_metadata(burst_id, measurement_id, burst):
        return (
            burst_id,
            measurement_id,
            datetime.datetime.strftime(burst.Time_stamp, '%Y-%m-%d %H:%M:%S.%f')[0:-3],
            burst.nAttenuators,
            burst.NAntennas * burst.NSubBursts * burst.nAttenuators,
            burst.NSubBursts,
            burst.fmcw_parameters.T,
            burst.fmcw_parameters.f_lower,
            burst.fmcw_parameters.f_upper,
            burst.AFGain,
            burst.Attenuator1,
            burst.fmcw_parameters.fs,
            str(burst.TxAnt),
            str(burst.RxAnt),
            burst.PowerCode,
            burst.BatteryVoltage,
            burst.Temp1,
            burst.Temp2,
            burst.RMB_Issue,
            burst.VAB_Issue,
            burst.Venom_Issue,
            burst.SW_Issue
        )

    @staticmethod
    def measurements_dict_from_pyapres_burst(burst):
        # Create empty dictionary
        meas_dict = dict()
        # Convert to fractional seconds
        time_out = datetime.datetime.strftime(
            burst.Time_stamp,
            "%Y-%m-%d %H:%M:%S.%f"
        )
        # Assign to measurement dictionary
        meas_dict['timestamp'] = time_out[0:-3]
        meas_dict['valid'] = 1
        meas_dict['latitude'] = burst.Latitude
        meas_dict['longitude'] = burst.Longitude
        meas_dict['elevation'] = None

        return meas_dict

class UninitializedDatabaseError(Exception):
    pass

if __name__ == "__main__":
    # Create database
    db = ApRESDatabase(pathlib.Path(DB_ROOT) / DB_NAME, create=True)
    dbman = ApRESDatabaseManager()

    for file in os.listdir(SEARCH_PATH):
        print(f"Found file {file}")
        if file.lower().endswith(".dat"):
            print(f"Adding file: {file}")
            dbman.add_dat_file(db, pathlib.Path(SEARCH_PATH) / file)