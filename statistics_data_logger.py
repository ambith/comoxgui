import math

# These constants are used with the Class_statistical_data_logger class to access specific random variable statistics.
# The constants are served as the data_arr_input parameter in the:
# ClassStatisticalDataLogger.update_statistics()
# ClassStatisticalDataLogger.retrieve_statistics()
# ClassStatisticalDataLogger.is_fresh_data_available()
stat_data_logger_index_lowpower_acc_x   = 0
stat_data_logger_index_lowpower_acc_y   = 1
stat_data_logger_index_lowpower_acc_z   = 2
stat_data_logger_index_acc_x            = 3
stat_data_logger_index_acc_y            = 4
stat_data_logger_index_acc_z            = 5
stat_data_logger_index_mag_x            = 6
stat_data_logger_index_mag_y            = 7
stat_data_logger_index_mag_z            = 8
stat_data_logger_index_mic              = 9
stat_data_logger_index_temp             = 10
stat_data_logger_index_wideband_acc_x   = 11


# The ClassRandomVarStatisticalData class provides a mechanism to store the statistical data of a single
# random variable, without storing the samples.
# The main difficulty in doing it for the statistics that we calculate is to update
# the standard deviation in a numerically stable way. This difficulty is solved by using the Welford's algorithm.
# The statistics we keep are:
# 1. (infinite population, biased for a finite one) standard deviation
# 2. mean
# 3. samples count
# 4. minimum sample value
# 5. maximum samples value
class ClassRandomVarStatisticalData:
    def __init__(self, name):
        self.name = name  # help debugging
        self.min = math.inf
        self.max = -math.inf
        self.mean = 0.0
        self.std = 0.0
        self.count = 0
        self.__M2__ = 0.0

    def clear(self):
        self.min = math.inf
        self.max = -math.inf
        self.mean = 0.0
        self.std = 0.0
        self.count = 0
        self.__M2__ = 0.0

    def update(self, samples):
        if len(samples) == 0:
            return
        # Update the min and max of the samples accumulated so far
        min_of_samples = min(samples)
        max_of_samples = max(samples)
        if min_of_samples < self.min:
            self.min = min_of_samples
        if max_of_samples > self.max:
            self.max = max_of_samples
        # Applying the Welford's algorithm in order to calculate the standard deviation of streaming samples
        for sample in samples:
            # Welford's algorithm
            self.count += 1
            delta = sample - self.mean
            self.mean += delta / self.count
            delta2 = sample - self.mean
            self.__M2__ += delta * delta2
        self.std = math.sqrt(self.__M2__ / self.count)


# The ClassStatisticalDataLogger class is a wrapper to access several ClassRandomVarStatisticalData classes
class ClassStatisticalDataLogger:
    def __init__(self):
        self.data_arr = []
        self.data_arr.append(ClassRandomVarStatisticalData(name="Low power Acc X"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Low power Acc Y"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Low power Acc Z"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Acc X"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Acc Y"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Acc Z"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Mag X"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Mag Y"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Mag Z"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Mic"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Temp"))
        self.data_arr.append(ClassRandomVarStatisticalData(name="Wideband Acc X"))

        self.fresh_statistics_bitmask = 0

    def clear(self):
        for data in self.data_arr:
            data.clear()
        self.fresh_statistics_bitmask = 0

    def is_fresh_data_available(self, data_arr_index):
        if (data_arr_index < 0) or (data_arr_index >= len(self.data_arr)):
            raise Exception("ClassStatisticalDataLogger.is_fresh_data_available(): wrong data_arr_index")
        return 0 != (self.fresh_statistics_bitmask & (1 << data_arr_index))

    def update_statistics(self, data_arr_index, new_samples):
        if (data_arr_index < 0) or (data_arr_index >= len(self.data_arr)):
            raise Exception("ClassStatisticalDataLogger.update_statistics(): wrong data_arr_index")
        if len(new_samples) > 0:
            self.data_arr[data_arr_index].update(new_samples)
            self.fresh_statistics_bitmask |= 1 << data_arr_index

    def retrieve_statistics(self, data_arr_index):
        if (data_arr_index < 0) or (data_arr_index >= len(self.data_arr)):
            raise Exception("ClassStatisticalDataLogger.retrieve_statistics(): wrong data_arr_index")
        self.fresh_statistics_bitmask &= ~(1 << data_arr_index)
        return [self.data_arr[data_arr_index].mean,
                self.data_arr[data_arr_index].std,
                self.data_arr[data_arr_index].min,
                self.data_arr[data_arr_index].max,
                self.data_arr[data_arr_index].count]

    def name_to_index(self, name):
        for i in range(0, len(self.data_arr)):
            if self.data_arr[i].name == name:
                return i
        return -1
