"""
@authors : Aymen Brahim Djelloul
version : 1.0
date : 04.08.2023
License : MIT


    // ProcessorPy is a Cross-Platform Light-weight pure python library to get all cpu specifications also
       its provide sensor readings for Windows and Linux systems

"""

from platform import system
from exceptions import *


if __name__ != "__main__":

    if system() == "Windows":
        from __Windows_ProcessorPy import Processor, Sensors

    elif system() == "Linux":
        from __Linux_ProcessorPy import Processor, Sensors

    else:
        raise NotSupportedPlatform(system())
