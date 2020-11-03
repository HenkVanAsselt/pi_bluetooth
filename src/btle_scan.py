##
# @file: btle_scan.py
# @brief: Bluetooth Low Energy scanner

"""Bluetooth Low Energy scanner
"""

# global imports
import sys

# local imports
from command import run_command


# -----------------------------------------------------------------------------
sample_output = """LE Scan ...
F4:9A:7C:BE:5F:2A (unknown)
F4:9A:7C:BE:5F:2A Hue Lamp
E2:A0:D0:D9:58:1D (unknown)
E2:A0:D0:D9:58:1D Hue Lamp
FC:03:9F:5E:05:75 (unknown)
00:7C:2D:E5:BE:D9 [TV] Samsung 7 Series (65)
"""


# -----------------------------------------------------------------------------
def process_le_scan(scanresults):
    """Process the list of scanned BTLE devices.

    :param scanresults: The result to process, which is a text with linebreaks
    :returns: dict of resolved and dict of unknown bt addreses
    """

    resolved = {}  # dictionary of bt addresses with names
    unknown = {}  # dictionary of bt addresses with unknown names.

    for line in scanresults.splitlines():

        if 'LE Scan ...' in line:
            continue
        bt_addr, name = line.split(' ', maxsplit=1)

        if name == '(unknown)':
            # Add the addr and name to the unknown dictionary
            unknown[bt_addr] = ""
        else:
            resolved[bt_addr] = name
            # As the name is known here, remove a resolved bt_addr from the unknown dictionary
            if bt_addr in unknown:
                del unknown[bt_addr]

    # Return the two dictionaries.
    return resolved, unknown


# -----------------------------------------------------------------------------
def print_btle_scan_results(resolved, unknown):
    """Print the contents of the bt address dictionaries
    :param resolved: dictionary with resolved names
    :param unknown: dictionary with unknown names
    """

    header = "RESOLVED BTLE DEVICES"
    print(f"\n{header}")
    print(f"{len(header)*'-'}")
    for key, value in resolved.items():
        print(key, value)

    header = "BTLE DEVICES WITHOUT NAME"
    print(f"\n{header}")
    print(f"{len(header)*'-'}")
    for key, value in unknown.items():
        print(key, value)


# =============================================================================
def main():

    # Determine if we are working online (on the Raspberry Pi) or offline on Windows
    online = False
    if sys.platform == "linux":
        online = True

    if online:
        timeout = 30
        print(f"BTLE Scanning for {timeout} seconds...")

        _ret = run_command("sudo hciconfig hci0 down")
        _ret = run_command("sudo hciconfig hci0 up")
        data = run_command("hcitool -i hci0 lescan", timeout=timeout)
    else:
        print("In offline mode, process sample_output")
        data = sample_output

    bt_known, bt_unknown = process_le_scan(data)
    print_btle_scan_results(bt_known, bt_unknown)


# =============================================================================
if __name__ == '__main__':
    main()
