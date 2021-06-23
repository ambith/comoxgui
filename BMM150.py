import numpy as np
from scipy.signal import welch
from scipy.signal.windows import hamming
import struct
import iCOMOX_messages

class class_BMM150:
    def __init__(self, quantile_for_noise_floor_estimator, minimum_SNR_for_speed_detection_dB):
        TicksInSamplingPeriod = int(0.5 + (0.003 / (1/32768)))  # number of ticks in 3msec
        self.Fs_Mag = 32768 / TicksInSamplingPeriod # 1/0.003
        self.NFFT_Mag = 512
        self.epsilon = 1E-100
        self.quantile_for_noise_floor_estimation = quantile_for_noise_floor_estimator
        self.minimum_SNR_for_speed_detection = pow(10, minimum_SNR_for_speed_detection_dB/10)      # default threshold of minimum of 20dB above the estimated noise floor density

    def to_PSD(self, mag_x_uT, mag_y_uT, mag_z_uT):
        (freq_mag, Pxxf_Mag_X) = welch(mag_x_uT, self.Fs_Mag, nfft=self.NFFT_Mag, return_onesided=True, detrend=False)
        (freq_mag, Pxxf_Mag_Y) = welch(mag_y_uT, self.Fs_Mag, nfft=self.NFFT_Mag, return_onesided=True, detrend=False)
        (freq_mag, Pxxf_Mag_Z) = welch(mag_z_uT, self.Fs_Mag, nfft=self.NFFT_Mag, return_onesided=True, detrend=False)
        return freq_mag, Pxxf_Mag_X, Pxxf_Mag_Y, Pxxf_Mag_Z

    def readings_to_uTesla(self, raw_samples):
        # Convert the reading to uTesla (by dividing by 16)
        # axis_len = len(raw_samples) // 3
        # mag_x_uTesla = np.array(raw_samples[0:axis_len]) / 16
        # mag_y_uTesla = np.array(raw_samples[axis_len:2*axis_len]) / 16
        # mag_z_uTesla = np.array(raw_samples[2*axis_len:]) / 16
        mag_x_uTesla = np.array(raw_samples[0::3]) / 16
        mag_y_uTesla = np.array(raw_samples[1::3]) / 16
        mag_z_uTesla = np.array(raw_samples[2::3]) / 16
        return mag_x_uTesla, mag_y_uTesla, mag_z_uTesla

    def msg_bytes_to_samples_uTesla(self, payload):
        samples = struct.unpack("<{}h".format(iCOMOX_messages.BMM150_SAMPLES_NUM * 3), payload)
        return self.readings_to_uTesla(raw_samples=samples)

    # Expecting Pxxf values to NOT be in dB. the DC component is not taken into account
    def maximum_of_PSD(self, time_series):
        (freq, Pxxf) = welch(time_series - np.mean(time_series), self.Fs_Mag, nfft=self.NFFT_Mag, return_onesided=True, detrend=False)
        noise_level = np.quantile(Pxxf, self.quantile_for_noise_floor_estimation)
        index_of_max_energy = np.argmax(Pxxf[1:-1]) + 1
        max_energy = Pxxf[index_of_max_energy]
        if max_energy/noise_level >= self.minimum_SNR_for_speed_detection:
            return self.parabola_peak(x1=freq[index_of_max_energy], dx=freq[1], y0=Pxxf[index_of_max_energy-1], y1=Pxxf[index_of_max_energy], y2=Pxxf[index_of_max_energy+1])
            # return freq[index_of_max_energy]
        else:
            return 0.0

    def parabola_peak(self, x1, dx, y0, y1, y2):
        return x1 - (y2 - y0) * dx / (2 * (y2 - 2 * y1 + y0))