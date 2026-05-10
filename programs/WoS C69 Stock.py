#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, TouchSensor, ColorSensor, InfraredSensor
from pybricks.parameters import Port, Button, Color
from pybricks.tools import wait

import json
import socket

brick = EV3Brick()
leftLever = Motor(Port.A)
middleLever = Motor(Port.B)
rightLever = Motor(Port.C)
color = ColorSensor(Port.S2)
touch = TouchSensor(Port.S3)
beacon = InfraredSensor(Port.S4)

with open("assets/specs.json", "r") as f:
    specs = json.load(f)
leftLeverMAX = specs.get("left")
middleLeverMAX = specs.get("middle")
rightLeverMAX = specs.get("right")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((specs.get("HOST"), specs.get("PORT")))

buttons = {
    -1: {"touch": ("c",)},
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
    2: {},
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

sequence_index = {ch: {btn: 0 for btn in buttons[ch]} for ch in buttons}
prev_pressed = {ch: {btn: False for btn in buttons[ch]} for ch in buttons}

def getNotch(lever, levermax, numNotches):
    if levermax == 0:
        return 0

    ratio = lever.angle() / levermax
    ratio = max(0, min(1, ratio))
    idx = int(ratio * numNotches)
    if idx >= numNotches:
        idx = numNotches - 1

    return idx

def evalMove(currTBC, currSS, nextTBC, nextSS):
    #TBC: 0:ShutDown, 1:Emergency, 2:Service, 3:Lap, 4:Max, 5:Nor, 6:Min, 7:Hold, 8:Off, 9:Shunt, 10:Series, 11:Parallel
    #SS:  0:ShutDown, 1:Auto, 2:Forward, 3:Inter, 4:Reverse
    # if currTBC >= 9 and currSS != nextSS:
    #     return False
    # if currTBC != nextTBC and nextTBC > 1 and currSS == 0:
    #     return False
    # if currTBC < nextTBC and nextTBC == 1 and currSS != 0:
    #     return False
    return True

def get_buttons(channel):
    if channel == -1:
        return ["touch"] if touch.pressed() else []
    elif channel == 0:
        return brick.buttons.pressed()
    else:
        return beacon.buttons(channel)

def handle_buttons(mapping, index_map, prev_map):
    out = []
    for ch in mapping:
        current = get_buttons(ch)
        for btn, seq in mapping[ch].items():
            is_pressed = btn in current
            was_pressed = prev_map[ch][btn]

            if is_pressed:
                out.append(seq[index_map[ch][btn]])

            if was_pressed and not is_pressed and len(seq) > 1:
                index_map[ch][btn] = (index_map[ch][btn] + 1) % len(seq)

            prev_map[ch][btn] = is_pressed
    return out

brick.screen.load_image("assets/images/WoS C69 Stock.png")

sock.send((json.dumps({
    "type": "CONFIG",
    "left": None,
    "middle": None,
    "right": None,
    "color": None
}) + "\n").encode())

deadman = False

TBCnotch = 0
SSnotch = 0

while True:
    if Button.CENTER in brick.buttons.pressed():
        sock.send((json.dumps({
            "type": "END",
        }) + "\n").encode())
        sock.close()
        break
    
    buttonsList = handle_buttons(buttons, sequence_index, prev_pressed)

    newTBC = getNotch(leftLever, leftLeverMAX, 12)
    newSS = getNotch(rightLever, rightLeverMAX, 5)
    if newTBC != TBCnotch or newSS != SSnotch:
        if evalMove(TBCnotch, SSnotch, newTBC, newSS):
            if newTBC < TBCnotch:
                buttonsList.append("d")
            elif newTBC > TBCnotch:
                buttonsList.append("a")
            if newSS < SSnotch:
                buttonsList.append("s")
            elif newSS > SSnotch:
                buttonsList.append("w")
    TBCnotch = newTBC
    SSnotch = newSS

    if not deadman and color.color() == Color.WHITE:
        buttonsList.append("/")
        deadman = True
    elif deadman and color.color() == Color.BLACK:
        buttonsList.append("/") 
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