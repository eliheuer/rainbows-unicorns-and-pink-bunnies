# Rainbows, Unicorns, and Pink Bunnies
#
# Run it with:   uv run main.py

import pyxel

import art
import controls as C
import levels
import save
import sounds
from consts import *
from game import Play
from story import Ending, Intro

TITLE = "Rainbows, Unicorns, and Pink Bunnies"


class Title:
    def __init__(self, app):
        self.app = app
        self.t = 0
        sounds.music(sounds.MUSIC_TITLE)

    def update(self):
        self.t += 1
        if C.ok():
            sounds.sfx(sounds.SELECT)
            if self.app.save["seen_intro"]:
                self.app.to_select(self.app.save["unlocked"])
            else:
                self.app.to_intro()
        elif C.pressed("up"):
            sounds.sfx(sounds.SELECT)
            self.app.to_intro()
        if C.pressed("back") or pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw(self):
        t = self.t
        art.draw_background(levels.THEMES[0], t * 0.5, t)
        pyxel.rect(0, 140, W, 20, BROWN)
        pyxel.rect(0, 140, W, 3, GREEN)
        art.rainbow_arc(W // 2, 140, 120, 4)
        art.big_center(18, "RAINBOWS,", RAINBOW, 3)
        art.big_center(42, "UNICORNS &", [WHITE, LPINK], 3)
        art.big_center(66, "PINK BUNNIES", [PINK, HOTPINK], 3)
        bx = (t * 1.5) % (W + 80) - 40
        art.draw_unicorn(bx - 30, 124, 1, (t // 6) % 2)
        art.draw_bunny(bx, 120, 1, "run", t // 5)
        for i in range(3):
            px = (bx + 60 + i * 18)
            art.draw_pig(px, 130, 1, t // 6 + i, "walk")
        if t % 40 < 28:
            art.center_text(100, "PRESS ENTER TO PLAY", WHITE)
        art.center_text(112, "PRESS UP TO WATCH THE STORY", LPINK)
        art.center_text(150, "SAVE ALL THE CARROTS FROM CARROT BOOM!", CREAM)


class Select:
    COLS = 8
    CW, CH = 28, 14

    def __init__(self, app, cursor):
        self.app = app
        self.cursor = clamp(cursor, 1, app.save["unlocked"])
        self.t = 0
        sounds.music(sounds.MUSIC_TITLE)

    def update(self):
        self.t += 1
        c = self.cursor - 1
        x, y = c % 8, c // 8
        if C.pressed("left", True):
            x -= 1
        if C.pressed("right", True):
            x += 1
        if C.pressed("up", True):
            y -= 1
        if C.pressed("down", True):
            y += 1
        x, y = clamp(x, 0, 7), clamp(y, 0, 7)
        new = y * 8 + x + 1
        if new != self.cursor:
            self.cursor = new
            sounds.sfx(sounds.COIN)
        if C.ok():
            if self.cursor <= self.app.save["unlocked"]:
                sounds.sfx(sounds.SELECT)
                self.app.play(self.cursor)
            else:
                sounds.sfx(sounds.NOPE)
        if C.pressed("back"):
            self.app.to_title()

    def draw(self):
        t = self.t
        sv = self.app.save
        pyxel.cls(NAVY)
        for i in range(30):
            pyxel.pset((i * 71 + t * 0.2) % W, (i * 37) % H, DPURPLE)
        art.big_center(4, "PICK A LEVEL", RAINBOW, 2)
        x0, y0 = 16, 22
        for n in range(1, LEVEL_COUNT + 1):
            c = n - 1
            x = x0 + (c % 8) * self.CW
            y = y0 + (c // 8) * (self.CH + 1)
            th = levels.theme_of(n)
            locked = n > sv["unlocked"]
            boss = levels.is_boss(n)
            if locked:
                pyxel.rect(x, y, self.CW - 2, self.CH, DGRAY)
                pyxel.rect(x + 10, y + 6, 6, 5, LAV)
                pyxel.rectb(x + 11, y + 3, 4, 4, LAV)
            else:
                pyxel.rect(x, y, self.CW - 2, self.CH, th["sky"])
                pyxel.rect(x, y + self.CH - 3, self.CW - 2, 3, th["grass"])
                label = str(n)
                tc = NAVY if th["sky"] not in (NAVY, DPURPLE, ORANGE) else WHITE
                if boss:
                    pyxel.rect(x, y, self.CW - 2, self.CH, RED)
                    pyxel.tri(x + 3, y + 3, x + 9, y + 3, x + 6, y + 0, YELLOW)
                    tc = WHITE
                pyxel.text(x + 13 - len(label) * 2, y + 3, label, tc)
                if not boss:
                    got = sv["carrots"].get(str(n), 0)
                    for i in range(3):
                        pyxel.rect(x + 3 + i * 3, y + self.CH - 2, 2, 2, ORANGE if i < got else DGRAY)
                if n in sv["beaten"]:
                    pyxel.pset(x + self.CW - 5, y + 2, YELLOW)
                    pyxel.pset(x + self.CW - 6, y + 3, YELLOW)
                    pyxel.pset(x + self.CW - 4, y + 3, YELLOW)
                    pyxel.pset(x + self.CW - 5, y + 4, YELLOW)
            if n == self.cursor:
                col = RAINBOW[(t // 4) % 6]
                pyxel.rectb(x - 2, y - 2, self.CW + 2, self.CH + 4, col)
                pyxel.rectb(x - 1, y - 1, self.CW, self.CH + 2, WHITE)
        n = self.cursor
        th = levels.theme_of(n)
        info = f"LEVEL {n}: {th['name']}"
        if levels.is_boss(n):
            info = f"LEVEL {n}: BOSS - " + " & ".join(levels.BOSS_NAMES[k] for k in levels.BOSSES[n])
        art.center_text(144, info, YELLOW)
        total = sum(sv["carrots"].values())
        art.text(4, 153, f"CARROTS {total}/168", ORANGE)
        art.text(W - 60, 153, f"COINS {sv['coins']}", YELLOW)
        art.center_text(153, "ESC: TITLE", LAV)


class App:
    def __init__(self):
        pyxel.init(W, H, title=TITLE, fps=60, quit_key=pyxel.KEY_NONE)
        pyxel.colors[:] = PALETTE
        sounds.setup()
        self.save = save.load()
        self.scene = Title(self)

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        self.scene.update()

    def draw(self):
        self.scene.draw()

    def to_title(self):
        self.scene = Title(self)

    def to_select(self, cursor):
        self.scene = Select(self, cursor)

    def play(self, n):
        self.scene = Play(self, n)

    def to_intro(self):
        self.scene = Intro(self)

    def to_ending(self):
        self.scene = Ending(self)

    def level_done(self, n, carrots, coins, power):
        sv = self.save
        sv["unlocked"] = max(sv["unlocked"], min(LEVEL_COUNT, n + 1))
        key = str(n)
        sv["carrots"][key] = max(sv["carrots"].get(key, 0), carrots)
        if levels.is_boss(n):
            sv["carrots"].pop(key, None)
        if n not in sv["beaten"]:
            sv["beaten"].append(n)
        sv["coins"] = coins
        sv["power"] = power
        save.write(sv)


if __name__ == "__main__":
    App().run()
