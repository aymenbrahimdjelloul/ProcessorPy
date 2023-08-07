"""
@author : Aymen Brahim Djelloul
version : 0.0.1
date : 05.08.2023
license : MIT


"""

# IMPORTS
import sys
from __ProcessorPy_core import ProcessorPyCore
from exceptions import *


class Processor(ProcessorPyCore):

    def __init__(self):
        super(Processor, self).__init__()

    def name(self) -> str:
        """ This method will return the cpu model name"""

    def manufacturer(self) -> str:
        """ This method will return the cpu manufacturer name"""

    def architecture(self):
        """ This method will return the cpu arch"""

    def family(self):
        """ This method will return the cpu family value"""

    def model(self):
        """ This method will return the cpu model value"""

    def stepping(self):
        """ This method will return the cpu stepping value"""

    def socket(self):
        """ This method will return the cpu socket"""

    def code_name(self):
        """ This method will return the cpu code name"""

    def l1_cache_size(self):
        """ This method will return the level 1 cpu cache size"""

    def l2_cache_size(self):
        """ This method will return the level 2 cpu cache size"""

    def l3_cache_size(self):
        """ This method will return the level 3 cpu cache size"""

    def min_clock_speed(self):
        """ This method will return the minimum cpu clock speed"""

    def max_clock_speed(self):
        """ This method will return the maximum cpu clock speed"""

    def is_boosted(self):
        """ This method will return if the has boost clock or not"""

    def is_virtualized(self):
        """ This method will return if the cpu support virtualization technology or not"""

    @staticmethod
    def core_count(logical: bool = False):
        """ This method will return the cpu cores and treads count number"""


class Sensors(ProcessorPyCore):

    def __init__(self):
        super(Sensors, self).__init__()

    def get_current_clock_speed(self, in_gigahertz: bool = True):
        """ This method will return th current cpu clock speed"""

    def get_current_load(self):
        """ This method will return the current cpu load percentage"""

    def get_voltage(self):
        """ This method will return the cpu voltage value"""


if __name__ == "__main__":
    sys.exit()
