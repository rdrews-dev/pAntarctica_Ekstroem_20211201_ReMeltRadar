

class FileRecord:

    FIELDS = [
        "filename",
        "size",
        "owner",
        "date_added",
        "comment"
    ]

    def __init__(self, path=None):
        # Assign None to all field values
        for field in self.FIELDS:
            setattr(self, field, None)
        # Set catalogued to false - assumed we haven't logged the file
        self.catalogued = False
        self.path = path

    def exists(self):
        if self.path == None:
            return False
        else:
            return self.path.is_file()

    def __eq__(self, other_file):
        # Behaviour for equal is that True is returned if filename and size match
        if isinstance(other_file, FileRecord):
            return (
                    self.filename == other_file.filename
                and self.size == other_file.size
            )
        else:
            TypeError("comparison must be made with another FileRecord object")

    def __ne__(self, other_file):
        return not self.__eq__(other_file)

    def __lt__(self, other_file):
        if isinstance(other_file, FileRecord):
            return (
                    self.filename == other_file.filename
                and self.size < other_file.size
            )
        else:
            TypeError("comparison must be made with another FileRecord object")

    def __gt__(self, other_file):
        if isinstance(other_file, FileRecord):
            return (
                    self.filename == other_file.filename
                and self.size > other_file.size
            )
        else:
            TypeError("comparison must be made with another FileRecord object")
        
    @staticmethod
    def from_csv_row(csv_path, header, values):

        # Check header and values are same length
        if len(header) != len(values):
            raise ValueError("header and values must have the same number of elements.")

        # Create new record
        new_file = FileRecord()

        # Iterate over fields
        for k in range(len(values)):
            setattr(new_file,header[k],values[k])

        # Assign path 
        new_file.path = csv_path / new_file.filename

        return new_file

    @staticmethod
    def from_path(path):

        # Cast to pathlib.Path object if we haven't already been passed one
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path);

        file_record = FileRecord()
        # Now load fields
        file_record.path = path
        file_record.filename = path.parts[-1]
        
        if path.exists():
            file_record.date_added = datetime.datetime.utcfromtimestamp(path.stat().st_mtime)
            try:
                file_record.owner = path.owner()
            except NotImplementedError:
                file_record.owner = ""
            file_record.size = path.stat().st_size
            file_record.comment = ""

        return file_record

class Catalogue:

    def __init__(self, path, **kwargs):
        
        # Initialise variables
        self.files = []
        self.path = path
        self.header_map = {}

        # Load catalogue from CSV
        if path.is_file():
            logger = logging.getLogger("data_report")
            logger.debug(f"Path {path} exists, loading from CSV.")
            self.load_from_csv()
        elif path.is_dir():
            # The path provided is a directory so we try to find the
            # catalogue.csv file within this directory, if not we will
            # return to the error below
            path = path / "catalogue.csv"
            # achieve this by calling the constructor on itself with 
            # the modified path variable.
            Catalogue.__init__(self, path, **kwargs)
        else:
            logger = logging.getLogger("data_report")
            logger.warning(f"Couldn't find {path} - continuing, but will warn it doesn't exist.")

    def exists(self):
        return self.path.exists()

    def dir(self):
        return self.path.parent

    def __contains__(self, record):
        for file in self.files:
            if record == file:
                return True
            # otherwise continue
        return False

    def load_from_csv(self, header_only=False):

        # Check whether catalogue.csv file path exists
        if not self.path.is_file():
            # Try to find catalogue.csv
            self.path = self.path / "catalogue.csv";
            if not self.path.is_file():
                raise FileNotFoundError(self.path)

        with open(self.path, 'r') as cat_file:
            cat_reader = csv.reader(cat_file)
            
            # Read first line and test for header
            header = cat_reader.__next__()
            self.header_map = {}
            #Store column index
            col_index = 0
            # Check each header and validate
            for header_name in header:
                # If valid store in map
                if header_name in FileRecord.FIELDS:
                    self.header_map[col_index] = header_name
                # otherwise error
                else:
                    raise ValueError(f"Invalid header name {header_name} in {path}.")
                col_index += 1

            # Quit here if only reading header
            if header_only:
                return

            # Now when we read from files we can use the header_map to 
            # select the correct column to read from
            for row in cat_reader:
                # Read file from row
                self.files.append(FileRecord.from_csv_row(self.path, self.header_map, row))

    def load_from_file_system(self, logger_name=__file__):

        logger = logging.getLogger(logger_name)
        # Iterate over path 
        for file in os.listdir(self.dir()):
            # Create path to file
            f_path = self.dir() / file
            # Load record 
            file_record = FileRecord.from_path(f_path)
            # Check whether it exists in catalogue (first check if catalogue exists)
            if self.exists() and file_record in self.files:
                logger.debug(f"Found file {f_path} in catalogue.")
                self.files
            else:
                logger.debug(f"Could not find {f_path} in catalogue. Adding record.")
                # Add file to local record
                self.files.append(file_record)
