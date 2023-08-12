# Author : Aymen Brahim Djelloul
# Date : 12.08.2023
# This file is an example for gettings all cpu infos in a CSV file report

# Import Processor Class from ProcessorPy
from ProcessorPy import Processor

# Create Processor object class
my_cpu = Processor()

# Define filename and report file path variable
filename = "cpu-report.csv"
path = "C:\\User\\[Your PC Name]\\Desktop\\"

# Get the cpu text report and save it with your path and name
save_path = my_cpu.get_csv_report(file_path=path, filename=filename)

# NOTE : if you didn't specified a filename or file path it will be saved in the same library directory 
          The saved file path will be returned

# Print out the file saved path
print(save_path)
