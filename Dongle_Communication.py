import HDLC_communication
import struct
import time
import helpers

LTC5800IPR_PROTOCOL_VERSION = 4

RC_OK               = 0
RC_INVALID_COMMAND  = 1
RC_INVALID_ARGUMENT = 2
RC_END_OF_LIST      = 11
RC_NO_RESOURCES     = 12
RC_IN_PROGRESS      = 13
RC_NACK             = 14
RC_WRITE_FAIL       = 15
RC_VALIDATION_ERROR = 16
RC_INV_STATE        = 17
RC_NOT_FOUND        = 18
RC_UNSUPPORTED      = 19

MOTE_STATE_LOST         = 0
MOTE_STATE_NEGOTIATING  = 1
MOTE_STATE_OPERATIONAL  = 4

SMIP_MAX_PAYLOAD_TO_MANAGER = 90


class class_Dongle_Communication(HDLC_communication.class_HDLC_Communication):
    def __init__(self,
                 comm_port,
                 callback_command_resp=None,            # response for commands
                 callback_notif_event=None,             # notification.events
                 callback_notif_log=None,               # notification.logs
                 callback_notif_data=None,              # notifications.data - here data from mote should be processed
                 callback_notif_ipData=None,            # notification.ipData - here data from mote using ipv6 should be processed
                 callback_notif_healthReport=None,      # notification.health RawDataSensors
                 callback_MgrHello=None,                # when manager disconnects from us and waiting for ClientHello message (is_active_session -> False)
                 callback_HelloResponse=None,           # when manager connects us and waiting for further messages from us (is_active_session -> True)
                 callback_serial_comm_open=None,        # serial COM port is now open
                 callback_serial_comm_close=None):      # serial COM port is now closed
        HDLC_communication.class_HDLC_Communication.__init__(
            self=self,
            comm_port=comm_port,
            callback_process_message=self.__process_message__,
            callback_serial_comm_open=self.__on_serial_comm_open__,
            callback_serial_comm_close=self.__on_serial_comm_close__
        )
        self.callback_command_resp = callback_command_resp
        self.callback_serial_comm_open = callback_serial_comm_open
        self.callback_serial_comm_close = callback_serial_comm_close
        self.callback_notif_event = callback_notif_event
        self.callback_notif_log = callback_notif_log
        self.callback_notif_data = callback_notif_data
        self.callback_notif_ipData = callback_notif_ipData
        self.callback_notif_healthReport = callback_notif_healthReport
        self.callback_MgrHello = callback_MgrHello
        self.callback_HelloResponse = callback_HelloResponse
        self.in_active_session = False
        self.MgrHelloCounter = 0    # up counter to decide when to send clientHello again
        self.mgrSeqNo = 0   # manager sequence number as received in HelloResponse packet, and by acknowledged messages that the manager sends us
        self.cliSeqNo = 0   # iComox sequence number sent in Hello message, and in iComox request messages
        self.seqNumber = 0  # contains the sequence number of the packet that was acknowledged. write_to_manager() checks it when it waits for response for messages that need to get ACK
        # manage the mechanism to send messages that requires returned ACK responses, again and again
        self.write_attempts = 0
        self.latest_time_for_ack_to_arrive = 0
        self.msg_requires_ack = bytearray()

    def __on_serial_comm_open__(self, comm):
        helpers.OUT("LTC5800IPR.__on_serial_comm_open__")
        self.in_active_session = False
        self.MgrHelloCounter = 0
        if callable(self.callback_serial_comm_open):
            self.callback_serial_comm_open(self)
        self.send_ClientHello()

    def __on_serial_comm_close__(self, comm):
        helpers.OUT("LTC5800IPR.__on_serial_comm_close__")
        self.in_active_session = False
        self.MgrHelloCounter = 0
        if callable(self.callback_serial_comm_close):
            self.callback_serial_comm_close(self)

    def __process_message__(self, comm, msg):
        #   helpers.OUT("LTC5800IPR.__process_message__")
        if len(msg) < 4:
            return
        control, packetType, seqNumber, payloadLen = struct.unpack("BBBB", msg[:4])

        if (control & 1) != 0:      # iComox received ack packet
            #   helpers.OUT("LTC5800IPR: ACK packet received")
            if (control & 2) != 0:  # iComox previously requested ACK
                if seqNumber == self.seqNumber:
                    return  # ignore the packet
                else:
                    self.seqNumber = seqNumber  # store the new incoming sequence number and process the message
            else:                   # iComox previously did not request ACK
                pass
        else:                       # iComox received data packet (probably notification)
            if (control & 2) != 0:  # manager requires ACK
                self.write_to_manager(packetType=packetType, AckPacket=True, serviceTypeAck=True)  # send ACK to the received message
            else:                   # manager requires no ACK
                pass
        # if (control & 1) != 0:      # dongle application received ack packet
        #     #   helpers.OUT("LTC5800IPR: ACK packet received")
        #     if (control & 2) != 0:  # dongle application previously requested ACK
        #         if seqNumber != self.cliSeqNo:
        #             self.send_ClientHello(cliSeqNo=0xFF)
        #             return
        #         else:
        #             pass
        #     else:                   # dongle application previously did not request ACK
        #         pass
        # else:                       # dongle application received data packet (probably notification)
        #     if (control & 2) != 0:  # manager requires ACK
        #         self.write_to_manager(packetType=packetType, AckPacket=True, serviceTypeAck=True)  # send ACK to the received message
        #         if seqNumber == self.seqNumber: # if duplicated packet
        #             return  # ignore the packet
        #         else:
        #             self.seqNumber = seqNumber  # store the new incoming sequence number and process the message
        #     else:                   # manager requires no ACK
        #         pass

        payload = msg[4:]

        if packetType == 0x14:  # notifications which can be events
            #   helpers.OUT("LTC5800IPR.notification received")
            if (payloadLen > 124) or (len(msg) != payloadLen + 4):
                return
            if len(payload) < 1:
                return
            notifType = payload[0]
            if notifType == 1:       # Event notification
                if len(payload) < 6:
                    return
                if callable(self.callback_notif_event):
                    eventId, eventType = struct.unpack_from(">LB", payload[:6], 1)
                    eventData = payload[6:]
                    self.callback_notif_event(self, eventId, eventType, eventData)

            elif notifType == 2:     # Log notification
                if len(payload) < 9:
                    return
                if callable(self.callback_notif_log):
                    macAddress = payload[1:9]
                    logMsg = payload[9:]
                    self.callback_notif_log(self, macAddress, logMsg)

            elif notifType == 4:     # Data payload notification
                if len(payload) < 25:
                    return
                if callable(self.callback_notif_data):
                    timestamp = payload[1:13]
                    macAddress = payload[13:21]
                    srcPort, dstPort = struct.unpack_from(">HH", payload[:25], 21)
                    data = payload[25:]
                    self.callback_notif_data(self, timestamp, macAddress, srcPort, dstPort, data)

            elif notifType == 5:     # 6lowpan packet notification
                if len(payload) < 21:
                   return
                if callable(self.callback_notif_ipData):
                    timestamp = payload[1:13]
                    macAddress = payload[13:21]
                    data = payload[21:]
                    self.callback_notif_ipData(self, timestamp, macAddress, data)

            elif notifType == 6:     # Health report notification
                if len(payload) < 9:
                    return
                if callable(self.callback_notif_healthReport):
                    macAddress = payload[1:9]
                    data = payload[9:]
                    self.callback_notif_healthReport(self, macAddress, data)

            else:
                return

        elif packetType == 2:   # Hello response
            helpers.OUT("LTC5800IPR.HelloResponse")
            if len(payload) < 5:
                return
            RC, version, self.mgrSeqNo, self.cliSeqNo, mode = struct.unpack("BBBBB", payload[:5])
            if RC == 0:
                self.in_active_session = True
                self.MgrHelloCounter = 0
                if callable(self.callback_HelloResponse):
                    self.callback_HelloResponse(self, RC, version, mode)
            else:
                self.send_ClientHello(self)

        elif packetType == 3:   # MgrHello
            helpers.OUT("LTC5800IPR.MgrHello")
            self.in_active_session = False
            self.MgrHelloCounter += 1
            if callable(self.callback_MgrHello):
                self.callback_MgrHello(self, self.MgrHelloCounter)
            #   self.send_ClientHello()

        else:
            if (len(payload) == 0) or (payloadLen > 124) or (len(msg) != payloadLen + 4):   # The RC field is not included in the payloadLen????
                helpers.OUT("__process_message__(): Illegal payload field, or payload does not contain RC field")
                return      # illegal payloadLen field, or payload does not contain the RC field

            if callable(self.callback_command_resp):
                RC = payload[0]
                if len(payload) < 2:
                    data = bytearray()
                else:
                    data = payload[1:]
                self.callback_command_resp(self, packetType, RC, data)

    def write_service_type_ack_msg_to_manager(self):
        if self.write_attempts > 0:
            self.write_attempts -= 1
            self.latest_time_for_ack_to_arrive = time.monotonic() + 0.2   # 200 msec before trying again
            result = self.write_hdlc_msg(msg=self.msg_requires_ack)
            if not result:
                self.write_attempts = 0
                self.close()
        else:
            self.send_ClientHello(cliSeqNo=0)
            result = False
        return result

    def write_to_manager(self, packetType, payload=bytearray(), AckPacket=False, serviceTypeAck=True):
        Control = 0
        if AckPacket:
            Control |= 1
        if serviceTypeAck:
            Control |= 2

        if serviceTypeAck:
            if AckPacket:
                seqNo = self.mgrSeqNo
            else:
                self.cliSeqNo = (self.cliSeqNo + 1) % 256
                seqNo = self.cliSeqNo
        else:
            seqNo = 0

        msg = bytearray([Control, packetType, seqNo, len(payload)]) + payload

        if serviceTypeAck:
            self.msg_requires_ack = msg
            self.write_attempts = 1
            return self.write_service_type_ack_msg_to_manager()
        else:
            return self.write_hdlc_msg(msg=msg)

    def send_ClientHello(self, cliSeqNo=None):
        helpers.OUT("ClientHello")
        if cliSeqNo is not None:
            self.cliSeqNo = cliSeqNo
        payload = bytearray(struct.pack("BBB", LTC5800IPR_PROTOCOL_VERSION, self.cliSeqNo, 0))

        return self.write_to_manager(packetType=0x01, payload=payload, serviceTypeAck=False)

    def send_resetSystem(self, serviceTypeAck=True):
        helpers.OUT("resetSystem")
        return self.write_to_manager(packetType=0x15, payload=bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00"), serviceTypeAck=serviceTypeAck)

    def send_resetMote(self, macAddress, serviceTypeAck=True):
        helpers.OUT("resetMote")
        payload = bytearray(b"\x02") + macAddress
        return self.write_to_manager(packetType=0x15, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_subscribe(self, filter, unackFilter, serviceTypeAck=True):
        helpers.OUT("subscribe")
        payload = bytearray(struct.pack(">LL", filter, unackFilter))
        return self.write_to_manager(packetType=0x16, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getTime(self, serviceTypeAck=True):
        helpers.OUT("getTime")
        return self.write_to_manager(packetType=0x17, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_setNetworkConfig(self, networkID, apTxPower, frameProfile, maxMotes, baseBandwidth, downFrameMultVal, numParents, ccaMode, channelList, bbMode, bbSize, isRadioTest, bwMult, oneChannel, serviceTypeAck=False):
        helpers.OUT("setNetworkConfig")
        payload = bytearray(struct.pack(">HbBHHBBBHBBBHB", networkID, apTxPower, frameProfile, maxMotes, baseBandwidth, downFrameMultVal, numParents, ccaMode, channelList, bbMode, bbSize, isRadioTest, bwMult, oneChannel))
        return self.write_to_manager(packetType=0x1A, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_clearStatistics(self, serviceTypeAck=True):
        helpers.OUT("clearStatistics")
        return self.write_to_manager(packetType=0x1F, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_exchangeMoteJoinKey(self, macAddress, key, serviceTypeAck=True):
        helpers.OUT("exchangeMoteJoinKey")
        payload = macAddress + key
        return self.write_to_manager(packetType=0x21, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_exchangeNetworkId(self, id, serviceTypeAck=True):
        helpers.OUT("exchangeNetworkId")
        return self.write_to_manager(packetType=0x22, payload=bytearray([id]), serviceTypeAck=serviceTypeAck)

    def send_radiotestTx(self, testType, chanMask, repeatCnt, txPower, seqSize, sequenceDef, stationId, serviceTypeAck=True):
        helpers.OUT("radiotestTx")
        assert(len(sequenceDef) <= 10)
        payload = bytearray(struct.pack(">BHHbB", testType, chanMask, repeatCnt, txPower, seqSize))
        for seqDef in sequenceDef:
            payload += bytearray(struct.pack(">BH", seqDef.pkLen, seqDef.delay))
        payload += bytearray([stationId])
        return self.write_to_manager(packetType=0x23, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_radiotestRx(self, mask, duration, stationId, serviceTypeAck=True):
        helpers.OUT("radiotestRx")
        payload = bytearray(struct.pack(">HHB", mask, duration, stationId))
        return self.write_to_manager(packetType=0x25, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getRadiotestStatistics(self, serviceTypeAck=True):
        helpers.OUT("getRadiotestStatistics")
        return self.write_to_manager(packetType=0x26, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_setACLEntry(self, macAddress, joinKey, serviceTypeAck=True):
        helpers.OUT("setACLEntry")
        payload = bytearray(macAddress) + bytearray(joinKey)
        return self.write_to_manager(packetType=0x27, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getNextACLEntry(self, macAddress, serviceTypeAck=True):
        helpers.OUT("getNextACLEntry")
        payload = bytearray(macAddress)
        return self.write_to_manager(packetType=0x28, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_deleteACLEntry(self, macAddress, serviceTypeAck=True):
        helpers.OUT("deleteACLEntry")
        payload = bytearray(macAddress)
        return self.write_to_manager(packetType=0x29, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_pingMote(self, macAddress, serviceTypeAck=True):
        helpers.OUT("pingMote")
        payload = bytearray(macAddress)
        return self.write_to_manager(packetType=0x2A, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getLog(self, macAddress, serviceTypeAck=True):
        helpers.OUT("getLog")
        payload = bytearray(macAddress)
        return self.write_to_manager(packetType=0x2B, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_sendData(self, macAddress, priority, srcPort, dstPort, data, serviceTypeAck=True):
        helpers.OUT("sendData")
        payload = bytearray(macAddress) + bytearray(struct.pack(">BHHB", priority, srcPort, dstPort, 0)) + bytearray(data)
        return self.write_to_manager(packetType=0x2C, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getSystemInfo(self, serviceTypeAck=True):
        helpers.OUT("getSystemInfo")
        return self.write_to_manager(packetType=0x2E, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_getMoteConfig(self, macAddress, next, serviceTypeAck=True):
        helpers.OUT("Send getMoteConfig() to {}".format(helpers.u8s_to_str(macAddress, ":", "")))
        payload = bytearray(macAddress) + bytearray([next])
        return self.write_to_manager(packetType=0x2F, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getPathInfo(self, sourceMacAddress, destMacAddress, serviceTypeAck=True):
        helpers.OUT("getPathInfo")
        payload = bytearray(sourceMacAddress) + bytearray(destMacAddress)
        return self.write_to_manager(packetType=0x30, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getNextPathInfo(self, macAddress, filter, pathId, serviceTypeAck=True):
        helpers.OUT("getNextPathInfo")
        payload = bytearray(macAddress) + bytearray(struct.pack(">BH", filter, pathId))
        return self.write_to_manager(packetType=0x31, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_setAdvertising(self, activate, serviceTypeAck=True):
        helpers.OUT("setAdvertising")
        payload = bytearray([activate])
        return self.write_to_manager(packetType=0x32, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_setDownstreamFrameMode(self, frameMode, serviceTypeAck=True):
        helpers.OUT("setDownstreamFrameMode")
        payload = bytearray([frameMode])
        return self.write_to_manager(packetType=0x33, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getManagerStatistics(self, serviceTypeAck=True):
        helpers.OUT("getManagerStatistics")
        return self.write_to_manager(packetType=0x35, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_setTime(self, trigger, utcTime, serviceTypeAck=True):
        helpers.OUT("setTime")
        payload = bytearray([trigger]) + bytearray(utcTime)
        return self.write_to_manager(packetType=0x36, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_setCLIUser(self, role, password, serviceTypeAck=True):
        helpers.OUT("setCLIUser")
        payload = bytearray([role]) + bytearray(password)
        return self.write_to_manager(packetType=0x3A, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_sendIP(self, macAddress, priority, options, encryptedOffset, data, serviceTypeAck=True):
        helpers.OUT("sendIP")
        payload = bytearray(macAddress) + bytearray(struct.pack(">BBB", priority, options, encryptedOffset)) + bytearray(data)
        return self.write_to_manager(packetType=0x3B, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_restoreFactoryDefaults(self, serviceTypeAck=True):
        helpers.OUT("restoreFactoryDefaults")
        return self.write_to_manager(packetType=0x3D, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_getMoteInfo(self, macAddress, serviceTypeAck=True):
        helpers.OUT("getMoteInfo")
        payload = bytearray(macAddress)
        return self.write_to_manager(packetType=0x3E, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getNetworkConfig(self, serviceTypeAck=True):
        helpers.OUT("getNetworkConfig")
        return self.write_to_manager(packetType=0x3F, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_getNetworkInfo(self, serviceTypeAck=True):
        helpers.OUT("getNetoworkInfo")
        return self.write_to_manager(packetType=0x40, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_getMoteConfigById(self, moteId, serviceTypeAck=True):
        helpers.OUT("getMoteConfigById")
        payload = bytearray(struct.pack(">H", moteId))
        return self.write_to_manager(packetType=0x41, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_setCommonJoinKey(self, key, serviceTypeAck=False):
        helpers.OUT("setCommonJoinKey")
        payload = bytearray(key)
        return self.write_to_manager(packetType=0x42, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getIPConfig(self, serviceTypeAck=True):
        helpers.OUT("getIPConfig")
        return self.write_to_manager(packetType=0x43, payload=bytearray(), serviceTypeAck=serviceTypeAck)

    def send_setIPConfig(self, ipv6Address, mask, serviceTypeAck=True):
        helpers.OUT("setIPConfig")
        payload = bytearray(ipv6Address) + bytearray(mask)
        return self.write_to_manager(packetType=0x44, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_deleteMote(self, macAddress, serviceTypeAck=True):
        helpers.OUT("deleteMote")
        payload = bytearray(macAddress)
        return self.write_to_manager(packetType=0x45, payload=payload, serviceTypeAck=serviceTypeAck)

    def send_getMoteLinks(self, macAddress, idx, serviceTypeAck=True):
        helpers.OUT("getMoteLinks")
        payload = bytearray(macAddress) + bytearray(struct.pack(">H", idx))
        return self.write_to_manager(packetType=0x46, payload=payload, serviceTypeAck=serviceTypeAck)
