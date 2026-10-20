# The story scenes: the opening news report and the big ending.
# Each scene is a little movie with words at the bottom.
# Press Enter to go to the next scene. Press Esc to skip them all.
import math
import random

import pyxel

import art
import controls as C
import save
import sounds
from consts import *

SKINS = [PEACH, PALETAN, TAN, BROWN, DBROWN]
SHIRTS = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, SKY, WHITE, HOTPINK]
HAIRS = [BLACK, DBROWN, BROWN, YELLOW, ORANGE, DGRAY]
BUNNY_BOOM = dict(body=WHITE, inner=LPINK, belly=CREAM, eye=RED, cheek=PINK)


# ---------------------------------------------------------------- little drawings

def person(x, y, look, pose="down", t=0, kid=False):
    """A little person standing with their feet at (x, y).
    look is (skin, shirt, hair). pose is down, wave, cheer or hands."""
    skin, shirt, hair = look
    s = 0.7 if kid else 1.0
    legs, body = int(5 * s), int(6 * s)
    top = y - legs - body
    pyxel.rect(x - 2, y - legs, 2, legs, NAVY if not kid else DBROWN)
    pyxel.rect(x + 1, y - legs, 2, legs, NAVY if not kid else DBROWN)
    pyxel.rect(x - 2, top, 5, body, shirt)
    pyxel.circ(x, top - 3, 2 if kid else 3, skin)
    pyxel.rect(x - (2 if kid else 3), top - (5 if kid else 6), 5 if kid else 7, 2, hair)
    sh = top + 1
    if pose == "wave":
        lift = 1 if (t // 8) % 2 else 0
        pyxel.line(x + 3, sh, x + 5 + lift, sh - 5, skin)
        pyxel.line(x - 3, sh, x - 4, sh + 4, skin)
    elif pose == "cheer":
        hop = 1 if (t // 6) % 2 else 0
        pyxel.line(x + 3, sh, x + 5, sh - 5 - hop, skin)
        pyxel.line(x - 3, sh, x - 5, sh - 5 - hop, skin)
    elif pose == "hands":
        pyxel.line(x + 3, sh + 1, x + 6, sh + 3, skin)
        pyxel.line(x - 3, sh + 1, x - 6, sh + 3, skin)
    else:
        pyxel.line(x + 3, sh, x + 3, sh + 4, skin)
        pyxel.line(x - 3, sh, x - 3, sh + 4, skin)


def big_person(x, y, skin, suit, hair, tie, talk=False, t=0, long_hair=False):
    """A newscaster or the President, from the belly up. (x, y) is the top of the head."""
    if long_hair:
        pyxel.rect(x - 12, y + 2, 25, 26, hair)
    pyxel.rect(x - 14, y + 22, 29, 30, suit)
    pyxel.tri(x - 4, y + 22, x + 4, y + 22, x, y + 30, WHITE)
    pyxel.rect(x - 1, y + 24, 3, 12, tie)
    pyxel.rect(x - 3, y + 17, 7, 6, skin)
    pyxel.elli(x - 9, y, 19, 21, skin)
    pyxel.elli(x - 10, y - 2, 21, 9, hair)
    pyxel.rect(x - 10, y + 2, 3, 8, hair)
    pyxel.rect(x + 8, y + 2, 3, 8, hair)
    pyxel.rect(x - 5, y + 9, 2, 3, BLACK)
    pyxel.rect(x + 4, y + 9, 2, 3, BLACK)
    if talk and (t // 6) % 2:
        pyxel.elli(x - 2, y + 14, 5, 4, PLUM)
    else:
        pyxel.line(x - 2, y + 15, x + 2, y + 15, PLUM)


def flag_usa(x, y, t, w=24, h=14):
    for i in range(7):
        wob = math.sin(t * 0.1 + i) * 0.6
        pyxel.rect(x, y + i * 2 + wob, w, 1, RED)
        pyxel.rect(x, y + i * 2 + 1 + wob, w, 1, WHITE)
    pyxel.rect(x, y, w * 0.4, h * 0.55, BLUE)
    for i in range(3):
        for j in range(2):
            pyxel.pset(x + 2 + i * 3, y + 2 + j * 3, WHITE)
    pyxel.line(x - 1, y - 2, x - 1, y + 40, LGRAY)


def tree(x, y, size=1.0, c=GREEN, fruit=None):
    pyxel.rect(x - 1, y - 10 * size, 3, 10 * size, BROWN)
    pyxel.circ(x, y - 13 * size, 7 * size, c)
    pyxel.circ(x - 5 * size, y - 9 * size, 5 * size, c)
    pyxel.circ(x + 5 * size, y - 9 * size, 5 * size, c)
    if fruit is not None:
        for k in range(4):
            pyxel.pset(x - 5 + (k * 7) % 11, y - 15 + (k * 5) % 9, fruit)


def palm(x, y, h=30):
    for i in range(h):
        pyxel.pset(x + math.sin(i * 0.08) * 3, y - i, BROWN)
    tx, ty = x + math.sin(h * 0.08) * 3, y - h
    for a in (-2.6, -2.0, -1.2, -0.5, 0.1):
        pyxel.line(tx, ty, tx + math.cos(a) * 12, ty + math.sin(a) * 5 + 4, GREEN)


def solar(x, y, w=16):
    pyxel.tri(x, y + 6, x + w, y + 6, x + 4, y, NAVY)
    pyxel.tri(x + 4, y, x + w + 4, y, x + w, y + 6, NAVY)
    for i in range(1, 4):
        pyxel.line(x + i * w / 4, y + 6, x + 4 + i * w / 4, y, BLUE)
    pyxel.line(x + 2, y + 3, x + w + 2, y + 3, BLUE)
    pyxel.line(x + w / 2, y + 6, x + w / 2, y + 9, LGRAY)


def turbine(x, y, h, t, speed=0.05):
    pyxel.line(x, y, x, y - h, WHITE)
    pyxel.line(x + 1, y, x + 1, y - h, LGRAY)
    for k in range(3):
        a = t * speed + k * math.tau / 3
        pyxel.line(x, y - h, x + math.cos(a) * h * 0.45, y - h + math.sin(a) * h * 0.45, WHITE)
    pyxel.circ(x, y - h, 1, LGRAY)


def kite(x, y, c, t):
    pyxel.tri(x, y - 5, x - 4, y, x + 4, y, c)
    pyxel.tri(x, y + 6, x - 4, y, x + 4, y, YELLOW)
    for i in range(6):
        pyxel.pset(x + math.sin(t * 0.1 + i) * 2, y + 7 + i * 2, RED)


def heart(x, y, c=RED):
    pyxel.circ(x - 2, y, 2, c)
    pyxel.circ(x + 2, y, 2, c)
    pyxel.tri(x - 4, y + 1, x + 4, y + 1, x, y + 6, c)


def medal(x, y, t):
    pyxel.line(x - 3, y - 7, x, y, RED)
    pyxel.line(x + 3, y - 7, x, y, BLUE)
    pyxel.circ(x, y + 2, 3, GOLD)
    pyxel.circ(x, y + 2, 2, YELLOW)
    if t % 30 < 4:
        pyxel.pset(x - 1, y + 1, WHITE)


def hero_on_unicorn(x, y, t, facing=1, trail=True, s=1):
    """The pink bunny riding the unicorn, with a rainbow behind them."""
    if trail:
        for k in range(36):
            tx = x + (4 if facing > 0 else 16) * s - facing * k * 3
            wob = math.sin(t * 0.15 - k * 0.3) * 2
            for i, c in enumerate(RAINBOW):
                pyxel.rect(tx, y + 6 * s + i + wob, 3, 1, c)
    art.draw_unicorn(x, y, facing, (t // 6) % 2, s=s)
    art.draw_bunny(x + (5 if facing > 0 else 3) * s, y - 13 * s, facing, "jump", t // 4, s=s)


def globe(cx, cy, r, rot):
    pyxel.circ(cx, cy, r + 2, SKY)
    pyxel.circ(cx, cy, r, BLUE)
    lands = [(0.0, 0.5, 0.30), (0.4, 0.2, 0.22), (1.2, 0.6, 0.28), (1.6, -0.2, 0.2),
             (2.5, 0.3, 0.32), (2.9, -0.4, 0.18), (3.7, 0.7, 0.24), (4.2, 0.1, 0.3),
             (4.6, -0.5, 0.2), (5.4, 0.4, 0.26), (5.9, -0.1, 0.18), (3.3, 0.0, 0.15)]
    for lon, lat, size in lands:
        a = lon + rot
        depth = math.cos(a)
        if depth <= 0.05:
            continue
        px = cx + r * math.sin(a) * math.cos(lat)
        py = cy - r * math.sin(lat)
        rr = r * size * (0.35 + 0.65 * depth)
        pyxel.circ(px, py, rr, GREEN)
        pyxel.circ(px - rr * 0.3, py - rr * 0.3, rr * 0.5, MINT)
    pyxel.circb(cx, cy, r, SKY)


def sky(top, bottom, split=60):
    pyxel.cls(top)
    for i in range(6):
        pyxel.dither(0.15 + i * 0.15)
        pyxel.rect(0, split + i * 6, W, 6, bottom)
    pyxel.dither(1.0)
    pyxel.rect(0, split + 36, W, H, bottom)


def stars(t, n=50):
    for i in range(n):
        if (t // 12 + i) % 9:
            pyxel.pset((i * 73) % W, (i * 41) % H, WHITE if i % 3 else YELLOW)


# ---------------------------------------------------------------- the movie player

class Cutscene:
    SCENES = []    # (name, frames or None, music, [(frame, speaker, words), ...])

    def __init__(self, app):
        self.app = app
        self.i = 0
        self.f = 0
        self.t = 0
        self.parts = []
        rnd = random.Random(7)
        self.crowd = [(rnd.choice(SKINS), rnd.choice(SHIRTS), rnd.choice(HAIRS))
                      for _ in range(40)]
        self.start_scene()

    @property
    def scene(self):
        return self.SCENES[self.i]

    def start_scene(self):
        self.f = 0
        self.parts = []
        sounds.music(self.scene[2])

    def update(self):
        self.t += 1
        self.f += 1
        name, frames = self.scene[0], self.scene[1]
        tick = getattr(self, "tick_" + name, None)
        if tick:
            tick(self.f, self.t)
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[6]
            p[4] -= 1
        self.parts = [p for p in self.parts if p[4] > 0]
        if C.pressed("back"):
            self.finish()
        elif (frames and self.f >= frames) or (self.f > 30 and C.ok()):
            if self.i + 1 < len(self.SCENES):
                self.i += 1
                self.start_scene()
            elif self.f > 30:
                self.finish()

    def add(self, x, y, vx, vy, life, col, grav=0.0, kind="dot"):
        self.parts.append([x, y, vx, vy, life, col, grav, kind])

    def draw_parts(self):
        for x, y, vx, vy, life, col, grav, kind in self.parts:
            if kind == "heart":
                heart(x, y, col)
            elif kind == "big":
                pyxel.rect(x, y, 2, 2, col)
            else:
                pyxel.pset(x, y, col)

    def draw(self):
        name, frames, _, lines = self.scene
        getattr(self, "draw_" + name)(self.f, self.t)
        self.draw_parts()
        self.draw_words(lines)
        # fade in and out
        fade = self.f if self.f < 20 else (frames - self.f if frames else 99)
        if fade < 20:
            pyxel.dither(1 - fade / 20)
            pyxel.rect(0, 0, W, H, BLACK)
            pyxel.dither(1.0)

    def draw_words(self, lines):
        now = None
        for start, who, words in lines:
            if self.f >= start:
                now = (start, who, words)
        if not now:
            return
        start, who, words = now
        shown = words[:max(0, (self.f - start) * 2 // 3)]
        rows = wrap(shown, 60)
        box = 9 + 8 * len(wrap(words, 60)) + (9 if who else 0)
        pyxel.dither(0.85)
        pyxel.rect(0, H - box, W, box, NAVY)
        pyxel.dither(1.0)
        y = H - box + 4
        if who:
            art.text(6, y, who, YELLOW)
            y += 9
        for row in rows:
            art.text(6 if who else W // 2 - len(row) * 2, y, row, WHITE)
            y += 8

    def finish(self):
        pass


def wrap(s, n):
    rows, row = [], ""
    for word in s.split(" "):
        if row and len(row) + 1 + len(word) > n:
            rows.append(row)
            row = word
        else:
            row = (row + " " + word).strip()
    if row:
        rows.append(row)
    return rows[:2]


# ---------------------------------------------------------------- the opening

class Intro(Cutscene):
    SCENES = [
        ("news", 600, sounds.MUSIC_BOSS, [
            (10, "NEWS LADY:", "BREAKING NEWS! BREAKING NEWS!"),
            (170, "NEWS LADY:", "CARROT BOOM, THE BAD BUNNY, IS DESTROYING THE WORLD!"),
            (380, "NEWS LADY:", "HE TOOK ALL THE CARROTS, AND HIS PIGS ARE EATING THEM!"),
        ]),
        ("chaos", 420, sounds.MUSIC_BOSS, [
            (20, "CARROT BOOM:", "HA HA HA! ALL THE CARROTS IN THE WORLD ARE MINE!"),
            (240, "CARROT BOOM:", "NOBODY CAN STOP ME! NOBODY!"),
        ]),
        ("phone", 660, sounds.MUSIC_TITLE, [
            (20, "", "MEANWHILE, ON A SUNNY FARM... RING! RING!"),
            (190, "THE PRESIDENT:", "PINK BUNNY! UNICORN! THE WORLD NEEDS YOU!"),
            (370, "THE PRESIDENT:", "ONLY YOU CAN SAVE THE WORLD FROM CARROT BOOM!"),
            (530, "PINK BUNNY:", "DON'T WORRY, MR. PRESIDENT. WE WILL SAVE THE WORLD!"),
        ]),
        ("go", 300, sounds.MUSIC_TITLE, [
            (30, "", "AND SO THE ADVENTURE BEGINS..."),
        ]),
    ]

    def finish(self):
        self.app.save["seen_intro"] = True
        save.write(self.app.save)
        self.app.to_select(self.app.save["unlocked"])

    # 1. The news on TV
    def draw_news(self, f, t):
        pyxel.cls(NAVY)
        for i in range(8):
            pyxel.rect(i * 32, 0, 30, 110, DPURPLE if i % 2 else DUSK)
        # the big screen behind her shows Carrot Boom
        pyxel.rect(140, 14, 104, 64, BLACK)
        pyxel.rect(142, 16, 100, 60, PLUM)
        for i in range(5):
            fx = 150 + i * 20
            fy = 70 - abs(math.sin(t * 0.2 + i)) * 10
            pyxel.tri(fx - 5, 76, fx + 5, 76, fx, fy - 6, ORANGE)
            pyxel.tri(fx - 3, 76, fx + 3, 76, fx, fy, YELLOW)
        art.draw_bunny(178, 26 + abs(math.sin(t * 0.15)) * 4, -1, "hold", t // 4, angry=True,
                       **BUNNY_BOOM, s=2)
        art.text(146, 18, "LIVE", RED)
        # the news lady at her desk
        talking = any(start <= f < start + len(words) * 3 // 2
                      for start, _, words in self.scene[3])
        big_person(70, 40, TAN, PLUM, DBROWN, HOTPINK, talking, t, long_hair=True)
        pyxel.rect(20, 86, 120, 30, LGRAY)
        pyxel.rect(20, 86, 120, 3, WHITE)
        pyxel.line(80, 70, 80, 86, DGRAY)
        pyxel.circ(80, 69, 2, DGRAY)
        # the red BREAKING NEWS bar and the words that slide by
        pyxel.rect(0, 116, W, 12, RED)
        art.text(4, 119, "BREAKING NEWS", WHITE if (t // 20) % 2 else YELLOW)
        pyxel.rect(60, 116, W - 60, 12, WHITE)
        msg = "CARROT BOOM TAKES ALL THE CARROTS!  PIGS EVERYWHERE!  STAY INSIDE!  "
        x = 256 - (t * 0.8) % (len(msg) * 4 + 200)
        pyxel.clip(60, 116, W - 60, 12)
        pyxel.text(x, 119, msg, NAVY)
        pyxel.clip()
        pyxel.rect(0, 128, W, 32, BLACK)

    # 2. Carrot Boom on a hill, with carrot bombs going off
    def tick_chaos(self, f, t):
        if f % 25 == 0:
            x, y = random.uniform(10, 246), random.uniform(80, 120)
            for _ in range(14):
                a = random.uniform(0, math.tau)
                v = random.uniform(0.5, 2)
                self.add(x, y, math.cos(a) * v, math.sin(a) * v, 30,
                         random.choice([ORANGE, YELLOW, RED]), 0.03, "big")
            sounds.sfx(sounds.BOOM)

    def draw_chaos(self, f, t):
        sky(PLUM, RED, 40)
        pyxel.circ(200, 40, 16, ORANGE)
        for i in range(7):
            x = i * 40 + 10
            h = 30 + (i * 17) % 25
            pyxel.rect(x, 128 - h, 26, h, DPURPLE)
            for k in range(3):
                pyxel.rect(x + 4 + k * 7, 128 - h + 6, 3, 4, ORANGE if (i + k + t // 30) % 3 else BLACK)
        pyxel.rect(0, 128, W, 32, DBROWN)
        pyxel.elli(70, 92, 120, 60, DGRAY)
        laugh = abs(math.sin(t * 0.3)) * 3
        art.draw_bunny(118, 52 - laugh, 1, "hold", t // 4, angry=True, **BUNNY_BOOM, s=2)
        pyxel.elli(100, 58, 18, 18, BROWN)
        art.draw_carrot(104, 52)
        for i in range(4):
            px = (f * 1.2 + i * 70) % (W + 40) - 20
            art.draw_pig(px, 118, 1, t // 6 + i, "walk")
            art.draw_carrot(px + 10, 112)
        if (t // 10) % 2:
            art.text(150, 50, "HA HA HA!", ORANGE)

    # 3. The President calls the pink bunny
    def draw_phone(self, f, t):
        pyxel.cls(NAVY)
        # left: the office of the President
        pyxel.clip(0, 0, 127, 135)
        pyxel.rect(0, 0, 127, 135, CREAM)
        pyxel.rect(0, 0, 127, 30, PALETAN)
        pyxel.rect(84, 20, 30, 40, SKY)
        pyxel.rectb(84, 20, 30, 40, WHITE)
        pyxel.line(99, 20, 99, 59, WHITE)
        flag_usa(14, 26, t)
        talk = 190 <= f < 530
        big_person(62, 44, PEACH, NAVY, LGRAY, RED, talk, t)
        pyxel.rect(10, 100, 107, 35, BROWN)
        pyxel.rect(10, 100, 107, 3, DBROWN)
        pyxel.rect(30, 94, 14, 6, RED)
        pyxel.line(37, 94, 50, 84, BLACK)
        art.text(36, 122, "THE PRESIDENT", WHITE)
        pyxel.clip()
        # right: the farm, with the pink bunny and the unicorn
        pyxel.clip(129, 0, 127, 135)
        pyxel.rect(129, 0, 127, 135, SKY)
        pyxel.circ(230, 20, 9, YELLOW)
        pyxel.circ(180, 150, 70, MINT)
        pyxel.rect(129, 112, 127, 23, GREEN)
        art.draw_unicorn(200, 96, -1, (t // 20) % 2)
        ring = f < 190
        art.draw_bunny(160, 92 - (abs(math.sin(t * 0.4)) * 3 if ring else 0), 1,
                       "zap" if not ring else "jump", t // 4)
        pyxel.rect(170, 98, 3, 6, RED)
        if ring and (t // 8) % 2:
            art.text(150, 70, "RING! RING!", RED)
        pyxel.clip()
        pyxel.line(128, 0, 128, 135, WHITE)
        # a phone line between them
        for k in range(6):
            x = 50 + k * 22 + (t * 2) % 22
            pyxel.pset(x, 84 - math.sin(k + t * 0.1) * 4, YELLOW)

    # 4. Off they go!
    def draw_go(self, f, t):
        sky(SKY, PEACH, 70)
        pyxel.circ(128, 120, 30, YELLOW)
        pyxel.rect(0, 120, W, 40, GREEN)
        art.rainbow_arc(W // 2, 130, 90, 4)
        x = -40 + f * 1.3
        hero_on_unicorn(x, 80 - f * 0.12, t)
        if f > 60:
            art.big_center(24, "LET'S GO!", [PINK, HOTPINK, YELLOW], 3)


# ---------------------------------------------------------------- the ending

class Ending(Cutscene):
    SCENES = [
        ("sorry", 600, sounds.MUSIC_ENDING, [
            (20, "", "CARROT BOOM SAT DOWN AND CRIED."),
            (180, "CARROT BOOM:", "I WAS NOT REALLY BAD. I WAS JUST SO, SO HUNGRY..."),
            (380, "", "SO THE PINK BUNNY SHARED A CARROT WITH HIM."),
        ]),
        ("fly", 420, sounds.MUSIC_ENDING, [
            (30, "", "THEN THE PINK BUNNY AND THE UNICORN FLEW ALL AROUND THE WORLD,"),
            (220, "", "TO SEE HOW EVERYONE WAS DOING NOW THAT CARROT BOOM WAS GOOD."),
        ]),
        ("france", 420, sounds.MUSIC_ENDING, [
            (40, "PARIS, FRANCE", "EVERY ROOF HAD A GARDEN, AND EVERYONE RODE BIKES."),
        ]),
        ("china", 420, sounds.MUSIC_ENDING, [
            (40, "CHINA", "KIDS FLEW KITES OVER THE GREAT WALL. THE SUN MADE CLEAN POWER."),
        ]),
        ("russia", 420, sounds.MUSIC_ENDING, [
            (40, "RUSSIA", "THE WIND TURNED BIG WHEELS, AND KEPT EVERY HOME WARM."),
        ]),
        ("brazil", 420, sounds.MUSIC_ENDING, [
            (40, "BRAZIL", "PEOPLE PLANTED THE RAINFOREST BACK, ONE TREE AT A TIME."),
        ]),
        ("israel", 420, sounds.MUSIC_ENDING, [
            (40, "JERUSALEM, ISRAEL", "NEIGHBORS SAT AT ONE LONG TABLE AND SHARED THEIR FOOD."),
        ]),
        ("dubai", 420, sounds.MUSIC_ENDING, [
            (40, "DUBAI", "GARDENS GREW IN THE DESERT, AND THE TALL TOWERS MADE SUN POWER."),
        ]),
        ("tv", 480, sounds.MUSIC_ENDING, [
            (30, "", "SOON THE PINK BUNNY WAS ON TV, ALL OVER THE WORLD."),
            (250, "NEWS LADY:", "GOOD NEWS! THE PINK BUNNY SAVED THE WORLD!"),
        ]),
        ("medal", 660, sounds.MUSIC_ENDING, [
            (30, "", "THE PRESIDENT HAD A BIG PARTY AT THE WHITE HOUSE."),
            (230, "THE PRESIDENT:", "PINK BUNNY, THIS MEDAL IS FOR YOU..."),
            (420, "THE PRESIDENT:", "...FOR FIXING THE WORLD! THANK YOU!"),
        ]),
        ("hands", 720, sounds.MUSIC_ENDING, [
            (40, "", "AND ALL AROUND THE WORLD, CHILDREN HELD HANDS..."),
            (330, "", "...AND SAID: THANK YOU, PINK BUNNY!"),
        ]),
        ("finale", None, sounds.MUSIC_ENDING, []),
    ]

    def finish(self):
        self.app.to_title()

    def flyby(self, f, t, y=26, start=60):
        if f > start:
            hero_on_unicorn(-40 + (f - start) * 1.1, y + math.sin(f * 0.05) * 4, t)

    def place_title(self, f, name):
        if 20 < f < 400:
            art.big_center(8, name, WHITE, 2)

    def tick_place(self, f, t):
        # hearts float up from the happy people when the bunny flies by
        if 120 < f < 380 and f % 9 == 0:
            self.add(random.uniform(20, 236), 120, random.uniform(-0.2, 0.2), -0.6, 90,
                     random.choice([RED, PINK, HOTPINK]), 0, "heart")

    tick_france = tick_china = tick_russia = tick_brazil = tick_israel = tick_dubai = tick_place

    def people(self, f, t, xs, y, poses=None, kid=False):
        for i, x in enumerate(xs):
            pose = (poses[i % len(poses)] if poses else "down")
            if 90 < f < 360:
                pose = "wave" if i % 2 else "cheer"
            person(x, y, self.crowd[(i * 7 + len(xs)) % len(self.crowd)], pose, t + i * 5, kid)

    # 1. Carrot Boom says sorry
    def tick_sorry(self, f, t):
        if 120 < f < 380 and f % 14 == 0:
            for side in (-1, 1):
                self.add(150 + side * 5, 92, side * 0.5, -0.6, 30, SKY, 0.06)
        if f > 440 and f % 15 == 0:
            self.add(random.uniform(110, 170), 80, 0, -0.5, 90, PINK, 0, "heart")

    def draw_sorry(self, f, t):
        sky(DPURPLE, PEACH, 50)
        pyxel.circ(60, 110, 26, YELLOW)
        pyxel.rect(0, 120, W, 40, DGRAY)
        pyxel.rect(0, 120, W, 2, LGRAY)
        art.draw_bunny(138, 80, -1, "crouch", 0, **BUNNY_BOOM, s=2)
        walk = min(f, 300)
        bx = -20 + walk * 0.45
        moving = f < 300
        art.draw_bunny(bx, 100, 1, "run" if moving else ("hold" if f > 380 else "stand"),
                       t // 5)
        if f > 380:
            art.draw_carrot(bx + 14, 96)
        if f > 460:
            art.text(132, 64, "THANK YOU!", WHITE)

    # 2. They fly up into the sky
    def draw_fly(self, f, t):
        sky(SKY, PEACH, 80)
        for i in range(5):
            art.draw_cloud((i * 70 - f * 0.4) % (W + 60) - 40, 20 + (i * 23) % 50, 1, WHITE)
        globe(128, 230, 120, f * 0.004)
        hero_on_unicorn(40 + f * 0.25, 110 - f * 0.18, t)

    # 3-8. A trip around the world
    def draw_france(self, f, t):
        sky(SKY, LPINK, 60)
        pyxel.circ(40, 30, 10, YELLOW)
        # the Eiffel Tower, with vines and flowers on it
        x, y = 170, 128
        pyxel.tri(x - 30, y, x - 4, y - 70, x - 18, y, BROWN)
        pyxel.tri(x + 30, y, x + 4, y - 70, x + 18, y, BROWN)
        pyxel.tri(x - 6, y - 70, x + 6, y - 70, x, y - 110, BROWN)
        pyxel.rect(x - 22, y - 40, 44, 4, BROWN)
        pyxel.rect(x - 12, y - 72, 24, 3, BROWN)
        pyxel.elli(x - 14, y - 22, 28, 22, SKY)
        for k in range(14):
            pyxel.circ(x - 26 + (k * 37) % 52, y - 4 - (k * 23) % 90 * 0.8, 2,
                       [GREEN, PINK, YELLOW][k % 3])
        # houses with gardens on the roofs and sun panels
        for i in range(4):
            hx = 6 + i * 36 if i < 3 else 215
            pyxel.rect(hx, 92, 30, 36, CREAM)
            pyxel.rect(hx, 88, 30, 5, GREEN)
            for k in range(4):
                pyxel.circ(hx + 4 + k * 7, 87, 3, [GREEN, MINT][k % 2])
                pyxel.pset(hx + 4 + k * 7, 85, [PINK, RED, YELLOW][k % 3])
            for k in range(2):
                pyxel.rect(hx + 5 + k * 13, 100, 6, 8, SKY)
            solar(hx + 6, 76, 12)
        pyxel.rect(0, 128, W, 32, LGRAY)
        pyxel.rect(0, 128, W, 2, GREEN)
        # bikes
        for i in range(2):
            bx = (f * 0.8 + i * 130) % (W + 40) - 20
            pyxel.circb(bx, 123, 4, BLACK)
            pyxel.circb(bx + 12, 123, 4, BLACK)
            pyxel.line(bx, 123, bx + 6, 117, RED)
            pyxel.line(bx + 6, 117, bx + 12, 123, RED)
            person(bx + 6, 119, self.crowd[i + 3], "down", t)
        self.people(f, t, [40, 70, 100, 210, 236], 127)
        self.flyby(f, t)
        self.place_title(f, "FRANCE")

    def draw_china(self, f, t):
        sky(SKY, CREAM, 60)
        for i in range(5):
            pyxel.circ(i * 70 + 10, 140, 60 - (i % 2) * 15, SAGE if i % 2 else MINT)
        # the Great Wall on the mountains
        pts = [(0, 96), (40, 78), (80, 92), (120, 70), (160, 86), (200, 66), (256, 84)]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for k in range(0, x2 - x1, 2):
                yy = y1 + (y2 - y1) * k / (x2 - x1)
                pyxel.rect(x1 + k, yy, 2, 8, TAN)
                if (k // 2) % 2:
                    pyxel.rect(x1 + k, yy - 2, 2, 2, TAN)
        for x, y in pts[1:-1]:
            pyxel.rect(x - 5, y - 10, 10, 16, PALETAN)
            pyxel.rect(x - 2, y - 6, 4, 5, DBROWN)
        for i in range(5):
            solar(14 + i * 22, 112, 14)
        pyxel.rect(0, 128, W, 32, GREEN)
        for i, c in enumerate([RED, YELLOW, PINK]):
            kite(150 + i * 32, 46 + math.sin(t * 0.05 + i) * 6, c, t)
        self.people(f, t, [150, 180, 214, 240], 126, kid=True)
        self.people(f, t, [128], 126)
        self.flyby(f, t, 20)
        self.place_title(f, "CHINA")

    def draw_russia(self, f, t):
        sky(SKY, WHITE, 60)
        # onion domes, like the colorful church in Moscow
        domes = [(70, 60, RED, GREEN), (100, 44, YELLOW, BLUE), (130, 56, GREEN, RED),
                 (160, 64, BLUE, YELLOW)]
        for x, top, body, dome in domes:
            pyxel.rect(x - 9, top, 18, 128 - top, body)
            for k in range(3):
                pyxel.rect(x - 9, top + 10 + k * 14, 18, 2, WHITE)
            pyxel.elli(x - 11, top - 16, 22, 18, dome)
            for k in range(3):
                pyxel.line(x - 8 + k * 8, top - 14, x - 4 + k * 4, top, WHITE)
            pyxel.tri(x - 3, top - 15, x + 3, top - 15, x, top - 26, YELLOW)
        for i in range(4):
            turbine(206 + (i % 2) * 26, 128 - (i // 2) * 30, 40 - (i // 2) * 12, t + i * 20)
        pyxel.rect(0, 128, W, 32, WHITE)
        pyxel.rect(0, 128, W, 2, LGRAY)
        # a snowman, and snow falling
        pyxel.circ(30, 122, 7, WHITE)
        pyxel.circ(30, 110, 5, WHITE)
        pyxel.pset(32, 109, ORANGE)
        pyxel.pset(29, 108, BLACK)
        for i in range(40):
            pyxel.pset((i * 53 + t * 0.2) % W, (i * 31 + t * 0.6) % H, WHITE)
        self.people(f, t, [50, 190, 236], 126)
        self.people(f, t, [70, 90, 110], 126, kid=True)
        self.flyby(f, t)
        self.place_title(f, "RUSSIA")

    def draw_brazil(self, f, t):
        sky(SKY, PEACH, 60)
        pyxel.circ(210, 40, 12, YELLOW)
        # Sugarloaf mountain by the sea
        pyxel.elli(140, 50, 50, 90, SAGE)
        pyxel.elli(180, 72, 40, 70, SAGE)
        pyxel.line(150, 52, 196, 74, DGRAY)
        pyxel.rect(171, 61, 5, 4, RED)
        pyxel.rect(110, 104, 146, 16, BLUE)
        for i in range(8):
            pyxel.line(120 + i * 18 + (t // 10) % 6, 108 + (i % 3) * 4, 128 + i * 18 + (t // 10) % 6,
                       108 + (i % 3) * 4, SKY)
        pyxel.rect(0, 118, W, 42, STRAW)
        # the rainforest growing back
        for i in range(6):
            tree(10 + i * 18, 128, 1.2 - (i % 2) * 0.2, GREEN if i % 2 else DGREEN)
        palm(118, 128, 34)
        palm(240, 128, 28)
        for i in range(3):
            x = 30 + i * 30
            grow = min(1.0, max(0.2, (f - 60 - i * 40) / 160))
            tree(x, 126, 0.6 * grow, MINT)
            person(x + 8, 126, self.crowd[i + 10], "down", t)
        # parrots
        for i in range(3):
            px = (t * 1.0 + i * 90) % (W + 20) - 10
            py = 60 + math.sin(t * 0.1 + i) * 6 + i * 10
            pyxel.rect(px, py, 4, 3, [RED, GREEN, BLUE][i])
            pyxel.pset(px + 4, py, YELLOW)
        self.people(f, t, [150, 175, 200, 225], 126)
        self.flyby(f, t)
        self.place_title(f, "BRAZIL")

    def draw_israel(self, f, t):
        sky(SKY, CREAM, 60)
        pyxel.circ(40, 30, 10, YELLOW)
        # the old stone walls of Jerusalem
        pyxel.rect(0, 70, W, 46, PALETAN)
        for k in range(0, W, 8):
            pyxel.rect(k, 64, 5, 6, PALETAN)
        for r in range(5):
            for k in range(0, W, 16):
                pyxel.rect(k + (r % 2) * 8, 74 + r * 8, 15, 1, TAN)
        pyxel.rect(110, 82, 36, 34, DBROWN)
        pyxel.circ(128, 82, 18, DBROWN)
        pyxel.rect(116, 86, 24, 30, BROWN)
        pyxel.circ(128, 86, 12, BROWN)
        pyxel.rect(40, 50, 22, 66, PALETAN)
        pyxel.rect(200, 54, 22, 62, PALETAN)
        for x in (40, 200):
            for k in range(0, 22, 6):
                pyxel.rect(x + k, 46 if x == 40 else 50, 4, 4, PALETAN)
        pyxel.rect(0, 116, W, 44, STRAW)
        # olive trees
        for x in (20, 236):
            tree(x, 128, 1.0, SAGE, DGREEN)
        # one long table full of food, and neighbors sharing it
        self.people(f, t, [48, 72, 96, 120, 144, 168, 192, 212], 124)
        pyxel.rect(36, 114, 184, 6, BROWN)
        pyxel.rect(36, 114, 184, 2, WHITE)
        for k in range(10):
            fx = 44 + k * 18
            pyxel.circ(fx, 112, 3, [ORANGE, RED, YELLOW, GREEN, PEACH][k % 5])
        pyxel.rect(42, 120, 2, 8, DBROWN)
        pyxel.rect(212, 120, 2, 8, DBROWN)
        self.flyby(f, t)
        self.place_title(f, "ISRAEL")

    def draw_dubai(self, f, t):
        sky(SKY, PEACH, 60)
        pyxel.circ(60, 36, 12, YELLOW)
        # the very tall tower, with gardens growing up the side
        x = 150
        for k, (w, h) in enumerate([(20, 40), (14, 40), (9, 30), (5, 20), (2, 16)]):
            y = 128 - sum(hh for _, hh in [(20, 40), (14, 40), (9, 30), (5, 20), (2, 16)][:k + 1])
            pyxel.rect(x - w / 2, y, w, h, LGRAY)
            pyxel.rect(x - w / 2 + 1, y, max(1, w / 2 - 2), h, SKY)
            if k < 3:
                for j in range(3):
                    pyxel.circ(x - w / 2 + (j * 7) % w, y + 4 + j * 10, 2, GREEN)
        for i, (tx, th) in enumerate([(100, 50), (200, 60), (226, 40)]):
            pyxel.rect(tx, 128 - th, 16, th, LGRAY)
            pyxel.rect(tx + 2, 128 - th, 5, th, SKY)
            solar(tx - 2, 128 - th - 9, 14)
        # sand dunes with gardens growing on them
        pyxel.elli(-40, 110, 160, 50, STRAW)
        pyxel.rect(0, 128, W, 32, STRAW)
        for i in range(7):
            gx = 10 + i * 13
            grow = min(1.0, max(0.1, (f - 40 - i * 20) / 120))
            pyxel.circ(gx, 128 - 4 * grow, 4 * grow, GREEN)
            if grow >= 1:
                pyxel.pset(gx, 122, PINK)
        palm(96, 140, 26)
        palm(250, 140, 30)
        self.people(f, t, [30, 60, 180, 214, 236], 126)
        self.flyby(f, t)
        self.place_title(f, "DUBAI")

    # 9. On TV
    def draw_tv(self, f, t):
        pyxel.cls(PALETAN)
        pyxel.rect(0, 0, W, 20, CREAM)
        pyxel.rect(0, 110, W, 50, TAN)
        # the TV
        pyxel.rect(50, 14, 156, 92, BLACK)
        pyxel.rect(56, 18, 144, 80, SKY)
        pyxel.circ(128, 120, 50, GREEN)
        pyxel.clip(56, 18, 144, 80)
        art.rainbow_arc(128, 98, 60, 3)
        hop = abs(math.sin(t * 0.12)) * 6
        art.draw_bunny(116, 50 - hop, 1, "zap" if (t // 30) % 2 else "jump", t // 4, s=2)
        medal(128, 76 - hop, t)
        pyxel.rect(56, 84, 144, 14, RED)
        msg = "GOOD NEWS!  PINK BUNNY SAVES THE WORLD!  CARROT BOOM SAYS SORRY!  "
        x = 200 - (t * 0.8) % (len(msg) * 4 + 160)
        pyxel.text(x, 88, msg, WHITE)
        pyxel.clip()
        pyxel.rect(110, 106, 36, 6, DGRAY)
        # a family on a couch, watching and cheering
        pyxel.rect(30, 128, 196, 22, PLUM)
        pyxel.rect(24, 120, 12, 30, PLUM)
        pyxel.rect(220, 120, 12, 30, PLUM)
        for i, x in enumerate([60, 96, 130, 160, 196]):
            look = self.crowd[i + 20]
            up = f > 250 and (t // 8 + i) % 2
            pyxel.circ(x, 126 - up * 2, 6 if i not in (2, 3) else 4, look[2])
            pyxel.rect(x - 6, 132 - up * 2, 12, 14, look[1])
            if f > 250:
                pyxel.line(x - 6, 132, x - 10, 120 - up * 3, look[0])
                pyxel.line(x + 6, 132, x + 10, 120 - up * 3, look[0])

    # 10. A medal from the President
    def tick_medal(self, f, t):
        if f > 420 and f % 2 == 0:
            self.add(random.uniform(0, W), -4, random.uniform(-0.3, 0.3), random.uniform(0.6, 1.2),
                     200, random.choice(RAINBOW + [WHITE, PINK]), 0, "big")

    def draw_medal(self, f, t):
        sky(SKY, CREAM, 70)
        # the White House
        pyxel.rect(40, 50, 176, 62, WHITE)
        pyxel.rect(40, 50, 176, 4, LGRAY)
        pyxel.tri(98, 50, 158, 50, 128, 30, WHITE)
        pyxel.trib(98, 50, 158, 50, 128, 30, LGRAY)
        for k in range(6):
            pyxel.rect(102 + k * 10, 56, 4, 50, CREAM)
        for k in range(4):
            for side in (50, 170):
                pyxel.rect(side + k * 10, 62, 5, 8, SKY)
                pyxel.rect(side + k * 10, 82, 5, 8, SKY)
        flag_usa(122, 14, t, 16, 10)
        pyxel.rect(0, 100, W, 60, GREEN)
        # the stage
        pyxel.rect(70, 98, 116, 8, RED)
        pyxel.rect(70, 98, 116, 2, WHITE)
        pyxel.rect(70, 104, 116, 2, BLUE)
        # the President walks up and gives the medal
        px = max(140, 210 - f * 0.4)
        person(px, 98, (PEACH, NAVY, LGRAY), "down" if px > 140 else "hands", t)
        pyxel.line(px, 86, px, 90, RED)
        art.draw_bunny(114, 78, 1, "stand" if f < 420 else "jump", t // 4)
        if f > 400:
            medal(120, 94, t)
        elif f > 260:
            medal(px - 7, 92, t)
        # the crowd
        for i in range(14):
            pose = "cheer" if f > 420 or (t // 40 + i) % 3 == 0 else "wave"
            x = 10 + i * 18
            person(x, 122 + (i % 2) * 6, self.crowd[i], pose, t + i * 7)
        # camera flashes
        if f > 420 and (t // 9) % 5 == 0:
            pyxel.circ(30 + (t * 37) % 200, 130, 4, WHITE)

    # 11. Children all around the world hold hands
    def tick_hands(self, f, t):
        if f % 10 == 0:
            self.add(random.uniform(20, 236), 60, 0, -0.4, 120,
                     random.choice([RED, PINK, HOTPINK]), 0, "heart")

    def draw_hands(self, f, t):
        pyxel.cls(NAVY)
        stars(t)
        cx, cy, r = 128, 260, 170
        globe(cx, cy, r, t * 0.004)
        kids = 17
        spots = []
        for i in range(kids):
            a = (i - kids // 2) * 0.075 + math.sin(t * 0.02) * 0.02
            x = cx + math.sin(a) * r
            y = cy - math.cos(a) * r
            spots.append((x, y))
        for (x1, y1), (x2, y2) in zip(spots, spots[1:]):
            pyxel.line(x1 + 6, y1 - 7, x2 - 6, y2 - 7, PEACH)
        for i, (x, y) in enumerate(spots):
            if i == kids // 2:
                art.draw_bunny(x - 6, y - 20 - abs(math.sin(t * 0.1)) * 3, 1, "jump", t // 4)
                medal(x, y - 6, t)
            else:
                sway = math.sin(t * 0.08 + i) * 1
                person(x, y + sway, self.crowd[i], "hands", t, kid=True)
        if f > 330:
            art.big_center(26, "THANK YOU,", [WHITE, LPINK], 2)
            art.big_center(44, "PINK BUNNY!", [PINK, HOTPINK], 3)

    # 12. The end
    def tick_finale(self, f, t):
        if f % 35 == 0:
            x, y = random.uniform(30, 226), random.uniform(20, 70)
            c = random.choice([RED, YELLOW, PINK, SKY, GREEN, PURPLE, WHITE])
            for k in range(24):
                a = k * math.tau / 24
                self.add(x, y, math.cos(a) * 1.4, math.sin(a) * 1.4, 45, c, 0.02, "big")
            sounds.sfx(sounds.POOF)

    def draw_finale(self, f, t):
        pyxel.cls(NAVY)
        stars(t)
        art.rainbow_arc(W // 2, 150, 120, 5)
        pyxel.rect(0, 136, W, 24, GREEN)
        pyxel.rect(0, 136, W, 2, MINT)
        # everyone is friends now
        art.draw_money_cat(10, 100, t, (t // 10) % 2)
        art.draw_pink_fireball(52, 100 + math.sin(t * 0.08) * 4, t)
        art.draw_unicorn(80, 120, 1, (t // 10) % 2)
        hop = abs(math.sin(t * 0.1)) * 8
        art.draw_bunny(116, 98 - hop, 1, "jump" if hop > 2 else "stand", t // 4, s=2)
        medal(128, 126 - hop, t)
        art.draw_bunny(150, 96, -1, "stand", 0, **BUNNY_BOOM, s=2)
        art.draw_carrot(146, 116)
        art.draw_moon_bunny(177, 102, -1)
        art.draw_scarecrow(214, 96, t, 0)
        art.big_center(18, "THE END", RAINBOW, 4)
        art.center_text(50, "THANK YOU FOR PLAYING!", WHITE)
        if f > 120 and t % 40 < 28:
            art.center_text(64, "PRESS ENTER", YELLOW)
