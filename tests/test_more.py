"""Tests de configuration TOML et de persistance du pilote servo."""
import importlib.util
import pathlib
import unittest.mock
import sys
import tomllib
import types
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]


class ExtraTests(unittest.TestCase):
    def test_toml_has_three_independent_powers(self):
        with (BASE / 'settings.toml').open('rb') as f:
            p = tomllib.load(f)
        self.assertEqual(p['MOTOR_POWER_BEFORE_RELEASE'], 100)
        self.assertEqual(p['MOTOR_POWER_DURING_RELEASE'], 100)
        self.assertEqual(p['MOTOR_POWER_AFTER_RELEASE'], 100)
        self.assertLess(p['STOP_PROPAGATION_HEIGHT'], p['END_PROPAGATION_HEIGHT'])
        self.assertLess(p['END_PROPAGATION_HEIGHT'], p['START_PROPAGATION_HEIGHT'])

    def test_servo_keeps_driver_and_calibration(self):
        class PWMOut:
            def __init__(self, pin, duty_cycle=0, frequency=50):
                self.pin, self.duty_cycle, self.frequency = pin, duty_cycle, frequency

        class AdafruitServo:
            init_calls = 0
            def __init__(self, pwm):
                AdafruitServo.init_calls += 1
                self.pwm = pwm
                self.pulse_range = (750, 2250)
                self.angle = None
            def set_pulse_width_range(self, a, b):
                self.pulse_range = a, b

        pwmio = types.ModuleType('pwmio')
        pwmio.PWMOut = PWMOut
        adafruit = types.ModuleType('adafruit_motor')
        adafruit.servo = types.SimpleNamespace(Servo=AdafruitServo)
        adafruit.motor = types.SimpleNamespace(DCMotor=lambda a,b: None)
        with unittest.mock.patch.dict(sys.modules, {'pwmio':pwmio, 'adafruit_motor':adafruit}):
            spec = importlib.util.spec_from_file_location('patched_wumons_motor', BASE / 'lib/wumons/motor.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            s = module.Servo('GP6')
            s.set_pulse_width_range(300, 1900)
            s.set_angle(45)
            s.set_angle(0)
            self.assertEqual(AdafruitServo.init_calls, 1)
            self.assertEqual(s._driver.pulse_range, (300, 1900))
            self.assertEqual(s.angle, 0)


if __name__ == '__main__':
    unittest.main()
