# Author : Aymen Brahim Djelloul
# Date : 12.08.2023
# This file is a test example for Processor class in ProcessorPy

from ProcessorPy import Processor

# Create Processor object
my_cpu = Processor()

def main():
  
  print(my_cpu.name)                        # Get the cpu Model Name or cpu Specification
  print(my_cpu.manufacturer)                # Get the cpu Manufacturer Name
  print(my_cpu.architecture)                # Get the cpu Architecture string
  print(my_cpu.family)                      # Get the cpu family value
  print(my_cpu.stepping)                    # Get the cpu stepping value
  print(my_cpu.socket)                      # Get the cpu socket name
  print(my_cpu.flags)                       # Get the cpu flags and features in list
  pritn(my_cpu.l1_cache_size())             # Get the Level 1 cache size in bytes & in Mb using friendly_format
  print(my_cpu.l2_cache_size())             # Get the Level 2 cache size in bytes & in Mb using friendly_format
  print(my_cpu.l3_cache_size())             # Get the Level 3 cache size in bytes & in Mb using friendly_format
  print(my_cpu.max_clock_speed())           # Get the max cpu clock speed in mhz
  print(my_cpu.is_support_virtualization())  # determine is your cpu support virtualization or hypervisor features
  print(my_cpu.core_count())                # Get the physical cores number
  print(my_cpu.core_count(logical=True))    # Get the logical cores or core Threads number


if __name__ == "__main__":
  main()
  
