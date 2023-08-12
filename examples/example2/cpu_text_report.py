# Author : Aymen Brahim Djelloul
# Date : 12.08.2023
# This file is an example for gettings all cpu infos in a text file report

# Import Processor Class from ProcessorPy
from ProcessorPy import Processor

# Create Processor object class
my_cpu = Processor()

# Define filename and report file path variable
filename = "cpu-report.txt"
file_path = "C:\\User\\[Your PC Name]\\Desktop\\"

# Get the cpu text report
my_cpu.get_text_report()
