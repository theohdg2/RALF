import time

from lib.asyncio import sleep
from available_musics import AvailableMusics
from utils import *
import settings

"""
    :function initialize_robot: bool
    :description: This function initializes the robot's components, including setting the trapdoor position and starting the motor. It also plays a success music sequence upon successful initialization. If any error occurs during initialization, it prints the error message and returns False. Otherwise, it returns True.
"""
def initialize_robot(trap_position=0, motor_speed=0) -> bool:
    try:
        # Initialize the robot's components
        set_trapdoor_position(trap_position)
        initialize_ultrasonic_sensor()
        forward(motor_speed)
        play_music(AvailableMusics.SUCCESS_START)
        return True
    except Exception as e:
        print(f"Error initializing robot: {e}")
        return False

"""
    :function get_height: int|None
    :description: This function retrieves the height measured by the distance sensor. If the distance sensor is not initialized, it returns None. Otherwise, it returns the distance in centimeters as an integer.
"""
def get_height() -> int|None:
    # Get the height from the distance sensor
    sensor = settings.distance_sensor
    return sensor.get_distance() if sensor is not None else None

def get_brightness() -> int|None:
    return brightness_sensor.get_value()/65535 * 100
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
    # Set the LEDs to a waiting state (blinking blue & white)
    wumons_leds.fill(colour_from_rgb(0, 0, 255))  # Blue
    wumons_leds.show()
def initialized_leds_state():
    # Set the LEDs to an initialized state (solid green)
    wumons_leds.fill(colour_from_rgb(0, 255, 0))  # Green
    wumons_leds.show()

"""
    :function loop: None
    :description: This function contains the main loop of the robot's operation. It continuously checks for button presses and manages the robot's state. When the start button is pressed, it initiates the robot's action sequence and plays a power-up music sequence.
"""
def loop():
    in_action = False
    state = "waiting"
    while True:
        if not in_action and state == "waiting":
            waiting_leds_state()

        if not in_action:
            print(str(get_brightness())+" %")
            time.sleep(0.25)

        if is_button_pressed(start_button) and not in_action:
            # Start the robot's action sequence
            print("Button pressed. Starting robot action sequence...")
            actions()
            in_action = False



def actions():
    set_trapdoor_position(90)
    forward(100)
    while True:
        if 10 > get_height() >= 0:
            stop()
            break



"""
    :function main: None
    :description: This is the main entry point of the program. It initializes the robot and enters the main loop. If initialization fails, it plays an error music sequence and sets the LEDs to an error state.
"""
def main():
    print("Starting robot...")
    print("Initializing components...")
    if initialize_robot():
        print("Robot initialized. Waiting for button press...")
        initialized_leds_state()
        time.sleep(0.5)
        loop()
    else:
        print("Failed to initialize robot. Please check the components and restart the program.")
        error_sound = False
        while True:
            if not error_sound:
                play_music(AvailableMusics.INIT_ERROR)
                error_sound = True
            error_leds_state()
if __name__ == "__main__":
    main()