#!/bin/bash
# Starts the game on the Steam Deck. Add this file to Steam as a Non-Steam Game.
# It needs uv (https://astral.sh/uv), which downloads Python and Pyxel itself.
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"
exec uv run main.py --fullscreen
