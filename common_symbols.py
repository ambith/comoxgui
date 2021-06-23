import configparser
import helpers

__VERSION_CODE__ = 0x020800
__VERSION__ = "{}.{}.{}".format(__VERSION_CODE__ >> 16, (__VERSION_CODE__ >> 8) & 0xFF, __VERSION_CODE__ & 0xFF)

__FAULT_DETECTION_ALGORITHM_INDEX__ = 1

__REST_SUPPORT__ = False

__PRODUCTION_SUPPORT__ = False
__ADXL1002_GRAPH_SUPPORT__ = False

# Configuration variables that should be read from an external configuration file
BMM150_quantile_for_noise_floor_estimator   = 0.25
BMM150_minimum_SNR_for_speed_detection_dB   = 20   # 20dB of minimum threshold above the noise floor to detect synchronous speed

ASYNC_MOTOR_number_of_poles_pairs           = 2
ASYNC_MOTOR_slip_factor_percentages         = 0.0

IOTC_enabled = False
IOTC_interval_between_reports_seconds       = 150.0 # For 20,000 messages/month the maximum interval is 133.92 seconds
IOTC_scopeID        = None
IOTC_deviceID       = None
IOTC_primaryKey     = None
IOTC_secondaryKey   = None

REST_enabled                                = False
REST_interval_between_reports_seconds       = 30.0
REST_Content_type                           = "application/json"
REST_URL                                    = "https://my.rayven.io:8082/api/main?uid=181829f4d6af889b418ababf3428c5fc0044&deviceid="

def InitializeConfiguration():
    global BMM150_minimum_SNR_for_speed_detection_dB
    global BMM150_quantile_for_noise_floor_estimator

    global ASYNC_MOTOR_number_of_poles_pairs
    global ASYNC_MOTOR_slip_factor_percentages

    global IOTC_enabled
    global IOTC_interval_between_reports_seconds
    global IOTC_scopeID
    global IOTC_deviceID
    global IOTC_primaryKey
    global IOTC_secondaryKey

    global REST_enabled
    global REST_interval_between_reports_seconds
    global REST_Content_type
    global REST_URL

    config = configparser.ConfigParser(allow_no_value=False)
    config.read(filenames="iCOMOX_GUI.ini")

    BMM150_quantile_for_noise_floor_estimator = config.getfloat(section="BMM150", option="BMM150_quantile_for_noise_floor_estimator", fallback=0.25)
    BMM150_minimum_SNR_for_speed_detection_dB = config.getfloat(section="BMM150", option="BMM150_minimum_SNR_for_speed_detection_dB", fallback=25)

    ASYNC_MOTOR_number_of_poles_pairs = config.getint(section="ASYNC_MOTOR", option="ASYNC_MOTOR_number_of_poles_pairs", fallback=2)
    ASYNC_MOTOR_slip_factor_percentages = config.getfloat(section="ASYNC_MOTOR", option="ASYNC_MOTOR_slip_factor_percentages", fallback=0.0)

    IOTC_enabled = config.getboolean(section="IOTC", option="IOTC_enabled", fallback=False)
    IOTC_interval_between_reports_seconds = config.getfloat(section="IOTC", option="IOTC_interval_between_reports_seconds", fallback=150.0)
    if IOTC_enabled:
        IOTC_scopeID = config.get(section="IOTC", option="IOTC_scopeID", fallback=None)
        IOTC_deviceID = config.get(section="IOTC", option="IOTC_deviceID", fallback="")
        IOTC_primaryKey = bytearray.fromhex(config.get(section="IOTC", option="IOTC_primaryKey", fallback=""))
        IOTC_secondaryKey = bytearray.fromhex(config.get(section="IOTC", option="IOTC_secondaryKey", fallback=""))
    else:
        IOTC_scopeID = ""
        IOTC_deviceID = ""
        IOTC_primaryKey = bytearray()
        IOTC_secondaryKey = bytearray()

    REST_enabled = config.getboolean(section="REST", option="REST_enabled", fallback=False)
    REST_interval_between_reports_seconds = config.getfloat(section="REST", option="REST_interval_between_reports_seconds", fallback=150.0)
    REST_Content_type = config.get(section="REST", option="REST_Content-type", fallback="application/json")
    REST_URL = config.get(section="REST", option="REST_URL", fallback="https://my.rayven.io:8082/api/main?uid=181829f4d6af889b418ababf3428c5fc0044&deviceid=")

    del config