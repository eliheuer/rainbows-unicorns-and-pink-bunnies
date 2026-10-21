# Which keys and gamepad buttons do what.
#
# The gamepad button names are the SDL names (an Xbox pad). On the Steam Deck
# the buttons are printed differently: SDL's X is the Deck's Y, and SDL's Y is
# the Deck's X. So "zap" is on B everywhere, and "grab" takes both X and Y.
import pyxel

KEYS = {
    "left": [pyxel.KEY_LEFT, pyxel.KEY_A, pyxel.GAMEPAD1_BUTTON_DPAD_LEFT],
    "right": [pyxel.KEY_RIGHT, pyxel.KEY_D, pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT],
    "up": [pyxel.KEY_UP, pyxel.KEY_W, pyxel.GAMEPAD1_BUTTON_DPAD_UP],
    "down": [pyxel.KEY_DOWN, pyxel.KEY_S, pyxel.GAMEPAD1_BUTTON_DPAD_DOWN],
    "jump": [pyxel.KEY_Z, pyxel.KEY_SPACE, pyxel.KEY_J, pyxel.GAMEPAD1_BUTTON_A],
    "zap": [pyxel.KEY_X, pyxel.KEY_K, pyxel.GAMEPAD1_BUTTON_B],
    "grab": [pyxel.KEY_C, pyxel.KEY_L, pyxel.GAMEPAD1_BUTTON_X, pyxel.GAMEPAD1_BUTTON_Y],
    "start": [pyxel.KEY_RETURN, pyxel.GAMEPAD1_BUTTON_START],
    "back": [pyxel.KEY_ESCAPE, pyxel.GAMEPAD1_BUTTON_BACK],
}

# The left stick works like the D-pad. It counts as pushed past this point
# (the stick goes from -32768 to 32767).
DEADZONE = 11000
STICK = {
    "left": (pyxel.GAMEPAD1_AXIS_LEFTX, -1),
    "right": (pyxel.GAMEPAD1_AXIS_LEFTX, 1),
    "up": (pyxel.GAMEPAD1_AXIS_LEFTY, -1),
    "down": (pyxel.GAMEPAD1_AXIS_LEFTY, 1),
}
_stick_frames = {name: 0 for name in STICK}   # how many frames each direction has been held
_stick_frame = -1


def _stick_held(name):
    """How many frames the stick has been pushed in this direction (0: not pushed)."""
    global _stick_frame
    if name not in STICK:
        return 0
    if _stick_frame != pyxel.frame_count:
        # once per frame, count up every direction the stick is pushed in
        _stick_frame = pyxel.frame_count
        for n, (axis, sign) in STICK.items():
            pushed = pyxel.btnv(axis) * sign > DEADZONE
            _stick_frames[n] = _stick_frames[n] + 1 if pushed else 0
    return _stick_frames[name]


def held(name):
    return any(pyxel.btn(k) for k in KEYS[name]) or _stick_held(name) > 0


def pressed(name, repeat=False):
    f = _stick_held(name)
    if repeat:
        # the same timing as btnp(k, 12, 4): once, then again every 4 frames after 12
        stick = f == 1 or (f > 12 and (f - 12) % 4 == 0)
        return any(pyxel.btnp(k, 12, 4) for k in KEYS[name]) or stick
    return any(pyxel.btnp(k) for k in KEYS[name]) or f == 1


def ok():
    """The 'yes, go' buttons in menus."""
    return pressed("start") or pressed("jump")
