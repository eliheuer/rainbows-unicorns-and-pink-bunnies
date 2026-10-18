# The bosses. One waits at the end of every 8th level.
import math
import random

import pyxel

import art
import sounds
from consts import *
from entities import Item, Particle, Pig, Shot

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
    PATTERNS = ["spiral", "waves", "rings", "flower"]
    SHOUTS = {"spiral": "SPIRAL!", "waves": "SINE WAVES!", "rings": "RING OF FIRE!",
              "flower": "FIRE FLOWER!"}

    def __init__(self, g, x, hard):
        super().__init__(g, x, hard, 22, 20, 20)
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
                self.timer = 260 if self.angry else 220
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
            self.timer = 80 if self.angry else 110
            g.float_text(self.cx, self.y - 14, "PANT... PANT...", LPINK)
            return
        self.fire()

    def fire(self):
        p = self.g.player
        f = self.fury
        pat = self.pattern
        aim = math.atan2(p.y + p.h / 2 - (self.y + self.h / 2), p.cx - self.cx)
        if pat == "spiral" and self.t % max(3, int(6 / f)) == 0:
            arms = 3 if self.angry else 2
            for k in range(arms):
                self.orb(self.a + k * math.tau / arms, 1.2)
            self.a += 0.31
        elif pat == "waves" and self.t % max(8, int(16 / f)) == 0:
            spread = (-0.4, 0, 0.4) if self.angry or self.hard else (-0.25, 0.25)
            for off in spread:
                self.orb(aim + off, 1.3, wave=12, wave_f=0.14, col=PURPLE)
        elif pat == "rings" and self.t % max(24, int(46 / f)) == 0:
            n = 16 if self.angry else 12
            self.shots_made += 1
            off = (self.shots_made % 2) * math.pi / n
            for k in range(n):
                self.orb(off + k * math.tau / n, 1.1, col=PINK)
        elif pat == "flower" and self.t % max(4, int(7 / f)) == 0:
            turn = 1 if (self.t // 60) % 2 else -1
            self.orb(self.a, 1.15, curve=0.016 * turn, col=LPINK)
            self.orb(self.a + math.pi, 1.15, curve=0.016 * turn, col=LPINK)
            self.a += 0.5
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
    1. She hides behind spinning moon rocks. Zap the rocks.
    2. She turns invisible. Watch her shadow and throw things at her.
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
            self.y = max(18, self.y - 22)
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
                g.banner("THE MOON BUNNY!", "ZAP HER MOON ROCKS WITH LIGHTNING!", 120)
            return
        if self.phase in (1, 2):
            self.x += self.vx
            if self.x < 12 or self.x > 222:
                self.vx = -self.vx
                self.x = clamp(self.x, 12, 222)
            chase = 0.03 if self.phase == 2 else 0.02
            self.x += clamp((p.cx - self.cx) * chase, -0.9, 0.9)
            home = 32 if self.phase == 1 else 70
            self.y += (home + math.sin(self.t / 24) * 9 - self.y) * 0.06
            self.timer -= 1
            if self.timer <= 0:
                self.timer = int((75 if self.phase == 1 else 95) / self.fury)
                aim = clamp((p.cx - self.cx) * 0.02, -1.2, 1.2)
                g.shots.append(Shot("rock", self.cx - 3, self.y + 26, 6, 6, aim, 0, 0.27, 300))
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
