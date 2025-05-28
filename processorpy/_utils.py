"""
@author : Aymen Brahim Djelloul
version : 0.1
date : 28.05.2025
licesne : MIT

"""

# IMPORTS
import sys
import os
import json
import requests
from dataclasses import dataclass


@dataclass
class Const:
    """ Const class contain the utilities logic constants"""

    # Define cache constants
    cache_dir: str = ".cache"
    cache_extension: str = ".bin"


class OnlineSearcher:
    pass


class CacheHandler(Const):

    def __init__(self, cache_dir) -> None:
        super().__init__()

        # Get the machine id
        self.machine_id: int = _get_machine_id()

        # Define if the cache is in presence
        self.is_cache: bool = self._check_cache_validity()

    def _get_machine_id(self) -> int:
        """ This method will calculate and return the machine id """

    def _check_cache_validity(self) -> bool:
        """ This method will check if the cache file is presence & valid"""

    def _read_cache(self) -> bytes:
        """ t"""

    def _clear_cache(self) -> None:
        """ This method clear the cache """

    def save_cache(self, items: str) -> None:
        """ This method save the cache """

    def get_cache(self) -> dict:
        """ This method return the cache in dictionary format """



class SensorSimulator:
    pass





if __name__ == '__main__':
    sys.exit(0)
