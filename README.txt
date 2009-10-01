=================================
Installing and Using pywinusb.hid
=================================

.. contents:: **Table of Contents**

------------
Introduction
------------

This project aims to be a simple USB/HID user application space (hence no system 
drivers needed) 100% python package (without C extensions). Initially targeting 
simple HID devices management, also planed, is `support for WinUSB`_ high level wrapping.

The vision for this project is to be something similar to `PySerial` or `PyParallel` 
but for USB/HID hardware enthusiasts.

.. _support for WinUSB: http://msdn.microsoft.com/en-us/library/aa476426.aspx

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

-------------------------
Installation Instructions
-------------------------

Windows
-------

No package releases yet.  For now you can access the code using `the svn repository`_.

I'm planning initially to have a mature pywinusb.hid name space (sub-package) 
implementation before attempting any of the pywinusb.winusb stuff.

.. _the svn repository: http://code.google.com/p/pywinusb/source/checkout

Other
-----

So far only Windows OS it's supported.

------------------
Using pywinusb.hid
------------------

View the `./examples` directory for some (ok, few right now) scripts. These show,
for instance, how to use pywinusb.hid to handle events from HID class devices usages events.

Gernal purpose instructions can be found on the `main project code page`_.

.. _main project code page: http://code.google.com/p/pywinusb

Utilities
---------

More on this later... 

 * The module pywinusb.hid.tools contains a function to check HID class devices capabilities, 
   for now it provides a basic human readable text report (see the hid.core package, 
   run it as main while HID class devices are connected to your system)

-------------------------
Feedback and Contributing
-------------------------

Feel free to contact me! use the `main code project page`_, just tell what do you think 
about the project or bring me anything you think might be cool to consider.

Any participation it's appreciated, if you are willing to contribute but don't have any 
ideas or spare time, `feel free to donate`_.

.. _main code project page: http://code.google.com/p/pywinusb
.. _feel free to donate: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=4640085

