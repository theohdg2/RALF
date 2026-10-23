# -*- coding: utf-8 -*
from adafruit_bus_device.i2c_device import I2CDevice

class DFRobot_RGB_Button(object):
    ## rgbbutton default i2c addr
    RGBBUTTON_DEFAULT_I2C_ADDR  = 0x2A
    ## RGBButton chip ID
    RGBBUTTON_PART_ID           = 0x43DF

    # RGBButton register address
    ## RGBButton I2C ADDR REG
    RGBBUTTON_I2C_ADDR_REG      = 0x00

    ## RGBButton RED REG
    RGBBUTTON_RED_REG           = 0x01
    ## RGBButton GREEN REG
    RGBBUTTON_GREEN_REG         = 0x02
    ## RGBButton BLUE REG
    RGBBUTTON_BLUE_REG          = 0x03

    ## RGBBUTTON BUTTON SIGNAL REG
    RGBBUTTON_BUTTON_SIGNAL_REG = 0x04

    ## RGBButton PID MSB REG
    RGBBUTTON_PID_MSB_REG       = 0x09
    ## RGBButton PID LSB REG
    RGBBUTTON_PID_LSB_REG       = 0x0A

    #BUTTON_DEFAULT_I2C_ADDR = const(0x2A)
    #BUTTON_PART_ID = const(0x43DF)
    #BUTTON_PID_MSB_REG = const(0x09)
    #BUTTON_COLOR_REG = const(0x01)
    #BUTTON_BUTTON_SIGNAL_REG = const(0x04)

    def __init__(self, i2c, address=RGBBUTTON_DEFAULT_I2C_ADDR):
        self.i2c_device = I2CDevice(i2c, address)
        self.address = address


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

    def begin(self) -> bool:
        """
        Initialise the button
        :return: bool
        """
        chip_id0 = self.__get_item__(self.RGBBUTTON_PID_MSB_REG)
        chip_id1 = self.__get_item__(self.RGBBUTTON_PID_MSB_REG+1)
        # chip_id = self._read_reg(self.BUTTON_PID_MSB_REG, 2)
        if self.RGBBUTTON_PART_ID != ((chip_id0 << 8) | chip_id1):
            return False
        else:
            return True

    def set_RGB_color(self, *args):
        rgb_buf = [0] * 3
        if 1 == len(args):
          rgb_buf[0] = (args[0] >> 16) & 0xFF
          rgb_buf[1] = (args[0] >> 8) & 0xFF
          rgb_buf[2] = args[0] & 0xFF
        elif 3 == len(args):
          rgb_buf[0] = args[0]
          rgb_buf[1] = args[1]
          rgb_buf[2] = args[2]
        self.__set_item__(self.RGBBUTTON_RED_REG, rgb_buf[0])
        self.__set_item__(self.RGBBUTTON_GREEN_REG, rgb_buf[1])
        self.__set_item__(self.RGBBUTTON_BLUE_REG, rgb_buf[2])

    def is_pressed(self):
        '''!
          @brief 获取模块按键状态
          @return 模块当前的按键状态:
          @retval   true - 按键按下
          @retval   false - 按键未按下
        '''
        button_status = False
        if 1 == self.__get_item__(self.RGBBUTTON_BUTTON_SIGNAL_REG) :
          button_status = True
        return button_status
