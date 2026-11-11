"""Configuration et initialisation matérielle de R.A.L.F."""

import supervisor
import wumons
from available_musics import AvailableMusics
from servo import Servo
from wumons_i2c.dfr_urm09 import DFRobot_URM09

# Hauteurs en cm : premier scotch noir, second scotch noir, repère final.
START_PROPAGATION_HEIGHT = supervisor.get_setting("START_PROPAGATION_HEIGHT", 20)
END_PROPAGATION_HEIGHT = supervisor.get_setting("END_PROPAGATION_HEIGHT", 10)
STOP_PROPAGATION_HEIGHT = supervisor.get_setting("STOP_PROPAGATION_HEIGHT", 5)
SECURITY_LEEWAY = supervisor.get_setting("SECURITY_LEEWAY", 1)

# Puissances PWM (%) ; ne représentent pas des vitesses mesurées.
MOTOR_POWER_BEFORE_RELEASE = supervisor.get_setting("MOTOR_POWER_BEFORE_RELEASE", 100)
MOTOR_POWER_DURING_RELEASE = supervisor.get_setting("MOTOR_POWER_DURING_RELEASE", 100)
MOTOR_POWER_AFTER_RELEASE = supervisor.get_setting("MOTOR_POWER_AFTER_RELEASE", 100)

BRIGHTNESS_DROP_DETECTION = supervisor.get_setting("BRIGHTNESS_DROP_DETECTION", 30)
STOP_BRIGHTNESS_CHANGE_PERCENT = supervisor.get_setting("STOP_BRIGHTNESS_CHANGE_PERCENT", 20)
STOP_DETECTION_MODE = supervisor.get_setting("STOP_DETECTION_MODE", "CONTRAST_OR_DISTANCE")

MAX_INVALID_READINGS = supervisor.get_setting("MAX_INVALID_READINGS", 8)
DISTANCE_SAMPLES = supervisor.get_setting("DISTANCE_SAMPLES", 3)
MAX_HEIGHT_CHANGE_CM_PER_READING = supervisor.get_setting("MAX_HEIGHT_CHANGE_CM_PER_READING", 2)
MAX_MEDIAN_JUMP_CM = supervisor.get_setting("MAX_MEDIAN_JUMP_CM", 4)
BRIGHTNESS_SAMPLES = supervisor.get_setting("BRIGHTNESS_SAMPLES", 20)
BRIGHTNESS_CONFIRM_SAMPLES = supervisor.get_setting("BRIGHTNESS_CONFIRM_SAMPLES", 2)
MIN_BRIGHTNESS_SAMPLES = supervisor.get_setting("MIN_BRIGHTNESS_SAMPLES", 5)
BRIGHTNESS_DETECTION_WINDOW = supervisor.get_setting("BRIGHTNESS_DETECTION_WINDOW", 1)
TRAPDOOR_OPEN_ANGLE = supervisor.get_setting("TRAPDOOR_OPEN_ANGLE", 45)
SENSOR_READ_INTERVAL_S = supervisor.get_setting("SENSOR_READ_INTERVAL_S", 0.05)
MAX_RUN_TIME_S = supervisor.get_setting("MAX_RUN_TIME_S", 120)

NEOPIXEL_BRIGHTNESS = 0.2
NEOPIXEL_AUTO_WRITE = False
TRAPDOOR_GP = wumons.board.GP6
TRAPDOOR_PULSE_RANGE = Servo.BIG_SERVO_PULSE
START_BUTTON_GP = wumons.board.GP28
BRIGHTNESS_SENSOR = wumons.board.GP26

wumons_leds = wumons.NeoPixel(wumons.board.GP22, 2, brightness=NEOPIXEL_BRIGHTNESS, auto_write=NEOPIXEL_AUTO_WRITE)
wumons_music_player = AvailableMusics(wumons.board.GP9)
motor = wumons.DCMotor(wumons.board.GP10, wumons.board.GP11)
trapdoor = Servo(TRAPDOOR_GP, TRAPDOOR_PULSE_RANGE)
brightness_sensor = wumons.Sensor(BRIGHTNESS_SENSOR)
start_button = wumons.Sensor(START_BUTTON_GP)
distance_sensor = None  # Initialisation I2C dans code.py via utils.initialize_ultrasonic_sensor
