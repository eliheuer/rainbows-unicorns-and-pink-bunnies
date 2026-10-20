# The last fights: the Pink Bunny Mech against the Carrot Mech, and then
# against the Carrot Mech and the Tornado Bunny Mech together.
# You see the fight from inside the cockpit, like the robot fights in
# Mystical Ninja for the Nintendo 64.
#
#   Left / Right   step to another lane, to dodge
#   Z or Space     punch (only reaches a mech that is close)
#   X              lightning beam (uses ZAP power, which comes back)
#
# Every attack shows "!" and red marks on the ground first.
# You can hurt a mech only when it is stuck or dizzy.
import math
import random

import pyxel

import art
import controls as C
import sounds
from consts import *

HORIZON = 64      # where the ground meets the sky on the screen
F = 60            # how big things look (the camera lens)
CAM_H = 3         # how high the cockpit is above the ground
LANE = 3          # how wide one lane is
NEAR, FAR = 5.0, 7.5

# TRY CHANGING THESE NUMBERS!
ARMOR = 8         # how many hits the Pink Bunny Mech can take
CARROT_HP = 48    # the Carrot Mech's health when it fights alone
TEAM_HP = 30      # each mech's health when the two fight together
PUNCH = 3         # damage of one punch
ZAP = 1           # damage of one lightning beam
ZAP_COST = 25     # ZAP power one beam uses (you have 100)
SUPPORT = 180     # with two mechs, how often the waiting one shoots at you


def sx(wx, z, cam):
    """Where a spot in the world shows up on the screen, left to right."""
    return 128 + (wx - cam) * F / z


def sy(h, z):
    """Where a spot h units above the ground shows up, top to bottom."""
    return HORIZON + (CAM_H - h) * F / z


# ---------------------------------------------------------------- the enemy mechs

class Mech:
    """One enemy mech. Each kind of mech adds its own moves."""
    name = ""
    color = WHITE
    MOVES = []
    SHOUTS = {}

    def __init__(self, fight, hp, lane):
        self.fight = fight
        self.hp = self.max_hp = hp
        self.ex = self.target = lane * LANE
        self.ez = FAR
        self.ey = 0.0          # how high it is off the ground
        self.phase = "walk"    # walk, warn, or the name of a move
        self.ptimer = 100
        self.step = ""         # where it is inside a move
        self.strike = 0        # the lane its attack will hit
        self.pose = "stand"
        self.flash = 0
        self.waves = 0
        self.move_n = 0
        self.danger = []       # lanes that are about to get hit
        self.dead = False
        self.fall = 0

    @property
    def angry(self):
        return self.hp <= self.max_hp // 2

    @property
    def fury(self):
        return 1.3 if self.angry else 1.0

    @property
    def move(self):
        return self.MOVES[self.move_n % len(self.MOVES)]

    @property
    def open(self):
        """True when it is stuck or dizzy, and you can hurt it."""
        return self.step in ("stuck", "dizzy")

    @property
    def lane(self):
        return round(self.ex / LANE)

    def say(self, words, c=WHITE, y=40):
        self.fight.say(words, c, y)

    def update(self):
        f = self.fight
        if self.flash:
            self.flash -= 1
        if self.dead:
            self.fall += 1
            if self.fall % 8 == 0 and self.fall < 100:
                f.boom(sx(self.ex, self.ez, f.cam) + random.uniform(-25, 25),
                       sy(4, self.ez) + random.uniform(-25, 25))
                sounds.sfx(sounds.BOOM)
            return
        self.ptimer -= 1
        self.ex += (self.target - self.ex) * 0.06
        if self.phase == "walk":
            self.pose = "stand"
            # with two mechs, the one that waits stays back, out of the other one's lane
            waiting = f.turn is not self and len(f.alive) > 1
            self.ez += (FAR + (3 if waiting else 0) - self.ez) * 0.04
            self.ey += (0 - self.ey) * 0.1
            taken = [round(m.target / LANE) for m in f.alive if m is not self]
            if f.t % 70 == 0 or round(self.target / LANE) in taken:
                self.target = random.choice([l for l in (-1, 0, 1) if l not in taken]) * LANE
            if self.ptimer <= 0 and f.turn is self:
                self.phase, self.ptimer = "warn", 50
                self.say(self.SHOUTS[self.move], self.color)
            elif f.turn is not self and f.t % SUPPORT == 0 and f.turn.phase != "bombs":
                # while the other mech attacks, this one helps with one shot
                f.shots.append([self.SHOT, self.ex, self.ez - 0.5, f.lane * LANE])
                sounds.sfx(sounds.THROW)
        elif self.phase == "warn":
            if self.ptimer <= 0:
                self.phase = self.move
                self.start()
        else:
            getattr(self, "do_" + self.move)()

    def done(self, rest=60):
        self.move_n += 1
        self.step = ""
        self.phase = "walk"
        self.ptimer = rest
        self.pose = "stand"
        self.danger = []
        self.fight.next_turn(self)

    def hit(self, dmg, words):
        f = self.fight
        if self.flash:
            return
        if not self.open:
            self.flash = 8
            sounds.sfx(sounds.NOPE)
            self.say("CLANG! WAIT TILL IT IS STUCK OR DIZZY!", LGRAY, 50)
            return
        was_angry = self.angry
        self.hp -= dmg
        self.flash = 12
        f.shake = 4
        sounds.sfx(sounds.BOSS_HIT)
        f.boom(sx(self.ex, self.ez, f.cam), sy(5, self.ez), 8, (WHITE, YELLOW))
        self.say(words, YELLOW, 50)
        if self.hp <= 0:
            self.dead = True
            self.danger = []
            self.say(f"THE {self.name} IS DOWN!", self.color, 30)
            f.next_turn(self)
        elif self.angry and not was_angry:
            self.say(f"THE {self.name} IS ANGRY!", RED, 30)


class CarrotMech(Mech):
    name = "CARROT MECH"
    color = ORANGE
    SHOT = "missile"
    MOVES = ["missiles", "drill", "bombs", "charge"]
    SHOUTS = {"missiles": "CARROT MISSILES!", "drill": "DRILL PUNCH!",
              "bombs": "BOMB RAIN!", "charge": "MECH CHARGE!"}

    def start(self):
        m = self.move
        if m == "missiles":
            self.waves = 5 if self.angry else 4
            self.ptimer = 40
        elif m == "bombs":
            self.waves = 3 if self.angry else 2
            self.new_bombs()
        else:
            self.step = "go" if m == "drill" else "back"
            self.ptimer = 999

    def do_missiles(self):
        f = self.fight
        self.ez += (FAR - self.ez) * 0.04
        if self.ptimer <= 0:
            if self.waves <= 0:
                self.done()
                return
            self.waves -= 1
            self.ptimer = int(58 / self.fury)
            f.shots.append(["missile", self.ex, self.ez - 0.5, f.lane * LANE])
            sounds.sfx(sounds.THROW)

    def do_drill(self):
        f = self.fight
        if self.step == "go":
            # walk up close, in front of you
            self.target = f.lane * LANE
            self.ez += (NEAR - self.ez) * 0.06
            if self.ez < NEAR + 0.3:
                self.step, self.ptimer = "windup", int(56 / self.fury)
                self.strike = f.lane
                self.target = self.strike * LANE
                self.danger = [self.strike]
                self.pose = "windup"
        elif self.step == "windup":
            if self.ptimer <= 0:
                self.step, self.ptimer = "stuck", 100
                self.pose = "stuck"
                f.shake = 10
                sounds.sfx(sounds.BOOM)
                self.danger = []
                if f.lane == self.strike:
                    f.ouch()
                self.say("ITS DRILL IS STUCK! PUNCH!", YELLOW, 60)
        elif self.step == "stuck":
            if self.ptimer <= 0:
                self.done()

    def new_bombs(self):
        safe = random.choice([-1, 0, 1])
        self.danger = [l for l in (-1, 0, 1) if l != safe]
        self.ptimer = int(66 / self.fury)
        self.bomb_time = self.ptimer
        sounds.sfx(sounds.THROW)

    def do_bombs(self):
        f = self.fight
        self.ez += (FAR - self.ez) * 0.04
        if self.ptimer <= 0:
            for l in self.danger:
                f.boom(sx(l * LANE, 1.8, f.cam), sy(0, 1.8), 20)
            sounds.sfx(sounds.BOOM)
            f.shake = 8
            if f.lane in self.danger:
                f.ouch()
            self.waves -= 1
            if self.waves > 0:
                self.new_bombs()
            else:
                self.done()

    def do_charge(self):
        f = self.fight
        if self.step == "back":
            self.ez += (11 - self.ez) * 0.05
            if self.ez > 10.5:
                self.step, self.ptimer = "roar", 40
                self.strike = f.lane
                self.target = self.strike * LANE
                self.danger = [self.strike]
                self.say("ROOOAAR!", RED, 30)
        elif self.step == "roar":
            if self.ptimer <= 0:
                self.step = "run"
                sounds.sfx(sounds.SPEED)
        elif self.step == "run":
            self.ez -= 0.15 * self.fury
            if self.angry and self.ez > 8:
                # when it is angry, it turns to follow you at the start of the run
                self.strike = f.lane
                self.target = self.strike * LANE
                self.danger = [self.strike]
            if f.t % 10 == 0:
                f.shake = 3
            if self.ez < 3.2:
                self.danger = []
                if f.lane == self.strike:
                    # it hit you, so it walks back, happy
                    f.ouch()
                    self.done()
                    return
                self.say("WHOA! IT IS DIZZY! PUNCH!", YELLOW, 60)
                self.ez = max(self.ez, 3.6)
                self.step, self.ptimer = "dizzy", 110
                self.pose = "dizzy"
        elif self.step == "dizzy":
            self.ez += (NEAR - self.ez) * 0.05
            if self.ptimer <= 0:
                self.done()

    def draw(self, t, f):
        pose = "dizzy" if self.dead else self.pose
        art.draw_carrot_mech(sx(self.ex, self.ez, f.cam), sy(self.ey, self.ez), F / self.ez / 6.5,
                             t, pose, self.angry, self.flash > 0 and t % 4 < 2)


class TornadoMech(Mech):
    name = "TORNADO MECH"
    color = HOTPINK
    SHOT = "tornado"
    MOVES = ["spin", "slam"]
    SHOUTS = {"spin": "TORNADO SPIN!", "slam": "SKY SLAM!"}

    def start(self):
        if self.move == "spin":
            self.waves = 4 if self.angry else 3
            self.ptimer = 30
        else:
            self.step = "up"
            self.ptimer = 999

    def do_spin(self):
        # it spins and sends tornadoes that follow your lane
        f = self.fight
        self.pose = "spin"
        self.ez += (FAR - self.ez) * 0.04
        if self.ptimer <= 0:
            if self.waves <= 0:
                self.done()
                return
            self.waves -= 1
            self.ptimer = int(60 / self.fury)
            f.shots.append(["tornado", self.ex, self.ez - 0.5, f.lane * LANE])
            sounds.sfx(sounds.SPEED)

    def do_slam(self):
        # it flies up out of sight, then falls down on your lane
        f = self.fight
        if self.step == "up":
            self.ey += 0.5
            if self.ey > 14:
                self.step, self.ptimer = "aim", int(60 / self.fury)
                self.ez = NEAR
                self.strike = f.lane
                self.ex = self.target = self.strike * LANE
                self.danger = [self.strike]
        elif self.step == "aim":
            if self.ptimer <= 0:
                self.step = "down"
        elif self.step == "down":
            self.ey -= 1.4
            if self.ey <= 0:
                self.ey = 0
                f.shake = 12
                sounds.sfx(sounds.BOOM)
                f.boom(sx(self.ex, self.ez, f.cam), sy(0, self.ez), 24, (WHITE, LGRAY, LAV))
                self.danger = []
                if f.lane == self.strike:
                    f.ouch()
                self.say("IT IS DIZZY! PUNCH!", YELLOW, 60)
                self.step, self.ptimer = "dizzy", 110
                self.pose = "dizzy"
        elif self.step == "dizzy":
            if self.ptimer <= 0:
                self.done()

    def draw(self, t, f):
        if self.step == "aim":
            # its shadow on the ground shows where it will land
            x = sx(self.ex, self.ez, f.cam)
            r = 24 * (1.2 - self.ptimer / 60)
            pyxel.elli(x - r, sy(0, self.ez) - 4, r * 2, 8, BLACK)
        pose = "dizzy" if self.dead else self.pose
        art.draw_tornado_mech(sx(self.ex, self.ez, f.cam), sy(self.ey, self.ez), F / self.ez / 6.5,
                              t, pose, self.angry, self.flash > 0 and t % 4 < 2)


# ---------------------------------------------------------------- the fight

class MechFight:
    def __init__(self, app, layer=2):
        self.app = app
        self.layer = layer     # 2: the Carrot Mech alone. 3: both mechs together.
        self.t = 0
        self.state = "ready"
        self.timer = 170
        # you
        self.lane = 0
        self.cam = 0.0
        self.armor = ARMOR
        self.power = 100.0
        self.hurt = 0
        self.punch = 0
        self.fist = 0          # which fist punches next
        self.beam = 0
        self.beam_x = 0.0
        self.beam_z = FAR
        # them
        if layer == 2:
            self.enemies = [CarrotMech(self, CARROT_HP, 0)]
        else:
            self.enemies = [CarrotMech(self, TEAM_HP, -1), TornadoMech(self, TEAM_HP, 1)]
            self.enemies[1].ptimer = 200
        self.turn = self.enemies[0]
        self.shots = []        # [kind, x, z, lane x it goes to]
        self.parts = []        # [x, y, vx, vy, life, color]
        self.texts = []        # [x, y, words, color, life]
        self.shake = 0
        self.bolt = 0          # lightning in the sky
        sounds.music(sounds.MUSIC_FINAL)

    @property
    def alive(self):
        return [m for m in self.enemies if not m.dead]

    @property
    def danger(self):
        return [l for m in self.alive for l in m.danger]

    def next_turn(self, after):
        i = self.enemies.index(after)
        for k in range(1, len(self.enemies) + 1):
            m = self.enemies[(i + k) % len(self.enemies)]
            if not m.dead:
                self.turn = m
                return

    def say(self, words, c=WHITE, y=40):
        self.texts.append([128, y, words, c, 70])

    def boom(self, x, y, n=16, colors=(RED, ORANGE, YELLOW, WHITE)):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.5, 3)
            self.parts.append([x, y, math.cos(a) * v, math.sin(a) * v, 24, random.choice(colors)])

    def ouch(self):
        if self.hurt:
            return
        self.armor -= 1
        self.hurt = 60
        self.shake = 12
        sounds.sfx(sounds.HURT)

    # ------------------------------------------------------------ update

    def update(self):
        self.t += 1
        if self.state == "pause":
            if C.pressed("start"):
                self.state = "fight"
            elif C.pressed("back"):
                sounds.music(None)
                self.app.to_select(LEVEL_COUNT)
            return
        if self.state == "fight" and (C.pressed("start") or C.pressed("back")):
            self.state = "pause"
            return
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.08
            p[4] -= 1
        self.parts = [p for p in self.parts if p[4] > 0]
        for tx in self.texts:
            tx[1] -= 0.3
            tx[4] -= 1
        self.texts = [tx for tx in self.texts if tx[4] > 0]
        for k in ("shake", "hurt", "punch", "beam", "bolt"):
            if getattr(self, k) > 0:
                setattr(self, k, getattr(self, k) - 1)
        if random.random() < 0.004:
            self.bolt = 8
        self.cam += (self.lane * LANE - self.cam) * 0.25

        if self.state == "ready":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "fight"
            return
        if self.state in ("won", "lost"):
            self.timer += 1
            for m in self.enemies:
                m.update()
            if self.timer > 120 and C.ok():
                if self.state == "lost":
                    self.app.to_mech(self.layer)
                elif self.layer == 2:
                    self.app.to_mech_intro2()
                else:
                    self.app.mech_won()
            return
        self.player()
        for m in self.enemies:
            m.update()
        self.fly_shots()
        if not self.alive:
            self.state, self.timer = "won", 0
            self.shots.clear()
            sounds.music(None)
            sounds.sfx(sounds.CLEAR)
        elif self.armor <= 0:
            self.state, self.timer = "lost", 0
            sounds.music(None)

    def in_my_lane(self):
        """The mechs in your lane, nearest first."""
        mine = [m for m in self.alive if abs(m.ex - self.cam) < 2]
        return sorted(mine, key=lambda m: m.ez)

    def player(self):
        if C.pressed("left") and self.lane > -1:
            self.lane -= 1
            sounds.sfx(sounds.JUMP)
        if C.pressed("right") and self.lane < 1:
            self.lane += 1
            sounds.sfx(sounds.JUMP)
        self.power = min(100.0, self.power + 0.45)
        if C.pressed("jump") and self.punch == 0:
            self.punch = 18
            self.fist = 1 - self.fist
            sounds.sfx(sounds.THROW)
            close = [m for m in self.in_my_lane() if m.ez < NEAR + 1 and m.ey < 2]
            if close:
                close[0].hit(PUNCH, "POW!")
        if C.pressed("zap"):
            if self.power >= ZAP_COST:
                self.power -= ZAP_COST
                self.beam = 12
                self.beam_x = self.cam
                self.beam_z = FAR
                sounds.sfx(sounds.ZAP)
                mine = [s for s in self.shots if abs(s[1] - self.cam) < 1.5]
                targets = self.in_my_lane()
                if mine:
                    s = min(mine, key=lambda s: s[2])
                    self.shots.remove(s)
                    self.beam_z = s[2]
                    self.boom(sx(s[1], s[2], self.cam), sy(3 if s[0] == "missile" else 1, s[2]), 10)
                    sounds.sfx(sounds.POOF)
                elif targets:
                    self.beam_z = targets[0].ez
                    targets[0].hit(ZAP, "ZAP!")
            else:
                sounds.sfx(sounds.NOPE)

    def fly_shots(self):
        for s in self.shots:
            s[2] -= 0.075 if s[0] == "missile" else 0.06
            # it moves over to the lane it aims at
            s[1] += (s[3] - s[1]) * 0.04
        for s in [s for s in self.shots if s[2] < 0.9]:
            self.shots.remove(s)
            if abs(s[1] - self.cam) < 1.5:
                self.ouch()
                self.boom(128, 110, 20)
                sounds.sfx(sounds.BOOM)

    # ------------------------------------------------------------ draw

    def draw(self):
        t = self.t
        ox = random.randint(-2, 2) if self.shake else 0
        oy = random.randint(-2, 2) if self.shake else 0
        pyxel.camera(ox, oy)
        self.draw_world(t)
        self.draw_danger(t)
        for m in sorted(self.enemies, key=lambda m: -m.ez):
            if not m.dead or m.fall < 100:
                m.draw(t, self)
        for s in sorted(self.shots, key=lambda s: -s[2]):
            if s[0] == "missile":
                self.draw_missile(sx(s[1], s[2], self.cam), sy(3, s[2]), F / s[2], t)
            else:
                k = F / s[2] / 6.5
                art.draw_tornado(sx(s[1], s[2], self.cam) - 8 * k, sy(0, s[2]) - 22 * k,
                                 16 * k, 22 * k, t)
        for m in self.alive:
            if m.step in ("windup", "aim") and t % 8 < 4:
                art.big_center(20, "!", RED, 3)
        if self.beam:
            x2, y2 = sx(self.beam_x, self.beam_z, self.cam), sy(4, self.beam_z)
            for k in (-1, 0, 1):
                pyxel.line(128 + k, 120, x2 + random.randint(-3, 3), y2, YELLOW if k else WHITE)
        for x, y, vx, vy, life, c in self.parts:
            pyxel.rect(x, y, 2, 2, c)
        self.draw_fists(t)
        pyxel.camera()
        self.draw_cockpit(t)
        for x, y, words, c, life in self.texts:
            art.center_text(y, words, c, cx=x)
        self.draw_overlay(t)

    def draw_world(self, t):
        pyxel.cls(NAVY if not self.bolt else LAV)
        pyxel.rect(0, 30, W, 20, DPURPLE)
        pyxel.rect(0, 50, W, HORIZON - 50, PLUM)
        pyxel.circ(200 - self.cam * 2, 26, 10, CREAM)
        if self.bolt:
            x = 60 + (self.t * 37) % 140
            pyxel.line(x, 10, x - 8, 26, WHITE)
            pyxel.line(x - 8, 26, x + 4, 40, WHITE)
        # the farm and the silo far away
        for i in range(9):
            bx = i * 34 - 20 - self.cam * 3
            h = 10 + (i * 7) % 14
            pyxel.rect(bx, HORIZON - h, 22, h, BLACK)
            pyxel.rect(bx + 5, HORIZON - h + 4, 3, 3, ORANGE if (i + t // 40) % 3 else BLACK)
        pyxel.rect(0, HORIZON, W, H - HORIZON, DBROWN)
        for z in (1.5, 2, 3, 4.5, 7, 11):
            pyxel.line(0, sy(0, z), W, sy(0, z), BROWN)
        for k in (-1.5, 1.5, -4.5, 4.5):
            pyxel.line(sx(k, 1, self.cam), sy(0, 1), sx(k, 30, self.cam), sy(0, 30), BROWN)

    def draw_danger(self, t):
        if not self.danger or t % 10 >= 6:
            return
        for l in set(self.danger):
            x = l * LANE
            near, far = 1.2, 12
            pts = [(sx(x - 1.4, near, self.cam), sy(0, near)), (sx(x + 1.4, near, self.cam), sy(0, near)),
                   (sx(x + 1.4, far, self.cam), sy(0, far)), (sx(x - 1.4, far, self.cam), sy(0, far))]
            pyxel.tri(*pts[0], *pts[1], *pts[2], RED)
            pyxel.tri(*pts[0], *pts[2], *pts[3], RED)
        for m in self.alive:
            if m.phase == "bombs":
                # bombs fall from the sky
                grow = 1 - m.ptimer / m.bomb_time
                for l in m.danger:
                    art.draw_carrot(sx(l * LANE, 1.8, self.cam) - 4, 10 + grow * 70, 2)

    def draw_missile(self, x, y, s, t):
        r = max(2, s * 0.35)
        pyxel.circ(x, y, r + 1, YELLOW if t % 4 < 2 else ORANGE)
        pyxel.circ(x, y, r, ORANGE)
        for k in range(5):
            a = k * math.tau / 5 + t * 0.2
            pyxel.line(x + math.cos(a) * r * 0.4, y + math.sin(a) * r * 0.4,
                       x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, BROWN)
        pyxel.circ(x, y, max(1, r * 0.25), GREEN)

    def draw_fists(self, t):
        for side in (-1, 1):
            punching = self.punch and (side > 0) == (self.fist == 1)
            k = self.punch / 18 if punching else 0
            reach = math.sin(k * math.pi)
            x = 128 + side * (78 - reach * 60)
            y = 132 - reach * 40 + (math.sin(t * 0.1) * 2 if not punching else 0)
            r = 20 - reach * 8
            pyxel.circ(x, y, r + 1, HOTPINK)
            pyxel.circ(x, y, r, PINK)
            for f in range(3):
                pyxel.circ(x - r * 0.5 + f * r * 0.5, y - r * 0.6, r * 0.25, LPINK)

    def draw_cockpit(self, t):
        top = 8 * len(self.enemies)
        # the window frame
        for side in (0, 1):
            def x(v):
                return W - 1 - v if side else v
            pyxel.tri(x(0), 0, x(26), 0, x(10), 142, PLUM)
            pyxel.tri(x(0), 0, x(10), 142, x(0), 142, PLUM)
            pyxel.line(x(26), 0, x(10), 142, HOTPINK)
        pyxel.rect(0, 0, W, top, PLUM)
        pyxel.rect(0, top, W, 1, HOTPINK)
        # their health bars at the top
        for i, m in enumerate(self.enemies):
            y = i * 8
            art.text(28, y + 1, m.name, m.color, None)
            pyxel.rect(90, y + 2, 130, 4, NAVY)
            pyxel.rect(90, y + 2, 130 * max(0, m.hp) / m.max_hp, 4, RED)
        # the dashboard
        pyxel.rect(0, 142, W, 18, PLUM)
        pyxel.rect(0, 142, W, 1, HOTPINK)
        art.text(6, 147, "ARMOR", WHITE)
        for i in range(ARMOR):
            c = PINK if i < self.armor else DGRAY
            pyxel.rect(30 + i * 9, 146, 7, 8, c)
        art.text(138, 147, "ZAP", WHITE)
        pyxel.rect(154, 147, 60, 6, NAVY)
        pyxel.rect(154, 147, 60 * self.power / 100, 6, YELLOW if self.power >= ZAP_COST else LAV)
        for i in range(3):
            pyxel.rect(224 + i * 9, 147, 7, 6, YELLOW if self.lane == i - 1 else DGRAY)
        if self.hurt and self.hurt % 8 < 4:
            pyxel.rectb(0, 0, W, H, RED)
            pyxel.rectb(1, 1, W - 2, H - 2, RED)
        if self.armor <= 3 and self.state == "fight":
            pyxel.line(40, 30, 70, 60, LGRAY)
            pyxel.line(70, 60, 62, 80, LGRAY)

    def draw_overlay(self, t):
        if self.state == "ready":
            pyxel.rect(0, 50, W, 52, NAVY)
            word = "READY..." if self.timer > 50 else "FIGHT!"
            if self.layer == 3 and self.timer > 50:
                word = "2 AGAINST 1!"
            art.big_center(56, word, [PINK, YELLOW], 3)
            art.center_text(84, "LEFT/RIGHT: DODGE   Z: PUNCH   X: ZAP", WHITE)
            art.center_text(93, "PUNCH A MECH WHEN IT IS STUCK OR DIZZY!", YELLOW)
        elif self.state == "pause":
            pyxel.rect(0, 60, W, 34, NAVY)
            art.center_text(66, "PAUSED", WHITE)
            art.center_text(78, "ENTER: KEEP PLAYING   ESC: LEVEL GRID", LGRAY)
        elif self.state == "won" and self.timer > 120:
            pyxel.rect(0, 50, W, 44, NAVY)
            art.big_center(56, "YOU WON!", RAINBOW, 3)
            if t % 40 < 28:
                art.center_text(82, "PRESS ENTER", YELLOW)
        elif self.state == "lost" and self.timer > 60:
            pyxel.rect(0, 50, W, 44, NAVY)
            art.big_center(56, "MECH DOWN!", [RED, ORANGE], 3)
            if t % 40 < 28:
                art.center_text(82, "PRESS ENTER TO TRY AGAIN", YELLOW)
