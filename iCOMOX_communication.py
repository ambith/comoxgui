import threading
import serial
import time
import iCOMOX_messages
import helpers
import common

class class_iCOMOX_Communication:
    def __init__(self, comm_port, callback_get_msg_size, callback_process_message, baudrate=115200, callback_open=None,
                 callback_close=None, duration_of_break_us=0, no_msg_read_timeout_sec=0,
                 callback_no_msg_read_timeout=None, serial_comm_thread=None):
        self.serObj = serial.Serial()
        self.serObj.baudrate = baudrate
        self.serObj.port = comm_port
        self.serObj.bytesize = serial.EIGHTBITS
        self.serObj.parity = serial.PARITY_NONE
        self.serObj.stopbits = serial.STOPBITS_TWO
        self.serObj.timeout = 1.0               # seconds, For read
        self.serObj.write_timeout = 1.0         # seconds
        self.serObj.interCharTimeout = None     # For both read & write
        self.serObj.xonxoff = False
        self.serObj.rtscts = False
        self.serObj.dsrdtr = False
        self.serObj.setRTS(False)
        self.serObj.setDTR(True)
        self.serObj.set_buffer_size(rx_size=100000, tx_size=4096)
        self.Terminate = False      # Terminate is checked by the open/read thread
        self.no_msg_read_timeout_sec = no_msg_read_timeout_sec
        self.__abs_time_sec__ = time.time()
        self.duration_of_break_us = duration_of_break_us * 1E-6
        self.OnProcessMessages = callback_process_message
        self.OnGetIncomingMsgSize = callback_get_msg_size
        self.OnOpen = callback_open
        self.OnClose = callback_close
        self.OnNoMsgReadTimeout = callback_no_msg_read_timeout
        self.internal_receive_buffer = bytearray()  # it does not remain local variable for debug purpose
        self.received_msg = bytearray()             # it does not remain local variable for debug purpose
        if serial_comm_thread is None:
            self.thread = threading.Thread(target=self.__serial_comm_thread__)  # , args=(self,))
        else:
            self.thread = threading.Thread(target=serial_comm_thread)
        self.thread.start()

    def __delete__(self, instance):
        self.Terminate = True
        self.close()

    def test_for_no_msg_read_timeout(self):
        if (self.no_msg_read_timeout_sec != 0) and (time.time() - self.__abs_time_sec__ >= self.no_msg_read_timeout_sec):
            if callable(self.OnNoMsgReadTimeout):
                self.OnNoMsgReadTimeout(self)
            self.__abs_time_sec__ = time.time()
            return True
        else:
            return False

    def open(self, commPort=""):
        if self.serObj is None:
            return False
        if self.is_open():
            if self.serObj.port != commPort:
                self.serObj.close()
            else:
                return True
        try:
            self.serObj.port = commPort
            self.serObj.open()
        except Exception as ex:
            # print(ex.messaage)
            result = False
        else:
            result = True
        finally:
            if result and callable(self.OnOpen):
                self.OnOpen(comm=self)
            return result

    def is_open(self):
        return self.serObj.is_open

    def close(self):
        if self.is_open():
            self.serObj.flushOutput()
            self.serObj.close()
            if callable(self.OnClose):
                self.OnClose(comm=self)

#    def read(self, bytes_to_read):
#        result = bytearray()
#        try:
#            while (bytes_to_read > 0) and not self.Terminate:
#                bytes_read = self.serObj.read(bytes_to_read)
#                bytes_to_read -= len(bytes_read)
#                result += bytes_read
#                if self.test_for_no_msg_read_timeout():
#                    raise Exception("class_iCOMOX_Communication.read(): waiting too long without message been received")
#        except Exception as ex:     # Exception as ex:
#            result = bytearray()
#        finally:
#            return result

    def write(self, buffer_to_write):
        try:
            if self.duration_of_break_us != 0:
                self.serObj.send_break(self.duration_of_break_us)
            while not self.Terminate and (len(buffer_to_write) > 0):
                bytes_written = self.serObj.write(buffer_to_write)
                buffer_to_write = buffer_to_write[bytes_written:]

            result = len(buffer_to_write) == 0
        except:     # Exception as ex:
            result = False
        finally:
            return result

    #def find(self, arr, subarr, startpos=0):
    #    if (len(arr) <= startpos) or (len(subarr) == 0):
    #        return -1
    #    result = -1
    #    for result in range(startpos, len(arr)-len(subarr)+1):
    #        for j in range(0, len(subarr)):
    #            if arr[i+j] != subarr[j]:
    #                break
    # __serial_comm_thread__ is the thread function
    # It reads bytes from the port, accumulating them to meaningful messages by using OnGetIncomingMsgSize() and call
    #       OnProcessMessage() with the accumulated message
    # It can also signal the user if there is no activity for too long periods
    def __serial_comm_thread__(self):
        if not callable(self.OnGetIncomingMsgSize) or not callable(self.OnProcessMessages):
            raise Exception("communication.__serial_comm_thread__: OnGetIncomingMsgSize() and OnProcessMessages()"
                            " callbacks must be callable functions")
        # receive loop
        while not self.Terminate:
            # Wait until communication is open
            while not self.Terminate and not self.is_open():
                time.sleep(0.5)
            if self.Terminate:
                break

            # communication is open.
            self.__abs_time_sec__ = time.time()
            self.internal_receive_buffer = bytearray()
            self.received_msg = bytearray()
            header_received_flag = False
            while not self.Terminate and self.is_open():
                try:
                    self.internal_receive_buffer += self.serObj.read_all()
                except:
                    self.internal_receive_buffer = bytearray()
                    self.received_msg = bytearray()
                    self.close()
                    continue
                finally:
                    pass

                # phase 1: detect the header UART_IN_MSG_PREFIX
                if not header_received_flag:
                    header_pos = self.internal_receive_buffer.find(iCOMOX_messages.UART_IN_MSG_PREFIX, 0)
                    if header_pos >= 0:
                        self.internal_receive_buffer = self.internal_receive_buffer[header_pos+len(iCOMOX_messages.UART_IN_MSG_PREFIX):]
                        header_received_flag = True
                    else:
                        self.internal_receive_buffer = self.internal_receive_buffer[-len(iCOMOX_messages.UART_IN_MSG_PREFIX)+1:]
                else:
                    # phase 2: detect the message
                    adxl356_smip = common.app.Information.icomox_board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_SMIP
                    bytes_to_read = self.OnGetIncomingMsgSize(accumulated_msg=self.received_msg, adxl356_smip=adxl356_smip)
                    if bytes_to_read < 0:   # if invalid message
                        #helpers.OUT("Invalid message: {}".format(helpers.u8s_to_str(arr=self.received_msg, separator=" ", prefix="")))
                        break
                    elif bytes_to_read == 0:    # if complete receiving a valid message
                        self.OnProcessMessages(msg=self.received_msg, CommPort=self.serObj.port)
                        # if (len(self.received_msg) > 1) and (self.received_msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Report):
                        #     helpers.OUT("Report message type 0x{:02X}, length {}".format(self.received_msg[1], len(self.received_msg)))
                        # else:
                        #     helpers.OUT("Received message type 0x{:02X}, length {}".format(self.received_msg[0], len(self.received_msg)))
                        self.received_msg = bytearray()
                        header_received_flag = False
                    else:                   # more bytes are needed to be accumulated for the current message
                        bytes_read = min(len(self.internal_receive_buffer), bytes_to_read)
                        self.received_msg += self.internal_receive_buffer[:bytes_read]
                        self.internal_receive_buffer = self.internal_receive_buffer[bytes_read:]
                self.test_for_no_msg_read_timeout()

        # Thread was requested to terminate, then close the serial port
        self.close()
        helpers.OUT("Left __serial_comm_thread__()")
