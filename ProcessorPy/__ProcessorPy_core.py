"""
@author: Aymen Brahim Djelloul
version : 0.0.1
date : 04.08.2023
license : MIT

"""

# IMPORTS
import sys
import csv
from math import ceil
from multiprocessing import cpu_count

__version__ = "0.0.1"


class ProcessorPyCore:

    @staticmethod
    def __megahertz_to_gigahertz(value: int) -> int:
        """ This method will convert mhz to ghz"""
        return ceil(value / 1000) if value is not None else None

    @staticmethod
    def __kilobytes_to_megabytes(value: int) -> int:
        """ This method will convert kb to mb"""
        return ceil(value / 1024) if value is not None else None

    def get_text_report(self, file_path: str, filename: str = "cpu-report.txt"):
        """ This method will export a text file report about the cpu"""

    def get_csv_report(self, report_path: str, filename: str = "cpu-report.csv"):
        """ This method will export a csv file report about the cpu"""

    def get_cpu_info(self) -> dict:
        """ This method will return all cpu information in a dit"""

    @property
    def version_string(self) -> str:
        # This method will return the ProcessorPy version in a string
        return __version__

    @property
    def version_tuple(self) -> tuple:
        # This method will return the ProcessorPy version in tuple
        return tuple(__version__.replace('.', ' ').split())


class ProcessorPyResult(tuple):

    def __new__(cls, *args):
        if len(args[0]) != len(cls._fields):
            raise TypeError(f'{cls.__name__} takes {len(cls._fields)} arguments ({len(args[0])} given)')
        return super(ProcessorPyResult, cls).__new__(cls, args[0])

    def __repr__(self):
        return f'{self.__class__.__name__}({", ".join(f"{name}={val}" for name, val in zip(self._fields, self))})'

    def __getattr__(self, name):
        try:
            idx = self._fields.index(name)
            return self[idx]
        except ValueError:
            raise AttributeError(f'{self.__class__.__name__} object has no attribute "{name}"')

    @classmethod
    def _make(cls, iterable):
        return cls(*iterable)

    def _asdict(self):
        return {name: val for name, val in zip(self._fields, self)}

    def _replace(self, **kwargs):
        current_fields = self._fields
        args = [kwargs[field] if field in kwargs else getattr(self, field) for field in current_fields]
        return self.__class__(*args)


class SensorsResult(ProcessorPyResult):
    _fields = tuple(f"core{x}" for x in range(cpu_count())) + ('total_usage',)


if __name__ == "__main__":
    sys.exit()
