##
# @file: hon_scanner.py
# @brief: Honeywell BT scanner receiver and tests

"""Honeywell BT scanner receiver and tests
"""
# global imports
import bluetooth
import time

# local imports
from btcommon import init_bluetooth, is_serial_service_running, add_serial_port
import btcommon


# -----------------------------------------------------------------------------
def hon_send_cmd(sock, cmd):
    """Send the given HON scanner command to the open socket.

    :param sock: The open socket
    :param cmd: The command string to send
    """

    cmdstring = f"\x16M\r{cmd}."
    bcmd = bytes(cmd, 'utf-8')
    # print(f"Sending command {repr(cmdstring)}")
    sock.send(cmdstring)

    response = sock.recv(1024)
    print(f'{cmd} Response: {repr(response)}')
    lines = response.splitlines()
    for s in lines:
        print(s)
        if bcmd in s and b'\x06' in s:
            print("All OK")
            break
        if bcmd in s and b'\x05' in s:
            print("Invalid Tag or Subtag")
            break
        if bcmd in s and b'\x15' in s:
            print("Command was good, but problem detected")
            break


# -----------------------------------------------------------------------------
def hon_scanner_report(sock):
    """Scanner Report.

    :param sock: The open socket
    """

    hon_send_cmd(sock, cmd="RPTSCN.")


# -----------------------------------------------------------------------------
def hon_scanner_addr(sock):
    """Scanner BT Address

    :param sock: The open socket
    """

    hon_send_cmd(sock, cmd="BT_LDA.")


# -----------------------------------------------------------------------------
def hon_base_addr(sock):
    """Scanner Base Address (can be a BT Accesspoint).

    :param sock: The open socket
    """

    hon_send_cmd(sock, cmd=":*:BASLDA.")


# -----------------------------------------------------------------------------
def hon_dataformat_settings(sock):
    """Scanner Data Format Settings

    :param sock: The open socket
    """

    hon_send_cmd(sock, cmd="DFMBK3?.")


# -----------------------------------------------------------------------------
def hon_test_menu_on(sock):
    """Test Menu On.

    When Test Menu is On, scanning a programming barcode will display the
    contents of that programming code. The programming function will still occur,
    but in addition, the content of that programming code is output to the terminal.

    :param sock: The open socket
    """

    hon_send_cmd(sock, cmd="TSTMNU1.")


# -----------------------------------------------------------------------------
def hon_test_menu_off(sock):
    """ Test Menu off

    When Test Menu is On, scanning a programming barcode will display the
    contents of that programming code. The programming function will still occur,
    but in addition, the content of that programming code is output to the terminal.

    :param sock: The open socket
    """

    hon_send_cmd(sock, cmd="TSTMNU0.")


# =============================================================================
def main():

    # Check if serial port service is already running
    port = 1

    if sys.platform == "linux":
        init_bluetooth()
        if not is_serial_service_running(verbose=True):
            add_serial_port(port, verbose=True)

    # Intialize the RFCOMM listener
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", port))
    server_sock.listen(1)
    print(f"\nBT SPP receiver, listening on port {port}")

    # Wait for incoming connection
    client_sock, address = server_sock.accept()
    print("Accepted connection from ", address)

    # Send a REVINF. command to learn the details of this scanner
    hon_send_cmd(client_sock, "REVINF")

    # Just for fun, make the scanner beep 3 times.
    hon_send_cmd(client_sock, "BEPEXE1")
    time.sleep(0.25)
    hon_send_cmd(client_sock, "BEPEXE1")
    time.sleep(0.25)
    hon_send_cmd(client_sock, "BEPEXE1")

    # Handle the incoming bt serial data
    while True:
        try:
            recvdata = client_sock.recv(1024)
            print(f"Received {recvdata}")

            if btcommon.is_honeywell_scanner_msg(recvdata):
                msg = btcommon.strip_honeywell_header(recvdata)
                print(f"HON Scanner data: {msg}")
            else:
                client_sock.send(f"Echoing back {recvdata}")
                
            if recvdata == b"Q\r\n":
                print("Exiting this connection")
                client_sock.close()
                continue

        except bluetooth.btcommon.BluetoothError as e:
            print(repr(e))
            client_sock, address = server_sock.accept()
            print("New connection accepted from ", address)

    client_sock.close()
    server_sock.close()


# =============================================================================
if __name__ == '__main__':

    import sys
    import doctest

    failed, tested = doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    if not failed == 0:
        sys.exit(0)

    main()
