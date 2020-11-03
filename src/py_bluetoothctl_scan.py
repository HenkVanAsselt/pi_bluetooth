##
# @file: py_bluetoothctl.py
# @brief: bluetoothctl scan functions

"""bluetoothctl scan functions
"""

# global imports
import sys
import datetime
import re

# local imports
from command import run_command
from lib.helper import print_header
from lib.helper import debug
from lib.helper import clear_debug_window
from lib.decorators import dumpFuncname, dumpArgs
from lib.helper import IteratorWithPushback
from device_dbase import DeviceDatabase


# -----------------------------------------------------------------------------
class BTDevice:
    dev: str
    addr: str
    name: str = ""
    timestamp: str = ""
    rssi: int = 0
    txpower: int = 0
    manufacturerdata: str = ""
    servicedata: str = ""
    info: str = ""  # The full info string
    props: dict = {}  # The info string, broken up in properties

    def __str__(self):
        s = f"BTDevice (str): addr={self.addr} \nname={self.name} \nprops={self.props} \ninfo={self.info}"
        return s

    def __repr__(self):
        s = f"BTDevice (repr): addr={self.addr} \nname={self.name} \nprops={self.props} \ninfo={self.info}"
        return s


bt_devices = {}  # dictionary of BTDevice, key is the address

# -----------------------------------------------------------------------------
sampleoutput_bluetoothctl_devices = """
Device 47:B6:7A:81:C4:BC 47-B6-7A-81-C4-BC
Device D8:DD:6B:81:74:8B Hue Lamp
Device 18:93:7F:B1:71:37 18-93-7F-B1-71-37
Device 5A:B5:65:89:46:37 5A-B5-65-89-46-37
Device E2:A0:D0:D9:58:1D Hue Lamp
Device F4:BA:5D:1A:3C:2F Hue Lamp
Device F4:9A:7C:BE:5F:2A Hue Lamp
Device 4D:FE:E2:0B:C2:C6 4D-FE-E2-0B-C2-C6
Device FC:03:9F:5E:05:75 FC-03-9F-5E-05-75
Device F5:8E:47:26:13:BD Hue Lamp
Device 24:FC:E5:8F:AB:89 [TV] Samsung Q70 Series (49)
Device 00:7C:2D:E5:BE:D9 [TV] Samsung 7 Series (65)
"""

# -----------------------------------------------------------------------------


Samsung_Q70_info = """Device 24:FC:E5:8F:AB:89 (public)
        Name: [TV] Samsung Q70 Series (49)
        Alias: [TV] Samsung Q70 Series (49)
        Class: 0x000c043c
        Icon: audio-card
        Paired: no
        Trusted: no
        Blocked: no
        Connected: no
        LegacyPairing: no
        UUID: Audio Source              (0000110a-0000-1000-8000-00805f9b34fb)
        UUID: Audio Sink                (0000110b-0000-1000-8000-00805f9b34fb)
        UUID: A/V Remote Control Target (0000110c-0000-1000-8000-00805f9b34fb)
        UUID: A/V Remote Control        (0000110e-0000-1000-8000-00805f9b34fb)
        UUID: PnP Information           (00001200-0000-1000-8000-00805f9b34fb)
        Modalias: bluetooth:v04E8p8080d0000
        ManufacturerData Key: 0x0075
        ManufacturerData Value:
  42 04 01 20 7e 19 0f 00 02 01 31 00 00 00 00 00  B.. ~.....1.....
  00 00 00 00 00 00 00 00                          ........
        ManufacturerData Key: 0xff19
        ManufacturerData Value:
  00 75 00 09 01 00 00 00 06 01 00 00 00 00 00 00  .u..............
  00 00 00 00 00 00 00 00                          ........
"""

Samsung_tablet_info = """Device 00:7C:2D:E5:BE:D9 (public)
        Name: [TV] Samsung 7 Series (65)
        Alias: [TV] Samsung 7 Series (65)
        Paired: no
        Trusted: no
        Blocked: no
        Connected: no
        LegacyPairing: no
        ManufacturerData Key: 0x0075
        ManufacturerData Value:
  42 04 01 80 60 00 7c 2d e5 be d9 02 7c 2d e5 be  B...`.|-....|-..
  d8 01 00 00 00 00 00 00                          ........
"""

sampleoutput_bluetoothctl_info = []
sampleoutput_bluetoothctl_info.append(Samsung_tablet_info)
sampleoutput_bluetoothctl_info.append(Samsung_Q70_info)


# -----------------------------------------------------------------------------
@dumpFuncname
def live_scan(timeout=5, verbose=False):
    """Perform a live Bluetooth scan

    :param timeout: Scan duration
    :param verbose: If True, print the scan results here
    :return: string with scan results. See [sample_output]
    """

    print(f"Scanning for {timeout} seconds...")

    scan_result = run_command(f"bluetoothctl --timeout {timeout} scan on")
    run_command("bluetoothctl scan off")

    # Show the live scan results
    if scan_result and verbose:
        print("output:")
        print(80 * "-")
        print(scan_result)
        print(80 * "-")

    # Return the live scan results
    return scan_result


# -----------------------------------------------------------------------------
@dumpFuncname
def get_live_devices(verbose=False):
    """Get the devices, found during a live scan

    :param verbose: If True, print the scan results here
    :return: string with scan results. See [sample_output]
    """

    devices_str = run_command("bluetoothctl devices")
    if verbose:
        print(devices_str)
    return devices_str


# -----------------------------------------------------------------------------
testdata = """Device 47:B6:7A:81:C4:BC 47-B6-7A-81-C4-BC\n
Device D8:DD:6B:81:74:8B Hue Lamp\n
Device 24:FC:E5:8F:AB:89 [TV] Samsung Q70 Series (49)
"""


def get_mac_addresses(data):
    r"""Process the output of 'bluetoothctl devices'

    :param data: string with the output of 'bluetoothctl devices'
    :returns: list of mac addresss found

    >>> get_mac_addresses(testdata)
    ['47:B6:7A:81:C4:BC', 'D8:DD:6B:81:74:8B', '24:FC:E5:8F:AB:89']
    """

    addr_list = []
    for line in data.splitlines():
        if not line:
            continue
        debug(f"line = '{line}'")
        dev, addr, value = line.split(" ", maxsplit=2)
        addr_list.append(addr)
    return addr_list


# -----------------------------------------------------------------------------
@dumpFuncname
def process_devices(data):
    """Process the bluetoothctl devices

    :param data: string with lines to process
    :returns: dictionary of bluetooth devices

    Example string: see [sample_output]
    """

    for line in data.splitlines():

        datetimestr = get_timestamp()

        if not line:
            continue

        # Reset values
        device = None
        addr = None

        try:
            dev, addr, value = line.split(" ", maxsplit=2)
            debug(f"{dev}, {addr}, {value}")

            if addr not in bt_devices:
                # This is a new device

                # device = BTDevice(addr=addr, dev=dev, timestamp=datetimestr, name=value)
                device = BTDevice()
                device.addr = addr
                device.dev = dev
                device.timestamp = datetimestr
                device.name = value

                # print('new device has been found', device)
            else:
                # This device was seen before. Update the information
                device = bt_devices.get(addr)
                device.timestamp = datetimestr
                # print('existing device has been updated:', device)
        except ValueError:
            print('ERROR: Problem in line "line"')

        # Add / Replace this device in the dictionary
        # print(device)
        if addr and device:
            bt_devices[addr] = device

    return bt_devices


# -----------------------------------------------------------------------------
def reset_value() -> list:
    return []


# -----------------------------------------------------------------------------
test_info_servicedata = r"""
Device 23:A0:64:00:3A:F1 (random)
    Alias: 23-A0-64-00-3A-F1
    Paired: no
    Trusted: no
    Blocked: no
    Connected: no
    LegacyPairing: no
    UUID: Unknown                   (0000fd6f-0000-1000-8000-00805f9b34fb)
    ServiceData Key: 0000fd6f-0000-1000-8000-00805f9b34fb
    ServiceData Value:
  d7 e5 ea 9f 94 47 4c 30 aa 0c 44 a9 55 26 0d d9  .....GL0..D.U&..
  4f b7 8c fd                                      O...
"""

test_info_manufdata = r"""
Device 24:FC:E5:8F:AB:89 (public)
    Name: [TV] Samsung Q70 Series (49)
    Alias: [TV] Samsung Q70 Series (49)
    Class: 0x000c043c
    Icon: audio-card
    Paired: no
    Trusted: no
    Blocked: no
    Connected: no
    LegacyPairing: no
    UUID: Audio Source              (0000110a-0000-1000-8000-00805f9b34fb)
    UUID: Audio Sink                (0000110b-0000-1000-8000-00805f9b34fb)
    UUID: A/V Remote Control Target (0000110c-0000-1000-8000-00805f9b34fb)
    UUID: A/V Remote Control        (0000110e-0000-1000-8000-00805f9b34fb)
    UUID: PnP Information           (00001200-0000-1000-8000-00805f9b34fb)
    Modalias: bluetooth:v04E8p8080d0000
    ManufacturerData Key: 0x0075
    ManufacturerData Value:
  42 04 01 20 7e 19 0f 00 02 01 31 00 00 00 00 00  B.. ~.....1.....
  00 00 00 00 00 00 00 00                          ........        
    ManufacturerData Key: 0xff19
    ManufacturerData Value:
  00 75 00 09 01 00 00 00 06 01 00 00 00 00 00 00  .u..............
  00 00 00 00 00 00 00 00                          ........
"""


def get_special_data(info, tag1, tag2) -> dict:
    """Extract ServiceData (key and value) from the info string
    :param info: The string to process
    :param tag1: The first tag to process, e.g. "ServiceData Key:" or "ManufacturerData Key:"
    :param tag2: The 2nd tag to process, e.g. "ServiceData Value:" or "ManufacturerData Value:"

    >>> get_special_data("abc", "ServiceData Key:", "ServiceData Value:")
    {}

    >>> clear_debug_window()
    >>> get_special_data(test_info_servicedata, "ServiceData Key:", "ServiceData Value:")
    {'0000fd6f-0000-1000-8000-00805f9b34fb': [215, 229, 234, 159, 148, 71, 76, 48, 170, 12, 68, 169, 85, 38, 13, 217, 79, 183, 140, 253]}
    """

    # @dumpArgs
    def get_key(line):
        _header, key = line.split(":")
        key = key.strip()
        # debug(f'Returning key = {key}')
        return key

    # @dumpArgs
    def get_valuelist_from_one_line(line) -> list:
        line = line.strip()
        list_to_return = []
        while True:
            s = line.split(" ", maxsplit=16)  # For example ['00', '00', '00', '00', '00', '00', '00', '00', '', '', '', '', '', '', '', '', '                 ........']
            # debug(s)
            try:
                for i, hexvalue in enumerate(s):
                    val = int(hexvalue, 16)
                    list_to_return.append(val)
            except ValueError:
                # End of the valid hex values
                break
        # debug(f"returning {list_to_return}")
        return list_to_return

    # @dumpArgs
    def get_value(lines) -> list:
        """Get the hex values out of next line of iterator
        :param lines: iterator of lines
        :returns: tuple of the next line (without hex values) and the list of values
        """
        value_list = []
        while True:
            try:
                line = next(lines)
                # debug(f"get_value {line}")
            except StopIteration:
                # debug(f"returning value_list1 {value_list}")
                return value_list
            tmp_list = get_valuelist_from_one_line(line)
            value_list.extend(tmp_list)
            # debug(f"current value_list = {value_list}")
            # debug(f"current line = {line}")
            if (tag1 in line) or (tag2 in line):
                debug(f'Pushing back line {line}')
                lines.push_back(line)
                # debug(f"returning value_list2 {value_list}")
                return value_list

    # Look ahead and see if the desired strings are available.
    # If not, then return immediately
    if (tag1 not in info) or (tag2 not in info):
        return {}

    # debug(info)

    key_to_return = None
    dict_to_return = {}

    lines = IteratorWithPushback(info.splitlines())
    line = next(lines)
    while True:
        # debug('-----')
        # debug(f"Start of while true 0, line={line}")
        try:
            # debug(f"key_to_return={key_to_return}")
            # debug(f"value_to_return={value_to_return}")
            if tag1 in line:
                # debug("-----")
                # debug(f"Found tag1 '{tag1}' in line '{line}'")
                key_to_return = get_key(line)
                # debug(f"key_to_return={key_to_return}")
                line = next(lines)
                continue   # We found the line with key
            elif tag2 in line:
                # debug("-----")
                # debug(f"Found tag2 '{tag2}' in line '{line}'")
                value_to_return = get_value(lines)
                # debug(f"final key={key_to_return} value_to_return={value_to_return}")
                # Add key and value to the dictionary to return
                if key_to_return and value_to_return:
                    dict_to_return[key_to_return] = value_to_return
                # Reset the key and value which will be build up
                key_to_return = ""
                value_to_return = []
                line = next(lines)
            else:
                line = next(lines)
                continue
        except StopIteration:
            # debug("End of iterator")
            break

    return dict_to_return


# -----------------------------------------------------------------------------
def get_service_data(info) -> dict:
    """Extract ServiceData (key and value) from the info string
    :param info: The string to process

    >>> get_special_data(test_info_servicedata, "ServiceData Key:", "ServiceData Value:")
    {'0000fd6f-0000-1000-8000-00805f9b34fb': [215, 229, 234, 159, 148, 71, 76, 48, 170, 12, 68, 169, 85, 38, 13, 217, 79, 183, 140, 253]}

    """

    d = get_special_data(info, "ServiceData Key:", "ServiceData Value:")
    return d


# -----------------------------------------------------------------------------
def get_manuf_data(info) -> dict:
    """Extract ServiceData (key and value) from the info string
    :param info: The string to process

    >>> clear_debug_window()
    >>> get_manuf_data(test_info_manufdata)
    {'0x0075': [66, 4, 1, 32, 126, 25, 15, 0, 2, 1, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], '0xff19': [0, 117, 0, 9, 1, 0, 0, 0, 6, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

    """

    d = get_special_data(info, "ManufacturerData Key:", "ManufacturerData Value:")
    return d


# -----------------------------------------------------------------------------
@dumpFuncname
def process_device_info(info) -> BTDevice:
    """Process deviceinfo string for one device

    :param info: The string to process. For an example, see ...
    """

    bt_device = BTDevice()
    hex_value_list = reset_value()
    key = ""

    for line in info.splitlines():

        line = line.strip()
        if not line:  # Empty line
            continue

        if line.startswith("Device "):
            dev_type, addr, comment = line.split(" ", maxsplit=2)
            bt_device.dev_type = dev_type
            bt_device.addr = addr
            bt_device.comment = comment
            bt_device.info = info
            debug(bt_device)
            continue

        try:
            key, val = line.split(":", maxsplit=1)
            key = key.strip()
            val = val.strip()
            debug(f"key={key}, val={val}")
            bt_device.props[key.strip()] = val
            hex_value_list = reset_value()
            continue
        except ValueError:
            # print(f"Could not use split(':') on line={line}")
            l2 = line
            if len(line) > 47:
                l2 = line[:47]
            t = re.findall(r"[0-9a-fA-F]+", l2)  # Find the hexadecimal combinations
            # print("regex output: ", t)
            hex_value_list.extend(t)
            bt_device.props[key.strip()] = hex_value_list

    print()
    print(bt_device)
    return bt_device


# -----------------------------------------------------------------------------
def get_timestamp():
    """Create current date-time stamp string.

    :returns: datetime string
    """
    dt_date = datetime.datetime.now()
    datetimestr = dt_date.strftime("%Y%m%d-%H%M%S.%f")
    return datetimestr


# =============================================================================
def main():

    # Determine if we are working online (on the Raspberry Pi) or offline on Windows
    online = False
    if sys.platform == "linux":
        online = True

    dbase_path = "./dbase/dbase.sql"
    db = DeviceDatabase(dbase_path)

    if online:
        live_scan(timeout=30)
        data = get_live_devices()
    else:
        print("No live capture was peformed, using sample output")
        data = sampleoutput_bluetoothctl_devices

    # Get a list of mac addresses from the ouput
    addresses = get_mac_addresses(data)
    print_header("List of MAC addresses")
    print(addresses)

    print_header("DEVICES")
    devs = process_devices(data)
    for dev in devs.items():
        print(dev)
    print()

    # Get information for each device:
    if online:
        # Get online info for each discovered device
        for addr in devs:
            info = run_command(f"bluetoothctl info {addr}", verbose=True)
            if info:
                process_device_info(info)
    else:
        # Use offline sample info
        for info in sampleoutput_bluetoothctl_info:
            process_device_info(info)


# -----------------------------------------------------------------------------
def do_doctest():
    import sys
    import doctest

    failed, tested = doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    if not failed == 0:
        sys.exit(0)


# =============================================================================
if __name__ == "__main__":

    # do_doctest

    # clear_debug_window()
    # ret = get_special_data(test_info_servicedata, "ServiceData Key:", "ServiceData Value:")
    # print(ret)

    main()
