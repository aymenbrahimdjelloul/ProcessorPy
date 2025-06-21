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

# IMPORTS
import re
import subprocess
import threading
import logging
import datetime
from enum import Enum
from typing import Dict, List, Tuple, Union, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from functools import lru_cache
from ._core import Const
from ._core import *

# Handle imports
try:
    import winreg
    import ctypes
    import ctypes.wintypes

except ImportError:
    pass

# Declare basic ProcessorPy constants
_supported_platforms: tuple = ("Windows", "Linux", "Darwin")

class _Processor(ABC):
    """ This class contain the abstract methods """

    # Intel patterns (ordered by specificity)
    _intel_patterns: tuple[str, ...] = (
        # Mobile processors (check first to avoid desktop matches)
        (r'i[3579].*[0-9]{3,4}[uy]', 7),  # Y-series ultra-low power
        (r'i[3579].*[0-9]{3,4}u', 15),  # U-series low power
        (r'i[3579].*[0-9]{3,4}h', 45),  # H-series mobile high perf
        (r'i[3579].*[0-9]{3,4}hk', 45),  # HK-series mobile
        (r'i[3579].*[0-9]{3,4}g[17]?', 28),  # G-series with graphics

        # Desktop high-performance (K/X/KF series)
        (r'i9.*[0-9]{4,5}k[fs]?', 125),  # i9 K/KF/KS series
        (r'i7.*[0-9]{4,5}k[fs]?', 95),  # i7 K/KF/KS series
        (r'i5.*[0-9]{4,5}k[fs]?', 95),  # i5 K/KF/KS series
        (r'i3.*[0-9]{4,5}k[fs]?', 91),  # i3 K/KF/KS series

        # Desktop standard (non-K)
        (r'i9.*[0-9]{4,5}(?![kfshuyg])', 65),  # Standard i9
        (r'i7.*[0-9]{4,5}(?![kfshuyg])', 65),  # Standard i7
        (r'i5.*[0-9]{4,5}(?![kfshuyg])', 65),  # Standard i5
        (r'i3.*[0-9]{4,5}(?![kfshuyg])', 65),  # Standard i3

        # Server/Workstation
        (r'xeon.*w-[0-9]+', 165),  # Xeon W-series
        (r'xeon.*[0-9]+', 95),  # Standard Xeon

        # Budget processors
        (r'pentium.*[0-9]+', 35),
        (r'celeron.*[0-9]+', 25),
    )

    # AMD patterns
    _amd_patterns: tuple[str, ...] = (
        # Mobile processors (check first)
        (r'ryzen [3579].*[0-9]{4}u', 15),  # U-series mobile
        (r'ryzen [3579].*[0-9]{4}h[sx]?', 45),  # H-series mobile

        # Desktop high-performance (X series)
        (r'ryzen 9.*[0-9]{4}x[t3d]?', 105),  # Ryzen 9 X-series
        (r'ryzen 7.*[0-9]{4}x[t3d]?', 105),  # Ryzen 7 X-series
        (r'ryzen 5.*[0-9]{4}x[t3d]?', 105),  # Ryzen 5 X-series

        # Desktop standard (non-X)
        (r'ryzen 9.*[0-9]{4}(?!x)', 65),  # Standard Ryzen 9
        (r'ryzen 7.*[0-9]{4}(?!x)', 65),  # Standard Ryzen 7
        (r'ryzen 5.*[0-9]{4}(?!x)', 65),  # Standard Ryzen 5
        (r'ryzen 3.*[0-9]{4}', 65),  # Ryzen 3

        # HEDT/Server
        (r'threadripper.*pro', 280),  # Threadripper Pro
        (r'threadripper.*[0-9]+wx', 250),  # Threadripper WX
        (r'threadripper.*[0-9]+x', 180),  # Threadripper X
        (r'threadripper.*[0-9]+', 180),  # Standard Threadripper
        (r'epyc.*[0-9]+', 225),  # EPYC processors

        # APU series
        (r'ryzen [3579].*[0-9]{4}g[e]?', 65),  # Desktop APUs
    )

    # Apple Silicon patterns
    _apple_patterns: tuple[str, ...] = (
        (r'm[123] (ultra|max)', 70),  # M1/M2/M3 Ultra/Max
        (r'm[123] pro', 30),  # M1/M2/M3 Pro
        (r'm[123](?! (pro|max|ultra))', 15),  # Base M1/M2/M3
        (r'a[0-9]{2}.*bionic', 5),  # A-series mobile chips
    )

    # ARM patterns
    _arm_patterns: tuple[str, ...] = (
        (r'cortex-a(53|55)', 2),  # Low-power ARM
        (r'cortex-a(57|72|73|75|76|77|78)', 5),  # Mid-range ARM
        (r'cortex-a(510|710|715)', 8),  # High-performance ARM
        (r'cortex-x[123]', 12),  # ARM X-series
        (r'snapdragon [0-9]{3}', 15),  # Qualcomm mobile
    )

    def __init__(self, developer_mode=False) -> None:

        self._dev_mode = developer_mode

        # Create the local cache handler
        self._cache_handler = CacheHandler()
        # Define empty variable for store cached cpu info
        self._cached_data: dict = self._cache_handler.cached_data

        # Pre-initialize critical data
        self._cpu_name: Optional[str] = None
        self._vendor: Optional[str] = None

    @abstractmethod
    def name(self) -> ProcessorPyResult:
        """ This method will get the cpu name string"""
        pass

    @abstractmethod
    def vendor(self) -> ProcessorPyResult:
        """Get CPU manufacturer"""
        pass

    @abstractmethod
    def release_date(self) -> ProcessorPyResult:
        """ This method will get the cpu release date"""
        pass

    @abstractmethod
    def architecture(self) -> ProcessorPyResult:
        """Get CPU architecture"""
        pass

    @abstractmethod
    def family(self) -> ProcessorPyResult:
        """Get CPU family"""
        pass

    @abstractmethod
    def socket(self) -> ProcessorPyResult:
        """Get CPU socket information"""
        pass

    @abstractmethod
    def stepping(self) -> ProcessorPyResult:
        """ This method will get the cpu stepping information"""
        pass

    @abstractmethod
    def get_cache_size(self, level: int, friendly: bool = False) -> ProcessorPyResult:
        """ This method will get the cache size"""
        pass

    @abstractmethod
    def get_max_clock(self, friendly: bool = False) -> ProcessorPyResult:
        """Get maximum clock speed"""
        pass

    @abstractmethod
    def get_cores(self, logical: bool = False) -> ProcessorPyResult:
        """Get number of cores or logical processors"""
        pass

    @abstractmethod
    def flags(self) -> Tuple[str, ...]:
        """Get CPU feature flags"""
        pass

    @abstractmethod
    def tdp(self) -> ProcessorPyResult:
        """Get CPU TDP (estimated based on CPU model)"""
        pass

    @abstractmethod
    def lithography(self) -> ProcessorPyResult:
        """ This method will get the cpu lithography in nm"""
        pass

    @abstractmethod
    def is_virtualization(self) -> ProcessorPyResult:
        """ This method will check if the cpu have virtualization feature"""
        pass

    @abstractmethod
    def is_support_boost(self) -> ProcessorPyResult:
        """ This method will check if the cpu have turboboost featrue"""
        pass

    @abstractmethod
    def is_ecc(self) -> ProcessorPyResult:
        """ This method will check if the cpu have ecc feature
        look : https://en.wikipedia.org/wiki/Error_correction_code
        """
        pass

    @abstractmethod
    def supported_memory_types(self) -> ProcessorPyResult:
        """ This method will get the cpu support memory types such as : DDR3, DDR4, DDR5"""
        pass

    @abstractmethod
    def supported_memory_channels(self) -> ProcessorPyResult:
        """ This method will get the memory channels supported. eg: 'single', 'dual' """
        pass

    @abstractmethod
    def supported_memory_bandwidth(self, friendly: bool = False) -> ProcessorPyResult:
        """ This method will get the maximum memory bandwidth supported by cpu"""
        pass

    @abstractmethod
    def supported_memory_size(self, friendly: bool = False) -> ProcessorPyResult:
        """ This method will get the maximum memory size supported by cpu"""
        pass

    @abstractmethod
    def transistor_count(self) -> ProcessorPyResult:
        """ This method will count the cpu transistor"""
        pass

    def code_name(self) -> ProcessorPyResult:
        """ This method will determine the cpu code nane string eg : ivy bridge, coffee lake"""
        pass

    def get_all_info(self, all_info: bool = False) -> Dict[str, Any]:
        """Collect comprehensive CPU information

        Args:
            all_info: If True, returns extended CPU information including cache,
                     memory interface, and feature details

        Returns:
            Dictionary containing CPU information with consistent data types
        """

        # Base CPU information (always included)
        cpu_data: Dict[str, Any] = {
            "cpu_name": self._safe_call(self.name),
            "vendor": self._safe_call(self.vendor),
            "release_date": self._safe_call(self.release_date),
            "architecture": self._safe_call(self.architecture),
            "code_name": self._safe_call(self.code_name),
            "socket": self._safe_call(self.socket),
            "cpu_tdp": self._safe_call(self.tdp),
            "cpu_lithography": self._safe_call(self.lithography),
            "cores": self._safe_call(self.get_cores),
            "threads": self._safe_call(self.get_cores, logical=True),
        }

        # Extended information if requested
        if all_info:
            extended_data: Dict[str, Any] = {
                # Cache information
                "l1_cache": self._safe_call(self.get_cache_size, level=1, friendly=True),
                "l2_cache": self._safe_call(self.get_cache_size, level=2, friendly=True),
                "l3_cache": self._safe_call(self.get_cache_size, level=3, friendly=True),

                # Performance specs
                "max_speed": self._safe_call(self.get_max_clock, friendly=True),

                # CPU Features
                "flags": self._safe_call(self.flags),
                "virtualization_support": self._safe_call(self.is_virtualization),
                "turbo_boost_support": self._safe_call(self.is_support_boost),
                "family": self._safe_call(self.family),
                "stepping": self._safe_call(self.stepping),

                # Memory interface
                "supported_memory_types": self._safe_call(self.supported_memory_types),
                "memory_channels": self._safe_call(self.supported_memory_channels),
                "max_memory_bandwidth": self._safe_call(self.supported_memory_bandwidth),
                "max_memory_size": self._safe_call(self.supported_memory_size),
                "ecc_support": self._safe_call(self.is_ecc),
            }

            # Merge extended data into base data
            cpu_data.update(extended_data)

            # Handle caching if needed
            self._handle_caching(cpu_data)

        return cpu_data

    def _safe_call(self, method, *args, **kwargs) -> Any:
        """Safely call a method and handle potential exceptions

        Args:
            method: The method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Method result or None if an exception occurs
        """
        try:
            if callable(method):
                return method(*args, **kwargs)
            else:
                # Handle properties/attributes
                return method

        except Exception as e:
            if self._dev_mode:
                print(f"[WARNING] Failed to get {method.__name__ if hasattr(method, '__name__') else str(method)}: {e}")
            return None

    def _handle_caching(self, data: Dict[str, Any]) -> None:
        """Handle caching logic for CPU data

        Args:
            data: The CPU data dictionary to cache
        """
        try:
            if hasattr(self, '_cache_handler') and self._cache_handler:
                self._cache_handler.set_cache(data)

                if self._dev_mode:
                    print("[INFO] Cache file created successfully!")
        except Exception as e:
            if self._dev_mode:
                print(f"[WARNING] Failed to create cache file: {e}")

    @lru_cache(maxsize=32)
    def _is_valid_string(self, value: str, min_length: int = 3) -> bool:
        """Cached validation for string meaningfulness"""
        if not value or len(value.strip()) < min_length:
            return False

        invalid_patterns: tuple = (
            r'^x86', r'^family\s+\d+', r'^model\s+\d+', r'^stepping\s+\d+',
            r'^\d+$', r'^unknown', r'^generic', r'^to be filled',
            r'^not specified', r'^default string', r'^oem', r'^system manufacturer'
        )

        value_lower: str = value.lower().strip()
        return not any(re.match(pattern, value_lower) for pattern in invalid_patterns)

    @staticmethod
    def _simplify_cpu_name(name: str) -> str:
        """Clean CPU name: 'Intel(R) Core(TM) i5-7300U CPU @ 2.60GHz' -> 'Intel Core i5-7300U'"""

        # Remove trademarks, frequency, and extra words
        clean = re.sub(r'\(R\)|\(TM\)|\(C\)|®|™|©', '', name)
        clean = re.sub(r'\s*@\s*[\d.]+\s*[GMK]?Hz.*$', '', clean, re.IGNORECASE)
        clean = re.sub(r'\s+(CPU|Processor)(\s|$)', ' ', clean, re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean or "Unknown CPU"

    def _estimate_cpu_lithography(self) -> int:
        """ This method will estimate the cpu lithography value"""

    def _estimate_cpu_arch(self, platform_arch: str) -> str:
        """ This method will estimate the cpu arch string"""

    @staticmethod
    def _normalize_architecture(arch: str) -> str:
        """Normalize architecture string"""

        arch_lower = arch.lower()
        if arch_lower in ['amd64', 'x86_64', 'x64']:
            return 'x86_64'
        elif arch_lower in ['i386', 'i686', 'x86']:
            return 'x86'
        elif arch_lower in ['arm64', 'aarch64']:
            return 'arm64'
        elif arch_lower.startswith('arm'):
            return 'arm'
        return arch

    @staticmethod
    def _format_bytes(size_bytes: int) -> str:
        """Format bytes into human-readable format"""
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024 ** 3):.2f} GB"
        elif size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} B"

    @staticmethod
    def _format_cache_size(size_kb: int) -> str:
        """Format cache size in human-readable format"""
        if size_kb >= 1024:
            return f"{size_kb / 1024:.1f} MB"
        return f"{size_kb} KB"

    @staticmethod
    def _get_die_size() -> int:
        """ This method will estimate the cpu die size in mm2"""
        return 80  # return this as default value, this method will be updated later


if Const.platform == 'win32':

    class _Const:
        """Constants for registry paths and commands"""

        CPU_REG_PATH: str = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"

        POWERSHELL_MASTER_COMMAND: str = "Get-CimInstance -ClassName Win32_Processor | Select-Object -ExpandProperty"

        WMIC_COMMANDS: dict[str, str] = {
            'cpu_name': 'wmic cpu get Name /value',
            'cpu_max_clock': 'wmic cpu get MaxClockSpeed /value',
            'cpu_cores_num': 'wmic cpu get NumberOfCores /value',
            'cpu_logical_num': 'wmic cpu get NumberOfLogicalProcessors /value',
            'cpu_manufacturer': 'wmic cpu get Manufacturer /value',
            'cpu_family': 'wmic cpu get Family /value',
            'cpu_stepping': 'wmic cpu get Stepping /value',
            'cpu_socket': 'wmic cpu get SocketDesignation /value',
            'cpu_l2_cache': 'wmic cpu get L2CacheSize /value',
            'cpu_l3_cache': 'wmic cpu get L3CacheSize /value',
        }

    class Processor(_Processor):

        def __init__(self, developer_mode: bool = False, use_searching: bool = False) -> None:

            super().__init__()

            # Configuration
            self._dev_mode = developer_mode
            self._use_searching = use_searching

            # Cache for expensive operations
            self._cache: dict = {}
            self._cache_lock = threading.Lock()

            # Pre-load registry handle for reuse
            self._registry_handle = None
            self._init_registry()

            self._model: Optional[str] = None
            self._family: Optional[str] = None
            self._stepping: Optional[str] = None

        def _init_registry(self) -> None:
            """Initialize registry handle for reuse"""
            try:
                self._registry_handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _Const.CPU_REG_PATH)
            except Exception as e:
                if self._dev_mode:
                    print(f"Registry initialization failed: {e}")
                self._registry_handle = None

        def _get_cached_or_compute(self, cache_key: str, compute_func, *args, **kwargs):
            """Thread-safe cache management"""

            with self._cache_lock:
                if cache_key in self._cache:
                    return self._cache[cache_key]

                result = compute_func(*args, **kwargs)
                self._cache[cache_key] = result
                return result

        def _read_registry_value(self, value_name: str) -> Optional[str]:
            """Fast registry value retrieval - simplified and optimized

            Args:
                value_name: The name of the registry value to read

            Returns:
                The registry value if successful, None otherwise
            """
            if not self._registry_handle:
                return None

            try:
                value, _ = winreg.QueryValueEx(self._registry_handle, value_name)
                return str(value) if value is not None else None
            except (WindowsError, OSError):
                # Registry operations are typically very fast (<1ms)
                # If they fail, they fail immediately - no need for timeout/threading
                return None

        def _execute_wmic_command(self, command: str, timeout: int = 5) -> Dict[str, str]:
            """Optimized WMIC execution with shorter timeout"""
            cache_key = f"wmic_{hash(command)}"
            return self._get_cached_or_compute(cache_key, self._wmic_execute, command, timeout)

        def _wmic_execute(self, command: str, timeout: int) -> Dict[str, str]:
            """Internal WMIC execution"""
            try:
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if result.returncode == 0:
                    output_dict: dict = {}
                    for line in result.stdout.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            clean_key = key.strip()
                            clean_value = value.strip()
                            if clean_value:  # Only store non-empty values
                                output_dict[clean_key] = clean_value
                    return output_dict

            except subprocess.TimeoutExpired:
                if self._dev_mode:
                    print(f"WMIC command timed out: {command}")

            except Exception as e:
                if self._dev_mode:
                    print(f"WMIC command failed: {e}")

            return {}

        def _execute_powershell_command(self, query: str, timeout: int = 3) -> Optional[str]:
            """Optimized PowerShell execution with shorter timeout"""
            cache_key = f"ps_{hash(query)}"
            return self._get_cached_or_compute(cache_key, self._powershell_execute, query, timeout)

        def _powershell_execute(self, query: str, timeout: int) -> Optional[str]:
            """Internal PowerShell execution"""
            try:
                ps_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                          f"{_Const.POWERSHELL_MASTER_COMMAND} {query}"]
                result = subprocess.run(
                    ps_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                elif self._dev_mode:
                    print(f"PowerShell failed: {result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                if self._dev_mode:
                    print(f"PowerShell timed out for query: {query}")
            except Exception as e:
                if self._dev_mode:
                    print(f"PowerShell command failed: {e}")

            return None

        def name(self) -> ProcessorPyResult:
            """Get CPU name using the fastest available method"""

            # Use active cache to return cpu name instantly
            # This will help when this method is called over and over
            if self._cpu_name:
                return self._cpu_name

            # Check for cached data
            if self._cache_handler.is_cache:
                result: ProcessorPyResult = self._cached_data.get("cpu_name")

                return ProcessorPyResult(value=result['value'],
                                         is_accurate=result['is_accurate'],
                                         method="cache")

            # Method 1: Registry (fastest - ~1ms)
            reg_value = self._read_registry_value("ProcessorNameString")

            if reg_value and self._is_valid_string(reg_value):
                original_value = self._simplify_cpu_name(reg_value.strip())
                self._cpu_name = ProcessorPyResult(original_value, True, "registry")

                return ProcessorPyResult(original_value, True, "registry")

            # Method 3: WMIC (medium speed - ~100-500ms)
            wmic_result = self._execute_wmic_command(_Const.WMIC_COMMANDS['cpu_name'])

            if wmic_result.get('Name') and self._is_valid_string(wmic_result['Name']):
                name = wmic_result['Name'].strip()
                self._cpu_name = ProcessorPyResult(name, True, "wmic")
                return ProcessorPyResult(self._simplify_cpu_name(name), True, "wmic")

            # Fallback
            self._cpu_name = ProcessorPyResult("n/a", None, None)
            return ProcessorPyResult("n/a", None, None)

        def release_date(self) -> ProcessorPyResult:
            """Optimized CPU release date detection with comprehensive manufacturer support."""

            cpu_info = self.name().value.strip()
            if not cpu_info:
                return ProcessorPyResult("n/a", False, "empty-name")

            current_year = datetime.datetime.now().year
            current_quarter = ((datetime.datetime.now().month - 1) // 3) + 1

            # Optimized CPU detection patterns with combined regex and direct lookups
            detection_rules = [
                # Intel Desktop (highest priority - most common)
                (r'(?:Core\s+)?i[3579]-(\d{1,2})\d{3}[A-Za-z]*', {
                    '14': (2024, 1, 0.95), '13': (2022, 4, 0.95), '12': (2021, 4, 0.95),
                    '11': (2021, 1, 0.95), '10': (2019, 2, 0.95), '9': (2018, 4, 0.95),
                    '8': (2017, 3, 0.95), '7': (2017, 1, 0.95), '6': (2015, 3, 0.95),
                    '5': (2015, 1, 0.95), '4': (2013, 2, 0.95), '3': (2012, 2, 0.95),
                    '2': (2011, 1, 0.95), '1': (2010, 1, 0.95)
                }, 'intel-desktop'),

                # AMD Ryzen Desktop
                (r'Ryzen\s+[3579]\s+(\d)000[XG]?[A-Za-z]*', {
                    '8': (2024, 1, 0.95), '7': (2022, 4, 0.95), '6': (2022, 1, 0.95),
                    '5': (2020, 4, 0.95), '4': (2020, 1, 0.95), '3': (2019, 3, 0.95),
                    '2': (2018, 2, 0.95), '1': (2017, 2, 0.95), '9': (2019, 1, 0.95)
                }, 'amd-ryzen'),

                # Apple Silicon (M & A series)
                (r'\b(M[1-4]|A1[0-7]|A[7-9])\b', {
                    'M4': (2024, 2, 0.95), 'M3': (2023, 4, 0.95), 'M2': (2022, 2, 0.95), 'M1': (2020, 4, 0.95),
                    'A17': (2023, 3, 0.95), 'A16': (2022, 3, 0.95), 'A15': (2021, 3, 0.95),
                    'A14': (2020, 3, 0.95), 'A13': (2019, 3, 0.95), 'A12': (2018, 3, 0.95),
                    'A11': (2017, 3, 0.95), 'A10': (2016, 3, 0.95), 'A9': (2015, 3, 0.95),
                    'A8': (2014, 3, 0.95), 'A7': (2013, 3, 0.95)
                }, 'apple'),

                # Intel Mobile
                (r'(?:Core\s+)?i[3579]-(\d{1,2})\d{2}[UYH][A-Za-z]*', {
                    '13': (2023, 1, 0.9), '12': (2022, 1, 0.9), '11': (2021, 3, 0.9),
                    '10': (2019, 3, 0.9), '8': (2018, 3, 0.9), '7': (2017, 3, 0.9),
                    '6': (2016, 3, 0.9), '5': (2015, 1, 0.9), '4': (2014, 2, 0.9)
                }, 'intel-mobile'),

                # AMD Mobile
                (r'Ryzen\s+[3579]\s+(\d)000[UH][A-Za-z]*', {
                    '7': (2023, 1, 0.9), '6': (2022, 1, 0.9), '5': (2021, 1, 0.9),
                    '4': (2020, 1, 0.9), '3': (2019, 1, 0.9), '2': (2018, 4, 0.9)
                }, 'amd-mobile'),

                # Qualcomm Snapdragon
                (r'Snapdragon\s+(?:8\s+Gen\s+([1-3])|(\d{3})|X\s+Elite)', {
                    '1': (2021, 4, 0.9), '2': (2022, 4, 0.9), '3': (2023, 4, 0.9),
                    '888': (2020, 4, 0.9), '865': (2019, 4, 0.9), '855': (2018, 4, 0.9),
                    '845': (2017, 4, 0.9), '835': (2017, 1, 0.9), 'elite': (2024, 2, 0.9)
                }, 'snapdragon'),

                # Intel Xeon
                (r'Xeon.*?(?:(\d{4})|(\d{2})\d{2})[A-Za-z]*', {
                    '2023': (2023, 2, 0.85), '2022': (2022, 2, 0.85), '2021': (2021, 2, 0.85),
                    '13': (2022, 4, 0.85), '12': (2021, 4, 0.85)
                }, 'intel-xeon'),

                # AMD EPYC
                (r'EPYC\s+(\d)000[A-Za-z]*', {
                    '9': (2024, 2, 0.9), '7': (2022, 2, 0.9), '6': (2021, 2, 0.9),
                    '4': (2021, 1, 0.9), '3': (2019, 2, 0.9), '2': (2018, 2, 0.9)
                }, 'amd-epyc'),

                # ARM Cortex
                (r'Cortex-([AX]\d{1,2})', {
                    'A78': (2020, 2, 0.85), 'A77': (2019, 2, 0.85), 'A76': (2018, 2, 0.85),
                    'A75': (2017, 2, 0.85), 'A73': (2016, 2, 0.85), 'A72': (2015, 2, 0.85),
                    'X4': (2023, 2, 0.85), 'X3': (2022, 2, 0.85), 'X2': (2021, 2, 0.85), 'X1': (2020, 2, 0.85)
                }, 'arm-cortex'),

                # MediaTek
                (r'(?:Dimensity\s+(\d{4})|Helio\s+([GP]\d{2}))', {
                    '9300': (2023, 4, 0.8), '9200': (2022, 4, 0.8), '9000': (2021, 4, 0.8),
                    '8100': (2022, 1, 0.8), '1200': (2021, 1, 0.8), 'G96': (2021, 3, 0.8)
                }, 'mediatek'),

                # Samsung Exynos
                (r'Exynos\s+(\d{4})', {
                    '2400': (2024, 1, 0.8), '2200': (2022, 1, 0.8), '2100': (2021, 1, 0.8),
                    '1080': (2020, 3, 0.8), '990': (2019, 4, 0.8), '9820': (2019, 1, 0.8)
                }, 'exynos')
            ]

            best_match = None
            highest_confidence = 0.0

            # Process each detection rule
            for pattern, mapping, cpu_type in detection_rules:
                match = re.search(pattern, cpu_info, re.IGNORECASE)
                if not match:
                    continue

                # Extract key from match groups
                key = None
                for group in match.groups():
                    if group:
                        key = group
                        break

                if not key:
                    continue

                # Special handling for specific patterns
                if cpu_type == 'snapdragon' and 'elite' in cpu_info.lower():
                    key = 'elite'
                elif cpu_type == 'apple':
                    key = key.upper()

                # Direct lookup
                if key in mapping:
                    year, quarter, confidence = mapping[key]
                    if 1990 <= year <= current_year + 2 and confidence > highest_confidence:
                        best_match = (year, quarter, confidence, f"{cpu_type}-{key}")
                        highest_confidence = confidence

                # Fallback estimation for Intel/AMD generations
                elif key.isdigit() and len(key) <= 2:
                    if cpu_type.startswith('intel'):
                        est_year = 2008 + int(key)
                        if 2008 <= est_year <= current_year + 1:
                            confidence = 0.6
                            if confidence > highest_confidence:
                                best_match = (est_year, 2, confidence, f"{cpu_type}-est-{key}")
                                highest_confidence = confidence
                    elif cpu_type.startswith('amd'):
                        est_year = 2017 + int(key)
                        if 2017 <= est_year <= current_year + 1:
                            confidence = 0.65
                            if confidence > highest_confidence:
                                best_match = (est_year, 2, confidence, f"{cpu_type}-est-{key}")
                                highest_confidence = confidence

            # Final fallback: extract year from CPU name
            if not best_match:
                year_match = re.search(r'\b(20[0-2][0-9])\b', cpu_info)
                if year_match:
                    year = int(year_match.group(1))
                    if 2000 <= year <= current_year + 1:
                        quarter = current_quarter if year == current_year else 2
                        best_match = (year, quarter, 0.5, 'year-fallback')

            # Return result
            if best_match:
                year, quarter, confidence, method = best_match

                # Adjust quarter for current year
                if year == current_year and quarter > current_quarter:
                    quarter = current_quarter

                return ProcessorPyResult(
                    value=f"Q{quarter} {year}",
                    is_accurate=confidence >= 0.8,
                    method=method
                )

            return ProcessorPyResult("n/a", False, "no-match")

        def vendor(self) -> ProcessorPyResult:
            """Get a normalized CPU vendor (e.g., 'Intel', 'AMD') using fastest available method."""

            if self._vendor:
                return self._vendor

            # Mapping all possible hints to canonical names
            vendor_map: dict[str, str] = {
                'intel': 'Intel',
                'genuineintel': 'Intel',
                'amd': 'AMD',
                'authenticamd': 'AMD',
                'arm': 'ARM Holdings',
                'arm limited': 'ARM Holdings',
                'qualcomm': 'Qualcomm',
                'apple': 'Apple Inc.',
                'apple inc.': 'Apple Inc.',
                'nvidia': 'NVIDIA Corporation'
            }

            # Method 1: Parse from CPU name (fastest)
            name_lower = self.name().value.lower()

            for key, value in vendor_map.items():
                if key in name_lower:
                    self._vendor = ProcessorPyResult(value, True, "name_parsing")
                    return self._vendor

            # Method 2: Registry
            reg_value = self._read_registry_value("VendorIdentifier")
            if reg_value and self._is_valid_string(reg_value):
                reg_key = reg_value.strip().lower()
                value = vendor_map.get(reg_key, reg_key.title())
                self._vendor = ProcessorPyResult(value, True, "registry")
                return self._vendor

            # Method 3: WMIC
            wmic_value = self._execute_wmic_command(_Const.WMIC_COMMANDS['cpu_manufacturer']).get('Manufacturer')
            if wmic_value:
                wmic_key = wmic_value.strip().lower()
                value = vendor_map.get(wmic_key, wmic_key.title())
                self._vendor = ProcessorPyResult(value, True, "wmic")
                return self._vendor

            # Fallback
            self._vendor = ProcessorPyResult("n/a", None, None)
            return self._vendor

        def architecture(self) -> ProcessorPyResult:
            """Get CPU architecture using the fastest method"""
            # Method 1: Environment variable (fastest)
            arch_env = os.environ.get('PROCESSOR_ARCHITECTURE', '')
            if arch_env:

                arch_map: dict[str, str] = {
                    'AMD64': 'x86_64',
                    'x86': 'x86',
                    'ARM64': 'arm64',
                    'ARM': 'arm'
                }
                mapped_arch = arch_map.get(arch_env, arch_env)
                return ProcessorPyResult(mapped_arch, True, "environment")

            # Method 2: Platform module (very fast)
            platform_arch: str = platform.machine()
            if platform_arch:
                return ProcessorPyResult(self._normalize_architecture(platform_arch), True, "platform")

            return ProcessorPyResult("Unknown", False, "fallback")

        def get_cores(self, logical: bool = False) -> ProcessorPyResult:
            """
            Get core count using environment variable (logical) or Windows Registry (physical).

            Args:
                logical (bool): If True, return logical cores. If False, return physical cores.

            Returns:
                ProcessorPyResult: Core count with source and accuracy info.
            """
            cache_key = f"_cores_{'logical' if logical else 'physical'}"

            # Early exit: return cached result if available
            if hasattr(self, cache_key):
                return getattr(self, cache_key)

            result = None

            if logical:
                # Try environment variable first
                try:
                    env_cores = os.environ.get("NUMBER_OF_PROCESSORS")
                    if env_cores and env_cores.isdigit():
                        core_count = int(env_cores)
                        if core_count > 0:
                            result = ProcessorPyResult(value=core_count, is_accurate=True, method="environment")
                except Exception as e:
                    if self._developer_mode:
                        print(f"[DEBUG] Environment variable method failed: {e}")

                # Fallback to os.cpu_count() for logical cores
                if not result:
                    try:
                        core_count = os.cpu_count()
                        if core_count and core_count > 0:
                            result = ProcessorPyResult(value=core_count, is_accurate=True, method="os.cpu_count")
                    except Exception as e:
                        if self._developer_mode:
                            print(f"[DEBUG] os.cpu_count() fallback failed: {e}")

            else:  # Physical cores
                # Try Windows Registry first
                try:
                    if not self._registry_handle:
                        self._registry_handle = winreg.OpenKey(
                            winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor"
                        )

                    subkey_count = winreg.QueryInfoKey(self._registry_handle)[0]
                    if subkey_count > 0:
                        result = ProcessorPyResult(value=subkey_count, is_accurate=True, method="winreg")
                except Exception as e:
                    if self._developer_mode:
                        print(f"[DEBUG] Registry method failed: {e}")

                # Fallback to os.cpu_count() for physical cores (less accurate but better than nothing)
                if not result:
                    try:
                        core_count = os.cpu_count()
                        if core_count and core_count > 0:
                            # Note: os.cpu_count() typically returns logical cores, so this is less accurate for physical
                            result = ProcessorPyResult(value=core_count, is_accurate=False,
                                                       method="os.cpu_count_fallback")
                    except Exception as e:
                        if self._developer_mode:
                            print(f"[DEBUG] os.cpu_count() fallback failed: {e}")

            # Final fallback if all methods failed
            if not result:
                result = ProcessorPyResult(value="unknown", is_accurate=False, method="error")
                if self._developer_mode:
                    print(f"[DEBUG] get_cores({logical}) - all methods failed")

            return result

        def get_max_clock(self, friendly: bool = False) -> ProcessorPyResult:
            """Get maximum clock speed"""
            # Method 1: Registry (fastest)
            reg_value = self._read_registry_value("~MHz")
            if reg_value and str(reg_value).isdigit():
                freq_mhz = int(reg_value)
                if friendly:
                    return ProcessorPyResult(f"{freq_mhz / 1000:.2f} GHz", True, "registry")
                return ProcessorPyResult(freq_mhz, True, "registry")

            # Method 2: WMIC (slower)
            wmic_result = self._execute_wmic_command(_Const.WMIC_COMMANDS['cpu_max_clock'])
            max_clock = wmic_result.get('MaxClockSpeed', '')
            if max_clock and max_clock.isdigit():
                freq_mhz = int(max_clock)
                if friendly:
                    return ProcessorPyResult(f"{freq_mhz / 1000:.2f} GHz", True, "wmic")
                return ProcessorPyResult(freq_mhz, True, "wmic")

            return ProcessorPyResult("Unknown", False, "fallback")

        def family(self) -> ProcessorPyResult:
            """Get the CPU family"""
            return ProcessorPyResult("n/a", None, None)

        def stepping(self) -> ProcessorPyResult:
            """ This method will get the cpu stepping information"""
            return ProcessorPyResult("n/a", None, None)

        def model(self) -> ProcessorPyResult:
            """ This method will get the cpu model information"""
            return self._model

        def _init_processor_identifier(self) -> Optional:
            """ This method will get the cpu identifier from winreg that contain
            cpu model, stepping, family and save it as cache after return the requested info

            Args:
                info_type: str, for example 'model' or 'stepping'

            Returns: ProcessorPyResult

            """

            id = self._read_registry_value("PROCESSOR_IDENTIFIER")
            return id


        def socket(self) -> ProcessorPyResult:
            """Get CPU socket/packaging information using all available detection methods"""

            # Get cpu name string
            cpu_name: str = self.name().value.strip()
            socket_info = "n/a"

            # Try to get CPUID info if available
            try:
                vendor = getattr(self, 'cpuid_vendor', lambda: "")()
                family = getattr(self, 'cpuid_family', lambda: 0)()
                model = getattr(self, 'cpuid_model', lambda: 0)()

            except Exception:
                vendor, family, model = "", 0, 0

            # Intel CPUID-based detection
            if vendor == "GenuineIntel":
                # Desktop/Server Sockets
                if family == 6:
                    # LGA1700 (12th-14th Gen)
                    if model in (0x97, 0x9A, 0xB7, 0xBF, 0xC6, 0xCF):
                        socket_info = "LGA1700"
                    # LGA1200 (10th-11th Gen)
                    elif model in (0xA5, 0xA6, 0xA7):
                        socket_info = "LGA1200"
                    # LGA1151 (6th-9th Gen)
                    elif model in (0x4E, 0x5E, 0x8E, 0x9E):
                        socket_info = "LGA1151"
                    # LGA2066 (Skylake-X)
                    elif model == 0x55:
                        socket_info = "LGA2066"
                    # LGA2011-3 (Haswell-E/Broadwell-E)
                    elif model in (0x3F, 0x4F, 0x56):
                        socket_info = "LGA2011-3"
                    # LGA1150 (Haswell)
                    elif model in (0x3C, 0x3F, 0x45, 0x46):
                        socket_info = "LGA1150"
                    # LGA1155 (Sandy/Ivy Bridge)
                    elif model in (0x2A, 0x2D, 0x3A, 0x3E):
                        socket_info = "LGA1155"
                    # LGA1366 (Nehalem/Westmere)
                    elif model in (0x1A, 0x1E, 0x1F, 0x2E, 0x25, 0x2C, 0x2F):
                        socket_info = "LGA1366"
                    # LGA775 (Core 2)
                    elif model in (0x0F, 0x17, 0x1D):
                        socket_info = "LGA775"

            # AMD CPUID-based detection
            elif vendor == "AuthenticAMD":
                # Check for EPYC (Server)
                if "EPYC" in cpu_name.upper():
                    if "7" in cpu_name.split()[1][0]:  # EPYC 7003/7002
                        socket_info = "SP3"
                    elif "9" in cpu_name.split()[1][0]:  # EPYC 9004
                        socket_info = "SP5"
                # Ryzen Desktop
                elif "Ryzen" in cpu_name:
                    if "Threadripper" in cpu_name:
                        if "PRO" in cpu_name:
                            socket_info = "sWRX8"
                        elif any(x in cpu_name for x in ["3970X", "3990X"]):
                            socket_info = "sTRX4"
                        else:
                            socket_info = "TR4"
                    elif "7" in cpu_name.split()[1][0]:  # Ryzen 7000 series
                        socket_info = "AM5"
                    else:
                        socket_info = "AM4"

            # If CPUID didn't identify, try name pattern matching
            if socket_info == "n/a" and cpu_name:
                # Intel Patterns
                if re.search(r'(i[3579]-|Xeon.*W-|Xeon E[23567]-).*1[2345]\d{3}', cpu_name, re.I):
                    socket_info = "LGA1700"
                elif re.search(r'(i[3579]-|Xeon.*W-|Xeon E-).*1[01]\d{2}', cpu_name, re.I):
                    socket_info = "LGA1200"
                elif re.search(r'(i[3579]-|Xeon E[23]-).*[89]00', cpu_name, re.I):
                    socket_info = "LGA1151"
                elif re.search(r'(i[3579]-|Xeon E3-).*[67]00', cpu_name, re.I):
                    socket_info = "LGA1151"
                elif re.search(r'(Xeon|Core i[79] Extreme).*X?[56]\d{3}', cpu_name, re.I):
                    socket_info = "LGA2066"

                # AMD Patterns
                elif re.search(r'Ryzen [79] [79]\d{2}', cpu_name, re.I):
                    socket_info = "AM5"
                elif re.search(r'Ryzen [3579] \d{4}', cpu_name, re.I):
                    socket_info = "AM4"
                elif re.search(r'Threadripper (29|39|59)', cpu_name, re.I):
                    socket_info = "TR4" if "29" in cpu_name else "sTRX4"

                # Apple Silicon
                elif re.search(r'M[123] (Max|Pro)?', cpu_name, re.I):
                    socket_info = "Apple FCBGA"

                # ARM Chips
                elif re.search(r'(Snapdragon|Tensor|Graviton|Ampere)', cpu_name, re.I):
                    socket_info = "SOC Package"

                # Mobile detection
                elif any(x in cpu_name for x in ["U Series", "H Series", "Y Series", "Mobile"]):
                    socket_info = "BGA"  # Generic mobile BGA package

            # Final fallbacks
            if socket_info == "n/a":
                if "ARM" in cpu_name or any(x in cpu_name for x in ["Cortex", "Neoverse"]):
                    socket_info = "SOC Package"
                elif "Apple" in cpu_name:
                    socket_info = "Apple SIP"

            return ProcessorPyResult(socket_info, None, None)

        def get_cache_size(self, level: int, friendly: bool = False) -> ProcessorPyResult:
            """Get cache size for specified level (1, 2, or 3)"""
            if level not in [1, 2, 3]:
                return ProcessorPyResult("Invalid level", False, "error")

            # Method 1: Registry (fastest)
            cache_keys = {
                1: "L1CacheSize",
                2: "L2CacheSize",
                3: "L3CacheSize"
            }

            reg_key = cache_keys.get(level)
            if reg_key:
                reg_value = self._read_registry_value(reg_key)
                if reg_value and str(reg_value).isdigit():
                    size_kb = int(reg_value)
                    if friendly:
                        return ProcessorPyResult(self._format_cache_size(size_kb), True, "registry")
                    return ProcessorPyResult(size_kb, True, "registry")

            # Method 2: WMIC (slower)
            wmic_commands = {
                2: _Const.WMIC_COMMANDS['cpu_l2_cache'],
                3: _Const.WMIC_COMMANDS['cpu_l3_cache']
            }

            if level in wmic_commands:
                wmic_result = self._execute_wmic_command(wmic_commands[level])
                cache_key = f'L{level}CacheSize'
                cache_size = wmic_result.get(cache_key, '')
                if cache_size and cache_size.isdigit():
                    size_kb = int(cache_size)
                    if friendly:
                        return ProcessorPyResult(self._format_cache_size(size_kb), True, "wmic")
                    return ProcessorPyResult(size_kb, True, "wmic")

            return ProcessorPyResult("Unknown", False, "fallback")

        def flags(self) -> Tuple[str, ...]:
            """Get CPU feature flags with manufacturer-specific optimizations and modern extensions.

            Returns:
                ProcessorPyResult: Contains:
                    - value: Tuple of feature flags
                    - is_accurate: True if manufacturer-specific flags were used
                    - method: Source of the flags ('cpuid', 'estimated', or 'fallback')
            """
            # Normalize manufacturer string
            manufacturer = self.vendor().value.strip()

            # Modern base flags (x86_64 common features)
            base_flags = [
                'fpu', 'vme', 'de', 'pse', 'tsc', 'msr', 'pae', 'mce',
                'cx8', 'apic', 'sep', 'mtrr', 'pge', 'mca', 'cmov',
                'pat', 'pse36', 'clflush', 'mmx', 'fxsr', 'sse', 'sse2'
            ]

            # Extended flag sets by manufacturer and architecture
            flag_sets = {
                # Intel features (including modern extensions)
                'intel': base_flags + [
                    'ssse3', 'sse4_1', 'sse4_2', 'avx', 'avx2', 'aes',
                    'fma', 'rdrand', 'xsave', 'xsaveopt', 'pclmulqdq'
                ],

                # AMD features (including modern extensions)
                'amd': base_flags + [
                    'sse3', 'sse4a', 'avx', 'fma4', 'aes', 'rdrand',
                    'xsave', 'pclmulqdq', 'sha', 'mmxext'
                ],

                # ARM features (AArch64 common features)
                'arm': [
                    'fp', 'asimd', 'evtstrm', 'aes', 'pmull', 'sha1',
                    'sha2', 'crc32', 'atomics', 'cpuid'
                ],

                # Apple Silicon (M-series) specific features
                'apple': [
                    'fp', 'asimd', 'aes', 'sha1', 'sha2', 'crc32',
                    'atomics', 'cpuid', 'apple_m1', 'amx'
                ]
            }

            # Vendor-specific mappings (including common substrings)
            vendor_mappings = {
                'intel': ['intel', 'genuineintel'],
                'amd': ['amd', 'authenticamd'],
                'arm': ['arm', 'aarch64', 'arm64'],
                'apple': ['apple', 'm1', 'm2']
            }

            # Try to detect manufacturer and return appropriate flags
            for vendor, patterns in vendor_mappings.items():
                if any(pattern in manufacturer for pattern in patterns):
                    return ProcessorPyResult(
                        value=tuple(flag_sets[vendor]),
                        is_accurate=True,
                        method="estimated"
                    )

            # Fallback: Try to determine architecture
            if 'x86' in manufacturer or 'amd64' in manufacturer:
                return ProcessorPyResult(
                    value=tuple(base_flags + ['sse3']),  # Most x86_64 CPUs have SSE3
                    is_accurate=False,
                    method="arch_fallback"
                )

            # Minimal ARM fallback
            if 'arm' in manufacturer:
                return ProcessorPyResult(
                    value=tuple(['fp', 'asimd']),  # Basic ARM features
                    is_accurate=False,
                    method="arch_fallback"
                )

            # Ultimate fallback - just base x86 flags
            return ProcessorPyResult(
                value=tuple(base_flags),
                is_accurate=False,
                method="minimal_fallback"
            )

        def tdp(self) -> ProcessorPyResult:
            """
            Get Thermal Design Power (TDP) estimation using regex patterns.

            Returns:
                Estimated TDP in watts, or None if no reasonable estimate can be made
            """

            # Declare stripped lowered cpu name string
            cpu_name: str = self.name().value.strip()

            # Check patterns in order of specificity
            all_patterns: list[Optional] = []

            # Determine CPU brand and add relevant patterns
            if any(brand in cpu_name for brand in ('intel', 'core', 'pentium', 'celeron', 'xeon')):
                all_patterns.extend(self._intel_patterns)
            elif any(brand in cpu_name for brand in ('amd', 'ryzen', 'threadripper', 'epyc')):
                all_patterns.extend(self._amd_patterns)
            elif any(brand in cpu_name for brand in ('apple', 'm1', 'm2', 'm3')):
                all_patterns.extend(self._apple_patterns)
            elif any(brand in cpu_name for brand in ('arm', 'cortex', 'snapdragon')):
                all_patterns.extend(self._arm_patterns)
            else:
                # Try all patterns if brand is unclear
                all_patterns.extend(self._intel_patterns + self._amd_patterns + self._apple_patterns + self._arm_patterns)

            # Match patterns
            for pattern, tdp in all_patterns:
                if re.search(pattern, cpu_name):
                    return ProcessorPyResult(value=tdp, is_accurate=True, method="estimated")

            # Fallback: estimate based on core count if available
            core_match = re.search(r'(\d+)[-\s]?core', cpu_name)
            if core_match:
                cores = int(core_match.group(1))

                if cores <= 2:
                    return ProcessorPyResult(value=25, is_accurate=True, method="fallback")

                elif cores <= 4:
                    return ProcessorPyResult(value=45, is_accurate=True, method="fallback")

                elif cores <= 8:
                    return ProcessorPyResult(value=85, is_accurate=True, method="fallback")

                elif cores <= 16:
                    return ProcessorPyResult(value=125, is_accurate=True, method="fallback")

                else:
                    return ProcessorPyResult(value=180, is_accurate=True, method="fallback")

            # Final fallback based on common naming patterns
            if any(term in cpu_name for term in ['mobile', 'laptop', 'notebook']):
                return ProcessorPyResult(value=15, is_accurate=True, method="fallback")

            elif any(term in cpu_name for term in ['server', 'workstation', 'enterprise']):
                return ProcessorPyResult(value=150, is_accurate=True, method="fallback")

            elif any(term in cpu_name for term in ['gaming', 'enthusiast', 'overclockable']):
                return ProcessorPyResult(value=95, is_accurate=True, method="fallback")

            return ProcessorPyResult("n/a", None, None)

        def transistor_count(self) -> ProcessorPyResult:
            """Estimate CPU transistor count based on lithography and die size.

            Returns:
                ProcessorPyResult: Estimated transistor count as human-readable string
            """
            try:
                cpu_name = self.name().value
                process_node = self.lithography().value  # in nm
                die_size = self._get_die_size()  # in mm²

                if not process_node or not die_size:
                    return ProcessorPyResult("n/a", None, "Missing lithography or die size")

                # Improved density model with better empirical constants
                # Based on actual transistor densities from modern processors
                node_nm = float(process_node)

                # More accurate density estimation based on real-world data
                if node_nm <= 3:  # 3nm and below
                    base_density = 300_000_000  # ~300M transistors/mm²
                elif node_nm <= 5:  # 4-5nm
                    base_density = 170_000_000  # ~170M transistors/mm²
                elif node_nm <= 7:  # 6-7nm
                    base_density = 100_000_000  # ~100M transistors/mm²
                elif node_nm <= 10:  # 8-10nm
                    base_density = 50_000_000  # ~50M transistors/mm²
                elif node_nm <= 14:  # 12-14nm
                    base_density = 30_000_000  # ~30M transistors/mm²
                elif node_nm <= 22:  # 16-22nm
                    base_density = 15_000_000  # ~15M transistors/mm²
                elif node_nm <= 32:  # 28-32nm
                    base_density = 8_000_000  # ~8M transistors/mm²
                elif node_nm <= 45:  # 40-45nm
                    base_density = 4_000_000  # ~4M transistors/mm²
                else:  # 65nm and above
                    base_density = 2_000_000  # ~2M transistors/mm²

                # Apply architecture efficiency factor (modern designs are more efficient)
                if cpu_name and any(arch in cpu_name.lower() for arch in ['zen', 'core', 'm1', 'm2', 'm3']):
                    efficiency_factor = 1.2  # Modern architectures pack more efficiently
                else:
                    efficiency_factor = 1.0

                density = base_density * efficiency_factor
                estimated_count = int(density * die_size)

                # Better formatting with proper rounding
                if estimated_count >= 1_000_000_000:
                    billions = estimated_count / 1_000_000_000
                    if billions >= 10:
                        value = f"{billions:.0f} billion"
                    else:
                        value = f"{billions:.1f} billion".replace(".0 ", " ")
                elif estimated_count >= 1_000_000:
                    millions = estimated_count / 1_000_000
                    if millions >= 100:
                        value = f"{millions:.0f} million"
                    else:
                        value = f"{millions:.1f} million".replace(".0 ", " ")
                else:
                    value = f"{estimated_count:,}"

                return ProcessorPyResult(
                    value=value,
                    is_accurate=False,
                    method=f"Estimated using {node_nm}nm node and {die_size}mm² die (~{int(density / 1_000_000):.0f}M transistors/mm²)"
                )

            except Exception as e:
                return ProcessorPyResult("n/a", None, f"Error during estimation: {e}")

        def code_name(self) -> ProcessorPyResult:
            """This method will determine the cpu code name string eg: ivy bridge, coffee lake"""
            try:
                cpu_name = self.name().value
                if not cpu_name:
                    return ProcessorPyResult("n/a", None, "CPU name not available")

                cpu_lower = cpu_name.lower()

                # Intel code names mapping
                intel_codenames = {
                    # Recent generations
                    ('13th gen', 'raptor lake', 'i3-13', 'i5-13', 'i7-13', 'i9-13'): 'Raptor Lake',
                    ('12th gen', 'alder lake', 'i3-12', 'i5-12', 'i7-12', 'i9-12'): 'Alder Lake',
                    ('11th gen', 'rocket lake', 'tiger lake', 'i3-11', 'i5-11', 'i7-11',
                     'i9-11'): 'Tiger Lake/Rocket Lake',
                    ('10th gen', 'comet lake', 'ice lake', 'i3-10', 'i5-10', 'i7-10', 'i9-10'): 'Comet Lake/Ice Lake',
                    ('9th gen', 'coffee lake', 'i3-9', 'i5-9', 'i7-9', 'i9-9'): 'Coffee Lake Refresh',
                    ('8th gen', 'i3-8', 'i5-8', 'i7-8', 'i9-8'): 'Coffee Lake',
                    ('7th gen', 'kaby lake', 'i3-7', 'i5-7', 'i7-7'): 'Kaby Lake',
                    ('6th gen', 'skylake', 'i3-6', 'i5-6', 'i7-6'): 'Skylake',
                    ('5th gen', 'broadwell', 'i3-5', 'i5-5', 'i7-5'): 'Broadwell',
                    ('4th gen', 'haswell', 'i3-4', 'i5-4', 'i7-4'): 'Haswell',
                    ('3rd gen', 'ivy bridge', 'i3-3', 'i5-3', 'i7-3'): 'Ivy Bridge',
                    ('2nd gen', 'sandy bridge', 'i3-2', 'i5-2', 'i7-2'): 'Sandy Bridge',
                    ('1st gen', 'nehalem', 'westmere', 'i3-1', 'i5-1', 'i7-1'): 'Nehalem/Westmere',
                }

                # AMD code names mapping
                amd_codenames = {
                    ('ryzen 7000', 'zen 4', '7950x', '7900x', '7700x', '7600x'): 'Zen 4 (Raphael)',
                    ('ryzen 6000', 'zen 3+', '6980hx', '6900hx', '6800h'): 'Zen 3+ (Rembrandt)',
                    ('ryzen 5000', 'zen 3', '5950x', '5900x', '5800x', '5600x'): 'Zen 3 (Vermeer)',
                    ('ryzen 4000', 'zen 2', '4750g', '4650g', '4350g'): 'Zen 2 (Renoir)',
                    ('ryzen 3000', '3950x', '3900x', '3800x', '3700x', '3600x'): 'Zen 2 (Matisse)',
                    ('ryzen 2000', 'zen+', '2700x', '2600x', '2400g', '2200g'): 'Zen+ (Pinnacle Ridge)',
                    ('ryzen 1000', 'zen', '1800x', '1700x', '1600x', '1500x'): 'Zen (Summit Ridge)',
                }

                # Apple code names mapping
                apple_codenames = {
                    ('m3', 'apple m3'): 'M3 (A17 Pro based)',
                    ('m2', 'apple m2'): 'M2 (A15 based)',
                    ('m1', 'apple m1'): 'M1 (A14 based)',
                    ('a17', 'apple a17'): 'A17 Pro (Bionic)',
                    ('a16', 'apple a16'): 'A16 Bionic',
                    ('a15', 'apple a15'): 'A15 Bionic',
                    ('a14', 'apple a14'): 'A14 Bionic',
                }

                # Check Intel codenames
                for keywords, codename in intel_codenames.items():
                    if any(keyword in cpu_lower for keyword in keywords):
                        return ProcessorPyResult(codename, True, f"Identified from CPU name: {cpu_name}")

                # Check AMD codenames
                for keywords, codename in amd_codenames.items():
                    if any(keyword in cpu_lower for keyword in keywords):
                        return ProcessorPyResult(codename, True, f"Identified from CPU name: {cpu_name}")

                # Check Apple codenames
                for keywords, codename in apple_codenames.items():
                    if any(keyword in cpu_lower for keyword in keywords):
                        return ProcessorPyResult(codename, True, f"Identified from CPU name: {cpu_name}")

                # Fallback: try to extract generation info
                import re

                # Intel generation pattern
                intel_gen_match = re.search(r'i[3579]-(\d{1,2})\d{3}', cpu_lower)
                if intel_gen_match:
                    gen = int(intel_gen_match.group(1))
                    if gen >= 13:
                        return ProcessorPyResult("Raptor Lake (13th gen)", False,
                                                 f"Estimated from model number: {cpu_name}")
                    elif gen >= 12:
                        return ProcessorPyResult("Alder Lake (12th gen)", False,
                                                 f"Estimated from model number: {cpu_name}")
                    elif gen >= 11:
                        return ProcessorPyResult("Tiger Lake/Rocket Lake (11th gen)", False,
                                                 f"Estimated from model number: {cpu_name}")
                    elif gen >= 10:
                        return ProcessorPyResult("Comet Lake/Ice Lake (10th gen)", False,
                                                 f"Estimated from model number: {cpu_name}")

                # AMD Ryzen generation pattern
                ryzen_match = re.search(r'ryzen.*(\d)000', cpu_lower)
                if ryzen_match:
                    gen = int(ryzen_match.group(1))
                    if gen >= 7:
                        return ProcessorPyResult("Zen 4", False, f"Estimated from model number: {cpu_name}")
                    elif gen >= 5:
                        return ProcessorPyResult("Zen 3", False, f"Estimated from model number: {cpu_name}")
                    elif gen >= 3:
                        return ProcessorPyResult("Zen 2", False, f"Estimated from model number: {cpu_name}")

                return ProcessorPyResult("Unknown", False, f"Could not determine codename for: {cpu_name}")

            except Exception as e:
                return ProcessorPyResult("n/a", None, f"Error determining codename: {e}")


        def lithography(self) -> ProcessorPyResult:
            """ This method will get the cpu lithography in nm"""
            """
            Enhanced CPU lithography (process node) detection in nanometers.
            Supports Intel, AMD, ARM, Qualcomm, Apple, and other processors.

            Args:
                cpu_name: CPU name/model string

            Returns:
                int: Process node in nm (e.g., 7, 5, 3) or None if unknown
            """

            # Declare cpu name string
            cpu_name: str = self.name().value.lower().strip()

            # Direct nm extraction (highest priority)
            nm_match = re.search(r"(\d+) ?nm", cpu_name)

            if nm_match:
                return ProcessorPyResult(value=int(nm_match.group(1)), is_accurate=True, method="estimated")

            # Intel processors - comprehensive detection
            if any(x in cpu_name for x in ("intel", "core", "xeon", "pentium", "celeron", "atom")):
                # Extract generation/model numbers
                gen_match = re.search(r"(?:gen(?:eration)?[ -]?|i[357][ -]?)(\d+)", cpu_name)
                model_match = re.search(r"(\d{4,5})[a-z]*", cpu_name)

                # 14th Gen (Raptor Lake Refresh) - Intel 7
                if (gen_match and int(gen_match.group(1)) == 14) or \
                        (model_match and str(model_match.group(1)).startswith("14")):
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                # 13th Gen (Raptor Lake) - Intel 7
                if (gen_match and int(gen_match.group(1)) == 13) or \
                        (model_match and str(model_match.group(1)).startswith("13")) or \
                        "raptor lake" in cpu_name:
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                # 12th Gen (Alder Lake) - Intel 7
                if (gen_match and int(gen_match.group(1)) == 12) or \
                        (model_match and str(model_match.group(1)).startswith("12")) or \
                        "alder lake" in cpu_name:
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                # 11th Gen (Tiger Lake/Rocket Lake) - 10nm SuperFin
                if (gen_match and int(gen_match.group(1)) == 11) or \
                        (model_match and str(model_match.group(1)).startswith("11")) or \
                        "tiger lake" in cpu_name or "rocket lake" in cpu_name:
                    return ProcessorPyResult(value=10, is_accurate=True, method="estimated")

                # 10th Gen (Ice Lake/Comet Lake) - 10nm/14nm
                if (gen_match and int(gen_match.group(1)) == 10) or \
                        (model_match and str(model_match.group(1)).startswith("10")) or \
                        "ice lake" in cpu_name:
                    return ProcessorPyResult(value=10, is_accurate=True, method="estimated")
                if "comet lake" in cpu_name:
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")

                # 9th Gen and earlier - 14nm
                if (gen_match and int(gen_match.group(1)) <= 9) or \
                        (model_match and int(str(model_match.group(1))[0:2]) <= 9):
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")

                # Specific Intel series
                if any(x in cpu_name for x in ["coffee lake", "kaby lake", "skylake"]):
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")
                if "broadwell" in cpu_name:
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")
                if "haswell" in cpu_name:
                    return ProcessorPyResult(value=22, is_accurate=True, method="estimated")
                if "ivy bridge" in cpu_name:
                    return ProcessorPyResult(value=22, is_accurate=True, method="estimated")
                if "sandy bridge" in cpu_name:
                    return ProcessorPyResult(value=32, is_accurate=True, method="estimated")

                # Atom processors
                if "atom" in cpu_name:
                    if any(x in cpu_name for x in ("tremont", "goldmont")):
                        return ProcessorPyResult(value=10, is_accurate=True, method="estimated")
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")

                return ProcessorPyResult(value=14, is_accurate=True, method="estimated")  # Default for older Intel

            # AMD processors
            if any(x in cpu_name for x in ("amd", "ryzen", "epyc", "threadripper", "athlon")):
                # Check for APU models first (they have different architectures than their series)

                # Ryzen 2000 series APUs (Zen) - 14nm
                if re.search(r"2[24]00g", cpu_name):  # 2200G, 2400G
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")

                # Ryzen 3000 series APUs (Zen+) - 12nm
                if re.search(r"3[24]00g", cpu_name):  # 3200G, 3400G
                    return ProcessorPyResult(value=12, is_accurate=True, method="estimated")

                # Now check regular series (non-APU)

                # Ryzen 7000 series (Zen 4) - TSMC 5nm
                if re.search(r"[78]\d{3}[a-z]*", cpu_name) or "zen 4" in cpu_name:
                    return ProcessorPyResult(value=5, is_accurate=True, method="estimated")

                # Ryzen 6000 series (Zen 3+) - TSMC 6nm
                if re.search(r"6\d{3}[a-z]*", cpu_name) or "zen 3+" in cpu_name:
                    return ProcessorPyResult(value=6, is_accurate=True, method="estimated")

                # Ryzen 5000 series (Zen 3) - TSMC 7nm
                if re.search(r"5\d{3}[a-z]*", cpu_name) or "zen 3" in cpu_name:
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                # Ryzen 4000 series (Zen 2) - TSMC 7nm
                if re.search(r"4\d{3}[a-z]*", cpu_name) or "zen 2" in cpu_name:
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                # Ryzen 3000 series (Zen 2) - TSMC 7nm
                if re.search(r"3\d{3}[a-z]*", cpu_name):
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                # Ryzen 2000 series (Zen+) - 12nm
                if re.search(r"2\d{3}[a-z]*", cpu_name) or "zen+" in cpu_name:
                    return ProcessorPyResult(value=12, is_accurate=True, method="estimated")

                # Ryzen 1000 series (Zen) - 14nm
                if re.search(r"1\d{3}[a-z]*", cpu_name) or "zen" in cpu_name:
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")

                # EPYC processors
                if "epyc" in cpu_name:
                    if "genoa" in cpu_name or "9004" in cpu_name:
                        return ProcessorPyResult(value=5, is_accurate=True, method="estimated")  # Zen 4
                    if "milan" in cpu_name or "7003" in cpu_name:
                        return ProcessorPyResult(value=7, is_accurate=True, method="estimated")  # Zen 3
                    if "rome" in cpu_name or "7002" in cpu_name:
                        return ProcessorPyResult(value=7, is_accurate=True, method="estimated")  # Zen 2
                    return ProcessorPyResult(value=14, is_accurate=True, method="estimated")

                return ProcessorPyResult(value=7, is_accurate=True, method="estimated")  # Default for modern AMD

            # ARM/Qualcomm processors
            if any(x in cpu_name for x in ("arm", "qualcomm", "snapdragon", "cortex")):
                # Snapdragon 8 series
                if "8 gen 3" in cpu_name or "8cx gen 3" in cpu_name:
                    return ProcessorPyResult(value=4, is_accurate=True, method="estimated")  # TSMC 4nm
                if "8 gen 2" in cpu_name or "8cx gen 2" in cpu_name:
                    return ProcessorPyResult(value=4, is_accurate=True, method="estimated")  # TSMC 4nm
                if "8 gen 1" in cpu_name or "8cx" in cpu_name:
                    return ProcessorPyResult(value=4, is_accurate=True, method="estimated")  # Samsung 4nm
                if "888" in cpu_name or "8cx" in cpu_name:
                    return ProcessorPyResult(value=5, is_accurate=True, method="estimated")  # Samsung 5nm

                # ARM Cortex series
                if any(x in cpu_name for x in ("cortex-x", "cortex-a78", "cortex-a77")):
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")
                if any(x in cpu_name for x in ("cortex-a76", "cortex-a75")):
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")

                return ProcessorPyResult(value=7, is_accurate=True, method="estimated")  # Default for ARM

            # Apple Silicon
            if any(x in cpu_name for x in ("apple", "m1", "m2", "m3", "a1")):
                # M3 series - TSMC N3
                if "m3" in cpu_name:
                    return ProcessorPyResult(value=3, is_accurate=True, method="estimated")

                # M2 series - TSMC N5P
                if "m2" in cpu_name:
                    return ProcessorPyResult(value=5, is_accurate=True, method="estimated")

                # M1 series - TSMC N5
                if "m1" in cpu_name:
                    return ProcessorPyResult(value=5, is_accurate=True, method="estimated")

                # A-series chips
                if re.search(r"a1[6-9]", cpu_name):
                    return ProcessorPyResult(value=3, is_accurate=True, method="estimated")  # A16-A19
                if re.search(r"a1[4-5]", cpu_name):
                    return ProcessorPyResult(value=5, is_accurate=True, method="estimated")  # A14-A15
                if re.search(r"a1[2-3]", cpu_name):
                    return ProcessorPyResult(value=7, is_accurate=True, method="estimated")   # A12-A13

                # Default for Apple Silicon
                return ProcessorPyResult(value=5, is_accurate=True, method="estimated")

            return ProcessorPyResult("n/a", None, None)

        def is_virtualization(self) -> ProcessorPyResult:
            """
            Checks CPU virtualization support using Windows Registry (winreg).

            Returns: ProcessorPyResult

            """
            try:
                # Open the processor registry key
                with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
                ) as key:

                    # Method 1: Check FeatureSet (most reliable)
                    try:
                        features, _ = winreg.QueryValueEx(key, "FeatureSet")
                        if features & 0x00000001:  # VT-x/AMD-V bit
                            return ProcessorPyResult(True, True, "winreg_feature_set")

                        return ProcessorPyResult("disabled", True, "winreg_feature_set")
                    except FileNotFoundError as e:

                        if self._dev_mode:
                            print(f"[ERROR] : {e}")

                    # Method 2: Check CPUID (fallback)
                    try:
                        vendor, _ = winreg.QueryValueEx(key, "VendorIdentifier")
                        if "GenuineIntel" in vendor:
                            # Check Intel VT-x via CPUID
                            cpuid, _ = winreg.QueryValueEx(key, "CPUID")
                            if cpuid[3] & (1 << 5):  # Bit 5 in ECX indicates VT-x
                                return ProcessorPyResult(True, True, "winreg_cpuid")

                        elif "AuthenticAMD" in vendor:
                            # Check AMD-V via CPUID
                            cpuid, _ = winreg.QueryValueEx(key, "CPUID")
                            if cpuid[3] & (1 << 2):  # Bit 2 in ECX indicates AMD-V
                                return ProcessorPyResult(True, True, "winreg_cpuid")

                    except FileNotFoundError as e:

                        if self._dev_mode:
                            print(f"[ERROR] : {e}")

                    # Method 3: Check brand string (last resort)
                    try:
                        brand, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                        if "VT-x" in brand or "AMD-V" in brand:
                            return ProcessorPyResult("enabled", False, "winreg_brand")

                    except FileNotFoundError as e:

                        if self._dev_mode:
                            print(f"[ERROR] : {e}")

            except Exception as e:

                if self._dev_mode:
                    print(f"[ERROR] : {e}")

            return ProcessorPyResult("n/a", None, None)

        def is_support_boost(self) -> ProcessorPyResult:
            """
            Detects if the CPU supports Turbo Boost or equivalent technology.
            Works for Intel, AMD, ARM, Apple, and Qualcomm processors on Windows.

            Returns: ProcessorPyResult
            """
            try:

                # For testing purposes, determine vendor from CPU name
                cpu_name: str = self.name().value
                vendor: str = self.vendor().value

                # Intel Turbo Boost
                if "intel" in vendor or "genuineintel" in vendor:
                    try:
                        # Try to check Intel Turbo Boost registry key
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                            r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\bc5038f7-23e0-4960-96da-33abaf5935ec") as key:
                            # If the registry key exists, Turbo Boost is likely supported
                            return ProcessorPyResult(True, True, "registry")

                    except FileNotFoundError:
                        pass  # Registry key doesn't exist, fall back to pattern matching

                    # Fallback to model pattern matching
                    if re.search(r'i[3-9]-\d+|xeon|core\s+i[3-9]', cpu_name):
                        return ProcessorPyResult(True, False, "estimated")
                    elif re.search(r'pentium|celeron|atom', cpu_name):
                        return ProcessorPyResult(False, True, "estimated")

                    return ProcessorPyResult("n/a", None, None)

                # AMD Precision Boost / Precision Boost Overdrive
                elif "amd" in vendor or "authenticamd" in vendor:
                    if re.search(r'ryzen|threadripper|epyc', cpu_name):
                        return ProcessorPyResult(True, True, "estimated")

                    elif re.search(r'fx-\d+|a\d+-\d+|athlon', cpu_name):
                        return ProcessorPyResult(False, True, "estimated")

                    return ProcessorPyResult("n/a", None, None)

                # ARM DynamIQ (Windows on ARM)
                elif "arm" in vendor or "qualcomm" in vendor:
                    if re.search(r'snapdragon\s*8\d+', cpu_name):
                        return ProcessorPyResult("supported", True, "arm_flagship_pattern")
                    elif re.search(r'snapdragon', cpu_name):
                        return ProcessorPyResult(True, False, "estimated")
                    return ProcessorPyResult("n/a", None, None)

                # Apple Silicon (M1/M2/M3 under Windows ARM via virtualization)
                elif "apple" in vendor or re.search(r'm[1-3]\s*(pro|max|ultra)?', cpu_name):
                    return ProcessorPyResult(True, True, "estimated")

                else:
                    return ProcessorPyResult("n/a", None, None)

            except Exception as e:
                return ProcessorPyResult("unknown", False, f"detection_failed: {str(e)}")

        def is_ecc(self) -> ProcessorPyResult:
            """

            Determines if a CPU supports ECC (Error-Correcting Code) memory.
            look : https://en.wikipedia.org/wiki/Error_correction_code

            Returns: ProcessorPyResult

            """

            try:
                cpu_name = self.name.value
                vendor = self.vendor.value

                # Intel ECC support
                if "intel" in vendor or "genuineintel" in vendor:
                    if any(keyword in cpu_name for keyword in
                           ["xeon", "atom c", "core i9-", "core i7-10", "core i7-11"]):
                        if "xeon" in cpu_name or "atom c" in cpu_name or "x" in cpu_name:
                            return ProcessorPyResult(True, True, "intel_model")
                    return ProcessorPyResult(False, True, "intel_model")

                # AMD ECC support
                elif "amd" in vendor or "authenticamd" in vendor:
                    if any(keyword in cpu_name for keyword in ["epyc", "ryzen pro", "threadripper pro"]):
                        return ProcessorPyResult(True, True, "amd_model")
                    return ProcessorPyResult(False, True, "amd_model")

                # Apple Silicon
                elif "apple" in vendor or "apple silicon" in cpu_name or "m1" in cpu_name or "m2" in cpu_name or "m3" in cpu_name:
                    if any(tag in cpu_name for tag in ["m1 max", "m1 ultra", "m2 max", "m2 ultra", "m3 max"]):
                        return ProcessorPyResult(True, True, "apple_silicon")
                    return ProcessorPyResult(False, True, "apple_silicon")

                # ARM / Qualcomm / MediaTek
                elif "arm" in vendor or "qualcomm" in vendor or "snapdragon" in cpu_name:
                    if "neoverse" in cpu_name or "ampere" in cpu_name:
                        return ProcessorPyResult(True, True, "arm_server")
                    return ProcessorPyResult(False, True, "arm_mobile")

            except Exception:
                pass

            return ProcessorPyResult(False, False, "detection_failed")

        @property
        def supported_memory_types(self) -> ProcessorPyResult:
            """
            Detects supported memory types (DDR3, DDR4, DDR5) based on CPU model patterns.

            Returns:
                ProcessorPyResult:
                    - value: List of supported types (e.g., ["DDR4", "DDR5"])
                    - is_accurate: True if based on model patterns, False if estimated
                    - method: Detection method used
            """
            try:
                cpu_name = self.name().value
                cpu_brand = self.vendor().value

                # Intel processors
                if "intel" in cpu_brand:
                    if "xeon" in cpu_name:
                        # Newer Xeon series (Sapphire Rapids, Emerald Rapids)
                        if any(series in cpu_name for series in ("8400", "8500", "6400", "6500")):
                            return ProcessorPyResult(("DDR5",), True, "intel_xeon_ddr5_only")

                        # Ice Lake and newer support DDR4/DDR5
                        elif any(series in cpu_name for series in ("8300", "6300", "5300")):
                            return ProcessorPyResult(("DDR4", "DDR5"), True, "intel_xeon_hybrid")

                        # Older Xeon E-series
                        elif "e3-" in cpu_name or "e-21" in cpu_name:
                            return ProcessorPyResult(("DDR4",), True, "intel_xeon_e_series")

                        # Default modern Xeon
                        return ProcessorPyResult(("DDR4", "DDR5"), True, "intel_xeon_modern")

                    elif "core i" in cpu_name:
                        # Extract generation from model number

                        gen_match = re.search(r'(\d{1,2})(?:th|rd|nd|st)?\s*gen|i[3579]-(\d{1,2})\d{3}', cpu_name)
                        if gen_match:
                            gen = int(gen_match.group(1) or gen_match.group(2))
                            if gen >= 12:  # 12th gen Alder Lake and newer
                                return ProcessorPyResult(("DDR4", "DDR5"), True, "intel_core_12th_plus")

                            elif gen >= 6:  # 6th gen Skylake to 11th gen
                                return ProcessorPyResult(("DDR4",), True, "intel_core_6th_11th")

                            elif gen >= 1:  # 1st to 5th gen
                                return ProcessorPyResult(("DDR3",), True, "intel_core_legacy")

                        # Fallback pattern matching for Core processors
                        if any(gen in cpu_name for gen in ("12", "13", "14")):
                            return ProcessorPyResult(("DDR4", "DDR5"), True, "intel_core_modern")
                        return ProcessorPyResult(("DDR4",), True, "intel_core_fallback")

                    elif "pentium" in cpu_name or "celeron" in cpu_name:
                        return ProcessorPyResult(("DDR4",), True, "intel_budget")

                # AMD processors
                elif "amd" in cpu_brand:
                    if "epyc" in cpu_name:
                        # Extract series number

                        series_match = re.search(r'epyc\s*(\d{4})', cpu_name)
                        if series_match:
                            series = int(series_match.group(1))
                            if series >= 9004:  # EPYC 9004 series (Genoa)
                                return ProcessorPyResult(("DDR5"), True, "amd_epyc_ddr5")
                            elif series >= 7003:  # EPYC 7003 series (Milan)
                                return ProcessorPyResult(("DDR4",), True, "amd_epyc_7003")

                        # Fallback for EPYC
                        if any(gen in cpu_name for gen in ("9", "8")):
                            return ProcessorPyResult(("DDR5",), True, "amd_epyc_modern")

                        return ProcessorPyResult(("DDR4",), True, "amd_epyc_legacy")

                    elif "ryzen" in cpu_name:
                        # Extract generation

                        gen_match = re.search(r'ryzen\s*[3579]?\s*(\d{1})\d{3}', cpu_name)
                        if gen_match:
                            gen = int(gen_match.group(1))
                            if gen >= 7:  # Ryzen 7000 series (Zen 4)
                                return ProcessorPyResult(("DDR5",), True, "amd_ryzen_7000_plus")
                            elif gen >= 3:  # Ryzen 3000-6000 series
                                return ProcessorPyResult(("DDR4",), True, "amd_ryzen_3000_6000")
                            elif gen >= 1:  # Ryzen 1000-2000 series
                                return ProcessorPyResult(("DDR4",), True, "amd_ryzen_1000_2000")

                        # Fallback pattern matching
                        if any(gen in cpu_name for gen in ("7", "8", "9")):
                            return ProcessorPyResult(("DDR5",), True, "amd_ryzen_modern")
                        return ProcessorPyResult(("DDR4",), True, "amd_ryzen_fallback")

                    elif "threadripper" in cpu_name:
                        if any(gen in cpu_name for gen in ("7", "8")):
                            return ProcessorPyResult(("DDR5",), True, "amd_threadripper_modern")
                        return ProcessorPyResult(("DDR4",), True, "amd_threadripper_legacy")

                # ARM processors
                elif "arm" in cpu_brand or "qualcomm" in cpu_brand:
                    if "snapdragon" in cpu_name:

                        # Extract model number
                        model_match = re.search(r'(\d{3})', cpu_name)
                        if model_match:
                            model = int(model_match.group(1))

                            if model >= 8:  # Snapdragon 8xx series
                                return ProcessorPyResult(("LPDDR5",), True, "snapdragon_8xx")

                            elif model >= 7:  # Snapdragon 7xx series
                                return ProcessorPyResult(("LPDDR4X", "LPDDR5"), True, "snapdragon_7xx")

                        return ProcessorPyResult(("LPDDR5",), True, "snapdragon_modern")

                    return ProcessorPyResult(("LPDDR4",), True, "arm_generic")

                # Apple Silicon
                elif "apple" in cpu_brand:
                    if any(chip in cpu_name for chip in ("m1", "m2", "m3")):
                        return ProcessorPyResult(("LPDDR5",), True, "apple_silicon")

                # Fallback for unknown processors
                return ProcessorPyResult(("DDR4",), False, "unknown_processor_fallback")

            except Exception as e:
                error_msg = f"Memory type detection failed: {str(e)}"
                if self._dev_mode:
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    raise

                else:
                    logging.warning(error_msg)

            return ProcessorPyResult("n/a", None, None)

        def supported_memory_channels(self) -> ProcessorPyResult:
            """
            Detects supported memory channels based on CPU model patterns.

            Returns:
                ProcessorPyResult:
                    - value: "single", "dual", "quad", "octa"
                    - is_accurate: True if based on model patterns
                    - method: Detection method used
            """
            try:

                cpu_name = self.name().value
                cpu_brand = self.vendor().value

                # Server/workstation chips typically have more channels
                if "xeon" in cpu_name:
                    # High-end Xeon processors
                    if any(series in cpu_name for series in ["platinum", "gold", "8400", "8500"]):
                        return ProcessorPyResult("octa", True, "xeon_server_high_end")
                    elif any(series in cpu_name for series in ["silver", "bronze", "6400", "5300"]):
                        return ProcessorPyResult("quad", True, "xeon_server_mid_range")
                    elif "e3-" in cpu_name or "e-21" in cpu_name:
                        return ProcessorPyResult("dual", True, "xeon_e_series")
                    return ProcessorPyResult("quad", True, "xeon_default")

                elif "epyc" in cpu_name:
                    # EPYC processors typically support 8-channel
                    return ProcessorPyResult("octa", True, "epyc_server")

                elif "threadripper" in cpu_name:
                    # Threadripper supports quad-channel
                    return ProcessorPyResult("quad", True, "threadripper_hedt")

                # High-end desktop processors
                elif any(model in cpu_name for model in ["core i9", "ryzen 9"]):
                    # Some i9 and Ryzen 9 models support quad-channel
                    if "x" in cpu_name or "extreme" in cpu_name:
                        return ProcessorPyResult("quad", True, "hedt_extreme")
                    return ProcessorPyResult("dual", True, "hedt_mainstream")

                # Standard desktop processors
                elif any(model in cpu_name for model in ["core i", "ryzen"]):
                    return ProcessorPyResult("dual", True, "desktop_standard")

                # Mobile/laptop processors
                elif any(suffix in cpu_name for suffix in ["u", "h", "hs", "hx", "p"]):
                    return ProcessorPyResult("dual", True, "mobile_laptop")

                # ARM/Mobile processors
                elif "snapdragon" in cpu_name or "apple" in cpu_brand:
                    return ProcessorPyResult("dual", True, "mobile_arm")

                # Low-power processors
                elif any(model in cpu_name for model in ["pentium", "celeron", "atom"]):
                    return ProcessorPyResult("single", True, "low_power")

                # Fallback
                return ProcessorPyResult("dual", False, "standard_fallback")

            except Exception as e:
                error_msg = f"Memory channel detection failed: {str(e)}"
                if self._dev_mode:
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    raise
                else:
                    logging.warning(error_msg)

            return ProcessorPyResult("unknown", False, "pattern_match_failed")

        def supported_memory_bandwidth(self, friendly: bool = False) -> ProcessorPyResult:
            """Estimates memory bandwidth - always returns a value."""

            # Memory specs: bandwidth per channel (GB/s) and efficiency
            specs = {
                "DDR3": (12.8, 0.75), "DDR3L": (12.8, 0.75),
                "DDR4": (25.6, 0.80), "DDR5": (38.4, 0.85),
                "LPDDR3": (12.8, 0.70), "LPDDR4": (25.6, 0.75),
                "LPDDR4X": (34.1, 0.78), "LPDDR5": (51.2, 0.82),
                "LPDDR5X": (68.3, 0.85)
            }

            # Channel multipliers
            channels = {"single": 1, "dual": 2, "triple": 3, "quad": 4, "octa": 8}

            # Default to DDR4 dual-channel (most common)
            mem_type = "DDR4"
            channel_count = "dual"
            is_estimated = True

            try:
                # Try to get actual memory type
                if hasattr(self, 'supported_memory_types'):
                    mem_result = getattr(self, 'supported_memory_types', None)
                    if mem_result and hasattr(mem_result, 'value') and mem_result.value:
                        if mem_result.value != ["unknown"] and mem_result.value != "unknown":
                            actual_type = mem_result.value[0] if isinstance(mem_result.value,
                                                                            list) else mem_result.value
                            if actual_type in specs:
                                mem_type = actual_type
                                is_estimated = False

                # Try to get actual channel count
                if hasattr(self, 'supported_memory_channels'):
                    ch_result = getattr(self, 'supported_memory_channels', None)
                    if ch_result and hasattr(ch_result, 'value') and ch_result.value:
                        if ch_result.value != "unknown" and ch_result.value in channels:
                            channel_count = ch_result.value
                            if not is_estimated:  # Only mark as non-estimated if both are accurate
                                is_estimated = False

                # Try processor-based inference for better estimates
                processor_info = ""
                for attr in ['name', 'brand', 'model', 'family']:
                    if hasattr(self, attr):
                        val = getattr(self, attr, "")
                        if val and val != "unknown":
                            processor_info += str(val).lower() + " "

                if processor_info:
                    # Intel generations
                    if any(gen in processor_info for gen in ['12th', '13th', '14th', 'alder', 'raptor']):
                        mem_type = "DDR5"
                    elif any(gen in processor_info for gen in
                             ['8th', '9th', '10th', '11th', 'coffee', 'comet', 'rocket']):
                        mem_type = "DDR4"
                    elif any(gen in processor_info for gen in ['6th', '7th', 'skylake', 'kaby']):
                        mem_type = "DDR4"

                    # AMD generations
                    elif 'ryzen' in processor_info:
                        if any(gen in processor_info for gen in ['7000', '8000']):
                            mem_type = "DDR5"
                        else:
                            mem_type = "DDR4"

                    # Mobile processors often use LPDDR
                    if any(mobile in processor_info for mobile in ['mobile', 'laptop', 'u-', 'h-', 'lp']):
                        if mem_type == "DDR5":
                            mem_type = "LPDDR5"
                        elif mem_type == "DDR4":
                            mem_type = "LPDDR4"
            except:
                pass  # Keep defaults

            # Calculate bandwidth
            base_bw, efficiency = specs[mem_type]
            multiplier = channels[channel_count]

            theoretical = base_bw * multiplier
            practical = theoretical * efficiency

            if friendly:
                suffix = " (estimated)" if is_estimated else ""
                return ProcessorPyResult(f"{practical:.1f} GB/s{suffix}", not is_estimated, "calculated")
            else:
                return ProcessorPyResult(round(practical, 1), not is_estimated, "calculated")

        def supported_memory_size(self, friendly: bool = False) -> ProcessorPyResult:
            """
            Estimates maximum supported memory size based on CPU architecture.

            Args:
                friendly: If True, returns human-readable string (e.g., "128 GB")

            Returns:
                ProcessorPyResult with size in GB or friendly string
            """
            try:
                cpu_name = self.name().value
                cpu_brand = self.vendor().value

                # Server processors - highest capacity
                if "xeon" in cpu_name:
                    if any(series in cpu_name for series in ("platinum", "gold", "8400", "8500")):
                        size = 4096  # 4TB for high-end Xeon
                    elif any(series in cpu_name for series in ("silver", "bronze")):
                        size = 2048  # 2TB for mid-range Xeon
                    elif "e3-" in cpu_name or "e-21" in cpu_name:
                        size = 128  # 128GB for Xeon E-series
                    else:
                        size = 2048  # Default for Xeon

                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "intel_xeon_pattern")

                elif "epyc" in cpu_name:
                    # AMD EPYC supports very high memory capacity
                    size = 4096  # 4TB for modern EPYC
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "amd_epyc_pattern")

                # Workstation/HEDT processors
                elif "threadripper" in cpu_name:
                    size = 512  # 512GB for Threadripper
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "amd_threadripper_pattern")

                elif "core i9" in cpu_name and ("x" in cpu_name or "extreme" in cpu_name):
                    size = 256  # 256GB for i9 Extreme
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "intel_hedt_pattern")

                # High-end desktop processors
                elif "core i9" in cpu_name or "ryzen 9" in cpu_name:
                    size = 128  # 128GB for high-end desktop
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "high_end_desktop_pattern")

                # Standard desktop processors
                elif any(model in cpu_name for model in ["core i7", "core i5", "ryzen 7", "ryzen 5"]):
                    size = 128  # 128GB for mainstream desktop
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "mainstream_desktop_pattern")

                elif any(model in cpu_name for model in ["core i3", "ryzen 3"]):
                    size = 64  # 64GB for entry-level desktop
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "entry_desktop_pattern")

                # Mobile processors
                elif any(suffix in cpu_name for suffix in ["u", "h", "hs", "hx", "p"]):
                    if "h" in cpu_name:
                        size = 64  # 64GB for mobile H-series
                    else:
                        size = 32  # 32GB for mobile U-series
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "mobile_pattern")

                # ARM/Mobile processors
                elif "snapdragon" in cpu_name:
                    size = 16  # 16GB typical for Snapdragon
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "snapdragon_pattern")

                elif "apple" in cpu_brand:
                    if "m1" in cpu_name or "m2" in cpu_name or "m3" in cpu_name:
                        size = 128  # Apple Silicon can support up to 128GB
                        value = f"{size} GB" if friendly else size
                        return ProcessorPyResult(value, True, "apple_silicon_pattern")

                # Budget processors
                elif any(model in cpu_name for model in ("pentium", "celeron", "atom")):
                    size = 32  # 32GB for budget processors
                    value = f"{size} GB" if friendly else size
                    return ProcessorPyResult(value, True, "budget_pattern")

                # Fallback for unknown processors
                size = 64  # Conservative default
                value = f"{size} GB" if friendly else size
                return ProcessorPyResult(value, False, "unknown_processor_fallback")

            except Exception as e:
                error_msg = f"Memory size detection failed: {str(e)}"
                if self._dev_mode:
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                    raise

            return ProcessorPyResult("n/a", None, None)


elif Const.platform == "linux":

    class Processor(_Processor):

        def __init__(self, dev_mode: bool = False) -> None:
            super().__init__()

            # Declare basic constants
            self._dev_mode = dev_mode


else:
    raise ProcessorPyException()


if __name__ == "__main__":
    sys.exit(0)
