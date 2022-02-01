from os import pathsep
import sqlite3
import pathlib

DB_ROOT = "./Doc/ApRES/Rover/HF"
DB_NAME = "Testing.db"

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

        try:
            self.get_connection(create)
        except UninitializedDatabaseError:
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
            cursor = self.db_con.cursor()
            # Check if database has data table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data';")
            if len(cursor.fetchall()) == 0:
                raise UninitializedDatabaseError(self.path)

        # Return sqlite3 connection object
        return self.db_con


    def get_cursor(self):
        connection = self.get_connection()
        return connection.cursor()

    def init_tables(self):
        cursor = self.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS 'data' (
                id INTEGER PRIMARY KEY,
                time REAL ASC,
                filename TEXT,
                path TEXT,
                location TEXT,
                comments TEXT
            );
        ''')

class UninitializedDatabaseError(Exception):
    pass

if __name__ == "__main__":
    # Create database
    db = ApRESDatabase(pathlib.Path(DB_ROOT) / DB_NAME, create=True)