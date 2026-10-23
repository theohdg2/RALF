import board
import digitalio
import analogio


class DigitalButton:
    def __init__(self, pin):
        self.pin = pin
        self.button = digitalio.DigitalInOut(self.pin)
        self.button.direction = digitalio.Direction.INPUT
        self.button.pull = digitalio.Pull.UP
        
    def is_pressed(self):
        return not(self.button.value)

class AnalogButton:
    def __init__(self, pin):
        self.pin = pin
        self.button = analogio.AnalogIn(self.pin)
        
    def is_pressed(self):
        return self.button.value
