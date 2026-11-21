"""Regenerates assets/images/*.png (placeholder art, same designs as the Python game).
Needs Pillow:  pip install pillow     Run:  python tools/make_assets.py
Replace any PNG with your own art of the same name and size; the game loads whatever is there."""
import math
import pathlib
import random

from PIL import Image, ImageDraw

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "images"
SS = 4   # draw 4x bigger, then shrink, for smooth edges


def make(name, w, h, draw):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = lambda pts: [(x * SS, y * SS) for x, y in pts]
    draw(d, s)
    im.resize((w, h), Image.LANCZOS).save(OUT / f"{name}.png")


def ship(d, s):
    d.polygon(s([(27, 46), (32, 58), (37, 46)]), fill=(255, 170, 40, 255))
    d.polygon(s([(32, 6), (52, 52), (32, 43), (12, 52)]), fill=(190, 210, 235, 255), outline=(255, 255, 255, 255), width=SS * 2)
    d.ellipse(s([(27, 22), (37, 32)]), fill=(70, 140, 220, 255))


def rock(d, s):
    rnd = random.Random(7)
    pts = [(32 + rnd.uniform(21, 29) * math.cos(2 * math.pi * k / 14), 32 + rnd.uniform(21, 29) * math.sin(2 * math.pi * k / 14)) for k in range(14)]
    d.polygon(s(pts), fill=(120, 105, 92, 255), outline=(190, 175, 160, 255), width=SS * 2)
    for _ in range(3):
        cx, cy, cr = rnd.uniform(20, 44), rnd.uniform(20, 44), rnd.uniform(3, 6)
        d.ellipse(s([(cx - cr, cy - cr), (cx + cr, cy + cr)]), fill=(85, 74, 66, 255))


def drifter(d, s):
    d.ellipse(s([(8, 26), (56, 46)]), fill=(70, 170, 90, 255), outline=(190, 255, 200, 255), width=SS)
    d.ellipse(s([(22, 14), (42, 34)]), fill=(150, 230, 255, 200), outline=(220, 250, 255, 255), width=SS)
    for k in range(5):
        x = 14 + k * 9
        d.ellipse(s([(x - 2, 34), (x + 2, 38)]), fill=(255, 255, 120, 255) if k % 4 == 0 else (60, 90, 60, 255))


def chaser(d, s):
    d.polygon(s([(27, 46), (32, 58), (37, 46)]), fill=(255, 200, 60, 255))
    d.polygon(s([(32, 6), (48, 52), (32, 42), (16, 52)]), fill=(210, 60, 60, 255), outline=(255, 200, 200, 255), width=SS)
    d.ellipse(s([(28, 22), (36, 30)]), fill=(255, 240, 120, 255))


def bullet(d, s):
    d.polygon(s([(6, 0), (11, 8), (11, 24), (6, 27), (1, 24), (1, 8)]), fill=(255, 230, 80, 255))


def wormhole(d, s):
    for k in range(8):
        r, c = 60 - k * 7, 255 - k * 22
        d.ellipse(s([(64 - r, 64 - r), (64 + r, 64 + r)]), outline=(c // 2, 80 + k * 10, c, 255), width=SS * 3)
    for a in range(4):
        d.arc(s([(12, 12), (116, 116)]), a * 90, a * 90 + 50, fill=(210, 170, 255, 255), width=SS * 5)
        d.arc(s([(28, 28), (100, 100)]), a * 90 + 45, a * 90 + 95, fill=(150, 210, 255, 255), width=SS * 4)
    d.ellipse(s([(50, 50), (78, 78)]), fill=(8, 0, 25, 255))


def powerup(color, kind):
    def draw(d, s):
        d.ellipse(s([(1, 1), (31, 31)]), fill=(20, 25, 45, 255), outline=color, width=SS * 2)
        if kind == "speed":
            d.polygon(s([(18, 4), (8, 18), (15, 18), (13, 28), (24, 13), (17, 13)]), fill=color)
        elif kind == "health":
            d.rectangle(s([(13, 7), (19, 25)]), fill=color)
            d.rectangle(s([(7, 13), (25, 19)]), fill=color)
        elif kind == "ammo":
            for x in (8, 14, 20):
                d.rectangle(s([(x, 8), (x + 3, 24)]), fill=color)
        else:
            d.ellipse(s([(7, 7), (24, 24)]), outline=color, width=SS * 3)
    return draw


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    make("ship", 64, 64, ship); make("rock", 64, 64, rock)
    make("drifter", 64, 64, drifter); make("chaser", 64, 64, chaser)
    make("bullet", 12, 28, bullet); make("wormhole", 128, 128, wormhole)
    make("speed", 32, 32, powerup((255, 220, 60, 255), "speed")); make("health", 32, 32, powerup((80, 230, 110, 255), "health"))
    make("shield", 32, 32, powerup((90, 220, 255, 255), "shield")); make("ammo", 32, 32, powerup((255, 150, 60, 255), "ammo"))
    print("wrote", len(list(OUT.glob("*.png"))), "images to", OUT)
