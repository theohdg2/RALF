"""Intelligence de descente R.A.L.F. : largage entre deux repères, arrêt au troisième.

La couleur du troisième repère n'est pas précisée par le BOSCARD.
Le mode CONTRAST_OR_DISTANCE vérifie un contraste lumineux près de sa hauteur,
avec un arrêt de secours fondé sur la distance. Ce n'est PAS une reconnaissance
colorimétrique du troisième ruban.
"""

import time

from utils import (
    AvailableMusics,
    DFRobot_URM09,
    Sensor,
    error_leds_state,
    forward,
    play_music,
    set_trapdoor_position,
    settings,
    stop,
)


class Intelligence:
    BEFORE_RELEASE = 0
    DURING_RELEASE = 1
    AFTER_RELEASE = 2

    def __init__(self, distance_sensor, brightness_sensor):
        self.distance_sensor = distance_sensor
        self.brightness_sensor = brightness_sensor

        self.start_propagation_height = settings.START_PROPAGATION_HEIGHT
        self.end_propagation_height = settings.END_PROPAGATION_HEIGHT
        self.stop_propagation_height = settings.STOP_PROPAGATION_HEIGHT
        self.security_leeway = settings.SECURITY_LEEWAY

        self.motor_power_before_release = settings.MOTOR_POWER_BEFORE_RELEASE
        self.motor_power_during_release = settings.MOTOR_POWER_DURING_RELEASE
        self.motor_power_after_release = settings.MOTOR_POWER_AFTER_RELEASE

        self.brightness_drop_detection = settings.BRIGHTNESS_DROP_DETECTION
        self.stop_brightness_change_percent = settings.STOP_BRIGHTNESS_CHANGE_PERCENT
        self.stop_detection_mode = settings.STOP_DETECTION_MODE
        self.max_invalid_readings = settings.MAX_INVALID_READINGS
        self.distance_samples = settings.DISTANCE_SAMPLES
        self.max_height_change_cm_per_reading = settings.MAX_HEIGHT_CHANGE_CM_PER_READING
        self.max_median_jump_cm = settings.MAX_MEDIAN_JUMP_CM
        self.brightness_samples = settings.BRIGHTNESS_SAMPLES
        self.brightness_confirm_samples = settings.BRIGHTNESS_CONFIRM_SAMPLES
        self.min_brightness_samples = settings.MIN_BRIGHTNESS_SAMPLES
        self.brightness_detection_window = settings.BRIGHTNESS_DETECTION_WINDOW
        self.trapdoor_open_angle = settings.TRAPDOOR_OPEN_ANGLE
        self.sensor_read_interval_s = settings.SENSOR_READ_INTERVAL_S
        self.max_run_time_s = settings.MAX_RUN_TIME_S

        if not self.test_values():
            raise ValueError("Configuration de l'intelligence invalide")

    @staticmethod
    def _number_in_range(value, minimum, maximum, min_inclusive=True):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if min_inclusive:
            return minimum <= value <= maximum
        return minimum < value <= maximum

    def test_values(self):
        # Ordre obligatoire des trois zones sur la descente.
        if not (0 < self.stop_propagation_height < self.end_propagation_height
                < self.start_propagation_height <= 320):
            return False
        if not isinstance(self.distance_sensor, DFRobot_URM09):
            return False
        if not isinstance(self.brightness_sensor, Sensor):
            return False

        # Puissance PWM : valeurs strictement positives pendant le déplacement.
        for power in (self.motor_power_before_release,
                      self.motor_power_during_release,
                      self.motor_power_after_release):
            if not self._number_in_range(power, 0, 100, min_inclusive=False):
                return False

        if not self._number_in_range(self.security_leeway, 0, 10, False):
            return False
        if not self._number_in_range(self.brightness_detection_window, 0, 10, False):
            return False
        if not self._number_in_range(self.brightness_drop_detection, 0, 100, False):
            return False
        if not self._number_in_range(self.stop_brightness_change_percent, 0, 100, False):
            return False
        if self.stop_detection_mode not in ("DISTANCE_ONLY", "CONTRAST_OR_DISTANCE"):
            return False
        if self.start_propagation_height - self.end_propagation_height <= 2 * self.brightness_detection_window:
            return False
        if self.end_propagation_height - self.stop_propagation_height <= 2 * self.brightness_detection_window:
            return False
        if not isinstance(self.max_invalid_readings, int) or self.max_invalid_readings < 1:
            return False
        if self.distance_samples != 3:
            return False  # la médiane est calculée par sorted(history)[1]
        if not self._number_in_range(self.max_height_change_cm_per_reading, 0, 320, False):
            return False
        if not self._number_in_range(self.max_median_jump_cm,
                                     self.max_height_change_cm_per_reading, 320):
            return False
        if not isinstance(self.brightness_samples, int) or self.brightness_samples < 2:
            return False
        if not isinstance(self.min_brightness_samples, int) or not (1 <= self.min_brightness_samples <= self.brightness_samples):
            return False
        if not isinstance(self.brightness_confirm_samples, int) or self.brightness_confirm_samples < 1:
            return False
        if not self._number_in_range(self.trapdoor_open_angle, 0, 180):
            return False
        if not self._number_in_range(self.sensor_read_interval_s, 0, 1, False):
            return False
        if not self._number_in_range(self.max_run_time_s, 0, 3600, False):
            return False
        return True

    @staticmethod
    def _valid_height(height):
        return isinstance(height, (int, float)) and not isinstance(height, bool) and 0 <= height <= 320

    @staticmethod
    def _valid_brightness(brightness):
        return isinstance(brightness, (int, float)) and not isinstance(brightness, bool) and 0 <= brightness <= 100

    def _read_brightness(self):
        return self.brightness_sensor.get_value() * 100 / 65535

    def _run_start_actions(self):
        print("Premier repere : ouverture de la trappe.")
        if not set_trapdoor_position(self.trapdoor_open_angle):
            raise RuntimeError("Impossible d'ouvrir la trappe")
        forward(self.motor_power_during_release)

    def _run_end_actions(self):
        print("Deuxieme repere : fermeture de la trappe, descente maintenue.")
        if not set_trapdoor_position(0):
            raise RuntimeError("Impossible de fermer la trappe")
        forward(self.motor_power_after_release)

    @staticmethod
    def _run_stop_actions():
        print("Troisieme repere / hauteur d'arret : moteur a l'arret.")
        stop()
        play_music(AvailableMusics.BIRTHDAY)

    @staticmethod
    def _run_emergency_actions(message):
        print("ARRET DE SECURITE :", message)
        stop()
        error_leds_state()

    def run_intelligence(self):
        """Retourne True pour une mission terminée, False pour un arrêt de sécurité.

        Le moteur et la trappe sont remis à leur état sûr par le bloc finally,
        même si une lecture ou un actionneur lève une exception.
        """
        phase = self.BEFORE_RELEASE
        distance_history = []
        brightness_history = []
        brightness_reference = None
        last_median_height = None
        consecutive_invalid = 0
        brightness_confirmations = 0
        start_time = time.monotonic()

        try:
            forward(self.motor_power_before_release)
            while True:
                if time.monotonic() - start_time >= self.max_run_time_s:
                    self._run_emergency_actions("duree maximale depassee")
                    return False

                time.sleep(self.sensor_read_interval_s)
                current_height = self.distance_sensor.get_distance()
                current_brightness = self._read_brightness()

                if not self._valid_height(current_height):
                    consecutive_invalid += 1
                    distance_history.clear()
                    brightness_confirmations = 0
                    if consecutive_invalid >= self.max_invalid_readings:
                        self._run_emergency_actions("mesures ultrasoniques invalides")
                        return False
                    continue

                distance_history.append(current_height)
                if len(distance_history) > self.distance_samples:
                    distance_history.pop(0)
                if len(distance_history) < self.distance_samples:
                    continue

                median_height = sorted(distance_history)[1]
                if last_median_height is not None:
                    # Plafond absolu : après plusieurs échecs, un saut aberrant
                    # ne doit pas devenir arbitrairement acceptable.
                    allowed_change = min(
                        self.max_height_change_cm_per_reading * (consecutive_invalid + 1),
                        self.max_median_jump_cm,
                    )
                    if abs(median_height - last_median_height) > allowed_change:
                        consecutive_invalid += 1
                        distance_history.clear()
                        brightness_confirmations = 0
                        if consecutive_invalid >= self.max_invalid_readings:
                            self._run_emergency_actions("variation de distance incoherente")
                            return False
                        continue

                last_median_height = median_height
                consecutive_invalid = 0

                if phase == self.BEFORE_RELEASE:
                    target = self.start_propagation_height
                    can_calibrate = median_height > target + self.security_leeway
                elif phase == self.DURING_RELEASE:
                    target = self.end_propagation_height
                    can_calibrate = (self.start_propagation_height - self.security_leeway
                                     > median_height > target + self.security_leeway)
                else:
                    target = self.stop_propagation_height
                    can_calibrate = (self.end_propagation_height - self.security_leeway
                                     > median_height > target + self.security_leeway)

                # Référence adaptée à chaque phase, sans hypothèse sur la lumière ambiante.
                if brightness_reference is None and self._valid_brightness(current_brightness):
                    if can_calibrate:
                        brightness_history.append(current_brightness)
                        if len(brightness_history) > self.brightness_samples:
                            brightness_history.pop(0)
                    elif len(brightness_history) >= self.min_brightness_samples:
                        brightness_reference = sum(brightness_history) / len(brightness_history)

                in_zone = target - self.brightness_detection_window <= median_height <= target + self.brightness_detection_window
                brightness_triggered = False

                if phase == self.AFTER_RELEASE:
                    # La couleur du troisième scotch est inconnue : seule une variation
                    # de reflectance est observable avec le capteur actuel.
                    if self.stop_detection_mode == "CONTRAST_OR_DISTANCE":
                        contrast = (
                            brightness_reference is not None
                            and brightness_reference > 0
                            and self._valid_brightness(current_brightness)
                            and in_zone
                            and abs(current_brightness - brightness_reference)
                            >= brightness_reference * self.stop_brightness_change_percent / 100
                        )
                        brightness_confirmations = brightness_confirmations + 1 if contrast else 0
                        brightness_triggered = brightness_confirmations >= self.brightness_confirm_samples
                    # Pour l'arrêt, la hauteur de secours correspond à la cible :
                    # ne pas poursuivre volontairement vers le sol pour attendre le scotch.
                    distance_triggered = median_height <= target
                else:
                    dark = (
                        brightness_reference is not None
                        and self._valid_brightness(current_brightness)
                        and in_zone
                        and current_brightness <= brightness_reference * (1 - self.brightness_drop_detection / 100)
                    )
                    brightness_confirmations = brightness_confirmations + 1 if dark else 0
                    brightness_triggered = brightness_confirmations >= self.brightness_confirm_samples
                    distance_triggered = median_height <= target - self.security_leeway

                if not (distance_triggered or brightness_triggered):
                    continue

                if phase == self.BEFORE_RELEASE:
                    self._run_start_actions()
                    phase = self.DURING_RELEASE
                elif phase == self.DURING_RELEASE:
                    self._run_end_actions()
                    phase = self.AFTER_RELEASE
                else:
                    self._run_stop_actions()
                    return True

                # Conserver la continuité du filtre ultrasonique entre phases.
                # Effacer uniquement la référence optique entre repères.
                brightness_history.clear()
                brightness_reference = None
                brightness_confirmations = 0
                consecutive_invalid = 0
                # Conserver distance_history et last_median_height : des lectures
                # valides antérieures restent utiles pour détecter un saut aberrant.
        except Exception as exc:
            self._run_emergency_actions(str(exc))
            return False
        finally:
            stop()
            try:
                set_trapdoor_position(0)
            except Exception as exc:
                print("Echec fermeture de securite de la trappe :", exc)
