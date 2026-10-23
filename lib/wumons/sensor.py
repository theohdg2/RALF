import board
import analogio


class Sensor:
    def __init__(self, pin):
        self.pin = pin
        self.sensor = analogio.AnalogIn(self.pin)

    def get_value(self):
        return self.sensor.value
