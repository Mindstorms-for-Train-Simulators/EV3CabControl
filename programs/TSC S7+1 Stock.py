#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor, InfraredSensor
from pybricks.parameters import Port, Button, Color
from pybricks.tools import wait

import json
import socket

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

# Unified button map (channel: {button: (sequence)})
buttons = {
    -1: {
        "touch": ("Shift+W", "Shift+S")
    },
    0: {
        Button.UP: (" "),
        Button.DOWN: ("B"),
        Button.LEFT: ("Left",),
        Button.RIGHT: ("Right",)
    },
    1: {
        Button.LEFT_UP: ("T+U", "R"),
        Button.RIGHT_UP: ("T+O", "R"),
        Button.LEFT_DOWN: ("Ctrl+U", "Shift+U"),
        Button.RIGHT_DOWN: ("Ctrl+O", "Shift+O")
    }, 
    2: {
        Button.LEFT_UP: ("V"),
        Button.LEFT_DOWN: ("Shift+V",)
    }, 
    3: {

    }, 
    4: {

    }  
}

HOST = "10.0.1.2"
PORT = 1337
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

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

            # If button is currently pressed
            if is_pressed:
                # Always output the current sequence key while held
                key = sequence[index_map[ch][btn]]
                output.append(key)

                # If this is a new press (rising edge), advance sequence
                if not was_pressed and len(sequence) > 1:
                    index_map[ch][btn] = (index_map[ch][btn] + 1) % len(sequence)

            # Update previous press state
            prev_map[ch][btn] = is_pressed

    return output

def setMCS():
    mcpos = scrunch(indbrake, indbrakeMAX)
    if mcpos == -100:
        # Shutdown
        return 1
    elif mcpos < -60:
        # Protected Manual
        return 2
    elif mcpos < -20:
        # Auto
        return 3
    elif mcpos < 20:
        # Tripcock - use for driving
        return 4
    elif mcpos < 60:
        # Forward
        return 5
    elif mcpos < 80:
        # Protected Manual
        return 6
    elif mcpos < 100:
        # Inter
        return 7
    else:
        #lever at 100, reverse.
        return 8

brick.screen.load_image("assets/images/TSC S7+1 Stock.png")

sock.send(json.dumps({
    "type": "CONFIG",
    "config": ["ThrottleAndBrake"]
}).encode())

deadman = False
mcs = 1 # 1-8 (1=shutdown)
while True:
    if Button.CENTER in brick.buttons.pressed():
        sock.send(json.dumps({
            "type": "END",
        }).encode())
        sock.close()
        break
    
    buttonsList = [handle_buttons(buttons, sequence_index, prev_pressed)]


    # Special Stuff
    # Check deadman
    if not deadman and reverser.color() == Color.WHITE:
        buttonsList.append("Shift+E")
        deadman = True
    elif deadman and reverser.color() == Color.BLACK:
        buttonsList.append("Shift+E") 
        deadman = False

    # Check MCS
    target = setMCS()
    if target != mcs:
        if target > mcs:
            buttonsList.append("W")
            mcs = mcs + 1
        elif target < mcs:
            buttonsList.append("S")
            mcs = mcs - 1

    sock.send(json.dumps({
        "type": "DATA",
        "levers": [scrunch(throttle, throttleMAX), None, None],
        "buttons": buttonsList
    }).encode())
    wait(5)