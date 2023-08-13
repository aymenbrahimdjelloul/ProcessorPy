# Author : Aymen Brahim Djelloul
# Date : 12.08.2023
# This file is an example for getting the sensros-readings from Sensors class in ProcessorPy

# Import Sensors class from ProcessorPy
from ProcessorPy import Sensors

# Create Sensors object class
sense = Sensors()

def main():

    # Get the current reading of CPU clock speed in Mhz
    print(sense.get_cpu_clock_speed())

    # Get the current CPU usage percentage with the usage percent of each core separatly
    print(sense.get_cpu_usage(per_core=True))

    # Get the available CPU voltage in friendly string or in integer
    print(sense.get_voltage(friendly_format=True))


if __name__ == "__main__":
    main()
