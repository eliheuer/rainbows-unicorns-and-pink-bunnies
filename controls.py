# Which keys and gamepad buttons do what.
import pyxel

KEYS = {
    "left": [pyxel.KEY_LEFT, pyxel.KEY_A, pyxel.GAMEPAD1_BUTTON_DPAD_LEFT],
    "right": [pyxel.KEY_RIGHT, pyxel.KEY_D, pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT],
    "up": [pyxel.KEY_UP, pyxel.KEY_W, pyxel.GAMEPAD1_BUTTON_DPAD_UP],
    "down": [pyxel.KEY_DOWN, pyxel.KEY_S, pyxel.GAMEPAD1_BUTTON_DPAD_DOWN],
    "jump": [pyxel.KEY_Z, pyxel.KEY_SPACE, pyxel.KEY_J, pyxel.GAMEPAD1_BUTTON_A],
    "zap": [pyxel.KEY_X, pyxel.KEY_K, pyxel.GAMEPAD1_BUTTON_X],
    "grab": [pyxel.KEY_C, pyxel.KEY_L, pyxel.GAMEPAD1_BUTTON_B],
    "start": [pyxel.KEY_RETURN, pyxel.GAMEPAD1_BUTTON_START],
    "back": [pyxel.KEY_ESCAPE, pyxel.GAMEPAD1_BUTTON_BACK],
}


def held(name):
    return any(pyxel.btn(k) for k in KEYS[name])


def pressed(name, repeat=False):
    if repeat:
        return any(pyxel.btnp(k, 12, 4) for k in KEYS[name])
    return any(pyxel.btnp(k) for k in KEYS[name])


def ok():
    """The 'yes, go' buttons in menus."""
    return pressed("start") or pressed("jump")
