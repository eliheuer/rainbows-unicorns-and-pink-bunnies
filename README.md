# Rainbows, Unicorns, and Pink Bunnies

A 2D platform game made with [Pyxel](https://github.com/kitao/pyxel).
You are a pink bunny with lightning powers and super speed.
Carrot Boom, a white bunny, wants to steal all the carrots in the world.
His pig friends want to eat them. Stop them and save the carrots!

## Play the game

You need [uv](https://docs.astral.sh/uv/). uv installs Python and Pyxel for you.

1. Install uv (Linux or macOS):

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Get the game:

   ```sh
   git clone https://github.com/eliheuer/rainbows-unicorns-and-pink-bunnies.git
   cd rainbows-unicorns-and-pink-bunnies
   ```

3. Play:

   ```sh
   uv run main.py
   ```

To get the newest version of the game, run `git pull` in the game folder.

## Controls

| Key | Gamepad | What it does |
|---|---|---|
| Arrows or WASD | D-pad | Run and climb vines |
| Z or Space | A | Jump |
| X | X | Lightning zap. Hold Up to zap up high. |
| C | B | Pull up a plant, pick up a pig, or throw what you carry |
| Down, then jump | Down, then A | Super jump. Hold Down until the bunny flashes. |
| Enter or Esc | Start | Pause |

When you carry something, hold Up to throw it high. Hold Down to put it down.

## The story

When you play for the first time, a short movie tells the story. Carrot Boom
is on the news, and the President calls the pink bunny for help. To watch
the story again, press Up on the title screen. When you beat the game, a big
ending movie plays.

In a movie, press Enter to go to the next scene. Press Esc to skip the movie.

## How the game works

The game has 64 levels in 8 worlds. When you beat a level, the next level
unlocks. The game saves your progress in `save.json`. On the level grid,
you can pick any level that you unlocked.

Each level has 3 carrots. Pigs eat carrots when they walk into them, so get
the carrots first. The orange dots on the level grid show your best score.

The game is like Super Mario Bros. 2:

- You do not stomp on pigs. You stand on them, pick them up, and throw them.
- Pull up plants to get turnips to throw. Some plants have coins or prizes.
- You have hearts. A hit takes one heart away.

## Worlds and enemies

Pigs live in every world, because pigs want carrots. Each world also has
its own enemies.

| Levels | World | Enemies |
|---|---|---|
| 1-8 | Sunny Farm | Pigs |
| 9-16 | Apple Orchard | Rotten apples roll at you and bounce. |
| 17-24 | Big Red Barn | Roosters crow, then run at you fast. |
| 25-32 | Corn Maze | Popcorn cobs hop and pop hot popcorn into the air. |
| 33-40 | Pumpkin Patch | Jack-o'-lanterns hop at you. Crows dive at you. |
| 41-48 | Rainbow Clouds | Little pink flames float and shoot pink fire. Pigs fly here. |
| 49-56 | Moonlight Farm | Bats dive at you. |
| 57-64 | Carrot Boom's Silo | Walking carrot bombs light their fuse when you get close. Pick one up and throw it! |

If you keep running fast, you get super speed, like Sonic. With super speed,
you knock out pigs when you run into them.

## Power-ups

| Power-up | What it does |
|---|---|
| Lightning ball | Makes your zap stronger. Level 2 zaps go through pigs. Level 3 shoots 3 zaps. |
| Unicorn | You ride a unicorn for 10 seconds. Hold Jump to fly. Nothing can hurt you. |
| Heart | Gives back one heart. If your hearts are full, you get a new heart. |

## Bosses

Every 8th level has a boss. Lightning does only 1 damage to a boss.
Throw things at bosses to do 3 damage. When a boss has half of its health,
it gets angry and attacks faster.

| Level | Boss | Tip |
|---|---|---|
| 8 | Money Cat | He shoots laser coins and laser beams. The gold Greedy Beam takes your coins, so jump over it. Hit him when he rests. |
| 16 | Eggbert | Jump on an egg, pick it up, and throw it back. |
| 24 | The Black Bunny | He hops on you. Jump over his shockwaves. |
| 32 | Tornado Bunny | Zap the tornadoes. Hold Up to zap up high. |
| 40 | The Scarecrow | He sends packs of crows and throws pumpkins. Throw the pumpkins back at him. |
| 48 | The Pink Fireball | She fills the sky with fire in spirals, waves, and rings. Hit her when she rests low. |
| 56 | The Moon Bunny | From the game Bunny Madness. When she swoops down, zap her moon rocks. Then she hides and hops. Watch her shadow and throw things at her. Then jump on her helmet. |
| 64 | Carrot Boom | He has 4 moves: carrot bombs, a tornado dance, hide and seek under the ground, and garden time. When he waters his carrots, his butt is in the air. Hit it to do double damage! If you are hurt, a heart falls after each move. |

## Change the game

| File | What is in it |
|---|---|
| `main.py` | Title screen, level grid, and ending |
| `game.py` | What happens in a level |
| `entities.py` | The bunny, pigs, items, and power-ups. Speed and jump numbers are at the top. |
| `bosses.py` | The bosses |
| `story.py` | The movie at the start and the ending |
| `levels.py` | How the levels are built, the worlds, and the boss list |
| `art.py` | How everything looks |
| `sounds.py` | Sound effects and music |

To start over, delete `save.json`.

## License

This game is free software under the GNU General Public License, version 3 or later. See `LICENSE`.
