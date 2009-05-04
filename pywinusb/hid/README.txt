``pywinusb.hid`` -- A package that simplifies HID communications on Windows
---------------------------------------------------------------------------

On Windows(TM), HID communications can be handled from user space 
applications, this means that no additional drivers are needed for simple
HID interfacing.

``pywinusb.hid``, allows to find specific HID class devices, and unless
most simple HID interfacing libraries, allows to work using *HID usages*.

Usages are the 'spices' of HID communications, in summary a HID device
provides descriptors describing the proper way to extract information from
raw reports.

Still ``pywinusb.hid`` allows to work at the low 'raw report' level, but
the convenience provided by working on top level usages allows a cleaner
interface.
