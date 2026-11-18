"""Saved player profile: in-game credits, owned ships, selected ship. (profile.json)

Credits exist only inside the game - they are earned by playing and spent in the Hangar.
Each player's profile lives on their own machine.
"""
import json

from .config import settings
from .constants import BASE_DIR

PROFILE_PATH = BASE_DIR / "profile.json"


class Profile:
    def __init__(self):
        self.credits = int(settings.get("credits.start_credits"))
        self.owned = ["scout"]
        self.selected = "scout"
        self.best_level = 1
        self.best_score = 0

    def load(self):
        if not PROFILE_PATH.exists():
            return
        try:
            data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self.credits = max(0, int(data.get("credits", self.credits)))
        owned = [s for s in data.get("owned", []) if s in settings.get("ships")]
        self.owned = sorted(set(owned) | {"scout"}, key=lambda s: list(settings.get("ships")).index(s))
        self.selected = data.get("selected", "scout")
        if self.selected not in self.owned:
            self.selected = "scout"
        self.best_level = int(data.get("best_level", 1))
        self.best_score = int(data.get("best_score", 0))

    def save(self):
        try:
            PROFILE_PATH.write_text(json.dumps({
                "credits": self.credits, "owned": self.owned, "selected": self.selected,
                "best_level": self.best_level, "best_score": self.best_score}, indent=2),
                encoding="utf-8")
        except OSError:
            pass

    def buy(self, ship_id):
        """Buy a ship. Returns True if it was bought (or already owned)."""
        if ship_id in self.owned:
            return True
        price = int(settings.get(f"ships.{ship_id}.price", 10 ** 9))
        if self.credits < price:
            return False
        self.credits -= price
        self.owned.append(ship_id)
        self.save()
        return True

    def select(self, ship_id):
        if ship_id in self.owned:
            self.selected = ship_id
            self.save()

    def record(self, level, score):
        self.best_level = max(self.best_level, int(level))
        self.best_score = max(self.best_score, int(score))


profile = Profile()
profile.load()
