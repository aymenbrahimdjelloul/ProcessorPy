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
import subprocess
from abc import ABC, abstractmethod
from ._core import Const
from typing import Union, Optional, List, Tuple


try:

    import ctypes
    import winreg

except ImportError:
    pass

class _Sensors(ABC):
    """Abstract base class for system sensor monitoring.

    This class defines the interface for retrieving various system sensor readings
    like CPU clock speed, voltage, temperature, and usage statistics.
    """

    @abstractmethod
    def get_clock_speed(self, friendly: bool = False) -> Union[float, str]:
        """Get the current CPU clock speed.

        Args:
            friendly: If True, returns a human-readable string with units.
                     If False, returns speed in MHz/GHz as float.

        Returns:
            float: Clock speed in MHz/GHz when friendly=False
            str: Formatted string (e.g., "3.5 GHz") when friendly=True
        """
        pass

    @abstractmethod
    def get_cpu_voltage(self, friendly: bool = False) -> Union[float, str]:
        """Get the current CPU voltage.

        Args:
            friendly: If True, returns a human-readable string with units.
                     If False, returns voltage as float.

        Returns:
            float: Voltage in volts when friendly=False
            str: Formatted string (e.g., "1.2V") when friendly=True
        """
        pass

    @abstractmethod
    def get_cpu_temperature(self,
                            friendly: bool = False,
                            sensor_id: Optional[int] = None) -> Union[float, str, List[Union[float, str]]]:
        """Get CPU temperature reading(s).

        Args:
            friendly: If True, returns a human-readable string with units.
                     If False, returns temperature as float.
            sensor_id: Specific sensor to query. If None, returns all sensors.

        Returns:
            float: Temperature in Celsius when friendly=False and sensor_id specified
            str: Formatted string (e.g., "45°C") when friendly=True and sensor_id specified
            List: All sensor readings when sensor_id=None
        """
        pass

    @abstractmethod
    def get_cpu_usage(self,
                      per_core: bool = False,
                      interval: float = 0.1) -> Union[float, Tuple[float, ...]]:
        """Get CPU usage percentage.

        Args:
            per_core: If True, returns usage for each core.
                     If False, returns aggregate usage.
            interval: Measurement interval in seconds.

        Returns:
            float: Aggregate CPU usage (0-100%) when per_core=False
            Tuple: Per-core usage percentages when per_core=True
        """
        pass

if Const.platform == "win32":

    class Sensors(_Sensors):

        def __init__(self):
            super().__init__()

        def get_clock_speed(self, friendly: bool = False) -> Union[float, str]:
            """Get the current CPU clock speed.

            Args:
                friendly: If True, returns a human-readable string with units.
                         If False, returns speed in MHz/GHz as float.

            Returns:
                float: Clock speed in MHz/GHz when friendly=False
                str: Formatted string (e.g., "3.5 GHz") when friendly=True
            """
            pass

        def get_cpu_voltage(self, friendly: bool = False) -> Union[float, str]:
            """Get the current CPU voltage.

            Args:
                friendly: If True, returns a human-readable string with units.
                         If False, returns voltage as float.

            Returns:
                float: Voltage in volts when friendly=False
                str: Formatted string (e.g., "1.2V") when friendly=True
            """
            pass

        def get_cpu_temperature(self,
                                friendly: bool = False,
                                sensor_id: Optional[int] = None) -> Union[float, str, List[Union[float, str]]]:
            """Get CPU temperature reading(s).

            Args:
                friendly: If True, returns a human-readable string with units.
                         If False, returns temperature as float.
                sensor_id: Specific sensor to query. If None, returns all sensors.

            Returns:
                float: Temperature in Celsius when friendly=False and sensor_id specified
                str: Formatted string (e.g., "45°C") when friendly=True and sensor_id specified
                List: All sensor readings when sensor_id=None
            """
            pass

        def get_cpu_usage(self,
                          per_core: bool = False,
                          interval: float = 0.1) -> Union[float, Tuple[float, ...]]:
            """Get CPU usage percentage.

            Args:
                per_core: If True, returns usage for each core.
                         If False, returns aggregate usage.
                interval: Measurement interval in seconds.

            Returns:
                float: Aggregate CPU usage (0-100%) when per_core=False
                Tuple: Per-core usage percentages when per_core=True
            """
            pass

elif Const.platform == "linux":

    class Sensors(_Sensors):

        def __init__(self) -> None:
            super().__init__()


if __name__ == "__main__":
    sys.exit(0)
