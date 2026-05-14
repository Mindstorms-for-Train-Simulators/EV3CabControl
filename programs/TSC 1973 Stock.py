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
        "touch": ("ctrl+shift+s",)
    },
    0: {
        Button.UP: ("space",),
        Button.DOWN: ("ctrl+=",),
        Button.LEFT: ("v",),
        Button.RIGHT: ("right",)
    },
    1: {
        Button.LEFT_UP: ("t",),
        Button.RIGHT_UP: ("t",),
        Button.LEFT_DOWN: ("shift+n",),
        Button.RIGHT_DOWN: ("shift+o",)
    }, 
    2: {
        Button.RIGHT_UP: ("pageup",),
        Button.RIGHT_DOWN: ("pagedown",)
    }, 
    3: {
        Button.LEFT_UP: ("h", "shift+h",),
        Button.RIGHT_UP: ("shift+l",),
        Button.LEFT_DOWN: ("l",),
        Button.RIGHT_DOWN: ("ctrl+shift+v",)
    }, 
    4: { # Cameras
        Button.LEFT_UP: ("1",),
        Button.RIGHT_UP: ("2",),
        Button.LEFT_DOWN: ("3",),
        Button.RIGHT_DOWN: ("8",)
    }  
}

# Normalize lever input
def scrunch(motor, max_val):
    if not max_val:
        return 0  # avoid division if config is missing or zero
    angle = motor.angle()
    s = (min(max(angle / max_val * 100, 0), 100) - 50) * 2
    return 0 if -5 < s < 5 else 95 + (s - 95) if s > 95 else -95 - (-95 - s) if s < -95 else s

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

brick.screen.load_image("assets/images/TSC 1973 Stock.png")

sock.send((json.dumps({
    "type": "CONFIG",
    "left": "ThrottleAndBrake",
    "middle": None,
    "right": "Reverser",
    "color": None
}) + "\n").encode())

handbrake = False

while True:
    if Button.CENTER in brick.buttons.pressed():
        sock.send((json.dumps({
            "type": "END",
        }) + "\n").encode())
        sock.close()
        break
    
    buttonsList = handle_buttons(buttons, sequence_index, prev_pressed)

    if not handbrake and color.color() == Color.WHITE:
        buttonsList.append("/")
        handbrake = True
    elif handbrake and color.color() == Color.BLACK:
        buttonsList.append("/") 
        handbrake = False

    sock.send((json.dumps({
        "type": "DATA",
        "left": scrunch(leftLever, leftLeverMAX),
        "middle": None,
        "right": scrunch(rightLever, rightLeverMAX),
        "color": None,
        "buttons": buttonsList
    }) + "\n").encode())

    wait(5)
