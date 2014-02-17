#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Set LED page mute (telephony) to on/off
"""
#this example requires >= python 2.7
import sys
import pywinusb.hid as hid

#version string
__version__ = "0.0.1"

def set_mute(mute_value):
    "Browse for mute usages and set value"
    all_mutes = ( \
            (0x8, 0x9), # LED page
            (0x1, 0xA7), # desktop page
            (0xb, 0x2f),
    )
    all_target_usages = [hid.get_full_usage_id(u[0], u[1]) for u in all_mutes]

    # usually you'll find and open the target device, here we'll browse for the
    # current connected devices
    all_devices = hid.find_all_hid_devices()

    success = 0
    if not all_devices:
        print("Can't any HID device!")
    else:
        # search for our target usage
        # target pageId, usageId
        for device in all_devices:
            try:
                device.open()
                # target 'to set' value could be in feature or output reports
                for report in device.find_output_reports() + device.find_feature_reports():
                    for target_usage in all_target_usages:
                        if target_usage in report:
                            # set our value and send
                            report[target_usage] = value
                            report.send()
                            success += 1
            finally:
                device.close()
    # fit to sys.exit() proper result values
    print("{0} Mute usage(s) set\n".format(success))
    if success:
        return 0
    return -1

if __name__ == '__main__':
    if (len(sys.argv[1:]) != 1) or sys.argv[1].lower() not in ('on', 'off'):
        print("Usage: {0} [on|off]\n".format(sys.argv[0]))
        sys.exit(-1)
    # go for it!
    value = (sys.argv[1] == 'on')
    sys.exit( set_mute( value ) )

