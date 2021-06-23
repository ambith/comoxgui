import numpy as np
from scipy.signal import welch
from scipy.signal.windows import hamming
import struct
import iCOMOX_messages
import messages_utils

class class_ADXL356_SMIP:
    def __init__(self):
        # Initializing Fs_Acc, MFFT_Acc, window
        Root_clk = 26e6
        ACLKDIV = 2  # ADC clock is determined by Root_clk/ACLKDIV
        SAMPLETIME = 255    #116  # AcquisitionTime-1 in terms of ADC clocks
        OverSMP = 1  # No over sample, No averaging in digital domain
        NumOfCh = 1  # Number of interleaved ChannelsBitmask
        DLY = 0  # Delay at the end of channels round, in units of ADC clocks

        if (DLY == 0):
            self.Fs_Acc = (Root_clk / ACLKDIV) / ((14 + SAMPLETIME) * OverSMP * NumOfCh)
        else:
            if NumOfCh == 1:
                self.Fs_Acc = (Root_clk / ACLKDIV) / ((14 + SAMPLETIME) * OverSMP * NumOfCh + DLY + 2)
            else:
                self.Fs_Acc = (Root_clk / ACLKDIV) / ((14 + SAMPLETIME) * OverSMP * NumOfCh + DLY + 3)
        self.NFFT_Acc = iCOMOX_messages.ADXL356_SMIP_SAMPLES_NUM_PER_PIN    # 512
        self.Sensitivity_Acc = 80E-3  # 80mV/g for range of +/-10g. 40mV/g for range of +/-20g. 0g is translated to 900mV
        self.window = hamming(M=self.NFFT_Acc)

    def ADC_readings_to_g_units(self, ADC_samples):
        # convert ADC samples to g units
        return np.array(ADC_samples) * 1.8 / (4096 * self.Sensitivity_Acc)

    def g_units_to_PSD(self, acc_units_g):
        (freq_Acc, Pxxf_Acc) = welch(x=acc_units_g, fs=self.Fs_Acc, window=self.window, noverlap=self.NFFT_Acc/2, nfft=self.NFFT_Acc, return_onesided=True, detrend=False)
        return freq_Acc, Pxxf_Acc

    def ADXL356_UnpackBytes(self, packed_bytes):  # arranging the compressed 12 bits in 16 bits elements (4 MSB bits of each element are 0)
        unpacked_bytes = bytearray(iCOMOX_messages.ADXL356_SMIP_SAMPLES_NUM_PER_PIN * 2)
        src_index = 0  # pointer to compress_samples
        dst_index = 0  # pointer to unpacked_bytes
        for i in range(0, iCOMOX_messages.ADXL356_SMIP_SAMPLES_NUM_PER_PIN // 2):  # iterate on the total number of samples divided by 2
            unpacked_bytes[dst_index] = packed_bytes[src_index]
            unpacked_bytes[dst_index + 1] = packed_bytes[src_index + 1] & 0x0F
            unpacked_bytes[dst_index + 2] = (packed_bytes[src_index + 1] >> 4) + ((packed_bytes[src_index + 2] & 0x0F) << 4)
            unpacked_bytes[dst_index + 3] = packed_bytes[src_index + 2] >> 4
            dst_index += 4
            src_index += 3
        return unpacked_bytes

    def msg_bytes_to_samples_g(self, payload):
        unpacked_bytes = messages_utils.ADC_Unpack_12bits_Array(packed_bytes=payload)
        ADC_samples = np.array(struct.unpack("<{}h".format(iCOMOX_messages.ADXL356_SMIP_SAMPLES_NUM_PER_PIN), unpacked_bytes)) - 2048
        return self.ADC_readings_to_g_units(ADC_samples=ADC_samples)
