import usagePages
from winapi import HidP_Input, HidP_Output, HidP_Feature

def writeDocumentation(self, outputFile):
    "Issue documentation report on outputFile file like object"
    if not self.isOpened():
        raise HIDError("Device has to be opened to get documentation")
    #format
    class CompundVarDict(object):
        def __init__(self, parent):
            self.parent = parent
        def __getitem__(self, key):
            if '.' not in key:
                return self.parent[key]
            else:
                allKeys = key.split('.')
                currVar = self.parent[allKeys[0]]
                for item in allKeys[1:]:
                    newVar = getattr(currVar, item)
                    currVar = newVar
                return newVar
    devVars = vars(self)
    devVars['mainUsageStr'] = repr( usagePages.HidUsage(self.hidCaps.UsagePage, self.hidCaps.Usage) )
    outputFile.write( """\
HID device documentation report
===============================

Top Level Details
-----------------

Manufacturer String:    %(ManufacturerStr)s
Product Sting:          %(ProductStr)s

Vendor ID:              0x%(VendorId)04x
Product ID:             0x%(ProductId)04x
Version number:         0x%(VersionNumber)04x

Device Path:            %(devicePath)s
Device Instance Id:     %(instanceId)s
Parent Instance Id:     %(parentInstanceId)s

Top level usage:        Page=0x%(hidCaps.UsagePage)04x, Usage=0x%(hidCaps.Usage)02x
Usage identification:   %(mainUsageStr)s
Link collections:       %(hidCaps.NumberLinkCollectionNodes)d collection(s)

Reports
-------

Input Report
~~~~~~~~~~~~
Length:     %(hidCaps.InputReportByteLength)d byte(s)
Buttons:    %(hidCaps.NumberInputButtonCaps)d button(s)
Values:     %(hidCaps.NumberInputValueCaps)d value(s)

Output Report
~~~~~~~~~~~~~
Length:     %(hidCaps.OutputReportByteLength)d byte(s)
Buttons:    %(hidCaps.NumberOutputButtonCaps)d button(s)
Values:     %(hidCaps.NumberOutputValueCaps)d value(s)

Feature Report
~~~~~~~~~~~~~
Length:     %(hidCaps.FeatureReportByteLength)d byte(s)
Buttons:    %(hidCaps.NumberFeatureButtonCaps)d button(s)
Values:     %(hidCaps.NumberFeatureValueCaps)d value(s)

""" % CompundVarDict(devVars)) #better than vars()!
    #return
    # inspect caps
    for reportKind in [HidP_Input, HidP_Output, HidP_Feature]:
        allUsages = self.usagesStorage.get(reportKind, [])
        if allUsages:
            print '*** %s Caps ***'%{HidP_Input:"Input", HidP_Output:"Output", HidP_Feature:"Feature"}[reportKind]
            for usageItem in allUsages:
                print usageItem.InspectStruct()
