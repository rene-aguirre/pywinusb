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
 
 * Not so fast top level interfacing. But you could still access, directly
   your raw data reports.

Installation Instructions
=========================

Windows
-------

The most convenient way of installing is using `easy_install` or `pip`, I
recomend to do this once you are familiar with the library as you might loose
track of the example source files, but you can take a look to the example or
the source browsing the github repository.

If using a source package (.zip) from PyPi un-zip your file, or get the source
from the main repository and run the familiar `setup.py install` command line
is sufficient, setuptools or distribute (for python 3) are required.


Other
-----

So far only Windows OS it's supported.

Using pywinusb.hid
==================

View the `./examples` directory for some (ok, few right now) scripts. These
show, for instance, how to use pywinusb.hid to handle events from HID class
devices usages events.

Gernal purpose instructions can be found on the `main project code page`_.

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

Any participation it's appreciated, if you are willing to contribute but don't
have any ideas or spare time, `feel free to donate`_.

.. _main code project page: https://github.com/rene-aguirre/pywinusb

.. _feel free to donate: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=4640085

