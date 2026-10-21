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
    """Every small enemy: pigs, and the other critters that live in each world.

    kind is one of: walk, charge, fly (pigs), apple, rooster, corn, jack,
    crow, bat, flame, carrotbomb, moon (a little crescent moon that drifts by),
    minimoon (a mini Moon Bunny with a red moon, that hops and throws moon rocks).
    """
    SIZES = {"corn": (10, 14), "flame": (10, 12), "rooster": (12, 12),
             "apple": (10, 10), "carrotbomb": (10, 12), "jack": (12, 11),
             "moon": (10, 10), "minimoon": (8, 8)}
    FLYERS = ("fly", "crow", "bat", "flame", "moon")
    CHOMPERS = ("walk", "charge", "fly", "crow", "bat", "rooster")   # these eat carrots

    def __init__(self, x, y, kind, speed):
        self.w, self.h = self.SIZES.get(kind, (12, 10))
        self.x, self.y = x, y - self.h      # y is where its feet go
        self.kind = kind
        self.speed = speed
        self.dir = -1
        self.vx = -speed
        self.vy = 0.0
        self.home_x = x
        self.base_y = self.y
        self.t = random.randint(0, 100)
        self.dead = False
        self.chomp = 0
        self.on_ground = False
        self.awake = False
        self.state = "hover"     # crows and bats: hover, swoop, climb, leave
        self.mode = "walk"       # roosters: walk, crow, dash
        self.timer = 0
        self.fuse = 0            # carrot bombs: counts down once lit
        self.cool = random.randint(30, 90)
        self.minion = False      # crows sent by the Scarecrow fly away after one swoop

    @property
    def rideable(self):
        return self.kind != "flame"

    def update(self, g):
        if not self.awake:
            if abs(self.x - g.player.x) < W:
                self.awake = True
            else:
                return
        self.t += 1
        if self.chomp > 0:
            self.chomp -= 1
        if self.kind in ("crow", "bat"):
            self.crow(g)
        elif self.kind == "flame":
            self.flame(g)
        elif self.kind == "moon":
            self.moon(g)
        elif self.kind == "fly":
            if g.move_x(self, self.vx) or abs(self.x - self.home_x) > 48:
                self.vx = -self.vx
                self.x += self.vx * 2
            old = self.y
            self.y = self.base_y + math.sin(self.t * 0.05) * 10
            self.vy = self.y - old
        else:
            self.walker(g)
        if self.kind in self.CHOMPERS:
            for c in g.pickups:
                if c.kind == "carrot" and not c.dead and overlap(self, c):
                    c.dead = True
                    self.chomp = 40
                    g.float_text(c.x + 4, c.y - 4, "CHOMP!", RED)
                    g.puff(c.x + 4, c.y + 5, ORANGE)
                    sounds.sfx(sounds.CHOMP)

    def walker(self, g):
        """Everything that walks, rolls, or hops along the ground."""
        p = g.player
        dx = p.cx - (self.x + self.w / 2)
        near = abs(dx) < 100 and abs(p.y - self.y) < 30
        speed = self.speed
        k = self.kind
        if k == "charge" and abs(dx) < 90 and abs(p.y - self.y) < 24:
            self.dir = sign(dx) or self.dir
            speed = 1.8
        elif k == "apple":
            # rolls fast and bounces a little
            speed = self.speed * 1.7
            if self.on_ground and self.t % 70 == 0:
                self.vy = -2.6
        elif k == "rooster":
            self.timer -= 1
            if self.mode == "walk":
                self.cool -= 1
                if near and self.cool <= 0:
                    self.mode, self.timer = "crow", 35
                    self.dir = sign(dx) or self.dir
                    g.float_text(self.x + 6, self.y - 8, "COCK-A-DOODLE-DOO!", WHITE)
                    sounds.sfx(sounds.SPEED)
            elif self.mode == "crow":
                speed = 0
                if self.timer <= 0:
                    self.mode, self.timer = "dash", 60
            else:
                speed = 2.6
                if self.timer <= 0:
                    self.mode, self.cool = "walk", 90
        elif k == "jack":
            # hops toward you
            speed = 1.3 if not self.on_ground else 0
            if self.on_ground and self.t % 45 == 0 and abs(dx) < 140:
                self.dir = sign(dx) or self.dir
                self.vy = -3.2
        elif k == "corn":
            speed = 0.3
            if self.on_ground and self.t % 90 == 0:
                self.vy = -4
        elif k == "minimoon":
            # a mini Moon Bunny: it does one slow moon walk hop toward you,
            # and when it lands it throws a moon rock
            speed = 0.6 if not self.on_ground else 0
            self.cool -= 1
            if self.on_ground and self.cool <= 0 and abs(dx) < 150 and abs(p.y - self.y) < 60:
                self.dir = sign(dx) or self.dir
                self.vy = -2.2
                self.cool = 110
            if not self.on_ground:
                self.dir = sign(dx) or self.dir
        elif k == "carrotbomb":
            if self.fuse:
                speed = 0
                self.fuse -= 1
                if self.fuse == 0:
                    self.dead = True
                    g.explode(self.x + self.w / 2, self.y + self.h / 2)
                    return
            elif abs(dx) < 50 and abs(p.y - self.y) < 30:
                self.fuse = 70
                g.float_text(self.x + 5, self.y - 8, "FSSST!", ORANGE)
                sounds.sfx(sounds.THROW)
        self.vx = 0 if self.chomp else self.dir * speed
        if g.move_x(self, self.vx):
            self.dir = -self.dir
        if self.on_ground:
            fx = self.x + self.w + 1 if self.dir > 0 else self.x - 1
            if g.tile_at(fx, self.y + self.h + 2) not in "#B=":
                self.dir = -self.dir
        grav = GRAVITY * 0.35 if k == "minimoon" else GRAVITY    # moon walk: low gravity
        self.vy = min(self.vy + grav, MAX_FALL)
        was = self.on_ground
        self.on_ground = g.move_y(self, self.vy) == "floor"
        if self.on_ground:
            self.vy = 0
            if k == "minimoon" and not was and abs(dx) < 150:
                # it landed: throw a moon rock at you
                aim = clamp(dx / 60, -1.6, 1.6)
                g.shots.append(Shot("moonrock", self.x + 1, self.y - 2, 6, 6, aim, -2.2, 0.12, 240))
                g.float_text(self.x + 4, self.y - 8, "MOON ROCK!", RED)
                sounds.sfx(sounds.THROW)
            if k == "corn" and not was:
                # POP! hot popcorn flies up
                for d in (-1, 1):
                    g.shots.append(Shot("popcorn", self.x + 3, self.y, 5, 5,
                                        d * random.uniform(0.6, 1.4), -3.5, 0.15, 200))
                sounds.sfx(sounds.POOF)
        if self.y > H:
            self.dead = True

    def moon(self, g):
        """A little crescent moon. It drifts slowly one way, bobbing, and turns at walls."""
        self.vx = self.dir * self.speed * 0.5
        if g.move_x(self, self.vx) or abs(self.x - self.home_x) > 70:
            self.dir = -self.dir
            self.x += self.dir * 2
        old = self.y
        self.y = self.base_y + math.sin(self.t * 0.04) * 6
        self.vy = self.y - old

    def flame(self, g):
        """Little pink flames float in waves and spit pink fire."""
        self.x = self.home_x + math.sin(self.t * 0.02) * 28
        old = self.y
        self.y = self.base_y + math.sin(self.t * 0.06) * 8
        self.vy = self.y - old
        p = g.player
        self.dir = sign(p.cx - self.x) or self.dir
        if self.t % 130 == 0 and abs(p.cx - self.x) < 150:
            ang = math.atan2(p.y + p.h / 2 - self.y - 6, p.cx - self.x - 5)
            s = Shot("orb", self.x + 3, self.y + 4, 4, 4, math.cos(ang) * 1.2, math.sin(ang) * 1.2, 0, 300)
            s.bx, s.by = s.x, s.y
            g.shots.append(s)

    def crow(self, g):
        """Crows and bats hover high up, then dive at you and fly back up."""
        p = g.player
        old_y = self.y
        if self.state == "hover":
            self.x += math.sin(self.t * 0.03) * 0.6
            self.y = self.base_y + math.sin(self.t * 0.07) * 4
            self.vx = 0
            self.cool -= 1
            if self.cool <= 0 and (self.minion or abs(p.cx - self.x) < 110) and p.y > self.y:
                self.swoop_at(p)
                g.float_text(self.x + 6, self.y - 6, "CAW!" if self.kind == "crow" else "SKREE!", WHITE)
        elif self.state == "swoop":
            self.x += self.vx
            self.y += self.dive
            self.dive -= 0.06            # curve back up, like a real swoop
            if self.dive < -1.5:
                self.state = "leave" if self.minion else "climb"
        elif self.state == "climb":
            self.vx *= 0.97
            self.x += self.vx
            self.y = max(self.base_y, self.y - 1.2)
            if self.y <= self.base_y + 0.5:
                self.state = "hover"
                self.cool = 100
        elif self.state == "leave":
            self.x += self.vx
            self.y -= 1.6
            if self.y < -24:
                self.dead = True
        self.vy = self.y - old_y
        self.dir = sign(self.vx) or (sign(p.cx - self.x) or self.dir)

    def swoop_at(self, p):
        self.state = "swoop"
        frames = 40
        self.vx = clamp((p.cx - self.x - self.w / 2) / frames, -3, 3)
        self.dive = clamp((p.y - self.y) / frames * 1.6, 1.0, 4.0)

    def draw(self, t):
        f = self.dir if self.kind != "fly" else (sign(self.vx) or 1)
        frame = self.t // 8
        if self.kind == "rooster" and self.mode == "dash":
            frame = self.t // 3
        lit = self.fuse if self.kind == "carrotbomb" else 0
        art.draw_critter(self.x, self.y, f, frame, self.kind, self.chomp, lit=lit)


class Item:
    """Things you can carry: turnips, pigs, eggs, pumpkins, and carrot bombs."""
    SIZES = {"turnip": (8, 8), "pig": (12, 10), "egg": (10, 8), "bomb": (10, 10),
             "pumpkin": (12, 10)}
    LANDS = ("bomb", "pumpkin")   # these sit on the ground after a throw

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
            if self.kind in self.LANDS:
                self.vx = 0
            else:
                self.poof(g)
                return
        if g.move_y(self, self.vy) == "floor":
            if self.kind in self.LANDS:
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
            g.puff(self.x + self.w / 2, self.y + self.h / 2,
                   ORANGE if self.kind == "pumpkin" else WHITE)
            if self.kind == "pig":
                g.knock_out_pig(self.x, self.y, self.variant, sign(self.vx) or 1)

    def draw(self, t):
        if self.kind == "turnip":
            art.draw_turnip(self.x, self.y)
        elif self.kind == "pig":
            art.draw_critter(self.x, self.y, sign(self.vx) or 1, t // 4, self.variant)
        elif self.kind == "egg":
            art.draw_egg(self.x, self.y)
        elif self.kind == "bomb":
            art.draw_carrot_bomb(self.x, self.y, self.fuse, t)
        elif self.kind == "pumpkin":
            art.draw_pumpkin(self.x, self.y)


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
        self.bx, self.by = x, y      # orbs fly along a path and wiggle around it
        self.wave = 0.0
        self.wave_f = 0.15
        self.curve = 0.0
        self.col = HOTPINK
        self.top = 1.6               # top speed of a chasing tornado
        self.chase = True            # False: the tornado rolls straight and does not follow you

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
        if self.kind == "tornado" and self.landed and self.chase:
            self.vx = clamp(self.vx + sign(p.cx - self.x - self.w / 2) * 0.03, -self.top, self.top)
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
                    self.vx = sign(p.cx - self.x) * (0.8 if self.chase else 0.6)
        elif self.kind in ("orb", "lasercoin"):
            # bullet-hell fire: can turn (curve) and wiggle (wave) as it flies
            if self.curve:
                c, s = math.cos(self.curve), math.sin(self.curve)
                self.vx, self.vy = self.vx * c - self.vy * s, self.vx * s + self.vy * c
            self.bx += self.vx
            self.by += self.vy
            wob = math.sin(self.t * self.wave_f) * self.wave if self.wave else 0
            sp = math.hypot(self.vx, self.vy) or 1
            self.x = self.bx - self.vy / sp * wob
            self.y = self.by + self.vx / sp * wob
            if not (g.cam_x - 10 < self.x < g.cam_x + W + 10) or not (-20 < self.y < H + 10):
                self.dead = True
            return
        else:
            self.x += self.vx
            self.y += self.vy
            if self.kind in ("fire", "rock", "moonrock", "popcorn") and g.rect_solid(self.x, self.y, self.w, self.h):
                self.dead = True
                if self.kind in ("rock", "moonrock"):
                    g.puff(self.x + self.w / 2, self.y + self.h, LAV if self.kind == "rock" else RED)
                    sounds.sfx(sounds.BOUNCE)
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
        elif self.kind == "orb":
            pyxel.circ(x + 2, y + 2, 3, self.col)
            pyxel.circ(x + 2, y + 2, 1, WHITE)
        elif self.kind == "lasercoin":
            # a spinning gold coin with a laser streak behind it
            sp = math.hypot(self.vx, self.vy) or 1
            tx, ty = x + 3 - self.vx / sp * 12, y + 3 - self.vy / sp * 12
            pyxel.line(x + 3, y + 3, tx, ty, ORANGE)
            pyxel.line(x + 3, y + 3, (x + 3 + tx) / 2, (y + 3 + ty) / 2, YELLOW)
            w = 2 + abs(math.sin(self.t * 0.3)) * 5
            pyxel.elli(x + 3 - w / 2, y - 1, w, 8, ORANGE)
            pyxel.elli(x + 4 - w / 2, y, max(1, w - 2), 6, YELLOW)
            pyxel.pset(x + 3, y + 1, WHITE)
        elif self.kind == "popcorn":
            pyxel.circ(x + 2, y + 2, 2, WHITE)
            pyxel.pset(x + 3, y + 1, CREAM)
            pyxel.pset(x + 1, y + 3, YELLOW)
        elif self.kind == "rock":
            pyxel.circ(x + 3, y + 3, 3, LAV)
            pyxel.circb(x + 3, y + 3, 3, SKY)
            pyxel.pset(x + 2, y + 2, WHITE)
        elif self.kind == "moonrock":
            # a little red moon rock
            pyxel.circ(x + 3, y + 3, 3, RED)
            pyxel.circb(x + 3, y + 3, 3, HOTPINK)
            pyxel.pset(x + 2, y + 2, PINK)


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
        art.draw_critter(self.x, self.y, 1, 0, self.kind, flipv=True)
