##
# @file: bt_discoverable_on.py
# @brief: Make this device discoverable

"""Make this device discoverable
"""

# global imports
import sys

# local imports
from command import run_command

ret = run_command("bt-adapter --set Discoverable 1")
print(ret)
