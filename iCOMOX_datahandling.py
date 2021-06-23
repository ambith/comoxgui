import common_symbols
import struct
import time
import datetime
import helpers
import numpy as np
import common
from PingPong import ClassPingPongArr
import statistics_data_logger
import Dongle_Communication
import iCOMOX_messages
import messages_utils
import TCP_connectivity
import iCOMOX_socket
import iCOMOX_over_Dongle_Communication
import iCOMOX_list

if common_symbols.IOTC_enabled:
    import IOT_connectivity
if common_symbols.__REST_SUPPORT__:
    import http_connectivity

CONNECTION_STATE_iCOMOX_Disconnect              = 0
CONNECTION_STATE_iCOMOX_Connecting              = 1
CONNECTION_STATE_iCOMOX_Connected               = 2
CONNECTION_STATE_Dongle_Disconnected            = 3
CONNECTION_STATE_Dongle_Connecting              = 4
CONNECTION_STATE_Dongle_Connected               = 5
CONNECTION_STATE_iCOMOX_Connected_via_Dongle    = 6
CONNECTION_STATE_TcpIp_ServerDisconnected       = 7
CONNECTION_STATE_TcpIp_ServerConnected          = 8
CONNECTION_STATE_TcpIp_ClientConnected          = 9
CONNECTION_STATE_iCOMOX_Connected_via_TcpIp     = 10

epsilon = 1E-100

class class_DataHandling:
    def __init__(self, iCOMOX_Comm=None, Dongle_Comm=None, TcpIp_Comm=None):
        self.TcpIp_Comm = TcpIp_Comm
        self.iCOMOX_Comm = iCOMOX_Comm
        self.Dongle_Comm = Dongle_Comm
        if common_symbols.IOTC_enabled:
            self.iot = IOT_connectivity.IOT_DEVICES_LIST()
        if common_symbols.__REST_SUPPORT__:
            self.http = http_connectivity.HTTP_DEVICES_LIST()
        self.logfile_info = None
        # self.schedule_callback_time = 0
        # self.schedule_state_no_reports = True
        self.PingPongArr = ClassPingPongArr(count=256)#iCOMOX_messages.cCOMOX_SENSOR_COUNT+2+1)    # The "+2" is for the extra 2 ADXL356 RawDataSensors (for Y & Z axis). "+1" is for knowtion report
        self.MAG_ENERGY = 0
        self.network_frequency_Hz = 0
        self.after_ID = None    # Used by the schedule mechanism

    def __delete__(self, instance):
        if self.TcpIp_Comm is not None:
            del self.TcpIp_Comm
        if self.iCOMOX_Comm is not None:
            del self.iCOMOX_Comm
        if self.Dongle_Comm is not None:
            del self.Dongle_Comm
        if common_symbols.IOTC_enabled:
            if self.iot is not None:
                del self.iot
        if common_symbols.__REST_SUPPORT__:
            if self.http is not None:
                del self.http

    def PSD_linear_to_logarithmic(self, Pxxf):
        return 10. * np.log10(abs(Pxxf) + epsilon)

    def application_terminated(self):
        return (common.app is None) or common.app.terminated

    # def set_configuration_from_GUI(self, channel=None, RawDataSensors=None, Commons=None):
    #     if RawDataSensors is None:
    #         RawDataSensors = common.app.Configuration.WindowToModuleRawData()
    #     if channel is None:
    #         channel = common.app.Configuration.radioCommChannel.get()
    #     if Commons is None:
    #         Commons = common.app.Configuration.WindowToCommon()
    #     if channel > iCOMOX_messages.cCOMOX_CONFIGURATION_COMM_CHANNEL_USB:
    #         channel = iCOMOX_messages.cCOMOX_CONFIGURATION_COMM_CHANNEL_AUX
    #     self.icomox_set_configuration(RawDataSensors=RawDataSensors, CommChannel=channel, Activate=Commons)

    def USB_on_open(self, comm):
        new_iComox = common.iCOMOXs.add(Type=iCOMOX_list.cCLIENT_TYPE_USB, CommPort=comm.serObj.port)
        if new_iComox is None:
            helpers.OUT("USB_on_open(): Failed to add new iCOMOX to the list")
            return

        helpers.OUT("Serial port is open")
        common.iCOMOXs.current = new_iComox
        comm.write(iCOMOX_messages.OUT_MSG_Hello())
        common.app.drawConnectionState(connected=True)   # connection state
        common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Connecting)
        #self.set_configuration_from_GUI(channel=iCOMOX_messages.cCOMOX_CONFIGURATION_COMM_CHANNEL_USB) # MAY BE CHANGED

    def USB_on_close(self, comm):
        helpers.OUT("Serial port is close")
        iComox = common.iCOMOXs.find_by_CommPort(CommPort=comm.serObj.port)
        if iComox is None:
            return
        if iComox == common.iCOMOXs.current:
            common.iCOMOXs.current = None
            if not self.application_terminated():
                common.app.drawConnectionState(connected=False)   # disconnection error state
                common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Disconnect)
                if common_symbols.IOTC_enabled:
                    self.iot.cloud_update_stop()
                if common_symbols.__REST_SUPPORT__:
                    self.http.cloud_update_stop()
                # self.PingPongArr.clear_all()
        iComox.clear()
        if iComox in common.iCOMOXs.list:   # preventing exception in case the iComox has already been removed from common.iCOMOXs.list by other thread
            common.iCOMOXs.list.remove(iComox)

    def on_dongle_connection_state_changed(self, serial_connection=False, session=False):
        if serial_connection:
            common.app.drawConnectionState(connected=session)
            if session:
                common.app.drawLedState(connection_state=CONNECTION_STATE_Dongle_Connected)
                if common_symbols.IOTC_enabled:
                    self.iot.cloud_update_start()
                if common_symbols.__REST_SUPPORT__:
                    self.http.cloud_update_start()
            else:
                common.app.drawLedState(connection_state=CONNECTION_STATE_Dongle_Connecting)

        else:
            if common_symbols.IOTC_enabled:
                self.iot.cloud_update_stop()
            if common_symbols.__REST_SUPPORT__:
                self.http.cloud_update_stop()
            common.iCOMOXs.current = None
            common.app.Clients.SmipClientsTreeView.delete_all()
            common.iCOMOXs.delete_all_of_type(Type=iCOMOX_list.cCLIENT_TYPE_SMIP)
            common.app.drawConnectionState(connected=False)
            common.app.drawLedState(connection_state=CONNECTION_STATE_Dongle_Disconnected)

    def on_dongle_updated_iCOMOX_list(self):
        current_SMIP_iCOMOXs = [*filter(lambda iCmx : iCmx.Type == iCOMOX_list.cCLIENT_TYPE_SMIP, common.iCOMOXs.list)]
        SMIP_iCOMOXs_to_remove = [*filter(lambda iCmx : iCmx.state != Dongle_Communication.MOTE_STATE_OPERATIONAL, current_SMIP_iCOMOXs)]
        # current_iCOMOX_SMIP = common.iCOMOXs.current
        for iComox in SMIP_iCOMOXs_to_remove:
            common.app.Clients.delete(iComox=iComox)
            # Delete the Hello & Reports[] field
            iComox.HelloRequestTime = None
            iComox.Hello = None
            iComox.Reports = [None]*256
            # common.iCOMOXs.list.remove(iComox)
            current_SMIP_iCOMOXs.remove(iComox)
        # if (current_iCOMOX_SMIP is not None) and (common.iCOMOXs.current is None):
        #     self.on_dongle_connection_state_changed(serial_connection=True, session=True)

        # iCOMOXs_list = []
        for iComox in current_SMIP_iCOMOXs:
            if iComox.Hello is not None:
                # iCOMOXs_list.append("Unique ID: {}, MAC address: {}".format(iComox.UniqueID().hex(), helpers.u8s_to_str(iComox.macAddress, ":", "")))
                common.app.Clients.insert(iComox=iComox)
                # else:
                #     self.send_msg(msg=iCOMOX_messages.OUT_MSG_Hello(), iComox=iComox)
            else:
                # iComox = common.iCOMOXs.add(Type=iCOMOX_list.cCLIENT_TYPE_SMIP, moteID=iComox.moteID, macAddress=iComox.macAddress, state=Dongle_Communication.MOTE_STATE_OPERATIONAL, isRouting=iComox.isRouting)
                iComox.state = Dongle_Communication.MOTE_STATE_OPERATIONAL
                current_time = datetime.datetime.now()
                if (iComox is not None) and ((iComox.HelloRequestTime is None) or ((current_time-iComox.HelloRequestTime).total_seconds() > 30)):
                    self.send_msg(msg=iCOMOX_messages.OUT_MSG_Hello(), iComox=iComox)
                    iComox.HelloRequestTime = current_time
                else:
                    helpers.OUT("Request hello message was not sent")

        # common.app.TopPane.cb_smip.configure(values=iCOMOXs_list)
        # helpers.cb_adjust_dropbox_width(combo=common.app.TopPane.cb_smip)
        # common.app.StatusBar.set(text="iCOMOX dongle list was updated. It now contains {} elements".format(len(iCOMOXs_list)))

    def on_tcpip_state_changed(self, tcpState, iComox=None):
        if tcpState == TCP_connectivity.cTCP_STATE_DISCONNECTED:
            common.app.drawConnectionState(connected=False, listen=False)
            common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Disconnect)
            common.app.Clients.delete_all()
        elif tcpState == TCP_connectivity.cTCP_STATE_LISTEN:
            common.app.drawConnectionState(connected=False, listen=True)
            common.app.drawLedState(connection_state=CONNECTION_STATE_TcpIp_ServerConnected)
            common.app.Clients.deleteZombieClients()
        elif tcpState == TCP_connectivity.cTCP_STATE_CLIENT_DISCONNECTED:
            common.app.Clients.delete(iComox=iComox)
        elif tcpState == TCP_connectivity.cTCP_STATE_CLIENT_CONNECTED:
            common.app.drawConnectionState(connected=False, listen=True)
            # common.app.drawLedState(connection_state=CONNECTION_STATE_TcpIp_ClientConnected)
            self.send_msg(msg=iCOMOX_messages.OUT_MSG_Hello(), iComox=iComox)
        elif tcpState == TCP_connectivity.cTCP_STATE_iCOMOX_CONNECTED:
            common.app.drawConnectionState(connected=True, listen=True)
            common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Connected_via_TcpIp)
            common.app.Clients.insert(iComox=iComox)
            common.app.Clients.deleteZombieClients()

    def send_msg(self, msg, iComox=None):
        if iComox is None:
            iComox = common.iCOMOXs.current
            if iComox is None:
                helpers.OUT("send_msg(): iComox is None and the current iCOMOX is None too")
                # raise Exception("send_msg(): iComox is None and the current iCOMOX is None too")
                return

        if iComox.Type == iCOMOX_list.cCLIENT_TYPE_USB:
            if (self.iCOMOX_Comm is not None) and (self.iCOMOX_Comm.is_open()):
                self.iCOMOX_Comm.write(msg)
        elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_SMIP:
            if (self.Dongle_Comm is not None) and (self.Dongle_Comm.is_open()):
                self.Dongle_Comm.send_message_to_iCOMOX(macAddress=iComox.macAddress, msg=msg)
        elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP:
            iComox.transmit_buffer += msg

    # def icomox_set_configuration(self, ConfigBitmask = iCOMOX_messages.cCOMOX_CONFIG_BITMASK_AbsoluteTime | iCOMOX_messages.cCOMOX_CONFIG_BITMASK_Common | iCOMOX_messages.cCOMOX_CONFIG_BITMASK_Modules, Common=0, ConfigBitmask=0, RawDataSensors=0, AnomalyDetection_Sensors=0, AnomalyDetection_StateToTrain=0):
    #     self.send_msg(iCOMOX_messages.OUT_MSG_SetConfiguration(
    #         ConfigBitmask=ConfigBitmask,
    #         Common=Common,
    #         ConfigBitmask=ConfigBitmask,
    #         LocalTimestamp=int(time.time() + (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()), # mktime(time.localtime()))
    #         RawData_Sensors=RawDataSensors, Repetition=0xFF, IntervalInMinutes=0xFFFF,
    #         AnomalyDetection_Sensors=AnomalyDetection_Sensors, AnomalyDetection_StateToTrain=AnomalyDetection_StateToTrain
    #     ))

    def USB_on_process_messages(self, msg, CommPort=None):
        if CommPort is None:
            raise Exception("USB_on_process_messages(): CommPort is None")
        iComox = common.iCOMOXs.find_by_CommPort(CommPort=CommPort)
        if iComox is not None:
            self.on_process_messages(msg=msg, iComox=iComox)

    def on_process_messages(self, msg, iComox=None):
        if iComox is None:
            raise Exception("on_process_messages(): iComox is None")

        if msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Report:    # Reports are kept to be processed by the idle task
            index = msg[1]
            # if iComox.Reports[index] is None:
            iComox.Reports[index] = msg

        else:
            if msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Hello:
                iComox.Hello = msg
                if iComox.Type == iCOMOX_list.cCLIENT_TYPE_USB:
                    pass
                elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_SMIP:
                    self.on_dongle_updated_iCOMOX_list()
                elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP:
                    common.app.Clients.insert(iComox=iComox)

            self.process_incoming_msg(msg=msg, iComox=iComox)   # Non report messages are processed immediately

    def process_report_messages_of_current_iCOMOX(self):
        current = common.iCOMOXs.current
        if current is None:
            return
        Reports = current.Reports
        if Reports is None:
            return
        for index in [*filter(lambda i : Reports[i] is not None, range(0, 256))]:
            self.process_incoming_msg(msg=Reports[index], iComox=current)
            Reports[index] = None
            # common.iCOMOXs.current.Reports[index] = None    # Mark on_process_messages() that it can push another report of the same kind

        # if common.iCOMOXs.current is None:
        #     return
        # if common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_USB:
        #     pass
        # elif common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_SMIP:
        #     #if (common.iCOMOXs.current.macAddress is not None) and (self.Dongle_Comm is not None):
        #     pass
        # elif common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP:
        #     pass
        # else:
        #     raise Exception("process_report_messages_of_current_iCOMOX: Invalid Type")

    # def schedule_callback(self):
    #     channel = common.app.get_current_report_channel()
    #     if channel < 0:
    #         self.schedule_state_no_reports = True
    #         self.schedule_callback_time = 0
    #         self.after_ID = None
    #     else:
    #         minutes_duration_in_secs = float(common.app.Configuration.time.get()) * 60
    #         if self.schedule_state_no_reports:
    #             reports = None  # Request GUI selected sensors data from iCOMOX
    #             self.schedule_callback_time += minutes_duration_in_secs
    #         else:
    #             reports = 0     # Stop sending RawDataSensors from the iCOMOX
    #             hours_period_in_secs = float(common.app.Configuration.schedule.get()) * 3600
    #             self.schedule_callback_time += hours_period_in_secs - minutes_duration_in_secs
    #
    #         self.schedule_state_no_reports = not self.schedule_state_no_reports
    #         # self.set_configuration_from_GUI(channel=channel, RawDataSensors=RawDataSensors)
    #         if reports is None:
    #             helpers.OUT("schedule_callback: start RawDataSensors")
    #         else:
    #             helpers.OUT("schedule_callback: stop RawDataSensors")
    #         self.after_ID = common.app.after(int(1000*(self.schedule_callback_time - time.time())), self.schedule_callback)
    #
    # def schedule_stop(self):
    #     if self.after_ID is not None:
    #         common.app.after_cancel(id=self.after_ID)
    #     self.after_ID = None
    #     self.schedule_state_no_reports = True
    #     self.schedule_callback_time = 0
    #
    # def schedule_start(self):
    #     self.schedule_stop()
    #     if common.app.Configuration.stream_schedule.get() == 2:     # GUI - on schedule
    #         self.schedule_callback_time = time.time()
    #         self.schedule_callback()
    #         return True     # iCOMOX configuration is set by this function
    #     else:
    #         return False    # iCOMOX configuration is not set by this function

    def process_incoming_msg(self, msg, iComox=None):
        if (iComox is None) or (iComox != common.iCOMOXs.current):
            return

        def cloud_start():
            if common_symbols.IOTC_enabled:
                self.iot.cloud_update_start()
            if common_symbols.__REST_SUPPORT__:
                self.http.cloud_update_start()

        if iComox == common.iCOMOXs.current:
            if common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_USB:
                # common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Connected)
                pass
            elif common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_SMIP:
                # if (common.iCOMOXs.current.macAddress is not None) and (self.Dongle_Comm is not None):
                # if common.app.TopPane.cb_smip.current() >= 0:
                #     common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Connected_via_Dongle)
                #     cloud_start()
                # else:
                #     common.app.drawLedState(connection_state=CONNECTION_STATE_Dongle_Disconnected)
                pass
            elif common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP:
                pass

            else:
                raise Exception("process_report_messages_of_current_iCOMOX: Invalid Type")
            cloud_start()

        # serial communication schedule_no_activity_event()
        msg_code = msg[0]
        if msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_Hello:
            # Extract the sCOMOX_IN_MSG_Hello fields
            hello_board_type, \
            hello_board_version_major, hello_board_version_minor, \
            hello_mcu_serial_number, \
            hello_firmware_release_version_major, hello_firmware_release_version_minor, hello_firmware_release_version_patch, hello_firmware_release_version_branch, \
            hello_firmware_build_version_date_year, hello_firmware_build_version_date_month, hello_firmware_build_version_date_day, \
            hello_firmware_build_version_time_hour, hello_firmware_build_version_time_minute, hello_firmware_build_version_time_second, \
            hello_bit_status, \
            hello_product_part_number, hello_production_serial_number, hello_name, \
            smip_swMajor, smip_swMinor, smip_swPatch, smip_swBuild = iCOMOX_messages.IN_MSG_Hello(msg=msg)

            hello_firmware_release_version = (hello_firmware_release_version_major << 16) + (hello_firmware_release_version_minor << 8) + hello_firmware_release_version_patch
            if common_symbols.__PRODUCTION_SUPPORT__ or ((hello_firmware_release_version & 0xFFFF00) == (common_symbols.__VERSION_CODE__ & 0xFFFF00)):
                iComox.Hello = msg
                common.app.TopPane.update_iCOMOX_name(hello=msg)
                common.app.EnableButtons(
                    liveDataTab=True,
                    configurationTab=True,
                    diagnosticTab=(common.iCOMOXs.current is not None) and (common.iCOMOXs.current.Type == iCOMOX_list.cCLIENT_TYPE_USB) and (common.iCOMOXs.current.board_type() == iCOMOX_messages.cCOMOX_BOARD_TYPE_NB_IOT),
                    eepromTab=True,
                    clientsTab=(common.iCOMOXs.current is not None) and (common.iCOMOXs.current.Type != iCOMOX_list.cCLIENT_TYPE_USB))
                # common.app.EnableButtons(configurationTab=iComox is None, eepromTab=iComox is None, clientsTab=iComox is not None)
                # update the information tabsheet of the main window
                common.app.Information.update_iCOMOX_version(board_type=hello_board_type, \
                    board_version_major=hello_board_version_major, board_version_minor=hello_board_version_minor, \
                    mcu_serial_number=hello_mcu_serial_number, \
                    firmware_release_version_major=hello_firmware_release_version_major, firmware_release_version_minor=hello_firmware_release_version_minor, firmware_release_version_patch=hello_firmware_release_version_patch, firmware_release_version_branch=hello_firmware_release_version_branch, \
                    firmware_build_version_year=hello_firmware_build_version_date_year, firmware_build_version_month=hello_firmware_build_version_date_month, firmware_build_version_day=hello_firmware_build_version_date_day, firmware_build_version_hour=hello_firmware_build_version_time_hour, firmware_build_version_min=hello_firmware_build_version_time_minute, firmware_build_version_sec=hello_firmware_build_version_time_second, \
                    bit_status=hello_bit_status, \
                    product_part_number=hello_product_part_number, production_serial_number=hello_production_serial_number, name=hello_name, \
                    smip_swMajor=smip_swMajor, smip_swMinor=smip_swMinor, smip_swPatch=smip_swPatch, smip_swBuild=smip_swBuild, \
                    icomox_version_available=True)

                # create log file
                BoardVersionStr = messages_utils.iCOMOX_BoardVersion_to_Str(board_version_major=hello_board_version_major, board_version_minor=hello_board_version_minor)
                self.logfile_info = [
                    "Log file format version: 1.3",
                    "Board type: {}".format(messages_utils.iCOMOX_BoardType_to_Str(hello_board_type)),
                    "Board version: {}".format(BoardVersionStr),
                    "MCU serial number: {:^32}".format(helpers.u8s_to_str(arr=hello_mcu_serial_number, separator="")),
                    "Firmware release version: {}.{}.{} {}".format(hello_firmware_release_version_major,
                                                                   hello_firmware_release_version_minor,
                                                                   hello_firmware_release_version_patch,
                                                                   messages_utils.iCOMOX_firmware_release_version_branch_to_Str(hello_firmware_release_version_branch)),
                    "Firmware build version: {:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(
                        hello_firmware_build_version_date_day, hello_firmware_build_version_date_month, hello_firmware_build_version_date_year,
                        hello_firmware_build_version_time_hour, hello_firmware_build_version_time_minute, hello_firmware_build_version_time_second
                    ),
                    "Production serial number: {}".format(helpers.bytearrayToString(hello_production_serial_number)),
                    "Part number: {}".format(helpers.bytearrayToString(hello_product_part_number)),
                    "Name: {}".format(helpers.bytearrayToString(hello_name)),
                    "BIT state: 0x{:02X}".format(hello_bit_status)
                ]
                if hello_board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_SMIP:
                    self.logfile_info.append("SmartMesh software version: {}.{}.{}.{}".format(smip_swMajor, smip_swMinor, smip_swPatch, smip_swBuild))
                elif hello_board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_NB_IOT:
                    self.logfile_info.append("NB-IoT test: 0x{:02X}".format(smip_swMajor))

                if BoardVersionStr == "":
                    del self.logfile_info[2]    # Remove the "Board version" element

                common.app.Configuration.Workbook_UpdateID(logfile_info=self.logfile_info)
                if common_symbols.IOTC_enabled:
                    self.iot.add_device(hello_mcu_serial_number)
                if common_symbols.__REST_SUPPORT__:
                    self.http.add_device(hello_mcu_serial_number)
                helpers.OUT("Processed hello message successfully")

                iComox.Hello = msg
                common.iCOMOXs.current = iComox
                # iComox.UniqueID = hello_mcu_serial_number
                # iComox.board_type = hello_board_type
                #if (self.schedule_callback_time == 0) and (iComox is None): # Set Configuration is automatically sent only for non TCP/IP
                    # if not self.schedule_start():
                if iComox.Type == iCOMOX_list.cCLIENT_TYPE_USB:
                    common.app.Configuration.SetConfiguration()
                    # self.set_configuration_from_GUI(channel=channel)
                    common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Connected)
                elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_SMIP:
                    common.app.drawLedState(connection_state=CONNECTION_STATE_iCOMOX_Connected_via_Dongle)
                elif iComox.Type == iCOMOX_list.cCLIENT_TYPE_TCPIP:
                    common.app.iCOMOX_Data.TcpIp_Comm.state_changed(tcpState=TCP_connectivity.cTCP_STATE_iCOMOX_CONNECTED, iComox=iComox)

            else:
                if iComox == common.iCOMOXs.current:
                    common.app.Information.update_iCOMOX_version(icomox_version_available=False)
                    common.app.StatusBar.set(text="Please update the iCOMOX firmware")
                    common.app.EnableButtons(liveData=False, diagnosticTab=False, configurationTab=False, eepromTab=False, clientsTab=False)
                    helpers.OUT("Mismatch iCOMOX firmware version: {}.{}.{}".format(hello_firmware_release_version_major, hello_firmware_release_version_minor, hello_firmware_release_version_patch))

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_Reset:
            if iComox == common.iCOMOXs.current:
                helpers.OUT("IN_MSG_Reset message\n")
            common.app.StatusBar.set(text="Received Reset response")

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_GetConfiguration:
            if iComox == common.iCOMOXs.current:
                common.app.Configuration.MsgToWindow(getConfigurationInMsg=msg)
            common.app.StatusBar.set(text="Received GetConfiguration response")

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_SetConfiguration:
            if iComox == common.iCOMOXs.current:
                result = iCOMOX_messages.IN_MSG_SetConfiguration(msg=msg)
                errStr = "Received SetConfiguration response " + messages_utils.eCOMOX_RESULT_to_Str(eCOMOX_RESULT=result)
                common.app.StatusBar.set(text=errStr)

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_ReadEEPROM:
            if iComox == common.iCOMOXs.current:
                count, address, result, data = struct.unpack_from("<BHB{}s".format(iCOMOX_messages.M24C64_PAGE_BYTE_SIZE), msg, 1)
                if result != 0:
                    result = common.app.EEPROM.cSTATE_ERROR
                else:
                    result = common.app.EEPROM.cSTATE_OK
                common.app.EEPROM.ReadEEPROM_callback(nextState=result, data=data)

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_WriteEEPROM:
            if iComox == common.iCOMOXs.current:
                count, address, result = struct.unpack_from("<BHB", msg, 1)
                if result != 0:
                    result = common.app.EEPROM.cSTATE_ERROR
                else:
                    result = common.app.EEPROM.cSTATE_OK
                common.app.EEPROM.ProgramEEPROM_callback(nextState=result)

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_VerifyEEPROM:
            if iComox == common.iCOMOXs.current:
                count, address, result = struct.unpack_from("<BHB", msg, 1)
                if result != 0:
                    result = common.app.EEPROM.cSTATE_ERROR
                else:
                    result = common.app.EEPROM.cSTATE_OK
                common.app.EEPROM.VerifyEEPROM_callback(nextState=result)

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_Debug:
            if iComox == common.iCOMOXs.current:
                if iComox.board_type() == iCOMOX_messages.cCOMOX_BOARD_TYPE_NB_IOT:
                    Cmd, Result = iCOMOX_messages.IN_MSG_Debug(msg=msg)
                    # common.app.DiagnosticMode.NBIOT_UpdateResponse(payload=payload)
                    errStr = "Received Debug.NB-IoT response with result code: {} for command: '{}'".format(Result, messages_utils.eCOMOX_DEBUG_NBIOT_CMD_to_Str(Cmd))
                    common.app.StatusBar.set(text=errStr)

        elif msg_code == iCOMOX_messages.cCOMOX_MSG_CODE_Report:
            if iComox == common.iCOMOXs.current:
                module, sensor, axis, timestamp = iCOMOX_messages.IN_MSG_Report(msg=msg)
                payload = msg[10:]
                UniqueID = iComox.UniqueID()

                if module == iCOMOX_messages.cMODULE_RawData:
                    if iCOMOX_messages.cCOMOX_SENSOR_ADXL362 == sensor:
                        acc_x_units_g, acc_y_units_g, acc_z_units_g = common.ADXL362.msg_bytes_to_samples_g(payload=payload)

                        freq_Acc, Pxxf_AccX = common.ADXL362.g_units_to_PSD(acc_units_g=acc_x_units_g)
                        Pxxf_AccX_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccX)
                        freq_Acc, Pxxf_AccY = common.ADXL362.g_units_to_PSD(acc_units_g=acc_y_units_g)
                        Pxxf_AccY_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccY)
                        freq_Acc, Pxxf_AccZ = common.ADXL362.g_units_to_PSD(acc_units_g=acc_z_units_g)
                        Pxxf_AccZ_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccZ)

                        # Add the new statistics to the statistics logger
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_lowpower_acc_x, new_samples=acc_x_units_g)
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_lowpower_acc_y, new_samples=acc_y_units_g)
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_lowpower_acc_z, new_samples=acc_z_units_g)

                        # Update the statistics pane in the GUI
                        common.app.Statistics.update_lowpower_acc()
                        # live data pane
                        common.app.LiveData.update_lowpower_acc_plot_data(freq_Acc=freq_Acc, Pxxf_Acc_X_dBg=Pxxf_AccX_dBg, Pxxf_Acc_Y_dBg=Pxxf_AccY_dBg, Pxxf_Acc_Z_dBg=Pxxf_AccZ_dBg)
                        common.app.LiveData.update_lowpower_acc_plot()

                        # log file
                        time_ns_acquired = time.time_ns()
                        common.app.Configuration.Workbook_Update_ADXL362(time_ns_acquired=time_ns_acquired, acc_x_units_g=acc_x_units_g, acc_y_units_g=acc_y_units_g, acc_z_units_g=acc_z_units_g)

                        # Update the cloud
                        if UniqueID is not None:
                            if common_symbols.IOTC_enabled:
                                iot_device = self.iot.device_by_uniqueID(UniqueID)
                                if iot_device is not None:
                                    iot_device.update_max_abs_acc(axis=axis, max_abs_acc_x=np.absolute(acc_x_units_g).max(), max_abs_acc_y=np.absolute(acc_y_units_g).max(), max_abs_acc_z=np.absolute(acc_z_units_g).max())
                                    # iot_device.update_acc_field(axis=axis, data=acc_units_g)
                            if common_symbols.__REST_SUPPORT__:
                                http_device = self.http.device_by_uniqueID(UniqueID)
                                if http_device is not None:
                                    http_device.update_max_abs_acc(axis=axis, max_abs_acc=np.absolute(acc_x_units_g).max())
                                    http_device.update_acc_field(axis=axis, data=payload)

                    elif iCOMOX_messages.cCOMOX_SENSOR_ADXL356 == sensor:
                        if iComox.board_type() is None:
                            self.send_msg(msg=iCOMOX_messages.OUT_MSG_Hello(), iComox=iComox)
                            return
                        if iComox.board_type() == iCOMOX_messages.cCOMOX_BOARD_TYPE_SMIP:
                            acc_units_g = common.ADXL356_SMIP.msg_bytes_to_samples_g(payload=payload)

                            # The formula I deduced from the datasheet:
                            #  temp_data = np.array(temp_data) * 1.8 / (4096 * 3E-3) + (0 - 892.2E-3/3E-3)
                            #  I expect 25 instead of 0 in the formula, but it gives incorrect results
                            # This formula was used by Anton:
                            #  temp_data = np.array(temp_data) / (2 ** 12 * 1.8 * 25 / 0.892)    # ADXL356 temperature data

                            # *********** GUI feedback ****************

                            freq_Acc, Pxxf_Acc = common.ADXL356_SMIP.g_units_to_PSD(acc_units_g=acc_units_g)
                            Pxxf_Acc_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_Acc)

                            # Add the new statistics to the statistics logger
                            if axis == iCOMOX_messages.cAXIS_X:
                                common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_acc_x, new_samples=acc_units_g)
                            elif axis == iCOMOX_messages.cAXIS_Y:
                                common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_acc_y, new_samples=acc_units_g)
                            else:
                                common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_acc_z, new_samples=acc_units_g)

                            # Update the statistics pane in the GUI
                            common.app.Statistics.update_acc()

                            # live data pane
                            common.app.LiveData.update_acc_plot_data(freq_Acc=freq_Acc, axis=axis, Pxxf_Acc_dBg=Pxxf_Acc_dBg)
                            common.app.LiveData.update_acc_plot()

                            # log file
                            common.app.Configuration.Workbook_Update_ADXL356(time_ns_acquired=time.time_ns(), axis=axis, acc_units_g=acc_units_g, adxl356_smip=True)

                            # Update the cloud
                            if UniqueID is not None:
                                if common_symbols.IOTC_enabled:
                                    iot_device = self.iot.device_by_uniqueID(UniqueID)
                                    if iot_device is not None:
                                        iot_device.update_max_abs_acc(axis=axis, max_abs_acc=np.absolute(acc_units_g).max())
                                        # iot_device.update_acc_field(axis=axis, data=acc_units_g)
                                if common_symbols.__REST_SUPPORT__:
                                    http_device = self.http.device_by_uniqueID(UniqueID)
                                    if http_device is not None:
                                        http_device.update_max_abs_acc(axis=axis, max_abs_acc=np.absolute(acc_units_g).max())
                                        http_device.update_acc_field(axis=axis, data=payload)

                        else:       # ADXL356 report in NBIOT & POE includes all the axis in the same report message
                            acc_x_units_g, acc_y_units_g, acc_z_units_g = common.ADXL356.msg_bytes_to_samples_g(payload=payload)

                            freq_Acc, Pxxf_AccX = common.ADXL356.g_units_to_PSD(acc_units_g=acc_x_units_g)
                            Pxxf_AccX_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccX)
                            freq_Acc, Pxxf_AccY = common.ADXL356.g_units_to_PSD(acc_units_g=acc_y_units_g)
                            Pxxf_AccY_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccY)
                            freq_Acc, Pxxf_AccZ = common.ADXL356.g_units_to_PSD(acc_units_g=acc_z_units_g)
                            Pxxf_AccZ_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccZ)

                            #self.max_acc = (freq_Acc[1:])[np.argmax(Pxxf_AccZ[1:])] #- freq_Acc[1]

                            # Add the new statistics to the statistics logger
                            common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_acc_x, new_samples=acc_x_units_g)
                            common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_acc_y, new_samples=acc_y_units_g)
                            common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_acc_z, new_samples=acc_z_units_g)

                            # Update the statistics pane in the GUI
                            common.app.Statistics.update_acc()

                            # live data pane
                            common.app.LiveData.update_acc_plot_data(freq_Acc=freq_Acc, axis=iCOMOX_messages.cAXIS_X, Pxxf_Acc_dBg=Pxxf_AccX_dBg)
                            common.app.LiveData.update_acc_plot_data(freq_Acc=freq_Acc, axis=iCOMOX_messages.cAXIS_Y, Pxxf_Acc_dBg=Pxxf_AccY_dBg)
                            common.app.LiveData.update_acc_plot_data(freq_Acc=freq_Acc, axis=iCOMOX_messages.cAXIS_Z, Pxxf_Acc_dBg=Pxxf_AccZ_dBg)
                            common.app.LiveData.update_acc_plot()

                            # log file
                            time_ns_acquired = time.time_ns()
                            common.app.Configuration.Workbook_Update_ADXL356(time_ns_acquired=time_ns_acquired, axis=iCOMOX_messages.cAXIS_X, acc_units_g=acc_x_units_g, adxl356_smip=False)
                            common.app.Configuration.Workbook_Update_ADXL356(time_ns_acquired=time_ns_acquired, axis=iCOMOX_messages.cAXIS_Y, acc_units_g=acc_y_units_g, adxl356_smip=False)
                            common.app.Configuration.Workbook_Update_ADXL356(time_ns_acquired=time_ns_acquired, axis=iCOMOX_messages.cAXIS_Z, acc_units_g=acc_z_units_g, adxl356_smip=False)

                    elif iCOMOX_messages.cCOMOX_SENSOR_BMM150 == sensor:
                        mag_x_data, mag_y_data, mag_z_data = common.BMM150.msg_bytes_to_samples_uTesla(payload=payload)

                        # mag_x_data -= np.mean(mag_x_data)

                        freq_mag, Pxxf_Mag_X, Pxxf_Mag_Y, Pxxf_Mag_Z = common.BMM150.to_PSD(mag_x_uT=mag_x_data, mag_y_uT=mag_y_data, mag_z_uT=mag_z_data)

                        Pxxf_Mag_X_dB = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_Mag_X)
                        Pxxf_Mag_Y_dB = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_Mag_Y)
                        Pxxf_Mag_Z_dB = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_Mag_Z)

                        noise_level_X_dB = np.quantile(Pxxf_Mag_X_dB, common_symbols.BMM150_quantile_for_noise_floor_estimator)
                        noise_level_Y_dB = np.quantile(Pxxf_Mag_Y_dB, common_symbols.BMM150_quantile_for_noise_floor_estimator)
                        noise_level_Z_dB = np.quantile(Pxxf_Mag_Z_dB, common_symbols.BMM150_quantile_for_noise_floor_estimator)

                        # Calculate the speed according to the magnetic field PSD's peak, in the chosen axis
                        plot_index = common.app.LiveData.axis_magPlot.get()
                        if plot_index == iCOMOX_messages.cAXIS_X:
                            mag = mag_x_data
                        elif plot_index == iCOMOX_messages.cAXIS_Y:
                            mag = mag_y_data
                        else:
                            mag = mag_z_data

                        self.network_frequency_Hz = common.BMM150.maximum_of_PSD(mag)   # "network" frequency is the one that provided by the rotor's controller (manually adjustable by the user)
                        synchronous_frequency_Hz = self.network_frequency_Hz / common_symbols.ASYNC_MOTOR_number_of_poles_pairs # the frequency of the rotating magnetic field that induces torque on the rotor
                        rotor_frequency_Hz = synchronous_frequency_Hz * (1-common_symbols.ASYNC_MOTOR_slip_factor_percentages/100)  # the actual rotor's frequency when considering the slip factor (constant load)
                        # speed gauge in live data
                        common.app.LiveData.speed_widget.set_value(rotor_frequency_Hz * 60) # convert the rotor frequency from Hz to RPM

                        # live data pane
                        common.app.LiveData.update_mag_plot_data(freq_mag, Pxxf_Mag_X_dB, Pxxf_Mag_Y_dB, Pxxf_Mag_Z_dB, noise_level_X_dB, noise_level_Y_dB, noise_level_Z_dB)
                        common.app.LiveData.update_mag_plot()

                        # Add the new statistics to the statistics logger
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_mag_x, new_samples=mag_x_data)
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_mag_y, new_samples=mag_y_data)
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_mag_z, new_samples=mag_z_data)

                        # Update the statistics pane in the GUI
                        common.app.Statistics.update_mag()

                        # log file
                        common.app.Configuration.Workbook_Update_BMM150(time_ns_acquired=time.time_ns(), mag_x_units_tesla=mag_x_data, mag_y_units_tesla=mag_y_data, mag_z_units_tesla=mag_z_data)

                        # Update the cloud
                        if UniqueID is not None:
                            if common_symbols.IOTC_enabled:
                                iot_device = self.iot.device_by_uniqueID(UniqueID)
                                if iot_device is not None:
                                    iot_device.update_motor_speed(motor_speed=self.network_frequency_Hz)
                            #         samples = struct.unpack("<{}h".format(iCOMOX_messages.BMM150_SAMPLES_NUM * 3), msg[2:])
                            #         iot_device.update_magnetic_field(axis=iCOMOX_messages.cAXIS_X, data=mag_x_data)
                            #         iot_device.update_magnetic_field(axis=iCOMOX_messages.cAXIS_Y, data=mag_y_data)
                            #         iot_device.update_magnetic_field(axis=iCOMOX_messages.cAXIS_Z, data=mag_z_data)
                            if common_symbols.__REST_SUPPORT__:
                                http_device = self.http.device_by_uniqueID(UniqueID)
                                if http_device is not None:
                                    http_device.update_motor_speed(motor_speed=self.network_frequency_Hz)
                                    http_device.update_magnetic_field(axis=iCOMOX_messages.cAXIS_X, data=mag_x_data)
                                    http_device.update_magnetic_field(axis=iCOMOX_messages.cAXIS_Y, data=mag_y_data)
                                    http_device.update_magnetic_field(axis=iCOMOX_messages.cAXIS_Z, data=mag_z_data)

                    elif iCOMOX_messages.cCOMOX_SENSOR_ADT7410 == sensor:
                        temp_data = common.ADT7410.msg_bytes_to_sample_Celsius(payload=payload)

                        common.app.LiveData.temp_widget.display(round(temp_data, 2))

                        # Add the new statistics to the statistics logger
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_temp, new_samples=[temp_data])
                        common.app.Statistics.update_temp()  # Update the statistics pane in the GUI
                        common.app.Configuration.Workbook_Update_ADT7410(time_ns_acquired=time.time_ns(), temp_unit_celsius=temp_data)

                        # Update the cloud
                        if UniqueID is not None:
                            if common_symbols.IOTC_enabled:
                                iot_device = self.iot.device_by_uniqueID(UniqueID)
                                if iot_device is not None:
                                    iot_device.update_temp(temp=temp_data)
                            if common_symbols.__REST_SUPPORT__:
                                http_device = self.http.device_by_uniqueID(UniqueID)
                                if http_device is not None:
                                    http_device.update_temp(temp=temp_data)

                    elif iCOMOX_messages.cCOMOX_SENSOR_IM69D130 == sensor:
                        samples_SPL = common.IM69D130.msg_bytes_to_samples_SPL(payload=payload)

                        # time domain display
                        #time_Mic = np.array(range(0, 1290)) * 1E3 / common.IM69D130.Fs_Mic
                        #samples_SPL = np.array(report_data) * 2800
                        #samples_SPL = samples_SPL - np.min(samples_SPL)
                        #samples_SPL_dB = 2*self.PSD_linear_to_logarithmic(Pxxf=samples_SPL)
                        #common.app.LiveData.PlotMicFFT.updatePlot(time_Mic, samples_SPL_dB)

                        freq_Mic, Pxxf_Mic = common.IM69D130.to_PSD(mic_units_spl=samples_SPL)
                        Pxxf_Mic_dB = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_Mic)
                        common.app.LiveData.PlotMicFFT.updatePlot(freq_Mic, Pxxf_Mic_dB)

                        # mean and standard deviation on logarithmic data
                        # this is done in order to prevent a "negative" (dB) value of the standard deviation
                        # (which is absolutely correct mathematically)
                        RMS_value_of_microhpne = [np.sqrt(np.sum(samples_SPL ** 2)/len(samples_SPL))]
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_mic, new_samples=RMS_value_of_microhpne)
                        common.app.Statistics.update_mic()  # Update the statistics pane in the GUI

                        common.app.Configuration.Workbook_Update_IM69D130(time_ns_acquired=time.time_ns(), sound_units_SPL=samples_SPL)

                        # # Update the cloud
                        # if UniqueID is not None:
                        #     if common_symbols.IOTC_enabled:
                        #         iot_device = self.iot.device_by_uniqueID(UniqueID)
                        #         if iot_device is not None:
                        #             iot_device.update_microphone_field(data=samples_SPL)
                        # if common_symbols.__REST_SUPPORT__:
                        #     http_device = self.http.device_by_uniqueID(UniqueID)
                        #     if http_device is not None:
                        #         http_device.update_microphone(data=samples_SPL)

                    elif iCOMOX_messages.cCOMOX_SENSOR_ADXL1002 == sensor:
                        acc_x_units_g = common.ADXL1002.msg_bytes_to_samples_g(payload=payload)

                        freq_Acc, Pxxf_AccX = common.ADXL1002.g_units_to_PSD(acc_units_g=acc_x_units_g)
                        Pxxf_AccX_dBg = self.PSD_linear_to_logarithmic(Pxxf=Pxxf_AccX)

                        # Add the new statistics to the statistics logger
                        common.app.statisticsLogger.update_statistics(data_arr_index=statistics_data_logger.stat_data_logger_index_wideband_acc_x, new_samples=acc_x_units_g)

                        # Update the statistics pane in the GUI
                        common.app.Statistics.update_wideband_acc()

                        # live data pane
                        common.app.LiveData.update_wideband_acc_plot_data(freq_Acc=freq_Acc, Pxxf_Acc_dBg=Pxxf_AccX_dBg)
                        # common.app.LiveData.update_wideband_acc_plot_data(freq_Acc=1/common.ADXL1002.Fs_Acc*np.array(range(0, iCOMOX_messages.ADXL1002_SAMPLES_NUM)), Pxxf_Acc_dBg=50*acc_x_units_g/3)
                        common.app.LiveData.update_wideband_acc_plot()

                        # log file
                        time_ns_acquired = time.time_ns()
                        common.app.Configuration.Workbook_Update_ADXL1002(time_ns_acquired=time_ns_acquired, acc_units_g=acc_x_units_g)

                    else:  # Illegal payload in IN_MSG_Report, but we should NEVER arrive to this point
                        helpers.OUT("Unknown report payload = 0x{:02X}".format(sensor))

                elif module == iCOMOX_messages.cMODULE_AnomalyDetection:
                    ValAnomaly, probState, ReportStatus, Sensors, Result = iCOMOX_messages.IN_MSG_REPORT_AnomalyDetection(payload=payload)
                    common.app.LiveData.AnomalyDetection_Report_Handler(ValAnomaly=ValAnomaly, probState=probState, ReportStatus=ReportStatus, Sensors=Sensors, Result=Result)

                elif module == iCOMOX_messages.cMODULE_Maintenance:
                    BasicStats, AlertsMagnitudes,  MotorOnTimeSec, TotalTimeSec, SyncSpeed, MotorSpeed, MinAlerts, MaxAlerts, IsMotorOn = iCOMOX_messages.IN_MSG_REPORT_Maintenance(msg=msg)

                elif module == iCOMOX_messages.cMODULE_Debug:
                    if iComox.board_type() == iCOMOX_messages.cCOMOX_BOARD_TYPE_NB_IOT:
                        common.app.DiagnosticMode.NBIOT_UpdateResponse(payload=iCOMOX_messages.IN_MSG_REPORT_Debug(payload=payload))
                        command = axis          # For IN_MSG_REPOR_Debug the iCOMOX_messages.IN_MSG_Report returns command in axis and last_packet in sensor
                        last_packet = sensor
                        statusStr = "Received report of NB-IoT test connectivity {}packet".format("last " if last_packet else "")
                        common.app.StatusBar.set(text=statusStr)

                else:   # Illegal module
                    helpers.OUT("Unknown module")

        else:  # Illegal message, but we should NEVER arrive to this point
            helpers.OUT("Invalid message code {}".format(msg_code))

    def on_no_activity(self, comm):
        if self.comm.is_open():
            self.comm.write(iCOMOX_messages.OUT_MSG_Hello())
            helpers.OUT("on_no_activity: Sent Hello request")
            #   schedule_no_activity_event()


    #def cancel_no_activity_event():
    #    global hEvent, hEventCallback
    #    if hEventCallback is not None:
    #        hEvent.cancel(hEventCallback)


    #def schedule_no_activity_event():
    #    global hEvent, hEventCallback
    #    cancel_no_activity_event()
    #    hEventCallback = hEvent.enter(iCOMOX_messages.NO_REPORT_TIMEOUT_SEC, 1, on_no_activity)
