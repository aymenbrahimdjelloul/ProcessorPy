"""
@author : Aymen Brahim Djelloul
version : 1.1
date    : 14.05.2025
license : MIT

"""

# IMPORTS
import sys

# Define constants
__version__: str = "1.1"

if sys.platform == 'win32':
    from ._win_processor import Processor, Sensors
else:
    from ._linux_processor import Processor, Sensors
