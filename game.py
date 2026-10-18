# Playing one level.
import math
import random

import pyxel

import art
import bosses
import controls as C
import levels
import sounds
from consts import *
from entities import Bolt, FlyingPig, Item, Particle, Pickup, Pig, Player, Tuft, UNICORN_TIME

SOLID = "#B"
EPS = 0.001   # so standing exactly on a tile edge does not count as touching it


class Goal:
    def __init__(self, x, ground_y):
        self.x, self.ground_y = x, ground_y


class Play:
    def __init__(self, app, n):
        self.app = app
        self.n = n
        self.lv = levels.build(n)
        self.grid = self.lv.grid
        self.width = self.lv.width
        self.theme = self.lv.theme
        self.boss_level = levels.is_boss(n)

        self.player = Player(*self.lv.start, power=app.save["power"])
        self.pigs, self.items, self.pickups, self.tufts = [], [], [], []
        self.shots, self.bolts, self.bosses, self.flyers = [], [], [], []
        self.particles, self.texts, self.signs = [], [], []
        self.goal = Goal(*self.lv.goal) if self.lv.goal else None
        self.coins = app.save["coins"]
        self.stolen = 0
        self.carrots = 0
        self.cam_x = 0.0
        self.shake = 0
        self.t = 0
        self.state = "play"
        self.timer = 0
        self.banner_info = None
        self.intro = 0

        speed = 0.45 + 0.35 * n / 64
        for kind, x, y, extra in self.lv.spawns:
            if kind == "pig":
                self.pigs.append(Pig(x, y, extra, speed))
            elif kind == "tuft":
                self.tufts.append(Tuft(x, y, regrow=self.boss_level))
            elif kind == "sign":
                self.signs.append((x, y, extra))
            else:
                self.pickups.append(Pickup(kind, x, y))

        if self.boss_level:
            kinds = self.lv.bosses
            twin = len(kinds) > 1
            self.bosses = [bosses.make(k, self, self.lv.hard, twin) for k in kinds]
            names = " AND ".join(levels.BOSS_NAMES[k] for k in kinds)
            self.banner("BOSS: " + names, levels.BOSS_TIPS[kinds[-1]], 150)
            self.intro = 120
            sounds.music(sounds.MUSIC_BOSS)
        else:
            self.banner(f"LEVEL {n}", self.theme["name"], 90)
            sounds.music(sounds.MUSIC_FARM)

    # ---------------------------------------------------------- tiles

    def tile(self, tx, ty):
        if tx < 0 or tx >= self.width:
            return "B"
        if ty < 0 or ty >= ROWS:
            return "."
        return self.grid[ty][tx]

    def tile_at(self, px, py):
        return self.tile(int(px // T), int(py // T))

    def rect_solid(self, x, y, w, h):
        for tx in range(int(x // T), int((x + w - EPS) // T) + 1):
            for ty in range(int(y // T), int((y + h - EPS) // T) + 1):
                if self.tile(tx, ty) in SOLID:
                    return True
        return False

    def move_x(self, o, dx):
        """Moves sideways, stopping at walls. Returns True if it hit a wall."""
        if dx == 0:
            return False
        steps = int(abs(dx) // 4) + 1
        step = dx / steps
        for _ in range(steps):
            o.x += step
            if self.rect_solid(o.x, o.y, o.w, o.h):
                if step > 0:
                    o.x = int((o.x + o.w - EPS) // T) * T - o.w
                else:
                    o.x = (int(o.x // T) + 1) * T
                return True
        return False

    def move_y(self, o, dy, oneway=True):
        """Moves up or down. Returns 'floor', 'ceil', or None."""
        if dy == 0:
            dy = 0.01
        steps = int(abs(dy) // 4) + 1
        step = dy / steps
        for _ in range(steps):
            prev_bottom = o.y + o.h
            o.y += step
            if step > 0:
                row = int((o.y + o.h - EPS) // T)
                hit = self.rect_solid(o.x, o.y, o.w, o.h)
                if not hit and oneway and prev_bottom <= row * T + 0.01:
                    for tx in range(int(o.x // T), int((o.x + o.w - EPS) // T) + 1):
                        if self.tile(tx, row) == "=":
                            hit = True
                            break
                if hit:
                    o.y = row * T - o.h
                    return "floor"
            elif self.rect_solid(o.x, o.y, o.w, o.h):
                o.y = (int(o.y // T) + 1) * T
                return "ceil"
        return None

    # ---------------------------------------------------------- helpers

    def rideables(self):
        out = [p for p in self.pigs if p.awake and not p.dead]
        out += [i for i in self.items if i.rideable and not i.dead]
        return out

    def float_text(self, x, y, s, c):
        self.texts.append([x - len(s) * 2, y, s, c, 60])

    def banner(self, title, sub, frames):
        self.banner_info = [title, sub, frames]

    def puff(self, x, y, c):
        for i in range(8):
            a = i * math.pi / 4
            self.particles.append(Particle(x, y, math.cos(a) * 1.2, math.sin(a) * 1.2, 16, c, 2))

    def sparkle(self, x, y, c):
        self.particles.append(Particle(x, y, random.uniform(-1.5, 1.5), random.uniform(-2, 0.5),
                                       20, c, 1, 0.08))

    def trail(self, p):
        c = RAINBOW[(self.t // 2) % len(RAINBOW)]
        self.particles.append(Particle(p.cx - p.facing * 5, p.y + random.uniform(2, p.h - 2),
                                       -p.vx * 0.1, 0, 18, c, 2))

    # ---------------------------------------------------------- actions

    def try_pick(self, p):
        o = p.ride
        if isinstance(o, Pig):
            o.dead = True
            p.holding = Item("pig", o.x, o.y, variant=o.kind)
            sounds.sfx(sounds.PLUCK)
            return
        if isinstance(o, Item) and o.pickable:
            o.state, o.owner, o.vx = "held", None, 0
            p.holding = o
            sounds.sfx(sounds.PLUCK)
            return
        feet = p.y + p.h
        for tuft in self.tufts:
            if tuft.active and tuft.x < p.x + p.w + 1 and tuft.x + 8 > p.x - 1 \
                    and abs(tuft.ground - feet) < 2:
                self.pluck(tuft, p)
                return
        for o in self.items:
            if o.pickable and not o.dead and o.x < p.x + p.w + 3 and o.x + o.w > p.x - 3 \
                    and o.y < feet + 2 and o.y + o.h > p.y:
                o.state, o.owner, o.vx = "held", None, 0
                p.holding = o
                sounds.sfx(sounds.PLUCK)
                return

    def pluck(self, tuft, p):
        tuft.active = False
        tuft.timer = 240
        sounds.sfx(sounds.PLUCK)
        self.puff(tuft.x + 4, tuft.ground - 2, BROWN)
        r = random.random()
        if self.boss_level:
            r = 0 if r < 0.92 else 0.80
        elif self.n == 1 and not tuft.regrow:
            r = 0
        if r < 0.74:
            p.holding = Item("turnip", tuft.x, tuft.ground - 8)
        elif r < 0.86:
            self.coins += 3
            sounds.sfx(sounds.COIN)
            self.float_text(p.cx, p.y - 8, "+3 COINS", YELLOW)
        elif r < 0.93:
            self.collect(Pickup("heart", 0, 0), p)
        elif r < 0.97:
            self.collect(Pickup("ball", 0, 0), p)
        else:
            self.collect(Pickup("unicorn", 0, 0), p)

    def zap(self, p, up):
        x = p.cx + p.facing * 6
        y = p.y + 6
        if up:
            dirs = [(p.facing * 4.2, -4.2)]
        else:
            dirs = [(p.facing * 6.5, 0)]
        if p.power >= 3:
            vx, vy = dirs[0]
            dirs += [(vx, vy - 1.3), (vx, vy + 1.3)]
        for vx, vy in dirs:
            self.bolts.append(Bolt(x, y, vx, vy, p.power))
        sounds.sfx(sounds.ZAP)

    def bolt_hits(self, b):
        for pig in self.pigs:
            if not pig.dead and pig.awake and pig not in b.hit and overlap(b, pig):
                b.hit.add(pig)
                self.defeat_pig(pig, sign(b.vx))
                if b.power == 1:
                    b.dead = True
                    return
        for boss in self.bosses:
            if boss.dead:
                continue
            if boss.catch_bolt(b):
                b.dead = True
                return
            if overlap(b, boss):
                boss.hit(1, "zap", b)    # lightning only tickles bosses. Throw things at them!
                b.dead = True
                return
        for s in self.shots:
            if not s.dead and s.kind in ("paw", "tornado", "fire", "rock") and overlap(b, s):
                s.dead = True
                b.dead = True
                self.puff(s.x + s.w / 2, s.y + s.h / 2, WHITE)
                sounds.sfx(sounds.POOF)
                return
        for o in self.items:
            if not o.dead and o.state != "held" and o.kind in ("egg", "bomb") and overlap(b, o):
                b.dead = True
                o.poof(self)
                return

    def thrown_hits(self, o):
        for pig in self.pigs:
            if not pig.dead and pig.awake and overlap(o, pig):
                self.defeat_pig(pig, sign(o.vx))
                o.poof(self)
                return
        for boss in self.bosses:
            if not boss.dead and overlap(o, boss):
                if o.kind != "bomb":
                    boss.hit(3, "throw", o)
                o.poof(self)
                return

    def defeat_pig(self, pig, dirx):
        pig.dead = True
        self.knock_out_pig(pig.x, pig.y, pig.kind, dirx)
        if random.random() < 0.3:
            c = Pickup("coin", pig.x + 3, pig.y, life=300)
            c.vy = -3
            self.pickups.append(c)

    def knock_out_pig(self, x, y, kind, dirx):
        self.flyers.append(FlyingPig(x, y, kind, dirx))
        self.puff(x + 6, y + 5, WHITE)
        sounds.sfx(sounds.POOF)

    def explode(self, x, y):
        sounds.sfx(sounds.BOOM)
        self.shake = 12
        for i in range(24):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.5, 3)
            c = random.choice([RED, ORANGE, YELLOW, WHITE])
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp, 24, c, 3))
        r = 26
        p = self.player
        if abs(p.cx - x) < r and abs(p.y + p.h / 2 - y) < r:
            p.hurt(self, x)
        for pig in self.pigs:
            if not pig.dead and abs(pig.x + 6 - x) < r and abs(pig.y + 5 - y) < r:
                self.defeat_pig(pig, sign(pig.x + 6 - x))
        for boss in self.bosses:
            if not boss.dead and abs(boss.cx - x) < r + boss.w / 2 and abs(boss.y + boss.h / 2 - y) < r + boss.h / 2:
                boss.hit(4, "boom")

    def collect(self, c, p):
        c.dead = True
        k = c.kind
        if k == "coin":
            self.coins += 1
            sounds.sfx(sounds.COIN)
        elif k == "carrot":
            self.carrots += 1
            sounds.sfx(sounds.CARROT)
            self.float_text(p.cx, p.y - 10, f"CARROT {self.carrots}/3", ORANGE)
        elif k == "ball":
            if p.power < 3:
                p.power += 1
                self.float_text(p.cx, p.y - 10, f"LIGHTNING POWER {p.power}!", YELLOW)
            else:
                self.coins += 10
                self.float_text(p.cx, p.y - 10, "MAX POWER! +10 COINS", YELLOW)
            sounds.sfx(sounds.POWER)
        elif k == "heart":
            if p.hearts >= p.max_hearts and p.max_hearts < 5:
                p.max_hearts += 1
            p.hearts = min(p.max_hearts, p.hearts + 1)
            sounds.sfx(sounds.POWER)
            self.float_text(p.cx, p.y - 10, "HEART!", RED)
        elif k == "unicorn":
            p.unicorn = UNICORN_TIME
            sounds.sfx(sounds.POWER)
            self.float_text(p.cx, p.y - 10, "UNICORN RIDE! HOLD JUMP TO FLY", WHITE)
        for _ in range(6):
            self.sparkle(c.x + c.w / 2, c.y + c.h / 2, random.choice([WHITE, YELLOW]))

    def steal_coins(self):
        take = min(self.coins, 20 if self.lv.hard else 10)
        self.coins -= take
        self.stolen += take
        sounds.sfx(sounds.STEAL)
        p = self.player
        cat = next((b for b in self.bosses if isinstance(b, bosses.MoneyCat)), None)
        for i in range(min(take, 12)):
            tx = cat.cx if cat else p.cx
            self.particles.append(Particle(p.cx, p.y, (tx - p.cx) / 40 + random.uniform(-0.5, 0.5),
                                           random.uniform(-3, -1), 40, YELLOW, 2, 0.1))
        if cat:
            cat.took_coins(take)
        if take:
            self.banner(f"MONEY CAT TOOK {take} COINS!", "JUMP OVER THE GREEDY BEAM!", 90)
        else:
            self.float_text(p.cx, p.y - 10, "NO COINS TO TAKE! HA!", YELLOW)

    def player_fell(self):
        p = self.player
        p.hearts -= 1
        sounds.sfx(sounds.HURT)
        if p.hearts <= 0:
            self.player_died()
            return
        p.holding = None
        p.x, p.y = p.safe
        p.vx = p.vy = 0
        p.invuln = 100
        p.fast = False

    def player_died(self):
        if self.state == "play":
            self.state = "oops"
            self.timer = 0
            sounds.music(None)

    def boss_defeated(self, boss):
        self.shake = 20
        for _ in range(30):
            self.sparkle(boss.cx, boss.y + boss.h / 2, random.choice(RAINBOW))
        self.puff(boss.cx, boss.y + boss.h / 2, WHITE)
        sounds.sfx(sounds.BOOM)
        if all(b.dead for b in self.bosses):
            self.shots.clear()
            for o in self.items:
                if o.kind in ("egg", "bomb") and o is not self.player.holding:
                    o.dead = True
            if self.player.holding and self.player.holding.kind == "bomb":
                self.player.holding.dead = True
                self.player.holding = None
            got_back = self.stolen * 2
            self.coins += got_back
            if self.n == 64:
                self.banner("YOU BEAT CARROT BOOM!", "ALL THE CARROTS ARE SAFE!", 180)
            elif boss.beaten_msg:
                self.banner(*boss.beaten_msg, 180)
            elif got_back:
                self.banner(f"{boss.name} IS BEATEN!", f"YOU GOT {got_back} COINS BACK!", 150)
            else:
                self.banner(f"{boss.name} IS BEATEN!", "GO TO THE RAINBOW!", 150)
            for i in range(20):
                c = Pickup("coin", random.uniform(20, 230), random.uniform(-40, 0), life=600)
                self.pickups.append(c)
            self.goal = Goal(W // 2, bosses.GROUND_Y)
            sounds.music(None)
            sounds.sfx(sounds.CLEAR)

    def finish(self):
        self.state = "clear"
        self.timer = 0
        sounds.music(None)
        sounds.sfx(sounds.CLEAR)
        self.app.level_done(self.n, self.carrots, self.coins, self.player.power)

    # ---------------------------------------------------------- update

    def update(self):
        if self.state == "pause":
            if C.pressed("start"):
                self.state = "play"
            elif C.pressed("back"):
                self.app.to_select(self.n)
            return
        if self.state == "oops":
            self.timer += 1
            if self.timer > 100:
                self.app.play(self.n)
            return
        if self.state == "clear":
            self.timer += 1
            self.update_world(hero=False)
            if self.timer > 50 and C.ok():
                if self.n == LEVEL_COUNT:
                    self.app.to_ending()
                else:
                    self.app.to_select(min(LEVEL_COUNT, self.n + 1))
            return
        if C.pressed("start") or C.pressed("back"):
            self.state = "pause"
            return
        self.t += 1
        self.update_world(hero=True)

    def update_world(self, hero):
        if self.intro > 0:
            self.intro -= 1
        for pig in self.pigs:
            pig.update(self)
        for o in self.items:
            o.update(self)
        if self.intro == 0:
            for b in self.bosses:
                if not b.dead:
                    b.update()
        for s in self.shots:
            s.update(self)
        p = self.player
        if hero:
            p.update(self)
            if self.state != "play":
                return
            self.check_touches(p)
        for b in self.bolts:
            b.update(self)
        for o in self.pickups:
            o.update(self)
        for tuft in self.tufts:
            tuft.update(self)
        for f in self.flyers:
            f.update(self)
        for pt in self.particles:
            pt.update()
        for tx in self.texts:
            tx[1] -= 0.4
            tx[4] -= 1
        if self.banner_info:
            self.banner_info[2] -= 1
            if self.banner_info[2] <= 0:
                self.banner_info = None
        if self.shake > 0:
            self.shake -= 1

        self.pigs = [o for o in self.pigs if not o.dead]
        self.items = [o for o in self.items if not o.dead]
        self.shots = [o for o in self.shots if not o.dead]
        self.bolts = [o for o in self.bolts if not o.dead]
        self.pickups = [o for o in self.pickups if not o.dead]
        self.flyers = [o for o in self.flyers if not o.dead]
        self.particles = [o for o in self.particles if o.life > 0]
        self.texts = [o for o in self.texts if o[4] > 0]

        lead = p.facing * (40 if p.fast else 14)
        target = clamp(p.cx - W / 2 + lead, 0, self.width * T - W)
        self.cam_x += (target - self.cam_x) * 0.12

    def check_touches(self, p):
        strong = p.fast or p.unicorn > 0
        for pig in self.pigs:
            if pig.dead or not pig.awake or pig is p.ride or not overlap(p, pig):
                continue
            if strong:
                self.defeat_pig(pig, p.facing)
            elif p.vy >= 0 and p.y + p.h - pig.y < 7:
                p.y = pig.y - p.h
                p.vy = 0
            else:
                p.hurt(self, pig.x + pig.w / 2)
        for o in self.items:
            if o.kind == "pumpkin" and o.state == "thrown" and o.owner == "boss" and overlap(p, o):
                if p.hurt(self, o.x + o.w / 2):
                    o.poof(self)
            if o.kind == "egg" and o.state == "moving" and o is not p.ride and overlap(p, o):
                if p.vy >= 0 and p.y + p.h - o.y < 6:
                    continue
                p.hurt(self, o.x + o.w / 2)
        for s in self.shots:
            if s.dead or not overlap(p, s):
                continue
            if s.kind == "paw":
                s.dead = True
                self.steal_coins()
            elif s.kind == "tornado":
                if p.hurt(self, s.x + s.w / 2):
                    p.vy = -6.5
                    p.spin = 40
                    s.dead = True
            elif s.kind == "coin":
                if p.hurt(self, s.x):
                    s.dead = True
            elif p.hurt(self, s.x + s.w / 2) and s.kind != "wave":
                s.dead = True
        for b in self.bosses:
            if b.dead or not overlap(p, b):
                continue
            if p.vy > 0 and p.y + p.h - b.y < 10:
                p.vy = -4.5
                sounds.sfx(sounds.BOUNCE)
                b.stomped()
            else:
                p.hurt(self, b.cx)
        for c in self.pickups:
            if not c.dead and overlap(p, c):
                self.collect(c, p)
        if self.goal and abs(p.cx - self.goal.x) < 12 and p.y + p.h > self.goal.ground_y - 40:
            self.finish()

    # ---------------------------------------------------------- draw

    def draw(self):
        t = self.t
        art.draw_background(self.theme, self.cam_x, t)
        sx = sy = 0
        if self.shake:
            sx, sy = random.randint(-2, 2), random.randint(-2, 2)
        cam = int(self.cam_x) + sx
        pyxel.camera(cam, sy)
        art.draw_tiles(self.grid, self.theme, cam, t)
        for x, y, msg in self.signs:
            if -200 < x - cam < W:
                art.text(x, y, msg, WHITE)
        if self.goal:
            art.draw_goal(self.goal.x, self.goal.ground_y, t)
        for tuft in self.tufts:
            tuft.draw(t)
        for c in self.pickups:
            c.draw(t)
        for pig in self.pigs:
            if pig.awake:
                pig.draw(t)
        for o in self.items:
            if o is not self.player.holding:
                o.draw(t)
        for b in self.bosses:
            if not b.dead:
                b.draw(t)
        for s in self.shots:
            s.draw(t)
        for f in self.flyers:
            f.draw(t)
        if self.state != "clear" or t % 2:
            self.player.draw(t)
        if self.player.holding:
            self.player.holding.draw(t)
        for b in self.bolts:
            b.draw(t)
        for pt in self.particles:
            pyxel.rect(pt.x, pt.y, pt.size, pt.size, pt.col)
        for x, y, s, c, life in self.texts:
            art.text(x, y, s, c)
        pyxel.camera()
        self.draw_hud()
        self.draw_overlays()

    def draw_hud(self):
        p = self.player
        pyxel.rect(0, 0, W, 11, NAVY)
        for i in range(p.max_hearts):
            art.draw_heart(3 + i * 10, 2, RED if i < p.hearts else DGRAY)
        art.draw_coin(56, 2, self.t)
        art.text(65, 3, f"x{self.coins}", YELLOW)
        if not self.boss_level:
            for i in range(3):
                if i < self.carrots:
                    art.draw_carrot(100 + i * 9, 1)
                else:
                    pyxel.tri(101 + i * 9, 4, 107 + i * 9, 4, 104 + i * 9, 11, DGRAY)
        art.text(134, 3, "ZAP", YELLOW)
        for i in range(3):
            pyxel.rect(148 + i * 5, 3, 3, 5, YELLOW if i < p.power else DGRAY)
        if p.unicorn:
            pyxel.rect(168, 4, 30, 3, DGRAY)
            pyxel.rect(168, 4, 30 * p.unicorn / UNICORN_TIME, 3, RAINBOW[(self.t // 4) % 6])
        if p.fast:
            art.text(168 if not p.unicorn else 202, 3, "FAST!" if p.unicorn else "SUPER FAST!",
                     RAINBOW[(self.t // 3) % 6])
        label = f"LEVEL {self.n}"
        art.text(W - len(label) * 4 - 3, 3, label, WHITE)
        alive = [b for b in self.bosses if not b.dead]
        for i, b in enumerate(alive):
            y = 14 + i * 9
            art.text(W - 4 - len(b.name) * 4, y, b.name, WHITE)
            bw = 60
            bx = W - 70 - len(b.name) * 4
            pyxel.rect(bx, y + 1, bw, 4, DGRAY)
            pyxel.rect(bx, y + 1, bw * max(0, b.hp) / b.max_hp, 4, RED)

    def draw_overlays(self):
        if self.banner_info and self.state == "play":
            title, sub, frames = self.banner_info
            y = 44
            pyxel.rect(0, y - 4, W, 26 if sub else 16, NAVY)
            art.center_text(y, title, RAINBOW[(self.t // 4) % 6] if self.boss_level else WHITE)
            if sub:
                art.center_text(y + 10, sub, YELLOW)
        if self.state == "pause":
            pyxel.dither(0.6)
            pyxel.rect(0, 0, W, H, NAVY)
            pyxel.dither(1.0)
            art.big_center(52, "PAUSED", RAINBOW, 3)
            art.center_text(84, "ENTER: KEEP PLAYING", WHITE)
            art.center_text(94, "ESC: BACK TO LEVELS", WHITE)
        if self.state == "oops":
            art.big_center(60, "OOPS!", RAINBOW, 4)
            art.center_text(92, "LET'S TRY AGAIN!", WHITE)
        if self.state == "clear":
            pyxel.rect(30, 30, W - 60, 92, NAVY)
            pyxel.rectb(30, 30, W - 60, 92, RAINBOW[(self.timer // 4) % 6])
            art.big_center(38, "LEVEL CLEAR!", RAINBOW, 2)
            if not self.boss_level:
                art.center_text(60, "CARROTS SAVED", WHITE)
                for i in range(3):
                    x = W // 2 - 22 + i * 16
                    if i < self.carrots:
                        art.draw_carrot(x, 70, 1)
                    else:
                        pyxel.tri(x + 1, 73, x + 7, 73, x + 4, 80, DGRAY)
            art.draw_coin(W // 2 - 20, 88, self.timer)
            art.text(W // 2 - 10, 89, f"x{self.coins}", YELLOW)
            if self.timer > 50 and self.timer % 30 < 20:
                art.center_text(108, "PRESS Z OR ENTER", WHITE)
