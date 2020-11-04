##
# @file: btcommon.py
# @brief: Small bluetooth helper functions

"""Small bluetooth helper functions
"""

# global imports
import sys
import re
import bluetooth

# local imports
from command import run_command
from lib.helper import debug

# Create an alias
_run = run_command


# -----------------------------------------------------------------------------
def is_bt_address(s):
    """Test if the given string is a BT address
    :param s: string to test

    >>> is_bt_address("6D-01-5E-34-31-1A")
    True

    >>> is_bt_address("F4:9A:7C:BE:5F:2A")
    True

    >>> is_bt_address("F49A7CBE5F2A")
    True

    >>> is_bt_address("something")
    False

    """
    if len(s) == 17:
        if s.count("-") == 5:
            return True
        elif s.count(":") == 5:
            return True
        else:
            return False

    if len(s) == 12:
        try:
            int(s, 16)
            return True
        except ValueError:
            return False

    return False


# -----------------------------------------------------------------------------
def is_honeywell_scanner_msg(msg) -> bool:
    r"""Test if this data could come from a Honeywell Scanner.
    This is done by looking for the string MSGGET.
    See https://honeywellaidc.force.com/supportppr/s/article/What-is-the-decode-header-information-and-how-to-disable-the-decode-header-message

    :param msg: received data
    :returns: True if this was a HON scanner message, False if not

    >>> is_honeywell_scanner_msg('\x16\xfe\x14\x00\x00\x00\rMSGGET0006jC0\x1dabcde\r')
    True

    >>> is_honeywell_scanner_msg('\x1dabcde\r')
    False

    """

    if isinstance(msg, bytes):
        if msg.startswith(b"\x16\xfe") and b"MSGGET" in msg:
            return True

    if isinstance(msg, str):
        if msg.startswith("\x16\xfe") and "MSGGET" in msg:
            return True

    return False


# -----------------------------------------------------------------------------
def strip_honeywell_header(data):
    r"""If this data is coming from a Honeywell scanner and has the Honeywell header, strip the header.

    :param data: data to inspect and strip
    :returns: Stripped data

    >>> strip_honeywell_header('\x16\xfe\x14\x00\x00\x00\rMSGGET0006jC0\x1dabcde\r')
    'abcde\r'

    """

    if is_honeywell_scanner_msg(data):
        return data[21:]
    else:
        return data


# -----------------------------------------------------------------------------
def init_bluetooth(verbose=False) -> bool:
    """Common Bluetooth initialization function.

    :param verbose: If true, show verbose output
    :returns: True if successfull, False if there was a problem.
    """

    if sys.platform == "linux":

        commands = [
            "sudo rfkill unblock all",
            "sudo bluetoothctl power on",
            "sudo bluetoothctl agent NoInputNoOutput",
            "sudo bluetoothctl discoverable yes",
            "sudo bluetoothctl pairable yes",
        ]

        for cmd in commands:
            ret = run_command(cmd)
            if verbose:
                print(f"cmd = {cmd}, ret='{ret}'")
        return True

    else:
        # Not implemented yet for Win32
        pass
        return False


# -----------------------------------------------------------------------------
def adapter_name(inter="hci0", name=None):
    """

    :param inter:
    :param name:
    :return:
    """

    if name is not None:  # Set the adaptername
        s = run_command(f"hciconfig {inter} name {name}")
        print(s)
    else:  # Get the adapter name.
        s = run_command(f"hciconfig {inter} name")
        return re.compile(r"Name: \'(.*)\'").findall(str(s))[0]


# -----------------------------------------------------------------------------
def enable_adapter(adapt, cond=True):
    run_command(["hciconfig", adapt, "up" if cond else "down"])


# -----------------------------------------------------------------------------
def reset_adapter(adapt):
    run_command(["hciconfig", adapt, "reset"])


# -----------------------------------------------------------------------------
def advertise_adapter(adapt, cond=True):
    run_command(["hciconfig", adapt, "piscan" if cond else "pscan"])


# -----------------------------------------------------------------------------
def enable_adapter_ssp(adapt, cond):
    run_command(["hciconfig", adapt, "sspmode", "1" if cond else "0"])


# -----------------------------------------------------------------------------
def list_adapters():
    s = _run(["hciconfig", "-a"])
    return re.compile(r"(hci[0-9]+):").findall(str(s))


# -----------------------------------------------------------------------------
def lookup_info(addr, **kwargs):
    Class = kwargs.get("Class", True)
    Name = kwargs.get("Name", True)
    Address = kwargs.get("Address", True)
    info = {}
    while True:
        s = _run(["hcitool", "inq"])
        for i in s.splitlines():
            i = str(i)
            if addr in i:
                info["class"] = re.compile(r"class: ([A-Fa-fx0-9]*)").findall(i)[0]
                info["addr"] = addr
                info["name"] = bluetooth.lookup_name(addr)
                return info

        print("Still looking for ", addr, "...", " Is it discoverable? ")


# -----------------------------------------------------------------------------
def adapter_address(inter, addr=None):
    s = _run(["hciconfig", inter])
    return re.compile(r"Address: ([A-Fa-f0-9:]*)").findall(str(s))[0]


# -----------------------------------------------------------------------------
def adapter_class(inter="hci0", clas=None):
    if clas:
        s = _run(["hciconfig", inter, "class", clas])
        return s
        # clone.set_adapter_class(inter,clas);
    else:
        s = _run(["hciconfig", inter, "class"])
        return re.compile(r"Class: ([A-Fa-fx0-9]*)").findall(str(s))[0]


# -----------------------------------------------------------------------------
def is_serial_service_running(verbose=False) -> bool:
    """Check if serial port service is already running on the given port/channel

    :param verbose: Show verbose results
    :return: True if the service was running, False if not
    """

    ret = run_command("sudo sdptool browse local")
    if "Service Name: Serial Port" in ret:
        if verbose:
            print(f"Serial port service is already running")
        return True
    else:
        if verbose:
            print(f"Serial port service is not running")
        return False


# -----------------------------------------------------------------------------
def add_serial_port(port=1, verbose=False) -> bool:
    """Add Bluetooth serial port service on given port.

    :param port: port/channel to add
    :param verbose: If true, show verbose results
    :returns: True if service was added, False if not (was already running)
    """

    if not is_serial_service_running():
        if verbose:
            print(f"Adding serial port service on channel {port}")
        ret = run_command(f"sudo sdptool add --channel {port} SP")
        if verbose:
            print(ret)
        return True
    else:
        if verbose:
            print(f"Serial port service is already running on channel {port}")
        return False


# -----------------------------------------------------------------------------
records_sample_data = """
Service RecHandle: 0x10000
Service Class ID List:
  "PnP Information" (0x1200)
Profile Descriptor List:
  "PnP Information" (0x1200)
    Version: 0x0103

Service Name: AVRCP CT
Service RecHandle: 0x10001
Service Class ID List:
  "AV Remote" (0x110e)
  "AV Remote Controller" (0x110f)
Protocol Descriptor List:
  "L2CAP" (0x0100)
    PSM: 23
  "AVCTP" (0x0017)
    uint16: 0x0103
Profile Descriptor List:
  "AV Remote" (0x110e)
    Version: 0x0106

Service Name: AVRCP TG
Service RecHandle: 0x10002
Service Class ID List:
  "AV Remote Target" (0x110c)
Protocol Descriptor List:
  "L2CAP" (0x0100)
    PSM: 23
  "AVCTP" (0x0017)
    uint16: 0x0103
Profile Descriptor List:
  "AV Remote" (0x110e)
    Version: 0x0105

Service Name: Audio Source
Service RecHandle: 0x10003
Service Class ID List:
  "Audio Source" (0x110a)
Protocol Descriptor List:
  "L2CAP" (0x0100)
    PSM: 25
  "AVDTP" (0x0019)
    uint16: 0x0103
Profile Descriptor List:
  "Advanced Audio" (0x110d)
    Version: 0x0103

Service Name: Headset Voice gateway
Service RecHandle: 0x10004
Service Class ID List:
  "Headset Audio Gateway" (0x1112)
  "Generic Audio" (0x1203)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 12
Profile Descriptor List:
  "Headset" (0x1108)
    Version: 0x0102

Service Name: Hands-Free Voice gateway
Service RecHandle: 0x10005
Service Class ID List:
  "Handsfree Audio Gateway" (0x111f)
  "Generic Audio" (0x1203)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 13
Profile Descriptor List:
  "Handsfree" (0x111e)
    Version: 0x0107

Service Name: Audio Sink
Service RecHandle: 0x10006
Service Class ID List:
  "Audio Sink" (0x110b)
Protocol Descriptor List:
  "L2CAP" (0x0100)
    PSM: 25
  "AVDTP" (0x0019)
    uint16: 0x0103
Profile Descriptor List:
  "Advanced Audio" (0x110d)
    Version: 0x0103

Service Name: :1.26/Profile/HSPHSProfile/00001108-0000-1000-8000-00805f9b34fb
Service RecHandle: 0x10007
Service Class ID List:
  UUID 128: 00001108-0000-1000-8000-00805f9b34fb
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 3
Profile Descriptor List:
  "Headset" (0x00001108-0000-1000-8000-00805f9b34fb)
    Version: 0x0102

Service Name: Serial Port
Service Description: COM Port
Service Provider: BlueZ
Service RecHandle: 0x10008
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 1
Language Base Attr List:
  code_ISO639: 0x656e
  encoding:    0x6a
  base_offset: 0x100
Profile Descriptor List:
  "Serial Port" (0x1101)
    Version: 0x0100

Service Name: Serial Port
Service Description: COM Port
Service Provider: BlueZ
Service RecHandle: 0x10009
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 1
Language Base Attr List:
  code_ISO639: 0x656e
  encoding:    0x6a
  base_offset: 0x100
Profile Descriptor List:
  "Serial Port" (0x1101)
    Version: 0x0100

Service Name: Serial Port
Service Description: COM Port
Service Provider: BlueZ
Service RecHandle: 0x1000a
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 1
Language Base Attr List:
  code_ISO639: 0x656e
  encoding:    0x6a
  base_offset: 0x100
Profile Descriptor List:
  "Serial Port" (0x1101)
    Version: 0x0100

Service Name: Serial Port
Service Description: COM Port
Service Provider: BlueZ
Service RecHandle: 0x1000b
Service Class ID List:
  "Serial Port" (0x1101)
Protocol Descriptor List:
  "L2CAP" (0x0100)
  "RFCOMM" (0x0003)
    Channel: 1
Language Base Attr List:
  code_ISO639: 0x656e
  encoding:    0x6a
  base_offset: 0x100
Profile Descriptor List:
  "Serial Port" (0x1101)
    Version: 0x0100
"""


# -----------------------------------------------------------------------------
def parse_inq(inq, target):
    if not isinstance(inq, str):
        inq = inq.decode("utf-8")
    lines = inq.split("\n")
    services = []
    device = {
        "host": target,
        "description": None,
        "provider": None,
        "service-classes": None,
        "service-id": None,
        "profiles": None,
    }
    append = False
    for linenr, line in enumerate(lines):
        debug(f"line101 = linenr={linenr}, line={repr(line)}")
        if append:
            if device.get("name", False):
                services.append(device)
                device = {
                    "host": target,
                    "description": None,
                    "provider": None,
                    "service-classes": None,
                    "service-id": None,
                    "profiles": None,
                }
                append = False
                debug("-----")
                debug(f"Appended device {device}")
        if not line:
            append = True
        else:
            line = line.strip()
            debug(f"line113={line}")
            if line.split(": ")[0] == "Service Name":
                device["name"] = line.split(": ")[1]
            elif line.split(": ")[0] == "Service Provider":
                device["provider"] = line.split(": ")[1]
            elif line.split(": ")[0] == "UUID 128":
                device["service-id"] = line.split(": ")[1]
            elif line.split(": ")[0] == "Channel":
                device["port"] = int(line.split(": ")[1])
                device["protocol"] = "RFCOMM"
            elif line.split(": ")[0] == "PSM":
                device["port"] = int(line.split(": ")[1])
                device["protocol"] = "L2CAP"
    return services


# -----------------------------------------------------------------------------
def inquire(addr):
    """Inquire the sdptool records and process them.

    :param addr: Address to require. Can be "local"

    See https://www.programcreek.com/python/?project_name=conorpp%2Fbtproxy#
    """

    records = run_command(f"sdptool records {addr}")
    print(repr(records))
    services = parse_inq(records, addr)
    print()
    for service in services:
        print(service)


# -----------------------------------------------------------------------------
def print_service(svc):
    print("Service Name: %s" % svc["name"])
    print("    Host:        %s" % svc["host"])
    print("    Description: %s" % svc["description"])
    print("    Provided By: %s" % svc["provider"])
    print("    Protocol:    %s" % svc["protocol"])
    print("    channel/PSM: %s" % svc["port"])
    print("    svc classes: %s " % svc["service-classes"])
    print("    profiles:    %s " % svc["profiles"])
    print("    service id:  %s " % svc["service-id"])


# =============================================================================
if __name__ == "__main__":

    import sys
    import doctest

    failed, tested = doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    if not failed == 0:
        sys.exit(0)

    # Determine if we are working online (on the Raspberry Pi) or offline on Windows
    online = False
    if sys.platform == "linux":
        online = True

    # if online:
    #     inquire("local")
    # else:
    #     clear_debug_window()
    #     parse_inq(records_sample_data, "local")

    if online:
        name = adapter_name()
        print(f"Name = {name}")
        ret = adapter_class()
        print(f"Adapter class: {ret}")
