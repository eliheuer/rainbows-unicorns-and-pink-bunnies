# Draws the Steam library art for the game from its own pixel art.
#
#   uv run steamdeck/make_art.py <kind> <out.png>
#
# kind is one of: portrait (600x900), landscape (460x216), hero (1920x620),
# icon (256x256). Each one is drawn small and saved 4 times bigger, so it
# keeps the chunky pixels.
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pyxel

import art
from consts import *

SIZES = {"portrait": (150, 225), "landscape": (115, 54), "hero": (480, 155), "icon": (64, 64)}
SCALE = 4


def sky(w, h, ground):
    pyxel.cls(SKY)
    for i in range(6):
        pyxel.dither(0.15 + i * 0.15)
        pyxel.rect(0, ground - 60 + i * 10, w, 10, LAV)
    pyxel.dither(1.0)
    # sun
    pyxel.circ(w - 22, 18, 12, YELLOW)
    pyxel.circ(w - 22, 18, 9, CREAM)
    # clouds
    for i in range(w // 40 + 1):
        art.draw_cloud(i * 44 + (i * 17) % 20, 8 + (i * 31) % 24, 1)
    # hills, then grass
    for i in range(w // 50 + 2):
        pyxel.circ(i * 55 - 10, ground + 14, 32, DGREEN)
    pyxel.rect(0, ground, w, h - ground, BROWN)
    pyxel.rect(0, ground, w, 3, GREEN)
    for i in range(w // 10):
        art.draw_tuft(i * 10 + (i * 7) % 5, ground - 3)


def big_center(cx, y, s, colors, scale):
    """Big letters centered on cx (the game's own helper assumes the 256 wide screen)."""
    art.big_text(cx - len(s) * 2 * scale, y, s, colors, scale)


def title(cx, y, scale):
    big_center(cx, y, "RAINBOWS,", RAINBOW, scale)
    big_center(cx, y + 9 * scale, "UNICORNS &", [WHITE, LPINK], scale)
    big_center(cx, y + 18 * scale, "PINK BUNNIES", [PINK, HOTPINK], scale)


def cast(x, ground, s=2):
    """The bunny, the unicorn, and a carrot, big."""
    art.draw_unicorn(x - 48 * s / 2, ground - 16 * s, 1, 0, s)
    art.draw_bunny(x - 6 * s, ground - 20 * s, 1, "stand", 0, s=s)
    art.draw_carrot(x + 12 * s, ground - 10 * s, s)
    for i in range(3):
        art.draw_pig(x + 20 * s + i * 15, ground - 10, 1, i, "walk")


def draw(kind):
    w, h = SIZES[kind]
    if kind == "portrait":
        ground = 190
        sky(w, h, ground)
        art.rainbow_arc(w // 2, ground, 68, 3)
        title(w // 2, 16, 3)
        cast(w // 2 - 16, ground, 3)
        art.center_text(h - 24, "SAVE THE CARROTS!", CREAM, cx=w // 2)
    elif kind == "landscape":
        ground = 44
        sky(w, h, ground)
        art.rainbow_arc(w - 36, ground, 46, 2)
        cast(w - 62, ground, 1)
        art.big_text(4, 4, "RAINBOWS,", RAINBOW, 1)
        art.big_text(4, 13, "UNICORNS &", [WHITE, LPINK], 1)
        art.big_text(4, 24, "PINK", [PINK, HOTPINK], 2)
        art.big_text(4, 38, "BUNNIES", [PINK, HOTPINK], 2)
    elif kind == "hero":
        ground = 128
        sky(w, h, ground)
        art.rainbow_arc(w // 2, ground, 150, 4)
        cast(w // 2, ground, 4)
        art.draw_pink_mech(60, ground, 1, 0)
        art.draw_carrot_mech(w - 60, ground, 1, 0)
    elif kind == "icon":
        ground = 56
        pyxel.cls(SKY)
        art.rainbow_arc(32, ground, 30, 3)
        pyxel.rect(0, ground, w, h - ground, GREEN)
        art.draw_bunny(14, ground - 40, 1, "stand", 0, s=2)
        art.draw_carrot(40, ground - 20, 2)


def main():
    kind, out = sys.argv[1], sys.argv[2]
    w, h = SIZES[kind]
    pyxel.init(w, h, title="art", fps=30, quit_key=pyxel.KEY_NONE)
    pyxel.colors[:] = PALETTE
    state = {"n": 0}

    def update():
        state["n"] += 1
        if state["n"] == 3:
            pyxel.screen.save(out, SCALE)
            pyxel.quit()

    pyxel.run(update, lambda: draw(kind))


main()
