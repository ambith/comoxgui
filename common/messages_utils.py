import iCOMOX_messages


# on_get_in_message_size(accumulated_msg)
# Parameter: accumulated_msg - byte array, the message that was accumulated so far
# Return: 0 - if no more bytes are needed to complete the message
#         positive number - number of bytes that are needed to complete the message
#         negative number - invalid message detected
def on_get_in_message_size(accumulated_msg, adxl356_smip=False):
    if len(accumulated_msg) == 0:  # if no byte was accumulated so far, then we need the IN_MSG_xxx.Code field
        return 1
    elif (accumulated_msg[0] > iCOMOX_messages.cCOMOX_MSG_CODE_COUNT) and (accumulated_msg[0] != iCOMOX_messages.cCOMOX_MSG_CODE_Report):
        return -1   # Invalid message code
    else:
        if accumulated_msg[0] < iCOMOX_messages.cCOMOX_MSG_CODE_COUNT:
            min_msg_size = iCOMOX_messages.COMOX_IN_MSG_SIZE[accumulated_msg[0]]
        else:
            min_msg_size = iCOMOX_messages.COMOX_IN_MSG_REPORT_HEADER_SIZE
        if len(accumulated_msg) < min_msg_size:
            return min_msg_size - len(accumulated_msg)
        elif accumulated_msg[0] != iCOMOX_messages.cCOMOX_MSG_CODE_Report:
            # Check if sCOMOX_IN_MSG_Debug.Cmd has a valid value
            if accumulated_msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Debug:
                Cmd, Result = iCOMOX_messages.IN_MSG_Debug(msg=accumulated_msg)
                if Cmd > iCOMOX_messages.cCOMOX_DEBUG_NBIOT_CMD_TestConnectivity:
                    return -1
            return 0    # Here, for non report message we have done to receive a complete valid message
        else:
            module, sensor, axis, timestamp = iCOMOX_messages.IN_MSG_Report(msg=accumulated_msg)
            if module == iCOMOX_messages.cMODULE_RawData:
                if sensor >= iCOMOX_messages.cCOMOX_SENSOR_COUNT:
                    return -1   # Invalid IN_MSG_Report.payloadType
                if adxl356_smip:
                    if (sensor != iCOMOX_messages.cCOMOX_SENSOR_ADXL356) or (axis <= iCOMOX_messages.cAXIS_Z):  # if valid IN_MSG_Report.payloadType.sensor or axis fields
                        if (accumulated_msg[1] & 0x07) >= len(iCOMOX_messages.COMOX_IN_MSG_REPORT_PAYLOAD_SIZE_adxl356_smip):
                            return -1
                        return iCOMOX_messages.COMOX_IN_MSG_REPORT_HEADER_SIZE + iCOMOX_messages.COMOX_IN_MSG_REPORT_PAYLOAD_SIZE_adxl356_smip[accumulated_msg[1] & 0x07] - len(accumulated_msg)
                    else:
                        return -1  # invalid IN_MSG_Report.payloadType.sensor
                else:
                    return iCOMOX_messages.COMOX_IN_MSG_REPORT_HEADER_SIZE + iCOMOX_messages.COMOX_IN_MSG_REPORT_PAYLOAD_SIZE[accumulated_msg[1] & 0x07] - len(accumulated_msg)
            elif module == iCOMOX_messages.cMODULE_AnomalyDetection:
                return iCOMOX_messages.COMOX_IN_MSG_REPORT_HEADER_SIZE + 23 - len(accumulated_msg)
            # elif module == iCOMOX_messages.cMODULE_Maintenance:
            #     return iCOMOX_messages.COMOX_IN_MSG_REPORT_HEADER_SIZE + iCOMOX_messages.cCOMOX_SENSOR_COUNT*10 + 15 - len(accumulated_msg)
            elif module == iCOMOX_messages.cMODULE_Debug:
                return iCOMOX_messages.COMOX_IN_MSG_REPORT_HEADER_SIZE + iCOMOX_messages.DEBUG_REPOR_PAYLOAD_SIZE - len(accumulated_msg)
            else:
                return -1


def AXIS_to_Str(Axis):
    if Axis == iCOMOX_messages.cAXIS_X:
        return "X"
    elif Axis == iCOMOX_messages.cAXIS_Y:
        return "Y"
    elif Axis == iCOMOX_messages.cAXIS_Z:
        return "Z"
    else:
        return None

def iCOMOX_BoardType_to_Str(board_type):
    if board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_SMIP:
        return "SMIP"
    elif board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_NB_IOT:
        return "NB-IOT"
    elif board_type == iCOMOX_messages.cCOMOX_BOARD_TYPE_POE:
        return "POE"
    else:
        return "Unknown (0x{:02X})".format(board_type)

def iCOMOX_BoardVersion_to_Str(board_version_major, board_version_minor):
    if (board_version_major == 0) and (board_version_minor == 0):
        return ""
    else:
        return "{}.{}".format(board_version_major, board_version_minor)


def iCOMOX_Sensor_to_Str(sensor):
    if sensor < iCOMOX_messages.cCOMOX_SENSOR_COUNT:
        return iCOMOX_messages.COMOX_SENSOSRS_NAMES[sensor]
    else:
        return ""


def iCOMOX_firmware_release_version_branch_to_Str(firmware_release_version_branch):
    return ""
    # if firmware_release_version_branch == 0:
    #     return "DA Kit"
    # elif firmware_release_version_branch == 1:
    #     return "Suitcase"
    # else:
    #     return ""

def get_IN_MSG_Description(msg):
    if len(msg) < 1:
        return ""
    elif msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Hello:
        return "Hello"
    elif msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Reset:
        return "Reset"
    elif msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_GetConfiguration:
        return "GetConfiguration"
    elif msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_SetConfiguration:
        return "SetConfiguration"
    elif msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Debug:
        return "Debug"
    elif msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Report:
        if len(msg) < 2:
            return "Report"
        desc = "Report."
        module, sensor, axis, timestamp = iCOMOX_messages.IN_MSG_Report(msg)
        if module == iCOMOX_messages.cMODULE_RawData:
            if sensor == iCOMOX_messages.cCOMOX_SENSOR_ADXL362:
                desc += "LowPowerAcc"
            elif sensor == iCOMOX_messages.cCOMOX_SENSOR_ADXL356:
                desc += "Accelerometer."
                if axis <= iCOMOX_messages.cAXIS_Z:
                    desc += AXIS_to_Str(Axis=axis)
                else:
                    desc += "Invalid axis"
            elif sensor == iCOMOX_messages.cCOMOX_SENSOR_BMM150:
                desc += "Magnetometer"
            elif sensor == iCOMOX_messages.cCOMOX_SENSOR_ADT7410:
                desc += "Thermometer"
            elif sensor == iCOMOX_messages.cCOMOX_SENSOR_IM69D130:
                desc += "Microphone"
            else:
                desc += "Invalid"
            return desc
        elif module == iCOMOX_messages.cMODULE_AnomalyDetection:
            return "Anomaly Detection report"
        elif module == iCOMOX_messages.cMODULE_Maintenance:
            return "Maintenance report"
        elif module == iCOMOX_messages.cMODULE_Debug:
            return "Debug report"
        else:
            return "Unrecognized module"
    else:
        return "Unrecognized"


def eCOMOX_RESULT_to_Str(eCOMOX_RESULT):
    if eCOMOX_RESULT == iCOMOX_messages.cCOMOX_RESULT_OK:
        return "OK"
    elif eCOMOX_RESULT == iCOMOX_messages.cCOMOX_RESULT_SD_CARD:
        return "Error in saving file to SD card"
    else:
        return "Unknown error"

def eCOMOX_DEBUG_NBIOT_CMD_to_Str(eCOMOX_DEBUG_NBIOT_CMD):
    if eCOMOX_DEBUG_NBIOT_CMD == iCOMOX_messages.cCOMOX_DEBUG_NBIOT_CMD_Send_AT_Command:
        return "Send AT command"
    elif eCOMOX_DEBUG_NBIOT_CMD == iCOMOX_messages.cCOMOX_DEBUG_NBIOT_CMD_Reset_BG96:
        return "Reset modem"
    elif eCOMOX_DEBUG_NBIOT_CMD == iCOMOX_messages.cCOMOX_DEBUG_NBIOT_CMD_TestConnectivity:
        return "Test connectivity"
    else:
        return "Unknown command"

def ADC_Unpack_12bits_Array(packed_bytes):  # Unpack the 12 bits that are stored in 16 bits elements (4 MSB bits of each element are 0)
    unpacked_bytes = bytearray(len(packed_bytes) * 4 // 3)
    src_index = 0  # pointer to compress_samples
    dst_index = 0  # pointer to unpacked_bytes
    for i in range(0, len(unpacked_bytes)//4):
        unpacked_bytes[dst_index] = packed_bytes[src_index]
        unpacked_bytes[dst_index + 1] = packed_bytes[src_index + 1] & 0x0F
        unpacked_bytes[dst_index + 2] = (packed_bytes[src_index + 1] >> 4) + ((packed_bytes[src_index + 2] & 0x0F) << 4)
        unpacked_bytes[dst_index + 3] = packed_bytes[src_index + 2] >> 4
        dst_index += 4
        src_index += 3
    return unpacked_bytes

def Config_Options_Split(Options):
    if (Options & 0x01) != 0:
        CommChannel = iCOMOX_messages.cCOMOX_CONFIGURATION_COMM_CHANNEL_AUX
    else:
        CommChannel = iCOMOX_messages.cCOMOX_CONFIGURATION_COMM_CHANNEL_USB
    VibratorEnabled = (Options & 0x02) != 0
    TransmitEnabled = (Options & 0x40) != 0
    SaveToFileEnabled = (Options & 0x80) != 0
    return CommChannel, VibratorEnabled, TransmitEnabled, SaveToFileEnabled

def Config_Options_Build(CommChannel, VibratorEnabled, TransmitEnabled, SaveToFileEnabled):
    Options = 0
    if CommChannel == iCOMOX_messages.cCOMOX_CONFIGURATION_COMM_CHANNEL_AUX:
        Options |= 0x01
    if VibratorEnabled:
        Options |= 0x02
    if TransmitEnabled:
        Options |= 0x40
    if SaveToFileEnabled:
        Options |= 0x80
    return Options
