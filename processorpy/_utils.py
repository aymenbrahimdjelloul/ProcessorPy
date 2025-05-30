"""
@author : Aymen Brahim Djelloul
version : 0.1
date : 28.05.2025
license : MIT

"""

# IMPORTS
import sys
import os
import json
import time
import hashlib
import requests
import html
from dataclasses import dataclass


@dataclass
class ProcessorPyResult:
    string: str | int | float | bool
    is_accurate: bool | None


class Const:
    """Const class contains utility logic constants"""

    # Define cache handler constants
    cache_dir: str = ".cache"
    cache_ext: str = ".bin"
    cache_expires: int = 60 * 60 * 24  # 24 hours

    # Define online search constants
    search_websites: tuple = ("",)
    headers: dict = {}
    timeout: int = 5

    # Define updater Constants
    latest_version_url: str = "https://api.github.com/repos/aymenbrahimdjelloul/ProcessorPy/releases/latest"


class CacheHandler:
    """Sophisticated caching system with validation and expiration"""

    def __init__(self, developer_mode: bool = False) -> None:
        self.dev_mode: bool = developer_mode
        self.cache_duration: int = Const.cache_expires
        self.machine_id: int = self._get_machine_id()

        os.makedirs(Const.cache_dir, exist_ok=True)

        # Find a valid cache file
        self.cache_file_path: str | None = self._find_cache()
        self._cache_data: dict | None = None
        self.is_cache: bool = False

        if self.cache_file_path and self._is_cache_valid(self.cache_file_path):

            self.is_cache = True
            self._cache_data = self._load_cache(self.cache_file_path)

            # Print developer message
            if self.dev_mode:
                print("[INFO] : Use cache")

                print(self._cache_data)

    def _find_cache(self) -> str | None:
        """Find and return a valid cache file path for this machine ID"""
        for fname in os.listdir(Const.cache_dir):
            if fname.startswith(str(self.machine_id)) and fname.endswith(Const.cache_ext):
                full_path = os.path.join(Const.cache_dir, fname)
                if self._is_cache_valid(full_path):
                    return full_path
        return None

    @staticmethod
    def _get_machine_id() -> int:
        unique_str = os.getenv("COMPUTERNAME") or os.getenv("HOSTNAME") or "default_id"
        return int(hashlib.md5(unique_str.encode()).hexdigest(), 16) % (10 ** 8)

    @staticmethod
    def _xor_bytes(data: bytes, key: int = 42) -> bytes:
        return bytes(b ^ key for b in data)

    @staticmethod
    def _clear_cache(filename: str) -> None:
        """ This method will clear the cache file"""
        os.remove(filename)

    def _corrupt_cache(self, data: dict) -> bytes:
        json_str = json.dumps(data)
        return self._xor_bytes(json_str.encode("utf-8"))

    def _restore_cache(self, data: bytes) -> dict:
        raw = self._xor_bytes(data)
        return json.loads(raw.decode("utf-8"))

    def _is_cache_valid(self, filepath: str) -> bool:
        """Validate cache filename structure, expiration, and existence"""
        try:
            if not os.path.isfile(filepath):
                return False

            filename = os.path.basename(filepath)
            name = os.path.splitext(filename)[0]
            file_mid_str, file_ts_str = name.split("_")

            file_mid = int(file_mid_str)
            file_ts = float(file_ts_str)

            if file_mid != self.machine_id:
                # Clean file
                self._clear_cache(filename)

                return False
            if (time.time() - file_ts) > self.cache_duration:
                # Clean file
                self._clear_cache(filename)

                return False

            return True

        except (ValueError, OSError, IndexError):
            # Clean file
            self._clear_cache(filename)

            return False

    def _load_cache(self, cache_file: str) -> dict:
        """ This method will load the cache file"""

        try:
            with open(cache_file, "rb") as f:
                corrupted_data = f.read()
                restored = self._restore_cache(corrupted_data)
                return restored.get("payload", {})
        except Exception as e:
            if self.dev_mode:
                print(f"[DEBUG] Cache load error: {e}")
            return {}

    def get_cached_data(self, key) -> str | int | None:
        return self._cache_data.get(key) if self._cache_data else None

    def set_cache(self, data: dict) -> None:
        """Create a new cache file with machine ID and timestamp"""
        timestamp = int(time.time())
        filename = f"{self.machine_id}_{timestamp}{Const.cache_ext}"
        self.cache_file_path = os.path.join(Const.cache_dir, filename)

        wrapped = {
            "timestamp": timestamp,
            "machine_id": self.machine_id,
            "payload": data
        }
        corrupted = self._corrupt_cache(wrapped)
        with open(self.cache_file_path, "wb") as f:
            f.write(corrupted)


class SensorSimulator:

    def __init__(self) -> None:
        pass

    def get_temperature(self) -> float:
        """ This method will simulate the temperature sensor readings"""

    def get_voltage(self) -> float:
        """ This method will simulate the voltage sensor readings"""

    def get_usage(self, per_core: bool = False) -> int | tuple:
        """ This method will simulate the usage sensor readings per core"""

    def get_clock_speed(self, per_core: bool = False) -> int | tuple:
        """ This method will simulate the clock speed sensor readings per core"""


class Updater:

    def __init__(self, version: float) -> None:

        # Define current version
        self.version: float = version

        # Create requests session
        self.r_session = requests.Session()

    def is_update(self) -> bool:
        """ This method will check if there is new updates"""

    def get_latest_version_desc(self) -> dict:
        """ This method will get the latest version data like size and date and description and """
        # Make a request to get the latest update data
        self.update_data = requests.get(Const.latest_version_url).json()

        # Define variables
        self.download_link: str = self.update_data['assets'][0]['browser_download_url']

class OnlineSearcher:

    def __init__(self, cpu_name: str) -> None:

        # Define constants
        self.cpu_name = cpu_name

    def get_value(self, query: str) -> str:
        """ This method will get the requested value online"""


if __name__ == '__main__':
    sys.exit(0)
