#!/usr/bin/env python3

"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 1.1
date : 26.05.2025
license : MIT


"""

# IMPORTS
import sys
import os
import ctypes
import platform
import time
import random

from processorpy._utils import CacheHandler, OnlineSearcher


class Const:

    # Command-line commands
    WMIC_COMMAND: str = "wmic cpu get"


class Processor(Const):

    def __init__(self, developer_mode: bool = False,
                 use_cache: bool = True,
                 use_searching: bool = True) -> None:

        super().__init__()

        # Define constants
        self.dev_mode = developer_mode
        self.use_cache = use_cache
        self.use_searching = use_searching

        # Create cache and Online search object
        self.cache_handler = CacheHandler()
        self.online_search = OnlineSearcher()

        # Check if there is cache
        if self.cache_handler.is_cache:
            pass

    @property
    def name(self) -> str:
        """ This method will get the cpu name string"""
        return "Intel Core I9"

    @property
    def manufacturer(self) -> str:
        """ This method will get the manufacturer string"""
        return ""

    @property
    def architecture(self) -> str:
        """ This method will get the architecture string"""
        return ""

    @property
    def family(self) -> str:
        """ This method will get the family string"""
        return ""

    @property
    def stepping(self) -> str:
        """ This method will get the cpu stepping string"""
        return ""

    @property
    def socket(self) -> str:
        """ This method will get the cpu socket string"""
        return ""

    def get_l1_cache_size(self, friendly: bool = False) -> int | str:
        """ This method will get the l1 cache size in bytes and friendly format"""

    def get_l2_cache_size(self, friendly: bool = False) -> int | str:
        """ This method will get the l2 cache size in bytes and friendly format"""

    def get_l3_cache_size(self, friendly: bool = False) -> int | str:
        """ This method will get the l3 cache size in bytes and friendly format"""

    def get_max_clock(self, friendly: bool = False) -> int | str:
        """ This method will get the max clock speed in bytes and friendly format"""

    def get_cores(self, logical: bool = False) -> int:
        """ This method will get the number of cores and threads"""

    def flags(self) -> tuple[str]:
        """ This method will get the cpu flags supported"""

    def get_all_info(self) -> dict:
        """ This method will collect all cpu info """
        time.sleep(3)
        return {
            "name": self.name,
            "Manufacturer": self.manufacturer,
            "Architecture": self.architecture,
            "Family": self.family,
            "Stepping": self.stepping,
            "Socket": self.socket,
            "L1 Cache": self.get_l1_cache_size(friendly=True),
            "L2 Cache": self.get_l2_cache_size(friendly=True),
            "L3 Cache": self.get_l3_cache_size(friendly=True),
            "Max clock speed": self.get_max_clock(friendly=True),
            "Cores": self.get_cores(),
            "Threads": self.get_cores(logical=True),
        }



class Sensors(Const):

    def __init__(self) -> None:
        super().__init__()


    def get_clock_speed(self, friendly: bool = False) -> float | str:
        """ This method will get the cpu current clock speed"""
        return random.uniform(3.8, 5.1)

    def get_cpu_voltage(self, friendly: bool = False) -> float | str:
        """ This method will get the cpu voltage string """
        return random.uniform(1.15, 1.35)

    def get_cpu_temperature(self, friendly: bool = False) -> float | str:
        """ This method will get the cpu temperature string """
        return random.randint(45, 75)

    def get_cpu_usage(self, per_core: bool = False) -> int | tuple:
        """ This method will get the cpu usage percentage string """
        return random.randint(20, 80)


class AdvancedProcessor:
    pass


def __main__() -> None:
    """ This is main function will print all values"""


if __name__ == "__main__":
    main()
