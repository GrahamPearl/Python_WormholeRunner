"""Small physics helpers."""
import math


def gravity_accel(dx, dy, mass, strength, softening, max_accel):
    """Acceleration toward a rock that is (dx, dy) away (use World.delta for wrap-around).

    Newtonian-style: grows with the rock's mass, falls with distance squared.
    """
    dist_sq = dx * dx + dy * dy + softening * softening
    dist = math.sqrt(dist_sq)
    accel = min(strength * mass / dist_sq, max_accel)
    return accel * dx / dist, accel * dy / dist


def rotate(x, y, degrees):
    rad = math.radians(degrees)
    c, s = math.cos(rad), math.sin(rad)
    return x * c - y * s, x * s + y * c
