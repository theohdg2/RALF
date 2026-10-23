# import wumons libraries
import wumons
from servo import Servo
from wumons_i2c.dfr_urm09 import DFRobot_URM09

#define global variables
NEOPIXEL_BRIGHTNESS = 0.2
NEOPIXEL_AUTO_WRITE = False
TRAPDOOR_GP = wumons.board.GP6
TRAPDOOR_PULSE_RANGE = Servo.BIG_SERVO_PULSE

START_BUTTON_GP = wumons.board.GP28
BRIGHTNESS_SENSOR = wumons.board.GP26

# define Wukong Leds
wumons_leds = wumons.NeoPixel(wumons.board.GP22,2, brightness=NEOPIXEL_BRIGHTNESS, auto_write=NEOPIXEL_AUTO_WRITE)
# define Wukong Music Player
wumons_music_player = wumons.Music(wumons.board.GP9)
#   Connect the four possible motors
motor = wumons.DCMotor(wumons.board.GP10, wumons.board.GP11)
# Connect the trapdoor servo
trapdoor = Servo(TRAPDOOR_GP, TRAPDOOR_PULSE_RANGE)
# Connect the brightness sensor
brightness_sensor = wumons.Sensor(BRIGHTNESS_SENSOR)
# connect the button sensor wich starts the robot
start_button = wumons.Sensor(START_BUTTON_GP)

""" 
    :var distance_sensor: DFRobot_URM09
    :type distance_sensor: DFRobot_URM09
    :description: This variable is used to store the instance of the DFRobot_URM09 ultrasonic sensor. It will be initialized in the main code and used to measure distances.
"""
distance_sensor: DFRobot_URM09 | None = None