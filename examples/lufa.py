#!/usr/bin/env python
# -*- coding: latin-1 -*-

import pywinusb.hid as hid

"""
This example shows how to communicate with a GenericHID LUFA device 
(Demos\Device\ClassDriver), refer to the LUFA projects for more details:
    * http://www.fourwalledcubicle.com/LUFA.php

This is the descriptor used in the device:

USB_Descriptor_HIDReport_Datatype_t PROGMEM GenericReport[] =
{
	0x06, 0x9c, 0xff,     /* Usage Page (Vendor Defined)                     */
	0x09, 0x01,           /* Usage (Vendor Defined)                          */
	0xa1, 0x01,           /* Collection (Vendor Defined)                     */
	0x09, 0x02,           /*   Usage (Vendor Defined)                        */
	0x75, 0x08,           /*   Report Size (8)                               */
	0x95, GENERIC_REPORT_SIZE, /*   Report Count (GENERIC_REPORT_SIZE)       */
	0x15, 0x80,           /*   Logical Minimum (-128)                        */
	0x25, 0x7F,           /*   Logical Maximum (127)                         */
	0x81, 0x02,           /*   Input (Data, Variable, Absolute)              */
	0x09, 0x03,           /*   Usage (Vendor Defined)                        */
	0x75, 0x08,           /*   Report Size (8)                               */
	0x95, GENERIC_REPORT_SIZE, /*   Report Count (GENERIC_REPORT_SIZE)       */
	0x15, 0x00,           /*   Logical Minimum (0)                           */
	0x25, 0xff,           /*   Logical Maximum (255)                         */
	0x91, 0x02,           /*   Output (Data, Variable, Absolute)             */
	0xc0                  /* End Collection                                  */
};

"""
# using latest repository values
vendor_id   = 0x03eb
product_id  = 0x204f

# usage definitions
usage_page_id   = 0xff9c
input_usage_id  = 0x02
output_usage_id = 0x03

#
input_usage  = hid.get_full_usage_id(usage_page_id, input_usage_id)
output_usage = hid.get_full_usage_id(usage_page_id, output_usage_id)

def ubyte_list_to_int(data):
    """ Convert a c_ubyte array to a plain integer array
    Due performance reasons, data is received as an array of c_ubyte"""
    [x.value for x in data]

def setup_monitor(device):
    def data_handler(data, event_type):
        event_type = event_type #avoid pylint warnings
        print "New Data: ", [hex(x) for x in ubyte_list_to_int(data)]

    # add event handler
    device.add_event_handler(target_usage, 
        data_handler, hid.HID_EVT_ALL) #level usage

if __name__ == '__main__':
    # search for any target device
    connected_devices = hid.HidDeviceFilter(vendor_id = vendor_id, 
            product_id = product_id).get_devices()
    if connected_devices:
        print "Multiple devices found, picking anyone..."
        device = connected_devices[0]
        try:
            device.open()
            
            print "\nWhat do you want to do?"
            print "  1) Monitor data"
            print "  2) Send data"
            print "  0) Exit"

            response = int( raw_input().strip() )

            if response == 1:
                # setup input report monitor
                setup_monitor()

                print "\nData handler ready..., ",
                print "press any key to exit (or unplug device)"
                while not kbhit() and device.is_plugged():
                    #just keep the device opened to receive events
                    sleep(0.5)
            elif reponse == 2:
                report = device.find_output_reports(usage_page = usage_page_id,
                        usage_id = output_usage_id)
                if report:
                    print "Input (hex format) data, comma separated,",
                    print "%d values:" % len(report[output_usage])
                    data = [int(x, 16) for x in raw_input().strip().split(',')]
                    if len(data) == len(report[output_usage]):
                        # now set report and send the data
                        report[output_usage] = data
                        report.send()
                        print "Ready!"
                    else:
                        print "Error, expecting %d data elements," % len(data),
                        print "got %d!" % len(report[output_usage])
                else:
                    print "Sorry, not able to find the output usage"
        finally:
            device.close()
    else:
        print "Target GenericHID LUFA device not found!"
        print "Verify your .VendorID and .ProductID device firmware settings"

