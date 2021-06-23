import messages_utils
import iCOMOX_messages
import struct
import datetime
import Dongle_Communication

cCLIENT_TYPE_USB    = 0
cCLIENT_TYPE_SMIP   = 1
cCLIENT_TYPE_TCPIP  = 2

cCLIENT_TYPE_BITMASK_USB    = 1 << cCLIENT_TYPE_USB
cCLIENT_TYPE_BITMASK_SMIP   = 1 << cCLIENT_TYPE_SMIP
cCLIENT_TYPE_BITMASK_TCPIP  = 1 << cCLIENT_TYPE_TCPIP

cCLIENT_TYPE_BITMASK_ALL = cCLIENT_TYPE_BITMASK_USB | cCLIENT_TYPE_BITMASK_SMIP | cCLIENT_TYPE_BITMASK_TCPIP

def list_to_first_element(list):
    if len(list) == 0:
        return None
    else:
        return list[0]

class sCOMOX():
    def __init__(self, Type):
        self.Type = Type    # Type of connection (cCLIENT_TYPE_xxx). It is not the type of the iCOMOX!!

        self.Hello = None
        self.Reports = [None] * 256
        # self.Configuration = bytearray()
        self.ConnectionTime = None  # datetime.datetime.now()
        # self.HelloReceivedTime = None

    def same_iCOMOX(self, iComox):
        if iComox.Type != self.Type:
            return False
        if (self.Hello is not None) and (iComox.Hello is not None):
            return self.UniqueID() == iComox.UniqueID()
        return None # Can't determine

    def copy_from(self, iComox):
        if (iComox is None) or (iComox.Type != self.Type):
            raise Exception("sCOMOX.copy_from(): Invalid iComox type")
        # self.Hello = iComox.Hello
        # self.Reports = iComox.Reports
        # self.ConnectionTime = iComox.ConnectionTime

    def clear(self):  # it does not clean the UniqueID field
        self.Type = None
        self.Hello = None
        self.Reports = [None] * 256
        self.ConnectionTime = None

    def UniqueID(self):
        if self.Hello is not None:
            return self.Hello[4:20]
        else:
            return None

    def board_type(self):
        if self.Hello is not None:
            return self.Hello[1]
        else:
            return None

    def Name(self):
        if self.Hello is not None:
            return self.Hello[96:128]
        else:
            return None


class sCOMOX_USB(sCOMOX):
    def __init__(self, CommPort):
        sCOMOX.__init__(self, Type=cCLIENT_TYPE_USB)
        self.CommPort = CommPort
        # self.HelloReceivedTime = datetime.datetime.now()

    def clear(self):
        sCOMOX.clear(self)
        self.CommPort = None

    def same_iCOMOX(self, iComox):
        same = sCOMOX.same_iCOMOX(self, iComox=iComox)
        if same is None:
            return self.CommPort == iComox.CommPort
        else:
            return same


class sCOMOX_SMIP(sCOMOX):
    def __init__(self, macAddress, moteID, state, isRouting):
        sCOMOX.__init__(self, Type=cCLIENT_TYPE_SMIP)
        self.macAddress = macAddress
        self.moteID = moteID
        self.state = state  # Dongle_Communication.MOTE_STATE_LOST
        self.isRouting = isRouting
        self.packetID = 0
        self.expected_msg_size = 0
        self.accumulated_msg = bytearray()
        self.HelloRequestTime = None

    def clear(self):
        sCOMOX.clear(self)
        self.macAddress = None
        self.moteID = None

    def same_iCOMOX(self, iComox):
        same = sCOMOX.same_iCOMOX(self, iComox=iComox)
        if same is None:
            return self.macAddress == iComox.macAddress
        else:
            return same

    def copy_from(self, iComox):
        sCOMOX.copy_from(self, iComox=iComox)
        self.moteID = iComox.moteID
        self.state = iComox.state
        self.isRouting = iComox.isRouting


class sCOMOX_TCPIP(sCOMOX):
    def __init__(self, remoteAddress, remotePort, socket):
        sCOMOX.__init__(self, Type=cCLIENT_TYPE_TCPIP)
        self.socket = socket
        self.remoteAddress = remoteAddress
        self.remotePort = remotePort
        self.transmit_buffer = bytearray()
        self.receive_buffer = bytearray()
        self.accumulated_msg = bytearray()

    def clear(self):
        sCOMOX.clear(self)
        self.socket = None
        self.remoteAddress = None
        self.remotePort = None
        self.transmit_buffer = None
        self.receive_buffer = None
        self.accumulated_msg = None

    def copy_from(self, iComox):
        sCOMOX.copy_from(self, iComox=iComox)
        self.socket = iComox.socket
        self.remoteAddress = iComox.remoteAddress
        self.remotePort = iComox.remotePort
        self.transmit_buffer = None
        self.receive_buffer = None
        self.accumulated_msg = None

class sCOMOXs_list():
    def __init__(self):
        self.list = []
        self.current = None

    def add(self, Type, CommPort=None, macAddress=None, moteID=None, state=None, isRouting=None, remoteAddress=None, remotePort=None, socket=None):
        if Type == cCLIENT_TYPE_USB:
            if CommPort is None:
                raise Exception("sCOMOXs_list.add(): Invalid CommPort")
            iComox = sCOMOX_USB(CommPort=CommPort)

        elif Type == cCLIENT_TYPE_SMIP:
            if macAddress is None:
                raise Exception("sCOMOXs_list.add(): Invalid macAddress")
            if moteID is None:
                raise Exception("sCOMOXs_list.add(): Invalid moteID")
            if state is None:
                raise Exception("sCOMOX_list.add(): Invalid state")
            if isRouting is None:
                raise Exception("sCOMOX_list.add(): Invalid isRouting")
            iComox = sCOMOX_SMIP(macAddress=macAddress, moteID=moteID, state=state, isRouting=isRouting)

        elif Type == cCLIENT_TYPE_TCPIP:
            if remoteAddress is None:
                raise Exception("sCOMOXs_list.add(): Invalid remoteAddress")
            if remotePort is None:
                raise Exception("sCOMOXs_list.add(): Invalid remotePort")
            if socket is None:
                raise Exception("sCOMOXs_list.add(): Invalid socket")
            iComox = sCOMOX_TCPIP(remoteAddress=remoteAddress, remotePort=remotePort, socket=socket)

        else:
            raise Exception("sCOMOXs_list.add(): Invalid Type")
        iComox.Type = Type

        ExistingComox = self.exists(iComox=iComox)
        if ExistingComox is not None:
            ExistingComox.copy_from(iComox=iComox)
            iComox.clear()
            del iComox
            return ExistingComox
        else:
            self.list.append(iComox)
            return iComox

    def exists(self, iComox):
        return list_to_first_element(list=[*filter(lambda Cmx : Cmx.same_iCOMOX(iComox=iComox), self.list)])

    def clear(self):
        for iComox in self.list:
            iComox.clear()
        self.list.clear()
        self.current = None

    def all_iComox_of_type(self, Type):
        return [*filter(lambda iCmx : iCmx.Type == Type, self.list)]

    def delete_all_of_type(self, Type):
        list_of_index_to_remove = [*filter(lambda i : self.list[i].Type == Type, range(0, len(self.list)))]
        for i in range(len(list_of_index_to_remove)-1, -1, -1):
            iCmxIndex = list_of_index_to_remove[i]
            self.list[iCmxIndex].clear()
            del self.list[iCmxIndex]

    def is_current_iCOMOX(self, iComox):
        return self.current == iComox

    # def get_all_iCOMOXs_by_type(self, Type):
    #     return [*filter(lambda iComox: iComox.Type == Type, self.list)]

    def find_by_macAddress(self, macAddress):
        return list_to_first_element(list=[*filter(lambda iComox : (iComox.Type == cCLIENT_TYPE_SMIP) and (iComox.macAddress == macAddress), self.list)])

    def find_index_by_macAddress(self, macAddress):
        for i in range(0, len(self.list)):
            iComox = self.list[i]
            if (iComox.Type == cCLIENT_TYPE_SMIP) and (iComox.macAddress == macAddress):
                return i
        return -1

    def find_by_CommPort(self, CommPort):
        return list_to_first_element(list=[*filter(lambda iComox : (iComox.Type == cCLIENT_TYPE_USB) and (iComox.CommPort == CommPort), self.list)])

    def find_index_by_CommPort(self, CommPort):
        for i in range(0, len(self.list)):
            iComox = self.list[i]
            if (iComox.Type == cCLIENT_TYPE_USB) and (iComox.CommPort == CommPort):
                return i
        return -1

    def find_by_UniuqeID(self, UniqueID, TypesBitmask=cCLIENT_TYPE_BITMASK_ALL):
        return list_to_first_element(list=[*filter(lambda iComox : ((iComox.Type & TypesBitmask) != 0) and (iComox.UniqueID() == UniqueID), self.list)])

    def find_index_by_uniqueID(self, UniqueID, TypesBitmask=cCLIENT_TYPE_BITMASK_ALL):
        for i in range(0, len(self.list)):
            iComox = self.list[i]
            if ((iComox.Type & TypesBitmask) != 0) and (iComox.UniqueID() == UniqueID):
                return i
        return -1

    def find_by_socket(self, socket):
        return list_to_first_element(list=[*filter(lambda iComox : (iComox.Type == cCLIENT_TYPE_TCPIP) and (iComox.socket == socket), self.list)])

    def find_index_by_socket(self, socket):
        for index in range(0, len(self.list)):
            iComox = self.list[index]
            if (iComox.Type == cCLIENT_TYPE_TCPIP) and (iComox.socket == socket):
                return index
        return None
