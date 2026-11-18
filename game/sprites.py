"""Sprite classes: Ship, Rock, PowerUp, Wormhole and the tiled Background."""
import math
import random

import arcade

from .assets import load_frames
from .config import settings
from .constants import ANGLE_SIGN
from .physics import rotate

POWERUP_KINDS = ("speed", "health", "shield", "ammo")
ROCK_TINTS = {"ice": (150, 205, 255, 255), "explosive": (255, 120, 90, 255),
              "gold": (255, 215, 70, 255), "metal": (175, 180, 195, 255)}
ROCK_SIZE_SCALE = {3: 1.6, 2: 1.0, 1: 0.6}   # size class -> scale multiplier


class AnimatedSprite(arcade.Sprite):
    """A sprite that plays a tile sequence described by a graphics spec."""

    def __init__(self, spec, scale_mult=1.0):
        frames = load_frames(spec)
        base_scale = float(spec.get("scale", 1.0)) * scale_mult
        super().__init__(frames[0], scale=base_scale)
        self.frames = frames
        self.base_scale = base_scale
        self.fps = float(spec.get("fps", 0))
        self._anim_time = random.random()
        self._frame = 0

    def animate(self, dt):
        if self.fps <= 0 or len(self.frames) < 2:
            return
        self._anim_time += dt
        idx = int(self._anim_time * self.fps) % len(self.frames)
        if idx != self._frame:
            self._frame = idx
            self.texture = self.frames[idx]


def control_step(bearing, speed, dt, up, down, left, right, boosted, mults=(1.0, 1.0, 1.0)):
    """Turning and throttle. Shared by the real ship and the joiner's predicted ship."""
    cfg = settings.get
    boost = cfg("ship.boost_multiplier") if boosted else 1.0
    speed_m, accel_m, turn_m = mults
    if left:
        bearing -= cfg("ship.turn_rate") * turn_m * dt
    if right:
        bearing += cfg("ship.turn_rate") * turn_m * dt
    if up:
        speed += cfg("ship.acceleration") * accel_m * boost * dt
    if down:
        speed -= cfg("ship.acceleration") * accel_m * boost * 1.5 * dt
    speed = max(0.0, min(speed, cfg("ship.max_speed") * speed_m * boost))
    return bearing % 360.0, speed


class Ship(AnimatedSprite):
    def __init__(self, cfg=None, tint=None):
        cfg = cfg or settings.get("ships.scout")
        super().__init__(settings.get(f"graphics.{cfg.get('graphic', 'ship')}")
                         or settings.get("graphics.ship"))
        if tint:
            self.color = tint
        self.cfg = cfg
        self.hit_radius = 0.5 * min(self.width, self.height) * 0.55
        self.max_health = float(cfg.get("health", settings.get("ship.max_health")))
        self.health = self.max_health
        self.speed_mult = cfg.get("speed_mult", 1.0)
        self.accel_mult = cfg.get("accel_mult", 1.0)
        self.turn_mult = cfg.get("turn_mult", 1.0)
        self.bearing = 0.0          # clockwise degrees from straight up
        self.speed = 0.0
        self.drift_x = 0.0          # velocity added by gravity
        self.drift_y = 0.0
        self.grace_timer = 0.0      # after a hit
        self.shield_timer = 0.0     # invincibility power-up
        self.boost_timer = 0.0      # speed power-up
        # special ability (SHIFT) and always-on traits
        self.ability = dict(cfg.get("ability") or {})
        self.ability_type = self.ability.get("type", "")
        self.ability_cd = 0.0
        self.active = 0.0           # seconds left of a timed ability
        passive = cfg.get("passive") or {}
        self.shield_max = float(passive.get("shield_max", 0.0))
        self.shield_hp = self.shield_max
        self.shield_rate = float(passive.get("shield_rate", 0.0))
        self.shield_delay = float(passive.get("shield_delay", 0.0))
        self.shield_wait = 0.0
        self.regen = float(passive.get("regen", 0.0))
        self.regen_delay = float(passive.get("regen_delay", 2.0))
        self.since_hit = 99.0
        self.in_nebula = False      # set by the game each frame
        self.jammed = False         # inside an ion storm

    # -- ability states
    def _on(self, kind):
        return self.ability_type == kind and self.active > 0

    cloaked = property(lambda self: self._on("cloak"))
    phased = property(lambda self: self._on("hyperspace"))
    deflecting = property(lambda self: self._on("deflect"))
    healing = property(lambda self: self._on("repair"))

    @property
    def mults(self):
        return (self.speed_mult, self.accel_mult, self.turn_mult)

    def velocity(self):
        """Current velocity vector (facing direction * speed + gravity drift)."""
        rad = math.radians(self.bearing)
        return (math.sin(rad) * self.speed + self.drift_x,
                math.cos(rad) * self.speed + self.drift_y)

    @property
    def invulnerable(self):
        return self.grace_timer > 0 or self.shield_timer > 0

    def update_ship(self, dt, up, down, left, right, ax, ay, world):
        cfg = settings.get
        self.bearing, self.speed = control_step(self.bearing, self.speed, dt, up, down,
                                                left, right, self.boost_timer > 0, self.mults)

        # Gravity changes the drift velocity, which slowly damps away.
        self.drift_x += ax * dt
        self.drift_y += ay * dt
        damp = max(0.0, 1.0 - cfg("physics.drift_damping") * dt)
        self.drift_x *= damp
        self.drift_y *= damp

        rad = math.radians(self.bearing)
        self.center_x += (math.sin(rad) * self.speed + self.drift_x) * dt
        self.center_y += (math.cos(rad) * self.speed + self.drift_y) * dt

        world.wrap(self)

        self.angle = ANGLE_SIGN * self.bearing
        self.grace_timer = max(0.0, self.grace_timer - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.boost_timer = max(0.0, self.boost_timer - dt)
        self.active = max(0.0, self.active - dt)
        self.since_hit += dt
        if not self.jammed:                       # ion storms stop all recharging
            self.ability_cd = max(0.0, self.ability_cd - dt)
            self.shield_wait = max(0.0, self.shield_wait - dt)
            if self.shield_max > 0 and self.shield_wait <= 0:
                self.shield_hp = min(self.shield_max, self.shield_hp + self.shield_rate * dt)
            if self.regen > 0 and self.since_hit >= self.regen_delay:
                self.health = min(self.max_health, self.health + self.regen * dt)
        blink = self.grace_timer > 0 and int(self.grace_timer * 12) % 2 == 0
        self.alpha = 110 if blink else 255
        if self.cloaked:
            self.alpha = 100
        elif self.phased:
            self.alpha = 70
        self.animate(dt)


class Rock(AnimatedSprite):
    def __init__(self, size_class, x, y, vx, vy, kind="normal"):
        super().__init__(settings.get("graphics.rock"), ROCK_SIZE_SCALE[size_class])
        self.kind = kind                 # normal | ice | explosive | gold | metal
        self.hp = 3 if kind == "metal" else 1
        if kind in ROCK_TINTS:
            self.color = ROCK_TINTS[kind]
        self.size_class = size_class
        self.mass = ROCK_SIZE_SCALE[size_class] ** 2    # bigger rock, stronger pull
        self.hit_radius = 0.5 * min(self.width, self.height) * 0.8
        self.vx, self.vy = vx, vy
        self.spin = random.uniform(-50, 50)
        self.cooldown = 0.0        # a fresh fragment can't be hit again immediately
        self.center_x, self.center_y = x, y

    def update_rock(self, dt, world):
        self.center_x += self.vx * dt
        self.center_y += self.vy * dt
        world.wrap(self)
        self.angle += self.spin * dt
        self.cooldown = max(0.0, self.cooldown - dt)
        self.animate(dt)

    def split(self):
        """Return smaller rocks (empty list for the smallest size). Ice shatters into three."""
        if self.size_class <= 1:
            return []
        angle = settings.get("rocks.split_angle")
        factor = settings.get("rocks.split_speed")
        offsets = (angle, 0.0, -angle) if self.kind == "ice" else (angle, -angle)
        kids = []
        for off in offsets:
            vx, vy = rotate(self.vx, self.vy, off)
            length = math.hypot(vx, vy) or 1.0
            ox = vx / length * self.hit_radius * 0.5
            oy = vy / length * self.hit_radius * 0.5
            kid = Rock(self.size_class - 1, self.center_x + ox, self.center_y + oy,
                       vx * factor, vy * factor, "ice" if self.kind == "ice" else "normal")
            kid.cooldown = 0.6
            kids.append(kid)
        return kids


class PowerUp(AnimatedSprite):
    """Power-ups, plus the objective items (crystal, pod) which never expire."""

    def __init__(self, kind, x, y, permanent=False, vx=0.0, vy=0.0):
        spec = (settings.get(f"graphics.powerup_{kind}")
                or settings.get(f"graphics.objective_{kind}"))
        super().__init__(spec)
        self.kind = kind
        self.permanent = permanent
        self.vx, self.vy = vx, vy
        self.hit_radius = 0.5 * min(self.width, self.height)
        self.life = float(settings.get("timing.powerup_lifetime"))
        self._age = 0.0
        self.center_x, self.center_y = x, y

    def update_powerup(self, dt, world=None):
        self._age += dt
        if self.vx or self.vy:
            self.center_x += self.vx * dt
            self.center_y += self.vy * dt
            if world:
                world.wrap(self)
        self.scale = self.base_scale * (1.0 + 0.12 * math.sin(self._age * 5))
        if self.permanent:
            self.alpha = 255
        else:
            self.life -= dt
            self.alpha = 120 if (self.life < 2.0 and int(self.life * 6) % 2 == 0) else 255
        self.animate(dt)

    @property
    def expired(self):
        return (not self.permanent) and self.life <= 0


class Freighter(AnimatedSprite):
    """The ship you escort in an Escort objective."""

    def __init__(self, x, y):
        super().__init__(settings.get("graphics.objective_freighter"))
        self.max_health = float(settings.get("objectives.freighter_health"))
        self.health = self.max_health
        self.hit_radius = 0.5 * min(self.width, self.height) * 0.7
        d = math.sqrt(0.5) * 55.0
        self.vx, self.vy = random.choice((-d, d)), random.choice((-d, d))
        self.hit_cd = 0.0
        self.center_x, self.center_y = x, y

    def update_freighter(self, dt, world):
        self.center_x += self.vx * dt
        self.center_y += self.vy * dt
        world.wrap(self)
        self.hit_cd = max(0.0, self.hit_cd - dt)
        self.angle = ANGLE_SIGN * math.degrees(math.atan2(self.vx, self.vy))


class Wormhole(AnimatedSprite):
    FADE = 0.7

    def __init__(self, x, y, life_scale=1.0):
        super().__init__(settings.get("graphics.wormhole"))
        self.full_radius = 0.5 * min(self.width, self.height) * 0.45
        self.lifetime = float(settings.get("timing.wormhole_lifetime")) * life_scale
        self.age = 0.0
        self.center_x, self.center_y = x, y
        self.scale = self.base_scale * 0.01

    def _grow(self):
        return max(0.01, min(1.0, self.age / self.FADE, (self.lifetime - self.age) / self.FADE))

    def update_wormhole(self, dt):
        self.age += dt
        self.scale = self.base_scale * self._grow()
        self.angle += 40 * dt
        self.animate(dt)

    @property
    def expired(self):
        return self.age >= self.lifetime

    @property
    def can_enter(self):
        return self._grow() >= 0.6


class Background:
    """Tiles the screen with a tile sequence (picks a tile per cell)."""

    def __init__(self, width, height):
        spec = settings.get("graphics.background")
        self.frames = load_frames(spec)
        self.fps = float(spec.get("fps", 0))
        scale = float(spec.get("scale", 1.0))
        tile_w = max(8, spec["frame_w"] * scale)
        tile_h = max(8, spec["frame_h"] * scale)
        self.sprites = arcade.SpriteList()
        self._offsets = []
        self._time = 0.0
        cols = int(width // tile_w) + 1
        rows = int(height // tile_h) + 1
        for i in range(cols):
            for j in range(rows):
                offset = (i * 7 + j * 13) % len(self.frames)
                sprite = arcade.Sprite(self.frames[offset], scale=scale)
                sprite.center_x = (i + 0.5) * tile_w
                sprite.center_y = (j + 0.5) * tile_h
                self.sprites.append(sprite)
                self._offsets.append(offset)

    def update(self, dt):
        if self.fps <= 0 or len(self.frames) < 2:
            return
        self._time += dt
        step = int(self._time * self.fps)
        for sprite, offset in zip(self.sprites, self._offsets):
            sprite.texture = self.frames[(offset + step) % len(self.frames)]

    def draw(self):
        self.sprites.draw()
