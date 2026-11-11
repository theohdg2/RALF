"""Point d'entrée du robot R.A.L.F. (CircuitPython)."""

import time

import settings
from intelligence import Intelligence
from utils import (
    AvailableMusics,
    error_leds_state,
    get_brightness,
    get_height,
    in_action_leds_state,
    initialize_ultrasonic_sensor,
    initialized_leds_state,
    is_button_pressed,
    play_music,
    set_trapdoor_position,
    stop,
    waiting_leds_state,
)


def initialize_robot() -> bool:
    try:
        stop()
        if not set_trapdoor_position(0):
            raise RuntimeError("Initialisation de la trappe impossible")
        if not initialize_ultrasonic_sensor():
            raise RuntimeError("Initialisation du capteur URM09 impossible")
        play_music(AvailableMusics.SUCCESS_START)
        return True
    except Exception as exc:
        print("Erreur d'initialisation :", exc)
        stop()
        return False


def monitor_idle_state():
    print("Luminosite :", get_brightness(), "% | Hauteur :", get_height(), "cm")
    time.sleep(0.125)


def handle_start_action(decision_engine) -> bool:
    print("Demarrage de la mission...")
    in_action_leds_state()
    try:
        return decision_engine.run_intelligence()
    finally:
        stop()


def loop():
    engine = Intelligence(settings.distance_sensor, settings.brightness_sensor)
    waiting_leds_state()

    while True:
        if not is_button_pressed(settings.start_button):
            monitor_idle_state()
            continue

        try:
            success = handle_start_action(engine)
        except Exception as exc:
            print("Erreur d'execution :", exc)
            success = False
            stop()
            try:
                set_trapdoor_position(0)
            except Exception:
                pass

        if not success:
            print("Mission interrompue : remise a zero necessaire.")
            error_leds_state()
            while True:
                time.sleep(1)

        print("Mission terminee.")
        waiting_leds_state()
        # Anti-redémarrage si le bouton reste appuyé.
        while is_button_pressed(settings.start_button):
            time.sleep(0.05)


def main():
    print("R.A.L.F. : initialisation")
    if not initialize_robot():
        error_leds_state()
        while True:
            time.sleep(1)

    print("Robot initialise. En attente du bouton.")
    initialized_leds_state()
    time.sleep(0.5)
    try:
        loop()
    except Exception as exc:
        stop()
        try:
            set_trapdoor_position(0)
        except Exception:
            pass
        print("Erreur fatale :", exc)
        error_leds_state()
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
