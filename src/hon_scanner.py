##
# @file: hon_scanner.py
# @brief: Honeywell BT scanner receiver and tests

"""Honeywell BT scanner receiver and tests
"""
# global imports
import bluetooth

# local imports
from command import run_command
from btcommon import init_bluetooth, is_serial_service_running, add_serial_port
import btcommon


# -----------------------------------------------------------------------------
def cmd_revinf():
    """Create a HON scanner REVINF command.

    :returns: The string with the REVINF command

    Note: '\x16' is <SYN>
    """

    s = b'\x16M\rREVINF.'
    return s


# -----------------------------------------------------------------------------
def hon_send_cmd(sock, cmd):
    """Send the given HON scanner command to the open socket
    """

    if not len(cmd) == 6:
        print("Problem in length of {cmd}. Must be 6")
        return

    # Send a REVINF. command to learn the details of this scanner
    cmdstring = f"\x16M\r{cmd}."
    # print(f"Sending command {repr(cmdstring)}")
    sock.send(cmdstring)

    while True:
        response = sock.recv(1024)
        # print(f'{cmd} Response: {repr(response)}')
        lines = response.splitlines()
        for s in lines:
            print(s)

        # Wait for ack/nak/problem response
        ack = sock.recv(1024)
        # print(f"ACK: {repr(ack)}")
        print()
        if b'\x06' in ack:
            print("All OK")
            break
        if b'\x05' in ack:
            print("Invalid Tag or Subtag")
            break
        if b'\x15' in ack:
            print("Command was good, but problem detected")
            break


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

    # # Send a REVINF. command to learn the details of this scanner
    # cmd = cmd_revinf()
    # print(f"Sending command {repr(cmd)}")
    # client_sock.send(cmd)
    # response = client_sock.recv(1024)
    # print('REVINF Response:')
    # # print(repr(response))
    # lines = response.splitlines()
    # for s in lines:
    #     print(s)
    # ack = client_sock.recv(1024)
    # print(f"ACK: {repr(ack)}")
    # print()
    hon_send_cmd(client_sock, "REVINF")

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
