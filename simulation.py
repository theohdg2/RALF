"""Simulation des capteurs et de l'intelligence du robot R.A.L.F.

Lancement : python "simulation(1).py"
get_height() fait descendre le robot d'un pas et retourne des cm entiers.
get_brightness() retourne un pourcentage a la meme position.
Le simulateur conserve les constantes d'origine, mais ajoute les pertes
ultrasoniques (-1), le filtrage et la confirmation lumineuse.
"""

import random

# ---------------- PARAMÈTRES MODIFIABLES DE LA SIMULATION ----------------
INITIAL_HEIGHT_CM = 60.0
DESCENT_CM_PER_READING = 0.2

START_MARKER_CM = 20.0
END_MARKER_CM = 10.0
MARKER_HALF_WIDTH_CM = 0.9

NORMAL_BRIGHTNESS = 60.0
MARKER_BRIGHTNESS = 35.0
BRIGHTNESS_NOISE = 0.25
HEIGHT_NOISE_CM = 0.25

HEIGHT_FALSE_READING_RATE = 0.02
HEIGHT_NO_ECHO_RATE = 0.02
BRIGHTNESS_FALSE_READING_RATE = 0.03

RANDOM_SEED = 0
NUMBER_OF_SIMULATIONS = 200000
PRINT_EACH_SIMULATION = True
# ---------------------------------------------------------
# ---------------- PARAMÈTRES MODIFIABLES DE LA SIMULATION (basé sur ceux du robot) ----------------
START_PROPAGATION_HEIGHT = 20
END_PROPAGATION_HEIGHT = 10
SECURITY_LEEWAY = 1

BRIGHTNESS_DROP_DETECTION = 30
MAX_INVALID_READINGS = 8
DISTANCE_SAMPLES = 3
MAX_HEIGHT_CHANGE_CM_PER_READING = 2

BRIGHTNESS_SAMPLES = 20
BRIGHTNESS_CONFIRM_SAMPLES = 2
MIN_BRIGHTNESS_SAMPLES = 5
BRIGHTNESS_DETECTION_WINDOW = 1
# ---------------------------------------------------------

# ---------------- PARAMÈTRES NON MODIFIABLES DE LA SIMULATION ----------------
# ---------------- PARAMÈTRES UTILISÉ POUR LA SIMULATION ----------------------
_rng = random.Random(RANDOM_SEED)
true_height = INITIAL_HEIGHT_CM
last_height_glitch = False
last_height_no_echo = False
last_brightness_glitch = False
# ---------------------------------------------------------

def reset_simulation(seed=RANDOM_SEED):
    """Reinitialise la hauteur ET le hasard pour une seed reproductible."""
    global _rng, RANDOM_SEED, true_height
    global last_height_glitch, last_height_no_echo, last_brightness_glitch
    RANDOM_SEED = seed
    _rng = random.Random(seed)
    true_height = INITIAL_HEIGHT_CM
    last_height_glitch = False
    last_height_no_echo = False
    last_brightness_glitch = False


def get_height(cm=True) -> int:
    """Distance en cm (int), ou -1 si l'ultrason ne capte aucun echo."""
    global true_height, last_height_glitch, last_height_no_echo

    # Le robot continue a descendre, meme si une mesure echoue.
    true_height = max(0.0, true_height - DESCENT_CM_PER_READING)

    last_height_no_echo = _rng.random() < HEIGHT_NO_ECHO_RATE
    if last_height_no_echo:
        last_height_glitch = True
        return -1

    measured = true_height + _rng.gauss(0, HEIGHT_NOISE_CM)
    last_height_glitch = _rng.random() < HEIGHT_FALSE_READING_RATE
    if last_height_glitch:
        measured += _rng.choice((-12.0, -8.0, 8.0, 12.0))

    return int(round(max(0.0, measured)))


def get_brightness(percent=True) -> float:
    """Luminosité en % (float), a la meme position que get_height()."""
    global last_brightness_glitch

    on_marker = (
        abs(true_height - START_MARKER_CM) <= MARKER_HALF_WIDTH_CM
        or abs(true_height - END_MARKER_CM) <= MARKER_HALF_WIDTH_CM
    )
    reference = MARKER_BRIGHTNESS if on_marker else NORMAL_BRIGHTNESS
    measured = reference + _rng.gauss(0, BRIGHTNESS_NOISE)

    last_brightness_glitch = _rng.random() < BRIGHTNESS_FALSE_READING_RATE
    if last_brightness_glitch:
        # Faux positif (cable) ou faux negatif (scotch).
        measured = (
            _rng.uniform(50.0, 75.0) if on_marker
            else _rng.uniform(15.0, 33.0)
        )

    return round(min(100.0, max(0.0, measured)), 2)


def _log_trigger(phase, median_height, current_height,
                 current_brightness, brightness_reference,
                 distance_triggered, brightness_triggered, verbose):
    """Journal compact : une ligne CSV par déclenchement."""
    if not verbose:
        return

    target = START_PROPAGATION_HEIGHT if phase == "START" else END_PROPAGATION_HEIGHT

    print("{},{:.2f},{},{},{:.2f},{},{},{},{}".format(
        phase,
        true_height,
        current_height,
        median_height,
        current_brightness,
        round(brightness_reference, 2) if brightness_reference is not None else "",
        int(distance_triggered),
        int(brightness_triggered),
        target
    ))


def run_intelligence(verbose=True):
    """Version simulable de run_intelligence() (memes seuils/conditions)."""
    # Simulation : forward(100) est remplace par la descente virtuelle
    # effectuee lors de chaque appel a get_height().
    distance_history = []
    brightness_history = []
    brightness_reference = None

    actions_start_ran = False
    last_median_height = None
    consecutive_invalid = 0
    brightness_confirmations = 0
    results = {"start": None, "end": None, "status": "RUNNING", "seed": RANDOM_SEED}

    while True:
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
            if consecutive_invalid >= MAX_INVALID_READINGS:
                results["status"] = "SENSOR_STOP"
                if verbose:
                    print("ARRÊT : trop de mesures ultrasoniques invalides")
                return results
            continue

        distance_history.append(current_height)
        if len(distance_history) > DISTANCE_SAMPLES:
            distance_history.pop(0)
        if len(distance_history) < DISTANCE_SAMPLES:
            continue

        median_height = sorted(distance_history)[1]

        if last_median_height is not None:
            allowed_change = (
                MAX_HEIGHT_CHANGE_CM_PER_READING * (consecutive_invalid + 1)
            )
            if abs(median_height - last_median_height) > allowed_change:
                consecutive_invalid += 1
                brightness_confirmations = 0
                if consecutive_invalid >= MAX_INVALID_READINGS:
                    results["status"] = "SENSOR_STOP"
                    if verbose:
                        print("ARRÊT : distances incohérentes répétées")
                    return results
                continue

        last_median_height = median_height
        consecutive_invalid = 0

        # --------------------------------------------------
        # 2. PHASE START OU END
        # --------------------------------------------------
        if not actions_start_ran:
            target_height = START_PROPAGATION_HEIGHT
            can_calibrate = (
                median_height > START_PROPAGATION_HEIGHT + SECURITY_LEEWAY
            )
        else:
            target_height = END_PROPAGATION_HEIGHT
            can_calibrate = (
                START_PROPAGATION_HEIGHT - SECURITY_LEEWAY
                > median_height
                > END_PROPAGATION_HEIGHT + SECURITY_LEEWAY
            )

        # --------------------------------------------------
        # 3. REFERENCE LUMINEUSE
        # --------------------------------------------------
        if brightness_reference is None:
            if can_calibrate:
                brightness_history.append(current_brightness)
                if len(brightness_history) > BRIGHTNESS_SAMPLES:
                    brightness_history.pop(0)
            elif len(brightness_history) >= MIN_BRIGHTNESS_SAMPLES:
                brightness_reference = (
                    sum(brightness_history) / len(brightness_history)
                )

        # --------------------------------------------------
        # 4. DÉCLENCHEMENTS
        # --------------------------------------------------
        distance_triggered = (
            median_height <= target_height - SECURITY_LEEWAY
        )

        in_brightness_zone = (
            target_height - BRIGHTNESS_DETECTION_WINDOW
            <= median_height
            <= target_height + BRIGHTNESS_DETECTION_WINDOW
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
            brightness_confirmations >= BRIGHTNESS_CONFIRM_SAMPLES
        )

        if not (distance_triggered or brightness_triggered):
            continue

        # --------------------------------------------------
        # 5. ACTIONS SIMULÉES
        # --------------------------------------------------
        phase = "END" if actions_start_ran else "START"
        _log_trigger(
            phase, median_height, current_height, current_brightness,
            brightness_reference, distance_triggered, brightness_triggered,
            verbose
        )

        results[phase.lower()] = true_height

        if not actions_start_ran:
            actions_start_ran = True
            distance_history.clear()
            brightness_history.clear()
            brightness_reference = None
            consecutive_invalid = 0
            brightness_confirmations = 0
            continue

        results["status"] = "FINISHED"
        return results


if __name__ == "__main__":
    complete = 0
    emergency_stops = 0
    starts = []
    ends = []
    print("CONFIG;" + ";".join(
        "{}={}".format(name, value)
        for name, value in globals().items()
        if name.isupper() and isinstance(value, (int, float, str, bool))
    ))
    for seed in range(NUMBER_OF_SIMULATIONS):
        reset_simulation(seed)
        if PRINT_EACH_SIMULATION:
            print("Simulation des capteurs : descente de {:.0f} cm a 0 cm avec seed : {}".format(
                INITIAL_HEIGHT_CM, seed
            ))
        result = run_intelligence(verbose=PRINT_EACH_SIMULATION)
        if result["status"] == "FINISHED":
            complete += 1
        else:
            emergency_stops += 1
        if result["start"] is not None:
            starts.append(result["start"])
        if result["end"] is not None:
            ends.append(result["end"])

    print("\n===== BILAN =====")
    print("Simulations terminées :", complete, "/", NUMBER_OF_SIMULATIONS)
    print("Arrêts par capteur défaillant :", emergency_stops)
    if starts:
        print("START moyen : {:.3f} cm".format(sum(starts) / len(starts)))
        print("START min / max : {:.2f} / {:.2f} cm".format(min(starts), max(starts)))
    if ends:
        print("END moyen : {:.3f} cm".format(sum(ends) / len(ends)))
        print("END min / max : {:.2f} / {:.2f} cm".format(min(ends), max(ends)))
