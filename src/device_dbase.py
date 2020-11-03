##
# @file device_dbase.py
# @brief BT Device database

""" BT Device database
"""

# Global imports
import pathlib
from pathlib import Path
import sqlite3

# Local imports
from lib.helper import debug
from lib.decorators import dumpArgs, dumpFuncname

DB_CREATE = """create table devices
            (addr text primary key, name text, info text)"""

SEARCH_ALL = "select * from devices"
SEARCH_ADDR = "select addr name from devices where addr GLOB ? order by addr"

# ===============================================================================
def get_dbasefile_path(dbase_filename="btdevice_dbase.sqlite") -> Path:
    """Determine full path to Database file
    :returns: fullpath to database file
    """

    path = pathlib.Path.cwd().joinpath("dbase")
    debug(f"path = {path}")
    # if not os.path.isdir(path):
    #     os.makedirs(path)
    path.mkdir(parents=True, exist_ok=True)
    fullpath = path.joinpath(dbase_filename)

    return fullpath


# ===============================================================================
class DeviceDatabase:
    """Database class"""

    def __init__(self, filename):
        """Intialize this class
        @param filename The name of the database file

        The database fields:
            create table software(path text primary key, name text)

        """

        debug("Initializing DeviceDatabase")

        if not filename:
            print("No DeviceDatabase filename given")

        self.dbasefile = pathlib.Path(filename)
        debug(f"dbasefile = {self.dbasefile}")

        if not self.dbasefile.parent.is_dir():
            print(f"Could not find foldername for {self.dbasefile}")
            self.dbasefile.parent.mkdir(exist_ok=True)

        self.con = None
        self.cur = None

        if self.dbasefile.is_file():
            self.open()
            debug("Opened existing database")
        else:
            self.create()
            debug("Created new database")

    # ===============================================================================
    #  open
    # ===============================================================================
    def delete(self) -> bool:
        """Delete the database from the disk

        :returns: True in case of success, False in case of an error
        """

        # first close the database, if it is still open
        self.close()

        # Check if the database exists
        if not self.dbasefile.is_file():
            debug(f"could not find {self.dbasefile} for deletion")
            return False

        # Unlink and delete the database file
        self.dbasefile.unlink()
        debug(f"database '{self.dbasefile}' has been deleted")
        # Re-check if the file is really not there anymore
        if self.dbasefile.is_file():
            debug("Error: Failed in deleting the database")
            return False

        # All is OK.
        return True

    # ===============================================================================
    #  open
    # ===============================================================================
    def create(self):
        """Create the database

        Originally, in rapidconfig, the following structure was used:
            self.cur.execute('''create table software
            (id text primary key, name text, device text, descr text, localpath text, serverpath text, ondisk INTEGER, onserver INTEGER, show INTEGER)''')

        """

        debug(f"Creating database {self.dbasefile}")

        # For check_same_thread=False option, see https://stackoverflow.com/questions/48218065/

        self.con = sqlite3.connect(self.dbasefile, check_same_thread=False)
        self.cur = self.con.cursor()
        debug(f'Creation string = {DB_CREATE}')
        self.cur.execute(DB_CREATE)
        debug(f"Returning {self.con}")
        return self.con

    # ===============================================================================
    def open(self) -> bool:
        """
        If the database does not exist yet, the table 'devices' will be created.
        If it already exists, it will just be openend.
        """

        debug(f"Opening database {self.dbasefile}")
        self.con = sqlite3.connect(self.dbasefile, check_same_thread=False)
        self.cur = self.con.cursor()
        if self.cur:
            return True
        else:
            return False

    # ===============================================================================
    #  close
    # ===============================================================================
    def close(self) -> bool:
        """Close the connection and the database"""

        # debug('Closing database connection')

        if self.con:
            self.con.close()
            debug("Database has been closed")
            return True
        return False

    # ===============================================================================
    #  commit
    # ===============================================================================
    def commit(self) -> bool:
        """Commit changes to the database
        Always returns True
        """
        # if self.con:
        self.con.commit()
        return True

    # ===============================================================================
    # add
    # ===============================================================================
    # @dumpArgs
    def add(self, addr, name, info) -> bool:
        """Add an entry to the sqlite database

        :param addr: BT address
        :param name: Name of the BT device
        :param info: Info string of this BT device
        :return: True in case of success, False in case of an error.
        """

        try:
            self.cur.execute(
                "insert into devices values (?, ?, ?)",
                (addr, name, info),
            )
        except sqlite3.IntegrityError:
            debug(f'Cannot not add addr "{addr}" twice')
            return False

        self.add(addr, name, info)
        self.con.commit()
        return True

    # ===============================================================================
    def search(self, searchfor) -> list:
        """Generic search in the software database for string s

        :param searchfor: The string to search for
        :return:  List of tuples like [(u'c:\\xxxx,), (u'c:\\yyyy,)]

        """

        if not searchfor:
            debug("search string or search list was not defined")
            return []

        if type(searchfor) == str:
            searchfor = [searchfor]  # Convert string to list with a single item

        list_of_tuples = []
        for searchstring in searchfor:
            debug(f"Searching for '{searchstring}' with GLOB")

            self.cur.execute(
                # "select addr from devices where addr GLOB ? order by addr",
                SEARCH_ADDR,
                [searchstring],
            )
            list_of_tuples.extend(self.cur.fetchall())
            debug(f"dbase search result = {list_of_tuples}")

        returnlist = [x[0] for x in list_of_tuples]
        returnlist = sorted(returnlist)
        debug(f"returnlist = {returnlist}")
        return returnlist

    # ===============================================================================
    def get_all_devices(self):
        """From the database, get all the entries

        :return: listctrl of tuples which are marked as 'ondisk'
        """

        self.cur.execute(SEARCH_ALL)
        rows = self.cur.fetchall()
        return rows


# ===============================================================================
if __name__ == "__main__":
    """ __main__ entry point

    Mainly used for tests
    """

    import sys
    import doctest

    failed, tested = doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    if not failed == 0:
        sys.exit(0)
