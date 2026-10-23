import wumons

"""
    :class Servo: This class represents a servo motor and provides methods for controlling its position.
"""
class Servo(wumons.Servo):

    BIG_SERVO_PULSE = [300, 1900]
    SMALL_SERVO_PULSE = [500, 2500]

    def __init__(self,pin,pusle_range: list[int]) -> None:
        super().__init__(pin)
        self.set_pulse_width_range(pusle_range[0], pusle_range[1])