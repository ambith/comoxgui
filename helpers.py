import struct
import datetime
import tkinter
import tkinter.ttk
import tkinter.font
import os
import sys
import ipaddress
if sys.platform.startswith("win"):
    import win32con
    import win32gui
    import win32api


def centralize_window(root):
    root.update_idletasks()
    if sys.platform.startswith("win"):
        captionHeight = win32api.GetSystemMetrics(win32con.SM_CYCAPTION) + 2*win32api.GetSystemMetrics(win32con.SM_CYFIXEDFRAME)
        windowWidth = root.winfo_reqwidth()
        windowHeight = root.winfo_reqheight() + captionHeight
        # rect = win32gui.SystemParametersInfo(win32con.SPI_GETWORKAREA, 0, 0)   # not supported yet
        monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0,0)))
        screenWidth = monitor_info.get("Work")[2]
        screenHeight = monitor_info.get("Work")[3]
    else:
        # Gets the requested values of the height and width
        windowWidth = root.winfo_reqwidth()
        windowHeight = root.winfo_reqheight()
        screenWidth = root.winfo_screenwidth()
        screenHeight = root.winfo_screenheight()
    positionRight = int((screenWidth - windowWidth)/2)
    positionDown = int((screenHeight - windowHeight)/2)
    # Positions the window in the center of the page
    root.geometry("+{}+{}".format(positionRight, positionDown))


def u16s_to_str(arr, seperator, prefix=""):
    s = ""
    if len(arr) > 0:
        if 1 == (len(arr) % 2):
            arr += b"\x00"
        u16s = struct.unpack("<{:d}H".format(len(arr) / 2))
        for i in range(0, (len(arr) / 2) - 2):
            s += prefix + "{:04X}".format(u16s[i]) + seperator
        s += prefix + "{:04X}".format(u16s[-1])  # add the last element of u16s
    return s


def u8s_to_str(arr, separator, prefix=""):
    s = ""
    if len(arr) > 0:
        for i in range(0, len(arr) - 1):
            s += prefix + "{:02X}".format(arr[i]) + separator
        s += prefix + "{:02X}".format(arr[-1])  # add the last element of arr
    return s


def string_without(str, chars_to_remove):
    return str.translate({ord(c): None for c in chars_to_remove})


def bytearrayToString(bytes):
    index = bytes.find(b"\xFF")
    if index >= 0:
        bytes = bytes[:index]

    index = bytes.find(b"\x00")
    if index >= 0:
        bytes = bytes[:index]

    try:
        result = str(bytes, "utf8")
    except:
        result = ""
    finally:
        pass
    return result


def stringToIpAddress(ipaddress_str):
    try:
        ipaddress_obj = ipaddress.ip_address(ipaddress_str)
    except:
        ipaddress_obj = None
    finally:
        pass
    return ipaddress_obj


def OUT(outStr):
    s = str(datetime.datetime.now()) + " " + outStr
    print(s)


def resource_path(relative_path):
    try:
        # base_path = sys._MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def cb_adjust_dropbox_width(combo):
    if 0 == len(combo.cget('values')):
        return
    style = tkinter.ttk.Style()
    long = max(combo.cget('values'), key=len)
    font = tkinter.font.nametofont(str(combo.cget('font')))
    width = max(0, font.measure(long.strip() + '0'))# - combo.winfo_width())
    #combo.configure("TCombobox", listboxwidth=width)   # property is not recognized
    style.configure('TCombobox', postoffset=(0, 0, width, 0))   # it has no effect
    if sys.platform.startswith("win"):
        handle = combo.winfo_id()
        if handle != 0:
            new_width = win32gui.SendMessage(handle, win32con.CB_SETDROPPEDWIDTH, width*4, 0)
            # if win32con.CB_ERR != new_width:
            #     OUT("ComboBox width has been changed to {}".format(new_width))
