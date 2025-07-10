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
