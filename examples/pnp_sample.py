#
"""
Plug and Play example

This script requires wxPython, but it could be easily (really!) changed
to work with any GUI working on windows, just make you you pass your frame window
handler to the HidPnPWindowMixin.__init__ initialization function.

A hook will be inserted on the message handler so the window could be used as
a target for PnP events, for now this are HID class wise, this means you'll have
to test if your device 'plug' status has changed.
"""

import wx
import pywinusb.hid as hid

# feel free to test
target_vendor_id = 0x1234
target_product_id = 0x0001

class MyFrame(wx.Frame,hid.HidPnPWindowMixin):
    # a device so we could easily discriminate wich devices to look at
    my_hid_target = hid.HidDeviceFilter(vendor_id = target_vendor_id, product_id = target_product_id)
    
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,-1,"Re-plug your USB HID device, watch the command window!...")
        hid.HidPnPWindowMixin.__init__(self, self.GetHandle())
        wx.EVT_CLOSE(self, self.on_close)
        self.device = None #no hid device... yet
        
        # kick the pnp engine
        self.on_hid_pnp()
        
    def on_hid_pnp(self, hid_event = None):
        """This function will be called on per class event changes,
        so we need to test if our device has being connected or is just gone"""
        if hid_event:
            print "Hey, a hid device just %s!" % hid_event
            
        if hid_event == "connected":
            # test if our device is available
            if self.device:
                # see, at this point we could detect multiple devices!
                # but... we only want just one
                pass
            else:
                self.test_for_connection()
        elif hid_event == "disconnected":
            # the hid object is automatically closed on disconnection
            # we just test if still is plugged (important as the object might be closing)
            if self.device and not self.device.is_plugged():
                self.device = None
                print "you removed my hid device!"
        else:
            # poll for devices
            self.test_for_connection()
        # update ui
        if old_Device != self.device:
            self.UpdateUsbStatus(False)
        
    def test_for_connection(self):
        all_items =  MyFrame.my_hid_target.get_devices()
        if all_items:
            # at this point, what we decided to be a valid hid target is already plugged
            if len(all_items) == 1:
                # this is easy, we only have a single hid device
                self.device = all_items[0]
            else:
                # at this point you might have multiple scenarios
                grouped_items = MyFrame.my_hid_target.get_devices_by_parent()
                print "%d devices now connected" % len(grouped_items)
                if len(grouped_items) > 1:
                    # 1) Really you have multiple devices connected
                    # so, make your rules, how do you help your user to handle multiple devices?
                    # maybe you here will find out wich is the new device, and tag this device
                    # so is easily identified (i.e. the WiiMote uses LEDs), or just your GUI
                    # shows some arbitrary identification for the user (device 2 connected)
                    pass
                else:
                    # 2) We have a single physical device, but the descriptors might
                    # might cause the OS to report is as multiple devices (collections maybe)
                    # so, what would be your target device?
                    # if you designed the device firmware, you already know the answer...
                    # otherwise one approach might be to browse the hid usages for a particular
                    # target...
                    # anyway, this could be complex, especially handling multiple physical devices
                    # that are reported as multiple hid paths (objects)... so...
                    # I recommend you creating a proxy class that is able to handle all your
                    # 'per parent id' grouped devices, (like a single .open() able to handle
                    # your buch of HidDevice() items
                    pass
                # but... we just arbitrarly select the first hid object path (how creative!)
                self.device = all_items[0]
        if self.device:
            self.device.open()
            print "got my device: %s!" % repr(self.device)
        else:
            print "saddly my device is not here... yet :-( "

    def on_close(self, event):
        event.Skip()
        if self.device:
            self.device.close()
            
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show()
    app.MainLoop()
