#helpers
import ctypes
from ctypes.wintypes import DWORD, WORD, BYTE
from WndProcHookMixin import WndProcHookMixin
from core import HIDError, GetHidGuid

#structures for ctypes
class GUID(ctypes.Structure):
    _fields_ = [("Data1", DWORD),
                ("Data2", WORD),
                ("Data3", WORD),
                ("Data4", BYTE * 8)]

#for PNP notifications
class DEV_BROADCAST_DEVICEINTERFACE(ctypes.Structure):
    _fields_ = [
        # size of the members plus the actual length of the dbcc_name string
        ("dbcc_size", DWORD), 
        ("dbcc_devicetype", DWORD),
        ("dbcc_reserved", DWORD),
        ("dbcc_classguid", GUID),
        ("dbcc_name", ctypes.c_wchar), #TCHAR
    ]

#***********************************
# PnP definitions
WM_DEVICECHANGE     = 0x0219
DBT_CONFIGCHANGED   = 0x0018 # pc docked or undocked
DBT_DEVICEARRIVAL   = 0x8000 #A device or piece of media has been inserted and is now available.
DBT_DEVICEREMOVECOMPLETE = 0x8004 #A device or piece of media has been removed.

RegisterDeviceNotification = ctypes.windll.user32.RegisterDeviceNotificationW
RegisterDeviceNotification.restype = ctypes.wintypes.HANDLE
RegisterDeviceNotification.argtypes = [
    ctypes.wintypes.HANDLE, 
    ctypes.c_void_p,
    DWORD
]

UnregisterDeviceNotification = ctypes.windll.user32.UnregisterDeviceNotification
RegisterDeviceNotification.restype = ctypes.wintypes.BOOL
UnregisterDeviceNotification.argtypes = [
    ctypes.wintypes.HANDLE,
]

#dbcc_devicetype, device interface only used
DBT_DEVTYP_DEVICEINTERFACE  = 0x00000005
DBT_DEVTYP_HANDLE           = 0x00000006

DEVICE_NOTIFY_WINDOW_HANDLE     = 0x00000000
DEVICE_NOTIFY_SERVICE_HANDLE    = 0x00000001

class UsbPnpWindowMixin(WndProcHookMixin):
    def __init__(self, hid_device_filter):
        WndProcHookMixin.__init__(self)
        self._h_notify = self.RegisterHidNotification()
        if self._h_notify:
            self.add_msg_handler(WM_DEVICECHANGE, self._OnHookedPnP)
            self.hook_wnd_proc()
        else:
            raise HIDError("PnP notification setup failed!")
        self.hid_filter = hid_device_filter
        self.current_status = "unknown"
            
    def unhook_wnd_proc(self):
        WndProcHookMixin.unhook_wnd_proc(self)
        if self._h_notify:
            self.UnRegisterHidNotification() #ignore result
            
    def _OnHookedPnP(self, w_param, l_param):
        "Process WM_DEVICECHANGE system messages"
        new_status = "unknown"
        if w_param == DBT_DEVICEARRIVAL:
            # hid device attached
            notify_obj = None
            if int(l_param) != 0:
                notify_obj = DEV_BROADCAST_DEVICEINTERFACE.from_address(l_param)
                #confirm if the right message received
                if notify_obj and notify_obj.dbcc_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    #only connect if already disconnected
                    if self.hid_filter.get_devices():
                        new_status = "connected"
        elif w_param == DBT_DEVICEREMOVECOMPLETE:
            # hid device removed
            notify_obj = None
            if int(l_param) != 0:
                notify_obj = DEV_BROADCAST_DEVICEINTERFACE.from_address(l_param)
                #
                if notify_obj and notify_obj.dbcc_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    #only connect if already disconnected
                    if not self.hid_filter.get_devices():
                        new_status = "disconnected"
                    
        #verify if need to call event handler
        if new_status != "unknown" and new_status != self.current_status:
            self.current_status = new_status
            self.OnUsbPnPEvent(self.current_status)
        #
        return True
        
    def RegisterHidNotification(self):
        """Register HID notification events on any window (passed by window handler),
        returns a notification handler"""
        
        #create structure
        notify_obj = DEV_BROADCAST_DEVICEINTERFACE()
        #fill up
        #ctypes.memset(ctypes.byref(notify_obj), 0, ctypes.sizeof(notify_obj))
        notify_obj.dbcc_size = ctypes.sizeof(notify_obj)
        notify_obj.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        notify_obj.dbcc_classguid = GetHidGuid()
        h_notify = RegisterDeviceNotification(self.GetHandle(), ctypes.byref(notify_obj), DEVICE_NOTIFY_WINDOW_HANDLE)
        #
        return int(h_notify)

    def UnRegisterHidNotification(self):
        "Remove PnP notification handler"
        if int(self._h_notify) == 0:
            return #invalid

        result = UnregisterDeviceNotification(self._h_notify)
        self._h_notify = None
        return int(result)
        
    def OnUsbPnPEvent(self):
        "'Virtual' function to refresh update for connection status"
        pass
