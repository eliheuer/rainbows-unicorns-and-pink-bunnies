# Shared numbers and colors for Rainbows, Unicorns, and Pink Bunnies.

W, H = 256, 160          # screen size in pixels
T = 8                    # tile size in pixels
ROWS = H // T            # every level is 20 tiles tall

GRAVITY = 0.3
MAX_FALL = 5.0

# Colors. 0-15 are the PICO-8 palette, 16+ are extra colors we add.
BLACK, NAVY, PLUM, DGREEN, BROWN, DGRAY, SKY, WHITE = 0, 1, 2, 3, 4, 5, 6, 7
RED, ORANGE, YELLOW, GREEN, BLUE, LAV, PINK, PEACH = 8, 9, 10, 11, 12, 13, 14, 15
LPINK, PURPLE, DBROWN, LGRAY, HOTPINK, CREAM, DPURPLE, GOLD = 16, 17, 18, 19, 20, 21, 22, 23
# Soft colors for faraway things, so they never look like ground you can stand on.
MINT, PALEMINT, SAGE, STRAW, TAN, PALETAN, DUSK, SLATE = 24, 25, 26, 27, 28, 29, 30, 31
PALEORANGE = 32

PALETTE = [
    0x000000, 0x1D2B53, 0x7E2553, 0x008751, 0xAB5236, 0x5F574F, 0x8FD3FF, 0xFFF1E8,
    0xFF004D, 0xFFA300, 0xFFEC27, 0x00E436, 0x29ADFF, 0x83769C, 0xFF77A8, 0xFFCCAA,
    0xFFC6E0, 0x9B5DE5, 0x6B3A25, 0xC2C3C7, 0xFF3D9A, 0xFFF6B0, 0x3B1F5C, 0xE8A900,
    0xA6E3A1, 0xCDEFC5, 0x7DB88A, 0xF2E3A0, 0xD9B48F, 0xE8CFAF, 0x2E3F78, 0x4B3F72,
    0xF7C99A,
]

RAINBOW = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]

LEVEL_COUNT = 64


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def sign(v):
    return 1 if v > 0 else -1 if v < 0 else 0


def overlap(a, b):
    """True when two objects with x, y, w, h touch."""
    return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y
