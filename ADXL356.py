import numpy as np
from scipy.signal import welch
from scipy.signal.windows import hamming
import struct
import iCOMOX_messages
import messages_utils

class class_ADXL356:
    def __init__(self):
        # Initializing Fs_Acc, MFFT_Acc, window
        Root_clk = 26e6
        ACLKDIV = 8  # ADC clock is determined by Root_clk/ACLKDIV
        SAMPLETIME = 61 #24+10  # AcquisitionTime-1 in terms of ADC clocks
        OverSMP = 4  # Over sampling to increase resolution, or averaging which keeps resolution in digital domain
        NumOfCh = 3 #4  # Number of interleaved ChannelsBitmask
        DLY = 0 #65+63  # Delay at the end of chnnales round, in units of ADC clocks

        if DLY == 0:
            self.Fs_Acc = (Root_clk / ACLKDIV) / ((14 + SAMPLETIME) * OverSMP * NumOfCh)
        else:
            if NumOfCh == 1:
                self.Fs_Acc = (Root_clk / ACLKDIV) / (((14 + SAMPLETIME) * OverSMP) + DLY + 2)
            else:
                self.Fs_Acc = (Root_clk / ACLKDIV) / (((14 + SAMPLETIME) * OverSMP * NumOfCh) + DLY + 3)
        self.NFFT_Acc = 1024 #iCOMOX_messages.ADXL356_SAMPLES_NUM_PER_PIN    # 512
        self.Sensitivity_Acc = 80E-3  # 80mV/g for range of +/-10g. 40mV/g for range of +/-20g. 0g is translated to 900mV
        self.window = hamming(M=self.NFFT_Acc)

    def ADC_readings_to_g_units(self, ADC_samples):
        # convert ADC samples to g units
        return np.array(ADC_samples) * 1.8 / (4096 * self.Sensitivity_Acc)

    def g_units_to_PSD(self, acc_units_g):
        (freq_Acc, Pxxf_Acc) = welch(x=acc_units_g, fs=self.Fs_Acc, window=self.window, noverlap=self.NFFT_Acc/2, nfft=self.NFFT_Acc, return_onesided=True, detrend=False)
        return freq_Acc, Pxxf_Acc

    def msg_bytes_to_samples_g(self, payload):
        unpacked_bytes = messages_utils.ADC_Unpack_12bits_Array(packed_bytes=payload)
        ADC_samples = np.array(struct.unpack("<{}H".format(iCOMOX_messages.ADXL356_SAMPLES_NUM_PER_PIN*3), unpacked_bytes)) - 2048
        ADC_samples = self.ADC_readings_to_g_units(ADC_samples=ADC_samples)
        return ADC_samples[0::3], ADC_samples[1::3], ADC_samples[2::3]
        # axis_len = len(ADC_samples) // 3
        # return ADC_samples[0:axis_len], ADC_samples[axis_len:2*axis_len], ADC_samples[2*axis_len:]

