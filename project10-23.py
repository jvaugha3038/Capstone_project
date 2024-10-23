import board
from time import sleep
from digitalio import DigitalInOut, Direction, Pull
import pwmio
from adafruit_motor import servo
import rotaryio
from lcd.lcd import LCD
import busio
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from lcd.lcd import CursorMode #most of the import soup

import adafruit_fingerprint
uart = busio.UART(board.GP0, board.GP1, baudrate=57600)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart) #fingerprint setup/imports

buttonA = DigitalInOut(board.GP15)
buttonA.direction = Direction.INPUT
buttonA.pull = Pull.DOWN #setting up button A

buttonB = DigitalInOut(board.GP14)
buttonB.direction = Direction.INPUT
buttonB.pull = Pull.DOWN #setting up button B

pwm = pwmio.PWMOut(board.GP13, frequency=50)
my_servo = servo.ContinuousServo(pwm) #servo setup

rButton = DigitalInOut(board.GP19)
rButton.direction = Direction.INPUT
rButton.pull = Pull.UP #this is VERY annoying but it didnt work when it was pulled down
enc = rotaryio.IncrementalEncoder(board.GP20, board.GP21)
last_position = None #all of the rotary encoder setup

i2c = busio.I2C(scl=board.GP3, sda=board.GP2)
lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=2, num_cols=16) #lcd setup

code="N/A"
state="write"
door="open" #some variables we need

def get_fingerprint(): #checks fingerprint for a match
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

# pylint: disable=too-many-branches
def get_fingerprint_detail(): #same as above, but returns error messages
    """Get a finger print image, template it, and see if it matches!
    This time, print out each error instead of just returning on failure"""
    print("Getting image...", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image taken")
    else:
        if i == adafruit_fingerprint.NOFINGER:
            print("No finger detected")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")
        return False

    print("Templating...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
        return False

    print("Searching...", end="")
    i = finger.finger_fast_search()
    # pylint: disable=no-else-return
    # This block needs to be refactored when it can be tested.
    if i == adafruit_fingerprint.OK:
        print("Found fingerprint!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No match found")
        else:
            print("Other error")
        return False

# pylint: disable=too-many-statements
def enroll_finger(location): 
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True


def get_num(): 
    """Use input() to get a valid number from 1 to 127. Retry till success!"""
    i = 0
    while (i > 127) or (i < 1):
        try:
            i = int(input("Enter ID # from 1-127: ")) #dial to pick #, button to select
        except ValueError:
            pass
    return i


def fPrintMenu(): 
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates:", finger.templates)
    print("e) enroll print") 
    print("f) find print") #only this one will be available if door is closed
    print("d) delete print")
    print("----------------") #menu will be controlled via rotary encoder
    c = input("> ") #A button will select mode

    if c == "e":
        enroll_finger(get_num())
    if c == "f":
        if get_fingerprint():
            print("Detected #", finger.finger_id, "with confidence", finger.confidence)
        else:
            print("Finger not found")
    if c == "d":
        if finger.delete_model(get_num()) == adafruit_fingerprint.OK:
            print("Deleted!")
        else:
            print("Failed to delete")

################################################## none of the functions above this have been implemented yet
################################################## every print statement will be an lcd.print instead

def setCode(): #lets user change code
    codeNew = ""
    x=["a","b","c","d","e"]
    for letter in x: #very mid method of looping this process but it works
        while rButton.value: #counterintuitive, but checks when button is NOT pressed
            position = enc.position
            if position != last_position:
                if abs(position) > 9: #number cant go past 0 or 9
                    position = 9
                if position < 0:
                    position = 0
                lcd.clear()
                lcd.print("New code:"+str(codeNew)+str(position)) #shows the code and the number you have selected, didnt feel like using f-strings
                sleep(.5)
        if not rButton.value:
            codeNew=(codeNew + str(position))
            print(codeNew)
            while buttonA.value:
                sleep(.1)

    if codeNew != "": #sets the code
        lcd.print("New code set.")
        code = int(codeNew)
        print(str(code))
        sleep(2)
        return code


def writeCode(): #exact same format as setCode but will open box if code is correct
    codeTry = ""
    x=["a","b","c","d","e"]
    for letter in x:
        while rButton.value:
            position = enc.position
            if position != last_position:
                if abs(position) > 9: 
                    position = 9
                if position < 0:
                    position = 0
                lcd.clear()
                lcd.print("Code:"+str(codeTry)+str(position))
                sleep(.5)
        if not rButton.value:
            codeTry=(codeTry + str(position))
            print(codeTry)
            while buttonA.value:
                sleep(.1)

    if codeTry != "":
        if codeTry == code:
            lcd.print("Code is correct.     Opening box...")
            door="open"
            sleep(5)
            return door
        else: #literally never tested
            lcd.print("Code is incorrect.")
            sleep(2) 

def infoMenu(): #simple instructions to use the box, now outdated
    page=-1 
    while not buttonB.value:
        if rButton.value:
            if page == 0:
                lcd.clear()
                lcd.print("Press A to swap between modes")
            if page == 1:
                lcd.clear()
                lcd.print("Press B to      select a mode") #weird text breaks like this are so words don't get cut off
            if page == 2:
                lcd.clear()
                lcd.print("SETTING A CODE  1.Enter set mode")
            if page == 3:
                lcd.clear()
                lcd.print("2.Turn dial to anumber, press A") 
            if page == 4:
                lcd.clear()
                lcd.print("Repeat until newcode is set")
            if page == 5:
                lcd.clear()
                lcd.print("ENTER A CODE 1. Enter write mode")
            if page == 6:
                lcd.clear()
                lcd.print("2. Turn dial to enter code")
            if page == 7:
                lcd.clear()
                lcd.print("Box must be opento set a code")
            if page == 8:
                lcd.clear()
                lcd.print("Press B to exit this, by the way")
            if page > 8:
                page = 0

        else:
            page+=1
            while not rButton.value: #these are so the program doesnt freak out when a button gets held 
                sleep(.1)
        sleep(.5)
    if buttonB.value:
        while buttonB.value: 
                sleep(.1)
        return(1)

while True:
    lcd.clear()
    lcd.print("Press dial for  instructions")
    if not rButton.value: 
        infoMenu()
    if buttonA.value: #changes mode based on whether box is open or closed
        if door == "closed": #can't change anything when box is closed
            if state == "write":
                lcd.clear()
                state = "fingerprint"
                lcd.print("STATE SET TO    FINGERPRINT")
                print(state)
                while buttonA.value:
                    sleep(.1)
            if state == "fingerprint":
                lcd.clear()
                state = "write"
                lcd.print("STATE SET TO    WRITE")
                print(state)
                while buttonA.value:
                    sleep(.1)
        if door == "open": #you can change code and add/remove fingerprints when box is open
            if state == "set":
                lcd.clear()
                state = "fingerprint"
                lcd.print("STATE SET TO    FINGERPRINT")
                print(state)
                while buttonA.value:
                    sleep(.1)
            if state == "fingerprint":
                lcd.clear()
                state = "door" #this exists bc i forgot to have a way to close the box
                lcd.print("STATE SET TO    DOOR") 
                print(state)
                while buttonA.value:
                    sleep(.1)
            if state == "door":
                lcd.clear()
                state = "set"
                lcd.print("STATE SET TO    SET")
                print(state)
                while buttonA.value:
                    sleep(.1)
    if buttonB.value: #starts whatever mode is currently on when pressed
        if door == "closed":    
            if state == "write":
                lcd.clear()
                lcd.print("--Enter Code--")
                sleep(2)
                enterCode()
            if state == "fingerprint":
                lcd.clear()
                lcd.print("-Open w/ Print-")
                sleep(2)
                #will lead to fingerprint section when implemented

        if door == "open":
            if state == "door"    
                lcd.clear()
                lcd.print("Closing box...")
                sleep(5)
                door="closed"
                state="write"
            if state == "set":
                lcd.clear()
                lcd.print("--Set New Code--")
                sleep(2)
                setCode()
            if state == "fingerprint":
                lcd.clear()
                lcd.print("Add/Remove Print")
                sleep(2)
                #will lead to fingerprint section when implemented

    position = last_position
    sleep(.5)