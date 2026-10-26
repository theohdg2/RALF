from intelligence import *
from utils import *

WAITING = "WAITING"
ACTION = "ACTION"

"""Initialize the robot hardware and bring it to a safe idle state."""


def initialize_robot(trap_position=0, motor_speed=0) -> bool:
    """Initialize the trapdoor, ultrasonic sensor and motor.

    The previous behavior is intentionally preserved: the function still tries the
    same setup steps and returns True/False based on the success of the sequence.
    """
    try:
        # Initialize the robot's components.
        set_trapdoor_position(trap_position)
        initialize_ultrasonic_sensor()
        forward(motor_speed)
        play_music(AvailableMusics.SUCCESS_START)
        return True
    except Exception as e:
        print(f"Error initializing robot: {e}")
        return False


"""Monitor the robot while it waits for a start signal."""


def monitor_idle_state():
    """Report the current brightness and ultrasonic distance while idle."""
    print(str(get_brightness()) + " % de luminosité & une hauteur de " + str(get_height()) + " cm.")
    time.sleep(0.125)


"""Execute the action sequence upon pressing the start button."""


def handle_start_action(decision_engine):
    """Launch the start action sequence and then return to idle wait mode."""
    print("Button pressed. Starting robot action sequence...")
    in_action_leds_state()
    decision_engine.run_intelligence()
    waiting_leds_state()


"""Main operational loop: wait for start while monitoring sensors."""


def loop():
    """Run the robot's waiting loop until the start button is pressed.

    This keeps the original logic: the robot keeps reporting sensor values while
    idle, and when the button is pressed it runs the intelligence cycle.
    """
    decision_engine = Intelligence(settings.distance_sensor, settings.brightness_sensor)
    state = WAITING
    waiting_leds_state()

    while True:
        if state == WAITING:
            if not is_button_pressed(start_button):
                monitor_idle_state()
                continue

            state = ACTION

        if state == ACTION:
            handle_start_action(decision_engine)
            state = WAITING


"""Entry point of the program."""


def main():
    """Initialize the robot and enter the main processing loop."""
    print("Starting robot...")
    print("Initializing components...")

    if initialize_robot():
        print("Robot initialized. Waiting for button press...")
        initialized_leds_state()
        time.sleep(0.5)
        loop()
    else:
        print("Failed to initialize robot. Please check the components and restart the program.")
        error_leds_state()
        while True:
            play_music(AvailableMusics.INIT_ERROR)
            time.sleep(1.5)


if __name__ == "__main__":
    main()
