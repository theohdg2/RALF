from lib.wumons.sensor import Sensor
from lib.wumons_i2c.dfr_urm09 import DFRobot_URM09
from utils import *


class Intelligence:

    distance_sensor: DFRobot_URM09
    brightness_sensor: Sensor


    def __init__(self,distance_sensor, brightness_sensor):
        self.distance_sensor = distance_sensor
        self.brightness_sensor = brightness_sensor
        self.start_propagation_height = settings.START_PROPAGATION_HEIGHT
        self.end_propagation_height = settings.END_PROPAGATION_HEIGHT
        if not self.test_values():
            # Todo return an error
            print("this is an error")

    def test_values(self):
        # Verify that start/end propagation height is an int between 0 and 320 cm
        if not 0 <= self.start_propagation_height <= 320:
            return False
        if not self.start_propagation_height >= self.end_propagation_height:
            return False
        if not isinstance(self.distance_sensor, DFRobot_URM09):
            return False
        if not isistance(self.brightness_sensor, Sensor):
            return False
        return False

    def run_intelligence(self):
        forward(100)
        while True:
            break



"""
    How intelligence work ?
    
    At the beginning, the motor start at 100% and then the main intelligence loop begin.
    (Maximun speed is not abusive) 
    
    1) catch height from dist. sensor
    2) catch brightness from bright. sensor
    
    3) le temps que la distance de l'ultra sons est assez loin (+-2cm de marge, configurable) enregistrer la valeur de l'intensité lumineuse pour faire une moyenne 
    4) dès que la valeur d'un des capteurs est déclencheuse (ultrasons bonne distance ou luminosité vrm différente) alors essayer de voir si le deuxieme capteur est proche 
    5)
    



"""
