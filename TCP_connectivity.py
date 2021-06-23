import iCOMOX_list
import socket
import threading
import ifaddr
import messages_utils
import common
# import BG96_Encoder
import time
import select
import errno
import sys
import iCOMOX_messages

cTCP_STATE_DISCONNECTED             = 0
cTCP_STATE_LISTEN                   = 1
cTCP_STATE_CLIENT_DISCONNECTED      = 2
cTCP_STATE_CLIENT_CONNECTED         = 3
cTCP_STATE_iCOMOX_CONNECTED         = 4
cTCP_STATE_ZOMBIE_CLIENT_DETECTED   = 5

def GetIpAddresses():
    result = []
    adapters = ifaddr.get_adapters()
    for adapter in adapters:
        # print("IPs of network adapter " + adapter.nice_name)
        for ip in adapter.ips:
            if type(ip.ip) is tuple:
                pass    #result += [ip.ip[0]]   # Collect only IPv4
            else:
                result += [ip.ip]
    return result

class class_iCOMOX_TcpServer:
    def __init__(self, callback_process_message, callback_state_changed):
        self.server = None
        self.Terminated = False
        self.OnProcessMessages = callback_process_message
        self.OnStateChanged = callback_state_changed

    def get_all_iComox_connected_as_TcpIp_clients(self):
        return [*filter(lambda iComox : iComox.socket.fileno() > 0, [*filter(lambda iComox : iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP, common.iCOMOXs.list)])]

    def send_to_all_clients(self, msg, UniqueID=None):
        iComox_clients = self.get_all_iComox_connected_as_TcpIp_clients()
        if UniqueID is not None:
            iComox_clients = [*filter(lambda iComox : iComox.UniqueID() == UniqueID, iComox_clients)]
        for iComox in iComox_clients:
            iComox.transmit_buffer += msg

    def is_listening(self):
        return self.server is not None

    def is_open(self):
        return self.is_listening() and (len(self.get_all_iComox_connected_as_TcpIp_clients()) > 0)

    def state_changed(self, tcpState, iComox = None):
        if callable(self.OnStateChanged):
            self.OnStateChanged(tcpState=tcpState, iComox=iComox)

    def close_client(self, iComox):
        if (iComox is None) or (iComox.Type != iCOMOX_list.cCLIENT_TYPE_TCPIP) or (iComox.socket is None):
            return

        iComox_clients = [*filter(lambda iCmx : (iCmx.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP) and (iCmx.UniqueID() is not None), common.iCOMOXs.list)]
        listed_in_iComox_clients = iComox in iComox_clients
        try:
            if listed_in_iComox_clients:
                self.state_changed(tcpState=cTCP_STATE_CLIENT_DISCONNECTED, iComox=iComox)
            iComox.socket.close()
            if common.iCOMOXs.current == iComox:
                common.iCOMOXs.current = None
            common.iCOMOXs.list.remove(iComox)
            del iComox
            if listed_in_iComox_clients and (len(iComox_clients) == 0):
                self.state_changed(tcpState=cTCP_STATE_LISTEN, iComox=None)
        except Exception as ex:
            pass
        finally:
            pass

    # def get_all_clients_sockets(self):
    #     return [*map(lambda iComox: iComox.socket, [*filter(lambda iComox: (iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP) and (iComox.socket is not None), common.iCOMOXs.list)])]

    def __non_blocking_server_thread__(self, host, port):
        if not callable(self.OnProcessMessages):
            raise Exception("class_iCOMOX_TcpServer.__non_blocking_server_thread__.OnProcessMessages is not callable")
        iComox = None
        try:
            #self.OnStateChanged(tcpState=cTCP_STATE_DISCONNECTED)
            if self.server is not None:
                self.server.close()
            self.close_all_clients()
            self.server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((host, port))
            self.server.listen()
            self.server.setblocking(False)
            self.Terminated = False
            self.state_changed(tcpState=cTCP_STATE_LISTEN, iComox=None)

            while not self.Terminated:
                # time.sleep(0.001)
                if self.server is None:
                    self.state_changed(tcpState=cTCP_STATE_DISCONNECTED, iComox=None)
                    return
                try:
                    socks_list = [*map(lambda iComox: iComox.socket, self.get_all_iComox_connected_as_TcpIp_clients())]
                    if not socks_list:
                        socks_list = [self.server]
                    else:
                        socks_list = [self.server, *socks_list]
                    # socks_list = [self.server, *filter(lambda iComox : iComox.socket, [*filter(lambda iComox : (iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP) and (iComox.socket is not None), common.iCOMOXs.list)])]
                    # socks_list = [self.server, *[cli.socket for cli in self.clients]]
                    readable, writeable, errored = select.select(socks_list, socks_list, socks_list, 0)
                    for sock in errored:
                        iComox = common.iCOMOXs.find_by_socket(socket=sock)
                        if iComox is None:
                            continue
                        if sock in readable:
                            readable.remove(sock)
                        if sock in writeable:
                            writeable.remove(sock)
                        self.close_client(iComox=iComox)

                    for sock in writeable:
                        iComox = common.iCOMOXs.find_by_socket(socket=sock)
                        if iComox is None:
                            continue
                        if len(iComox.transmit_buffer) > 0:
                            bytes_sent = iComox.socket.send(iComox.transmit_buffer)
                            if bytes_sent != 0:
                                iComox.transmit_buffer = iComox.transmit_buffer[bytes_sent:]
                            else:
                                if sock in readable:
                                    readable.remove(sock)
                                self.close_client(iComox=iComox)

                    for sock in readable:
                        if sock is self.server:  # New iComox socket tries to connect. Here the accept does not block
                            new_client_socket, [remoteAddress, remotePort] = self.server.accept()
                            self.setTcpKeepalive(sock=new_client_socket, enable=True, keepaliveIntervalSec=10, keepaliveProbeCount=2) #keepaliveIntervalSec=10
                            new_iComox = common.iCOMOXs.add(Type=iCOMOX_list.cCLIENT_TYPE_TCPIP, remoteAddress=remoteAddress, remotePort=remotePort, socket=new_client_socket)
                            self.state_changed(tcpState=cTCP_STATE_CLIENT_CONNECTED, iComox=new_iComox)
                        else:   # iComox sent data
                            iComox = common.iCOMOXs.find_by_socket(socket=sock)
                            if iComox is None:
                                continue
                            adxl356_smip = (iComox.Hello is None) or (iComox.board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_SMIP)
                            bytes_read = sock.recv(16384)
                            if bytes_read:
                                iComox.receive_buffer += bytes_read
                                while len(iComox.receive_buffer) >= 0:
                                    bytes_to_read = messages_utils.on_get_in_message_size(accumulated_msg=iComox.accumulated_msg, adxl356_smip=adxl356_smip)
                                    if bytes_to_read == 0:
                                        self.OnProcessMessages(msg=iComox.accumulated_msg, iComox=iComox)
                                        iComox.accumulated_msg = bytearray()

                                    elif bytes_to_read < 0: # if illegal message then close the socket
                                        self.close_client(iComox=iComox)
                                        break

                                    else:   # bytes_to_read > 0
                                        if len(iComox.receive_buffer) == 0: # if currently can't read more bytes then break
                                            break
                                        bytes_read = iComox.receive_buffer[:bytes_to_read]
                                        iComox.receive_buffer = iComox.receive_buffer[len(bytes_read):]
                                        bytes_to_read -= len(bytes_read)
                                        iComox.accumulated_msg += bytes_read
                            else:
                                self.close_client(iComox=iComox)    # Detection of FIN signal
                except socket.error as e:
                    err = e.args[0]
                    if (err != errno.EAGAIN) and (err != errno.EWOULDBLOCK):
                        self.close_client(iComox=iComox)
                finally:
                    pass

        except socket.error as e:
            # err = e.args[0]
            # if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            #     continue
            print(str(e))
            self.close_all_clients()
            self.server.close()
            self.server = None
        finally:
            self.Terminated = True
            self.state_changed(tcpState=cTCP_STATE_DISCONNECTED, iComox=None)

    def close_all_clients(self):
        iComoxs = [*filter(lambda iComox : (iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP) and (iComox.socket is not None), common.iCOMOXs.list)]
        for iComox in iComoxs:
            self.close_client(iComox=iComox)

    def start(self, host, port):
        if self.server is not None:
            self.server.close()
        self.Terminated = False
        new_server_thread = threading.Thread(target=self.__non_blocking_server_thread__, args=(host, port,))
        new_server_thread.daemon = True # Exit the server thread when the main thread terminates
        new_server_thread.start()

    def shutdown(self):
        if self.server is not None:
            self.Terminated = True
            self.server.close()
            self.server = None
            for iComox in self.get_all_iComox_connected_as_TcpIp_clients():
                self.close_client(iComox=iComox)
            self.state_changed(tcpState=cTCP_STATE_DISCONNECTED, iComox=None)

    def close(self):
        self.shutdown()

    def setTcpKeepalive(self, sock, enable, keepaliveIntervalSec, keepaliveProbeCount):
        # keepalive idle is the time until the first transmission of the keepalive packet
        # Keepalive time is the duration between two keepalive transmissions in idle condition.
        # Keepalive interval is the duration between two successive keepalive retransmissions, if acknowledgement to the previous keepalive transmission is not received.
        # Keepalive retry is the number of retransmissions to be carried out before declaring that remote end is not available
        if enable:
            enable = 1
        else:
            enable = 0

        if sys.platform.startswith("win"):  # Windows
            TCP_KEEPCNT = 16
            # keepalive enable, keepalive idle in miliseconds, keepalive interval in miliseconds
            sock.ioctl(socket.SIO_KEEPALIVE_VALS, (enable, int(keepaliveIntervalSec * 1000), int(keepaliveIntervalSec * 1000)))
            sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPCNT, keepaliveProbeCount)

        elif sys.platform.startswith("darwin"): # macOS
            sock.setsockopt(socket.SOL_SOCKET,  socket.SO_KEEPALIVE, enable)                  # on
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, keepaliveIntervalSec)   # interval in seconds

        elif sys.platform.startswith("linux"):  # Linux
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, enable)                   # on
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, keepaliveIntervalSec)        # interval in seconds
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, keepaliveIntervalSec)       # interval in seconds
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, keepaliveProbeCount)
        else:
            raise Exception("Please add the set")
