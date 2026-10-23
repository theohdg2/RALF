# -*- coding: utf-8 -*
from adafruit_bus_device.i2c_device import I2CDevice


class DFRobot_URM09(object):
    # Default address
    DEFAULT_ADDRESS = const(0x11)
    # automatic mode
    MEASURE_MODE_AUTOMATIC = const(0x80)
    # passive mode
    MEASURE_MODE_PASSIVE = const(0x00)
    # passive mode configure registers
    CMD_DISTANCE_MEASURE = const(0x01)
    # Ranging from 500
    MEASURE_RANG_500 = const(0x20)
    # Ranging from 300
    MEASURE_RANG_300 = const(0x10)
    # Ranging from 150
    MEASURE_RANG_150 = const(0x00)

    def __init__(self, i2c, address=DEFAULT_ADDRESS):
        self.i2c_device = I2CDevice(i2c, address)
        self.address = address
        if self.__get_item__(0x01) != 0x01:
            raise RuntimeError("Could not find URM09. Is it connected and powered ?")
        self.set_mode_range()

    def __get_item__(self, registerIndex):
        buf = bytearray(2)
        buf[0] = registerIndex
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return buf[1]

    def __set_item__(self, registerIndex, value):
        buf = bytearray(2)
        buf[0] = registerIndex
        buf[1] = value
        with self.i2c_device as i2c:
            i2c.write(buf)

    def set_mode_range(
        self, measureMode=MEASURE_MODE_AUTOMATIC, measureRange=MEASURE_RANG_500
    ):
        # Config the device
        self.__set_item__(0x07, (measureMode | measureRange) & 0xFF)

    def get_temperature(self):
        realTemp = (float)(
            ((self.__get_item__(0x05) << 8) + self.__get_item__(0x06)) / 10
        )
        return realTemp

    def start_distance_deasurement(self):
        # start measurement of distance, if the sensor is in manual mode
        self.__set_item__(0x08, self.CMD_DISTANCE_MEASURE)

    def get_distance(self):
        realDist = (self.__get_item__(0x03) << 8) + self.__get_item__(0x04)
        if realDist >= 32768:
            realDist = realDist - 65536
        return realDist
