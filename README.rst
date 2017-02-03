*********************************
Installing and Using pywinusb.hid
*********************************

.. contents:: **Table of Contents**

Introduction
============

This project aims to be a simple USB/HID user application space (hence no system 
drivers needed) 100% python package (without C extensions). Initially targeting 
simple HID devices management.

The vision for this project is to be something similar to `PySerial` or `PyParallel` 
but for USB/HID hardware enthusiasts.

Advantages
----------

 * All python code, using ctypes
 
 * Top level handling of HID events (usage events calling hook function handlers)

Current limitations
-------------------

Depending on your application you might find these limitations

 * Windows only (so far...)
 
 * Maybe speed. I've had feedback by some users that speed is not a problem for high data throughput, but I think you might hit some Python limits if you are require any real time processing.

Installation Instructions
=========================

Windows
-------

The most convenient way of installing is using ``easy_install`` or ``pip`` 
(see below for ``pip`` install commands in Windows). I recommend you do  
this once you are familiar with the library as you might otherwise  
loose track of the example source files. However, you can always  
come back and take a look at the examples or the source browsing the  
github repository here.  

| **pip install commands:**  
| *For Python 2:* ``pip install pywinusb``, or ``py -2 -m pip install pywinusb``    
| *For Python 3:* ``py -3 -m pip install pywinusb``  
| (More on pip installation instructions here: https://docs.python.org/3/installing/)
| 
| If using a source package (.zip) from PyPi, un-zip your file (or get the source  
from the main repository) and run the familiar `setup.py install` command  
from the command line, as this is sufficient. Note that setuptools or distribute  
(for python 3) are required.  


Other  
-----

So far only Windows OS it's supported.  

Using pywinusb.hid
==================

View the `./examples` directory for some (ok, few right now) scripts. These
show, for instance, how to use pywinusb.hid to handle events from HID class
devices usages events.

Latest code and some Wiki information can be found on the `main project code page`_.

.. _main project code page: https://github.com/rene-aguirre/pywinusb

Utilities
---------

More on this later... 

 * The module pywinusb.hid.tools contains a function to check HID class devices
   capabilities, for now it provides a basic human readable text report (see
   the hid.core package, run it as main while HID class devices are connected
   to your system)

Feedback and Contributing
=========================

Feel free to contact me! use the `main code project page`_, just tell what do
you think about the project or bring me anything you think might be cool to
consider.

Any participation it's appreciated, feel free to contribute more examples or applications or just a reference to your open source project that uses the library.

.. _main code project page: https://github.com/rene-aguirre/pywinusb


