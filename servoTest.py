import board
from time import sleep
from digitalio import DigitalInOut, Direction, Pull
import pwmio
from adafruit_motor import servo

buttonA = DigitalInOut(board.GP15)
buttonA.direction = Direction.INPUT
buttonA.pull = Pull.DOWN

buttonB = DigitalInOut(board.GP14)
buttonB.direction = Direction.INPUT
buttonB.pull = Pull.DOWN

# create a PWMOut object on Pin A2.
pwm = pwmio.PWMOut(board.GP13, frequency=50)
# Create a servo object, my_servo.
my_servo = servo.ContinuousServo(pwm)

while True:
    if buttonA.value == True and buttonB.value == False:
        print("A")
        my_servo.throttle = 1.0
    elif buttonB.value == True and buttonA.value == False:
        print("B")
        my_servo.throttle = -1.0
    else:
        my_servo.throttle = 0.0