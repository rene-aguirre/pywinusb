##########################################################################
##
##  This is a modification of the original WndProcHookMixin by Kevin Moore,
##  modified to use ctypes only instead of pywin32, so it can be used
##  with no additional dependencies in Python 2.5
##
##########################################################################

import ctypes
from ctypes import c_long, c_int

import wx

## It's probably not neccesary to make this distinction, but it never hurts to be safe
if 'unicode' not in wx.PlatformInfo:
    SetWindowLong = ctypes.windll.user32.SetWindowLongW
    CallWindowProc = ctypes.windll.user32.CallWindowProcW
else:
    SetWindowLong = ctypes.windll.user32.SetWindowLongA
    CallWindowProc = ctypes.windll.user32.CallWindowProcA
    
GWL_WNDPROC = -4
WM_DESTROY  = 2

## Create a type that will be used to cast a python callable to a c callback function
## first arg is return type, the rest are the arguments
WndProcType = ctypes.WINFUNCTYPE(c_int, c_long, c_int, c_int, c_int)

class WndProcHookMixin:
    """
    This class can be mixed in with any wxWindows window class in order to hook it's WndProc function. 
    You supply a set of message handler functions with the function addMsgHandler. When the window receives that
    message, the specified handler function is invoked. If the handler explicitly returns False then the standard 
    WindowProc will not be invoked with the message. You can really screw things up this way, so be careful. 
    This is not the correct way to deal with standard windows messages in wxPython (i.e. button click, paint, etc) 
    use the standard wxWindows method of binding events for that. This is really for capturing custom windows messages
    or windows messages that are outside of the wxWindows world.
    """
    def __init__(self):
        self.__msgDict = {}
        ## We need to maintain a reference to the WndProcType wrapper
        ## because ctypes doesn't
        self.__localWndProcWrapped = None 
        
    def hookWndProc(self):
        self.__localWndProcWrapped = WndProcType(self.localWndProc)
        self.__oldWndProc = SetWindowLong(self.GetHandle(),
                                        GWL_WNDPROC,
                                        self.__localWndProcWrapped)
    def unhookWndProc(self):
        SetWindowLong(self.GetHandle(),
                        GWL_WNDPROC,
                        self.__oldWndProc)
        
        ## Allow the ctypes wrapper to be garbage collected
        self.__localWndProcWrapped = None

    def addMsgHandler(self,messageNumber,handler):
        self.__msgDict[messageNumber] = handler

    def localWndProc(self, hWnd, msg, wParam, lParam):
        # call the handler if one exists
        # performance note: has_key is the fastest way to check for a key
        # when the key is unlikely to be found
        # (which is the case here, since most messages will not have handlers).
        # This is called via a ctypes shim for every single windows message 
        # so dispatch speed is important
        if self.__msgDict.has_key(msg):
            # if the handler returns false, we terminate the message here
            # Note that we don't pass the hwnd or the message along
            # Handlers should be really, really careful about returning false here
            if self.__msgDict[msg](wParam,lParam) == False:
                return

        # Restore the old WndProc on Destroy.
        if msg == WM_DESTROY: self.unhookWndProc()

        return CallWindowProc(self.__oldWndProc,
                                hWnd, msg, wParam, lParam)
                                
# a simple example
if __name__ == "__main__":
    
    class MyFrame(wx.Frame,WndProcHookMixin):
        def __init__(self,parent):
            WndProcHookMixin.__init__(self)
            frameSize = wx.Size(640,480)
            wx.Frame.__init__(self,parent,-1,"Change my size and watch stdout",size=frameSize)
            # this is for demo purposes only, use the wxPython method for getting events 
            # on window size changes and other standard windowing messages
            WM_SIZE = 5
            self.addMsgHandler(WM_SIZE, self.onHookedSize)
            self.hookWndProc()
        
        def onHookedSize(self,wParam,lParam):
            print "WM_SIZE [WPARAM:%i][LPARAM:%i]"%(wParam,lParam)
            return True

    app = wx.App(False)
    frame = MyFrame(None)
    frame.Show()
    app.MainLoop()
