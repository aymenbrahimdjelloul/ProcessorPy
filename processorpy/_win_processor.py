#!/usr/bin/env python3

"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 0.1
date : 29.05.2025
license : MIT

"""

import ctypes
import ctypes.wintypes
import platform
import subprocess
import random
from ._utils import *
from typing import Dict, List, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import winreg
import re


class CPUVendor(Enum):
    INTEL = "Intel"
    AMD = "AMD"
    ARM = "ARM"
    QUALCOMM = "Qualcomm"
    VIA = "VIA"
    UNKNOWN = "Unknown"


class CacheType(Enum):
    DATA = "Data"
    INSTRUCTION = "Instruction"
    UNIFIED = "Unified"


@dataclass
class CPUCache:
    level: int
    size_bytes: int
    associativity: int
    line_size: int
    cache_type: str
    shared_cores: int = 1


@dataclass
class ThermalInfo:
    temperature: float
    tjmax: int = 100
    thermal_margin: int = 0
    throttling: bool = False


@dataclass
class PowerInfo:
    voltage: float
    tdp: int
    base_frequency: int
    max_turbo_frequency: int
    current_frequency: int


class WindowsSystemInfo:
    """Advanced Windows System Information using only built-in APIs"""

    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32
        self.ntdll = ctypes.windll.ntdll
        self._performance_frequency = self._get_performance_frequency()

    def _get_performance_frequency(self) -> int:
        """Get high-resolution performance counter frequency"""
        freq = ctypes.c_longlong()
        self.kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
        return freq.value

    def get_performance_counter(self) -> float:
        """Get high-resolution performance counter"""
        counter = ctypes.c_longlong()
        self.kernel32.QueryPerformanceCounter(ctypes.byref(counter))
        return counter.value / self._performance_frequency


class CPUIDReader:
    """CPUID instruction reader using ctypes"""

    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32

    def read_cpuid(self, eax: int, ecx: int = 0) -> Tuple[int, int, int, int]:
        """Read CPUID instruction results"""
        try:
            # Try to use inline assembly via ctypes
            class CPUIDResult(ctypes.Structure):
                _fields_ = [("eax", ctypes.c_uint32),
                            ("ebx", ctypes.c_uint32),
                            ("ecx", ctypes.c_uint32),
                            ("edx", ctypes.c_uint32)]

            # This is a simplified approach - in reality, you'd need more complex
            # assembly code injection or use a compiled DLL
            return (0, 0, 0, 0)  # Placeholder
        except Exception:
            return 0, 0, 0, 0



class _Const:
    """Constants for the processor library"""

    # Registry paths
    _CPU_REG_PATH: str = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    _SYSTEM_REG_PATH: str = r"HARDWARE\DESCRIPTION\System"

    # Performance counter names
    _PERF_COUNTERS: dict[str, str] = {
        'processor_time': r'\Processor(_Total)\% Processor Time',
        'frequency': r'\Processor Information(_Total)\Processor Frequency',
        'temperature': r'\Thermal Zone Information\Temperature',
    }

    # Command templates
    _WMIC_COMMANDS: dict[str, str] = {
        'cpu_name': 'wmic cpu get Name /format:list',
        "cpu_manufacturer": "wmic cpu get Manufacturer /format:list",
        "cpu_family": "wmic cpu get Family /format:list",
        "cpu_model": "wmic cpu get Model /format:list",
        'cpu_stepping': "wmic cpu get Stepping /format:list",
        "cpu_max_clock": "wmic cpu get MaxClockSpeed /format:list",
        "cpu_current_clock": "wmic cpu get CurrentClockSpeed /format:list",
        "cpu_cores_num": "wmic cpu get NumberOfCores /format:list",
        "cpu_logical_num": "wmic cpu get NumberOfLogicalProcessors /format:list",
        "cpu_arch": "wmic cpu get Architecture /format:list",

        'cache_info': 'wmic path Win32_CacheMemory get Purpose,InstalledSize,Level,Associativity,LineSize /format:list',
        'temp_info': 'wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature /format:list',
        'power_info': 'wmic path Win32_Processor get CurrentVoltage,VoltageCaps /format:list'
    }

    _POWERSHELL_COMMANDS: dict[str, str] = {
        'cpu_detailed': "Get-CimInstance -ClassName Win32_Processor | Select-Object Name,Manufacturer,Family,Model,Stepping,MaxClockSpeed,CurrentClockSpeed,NumberOfCores,NumberOfLogicalProcessors,Architecture,Description,SocketDesignation,ProcessorType,Voltage,CurrentVoltage | ConvertTo-Json",
        'cache_detailed': "Get-CimInstance -ClassName Win32_CacheMemory | Select-Object Purpose,InstalledSize,Level,Associativity,LineSize | ConvertTo-Json",
        'thermal_info': "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | Select-Object CurrentTemperature | ConvertTo-Json"
    }


class Processor(_Const):
    """Advanced Windows Processor Information and Monitoring Class"""

    def __init__(self, developer_mode: bool = True,
                 use_cache: bool = True,
                 use_searching: bool = False) -> None:

        super().__init__()

        # Configuration
        self.dev_mode = developer_mode
        self.use_cache = use_cache
        self.use_searching = use_searching

        # Initialize information interfaces
        self.system_info = WindowsSystemInfo()
        self.cpuid_reader = CPUIDReader()

        # Initialize cpu name first
        self.cpu_name = self.name

        # Initialize components
        self.cache_handler = CacheHandler(developer_mode) if use_cache else None
        self.online_searcher = OnlineSearcher(self.cpu_name) if use_searching else None

    @staticmethod
    def _is_valid_string(value: str, min_length: int = 3) -> bool:
        """Validate if a string contains meaningful data"""
        if not value or len(value.strip()) < min_length:
            return False

        invalid_patterns = [
            r'^x86', r'^family\s+\d+', r'^model\s+\d+', r'^stepping\s+\d+',
            r'^\d+$', r'^unknown', r'^generic', r'^to be filled',
            r'^not specified', r'^default string', r'^oem', r'^system manufacturer'
        ]

        value_lower = value.lower().strip()
        return not any(re.match(pattern, value_lower) for pattern in invalid_patterns)

    def _execute_wmic_command(self, command: str, timeout: int = 10) -> Dict[str, str]:
        """Execute WMIC command and parse results"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                output_dict = {}
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        output_dict[key.strip()] = value.strip()
                return output_dict
        except Exception as e:
            if self.dev_mode:
                print(f"WMIC command failed: {e}")

        return {}

    def _execute_powershell_command(self, command: str, timeout: int = 10) -> Any:
        """Execute PowerShell command and parse JSON results"""
        try:
            ps_cmd = ["powershell", "-NoProfile", "-Command", command]
            result = subprocess.run(
                ps_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except Exception as e:
            if self.dev_mode:
                print(f"PowerShell command failed: {e}")

        return None

    @staticmethod
    def _parse_cache_data(data: Dict) -> CPUCache:
        """Parse cache data from WMI/WMIC output"""
        level = 1
        size_bytes = 0
        associativity = 0
        line_size = 64  # Default
        cache_type = CacheType.UNIFIED.value

        if 'Level' in data:
            level = int(data['Level']) if data['Level'] else 1
        elif 'Purpose' in data:
            purpose = data['Purpose'].lower()
            if 'l1' in purpose:
                level = 1
            elif 'l2' in purpose:
                level = 2
            elif 'l3' in purpose:
                level = 3

        if 'InstalledSize' in data and data['InstalledSize']:
            size_bytes = int(data['InstalledSize']) * 1024  # Convert KB to bytes

        if 'Associativity' in data and data['Associativity']:
            associativity = int(data['Associativity'])

        if 'LineSize' in data and data['LineSize']:
            line_size = int(data['LineSize'])

        return CPUCache(level, size_bytes, associativity, line_size, cache_type)

    def _get_cache_info(self) -> List[CPUCache]:
        """Get detailed cache information"""
        cache_key = 'cache_info'

        if self.use_cache and self.cache_handler:
            cached = self.cache_handler.get_cached_data(cache_key)
            if cached:
                return [CPUCache(**cache) for cache in cached]

        caches = []

        # Try PowerShell first
        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cache_detailed'])
        if ps_result:
            if isinstance(ps_result, list):
                for cache_data in ps_result:
                    if isinstance(cache_data, dict):
                        caches.append(self._parse_cache_data(cache_data))
            elif isinstance(ps_result, dict):
                caches.append(self._parse_cache_data(ps_result))

        # Fallback to WMIC
        if not caches:
            wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cache_info'])
            if wmic_result:
                caches.append(self._parse_cache_data(wmic_result))

        if self.use_cache and self.cache_handler and caches:
            cache_dicts = [{'level': c.level, 'size_bytes': c.size_bytes,
                            'associativity': c.associativity, 'line_size': c.line_size,
                            'cache_type': c.cache_type, 'shared_cores': c.shared_cores}
                           for c in caches]

        return caches

    @property
    def name(self) -> ProcessorPyResult:
        """Get CPU name using multiple robust methods"""

        if self.use_cache and self.cache_handler.is_cache:
            cached = self.cache_handler.get_cached_data("name")
            if cached:
                return ProcessorPyResult(cached, True, "cache")

        # Method 1: Registry (fastest)
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self._CPU_REG_PATH) as key:
                value, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                if self._is_valid_string(value):
                    return ProcessorPyResult(value.strip(), True, "registry")

        except Exception:
            pass

        # Method 2: PowerShell with detailed info
        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        if ps_result and isinstance(ps_result, dict):
            name = ps_result.get('Name', '')
            if self._is_valid_string(name):
                return ProcessorPyResult(name.strip(), True, "powershell")

        # Method 3: WMIC
        wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_info'])
        if wmic_result.get('Name') and self._is_valid_string(wmic_result['Name']):
            name = wmic_result['Name']

            return ProcessorPyResult(name.strip(), True, "wmic")

        return ProcessorPyResult("Unknown", None, None)

    @property
    def manufacturer(self) -> ProcessorPyResult:
        """Get CPU manufacturer"""

        manufacturer: str = ""

        if self.use_cache and self.cache_handler:
            cached = self.cache_handler.get_cached_data("manufacturer")
            if cached:
                return ProcessorPyResult(cached, None, "cache")

        # First try wmic (fast)
        wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_manufcaturer'])
        # manufacturer = wmic_result.get('Manufacturer', '')
        if self._is_valid_string(manufacturer):
            return ProcessorPyResult(manufacturer, True, "wmic")

        # Try powershell (slow)
        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        if ps_result and isinstance(ps_result, dict):
            manufacturer = ps_result.get('Manufacturer', '')
            if self._is_valid_string(manufacturer):
                return ProcessorPyResult(manufacturer, True, "powershell")

        # Fallback : detect from name
        name: str = self.cpu_name.value.lower()
        if 'intel' in name:
            manufacturer = "Intel"
        elif 'amd' in name:
            manufacturer = "AMD"
        elif 'arm' in name:
            manufacturer = "ARM Holdings"
        elif 'qualcomm' in name:
            manufacturer = "Qualcomm"

        return ProcessorPyResult(manufacturer, True, "string_parsing")

    @property
    def release_date(self) -> ProcessorPyResult:
        """ This method will get the cpu release date"""

    @property
    def architecture(self) -> ProcessorPyResult:
        """Get CPU architecture"""
        cache_key = 'cpu_architecture'

        if self.use_cache and self.cache_handler:
            cached = self.cache_handler.get_cached_data(cache_key)
            if cached:
                return ProcessorPyResult(cached, None, None)

        # Get from system
        arch = platform.machine()
        if arch in ['AMD64', 'x86_64']:
            result = "x86_64"
        elif arch in ['x86', 'i386', 'i686']:
            result = "x86"
        elif 'ARM' in arch.upper():
            result = "ARM64" if '64' in arch else "ARM32"
        else:
            result = arch

        return ProcessorPyResult(result, False, "python")

    @property
    def family(self) -> ProcessorPyResult:
        """Get CPU family"""

        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        if ps_result and isinstance(ps_result, dict):
            family = ps_result.get('Family')
            if family:
                return ProcessorPyResult(str(family), True, "powershell")

        wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_info'])
        family = wmic_result.get('Family', '')
        return ProcessorPyResult(family, True, "wmic") if family else ProcessorPyResult("Unknown", None, None)

    @property
    def stepping(self) -> ProcessorPyResult:
        """Get CPU stepping"""
        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        if ps_result and isinstance(ps_result, dict):
            stepping = ps_result.get('Stepping')
            if stepping:
                return str(stepping)

        wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_info'])
        stepping = wmic_result.get('Stepping', '')
        return ProcessorPyResult(stepping, True) if stepping else ProcessorPyResult("Unknown", None)

    @property
    def socket(self) -> ProcessorPyResult:
        """Get CPU socket information"""
        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        if ps_result and isinstance(ps_result, dict):
            socket = ps_result.get('SocketDesignation', '')
            if self._is_valid_string(socket):
                return ProcessorPyResult(socket, True)

        # Try registry for socket info
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self._CPU_REG_PATH) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, "Identifier")
                    if self._is_valid_string(value):
                        return ProcessorPyResult(value, True)

                except FileNotFoundError:
                    pass

        except Exception:
            pass

        return ProcessorPyResult("Unknown", None)

    def get_l1_cache_size(self, friendly: bool = False) -> ProcessorPyResult:
        """Get L1 cache size"""
        cache_info = self._get_cache_info()
        l1_cache = next((cache for cache in cache_info if cache.level == 1), None)

        if l1_cache:
            size = l1_cache.size_bytes
            return ProcessorPyResult(self._format_bytes(size), True) if friendly else\
                ProcessorPyResult(size, True)

        return ProcessorPyResult("Unknown", None)

    def get_l2_cache_size(self, friendly: bool = False) -> ProcessorPyResult:
        """Get L2 cache size"""
        cache_info = self._get_cache_info()
        l2_cache = next((cache for cache in cache_info if cache.level == 2), None)

        if l2_cache:
            size = l2_cache.size_bytes
            return ProcessorPyResult(self._format_bytes(size), True) if friendly else\
                ProcessorPyResult(size, True)

        return ProcessorPyResult("Unknown", None)

    def get_l3_cache_size(self, friendly: bool = False) -> ProcessorPyResult:
        """Get L3 cache size"""
        cache_info = self._get_cache_info()
        l3_cache = next((cache for cache in cache_info if cache.level == 3), None)

        if l3_cache:
            size = l3_cache.size_bytes
            return ProcessorPyResult(self._format_bytes(size), True) if friendly else\
                ProcessorPyResult(size, True)

        return ProcessorPyResult("Unknown", None)

    def get_max_clock(self, friendly: bool = False) -> ProcessorPyResult:
        """Get maximum clock speed"""

        ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        if ps_result and isinstance(ps_result, dict):
            max_clock = ps_result.get('MaxClockSpeed')
            if max_clock:
                freq_mhz = int(max_clock)

                return ProcessorPyResult(f"{freq_mhz / 1000:.2f} GHz", True) if friendly else\
                    ProcessorPyResult(freq_mhz, True, "powershell")

        wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_info'])
        max_clock = wmic_result.get('MaxClockSpeed', '')
        if max_clock and max_clock.isdigit():
            freq_mhz = int(max_clock)
            return ProcessorPyResult(f"{freq_mhz / 1000:.2f} GHz", True, "wmic") if friendly else\
                ProcessorPyResult(freq_mhz, True, "wmic")

        return ProcessorPyResult("Unknown", None, None)

    def get_cores(self, logical: bool = False) -> ProcessorPyResult:
        """Get number of cores or logical processors"""

        # ps_result = self._execute_powershell_command(self._POWERSHELL_COMMANDS['cpu_detailed'])
        # if ps_result and isinstance(ps_result, dict):
        #     if logical:
        #         threads = ps_result.get('NumberOfLogicalProcessors')
        #         if threads:
        #             return int(threads)
        #     else:
        #         cores = ps_result.get('NumberOfCores')
        #         if cores:
        #             return int(cores)

        if logical:
            wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_cores_num'])

            threads = wmic_result.get('NumberOfLogicalProcessors', '')
            if threads and threads.isdigit():
                return int(threads)
        else:
            wmic_result = self._execute_wmic_command(self._WMIC_COMMANDS['cpu_logical_num'])
            print()
            cores = wmic_result.get('NumberOfCores', '')
            if cores and cores.isdigit():
                return int(cores)

        # Fallback to os.cpu_count()
        cpu_count = os.cpu_count()
        return cpu_count if cpu_count else 1

    def flags(self) -> Tuple[str, ...]:
        """Get CPU feature flags"""
        # This would require CPUID instruction implementation
        # For now, return common flags based on manufacturer
        manufacturer = self.manufacturer.lower()
        common_flags = ['fpu', 'vme', 'de', 'pse', 'tsc', 'msr', 'pae', 'mce', 'cx8', 'apic']

        if 'intel' in manufacturer:
            intel_flags = ['sep', 'mtrr', 'pge', 'mca', 'cmov', 'pat', 'pse36', 'clflush', 'mmx', 'fxsr', 'sse', 'sse2']
            return tuple(common_flags + intel_flags)
        elif 'amd' in manufacturer:
            amd_flags = ['sep', 'mtrr', 'pge', 'mca', 'cmov', 'pat', 'pse36', 'clflush', 'mmx', 'fxsr', 'sse', 'sse2',
                         'sse3']
            return tuple(common_flags + amd_flags)

        return tuple(common_flags)

    @property
    def cpu_tdp(self) -> ProcessorPyResult:
        """Get CPU TDP (estimated based on CPU model)"""

        # Define tdp value
        tdp: int = 0
        # Get lower cpu name string
        name = self.cpu_name.value.lower()

        # First try ..

        # Fallback : use Basic TDP estimation based on CPU series
        if 'i9' in name or 'ryzen 9' in name:
            tdp = 125
        elif 'i7' in name or 'ryzen 7' in name:
            tdp = 95
        elif 'i5' in name or 'ryzen 5' in name:
            tdp = 65
        elif 'i3' in name or 'ryzen 3' in name:
            tdp = 45
        elif 'celeron' in name or 'pentium' in name:
            tdp = 35
        elif 'xeon' in name or 'epyc' in name:
            tdp = 150

        tdp = 65  # Default estimate

        return ProcessorPyResult(tdp, False, "fallback")

    @property
    def lithography(self) -> ProcessorPyResult:
        """ This method will get the cpu lithography in nm"""

    def is_virtualization(self) -> ProcessorPyResult:
        """ This method will check if the cpu have virtualization feature"""

    def is_turbo_boosted(self) -> ProcessorPyResult:
        """ This method will check if the cpu have turbo boost featrue"""

    def is_ecc(self) -> ProcessorPyResult:
        """ This method will check if the cpu have ecc feature
        look : https://en.wikipedia.org/wiki/Error_correction_code
        """

    @property
    def get_memory_types(self) -> ProcessorPyResult:
        """ This method will get the cpu support memory types such as : DDR3, DDR4, DDR5"""

    def get_memory_channels(self) -> ProcessorPyResult:
        """ This method will get the memory channels supported. eg: 'single', 'dual' """

    def get_memory_bandwidths(self, friendly: bool = False) -> ProcessorPyResult:
        """ This method will get the maximum memory bandwidth supported by cpu"""

    def get_memory_size(self, friendly: bool = False) -> ProcessorPyResult:
        """ This method will get the maximum memory size supported by cpu"""

    @staticmethod
    def _format_bytes(size_bytes: int) -> str:
        """Format bytes into human readable format"""
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024 ** 3):.2f} GB"
        elif size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} B"

    def get_all_info(self) -> Dict[str, Any]:
        """Collect comprehensive CPU information"""

        data: dict = {
            # GENERAL
            "name": self.name,
            "Release date": self.release_date,
            "manufacturer": self.manufacturer,
            "Arch": self.architecture,
            "Socket": self.socket,
            "L1 Cache": self.get_l1_cache_size(friendly=True),
            "L2 Cache": self.get_l2_cache_size(friendly=True),
            "L3 Cache": self.get_l3_cache_size(friendly=True),
            "Max Speed": self.get_max_clock(friendly=True),
            "Cores": self.get_cores(),
            "Threads": self.get_cores(logical=True),
            # FEATURES
            "Lithography": self.lithography,
            "TDP": self.cpu_tdp,
            "Flags": self.flags,
            "Support Virtualization": self.is_virtualization(),
            "Support Turbo boost": self.is_turbo_boosted(),
            "Family": self.family,
            "Stepping": self.stepping,
            # MEMORY INTERFACE
            "Memory supported types": self.get_memory_types,
            "Memory channels": self.get_memory_channels(),
            "Max memory bandwidth": self.get_memory_bandwidth(friendly=True),
            "Max memory size": self.get_memory_size(friendly=True),
            "Support ECC": self.is_ecc(),
        }

        # Set cache file
        if self.use_cache and self.cache_handler.is_cache is False:
            # Print message for developer
            if self.dev_mode:
                print("[INFO] : Cache file created !")

            self.cache_handler.set_cache(data)

        return data


class Sensors(_Const):

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


if __name__ == "__main__":
    sys.exit(0)
