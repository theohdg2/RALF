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
        if not isinstance(self.brightness_sensor, Sensor):
            return False
        return False

    def run_start_actions(self):
        print("TODO")

    def run_end_actions(self):
        print("TODO")

    def run_intelligence(self):
        forward(100) # met le robot en mouvement

        # définis des variables qui vont être utiles
        avg_brightness = 0
        laps = 0
        fixed_brightness = False

        safety_dist = []
        actions_start_ran = False

        brightness_reinitialized = False

        while True:
            current_height = get_height(True)
            current_brightness = get_brightness(True)
            ###################################################################################################
            ###                                   START DETECTION SECTION                                  ####
            ###################################################################################################
            if not actions_start_ran: # cette partie du code ne s'active que lorsque le robot à la trappe fermée
                if current_height > START_PROPAGATION_HEIGHT + SECURITY_LEEWAY: # Si je suis au dessus de la marge de sécurité
                    avg_brightness += current_brightness
                    laps += 1

                if START_PROPAGATION_HEIGHT + SECURITY_LEEWAY >= current_height >= START_PROPAGATION_HEIGHT - SECURITY_LEEWAY: # Quand je rentre dans ma zone sensible
                    if not fixed_brightness and laps > 0: # si je n'ai pas encore fixé ma valeur moyenne, je la fixe (une et une seule fois)
                        avg_brightness /= laps
                        fixed_brightness = True
                    if current_brightness <= avg_brightness * (1 - BRIGHTNESS_DROP_DETECTION / 100): # si l'écart est suffisant (erreur relative et pas différence)
                        if len(safety_dist) < 3: # je prends 3 mesures de hauteur
                            safety_dist.append(current_height)
                            continue
                        avg_safety_dist = sorted(safety_dist)[1] # je fais la médianne de ces hauteurs
                        if START_PROPAGATION_HEIGHT + SECURITY_LEEWAY/2 >= avg_safety_dist >= START_PROPAGATION_HEIGHT - SECURITY_LEEWAY/2: # Si je suis dans ma marge restreinte
                            if not actions_start_ran:
                                self.run_start_actions()
                                safety_dist = []
                                actions_start_ran = True
                        else:
                            safety_dist = []
                            avg_safety_dist = 0
                if current_height <= START_PROPAGATION_HEIGHT - SECURITY_LEEWAY: # activation du dernièr espoir
                    self.run_start_actions()
                    actions_start_ran = True
                    safety_dist = []
                    avg_safety_dist = []
            ###################################################################################################
            ###                                   END DETECTION SECTION                                  ####
            ###################################################################################################
            if actions_start_ran: # cette partie du code ne s'active que lorsque le robot a ouvert sa trappe
                if current_height > END_PROPAGATION_HEIGHT + SECURITY_LEEWAY  and not brightness_reinitialized: # réinisialisation des paramètres de luminosité
                    avg_brightness = 0
                    laps = 0
                    brightness_reinitialized = True
                    fixed_brightness = False
                if START_PROPAGATION_HEIGHT - SECURITY_LEEWAY > current_height > END_PROPAGATION_HEIGHT + SECURITY_LEEWAY:
                    avg_brightness += current_brightness
                    laps += 1

                if END_PROPAGATION_HEIGHT - SECURITY_LEEWAY <= current_height <= END_PROPAGATION_HEIGHT + SECURITY_LEEWAY: # Si je rentre dans ma zone sensible
                    if not fixed_brightness and laps > 0:  # si je n'ai pas encore fixé ma valeur moyenne, je la fixe (une et une seule fois)
                        avg_brightness /= laps
                        fixed_brightness = True

                    if current_brightness <= avg_brightness * (1 - BRIGHTNESS_DROP_DETECTION / 100): # si l'écart est suffisant (erreur relative et pas différence)
                        if len(safety_dist) < 3: # je prends 3 mesures de hauteur
                            safety_dist.append(current_height)
                            continue
                        avg_safety_dist = sorted(safety_dist)[1] # je fais la médianne de ces hauteurs
                        if END_PROPAGATION_HEIGHT + SECURITY_LEEWAY/2 >= avg_safety_dist >= END_PROPAGATION_HEIGHT - SECURITY_LEEWAY/2: # Si je suis dans ma marge restreinte
                            self.run_end_actions()
                            break
                        else:
                            safety_dist = []
                            avg_safety_dist = 0
                if current_height <= END_PROPAGATION_HEIGHT - SECURITY_LEEWAY: # activation du dernièr espoir
                    self.run_end_actions()
                    break



"""
    How does the intelligence work?

    At startup, the motor runs at 100% speed.
    (All parameters are configurable.)
"""
"""
START DETECTION (Target: 20 cm)

    1) Read the distance (cm) and brightness (%).

    2) While the distance is above 24 cm, continuously calculate
    a moving average of the brightness.

    3) When the distance reaches 24 cm, freeze the brightness
    average to keep a stable reference.

    4) Check the triggering conditions:
        - Distance > 24 cm: Continue moving.
        - Distance between 22 and 24 cm: Trigger if brightness
            drops by at least 40% compared to the average.
        - Distance <= 22 cm: Trigger regardless of brightness.

    5) Use the median of the last 3 distance readings to
        filter out incorrect sensor values.

    6) Once a condition is met, execute run_start_actions()
        only once.
"""
"""
END DETECTION (Target: 10 cm)

    7) Reset and recalculate the moving brightness average
        after leaving the starting marker.

    8) When the distance reaches 14 cm, freeze the new
        brightness average.

    9) Check the stopping conditions:
        - Distance > 14 cm: Continue moving.
        - Distance between 12 and 14 cm: Stop if brightness
            drops by at least 40% compared to the average.
        - Distance <= 12 cm: Stop regardless of brightness.

    10) Use the median of the last 3 distance readings
        to avoid false triggers.

    11) Once a stopping condition is met, stop the motor
        using forward(0), only once.

    12) Stop the main intelligence loop.
"""
