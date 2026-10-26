import time

import settings
from settings import *
from wumons import Sensor, I2C

"""
    :function colour_from_rgb: int
    :description: This function converts RGB values (0-255) to a single integer color value.
"""


def colour_from_rgb(r, g, b):
    r = round(min(255, max(0, r)))
    g = round(min(255, max(0, g)))
    b = round(min(255, max(0, b)))
    return (r << 16) | (g << 8) | b


"""
    :function forward: None
    :description: This function makes the robot move forward at a given speed (0-100) in percentage.
"""


def forward(speed: int = 100):
    speed = round(min(100, max(0, speed)))
    motor.set_speed(speed)


"""
    :function backward: None
    :description: This function makes the robot move backward at a given speed (0-100) in percentage.
"""


def backward(speed: int = 100):
    speed = round(min(100, max(0, speed)))
    motor.set_speed(-speed)


"""
    :function stop: None
    :description: This function stops the robot by setting the motor speed to 0.
"""


def stop():
    motor.set_speed(0)


"""
    :function set_trapdoor_position: bool
    :description: This function sets the position of the trapdoor to a given angle (0-180) in degrees.
"""


def set_trapdoor_position(degrees: int) -> bool:
    if degrees < 0 or degrees > 180:
        return False
    trapdoor.set_angle(degrees)
    return True


"""
    :function is_button_pressed: bool
    :description: This function checks if a button is pressed based on its sensor value and precision.
"""


def is_button_pressed(button: Sensor, precision: int = 40000) -> bool:
    return button.get_value() <= precision


"""
    :function initialize_ultrasonic_sensor: bool
    :description: This function initializes the ultrasonic sensor and returns True if successful, False otherwise.
"""


def initialize_ultrasonic_sensor() -> bool:
    try:
        settings.distance_sensor = DFRobot_URM09(I2C)
        return True
    except Exception as e:
        print(f"Error initializing ultrasonic sensor: {e}")
        return False


"""
    :function play_music: None
    :description: This function plays a given music sequence using the wukong Music Player.
"""


def play_music(music_sequence: list):
    if not isinstance(music_sequence, list):
        raise TypeError("Invalid music sequence. Expected a list of notes.")
    wumons_music_player.play(music_sequence)


"""
    :function get_height: int|None
    :description: This function retrieves the height measured by the distance sensor. If the distance sensor is not initialized, it returns None. Otherwise, it returns the distance in centimeters as an integer.
"""


def get_height(test_mode: bool = False) -> int | None:
    if test_mode:
        import simulation
        return simulation.get_height()
    # Get the height from the distance sensor
    sensor = settings.distance_sensor
    return sensor.get_distance() if sensor is not None else None


def get_brightness(test_mode: bool = False) -> float | None:
    if test_mode:
        import simulation
        return simulation.get_brightness()
    return brightness_sensor.get_value() / 65535 * 100


def read_sensor_snapshot(test_mode: bool = False):
    """Return a simple snapshot of the current sensed values in the same units used by the robot."""
    return {
        "brightness_percent": get_brightness(test_mode=test_mode),
        "height_cm": get_height(test_mode=test_mode),
    }


"""
    :function error_leds_state: None
    :description: This function sets the LEDs to an error state by blinking red. It fills the LEDs with red color, shows the change
"""


def error_leds_state():
    # Set the LEDs to an error state (blinking red)
    wumons_leds.fill(colour_from_rgb(255, 0, 0))  # Red
    wumons_leds.show()
    time.sleep(0.5)


"""
    :function waiting_leds_state: None
    :description: This function sets the LEDs to a waiting state by blinking blue and white.
"""


def waiting_leds_state():
    # Set the LEDs to a waiting state (solid blue)
    wumons_leds.fill(colour_from_rgb(0, 0, 255))  # Blue
    wumons_leds.show()


def initialized_leds_state():
    # Set the LEDs to an initialized state (solid green)
    wumons_leds.fill(colour_from_rgb(0, 255, 0))  # Green
    wumons_leds.show()


def in_action_leds_state():
    # Set the LEDs to an in_action state (solid orange)
    wumons_leds.fill(colour_from_rgb(255, 165, 0))  # Orange
    wumons_leds.show()
