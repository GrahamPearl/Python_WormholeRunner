"""A player = one ship + its weapons, score, credits and (for the remote player) its inputs."""
from .config import settings
from .sprites import Ship
from .weapons import WeaponSystem

TINTS = {1: None, 2: (130, 255, 160, 255)}      # player 2's ship is tinted green


class Player:
    def __init__(self, pid, name, local=True, ship_id="scout"):
        self.id, self.name, self.local = pid, name, local
        self.ship_id = ship_id if settings.get(f"ships.{ship_id}") else "scout"
        self.keys = set()
        self.last_want = 1
        self.last_pk = 0
        self.ability_prev = False
        self.reset()

    def reset(self):
        """Fresh ship, weapons, score and perks (new game)."""
        cfg = settings.get(f"ships.{self.ship_id}")
        self.ship = Ship(cfg, TINTS.get(self.id))
        weapon = cfg.get("weapon") or None
        self.weapons = WeaponSystem({7: weapon} if weapon else None)
        self.score = 0.0
        self.credits_run = 0.0
        self.alive = True
        self.thrust_cooldown = 0.0
        self.last_want = 1
        self.perks = {}
        self.perk_options = []
        self.perk_choice = 0
        self.dmg_mult = 1.0
        self.cd_mult = 1.0
        self.credit_mult = 1.0
        self.magnet = 0.0

    def revive(self):
        """Back in the game at the start of the next level, at half health."""
        self.alive = True
        self.ship.health = max(self.ship.health, self.ship.max_health * 0.5)
        self.ship.grace_timer = 1.5
