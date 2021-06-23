import struct
import common_symbols

NO_REPORT_TIMEOUT_SEC               = 0
UART_IN_MSG_PREFIX = bytes(b"KOBI")
SMIP_PACKET_HEADER_SIZE             = 1

M24C64_PAGE_BYTE_SIZE               = 32
M24C64_BYTES_SIZE                   = 8192

# eAXIS
cAXIS_X                             = 0
cAXIS_Y                             = 1
cAXIS_Z                             = 2

# eBACKBONE_PROTOCOL
cBACKBONE_PROTOCOL_TCP              = 0
cBACKBONE_PROTOCOL_MQTT             = 1

cBACKBONE_PROTOCOL_COUNT            = 1 # No MQTT right now

# eCOMOX_MSG_CODE
cCOMOX_MSG_CODE_Hello               = 0
cCOMOX_MSG_CODE_Reset               = 1
cCOMOX_MSG_CODE_GetConfiguration    = 2
cCOMOX_MSG_CODE_SetConfiguration    = 3
cCOMOX_MSG_CODE_ReadEEPROM          = 4
cCOMOX_MSG_CODE_WriteEEPROM         = 5
cCOMOX_MSG_CODE_VerifyEEPROM        = 6
cCOMOX_MSG_CODE_Debug               = 7

cCOMOX_MSG_CODE_COUNT               = 8
cCOMOX_MSG_CODE_Report              = 0xFF


# eCOMOX_RESULT
cCOMOX_RESULT_OK                                = 0
cCOMOX_RESULT_UNKNOWN_ERROR                     = 1
cCOMOX_RESULT_UNSUPPORTED_FEATURE               = 2
cCOMOX_RESULT_SD_CARD                           = 3
cCOMOX_RESULT_INVALID_EEPROM_COUNT              = 4
cCOMOX_RESULT_INVALID_EEPROM_ADDRESS            = 5
cCOMOX_RESULT_INVALID_EEPROM_ADDRESS_AND_COUNT  = 6
cCOMOX_RESULT_EEPROM_WRITE_BOUNDARY_ERROR       = 7
cCOMOX_RESULT_EEPROM_VERIFY_FAILED              = 8
cCOMOX_RESULT_EEPROM_ACCESS_IS_NOT_ALLOWED      = 9

cCOMOX_RESULT_COUNT                 = 9

# eCOMOX_BOARD_TYPR
cCOMOX_BOARD_TYPE_SMIP              = 0
cCOMOX_BOARD_TYPE_NB_IOT            = 1
cCOMOX_BOARD_TYPE_POE               = 2

cCOMOX_BOARD_TYPE_COUNT             = 3

# eCOMOX_PAYLOAD for sIN_MSG_Report.payloadType:
cCOMOX_SENSOR_ADXL362               = 0
cCOMOX_SENSOR_ADXL356               = 1
cCOMOX_SENSOR_BMM150                = 2
cCOMOX_SENSOR_ADT7410               = 3
cCOMOX_SENSOR_IM69D130              = 4
cCOMOX_SENSOR_ADXL1002              = 5

cCOMOX_SENSOR_COUNT                 = 6

# cCOMOX_KeepAlive                    = 0xFF

# uCOMOX_CONFIGURATION_ReportedPayloads
cCOMOX_SENSOR_BITMASK_ADXL362       = 1 << 0
cCOMOX_SENSOR_BITMASK_ADXL356       = 1 << 1
cCOMOX_SENSOR_BITMASK_BMM150        = 1 << 2
cCOMOX_SENSOR_BITMASK_ADT7410       = 1 << 3
cCOMOX_SENSOR_BITMASK_IM69D130      = 1 << 4
cCOMOX_SENSOR_BITMASK_ADXL1002      = 1 << 5

# uCOMOX_CONFIGURATION_CommChannel
cCOMOX_CONFIGURATION_COMM_CHANNEL_USB              = 0
cCOMOX_CONFIGURATION_COMM_CHANNEL_AUX              = 1

# uCOMOX_CONFIG_Common
cCOMOX_CONFIGURATION_Activate_CommChannelIsAux      = 1 << 0
cCOMOX_CONFIGURATION_Activate_Vibrator              = 1 << 1
cCOMOX_CONFIGURATION_Activate_Transmit              = 1 << 6
cCOMOX_CONFIGURATION_Activate_SaveToFile            = 1 << 7

# eCOMOX_RESET_TYPE
cCOMOX_RESET_TYPE_Software          = 0
cCOMOX_RESET_TYPE_Hardware          = 1
cCOMOX_RESET_TYPE_FirmwareUpdate    = 2

# eBG96_ACTIVITY_BITMASK
cBG96_ACTIVITY_BITMASK_UART         = 0x01
cBG96_ACTIVITY_BITMASK_SIM          = 0x02
cBG96_ACTIVITY_BITMASK_Ping         = 0x04

cMODULE_RawData                     = 0
cMODULE_AnomalyDetection            = 1
cMODULE_Maintenance                 = 2
cMODULE_Debug                       = 3
# cMODULE_COUNT                       = 4

cMODULE_BITMASK_RawData             = 0x01
cMODULE_BITMASK_AnomalyDetection    = 0x02
cMODULE_BITMASK_Maintenance         = 0x04

cCOMOX_CONFIG_BITMASK_AbsoluteTime          = 0x01
cCOMOX_CONFIG_BITMASK_Common                = 0x02
cCOMOX_CONFIG_BITMASK_PeriodicActivation    = 0x04

cANOMALY_DETECTION_COMMAND_Train             = 0
cANOMALY_DETECTION_COMMAND_Reset             = 1

cCOMOX_DEBUG_NBIOT_CMD_Send_AT_Command      = 0
cCOMOX_DEBUG_NBIOT_CMD_Reset_BG96           = 1
cCOMOX_DEBUG_NBIOT_CMD_TestConnectivity     = 2

DEBUG_REPOR_PAYLOAD_SIZE                    = 2048

# sCOMOX_OUT_MSG_xxxx
def OUT_MSG_Hello():
    return struct.pack("<B", cCOMOX_MSG_CODE_Hello)


def OUT_MSG_Reset(ResetType):
    return struct.pack("<BB", cCOMOX_MSG_CODE_Reset, ResetType)


def OUT_MSG_GetConfiguration():
    return struct.pack("<B", cCOMOX_MSG_CODE_GetConfiguration)


def OUT_MSG_SetConfiguration(ConfigBitmask=0, ConfigModulesBitmask=0, Common=0, LocalTimestamp=0, ActiveModules=0, RawData_Sensors=0, Repetition=0, IntervalInMinutes=0, AnomalyDetection_Command=cANOMALY_DETECTION_COMMAND_Train, AnomalyDetection_Sensors=0, AnomalyDetection_StateToTrain=0, Maintenance_Sensors=0, Maintenance_Flags=0, Maintenance_Alpha=0):
    return struct.pack("<BBBB" "q" "HB" "B" "B" "BBB" "BBH",
                       cCOMOX_MSG_CODE_SetConfiguration, ConfigBitmask, ConfigModulesBitmask, Common,
                       LocalTimestamp,
                       IntervalInMinutes, Repetition,
                       ActiveModules,
                       RawData_Sensors,
                       AnomalyDetection_Command, AnomalyDetection_Sensors, AnomalyDetection_StateToTrain,
                       Maintenance_Sensors, Maintenance_Flags, Maintenance_Alpha
                       )

# def OUT_MSG_SetConfiguration(RawDataSensors, CommChannel, Activate, Repetition, IntervalInMinutes, LocalTimestamp):
#     return struct.pack("<BBBBBHq", cCOMOX_MSG_CODE_SetConfiguration, RawDataSensors, CommChannel, Activate, Repetition, IntervalInMinutes, LocalTimestamp)


def OUT_MSG_ReadEEPROM(Count, Address):
    return struct.pack("<BBH", cCOMOX_MSG_CODE_ReadEEPROM, Count, Address)


def OUT_MSG_WriteEEPROM(Count, Address, Data):
    if len(Data) < M24C64_PAGE_BYTE_SIZE:
        Data += bytearray(M24C64_PAGE_BYTE_SIZE-len(Data))
    return struct.pack("<BBH", cCOMOX_MSG_CODE_WriteEEPROM, Count, Address) + Data


def OUT_MSG_VerifyEEPROM(Count, Address, Data):
    if len(Data) < M24C64_PAGE_BYTE_SIZE:
        Data += bytearray(M24C64_PAGE_BYTE_SIZE-len(Data))
    return struct.pack("<BBH", cCOMOX_MSG_CODE_VerifyEEPROM, Count, Address) + Data


def OUT_MSG_Debug_Send_AT_Command(AT_command_string, timeout_in_msec):
    return struct.pack("<BBH128s", cCOMOX_MSG_CODE_Debug, cCOMOX_DEBUG_NBIOT_CMD_Send_AT_Command, timeout_in_msec, bytearray(AT_command_string, "utf-8"))


def OUT_MSG_Debug_Reset_BG96():
    return struct.pack("<BB130s", cCOMOX_MSG_CODE_Debug, cCOMOX_DEBUG_NBIOT_CMD_Reset_BG96, bytearray(130))


def OUT_MSG_Debug_TestConnectivity():
    return struct.pack("<BB130s", cCOMOX_MSG_CODE_Debug, cCOMOX_DEBUG_NBIOT_CMD_TestConnectivity, bytearray(130))


# sCOMOX_IN_MSG_xxxx
def IN_MSG_Hello(msg):
    board_type, \
    board_version_major, board_version_minor = struct.unpack_from("<BBB", msg, 1)
    mcu_serial_number = msg[4:20]
    firmware_release_version_major, firmware_release_version_minor, firmware_release_version_patch, firmware_release_version_branch, \
    firmware_build_version_date_year, firmware_build_version_date_month, firmware_build_version_date_day, \
    firmware_build_version_time_hour, firmware_build_version_time_minute, firmware_build_version_time_second, \
    bit_status, \
    product_part_number, production_serial_number, name, \
    smip_swMajor, smip_swMinor, smip_swPatch, smip_swBuild = struct.unpack_from("<BBBBHBBBBBB32s32s32sBBBH", msg, 20)
    return board_type, \
           board_version_major, board_version_minor, \
           mcu_serial_number, \
           firmware_release_version_major, firmware_release_version_minor, firmware_release_version_patch, firmware_release_version_branch, \
           firmware_build_version_date_year, firmware_build_version_date_month, firmware_build_version_date_day, \
           firmware_build_version_time_hour, firmware_build_version_time_minute, firmware_build_version_time_second, \
           bit_status, \
           product_part_number, production_serial_number, name, \
           smip_swMajor, smip_swMinor, smip_swPatch, smip_swBuild


def IN_MSG_Reset(msg):
    return


def IN_MSG_GetConfiguration(msg):
    Common, \
    TransmitRepetition, TransmitIntervalInMinutes, \
    ActiveModules, \
    RawDataSensors, \
    AnomalyDetectionModule_target, AnomalyDetectionModule_selSensor, AnomalyDetectionModule, AnomalyDetectionModule_modelLearned, \
    MaintenanceModule_sensors, MaintenanceModule_flags, MaintenanceModule_alpha = \
        struct.unpack_from("<B" "BH" "B" "B" "BBBB" "BBH", msg, 1)
    return Common, TransmitRepetition, TransmitIntervalInMinutes, ActiveModules, \
            RawDataSensors, \
            AnomalyDetectionModule_target, AnomalyDetectionModule_selSensor, AnomalyDetectionModule, AnomalyDetectionModule_modelLearned, \
            MaintenanceModule_sensors, MaintenanceModule_flags, MaintenanceModule_alpha


def IN_MSG_SetConfiguration(msg):
    return msg[1]


def IN_MSG_Debug(msg):
    # [s] = struct.unpack_from("<{}s".format(DEBUG_REPOR_PAYLOAD_SIZE), msg, 1)
    # return s    #.decode("utf-8")
    Cmd, Result = struct.unpack_from("<BB", msg, 1)
    return Cmd, Result


def IN_MSG_Report(msg):
    module = msg[1] >> 6
    [timestamp] = struct.unpack_from("<q", msg, 2)
    if module == cMODULE_RawData:
        axis = (msg[1] >> 4) & 0x03
        sensor = msg[1] & 0x07
    elif module == cMODULE_Debug:
        command = (msg[1] & 0x03)
        last_packet = (msg[1] & 0x20) != 0
        return module, last_packet, command, timestamp
    else:
        axis = None
        sensor = None
    return module, sensor, axis, timestamp


def IN_MSG_REPORT_AnomalyDetection(payload):
    probState = [0] * 4
    ValAnomaly, probState[0], probState[1], probState[2], probState[3], ReportStatus, Sensors, Result = struct.unpack("<f4fBBB", payload)
    return ValAnomaly, probState, ReportStatus, Sensors, Result


# def IN_MSG_REPORT_Maintenance(payload):
    # BasicStats = [0, 0, 0, 0] * 6
    # for i in range(0, cCOMOX_SENSOR_COUNT):
    #     struct.unpack_from("<hhhh", payload, i * 8)
    # AlertsMagnitudes = struct.unpack_from("<{}h".format(cCOMOX_SENSOR_COUNT),
    #                                       2 + cCOMOX_SENSOR_COUNT * 8)
    # MotorOnTimeSec, TotalTimeSec, SyncSpeed, MotorSpeed, MinAlerts, MaxAlerts, IsMotorOn = struct.unpack_from("<LLhhBB?", msg, 2 + cCOMOX_SENSOR_COUNT * 10)
    # return BasicStats, AlertsMagnitudes,  MotorOnTimeSec, TotalTimeSec, SyncSpeed, MotorSpeed, MinAlerts, MaxAlerts, IsMotorOn


def IN_MSG_REPORT_Debug(payload):
    [s] = struct.unpack_from("<{}s".format(DEBUG_REPOR_PAYLOAD_SIZE), payload)
    return s    #.decode("utf-8")
    # debug_cmd, s = struct.unpack_from("<B{}s".format(DEBUG_REPOR_PAYLOAD_SIZE), msg, 1)
    # return debug_cmd, s    #.decode("utf-8")


# helpers for the OnGetIncomingMsgSize
COMOX_IN_MSG_SIZE =   \
(
    133,    # Hello
    1,      # Reset
    15,     # GetConfiguration
    2,      # SetConfiguration
    37,     # ReadEEPROM
    5,      # WriteEEPROM,
    5,      # VerifyEEPROM
    3       # Debug
)

COMOX_IN_MSG_REPORT_HEADER_SIZE = 10    # Report (only msg code + payload type + timestamp)

ADXL362_SAMPLES_NUM                 = 1024
ADXL356_SAMPLES_NUM_PER_PIN         = 2048
BMM150_SAMPLES_NUM                  = 512
IM69D130_SAMPLES_NUM                = 1024
ADXL1002_SAMPLES_NUM                = 2048

ADXL356_SMIP_SAMPLES_NUM_PER_PIN    = 8192

COMOX_IN_MSG_REPORT_PAYLOAD_SIZE =   \
(
    ADXL362_SAMPLES_NUM * 2 * 3,                    # ADXL362 - 16 bits array, 3 interleaved axis
    ADXL356_SAMPLES_NUM_PER_PIN * 2 * 3 * 12 // 16, # ADXL356 - 16 bits array, 3 axis, 1.5 bytes (=12 bits) each sample
    BMM150_SAMPLES_NUM * 3 * 2,                     # BMM150 - Each sample includes: Bx, By, Bz. Each is of 16 bits
    2,                                              # ADT7410 - temperature data, signed 16 bits, Q9.7 format
    IM69D130_SAMPLES_NUM * 2,                       # IM69D130 - Each sample is of 16 bits
    ADXL1002_SAMPLES_NUM * 2 * 12 // 16
)

COMOX_IN_MSG_REPORT_PAYLOAD_SIZE_adxl356_smip =   \
(
    ADXL362_SAMPLES_NUM * 2 * 3,                    # ADXL362 - 16 bits array, 3 interleaved axis
    ADXL356_SMIP_SAMPLES_NUM_PER_PIN * 2 * 12 // 16,# ADXL356 - 16 bits arrays of samples from a single axis. Each sample is of 12 bits compressed in the array.    #ADXL356_SAMPLES_NUM_PER_PIN * 2 * 12 // 16,
    BMM150_SAMPLES_NUM * 3 * 2,                     # BMM150 - Each sample includes: Bx, By, Bz. Each is of 16 bits
    2,                                              # ADT7410 - temperature data, signed 16 bits, Q9.7 format
    IM69D130_SAMPLES_NUM * 2                        # IM69D130 - Each sample is of 16 bits
)

COMOX_SENSOSRS_NAMES = \
(
    "ADXL362",
    "ADXL356",
    "BMM150",
    "ADT7410",
    "IM69D130",
    "ADXL1002"
)
