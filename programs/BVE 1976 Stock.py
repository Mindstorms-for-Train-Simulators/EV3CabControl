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
    -1: {"touch": ("delete",)},
    0: {
        Button.UP: ("add",),
        Button.DOWN: ("enter",),
        Button.LEFT: ("insert",),
        Button.RIGHT: ("1",)
    },
    1: {
        Button.LEFT_UP: ("f5",),
        Button.RIGHT_UP: ("f6",),
        Button.LEFT_DOWN: ("home",),
        Button.RIGHT_DOWN: ("end",)
    },
    2: {
        Button.LEFT_UP: ("8",),
        Button.RIGHT_UP: ("2",),
        Button.LEFT_DOWN: ("9",),
        Button.RIGHT_DOWN: ("0",)
    },
    3: {
        Button.LEFT_DOWN: ("7",),
        Button.RIGHT_DOWN: ("e", "e", "ctrl+e", "ctrl+e")
    },
    4: {
        Button.LEFT_UP: ("f1",),
        Button.RIGHT_UP: ("f2",),
        Button.LEFT_DOWN: ("f3",),
        Button.RIGHT_DOWN: ("f4",)
    }
}

sequence_index = {ch: {btn: 0 for btn in buttons[ch]} for ch in buttons}
prev_pressed = {ch: {btn: False for btn in buttons[ch]} for ch in buttons}

class LeverOutput:
    def __init__(self, lever, levermax, num_notches, toNext, toBack):
        self.lever = lever
        self.levermax = levermax
        self.num_notches = num_notches
        self.last = 0
        self.next = toNext
        self.back = toBack
        self.cooldown = 0
        self.pending = 0

    def get_notch(self):
        if not self.levermax:
            return 0
        r = max(0, min(1, self.lever.angle() / self.levermax))
        i = int(r * self.num_notches)
        return min(i, self.num_notches - 1)

    def update(self):
        current = self.get_notch()
        out = []

        delta = current - self.last

        if self.cooldown:
            self.cooldown = 0
            return out

        if delta != 0:
            step = 1 if delta > 0 else -1

            self.last += step
            self.cooldown = 1

            out.append(self.next if step > 0 else self.back)

        return out

tbc_axis = LeverOutput(middleLever, middleLeverMAX, 7, "z", "q")
ss_axis = LeverOutput(rightLever, rightLeverMAX, 6, "page down", "page up")

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

while True:
    if Button.CENTER in brick.buttons.pressed():
        sock.send((json.dumps({"type": "END"}) + "\n").encode())
        sock.close()
        break

    buttonsList = handle_buttons(buttons, sequence_index, prev_pressed)

    buttonsList.extend(tbc_axis.update())
    buttonsList.extend(ss_axis.update())

    if not deadman and color.color() == Color.WHITE:
        buttonsList.append("space")
        deadman = True
    elif deadman and color.color() == Color.BLACK:
        buttonsList.append("space")
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