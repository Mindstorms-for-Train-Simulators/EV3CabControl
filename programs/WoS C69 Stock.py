#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor, InfraredSensor
from pybricks.parameters import Port, Button, Color
from pybricks.tools import wait

import json
import socket

# Initialize hardware
brick = EV3Brick()
leftLever = Motor(Port.A)
middleLever = Motor(Port.B)
rightLever = Motor(Port.C)
color = ColorSensor(Port.S2)
touch = TouchSensor(Port.S3)
beacon = InfraredSensor(Port.S4)

# Load configuration
with open("assets/specs.json", "r") as f:
    specs = json.load(f)
leftLeverMAX = specs.get("left")
middleLeverMAX = specs.get("middle")
rightLeverMAX = specs.get("right")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((specs.get("HOST"), specs.get("PORT")))

# Unified button map (channel: {button: (sequence)})
buttons = {
    -1: {
        "touch": ("c",)
    },
    0: {
        Button.UP: ("h",),
        Button.LEFT: ("x",)
    },
    1: {
        Button.LEFT_UP: ("f5",),
        Button.RIGHT_UP: ("f6",),
        Button.LEFT_DOWN: ("f7",),
        Button.RIGHT_DOWN: ("f8",)
    }, 
    2: {
    }, 
    3: {
        Button.LEFT_UP: ("l",),
        Button.RIGHT_UP: ("0",),
        Button.LEFT_DOWN: ("9",),
        Button.RIGHT_DOWN: ("b+v",)
    }, 
    4: {
        Button.LEFT_UP: ("end",),
        Button.RIGHT_UP: ("down",),
        Button.LEFT_DOWN: ("page down",)
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
            is_pressed = btn in current
            was_pressed = prev_map[ch][btn]

            # Output current sequence while button is held
            if is_pressed:
                key = sequence[index_map[ch][btn]]
                output.append(key)

            # Advance sequence only after full release + next press (falling edge then rising edge)
            if was_pressed and not is_pressed and len(sequence) > 1:
                index_map[ch][btn] = (index_map[ch][btn] + 1) % len(sequence)

            # Update previous press state
            prev_map[ch][btn] = is_pressed

    return output

brick.screen.load_image("assets/images/TSC C69 Stock.png")

sock.send((json.dumps({
    "type": "CONFIG",
    "left": None,
    "middle": None,
    "right": None,
    "color": None
}) + "\n").encode())

deadman = False

while True:
    if Button.CENTER in brick.buttons.pressed():
        sock.send((json.dumps({
            "type": "END",
        }) + "\n").encode())
        sock.close()
        break
    
    buttonsList = handle_buttons(buttons, sequence_index, prev_pressed)

    # Special Stuff
    # Check deadman
    if not deadman and color.color() == Color.WHITE:
        buttonsList.append("tab")
        deadman = True
    elif deadman and color.color() == Color.BLACK:
        buttonsList.append("tab") 
        deadman = False

    sock.send((json.dumps({
        "type": "DATA",
        "left": None,
        "middle": None,
        "right": None,
        "color": None,
        "buttons": buttonsList
    }) + "\n").encode())

    wait(5)
