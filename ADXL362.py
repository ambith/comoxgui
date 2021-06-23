import numpy as np
from scipy.signal import welch
from scipy.signal.windows import hamming
import struct
import iCOMOX_messages
import messages_utils

class class_ADXL362:
    def __init__(self):
        # Initializing Fs_Acc, MFFT_Acc, window
        TicksInSamplingTimePeriod = int(0.5 + (0.0025 / (1/32768)))
        self.Fs_Acc = 32768 / TicksInSamplingTimePeriod    # 400 Hz
        self.NFFT_Acc = 512 #iCOMOX_messages.ADXL362_SAMPLES_NUM_PER_PIN    # 512
        self.Sensitivity_Acc = 1/1024  # LSB = 1/1024 [g] for the +/-2g range
        self.window = hamming(M=self.NFFT_Acc)

    def ADC_readings_to_g_units(self, ADC_samples):
        # convert ADC samples to g units
        return np.array(ADC_samples) * self.Sensitivity_Acc

    def g_units_to_PSD(self, acc_units_g):
        (freq_Acc, Pxxf_Acc) = welch(x=acc_units_g, fs=self.Fs_Acc, window=self.window, noverlap=self.NFFT_Acc/2, nfft=self.NFFT_Acc, return_onesided=True, detrend=False)
        return freq_Acc, Pxxf_Acc

    def msg_bytes_to_samples_g(self, payload):
        ADC_samples = np.array(struct.unpack("<{}h".format(iCOMOX_messages.ADXL362_SAMPLES_NUM*3), payload))
        ADC_samples = self.ADC_readings_to_g_units(ADC_samples=ADC_samples)
        return ADC_samples[0::3], ADC_samples[1::3], ADC_samples[2::3]
        # axis_len = len(ADC_samples) // 3
        # return ADC_samples[0:axis_len], ADC_samples[axis_len:2*axis_len], ADC_samples[2*axis_len:]