from pywinusb import hid

from time import sleep
from msvcrt import kbhit

def test_telephony_hook():
    # play with this value (or set it if you know your device capabilities)
    # this allows to poll the telephony device for the current usage value
    DEVICE_SUPPORTS_INTERRUPTS_TRANSFERS = False
    
    # get all currently connected HID devices we could filter by doing something
    # like hid.HidDeviceFilter(VendorId=0x1234), product Id filters (with masks) 
    # and other capabilities also available
    allDevices = hid.HidDeviceFilter().getDevices() #plantronics

    if not allDevices:
        print "No HID class devices attached."
    else:
        # search for our target usage (the hook button)
        USAGE_TELEPHONY_HOOK = hid.getFullUsageId(0xb, 0x20) #target pageId, usageId
               
        def hook_pressed(newValue, eventType):
            # this simple handler is called on 'pressed' events
            # this means the usage value has changed from '1' to '0'
            # no need to check the value
            if newValue:
                print "On Hook!"
            else:
                print "Off Hook!"
        
        for device in allDevices:
            try:
                device.Open()
                
                # browse input reports
                allInputReports = device.findInputReports()
                
                for inputReport in allInputReports:
                    if USAGE_TELEPHONY_HOOK in inputReport:
                        #found a telephony device w/ hook button
                        print "\nMonitoring %s %s device.\n"%(device.ManufacturerStr, device.ProductStr)
                        print "Press any key to exit monitoring (or remove HID device)..."
                        
                        # add event handler (other events: EVT_PRESSED, EVT_RELEASED, EVT_ALL, ...)
                        device.addEventHandler(USAGE_TELEPHONY_HOOK,  hook_pressed, hid.HID_EVT_CHANGED) #level usage
                        
                        if DEVICE_SUPPORTS_INTERRUPTS_TRANSFERS:
                            # poll the current value (GET_REPORT directive), 
                            # allow handler to process result
                            inputReport.Get()
                        
                        while not kbhit() and hid.hidDevicePathExists(device.devicePath):
                            #just keeps the device opened
                            sleep(0.5)
                        break
                        return
            finally:
                device.Close()
        print "Sorry, no one of the attached HID class devices provide any Telephony Hook button"
    #
if __name__ == '__main__':
    test_telephony_hook()
