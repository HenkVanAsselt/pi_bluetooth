"""Run a command on the Linux server"""

import sys
from shlex import split
# global imports
from subprocess import Popen, PIPE, STDOUT


# -----------------------------------------------------------------------------
def run_command(cmd, sudo=False, timeout=0, verbose=False) -> str:
    """

    :param cmd: The command string or list of commands to use
    :param sudo: Add 'sudo' command if this is set to True
    :param timeout: A process timeout in seconds for commands which never end, like 'hcitool -i hci0 lescan'
    :param verbose: Show intermediate (debug) results

    If a timeout value is given, it will prepend the command with 'sudo timeout -s SIGINT {timeout}s '
    """

    if not sys.platform == 'linux':
        print(f"ERROR: Command \"{cmd}\" is for Linux systems only...")
        return ""


    if isinstance(cmd, list):
        # Convert list to string
        cmd = ' '.join(cmd)
    else:
        # This was already a string
        pass

    ret = ""

    try:

        if timeout:
            cmd = f"sudo timeout -s SIGINT {timeout}s {cmd}"

        if sudo and "sudo" not in cmd:
            cmd = f"sudo {cmd}"

        if verbose:
            print(f'cmd={cmd}')

        cmdlist = split(cmd)
        if verbose:
            print(f"cmdlist={cmdlist}")

        if timeout:
            timeout_str = f"sudo timeout -s SIGINT {timeout}s"

        process = Popen(cmdlist, stdout=PIPE, stderr=STDOUT, encoding="utf8")
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                if verbose:
                    print("=== end of output ===")
                break
            if output:
                if verbose:
                    print(f">>> {output.strip()}")
                ret += output
        _rc = process.poll()
        # return _rc
        return ret.strip()
    except KeyboardInterrupt:
        # process.terminate()
        return ret.strip()
    except Exception as ex:
        print("Encountered exception: ", ex)
        return ret.strip()


# =============================================================================
if __name__ == '__main__':
    pass
