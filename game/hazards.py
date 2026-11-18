"""Map hazards (Expedition mode). They are plain data; GameView applies their effects.

blackhole  pulls ships and rocks in and hurts anything that reaches the centre
nebula     a cloud that hides ships inside it from aliens
ion        an ion storm: abilities and shields stop recharging, controls get jittery
flare      a solar flare: a warning band, then a burst that damages everything inside it
"""
import random


class Hazard:
    kind = "hazard"

    def __init__(self, x, y, radius):
        self.x, self.y, self.radius = x, y, radius
        self.vx = self.vy = 0.0
        self.core = 0.0

    def update(self, dt, world):
        self.x = (self.x + self.vx * dt) % world.width
        self.y = (self.y + self.vy * dt) % world.height


class BlackHole(Hazard):
    kind = "blackhole"

    def __init__(self, x, y):
        super().__init__(x, y, 650.0)       # radius = how far the pull reaches
        self.core = 34.0


class Nebula(Hazard):
    kind = "nebula"

    def __init__(self, x, y):
        super().__init__(x, y, random.uniform(200, 300))
        self.vx, self.vy = random.uniform(-8, 8), random.uniform(-8, 8)


class IonStorm(Hazard):
    kind = "ion"

    def __init__(self, x, y):
        super().__init__(x, y, random.uniform(170, 230))
        self.vx, self.vy = random.uniform(-18, 18), random.uniform(-18, 18)


class SolarFlare:
    kind = "flare"
    WARN, ACTIVE = 2.5, 0.8

    def __init__(self, world, thickness=140.0):
        self.vertical = random.random() < 0.5
        self.thickness = thickness
        if self.vertical:
            self.x, self.y = random.uniform(0, world.width), world.height / 2
            self.w, self.h = thickness, world.height
        else:
            self.x, self.y = world.width / 2, random.uniform(0, world.height)
            self.w, self.h = world.width, thickness
        self.t = 0.0
        self.fired = False

    @property
    def phase(self):                 # 0 = warning, 1 = burning
        return 0 if self.t < self.WARN else 1

    @property
    def finished(self):
        return self.t >= self.WARN + self.ACTIVE

    def covers(self, world, x, y, pad=0.0):
        dx, dy = world.delta(self.x, self.y, x, y)
        if self.vertical:
            return abs(dx) < self.thickness / 2 + pad
        return abs(dy) < self.thickness / 2 + pad
