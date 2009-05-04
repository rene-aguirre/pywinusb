#helpers
from ctypes.wintypes import ULONG, BOOLEAN, BYTE, WORD, DWORD, HANDLE
from WndProcHookMixin import WndProcHookMixin

#for PNP notifications
class DEV_BROADCAST_DEVICEINTERFACE(Structure):
    _fields_ = [
        # size of the members plus the actual length of the dbcc_name string
        ("dbcc_size", DWORD), 
        ("dbcc_devicetype", DWORD),
        ("dbcc_reserved", DWORD),
        ("dbcc_classguid", GUID),
        ("dbcc_name", c_wchar), #TCHAR
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
    def __init__(self, hidDeviceFilter):
        WndProcHookMixin.__init__(self)
        self._hNotify = self.RegisterHidNotification()
        if self._hNotify:
            self.addMsgHandler(WM_DEVICECHANGE, self._OnHookedPnP)
            self.hookWndProc()
        else:
            raise HIDError("PnP notification setup failed!")
        self.hidFilter = hidDeviceFilter
        self.currentStatus = "unknown"
            
    def unhookWndProc(self):
        WndProcHookMixin.unhookWndProc(self)
        if self._hNotify:
            self.UnRegisterHidNotification() #ignore result
            
    def _OnHookedPnP(self, wParam, lParam):
        "Process WM_DEVICECHANGE system messages"
        newStatus = "unknown"
        if wParam == DBT_DEVICEARRIVAL:
            # hid device attached
            notifyObj = None
            if int(lParam) != 0:
                notifyObj = DEV_BROADCAST_DEVICEINTERFACE.from_address(lParam)
                #confirm if the right message received
                if notifyObj and notifyObj.dbcc_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    #only connect if already disconnected
                    if self.hidFilter.getDevices():
                        newStatus = "connected"
        elif wParam == DBT_DEVICEREMOVECOMPLETE:
            # hid device removed
            notifyObj = None
            if int(lParam) != 0:
                notifyObj = DEV_BROADCAST_DEVICEINTERFACE.from_address(lParam)
                #
                if notifyObj and notifyObj.dbcc_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    #only connect if already disconnected
                    if not self.hidFilter.getDevices():
                        newStatus = "disconnected"
                    
        #verify if need to call event handler
        if newStatus != "unknown" and newStatus != self.currentStatus:
            self.currentStatus = newStatus
            self.OnUsbPnPEvent(self.currentStatus)
        #
        return True
        
    def RegisterHidNotification(self):
        """Register HID notification events on any window (passed by window handler),
        returns a notification handler"""
        
        #create structure
        notifyObj = DEV_BROADCAST_DEVICEINTERFACE()
        #fill up
        #ctypes.memset(byref(notifyObj), 0, sizeof(notifyObj))
        notifyObj.dbcc_size = sizeof(notifyObj)
        notifyObj.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        notifyObj.dbcc_classguid = GetHidGuid()
        hNotify = RegisterDeviceNotification(self.GetHandle(), byref(notifyObj), DEVICE_NOTIFY_WINDOW_HANDLE)
        #
        return int(hNotify)

    def UnRegisterHidNotification(self):
        "Remove PnP notification handler"
        if int(self._hNotify) == 0:
            return #invalid

        result = UnregisterDeviceNotification(self._hNotify)
        self._hNotify = None
        return int(result)
        
    def OnUsbPnPEvent(self):
        "'Virtual' function to refresh update for connection status"
        pass
