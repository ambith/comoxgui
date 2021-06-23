import common
import os
import iCOMOX_messages
import messages_utils
import helpers
import struct
import ADXL356
import BMM150
import IM69D130
import ADT7410

cFILE_TYPE_REPORTS_VERSION_1                    = 0
cFILE_TYPE_REPORTS_VERSION_2                    = 1 # addition of time before each sensor's samples (int64_t - ticks of 32.768KHz since 1.1.1970 in local time)
cFILE_TYPE_REPORTS_VERSIONS_COUNT               = 2

cBIN_FILE_CONVERSION_OK                         = 0
cBIN_FILE_CONVERSION_UnrecognizedMsg            = 1
cBIN_FILE_CONVERSION_NonReportMsgFound          = 2
cBIN_FILE_CONVERSION_NotEnoughBytes             = 3
cBIN_FILE_CONVERSION_NotEnoughBytesInTheLastMsg = 4
cBIN_FILE_CONVERSION_UnrecognizedHeader         = 5

def sFileHeader_to_Str(FileHeader):
    if FileHeader[0] >= cFILE_TYPE_REPORTS_VERSIONS_COUNT:
        return None
    if FileHeader[1] > iCOMOX_messages.cCOMOX_BOARD_TYPE_POE:
        return None

    FileVersion = "{:d}".format(FileHeader[0]+1)
    BoardType = messages_utils.iCOMOX_BoardType_to_Str(board_type=FileHeader[1])
    BoardVersion = messages_utils.iCOMOX_BoardVersion_to_Str(board_version_major=FileHeader[2], board_version_minor=FileHeader[3])
    McuSerialNumber = "{:^32}".format(helpers.u8s_to_str(arr=FileHeader[4:4+16], separator=""))
    FirmwareReleaseVersion = "{}.{}.{} {}".format(FileHeader[20], FileHeader[21], FileHeader[22], messages_utils.iCOMOX_firmware_release_version_branch_to_Str(FileHeader[23]))

    hello_firmware_build_version_date_year, hello_firmware_build_version_date_month, hello_firmware_build_version_date_day, \
    hello_firmware_build_version_time_hour, hello_firmware_build_version_time_minute, hello_firmware_build_version_time_second = \
        struct.unpack_from("<HBBBBB", FileHeader, 24)

    Firmware_build_version = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(
        hello_firmware_build_version_date_day, hello_firmware_build_version_date_month, hello_firmware_build_version_date_year, \
        hello_firmware_build_version_time_hour, hello_firmware_build_version_time_minute, hello_firmware_build_version_time_second)

    s = "iCOMOX RawDataSensors file version: {}\r\nMCU serial number: {}\r\nFirmware release version: {}\r\nFirmware build at: {}\r\nBoard type: {}\r\n".format(
        FileVersion, McuSerialNumber, FirmwareReleaseVersion, Firmware_build_version, BoardType)
    if BoardVersion != "":
        s += "Board version: {}\r\n".format(BoardVersion)
    return s

def BinFileConversion(bin_file_name, text_file_name):
    hText = None
    hBinary = None
    reportsCount = 0
    result = cBIN_FILE_CONVERSION_OK
    bin_size = os.stat(bin_file_name).st_size
    try:
        hBinary = open(file=bin_file_name, mode="rb")
        hText = open(file=text_file_name, mode="w+t", newline="", encoding="utf-8")

        # Convert header
        if bin_size < 31:
            result = cBIN_FILE_CONVERSION_NotEnoughBytes
            return
        bin_size -= 31
        FileHeader = hBinary.read(31)
        FileHeaderStrs = sFileHeader_to_Str(FileHeader=FileHeader)
        if FileHeaderStrs is None:
            result = cBIN_FILE_CONVERSION_UnrecognizedHeader
            return
        hText.write(FileHeaderStrs)
        adxl356_smip = FileHeader[1] == iCOMOX_messages.cCOMOX_BOARD_TYPE_SMIP

        # Convert RawDataSensors
        msg = bytearray()
        while bin_size > 0:
            # if (len(msg) == 0) and (FileHeader[0] == cFILE_TYPE_REPORTS_VERSION_2):
            #     msg_timestamp = hBinary.read(8)
            #     timestamp = struct.unpack("<q", msg_timestamp)  # right now we don't translate this time to a proper string
            #     bin_size -= 8

            bytes_to_read = messages_utils.on_get_in_message_size(accumulated_msg=msg, adxl356_smip=adxl356_smip)
            if bytes_to_read < 0:
                reportsCount = 0
                result = cBIN_FILE_CONVERSION_UnrecognizedMsg
                return
            elif bytes_to_read == 0:
                if msg[0] == iCOMOX_messages.cCOMOX_MSG_CODE_Report:
                    module, sensor, axis, timestamp = iCOMOX_messages.IN_MSG_Report(msg=msg)
                    payload = msg[2+8:]
                    if module == iCOMOX_messages.cMODULE_RawData:
                        if sensor == iCOMOX_messages.cCOMOX_SENSOR_ADXL362:
                            samples_g = common.ADXL362.msg_bytes_to_samples_g(payload=payload)
                            hText.write("ADXL362:\r\n")
                            hText.write("{:^9s}{:^16s}{:^16s}{:^16s}\r\n".format("t[msec]", "aX[g=9.81 m/s²]", "aY[g=9.81 m/s²]", "aZ[g=9.81 m/s²]"))
                            for i in range(0, len(samples_g[0])):
                                hText.write("{:^9.3f}{:^16.3f}{:^16.3f}{:^16.3f}\r\n".format(1E3 * i / common.ADXL362.Fs_Acc, samples_g[0][i], samples_g[1][i], samples_g[2][i]))

                        elif sensor == iCOMOX_messages.cCOMOX_SENSOR_ADXL356:
                                if adxl356_smip: # 48.3KSPS with 3 different messages for each axis
                                    samples_g = common.ADXL356_SMIP.msg_bytes_to_samples_g(payload=payload)
                                    hText.write("ADXL356.{}:\r\n".format(messages_utils.AXIS_to_Str(Axis=axis)))
                                    hText.write("{:^9s}{:^16s}\r\n".format("t[msec]", "a[g=9.81 m/s²]"))
                                    for i in range(0, len(samples_g)):
                                        hText.write("{:^9.3f}{:^16.3f}\r\n".format(1E3 * i / common.ADXL356_SMIP.Fs_Acc, samples_g[i]))
                                else:
                                    # 3.611KSPS with a single messages for all the 3 axis
                                    samples_g = common.ADXL356.msg_bytes_to_samples_g(payload=payload)
                                    hText.write("ADXL356:\r\n")
                                    hText.write("{:^9s}{:^16s}{:^16s}{:^16s}\r\n".format("t[msec]", "aX[g=9.81 m/s²]", "aY[g=9.81 m/s²]", "aZ[g=9.81 m/s²]"))
                                    for i in range(0, len(samples_g[0])):
                                        hText.write("{:^9.3f}{:^16.3f}{:^16.3f}{:^16.3f}\r\n".format(1E3 * i / common.ADXL356.Fs_Acc, samples_g[0][i], samples_g[1][i], samples_g[2][i]))

                        elif sensor == iCOMOX_messages.cCOMOX_SENSOR_BMM150:
                            mag_x_uTesla, mag_y_uTesla, mag_z_uTesla = common.BMM150.msg_bytes_to_samples_uTesla(payload=payload)
                            hText.write("BMM150:\r\n")
                            hText.write("{:^9s}{:^9s}{:^9s}{:^9s}\r\n".format("t[msec]", "X[μT]", "Y[μT]", "Z[μT]"))
                            for i in range(0, len(mag_x_uTesla)):
                                hText.write("{:^9.3f}{:^9.3f}{:^9.3f}{:^9.3f}\r\n".format(1E3*i/common.BMM150.Fs_Mag, mag_x_uTesla[i], mag_y_uTesla[i], mag_z_uTesla[i]))

                        elif sensor == iCOMOX_messages.cCOMOX_SENSOR_ADT7410:
                            sample_Celsius = common.ADT7410.msg_bytes_to_sample_Celsius(payload=payload)
                            hText.write("ADT7410 [°C]:\r\n")
                            hText.write("{:<.3f}\r\n".format(sample_Celsius))

                        elif sensor == iCOMOX_messages.cCOMOX_SENSOR_IM69D130:
                            samples_SPL = common.IM69D130.msg_bytes_to_samples_SPL(payload=payload)
                            hText.write("IM69D130:\r\n")
                            hText.write("{:^9s}{:^12s}\r\n".format("t[msec]", "Sound[SPL]"))
                            for i in range(0, len(samples_SPL)):
                                hText.write("{:^9.3f}{:^12.3f}\r\n".format(1E3*i/common.IM69D130.Fs_Mic, samples_SPL[i]))

                        elif sensor == iCOMOX_messages.cCOMOX_SENSOR_ADXL1002:
                            samples_g = common.ADXL1002.msg_bytes_to_samples_g(payload=payload)
                            hText.write("ADXL1002:\r\n")
                            hText.write("{:^9s}{:^16s}\r\n".format("t[msec]", "a[g=9.81 m/s²]"))
                            for i in range(0, len(samples_g)):
                                hText.write("{:^9.3f}{:^16.3f}\r\n".format(1E3 * i / common.ADXL1002.Fs_Acc, samples_g[i]))

                        else:
                            reportsCount = 0
                            result = cBIN_FILE_CONVERSION_UnrecognizedMsg
                            return

                    elif module == iCOMOX_messages.cMODULE_AnomalyDetection:
                        ValAnomaly, probState, ReportStatus, Sensors, Result = iCOMOX_messages.IN_MSG_REPORT_AnomalyDetection(payload=payload)
                        IsTrainReport = (ReportStatus & 0x80) != 0  # Train ("1") or Inference ("0")  result
                        if IsTrainReport:
                            hText.write("Anomaly Detection: Train report\r\n")
                        else:
                            hText.write("Anomaly Detection: Inference report\r\n")
                        if Result == 0:
                            if not IsTrainReport:
                                hText.write("{:^12s}{:^12s}{:^12s}{:^12s}{:^12s}{:^12s}\r\n".format("Anomaly [%]", "P(s0)", "P(s1)", "P(s2)", "P(s3)", "Learning"))
                                hText.write("{:^12.3f}{:^12.3f}{:^12.3f}{:^12.3f}{:^12.3f}{:^12s}\r\n".format(ValAnomaly, probState[0], probState[1], probState[2], probState[3], str((ReportStatus & 0x80) != 0)))
                        else:
                            hText.write("Error {}\r\n".format(Result))

                    # elif module == iCOMOX_messages.cMODULE_Maintenance:
                    #     BasicStats, AlertsMagnitudes,  MotorOnTimeSec, TotalTimeSec, SyncSpeed, MotorSpeed, MinAlerts, MaxAlerts, IsMotorOn = iCOMOX_messages.IN_MSG_REPORT_Maintenance(msg=payload)
                    #     BasicStats[0] = common.ADXL362.ADC_readings_to_g_units(ADC_samples=BasicStats[0])
                    #     AlertsMagnitudes[0] = common.ADXL362.ADC_readings_to_g_units(ADC_samples=AlertsMagnitudes[0])
                    #     BasicStats[1] = common.ADXL356.ADC_readings_to_g_units(ADC_samples=BasicStats[1])
                    #     AlertsMagnitudes[1] = common.ADXL356.ADC_readings_to_g_units(ADC_samples=AlertsMagnitudes[1])
                    #     BasicStats[2] = common.BMM150.msg_bytes_to_samples_uTesla(payload=BasicStats[2])
                    #     AlertsMagnitudes[2] = common.BMM150.msg_bytes_to_samples_uTesla(payload=AlertsMagnitudes[2])
                    #     for i in range(0, len(BasicStats[3])):
                    #         BasicStats[3][i] = common.ADT7410.readings_to_Celsius(raw_sample=BasicStats[3][i])
                    #     AlertsMagnitudes[3] = common.ADT7410.readings_to_Celsius(raw_sample=AlertsMagnitudes[3])
                    #     BasicStats[4] = common.IM69D130.msg_bytes_to_samples_SPL(payload=BasicStats[4])
                    #     AlertsMagnitudes[4] = common.IM69D130.msg_bytes_to_samples_SPL(payload=AlertsMagnitudes[4])
                    #     BasicStats[5] = common.ADXL1002.ADC_readings_to_g_units(ADC_samples=BasicStats[5])
                    #     AlertsMagnitudes[5] = common.ADXL1002.ADC_readings_to_g_units(ADC_samples=AlertsMagnitudes[5])
                    #     hText.write("Maintenane:\r\n")
                    #     if IsMotorOn:
                    #         MotorStateStr = "ON"
                    #     else:
                    #         MotorStateStr = "OFF"
                    #     hText.write("Motor is " + MotorStateStr + "\r\n")
                    #     hText.write("Motor synchronous speed is {} [RPM]".format(SyncSpeed))
                    #     hText.write("Motor speed is {} [RPM]".format(MotorSpeed))
                    #     hText.write("Motor ON time: {} [sec], out of {} [sec]\r\n".format(MotorOnTimeSec, TotalTimeSec))
                    #     hText.write("{:^15s}{:^12.3s}{:^12.3s}{:^12.3s}{:^12.3s}{:^12.3s}{:^15s}{:^15s}\r\n".format("Sensor", "Minimum", "Maximum", "Mean", "Std. Dev.", "Last value", "Alert minimum", "Alert maximum"))
                    #     for i in range(0, iCOMOX_messages.cCOMOX_SENSOR_COUNT):
                    #         if 0 != MinAlerts & (1 << i):
                    #             MinAlert = "ALERT"
                    #         else:
                    #             MinAlert = ""
                    #         if 0 != MaxAlerts & (1 << i):
                    #             MaxAlert = "ALERT"
                    #         else:
                    #             MaxAlert = ""
                    #         hText.write("{:^15s}{:^12.3f}{:^12.3f}{:^12.3f}{:^12.3f}{:^12.3f}{:^15s}{:^15s}\r\n".format( \
                    #             iCOMOX_messages.COMOX_SENSOSRS_NAMES[i], \
                    #             BasicStats[i][0], BasicStats[i][1], BasicStats[i][2], BasicStats[i][3], AlertsMagnitudes[i], MinAlert, MaxAlert))

                    else:
                        reportsCount = 0
                        result = cBIN_FILE_CONVERSION_NonReportMsgFound
                        return

                    hText.write("\r\n")
                    reportsCount += 1
                else:
                    reportsCount = 0
                    result = cBIN_FILE_CONVERSION_NonReportMsgFound
                    return
                msg = bytearray()
            else:
                if bin_size < bytes_to_read:
                    reportsCount = 0
                    result = cBIN_FILE_CONVERSION_NotEnoughBytesInTheLastMsg
                msg += hBinary.read(bytes_to_read)
                bin_size -= bytes_to_read

    except Exception as ex:
        if hasattr(ex, 'message'):
            helpers.OUT(ex.message)

    finally:
        if hBinary is not None:
            hBinary.close()
        if hText is not None:
            hText.close()
        return result, reportsCount
