# Author: Aymen Brahim Djelloul
# Date : 13.08.2023
# This code will test ProcessorPy if it's work properly without any issues or missed info on diffrent platforms

from processor_py import ProcessorPy
import platform

my_cpu = ProcessorPy.Processor()
sensors = ProcessorPy.Sensors()


def processor_py_test():
    """ This function will test ProcessorPy and return the testing result """

    # First test Processor Class if it works properly
    cpu_info_dict: dict = my_cpu.get_cpu_info()

    # Check if there is None value in CPU info dictionary
    for value in cpu_info_dict.values():

        if value is None:
            return False

    # Check sensors result
    sensors_result = (sensors.get_cpu_clock_speed(), sensors.get_cpu_usage(), sensors.get_cpu_voltage())
    for sensor in sensors_result:

        if sensor is None:
            return False

    return True


if processor_py_test():
    print(f"ProcessorPy is working properly on {platform.freedesktop_os_release()['PRETTY_NAME']} \n"
          f"with {my_cpu.name} CPU ")

else:
    print(f"ProcessorPy Failed to run properly on {platform.freedesktop_os_release()['PRETTY_NAME']}\n"
          f"with {my_cpu.name} CPU")
