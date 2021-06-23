import sys
if sys.platform.startswith("win"):
    import serial.win32
    import _winapi

hUniqueEvent = 0

def IsSingleAppInstance():
    global hUniqueEvent

    if not sys.platform.startswith("win"):
        return True

    if 0 != hUniqueEvent:
        return True
    hUniqueEvent = serial.win32.CreateEvent(None, True, False, "Global\\iCOMOX")
    return serial.win32.GetLastError() != _winapi.ERROR_ALREADY_EXISTS

def CloseSingleAppInstanceMarker():
    global hUniqueEvent

    if not sys.platform.startswith("win"):
        return
    if 0 != hUniqueEvent:
        serial.win32.CloseHandle(hUniqueEvent)