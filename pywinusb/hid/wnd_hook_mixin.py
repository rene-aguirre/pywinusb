##########################################################################
##
##  This is a modification of the original WndProcHookMixin by Kevin Moore,
##  modified to use ctypes only instead of pywin32, so it can be used
##  with no additional dependencies in Python 2.5
##
##########################################################################

import ctypes
from ctypes import c_long, c_int


## It's probably not neccesary to make this distinction, but it never hurts to be safe
SetWindowLong = ctypes.windll.user32.SetWindowLongW
CallWindowProc = ctypes.windll.user32.CallWindowProcW
    
GWL_WNDPROC = -4
WM_DESTROY  = 2

## Create a type that will be used to cast a python callable to a c callback function
## first arg is return type, the rest are the arguments
WndProcType = ctypes.WINFUNCTYPE(c_int, c_long, c_int, c_int, c_int)

class WndProcHookMixin:
    """
    This class can be mixed in with any window class in order to hook it's WndProc function. 
    You supply a set of message handler functions with the function add_msg_handler. When the window receives that
    message, the specified handler function is invoked. If the handler explicitly returns False then the standard 
    WindowProc will not be invoked with the message. You can really screw things up this way, so be careful. 
    This is not the correct way to deal with standard windows messages in wxPython (i.e. button click, paint, etc) 
    use the standard wxWindows method of binding events for that. This is really for capturing custom windows messages
    or windows messages that are outside of the wxWindows world.
    """
    def __init__(self, wnd_handle):
        self.__msg_dict = {}
        ## We need to maintain a reference to the WndProcType wrapper
        ## because ctypes doesn't
        self.__local_wnd_proc_wrapped = None 
        # keep window handle
        self.__local_win_handle = wnd_handle
        
    def hook_wnd_proc(self):
        self.__local_wnd_proc_wrapped = WndProcType(self.local_wnd_proc)
        self.__old_wnd_proc = SetWindowLong(self.__local_win_handle,
                                        GWL_WNDPROC,
                                        self.__local_wnd_proc_wrapped)
    def unhook_wnd_proc(self):
        SetWindowLong(self.__local_win_handle,
                        GWL_WNDPROC,
                        self.__old_wnd_proc)
        
        ## Allow the ctypes wrapper to be garbage collected
        self.__local_wnd_proc_wrapped = None

    def add_msg_handler(self,message_number,handler):
        self.__msg_dict[message_number] = handler

    def local_wnd_proc(self, h_wnd, msg, w_param, l_param):
        # call the handler if one exists
        # performance note: has_key is the fastest way to check for a key
        # when the key is unlikely to be found
        # (which is the case here, since most messages will not have handlers).
        # This is called via a ctypes shim for every single windows message 
        # so dispatch speed is important
        if self.__msg_dict.has_key(msg):
            # if the handler returns false, we terminate the message here
            # Note that we don't pass the hwnd or the message along
            # Handlers should be really, really careful about returning false here
            if self.__msg_dict[msg](w_param,l_param) == False:
                return

        # Restore the old WndProc on Destroy.
        if msg == WM_DESTROY: self.unhook_wnd_proc()

        return CallWindowProc(self.__old_wnd_proc,
                                h_wnd, msg, w_param, l_param)
                                
# a simple example
if __name__ == "__main__":
    import wx
    class MyFrame(wx.Frame,WndProcHookMixin):
        def __init__(self,parent):
            frame_size = wx.Size(640,480)
            wx.Frame.__init__(self,parent,-1,"Change my size and watch stdout",size=frame_size)
            WndProcHookMixin.__init__(self, self.GetHandle())
            # this is for demo purposes only, use the wxPython method for getting events 
            # on window size changes and other standard windowing messages
            WM_SIZE = 5
            self.add_msg_handler(WM_SIZE, self.on_hooked_size)
            self.hook_wnd_proc()
        
        def on_hooked_size(self,w_param,l_param):
            print "WM_SIZE [WPARAM:%i][LPARAM:%i]"%(w_param,l_param)
            return True

    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show()
    app.MainLoop()
