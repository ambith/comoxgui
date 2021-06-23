import Dongle_Communication
import iCOMOX_messages
import messages_utils
import struct
import helpers
import common
import math
import iCOMOX_list

# once there is a session with the manager, we start the following chain:
# getSystemInfo - to get the manager's macAddress as hardware and software versions
# subscribe - to register to get events and data notifications
#
class class_iCOMOX_over_Dongle_Communication(Dongle_Communication.class_Dongle_Communication):
    def __init__(self, comm_port, callback_iCOMOX_added=None, callback_iCOMOX_removed=None, callback_updated_iCOMOX_SMIP_list=None, callback_process_message=None, callback_data_sent=None, callback_connection_state=None):# callback_serial_com_open=None, callback_serial_com_close=None)
        Dongle_Communication.class_Dongle_Communication.__init__(
            self=self,
            comm_port=comm_port,
            callback_command_resp=self.on_command_response,
            callback_notif_event=self.on_notif_event,               # notification.events
            callback_notif_log=None,                                # notification.logs
            callback_notif_data=self.on_notif_data,                 # notifications.data - here data from mote should be processed
            callback_notif_ipData=None,                             # notification.ipData - here data from mote using ipv6 should be processed
            callback_notif_healthReport=None,                       # notification.health RawDataSensors
            callback_MgrHello=self.on_manager_session_stop,         # when manager disconnects from us and waiting for ClientHello message (is_active_session -> False)
            callback_HelloResponse=self.on_manager_session_start,   # when manager connects us and waiting for further messages from us (is_active_session -> True)
            callback_serial_comm_open=self.on_serial_comm_open,     # serial COM port is now open
            callback_serial_comm_close=self.on_serial_comm_close    # serial COM port is now closed
        )
        # self.current_iCOMOX_list = []
        # self.temp_iCOMOX_list = []
        self.manager_macAddress = bytearray(8)
        self.sendData_callbackId = 0
        self.callback_updated_iCOMOX_SMIP_list = callback_updated_iCOMOX_SMIP_list
        self.callback_iCOMOX_added = callback_iCOMOX_added
        self.callback_iCOMOX_removed = callback_iCOMOX_removed
        self.callback_process_message = callback_process_message
        self.callback_data_sent = callback_data_sent
        self.callback_connection_state = callback_connection_state

    def send_message_to_iCOMOX(self, macAddress, msg, priority=1, srcPort=0xF0B8, dstPort=0xF0B8):
        return self.send_sendData(macAddress=macAddress, priority=priority, srcPort=srcPort, dstPort=dstPort, data=msg)

    def on_command_response(self, comm, packetType, RC, data):
        if packetType == 0x15:          # reset
            helpers.OUT("Reset ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x16:        # subscribe
            helpers.OUT("subscribe ACK, RC={}".format(hex(RC)))
            self.refresh_current_iCOMOX_list()

        elif packetType == 0x17:        # getTime
            pass
        elif packetType == 0x1A:        # setNetworkConfig
            helpers.OUT("getNetworkConfig ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x1F:        # clearStatistics
            helpers.OUT("clearStatistics ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x21:        # exchangeMoteJoinKey
            pass
        elif packetType == 0x22:        # exchangeNetworkId
            pass
        elif packetType == 0x23:        # radiotestTx
            pass
        elif packetType == 0x25:        # radiotestRx
            pass
        elif packetType == 0x26:        # getRadiotestStatistics
            pass
        elif packetType == 0x27:        # setACLEntry
            pass
        elif packetType == 0x28:        # getNextACLEntry
            pass
        elif packetType == 0x29:        # deleteACLEntry
            pass
        elif packetType == 0x2A:        # pingMote
            helpers.OUT("pingMote ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x2B:        # getLog
            pass
        elif packetType == 0x2C:        # sendData
            if RC == Dongle_Communication.RC_OK:
                [self.sendData_callbackId] = struct.unpack(">L", data)
            else:
                self.sendData_callbackId = 0
            helpers.OUT("sendData ACK, RC={}, callback ID={}".format(hex(RC), hex(self.sendData_callbackId)))

        elif packetType == 0x2D:        # startNetwork (deprecated)
            pass
        elif packetType == 0x2E:        # getSystemInfo
            helpers.OUT("getSystemInfo ACK, RC={}".format(hex(RC)))
            self.manager_macAddress = data[:8]
            hwModel, hwRev, swMajor, swMinor, swPatch, swBuild = struct.unpack_from(">BBBBBH", data, 8)
            common.app.Information.update_dongle_version(hwModel=hwModel, hwRev=hwRev, swMajor=swMajor, swMinor=swMinor, swPatch=swPatch, swBuild=swBuild, dongle_version_available=True)

            self.send_subscribe(filter=0x12, unackFilter=0xFFFFFFFF)    # subscribe to events (0x02) and data (0x10)

        elif packetType == 0x2F:        # getMoteConfig
            if RC == Dongle_Communication.RC_OK:
                macAddress = data[:8]
                moteID, isAP, state, reserved, isRouting = struct.unpack_from(">HBBBB", data, 8)
                if not isAP:
                    iCOMOX = common.iCOMOXs.add(Type=iCOMOX_list.cCLIENT_TYPE_SMIP, macAddress=macAddress, moteID=moteID, state=state, isRouting=isRouting)
                    if iCOMOX is not None:
                        iCOMOX.state = state
                        iCOMOX.isRouting = isRouting
                        # helpers.OUT("getMoteConfig: failed to add iCOMOX with MAC {}".format(helpers.u8s_to_str(macAddress, ":", "")))
                    self.send_getMoteConfig(macAddress=iCOMOX.macAddress, next=True)
                else:
                    helpers.OUT("Not sending the next getMoteConfig request since we got Access Point mote")

            elif RC == Dongle_Communication.RC_END_OF_LIST:
                # # Copy current_iCOMOX_list[] into temp_iCOMOX_list[]
                # for i in range(0, len(self.temp_iCOMOX_list)):
                #     index = self.index_by_macAddress(macAddress=self.temp_iCOMOX_list[i].macAddress)
                #     if index >= 0:
                #         self.temp_iCOMOX_list[i].packetID = self.current_iCOMOX_list[index].packetID
                #         self.temp_iCOMOX_list[i].received_msg = self.current_iCOMOX_list[index].received_msg
                #         self.temp_iCOMOX_list[i].Reports = self.current_iCOMOX_list[index].Reports
                #         self.temp_iCOMOX_list[i].Hello = self.current_iCOMOX_list[index].Hello
                #         self.temp_iCOMOX_list[i].Name = self.current_iCOMOX_list[index].Name
                #         self.temp_iCOMOX_list[i].UniqueID = self.current_iCOMOX_list[index].UniqueID
                #         self.temp_iCOMOX_list[i].board_type = self.current_iCOMOX_list[index].board_type
                #         # in this copy, state, moteID & isRouting might change due to new information in temp_iCOMOX_list[i]
                #
                # # Exchange between the current_iCOMOX_list & temp_iCOMOX_list without copying anything
                # self.current_iCOMOX_list, self.temp_iCOMOX_list = self.temp_iCOMOX_list, self.current_iCOMOX_list
                # self.temp_iCOMOX_list.clear()

                if callable(self.callback_updated_iCOMOX_SMIP_list):
                    self.callback_updated_iCOMOX_SMIP_list()
                else:
                    helpers.OUT("NO call to callback_updated_iCOMOX_SMIP_list()")
                helpers.OUT("getMoteConfig: RC=RC_END_OF_LIST")
            else:
                helpers.OUT("getMoteConfig RC={}".format(hex(RC)))

        elif packetType == 0x30:        # getPathInfo
            pass
        elif packetType == 0x31:        # getNextPathInfo
            pass
        elif packetType == 0x32:        # setAdvertising
            pass
        elif packetType == 0x33:        # setDownstreamFrameMode
            pass
        elif packetType == 0x35:        # getManagerStatistics
            pass
        elif packetType == 0x36:        # setTime
            pass
        elif packetType == 0x37:        # getLicense (deprecated)
            pass
        elif packetType == 0x38:        # setLicense (deprecated)
            pass
        elif packetType == 0x3A:        # setCLIUser
            pass
        elif packetType == 0x3B:        # sendIP
            pass
        elif packetType == 0x3D:        # restoreFactoryDefaults
            pass
        elif packetType == 0x3E:        # getMoteInfo
            pass
        elif packetType == 0x3F:        # getNetworkConfig
            pass
        elif packetType == 0x40:        # getNetworkInfo
            helpers.OUT("getNetworkInfo ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x41:        # getMoteConfigById
            helpers.OUT("getMoteConfiguById ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x42:        # setCommonJoinKey
            pass
        elif packetType == 0x43:        # getIPConfig
            pass
        elif packetType == 0x44:        # setIPConfig
            pass
        elif packetType == 0x45:        # deleteMote
            helpers.OUT("deleteMote ACK, RC={}".format(hex(RC)))
            pass
        elif packetType == 0x46:        # getMoteLinks
            pass

    # def delete_mote_from_list(self, macAddress):
    #     index = self.index_by_macAddress(macAddress=macAddress)
    #     if index >= 0:
    #         del self.current_iCOMOX_list[index]
    #         if callable(self.callback_iCOMOX_removed):
    #             self.callback_iCOMOX_removed(macAddress=macAddress)

    # def delete_all_motes_from_list(self):
    #     if callable(self.callback_iCOMOX_removed):
    #         for i in range(len(self.current_iCOMOX_list)-1, -1, -1):
    #             macAddress = self.current_iCOMOX_list[i].macAddress
    #             self.callback_iCOMOX_removed(macAddress=macAddress)
    #     del self.current_iCOMOX_list[:]

    # def add_mote_to_list(self, macAddress):
    #     index = self.index_by_macAddress(macAddress=macAddress)
    #     if index < 0:
    #         self.send_getMoteConfig(macAddress=macAddress, next=False)
    #     else:
    #         if callable(self.callback_iCOMOX_added):
    #             self.callback_iCOMOX_added(self.current_iCOMOX_list[index])

    # def add_all_motes_to_list(self):
    #     if callable(self.callback_iCOMOX_added):
    #         for iCmxSmip in self.current_iCOMOX_list:
    #             self.callback_iCOMOX_added(iCmxSmip)

    def change_iCOMOX_SMIP_state(self, macAddress, state=None):
        try:
            iComox = common.iCOMOXs.find_by_macAddress(macAddress=macAddress)
            if iComox is not None:
                if state is not None:
                    iComox.state = state
                if callable(self.callback_updated_iCOMOX_SMIP_list):
                    self.callback_updated_iCOMOX_SMIP_list()
            else:
                helpers.OUT("Failed to find MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
                self.send_getMoteConfig(macAddress=macAddress, next=False)
        except Exception as ex:
            if hasattr(ex, 'message'):
                helpers.OUT(ex.message)
        finally:
            pass

    def on_notif_event(self, comm, eventId, eventType, eventData):
        if eventType == 0:              # moteReset
            macAddress=eventData[0:8]
            helpers.OUT("DeleteMote MAC={}".format(helpers.u8s_to_str(macAddress, ":", "")))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_LOST)
            # self.refresh_current_iCOMOX_list()

        elif eventType == 1:            # networkReset
            common.iCOMOXs.delete_all_of_type(Type=iCOMOX_list.cCLIENT_TYPE_SMIP)
            common.app.Clients.delete_all()
            # self.refresh_current_iCOMOX_list()

        elif eventType == 2:            # commandFinish
            pass

        elif eventType == 3:            # moteJoin
            macAddress = eventData[0:8]
            helpers.OUT("moteJoin MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_NEGOTIATING)

        elif eventType == 4:            # moteOperational
            macAddress = eventData[0:8]
            helpers.OUT("moteOperational MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_OPERATIONAL)

        elif eventType == 5:            # moteLost
            macAddress = eventData[0:8]
            helpers.OUT("moteLost MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_LOST)

        elif eventType == 6:            # networkTime
            pass
        elif eventType == 7:            # pingResponse
            pass
        elif eventType == 10:           # pathCreate
            pass
        elif eventType == 11:           # pathDelete
            pass
        elif eventType == 12:           # packetSent
            # Triggered by successful sendData command
            if callable(self.callback_data_sent):
                sendData_callbackId, RC = struct.unpack(">LB", eventData)
                self.callback_data_sent(self.Comm_LTC5800IPR, RC, sendData_callbackId == self.sendData_callbackId)
            self.sendData_callbackId = 0

        elif eventType == 13:           # moteCreate
            macAddress = eventData[0:8]
            [moteID] = struct.unpack_from(">H", eventData, 8)
            helpers.OUT("moteCreate MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
            iComox = common.iCOMOXs.add(Type=iCOMOX_list.cCLIENT_TYPE_SMIP, macAddress=macAddress, isRouting=False, moteID=moteID, state=Dongle_Communication.MOTE_STATE_LOST)
            # self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=None)

        elif eventType == 14:           # moteDelete
            macAddress = eventData[0:8]
            helpers.OUT("moteDelete MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_LOST)

        elif eventType == 15:           # joinFailed
            macAddress = eventData[0:8]
            helpers.OUT("joinFailed MAC: {}, due to reason {}".format(helpers.u8s_to_str(macAddress, ":", ""), eventData[8]))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_NEGOTIATING)

        elif eventType == 16:           # invalidMIC
            macAddress = eventData[0:8]
            helpers.OUT("InvalidMIC MAC: {}".format(helpers.u8s_to_str(macAddress, ":", "")))
            self.change_iCOMOX_SMIP_state(macAddress=macAddress, state=Dongle_Communication.MOTE_STATE_LOST)

    def on_notif_data(self, comm, timestamp, macAddress, srcPort, dstPort, data):
        iComox = common.iCOMOXs.find_by_macAddress(macAddress=macAddress)
        if (iComox is None) or (len(data) < iCOMOX_messages.SMIP_PACKET_HEADER_SIZE + 1):  # = sizeof(packet index) + at least 1 byte for data
            return

        packet_index = data[0]
        packet_data = data[iCOMOX_messages.SMIP_PACKET_HEADER_SIZE:]

        if packet_index == 0:    # start a new message
            if (packet_data[0] < iCOMOX_messages.cCOMOX_MSG_CODE_COUNT) and (packet_data[0] != iCOMOX_messages.cCOMOX_MSG_CODE_Report):
                helpers.OUT("Get message ({}) from {}".format(hex(packet_data[0]), helpers.u8s_to_str(macAddress, ":", "")))
            iComox.accumulated_msg = bytearray()
            iComox.expected_msg_size = 0
            iComox.packetID = 0
            # if (packet_data[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Report) and (len(packet_data) < iCOMOX_messages.COMOX_IN_MSG_SIZE[iCOMOX_messages.cCOMOX_MSG_CODE_Report]):
            #     helpers.OUT("on_notify_data: packet 0 contains less bytes than report message header")
            #     return
            # Determine the incoming message expected size, assuming packet 0 is enough for determining it
            while len(packet_data) > 0:
                bytes_to_read = messages_utils.on_get_in_message_size(accumulated_msg=iComox.accumulated_msg, adxl356_smip=True)
                if bytes_to_read < 0:   # check if the message is a legal one
                    helpers.OUT("on_notif_data: Illegal message was received")
                    if iComox == common.iCOMOXs.current:
                        common.app.StatusBar.set("Unrecognized message received")
                        common.app.StatusBar.progressbar_hide()
                    return
                elif bytes_to_read > 0:
                    iComox.expected_msg_size = len(iComox.accumulated_msg) + bytes_to_read
                    bytes_read = min(len(packet_data), bytes_to_read)
                    iComox.accumulated_msg += packet_data[:bytes_read]
                    packet_data = packet_data[bytes_read:]
                    # bytes_to_read -= bytes_read
                else:
                    break

        else:
            if packet_index != iComox.packetID:   # if we got an unexpected packetID in the packet
                if iComox == common.iCOMOXs.current:
                    common.app.StatusBar.set("Unexpected packet ID (received: {}, expected: {})".format(packet_index+1, iComox.packetID+1))
                    common.app.StatusBar.progressbar_hide()
                iComox.packetID = 0  # mark that the next packet must start a new message (packetID = 0)
                return

            # Add the received packet to the accumulated message
            iComox.accumulated_msg += packet_data[0:min(len(packet_data), Dongle_Communication.SMIP_MAX_PAYLOAD_TO_MANAGER-iCOMOX_messages.SMIP_PACKET_HEADER_SIZE, iComox.expected_msg_size - len(iComox.accumulated_msg))]

        # Display the message progress in statusBar
        max_num_of_packets = int(math.ceil(iComox.expected_msg_size/(Dongle_Communication.SMIP_MAX_PAYLOAD_TO_MANAGER-iCOMOX_messages.SMIP_PACKET_HEADER_SIZE)))
        if iComox == common.iCOMOXs.current:
            msg_description = messages_utils.get_IN_MSG_Description(msg=iComox.accumulated_msg)
            s = 'Received packet {} out of {} ({}) from MAC address {}'.format(packet_index+1, max_num_of_packets, msg_description, helpers.u8s_to_str(macAddress, ":"))
            common.app.StatusBar.set(s)
            common.app.StatusBar.message_progress(packet_index=packet_index+1, total_packets=max_num_of_packets)
            #helpers.OUT(s)

        if len(iComox.accumulated_msg) >= iComox.expected_msg_size:
            iComox.accumulated_msg = iComox.accumulated_msg[:iComox.expected_msg_size]
            if callable(self.callback_process_message):
                self.callback_process_message(msg=iComox.accumulated_msg, iComox=iComox)
            iComox.packetID = 0    # mark that the next packet must start a new message (packetID = 0)
            if iComox == common.iCOMOXs.current:
                common.app.StatusBar.message_progress(packet_index=0, total_packets=max_num_of_packets)
        else:
            iComox.packetID += 1

    def on_manager_session_stop(self, comm, mgrHelloCounter):
        if (mgrHelloCounter >= 3):
            comm.send_ClientHello()
        if self.callback_connection_state is not None:
            self.callback_connection_state(serial_connection=True, session=False)

    def on_manager_session_start(self, comm, RC, version, mode):
        self.send_getSystemInfo()
        if self.callback_connection_state is not None:
            self.callback_connection_state(serial_connection=True, session=True)

    def on_serial_comm_open(self, comm):
        if self.callback_connection_state is not None:
            self.callback_connection_state(serial_connection=True, session=False)

    def on_serial_comm_close(self, comm):
        if self.callback_connection_state is not None:
            self.callback_connection_state(serial_connection=False, session=False)

    def refresh_current_iCOMOX_list(self):
        # self.temp_iCOMOX_list.clear()
        return self.send_getMoteConfig(macAddress=self.manager_macAddress, next=True)
    #
    # def index_by_macAddress(self, macAddress):
    #     # return [i if macAddress == x.macAddress else -1 for i, x in enumerate(self.current_iCOMOX_list)]
    #     for i in range(0, len(self.current_iCOMOX_list)):
    #         if self.current_iCOMOX_list[i].macAddress == macAddress:
    #             return i
    #     return -1
    #
    # def index_by_moteId(self, moteId):
    #     # return [i if moteId == x.moteId else -1 for i, x in enumerate(self.current_iCOMOX_list)]
    #     for i in range(0, len(self.current_iCOMOX_list)):
    #         if self.current_iCOMOX_list[i].moteId == moteId:
    #             return i
    #     return -1

