<!-- GitHub README.md -->

<h1>ProcessorPy</h1>

<p>ProcessorPy is a Cross-platform, Pure python Library that's will get CPU information's & specifications also it's provide a sensors readings.
ProcessorPy should do it without any external dependecies or any kind of C/C++ or Assembly scripts, It's piece of a pure-python work for both Windows and Linux-debian systems</p>

<h2>Features</h2>

-[x] Cross platform (ProcessorPy support both of Windows and Linux systems)

-[x] Easy & Fast !

-[x] Provide accurate inforamtions

-[x] Pure python (No need for external dependencies)

<h2>How It's Work ?</h2>
<p1>ProcessorPy do it perfect job by using multiple methods and system built-in tools in both Windows and Linux-Debian systems,
  ProcessorPy parse the output of the operating system built-in tools and return it as friendly-user inforamtion's
</p1>

<h2>Testing</h2>
<h4>ProcessorPy is Tested and worked in this Operating Systems</h4>

| OS      | CPU Platform |  Worked Succefully  |
|-----------|---------------|-------------------|
| Widnwows 11 Pro  | AMD Ryzen 3 3200G | YES |


Simple Usage
-----
~~~python
# First import the Processor class from ProcessorPy
from ProcessorPy import Processor

# Create a Processor Object
my_cpu = Processor()

# Print out your CPU Name !
print(my_cpu.name)

~~~

Sensors Usage
-----
~~~python
# Import the Sensors class from ProcessorPy
from ProcessorPy import Sensors

# Create Sensors object
sensor = Sensors()

# Print out the current cpu clock speed in mhz
print(sensor.get_cpu_clock_speed())

~~~


<h2>License</h2>
<h4>This project is published under MIT License </h4>

~~~
MIT License

Copyright (c) 2023 Aymen Brahim Djelloul

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

~~~
