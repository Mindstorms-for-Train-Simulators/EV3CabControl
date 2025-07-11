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
reverser = ColorSensor(Port.S2)

# Buttons
touch = TouchSensor(Port.S3)
beacon = InfraredSensor(Port.S4)
brick = EV3Brick()

with open("assets/specs.json", "r") as f:
    data = json.load(f)

# Extract values
throttleMAX = data.get("throttle")
autobrakeMAX = data.get("autobrake")
indbrakeMAX = data.get("indbrake")


while True:
    masterList = [[scrunch(throttle, throttleMAX), None, None], []] # Levers, Keys

    wait(10)



def scrunch(v, max_val):
    s = (min(max(v / max_val * 100, 0), 100) - 50) * 2
    return 0 if -5 < s < 5 else 95 + (s - 95) if s > 95 else -95 - (-95 - s) if s < -95 else s