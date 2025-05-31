"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 0.1
date : 29.05.2025
license : MIT License

"""

# IMPORTS
import sys


class Const:
    pass


class Interface:
    pass



def main() -> None:
    """ This function is executed when this file is
     executed from the command line """


    try:

        app = Interface()
        app.run()

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    sys.exit(0)
