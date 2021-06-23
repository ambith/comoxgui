import numpy as np
from scipy.signal import welch
from scipy.signal.windows import hamming
import struct
import iCOMOX_messages
import messages_utils

class class_ADXL1002:
    def __init__(self):
        # Initializing Fs_Acc, MFFT_Acc, window
        Root_clk = 26e6
        ACLKDIV = 4
        SAMPLETIME = 51
        OverSMP = 4
        DLY = 0

        if DLY == 0:
            self.Fs_Acc = (Root_clk / ACLKDIV) / ((14 + SAMPLETIME) * OverSMP)
        else:
            self.Fs_Acc = (Root_clk / ACLKDIV) / ((14 + SAMPLETIME) * OverSMP + DLY + 2)
        self.NFFT_Acc = 512 #iCOMOX_messages.ADXL1002_SAMPLES_NUM_PER_PIN    # 512
        self.Sensitivity_Acc = 0.9/50 # = 0.9[V]/50[g] = 0.018 [V/g] = 18 [mV/g]
        self.window = hamming(M=self.NFFT_Acc)

    def ADC_readings_to_g_units(self, ADC_samples):
        # convert ADC samples to g units. It is based on the following equation: V_ADC = 1.8 * ADC / 4096 and also V_ADC = 0.9 - Sensitivity_Acc * a = 0.9 - 0.018 * a
        # so we get that a[g] = 50 - 25*ADC/1024
        # The actual formula should be written with + instead of -, due to the inverting OPA:
        # a[g] = -50 + 25*ADC/1024
        samples = -50 + 25*np.array(ADC_samples)/1024   #(0.9/self.Sensitivity_Acc) * (1 - np.array(ADC_samples)/2048)
        # samples -= np.mean(samples)
        return  samples

    def g_units_to_PSD(self, acc_units_g):
        (freq_Acc, Pxxf_Acc) = welch(x=acc_units_g, fs=self.Fs_Acc, window=self.window, noverlap=self.NFFT_Acc/2, nfft=self.NFFT_Acc, return_onesided=True, detrend=False)
        return freq_Acc, Pxxf_Acc

    def msg_bytes_to_samples_g(self, payload):
        unpacked_bytes = messages_utils.ADC_Unpack_12bits_Array(packed_bytes=payload)
        ADC_samples = np.array(struct.unpack("<{}h".format(iCOMOX_messages.ADXL1002_SAMPLES_NUM), unpacked_bytes))
        ADC_samples = self.ADC_readings_to_g_units(ADC_samples=ADC_samples)
        return ADC_samples
