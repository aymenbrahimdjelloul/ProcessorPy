"""
@author: Aymen Brahim Djelloul
version 0.0.1
date: 04.08.2023
license: MIT

"""

# IMPORTS
import sys


class NotSupportedPlatform(BaseException):

    def __init__(self, platform: str):
        self.__platform = platform

    def __str__(self):
        return f"ProcessorPy does not support {self.__platform} Operating system!"


class SystemDriverDoesntError(BaseException):

    def __init__(self, driver: str):
        self.__driver = driver

    def __str__(self):
        return f"ProcessorPy cannot reach your cpu information because '{self.__driver}' not worked properly."


if __name__ == "__main__":
    sys.exit()
