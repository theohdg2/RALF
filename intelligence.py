from lib.wumons.sensor import Sensor
from utils import *


class Intelligence:
    distance_sensor: DFRobot_URM09
    brightness_sensor: Sensor

    def __init__(self, distance_sensor, brightness_sensor):
        self.distance_sensor = distance_sensor
        self.brightness_sensor = brightness_sensor
        self.start_propagation_height = settings.START_PROPAGATION_HEIGHT
        self.end_propagation_height = settings.END_PROPAGATION_HEIGHT
        self.max_invalid_readings = settings.MAX_INVALID_READINGS
        self.distance_samples = settings.DISTANCE_SAMPLES
        self.max_height_change_cm_per_reading = settings.MAX_HEIGHT_CHANGE_CM_PER_READING
        self.brightness_samples = settings.BRIGHTNESS_SAMPLES
        self.brightness_confirm_samples = settings.BRIGHTNESS_CONFIRM_SAMPLES
        self.min_brightness_samples = settings.MIN_BRIGHTNESS_SAMPLES
        self.brightness_detection_window = settings.BRIGHTNESS_DETECTION_WINDOW

        if not self.test_values():
            # TODO: remplacer par la gestion d'erreur du projet.
            print("this is an error")

    def test_values(self):
        # Verifier les cibles et les capteurs.
        if not 0 <= self.start_propagation_height <= 320:
            return False
        if not 0 <= self.end_propagation_height <= 320:
            return False
        if not self.start_propagation_height >= self.end_propagation_height:
            return False
        if not isinstance(self.distance_sensor, DFRobot_URM09):
            return False
        if not isinstance(self.brightness_sensor, Sensor):
            return False
        return True

    def _run_start_actions(self):
        print("Déclenchement du début")

    def _run_end_actions(self):
        forward(0)
        print("Déclenchement de fin")

    def run_intelligence(self):
        # Mouvement du robot vers le bas.
        forward(100)

        distance_history = []
        brightness_history = []
        brightness_reference = None

        actions_start_ran = False
        last_median_height = None
        consecutive_invalid = 0
        brightness_confirmations = 0

        while True:
            # Fonctions de lecture deja fournies par utils.
            current_height = get_height()
            current_brightness = get_brightness()

            # --------------------------------------------------
            # 1. FILTRE ULTRASON : -1 = aucun echo recu
            # --------------------------------------------------
            invalid_height = (
                current_height is None
                or current_height < 0
                or current_height > 320
            )

            if invalid_height:
                consecutive_invalid += 1
                distance_history.clear()
                brightness_confirmations = 0
                if consecutive_invalid >= self.max_invalid_readings:
                    forward(0)  # Arret si le capteur ne repond plus.
                    return
                continue

            # Mediane glissante : une valeur erronée sur trois est ignoree.
            distance_history.append(current_height)
            if len(distance_history) > self.distance_samples:
                distance_history.pop(0)
            if len(distance_history) < self.distance_samples:
                continue

            median_height = sorted(distance_history)[1]

            # Rejeter les sauts impossibles entre medianes successives.
            if last_median_height is not None:
                allowed_change = (
                    self.max_height_change_cm_per_reading
                    * (consecutive_invalid + 1)
                )
                if abs(median_height - last_median_height) > allowed_change:
                    consecutive_invalid += 1
                    brightness_confirmations = 0
                    if consecutive_invalid >= self.max_invalid_readings:
                        forward(0)
                        return
                    continue

            last_median_height = median_height
            consecutive_invalid = 0

            # --------------------------------------------------
            # 2. PHASE START OU END
            # --------------------------------------------------
            if not actions_start_ran:
                target_height = self.start_propagation_height
                can_calibrate = (
                    median_height > self.start_propagation_height + SECURITY_LEEWAY
                )
            else:
                target_height = self.end_propagation_height
                can_calibrate = (
                    self.start_propagation_height - SECURITY_LEEWAY
                    > median_height
                    > self.end_propagation_height + SECURITY_LEEWAY
                )

            # --------------------------------------------------
            # 3. REFERENCE LUMINEUSE (moyenne glissante, puis figee)
            # --------------------------------------------------
            if brightness_reference is None:
                if can_calibrate:
                    brightness_history.append(current_brightness)
                    if len(brightness_history) > self.brightness_samples:
                        brightness_history.pop(0)
                elif len(brightness_history) >= self.min_brightness_samples:
                    brightness_reference = (
                        sum(brightness_history) / len(brightness_history)
                    )

            # --------------------------------------------------
            # 4. DECLENCHEMENTS
            # --------------------------------------------------
            # Secours : 18 cm pour START, 8 cm pour END (marge = 2).
            distance_triggered = (
                median_height <= target_height - SECURITY_LEEWAY
            )

            # Detection du scotch uniquement autour de la cible (+/- 1 cm).
            in_brightness_zone = (
                target_height - self.brightness_detection_window
                <= median_height
                <= target_height + self.brightness_detection_window
            )
            brightness_low = (
                brightness_reference is not None
                and in_brightness_zone
                and current_brightness <= brightness_reference * (
                    1 - BRIGHTNESS_DROP_DETECTION / 100
                )
            )

            if brightness_low:
                brightness_confirmations += 1
            else:
                brightness_confirmations = 0

            brightness_triggered = (
                brightness_confirmations >= self.brightness_confirm_samples
            )

            if not (distance_triggered or brightness_triggered):
                continue

            # --------------------------------------------------
            # 5. ACTIONS
            # --------------------------------------------------
            if not actions_start_ran:
                self._run_start_actions()
                actions_start_ran = True

                # La calibration END doit repartir du cable gris.
                distance_history.clear()
                brightness_history.clear()
                brightness_reference = None
                consecutive_invalid = 0
                brightness_confirmations = 0
                continue

            self._run_end_actions()
            break


"""
R.A.L.F. - Intelligence de descente

START (cible 20 cm, marge 2 cm) :
- Calibrer la luminosite avant 22 cm.
- Detecter le scotch entre 19 et 21 cm si deux mesures successives
  ont une baisse relative suffisante.
- Declencher le secours a 18 cm ou moins.

END (cible 10 cm, marge 2 cm) :
- Recalibrer sur le cable entre 18 et 12 cm.
- Detecter le scotch entre 9 et 11 cm selon les memes conditions.
- Declencher le secours a 8 cm ou moins, puis arreter le moteur.

Dans les deux phases :
- Ignorer une mesure ultrasonique egale a -1.
- Utiliser la mediane glissante des trois dernieres mesures valides.
- Ignorer les sauts de distance incoherents.
- Arreter le moteur apres huit mesures de distance invalides consecutives.
"""
