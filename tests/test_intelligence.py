"""Tests sur PC par simulation des lectures et actionneurs (aucun matériel requis)."""
import importlib.util
import pathlib
import sys
import types
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def monotonic(self):
        return self.t

    def sleep(self, duration):
        self.t += duration


class FakeSensor:
    def __init__(self, distance=None):
        self.distance = distance

    def get_value(self):
        if self.distance is None:
            return 0
        return round(self.distance.brightness / 100 * 65535)


class FakeDistance:
    def __init__(self, series, brightness_fn=None):
        self.readings = iter(series)
        self.brightness_fn = brightness_fn or (lambda h: 60)
        self.brightness = 60
        self.heights = []

    def get_distance(self):
        h = next(self.readings, -1)
        self.heights.append(h)
        self.brightness = self.brightness_fn(h)
        return h


def load_module(readings, brightness_fn=None, *, mode="CONTRAST_OR_DISTANCE", overrides=None):
    settings = types.SimpleNamespace(
        START_PROPAGATION_HEIGHT=20, END_PROPAGATION_HEIGHT=10,
        STOP_PROPAGATION_HEIGHT=5, SECURITY_LEEWAY=1,
        MOTOR_POWER_BEFORE_RELEASE=37, MOTOR_POWER_DURING_RELEASE=61,
        MOTOR_POWER_AFTER_RELEASE=23,
        BRIGHTNESS_DROP_DETECTION=30, STOP_BRIGHTNESS_CHANGE_PERCENT=20,
        STOP_DETECTION_MODE=mode, MAX_INVALID_READINGS=8,
        DISTANCE_SAMPLES=3, MAX_HEIGHT_CHANGE_CM_PER_READING=2,
        MAX_MEDIAN_JUMP_CM=4, BRIGHTNESS_SAMPLES=20,
        BRIGHTNESS_CONFIRM_SAMPLES=2, MIN_BRIGHTNESS_SAMPLES=5,
        BRIGHTNESS_DETECTION_WINDOW=1, TRAPDOOR_OPEN_ANGLE=45,
        SENSOR_READ_INTERVAL_S=0.05, MAX_RUN_TIME_S=100,
    )
    for key, val in (overrides or {}).items():
        setattr(settings, key, val)

    logger = []
    clock = FakeClock()
    height = FakeDistance(readings, brightness_fn)
    brightness = FakeSensor(height)
    fake_utils = types.ModuleType("utils")
    fake_utils.settings = settings
    fake_utils.DFRobot_URM09 = FakeDistance
    fake_utils.Sensor = FakeSensor
    fake_utils.AvailableMusics = types.SimpleNamespace(BIRTHDAY=["note"])
    fake_utils.error_leds_state = lambda: logger.append(("error_leds", None))
    fake_utils.forward = lambda speed: logger.append(("motor", speed))
    fake_utils.stop = lambda: logger.append(("stop", 0))
    fake_utils.play_music = lambda tune: logger.append(("music", tune))
    fake_utils.set_trapdoor_position = lambda angle: (logger.append(("trap", angle)), True)[1]
    sys.modules["utils"] = fake_utils
    spec = importlib.util.spec_from_file_location("ralf_intelligence_testing", BASE / "intelligence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.time = clock
    engine = module.Intelligence(height, brightness)
    return engine, logger, height, clock, module


class IntelligenceTests(unittest.TestCase):
    def test_three_steps_distance_fallback(self):
        engine, log, height, _, _ = load_module(range(60, -1, -1))
        self.assertTrue(engine.run_intelligence())
        self.assertEqual([v for k, v in log if k == "motor"], [37, 61, 23])
        self.assertEqual([v for k, v in log if k == "trap"], [45, 0, 0])
        self.assertGreaterEqual(len([1 for k, _ in log if k == "stop"]), 2)
        self.assertTrue(any(v <= 5 for v in height.heights if isinstance(v, int)))
        self.assertLess(height.heights[-1], 10)

    def test_brightness_contrast_for_final_tape(self):
        steps = [round(60 - i * 0.1, 1) for i in range(580)]
        def brightness(h):
            if 19.5 <= h <= 20.5 or 9.5 <= h <= 10.5:
                return 20
            if 5.3 <= h <= 5.9:
                return 90  # 3e repère plus clair que le câble
            return 60
        engine, log, height, _, _ = load_module(steps, brightness_fn=brightness)
        self.assertTrue(engine.run_intelligence())
        self.assertEqual([v for k, v in log if k == "motor"], [37, 61, 23])
        self.assertTrue(5 < height.heights[-1] < 7,
                        "le scotch final lumineux doit être détecté avant le seuil de secours")

    def test_no_contrast_mode_stops_at_height(self):
        steps = [round(60 - i * 0.1, 1) for i in range(600)]
        engine, log, height, _, _ = load_module(steps, mode="DISTANCE_ONLY")
        self.assertTrue(engine.run_intelligence())
        self.assertLessEqual(height.heights[-1], 5)
        self.assertIn(("motor", 23), log)

    def test_invalid_sensor_samples_force_emergency(self):
        readings = [60, 59, 58] + [-1] * 10
        engine, log, _, _, _ = load_module(readings)
        self.assertFalse(engine.run_intelligence())
        self.assertNotIn(("trap", 45), log)
        self.assertIn(("error_leds", None), log)
        self.assertEqual(log[-1], ("trap", 0))

    def test_invalid_power_refused_before_motor(self):
        for value in [-1, 0, 101, True, "50"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    load_module([60] * 20, overrides={"MOTOR_POWER_AFTER_RELEASE": value})

    def test_bad_height_order_refused(self):
        with self.assertRaises(ValueError):
            load_module([60] * 20, overrides={"STOP_PROPAGATION_HEIGHT": 12})

    def test_invalid_stop_mode_refused(self):
        with self.assertRaises(ValueError):
            load_module([60] * 20, mode="COLOR_SENSOR")

    def test_timeout_stops_motor(self):
        engine, log, _, _, _ = load_module([60]*150, overrides={"MAX_RUN_TIME_S": 0.5})
        self.assertFalse(engine.run_intelligence())
        self.assertEqual(log[-1], ("trap", 0))
        self.assertIn(("error_leds", None), log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
