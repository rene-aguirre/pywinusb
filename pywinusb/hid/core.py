#
import sys
import ctypes
import _winreg
import threading
import time

from UserList import UserList
from ctypes import Structure, Union, c_byte, c_char, c_int, c_long, c_ulong, c_ushort, c_wchar
from ctypes import pointer, byref, sizeof, POINTER
from ctypes.wintypes import ULONG, BOOLEAN, BYTE, WORD, DWORD, HANDLE
#local modules
from winapi import *
from helpers import synchronized

USAGE = c_ushort
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

usageEvents = [
    HID_EVT_NONE,
    HID_EVT_CHANGED,
    HID_EVT_PRESSED,
    HID_EVT_RELEASED,
    HID_EVT_SET,
    HID_EVT_CLEAR,
] = range(6)

def getFullUsageId(pageId, usageId):
    return (pageId << 16) | usageId

def getUsagePageId(fullUsageId):
    return (fullUsageId >> 16) & 0xffff

def getShortUsageId(fullUsageId):
    return fullUsageId & 0xffff

def hidDevicePathExists(devicePath, hidGuid = GetHidGuid()):
    "Test if required devicePath is still valid (HID device connected to host)"
    # get HID device class guid

    # handle to an opaque device information set
    hInfo = SetupDiGetClassDevs(byref(hidGuid), None, None, (DIGCF_PRESENT | DIGCF_DEVICEINTERFACE))

    if hInfo == INVALID_HANDLE_VALUE:
        return False
    try:
        # retrieve all the available interface information.
        deviceInterface = SP_DEVICE_INTERFACE_DATA()
        deviceInterface.cbSize = sizeof(deviceInterface)

        deviceInterfaceDetail = SP_DEVICE_INTERFACE_DETAIL_DATA()
        deviceInterfaceDetail.cbSize = sizeof(deviceInterfaceDetail) - (sizeof(c_tchar)*(MAX_SP_DEV_INTERF_DETAIL_SIZE-1))

        devIndex = 0
        requiredSize = c_ulong()
        while setupapiDLL.SetupDiEnumDeviceInterfaces(hInfo, None, byref(hidGuid), devIndex, byref(deviceInterface)):
            devIndex += 1

            # validate if hid path would fit
            requiredSize.value = 0
            SetupDiGetDeviceInterfaceDetail(hInfo, byref(deviceInterface), None, 0, byref(requiredSize), None)
            if requiredSize.value > sizeof(deviceInterfaceDetail):
                sys.stderr.write("Error getting HID device info.\n")
                continue

            # it's ok to get the details
            SetupDiGetDeviceInterfaceDetail(hInfo, byref(deviceInterface), byref(deviceInterfaceDetail), requiredSize, None, None)

            if deviceInterfaceDetail.DevicePath == devicePath:
                return True
    finally:
        # clean up
        setupapiDLL.SetupDiDestroyDeviceInfoList(hInfo)
    #
    return False

def findAllHidDevices():
    "Finds all HID devices connected to the system"
    """From ddk documentation (finding and Opening HID collection):
    After a user-mode application is loaded, it does the following sequence of operations:
        * Calls HidD_GetHidGuid to obtain the system-defined GUID for HIDClass devices.
        * Calls SetupDiGetClassDevs to obtain a handle to an opaque device information set
          that describes the device interfaces supported by all the HID collections currently
          installed in the system. The application should specify DIGCF_PRESENT and
          DIGCF_INTERFACEDEVICE in the Flags parameter passed to SetupDiGetClassDevs.
        * Calls SetupDiEnumDeviceInterfaces repeatedly to retrieve all the available
          interface information.
        * Calls SetupDiGetDeviceInterfaceDetail to format interface information for each
          collection as a SP_INTERFACE_DEVICE_DETAIL_DATA structure. The DevicePath member
          of this structure contains the user-mode name that the application uses with the
          Win32 function CreateFile to obtain a file handle to a HID collection.
    """
    # get HID device class guid
    g = GetHidGuid()

    # handle to an opaque device information set
    hInfo = SetupDiGetClassDevs(byref(g), None, None, (DIGCF_PRESENT | DIGCF_DEVICEINTERFACE))

    if hInfo == INVALID_HANDLE_VALUE:
        return []

    try:
        # retrieve all the available interface information.
        deviceInterface = SP_DEVICE_INTERFACE_DATA()
        deviceInterface.cbSize = sizeof(deviceInterface)

        deviceInterfaceDetail = SP_DEVICE_INTERFACE_DETAIL_DATA()
        deviceInterfaceDetail.cbSize = sizeof(deviceInterfaceDetail) - (sizeof(c_tchar)*(MAX_SP_DEV_INTERF_DETAIL_SIZE-1))

        deviceInfoData = SP_DEVINFO_DATA()
        deviceInfoData.cbSize = sizeof(deviceInfoData)

        i = 0
        requiredSize = c_ulong()
        parentDevice = c_ulong()
        results = []
        while setupapiDLL.SetupDiEnumDeviceInterfaces(hInfo, None, byref(g), i, byref(deviceInterface)):
            i += 1

            # validate if hid path would fit
            requiredSize.value = 0
            SetupDiGetDeviceInterfaceDetail(hInfo, byref(deviceInterface), None, 0, byref(requiredSize), None)
            if requiredSize.value > sizeof(deviceInterfaceDetail):
                sys.stderr.write("Error getting HID device info.\n")
                continue

            # it's ok to get the details
            SetupDiGetDeviceInterfaceDetail(hInfo, byref(deviceInterface), byref(deviceInterfaceDetail), requiredSize, None, byref(deviceInfoData))

            #get parent instance id (so we can discriminate on port)
            if setupapiDLL.CM_Get_Parent(byref(parentDevice), deviceInfoData.DevInst, 0) != 0: #CR_SUCCESS = 0
                parentDevice.value = 0 #null

            #get unique instance id str
            requiredSize.value = 0
            SetupDiGetDeviceInstanceId(hInfo, byref(deviceInfoData), None, 0, byref(requiredSize))
            if requiredSize.value > 0:
                deviceInstanceIdType = c_tchar * requiredSize.value
                deviceInstanceId = deviceInstanceIdType()
                SetupDiGetDeviceInstanceId(hInfo, byref(deviceInfoData), byref(deviceInstanceId), requiredSize, byref(requiredSize))
                hidDevice = HidDevice(deviceInterfaceDetail.DevicePath, parentDevice.value, deviceInstanceId.value)
            else:
                hidDevice = HidDevice(deviceInterfaceDetail.DevicePath, parentDevice.value)
            # add device to results
            if hidDevice.VendorId: #this means device it's not protected
                results.append(hidDevice)

    finally:
        # clean up
        setupapiDLL.SetupDiDestroyDeviceInfoList(hInfo)
    return results

class HidDeviceFilter(object):
    """This class allows searching for HID devices currently connected to the system, it also allows
    to search for specific devices (by filtering)"""
    def __init__(self, *args, **kwrds):
        self.filterParams = kwrds

    def getDevicesByParent(self, hidFilter=None):
        allDevs = self.getDevices(hidFilter)
        groupedDevs = dict()
        for hidDevice in allDevs:
            #keep a list of known devices matching parent device Ids
            parentId = hidDevice.getParentInstanceId()
            deviceSet = groupedDevs.get(parentId, [])
            deviceSet.append(hidDevice)
            if parentId not in groupedDevs:
                #add new
                groupedDevs[parentId] = deviceSet
        return groupedDevs

    def getDevices(self, hidFilter = None):
        """Filter a HID device list by current object parameters. Devices must match the
        all of the filterin parameters
        """
        if not hidFilter: #empty list or called without any parameters
            if type(hidFilter) == type(None):
                #request to query connected devices
                hidFilter = findAllHidDevices()
            else:
                return hidFilter
        #initially all accepted
        results = {}.fromkeys(hidFilter)

        #the filter parameters
        validatingAttributes = self.filterParams.keys()

        #first filter out restricted access devices
        for item in results.keys():
            if not item.isActive():
                del results[item]

        #filter out
        for item in validatingAttributes:
            if item.endswith("Includes"):
                item = item[:-len("Includes")]
            elif item.endswith("Mask"):
                item = item[:-len("Mask")]
            elif item +"Mask" in self.filterParams or item + "Includes" in self.filterParams:
                continue # value mask or string search is being queried
            elif item not in HidDevice._filter_attributes_:
                continue # field does not exist sys.error.write(...)
            #start filtering out
            for device in results.keys():
                if not hasattr(device, item):
                    del results[device]
                elif item + "Mask" in validatingAttributes:
                    #masked value
                    if getattr(device, item) & self.filterParams[item + "Mask"] != self.filterParams[item] & self.filterParams[item + "Mask"]:
                        del results[device]
                elif item + "Includes" in validatingAttributes:
                    #subset item
                    if self.filterParams[item + "Includes"] not in getattr(device, item):
                        del results[device]
                else:
                    #plain comparition
                    if getattr(device, item) != self.filterParams[item]:
                        del results[device]
            #
        return results.keys()

MAX_DEVICE_ID_LEN = 200 + 1 #+EOL (just in case)
class HidDeviceBaseClass(object):
    "Utility parent class for main HID device class"
    _rawReportsLock = threading.Lock()

class HidDevice(HidDeviceBaseClass):
    MAX_MANUFACTURER_STRING_LEN = 128 #it's actually 126 + 1 (null)
    MAX_PRODUCT_STRING_LEN = 128 #it's actually 126 + 1 (null)
    _filter_attributes_ = ["VendorId", "ProductId", "VersionNumber", "ProductStr", "ManufacturerStr"]

    def getParentInstanceId(self):
        return self.parentInstanceId

    def getParentDevice(self):
        if not self.parentInstanceId:
            return ""
        devBufferType = c_tchar * MAX_DEVICE_ID_LEN
        devBuffer = devBufferType()
        if CM_Get_Device_ID(self.parentInstanceId, byref(devBuffer), MAX_DEVICE_ID_LEN, 0) == 0: #success
            return devBuffer.value
        return ""

    def __init__(self, devicePath, parentInstanceId = 0, instanceId=""):
        "Interface for HID device as referenced by devicePath parameter"
        #allow safe access (and object browsing)
        self.__resetVars() #init hw related vars
        self.devicePath = devicePath
        self.instanceId = instanceId
        self.parentInstanceId = parentInstanceId
        self.ProductStr = ""
        self.ManufacturerStr = ""
        self.VendorId  = 0
        self.ProductId = 0
        self.VersionNumber = 0

        # HID device handle first
        hHid = CreateFile(devicePath, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, 0)
        if hHid == INVALID_HANDLE_VALUE:
            return

        try:
            # get device attributes
            hiddAttributes = HIDD_ATTRIBUTES()
            hiddAttributes.cbSize = sizeof(hiddAttributes)
            if not hidDll.HidD_GetAttributes(int(hHid), byref(hiddAttributes)):
                return #can't read attributes

            #set local references
            self.VendorId  = hiddAttributes.VendorId
            self.ProductId = hiddAttributes.ProductId
            self.VersionNumber = hiddAttributes.VersionNumber

            # manufacturer string
            vendorStringType = c_wchar * self.MAX_MANUFACTURER_STRING_LEN
            vendorStr = vendorStringType()
            if not hidDll.HidD_GetManufacturerString(int(hHid), byref(vendorStr), sizeof(vendorStr)) or not len(vendorStr.value):
                # would be any possibility to get a vendor id table?, maybe not worth it
                self.ManufacturerStr = "Unknown manufacturer"
            else:
                self.ManufacturerStr = vendorStr.value

            # string buffer for product string
            productStringType = c_wchar * self.MAX_PRODUCT_STRING_LEN
            productStr = productStringType()
            if not hidDll.HidD_GetProductString(int(hHid), byref(productStr), sizeof(productStr)) or not len(productStr.value):
                # alternate methode, refer to windows registry for product information
                pathParts = devicePath[len("\\\\.\\"):].split("#") # starts with r"\\.\" but my syntax highlighting has issues
                hReg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Enum\\" + \
                    pathParts[0] + "\\" + \
                    pathParts[1] + "\\" + \
                    pathParts[2]
                )
                self.ProductStr, r = _winreg.QueryValueEx(hReg, "DeviceDesc")
                _winreg.CloseKey(hReg)
            else:
                self.ProductStr = productStr.value

        finally:
            # clean up
            CloseHandle(hHid)

    def isActive(self):
        if not self.VendorId:
            return False
        return True

    def Open(self, inputReportHandler = None):
        """Open HID device and obtain 'Collection Information'.
        It effectevely prepares the HidDevice object for reading and writing"""
        if not self.VendorId or self.isOpened():
            return

        if self.isOpened():
            raise HIDError("Device already opened")

        hidHandle = CreateFile(
            self.devicePath,
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None, # no security
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED,
            0 )
        if hidHandle == INVALID_HANDLE_VALUE:
            raise HIDError("Error opening HID device: %s\n"%self.deviceName)

        self.__openStatus = True
        self.hidHandle = hidHandle
        #get preparsed data
        pPreparsedData = c_ulong()
        if not hidDll.HidD_GetPreparsedData(int(hidHandle), byref(pPreparsedData)):
            self.Close()
            raise HIDError("Failure to get HID preparsed data")
        self.pPreparsedData = pPreparsedData

        #get top level capabilities
        hidCaps = HIDP_CAPS()
        HIDP_STATUS( hidDll.HidP_GetCaps(pPreparsedData, byref(hidCaps)) )
        self.hidCaps = hidCaps

        #self.UsagePage = UsagePage(hidCaps.UsagePage) #friendly usage page name
        #self.Usage = Usage(hidCaps.UsagePage, hidCaps.Usage) #friendly usage name

        #proceed with button capabilities
        capsLength = c_ulong()

        allItems = [\
            (HidP_Input,   HIDP_BUTTON_CAPS, int(hidCaps.NumberInputButtonCaps),    hidDll.HidP_GetButtonCaps),
            (HidP_Input,   HIDP_VALUE_CAPS,  int(hidCaps.NumberInputValueCaps),     hidDll.HidP_GetValueCaps),
            (HidP_Output,  HIDP_BUTTON_CAPS, int(hidCaps.NumberOutputButtonCaps),   hidDll.HidP_GetButtonCaps),
            (HidP_Output,  HIDP_VALUE_CAPS,  int(hidCaps.NumberOutputValueCaps),    hidDll.HidP_GetValueCaps),
            (HidP_Feature, HIDP_BUTTON_CAPS, int(hidCaps.NumberFeatureButtonCaps),  hidDll.HidP_GetButtonCaps),
            (HidP_Feature, HIDP_VALUE_CAPS,  int(hidCaps.NumberFeatureValueCaps),   hidDll.HidP_GetValueCaps),
        ]

        for reportKind, structType, maxItems, getControlCaps in allItems:
            if not int(maxItems): continue #nothing here
            #create storage for control/data
            ctrlArrayType = structType * maxItems
            ctrlArray = ctrlArrayType()

            #target max size for api function
            capsLength.value = maxItems
            HIDP_STATUS( getControlCaps(\
                reportKind,
                byref(ctrlArray),
                byref(capsLength),
                pPreparsedData) )
            #keep reference of usages
            for idx in range(capsLength.value):
                usageItem = ctrlArray[idx]
                #by report type
                if not self.usagesStorage.has_key(reportKind):
                    self.usagesStorage[reportKind] = list()
                self.usagesStorage[reportKind].append( usageItem )
                #also add reportId to known reports set
                if not self.reportSet.has_key(reportKind):
                    self.reportSet[reportKind] = set()
                self.reportSet[reportKind].add( usageItem.ReportID )
        #now prepare the input report handler
        if hidCaps.InputReportByteLength:
            #first make templates for easy parsing input reports
            self.__inputReportTemplates = dict()
            for reportId in self.reportSet[HidP_Input]:
                self.__inputReportTemplates[reportId] = HidDevice.HidReport(self, HidP_Input, reportId)
            #prepare input reports handlers
            self._inputReportQueue = HidDevice.InputReportQueue(self.maxInputQueueSize, hidCaps.InputReportByteLength)
            self.__inputProcessingThread = HidDevice.InputReportProcessingThread(self)
            self.__readingThread = HidDevice.InputReportReaderThread(self, hidCaps.InputReportByteLength)
        #

    def SendOutputReport(self, data):
        """Send input/output/feature report ID = reportId, data should be a c_byte object
        with included the required report data"""
        assert( self.isOpened() )

        #make sure we have c_byte array storage
        if not ( isinstance(data, ctypes.Array) and issubclass(data._type_, c_byte) ):
            rawDataType = c_byte * len(data)
            rawData = rawDataType()
            for index, value in enumerate(data):
                rawData[index] = data[index]
        else:
            rawData = data
        #
        #TODO: Add a lock when writing (overlaped writes)
        overWrite = OVERLAPPED()
        overWrite.hEvent = CreateEvent(None, 0, 0, None)
        if overWrite.hEvent:
            _overlappedWrite = overWrite
            WriteFile(int(self.hidHandle), byref(rawData), len(rawData),
                None, byref(_overlappedWrite)) #none overlaped
            #print "ww"
            result = WaitForSingleObject(_overlappedWrite.hEvent, 10000 )
            #print "wf"
            CloseHandle(_overlappedWrite.hEvent)
            if result != WAIT_OBJECT_0: #success
                return False #device has being disconnected
        else:
            return WriteFile(int(self.hidHandle), byref(rawData), len(rawData),
                None, None) #none overlaped
        return True #completed

    def SendFeatureReport(self, data):
        """Send input/output/feature report ID = reportId, data should be a c_byte object
        with included the required report data"""
        #make sure we have c_byte array storage
        if not ( isinstance(data, ctypes.Array) and issubclass(data._type_, c_byte) ):
            rawDataType = c_byte * len(data)
            rawData = rawDataType()
            for index, value in enumerate(data):
                rawData[index] = data[index]
        else:
            rawData = data
        #
        bytesWritten = c_ulong()
        #TODO: Add a lock when writing (overlaped writes)
        return hidDll.HidD_SetFeature(int(self.hidHandle), byref(rawData), len(rawData))

    def __resetVars(self):
        #reset vars (for init or gc)
        self.__openStatus = False
        self.usagesStorage = dict()
        self.reportSet = dict()
        self.hidCaps = None
        self.pPreparsedData = None
        self.hidHandle = None
        #don't clean up the report quque because the
        #consumer & producer threads might neede it
        #self._inputReportQueue = None
        self.__evtHandlers = dict()

    def isPlugged(self):
        return self.devicePath and devicePathIsValid(self.devicePath)

    def isOpened(self):
        return self.__openStatus

    def Close(self):
        # free parsed data
        if not self.isOpened():
            #print "Already closed: %d"%self.hidHandle
            return
        #print "Closing: %d"%self.hidHandle
        self.__openStatus = False

        #finish reading thread
        if self.__readingThread and self.__readingThread.isAlive():
            self.__readingThread.abort()
            self.__readingThread = None

        #avoid posting new reports
        if self._inputReportQueue:
            self._inputReportQueue.release_events() #allow thead deadlocks
        #input report processor
        if self.__inputProcessingThread and self.__inputProcessingThread.isAlive():
            self.__inputProcessingThread.abort()
            self.__inputProcessingThread = None
        #properly close api handlers and pointers
        if self.pPreparsedData:
            hidDll.HidD_FreePreparsedData(self.pPreparsedData)
        if self.hidHandle:
            CloseHandle(self.hidHandle)
        #reset vars (for gc)
        self.__resetVars()

    def __del__(self):
        if self.isOpened():
            self.Close()

    class HidReport(object):
        """This class interfaces an actual HID physical report, providing a wrapper that exposes
        specific usages (usage page and usage ID) as a usageIdvalue map (dictionary).
        Example: A HID device might have an output report ID = 0x01, with the following usages;
        0x20 as a boolean (button), and 0x21 as a 3 bit value, then querying the HID object
        for the output report (by using hidObj.getOutputReport(0x01))
        """
        class ReportItem(object):
            def __init__(self, hidReport, capsRecord, usageId = 0):
                #assert(type(usageId) == type(1) or type(usageId) == type(1L)), "Numeric values of usageId only"
                self.hidReport = hidReport #from here we can get the parent hidObject
                self.capsRecord = capsRecord
                self.__isButton = isinstance(capsRecord, HIDP_BUTTON_CAPS)
                self.__isValue = isinstance(capsRecord, HIDP_VALUE_CAPS)
                self.__isValueArray = bool(self.__isValue and capsRecord.ReportCount > 1)
                self.__bitSize = 1
                self.__reportCount = 1
                if not usageId:
                    assert(not capsRecord.IsRange), "usageId should be supplied for range items"
                    self.usageId = capsRecord.union.NotRange.Usage
                else:
                    self.usageId = usageId
                self.__reportId = c_byte(capsRecord.ReportID)
                self.pageId = capsRecord.UsagePage
                self.__value = 0
                if capsRecord.IsRange:
                    #reference to usage within usage range
                    union = capsRecord.union.Range
                    offset = union.UsageMin - usageId
                    self.dataIndex = union.DataIndexMin + offset
                    self.stringIndex = union.StringMin + offset
                    self.designatorIndex = union.DesignatorMin + offset
                else:
                    #straigth reference
                    union = capsRecord.union.NotRange
                    self.dataIndex = union.DataIndex
                    self.stringIndex = union.StringIndex
                    self.designatorIndex = union.DesignatorIndex
                #verify it item is value array
                if self.__isValue:
                    if self.__isValueArray:
                        byteSize = (capsRecord.BitSize * capsRecord.ReportCount) / 8
                        if (capsRecord.BitSize * capsRecord.ReportCount) % 8: #remainder
                            byteSize += 1
                        valueType = c_byte * byteSize
                        self.__value = valueType()
                    self.__bitSize = capsRecord.BitSize
                    self.__reportCount = capsRecord.ReportCount

            def __len__(self):
                return self.__reportCount

            def __setitem__(self, index, value):
                "Allow to access value array by index"
                if not self.__isValueArray:
                    raise ValueError("Report item is not value usage array")
                if index < self.__reportCount:
                    byteIndex = (index * self.__bitSize) / 8
                    bitOffset = (index * self.__bitSize) % 8
                    bitValue = (value & ((1 << self.__bitSize) - 1)) << bitOffset
                    self.__value[byteIndex] &= bitValue
                    self.__value[byteIndex] |= bitValue
                else:
                    raise IndexError

            def __getitem__(self, index):
                "Allow to access value array by index"
                if not self.__isValueArray:
                    raise ValueError("Report item is not value usage array")
                if index < self.__reportCount:
                    byteIndex = (index * self.__bitSize) / 8
                    bitOffset = (index * self.__bitSize) % 8
                    return ((self.__value[byteIndex] >> bitOffset) & self.__bitSize )
                else:
                    raise IndexError

            def setValue(self, value):
                if self.__isValueArray:
                    if len(value) == self.__reportCount:
                        for index, item in enumerate(value):
                            self.__setitem__(index, item)
                    else:
                        raise ValueError("Value size should match report item size length")
                else:
                    self.__value = value & ((1 << self.__bitSize) - 1) #valid bits only

            def getValue(self):
                if self.__isValueArray:
                    if self.__bitSize == 8: #matching c_byte
                        return list(self.__value)
                    else:
                        result = []
                        for i in range(self.__reportCount):
                            result.append(self.__getitem__(i))
                        return result
                else:
                    return self.__value
            #value property
            value = property(getValue, setValue)

            @property
            def valueArray(self):
                #read only property
                return self.__value

            def key(self):
                "returns unique usage page & id long value"
                return (self.pageId << 16) | self.usageId

            def isValue(self):
                return self.__isValue

            def isButton(self):
                return self.__isButton

            def isValueArray(self):
                return self.__isValueArray

            def getUsageString(self):
                "Returns usage representation string (as embeded in HID device if available)"
                if self.stringIndex:
                    MAX_HID_STRING_LENGTH = 128
                    strUsageType = c_wchar * MAX_HID_STRING_LENGTH #128 max string length
                    buffer = strUsageType()
                    hidDll.HidD_GetIndexedString(self.hidReport.getHidObject(), self.stringIndex,
                        byref(buffer), MAX_HID_STRING_LENGTH-1)
                    return buffer.value
                return ""

            def __repr__(self):
                r = []
                if self.stringIndex:
                    r.append( self.getUsageString() )
                r.append( "pageId=%s"%hex(self.pageId) )
                r.append( "usageId=%s"%hex(self.usageId) )
                #r.append( "dataIndex=%s"%self.dataIndex )
                #r.append( "reportId=%s"%hex(self.__reportId.value) )
                if self.__value != None:
                    r.append( "value=%s)"%hex(self.__value) )
                else:
                    r.append( "value=[None])" )
                usageType = ""
                if self.isButton():
                    usageType = "Button"
                elif self.isValue():
                    usageType = "Value"
                return usageType + "Usage item, %s (" % hex(getFullUsageId(self.pageId, self.usageId)) + ', '.join(r) + ')'
        #class ReportItem finishes ***********************

        def __init__(self, hidObj, reportType, reportId):
            if reportType == HidP_Input:
                self.__rawReportSize = hidObj.hidCaps.InputReportByteLength
            elif reportType == HidP_Output:
                self.__rawReportSize = hidObj.hidCaps.OutputReportByteLength
            elif reportType == HidP_Feature:
                self.__rawReportSize = hidObj.hidCaps.FeatureReportByteLength
            else:
                raise HIDError("Unsupported report type")
            self.__reportType = reportType  #target report type
            self.__valueArrayItems = list() #array of usages items
            self.__hidObj = hidObj      #parent hid object
            self.__reportId = c_byte(reportId)  #target report Id
            self.__items = dict()       #access items by 'full usage' key
            self.__indexItems = dict()  #access internal items by HID dll usage index
            self.__rawData = None       #buffer storage (if needed)
            self.__usageDataList = None #hid api HIDP_DATA array (if allocated)
            #build report items list, browse parent hid object for report items
            for item in hidObj.usagesStorage.get(reportType, []):
                if item.ReportID == reportId:
                    if not item.IsRange:
                        #regular 'single' usage
                        reportItem = self.ReportItem(self, item)
                        self.__items[reportItem.key()] = reportItem
                        self.__indexItems[reportItem.dataIndex] = reportItem
                        if reportItem.isValueArray():
                            self.__bAnyValueArray = True
                    else:
                        for usageId in range(item.union.Range.UsageMin, item.union.Range.UsageMax):
                            reportItem =  self.ReportItem(self, item, usageId)
                            self.__items[reportItem.key()] = reportItem
                            self.__indexItems[reportItem.dataIndex] = reportItem
                    #item is value array?
                    if isinstance(item, HIDP_VALUE_CAPS) and item.ReportCount > 1:
                        self.__valueArrayItems.append(reportItem)
                #
            #
        __reportTypeDict = {
            HidP_Input: "Input",
            HidP_Output: "Output",
            HidP_Feature: "Feature",
        }
        #read only properties
        @property
        def reportId(self):
            return self.__reportId.value

        @property
        def reportType(self):
            return self.__reportTypeDict[self.__reportType]

        @property
        def hidObject(self):
            return self.__hidObject

        def __repr__(self):
            return "HID report object (%s report, id=0x%02x), %d items included" \
                % (self.reportType, self.__reportId.value, len(self.__items) )

        def __getitem__(self, key):
            if isinstance(key, self.ReportItem):
                key = key.key()
            return self.__items[key]

        def __contains__(self, key):
            if isinstance(key, self.ReportItem):
                key = key.key()
            return key in self.__items

        def __len__(self):
            return len(self.__items)

        def has_key(self, key):
            return self.__contains__(key)

        def items(self):
            return self.__items.items()

        def keys(self):
            return self.__items.keys()

        def values(self):
            return self.__items.values()

        def getHidObject(self):
            return self.__hidObj

        def getUsages(self):
            "Return a dictionary mapping full usages Ids to plain values"
            retValue = dict()
            for key, usage in self.items():
                retValue[key] = usage.value
            return retValue

        def setRawData(self, rawData):
            """Set usage values based on given raw data, item[0] is reportId, lenght should match 'rawDataLength' value,
            best performance if rawData is c_byte ctypes array object type"""
            #pre-parsed data should exist
            if not self.__hidObj.pPreparsedData:
                raise HIDError("HID object close or unable to request preparsed report data")
            #valid lenght
            if len(rawData) != self.__rawReportSize:
                raise HIDError("Report size has to be %d elements (bytes)" % self.__rawReportSize)

            #allocate c_byte storage
            if self.__rawData == None: #first time only, create storage
                rawDataType = c_byte * self.__rawReportSize
                self.__rawData = rawDataType()
            else:
                #initialize
                ctypes.memset(self.__rawData, 0, len(self.__rawData))
            #convert types if not appropiate
            for index, value in enumerate(rawData):
                self.__rawData[index] = rawData[index]
            if not self.__usageDataList: # create HIDP_DATA buffer
                maxItems = hidDll.HidP_MaxDataListLength(self.__reportType, self.__hidObj.pPreparsedData)
                dataListType = HIDP_DATA * maxItems
                self.__usageDataList = dataListType()
            #reference HIDP_DATA bufer
            dataList = self.__usageDataList
            dataLen = c_ulong(len(dataList))

            #reset old values
            for item in self.values():
                if item.isValueArray():
                    item.value = [0,]*len(item)
                else:
                    item.value = 0
            #ready, parse raw data
            HIDP_STATUS( hidDll.HidP_GetData(self.__reportType, byref(dataList), byref(dataLen), self.__hidObj.pPreparsedData,
                byref(self.__rawData), len(self.__rawData)) )
            #set values on internal report item objects
            for idx in range(dataLen.value):
                valueItem = dataList[idx]
                reportItem = self.__indexItems.get(valueItem.DataIndex)
                if not reportItem:
                    #TODO: This is not expected to happen
                    continue
                if reportItem.isValue():
                    reportItem.value = valueItem.Value.RawValue
                elif reportItem.isButton():
                    reportItem.value = valueItem.Value.On
                else:
                    pass # HID api should give us either, at least one of 'em
            #get values of array items
            for item in self.__valueArrayItems:
                #ask hid api to parse
                HIDP_STATUS( hidDll.HidP_GetUsageValueArray(self.__reportType, item.pageId,
                    0, #link collection
                    item.usageId, #short usage
                    byref(item.valueArray), #output data (c_byte storage)
                    len(item.valueArray), self.__hidObj.pPreparsedData, byref(rawData), sizeof(rawData)) )
                #
                #print list(item.valueArray)

        class ReadOnlyList(UserList):
            "Read only sequence wrapper"
            def __init__(self, anyList):
                UserList.__init__(self, anyList)
            def __setitem__(self, index, value):
                raise ValueError("Object is read-only")

        def __prepareRawData(self):
            "Format internal __rawData storage according to usages setting"
            #pre-parsed data should exist
            if not self.__hidObj.pPreparsedData:
                raise HIDError("HID object close or unable to request preparsed report data")
            #allocate c_byte storage
            if self.__rawData == None: #first time only, create storage
                rawDataType = c_byte * self.__rawReportSize
                self.__rawData = rawDataType()
            else:
                #initialize
                ctypes.memset(self.__rawData, 0, len(self.__rawData))
            try:
                HIDP_STATUS( hidDll.HidP_InitializeReportForID(self.__reportType, self.__reportId, self.__hidObj.pPreparsedData,
                    byref(self.__rawData), self.__rawReportSize) )
                #
            except HIDError:
                self.__rawData[0] = self.__reportId
            #check if we have pre-allocated usage storage
            if not self.__usageDataList: # create HIDP_DATA buffer
                maxItems = hidDll.HidP_MaxDataListLength(self.__reportType, self.__hidObj.pPreparsedData)
                if not maxItems:
                    raise HIDError("Internal error while requesing usage length")
                dataListType = HIDP_DATA * maxItems
                self.__usageDataList = dataListType()
            #reference HIDP_DATA bufer
            dataList = self.__usageDataList
            #set buttons and values usages first
            nTotalUsages = 0
            singleUsage = USAGE()
            singleUsageLen = c_ulong()
            for dataIndex, reportItem in self.__indexItems.items():
                if (not reportItem.isValueArray()) and reportItem.value != None:
                    #set by user, include in request
                    if reportItem.isButton() and reportItem.value:
                        #windows just can't handle button arrays!, we just don't know if usage
                        #is button array or plain single usage, so we set all usages at once
                        singleUsage.value = reportItem.usageId
                        singleUsageLen.value = 1
                        HIDP_STATUS( hidDll.HidP_SetUsages(self.__reportType, reportItem.pageId, 0,
                            byref(singleUsage), byref(singleUsageLen), self.__hidObj.pPreparsedData,
                            byref(self.__rawData), self.__rawReportSize) )
                        continue
                    elif reportItem.isValue() and not reportItem.isValueArray():
                        dataList[nTotalUsages].Value.RawValue = reportItem.value
                    else:
                        continue #do nothing
                    dataList[nTotalUsages].Reserved = 0 #reset
                    dataList[nTotalUsages].DataIndex = dataIndex #reference
                    nTotalUsages += 1
            #set data if any usage is not 'none' (and not any value array)
            if nTotalUsages:
                #some usages set
                usageLen = c_ulong(nTotalUsages)
                HIDP_STATUS( hidDll.HidP_SetData(self.__reportType, byref(dataList), byref(usageLen), self.__hidObj.pPreparsedData,
                    byref(self.__rawData), self.__rawReportSize) )
            #set values based on value arrays
            for reportItem in self.__valueArrayItems:
                HIDP_STATUS( hidDll.HidP_SetUsageValueArray(self.__reportType, reportItem.pageId,
                    0, #all link collections
                    reportItem.usageId,
                    byref(reportItem.valueArray),
                    len(reportItem.valueArray),
                    self.__hidObj.pPreparsedData, byref(self.__rawData), len(self.__rawData)) )

        def getRawData(self):
            """Get raw HID report based on internal report item settings, creates new c_bytes storage"""
            if self.__reportType != HidP_Output and self.__reportType != HidP_Feature:
                raise HidError("Only for output or feature reports")
            self.__prepareRawData()
            #return read-only object for internal storage
            return self.ReadOnlyList(self.__rawData)

        def Send(self, rawData = None, bRefreshItems = False):
            "Prepare HID raw report (unless rawData is provided) and send it to HID device"
            if self.__reportType != HidP_Output and self.__reportType != HidP_Feature:
                raise HidError("Only for output or feature reports")
            #valid lenght
            if rawData and (len(rawData) != self.__rawReportSize):
                raise HIDError("Report size has to be %d elements (bytes)" % self.__rawReportSize)
            #shold be valid report id
            if rawData and rawData[0] != self.__reportId:
                raise HIDError("Not matching report id")
            #
            if self.__reportType != HidP_Output and self.__reportType != HidP_Feature:
                raise HidError("Can only send output or feature reports")
            #
            #convert types if not appropiate
            if not rawData:
                self.__prepareRawData()
            elif not ( isinstance(rawData, ctypes.Array) and issubclass(rawData._type_, c_byte) ):
                if self.__rawData == None: #first time only, create storage
                    rawDataType = c_byte * len(rawData)
                    self.__rawData = rawDataType()
                for index, value in enumerate(rawData):
                    self.__rawData[index] = rawData[index]
            #reference proper object
            rawData = self.__rawData
            if self.__reportType == HidP_Output:
                self.__hidObj.SendOutputReport(rawData)
            elif self.__reportType == HidP_Feature:
                self.__hidObj.SendFeatureReport(rawData)
            else:
                pass #can't get here (yet)

        def Get(self, bProcessRawReport = True):
            "Read report from device"
            if self.__reportType != HidP_Input and self.__reportType != HidP_Feature:
                raise HidError("Only for input or feature reports")
            #allocate c_byte storage
            if self.__rawData == None: #first time only, create storage
                rawDataType = c_byte * self.__rawReportSize
                self.__rawData = rawDataType()
            else:
                #initialize
                ctypes.memset(self.__rawData, 0, len(self.__rawData))
            rawData = self.__rawData
            rawData[0] = self.__reportId
            readFunction = None
            if self.__reportType == HidP_Feature:
                readFunction = hidDll.HidD_GetFeature
            elif self.__reportType == HidP_Input:
                readFunction = hidDll.HidD_GetInputReport
            if readFunction and readFunction(int(self.__hidObj.hidHandle), byref(rawData), len(rawData)):
                #success
                if bProcessRawReport:
                    self.__hidObj._processRawReport(rawData)
                return self.ReadOnlyList(rawData)
            return self.ReadOnlyList([])

        #class HIDReport finishes ***********************

    def __findReports(self, reportType, usagePage, usageId = 0):
        "Find input report referencing HID usage control/data item"
        if not self.isOpened():
            raise HIDError("Device must be opened")
        #
        results = list()
        if usagePage:
            for reportId in self.reportSet.get(reportType, set()):
                #build report object, gathering usages matching reportId
                reportObj = HidDevice.HidReport(self, reportType, reportId)
                if getFullUsageId(usagePage, usageId) in reportObj:
                    results.append( reportObj )
        else:
            #all (any one)
            for reportId in self.reportSet.get(reportType, set()):
                reportObj = HidDevice.HidReport(self, reportType, reportId)
                results.append( reportObj )
        return results

    def countAllFeatureReports(self):
        return self.hidCaps.NumberFeatureButtonCaps + self.hidCaps.NumberFeatureValueCaps

    def findInputReports(self, usagePage = 0, usageId = 0):
        "Find input reports referencing HID usage item"
        return self.__findReports(HidP_Input, usagePage, usageId)

    def findOutputReports(self, usagePage = 0, usageId = 0):
        "Find output report referencing HID usage control/data item"
        return self.__findReports(HidP_Output, usagePage, usageId)

    def findFeatureReports(self, usagePage = 0, usageId = 0):
        "Find feature report referencing HID usage control/data item"
        return self.__findReports(HidP_Feature, usagePage, usageId)

    def findAnyReports(self, usagePage = 0, usageId = 0):
        """Find any report type referencing HID usage control/data item
        Results are returned in a dictionary mapping reportType to usage lists"""
        result = []
        items = [
            (HidP_Input,    self.FindInputReport(usagePage, usageId)),
            (HidP_Output,   self.FindOutputReport(usagePage, usageId)),
            (HidP_Feature,  self.FindFeatureReport(usagePage, usageId)),
        ]
        return dict([(t,r) for t,r in items if r])

    maxInputQueueSize = 20
    evt_decision = {
        #a=oldValue, b=newValue
        HID_EVT_NONE: False ,
        HID_EVT_CHANGED:    lambda a,b: a != b,
        HID_EVT_PRESSED:    lambda a,b: b and not a,
        HID_EVT_RELEASED:   lambda a,b: a and not b,
        HID_EVT_SET:        lambda a,b: bool(b),
        HID_EVT_CLEAR:      lambda a,b: not b,
    }

    @synchronized(HidDeviceBaseClass._rawReportsLock)
    def _processRawReport(self, rawReport):
        "Default raw input report data handler"
        myDebug = False
        if not self.__evtHandlers or not self.isOpened():
            return

        if not rawReport[0] and not devicePathIsValid(self.devicePath):
            #windows XP sends empty report when disconnecting
            self.Close() #device disconnected
            return
        #used pre-parsed report templates
        reportTemplate = self.__inputReportTemplates[rawReport[0]] #by report id
        #old condition
        oldValues = reportTemplate.getUsages()
        #parset incomming data
        reportTemplate.setRawData(rawReport)
        #get new data
        newValues = reportTemplate.getUsages()
        #now diff
        event_applies = self.evt_decision
        for key in newValues:
            if key in self.__evtHandlers:
                #check if event handler exist!
                for eventType, handlers in self.__evtHandlers[key].items(): #key=eventType, values=handler set
                    newValue = newValues[key]
                    if event_applies[eventType](oldValues[key], newValue):
                        #decison applies, call handlers
                        for hFcnt in handlers:
                            hFcnt(newValue, eventType)
        if myDebug:
            print 'HID report:',
            for item in rawReport:
                print hex(item),
            print '\n'

    def findInputUsage(self, fullUsageId):
        "Check if full usage Id included in input reports set"
        for reportId, reportObj in self.__inputReportTemplates.items():
            if fullUsageId in reportObj:
                return reportId
        return 0

    def addEventHandler(self, fullUsageId, handlerFunction, eventType = HID_EVT_CHANGED):
        "Add event handler for usage value/button changes"
        if not self.findInputUsage(fullUsageId):
            #do not add handler
            return
        #get dict for full usages
        topMapHandler = self.__evtHandlers.get(fullUsageId, dict())
        eventHandlerSet = topMapHandler.get(eventType, set())
        if handlerFunction not in eventHandlerSet:
            #add a new handler
            eventHandlerSet.add(handlerFunction)
        if eventType not in topMapHandler:
            topMapHandler[eventType] = eventHandlerSet
        if fullUsageId not in self.__evtHandlers:
            self.__evtHandlers[fullUsageId] = topMapHandler

    class InputReportQueue(object):
        def __init__(self, maxSize, reportSize):
            self.__lockedDown = False
            self.maxSize = maxSize
            self.bufReportType = c_byte * reportSize
            self.usedQueue = []
            self.freshQueue = []
            self.usedLock = threading.Lock()
            self.freshLock = threading.Lock()
            self.freshChangedEvent = threading.Event()

        #@logging_decorator
        def getNew(self):
            "Allocates storage for input report"
            if self.__lockedDown:
                return None
            self.usedLock.acquire()
            if len(self.usedQueue):
                #we can reuse items
                emptyReport = self.usedQueue.pop(0)
                if not self.freshQueue and self.usedQueue:
                    #the consumer thread seems now faster than the producers, so...
                    del emptyReport
                    emptyReport = self.usedQueue.pop(0) #reduce the spare buffers queue
                self.usedLock.release()
                ctypes.memset(emptyReport, 0, sizeof(emptyReport))
            else:
                self.usedLock.release()
                #create brand new storage
                emptyReport = self.bufReportType() #auto initialized to '0' by ctypes
            return emptyReport

        #@logging_decorator
        def post(self, rawReport):
            if self.__lockedDown:
                return
            while True:
                self.freshLock.acquire()
                if len(self.freshQueue) >= self.maxSize:
                    self.freshLock.release()
                    self.freshChangedEvent.wait()
                    if self.__lockedDown:
                        return
                    self.freshChangedEvent.clear()
                    continue
                break
            self.freshQueue.append( rawReport )
            self.freshLock.release()
            self.freshChangedEvent.set()

        def reuse(self, rawReport):
            "Reuse not posted report"
            if self.__lockedDown:
                return
            self.usedLock.acquire()
            #we can reuse this item
            self.usedQueue.append(rawReport)
            self.usedLock.release()

        #@logging_decorator
        def get(self):
            if self.__lockedDown:
                return None
            while True:
                self.freshLock.acquire()
                if not self.freshQueue: # resource locked but no data!
                    self.freshLock.release()
                    self.freshChangedEvent.wait()
                    if self.__lockedDown:
                        return None
                    self.freshChangedEvent.clear()
                    continue
                break
            item = self.freshQueue.pop(0)
            self.freshLock.release()
            self.freshChangedEvent.set()
            return item

        def release_events(self):
            self.__lockedDown = True
            self.freshChangedEvent.set()

    class InputReportProcessingThread(threading.Thread):
        "Input reports handler helper class"
        def __init__(self, hidObj):
            threading.Thread.__init__(self)
            self.__abort = False
            self.hidObj = hidObj
            self.start()

        def abort(self):
            self.__abort = True
            maxTime = 1.0
            while maxTime > 0.0 and self.isAlive():
                time.sleep(0.050)
                maxTime -= 0.050

        def run(self):
            hidObj = self.hidObj
            while hidObj.isOpened() and not self.__abort:
                rawReport = hidObj._inputReportQueue.get()
                if not rawReport: continue
                hidObj._processRawReport(rawReport)

        def __del__(self):
            self.abort()

    class InputReportReaderThread(threading.Thread):
        "Helper to receive input reports"
        def __init__(self, hidObj, rawReportSize):
            threading.Thread.__init__(self)
            self.__abort = False
            self.hidObj = hidObj
            self.rawReportSize = rawReportSize
            self.__overlappedReadObj = None
            if self.rawReportSize:
                self.start()

        def abort(self):
            if not self.__abort:
                self.__abort = True
            if self.isAlive() and self.__overlappedReadObj:
                # force overlapped events completition
                SetEvent(self.__overlappedReadObj.hEvent)
            maxTime = 1.0
            while maxTime > 0 and self.isAlive():
                time.sleep(0.050)
                maxTime -= 0.050

        def __del__(self):
            self.abort() #make sure we do a clean exit

        def run(self):
            reportLen = self.rawReportSize
            if not self.rawReportSize:
                #don't raise any error as the hid object can still be used for writing reports
                raise HIDError("Attempting to read input reports on non capable HID device")

            overRead = OVERLAPPED()
            overRead.hEvent = CreateEvent(None, 0, 0, None)
            if overRead.hEvent:
                self.__overlappedReadObj = overRead
            else:
                raise HIDError("Error when create hid event resource")

            bytesRead = c_ulong()
            #
            hidObj = self.hidObj
            n = self.rawReportSize
            #print "reader set: %d"%hidObj.hidHandle
            while not self.__abort:
                #get storage
                bufReport = hidObj._inputReportQueue.getNew()
                if not bufReport: continue
                # async read from device
                bytesRead.value = 0
                if self.__abort:
                    break
                result = ReadFile(int(hidObj.hidHandle), byref(bufReport), int(n), byref(bytesRead), byref(self.__overlappedReadObj))
                if result == NO_ERROR or result == ERROR_IO_PENDING:
                    #wait for event
                    if self.__abort:
                        break
                    #print "rw: %d"%hidObj.hidHandle
                    result = WaitForSingleObject(self.__overlappedReadObj.hEvent, INFINITE )
                    #print "rf: %d"%hidObj.hidHandle
                    if result != WAIT_OBJECT_0: #success
                        break #device has being disconnected
                else:
                    error = ctypes.GetLastError()
                    if error == 997: #overlapped operation in progress
                        time.sleep(0.05) #HACKME: This aint pretty!, 50ms
                        hidObj._inputReportQueue.reuse(bufReport)
                        #print 'rc'
                        continue
                    raise HIDError("Error %d when trying to read from HID device: %s"%(error, ctypes.FormatError(error)))
                # signal raw data already read
                hidObj._inputReportQueue.post( bufReport )
            #clen up
            overRead = self.__overlappedReadObj
            self.__overlappedReadObj = None
            CloseHandle(overRead.hEvent)
            hidObj.Close()
            #print "reader closed: %d"%hidObj.hidHandle

    def __repr__(self):
        return "HID device (vID=0x%04x, pID=0x%04x, v=0x%04x); %s; %s, Path: %s"%(self.VendorId, self.ProductId, self.VersionNumber, self.ManufacturerStr, self.ProductStr, self.devicePath)

if __name__ == '__main__':
    #simple test
    from tools import writeDocumentation
    allHids = findAllHidDevices()
    if allHids:
        print "Found HID class devices!, full details..."
        for dev in allHids:
            print dev, '\tPath:', dev.devicePath, '\n\tInstance:', dev.instanceId, '\n\t\Port (ID):', dev.getParentInstanceId(), '\n\tPort (str)', dev.getParentDevice()
            #
            print "Checking caps..."
            print "-----------------"
            #
            for dev in HidDeviceFilter().getDevices():
                #dev = HidDeviceFilter(ManufacturerStrIncludes='Plantronics').getDevices()[1]
                print '*', dev
                try:
                    dev.Open()
                    readingOnly = False
                    if not readingOnly:
                        writeDocumentation(dev, sys.stdout)
                    else:
                        print "Waiting for data..."
                        while dev.isOpened():
                            pass
                        break
                finally:
                    dev.Close()
    else:
        print "There's not any non system HID class device available"
#
