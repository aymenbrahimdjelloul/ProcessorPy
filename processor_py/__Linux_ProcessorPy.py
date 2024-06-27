"""
@author : Aymen Brahim Djelloul
version : 1.0
date : 05.08.2023
license : MIT


sources :
    - https://www.tecmint.com/check-linux-cpu-information/
    - https://www.javatpoint.com/linux-top
    - https://www.geeksforgeeks.org/top-command-in-linux-with-examples/


"""
# IMPORTS
import re
import os.path
import time
import subprocess
from __ProcessorPy_core import ProcessorPyCore, sys, cpu_count, ceil
from exceptions import SystemDriverDoesntError


class Processor(ProcessorPyCore):

    def __init__(self):
        super(Processor, self).__init__(self)

        # make lscpu result in text file
        lscpu_file_path: str = f"{os.getcwd()}/lscpu_report.txt"
        os.system(f"lscpu > {lscpu_file_path}")

        # Check if files are present
        if not os.path.exists(lscpu_file_path):
            raise SystemDriverDoesntError("lscpu")

        # Read the 'cpuinfo' file
        self.__lscpu_info = open(lscpu_file_path, 'r').read()

        # Delete lscpu result text file
        subprocess.run(["rm", lscpu_file_path])

    @property
    def name(self) -> str:
        """ This method will return the cpu model name"""
        return self.__get_text_info(r"Model name:")

    @property
    def manufacturer(self) -> str:
        """ This method will return the cpu manufacturer name"""
        return self.__get_text_info(r"Vendor ID:")

    @property
    def architecture(self) -> str:
        """ This method will return the cpu arch"""
        return self.__get_text_info(r"Architecture:")

    @property
    def family(self) -> str | None:
        """ This method will return the cpu family value"""
        return self.__get_text_info(r"CPU family:")

    # @property
    # def model(self) -> str | None:
    #     """ This method will return the cpu model value"""
    #     return self.__get_text_info(r"Model:")

    def stepping(self) -> str | None:
        """ This method will return the cpu stepping value"""
        return self.__get_text_info(r"Stepping:")

    def socket(self) -> str | None:
        """ This method will return the cpu socket"""
        return None    # This method isnt maintined yed it will be updated later
    
    @property
    def flags(self) -> list | None:
        """ This method will return the cpu flags"""
        return self.__get_text_info(r"Flags:").split()

    def l1_cache_size(self, friendly_format: bool = True) -> int | str | None:
        """ This method will return the level 1 cpu cache size"""
        return self.__get_text_info(r"L1d cache:") if friendly_format else \
            self._ProcessorPyCore__kilobytes_to_bytes(
                self.__get_text_info(r"L1d cache:").split()[0])

    def l2_cache_size(self, friendly_format: bool = True) -> int | str | None:
        """ This method will return the level 2 cpu cache size"""
        return self.__get_text_info(r"L2 cache:") if friendly_format else \
            self._ProcessorPyCore__kilobytes_to_bytes(
                self.__get_text_info(r"L2 cache:").split()[0])

    def l3_cache_size(self, friendly_format: bool = True) -> int | str | None:
        """ This method will return the level 3 cpu cache size"""
        return self.__get_text_info(r"L3 cache:") if friendly_format else \
            self._ProcessorPyCore__kilobytes_to_bytes(
                self.__get_text_info(r"L3 cache:").split()[0])

    def max_clock_speed(self) -> str | None:
        """ This method will return the maximum cpu clock speed"""

        if self.__get_text_info(r"CPU MHz:") is None:

            try:
                # Execute the command and get the output
                output = subprocess.check_output("cat /proc/cpuinfo | grep 'cpu MHz'", shell=True, text=True)
                
                # Extract the maximum clock speed from the output
                max_speed = 0.0
                for line in output.split('\n'):
                    if "cpu MHz" in line:
                        speed = float(line.split(':')[-1].strip())
                        if speed > max_speed:
                            max_speed = speed
                return max_speed if max_speed > 0 else None
            except subprocess.CalledProcessError as e:
                return None

    # def is_turbo_boosted(self) -> bool | None:
    #     """ This method will determine if the cpu is turbo boosted feature"""

    def is_support_virtualization(self) -> bool:
        """ This method will return if the cpu support virtualization technology or not"""

        # Define hypervisors flags for each cpu manufacturer
        virtualization_detect_patterns = {
            "AMD": {
                "flag": "hypervisor",
                "virtualization": "AMD-V"
            },

            "Intel": {
                "flag": "",
                "virtualization": ""
            },

            "ARM": {
                "flag": None,
                "virtualization": None
            }

        }

        # Figure out the cpu manufacturer
        search_match = re.search(r"Intel|AMD", self.manufacturer)

        cpu_manufacturer = search_match.group()

        # Check the virtualization type
        if self.__get_text_info(r"Virtualization type:") == "full":
            # Clear memory
            del virtualization_detect_patterns, search_match, cpu_manufacturer

            return True

        # Check if there is a hypervisor vendor column
        if self.__get_text_info(r"Hypervisor vendor:"):
            # Clear memory
            del virtualization_detect_patterns, search_match, cpu_manufacturer

            return True

        # Check for virtualization column
        if (self.__get_text_info(r"Virtualization:") ==
                virtualization_detect_patterns[cpu_manufacturer]["virtualization"]):
            # Clear memory
            del virtualization_detect_patterns, search_match, cpu_manufacturer

            return True

        # Check if the virtualization flag exists in flag list
        if virtualization_detect_patterns[cpu_manufacturer]["flag"] in self.flags:
            # Clear memory
            del virtualization_detect_patterns, search_match, cpu_manufacturer

            return True

        # Clear memory
        del virtualization_detect_patterns, search_match, cpu_manufacturer

        # Return false if no of previous checks is True
        return False

    def core_count(self, logical: bool = False) -> int | None:

        if logical:
            # Get number of threads per core
            thread_per_core = self.__get_text_info(search_pattern=r"^Thread\(s\)\s+per\s+core:\s+(\d+)",
                                                   pattern_text=r"Thread\(s\)s+per\s+core:",
                                                   re_search_method=re.MULTILINE)

            # Get the thread per core number
            thread_per_core = [char for char in thread_per_core if char.isdigit()]
            # Return the all threads count
            return int(''.join(thread_per_core)) * cpu_count() if thread_per_core is not None else None

        elif not logical:
            return cpu_count()

    def __get_text_info(self, search_pattern: str,
                        file: str = None,
                        pattern_text: str = None,
                        re_search_method: re.RegexFlag = re.IGNORECASE,
                        text_clear: bool = True) -> str | None:
        """ This method will search through the given file using a search pattern and return the extracted info """

        # Define empty variable to store extracted text
        text: str = ""

        # Check file parameter
        if file is None:
            file = self.__lscpu_info

        # Search through the file using search patterns
        search_match = re.search(search_pattern, file, re_search_method)
        if search_match:

            # Get the line searched column
            start_index = search_match.start()

            for char in file[start_index:start_index + 500]:

                if char == "\n":
                    break

                text = text + char

            # Clear extracted text from search pattern
            if text_clear:
                if pattern_text is None:
                    pattern_text = search_pattern

                text = re.sub(pattern_text, "", text)

            # Clear memory
            del start_index, char, file, search_match, text_clear, pattern_text

        return text.lstrip(" ") if text != "" else None


class Sensors(ProcessorPyCore):

    def __init__(self):
        super(Sensors, self).__init__(self)

        # Define the max clock speed
        self.__max_clock_speed = float(Processor().max_clock_speed())

    def get_cpu_clock_speed(self) -> float | None:
        """ This method will return th current cpu clock speed"""
        current_cpu_percent = self.get_cpu_usage()
        return (current_cpu_percent / 100.0) * self.__max_clock_speed if current_cpu_percent is not None else None

    @staticmethod
    def get_cpu_usage() -> float | None:
        """ This method will return the current cpu load percentage"""

        try:
            # Run top command and capture output
            output = subprocess.check_output(['top', '-bn', '1'], universal_newlines=True)

            # Extract CPU usage from the output using regular expressions
            cpu_usage_match = re.search(r'%Cpu\(s\):\s+(\d+\.\d+)\s+us', output)

            if cpu_usage_match:
                return ceil(float(cpu_usage_match.group(1)))

            else:
                return None

        except subprocess.CalledProcessError:
            return None

    def get_cpu_voltage(self, friendly_format: bool = True) -> int | str | None:
        """ This method will return the cpu voltage value"""
        return None     # This method is not maintained, yet it will be updated in recent versions


if __name__ == "__main__":
    sys.exit()
