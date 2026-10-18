# Sound effects and music. Music uses channels 0-2, sound effects use channel 3.
import pyxel

JUMP, COIN, ZAP, PLUCK, THROW, HURT, POOF, POWER = 0, 1, 2, 3, 4, 5, 6, 7
BOSS_HIT, BOOM, CLEAR, STEAL, CARROT, CHOMP, SPEED, NOPE = 8, 9, 10, 11, 12, 13, 14, 15
SUPER_JUMP, SELECT, BOUNCE = 16, 17, 18

MUSIC_FARM, MUSIC_BOSS, MUSIC_TITLE = 0, 1, 2


def setup():
    s = pyxel.sounds
    s[JUMP].set("c2g2c3", "p", "5", "s", 3)
    s[COIN].set("b3e4", "p", "54", "nf", 6)
    s[ZAP].set("c4g3c3g2c2", "n", "76543", "n", 2)
    s[PLUCK].set("c3c4", "t", "6", "s", 4)
    s[THROW].set("g3c3", "n", "5", "f", 4)
    s[HURT].set("f3c3f2c2", "s", "6", "n", 5)
    s[POOF].set("c4g3e3c3", "p", "5", "f", 3)
    s[POWER].set("c3e3g3c4e4g4c4e4g4", "p", "5", "n", 4)
    s[BOSS_HIT].set("c2f1c1", "n", "7", "f", 5)
    s[BOOM].set("c2a1f1c1", "n", "7776", "f", 9)
    s[CLEAR].set("c3e3g3c4rg3c4e4g4", "p", "6", "n", 7)
    s[STEAL].set("e4b3g3e3b2g2", "p", "6", "n", 5)
    s[CARROT].set("g3c4e4g4", "t", "6", "n", 4)
    s[CHOMP].set("c2rc2", "n", "6", "f", 5)
    s[SPEED].set("c3g3c4g4c4", "s", "4", "s", 3)
    s[NOPE].set("c2c2", "s", "5", "n", 8)
    s[SUPER_JUMP].set("c2c3c4c4", "p", "6", "s", 3)
    s[SELECT].set("e3a3", "p", "5", "n", 4)
    s[BOUNCE].set("g2g3", "t", "6", "s", 3)

    # Farm song: a happy tune in C.
    s[40].set(
        "e3g3c4g3 a3g3e3c3 d3f3a3f3 g3f3d3b2"
        "e3g3c4e4 d4c4a3g3 f3a3g3f3 e3d3c3r",
        "p", "4", "nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnf", 18)
    s[41].set(
        "c2rg1r a1re1r d2ra1r g1rg1b1"
        "c2rg1r a1re1r f1rg1r c2rc2r",
        "t", "5", "n", 18)
    s[42].set("c1rrr" * 8, "n", "2", "f", 18)

    # Boss song: faster and spookier.
    s[43].set(
        "a2c3e3c3 a2c3f3c3 g2b2d3b2 g2b2e3d3"
        "a2c3e3a3 g3e3c3a2 f2a2c3f3 e3rg#2r",
        "s", "3", "n", 12)
    s[44].set(
        "a1ra1a1 f1rf1f1 g1rg1g1 e1re1e1"
        "a1ra1a1 c2rc2c2 f1rf1f1 e1re1e1",
        "t", "5", "n", 12)
    s[45].set("c1rc1r" * 8, "n", "3", "f", 12)

    # Title song.
    s[46].set(
        "c3e3g3c4 b3g3e3g3 a3f3c3f3 g3rrr"
        "c3e3g3c4 e4d4c4a3 g3f3e3d3 c3rrr",
        "t", "5", "n", 22)
    s[47].set(
        "c2rrr e1rrr f1rrr g1rrr"
        "c2rrr a1rrr g1rrr c2rrr",
        "t", "4", "n", 22)

    pyxel.musics[MUSIC_FARM].set([40], [41], [42])
    pyxel.musics[MUSIC_BOSS].set([43], [44], [45])
    pyxel.musics[MUSIC_TITLE].set([46], [47], [])


def sfx(n):
    pyxel.play(3, n)


_current = None


def music(n):
    global _current
    if n != _current:
        _current = n
        if n is None:
            for ch in range(3):
                pyxel.stop(ch)
        else:
            pyxel.playm(n, loop=True)
