#
import ctypes
from ctypes import Structure, Union, c_byte, c_char, c_int, c_long, c_ulong, c_ushort, c_wchar
from ctypes import pointer, byref, sizeof, POINTER
from ctypes.wintypes import c_char, ULONG, BOOLEAN, BYTE, WORD, DWORD, HANDLE
from helpers import InspectStruct

def os_supports_unicode():
    return False
    
#dll references
setupapiDLL         = ctypes.windll.setupapi
hidDll              = ctypes.windll.hid
kernel32            = ctypes.windll.kernel32

#os independent functions
ReadFile            = kernel32.ReadFile
WriteFile           = kernel32.WriteFile
CloseHandle         = kernel32.CloseHandle
SetEvent            = kernel32.SetEvent
WaitForSingleObject = kernel32.WaitForSingleObject
#SetupDiGetDeviceInstanceId = setupapiDLL.SetupDiGetDeviceInstanceId

#os dependant functions and definitions
if not os_supports_unicode():
    c_tchar = c_char
    SetupDiGetDeviceInterfaceDetail = setupapiDLL.SetupDiGetDeviceInterfaceDetailA
    SetupDiGetDeviceInstanceId      = setupapiDLL.SetupDiGetDeviceInstanceIdA
    SetupDiGetClassDevs = setupapiDLL.SetupDiGetClassDevsA
    CM_Get_Device_ID    = setupapiDLL.CM_Get_Device_IDA
    CreateFile          = kernel32.CreateFileA
    CreateEvent         = kernel32.CreateEventA
else:
    c_tchar = c_wchar
    SetupDiGetDeviceInterfaceDetail = setupapiDLL.SetupDiGetDeviceInterfaceDetailW
    SetupDiGetDeviceInstanceId      = setupapiDLL.SetupDiGetDeviceInstanceIdA
    SetupDiGetClassDevs = setupapiDLL.SetupDiGetClassDevsW
    CM_Get_Device_ID    = setupapiDLL.CM_Get_Device_IDW
    CreateFile          = kernel32.CreateFileW
    CreateEvent         = kernel32.CreateEventW


bVerbose = True
usbVerbose = False
class HIDError(Exception):
    pass
    
#structures for ctypes
class GUID(Structure):
    _fields_ = [("Data1", DWORD),
                ("Data2", WORD),
                ("Data3", WORD),
                ("Data4", BYTE * 8)]

class OVERLAPPED(Structure):
    _fields_ = [
        ("Internal", c_ulong),
        ("InternalHigh", c_ulong),
        ("Offset", c_ulong),
        ("OffsetHigh", c_ulong),
        ("hEvent", c_ulong)
    ]
    
#**************
# SetupApi.dll
class SP_DEVICE_INTERFACE_DATA(Structure):
    _fields_ = [("cbSize", c_ulong),
        ("InterfaceClassGuid", GUID),
        ("Flags", c_ulong),
        ("Reserved", POINTER(ULONG))
    ]

MAX_SP_DEV_INTERF_DETAIL_SIZE = 512
class SP_DEVICE_INTERFACE_DETAIL_DATA(Structure):
    _fields_ = [("cbSize", DWORD),
        ("DevicePath", c_tchar * MAX_SP_DEV_INTERF_DETAIL_SIZE)
    ]

class SP_DEVINFO_DATA(Structure):
    _fields_ = [("cbSize", DWORD),
        ("ClassGuid", GUID),
        ("DevInst", DWORD),
        ("Reserved", POINTER(ULONG)),
    ]
    
# Flags controlling what is included in the device information set built
# by SetupDiGetClassDevs
DIGCF_DEFAULT         = 0x00000001  # only valid with DIGCF_DEVICEINTERFACE
DIGCF_PRESENT         = 0x00000002
DIGCF_ALLCLASSES      = 0x00000004
DIGCF_PROFILE         = 0x00000008
DIGCF_DEVICEINTERFACE = 0x00000010

#*******
# hid.dll
class HIDD_ATTRIBUTES(Structure):
    _fields_ = [("cbSize", DWORD),
        ("VendorId", c_ushort),
        ("ProductId", c_ushort),
        ("VersionNumber", c_ushort)
    ]

class HIDP_CAPS(Structure):
    _fields_ = [
        ("Usage", c_ushort), #usage id
        ("UsagePage", c_ushort), #usage page
        ("InputReportByteLength", c_ushort),
        ("OutputReportByteLength", c_ushort),
        ("FeatureReportByteLength", c_ushort),
        ("Reserved", c_ushort * 17),
        ("NumberLinkCollectionNodes", c_ushort),
        ("NumberInputButtonCaps", c_ushort),
        ("NumberInputValueCaps", c_ushort),
        ("NumberInputDataIndices", c_ushort),
        ("NumberOutputButtonCaps", c_ushort),
        ("NumberOutputValueCaps", c_ushort),
        ("NumberOutputDataIndices", c_ushort),
        ("NumberFeatureButtonCaps", c_ushort),
        ("NumberFeatureValueCaps", c_ushort),
        ("NumberFeatureDataIndices", c_ushort)
    ]

class HIDP_BUTTON_CAPS(Structure):
    class RANGE_NOT_RANGE(Union):
        class RANGE(Structure):
            _fields_ = [
                ("UsageMin", c_ushort),     ("UsageMax", c_ushort),
                ("StringMin", c_ushort),    ("StringMax", c_ushort),
                ("DesignatorMin", c_ushort),("DesignatorMax", c_ushort),
                ("DataIndexMin", c_ushort), ("DataIndexMax", c_ushort)
            ]

        class NOT_RANGE(Structure):
            _fields_ = [
                ("Usage", c_ushort),            ("Reserved1", c_ushort),
                ("StringIndex", c_ushort),      ("Reserved2", c_ushort),
                ("DesignatorIndex", c_ushort),  ("Reserved3", c_ushort),
                ("DataIndex", c_ushort),        ("Reserved4", c_ushort)
            ]
        _fields_ = [
            ("Range", RANGE),
            ("NotRange", NOT_RANGE)
        ]

    _fields_ = [
        ("UsagePage", c_ushort),
        ("ReportID", c_byte),
        ("IsAlias", BOOLEAN),
        ("BitField", c_ushort),
        ("LinkCollection", c_ushort),
        ("LinkUsage", c_ushort),
        ("LinkUsagePage", c_ushort),
        ("IsRange", BOOLEAN),
        ("IsStringRange", BOOLEAN),
        ("IsDesignatorRange", BOOLEAN),
        ("IsAbsolute", BOOLEAN),
        ("Reserved", c_ulong * 10),
        ("union", RANGE_NOT_RANGE)
    ]
    def InspectStruct(self):
        if self.IsRange:
            return InspectStruct(self)+InspectStruct(self.union.Range)
        else:
            return InspectStruct(self)+InspectStruct(self.union.NotRange)
            
class HIDP_VALUE_CAPS(Structure):
    class RANGE_NOT_RANGE(Union):
        class RANGE(Structure):
            _fields_ = [
                ("UsageMin", c_ushort),     ("UsageMax", c_ushort),
                ("StringMin", c_ushort),    ("StringMax", c_ushort),
                ("DesignatorMin", c_ushort),("DesignatorMax", c_ushort),
                ("DataIndexMin", c_ushort), ("DataIndexMax", c_ushort)
            ]

        class NOT_RANGE(Structure):
            _fields_ = [
                ("Usage", c_ushort),            ("Reserved1", c_ushort),
                ("StringIndex", c_ushort),      ("Reserved2", c_ushort),
                ("DesignatorIndex", c_ushort),  ("Reserved3", c_ushort),
                ("DataIndex", c_ushort),        ("Reserved4", c_ushort)
            ]
        _fields_ = [
            ("Range", RANGE),
            ("NotRange", NOT_RANGE)
        ]
        
    _fields_ = [
        ("UsagePage", c_ushort),
        ("ReportID", c_byte),
        ("IsAlias", BOOLEAN),
        ("BitField", c_ushort),
        ("LinkCollection", c_ushort),
        ("LinkUsage", c_ushort),
        ("LinkUsagePage", c_ushort),
        ("IsRange", BOOLEAN),
        ("IsStringRange", BOOLEAN),
        ("IsDesignatorRange", BOOLEAN),
        ("IsAbsolute", BOOLEAN),
        ("HasNull", BOOLEAN),
        ("Reserved", c_byte),
        ("BitSize", c_ushort),
        ("ReportCount", c_ushort),
        ("Reserved2", c_ushort * 5),
        ("UnitsExp", c_ulong),
        ("Units", c_ulong),
        ("LogicalMin", c_long),
        ("LogicalMax", c_long),
        ("PhysicalMin", c_long),
        ("PhysicalMax", c_long),
        ("union", RANGE_NOT_RANGE)
    ]
    def InspectStruct(self):
        if self.IsRange:
            return InspectStruct(self)+InspectStruct(self.union.Range)
        else:
            return InspectStruct(self)+InspectStruct(self.union.NotRange)

class HIDP_DATA(Structure):
    class HIDP_DATA_VALUE(Union):
        _fields_ = [
            ("RawValue", c_ulong),
            ("On", BOOLEAN),
        ]

    _fields_ = [
        ("DataIndex", c_ushort),
        ("Reserved", c_ushort),
        ("Value", HIDP_DATA_VALUE)
    ]

#get report
HidP_Input   = 0x0000
HidP_Output  = 0x0001
HidP_Feature = 0x0002

FACILITY_HID_ERROR_CODE = 0x11
def HIDP_ERROR_CODES(SEV, CODE):
    return (((SEV) << 28) | (FACILITY_HID_ERROR_CODE << 16) | (CODE)) & 0xFFFFFFFF

class HIDP_STATUS(object):
    HIDP_STATUS_SUCCESS                  = (HIDP_ERROR_CODES(0x0,0))
    HIDP_STATUS_NULL                     = (HIDP_ERROR_CODES(0x8,1))
    HIDP_STATUS_INVALID_PREPARSED_DATA   = (HIDP_ERROR_CODES(0xC,1))
    HIDP_STATUS_INVALID_REPORT_TYPE      = (HIDP_ERROR_CODES(0xC,2))
    HIDP_STATUS_INVALID_REPORT_LENGTH    = (HIDP_ERROR_CODES(0xC,3))
    HIDP_STATUS_USAGE_NOT_FOUND          = (HIDP_ERROR_CODES(0xC,4))
    HIDP_STATUS_VALUE_OUT_OF_RANGE       = (HIDP_ERROR_CODES(0xC,5))
    HIDP_STATUS_BAD_LOG_PHY_VALUES       = (HIDP_ERROR_CODES(0xC,6))
    HIDP_STATUS_BUFFER_TOO_SMALL         = (HIDP_ERROR_CODES(0xC,7))
    HIDP_STATUS_INTERNAL_ERROR           = (HIDP_ERROR_CODES(0xC,8))
    HIDP_STATUS_I8042_TRANS_UNKNOWN      = (HIDP_ERROR_CODES(0xC,9))
    HIDP_STATUS_INCOMPATIBLE_REPORT_ID   = (HIDP_ERROR_CODES(0xC,0xA))
    HIDP_STATUS_NOT_VALUE_ARRAY          = (HIDP_ERROR_CODES(0xC,0xB))
    HIDP_STATUS_IS_VALUE_ARRAY           = (HIDP_ERROR_CODES(0xC,0xC))
    HIDP_STATUS_DATA_INDEX_NOT_FOUND     = (HIDP_ERROR_CODES(0xC,0xD))
    HIDP_STATUS_DATA_INDEX_OUT_OF_RANGE  = (HIDP_ERROR_CODES(0xC,0xE))
    HIDP_STATUS_BUTTON_NOT_PRESSED       = (HIDP_ERROR_CODES(0xC,0xF))
    HIDP_STATUS_REPORT_DOES_NOT_EXIST    = (HIDP_ERROR_CODES(0xC,0x10))
    HIDP_STATUS_NOT_IMPLEMENTED          = (HIDP_ERROR_CODES(0xC,0x20))

    errorMessageDict = {
        HIDP_STATUS_SUCCESS                  : "Success",
        HIDP_STATUS_NULL                     : "Null",
        HIDP_STATUS_INVALID_PREPARSED_DATA   : "Invalid preparsed data",
        HIDP_STATUS_INVALID_REPORT_TYPE      : "Invalid report type",
        HIDP_STATUS_INVALID_REPORT_LENGTH    : "Invalid report length",
        HIDP_STATUS_USAGE_NOT_FOUND          : "Usage not found",
        HIDP_STATUS_VALUE_OUT_OF_RANGE       : "Value out of range",
        HIDP_STATUS_BAD_LOG_PHY_VALUES       : "Bad log phy values",
        HIDP_STATUS_BUFFER_TOO_SMALL         : "Buffer too small",
        HIDP_STATUS_INTERNAL_ERROR           : "Internal error",
        HIDP_STATUS_I8042_TRANS_UNKNOWN      : "I8042/I8242 trans unknown",
        HIDP_STATUS_INCOMPATIBLE_REPORT_ID   : "Incompatible report ID",
        HIDP_STATUS_NOT_VALUE_ARRAY          : "Not value array",
        HIDP_STATUS_IS_VALUE_ARRAY           : "Is value array",
        HIDP_STATUS_DATA_INDEX_NOT_FOUND     : "Data index not found",
        HIDP_STATUS_DATA_INDEX_OUT_OF_RANGE  : "Data index out of range",
        HIDP_STATUS_BUTTON_NOT_PRESSED       : "Button not pressed",
        HIDP_STATUS_REPORT_DOES_NOT_EXIST    : "Report does not exist",
        HIDP_STATUS_NOT_IMPLEMENTED          : "Not implemented"
    }
        
    def __init__(self, errorCode):
        errorCode &= 0xFFFFFFFF
        self.errorCode = errorCode
        if errorCode != self.HIDP_STATUS_SUCCESS:
            if errorCode in self.errorMessageDict:
                raise HIDError("HidP error: %s" % self.errorMessageDict[errorCode])
            else:
                raise HIDError("Unknown HidP error (%s)"%hex(errorCode))

#*****************
# kernel32
#
#wait for single object
WAIT_ABANDONED = 0x00000080 # mutex used by another thread
WAIT_OBJECT_0  = 0x00000000 # signaled
WAIT_TIMEOUT   = 0x00000102 # object signal timed out
WAIT_FAILED    = 0xFFFFFFFF #failed
INFINITE       = 0xFFFFFFFF

GENERIC_READ    = (-2147483648)
GENERIC_WRITE   = (1073741824)
FILE_SHARE_READ = 1
FILE_SHARE_WRITE= 2
#
OPEN_EXISTING   = 3
OPEN_ALWAYS     = 4
#
FILE_FLAG_OVERLAPPED    = 1073741824
FILE_ATTRIBUTE_NORMAL   = 128
#
NO_ERROR = 0
ERROR_IO_PENDING = 997

def GetHidGuid():
    "Get system-defined GUID for HIDClass devices"
    g = GUID()
    hidDll.HidD_GetHidGuid(byref(g))
    return g

