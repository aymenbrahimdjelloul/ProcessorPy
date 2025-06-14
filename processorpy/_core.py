"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.


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
from pathlib import Path
from typing import Union, Optional, Dict, Any


@dataclass
class ProcessorPyResult:
    """Holds a single data point extracted from CPU info, along with metadata."""

    value: Union[str, int, float, bool]
    is_accurate: Optional[bool]
    method: Optional[str]


class ProcessorPyException(Exception):
    pass


class Const:
    """Const class contains utility logic constants"""

    author: str = "Aymen Brahim Djelloul"
    version: str = "1.1"

    # Define cache handler constants
    cache_dir: str = ".cache"
    cache_ext: str = ".bin"
    cache_expires: int = 60 * 60 * 24  # 24 hours

    # Define online search constants
    search_websites: tuple = ("",)
    headers: dict = {}
    timeout: int = 5


class CacheHandler:
    """ This CacheHandler is caching system with validation and expiration"""

    def __init__(self, developer_mode: bool = False) -> None:

        # Declare constants
        self.dev_mode: bool = developer_mode
        self.cache_duration: int = Const.cache_expires
        self.machine_id: int = self._get_machine_id()

        # Check for cache directory
        os.makedirs(Const.cache_dir, exist_ok=True)

        # Find a valid cache file
        self.cache_file_path: str | None = self._find_cache()
        self.cache_data: dict | None = None
        self.is_cache: bool = False

        if self.cache_file_path and self._is_cache_valid(self.cache_file_path):

            self.is_cache = True
            self.cache_data = self._load_cache(self.cache_file_path)

            # Print developer message
            if self.dev_mode:
                print("[INFO] : Use cache")
                print(self.cache_data)

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
                self._clear_cache(filepath)
                return False
            if (time.time() - file_ts) > self.cache_duration:
                # Clean file
                self._clear_cache(filepath)
                return False

            return True

        except (ValueError, OSError, IndexError):
            # Clean file
            self._clear_cache(filepath)
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

    def get_cached_data(self, key: str) -> dict | None:
        """Get cached data for a key, returns dict with value, is_accurate, method"""
        return self.cache_data.get(key) if self.cache_data else None

    def get_cached_value(self, key: str) -> Union[str, int, float, bool, None]:
        """Get only the value from cached data for a key"""
        cached_item = self.get_cached_data(key)
        return cached_item.get("value") if cached_item else None

    def get_cached_accuracy(self, key: str) -> Optional[bool]:
        """Get only the is_accurate flag from cached data for a key"""
        cached_item = self.get_cached_data(key)
        return cached_item.get("is_accurate") if cached_item else None

    def get_cached_method(self, key: str) -> Optional[str]:
        """Get only the method from cached data for a key"""
        cached_item = self.get_cached_data(key)
        return cached_item.get("method") if cached_item else None

    def set_cache(self, data: dict) -> None:
        """Create a new cache file with machine ID and timestamp"""

        # Declare basic cache file constants
        timestamp = int(time.time())
        filename: str = f"{self.machine_id}_{timestamp}{Const.cache_ext}"
        self.cache_file_path: str = os.path.join(Const.cache_dir, filename)

        # Convert ProcessorPyResult objects to dictionaries with all three fields
        processed_data: dict[str, dict] = {}

        for key, processor_result in data.items():
            processed_data[key] = {
                "value": processor_result.value,
                "is_accurate": processor_result.is_accurate,
                "method": processor_result.method
            }

        wrapped: dict[str, Any] = {
            "timestamp": timestamp,
            "machine_id": self.machine_id,
            "payload": processed_data
        }

        corrupted = self._corrupt_cache(wrapped)
        with open(self.cache_file_path, "wb") as f:
            f.write(corrupted)

        # Print developer feedback
        if self.dev_mode:
            print("[INFO] : Cache saved !")





class Updater:
    """Updater class contains the logic to check for new updates from GitHub releases"""

    repo_owner: str = Const.author.replace(" ", "").lower()
    repo_name: str = "ProcessorPy"

    # GitHub API URL for the latest release
    latest_release_url: str = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    # Headers to avoid rate limiting and identify your app
    headers: dict[str, str] = {
        "User-Agent": f"{repo_name}-Updater/1.0",
        "Accept": "application/vnd.github.v3+json"
    }

    # Declare timeout
    timeout: int = 5

    # Cache settings
    cache_file: Path = Path(".cache") / "update_cache.json"
    cache_expiry_hours: int = 24

    def __init__(self, dev_mode: bool = True) -> None:

        # Declare constants
        self.dev_mode = dev_mode

        # Define requests session
        self.r_session = requests.Session()
        self.r_session.headers.update(self.headers)

    def is_update(self) -> Optional[bool]:
        """
        Check if there's a new update available

        Returns:
            True if update available, False if current, None if error occurred
        """
        try:
            latest_info = self._get_latest_release_info()
            if not latest_info:
                return None

            latest_version = latest_info.get('version', '').lstrip('v')
            current_version = batterypy.version

            # Simple version comparison (you might want to use semantic versioning)
            return self._compare_versions(current_version, latest_version)

        except Exception as e:

            if self.dev_mode:
                print(f"Error checking for updates: {e}")
            return None

    def get_update_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about the latest release

        Returns:
            Dictionary with the version, description, download_size_mb, download_url
        """
        try:
            return self._get_latest_release_info()

        except Exception as e:

            if self.dev_mode:
                print(f"Error getting update info: {e}")
            return None

    def _get_latest_release_info(self) -> Optional[Dict[str, Any]]:
        """Get the latest release info with caching"""
        # Try to get from cache first
        cached_data = self._get_cached_data()
        if cached_data:
            return cached_data

        # Fetch fresh data
        response = self._request_latest_release()
        if not response:
            return None

        parsed_data = self._parse_latest_release(response)
        if parsed_data:
            self._save_to_cache(parsed_data)

        return parsed_data

    def _request_latest_release(self) -> Optional:
        """Make HTTP request to GitHub API for the latest release"""
        try:
            response: Optional = self.r_session.get(
                self.latest_release_url,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                print(f"Repository {self.repo_owner}/{self.repo_name} not found or no releases")
            elif response.status_code == 403:
                print("GitHub API rate limit exceeded")
            else:
                print(f"GitHub API returned status code: {response.status_code}")

            return None

        except requests.exceptions.Timeout:

            if self.dev_mode:
                print("Request timed out")
            return None

        except requests.exceptions.ConnectionError:

            if self.dev_mode:
                print("Connection error occurred")
            return None

        except Exception as e:

            if self.dev_mode:
                print(f"Request error: {e}")
            return None

    def _parse_latest_release(self, response: Optional) -> Optional[Dict[str, Any]]:
        """Parse the GitHub latest release JSON response"""
        try:
            data: Optional = response.json()

            # Extract the main information
            version: str = data.get('tag_name', '')
            description: str = data.get('body', 'No description available')
            published_at: str = data.get('published_at', '')
            html_url: str = data.get('html_url', '')

            # Get download information from assets
            assets = data.get('assets', [])
            download_info: Optional = self._extract_download_info(assets)

            if not download_info:
                print("No valid installer asset found")
                return None

            parsed_info: dict[str, str] = {
                'version': version,
                'description': description,
                'published_at': published_at,
                'html_url': html_url,
                'download_size_mb': download_info['size_mb'],
                'download_url': download_info['download_url'],
                'asset_name': download_info['asset_name'],
                'cached_at': datetime.now().isoformat()
            }

            return parsed_info

        except json.JSONDecodeError:
            print("Failed to parse JSON response")
            return None
        except Exception as e:
            print(f"Error parsing release data: {e}")
            return None

    @staticmethod
    def _extract_download_info(assets: list) -> Optional[Dict[str, Any]]:
        """Extract download information from release assets, selecting the asset ending with 'installer'"""
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('installer.exe'):
                size_bytes = asset.get('size', 0)
                return {
                    'asset_name': asset.get('name', ''),
                    'download_url': asset.get('browser_download_url', ''),
                    'size_mb': f"{size_bytes / (1024 * 1024):.2f} MB"
                }
        return None

    @staticmethod
    def _compare_versions(current: str, latest: str) -> bool:
        """
        Simple version comparison
        For production, consider using packaging.version for semantic versioning
        """
        try:
            # Remove 'v' prefix if present and split by dots
            current_parts = [int(x) for x in current.replace('v', '').split('.')]
            latest_parts = [int(x) for x in latest.replace('v', '').split('.')]

            # Pad shorter version with zeros
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))

            return latest_parts > current_parts

        except (ValueError, AttributeError):
            # Fallback to string comparison
            return latest > current

    def _get_cached_data(self) -> Optional[Dict[str, Any]]:
        """Get data from cache if it exists and hasn't expired"""
        try:
            with open(self.cache_file) as f:
                cached_data = json.load(f)

            cached_time = datetime.fromisoformat(cached_data.get('cached_at', ''))
            expiry_time = cached_time + timedelta(hours=self.cache_expiry_hours)

            if datetime.now() < expiry_time:
                return cached_data
            else:
                # Cache expired
                return None

        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            return None

    def _save_to_cache(self, data: Dict[str, Any]) -> None:
        """Save data to the cache file, creating directories if needed."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            # Save JSON data
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Cache successfully saved to: {self.cache_file}")

        except Exception as e:
            print(f"Failed to save cache to {self.cache_file}: {e}")

    def clear_cache(self) -> None:
        """Clear the cache file"""
        try:
            import os
            os.remove(self.cache_file)
            print("Cache cleared successfully")
        except FileNotFoundError:
            print("No cache file to clear")
        except Exception as e:
            print(f"Error clearing cache: {e}")


class OnlineSearcher:

    def __init__(self, cpu_name: str) -> None:

        # Define constants
        self.cpu_name = cpu_name

    def get_value(self, query: str) -> str:
        """ This method will get the requested value online"""


if __name__ == '__main__':
    sys.exit(0)
