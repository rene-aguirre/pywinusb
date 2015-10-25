#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plug and Play example

This is a port of wxPython PnP sample to PySide (in theory could work with PyQt),
but intended to show as much as possible of PyWinUSB plug and play functionality.

Tested with PySide 1.2.1, PyWinUsb 0.3.6, Python 2.7.9
"""
import sys
from PySide.QtCore import *
from PySide.QtGui import *
import pywinusb.hid as hid
import ctypes

# feel free to test for any default target HID device
default_vendor_id  = 0x1234
default_product_id = 0x0001

class HidQtPnPWindowMixin(hid.HidPnPWindowMixin):
    """PySide PnP helper mixin' class"""
    # PnP connection/disconnection signal
    pnpChanged = Signal(str)
    # hid connection/disconnection signal
    hidConnected = Signal(hid.HidDevice, str)

    def __init__(self):
        # pass system window handle to trap PnP event
        getAsPtr = ctypes.pythonapi.PyCObject_AsVoidPtr
        getAsPtr.restype = ctypes.c_void_p
        getAsPtr.argtypes = [ctypes.py_object]
        window_hnd = getAsPtr(self.winId())

        hid.HidPnPWindowMixin.__init__(self, window_hnd)
        self.hid_device = None      # no hid device... yet
        self._hid_target = None   # filter
        # kick the pnp state machine for one shot polling
        self.on_hid_pnp()

    def on_hid_pnp(self, hid_event = None):
        """This function will be called on per class event changes, so we need
        to test if our device has being connected or is just gone"""
        old_device = self.hid_device

        if hid_event:
            self.pnpChanged.emit(hid_event)

        if hid_event == "connected":
            # test if our device is available
            if self.hid_device:
                # see, at this point we could detect multiple devices!
                # but... we only want just one
                pass
            else:
                self.test_for_connection()
        elif hid_event == "disconnected":
            # the hid object is automatically closed on disconnection we just
            # test if still is plugged (important as the object might be
            # closing)
            if self.hid_device and not self.hid_device.is_plugged():
                self.hid_device = None
        else:
            # poll for devices
            self.test_for_connection()
        # update ui
        if old_device != self.hid_device:
            if hid_event == "disconnected":
                self.hidConnected.emit(old_device, hid_event)
            else:
                self.hidConnected.emit(self.hid_device, hid_event)

    def test_for_connection(self):
        """ This funnction validates we have a valid HID target device
        connected, it could be extended to manage multiple HID devices
        mapped to different device paths, but so far only expects a
        single device, so in case of multiple devices being connected
        resolution it is arbitrary"""
        # poll for all connections
        if not self._hid_target:
            return
        all_items =  self._hid_target.get_devices()

        if all_items:
            # at this point, what we decided to be a valid hid target is
            # already plugged
            if len(all_items) == 1:
                # this is easy, we only have a single hid device
                self.hid_device = all_items[0]
            else:
                # at this point you might have multiple scenarios
                grouped_items = self._hid_target.get_devices_by_parent()
                if len(grouped_items) > 1:
                    # 1) We have multiple devices connected so, make
                    # your rules, how do you help your user to handle multiple
                    # devices?
                    # maybe you here will find out wich is the new device, and
                    # tag this device so is easily identified (i.e. the WiiMote
                    # uses LEDs), or just your GUI shows some arbitrary
                    # identification for the user (device 2 connected)
                    pass
                else:
                    # 2) We have a single physical device, but the descriptors
                    # might might cause the OS to report is as multiple devices
                    # (collections maybe) so, what would be your target device?
                    # if you designed the device firmware, you already know the
                    # answer...  otherwise one approach might be to browse the
                    # hid usages for a particular target...  anyway, this could
                    # be complex, especially handling multiple physical devices
                    # that are reported as multiple hid paths (objects)...
                    # so...  I recommend you creating a proxy class that is
                    # able to handle all your 'per parent id' grouped devices,
                    # (like a single .open() able to handle your buch of
                    # HidDevice() items
                    pass
                # but... we just arbitrarly select the first hid object path
                # (how creative!)
                self.hid_device = all_items[0]
        if self.hid_device:
            self.hid_device.open()

    def set_target(self, hid_filter):
        self._hid_target = hid_filter
        self.test_for_connection()
        if self.hid_device:
            # in case target set while already connected
            self.hidConnected.emit(self.hid_device, "connected")

class HidPnPForm(QDialog, HidQtPnPWindowMixin):
    """PyWinUsb PnP (Plug & Play) test dialog"""

    def __init__(self, parent = None):
        super(HidPnPForm, self).__init__(parent)

        # init PnP management
        HidQtPnPWindowMixin.__init__(self)

        self.vendorIdText  = QLineEdit()
        self.vendorIdText.setInputMask("HHHH")
        self.vendorIdText.setText("{0:04X}".format( default_vendor_id ))

        self.productIdText = QLineEdit()
        self.productIdText.setInputMask("HHHH")
        self.productIdText.setText("{0:04X}".format( default_product_id ))

        self.testButton = QPushButton("Set Test", self)
        self.statusLabel = QLabel("Set Test first")
        self.logText  = QTextEdit()

        grid = QGridLayout()
        grid.setSpacing( 10 )

        grid.addWidget(QLabel("Set target HID device (Hex values)"),    0, 0)
        grid.addWidget(QLabel("Vendor Id:"), 1, 0, 1, 1, Qt.AlignRight)
        grid.addWidget(self.vendorIdText,    1, 1)

        grid.addWidget(QLabel("Product Id:"), 2, 0, 1, 1, Qt.AlignRight)
        grid.addWidget(self.productIdText,    2, 1)

        grid.addWidget(self.statusLabel,    3, 0)
        grid.addWidget(self.testButton,     4, 0)
        grid.addWidget(self.logText,        5, 0, 4, 2)
        self.setLayout(grid)

        self.testButton.clicked.connect( self.on_test )
        self.finished.connect( self.on_close )

        # custom hid signals
        self.pnpChanged.connect( self.on_pnp_changed )
        self.hidConnected.connect( self.on_connected )

    def on_test(self):
        "Triggers HID polling and sets new PnP filter"
        # a device so we could easily discriminate wich devices to look at
        vId = int(self.vendorIdText.text(), 16)
        pId = int(self.productIdText.text(), 16)
        self.statusLabel.setText( "waiting device ..." )
        self.set_target( hid.HidDeviceFilter(vendor_id = vId, product_id = pId) )

    def on_close(self, result):
        if self.hid_device:
            self.hid_device.close()

    def show_hids(self):
        all_hids = hid.find_all_hid_devices()
        if all_hids:
            self.logText.append( "Available HID devices:" )
            for hid_device in all_hids:
                self.logText.append( "  vId={0:04X}, pId= {1:04X}".format(
                    hid_device.vendor_id, hid_device.product_id ))
        else:
            self.logText.append( "No HID USB devices attached now" )

    def on_pnp_changed(self, event_str):
        self.logText.append( "\nAny HID USB device {}".format( event_str ))
        self.show_hids()

    def on_connected(self, my_hid, event_str):
        self.statusLabel.setText( "vId={0:04x}, pId={1:04x}: {2}".format(
            my_hid.vendor_id, my_hid.product_id, event_str ))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = HidPnPForm()
    form.show()
    app.exec_()
    sys.exit()

