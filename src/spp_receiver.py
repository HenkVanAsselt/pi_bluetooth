# global imports
import bluetooth

# local imports
from command import run_command
from btcommon import init_bluetooth, is_serial_service_running, add_serial_port
import btcommon


# =============================================================================
def main():

    # commands = [
    #     "sudo rfkill unblock all",
    #     # "sudo bluetoothctl power off",
    #     "sudo bluetoothctl power on",
    #     "sudo bluetoothctl agent NoInputNoOutput",
    #     "sudo bluetoothctl discoverable yes",
    #     "sudo bluetoothctl pairable yes",
    # ]
    #
    # for cmd in commands:
    #     ret = run_command(cmd)
    #     print(f"cmd = {cmd}, ret='{ret}'")

    init_bluetooth()

    # Check if serial port service is already running
    port = 1
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
