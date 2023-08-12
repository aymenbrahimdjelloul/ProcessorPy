"""

@author : Aymen Brahim Djelloul
version : 0.0.1
date : 04.08.2023
license : MIT


sources :
    https://community.spiceworks.com/how_to/170332-how-to-get-cpu-information-in-windows-powershell
    https://xkln.net/blog/analyzing-cpu-usage-with-powershell-wmi-and-excel/

"""

# IMPORTS
import sys
import subprocess
import platform
from threading import Thread
from __ProcessorPy_core import ProcessorPyCore, ProcessorPyResult, SensorsResult


class Processor(ProcessorPyCore):

    def __init__(self):
        super(Processor, self).__init__(self)

        # Get powershell path
        self.__powershell_path = "C:\\Windows\\System32\\WindowsPowershell\\v1.0\\powershell.exe"

    @property
    def name(self) -> str | None:
        """ This method will return the cpu model name"""
        return self.__get_win32_procesor_info("Name")

    @property
    def manufacturer(self) -> str | None:
        """ This method will return the cpu manufacturer name"""
        return self.__get_win32_procesor_info("Manufacturer")

    @property
    def architecture(self) -> str:
        """ This method will return the cpu arch"""
        return platform.machine()

    @property
    def family(self) -> str | None:
        """ This method will return the cpu family value"""
        return self.__get_win32_procesor_info("Family")

    def stepping(self) -> str:
        """ This method will return the cpu stepping value"""
        return self.__get_win32_procesor_info("Stepping")

    def socket(self):
        """ This method will return the cpu socket"""
        return self.__get_win32_procesor_info("SocketDesignation")

    def l2_cache_size(self, friendly_format: bool = True) -> str | int | None:
        """ This method will return the level 2 cpu cache size"""

        return int(self.__get_win32_procesor_info("L2CacheSize")) if not friendly_format else \
            self._ProcessorPyCore__kilobytes_to_megabytes(int(self.__get_win32_procesor_info("L2CacheSize")))

    def l3_cache_size(self, friendly_format: bool = True) -> str | int | None:
        """ This method will return the level 3 cpu cache size"""

        return int(self.__get_win32_procesor_info("L3CacheSize")) if not friendly_format else \
            f'{self._ProcessorPyCore__kilobytes_to_megabytes(int(self.__get_win32_procesor_info("L3CacheSize")))} Mb'

    def max_clock_speed(self, friendly_format: bool = True) -> str | int | None:
        """ This method will return the maximum cpu clock speed"""

        return int(self.__get_win32_procesor_info("MaxClockSpeed")) if not friendly_format else \
            f'{self.ProcessorPyCore__megahertz_to_gigahertz(int(self.__get_win32_procesor_info("MaxClockSpeed")))} Mb'

    # def is_turbo_boosted(self) -> bool | None:
    #     """ This method will determine if the cpu is turbo boosted feature"""

    def is_support_virtualization(self) -> bool | None:
        """ This method will return if the cpu support virtualization technology or not"""
        return True if self.__get_win32_procesor_info("VirtualizationFirmwareEnabled") == " True" else False

    def core_count(self, logical: bool = False) -> int:
        """ This method will return the cpu cores and treads count number"""

        return self.__get_win32_procesor_info("ThreadCount") if logical else \
            int(self.__get_win32_procesor_info("NumberOfCores"))

    def __get_win32_procesor_info(self, query: str) -> str | None:
        """ This method will make a command in powershell to get the cpu info"""

        _process_output = subprocess.check_output([self.__powershell_path, "Get-WmiObject", "-Class", "Win32_Processor",
                                                   "-ComputerName.", "|", "Select-Object", "-Property", query],
                                                  text=True).split()
        # Remove query from output
        _process_output.remove(query)
        return ' '.join(_process_output).strip('-') if len(_process_output) > 1 else None


class Sensors(ProcessorPyCore):
    __max_clock_speed: int

    def __init__(self):
        super(Sensors, self).__init__()

        # Get powershell path
        self.__powershell_path = "C:\\Windows\\System32\\WindowsPowershell\\v1.0\\powershell.exe"
        # Create Processor object
        self.__cpu = Processor()

        # Get cpu max clock speed to use it to get cpu current clock speed
        # Use multithreading to make it fast
        thread1 = Thread(target=self.__get_max_clock_speed)
        thread1.start()

    def get_cpu_clock_speed(self) -> float | None:
        """ This method will return th current cpu clock speed"""

        cpu_load_percentage = float(
            subprocess.check_output([self.__powershell_path, 'Get-Counter', '-Counter', '"\Processor',
                                     'Information(_Total)\%', 'Processor', 'Performance"'], text=False).split()[-1])

        # print(cpu_load_percentage * self.__max_clock_speed / 100.0)
        return round(cpu_load_percentage * self.__max_clock_speed / 100.0, 2)

    def get_cpu_usage(self, per_core: bool = True) -> int | ProcessorPyResult | None:
        """ This method will return the current cpu load percentage"""

        # Define cpu usage variable
        cpu_usage: int | ProcessorPyResult = 0

        # Get process output
        _process_output = subprocess.check_output([self.__powershell_path, 'Get-CimInstance', '-Query', '"select',
                                                   'Name,', 'PercentProcessorTime', 'from',
                                                   'Win32_PerfFormattedData_PerfOS_Processor"', '|', 'Select',
                                                   'Name,',
                                                   'PercentProcessorTime'], text=True).replace('-', '').split()

        # Remove unwanted items
        _process_output.remove("Name")
        _process_output.remove("PercentProcessorTime")

        if per_core:
            # THIS SECTION WILL GET THE CPU USAGE PERCENTAGE FOR EACH CORE

            # Get cores usage percentage in tuple
            core_usage_percentage = []
            value_gotten = False
            for _ in _process_output:

                if _ == "_Total":
                    core_usage_percentage.append(_process_output[_process_output.index('_Total') + 1])
                    break

                if value_gotten:
                    value_gotten = False
                    continue

                elif not value_gotten:
                    core_usage_percentage.append(_process_output[_process_output.index(_) + 1])
                    value_gotten = True

            # Set result to the SensorsResult class
            cpu_usage = SensorsResult(tuple(x for x in core_usage_percentage))

            # Clear memory
            del core_usage_percentage, value_gotten, _, _process_output

        elif not per_core:
            # THIS SECTION WILL GET THE TOTAL CPU USAGE
            cpu_usage = int(_process_output[-1])

            # Clear memory
            del _process_output

        # Return result
        return cpu_usage

    def get_cpu_voltage(self, friendly_format: bool = True) -> int | str | None:
        """ This method will return the cpu voltage value"""

        # Get voltage using WMIC API
        _process_output = subprocess.check_output(["WMIC", "CPU", "GET", "CurrentVoltage"],
                                                  text=True).split()

        _process_output.remove("CurrentVoltage")
        if len(_process_output) < 0:
            return None

        return self.__adjust_voltage_string(int(_process_output[0])) if friendly_format else int(_process_output[0])

    @staticmethod
    def __adjust_voltage_string(value: int) -> str:
        """ This method will adjust the voltage value and return it as friendly format"""
        return f"{value / 10.0}v"

    def __get_max_clock_speed(self):
        """ This method will return the cpu max clock speed"""
        self.__max_clock_speed = int(subprocess.check_output(["WMIC", "CPU", "GET", "MaxClockSpeed"],
                                                             text=True).split()[-1])


if __name__ == "__main__":
    sys.exit()
