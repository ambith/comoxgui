import struct

class class_ADT7410:
    def readings_to_Celsius(self, raw_sample):
        return raw_sample/128

    def msg_bytes_to_sample_Celsius(self, payload):
        [temp] = struct.unpack("<h", payload)
        return self.readings_to_Celsius(raw_sample=temp)  # ADT7410 temperature data
