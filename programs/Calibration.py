#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor, InfraredSensor)
from pybricks.parameters import Port
from pybricks.tools import wait

# Other imports
import json

throttle = Motor(Port.A)
autobrake = Motor(Port.B)
indbrake = Motor(Port.C)
reverser = ColorSensor(Port.S1)

# Buttons
touch = TouchSensor(Port.S2)
beacon = InfraredSensor(Port.S3)
brick = EV3Brick()

brick.screen.clear()
brick.screen.print("Please set all levers\nto the most back\nwards position.")
brick.speaker.beep()
brick.screen.print("Press the touch\nsensor to continue.")
while not touch.pressed():
    wait(10)

while touch.pressed():
    wait(10)


throttle.reset_angle(0)
autobrake.reset_angle(0)
indbrake.reset_angle(0)

brick.screen.clear()
brick.screen.print("Please set all levers\nto the most forw\nard position.")
brick.speaker.beep()
brick.screen.print("Press the touch\nsensor to continue.")
while not touch.pressed():
    wait(10)

while touch.pressed():
    wait(10)


throttlemax = throttle.angle()
autobrakemax = autobrake.angle()
indbrakemax = indbrake.angle()

# Path to your JSON file
filename = 'assets/specs.json'

# Step 1: Load existing JSON data
with open(filename, 'r') as file:
    data = json.load(file)

# Step 2: Modify the values
data['throttle'] = throttlemax
data['autobrake'] = autobrakemax
data['indbrake'] = indbrakemax

# Step 3: Write updated data back to the JSON file
with open(filename, 'w') as file:
    json.dump(data, file, indent=4)

brick.screen.clear()
brick.screen.print("Calibration complete!")
brick.screen.print("Exit the program by\npressing the back\nbutton")
brick.speaker.beep()

while not touch.pressed():
    wait(10)

brick.screen.clear()
brick.screen.print("In debugging mode.")

while True:
    print("----------------------------------------------------")
    print(brick.buttons.pressed())
    print(str(beacon.buttons(1)) + ", " + str(beacon.buttons(2)) + ", " + str(beacon.buttons(3)) + ", " + str(beacon.buttons(4)))
    print(str(throttle.angle()) + ", " + str(autobrake.angle()) + ", " + str(indbrake.angle()))
    print(str(reverser.color()) + ", " + str(touch.pressed()))
    wait(10)