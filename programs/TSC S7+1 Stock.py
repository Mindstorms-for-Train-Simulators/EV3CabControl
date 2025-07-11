#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor, InfraredSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait
import json

# Initialize hardware
brick = EV3Brick()
throttle = Motor(Port.A)
autobrake = Motor(Port.B)
indbrake = Motor(Port.C)
reverser = ColorSensor(Port.S2)
touch = TouchSensor(Port.S3)
beacon = InfraredSensor(Port.S4)

# Load configuration
with open("assets/specs.json", "r") as f:
    specs = json.load(f)
throttleMAX = specs.get("throttle")
autobrakeMAX = specs.get("autobrake")
indbrakeMAX = specs.get("indbrake")

# Normalize lever input
def scrunch(motor, max_val):
    if not max_val:
        return 0  # avoid division if config is missing or zero
    angle = motor.angle()
    s = (min(max(angle / max_val * 100, 0), 100) - 50) * 2
    return 0 if -5 < s < 5 else 95 + (s - 95) if s > 95 else -95 - (-95 - s) if s < -95 else s

# Unified button map (channel: {button: (sequence)})
buttons = {
    -1: {
        "touch": ("Shift+W", "Shift+S")
    },
    0: {
        Button.UP: ("B"),
        Button.DOWN: (" "),
        Button.LEFT: ("Left"),
        Button.RIGHT: (" Right")
    },
    1: {
        Button.LEFT_UP: ("U", "R"),
        Button.RIGHT_UP: ("O", "R"),
        Button.LEFT_DOWN: ("Ctrl+U", "Shift+U"),
        Button.RIGHT_DOWN: ("Ctrl+O", "Shift+O")
    }, 
    2: {
        Button.LEFT_UP: ("V"),
        Button.RIGHT_UP: (),
        Button.LEFT_DOWN: ("Shift+V"),
        Button.RIGHT_DOWN: ()
    }, 
    3: {

    }, 
    4: {

    }  
}

# State trackers
sequence_index = {ch: {btn: 0 for btn in buttons[ch]} for ch in buttons}
prev_pressed = {ch: {btn: False for btn in buttons[ch]} for ch in buttons}

# Get current buttons per channel
def get_buttons(channel):
    if channel == -1:
        return ["touch"] if touch.pressed() else []
    elif channel == 0:
        return brick.buttons.pressed()
    else:
        return beacon.buttons(channel)

# Handle all inputs
def handle_buttons(mapping, index_map, prev_map):
    output = []
    for ch in mapping:
        current = get_buttons(ch)
        for btn, sequence in mapping[ch].items():
            pressed = btn in current
            if pressed and not prev_map[ch][btn]:
                key = sequence[index_map[ch][btn]]
                output.append(key)
                if len(sequence) > 1:
                    index_map[ch][btn] = (index_map[ch][btn] + 1) % len(sequence)
            prev_map[ch][btn] = pressed
    return output

while True:
    if Button.CENTER in brick.buttons.pressed():
        break
    
    levers = [scrunch(throttle, throttleMAX), None, None]
    keys = handle_buttons(buttons, sequence_index, prev_pressed)
    masterList = [levers, keys]
    print(masterList)
    wait(10)