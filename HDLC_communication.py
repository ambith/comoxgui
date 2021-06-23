from iCOMOX_communication import class_iCOMOX_Communication
import hdlc
import time
import helpers

class class_HDLC_Communication(class_iCOMOX_Communication):
    ACK_TIMEOUT         = 0.2   # 200 msec
    MAX_NO_ACK_RETRIES  = 3

    def __init__(self, comm_port, callback_process_message, callback_serial_comm_open=None, callback_serial_comm_close=None, callback_no_ack_timeout=None):  #   , no_msg_read_timeout_sec=3, callback_no_msg_read_timeout=None):
        class_iCOMOX_Communication.__init__(
            self=self,
            comm_port=comm_port,
            baudrate=115200,
            #duration_us_of_break_before_write=0,   # 0 is the default value
            callback_get_msg_size=None,
            callback_process_message=callback_process_message,
            callback_open=callback_serial_comm_open,
            callback_close=callback_serial_comm_close,
            no_msg_read_timeout_sec=0,
            callback_no_msg_read_timeout=None,
            serial_comm_thread=self.__serial_comm_thread__
        )
        self.callback_timeout = callback_no_ack_timeout
        self.no_ack_timeout = None
        self.no_ack_retries = None

    def __build_hdlc_frame__(self, msg):
        result = bytearray(b"\x7E")
        msg += hdlc.FCS16_Calculate(msg)
        for Ch in msg:
            if (Ch == 0x7D) or (Ch == 0x7E):
                result += bytearray(b"\x7D")
                result += bytearray([Ch ^ 0x20])
            else:
                result += bytearray([Ch])
        result += bytearray(b"\x7E")
        return result

    def __extract_msg_from_hdlc_frame__(self, hdlc_frame):
        msg = bytearray(b"")
        if (len(hdlc_frame) < 2) or (hdlc_frame[0] != 0x7E) or (hdlc_frame[-1] != 0x7E):
            return [bytearray(b""), False]
        escaped = False
        for Ch in hdlc_frame[1:-1]:
            if escaped:
                if (Ch == 0x5D) or (Ch == 0x5E):
                    msg += bytearray([Ch ^ 0x20])
                    escaped = False
                else:
                    return [bytearray(b""), False]
            else:
                if Ch == 0x7E:
                    return [bytearray(b""), False]
                elif Ch == 0x7D:
                    escaped = True
                else:
                    msg += bytearray([Ch])
        if len(msg) >= 3:    # at least one character to process + 2 bytes of FCS
            FCS = msg[-2:]
            msg = msg[:-2]
            if FCS != hdlc.FCS16_Calculate(msg):
                return [bytearray(b""), False]
            else:
                return [msg, True]
        else:
            return [bytearray(b""), False]

#    def bytearray_find(self, bytesarr, value, start=0):
#        for i in range(start, len(bytesarr)):
#            if bytesarr[i] == value:
#                return i
#        return -1

    def __extractable_size_of_hdlc_frame__(self, data):
        firstEscapeIndex = data.find(b"\x7E", 0)     #firstEscapeIndex = self.bytearray_find(bytesarr=data, value=0x7E, start=0)
        if firstEscapeIndex > 0:
            return firstEscapeIndex, False   # extract the leading firstEscapeIndex bytes, no HDLC frame was detected
        elif firstEscapeIndex < 0:
            return 0, False

        if len(data) < 2:
            return 0, False

        lastEscapeIndex = data.find(b"\x7E", 1)     #lastEscapeIndex = self.bytearray_find(bytesarr=data, value=0x7E, start=1)
        if lastEscapeIndex < 0:
            return 0, False

        return lastEscapeIndex - firstEscapeIndex + 1, True

    def write_hdlc_msg(self, msg):
        hdlc_frame = self.__build_hdlc_frame__(msg)
        # helpers.OUT("TX mesage: " + helpers.u8s_to_str(hdlc_frame, " ", ""))
        return self.write(hdlc_frame)

#    def read_hdlc_msg(self):
#        result = True
#        try:
#            hdlc_frame = self.serObj.read_until(terminator="\x7E")
#        except:
#            hdlc_frame = bytearray()
#            result = False
#        finally:
#            if len(hdlc_frame) == 0:
#                return hdlc_frame, result
#            else:
#                return self.__extract_msg_from_hdlc_frame__(hdlc_frame)

    # __serial_comm_thread__ is the thread function
    # It serves 2 purposes:
    # 1. Handle events of close by trying to reopen the port
    # 2. Read HDLC messages from the port and call OnProcessMessage() with the accumulated message
    def __serial_comm_thread__(self):
        if not callable(self.OnProcessMessages):
            raise Exception("communicationHDLC.__serial_comm_thread__: OnProcessMessages()"
                            " callback must be a callable function")
        # reopen loop
        while not self.Terminate:
            # Wait until communication is open
            while not self.Terminate and not self.is_open():
                time.sleep(0.5)

            # read loop
            received_bytes = bytearray()
            while not self.Terminate and self.is_open():
                try:
                    received_bytes += self.serObj.read(size=self.serObj.in_waiting)
                except:
                    received_bytes = bytearray()
                    self.close()
                    continue
                finally:
                    pass

                bytes_to_extract, hdlc_frame_detected = self.__extractable_size_of_hdlc_frame__(received_bytes)
                if hdlc_frame_detected:
                    hdlc_frame = received_bytes[:bytes_to_extract]
                    received_bytes = received_bytes[bytes_to_extract:]
                    received_msg, result = self.__extract_msg_from_hdlc_frame__(hdlc_frame=hdlc_frame)
                    if not result:   # if invalid message due to any reason: length, flag char in the middle, too short message, checksum failure
                        self.close()
                        break
                    elif len(received_msg) != 0:           # if valid message was received
                        # helpers.OUT("RX message: " + helpers.u8s_to_str(hdlc_frame, " ", ""))
                        if callable(self.OnProcessMessages):
                            self.OnProcessMessages(self, received_msg)
                else:
                    received_bytes = received_bytes[bytes_to_extract:]

        # Thread was requested to terminate, then close the serial port
        self.close()
