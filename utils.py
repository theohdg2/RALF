from settings import *
import settings

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
def is_button_pressed(button: wumons.sensor, precision: int = 40000) -> bool:
    return button.get_value() <= precision

"""
    :function initialize_ultrasonic_sensor: bool
    :description: This function initializes the ultrasonic sensor and returns True if successful, False otherwise.
"""
def initialize_ultrasonic_sensor() -> bool:
    try:
        settings.distance_sensor = DFRobot_URM09(wumons.i2c)
        return True
    except Exception as e:
        print(f"Error initializing ultrasonic sensor: {e}")
        return False

"""
    :function play_music: None
    :description: This function plays a given music sequence using the Wukong Music Player.
"""
def play_music(music_sequence: list):
    if not isinstance(music_sequence, list):
        raise TypeError("Invalid music sequence. Expected a list of notes.")
    wumons_music_player.play(music_sequence)