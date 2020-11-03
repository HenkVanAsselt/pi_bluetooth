##
# @file: py_hciconfig.py
# @brief: Python hciconfig wrapper

"""Python hciconfig wrapper
"""
# local imports
from command import run_command


# -----------------------------------------------------------------------------
def hciconfig():
    """Run the hciconfig command"""
    s = run_command("hciconfig")
    return s


# -----------------------------------------------------------------------------
def main():
    ret = hciconfig()
    print(ret)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
