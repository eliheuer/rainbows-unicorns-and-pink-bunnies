# All the drawing. Every character is drawn with simple shapes, so you can
# change how something looks by editing the numbers and colors here.
import math

import pyxel

from consts import *


class Pen:
    """Draws shapes inside a small box that can be flipped and scaled.

    Characters are designed facing right. flip=True mirrors them to face left.
    """

    def __init__(self, ox, oy, w, h, flip=False, flipv=False, s=1):
        self.ox, self.oy, self.w, self.h = ox, oy, w, h
        self.flip, self.flipv, self.s = flip, flipv, s

    def _x(self, x, w=1):
        return self.ox + ((self.w - x - w) if self.flip else x) * self.s

    def _y(self, y, h=1):
        return self.oy + ((self.h - y - h) if self.flipv else y) * self.s

    def rect(self, x, y, w, h, c):
        pyxel.rect(self._x(x, w), self._y(y, h), w * self.s, h * self.s, c)

    def pset(self, x, y, c):
        self.rect(x, y, 1, 1, c)

    def elli(self, x, y, w, h, c):
        pyxel.elli(self._x(x, w), self._y(y, h), w * self.s, h * self.s, c)

    def circ(self, x, y, r, c):
        o = (self.s - 1) / 2
        pyxel.circ(self._x(x) + o, self._y(y) + o, r * self.s, c)

    def line(self, x1, y1, x2, y2, c):
        o = (self.s - 1) / 2
        for d in range(self.s):
            pyxel.line(self._x(x1) + d, self._y(y1) + o, self._x(x2) + d, self._y(y2) + o, c)

    def tri(self, x1, y1, x2, y2, x3, y3, c):
        pyxel.tri(self._x(x1), self._y(y1), self._x(x2), self._y(y2),
                  self._x(x3), self._y(y3), c)


# ---------------------------------------------------------------- text

def text(x, y, s, c, shadow=NAVY):
    if shadow is not None:
        pyxel.text(x + 1, y + 1, s, shadow)
    pyxel.text(x, y, s, c)


def center_text(y, s, c, shadow=NAVY, cx=W // 2):
    text(cx - len(s) * 2, y, s, c, shadow)


def big_text(x, y, s, colors, scale=2, shadow=NAVY):
    """Big letters. colors can be one color or a list that cycles per letter."""
    img = pyxel.images[2]
    if isinstance(colors, int):
        colors = [colors]
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        img.rect(0, 0, 4, 6, 0)
        img.text(0, 0, ch, 7)
        lx = x + i * 4 * scale
        dots = [(px, py) for py in range(6) for px in range(4) if img.pget(px, py)]
        if shadow is not None:
            for px, py in dots:
                pyxel.rect(lx + px * scale - 1, y + py * scale - 1, scale + 2, scale + 3, shadow)
        col = colors[i % len(colors)]
        for px, py in dots:
            pyxel.rect(lx + px * scale, y + py * scale, scale, scale, col)


def big_center(y, s, colors, scale=2, shadow=NAVY):
    big_text(W // 2 - len(s) * 2 * scale, y, s, colors, scale, shadow)


# ---------------------------------------------------------------- heroes

def draw_bunny(x, y, facing=1, pose="stand", frame=0, body=PINK, inner=LPINK,
               belly=WHITE, eye=BLACK, cheek=HOTPINK, angry=False, s=1):
    """A bunny in a 12x20 box. (x, y) is the top-left of the box."""
    p = Pen(x, y, 12, 20, flip=facing < 0, s=s)
    dy = 2 if pose == "crouch" else 0
    # ears
    tilt = 1 if pose in ("run", "fast") else 0
    p.elli(2 - tilt, 1 + dy, 3, 8, body)
    p.elli(6 - tilt, 0 + dy, 3, 9, body)
    p.rect(3 - tilt, 2 + dy, 1, 5, inner)
    p.rect(7 - tilt, 1 + dy, 1, 6, inner)
    # body and tail
    p.elli(2, 12 + dy // 2, 8, 7 - dy // 2, body)
    p.elli(4, 13 + dy // 2, 4, 5 - dy // 2, belly)
    p.circ(1, 15, 1, WHITE if body != WHITE else LGRAY)
    # head
    p.elli(1, 6 + dy, 10, 8, body)
    p.rect(7, 8 + dy, 2, 2, eye)
    p.pset(8, 8 + dy, WHITE if eye == BLACK else YELLOW)
    if angry:
        p.line(6, 6 + dy, 9, 7 + dy, BLACK if body != BLACK else RED)
    p.pset(6, 11 + dy, cheek)
    p.pset(10, 10 + dy, RED)
    # arm
    if pose == "zap":
        p.rect(9, 13, 3, 2, body)
    elif pose == "hold":
        p.rect(3, 9, 1, 4, body)
        p.rect(8, 9, 1, 4, body)
    else:
        p.rect(8, 14, 2, 2, body)
    # feet
    if pose in ("run", "fast"):
        if frame % 2 == 0:
            p.rect(1, 17, 3, 2, inner)
            p.rect(8, 18, 3, 2, inner)
        else:
            p.rect(3, 18, 3, 2, inner)
            p.rect(6, 17, 3, 2, inner)
    elif pose == "jump":
        p.rect(1, 17, 3, 2, inner)
        p.rect(8, 16, 3, 2, inner)
    elif pose == "climb":
        p.rect(2, 17 - frame % 2, 3, 2, inner)
        p.rect(7, 16 + frame % 2, 3, 2, inner)
    else:
        p.rect(2, 18, 3, 2, inner)
        p.rect(7, 18, 3, 2, inner)


def draw_unicorn(x, y, facing=1, frame=0, s=1):
    """A unicorn in a 20x16 box with a horn sticking up above it."""
    p = Pen(x, y, 20, 16, flip=facing < 0, s=s)
    step = frame % 2
    # outline first, then fill
    p.elli(1, 4, 17, 10, LAV)
    p.elli(12, 0, 9, 7, LAV)
    p.rect(12, 1, 6, 8, LAV)
    for lx, off in ((4, step), (7, 1 - step), (12, 1 - step), (15, step)):
        p.rect(lx - 1, 10, 4, 6 - off, LAV)
    for lx, off in ((4, step), (7, 1 - step), (12, 1 - step), (15, step)):
        p.rect(lx, 11, 2, 4 - off, WHITE)
        p.rect(lx, 15 - off, 2, 1, LAV)
    p.elli(2, 5, 15, 8, WHITE)
    p.rect(13, 2, 4, 7, WHITE)
    p.elli(13, 1, 7, 5, WHITE)
    p.rect(17, 3, 3, 3, WHITE)
    p.pset(19, 4, LAV)
    p.pset(16, 2, BLACK)
    p.pset(15, 4, LPINK)
    # horn
    p.tri(15, 1, 17, 1, 17, -4, YELLOW)
    p.pset(16, -1, ORANGE)
    # rainbow mane
    for i, c in enumerate(RAINBOW):
        p.rect(12 - i // 2, 1 + i, 2, 1, c)
    # rainbow tail
    for i, c in enumerate(RAINBOW):
        p.line(2, 5 + i, 0, 8 + i + step, c)


def draw_pig(x, y, facing, frame, kind="walk", chomp=0, flipv=False):
    """A pig in a 12x10 box."""
    p = Pen(x, y, 12, 10, flip=facing < 0, flipv=flipv)
    body, snout = (BROWN, PEACH) if kind == "charge" else (PEACH, PINK)
    step = frame % 2
    p.rect(2, 7 + step, 2, 3 - step, snout if kind != "charge" else DBROWN)
    p.rect(7, 8 - step, 2, 2 + step, snout if kind != "charge" else DBROWN)
    p.elli(0, 1, 11, 8, body)
    p.tri(5, 1, 8, 1, 7, -2, snout)
    p.rect(9, 3, 3, 3, snout)
    p.pset(10, 4, DBROWN)
    p.pset(11, 4, DBROWN)
    p.pset(8, 3, BLACK)
    p.pset(0, 3, snout)
    p.pset(-1, 2, snout)
    if kind == "charge":
        p.pset(11, 6, WHITE)
        p.line(2, 1, 6, 1, DBROWN)
        p.pset(7, 2, RED)
    if chomp > 0 and (chomp // 4) % 2 == 0:
        p.rect(9, 6, 3, 1, BLACK)
    if kind == "fly":
        up = (frame // 1) % 2
        p.tri(3, 3, 7, 3, 4, -3 if up else 6, WHITE)


def draw_crow(x, y, facing, frame, flipv=False):
    """A black crow in a 12x10 box."""
    p = Pen(x, y, 12, 10, flip=facing < 0, flipv=flipv)
    up = frame % 2
    p.tri(0, 4, 3, 3, 0, 7, NAVY)                   # tail
    p.elli(1, 3, 9, 6, BLACK)                      # body
    p.circ(9, 3, 2, BLACK)                         # head
    p.tri(10, 2, 13, 4, 10, 4, ORANGE)             # beak
    p.pset(9, 2, RED)                              # eye
    p.pset(4, 8, ORANGE)
    p.pset(6, 8, ORANGE)
    if up:
        p.tri(3, 4, 7, 4, 4, -2, DGRAY)            # wing up
    else:
        p.tri(3, 5, 7, 5, 5, 10, DGRAY)            # wing down


def draw_critter(x, y, facing, frame, kind="walk", chomp=0, flipv=False):
    """Any small enemy: pigs or crows."""
    if kind == "crow":
        draw_crow(x, y, facing, frame, flipv)
    else:
        draw_pig(x, y, facing, frame, kind, chomp, flipv)


def draw_pumpkin(x, y):
    pyxel.elli(x, y + 1, 12, 9, ORANGE)
    pyxel.line(x + 4, y + 2, x + 4, y + 9, BROWN)
    pyxel.line(x + 8, y + 2, x + 8, y + 9, BROWN)
    pyxel.rect(x + 5, y - 1, 2, 3, DGREEN)
    pyxel.pset(x + 3, y + 3, YELLOW)


def draw_turnip(x, y):
    p = Pen(x, y, 8, 8)
    p.line(3, 2, 1, 0, GREEN)
    p.line(4, 2, 4, 0, GREEN)
    p.line(5, 2, 7, 0, GREEN)
    p.elli(1, 2, 6, 6, WHITE)
    p.rect(2, 2, 4, 2, PURPLE)
    p.pset(4, 7, LGRAY)


def draw_tuft(x, y, t=0):
    """Leaves sticking out of the ground. (x, y) is the ground top-left."""
    sway = 1 if (t // 20) % 2 else 0
    pyxel.line(x + 2, y, x + 1 - sway, y - 3, GREEN)
    pyxel.line(x + 4, y, x + 4, y - 4, GREEN)
    pyxel.line(x + 6, y, x + 7 + sway, y - 3, GREEN)
    pyxel.pset(x + 4, y - 4, DGREEN)


def draw_coin(x, y, t):
    w = [6, 4, 2, 4][(t // 5) % 4]
    cx = x + 3
    pyxel.elli(cx - w / 2, y, w, 8, ORANGE)
    if w > 2:
        pyxel.elli(cx - w / 2 + 1, y + 1, w - 2, 6, YELLOW)
    pyxel.pset(cx, y + 2, WHITE)


def draw_carrot(x, y, s=1):
    p = Pen(x, y, 8, 10, s=s)
    p.line(4, 3, 2, 0, GREEN)
    p.line(4, 3, 4, 0, DGREEN)
    p.line(4, 3, 6, 0, GREEN)
    p.tri(1, 3, 7, 3, 4, 10, ORANGE)
    p.pset(3, 5, BROWN)
    p.pset(5, 7, BROWN)


def draw_heart(x, y, c=RED):
    pyxel.circ(x + 2, y + 2, 2, c)
    pyxel.circ(x + 5, y + 2, 2, c)
    pyxel.tri(x, y + 3, x + 7, y + 3, x + 3.5, y + 7, c)
    if c == RED:
        pyxel.pset(x + 1, y + 1, WHITE)


def draw_ball(x, y, t):
    r = 4 + (1 if (t // 6) % 2 else 0)
    pyxel.circ(x + 4, y + 4, r, BLUE)
    pyxel.circ(x + 4, y + 4, r - 1, YELLOW)
    pyxel.line(x + 5, y + 1, x + 3, y + 4, WHITE)
    pyxel.line(x + 3, y + 4, x + 5, y + 4, WHITE)
    pyxel.line(x + 5, y + 4, x + 3, y + 7, WHITE)


def draw_bolt(b, t):
    """A lightning zap."""
    x, y, w, h = b.x, b.y, b.w, b.h
    cy = y + h / 2
    pts = []
    n = 5
    for i in range(n + 1):
        px = x + w * i / n
        py = cy + (((i + t) % 2) * 2 - 1) * (h / 2 - 1) if 0 < i < n else cy
        pts.append((px, py))
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if b.power >= 2:
            pyxel.line(x1, y1 - 1, x2, y2 - 1, BLUE)
            pyxel.line(x1, y1 + 1, x2, y2 + 1, BLUE)
        pyxel.line(x1, y1, x2, y2, YELLOW if t % 4 < 2 else WHITE)
    pyxel.circ(pts[-1][0] if b.vx > 0 else pts[0][0], cy, 2 if b.power >= 2 else 1, WHITE)


def draw_egg(x, y):
    pyxel.elli(x, y, 10, 8, WHITE)
    pyxel.pset(x + 3, y + 2, PINK)
    pyxel.pset(x + 6, y + 5, PINK)
    pyxel.pset(x + 7, y + 2, PINK)


def draw_carrot_bomb(x, y, fuse, t):
    """A big carrot with a burning fuse. Blinks red when it is about to go boom."""
    hot = fuse < 60 and (t // (2 if fuse < 25 else 4)) % 2 == 0
    body = RED if hot else ORANGE
    pyxel.tri(x, y + 2, x + 9, y + 2, x + 4.5, y + 11, body)
    pyxel.rect(x, y + 1, 10, 3, body)
    pyxel.pset(x + 3, y + 5, BROWN)
    pyxel.pset(x + 6, y + 7, BROWN)
    pyxel.line(x + 5, y + 1, x + 7, y - 2, DGRAY)
    spark = [YELLOW, WHITE, ORANGE][t % 3]
    pyxel.pset(x + 7 + (t % 2), y - 3, spark)


def draw_tornado(x, y, w, h, t):
    for i in range(7):
        ww = 4 + i * (w - 4) / 6
        yy = y + h - (i + 1) * h / 7
        sx = math.sin(t * 0.3 + i) * 2
        c = [LGRAY, WHITE, LAV][(i + t // 3) % 3]
        pyxel.elli(x + w / 2 - ww / 2 + sx, yy, ww, h / 7 + 2, c)


def draw_paw(x, y, t):
    pyxel.circ(x + 6, y + 6, 6, GOLD)
    pyxel.circ(x + 6, y + 7, 4, YELLOW)
    for dx in (2, 6, 10):
        pyxel.circ(x + dx, y + 1, 2, YELLOW)
    if t % 6 < 3:
        pyxel.pset(x - 2, y + 2, WHITE)
        pyxel.pset(x + 13, y + 10, WHITE)


def draw_fireball(x, y, t):
    pyxel.circ(x + 4, y + 4, 4, RED)
    pyxel.circ(x + 4, y + 4, 2 + t % 2, ORANGE)
    pyxel.pset(x + 4, y + 4, YELLOW)


# ---------------------------------------------------------------- bosses

def draw_money_cat(x, y, t, wave, facing=1, angry=False):
    """The lucky cat from the gift shop: sitting up, one paw raised and waving,
    holding a big gold coin. 32x34 box with a dark outline."""
    p = Pen(x, y, 32, 34, flip=facing < 0)
    bend = int((math.sin(wave) + 1) * 1.5)      # the waving paw bobs 0-3 pixels
    ink = NAVY

    def blob(fill):
        # every round part of the cat; drawn once bigger in ink as an outline
        o = 1 if fill == ink else 0
        p.elli(6 - o, 15 - o, 22 + 2 * o, 18 + 2 * o, fill)        # body
        p.elli(8 - o, 29 - o, 7 + 2 * o, 5 + 2 * o, fill)          # foot
        p.elli(19 - o, 29 - o, 7 + 2 * o, 5 + 2 * o, fill)         # foot
        p.elli(4 - o, 2 - o, 26 + 2 * o, 17 + 2 * o, fill)         # head

    def arm(fill):
        # the raised, waving arm sticks up beside the head
        o = 1 if fill == ink else 0
        p.rect(0 - o, 2 + bend, 5 + 2 * o, 16 - bend + o, fill)
        p.elli(-3 - o, -5 + bend - o, 9 + 2 * o, 9 + 2 * o, fill)

    p.tri(5, 9, 9, -2, 16, 5, ink)
    p.tri(18, 5, 25, -2, 29, 9, ink)
    blob(ink)
    p.tri(6, 8, 9, 0, 15, 4, WHITE)
    p.tri(19, 4, 25, 0, 28, 8, WHITE)
    blob(WHITE)
    arm(ink)
    arm(WHITE)
    p.tri(8, 6, 9, 2, 12, 4, RED)
    p.tri(22, 4, 25, 2, 26, 6, RED)

    # calico spots
    p.elli(20, 3, 8, 5, ORANGE)
    p.elli(12, 2, 5, 3, BLACK)
    p.elli(8, 21, 6, 5, ORANGE)

    # paw pads on the raised paw
    p.elli(-1, -1 + bend, 5, 3, LPINK)
    p.pset(-1, -3 + bend, PINK)
    p.pset(1, -4 + bend, PINK)
    p.pset(3, -3 + bend, PINK)

    # face
    if angry:
        p.line(10, 8, 13, 10, BLACK)
        p.line(23, 8, 20, 10, BLACK)
        p.rect(11, 10, 2, 2, RED)
        p.rect(21, 10, 2, 2, RED)
    else:
        for ex in (10, 20):     # happy closed eyes: ^ ^
            p.pset(ex, 11, BLACK)
            p.pset(ex + 1, 10, BLACK)
            p.pset(ex + 2, 10, BLACK)
            p.pset(ex + 3, 11, BLACK)
    p.elli(7, 12, 4, 2, LPINK)
    p.elli(23, 12, 4, 2, LPINK)
    p.rect(16, 12, 2, 1, PINK)
    p.pset(15, 14, DGRAY)
    p.pset(16, 15, DGRAY)
    p.pset(17, 15, DGRAY)
    p.pset(18, 14, DGRAY)
    p.line(5, 12, 0, 11, LGRAY)
    p.line(5, 14, 0, 15, LGRAY)
    p.line(28, 12, 31, 11, LGRAY)
    p.line(28, 14, 31, 15, LGRAY)

    # red collar and gold bell
    p.rect(9, 18, 16, 2, RED)
    p.circ(17, 21, 2, GOLD)
    p.pset(16, 20, YELLOW)
    p.pset(17, 22, ORANGE)

    # the big gold coin (a koban) held in the other paw
    p.elli(19, 19, 10, 13, ink)
    p.elli(20, 20, 8, 11, GOLD)
    p.elli(21, 21, 6, 9, YELLOW)
    p.line(24, 22, 24, 28, ORANGE)
    p.line(22, 24, 26, 24, ORANGE)
    p.line(22, 27, 26, 27, ORANGE)
    shine = (t // 6) % 12
    if shine < 3:
        p.pset(22, 21 + shine * 2, WHITE)
    p.elli(16, 24, 6, 5, ink)
    p.elli(17, 25, 4, 3, WHITE)


def draw_eggbert(x, y, facing, t, angry=False, s=2):
    """Pink dinosaur with a bow who spits eggs. 12x16 box, scaled up."""
    p = Pen(x, y, 12, 16, flip=facing < 0, s=s)
    step = (t // 8) % 2
    p.rect(2, 14 + step, 3, 2 - step, RED)
    p.rect(7, 15 - step, 3, 1 + step, RED)
    p.elli(1, 6, 10, 10, PINK)
    p.elli(4, 8, 5, 6, WHITE)
    p.elli(2, 0, 8, 8, PINK)
    p.elli(8, 2, 4, 5, PINK)
    p.circ(10, 4, 1, DBROWN)
    p.rect(5, 2, 2, 3, WHITE)
    p.pset(6, 3, BLACK)
    p.line(5, 1, 7, 1, BLACK)
    # bow
    p.tri(1, 0, 3, 1, 1, 3, RED if not angry else PURPLE)
    p.tri(5, 0, 3, 1, 5, 3, RED if not angry else PURPLE)
    p.pset(3, 1, WHITE)
    p.rect(0, 8, 2, 2, PINK)
    p.pset(9, 11, RED)


def draw_scarecrow(x, y, t, hop, angry=False):
    """A scarecrow bouncing on his pole like a pogo stick. 32x44 box."""
    flap = (t // 10) % 2
    # pole
    pyxel.rect(x + 15, y + 30, 3, 14, DBROWN)
    pyxel.rect(x + 12, y + 41, 9, 3, DBROWN)
    # arms on a stick, with straw hands
    pyxel.rect(x + 1, y + 18, 30, 3, DBROWN)
    for hx in (x - 2, x + 30):
        pyxel.line(hx, y + 17, hx + 3, y + 22 + flap, YELLOW)
        pyxel.line(hx + 1, y + 16, hx + 3, y + 23, GOLD)
        pyxel.line(hx + 3, y + 17, hx, y + 22 - flap, YELLOW)
    # sleeves and plaid shirt
    pyxel.rect(x + 3, y + 16, 26, 6, RED)
    pyxel.rect(x + 9, y + 16, 15, 16, RED)
    for i in range(0, 15, 4):
        pyxel.line(x + 9 + i, y + 16, x + 9 + i, y + 31, DBROWN)
    for j in range(0, 16, 4):
        pyxel.line(x + 9, y + 17 + j, x + 23, y + 17 + j, ORANGE)
    pyxel.rect(x + 15, y + 22, 3, 3, TAN)                 # patch
    # straw sticking out at the waist and neck
    for i in range(6):
        pyxel.line(x + 10 + i * 3, y + 31, x + 9 + i * 3 + (i + flap) % 3, y + 35, YELLOW)
    # burlap sack head
    pyxel.circ(x + 16, y + 9, 8, TAN)
    pyxel.circ(x + 16, y + 9, 7, PALETAN)
    eye = RED if angry else BLACK
    pyxel.rect(x + 12, y + 6, 3, 3, eye)
    pyxel.rect(x + 18, y + 6, 3, 3, eye)
    pyxel.pset(x + 13, y + 7, WHITE if not angry else YELLOW)
    pyxel.pset(x + 19, y + 7, WHITE if not angry else YELLOW)
    # stitched smile
    for i in range(5):
        pyxel.pset(x + 12 + i * 2, y + 12 + (1 if 0 < i < 4 else 0), DBROWN)
        pyxel.pset(x + 12 + i * 2, y + 11 + (1 if 0 < i < 4 else 0), DBROWN)
    # floppy hat
    pyxel.rect(x + 4, y + 2, 24, 3, BROWN)
    pyxel.tri(x + 9, y + 2, x + 23, y + 2, x + 18, y - 9, BROWN)
    pyxel.rect(x + 10, y, 13, 2, RED)
    # a crow friend on his arm
    draw_crow(x + 23, y + 8 - flap, -1, t // 6)


def draw_pink_fireball(x, y, t, angry=False, resting=False):
    """A big pink ball of fire with a face. Centered in a 24x24 box."""
    cx, cy = x + 12, y + 12
    for i in range(5):
        a = t * 0.2 + i * 1.25
        fx = cx + math.cos(a) * 7
        pyxel.tri(fx - 4, cy - 2, fx + 4, cy - 2, fx + math.sin(t * 0.3 + i) * 2, cy - 15 - (t + i * 3) % 5,
                  HOTPINK if i % 2 else PINK)
    pyxel.circ(cx, cy, 11 + (t // 4) % 2, HOTPINK)
    pyxel.circ(cx, cy, 9, PINK)
    pyxel.circ(cx, cy + 1, 6, LPINK)
    pyxel.circ(cx, cy + 2, 3, WHITE)
    if resting:
        pyxel.line(cx - 6, cy - 2, cx - 3, cy - 2, PLUM)
        pyxel.line(cx + 3, cy - 2, cx + 6, cy - 2, PLUM)
    else:
        pyxel.rect(cx - 6, cy - 4, 3, 4, WHITE)
        pyxel.rect(cx + 3, cy - 4, 3, 4, WHITE)
        pyxel.rect(cx - 5, cy - 3, 2, 3, PLUM)
        pyxel.rect(cx + 4, cy - 3, 2, 3, PLUM)
        if angry:
            pyxel.line(cx - 7, cy - 7, cx - 3, cy - 5, PLUM)
            pyxel.line(cx + 7, cy - 7, cx + 3, cy - 5, PLUM)
    pyxel.rect(cx - 2, cy + 3, 5, 2, PLUM)


# The Moon Bunny, from Bunny Madness. 0 = see-through, 7 = white,
# 6 = light blue, c = blue.
MOON_BUNNY = [
    "07000070",
    "0760076c",
    "00777700",
    "07c77c70",
    "77777777",
    "76777767",
    "07777770",
    "07700770",
]
MOON_COLORS = {"7": WHITE, "6": SKY, "c": BLUE}


def draw_moon_bunny(x, y, facing, scale=4):
    for py, row in enumerate(MOON_BUNNY):
        for px, ch in enumerate(row):
            if ch != "0":
                dx = px if facing > 0 else 7 - px
                pyxel.rect(x + dx * scale, y + py * scale, scale, scale, MOON_COLORS[ch])


def draw_cloud(x, y, size=1, c=WHITE):
    pyxel.elli(x, y + 4 * size, 30 * size, 9 * size, c)
    pyxel.circ(x + 9 * size, y + 5 * size, 6 * size, c)
    pyxel.circ(x + 18 * size, y + 4 * size, 7 * size, c)


# ---------------------------------------------------------------- the world

def rainbow_arc(cx, base_y, r, band=2):
    """Draws the top half of a rainbow."""
    for i, c in enumerate(RAINBOW):
        rr = r - i * band
        steps = int(rr * 1.7) + 8
        for k in range(steps + 1):
            a = math.pi * k / steps
            px = cx + math.cos(a) * rr
            py = base_y - math.sin(a) * rr
            pyxel.rect(px - band / 2, py - band / 2, band + 1, band + 1, c)


def draw_background(th, cam_x, t):
    pyxel.cls(th["sky"])
    if th.get("sky2") is not None:
        for i in range(6):
            pyxel.dither(0.15 + i * 0.15)
            pyxel.rect(0, 70 + i * 10, W, 10, th["sky2"])
        pyxel.dither(1.0)
        pyxel.rect(0, 130, W, 30, th["sky2"])

    if th["night"]:
        for i in range(40):
            sx = (i * 73 - cam_x * 0.02) % W
            sy = (i * 41) % 90
            if (t // 15 + i) % 7:
                pyxel.pset(sx, sy, WHITE if i % 3 else YELLOW)
        pyxel.circ(206, 30, 11, CREAM)
        pyxel.circ(201, 27, 10, th["sky"])
    else:
        pyxel.circ(212, 28, 12, YELLOW)
        pyxel.circ(212, 28, 9, CREAM)

    # a big rainbow far away
    rx = 140 - (cam_x * 0.04) % 400
    if rx < -100:
        rx += 400
    for i, c in enumerate(RAINBOW):
        for k in range(3):
            pyxel.circb(rx, 160, 110 - i * 3 - k, c)

    # clouds
    for i in range(6):
        cx = (i * 97 - cam_x * 0.12) % (W + 80) - 40
        cy = 14 + (i * 23) % 40
        draw_cloud(cx, cy, 1, th["cloud"])

    # far hills
    k0 = int(cam_x * 0.25 // 48)
    off = (cam_x * 0.25) % 48
    for i in range(-1, W // 48 + 3):
        k = k0 + i
        r = 26 + (k * 37) % 18
        pyxel.circ(i * 48 - off + 24, 132 - r // 3, r, th["hill2"])
    k0 = int(cam_x * 0.4 // 64)
    off = (cam_x * 0.4) % 64
    for i in range(-1, W // 64 + 3):
        k = k0 + i
        r = 22 + (k * 53) % 16
        pyxel.circ(i * 64 - off + 32, 146 - r // 4, r, th["hill"])

    draw_deco(th, cam_x * 0.55, t)


def draw_deco(th, sx, t):
    kind = th["deco"]
    if kind == "fence":
        off = sx % 16
        for i in range(-1, W // 16 + 2):
            x = i * 16 - off
            pyxel.rect(x, 112, 3, 30, LGRAY)
            pyxel.pset(x + 1, 111, LGRAY)
        pyxel.rect(0, 117, W, 2, LGRAY)
        pyxel.rect(0, 125, W, 2, LGRAY)
    elif kind == "trees":
        off = sx % 56
        k0 = int(sx // 56)
        for i in range(-1, W // 56 + 2):
            x = i * 56 - off
            pyxel.rect(x + 12, 104, 5, 40, TAN)
            pyxel.circ(x + 14, 98, 14, SAGE)
            pyxel.circ(x + 6, 104, 9, SAGE)
            pyxel.circ(x + 23, 104, 9, SAGE)
            for a in range(5):
                pyxel.circ(x + 4 + (a * 7 + k0 + i) % 22, 92 + (a * 5) % 16, 1, RED)
    elif kind == "barn":
        off = sx % 150
        for i in range(-1, W // 150 + 2):
            x = i * 150 - off
            pyxel.rect(x + 20, 92, 56, 50, RED)
            pyxel.tri(x + 16, 94, x + 80, 94, x + 48, 66, DBROWN)
            pyxel.rect(x + 36, 110, 24, 32, WHITE)
            pyxel.rect(x + 38, 112, 20, 30, RED)
            pyxel.line(x + 38, 112, x + 57, 141, WHITE)
            pyxel.line(x + 57, 112, x + 38, 141, WHITE)
            pyxel.rect(x + 43, 80, 10, 8, WHITE)
            pyxel.rect(x + 100, 114, 30, 18, STRAW)
            pyxel.line(x + 100, 120, x + 129, 120, TAN)
    elif kind == "corn":
        off = sx % 7
        for i in range(-1, W // 7 + 2):
            x = i * 7 - off
            h = 34 + ((i + int(sx // 7)) * 13) % 12
            pyxel.line(x, 142, x, 142 - h, SAGE)
            pyxel.line(x, 130 - h // 3, x + 3, 126 - h // 3, MINT)
            pyxel.elli(x - 1, 138 - h, 3, 6, YELLOW)
    elif kind == "pumpkins":
        off = sx % 40
        for i in range(-1, W // 40 + 2):
            x = i * 40 - off
            pyxel.elli(x + 4, 120, 16, 11, PALEORANGE)
            pyxel.line(x + 12, 121, x + 12, 130, TAN)
            pyxel.rect(x + 11, 117, 2, 4, SAGE)
            pyxel.elli(x + 26, 125, 10, 7, PALEORANGE)
    elif kind == "clouds":
        off = sx % 70
        for i in range(-1, W // 70 + 2):
            x = i * 70 - off
            draw_cloud(x, 112, 1, LPINK)
    elif kind == "night":
        off = sx % 16
        for i in range(-1, W // 16 + 2):
            x = i * 16 - off
            pyxel.rect(x, 112, 3, 30, LAV)
        pyxel.rect(0, 117, W, 2, LAV)
        pyxel.rect(0, 125, W, 2, LAV)
        for i in range(12):
            fx = (i * 53 + t * 0.3 - sx * 0.2) % W
            fy = 90 + math.sin(t * 0.05 + i) * 12 + (i * 7) % 20
            if (t // 10 + i) % 4:
                pyxel.pset(fx, fy, YELLOW)
    elif kind == "silo":
        off = sx % 90
        for i in range(-1, W // 90 + 2):
            x = i * 90 - off
            pyxel.rect(x + 10, 70, 28, 72, LAV)
            pyxel.circ(x + 23, 70, 14, LAV)
            pyxel.rect(x + 10, 84, 28, 2, DGRAY)
            pyxel.rect(x + 10, 104, 28, 2, DGRAY)
            pyxel.line(x + 23, 56, x + 23, 44, DGRAY)
            pyxel.tri(x + 24, 44, x + 34, 47, x + 24, 50, ORANGE)


def draw_tiles(grid, th, cam_x, t):
    x0 = max(0, int(cam_x // T))
    x1 = min(len(grid[0]), x0 + W // T + 2)
    for ty in range(ROWS):
        row = grid[ty]
        above = grid[ty - 1] if ty > 0 else None
        for tx in range(x0, x1):
            c = row[tx]
            if c == ".":
                continue
            x, y = tx * T, ty * T
            if c == "#":
                top = above is None or above[tx] != "#"
                pyxel.rect(x, y, T, T, th["dirt"])
                k = (tx * 7 + ty * 13) % 5
                pyxel.pset(x + k + 1, y + (k * 3) % 6 + 1, th["dirt2"])
                pyxel.pset(x + (k + 4) % 7, y + (k * 5) % 7, th["dirt2"])
                # dark edges on open sides, so you can see where the ground ends
                if tx > 0 and row[tx - 1] != "#":
                    pyxel.rect(x, y, 1, T, th["dirt2"])
                if tx + 1 < len(row) and row[tx + 1] != "#":
                    pyxel.rect(x + T - 1, y, 1, T, th["dirt2"])
                if top:
                    edge = th["edge"]
                    pyxel.rect(x, y, T, 4, edge)
                    pyxel.rect(x, y, T, 3, th["grass"])
                    pyxel.pset(x + k, y + 4, edge)
                    pyxel.pset(x + (k + 3) % 8, y + 4, edge)
                    pyxel.pset(x + (k + 5) % 8, y - 1, th["grass"])
                    pyxel.pset(x + (k + 1) % 8, y + 1, edge)
            elif c == "B":
                block = th["block"]
                if block == "hay":
                    pyxel.rect(x, y, T, T, YELLOW)
                    pyxel.line(x, y + 2, x + 7, y + 2, ORANGE)
                    pyxel.line(x, y + 5, x + 7, y + 5, ORANGE)
                    pyxel.rectb(x, y, T, T, GOLD)
                elif block == "candy":
                    pyxel.rect(x, y, T, T, LPINK)
                    pyxel.line(x, y + 7, x + 7, y, WHITE)
                    pyxel.rectb(x, y, T, T, PINK)
                else:
                    pyxel.rect(x, y, T, T, LGRAY)
                    pyxel.line(x, y + 3, x + 7, y + 3, DGRAY)
                    pyxel.line(x + 3 if ty % 2 else x + 6, y, x + 3 if ty % 2 else x + 6, y + 3, DGRAY)
                    pyxel.rectb(x, y, T, T, DGRAY)
            elif c == "=":
                pyxel.elli(x - 1, y, T + 2, 6, WHITE)
                pyxel.rect(x, y + 4, T, 2, LGRAY)
                pyxel.pset(x + 3, y + 1, CREAM)
            elif c == "H":
                sway = 1 if ((ty + t // 15) % 2) else -1
                pyxel.line(x + 4, y, x + 4 + sway, y + 7, DGREEN)
                pyxel.pset(x + 4 - sway * 2, y + 3, GREEN)
                pyxel.pset(x + 4 + sway * 2, y + 6, GREEN)
                pyxel.pset(x + 5 - sway * 2, y + 3, GREEN)


def draw_goal(x, ground_y, t):
    rainbow_arc(x, ground_y, 30, 3)
    draw_unicorn(x - 10, ground_y - 16, -1, (t // 15) % 2)
    if t % 20 < 10:
        pyxel.pset(x - 18, ground_y - 30, WHITE)
        pyxel.pset(x + 16, ground_y - 22, YELLOW)
