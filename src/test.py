# Author: Aymen Brahim Djelloul
# Date : 13.08.2023
# This code will test ProcessorPy if it's work properly without any issues or missed info on diffrent platforms

import ProcessorPy
import platform
import os
import sys

processor_py_obj = ProcessorPy.Processor()
sensors_obj = ProcessorPy.Sensors()


def processor_py_test():
    """ This function will test ProcessorPy and return the testing result """

    # Define passed tests count
    test_passed: int = 0
    # Define failed tests count
    test_failed: int = 0

    # First test Processor Class if it works properly
    cpu_info_dict: dict = processor_py_obj.get_cpu_info()

    # print(cpu_info_dict)
    # Check if there is None value in CPU info dictionary
    for value in cpu_info_dict.values():

        if value is None:
            test_failed += 1
        else:
            test_passed += 1

    # Check sensors result
    sensors_result = (sensors_obj.get_cpu_clock_speed(), sensors_obj.get_cpu_usage(), sensors_obj.get_cpu_voltage())

    # print(sensors_result)
    for sensor in sensors_result:

        if sensor is None:
            test_failed += 1
        else:
            test_passed += 1

    # Clear memory
    del cpu_info_dict, value, sensors_result, sensor

    return True if test_passed > test_failed else False


if __name__ == "__main__":

    # Print the welcome message!
    print(f"{' ' * 30}Welcome to the tester program of ProcessorPy '{processor_py_obj.version_string}'\n\n"
          f"Please Wait.. until the test is Done !")

    if processor_py_test():

        # Print test result
        print(f"ProcessorPy is working properly on {platform.platform(aliased=True)} \n"
              f"with '{processor_py_obj.name}' CPU ")
    
    else:
        # Clear
        # Print the test result
        print(f"ProcessorPy Failed to run properly on {platform.platform(aliased=True)}\n"
              f"with {processor_py_obj.name} CPU")

    # To prevent exiting directly
    input("\n\n Press Enter to exit.")
    
    # exit
    sys.exit()
