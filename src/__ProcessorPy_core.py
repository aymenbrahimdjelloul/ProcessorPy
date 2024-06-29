"""
@author: Aymen Brahim Djelloul
version : 1.0
date : 04.08.2023
license : MIT

"""

# IMPORTS
import sys
import csv
import os
import platform
from math import ceil
from multiprocessing import cpu_count
from datetime import datetime

__version__ = "1.0"


class ProcessorPyCore:

    def __init__(self, processor_address: object):
        self.__processor_object = processor_address

    @staticmethod
    def __kilobytes_to_bytes(value: str) -> int | None:
        """ This method will convert kb to bytes"""
        return ceil(int(value) * 1024) if value is not None else None

    @staticmethod
    def __megabytes_to_bytes(value: str) -> int | None:
        """ This method will convert mb to bytes"""
        return ceil(int(value) * 10485761) if value is not None else None

    @staticmethod
    def __megahertz_to_gigahertz(value: int) -> int | None:
        """ This method will convert mhz to ghz"""
        return ceil(value / 1000) if value is not None else None

    @staticmethod
    def __kilobytes_to_megabytes(value: int) -> int | None:
        """ This method will convert kb to mb"""
        return ceil(value / 1024) if value is not None else None

    def get_text_report(self, file_path: str = os.getcwd(), filename: str = "cpu-report.txt"):
        """ This method will export a text file report about the cpu"""

        cpu_info_dict: dict = self.get_cpu_info()

        # Format the dictionary to make it readable
        max_key_length: int = max(len(str(key)) for key in cpu_info_dict.keys())
        max_value_length: int = max(len(str(value)) for value in cpu_info_dict.values())
        formatted_string: str = ""

        with open(f"{file_path}/{filename}", 'w') as file:

            for key, value in cpu_info_dict.items():

                # Reformat the key
                key: str = key.title().replace('_', ' ')

                key_padding: str = " " * (max_key_length - len(str(key)))
                value_padding: str = " " * (max_value_length - len(str(value)))

                formatted_string += f"{str(key)} :{key_padding}         {str(value)}{value_padding}\n"

            # Clear memory
            del (key_padding, value_padding, key, value, max_key_length,
                 max_value_length, cpu_info_dict)

            print(formatted_string)
            for row in formatted_string:
                file.write(row)

            file.close()

            # Clear memory
            del row, formatted_string, file

            # Return file report path
            return f"{file_path}/{filename}"

    def get_csv_report(self, file_path: str = os.getcwd(), filename: str = "cpu-report.csv"):
        """ This method will export a csv file report about the cpu"""

        cpu_info_dict: dict = self.get_cpu_info()

        with open(f"{file_path}/{filename}", 'w') as file:
            writer = csv.writer(file)
            writer.writerow(["key", "value"])   # Write Header row

            for key, value in cpu_info_dict.items():
                writer.writerow([key, value])

            file.close()

            # Clear memory
            del cpu_info_dict, writer, key, value, file

        # Return the file report path
        return f"{file_path}/{filename}"

    def get_cpu_info(self) -> dict:
        """ This method will return all cpu information in a dit"""
        return {
            # "operating_system": platform.freedesktop_os_release()["PRETTY_NAME"],
            "cpu_name": self.__processor_object.name,
            "manufacturer": self.__processor_object.manufacturer,
            "arch": self.__processor_object.architecture,
            "family": self.__processor_object.family,
            # "model": self.__processor_object.model,
            "stepping": self.__processor_object.stepping(),
            "flags": self.__processor_object.flags,
            "l1_cache_size": self.__processor_object.l1_cache_size(),
            "l2_cache_size": self.__processor_object.l2_cache_size(),
            "l3_cache_size": self.__processor_object.l3_cache_size(),
            "max_clock_speed": self.__processor_object.max_clock_speed(),
            # "is_turbo_boosted": self.__processor_object.is_turbo_boosted(),
            "is_support_virtualization": self.__processor_object.is_support_virtualization(),
            "cpu_cores": self.__processor_object.core_count(),
            "cpu_threads": self.__processor_object.core_count(logical=True),
            "report_date": datetime.now().strftime("%d/%m/%Y %H:%M")
        }


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
    _fields = tuple(f"core{x}" for x in range(cpu_count())) + ('total',)


if __name__ == "__main__":
    sys.exit()
