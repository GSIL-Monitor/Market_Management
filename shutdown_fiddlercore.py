import clr
import sys
import win32api
import win32con
from datetime import datetime
# from certificate import *

sys.path.append("C:\\Users\\叮咚\\Desktop\\FiddlerCoreAPI")
clr.FindAssembly("FiddlerCore4")
clr.AddReference("FiddlerCore4")
import Fiddler as FC

def onClose(sig):
    print(chr(7))
    FC.FiddlerApplication.Shutdown()
    win32api.MessageBox(win32con.NULL, 'See you later', 'Exit', win32con.MB_OK)

def fiddler(FC,flags):   
    # register event handler
    # object.SomeEvent += handler
    #
    # unregister event handler
    # object.SomeEvent -= handler
    #
    # passed a callable Python object to get a delegate instance.
    # FC.FiddlerApplication.Log.OnLogString += printLog
    # FC.FiddlerApplication.AfterSessionComplete += printSession
    
    # When decrypting HTTPS traffic,ignore the server certificate errors  
    FC.CONFIG.IgnoreServerCertErrors = False
     
    # start up capture
    FC.FiddlerApplication.Startup(7777, flags)

if __name__ == '__main__':
   
    win32api.SetConsoleCtrlHandler(onClose, 1)
    captureType = "http"
    
    #RegisterAsSystemProxy:1
    #OptimizeThreadPool:512
    #MonitorAllConnections:32
    #DecryptSSL:2
    #AllowRemoteClients:8
    
    # if captureType == "https":
    #     prepareCert(FC)      
    #     fiddler(FC, 1+512+32+2)
    # else:
        # fiddler(FC, 1+512+32)
        
    fiddler(FC, 1+512+32)  
    onClose(1)  
    try:
        # keep console window be open        
        raw_input()
    except:
        pass