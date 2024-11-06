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

x=0 # "if x==0:" shows up a few times, its just so LCD prints don't get printed again if nothing changed
code="N/A" #technically, you can forgo setting a code if you want it to be more 'secure'. do not recommend.
state="set" 
door="open" #some variables we need

def get_fingerprint(): #checks fingerprint for a match
    """Get a finger print image, template it, and see if it matches!"""
    lcd.clear()
    lcd.print("Waiting for     image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    lcd.clear()
    lcd.print("Templating...")
    sleep(.3)
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    lcd.clear()
    lcd.print("Searching...")
    sleep(.3)
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

# pylint: disable=too-many-branches
def get_fingerprint_detail(): #same as above, but returns error messages
    """Get a finger print image, template it, and see if it matches!
    This time, print out each error instead of just returning on failure"""
    lcd.clear()
    lcd.print("Getting image...")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        lcd.clear()
        lcd.print("Image taken")
        sleep(2)
    else:
        lcd.print()
        if i == adafruit_fingerprint.NOFINGER:
            lcd.print("No finger       detected")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            lcd.print("Imaging error")
        else:
            lcd.print("Other error")
        sleep(2)
        return False
    lcd.clear()
    lcd.print("Templating...")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        lcd.clear()
        print("Templated")
    else:
        lcd.clear()
        if i == adafruit_fingerprint.IMAGEMESS:
            lcd.print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            lcd.print("Couldnt identifyfeatures")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            lcd.print("Image invalid")
        else:
            lcd.print("Other error")
        sleep(2)
        return False
    lcd.clear()
    lcd.print("Searching...")
    i = finger.finger_fast_search()
    # pylint: disable=no-else-return
    # This block needs to be refactored when it can be tested.
    # ^ really not sure what this means
    if i == adafruit_fingerprint.OK:
        lcd.clear()
        lcd.print("Matching print  found!")
        sleep(2)
        return True
    else:
        lcd.clear()
        if i == adafruit_fingerprint.NOTFOUND:
            lcd.print("No match found")
        else:
            lcd.print("Other error")
        sleep(2)
        return False

# pylint: disable=too-many-statements
def enroll_finger(location): 
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        lcd.clear()
        if fingerimg == 1:
            lcd.print("Place finger on sensor...")
            sleep(1.5)
        else:
            lcd.clear()
            lcd.print("Place same      finger again...")
            sleep(1.5)
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                lcd.clear()
                lcd.print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                lcd.clear()
                lcd.print("...")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                lcd.clear()
                lcd.print("Imaging error")
                return False
            else:
                lcd.clear()
                lcd.print("Other error")
                return False
                sleep(2)
        lcd.clear()
        lcd.print("Templating...")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            lcd.clear()
            lcd.print("Templated")
        else:
            lcd.clear()
            if i == adafruit_fingerprint.IMAGEMESS:
                lcd.print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                lcd.print("Couldnt identifyfeatures")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                lcd.print("Image invalid")
            else:
                lcd.print("Other error")
            sleep(2)
            return False

        if fingerimg == 1:
            lcd.clear()
            lcd.print("Remove finger")
            sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()
    lcd.clear()
    lcd.print("Creating model...")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        lcd.clear()
        lcd.print("Created")
        sleep(2)
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            lcd.clear()
            lcd.print("Prints did not match")
        else:
            lcd.clear()
            lcd.print("Other error")
        sleep(2)
        return False
    lcd.clear()
    lcd.print("Storing model #%d..." % location)
    sleep(.2)
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        lcd.clear()
        lcd.print("Stored")
    else:
        lcd.clear()
        if i == adafruit_fingerprint.BADLOCATION:
            lcd.print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            lcd.print("Flash storage error")
        else:
            lcd.print("Other error")
        sleep(2)
        return False

    return True
##################### i didnt touch any of the code above this besides changing prints to lcd.prints
def get_num(): 
    """Use input() to get a valid number from 1 to 127. Retry till success!"""
    i=0
    while rButton.value:
        position = enc.position % 127 #number cant go past 1 or 127
        if position != last_position:
            lcd.clear()
            lcd.print("Enter ID# 1-127:"+str(position))
    if not rButton.value:
        return i

def fPrintMenu(door): 
    x=0
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates:", finger.templates)
    page=0
    while not buttonB.value:
        if door == "open": #when box is open:
            if x==0:
                if page == 0: #add a new print to system
                    lcd.clear()
                    lcd.print("--Fingerprint-- -Add Print")
                if page == 1: #check if your print is in system
                    lcd.clear()
                    lcd.print("--Fingerprint-- -Find Print")
                if page == 2: #remove your print from system
                    lcd.clear()
                    lcd.print("--Fingerprint-- -Delete Print")
                if page == 3: #exit fingerprint menu
                    lcd.clear()
                    lcd.print("--Fingerprint-- -Exit")
                x=1
                if buttonA.value:
                    page+=1
                    x=0
                    if page > 3:
                        page=0
                    while not buttonA.value:
                        sleep(.1)
        else: #if box is closed:
            if x==0:
                if page == 0: #check if your print is in system, open box if true
                    lcd.clear()
                    lcd.print("--Fingerprint-- -Check Print")
                if page == 1: #exit fingerprint menu
                    lcd.clear()
                    lcd.print("--Fingerprint-- -Exit")
                x=1
                if buttonA.value:
                    page+=1
                    x=0
                    if page > 1:
                        page=0
                    while not buttonA.value:
                        sleep(.1)
    
    if buttonB.value: #just activates whatever option is up
        if door == "open":
            if page == 0:
                enroll_finger(get_num())
            if page == 1:
                if get_fingerprint():
                    lcd.clear()
                    lcd.print("Detected #" + str(finger.finger_id)+ "   Confidence: "+str(finger.confidence))
                    sleep(2)
            if page == 2:
                if finger.delete_model(get_num()) == adafruit_fingerprint.OK:
                    lcd.clear()
                    lcd.print("Deleted!")
                else:
                    lcd.clear()
                    lcd.print("Failed to delete")
                sleep(2)
            if page == 3:
                return(1)
        if door == "closed":
            if page == 0:
                if get_fingerprint():
                    lcd.clear()
                    lcd.print("Detected #" + str(finger.finger_id)+ "   Confidence: "+str(finger.confidence))
                    sleep(2)
                    lcd.print("Opening box...")
                    door="open"
                    sleep(5)
                    return(door)
                else:
                    print("Finger not found")
            if page == 1:
                return(1)

##################################################
################################################## 

def setCode(): #lets user change code
    codeNew = ""
    x=["a","b","c","d","e"]
    for letter in x: #very mid method of looping this process but it works
        while rButton.value: #counterintuitive, but checks when button is NOT pressed
            position = enc.position % 9
            if position != last_position:
                lcd.clear()
                lcd.print("New code:"+str(codeNew)+str(position)) #shows the code and the number you have selected, didnt feel like using f-strings
                sleep(.5)
        if not rButton.value:
            codeNew=(codeNew + str(position))
            print(codeNew)
            while not rButton.value:
                sleep(.1)

    if codeNew != "": #sets the code
        lcd.clear()
        lcd.print("New code set.")
        code = codeNew
        print(code)
        sleep(2)
        return code

def writeCode(code): #exact same format as setCode but will open box if code is correct
    codeTry = ""
    x=["a","b","c","d","e"]
    for letter in x:
        while rButton.value:
            position = enc.position % 9
            if position != last_position:
                lcd.clear()
                lcd.print("Code:"+str(codeTry)+str(position))
                sleep(.5)
        if not rButton.value:
            codeTry=(codeTry + str(position))
            print(codeTry)
            while not rButton.value:
                sleep(.1)

    if codeTry != "":
        print("-------")
        print(code)
        print("---")
        print(codeTry)
        if codeTry == code:
            lcd.clear()
            lcd.print("Code is correct.Opening box...")
            door="open"
            sleep(5)
            return door
        else: #literally never tested
            lcd.clear()
            lcd.print("Code is incorrect.")
            sleep(2)
            door="closed"
            return door

def infoMenu(): #simple instructions to use the box
    x=0
    page=0
    while not buttonB.value:
        if rButton.value:
            if x==0:
                if page == 0:
                    lcd.clear()
                    lcd.print("Press A (right) to switch modes")
                if page == 1:
                    lcd.clear()
                    lcd.print("Press B (left)  to select a mode") #weird formatting like this is so words don't get cut off
                if page == 2:
                    lcd.clear()
                    lcd.print("Use SET mode to set new code")
                if page == 3:
                    lcd.clear()
                    lcd.print("FINGERPRINT modeopens a new menu") 
                if page == 4:
                    lcd.clear()
                    lcd.print("Use DOOR mode toclose door")
                if page == 5:
                    lcd.clear()
                    lcd.print("WRITE mode is toopen box w/ code")
                if page == 6:
                    lcd.clear()
                    lcd.print("Open box to set new code/print")
                if page == 7:
                    lcd.clear()
                    lcd.print("Prints are only saved locally")
                if page == 8:
                    lcd.clear()
                    lcd.print("Press B to exit this, by the way")
                x=1
                if page > 8:
                    page = 0

        else:
            page+=1
            x=0
            while not rButton.value: #these are so the program doesnt freak out when a button gets held 
                sleep(.1)
        sleep(.5)
    if buttonB.value:
        while buttonB.value: 
                sleep(.1)
        return(1)

while True:
    if x==0: #only prints this line once, instead of reprinting it every [int] seconds 
        lcd.clear()
        lcd.print("Press dial for  instructions")
        x=1 
    if not rButton.value: 
        while not rButton.value:
            sleep(.1)    
        infoMenu()
        x=0 
    if buttonA.value: #changes mode based on whether box is open or closed
        if door == "closed": #can't change anything when box is closed
            if state == "write":
                lcd.clear()
                state = "fingerprint"
                lcd.print("STATE SET TO    FINGERPRINT")
                print(state)
                while buttonA.value:
                    sleep(.2)
            elif state == "fingerprint":
                lcd.clear()
                state = "write"
                lcd.print("STATE SET TO    WRITE")
                print(state)
                while buttonA.value:
                    sleep(.2)
        if door == "open": #you can change code and add/remove fingerprints when box is open
            if state == "set":
                lcd.clear()
                state = "fingerprint"
                lcd.print("STATE SET TO    FINGERPRINT")
                print(state)
                while buttonA.value:
                    sleep(.2)
            elif state == "fingerprint":
                lcd.clear()
                state = "door" 
                lcd.print("STATE SET TO    DOOR") 
                print(state)
                while buttonA.value:
                    sleep(.2)
            elif state == "door":
                lcd.clear()
                state = "set"
                lcd.print("STATE SET TO    SET")
                print(state)
                while buttonA.value:
                    sleep(.2)
        x=0
        sleep(2)
    if buttonB.value: #starts whatever mode is currently on when pressed
        if door == "closed":    
            if state == "write":
                lcd.clear()
                lcd.print(" --Enter Code-- ")
                sleep(2)
                door=(writeCode(code))
            if state == "fingerprint":
                lcd.clear()
                lcd.print(" --Print Menu-- ")
                sleep(2)
                if fPrintMenu(door) == "open":
                    door="open"
        if door == "open":
            if state == "door": #this exists bc i forgot to have a way to close the box
                lcd.clear()
                lcd.print("Closing box...")
                sleep(5)
                door="closed"
                state="write"
            if state == "set":
                lcd.clear()
                lcd.print("--Set New Code--")
                sleep(2)
                code = (setCode())
            if state == "fingerprint":
                lcd.clear()
                lcd.print(" --Print Menu-- ")
                sleep(2)
                fPrintMenu(door)
        x=0
    position = last_position