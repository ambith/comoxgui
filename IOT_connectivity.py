# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

import iotc
import IOT_Shiratech
#import IOT_icomoxlab
import PingPong
import helpers
import threading
import time
import iCOMOX_messages

#
# Credentials FOR DEVICE #1 from IoT Central APP https://icomox-demo.azureiotcentral.com/
# DO NOT DISTRIBUTE CODE WITH CREDENTIALS TO CUSTOMERS!
#

class IOT_DEVICE_REPORT:
    def __init__(self):
        self.time = time.time()


class IOT_DEVICE_REPORT_TEMP(IOT_DEVICE_REPORT):
    def __init__(self, temp):
        super(IOT_DEVICE_REPORT_TEMP, self).__init__()
        self.temp = temp

class IOT_DEVICE_REPORT_MAX_ABS_LOW_POWER_ACC(IOT_DEVICE_REPORT):
    def __init__(self, max_abs_acc_x, max_abs_acc_y, max_abs_acc_z):
        super(IOT_DEVICE_REPORT_MAX_ABS_LOW_POWER_ACC, self).__init__()
        self.max_abs_acc_x = max_abs_acc_x
        self.max_abs_acc_y = max_abs_acc_y
        self.max_abs_acc_z = max_abs_acc_z

class IOT_DEVICE_REPORT_MAX_ABS_ACC(IOT_DEVICE_REPORT):
    def __init__(self, max_abs_acc):
        super(IOT_DEVICE_REPORT_MAX_ABS_ACC, self).__init__()
        self.max_abs_acc = max_abs_acc

class IOT_DEVICE_REPORT_MOTOR_SPEED(IOT_DEVICE_REPORT):
    def __init__(self, motor_speed):
        super(IOT_DEVICE_REPORT_MOTOR_SPEED, self).__init__()
        self.motor_speed = motor_speed

class IOT_DEVICE_REPORT_FAULT(IOT_DEVICE_REPORT):
    def __init__(self, fault):
        super(IOT_DEVICE_REPORT_FAULT, self).__init__()
        self.fault = fault

class IOT_DEVICE_REPORT_ACC(IOT_DEVICE_REPORT):
    def __init__(self, acc):
        super(IOT_DEVICE_REPORT_ACC, self).__init__()
        self.acc = acc

class IOT_DEVICE_REPORT_MAG(IOT_DEVICE_REPORT):
    def __init__(self, mag):
        super(IOT_DEVICE_REPORT_MAG, self).__init__()
        self.mag = mag

class IOT_DEVICE_REPORT_MIC(IOT_DEVICE_REPORT):
    def __init__(self, mic):
        super(IOT_DEVICE_REPORT_MIC, self).__init__()
        self.mic = mic

class IOT_DEVICE:
    def __init__(self, uniqueID):
        self.iotc = None
        try:
            scopeID, deviceID, primaryKey, secondaryKey = IOT_Shiratech.uniqueID_to_IotcInfo(uniqueID=uniqueID)
        except:
            raise Exception("Currently IOT_DEVICE does not support this unique ID")
        finally:
            pass
        self.uniqueID = uniqueID
        #self.canSend = False
        self.PingPong_MaxAbsLowPowerAcc = PingPong.ClassPingPong()
        self.PingPong_Temp = PingPong.ClassPingPong()
        self.PingPong_MotorSpeed = PingPong.ClassPingPong()
        self.PingPong_MaxAbsAcc = [PingPong.ClassPingPong(), PingPong.ClassPingPong(), PingPong.ClassPingPong()]
        self.PingPong_Fault = PingPong.ClassPingPong()
        self.PingPong_Acc = [PingPong.ClassPingPong(), PingPong.ClassPingPong(), PingPong.ClassPingPong()]
        self.PingPong_Mag = [PingPong.ClassPingPong(), PingPong.ClassPingPong(), PingPong.ClassPingPong()]
        self.PingPong_Mic = PingPong.ClassPingPong()

        #secret = primaryKey[index]  # uniqueID_to_PrimaryKey(uniqueID=uniqueID)
        #Key = self.computeKey(secret=secret, regId=deviceIDs[index], microPython=False)
        self.iotc = iotc.Device(scopeId=scopeID, keyORCert=primaryKey, deviceId=deviceID, credType=iotc.IOTConnectType.IOTC_CONNECT_SYMM_KEY)
        self.iotc.setLogLevel(iotc.IOTLogLevel.IOTC_LOGGING_ALL)
        self.shouldConnect = True

    def __del__(self):
        if self.isConnected():
            self.iotc.disconnect()

    def reconnect(self):
        if self.shouldConnect:
            return
        if self.isConnected():
            self.iotc.disconnect()
            self.iotc.doNext()  # do the async work needed to be done for MQTT
        self.shouldConnect = True

    def canSend(self):
        return self.iotc.isConnected()

    def isConnected(self):
        return self.iotc is not None and self.iotc.isConnected()

    def doNext(self):
        if self.iotc is not None:
            self.iotc.doNext()

    def update_temp(self, temp):
        self.PingPong_Temp.try_push_msg(IOT_DEVICE_REPORT_TEMP(temp=temp))

    def update_motor_speed(self, motor_speed):
        self.PingPong_MotorSpeed.try_push_msg(IOT_DEVICE_REPORT_MOTOR_SPEED(motor_speed=motor_speed))

    def update_max_abs_lowpower_acc(self, axis, max_abs_acc_x, max_abs_acc_y, max_abs_acc_z):
        self.PingPong_MaxAbsLowPowerAcc.try_push_msg(msg=IOT_DEVICE_REPORT_MAX_ABS_LOW_POWER_ACC(max_abs_acc_x=max_abs_acc_x, max_abs_acc_y=max_abs_acc_y, max_abs_acc_z=max_abs_acc_z))

    def update_max_abs_acc(self, axis, max_abs_acc):
        self.PingPong_MaxAbsAcc[axis].try_push_msg(msg=IOT_DEVICE_REPORT_MAX_ABS_ACC(max_abs_acc=max_abs_acc))

    def update_fault(self, fault):
        self.PingPong_Fault.try_push_msg(IOT_DEVICE_REPORT_FAULT(fault=fault))

    def update_acc_field(self, axis, data):
        self.PingPong_Acc[axis].try_push_msg(IOT_DEVICE_REPORT_ACC(acc=data))

    def update_magnetic_field(self, axis, data):
        self.PingPong_Mag[axis].try_push_msg(IOT_DEVICE_REPORT_MAG(mag=data))

    def update_microphone_field(self, data):
        self.PingPong_Mic.try_push_msg(IOT_DEVICE_REPORT_MIC(mic=data))

    def onconnect(self, info):
        helpers.OUT("- [onconnect] => state:" + str(info.getStatusCode()))
        #self.canSend = (info.getStatusCode() == 0) and self.iotc.isConnected()
        # if self.canSend:
        #     self.shouldConnect = False

    def onmessagesent(self, info):
        helpers.OUT("\t- [onmessagesent] => " + str(info.getPayload()))

    def oncommand(self, info):
        helpers.OUT("- [oncommand] => " + info.getTag() + " => " + str(info.getPayload()))

    def onsettingsupdated(self, info):
        helpers.OUT("- [onsettingsupdated] => " + info.getTag() + " => " + info.getPayload())

    # def computeKey(self, secret, regId, microPython):
    #     try:
    #         secret = base64.b64decode(secret)
    #     except:
    #         print("ERROR: broken base64 secret => `" + secret + "`")
    #         sys.exit()
    #
    #     if microPython == False:
    #         return base64.b64encode(hmac.new(secret, msg=regId.encode('utf8'), digestmod=hashlib.sha256).digest())
    #     else:
    #         return base64.b64encode(hmac.new(secret, msg=regId.encode('utf8'), digestmod=hashlib._sha256.sha256).digest())

    def connectdevice(self):
        self.iotc.on("ConnectionStatus", self.onconnect)
        self.iotc.on("MessageSent", self.onmessagesent)
        self.iotc.on("Command", self.oncommand)
        self.iotc.on("SettingsUpdated", self.onsettingsupdated)
        try:
            self.iotc.connect()
        except Exception as ex:
            if hasattr(ex, 'message'):
                helpers.OUT(ex.message)
            # self.shouldConnect = True
        finally:
            pass


class IOT_DEVICES_LIST():
    def __init__(self):
        self.iot_device_arr = []
        self.timer = None
        # Due to 50000 messages per device per month for free service,
        # we get a minimum of 31*24*3600/50000 = 53.568 seconds, so we chose 60 seconds
        self.period = 60
        self.Terminated = False

    def __del__(self):
        if self.iot_device_arr is not None:
            for iot_device in self.iot_device_arr:
                del iot_device
        self.iot_device_arr = None

    def add_device(self, uniqueID):
        if self.device_by_uniqueID(uniqueID) is not None:
            return
        try:
            iot_device = IOT_DEVICE(uniqueID=uniqueID)
        except Exception as ex:
            iot_device = None
        else:
            self.iot_device_arr.append(iot_device)
            iot_device.connectdevice()
        finally:
            pass

    def reconnect_device(self, uniqueID):
        device = self.device_by_uniqueID(uniqueID=uniqueID)
        if device is None:
            return
        device.reconnect()

    def device_by_uniqueID(self, uniqueID):
        for iot_device in self.iot_device_arr:
            if iot_device.uniqueID == uniqueID:
                return iot_device
        return None

    def cloud_update_start(self):
        if self.timer is None:
            self.Terminated = False
            self.timer = threading.Thread(target=self.SendTelemetry)
            self.timer.start()
        #else:
        #    helpers.OUT("IOT_DEVICE_LIST.cloud_update_start() tries to start without stop first")

    def cloud_update_stop(self):
        self.Terminated = True
        del self.timer
        self.timer = None

    def SendTelemetry(self):
        max_abs_lowpower_acc = [None]*3
        max_abs_acc = [None] * 3
        acc = [None]*3
        mag = [None]*3
        mic = None
        wideband_acc = None
        while not self.Terminated:
            for iot_device in self.iot_device_arr:
                if iot_device.isConnected():
                    iot_device.doNext()  # do the async work needed to be done for MQTT
                    if iot_device.canSend():
                        new_data_available = False

                        # Get the temperature data if available
                        temp = iot_device.PingPong_Temp.try_pop_msg()
                        if temp is not None:
                            temp = temp.temp
                            if temp < 0:
                                temp_state = -1
                            elif temp > 70:
                                temp_state = 1
                            else:
                                temp_state = 0
                            new_data_available = True
                        else:
                            temp_state = None

                        # Get the motor speed if available
                        motor_speed = iot_device.PingPong_MotorSpeed.try_pop_msg()
                        if motor_speed is not None:
                            motor_speed = motor_speed.network_frequency_Hz
                            new_data_available = True

                        max_abs_lowpower_acc = iot_device.PingPong_MaxAbsLowPowerAcc.try_pop_msg()
                        if max_abs_lowpower_acc is not None:
                            max_abs_lowpower_acc = max_abs_lowpower_acc.max_abs_lowpower_acc
                            new_data_available = True

                        # Get accelerometer data in each axis if available
                        for axis in range(iCOMOX_messages.cAXIS_X, iCOMOX_messages.cAXIS_Z+1):
                            max_abs_acc[axis] = iot_device.PingPong_MaxAbsAcc[axis].try_pop_msg()
                            if max_abs_acc[axis] is not None:
                                max_abs_acc[axis] = max_abs_acc[axis].max_abs_acc
                                new_data_available = True

                        # Get motor state if available
                        motor_state = iot_device.PingPong_Fault.try_pop_msg()
                        if motor_state is not None:
                            motor_state = motor_state.fault
                            new_data_available = True

                        # Get new accelerometer data for each axis if available
                        for axis in range(iCOMOX_messages.cAXIS_X, iCOMOX_messages.cAXIS_Z + 1):
                            acc[axis] = iot_device.PingPong_Acc[axis].try_pop_msg()
                            if acc[axis] is not None:
                                acc[axis] = acc[axis].acc
                                new_data_available = True

                        wideband_acc_max_abs = iot_device.PingPong_MaxAbsWidebandAcc.try_pop_msg()
                        if wideband_acc_max_abs is not None:
                            wideband_acc_max_abs = wideband_acc_max_abs.wideband_acc_max_abs
                            new_data_available = True

                        # # Get new magnetometer data for each axis if available
                        # for axis in range(iCOMOX_messages.cAXIS_X, iCOMOX_messages.cAXIS_Z + 1):
                        #     mag[axis] = iot_device.PingPong_Mag[axis].try_pop_msg()
                        #     if mag[axis] is not None:
                        #         mag[axis] = mag[axis].mag
                        #         new_data_available = True
                        #
                        # # Get new microphone data
                        # mic = iot_device.PingPong_Mic.try_pop_msg()
                        # if mic is not None:
                        #     new_data_available = True

                        # Send data if any new data is available
                        if new_data_available:
                            # helpers.OUT("Sending telemetry..")
                            telemetry = self.build_json_struct(temp=temp, temp_state=temp_state, motor_speed=motor_speed, max_abs_acc=max_abs_acc, motor_state=motor_state, acc=acc, mag=mag, mic=mic)
                            #helpers.OUT(telemetry)
                            iot_device.iotc.sendTelemetry(telemetry)
                else:
                    iot_device.reconnect()
                    if iot_device.shouldConnect:
                        iot_device.shouldConnect = False
                        iot_device.connectdevice()
                        iot_device.doNext()  # do the async work needed to be done for MQTT
                    #helpers.OUT("Attempt to reconnect device")

            time_counter = self.period
            while not self.Terminated and time_counter > 0:
                time.sleep(1)
                time_counter -= 1

    def build_json_struct(self, temp=None, temp_state=None, motor_speed=None, max_abs_acc=[None]*3, motor_state=None, acc=[None]*3, mag=[None]*3, mic=None):
        def to_json_field(field_name, value):
            if value is None:
                return ""
            return '\"' + field_name + '\": ' + str(value) + ", "

        def to_json_array_field(field_name, value):
            if value is None:
                return ""
            array_string = ",".join(list(map("{:.2f}".format, value)))
            return '"' + field_name + '\": [ ' + array_string + " ], "

        if motor_state is not None:
            if motor_state:
                motor_state = "true"
            else:
                motor_state = "false"

        result =    '{ ' + \
                    to_json_field(field_name="Temperature", value=temp) + \
                    to_json_field(field_name="TemperatureState", value=temp_state) + \
                    to_json_field(field_name="MotorSpeed", value=motor_speed) + \
                    to_json_field(field_name="MaxAbsAccX", value=max_abs_acc[iCOMOX_messages.cAXIS_X]) + \
                    to_json_field(field_name="MaxAbsAccY", value=max_abs_acc[iCOMOX_messages.cAXIS_Y]) + \
                    to_json_field(field_name="MaxAbsAccZ", value=max_abs_acc[iCOMOX_messages.cAXIS_Z]) + \
                    to_json_field(field_name="MotorState", value=motor_state)
                    # to_json_array_field(field_name="AccX", value=acc[iCOMOX_messages.cAXIS_X]) + \
                    # to_json_array_field(field_name="AccY", value=acc[iCOMOX_messages.cAXIS_Y]) + \
                    # to_json_array_field(field_name="AccZ", value=acc[iCOMOX_messages.cAXIS_Z]) + \
                    # to_json_array_field(field_name="MagX", value=mag[iCOMOX_messages.cAXIS_X]) + \
                    # to_json_array_field(field_name="MagY", value=mag[iCOMOX_messages.cAXIS_Y]) + \
                    # to_json_array_field(field_name="MagZ", value=mag[iCOMOX_messages.cAXIS_Z]) + \
                    # to_json_array_field(field_name="Mic", value=mic)
            #to_json_field(field_name="FaultCondition", value=motor_state)
        if len(result) > 2:
            result = result[:-2]    # remove the last ",\n"
        result += ' }'
        return result
