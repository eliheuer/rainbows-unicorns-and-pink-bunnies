# The bosses. One waits at the end of every 8th level.
import math
import random

import pyxel

import art
import sounds
from consts import *
from entities import Item, Particle, Pickup, Pig, Shot

GROUND_Y = 17 * T   # the floor of every boss room


class Boss:
    name = "BOSS"
    harmless = False    # True when touching the boss does not hurt you

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

    beaten_msg = None    # (title, subtitle) shown when you win, if not the usual one

    def hit(self, dmg, how, obj=None):
        """Something hit the boss. how is "zap", "throw", "boom" or "stomp"."""
        return self.hurt(dmg)

    def catch_bolt(self, b):
        """Return True if the boss blocks this lightning bolt in a special way."""
        return False

    def stomped(self):
        """The bunny bounced on the boss's head."""

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


def seg_dist(px, py, x1, y1, x2, y2):
    """How far the point (px, py) is from the line from (x1, y1) to (x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    k = clamp(((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1), 0, 1)
    return math.hypot(px - (x1 + k * dx), py - (y1 + k * dy))


class MoneyCat(Boss):
    """The lucky cat. He fires laser coins and red lucky beams from his
    waving paw, and a gold greedy beam from the big coin he holds. Between attacks he rests. That is
    when you throw things at him!"""
    name = "MONEY CAT"
    PATTERNS = ["coins", "beam", "ring", "greedy"]
    SHOUTS = {"coins": "LASER COINS!", "beam": "LUCKY BEAM!", "ring": "COIN RING!",
              "greedy": "GREEDY BEAM!"}

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 26 if hard else 18, 28, 30)
        self.wave = 0.0
        self.state = "warn"
        self.timer = 50
        self.n = 0
        self.rings = 0
        self.beam = None     # [x1, y1, x2, y2, frames left, "aim" or "fire", kind]
        self.beams_left = 0
        self.home = x

    @property
    def pattern(self):
        return self.PATTERNS[self.n % len(self.PATTERNS)]

    def paw(self):
        """Where his raised, waving paw is."""
        dx = 1 if self.facing > 0 else 30
        return self.x - 2 + dx, self.y - 3 + (math.sin(self.wave) + 1) * 1.5

    def coin(self):
        """Where the big gold coin he holds is."""
        dx = 24 if self.facing > 0 else 7
        return self.x - 2 + dx, self.y - 4 + 25

    def laser_coin(self, x, y, angle, speed=2.4):
        s = Shot("lasercoin", x - 3, y - 3, 6, 6,
                 math.cos(angle) * speed, math.sin(angle) * speed, 0, 400)
        s.bx, s.by = s.x, s.y
        self.g.shots.append(s)

    def think(self):
        g = self.g
        p = g.player
        self.physics()
        if self.on_ground:
            self.vx = 0
        self.timer -= 1
        busy = self.state == "fire"
        self.wave += 0.45 if busy else 0.12
        if self.state != "fire" or self.pattern != "greedy":
            self.face_player()

        if self.state == "warn":
            if self.timer <= 0:
                self.state = "fire"
                self.timer = {"coins": 150, "beam": 0, "ring": 130, "greedy": 0}[self.pattern]
                self.rings = 0
                g.float_text(self.cx, self.y - 30, self.SHOUTS[self.pattern], GOLD)
                if self.pattern == "beam":
                    self.beams_left = 2 if self.angry or self.hard else 1
                    self.start_beam("lucky")
                elif self.pattern == "greedy":
                    self.start_beam("greedy")
            return
        if self.state == "rest":
            if self.on_ground and self.timer == 70:
                # hop to the other side of the room
                self.home = 40 if self.home > 120 else 190
                self.vy = -4.5
                self.vx = (self.home - self.x) / 30
            if self.timer <= 0:
                self.n += 1
                self.state = "warn"
                self.timer = 40
            return

        # ---- firing
        pat = self.pattern
        if pat == "coins":
            every = 14 if self.angry else 20
            if self.timer % every == 0:
                px, py = self.paw()
                aim = math.atan2(p.y + p.h / 2 - py, p.cx - px)
                spread = (-0.3, 0, 0.3) if self.angry or self.hard else (0,)
                for off in spread:
                    self.laser_coin(px, py, aim + off)
                sounds.sfx(sounds.ZAP)
        elif pat == "ring":
            if self.timer % 40 == 0:
                self.rings += 1
                n = 14 if self.angry else 10
                off = (self.rings % 2) * math.pi / n
                cx, cy = self.cx, self.y + 12
                for k in range(n):
                    self.laser_coin(cx, cy, off + k * math.tau / n, 1.3)
                sounds.sfx(sounds.COIN)
        elif self.beam:
            self.update_beam()
            return
        if self.timer <= 0:
            self.rest()

    def rest(self):
        self.state = "rest"
        self.timer = 75 if self.angry else 105
        self.beam = None
        self.g.float_text(self.cx, self.y - 30, "PURR...", LPINK)

    def start_beam(self, kind):
        x1, y1 = self.paw()
        if kind == "greedy":
            y1 = GROUND_Y - 7
            x2 = 248 if self.facing > 0 else 8
            self.beam = [self.cx, y1, x2, y1, 55, "aim", kind]
        else:
            self.beam = [x1, y1, x1, y1, 50, "aim", kind]
        sounds.sfx(sounds.SELECT)

    def update_beam(self):
        g = self.g
        p = g.player
        b = self.beam
        b[4] -= 1
        if b[5] == "aim":
            if b[6] == "lucky":
                b[0], b[1] = self.paw()
                if b[4] > 15:      # follow the bunny, then lock on
                    ang = math.atan2(p.y + p.h / 2 - b[1], p.cx - b[0])
                    b[2], b[3] = b[0] + math.cos(ang) * 400, b[1] + math.sin(ang) * 400
            if b[4] <= 0:
                b[5] = "fire"
                b[4] = 28
                g.shake = 6
                sounds.sfx(sounds.BOOM)
            return
        # fire!
        if b[6] == "greedy":
            b[0] = self.cx      # the beam sweeps out across the floor
            reach = 28 - b[4]
            b[2] = self.cx + self.facing * min(240, reach * 18)
            lo, hi = sorted((b[0], b[2]))
            if lo < p.cx < hi and p.y + p.h > GROUND_Y - 12 and not p.invuln:
                g.steal_coins()
                p.invuln = 60
        else:
            if seg_dist(p.cx, p.y + p.h / 2, *b[:4]) < 8:
                p.hurt(g, b[0])
        if b[4] % 6 == 0:
            g.sparkle(b[2] if b[6] == "greedy" else b[0], b[3], YELLOW)
        if b[4] <= 0:
            self.beams_left -= 1
            if b[6] == "lucky" and self.beams_left > 0:
                self.start_beam("lucky")
            else:
                self.rest()

    def took_coins(self, n):
        """Every 5 coins he takes heals him a little."""
        if n:
            self.hp = min(self.max_hp, self.hp + max(1, n // 5))
            self.g.float_text(self.cx, self.y - 16, "MORE MONEY, MORE POWER!", GOLD)

    def draw_beam(self, t):
        b = self.beam
        if not b:
            return
        x1, y1, x2, y2, left, mode, kind = b
        pyxel.clip(8, 0, 240, GROUND_Y)
        if mode == "aim":
            # a blinking dotted line shows where the beam will go
            if kind == "lucky" and (left > 15 or t % 4 < 2):
                # thick moving dashes, gold while aiming, red when locked on
                col = GOLD if left > 15 else RED
                length = math.hypot(x2 - x1, y2 - y1) or 1
                ux, uy = (x2 - x1) / length, (y2 - y1) / length
                for d in range(int(t % 10), int(length), 10):
                    ax, ay = x1 + ux * d, y1 + uy * d
                    for o in (-1, 0, 1):
                        pyxel.line(ax - uy * o, ay + ux * o, ax + ux * 5 - uy * o, ay + uy * 5 + ux * o, col)
                if left <= 15:
                    p = self.g.player
                    pyxel.circb(p.cx, p.y + p.h / 2, 9, RED)
                    pyxel.line(p.cx - 12, p.y + p.h / 2, p.cx + 12, p.y + p.h / 2, RED)
            elif kind == "greedy":
                # the floor glows where the greedy beam will go
                lo, hi = (x1, x2) if x1 < x2 else (x2, x1)
                pyxel.dither(0.5 if t % 8 < 4 else 0.25)
                pyxel.rect(lo, y1 - 5, hi - lo, 10, GOLD)
                pyxel.dither(1.0)
                pyxel.rectb(lo, y1 - 5, hi - lo, 10, YELLOW if t % 8 < 4 else ORANGE)
                for ax in range(int(lo) + 8, int(hi), 24):
                    art.draw_coin(ax, y1 - 4, t)
        else:
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy / length, dx / length
            # lucky beams are lucky red, greedy beams are gold
            cols = (RED, HOTPINK, WHITE) if kind == "lucky" else (GOLD, YELLOW, WHITE)
            for half, col in zip((5, 3, 1), cols):
                hx, hy = nx * half, ny * half
                pyxel.tri(x1 + hx, y1 + hy, x2 + hx, y2 + hy, x1 - hx, y1 - hy, col)
                pyxel.tri(x2 + hx, y2 + hy, x2 - hx, y2 - hy, x1 - hx, y1 - hy, col)
            # spinning coins ride along the beam
            for d in range(int((t * 4) % 16), int(length), 16):
                cx, cy = x1 + dx / length * d, y1 + dy / length * d
                w = 2 + abs(math.sin(t * 0.3 + d)) * 5
                pyxel.elli(cx - w / 2, cy - 4, w, 8, ORANGE)
                pyxel.elli(cx - w / 2 + 1, cy - 3, max(1, w - 2), 6, YELLOW)
        pyxel.clip()

    def draw(self, t):
        self.draw_beam(t)
        if self.visible(t):
            art.draw_money_cat(self.x - 2, self.y - 4, t, self.wave, self.facing, self.angry)
            b = self.beam
            if b and b[5] == "aim":
                # his paw or coin glows while he charges up
                lucky = b[6] == "lucky"
                gx, gy = self.paw() if lucky else self.coin()
                pyxel.circb(gx, gy, 3 + (t // 3) % 3, RED if lucky else YELLOW)
                pyxel.circb(gx, gy, 5 + (t // 3) % 3, HOTPINK if lucky else ORANGE)
            if self.state == "warn":
                self.warn(t)
            if self.state == "rest" and t % 40 < 20:
                art.text(self.cx + 8, self.y - 8, "z", LPINK)


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


class MiniTornadoBunny:
    """A little Tornado Bunny that helps Carrot Boom. It floats over you,
    shakes, and then dives down. Zap it two times and it flies away."""

    def __init__(self, g, dives):
        self.g = g
        self.x, self.y = -20.0, 20.0
        self.w, self.h = 16, 28
        self.state = "in"
        self.timer = 0
        self.dives = dives
        self.hp = 2
        self.flash = 0
        self.gone = False
        self.t = 0

    @property
    def cx(self):
        return self.x + self.w / 2

    def zapped(self, b):
        if self.state == "leave" or not overlap(b, self):
            return False
        if self.flash == 0:
            self.hp -= 1
            self.flash = 30
            sounds.sfx(sounds.BOSS_HIT)
            for _ in range(8):
                self.g.sparkle(self.cx, self.y + 10, random.choice([PINK, WHITE, YELLOW]))
            if self.hp <= 0:
                self.state = "leave"
                self.g.float_text(self.cx, self.y - 10, "BYE BYE!", PINK)
        return True

    def update(self):
        g, p = self.g, self.g.player
        self.t += 1
        self.timer -= 1
        if self.flash:
            self.flash -= 1
        hover = 34 + math.sin(self.t * 0.08) * 4
        if self.state == "in":
            self.x += clamp(p.cx - self.cx, -2, 2)
            self.y += (hover - self.y) * 0.08
            if abs(p.cx - self.cx) < 6:
                self.state, self.timer = "follow", 70
        elif self.state == "follow":
            self.x += clamp(p.cx - self.cx, -1.3, 1.3)
            self.y += (hover - self.y) * 0.1
            if self.timer <= 0:
                self.state, self.timer = "warn", 35
        elif self.state == "warn":
            self.x += math.sin(self.t * 1.3) * 1.2
            if self.timer <= 0:
                self.state = "dive"
                sounds.sfx(sounds.SPEED)
        elif self.state == "dive":
            self.y += 3.5
            if overlap(p, self):
                p.hurt(g, self.cx)
            if self.y >= GROUND_Y - self.h:
                self.y = GROUND_Y - self.h
                self.state, self.timer = "dizzy", 45
                g.shake = 6
                g.puff(self.cx, GROUND_Y, WHITE)
                sounds.sfx(sounds.BOOM)
        elif self.state == "dizzy":
            if self.timer <= 0:
                self.dives -= 1
                self.state = "rise" if self.dives > 0 else "leave"
        elif self.state == "rise":
            self.y -= 1.5
            if self.y <= hover:
                self.state, self.timer = "follow", 60
        elif self.state == "leave":
            self.y -= 2.5
            self.x += 1.5
            if self.y < -40:
                self.gone = True

    def draw(self, t):
        if self.state in ("warn", "dive"):
            pyxel.elli(self.cx - 8, GROUND_Y - 2, 16, 4, BLACK)
        if self.flash and t % 4 < 2:
            return
        art.draw_tornado(self.x, self.y + 14, 16, 14, t)
        art.draw_bunny(self.x + 2, self.y - 4, 1, "jump", 0, body=HOTPINK, inner=LPINK,
                       belly=LPINK, eye=PURPLE, cheek=RED, angry=True)
        if self.state == "warn" and t % 8 < 4:
            art.text(self.cx - 2, self.y - 12, "!", RED)
        if self.state == "dizzy":
            for i in range(3):
                a = t * 0.15 + i * 2.1
                pyxel.pset(self.cx + math.cos(a) * 8, self.y - 6 + math.sin(a) * 3, YELLOW)


class CarrotBoom(Boss):
    """The final boss! He does five moves, one after the other:
    1. Carrot bombs: he hops around and throws carrot bombs.
    2. Tornado dance: he spins and sends little tornadoes at you.
    3. Hide and seek: he digs under the ground and pops up under you.
    4. Tornado Bunny: he calls a little Tornado Bunny that dives at you. Zap it!
    5. Garden time: he waters his carrots with his butt in the air. Bonk it!"""
    name = "CARROT BOOM"
    MOVES = ["bombs", "dance", "dig", "tornado", "garden"]
    SHOUTS = {"bombs": "CARROT BOMBS!", "dance": "TORNADO DANCE!",
              "dig": "HIDE AND SEEK!", "tornado": "GO, TORNADO BUNNY!",
              "garden": "GARDEN TIME!"}

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 24, 22, 26)
        self.mini = None       # the little Tornado Bunny he calls for help
        self.n = 0
        self.state = "warn"
        self.timer = 60
        self.step = 0          # how far he is in the move
        self.hidden = False    # under the ground
        self.ears_x = 0.0
        self.bonks = 0         # butt bonks in this garden time
        self.harmless = True   # he only hurts you when he pops out of the ground

    @property
    def move(self):
        return self.MOVES[self.n % len(self.MOVES)]

    def next_move(self):
        self.n += 1
        self.state = "warn"
        self.timer = 50

    def hit(self, dmg, how, obj=None):
        if self.hidden:
            return False
        if self.move == "garden" and self.state == "do":
            if not self.hurt(dmg * 2):
                return False
            self.bonks += 1
            self.g.float_text(self.cx, self.y - 20, "BUTT BONK!", YELLOW)
            if self.bonks >= 3 and not self.dead:
                # he jumps up and gets back to work
                self.vy = -4
                self.g.float_text(self.cx, self.y - 30, "HEY!!", RED)
                self.next_move()
            return True
        return self.hurt(dmg)

    def stomped(self):
        if self.move == "garden" and self.state == "do":
            self.hit(2, "stomp")

    def throw_bomb(self, vx, vy, fuse=180):
        bomb = Item("bomb", self.cx - 5, self.y - 6, state="thrown")
        bomb.owner = "boss"
        bomb.vx, bomb.vy = vx, vy
        bomb.fuse = fuse
        self.g.items.append(bomb)

    def think(self):
        g = self.g
        p = g.player
        self.timer -= 1
        if self.hidden:
            self.dig(p)
            return
        landed = self.physics()
        self.harmless = not (self.state == "rest" and self.move == "dig" and self.vy < 0)
        if self.on_ground:
            self.vx *= 0.85
        if landed:
            g.puff(self.cx, GROUND_Y, WHITE)
        if self.state == "warn":
            self.face_player()
            if self.timer <= 0:
                self.state = "do"
                self.step = 0
                g.float_text(self.cx, self.y - 30, self.SHOUTS[self.move], ORANGE)
                self.start()
            return
        if self.state == "rest":
            if self.timer <= 0:
                self.next_move()
            return
        getattr(self, "do_" + self.move)(p)

    def start(self):
        g = self.g
        move = self.move
        if move == "bombs":
            self.timer = 300 if self.angry else 240
            if self.angry:
                g.banner("CARROT RAIN!", "", 60)
                for _ in range(2):
                    b = Item("bomb", random.uniform(30, 218), random.uniform(-40, -12), state="thrown")
                    b.owner = "boss"
                    b.fuse = 200
                    g.items.append(b)
        elif move == "dance":
            self.timer = 220
        elif move == "dig":
            self.vy = -4.5
            self.timer = 999
        elif move == "tornado":
            self.mini = MiniTornadoBunny(self.g, 3 if not self.angry else 4)
        else:
            self.timer = 300
            self.bonks = 0
            self.drop_heart()
            # his watering can makes the carrots grow back right away
            for tuft in g.tufts:
                if not tuft.active:
                    tuft.timer = 1

    def drop_heart(self):
        """If you are hurt, a heart falls from the sky to help you."""
        g, p = self.g, self.g.player
        if p.hearts < p.max_hearts and not any(c.kind == "heart" for c in g.pickups):
            g.pickups.append(Pickup("heart", random.uniform(30, 210), -10, life=600))

    def rest(self, frames, msg="PHEW!"):
        self.state = "rest"
        self.timer = frames
        self.drop_heart()
        self.g.float_text(self.cx, self.y - 30, msg, WHITE)

    def do_bombs(self, p):
        self.face_player()
        if self.on_ground and self.every(60):
            target = random.uniform(40, 200)
            self.vy = -3.5
            self.vx = clamp((target - self.x) / 23, -2, 2)
        if self.every(115):
            self.throw_bomb(clamp((p.cx - self.cx) / 55, -3, 3), -4)
            sounds.sfx(sounds.THROW)
        if self.timer <= 0:
            self.rest(50)

    def do_dance(self, p):
        # he spins and hops, and every so often a little tornado flies out
        self.step += 1
        if self.step % 8 == 0:
            self.facing = -self.facing
        if self.on_ground and self.step % 30 == 0:
            self.vy = -2
        if self.step % 18 == 0:
            self.g.particles.append(Particle(self.cx + random.uniform(-10, 10), self.y - 8,
                                             random.uniform(-0.5, 0.5), -0.7, 30,
                                             random.choice([PINK, YELLOW, SKY]), 2))
        when = (50, 150)
        if self.step in when:
            side = 1 if p.cx > self.cx else -1
            s = Shot("tornado", self.cx - 5 + side * 16, GROUND_Y - 16, 10, 16, side * 0.6, 0, 0.2, 300)
            s.chase = False
            self.g.shots.append(s)
            sounds.sfx(sounds.SPEED)
        if self.timer <= 0:
            self.rest(50, "SO DIZZY!")

    def do_dig(self, p):
        # jump up, then dive into the ground
        if self.on_ground and self.vy >= 0 and self.step == 0 and self.timer < 990:
            self.step = 1
            self.hidden = True
            self.ears_x = self.cx
            self.timer = 160
            self.vx = 0
            self.y = GROUND_Y + 40   # out of the way, under the floor
            self.g.puff(self.ears_x, GROUND_Y, BROWN)
            sounds.sfx(sounds.POOF)

    def dig(self, p):
        """He is under the ground. Only his ears stick out."""
        g = self.g
        if self.step == 1:
            # the ears chase you
            speed = 1.3 if self.angry else 1.0
            self.ears_x += clamp(p.cx - self.ears_x, -speed, speed)
            self.ears_x = clamp(self.ears_x, 20, 236)
            if self.t % 5 == 0:
                g.particles.append(Particle(self.ears_x + random.uniform(-6, 6), GROUND_Y - 1,
                                            random.uniform(-0.6, 0.6), -1.2, 16, BROWN, 2))
            if self.timer <= 0:
                self.step = 2
                self.timer = 55     # the ears shake: get out of the way!
        elif self.step == 2:
            if self.timer <= 0:
                self.hidden = False
                self.x = self.ears_x - self.w / 2
                self.y = GROUND_Y - self.h
                self.vy = -6
                g.puff(self.ears_x, GROUND_Y, BROWN)
                g.shake = 6
                sounds.sfx(sounds.BOOM)
                self.rest(70, "PEEKABOO!")

    def do_tornado(self, p):
        self.face_player()
        if self.every(150):
            self.throw_bomb(clamp((p.cx - self.cx) / 55, -3, 3), -4)
            sounds.sfx(sounds.THROW)
        if self.mini:
            self.mini.update()
            if self.mini.gone:
                self.mini = None
                self.rest(50, "AW, MAN!")

    def catch_bolt(self, b):
        return bool(self.mini) and self.mini.zapped(b)

    def do_garden(self, p):
        if self.t % 4 == 0:
            spout = self.cx + self.facing * 22
            self.g.particles.append(Particle(spout, self.y + 12, self.facing * 0.4, 1.2, 14, SKY, 1))
        if self.timer <= 0:
            self.next_move()

    def draw(self, t):
        if self.mini:
            self.mini.draw(t)
        if self.hidden:
            ex = self.ears_x + (random.uniform(-1.5, 1.5) if self.step == 2 else 0)
            pyxel.elli(ex - 9, GROUND_Y - 4, 18, 6, BROWN)
            pyxel.elli(ex - 5, GROUND_Y - 13, 4, 11, WHITE)
            pyxel.elli(ex + 1, GROUND_Y - 14, 4, 12, WHITE)
            pyxel.rect(ex - 4, GROUND_Y - 11, 2, 6, LPINK)
            pyxel.rect(ex + 2, GROUND_Y - 12, 2, 7, LPINK)
            if self.step == 2 and t % 8 < 4:
                art.text(ex - 2, GROUND_Y - 26, "!", RED)
            return
        if not self.visible(t):
            return
        if self.move == "garden" and self.state == "do":
            art.draw_boom_garden(self.x, self.y, self.facing, t)
            return
        back = -self.facing
        # carrot sack on his back
        sx = self.cx + back * 12 - 7
        pyxel.elli(sx, self.y + 2, 14, 14, BROWN)
        art.draw_carrot(sx + 3, self.y - 4)
        if self.state == "rest":
            pose = "stand"
        elif self.move == "dance" and self.state == "do":
            pose = "jump" if (t // 8) % 2 else "hold"
        else:
            pose = "hold" if self.on_ground else "jump"
        art.draw_bunny(self.x - 1, self.y - 14, self.facing, pose, t // 4,
                       body=WHITE, inner=LPINK, belly=CREAM, eye=RED, cheek=PINK,
                       angry=True, s=2)
        if self.state == "warn":
            self.warn(t)


class Scarecrow(Boss):
    """Bounces on his pole, sends packs of crows, and lobs pumpkins
    that you can pick up and throw back."""
    name = "THE SCARECROW"

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 24, 24, 40)
        self.target = x
        self.calling = 0

    def think(self):
        g = self.g
        self.face_player()
        landed = self.physics()
        if self.on_ground:
            self.vx = 0
        if landed:
            sounds.sfx(sounds.BOUNCE)
            g.puff(self.cx, GROUND_Y, YELLOW)
        if self.on_ground and self.every(45):
            # boing! hop toward a new spot
            if abs(self.target - self.x) < 12 or random.random() < 0.3:
                self.target = random.uniform(40, 190)
            self.vy = -4.5 if not self.angry else -5.5
            self.vx = clamp((self.target - self.x) / 30, -1.8, 1.8)
        if self.every(100):
            n = 2 if self.angry else 1
            for i in range(n):
                pk = Item("pumpkin", self.cx - 6, self.y + 6, state="thrown")
                pk.owner = "boss"
                pk.vx = clamp((g.player.cx - self.cx) / 50, -3.2, 3.2) + (i - (n - 1) / 2) * 1.4
                pk.vy = -4.5
                g.items.append(pk)
            sounds.sfx(sounds.THROW)
            resting = [o for o in g.items if o.kind == "pumpkin" and o.state == "rest"]
            for o in resting[:-3]:
                o.poof(g)
        if self.every(260) and not self.calling:
            self.calling = 40
            g.float_text(self.cx, self.y - 14, "CAW CAW! GET HER, CROWS!", WHITE)
        if self.calling:
            self.calling -= 1
            if self.calling == 0:
                self.send_crows()

    def send_crows(self):
        g = self.g
        n = 5 if self.angry or self.hard else 3
        side = random.choice((-1, 1))
        for i in range(n):
            x = (24 if side < 0 else 220) + side * -i * 16
            c = Pig(x, -12, "crow", 0)
            c.minion = True
            c.awake = True
            c.base_y = 14 + (i % 2) * 10
            c.cool = 20 + i * 14
            g.pigs.append(c)
        sounds.sfx(sounds.SPEED)

    def draw(self, t):
        if self.visible(t):
            art.draw_scarecrow(self.x - 4, self.y - 4, t, not self.on_ground, self.angry)
            if self.calling:
                self.warn(t)


class PinkFireball(Boss):
    """A bullet-hell boss. She fills the sky with fire in pretty math
    patterns, then rests down low. That is when you hit her!"""
    name = "THE PINK FIREBALL"
    PATTERNS = ["spiral", "waves", "rings"]
    SHOUTS = {"spiral": "SPIRAL!", "waves": "SINE WAVES!", "rings": "RING OF FIRE!"}

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 18, 20, 20)
        self.y = 50
        self.state = "warn"
        self.timer = 40
        self.n = 0
        self.a = 0.0
        self.shots_made = 0

    @property
    def pattern(self):
        return self.PATTERNS[self.n % len(self.PATTERNS)]

    def orb(self, angle, speed, wave=0.0, wave_f=0.15, curve=0.0, col=HOTPINK):
        s = Shot("orb", self.cx - 2, self.y + self.h / 2 - 2, 4, 4,
                 math.cos(angle) * speed, math.sin(angle) * speed, 0, 500)
        s.bx, s.by = s.x, s.y
        s.wave, s.wave_f, s.curve, s.col = wave, wave_f, curve, col
        self.g.shots.append(s)

    def think(self):
        g = self.g
        self.face_player()
        self.timer -= 1
        t = self.t
        if self.state == "rest":
            tx, ty = 118, GROUND_Y - 46 + math.sin(t * 0.05) * 4
        elif self.pattern == "waves":
            # she stays in the middle, so you can always run around her waves
            tx, ty = 118, 40
        else:
            tx = 118 + math.sin(t * 0.013) * 85
            ty = 46 + math.sin(t * 0.027) * 20
        self.x += (tx - self.x) * 0.04
        self.y += (ty - self.y) * 0.04
        if self.t % 3 == 0:
            g.particles.append(Particle(self.cx + random.uniform(-6, 6), self.y + self.h,
                                        0, 0.6, 14, random.choice([PINK, HOTPINK, LPINK]), 2))
        if self.state == "warn":
            if self.timer <= 0:
                self.state = "fire"
                self.timer = 220 if self.angry else 180
                g.float_text(self.cx, self.y - 14, self.SHOUTS[self.pattern], HOTPINK)
            return
        if self.state == "rest":
            if self.timer <= 0:
                self.n += 1
                self.state = "warn"
                self.timer = 40
            return
        if self.timer <= 0:
            self.state = "rest"
            self.timer = 110 if self.angry else 140
            g.float_text(self.cx, self.y - 14, "PANT... PANT...", LPINK)
            return
        self.fire()

    def fire(self):
        p = self.g.player
        f = self.fury
        pat = self.pattern
        aim = math.atan2(p.y + p.h / 2 - (self.y + self.h / 2), p.cx - self.cx)
        if pat == "spiral" and self.t % max(8, int(11 / f)) == 0:
            # a slow sprinkler with two arms. Walk along with the gap!
            for k in range(2):
                self.orb(self.a + k * math.pi, 1.0)
            self.a += 0.22
        elif pat == "waves" and self.t % max(16, int(24 / f)) == 0:
            # two wiggly lines on each side of you. Stand still in the gap!
            for off in (-0.45, 0.45):
                self.orb(aim + off, 1.2, wave=7, wave_f=0.14, col=PURPLE)
        elif pat == "rings" and self.t % max(45, int(60 / f)) == 0:
            # a ring with a big hole where you stand. Stay in the hole!
            n = 10
            for k in range(n):
                a = aim + math.pi / n + k * math.tau / n
                if abs(math.remainder(a - aim, math.tau)) > 0.6:
                    self.orb(a, 1.0, col=PINK)
        else:
            return
        if self.t % 12 == 0:
            sounds.sfx(sounds.ZAP)

    def draw(self, t):
        if self.visible(t):
            art.draw_pink_fireball(self.x - 2, self.y - 2, t, self.angry, self.state == "rest")
            if self.state == "warn":
                self.warn(t)


class MoonBunny(Boss):
    """The Moon Bunny from Bunny Madness!
    1. She hides behind spinning moon rocks. Zap the rocks when she swoops low.
    2. She turns invisible and hops. Watch her shadow and throw things at her.
    3. She puts on a moon rock helmet and charges. Jump on her head!"""
    name = "THE MOON BUNNY"
    beaten_msg = ("THE MOON BUNNY GIVES UP!", "SHE ONLY WANTED TO PLAY!")
    ROCKS = 4
    BONKS = 3
    HEAD_HITS = 2

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, self.ROCKS + self.BONKS + self.HEAD_HITS, 22, 26)
        self.x, self.y = 195, 14
        self.phase = 0
        self.spin = 0.0
        self.shield = list(range(self.ROCKS))
        self.timer = 70
        self.vx = -0.9
        self.seen = 0
        self.clang = 0
        self.drops = 0
        self.low = 0       # phase 1: frames left in a low swoop
        self.hop = 0.0     # phase 2: where she is in her hop

    def rock_pos(self, i):
        a = self.spin + i * math.tau / self.ROCKS
        return self.cx + math.cos(a) * 26, self.y + 13 + math.sin(a) * 26

    def say(self, msg, c=WHITE):
        if self.clang == 0:
            self.clang = 60
            self.g.float_text(self.cx, self.y - 22, msg, c)

    def catch_bolt(self, b):
        g = self.g
        if self.phase == 1:
            for i in list(self.shield):
                rx, ry = self.rock_pos(i)
                if b.x - 4 < rx < b.x + b.w + 4 and b.y - 4 < ry < b.y + b.h + 4:
                    self.shield.remove(i)
                    self.hp -= 1
                    for _ in range(10):
                        g.sparkle(rx, ry, random.choice([LAV, SKY, WHITE]))
                    sounds.sfx(sounds.BOSS_HIT)
                    if self.shield:
                        g.float_text(rx, ry - 8, f"CRACK! {len(self.shield)} MORE!", SKY)
                    else:
                        self.phase = 2
                        self.flash = 45
                        self.timer = 90
                        g.banner("POOF! SHE VANISHED!", "WATCH HER SHADOW! THROW THINGS AT HER!", 120)
                    return True
        if self.phase == 2 and overlap(b, self):
            self.seen = 50
            self.say("THERE SHE IS!", SKY)
            return True
        return False

    def hit(self, dmg, how, obj=None):
        g = self.g
        if self.flash or self.phase == 0 or self.dead:
            return False
        if self.phase == 1:
            self.say("CLANG! ZAP HER MOON ROCKS!")
            return False
        if self.phase == 2:
            if how not in ("throw", "boom"):
                return False
            self.hp -= 1
            self.flash = 45
            self.seen = 45
            self.hop = 0.0
            self.vx = -self.vx
            sounds.sfx(sounds.BOSS_HIT)
            if self.hp > self.HEAD_HITS:
                g.float_text(self.cx, self.y - 20, f"BONK! {self.hp - self.HEAD_HITS} MORE!", WHITE)
            else:
                self.phase = 3
                self.flash = 50
                self.timer = 40
                self.vx = 2.5 if g.player.cx < self.cx else -2.5
                g.banner("A MOON ROCK HELMET!", "JUMP ON HER HEAD!", 120)
            return True
        # phase 3: only hits from above count
        from_above = how == "stomp" or (obj is not None and obj.vy > 0
                                         and obj.y + obj.h < self.y + 10)
        if not from_above:
            self.say("CLANG! HIT HER FROM ABOVE!")
            return False
        self.hp -= 1
        self.flash = 50
        sounds.sfx(sounds.BOSS_HIT)
        if self.hp <= 0:
            self.dead = True
            g.boss_defeated(self)
        else:
            g.float_text(self.cx, self.y - 20, f"BONK! {self.hp} MORE!", WHITE)
        return True

    def stomped(self):
        self.hit(1, "stomp")

    def think(self):
        g = self.g
        p = g.player
        self.spin += 0.045 * self.fury
        if self.seen:
            self.seen -= 1
        if self.clang:
            self.clang -= 1
        self.face_player()
        if self.phase == 0:
            # she climbs out of the cracked moon
            self.y += 0.5
            self.x += (150 - self.x) * 0.01
            if self.y >= 32:
                self.phase = 1
                self.timer = 70
                g.banner("THE MOON BUNNY!", "ZAP HER MOON ROCKS WHEN SHE COMES DOWN!", 120)
            return
        if self.phase == 1:
            # She floats high and drops rocks. Then she swoops low,
            # so her moon rocks come down where your zaps can reach them.
            self.x += self.vx
            if self.x < 12 or self.x > 222:
                self.vx = -self.vx
                self.x = clamp(self.x, 12, 222)
            self.x += clamp((p.cx - self.cx) * 0.02, -0.9, 0.9)
            if self.low:
                self.low -= 1
                home = 84
                if self.low == 1:
                    self.timer = 60
            else:
                home = 32 + math.sin(self.t / 24) * 9
            self.y += (home - self.y) * 0.06
            self.timer -= 1
            if self.timer <= 0 and not self.low:
                self.timer = int(75 / self.fury)
                self.drops += 1
                if self.drops % 3 == 0:
                    self.low = 170
                    self.say("ZAP HER ROCKS NOW!", YELLOW)
                else:
                    aim = clamp((p.cx - self.cx) * 0.02, -1.2, 1.2)
                    g.shots.append(Shot("rock", self.cx - 3, self.y + 26, 6, 6, aim, 0, 0.27, 300))
                    sounds.sfx(sounds.THROW)
        elif self.phase == 2:
            # Invisible hops along the ground. Her shadow shows where she is.
            self.x += self.vx * 0.8
            if self.x < 12 or self.x > 222:
                self.vx = -self.vx
                self.x = clamp(self.x, 12, 222)
            self.x += clamp((p.cx - self.cx) * 0.01, -0.5, 0.5)
            self.hop += 0.035 * self.fury
            floor = GROUND_Y - self.h
            self.y = floor - abs(math.sin(self.hop)) * 46
            self.timer -= 1
            if self.timer <= 0 and math.cos(self.hop) * math.sin(self.hop) < 0:
                self.timer = int(110 / self.fury)
                aim = clamp((p.cx - self.cx) * 0.02, -1.2, 1.2)
                g.shots.append(Shot("rock", self.cx - 3, self.y, 6, 6, aim, -1.5, 0.27, 300))
                sounds.sfx(sounds.THROW)
        else:
            floor = GROUND_Y - self.h
            self.y = min(self.y + 2, floor)
            self.timer -= 1
            if self.y >= floor and self.timer <= 0:
                self.x += self.vx * (1.2 if self.hard else 1)
                if self.x < 10 or self.x > 224:
                    self.x = clamp(self.x, 10, 224)
                    self.vx = -self.vx
                    self.timer = 30
                    sounds.sfx(sounds.BOUNCE)
                    g.puff(self.cx, GROUND_Y, LAV)

    def draw(self, t):
        g = self.g
        if self.phase == 0:
            # the moon cracks open!
            pyxel.circ(206, 30, 11, CREAM)
            pyxel.line(200, 22, 205, 30, DGRAY)
            pyxel.line(205, 30, 202, 37, DGRAY)
            pyxel.line(205, 30, 213, 27, DGRAY)
        if self.phase in (1, 2):
            pyxel.elli(self.cx - 11, GROUND_Y - 2, 22, 5, BLACK)
        shimmer = t % 90 < 5
        seen = self.phase != 2 or self.seen > 0 or self.flash > 0 or shimmer
        if seen and self.visible(t):
            if self.phase == 2 and shimmer and not self.seen:
                pyxel.dither(0.4)
            pyxel.circb(self.cx, self.y + 13, 20 + (t // 6) % 3, BLUE if self.phase == 2 else SKY)
            art.draw_moon_bunny(self.x - 5, self.y - 4, self.facing)
            if self.phase == 3:
                hx, hy = self.x, self.y - 1
                pyxel.rect(hx, hy, 22, 6, LAV)
                pyxel.rectb(hx, hy, 22, 6, SKY)
                pyxel.pset(hx + 4, hy + 2, WHITE)
                if g.player.y + g.player.h <= self.y + 4:
                    pyxel.circb(self.cx, hy + 3, 9 + (t // 4) % 3, YELLOW)
            pyxel.dither(1.0)
        for i in self.shield if self.phase >= 1 else []:
            rx, ry = self.rock_pos(i)
            pyxel.circ(rx, ry, 4, LAV)
            pyxel.circb(rx, ry, 4, SKY)
            pyxel.pset(rx - 1, ry - 1, WHITE)


def make(kind, g, hard, twin=False):
    if kind == "moneycat":
        return MoneyCat(g, 190, hard)
    if kind == "eggbert":
        return Eggbert(g, 200, hard)
    if kind == "blackbunny":
        return BlackBunny(g, 140 if twin else 190, hard, twin)
    if kind == "tornado":
        return TornadoBunny(g, 100 if twin else 160, hard, twin)
    if kind == "scarecrow":
        return Scarecrow(g, 180, hard)
    if kind == "pinkfire":
        return PinkFireball(g, 150, hard)
    if kind == "moonbunny":
        return MoonBunny(g, 195, hard)
    return CarrotBoom(g, 190, hard)
