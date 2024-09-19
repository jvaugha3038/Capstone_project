import board
from time import sleep
from digitalio import DigitalInOut, Direction

buttonA = DigitalInOut(board.GP0)
buttonA.direction = Direction.INPUT
buttonA.pull = Pull.DOWN

buttonB = DigitalInOut(board.GP1)
buttonB.direction = Direction.INPUT
buttonB.pull = Pull.DOWN

while True:
    if buttonA == True:
        print("A")
    if buttonB == True:
        print("B")