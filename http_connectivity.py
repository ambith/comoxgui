# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

import PingPong
import helpers
import iCOMOX_messages
import threading
import datetime
import time
import requests
import common_symbols
#import json

class HTTP_DEVICE_REPORT:
    def __init__(self):
        self.time = time.time()


class HTTP_DEVICE_REPORT_TEMP(HTTP_DEVICE_REPORT):
    def __init__(self, temp):
        super(HTTP_DEVICE_REPORT_TEMP, self).__init__()
        self.temp = temp


class HTTP_DEVICE_REPORT_MAX_ABS_ACC(HTTP_DEVICE_REPORT):
    def __init__(self, max_abs_acc):
        super(HTTP_DEVICE_REPORT_MAX_ABS_ACC, self).__init__()
        self.max_abs_acc = max_abs_acc


class HTTP_DEVICE_REPORT_MOTOR_SPEED(HTTP_DEVICE_REPORT):
    def __init__(self, motor_speed):
        super(HTTP_DEVICE_REPORT_MOTOR_SPEED, self).__init__()
        self.motor_speed = motor_speed


class HTTP_DEVICE_REPORT_FAULT(HTTP_DEVICE_REPORT):
    def __init__(self, fault):
        super(HTTP_DEVICE_REPORT_FAULT, self).__init__()
        self.fault = fault

class HTTP_DEVICE_REPORT_ACC(HTTP_DEVICE_REPORT):
    def __init__(self, acc):
        super(HTTP_DEVICE_REPORT_ACC, self).__init__()
        self.acc = acc

class HTTP_DEVICE_REPORT_MAG(HTTP_DEVICE_REPORT):
    def __init__(self, mag):
        super(HTTP_DEVICE_REPORT_MAG, self).__init__()
        self.mag = mag

class HTTP_DEVICE_REPORT_MIC(HTTP_DEVICE_REPORT):
    def __init__(self, mic):
        super(HTTP_DEVICE_REPORT_MIC, self).__init__()
        self.mic = mic

class HTTP_DEVICE:
    def __init__(self, uniqueID):
        self.uniqueID = uniqueID
        self.PingPong_Temp = PingPong.ClassPingPong()
        self.PingPong_MotorSpeed = PingPong.ClassPingPong()
        self.PingPong_MaxAbsAcc = [PingPong.ClassPingPong(), PingPong.ClassPingPong(), PingPong.ClassPingPong()]
        self.PingPong_Fault = PingPong.ClassPingPong()
        self.PingPong_Acc = [PingPong.ClassPingPong(), PingPong.ClassPingPong(), PingPong.ClassPingPong()]
        self.PingPong_Mag = [PingPong.ClassPingPong(), PingPong.ClassPingPong(), PingPong.ClassPingPong()]
        self.PingPong_Mic = PingPong.ClassPingPong()

    def update_temp(self, temp):
        self.PingPong_Temp.try_push_msg(HTTP_DEVICE_REPORT_TEMP(temp=temp))

    def update_motor_speed(self, motor_speed):
        self.PingPong_MotorSpeed.try_push_msg(HTTP_DEVICE_REPORT_MOTOR_SPEED(motor_speed=motor_speed))

    def update_max_abs_acc(self, axis, max_abs_acc):
        self.PingPong_MaxAbsAcc[axis].try_push_msg(msg=HTTP_DEVICE_REPORT_MAX_ABS_ACC(max_abs_acc=max_abs_acc))

    def update_fault(self, fault):
        self.PingPong_Fault.try_push_msg(HTTP_DEVICE_REPORT_FAULT(fault=fault))

    def update_acc_field(self, axis, data):
        self.PingPong_Acc[axis].try_push_msg(HTTP_DEVICE_REPORT_ACC(acc=data))

    def update_magnetic_field(self, axis, data):
        self.PingPong_Mag[axis].try_push_msg(HTTP_DEVICE_REPORT_MAG(mag=data))

    def update_microphone_field(self, data):
        self.PingPong_Mic.try_push_msg(HTTP_DEVICE_REPORT_MIC(mic=data))

class HTTP_DEVICES_LIST():
    def __init__(self):
        self.http_device_arr = []
        self.timer = None
        self.short_period = datetime.timedelta(minutes=10)  # 10 minutes
        self.long_period = datetime.timedelta(days=1)      # 24 hours
        #self.short_period = datetime.timedelta(seconds=10)
        #self.long_period = datetime.timedelta(seconds=30)
        self.Terminated = False

    def __del__(self):
        if self.http_device_arr is not None:
            for http_device in self.http_device_arr:
                del http_device
        self.http_device_arr = None

    def add_device(self, uniqueID):
        if self.device_by_uniqueID(uniqueID) is not None:
            return
        http_device = HTTP_DEVICE(uniqueID=uniqueID)
        if http_device is not None:
            self.http_device_arr.append(http_device)

    def device_by_uniqueID(self, uniqueID):
        for http_device in self.http_device_arr:
            if http_device.uniqueID == uniqueID:
                return http_device
        return None

    def cloud_update_start(self):
        if not common_symbols.__REST_SUPPORT__:
            return
        if self.timer is None:
            self.Terminated = False
            self.timer = threading.Thread(target=self.SendTelemetry)
            self.timer.start()
        #else:
        #    helpers.OUT("HTTP_DEVICE_LIST.cloud_update_start() tries to start without stop first")

    def cloud_update_stop(self):
        self.Terminated = True
        del self.timer
        self.timer = None

    def SendTelemetry(self):
        # short message items
        max_abs_acc = [None]*3
        # long message items
        acc = [None]*3
        mag = [None]*3
        mic = None
        next_short_msg_update = datetime.datetime.now()
        next_long_msg_update = datetime.datetime.now()
        while not self.Terminated:
            # short sleep and then checking if transmission time has arrived.
            # The sleep must be short enough in case the application terminates before the next transmission time arrives.
            time.sleep(10)

            for http_device in self.http_device_arr:
                new_data_for_short_msg_available = False
                new_data_for_long_msg_available = False

                # Get new temperature if available
                temp = http_device.PingPong_Temp.try_pop_msg()
                if temp is not None:
                    temp = temp.temp
                    if temp < 0:
                        temp_state = -1
                    elif temp > 70:
                        temp_state = 1
                    else:
                        temp_state = 0
                    new_data_for_short_msg_available = True
                else:
                    temp_state = None

                # Get new motor speed if available
                motor_speed = http_device.PingPong_MotorSpeed.try_pop_msg()
                if motor_speed is not None:
                    motor_speed = motor_speed.network_frequency_Hz
                    new_data_for_short_msg_available = True

                # Get new acelerometer data for each axis if available
                for axis in range(iCOMOX_messages.cAXIS_X, iCOMOX_messages.cAXIS_Z+1):
                    max_abs_acc[axis] = http_device.PingPong_MaxAbsAcc[axis].try_pop_msg()
                    if max_abs_acc[axis] is not None:
                        max_abs_acc[axis] = max_abs_acc[axis].max_abs_acc
                        new_data_for_short_msg_available = True

                # Get the new motor state if available
                # motor_state = http_device.PingPong_Fault.try_pop_msg()
                # if motor_state is not None:
                #     motor_state = motor_state.fault
                #     new_data_for_short_msg_available = True

                # Get new accelerometer data for each axis if available
                for axis in range(iCOMOX_messages.cAXIS_X, iCOMOX_messages.cAXIS_Z+1):
                    acc[axis] = http_device.PingPong_Acc[axis].try_pop_msg()
                    if acc[axis] is not None:
                        acc[axis] = acc[axis].acc
                        new_data_for_long_msg_available = True

                # Get new magnetometer data for each axis if available
                for axis in range(iCOMOX_messages.cAXIS_X, iCOMOX_messages.cAXIS_Z+1):
                    mag[axis] = http_device.PingPong_Mag[axis].try_pop_msg()
                    if mag[axis] is not None:
                        mag[axis] = mag[axis].mag
                        new_data_for_long_msg_available = True

                # Get new microphone data
                mic = http_device.PingPong_Mic.try_pop_msg()
                if mic is not None:
                    new_data_for_long_msg_available = True

                # send short message
                if (next_short_msg_update <= datetime.datetime.now()) and (new_data_for_short_msg_available):
                    next_short_msg_update += self.short_period  # next time to send short message

                    telemetry = self.build_json_struct(temp=temp, temp_state=temp_state, motor_speed=motor_speed, max_abs_acc=max_abs_acc, motor_state=None)
                    headers = {'Content-type': 'application/json'}
                    device_id = http_device.uniqueID
                    url = "https://my.rayven.io:8082/api/main?uid=181829f4d6af889b418ababf3428c5fc0044&deviceid={}".format(helpers.u8s_to_str(arr=device_id, separator="", prefix=""))
                    response = requests.post(url, data=telemetry, headers=headers)
                    helpers.OUT("send short telemetry: \"{}\", to {}, with response {}".format(telemetry, url, response))

                # send long message
                if (next_long_msg_update <= datetime.datetime.now()) and (new_data_for_long_msg_available):
                    next_long_msg_update += self.long_period    # set the next time to send long message

                    telemetry = self.build_json_struct(acc=acc, mag=mag, mic=mic)
                    headers = {'Content-type': 'application/json'}
                    device_id = http_device.uniqueID
                    url = "https://my.rayven.io:8082/api/main?uid=1818c2dd6f4027f64fcc8b5f3a024afbdb47&deviceid={}".format(helpers.u8s_to_str(arr=device_id, separator="", prefix=""))
                    response = requests.post(url, data=telemetry, headers=headers)
                    helpers.OUT("send long telemetry: \"{}\", to {}, with response {}".format(telemetry, url, response))

                # if new_data_for_short_msg_available:
                #     #helpers.OUT("Sending telemetry..")
                #     telemetry = self.build_json_struct(temp=temp, temp_state=temp_state, network_frequency_Hz=network_frequency_Hz, max_abs_acc=max_abs_acc, motor_state=motor_state, acc=acc, mag=mag)
                #     #helpers.OUT(telemetry)
                #     headers = {'Content-type': 'application/json'}
                #     device_id = http_device.uniqueID
                #     url = "https://my.rayven.io:8082/api/main?uid=17054b5a87ab48cd480e86f9c88f1c54783c&deviceid={}".format(helpers.u8s_to_str(arr=device_id, separator="", prefix=""))
                #     response = requests.post(url, data=telemetry, headers=headers)
                #     helpers.OUT("send telemetry: \"{}\", to {}, with response {}".format(telemetry, url, response))

    def build_json_struct(self, temp=None, temp_state=None, motor_speed=None, max_abs_acc=[None]*3, motor_state=None, acc=[None]*3, mag=[None]*3, mic=None):
        def to_json_field(field_name, value):
            if value is None:
                return ""
            return '\r\n"' + field_name + '\": ' + str(value) + ", "

        def to_json_binary_field(field_name, value):
            if value is None:
                return ""
            return '\r\n\"' + field_name + '\": \"' + value.hex() + "\", "

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
                    to_json_field(field_name="MotorState", value=motor_state) + \
                    to_json_binary_field(field_name="AccX", value=acc[iCOMOX_messages.cAXIS_X]) + \
                    to_json_binary_field(field_name="AccY", value=acc[iCOMOX_messages.cAXIS_Y]) + \
                    to_json_binary_field(field_name="AccZ", value=acc[iCOMOX_messages.cAXIS_Z]) + \
                    to_json_binary_field(field_name="MagX", value=mag[iCOMOX_messages.cAXIS_X]) + \
                    to_json_binary_field(field_name="MagY", value=mag[iCOMOX_messages.cAXIS_Y]) + \
                    to_json_binary_field(field_name="MagZ", value=mag[iCOMOX_messages.cAXIS_Z]) + \
                    to_json_binary_field(field_name="Mic", value=mic)
                    #to_json_field(field_name="FaultCondition", value=motor_state)
        if len(result) > 2:
            result = result[:-2]    # remove the last ",\n"
        result += '\r\n}'
        return result
