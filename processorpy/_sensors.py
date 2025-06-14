"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.


@author : Aymen Brahim Djelloul
version : 0.1
date : 12.06.2025
license : MIT License

"""

# IMPORTS
import sys
import platform
from abc import ABC, abstractmethod


# Declare platform string
_platform: str = platform.system()


class _Sensors(ABC):

    @abstractmethod
    def get_temperature(self) -> float:
        """ This method will simulate the temperature sensor readings"""
        return random.randint(45, 75)

    @abstractmethod
    def get_voltage(self) -> float:
        """ This method will simulate the voltage sensor readings"""
        return random.uniform(1.15, 1.35)

    @abstractmethod
    def get_usage(self, per_core: bool = False) -> int | tuple:
        """ This method will simulate the usage sensor readings per core"""
        return random.randint(20, 80)

    @abstractmethod
    def get_clock_speed(self, per_core: bool = False) -> int | tuple:
        """ This method will simulate the clock speed sensor readings per core"""
        return random.uniform(3.8, 5.1)

if _platform == "Windows":

    class Sensors:
        pass



if __name__ == "__main__":
    sys.exit(0)
