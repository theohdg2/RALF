import board
import pwmio
from adafruit_motor import motor, servo

def help():
    print("Motor help")

class DCMotor:
    def __init__(self, pinA, pinB):
        self.pinA = pinA
        self.pinB = pinB
        self.pwmA = pwmio.PWMOut(self.pinA, frequency=1000)
        self.pwmB = pwmio.PWMOut(self.pinB, frequency=1000)

    def reverse(self):
        self.pinA, self.pinB = self.pinB, self.pinA

    def set_speed(self, speed = 0):
        setDCMotor = motor.DCMotor(self.pwmA, self.pwmB)
        self.speed = speed
        setDCMotor.throttle = self.speed/100


class Servo:
    def __init__(self, pin):
        self.pin = pin
        self.pwm = pwmio.PWMOut(self.pin, duty_cycle=2 ** 15, frequency=50)

    def set_pulse_width_range(self, min_pulse: int = 750, max_pulse: int = 2250):
        setServo = servo.Servo(self.pwm)
        setServo.set_pulse_width_range(min_pulse, max_pulse)

    def set_angle(self, angle = 90):
        setServo = servo.Servo(self.pwm)
        self.angle = angle
        setServo.angle = self.angle
