# Playing on the Steam Deck

The Steam Deck runs Linux, so the game runs on it with no Steam account
tricks. You add it to Steam as a "Non-Steam Game" and it shows up in
Gaming Mode with the other games.

## One time setup on the Deck

1. Hold the power button and pick **Switch to Desktop**.
2. Open **Konsole** and set a password: `passwd`
3. Turn on SSH: `sudo systemctl enable --now sshd`
4. Find the Deck's address: `ip -4 addr show wlan0 | grep inet`

## From another computer

```sh
ssh deck@<the address>
curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir -p ~/Games && cd ~/Games
git clone https://github.com/eliheuer/rainbows-unicorns-and-pink-bunnies.git
cd rainbows-unicorns-and-pink-bunnies
~/.local/bin/uv sync
```

## Add it to Steam

1. In Desktop Mode open Steam. Pick **Games > Add a Non-Steam Game to My Library**.
2. Click **Browse**, set the file type to **All Files**, and pick
   `~/Games/rainbows-unicorns-and-pink-bunnies/steamdeck/run.sh`.
3. Right click the new entry, pick **Properties**, and rename it
   "Rainbows, Unicorns, and Pink Bunnies". Click the blank picture to set artwork.
4. Under **Controller**, pick the **Gamepad** layout if it is not already on.
5. Go back to Gaming Mode. The game is in your library under **Non-Steam**.

The D-pad or the left stick moves, A jumps, B zaps, X or Y grabs, Start pauses,
and the Select button goes back.
Progress saves to `save.json` in the game folder.

## The quick way, over SSH

`steamdeck/install_steam.py` does the "Add it to Steam" part for you, with
library art drawn by `steamdeck/make_art.py`. On the Deck, with Steam closed:

```sh
steam -shutdown
cd ~/Games/rainbows-unicorns-and-pink-bunnies && uv run steamdeck/install_steam.py
steam &
```
