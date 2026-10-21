# Builds all 64 levels. Each level is made from a seed, so level 5 is
# always the same level 5. Every 8th level is a boss fight.
#
# Tiles:  .  air      #  ground     B  hay bale / block
#         =  cloud you can jump up through     H  vine you can climb
import random

from consts import *

THEMES = [
    dict(name="SUNNY FARM", sky=SKY, sky2=CREAM, cloud=WHITE, hill=MINT, hill2=PALEMINT,
         dirt=BROWN, dirt2=DBROWN, grass=GREEN, edge=DGREEN, block="hay", front=SAGE, deco="fence", night=False),
    dict(name="APPLE ORCHARD", sky=BLUE, sky2=SKY, cloud=WHITE, hill=MINT, hill2=PALEMINT,
         dirt=BROWN, dirt2=DBROWN, grass=GREEN, edge=DGREEN, block="hay", front=SAGE, deco="trees", night=False),
    dict(name="BIG RED BARN", sky=PEACH, sky2=CREAM, cloud=WHITE, hill=MINT, hill2=PALEMINT,
         dirt=BROWN, dirt2=DBROWN, grass=GREEN, edge=DGREEN, block="hay", front=SAGE, deco="barn", night=False),
    dict(name="CORN MAZE", sky=SKY, sky2=WHITE, cloud=WHITE, hill=STRAW, hill2=CREAM,
         dirt=BROWN, dirt2=DBROWN, grass=GREEN, edge=DGREEN, block="hay", front=TAN, deco="corn", night=False),
    dict(name="PUMPKIN PATCH", sky=ORANGE, sky2=YELLOW, cloud=PEACH, hill=TAN, hill2=PALETAN,
         dirt=DBROWN, dirt2=BLACK, grass=GREEN, edge=DGREEN, block="hay", front=SAGE, deco="pumpkins", night=False),
    dict(name="RAINBOW CLOUDS", sky=LPINK, sky2=SKY, cloud=WHITE, hill=WHITE, hill2=SKY,
         dirt=PINK, dirt2=HOTPINK, grass=WHITE, edge=LPINK, block="candy", front=LPINK, deco="clouds", night=False),
    dict(name="MOONLIGHT FARM", sky=NAVY, sky2=DPURPLE, cloud=DGRAY, hill=DUSK, hill2=DPURPLE,
         dirt=DBROWN, dirt2=BLACK, grass=GREEN, edge=DGREEN, block="hay", front=NAVY, deco="night", night=True),
    dict(name="CARROT BOOM'S SILO", sky=DPURPLE, sky2=PLUM, cloud=LAV, hill=SLATE, hill2=NAVY,
         dirt=DGRAY, dirt2=BLACK, grass=LGRAY, edge=LAV, block="brick", front=DPURPLE, deco="silo", night=True),
]

BOSSES = {
    8: ["moneycat"],
    16: ["eggbert"],
    24: ["blackbunny"],
    32: ["tornado"],
    40: ["scarecrow"],
    48: ["pinkfire"],
    56: ["moonbunny"],
    64: ["carrotboom"],
}

BOSS_NAMES = {
    "moneycat": "MONEY CAT",
    "eggbert": "EGGBERT",
    "blackbunny": "THE BLACK BUNNY",
    "tornado": "TORNADO BUNNY",
    "carrotboom": "CARROT BOOM",
    "scarecrow": "THE SCARECROW",
    "pinkfire": "THE PINK FIREBALL",
    "moonbunny": "THE MOON BUNNY",
}

BOSS_TIPS = {
    "moneycat": "DODGE THE LASERS! HIT HIM WHEN HE RESTS!",
    "eggbert": "JUMP ON AN EGG, PICK IT UP, THROW IT BACK!",
    "blackbunny": "JUMP OVER THE SHOCKWAVES!",
    "tornado": "ZAP THE TORNADOES! HOLD UP TO AIM HIGH!",
    "carrotboom": "WHEN HE WATERS HIS CARROTS, BONK HIS BUTT!",
    "scarecrow": "THROW HIS PUMPKINS BACK! ZAP THE CROWS!",
    "pinkfire": "DODGE THE FIRE! HIT HER WHEN SHE RESTS!",
    "moonbunny": "LOOK AT THE MOON...",
}


# Which enemies live in each world, and how often they show up.
# Pigs live everywhere, because pigs want carrots.
ENEMIES = [
    {"walk": 1},                                            # Sunny Farm
    {"walk": 3, "charge": 2, "apple": 5},                   # Apple Orchard
    {"walk": 3, "charge": 1, "rooster": 4, "fly": 2},       # Big Red Barn
    {"walk": 2, "charge": 2, "corn": 4, "fly": 2},          # Corn Maze
    {"walk": 2, "charge": 1, "jack": 4, "crow": 3},         # Pumpkin Patch
    {"walk": 1, "fly": 3, "flame": 5},                      # Rainbow Clouds
    {"walk": 2, "charge": 1, "bat": 3, "moon": 3, "minimoon": 3},   # Moonlight Farm
    {"walk": 2, "charge": 2, "fly": 1, "carrotbomb": 4},    # Carrot Boom's Silo
]

# How many tiles above the ground the flying enemies float.
AIR_HEIGHT = {"fly": 4, "crow": 6, "bat": 6, "flame": 3, "moon": 4}


def pick(rnd, weights):
    r = rnd.uniform(0, sum(weights.values()))
    for kind, w in weights.items():
        r -= w
        if r <= 0:
            return kind
    return kind


def world_of(n):
    return (n - 1) // 8


def theme_of(n):
    return THEMES[world_of(n)]


def is_boss(n):
    return n % 8 == 0


class Level:
    def __init__(self, n):
        self.n = n
        self.theme = theme_of(n)
        self.grid = []
        self.width = 0
        self.spawns = []        # (kind, x, y, extra)
        self.start = (24, 100)
        self.goal = None        # (x, ground_y)
        self.bosses = []
        self.hard = n >= 40


def build(n):
    rnd = random.Random(n * 7919 + 13)
    lv = Level(n)
    if is_boss(n):
        _build_boss(lv)
    else:
        _build_normal(lv, rnd)
    return lv


def _build_boss(lv):
    width = 32
    grid = [["."] * width for _ in range(ROWS)]
    for ty in range(17, ROWS):
        for tx in range(width):
            grid[ty][tx] = "#"
    for ty in range(ROWS):
        grid[ty][0] = "B"
        grid[ty][width - 1] = "B"
    for tx in range(4, 9):
        grid[12][tx] = "="
    for tx in range(23, 28):
        grid[12][tx] = "="
    if lv.n >= 32:
        for tx in range(13, 19):
            grid[8][tx] = "="
    lv.grid, lv.width = grid, width
    lv.start = (3 * T, 17 * T - 14)
    for tx in (3, 7, 11, 15, 20, 25):
        lv.spawns.append(("tuft", tx * T, 17 * T, None))
    lv.bosses = BOSSES[lv.n]


def _build_normal(lv, rnd):
    n = lv.n
    world = world_of(n)
    d = n / 64
    width = 120 + n * 3
    heights = [None] * width
    clouds = []      # one-way platforms over big gaps
    gaps = []        # (start, width, height)

    def fill(x, length, h):
        for i in range(length):
            if 0 <= x + i < width:
                heights[x + i] = h

    x, h = 0, 16
    fill(0, 14, h)
    x = 14
    while x < width - 26:
        r = rnd.random()
        if r < 0.28:
            length = rnd.randint(4, 10)
            fill(x, length, h)
            x += length
        elif r < 0.45 + 0.15 * d:
            gw = rnd.randint(2, 3 + min(2, world // 2))
            gaps.append((x, gw, h))
            x += gw
            fill(x, 4, h)
            x += 4
        elif r < 0.78:
            h = clamp(h + rnd.choice([-2, -1, 1, 2]), 11, 17)
            length = rnd.randint(4, 9)
            fill(x, length, h)
            x += length
        elif n >= 3:
            gw = rnd.randint(7, 9)
            gaps.append((x, gw, h))
            cx = x + gw // 2 - 1
            clouds.append((cx, h - 3, 3))
            x += gw
            fill(x, 4, h)
            x += 4
        else:
            fill(x, 6, h)
            x += 6
    fill(x, width - x, 16)

    grid = [["."] * width for _ in range(ROWS)]
    for tx, hh in enumerate(heights):
        if hh is not None:
            for ty in range(hh, ROWS):
                grid[ty][tx] = "#"
    for cx, cy, cl in clouds:
        for i in range(cl):
            grid[cy][cx + i] = "="

    # flat runs of ground, used for placing things
    runs = []
    s = 0
    for tx in range(1, width + 1):
        if tx == width or heights[tx] != heights[s]:
            if heights[s] is not None and tx - s >= 4:
                runs.append((s, tx, heights[s]))
            s = tx

    spots_platform = []   # (x tile, top row) places on top of platforms
    spots_high = []
    used = set()
    for (a, b, hh) in runs:
        if a < 16 or b > width - 18:
            continue
        length = b - a
        if length >= 10 and hh >= 12 and rnd.random() < 0.3:
            ps = a + 2
            row = hh - 8
            for i in range(5):
                grid[row][ps + i] = "="
            for vy in range(row - 1, hh):
                grid[vy][ps - 1] = "H"
            spots_high.append((ps + 2, row))
            for i in range(5):
                used.add(ps - 1 + i)
            for i in range(1, 4):
                lv.spawns.append(("coin", (ps + i) * T + 1, (row - 2) * T, None))
        elif length >= 7 and rnd.random() < 0.6:
            pl = rnd.randint(3, 5)
            ps = a + rnd.randint(1, length - pl - 1)
            row = hh - 4
            tile = "=" if rnd.random() < 0.55 else "B"
            for i in range(pl):
                grid[row][ps + i] = tile
                used.add(ps + i)
            spots_platform.append((ps + pl // 2, row))
            for i in range(pl):
                if rnd.random() < 0.7:
                    lv.spawns.append(("coin", (ps + i) * T + 1, (row - 2) * T, None))

    # coins over the gaps
    for (gx, gw, hh) in gaps:
        for i in range(gw + 2):
            arc = 1 if 0 < i < gw + 1 else 0
            lv.spawns.append(("coin", (gx - 1 + i) * T + 1, (hh - 4 - arc) * T, None))
    # coin rows on the ground
    for (a, b, hh) in runs:
        if b - a >= 6 and rnd.random() < 0.4:
            cs = a + rnd.randint(0, b - a - 4)
            for i in range(3):
                if cs + i not in used:
                    lv.spawns.append(("coin", (cs + i) * T + 1, (hh - 3) * T, None))

    # grass tufts you can pull up
    for tx in range(6, width - 12):
        hh = heights[tx]
        if hh is None or tx in used or grid[hh - 1][tx] != ".":
            continue
        if rnd.random() < 0.07 or (n == 1 and tx in (9, 11)):
            lv.spawns.append(("tuft", tx * T, hh * T, None))

    # pigs
    count = min(26, 3 + n // 2)
    places = [tx for (a, b, hh) in runs for tx in range(a + 1, b - 1) if 22 <= tx < width - 14]
    rnd.shuffle(places)
    taken = []
    for tx in places:
        if len(taken) >= count:
            break
        if any(abs(tx - o) < 6 for o in taken):
            continue
        taken.append(tx)
        hh = heights[tx]
        kind = pick(rnd, ENEMIES[world])
        # py is where the enemy's feet are: on the ground, or up in the air for flyers
        py = (hh - AIR_HEIGHT.get(kind, 0)) * T
        lv.spawns.append(("pig", tx * T, py, kind))

    # three carrots to rescue
    carrot_spots = []
    if spots_high:
        carrot_spots.append(rnd.choice(spots_high))
    rnd.shuffle(spots_platform)
    carrot_spots += spots_platform[:3 - len(carrot_spots)]
    ground_spots = [(tx, heights[tx]) for tx in taken[::2]] or [(width // 2, heights[width // 2])]
    while len(carrot_spots) < 3:
        carrot_spots.append(ground_spots[len(carrot_spots) % len(ground_spots)])
    for (tx, row) in carrot_spots[:3]:
        lv.spawns.append(("carrot", tx * T, row * T - 12, None))

    # power-ups
    if n == 1:
        lv.spawns.append(("ball", 34 * T, (heights[34] or 16) * T - 22, None))
    elif rnd.random() < 0.45 and spots_platform:
        tx, row = spots_platform[-1]
        lv.spawns.append(("ball", tx * T, row * T - 22, None))
    if rnd.random() < 0.35:
        tx = rnd.randint(30, width - 30)
        if heights[tx] is not None:
            lv.spawns.append(("heart", tx * T, heights[tx] * T - 20, None))
    if n % 3 == 0 or n == 2:
        tx = width // 2
        while heights[tx] is None:
            tx += 1
        lv.spawns.append(("unicorn", tx * T, heights[tx] * T - 30, None))

    if n == 1:
        for tx, msg in ((3, "ARROWS: RUN   Z: JUMP"),
                        (12, "STAND ON LEAVES, PRESS C TO PULL"),
                        (24, "X: LIGHTNING ZAP"),
                        (40, "KEEP RUNNING FOR SUPER SPEED!"),
                        (60, "HOLD DOWN, THEN JUMP: SUPER JUMP"),
                        (80, "JUMP ON A PIG, PRESS C TO PICK IT UP!")):
            lv.spawns.append(("sign", tx * T, 7 * T, msg))
    if n == 2:
        lv.spawns.append(("sign", 3 * T, 7 * T, "PIGS EAT CARROTS! SAVE THEM FIRST!"))

    lv.grid, lv.width = grid, width
    lv.start = (3 * T, 16 * T - 14)
    gx = width - 8
    lv.goal = (gx * T, heights[gx] * T)
