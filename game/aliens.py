"""Alien ships. Each type has its own movement + AI in ``think``.

drifter    wanders along a sine-wave path, never shoots
chaser     homes in on the ship with a limited turn rate and rams it
sniper     keeps its distance, strafes and fires lead-aimed shots
swarm      a group that orbits the ship and fires from all sides
seeker     patrols until it detects you (even when cloaked, within its detect range), then hunts
teleporter blinks to a random spot around you and fires a burst
minelayer  patrols the map dropping proximity mines
mothership boss: keeps its distance, fires aimed bursts and rings, launches chasers
"""
import math
import random

from .config import settings
from .constants import ANGLE_SIGN
from .sprites import AnimatedSprite


class Alien(AnimatedSprite):
    kind = "drifter"
    faces_heading = True
    needs_target = True          # no visible ship -> wander instead of thinking
    detect_range = 0.0           # >0: notices hidden (cloaked / nebula) ships this close

    def __init__(self, x, y, level, overrides=None):
        cfg = dict(settings.get(f"aliens.{self.kind}"))
        cfg.update(overrides or {})
        super().__init__(settings.get(f"graphics.alien_{self.kind}"))
        self.cfg = cfg
        grow = 1 + settings.get("difficulty.alien_health_per_level") * max(0, level - cfg["min_level"])
        self.max_health = cfg["health"] * grow
        self.health = self.max_health
        self.speed = float(cfg["speed"])
        self.hit_radius = 0.5 * min(self.width, self.height) * 0.75
        self.vx = self.vy = 0.0
        self.heading = random.uniform(0, 360)      # bearing, degrees clockwise from up
        self.t = random.uniform(0, 10)
        interval = float(cfg.get("fire_interval", 0))
        self.fire_timer = random.uniform(0.5, max(0.6, interval)) if interval > 0 else 1e9
        self.flash = 0.0
        self.ram_cd = 0.0
        self.minion = False
        self.charging = False
        self.target = None                         # nearest ship, chosen every frame
        self.center_x, self.center_y = x, y

    # -- helpers
    def to_ship(self, ctx):
        dx, dy = ctx.world.delta(self.center_x, self.center_y,
                                 self.target.center_x, self.target.center_y)
        return dx, dy, math.hypot(dx, dy)

    def take_damage(self, amount):
        self.health -= amount
        self.flash = 0.15

    def set_velocity_toward(self, dx, dy, speed):
        d = math.hypot(dx, dy) or 1.0
        self.vx, self.vy = dx / d * speed, dy / d * speed

    # -- per frame
    def think(self, dt, ctx):
        pass

    def wander(self, dt):
        """Nothing to chase (everyone is hidden): drift about aimlessly."""
        self.charging = False
        self.heading = (self.heading + random.uniform(-40, 40) * dt) % 360
        rad = math.radians(self.heading)
        self.vx, self.vy = math.sin(rad) * self.speed * 0.5, math.cos(rad) * self.speed * 0.5

    def update_alien(self, dt, ctx):
        self.t += dt
        self.target = ctx.nearest_ship(self.center_x, self.center_y, self)
        if self.target is None and self.needs_target:
            self.wander(dt)
        else:
            self.think(dt, ctx)
        self.center_x += self.vx * dt
        self.center_y += self.vy * dt
        ctx.world.wrap(self)
        self.ram_cd = max(0.0, self.ram_cd - dt)
        self.flash = max(0.0, self.flash - dt)
        if self.faces_heading and (self.vx or self.vy):
            self.angle = ANGLE_SIGN * math.degrees(math.atan2(self.vx, self.vy))
        hit_blink = self.flash > 0 and int(self.flash * 40) % 2 == 0
        charge_blink = self.charging and int(self.t * 20) % 2 == 0
        self.alpha = 140 if (hit_blink or charge_blink) else 255
        self.animate(dt)


class Drifter(Alien):
    kind = "drifter"
    faces_heading = False
    needs_target = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.base = math.radians(random.choice((45, 135, 225, 315)))

    def think(self, dt, ctx):
        c = self.cfg
        bx, by = math.sin(self.base), math.cos(self.base)
        wobble = c["wave_amp"] * c["wave_freq"] * math.cos(c["wave_freq"] * self.t)
        self.vx = bx * self.speed - by * wobble
        self.vy = by * self.speed + bx * wobble
        self.angle += 30 * dt


class Chaser(Alien):
    kind = "chaser"

    def think(self, dt, ctx):
        dx, dy, _ = self.to_ship(ctx)
        wanted = math.degrees(math.atan2(dx, dy))
        diff = (wanted - self.heading + 180) % 360 - 180
        turn = self.cfg["turn_rate"] * dt
        self.heading += max(-turn, min(turn, diff))
        rad = math.radians(self.heading)
        self.vx, self.vy = math.sin(rad) * self.speed, math.cos(rad) * self.speed


class Sniper(Alien):
    kind = "sniper"
    faces_heading = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.strafe = random.choice((-1, 1))
        self.strafe_timer = random.uniform(2, 4)

    def think(self, dt, ctx):
        dx, dy, dist = self.to_ship(ctx)
        ux, uy = (dx / dist, dy / dist) if dist else (0.0, 1.0)
        keep = self.cfg["keep_distance"]
        radial = 1.0 if dist > keep + 40 else -1.0 if dist < keep - 40 else 0.0
        self.strafe_timer -= dt
        if self.strafe_timer <= 0:
            self.strafe, self.strafe_timer = -self.strafe, random.uniform(2, 4)
        mx = ux * radial - uy * self.strafe * 0.7
        my = uy * radial + ux * self.strafe * 0.7
        self.set_velocity_toward(mx, my, self.speed)
        self.angle = ANGLE_SIGN * math.degrees(math.atan2(dx, dy))

        self.fire_timer -= dt
        self.charging = self.fire_timer < 0.4
        if self.fire_timer <= 0:
            self.fire_timer = self.cfg["fire_interval"]
            t = dist / max(1.0, self.cfg["bullet_speed"])      # lead the target
            svx, svy = self.target.velocity()
            aim = math.degrees(math.atan2(dx + svx * t, dy + svy * t))
            ctx.fire_alien_bullet(self, aim)


class Swarm(Alien):
    kind = "swarm"
    faces_heading = False

    def __init__(self, x, y, level, slot=0, group=1, group_phase=0.0, overrides=None):
        super().__init__(x, y, level, overrides)
        self.slot, self.group, self.group_phase = slot, max(1, group), group_phase

    def think(self, dt, ctx):
        c = self.cfg
        ang = math.radians(c["orbit_speed"] * ctx.time + self.group_phase
                           + self.slot * 360.0 / self.group)
        dx, dy, dist = self.to_ship(ctx)
        tx = dx + math.sin(ang) * c["orbit_radius"]
        ty = dy + math.cos(ang) * c["orbit_radius"]
        self.set_velocity_toward(tx, ty, min(self.speed, math.hypot(tx, ty) * 3))
        self.angle = ANGLE_SIGN * math.degrees(math.atan2(dx, dy))
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = c["fire_interval"] * random.uniform(0.8, 1.3)
            ctx.fire_alien_bullet(self, math.degrees(math.atan2(dx, dy)))


class Mothership(Alien):
    kind = "mothership"
    faces_heading = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.spawn_timer = float(self.cfg["spawn_interval"])
        self.volley = 0
        self.ring_offset = 0.0

    def think(self, dt, ctx):
        dx, dy, dist = self.to_ship(ctx)
        keep = self.cfg["keep_distance"]
        radial = 1.0 if dist > keep + 60 else -1.0 if dist < keep - 60 else 0.0
        self.set_velocity_toward(dx, dy, self.speed * radial)
        self.angle += 12 * dt

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.cfg["spawn_interval"]
            ctx.spawn_minion(self)

        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = self.cfg["fire_interval"]
            self.volley += 1
            aim = math.degrees(math.atan2(dx, dy))
            if self.volley % 2:                       # aimed triple burst
                for off in (-14, 0, 14):
                    ctx.fire_alien_bullet(self, aim + off, play_sound=off == 0)
            else:                                      # rotating ring
                n = max(3, int(self.cfg["ring_bullets"]))
                self.ring_offset += 11
                for i in range(n):
                    ctx.fire_alien_bullet(self, self.ring_offset + i * 360.0 / n,
                                          play_sound=i == 0)


class Seeker(Alien):
    kind = "seeker"
    faces_heading = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.detect_range = float(self.cfg["detect_range"])
        self.locked = False

    def wander(self, dt):
        super().wander(dt)                      # patrol while searching
        self.locked = False
        self.angle += 90 * dt                   # scanning spin

    def think(self, dt, ctx):
        dx, dy, dist = self.to_ship(ctx)
        self.locked = True
        wanted = math.degrees(math.atan2(dx, dy))
        diff = (wanted - self.heading + 180) % 360 - 180
        turn = 200 * dt
        self.heading += max(-turn, min(turn, diff))
        rad = math.radians(self.heading)
        boost = 1.4 if dist < 500 else 1.0
        self.vx, self.vy = math.sin(rad) * self.speed * boost, math.cos(rad) * self.speed * boost
        self.angle = ANGLE_SIGN * self.heading
        self.fire_timer -= dt
        self.charging = self.fire_timer < 0.4
        if self.fire_timer <= 0:
            self.fire_timer = self.cfg["fire_interval"]
            ctx.fire_alien_bullet(self, wanted)


class Teleporter(Alien):
    kind = "teleporter"
    faces_heading = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.blink_timer = random.uniform(1.5, float(self.cfg["blink_interval"]))
        self.burst_left = 0
        self.burst_timer = 0.0

    def think(self, dt, ctx):
        dx, dy, dist = self.to_ship(ctx)
        self.set_velocity_toward(dx, dy, self.speed if dist > 200 else 0.0)
        self.angle = ANGLE_SIGN * math.degrees(math.atan2(dx, dy))
        self.blink_timer -= dt
        self.charging = 0 < self.blink_timer < 0.6
        if self.blink_timer <= 0:                  # blink to a spot on a ring around the target
            ang = random.uniform(0, 2 * math.pi)
            ring = float(self.cfg["ring"]) * random.uniform(0.8, 1.2)
            tx, ty = self.target.center_x, self.target.center_y
            self.center_x = tx + math.sin(ang) * ring
            self.center_y = ty + math.cos(ang) * ring
            ctx.world.wrap(self)
            ctx.effect_at(self.center_x, self.center_y, self.hit_radius * 2.5, (200, 120, 255))
            ctx.play_sfx("teleporter_blink")
            self.blink_timer = float(self.cfg["blink_interval"]) * random.uniform(0.8, 1.3)
            self.burst_left = int(self.cfg["burst_count"])
            self.burst_timer = 0.3
        if self.burst_left > 0:
            self.burst_timer -= dt
            if self.burst_timer <= 0:
                self.burst_left -= 1
                self.burst_timer = 0.18
                dx, dy, _ = self.to_ship(ctx)
                ctx.fire_alien_bullet(self, math.degrees(math.atan2(dx, dy)))


class Minelayer(Alien):
    kind = "minelayer"
    needs_target = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.drop_timer = float(self.cfg["mine_interval"])

    def think(self, dt, ctx):
        self.heading = (self.heading + 25 * math.sin(self.t * 0.7) * dt) % 360   # lazy weave
        rad = math.radians(self.heading)
        self.vx, self.vy = math.sin(rad) * self.speed, math.cos(rad) * self.speed
        self.drop_timer -= dt
        if self.drop_timer <= 0:
            self.drop_timer = float(self.cfg["mine_interval"])
            ctx.drop_alien_mine(self)


ALIEN_CLASSES = {"drifter": Drifter, "chaser": Chaser, "sniper": Sniper, "swarm": Swarm,
                 "seeker": Seeker, "teleporter": Teleporter, "minelayer": Minelayer,
                 "mothership": Mothership}
