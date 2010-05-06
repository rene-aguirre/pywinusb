#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
"""
Handling raw data inputs example
"""
from time import sleep
from msvcrt import kbhit

import pywinusb.hid as hid

def sample_handler(data):
    print "Raw data: ", data

def raw_test():
    # simple test
    # first be kind with local encodings
    import codecs, sys
    sys.stdout = codecs.getwriter('mbcs')(sys.stdout)
    # browse devices...
    all_hids = hid.find_all_hid_devices()
    if all_hids:
        while True:
            print "Choose a device to monitor raw input reports:\n"
            print "0 => Exit"
            for index, dev in enumerate(all_hids):
                device_name = unicode("%s %s (vID=%04x, pID=%04x)" % \
                        (dev.vendor_name, dev.product_name, dev.vendor_id, dev.product_id))
                print index+1, '=>', device_name
            print "\n\tDevice ('0' to '%d', '0' to exit?) [press enter after number]:" % len(all_hids),
            index_option = raw_input()
            if index_option.isdigit() and int(index_option) <= len(all_hids):
                break;
        int_option = int(index_option)
        if int_option:
            device = all_hids[int_option-1]
            try:
                device.open()

                #set custom raw data handler
                device.set_raw_data_handler(sample_handler)

                print "\nWaiting for data...\nPress any (system keyboard) key to stop..."
                while not kbhit() and device.is_plugged():
                    #just keep the device opened to receive events
                    sleep(0.5)
                return
            finally:
                device.close()
    else:
        print "There's not any non system HID class device available"
#
if __name__ == '__main__':
    raw_test()

