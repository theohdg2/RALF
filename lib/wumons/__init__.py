# SPDX-FileCopyrightText: 2024 Philippe Fortemps
#
# SPDX-License-Identifier: MIT
#
# MicroPython uasyncio module
# MIT license; Copyright (c) 2024 Philippe Fortemps
#
# This code comes from MicroPython, and has not been run through black or pylint there.
# Altering these files significantly would make merging difficult, so we will not use
# pylint or black.
# pylint: skip-file
# fmt: off

import board
from busio import I2C

from wumons.button import DigitalButton, AnalogButton
from wumons.motor import Servo, DCMotor
from wumons.music import Music
from wumons.neopixel import NeoPixel
from wumons.sensor import Sensor


def help():
    print("With this python package, you can")
    print("* use buttons (Digital, Analog...); for more help, call wumons.button.help()")
    print("* use sensors (Digital, Analog...); for more help, call wumons.sensor.help()")
    print("* use sets of LEDs (NeoPixels); for more help, call wumons.neopixel.help()")
    print("* use motors (DC motors, servos...); for more help, call wumons.motor.help()")
    print("* make noise or music; for more help, call wumons.music.help()")
    print("* connect additional equipments on I2C; for more help, call wumons.i2c.help()")


i2c = I2C(board.GP17, board.GP16)  # uses board.SCL and board.SDA
