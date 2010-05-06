#
"""
Simple example on how to handle usage control events
"""
from time import sleep
from msvcrt import kbhit

import pywinusb.hid as hid

def test_telephony_hook():
    """Browse for non system HID class devices, if a telephony page
    hook usage control is available monitor value change events"""
    # play with this value (or set it if you know your device capabilities)
    # this allows to poll the telephony device for the current usage value
    input_interrupt_transfers = False
    
    # get all currently connected HID devices we could filter by doing 
    # something like hid.HidDeviceFilter(VendorId=0x1234), product Id 
    # filters (with masks) and other capabilities also available
    all_devices = hid.HidDeviceFilter().get_devices() 

    if not all_devices:
        print "No HID class devices attached."
    else:
        # search for our target usage (the hook button)
        #target pageId, usageId
        usage_telephony_hook = hid.get_full_usage_id(0xb, 0x20)
               
        def hook_pressed(new_value, event_type):
            "simple usage control handler"
            # this simple handler is called on 'pressed' events
            # this means the usage value has changed from '1' to '0'
            # no need to check the value
            event_type = event_type #avoid pylint warnings
            if new_value:
                print "On Hook!"
            else:
                print "Off Hook!"
        
        for device in all_devices:
            try:
                device.open()
                
                # browse input reports
                all_input_reports = device.find_input_reports()
                
                for input_report in all_input_reports:
                    if usage_telephony_hook in input_report:
                        #found a telephony device w/ hook button
                        print "\nMonitoring %s %s device.\n" \
                            % (device.vendor_name, device.product_name)
                        print "Press any key to exit monitoring "\
                            "(or remove HID device)..."
                        
                        # add event handler (example of other available 
                        # events: EVT_PRESSED, EVT_RELEASED, EVT_ALL, ...)
                        device.add_event_handler(usage_telephony_hook, 
                            hook_pressed, hid.HID_EVT_CHANGED) #level usage
                        
                        if input_interrupt_transfers:
                            # poll the current value (GET_REPORT directive), 
                            # allow handler to process result
                            input_report.get()
                        
                        while not kbhit() and device.is_plugged():
                            #just keep the device opened to receive events
                            sleep(0.5)
                        return
            finally:
                device.close()
        print "Sorry, no one of the attached HID class devices "\
            "provide any Telephony Hook button"
    #
if __name__ == '__main__':
    test_telephony_hook()
