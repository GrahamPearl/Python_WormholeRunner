"""Bullets (all projectile kinds) and the weapon system (selection, ammo, firing)."""
import math

from .config import settings
from .constants import ANGLE_SIGN
from .sprites import AnimatedSprite


class Bullet(AnimatedSprite):
    """kind: 'bolt' flies straight, 'homing' steers to a target, 'mine' sits still and explodes."""

    def __init__(self, graphic, owner, x, y, vx, vy, damage, life, pierce=1,
                 kind="bolt", turn_rate=0.0, blast=0.0, fuse=0.0):
        super().__init__(settings.get(f"graphics.{graphic}"))
        self.gfx = graphic
        self.heal = 0                       # >0: heals an ally it touches
        self.silent = False                 # does not break a cloak
        self.player_id = 0                  # who fired it (for scoring)
        self.owner = owner                  # "player" or "alien"
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.life = life
        self.pierce = max(1, int(pierce))   # targets it can pass through
        self.kind = kind
        self.turn_rate = turn_rate
        self.blast = blast
        self.fuse = fuse
        self.arm = 0.5                      # mines ignore triggers briefly
        self.hit_ids = set()
        self.hit_radius = max(4.0, 0.25 * (self.width + self.height))
        self.center_x, self.center_y = x, y
        self._point()

    def _point(self):
        if self.kind != "mine" and (self.vx or self.vy):
            self.angle = ANGLE_SIGN * math.degrees(math.atan2(self.vx, self.vy))

    def _steer(self, dt, world, aliens, rocks):
        best, best_d = None, 800.0
        for group in (aliens, rocks):        # prefer aliens, then rocks
            for t in group:
                dx, dy = world.delta(self.center_x, self.center_y, t.center_x, t.center_y)
                d = math.hypot(dx, dy)
                if d < best_d:
                    best, best_d = (dx, dy), d
            if best:
                break
        if not best:
            return
        speed = math.hypot(self.vx, self.vy) or 1.0
        heading = math.atan2(self.vx, self.vy)
        wanted = math.atan2(best[0], best[1])
        diff = (wanted - heading + math.pi) % (2 * math.pi) - math.pi
        limit = math.radians(self.turn_rate) * dt
        heading += max(-limit, min(limit, diff))
        self.vx, self.vy = math.sin(heading) * speed, math.cos(heading) * speed

    def update_bullet(self, dt, world, aliens, rocks):
        if self.kind == "mine":
            self.fuse -= dt
            self.arm -= dt
            self.angle += 60 * dt
            self.animate(dt)
            return
        if self.kind == "homing" and self.owner == "player":
            self._steer(dt, world, aliens, rocks)
        self.center_x += self.vx * dt
        self.center_y += self.vy * dt
        world.wrap(self)
        self.life -= dt
        self._point()
        self.animate(dt)


class WeaponSystem:
    """Weapon slots 1-9 are defined under 'weapons' in the settings."""

    def __init__(self, overrides=None):
        """overrides: {slot: weapon settings} - a ship's own weapon takes slot 7."""
        self.overrides = overrides or {}
        self.slot = 1
        self.cooldown = 0.0
        self.ammo = {s: int(self.cfg(s).get("ammo", -1)) for s in range(1, 10)}

    def cfg(self, slot):
        return self.overrides.get(slot) or settings.get(f"weapons.w{slot}") or {}

    def unlocked(self, slot, level):
        c = self.cfg(slot)
        return bool(c.get("enabled")) and level >= c.get("unlock_level", 1)

    def select(self, slot, level):
        if self.unlocked(slot, level):
            changed = slot != self.slot
            self.slot = slot
            return changed
        return False

    def update(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)

    def add_ammo(self):
        for slot in range(1, 10):
            c = self.cfg(slot)
            if c.get("ammo", -1) > 0:
                cap = 2 * c["ammo"]
                self.ammo[slot] = min(cap, self.ammo[slot] + c.get("ammo_pack", 0))

    def fire(self, ship, dmg_mult=1.0):
        """Return (bullets, sound_event). Nothing is fired while cooling down."""
        c = self.cfg(self.slot)
        if self.cooldown > 0 or not c:
            return [], None
        if self.ammo[self.slot] == 0:
            self.cooldown = 0.3
            return [], "no_ammo"
        if self.ammo[self.slot] > 0:
            self.ammo[self.slot] -= 1
        self.cooldown = c["cooldown"]

        graphic = c.get("graphic") or f"bullet_w{self.slot}"
        damage = c["damage"] * dmg_mult
        rad = math.radians(ship.bearing)
        dx, dy = math.sin(rad), math.cos(rad)
        nose = ship.hit_radius + 14
        svx, svy = ship.velocity()
        bullets = []
        if c["type"] == "pulse":                 # instant blast centred on the ship
            pulse = Bullet(graphic, "player", ship.center_x, ship.center_y, 0.0, 0.0,
                           damage, 999.0, kind="mine", blast=c["blast_radius"], fuse=0.0)
            pulse.arm = 0.0
            bullets.append(pulse)
        elif c["type"] == "mine":
            bullets.append(Bullet(graphic, "player",
                                  ship.center_x - dx * (nose + 16), ship.center_y - dy * (nose + 16),
                                  0.0, 0.0, damage, 999.0, kind="mine",
                                  blast=c["blast_radius"], fuse=c["fuse"]))
        else:
            n = max(1, int(c["count"]))
            speed = max(1.0, c["speed"])
            for i in range(n):
                off = 0.0 if n == 1 else -c["spread"] / 2 + c["spread"] * i / (n - 1)
                r = math.radians(ship.bearing + off)
                bx, by = math.sin(r), math.cos(r)
                bullets.append(Bullet(
                    graphic, "player", ship.center_x + bx * nose, ship.center_y + by * nose,
                    bx * speed + svx, by * speed + svy, damage, c["range"] / speed,
                    pierce=c["pierce"], kind="homing" if c["type"] == "homing" else "bolt",
                    turn_rate=c["turn_rate"]))
        for b in bullets:
            b.heal = c.get("heal", 0)
            b.silent = bool(c.get("silent", False))
        return bullets, c.get("sound")
