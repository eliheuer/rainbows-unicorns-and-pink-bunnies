# Saves your progress to save.json next to the game.
import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")


def new_save():
    return {
        "unlocked": 1,     # highest level you can play
        "carrots": {},     # level number (as text) -> best carrots saved (0-3)
        "beaten": [],      # levels you have beaten
        "coins": 0,        # coins you are carrying
        "power": 1,        # lightning power (1-3)
        "seen_intro": False,  # True after you watch the story at the start
    }


def load():
    data = new_save()
    try:
        with open(SAVE_PATH) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    return data


def write(data):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f, indent=1)
    except OSError:
        pass
