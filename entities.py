# The pink bunny, the pigs, and all the stuff in a level.
import math
import random

import pyxel

import art
import controls as C
import sounds
from consts import *

# How the bunny moves. Change these to make the game feel different!
RUN_ACCEL = 0.14
AIR_ACCEL = 0.10
TOP_SPEED = 2.6
SUPER_SPEED = 4.4
SUPER_AFTER = 50         # frames at top speed before super speed kicks in
JUMP = 5.0
SUPER_JUMP = 6.6
CHARGE_TIME = 40         # frames to hold down for a super jump
UNICORN_TIME = 600


class Player:
    def __init__(self, x, y, power=1):
        self.x, self.y, self.w, self.h = x, y, 10, 14
        self.vx = self.vy = 0.0
        self.facing = 1
        self.on_ground = False
        self.ride = None
        self.hearts = self.max_hearts = 3
        self.invuln = 0
        self.holding = None
        self.charge = 0
        self.top_time = 0
        self.fast = False
        self.climbing = False
        self.power = power
        self.unicorn = 0
        self.zap_cd = 0
        self.zap_pose = 0
        self.anim = 0.0
        self.air_time = 0
        self.safe = (x, y)
        self.big_jump = False
        self.spin = 0

    @property
    def cx(self):
        return self.x + self.w / 2

    def update(self, g):
        left, right = C.held("left"), C.held("right")
        up, down = C.held("up"), C.held("down")
        if self.invuln > 0:
            self.invuln -= 1
        if self.zap_cd > 0:
            self.zap_cd -= 1
        if self.zap_pose > 0:
            self.zap_pose -= 1
        if self.spin > 0:
            self.spin -= 1
        if self.unicorn > 0:
            self.unicorn -= 1
            if self.unicorn == 0:
                g.float_text(self.cx, self.y - 10, "BYE BYE UNICORN!", WHITE)
            if g.t % 2 == 0:
                g.trail(self)

        if self.fast and g.t % 2 == 0:
            g.trail(self)

        # ---- climbing vines
        on_vine = g.tile_at(self.cx, self.y + self.h / 2) == "H"
        if self.climbing:
            if not on_vine or C.pressed("jump"):
                self.climbing = False
                if C.pressed("jump"):
                    self.vy = -4.2
                    sounds.sfx(sounds.JUMP)
            else:
                self.vx = (right - left) * 1.0
                self.vy = (down - up) * 1.2
                if self.vx:
                    self.facing = sign(self.vx)
                g.move_x(self, self.vx)
                old_y = self.y
                hit = g.move_y(self, self.vy, oneway=False)
                if self.vy < 0 and g.tile_at(self.cx, self.y + self.h / 2) != "H":
                    self.y = old_y
                if hit == "floor":
                    self.climbing = False
                if self.vx or self.vy:
                    self.anim += 0.15
                self._actions(g, up, down)
                return
        elif up and on_vine and not self.holding:
            self.climbing = True
            self.vx = self.vy = 0
            self.fast = False
            self.x = int(self.cx // T) * T + T / 2 - self.w / 2
            return

        # ---- running
        dirx = right - left
        crouch = down and self.on_ground
        top = TOP_SPEED
        if self.holding:
            top = 2.2
        if self.fast:
            top = SUPER_SPEED
        if self.unicorn:
            top = max(top, 3.4)
        accel = RUN_ACCEL if self.on_ground else AIR_ACCEL
        if self.fast:
            accel *= 1.4

        if crouch:
            self.vx *= 0.8
            if abs(self.vx) < 0.4:
                self.charge += 1
                if self.charge == CHARGE_TIME:
                    sounds.sfx(sounds.SELECT)
        else:
            self.charge = 0
            if dirx:
                if self.vx * dirx < 0:
                    self.vx += dirx * (0.35 if self.on_ground else 0.15)
                elif abs(self.vx) < top:
                    self.vx = dirx * min(top, abs(self.vx) + accel)
                self.facing = dirx
            elif self.on_ground:
                self.vx = sign(self.vx) * max(0, abs(self.vx) - 0.18)
            else:
                self.vx = sign(self.vx) * max(0, abs(self.vx) - 0.03)
        if abs(self.vx) > top:
            self.vx = sign(self.vx) * max(top, abs(self.vx) - 0.12)

        # ---- super speed (like Sonic!)
        if self.on_ground and dirx and dirx == sign(self.vx) and abs(self.vx) >= TOP_SPEED - 0.05 \
                and not self.holding:
            self.top_time += 1
            if self.top_time == SUPER_AFTER and not self.fast:
                self.fast = True
                sounds.sfx(sounds.SPEED)
                g.float_text(self.cx, self.y - 8, "SUPER SPEED!", YELLOW)
        elif abs(self.vx) < 2.0 or self.holding or (dirx and dirx != sign(self.vx)):
            self.top_time = 0
            self.fast = False

        # ---- jumping
        if self.on_ground:
            self.air_time = 0
        else:
            self.air_time += 1
        if C.pressed("jump") and (self.on_ground or self.air_time < 6):
            if self.charge >= CHARGE_TIME:
                self.vy = -SUPER_JUMP
                self.big_jump = True
                sounds.sfx(sounds.SUPER_JUMP)
                for i in range(8):
                    g.sparkle(self.cx, self.y + self.h, random.choice(RAINBOW))
            else:
                self.vy = -(JUMP + (0.4 if self.fast else 0))
                self.big_jump = False
                sounds.sfx(sounds.JUMP)
            self.charge = 0
            self.on_ground = False
            self.air_time = 99
            self.ride = None
        if self.unicorn and C.held("jump") and not self.on_ground and self.vy > -3.2:
            self.vy -= 0.55
        if not C.held("jump") and self.vy < -2.5 and not self.big_jump:
            self.vy = -2.5

        # ---- move
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        if self.ride is not None:
            g.move_x(self, self.ride.vx)
        if g.move_x(self, self.vx):
            self.vx = 0
            self.top_time = 0
            self.fast = False
        self.x = clamp(self.x, 0, g.width * T - self.w)

        prev_bottom = self.y + self.h
        hit = g.move_y(self, self.vy)
        self.on_ground = False
        self.ride = None
        if hit == "floor":
            self.vy = 0
            self.on_ground = True
            self.big_jump = False
        elif hit == "ceil":
            self.vy = 0.5
        if not self.on_ground and self.vy >= 0:
            for o in g.rideables():
                if self.x < o.x + o.w and self.x + self.w > o.x \
                        and prev_bottom <= o.y + 4 and self.y + self.h >= o.y:
                    self.y = o.y - self.h
                    self.vy = 0
                    self.on_ground = True
                    self.big_jump = False
                    self.ride = o
                    break
        if self.on_ground and self.ride is None:
            under_l = g.tile_at(self.x + 1, self.y + self.h + 1)
            under_r = g.tile_at(self.x + self.w - 1, self.y + self.h + 1)
            if under_l in "#B" and under_r in "#B":
                self.safe = (self.x, self.y)

        if self.on_ground:
            self.anim += abs(self.vx) * 0.12

        # ---- fell in a hole
        if self.y > H + 8:
            if self.unicorn:
                self.y = H - 4
                self.vy = -6
            else:
                g.player_fell()
                return

        self._actions(g, up, down)

    def _actions(self, g, up, down):
        # zap lightning
        if C.pressed("zap") and self.zap_cd == 0:
            g.zap(self, up)
            self.zap_cd = 12 if self.power >= 3 else 16
            self.zap_pose = 8
        # pick up and throw
        if C.pressed("grab"):
            if self.holding:
                self.throw(g, up, down)
            elif self.on_ground and not self.climbing:
                g.try_pick(self)
        if self.holding:
            o = self.holding
            o.x = self.cx - o.w / 2
            o.y = self.y - o.h + 2

    def throw(self, g, up, down):
        o = self.holding
        self.holding = None
        o.state = "thrown"
        o.owner = "player"
        if down:
            o.vx, o.vy = self.facing * 0.6, 0
            o.x = self.cx - o.w / 2 + self.facing * 8
        elif up:
            o.vx, o.vy = self.facing * 1.4 + self.vx * 0.3, -5.6
        else:
            o.vx, o.vy = self.facing * 4.6 + self.vx * 0.4, -1.3
        sounds.sfx(sounds.THROW)

    def drop(self):
        if self.holding:
            o = self.holding
            self.holding = None
            o.state = "thrown"
            o.owner = None
            o.vx, o.vy = -self.facing * 0.5, -1.5

    def hurt(self, g, from_x):
        if self.invuln > 0 or self.unicorn > 0:
            return False
        self.hearts -= 1
        self.invuln = 100
        away = sign(self.cx - from_x) or -self.facing
        self.vx = away * 2.5
        self.vy = -3
        self.fast = False
        self.top_time = 0
        self.climbing = False
        self.drop()
        sounds.sfx(sounds.HURT)
        g.shake = 6
        if self.hearts <= 0:
            g.player_died()
        return True

    def pose(self):
        if self.climbing:
            return "climb"
        if self.zap_pose:
            return "zap"
        if not self.on_ground:
            return "jump"
        if self.charge > 0:
            return "crouch"
        if self.holding:
            return "hold" if abs(self.vx) < 0.3 else "run"
        if abs(self.vx) > 0.3:
            return "fast" if self.fast else "run"
        return "stand"

    def draw(self, t):
        if self.invuln and (t // 3) % 2 == 0:
            return
        bx, by = self.x - 1, self.y - 6
        facing = self.facing
        if self.spin:
            facing = 1 if (t // 3) % 2 else -1
        if self.unicorn:
            frame = int(t // 4) if abs(self.vx) > 0.3 else 0
            art.draw_unicorn(self.x - 5, self.y + 2, facing, frame)
            by -= 6
        body = PINK
        if self.charge >= CHARGE_TIME and t % 6 < 3:
            body = HOTPINK
        art.draw_bunny(bx, by, facing, self.pose(), int(self.anim), body=body)


class Pig:
    def __init__(self, x, y, kind, speed):
        self.x, self.y, self.w, self.h = x, y, 12, 10
        self.kind = kind
        self.speed = speed
        self.dir = -1
        self.vx = -speed
        self.vy = 0.0
        self.home_x = x
        self.base_y = y
        self.t = random.randint(0, 100)
        self.dead = False
        self.chomp = 0
        self.on_ground = False
        self.awake = False

    def update(self, g):
        if not self.awake:
            if abs(self.x - g.player.x) < W:
                self.awake = True
            else:
                return
        self.t += 1
        if self.chomp > 0:
            self.chomp -= 1
        if self.kind == "fly":
            if g.move_x(self, self.vx) or abs(self.x - self.home_x) > 48:
                self.vx = -self.vx
                self.x += self.vx * 2
            old = self.y
            self.y = self.base_y + math.sin(self.t * 0.05) * 10
            self.vy = self.y - old
        else:
            p = g.player
            speed = self.speed
            if self.kind == "charge" and abs(p.cx - self.x) < 90 and abs(p.y - self.y) < 24:
                self.dir = sign(p.cx - self.x - self.w / 2) or self.dir
                speed = 1.8
            self.vx = 0 if self.chomp else self.dir * speed
            if g.move_x(self, self.vx):
                self.dir = -self.dir
            if self.on_ground:
                fx = self.x + self.w + 1 if self.dir > 0 else self.x - 1
                if g.tile_at(fx, self.y + self.h + 2) not in "#B=":
                    self.dir = -self.dir
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
            self.on_ground = g.move_y(self, self.vy) == "floor"
            if self.on_ground:
                self.vy = 0
            if self.y > H:
                self.dead = True
        for c in g.pickups:
            if c.kind == "carrot" and not c.dead and overlap(self, c):
                c.dead = True
                self.chomp = 40
                g.float_text(c.x + 4, c.y - 4, "CHOMP!", RED)
                g.puff(c.x + 4, c.y + 5, ORANGE)
                sounds.sfx(sounds.CHOMP)

    def draw(self, t):
        f = self.dir if self.kind != "fly" else (sign(self.vx) or 1)
        art.draw_pig(self.x, self.y, f, (self.t // 8), self.kind, self.chomp)


class Item:
    """Things you can carry: turnips, pigs, eggs, and carrot bombs."""
    SIZES = {"turnip": (8, 8), "pig": (12, 10), "egg": (10, 8), "bomb": (10, 10)}

    def __init__(self, kind, x, y, state="held", variant=None):
        self.kind = kind
        self.w, self.h = self.SIZES[kind]
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.state = state       # held, thrown, rest, moving
        self.owner = None
        self.variant = variant
        self.fuse = 150 if kind == "bomb" else 0
        self.dead = False
        self.t = 0

    @property
    def rideable(self):
        return self.state in ("rest", "moving")

    @property
    def pickable(self):
        return self.state in ("rest", "moving")

    def update(self, g):
        self.t += 1
        if self.kind == "bomb":
            self.fuse -= 1
            if self.fuse <= 0:
                self.dead = True
                if g.player.holding is self:
                    g.player.holding = None
                g.explode(self.x + self.w / 2, self.y + self.h / 2)
                return
        if self.state == "held":
            return
        if self.state == "moving":
            self.x += self.vx
            if g.rect_solid(self.x, self.y, self.w, self.h) or self.x < -20 or self.x > g.width * T:
                self.poof(g)
            return
        if self.state == "rest":
            self.vx *= 0.8
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
            g.move_x(self, self.vx)
            if g.move_y(self, self.vy) == "floor":
                self.vy = 0
            if self.y > H:
                self.dead = True
            return
        # thrown
        self.vy = min(self.vy + 0.2, MAX_FALL)
        if g.move_x(self, self.vx):
            if self.kind == "bomb":
                self.vx = 0
            else:
                self.poof(g)
                return
        if g.move_y(self, self.vy) == "floor":
            if self.kind == "bomb":
                self.state = "rest"
                self.owner = None
                self.vy = 0
                sounds.sfx(sounds.BOUNCE)
            else:
                self.poof(g)
                return
        if self.y > H + 20:
            self.dead = True
        if self.owner == "player":
            g.thrown_hits(self)

    def poof(self, g):
        self.dead = True
        if self.kind == "bomb":
            g.explode(self.x + self.w / 2, self.y + self.h / 2)
        else:
            g.puff(self.x + self.w / 2, self.y + self.h / 2, WHITE)
            if self.kind == "pig":
                g.knock_out_pig(self.x, self.y, self.variant, sign(self.vx) or 1)

    def draw(self, t):
        if self.kind == "turnip":
            art.draw_turnip(self.x, self.y)
        elif self.kind == "pig":
            art.draw_pig(self.x, self.y, sign(self.vx) or 1, t // 4, self.variant)
        elif self.kind == "egg":
            art.draw_egg(self.x, self.y)
        elif self.kind == "bomb":
            art.draw_carrot_bomb(self.x, self.y, self.fuse, t)


class Pickup:
    """Coins, carrots, and power-ups you touch to collect."""
    SIZES = {"coin": (7, 8), "carrot": (8, 10), "ball": (9, 9), "heart": (8, 8), "unicorn": (18, 14)}

    def __init__(self, kind, x, y, life=0):
        self.kind = kind
        self.w, self.h = self.SIZES[kind]
        self.x, self.y = x, y
        self.vy = 0.0
        self.life = life          # 0 means it stays forever
        self.dead = False
        self.t = random.randint(0, 60)
        self.falls = life > 0

    def update(self, g):
        self.t += 1
        if self.life:
            self.life -= 1
            if self.life <= 0:
                self.dead = True
        if self.falls:
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
            if g.move_y(self, self.vy) == "floor":
                self.vy = 0

    def draw(self, t):
        if self.life and self.life < 60 and t % 4 < 2:
            return
        bob = math.sin(self.t * 0.08) * 1.5 if not self.falls else 0
        x, y = self.x, self.y + bob
        if self.kind == "coin":
            art.draw_coin(x, y, self.t)
        elif self.kind == "carrot":
            art.draw_carrot(x, y)
            if self.t % 30 < 4:
                pyxel_sparkle(x + 6, y + 1)
        elif self.kind == "ball":
            art.draw_ball(x, y, self.t)
        elif self.kind == "heart":
            art.draw_heart(x, y)
        elif self.kind == "unicorn":
            art.draw_unicorn(x, y, 1, (self.t // 10) % 2)


def pyxel_sparkle(x, y):
    pyxel.pset(x, y, WHITE)
    pyxel.pset(x - 1, y, YELLOW)
    pyxel.pset(x + 1, y, YELLOW)
    pyxel.pset(x, y - 1, YELLOW)
    pyxel.pset(x, y + 1, YELLOW)


class Tuft:
    def __init__(self, x, y, regrow=False):
        self.x, self.y, self.w, self.h = x, y - 4, 8, 4
        self.ground = y
        self.active = True
        self.regrow = regrow
        self.timer = 0

    def update(self, g):
        if not self.active and self.regrow:
            self.timer -= 1
            if self.timer <= 0:
                self.active = True
                g.puff(self.x + 4, self.ground - 2, GREEN)

    def draw(self, t):
        if self.active:
            art.draw_tuft(self.x, self.ground, t)


class Bolt:
    def __init__(self, x, y, vx, vy, power):
        self.power = power
        self.w, self.h = (14, 9) if power >= 2 else (10, 6)
        self.x, self.y = x - self.w / 2, y - self.h / 2
        self.vx, self.vy = vx, vy
        self.life = 26 if power == 1 else 32
        self.dead = False
        self.hit = set()

    def update(self, g):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.dead = True
        elif g.rect_solid(self.x + 3, self.y + 2, self.w - 6, self.h - 4):
            self.dead = True
            g.sparkle(self.x + self.w / 2, self.y + self.h / 2, YELLOW)
        g.bolt_hits(self)

    def draw(self, t):
        art.draw_bolt(self, t)


class Shot:
    """Things bosses throw at you."""

    def __init__(self, kind, x, y, w, h, vx=0.0, vy=0.0, grav=0.0, life=300):
        self.kind = kind
        self.x, self.y, self.w, self.h = x, y, w, h
        self.vx, self.vy, self.grav = vx, vy, grav
        self.life = life
        self.dead = False
        self.t = 0
        self.landed = False

    def update(self, g):
        self.t += 1
        self.life -= 1
        if self.life <= 0:
            self.dead = True
            return
        p = g.player
        if self.kind == "paw":
            ty = p.y + p.h / 2 - self.h / 2
            self.vy += clamp((ty - self.y) * 0.004, -0.06, 0.06)
            self.vy = clamp(self.vy, -1.2, 1.2)
        if self.kind == "tornado" and self.landed:
            self.vx = clamp(self.vx + sign(p.cx - self.x - self.w / 2) * 0.03, -1.6, 1.6)
        self.vy = min(self.vy + self.grav, MAX_FALL)
        if self.kind in ("coin", "tornado", "wave"):
            if g.move_x(self, self.vx) and self.kind != "tornado":
                self.dead = True
            res = g.move_y(self, self.vy)
            if res == "floor":
                if self.kind == "coin":
                    self.dead = True
                    g.pickups.append(Pickup("coin", self.x, self.y, life=360))
                    return
                self.vy = 0
                if self.kind == "tornado" and not self.landed:
                    self.landed = True
                    self.vx = sign(p.cx - self.x) * 0.8
        else:
            self.x += self.vx
            self.y += self.vy
            if self.kind == "fire" and g.rect_solid(self.x, self.y, self.w, self.h):
                self.dead = True
        if self.x < -30 or self.x > g.width * T + 30 or self.y > H + 30:
            self.dead = True

    def draw(self, t):
        x, y = self.x, self.y
        if self.kind == "coin":
            art.draw_coin(x, y, self.t)
        elif self.kind == "fire":
            art.draw_fireball(x, y, t)
        elif self.kind == "wave":
            for i in range(3):
                h = 6 - abs(1 - i) * 2 - (t // 2) % 2
                pyxel.rect(x + i * 3, y + 6 - h, 2, h, LAV if i % 2 else WHITE)
        elif self.kind == "tornado":
            art.draw_tornado(x, y, self.w, self.h, self.t)
        elif self.kind == "paw":
            art.draw_paw(x, y, t)


class Particle:
    def __init__(self, x, y, vx, vy, life, col, size=1, grav=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.size, self.grav = life, col, size, grav

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.grav
        self.life -= 1


class FlyingPig:
    """A knocked-out pig flipping off the screen."""

    def __init__(self, x, y, kind, dirx):
        self.x, self.y, self.kind = x, y, kind
        self.vx, self.vy = dirx * 1.5, -4.0
        self.dead = False

    def update(self, g):
        self.x += self.vx
        self.vy += 0.25
        self.y += self.vy
        if self.y > H + 20:
            self.dead = True

    def draw(self, t):
        art.draw_pig(self.x, self.y, 1, 0, self.kind, flipv=True)
