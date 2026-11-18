"""The play area. It wraps around: leaving one edge re-enters on the opposite one."""
import random


class World:
    def __init__(self, width, height):
        self.width = float(width)
        self.height = float(height)

    @property
    def center(self):
        return self.width / 2, self.height / 2

    def wrap(self, sprite):
        sprite.center_x = sprite.center_x % self.width
        sprite.center_y = sprite.center_y % self.height

    def delta(self, ax, ay, bx, by):
        """Shortest vector from a to b on the wrapped world."""
        dx = (bx - ax) % self.width
        dy = (by - ay) % self.height
        if dx > self.width / 2:
            dx -= self.width
        if dy > self.height / 2:
            dy -= self.height
        return dx, dy

    def random_pos(self):
        return random.uniform(0, self.width), random.uniform(0, self.height)
