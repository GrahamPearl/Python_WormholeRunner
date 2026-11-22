"""Draws every sprite sheet in assets/images/ (placeholder art). Needs Pillow:  pip install pillow
Run:  python tools/make_assets.py
Each PNG is a row of animation frames. Replace any PNG with your own art of the same name and tile size,
or change the tile size / frame count / fps in the Game Editor (Images section)."""
import math
import pathlib
import random

from PIL import Image, ImageDraw

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "images"
SS = 4


def sheet(name, w, h, frames, draw):
    im = Image.new("RGBA", (w * frames * SS, h * SS), (0, 0, 0, 0))
    for i in range(frames):
        frame = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        draw(d, lambda pts, k=SS: [(x * k, y * k) for x, y in pts], i)
        im.paste(frame, (i * w * SS, 0))
    im.resize((w * frames, h), Image.LANCZOS).save(OUT / name)


def box(c1, c2):
    return [(c1[0], c1[1]), (c2[0], c2[1])]


def ship(body, flame=(255, 170, 40, 255)):
    def draw(d, s, i):
        fl = 6 + (i % 2) * 6 + (i // 2) * 2
        d.polygon(s([(27, 46), (32, 46 + fl), (37, 46)]), fill=flame)
        body(d, s, i)
    return draw


def poly(pts, fill, outline=(255, 255, 255, 255)):
    return lambda d, s: d.polygon(s(pts), fill=fill, outline=outline, width=SS * 2)


def bodies():
    def scout(d, s, i):
        d.polygon(s([(32, 6), (52, 52), (32, 43), (12, 52)]), fill=(190, 210, 235, 255), outline=(255, 255, 255, 255), width=SS * 2)
        d.ellipse(s(box((28, 22), (36, 32))), fill=(70, 140, 220, 255))

    def phantom(d, s, i):
        d.polygon(s([(32, 4), (46, 54), (32, 46), (18, 54)]), fill=(40, 60, 110, 255), outline=(120, 170, 255, 255), width=SS * 2)
        d.line(s([(32, 10), (32, 40)]), fill=(120, 170, 255, 255), width=SS * 2)

    def skipper(d, s, i):
        d.polygon(s([(32, 8), (50, 48), (32, 40), (14, 48)]), fill=(240, 200, 60, 255), outline=(255, 245, 170, 255), width=SS * 2)
        d.polygon(s([(14, 48), (6, 56), (22, 50)]), fill=(200, 150, 40, 255)); d.polygon(s([(50, 48), (58, 56), (42, 50)]), fill=(200, 150, 40, 255))

    def specter(d, s, i):
        d.polygon(s([(32, 6), (52, 50), (32, 42), (12, 50)]), fill=(150, 100, 220, 150 + (i % 2) * 50), outline=(225, 200, 255, 255), width=SS * 2)
        d.ellipse(s(box((26, 20), (38, 34))), outline=(235, 220, 255, 255), width=SS * 2)

    def bulwark(d, s, i):
        d.polygon(s([(32, 6), (54, 24), (54, 52), (32, 58), (10, 52), (10, 24)]), fill=(120, 125, 140, 255), outline=(210, 215, 230, 255), width=SS * 2)
        d.rectangle(s(box((26, 18), (38, 36))), fill=(70, 150, 230, 255))

    def medic(d, s, i):
        d.polygon(s([(32, 6), (50, 50), (32, 42), (14, 50)]), fill=(235, 240, 245, 255), outline=(255, 255, 255, 255), width=SS * 2)
        d.rectangle(s(box((29, 18), (35, 38))), fill=(60, 200, 100, 255)); d.rectangle(s(box((23, 24), (41, 30))), fill=(60, 200, 100, 255))

    def comet(d, s, i):
        d.polygon(s([(32, 4), (42, 50), (32, 44), (22, 50)]), fill=(255, 120, 60, 255), outline=(255, 230, 180, 255), width=SS * 2)
        d.ellipse(s(box((29, 20), (35, 28))), fill=(255, 240, 160, 255))

    def lancer(d, s, i):
        d.polygon(s([(32, 2), (38, 46), (32, 58), (26, 46)]), fill=(200, 210, 230, 255), outline=(255, 255, 255, 255), width=SS * 2)
        d.line(s([(32, 6), (32, 40)]), fill=(80, 160, 255, 255), width=SS * 2)
        d.polygon(s([(26, 46), (14, 56), (28, 50)]), fill=(120, 130, 160, 255)); d.polygon(s([(38, 46), (50, 56), (36, 50)]), fill=(120, 130, 160, 255))

    def prospector(d, s, i):
        d.ellipse(s(box((14, 16), (50, 52))), fill=(190, 140, 60, 255), outline=(255, 220, 140, 255), width=SS * 2)
        d.rectangle(s(box((26, 8), (38, 20))), fill=(150, 110, 50, 255))
        d.line(s([(14, 30), (6, 22)]), fill=(255, 220, 140, 255), width=SS * 3); d.line(s([(50, 30), (58, 22)]), fill=(255, 220, 140, 255), width=SS * 3)

    def nova(d, s, i):
        pts = [(32 + (28 if k % 2 == 0 else 13) * math.sin(k * math.pi / 5), 32 - (28 if k % 2 == 0 else 13) * math.cos(k * math.pi / 5)) for k in range(10)]
        d.polygon(s(pts), fill=(255, 150, 60, 255), outline=(255, 240, 180, 255), width=SS * 2)
        d.ellipse(s(box((26, 26), (38, 38))), fill=(255, 255, 210, 255))

    def juggernaut(d, s, i):
        d.polygon(s([(32, 4), (56, 22), (58, 54), (32, 60), (6, 54), (8, 22)]), fill=(110, 90, 90, 255), outline=(230, 190, 170, 255), width=SS * 2)
        d.polygon(s([(22, 6), (42, 6), (38, 20), (26, 20)]), fill=(190, 80, 60, 255)); d.rectangle(s(box((26, 26), (38, 44))), fill=(60, 50, 50, 255))

    def chronos(d, s, i):
        d.polygon(s([(32, 4), (50, 52), (32, 44), (14, 52)]), fill=(70, 80, 150, 255), outline=(190, 200, 255, 255), width=SS * 2)
        d.ellipse(s(box((22, 20), (42, 40))), fill=(230, 235, 255, 255), outline=(40, 50, 110, 255), width=SS * 2)
        a = i * math.pi / 2; d.line(s([(32, 30), (32 + 7 * math.sin(a), 30 - 7 * math.cos(a))]), fill=(40, 50, 110, 255), width=SS * 2)

    def carrier(d, s, i):
        d.polygon(s([(32, 4), (46, 20), (50, 56), (32, 60), (14, 56), (18, 20)]), fill=(80, 130, 120, 255), outline=(190, 240, 220, 255), width=SS * 2)
        for y in (26, 38, 50):
            d.rectangle(s(box((22, y), (42, y + 5))), fill=(40, 70, 65, 255), outline=(150, 210, 190, 255))
    return {"ship_sheet": (scout, None), "ship_phantom": (phantom, None), "ship_skipper": (skipper, None), "ship_specter": (specter, (200, 150, 255, 255)),
            "ship_bulwark": (bulwark, (120, 190, 255, 255)), "ship_medic": (medic, (120, 255, 170, 255)), "ship_comet": (comet, (255, 210, 90, 255)),
            "ship_lancer": (lancer, (120, 190, 255, 255)), "ship_prospector": (prospector, (255, 190, 80, 255)), "ship_nova": (nova, (255, 220, 120, 255)),
            "ship_juggernaut": (juggernaut, (255, 130, 70, 255)), "ship_chronos": (chronos, (160, 180, 255, 255)), "ship_carrier": (carrier, (120, 255, 210, 255))}


def aliens():
    def drifter(d, s, i):
        d.ellipse(s(box((8, 26), (56, 46))), fill=(70, 170, 90, 255), outline=(190, 255, 200, 255), width=SS * 2)
        d.ellipse(s(box((22, 14), (42, 34))), fill=(150, 230, 255, 200), outline=(220, 250, 255, 255), width=SS)
        for k in range(5):
            x = 14 + k * 9; d.ellipse(s(box((x - 2, 34), (x + 2, 38))), fill=(255, 255, 120, 255) if (k + i) % 4 == 0 else (60, 90, 60, 255))

    def chaser(d, s, i):
        d.polygon(s([(27, 46), (32, 46 + 6 + (i % 2) * 6), (37, 46)]), fill=(255, 200, 60, 255))
        d.polygon(s([(32, 6), (48, 52), (32, 42), (16, 52)]), fill=(210, 60, 60, 255), outline=(255, 200, 200, 255), width=SS * 2)
        d.ellipse(s(box((28, 22), (36, 30))), fill=(255, 240, 120, 255))

    def sniper(d, s, i):
        d.polygon(s([(14, 46), (32, 34), (50, 46), (32, 54)]), fill=(110, 80, 190, 255), outline=(200, 180, 255, 255), width=SS * 2)
        d.polygon(s([(32, 8), (39, 40), (32, 56), (25, 40)]), fill=(150, 120, 230, 255), outline=(230, 220, 255, 255), width=SS * 2)
        r = 2 + (i % 4); d.ellipse(s(box((32 - r, 10 - r), (32 + r, 10 + r))), fill=(255, 120, 120, 255))

    def swarm(d, s, i):
        d.polygon(s([(32, 12), (46, 32), (32, 52), (18, 32)]), fill=(240, 150, 40, 255), outline=(255, 230, 170, 255), width=SS * 2)
        o = (i % 2) * 4; d.line(s([(8, 22 + o), (22, 32)]), fill=(255, 200, 100, 255), width=SS * 3); d.line(s([(56, 22 + o), (42, 32)]), fill=(255, 200, 100, 255), width=SS * 3)
        d.ellipse(s(box((28, 28), (36, 36))), fill=(120, 30, 20, 255))

    def mothership(d, s, i):
        d.ellipse(s(box((6, 44), (122, 100))), fill=(90, 80, 130, 255), outline=(200, 190, 240, 255), width=SS * 3)
        d.ellipse(s(box((40, 22), (88, 68))), fill=(140, 200, 240, 190), outline=(230, 245, 255, 255), width=SS * 2)
        for k in range(8):
            x = 16 + k * 14; d.ellipse(s(box((x - 3, 68), (x + 3, 74))), fill=(255, 230, 90, 255) if (k + i * 2) % 8 < 3 else (70, 60, 90, 255))
        d.rectangle(s(box((58, 96), (70, 112))), fill=(160, 150, 200, 255))

    def seeker(d, s, i):
        d.ellipse(s(box((12, 18), (52, 46))), fill=(60, 90, 70, 255), outline=(150, 255, 180, 255), width=SS * 2)
        r = 3 + (i % 4); d.ellipse(s(box((32 - r, 32 - r), (32 + r, 32 + r))), fill=(255, 80, 80, 255))
        d.line(s([(32, 32), (32 + 22 * math.sin(i * 1.5), 32 - 22 * math.cos(i * 1.5))]), fill=(255, 120, 120, 255), width=SS * 2)

    def teleporter(d, s, i):
        d.polygon(s([(32, 8), (50, 32), (32, 56), (14, 32)]), fill=(120, 60, 180, 200), outline=(220, 170, 255, 255), width=SS * 2)
        d.polygon(s([(32, 20), (42, 32), (32, 44), (22, 32)]), outline=(255, 255, 255, 120 + 40 * (i % 3)), width=SS)

    def minelayer(d, s, i):
        d.rectangle(s(box((14, 22), (50, 44))), fill=(150, 90, 40, 255), outline=(255, 200, 120, 255), width=SS * 2)
        d.rectangle(s(box((26, 44), (38, 56))), fill=(110, 60, 30, 255))
        d.ellipse(s(box((28, 28), (36, 36))), fill=(255, 220, 90, 255) if i % 2 else (90, 70, 40, 255))

    def mine(d, s, i):
        d.ellipse(s(box((6, 6), (25, 25))), fill=(120, 40, 40, 255), outline=(255, 120, 120, 255), width=SS * 2)
        for k in range(8):
            a = k * math.pi / 4; d.line(s([(16 + 9 * math.cos(a), 16 + 9 * math.sin(a)), (16 + 14 * math.cos(a), 16 + 14 * math.sin(a))]), fill=(255, 120, 120, 255), width=SS * 2)
        d.ellipse(s(box((13, 13), (19, 19))), fill=(255, 255, 120, 255) if i % 2 else (80, 30, 30, 255))

    def abullet(d, s, i):
        r = 5 + (i % 2) * 2; d.ellipse(s(box((8 - r, 8 - r), (8 + r, 8 + r))), fill=(255, 70, 70, 255)); d.ellipse(s(box((5, 5), (11, 11))), fill=(255, 230, 230, 255))
    return [("alien_drifter", 64, 4, drifter), ("alien_chaser", 64, 4, chaser), ("alien_sniper", 64, 4, sniper), ("alien_swarm", 64, 4, swarm), ("alien_mothership", 128, 4, mothership),
            ("alien_seeker", 64, 4, seeker), ("alien_teleporter", 64, 4, teleporter), ("alien_minelayer", 64, 4, minelayer), ("alien_mine", 32, 2, mine), ("alien_bullet", 16, 2, abullet)]


def allies():
    def wingman(d, s, i):
        d.polygon(s([(27, 46), (32, 52 + (i % 2) * 6), (37, 46)]), fill=(120, 220, 255, 255))
        d.polygon(s([(32, 8), (48, 52), (32, 42), (16, 52)]), fill=(60, 150, 255, 255), outline=(210, 240, 255, 255), width=SS * 2)
        d.ellipse(s(box((28, 22), (36, 30))), fill=(210, 255, 220, 255))

    def repair(d, s, i):
        d.ellipse(s(box((14, 14), (50, 50))), fill=(235, 245, 240, 255), outline=(120, 255, 170, 255), width=SS * 2)
        d.rectangle(s(box((29, 20), (35, 44))), fill=(60, 200, 100, 255)); d.rectangle(s(box((20, 29), (44, 35))), fill=(60, 200, 100, 255))

    def cutter(d, s, i):
        d.polygon(s([(32, 6), (52, 40), (46, 58), (18, 58), (12, 40)]), fill=(40, 150, 150, 255), outline=(180, 255, 245, 255), width=SS * 2)
        d.rectangle(s(box((28, 20), (36, 34))), fill=(210, 255, 250, 255))
        lit = (120, 255, 200, 255) if i % 2 else (30, 80, 70, 255); d.ellipse(s(box((8, 44), (16, 52))), fill=lit); d.ellipse(s(box((48, 44), (56, 52))), fill=lit)

    def trader(d, s, i):
        d.rectangle(s(box((14, 18), (50, 46))), fill=(220, 190, 80, 255), outline=(255, 240, 170, 255), width=SS * 2); d.rectangle(s(box((20, 24), (44, 40))), fill=(150, 120, 40, 255))
        d.polygon(s([(26, 46), (32, 54 + (i % 2) * 4), (38, 46)]), fill=(120, 220, 255, 255)); d.ellipse(s(box((28, 10), (36, 18))), fill=(120, 255, 170, 255))

    def stranded(d, s, i):
        d.polygon(s([(32, 10), (46, 50), (32, 42), (18, 50)]), fill=(130, 130, 145, 255), outline=(200, 200, 215, 255), width=SS * 2)
        d.line(s([(24, 24), (40, 36)]), fill=(60, 60, 70, 255), width=SS * 3)
        d.ellipse(s(box((28, 4), (36, 12))), fill=(255, 70, 70, 255) if i % 2 == 0 else (90, 30, 30, 255))
    return [("ally_wingman", wingman), ("ally_repair", repair), ("ally_cutter", cutter), ("ally_trader", trader), ("ally_stranded", stranded)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (body, flame) in bodies().items():
        sheet(f"{name}.png", 64, 64, 4, ship(body, flame) if flame else ship(body))
    for name, size, frames, fn in aliens():
        sheet(f"{name}.png", size, size, frames, fn)
    for name, fn in allies():
        sheet(f"{name}.png", 64, 64, 4, fn)

    def rock(d, s, i):
        rnd = random.Random(7 + i)
        pts = [(32 + rnd.uniform(21, 29) * math.cos(2 * math.pi * k / 14), 32 + rnd.uniform(21, 29) * math.sin(2 * math.pi * k / 14)) for k in range(14)]
        d.polygon(s(pts), fill=(120, 105, 92, 255), outline=(190, 175, 160, 255), width=SS * 2)
        for _ in range(3):
            cx, cy, cr = rnd.uniform(20, 44), rnd.uniform(20, 44), rnd.uniform(3, 6); d.ellipse(s(box((cx - cr, cy - cr), (cx + cr, cy + cr))), fill=(85, 74, 66, 255))
    sheet("rock_sheet.png", 64, 64, 4, rock)

    def wormhole(d, s, i):
        for k in range(8):
            r = 60 - k * 7; c = 255 - k * 22; d.ellipse(s(box((64 - r, 64 - r), (64 + r, 64 + r))), outline=(c // 2, 80 + k * 10, c, 255), width=SS * 3)
        for arm in range(4):
            st = i * (90 / 8) + arm * 90
            d.arc(s(box((8, 8), (120, 120))), st, st + 50, fill=(210, 170, 255, 255), width=SS * 5); d.arc(s(box((28, 28), (100, 100))), st + 45, st + 95, fill=(150, 210, 255, 255), width=SS * 4)
        d.ellipse(s(box((50, 50), (78, 78))), fill=(8, 0, 25, 255))
    sheet("wormhole_sheet.png", 128, 128, 8, wormhole)

    def pu(color, kind):
        def draw(d, s, i):
            d.ellipse(s(box((1, 1), (31, 31))), fill=(20, 25, 45, 255), outline=color, width=SS * 2)
            if kind == "speed": d.polygon(s([(18, 4), (8, 18), (15, 18), (13, 28), (24, 13), (17, 13)]), fill=color)
            elif kind == "health": d.rectangle(s(box((13, 7), (18, 24))), fill=color); d.rectangle(s(box((7, 13), (24, 18))), fill=color)
            elif kind == "ammo":
                for x in (8, 14, 20): d.rectangle(s(box((x, 8), (x + 3, 24))), fill=color); d.polygon(s([(x, 8), (x + 3, 8), (x + 1.5, 4)]), fill=color)
            else: d.ellipse(s(box((7, 7), (24, 24))), outline=color, width=SS * 3)
        return draw
    for k, col in (("speed", (255, 220, 60, 255)), ("health", (80, 230, 110, 255)), ("shield", (90, 220, 255, 255)), ("ammo", (255, 150, 60, 255))):
        sheet(f"powerup_{k}.png", 32, 32, 1, pu(col, k))

    def bul(fill, fn=None):
        return lambda d, s, i: fn(d, s, i) if fn else None
    B = {
        "bullet_w1": (12, 28, 1, lambda d, s, i: d.polygon(s([(6, 0), (11, 8), (11, 24), (6, 27), (1, 24), (1, 8)]), fill=(255, 230, 80, 255))),
        "bullet_w2": (12, 20, 1, lambda d, s, i: d.ellipse(s(box((1, 1), (10, 18))), fill=(110, 255, 140, 255), outline=(220, 255, 230, 255))),
        "bullet_w3": (8, 16, 1, lambda d, s, i: d.rectangle(s(box((2, 0), (5, 15))), fill=(200, 230, 255, 255))),
        "bullet_w4": (16, 32, 2, lambda d, s, i: (d.polygon(s([(5, 28), (8, 30 + (i % 2) * 2), (11, 28)]), fill=(255, 190, 60, 255)), d.rectangle(s(box((5, 8), (10, 28))), fill=(190, 195, 205, 255)), d.polygon(s([(5, 8), (8, 0), (11, 8)]), fill=(235, 80, 60, 255)))),
        "bullet_w5": (8, 48, 1, lambda d, s, i: (d.rectangle(s(box((0, 0), (7, 47))), fill=(60, 200, 255, 200)), d.rectangle(s(box((3, 0), (4, 47))), fill=(240, 255, 255, 255)))),
        "bullet_w6": (32, 32, 2, lambda d, s, i: (d.ellipse(s(box((6, 6), (25, 25))), fill=(60, 65, 85, 255), outline=(170, 175, 200, 255), width=SS * 2), d.ellipse(s(box((13, 13), (19, 19))), fill=(255, 60, 60, 255) if i % 2 == 0 else (90, 30, 30, 255)))),
        "bullet_phantom": (6, 40, 1, lambda d, s, i: d.rectangle(s(box((2, 0), (3, 39))), fill=(130, 190, 255, 230))),
        "bullet_skipper": (32, 32, 1, lambda d, s, i: (d.ellipse(s(box((2, 2), (29, 29))), outline=(255, 230, 120, 255), width=SS * 3), d.ellipse(s(box((10, 10), (21, 21))), fill=(255, 245, 190, 255)))),
        "bullet_specter": (10, 56, 1, lambda d, s, i: (d.rectangle(s(box((1, 0), (8, 55))), fill=(170, 110, 255, 210)), d.rectangle(s(box((4, 0), (5, 55))), fill=(245, 235, 255, 255)))),
        "bullet_bulwark": (10, 10, 1, lambda d, s, i: d.ellipse(s(box((0, 0), (9, 9))), fill=(255, 170, 60, 255), outline=(255, 235, 170, 255))),
        "bullet_medic": (16, 16, 1, lambda d, s, i: (d.rectangle(s(box((6, 1), (9, 14))), fill=(90, 240, 140, 255)), d.rectangle(s(box((1, 6), (14, 9))), fill=(90, 240, 140, 255)))),
    }
    for name, (w, h, n, fn) in B.items():
        sheet(f"{name}.png", w, h, n, fn)

    def crystal(d, s, i):
        d.polygon(s([(16, 2), (28, 14), (24, 30), (8, 30), (4, 14)]), fill=(90, 220, 255, 200 + 55 * (i % 2)), outline=(230, 250, 255, 255), width=SS)
    sheet("objective_crystal.png", 32, 32, 2, crystal)

    def pod(d, s, i):
        d.ellipse(s(box((6, 8), (34, 32))), fill=(230, 230, 240, 255), outline=(255, 255, 255, 255), width=SS * 2); d.ellipse(s(box((14, 14), (26, 24))), fill=(90, 160, 230, 255))
        d.ellipse(s(box((17, 3), (23, 9))), fill=(255, 80, 80, 255) if i % 2 else (90, 30, 30, 255))
    sheet("objective_pod.png", 40, 40, 2, pod)

    def freighter(d, s, i):
        d.rectangle(s(box((26, 8), (70, 88))), fill=(90, 130, 100, 255), outline=(190, 240, 200, 255), width=SS * 3); d.rectangle(s(box((30, 4), (66, 12))), fill=(130, 180, 140, 255))
        for k in range(4): d.rectangle(s(box((32, 20 + k * 16), (64, 30 + k * 16))), fill=(60, 95, 70, 255), outline=(150, 200, 160, 255))
        d.polygon(s([(38, 88), (48, 96), (58, 88)]), fill=(255, 190, 80, 255))
    sheet("objective_freighter.png", 96, 96, 1, freighter)
    print("wrote", len(list(OUT.glob("*.png"))), "images to", OUT)


if __name__ == "__main__":
    main()
