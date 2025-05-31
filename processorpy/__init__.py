"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.


@author : Aymen Brahim Djelloul
version : 1.1
date    : 14.05.2025
license : MIT

"""

# IMPORTS
import sys

if sys.platform == 'win32':
    from ._win_processor import Processor, Sensors
else:
    from ._linux_processor import Processor, Sensors
