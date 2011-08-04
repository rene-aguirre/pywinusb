#helpers
import ctypes
from ctypes.wintypes import DWORD, WORD, BYTE
from wnd_hook_mixin import WndProcHookMixin
from core import HIDError, GetHidGuid
from winapi import GUID

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

class HidPnPWindowMixin(WndProcHookMixin):
    def __init__(self, wnd_handle):
        WndProcHookMixin.__init__(self, wnd_handle)
        self.__hid_hwnd = wnd_handle
        self.current_status = "unknown"
        #register hid notification msg handler
        self.__h_notify = self._register_hid_notification()
        if not self.__h_notify:
            raise HIDError("PnP notification setup failed!")
        else:
            self.add_msg_handler(WM_DEVICECHANGE, self._on_hid_pnp)
            # add capability to filter out windows messages
            self.hook_wnd_proc()
    
    def unhook_wnd_proc(self):
        "This function must be called to clean up system resources"
        WndProcHookMixin.unhook_wnd_proc(self)
        if self.__h_notify:
            self._unregister_hid_notification() #ignore result

    def _on_hid_pnp(self, w_param, l_param):
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
                    new_status = "connected"
        elif w_param == DBT_DEVICEREMOVECOMPLETE:
            # hid device removed
            notify_obj = None
            if int(l_param) != 0:
                notify_obj = DEV_BROADCAST_DEVICEINTERFACE.from_address(l_param)
                #
                if notify_obj and notify_obj.dbcc_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    #only connect if already disconnected
                    new_status = "disconnected"
                    
        #verify if need to call event handler
        if new_status != "unknown" and new_status != self.current_status:
            self.current_status = new_status
            self.on_hid_pnp(self.current_status)
        #
        return True
        
    def _register_hid_notification(self):
        """Register HID notification events on any window (passed by window handler),
        returns a notification handler"""
        #create structure
        notify_obj = DEV_BROADCAST_DEVICEINTERFACE()
        #fill up
        #ctypes.memset(ctypes.byref(notify_obj), 0, ctypes.sizeof(notify_obj))
        notify_obj.dbcc_size = ctypes.sizeof(notify_obj)
        notify_obj.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        notify_obj.dbcc_classguid = GetHidGuid()
        h_notify = RegisterDeviceNotification(self.__hid_hwnd, ctypes.byref(notify_obj), DEVICE_NOTIFY_WINDOW_HANDLE)
        #
        return int(h_notify)

    def _unregister_hid_notification(self):
        "Remove PnP notification handler"
        if int(self.__h_notify) == 0:
            return #invalid
        result = UnregisterDeviceNotification(self.__h_notify)
        self.__h_notify = None
        return int(result)
        
    def on_hid_pnp(self, new_status):
        "'Virtual' like function to refresh update for connection status"
        print "HID:", new_status

