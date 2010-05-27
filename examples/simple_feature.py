#!/usr/bin/env python
# -*- coding: latin-1 -*-

"""
Simple example on how to poll feature reports usages
"""
import pywinusb.hid as hid

def read_values(target_usage):
    """read feature report values"""
    # browse all devices
    all_devices = hid.HidDeviceFilter().get_devices()
    
    if not all_devices:
        print "Can't find any non system HID device connected"
    else:
        # search for our target usage
        usage_found = False
        for device in all_devices:
            try:
                device.open()
                # browse feature reports
                for report in device.find_feature_reports():
                    if target_usage in report:
                        # we found our usage
                        report.get()
                        # print result
                        print "The value:", list(report[target_usage])
                        print "All the report:", report.get_raw_data()
                        usage_found = True
            finally:
                device.close()
        if not usage_found:
            print "The target device was found, but the requested usage does not exist!\n"
    #
if __name__ == '__main__':
    target_usage = hid.get_full_usage_id(0xff00, 0x02) # generic vendor page, usage_id = 2
    # go for it!
    read_values(target_usage)

