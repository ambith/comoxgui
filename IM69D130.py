import numpy as np
from scipy.signal import welch
from scipy.signal.windows import hamming
from scipy.signal.filter_design import butter
from scipy.signal import sosfilt
import struct
import iCOMOX_messages


class class_IM69D130:
    def __init__(self):
        # Initializing Fs_Mic, MFFT_Mic, Scaling_Mic, window
        Root_clk = 26e6
        CLKDIV = 10  # SPORT clock is determined by Root_clk/(2*(SPORT_DIV_xCLKDIV+1))
        self.Fs_Mic = Root_clk / (2*64*CLKDIV)  # 64 bits clock provide 2 samples: left & right. We further divide the SPORT clock by 2 to get 20.3125KSPS
        self.NFFT_Mic = 512
        self.Scaling_Mic = 10**(130/20)/32768   #2.8 * 1E2
        self.window = hamming(M=self.NFFT_Mic)
        # self.sos = butter(100, 300.0, 'hp', fs=self.Fs_Mic, output='sos') # 10th order high pass filter, with half BW @28Hz

    #def Mic_readings_to_SPL_units(self, Mic_samples):
        # remove any DC components and scale the samples to SPL units

        # For IM69D130 (16 MSBs out of 20 bits, as we currently truncates the 4 LSBs):
        # Y_AOP = 130 dBSPL = 3,162,277.66 SPL for X_AOP = 32768 LSB
        # Y0 = 0 SPL, for X0 = 0 LSB
        # Now we can fit a linear curve using 2 known points:
        # Y - Y0 = (X - X0)*(Y_AOP - Y0)/(X_AOP - X0)
        # Solving it results in the following linear curve:
        # Y[SPL] = 96.505[SPL/LSB] * X[LSB]
        #return self.Scaling_Mic * (np.array(Mic_samples) - np.mean(Mic_samples))
        #return self.Scaling_Mic * np.array(Mic_samples)

    def to_PSD(self, mic_units_spl):
        (freq_Acc, Pxxf_Mic) = welch(x=mic_units_spl, fs=self.Fs_Mic, window=self.window, noverlap=self.NFFT_Mic/2, nfft=self.NFFT_Mic, return_onesided=True, detrend=False)
        # Pxxf_Mic[0:2] = np.mean(Pxxf_Mic[2:])
        return freq_Acc, Pxxf_Mic

    def msg_bytes_to_samples_SPL(self, payload):
        unscaled_samples = struct.unpack("<{}h".format(iCOMOX_messages.IM69D130_SAMPLES_NUM), payload)
        # filtered = sosfilt(self.sos, unscaled_samples)
        # return self.Scaling_Mic * np.array(filtered)
        return self.Scaling_Mic * (np.array(unscaled_samples) - np.mean(unscaled_samples))  #- np.mean(unscaled_samples))
