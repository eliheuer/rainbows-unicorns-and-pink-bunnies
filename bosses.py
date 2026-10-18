# The bosses. One waits at the end of every 8th level.
import math
import random

import pyxel

import art
import sounds
from consts import *
from entities import Item, Shot

GROUND_Y = 17 * T   # the floor of every boss room


class Boss:
    name = "BOSS"

    def __init__(self, g, x, hard, hp, w, h):
        self.g = g
        self.hard = hard
        self.w, self.h = w, h
        self.x, self.y = x, GROUND_Y - h
        self.vx = self.vy = 0.0
        self.hp = self.max_hp = hp
        self.flash = 0
        self.dead = False
        self.t = 0
        self.facing = -1
        self.on_ground = True
        self.angry = False

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def fury(self):
        """How fast the boss attacks. Bigger means faster."""
        return 1.0 + (0.25 if self.hard else 0) + (0.35 if self.angry else 0)

    def every(self, frames):
        """True once every `frames` frames, sooner when the boss is angry."""
        return self.t % max(1, int(frames / self.fury)) == 0

    def hurt(self, dmg):
        if self.flash > 0 or self.dead:
            return False
        self.hp -= dmg
        self.flash = 30
        sounds.sfx(sounds.BOSS_HIT)
        self.g.shake = 4
        for _ in range(6):
            self.g.sparkle(self.cx, self.y + self.h / 2, random.choice([WHITE, YELLOW]))
        if self.hp <= 0:
            self.dead = True
            self.g.boss_defeated(self)
        elif not self.angry and self.hp <= self.max_hp // 2:
            self.angry = True
            self.g.banner(f"{self.name} IS ANGRY!", "WATCH OUT!", 90)
        return True

    def face_player(self):
        self.facing = sign(self.g.player.cx - self.cx) or self.facing

    def physics(self):
        """Falls and walks. Returns True when it just landed."""
        g = self.g
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        if g.move_x(self, self.vx):
            self.vx = -self.vx
        was = self.on_ground
        self.on_ground = g.move_y(self, self.vy, oneway=False) == "floor"
        if self.on_ground:
            self.vy = 0
        return self.on_ground and not was

    def update(self):
        self.t += 1
        if self.flash > 0:
            self.flash -= 1
        self.think()

    def think(self):
        pass

    def visible(self, t):
        return not (self.flash and (t // 2) % 2 == 0)

    def warn(self, t):
        if t % 8 < 4:
            art.text(self.cx - 2, self.y - 26, "!", RED)


class MoneyCat(Boss):
    """Throws coins, steals your coins with his lucky paw, and gets
    stronger with every coin he takes."""
    name = "MONEY CAT"

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 26 if hard else 18, 28, 30)
        self.vx = 0.8 if hard else 0.6
        self.wave = 0.0
        self.winding = 0
        self.rain = 0

    def think(self):
        g = self.g
        self.face_player()
        self.wave += 0.5 if self.winding else 0.15
        self.physics()
        if self.x < 50 or self.x > 205:
            self.vx = -self.vx
            self.x = clamp(self.x, 50, 205)
        if self.on_ground and self.every(170):
            self.vy = -4.5
            self.vx = sign(g.player.cx - self.cx) * abs(self.vx)
        if self.every(70):
            n = 5 if self.angry or self.hard else 3
            for i in range(n):
                g.shots.append(Shot("coin", self.cx - 3, self.y + 6, 7, 8,
                                    self.facing * (0.8 + i * 0.6), -3.8 + i * 0.3, 0.15))
            sounds.sfx(sounds.COIN)
        if self.every(240) and not self.winding:
            self.winding = 45
            g.float_text(self.cx, self.y - 8, "LUCKY PAW!", GOLD)
        if self.winding:
            self.winding -= 1
            if self.winding == 0:
                speed = 2.4 if self.hard else 1.9
                g.shots.append(Shot("paw", self.cx - 6, self.y + 8, 12, 12,
                                    self.facing * speed, 0, 0, 220))
                if self.angry or self.hard:
                    g.shots.append(Shot("paw", self.cx - 6, self.y - 16, 12, 12,
                                        self.facing * speed * 0.8, -0.6, 0, 220))
                sounds.sfx(sounds.STEAL)
        if self.angry:
            self.rain += 1
            if self.rain % 420 == 1:
                g.banner("COIN STORM!", "", 60)
                for _ in range(8):
                    g.shots.append(Shot("coin", random.uniform(16, 232), random.uniform(-60, -8),
                                        7, 8, 0, 0, 0.12))

    def took_coins(self, n):
        """Every 5 coins he takes heals him a little."""
        if n:
            self.hp = min(self.max_hp, self.hp + max(1, n // 5))
            self.g.float_text(self.cx, self.y - 16, "MORE MONEY, MORE POWER!", GOLD)

    def draw(self, t):
        if self.visible(t):
            art.draw_money_cat(self.x - 2, self.y - 4, t, self.wave, self.facing, self.angry)
            if self.winding:
                self.warn(t)


class Eggbert(Boss):
    """Spits eggs you can ride and catch, and fireballs you can't."""
    name = "EGGBERT"

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 22 if hard else 16, 22, 28)
        self.vx = 0.7
        self.shots_fired = 0
        self.burst = 0
        self.double = 0

    def think(self):
        g = self.g
        self.face_player()
        self.physics()
        if self.x < 110 or self.x > 222:
            self.vx = -self.vx
            self.x = clamp(self.x, 110, 222)
        if self.on_ground and self.every(110):
            self.vy = -4.5
        mouth_x = self.x + self.w if self.facing > 0 else self.x - 10
        if self.on_ground and self.every(80):
            self.shots_fired += 1
            fire_turn = 3 if (self.hard or self.angry) else 4
            if self.shots_fired % fire_turn == 0:
                self.burst = 4 if self.angry else 3
            else:
                self.spit_egg(mouth_x)
                if self.angry:
                    self.double = 18
        if self.double:
            self.double -= 1
            if self.double == 0:
                self.spit_egg(mouth_x)
        if self.burst and self.t % 10 == 0:
            self.burst -= 1
            fy = self.y + random.choice((6, 14, 20))
            g.shots.append(Shot("fire", mouth_x, fy, 8, 8, self.facing * 2.6, 0, 0, 200))
            sounds.sfx(sounds.ZAP)

    def spit_egg(self, mouth_x):
        egg = Item("egg", mouth_x, self.y + 16, state="moving")
        egg.vx = self.facing * random.uniform(1.6, 2.6 if self.hard else 2.2)
        egg.owner = "boss"
        self.g.items.append(egg)
        sounds.sfx(sounds.THROW)

    def draw(self, t):
        if self.visible(t):
            art.draw_eggbert(self.x - 1, self.y - 4, self.facing, t, self.hard or self.angry)
            if self.burst:
                self.warn(t)


class BlackBunny(Boss):
    """Hops on you. Every landing sends shockwaves along the floor."""
    name = "THE BLACK BUNNY"

    def __init__(self, g, x, hard, twin=False):
        super().__init__(g, x, hard, 11 if twin else 16, 20, 24)
        self.state = "wait"
        self.timer = 70
        self.jumps = 0
        self.combo = 0

    def think(self):
        g = self.g
        self.face_player()
        if self.state == "wait":
            self.vx = 0
            self.physics()
            self.timer -= 1
            if self.timer <= 0:
                self.jumps += 1
                big = self.jumps % 3 == 0
                self.vy = -8.5 if big else -6.5
                air = 2 * -self.vy / GRAVITY
                lead = g.player.vx * air * 0.5 if self.angry else 0
                self.vx = clamp((g.player.cx + lead - self.cx) / air, -3.5, 3.5)
                self.state = "air"
                self.on_ground = False
                sounds.sfx(sounds.JUMP)
        else:
            if self.physics():
                big = self.jumps % 3 == 0
                self.state = "wait"
                if self.combo > 0:
                    self.combo -= 1
                    self.timer = 10
                else:
                    self.timer = int(50 / self.fury)
                    if self.angry:
                        self.combo = 2
                self.vx = 0
                g.shake = 12 if big else 8
                sounds.sfx(sounds.BOOM)
                speeds = (2.6, 1.5) if big else (2.6,)
                for sp in speeds:
                    for d in (-1, 1):
                        g.shots.append(Shot("wave", self.cx - 4 + d * 8, GROUND_Y - 6, 9, 6,
                                            d * sp, 0, 0, 160))
                g.puff(self.cx, GROUND_Y, LGRAY)

    def draw(self, t):
        if self.visible(t):
            pose = "jump" if self.state == "air" else ("crouch" if self.timer < 20 else "stand")
            art.draw_bunny(self.x - 2, self.y - 16, self.facing, pose, 0, body=BLACK,
                           inner=DGRAY, belly=DGRAY, eye=RED, cheek=PLUM, angry=True, s=2)


class TornadoBunny(Boss):
    """Floats in the sky, drops tornadoes, and swoops down at you."""
    name = "TORNADO BUNNY"

    def __init__(self, g, x, hard, twin=False):
        super().__init__(g, x, hard, 11 if twin else 16, 20, 24)
        self.vx = 0.9
        self.base = 48
        self.y = 60
        self.state = "float"
        self.timer = 0

    def think(self):
        g = self.g
        self.face_player()
        if self.state == "float":
            self.x += self.vx * self.fury
            if self.x < 30 or self.x > 206:
                self.vx = -self.vx
                self.x = clamp(self.x, 30, 206)
            self.y = self.base + math.sin(self.t * 0.025) * 26 + 6
            if self.every(110):
                g.shots.append(Shot("tornado", self.cx - 7, self.y + self.h, 14, 24, 0, 1, 0.2, 420))
                if self.angry:
                    g.shots.append(Shot("tornado", 248 - self.cx - 7, 20, 14, 24, 0, 1, 0.2, 420))
                sounds.sfx(sounds.SPEED)
            if self.every(320):
                self.state = "warn"
                self.timer = 40
        elif self.state == "warn":
            self.timer -= 1
            self.x += math.sin(self.t * 1.3) * 1.5
            if self.timer <= 0:
                self.state = "dive"
                self.target = clamp(g.player.cx - self.w / 2, 20, 216)
        elif self.state == "dive":
            self.x += clamp(self.target - self.x, -3, 3)
            self.y += 3.5
            if self.y >= GROUND_Y - self.h:
                self.y = GROUND_Y - self.h
                self.state = "dizzy"
                self.timer = 50
                g.shake = 8
                g.puff(self.cx, GROUND_Y, WHITE)
                sounds.sfx(sounds.BOOM)
        elif self.state == "dizzy":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "rise"
        elif self.state == "rise":
            self.y -= 1.5
            goal = self.base + math.sin(self.t * 0.025) * 26 + 6
            if self.y <= goal:
                self.state = "float"

    def draw(self, t):
        if self.visible(t):
            art.draw_tornado(self.x - 2, self.y + 14, 24, 18, t)
            art.draw_bunny(self.x - 2, self.y - 16, self.facing, "jump", 0, body=HOTPINK,
                           inner=LPINK, belly=LPINK, eye=PURPLE, cheek=RED, angry=True, s=2)
            if self.state == "warn":
                self.warn(t)
            if self.state == "dizzy":
                for i in range(3):
                    a = t * 0.15 + i * 2.1
                    pyxel.pset(self.cx + math.cos(a) * 10, self.y - 18 + math.sin(a) * 3, YELLOW)


class CarrotBoom(Boss):
    """Throws carrot bombs, rains them from the sky, and charges at you."""
    name = "CARROT BOOM"

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 30, 22, 26)
        self.rain = 0
        self.charge = 0

    def think(self):
        g = self.g
        if self.charge > 0:
            # get ready... then run across the room
            self.charge -= 1
            if self.charge > 30:
                self.vx = 0
            elif self.charge == 30:
                self.face_player()
                self.vx = self.facing * 3.4
                sounds.sfx(sounds.SPEED)
            self.physics()
            if self.charge == 0 or self.x <= 9 or self.x + self.w >= 247:
                self.charge = 0
                self.vx = 0
            return
        self.face_player()
        landed = self.physics()
        if self.on_ground:
            self.vx *= 0.85
        if landed:
            g.puff(self.cx, GROUND_Y, WHITE)
        if self.on_ground and self.every(50):
            target = random.uniform(40, 200)
            self.vy = -3.5
            self.vx = clamp((target - self.x) / 23, -2, 2)
        if self.every(85):
            n = 2 if self.angry else 1
            for i in range(n):
                bomb = Item("bomb", self.cx - 5, self.y - 6, state="thrown")
                bomb.owner = "boss"
                bomb.vx = clamp((g.player.cx - self.cx) / 55, -3, 3) + (i * 1.2 - 0.6) * (n - 1)
                bomb.vy = -4 - i
                bomb.fuse = 140
                g.items.append(bomb)
            sounds.sfx(sounds.THROW)
        if self.on_ground and self.every(330):
            self.charge = 70
            g.float_text(self.cx, self.y - 30, "CARROT CHARGE!", ORANGE)
        if self.angry:
            self.rain += 1
            if self.rain % 300 == 1:
                g.banner("CARROT RAIN!", "", 90)
                for _ in range(5):
                    b = Item("bomb", random.uniform(20, 228), random.uniform(-40, -12), state="thrown")
                    b.owner = "boss"
                    b.fuse = 200
                    g.items.append(b)

    def draw(self, t):
        if self.visible(t):
            back = -self.facing
            # carrot sack on his back
            sx = self.cx + back * 12 - 7
            pyxel.elli(sx, self.y + 2, 14, 14, BROWN)
            art.draw_carrot(sx + 3, self.y - 4)
            pose = "run" if self.charge and self.charge <= 30 else ("hold" if self.on_ground else "jump")
            art.draw_bunny(self.x - 1, self.y - 14, self.facing, pose, t // 4,
                           body=WHITE, inner=LPINK, belly=CREAM, eye=RED, cheek=PINK,
                           angry=True, s=2)
            if self.charge > 30:
                self.warn(t)


def make(kind, g, hard, twin=False):
    if kind == "moneycat":
        return MoneyCat(g, 190, hard)
    if kind == "eggbert":
        return Eggbert(g, 200, hard)
    if kind == "blackbunny":
        return BlackBunny(g, 140 if twin else 190, hard, twin)
    if kind == "tornado":
        return TornadoBunny(g, 100 if twin else 160, hard, twin)
    return CarrotBoom(g, 190, hard)
