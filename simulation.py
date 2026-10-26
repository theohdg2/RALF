# PROTOTYPE EXPÉRIMENTAL : simulation optimisée de R.A.L.F. pour Python sur PC.
# Contient les conditions dégradées de logs(8) ; fichiers de production non modifiés.
# La valeur DESCENT_CM_PER_READING sert à modéliser la progression simulée.
# Sur le robot, remplacer cette estimation par vitesse maximale réelle × temps écoulé.
# Recommandation : valider aussi sous des conditions réalistes avant déploiement.

"""Simulation des capteurs et de l'intelligence du robot R.A.L.F.

Lancement : python "simulation(1).py"
Get_height() fait descendre le robot d'un pas et retourne des cm entiers.
Get_brightness() retourne un pourcentage à la meme position.
Le simulateur conserve les constantes d'origine, mais ajoute les pertes
ultrasoniques (-1), le filtrage et la confirmation lumineuse.
"""

import random

# ---------------- PARAMÈTRES MODIFIABLES ----------------
INITIAL_HEIGHT_CM = 60.0
DESCENT_CM_PER_READING = 0.1

SECURITY_LEEWAY = 1
BRIGHTNESS_DETECTION_WINDOW = 1  # cm autour de la cible
START_PROPAGATION_HEIGHT = 20
END_PROPAGATION_HEIGHT = 10
BRIGHTNESS_DROP_DETECTION = 20

START_MARKER_CM = 20.0
END_MARKER_CM = 10.0
MARKER_HALF_WIDTH_CM = 0.5

NORMAL_BRIGHTNESS = 60.0
MARKER_BRIGHTNESS = 45.0
BRIGHTNESS_NOISE = 0.5  # Ecart-type, points de pourcentage
HEIGHT_NOISE_CM = 0.5  # Ecart-type, cm

HEIGHT_FALSE_READING_RATE = 0.1
HEIGHT_NO_ECHO_RATE = 0.1  # Retour -1 en l'absence d'écho
BRIGHTNESS_FALSE_READING_RATE = 0.1

# Meme paramètres de filtrage que dans intelligence.py
DISTANCE_SAMPLES = 3
BRIGHTNESS_SAMPLES = 20
MIN_BRIGHTNESS_SAMPLES = 5
BRIGHTNESS_CONFIRM_SAMPLES = 3
MAX_HEIGHT_CHANGE_CM_PER_READING = 2.0
MAX_INVALID_READINGS = 8

RANDOM_SEED = 0
NUMBER_OF_SIMULATIONS = 1000
PRINT_EACH_SIMULATION = False
# ---------------------------------------------------------

_rng = random.Random(RANDOM_SEED)
true_height = INITIAL_HEIGHT_CM
last_height_glitch = False
last_height_no_echo = False
last_brightness_glitch = False


def reset_simulation():
    """Reinitialise la hauteur ET le hasard pour une seed reproductible."""
    global _rng, RANDOM_SEED, true_height
    global last_height_glitch, last_height_no_echo, last_brightness_glitch
    RANDOM_SEED = seed
    _rng = random.Random(seed)
    true_height = INITIAL_HEIGHT_CM
    last_height_glitch = False
    last_height_no_echo = False
    last_brightness_glitch = False


def get_height() -> int:
    """Distance en cm (int), ou -1 si l'ultrason ne capte aucun echo."""
    global true_height, last_height_glitch, last_height_no_echo

    # Le robot continu à descendre, meme si une mesure échoue.
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


def get_brightness() -> float:
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
        # Faux positif (cable) ou faux négatif (scotch).
        measured = (
            _rng.uniform(50.0, 75.0) if on_marker
            else _rng.uniform(15.0, 33.0)
        )

    return round(min(100.0, max(0.0, measured)), 2)


def _log_trigger(phase, median_height, current_height,
                 current_brightness, brightness_reference,
                 distance_triggered, brightness_triggered, verbose):
    """Journal permettant de comprendre la cause de chaque déclenchement."""
    if not verbose:
        return
    print("Déclenchement de l'action de {} à {:.2f}".format(
        "début" if phase == "START" else "fin", true_height
    ))
    print("--------------------[INFOS]--------------------")
    print("Distance réelle simulée (cm)", round(true_height, 2))
    print("Distance brute mesurée (cm)", current_height)
    print("Médiane des 3 distances", median_height)
    print("Luminosité actuelle (%)", current_brightness)
    print("Luminosité moyenne de référence (%)", brightness_reference)
    print("Déclenchement par distance", distance_triggered)
    print("Déclenchement par luminosité", brightness_triggered)
    print("Distance cible actuelle", (
        START_PROPAGATION_HEIGHT if phase == "START"
        else END_PROPAGATION_HEIGHT
    ))
    print("--------------------[INFOS]--------------------")


def run_intelligence(verbose=True):
    """Version simulable de run_intelligence() (memes seuils/conditions)."""
    # Simulation : forward(100) est remplace par la descente virtuelle
    # effectuée lors de chaque appel a get_height().
    distance_history = []
    brightness_history = []
    brightness_reference = None

    actions_start_ran = False
    last_median_height = None
    no_echo_streak = 0
    rejected_window_streak = 0
    brightness_confirmations = 0
    iteration = 0
    last_accepted_iteration = 0
    results = {"start": None, "end": None, "status": "RUNNING", "seed": RANDOM_SEED}

    while True:
        iteration += 1
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
            no_echo_streak += 1
            # keep last two valid distance readings
            brightness_confirmations = 0
            if no_echo_streak >= MAX_INVALID_READINGS:
                results["status"] = "SENSOR_STOP"
                if verbose:
                    print("ARRÊT : trop de mesures ultrasoniques invalides")
                return results
            continue

        no_echo_streak = 0
        distance_history.append(current_height)
        if len(distance_history) > DISTANCE_SAMPLES:
            distance_history.pop(0)
        if len(distance_history) < DISTANCE_SAMPLES:
            continue

        median_height = sorted(distance_history)[1]

        if last_median_height is not None:
            allowed_change = min(4.0, 2.0 + DESCENT_CM_PER_READING * (iteration - last_accepted_iteration))
            if abs(median_height - last_median_height) > allowed_change:
                rejected_window_streak += 1
                distance_history.clear()  # discard suspect window
                brightness_confirmations = 0
                if rejected_window_streak >= MAX_INVALID_READINGS:
                    results["status"] = "SENSOR_STOP"
                    if verbose:
                        print("ARRÊT : distances incohérentes répétées")
                    return results
                continue

        last_accepted_iteration = iteration
        last_median_height = median_height
        rejected_window_streak = 0

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
                    sorted(brightness_history)[len(brightness_history) // 2]
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
            # préserve last_median_height
            no_echo_streak = 0
            brightness_confirmations = 0
            continue

        results["status"] = "FINISHED"
        return results


if __name__ == "__main__":
    complete = 0
    emergency_stops = 0
    starts = []
    ends = []
    for seed in range(NUMBER_OF_SIMULATIONS):
        reset_simulation()
        if PRINT_EACH_SIMULATION:
            print(
                "Simulation des capteurs : descente de {:.0f} cm a 0 cm avec seed : {}".format(INITIAL_HEIGHT_CM, seed))
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
