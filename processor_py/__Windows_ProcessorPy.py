"""

@author : Aymen Brahim Djelloul
version : 1.0
date : 04.08.2023
license : MIT


sources :
    - https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-counter?view=powershell-7.3
    - https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-processor
    - https://community.spiceworks.com/how_to/170332-how-to-get-cpu-information-in-windows-powershell
    - https://xkln.net/blog/analyzing-cpu-usage-with-powershell-wmi-and-excel/

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

    @property
    def socket(self):
        """ This method will return the cpu socket"""
        return self.__get_win32_procesor_info("SocketDesignation")

    @property
    def flags(self) -> list | None:
        """ This method will return the cpu flags"""
        return None    # This method isn't maintained yet it will be updated later

    def l1_cache_size(self, fiendly_format: bool = True) -> str | int | None:
        """ This method will return the level 1 cpu cache size"""
        return None    # This method isn't maintained yet it will be updated later
    
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

        try:
            # Run the command to get CPU information
            output = subprocess.check_output("wmic cpu get CurrentClockSpeed /value", shell=True).decode()

            # Process the output to extract the clock speed value
            for line in output.splitlines():

                if line.startswith("CurrentClockSpeed"):
                    # Extract the value after the '=' sign
                    return int(line.split('=')[1].strip()) if not friendly_format else \
                        f'{self._ProcessorPyCore__megahertz_to_gigahertz(int(line.split('=')[1].strip()))} Ghz'

        except subprocess.SubprocessError:
            return None
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
        super(Sensors, self).__init__(Processor)

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

    def get_cpu_usage(self, per_core: bool = False) -> int | ProcessorPyResult | None:
        """ This method will return the current cpu load percentage"""

        if per_core:

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
            # return the result
            return cpu_usage

        elif not per_core:

            # Take the initial reading
            prev_idle, prev_total = self.__get_cpu_times()

            # Sleep for the specified interval
            sleep(0.1)

            # Take the second reading
            idle, total = self.__get_cpu_times()

            # Calculate the CPU usage
            idle_delta = idle - prev_idle
            total_delta = total - prev_total

            if total_delta == 0:
                return 0

            cpu_usage = int(100 * (1 - (idle_delta / total_delta)))
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

    @staticmethod
    def __get_cpu_times():
        idle_time = ctypes.c_ulonglong()
        kernel_time = ctypes.c_ulonglong()
        user_time = ctypes.c_ulonglong()

        if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time)
        ):
            raise Exception("Failed to get system times")

        return idle_time.value, kernel_time.value + user_time.value


if __name__ == "__main__":
    sys.exit()
