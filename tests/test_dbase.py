# global imports
import pathlib
import sys

sys.path.insert(0, '../src')
sys.path.insert(0, '../src/lib')
print('sys.path = %s' % sys.path)

# local imports
from lib.helper import clear_debug_window
clear_debug_window()

import device_dbase

print('SQLite3 version %s' % device_dbase.sqlite3.version)

# Bad habit, I know, but this fixed path is just for test purposes.
dbase_path = 'Z:/pi_bluetooth/tests/dbase/test_btdevice_dbase.sqlite'


def test_dbase_path():

    print("hello henk")
    dbase_path = device_dbase.get_dbasefile_path()
    assert dbase_path == pathlib.WindowsPath(dbase_path)

    # The folder has to exist...
    assert dbase_path.parent.is_dir()

def test_dbase():

    db = device_dbase.DeviceDatabase(dbase_path)
    assert db.dbasefile == pathlib.WindowsPath(dbase_path)

    db.add('aa:bb:cc:dd:ee:ff', 'testname1', 'testinfo4')
    db.add('11:22:33:44:55:66', 'testname2', 'testinfo5')

    # Show all existing devices in this database
    ret_list = db.get_all_devices()
    print('\nAll devices:', ret_list)

    # Test for a non-existing device
    ret_list = (db.search('*'))
    print(f"{ret_list=}")
    assert db.search('doesnotexist') == []

    # Test if an existing device can be found
    search_str = 'aa:bb:cc:dd:ee:ff'
    ret_list = db.search(search_str)
    ret_str = ','.join(ret_list)
    print(f'search for {search_str} returned "{ret_list}"')
    assert search_str in ret_str

    search_str = 'xx:yy:zz:xx:yy:zz'
    ret_list = db.search(search_str)
    ret_str = ','.join(ret_list)
    print(f'search for {search_str} returned {ret_list}')
    assert search_str not in ret_str

    # Delete the test database after the tests
    db.delete()
