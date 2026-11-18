"""Generates placeholder images and sounds the first time the game runs.

Files that already exist are never overwritten, so replace any of them with your
own art/sound (same names, or pick new names in the editor).
"""
import math
import random
import struct
import wave

from PIL import Image, ImageDraw

from .constants import IMAGES_DIR, SOUNDS_DIR

RATE = 22050


# ---------------------------------------------------------------- images
def _ship(path):
    fw = 64
    sheet = Image.new("RGBA", (fw * 4, fw), (0, 0, 0, 0))
    for i in range(4):
        im = Image.new("RGBA", (fw, fw), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        flame = 6 + (i % 2) * 6 + (i // 2) * 2
        d.polygon([(27, 46), (32, 46 + flame), (37, 46)], fill=(255, 170, 40, 255))
        d.polygon([(32, 6), (52, 52), (32, 43), (12, 52)],
                  fill=(190, 210, 235, 255), outline=(255, 255, 255, 255))
        d.ellipse((28, 22, 36, 32), fill=(70, 140, 220, 255))
        sheet.paste(im, (i * fw, 0))
    sheet.save(path)


def _rock(path):
    rnd = random.Random(7)
    fw = 64
    sheet = Image.new("RGBA", (fw * 4, fw), (0, 0, 0, 0))
    for i in range(4):
        im = Image.new("RGBA", (fw, fw), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = []
        for k in range(14):
            a = 2 * math.pi * k / 14
            r = rnd.uniform(21, 29)
            pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
        d.polygon(pts, fill=(120, 105, 92, 255), outline=(190, 175, 160, 255))
        for _ in range(3):
            cx, cy, cr = rnd.uniform(20, 44), rnd.uniform(20, 44), rnd.uniform(3, 6)
            d.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(85, 74, 66, 255))
        sheet.paste(im, (i * fw, 0))
    sheet.save(path)


def _wormhole(path):
    fw, frames = 128, 8
    sheet = Image.new("RGBA", (fw * frames, fw), (0, 0, 0, 0))
    for i in range(frames):
        im = Image.new("RGBA", (fw, fw), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for k in range(8):
            r = 60 - k * 7
            shade = 255 - k * 22
            d.ellipse((64 - r, 64 - r, 64 + r, 64 + r),
                      outline=(shade // 2, 80 + k * 10, shade, 255), width=3)
        for arm in range(4):
            start = i * (90 / frames) + arm * 90
            d.arc((8, 8, 120, 120), start, start + 50, fill=(210, 170, 255, 255), width=5)
            d.arc((28, 28, 100, 100), start + 45, start + 95, fill=(150, 210, 255, 255), width=4)
        d.ellipse((50, 50, 78, 78), fill=(8, 0, 25, 255))
        sheet.paste(im, (i * fw, 0))
    sheet.save(path)


def _background(path):
    size, tiles = 256, 4
    sheet = Image.new("RGBA", (size * tiles, size), (0, 0, 0, 0))
    for t in range(tiles):
        rnd = random.Random(100 + t)
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for _ in range(70):
            x, y = rnd.randrange(size), rnd.randrange(size)
            b = rnd.randint(90, 255)
            r = rnd.choice((0, 0, 0, 1))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(b, b, min(255, b + 20), 255))
        sheet.paste(im, (t * size, 0))
    sheet.save(path)


def _powerup(color, kind):
    def build(path):
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((1, 1, 30, 30), fill=(20, 25, 45, 255), outline=color, width=2)
        if kind == "speed":
            d.polygon([(18, 4), (8, 18), (15, 18), (13, 28), (24, 13), (17, 13)], fill=color)
        elif kind == "health":
            d.rectangle((13, 7, 18, 24), fill=color)
            d.rectangle((7, 13, 24, 18), fill=color)
        elif kind == "ammo":
            for x in (8, 14, 20):
                d.rectangle((x, 8, x + 3, 24), fill=color)
                d.polygon([(x, 8), (x + 3, 8), (x + 1.5, 4)], fill=color)
        else:
            d.ellipse((7, 7, 24, 24), outline=color, width=3)
        im.save(path)
    return build


def _sheet(path, draw, frames, w, h):
    sheet = Image.new("RGBA", (w * frames, h), (0, 0, 0, 0))
    for i in range(frames):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw(ImageDraw.Draw(im), i)
        sheet.paste(im, (i * w, 0))
    sheet.save(path)


def _drifter(d, i):
    d.ellipse((8, 26, 56, 46), fill=(70, 170, 90, 255), outline=(190, 255, 200, 255))
    d.ellipse((22, 14, 42, 34), fill=(150, 230, 255, 200), outline=(220, 250, 255, 255))
    for k in range(5):
        lit = (k + i) % 4 == 0
        x = 14 + k * 9
        d.ellipse((x - 2, 34, x + 2, 38), fill=(255, 255, 120, 255) if lit else (60, 90, 60, 255))


def _chaser(d, i):
    fl = 6 + (i % 2) * 6
    d.polygon([(27, 46), (32, 46 + fl), (37, 46)], fill=(255, 200, 60, 255))
    d.polygon([(32, 6), (48, 52), (32, 42), (16, 52)], fill=(210, 60, 60, 255),
              outline=(255, 200, 200, 255))
    d.ellipse((28, 22, 36, 30), fill=(255, 240, 120, 255))


def _sniper(d, i):
    d.polygon([(14, 46), (32, 34), (50, 46), (32, 54)], fill=(110, 80, 190, 255),
              outline=(200, 180, 255, 255))
    d.polygon([(32, 8), (39, 40), (32, 56), (25, 40)], fill=(150, 120, 230, 255),
              outline=(230, 220, 255, 255))
    r = 2 + (i % 4)
    d.ellipse((32 - r, 8 - r + 2, 32 + r, 8 + r + 2), fill=(255, 120, 120, 255))


def _swarm(d, i):
    d.polygon([(32, 12), (46, 32), (32, 52), (18, 32)], fill=(240, 150, 40, 255),
              outline=(255, 230, 170, 255))
    off = (i % 2) * 4
    d.line((8, 22 + off, 22, 32), fill=(255, 200, 100, 255), width=3)
    d.line((56, 22 + off, 42, 32), fill=(255, 200, 100, 255), width=3)
    d.ellipse((28, 28, 36, 36), fill=(120, 30, 20, 255))


def _mothership(d, i):
    d.ellipse((6, 44, 122, 100), fill=(90, 80, 130, 255), outline=(200, 190, 240, 255), width=3)
    d.ellipse((40, 22, 88, 68), fill=(140, 200, 240, 190), outline=(230, 245, 255, 255), width=2)
    for k in range(8):
        lit = (k + i * 2) % 8 < 3
        x = 16 + k * 14
        d.ellipse((x - 3, 68, x + 3, 74), fill=(255, 230, 90, 255) if lit else (70, 60, 90, 255))
    d.rectangle((58, 96, 70, 112), fill=(160, 150, 200, 255))


def _alien_bullet(d, i):
    r = 5 + (i % 2) * 2
    d.ellipse((8 - r, 8 - r, 8 + r, 8 + r), fill=(255, 70, 70, 255))
    d.ellipse((5, 5, 11, 11), fill=(255, 230, 230, 255))


def _bullet_w1(d, i):
    d.polygon([(6, 0), (11, 8), (11, 24), (6, 27), (1, 24), (1, 8)], fill=(255, 230, 80, 255))


def _bullet_w2(d, i):
    d.ellipse((1, 1, 10, 18), fill=(110, 255, 140, 255), outline=(220, 255, 230, 255))


def _bullet_w3(d, i):
    d.rectangle((2, 0, 5, 15), fill=(200, 230, 255, 255))


def _bullet_w4(d, i):
    fl = 3 + (i % 2) * 5
    d.polygon([(5, 28), (8, 28 + fl // 2 + 2), (11, 28)], fill=(255, 190, 60, 255))
    d.rectangle((5, 8, 10, 28), fill=(190, 195, 205, 255))
    d.polygon([(5, 8), (8, 0), (11, 8)], fill=(235, 80, 60, 255))
    d.polygon([(2, 28), (5, 20), (5, 28)], fill=(150, 150, 170, 255))
    d.polygon([(14, 28), (11, 20), (11, 28)], fill=(150, 150, 170, 255))


def _bullet_w5(d, i):
    d.rectangle((0, 0, 7, 47), fill=(60, 200, 255, 200))
    d.rectangle((3, 0, 4, 47), fill=(240, 255, 255, 255))


def _bullet_w6(d, i):
    d.ellipse((6, 6, 25, 25), fill=(60, 65, 85, 255), outline=(170, 175, 200, 255), width=2)
    for k in range(8):
        a = k * math.pi / 4
        d.line((16 + 9 * math.cos(a), 16 + 9 * math.sin(a),
                16 + 14 * math.cos(a), 16 + 14 * math.sin(a)), fill=(170, 175, 200, 255), width=2)
    lit = (255, 60, 60, 255) if i % 2 == 0 else (90, 30, 30, 255)
    d.ellipse((13, 13, 19, 19), fill=lit)


def _extra_images():
    return {
        "powerup_ammo.png": _powerup((255, 150, 60, 255), "ammo"),
        "alien_drifter.png": lambda p: _sheet(p, _drifter, 4, 64, 64),
        "alien_chaser.png": lambda p: _sheet(p, _chaser, 4, 64, 64),
        "alien_sniper.png": lambda p: _sheet(p, _sniper, 4, 64, 64),
        "alien_swarm.png": lambda p: _sheet(p, _swarm, 4, 64, 64),
        "alien_mothership.png": lambda p: _sheet(p, _mothership, 4, 128, 128),
        "alien_bullet.png": lambda p: _sheet(p, _alien_bullet, 2, 16, 16),
        "bullet_w1.png": lambda p: _sheet(p, _bullet_w1, 1, 12, 28),
        "bullet_w2.png": lambda p: _sheet(p, _bullet_w2, 1, 12, 20),
        "bullet_w3.png": lambda p: _sheet(p, _bullet_w3, 1, 8, 16),
        "bullet_w4.png": lambda p: _sheet(p, _bullet_w4, 2, 16, 32),
        "bullet_w5.png": lambda p: _sheet(p, _bullet_w5, 1, 8, 48),
        "bullet_w6.png": lambda p: _sheet(p, _bullet_w6, 2, 32, 32),
    }



def _ship_body(body, trim, fl_color=(255, 170, 40, 255)):
    def draw(d, i):
        fl = 6 + (i % 2) * 6
        d.polygon([(27, 46), (32, 46 + fl), (37, 46)], fill=fl_color)
        body(d, i)
    return draw


def _phantom(d, i):
    d.polygon([(32, 4), (46, 54), (32, 46), (18, 54)], fill=(40, 60, 110, 255), outline=(120, 170, 255, 255))
    d.line((32, 10, 32, 40), fill=(120, 170, 255, 255), width=2)


def _skipper(d, i):
    d.polygon([(32, 8), (50, 48), (32, 40), (14, 48)], fill=(240, 200, 60, 255), outline=(255, 245, 170, 255))
    d.polygon([(14, 48), (6, 56), (22, 50)], fill=(200, 150, 40, 255))
    d.polygon([(50, 48), (58, 56), (42, 50)], fill=(200, 150, 40, 255))
    d.ellipse((28, 22, 36, 30), fill=(90, 60, 10, 255))


def _specter(d, i):
    ring = 150 + (i % 2) * 50
    d.polygon([(32, 6), (52, 50), (32, 42), (12, 50)], fill=(150, 100, 220, ring), outline=(225, 200, 255, 255))
    d.ellipse((26, 20, 38, 34), outline=(235, 220, 255, 255), width=2)


def _bulwark(d, i):
    d.polygon([(32, 6), (54, 24), (54, 52), (32, 58), (10, 52), (10, 24)], fill=(120, 125, 140, 255),
              outline=(210, 215, 230, 255), width=2)
    d.rectangle((26, 18, 38, 36), fill=(70, 150, 230, 255))
    d.rectangle((14, 30, 18, 50), fill=(90, 95, 110, 255))
    d.rectangle((46, 30, 50, 50), fill=(90, 95, 110, 255))


def _medic(d, i):
    d.polygon([(32, 6), (50, 50), (32, 42), (14, 50)], fill=(235, 240, 245, 255), outline=(255, 255, 255, 255))
    d.rectangle((29, 18, 35, 38), fill=(60, 200, 100, 255))
    d.rectangle((23, 24, 41, 30), fill=(60, 200, 100, 255))


def _seeker(d, i):
    d.ellipse((12, 18, 52, 46), fill=(60, 90, 70, 255), outline=(150, 255, 180, 255))
    r = 3 + (i % 4)
    d.ellipse((32 - r, 32 - r, 32 + r, 32 + r), fill=(255, 80, 80, 255))
    d.line((32, 32, 32 + 22 * math.sin(i * 1.5), 32 - 22 * math.cos(i * 1.5)), fill=(255, 120, 120, 255), width=2)


def _teleporter(d, i):
    d.polygon([(32, 8), (50, 32), (32, 56), (14, 32)], fill=(120, 60, 180, 200), outline=(220, 170, 255, 255))
    d.polygon([(32, 20), (42, 32), (32, 44), (22, 32)], outline=(255, 255, 255, 120 + 40 * (i % 3)))


def _minelayer(d, i):
    d.rectangle((14, 22, 50, 44), fill=(150, 90, 40, 255), outline=(255, 200, 120, 255), width=2)
    d.rectangle((26, 44, 38, 56), fill=(110, 60, 30, 255))
    lit = (255, 220, 90, 255) if i % 2 else (90, 70, 40, 255)
    d.ellipse((28, 28, 36, 36), fill=lit)


def _alien_mine(d, i):
    d.ellipse((6, 6, 25, 25), fill=(120, 40, 40, 255), outline=(255, 120, 120, 255), width=2)
    for k in range(8):
        a = k * math.pi / 4
        d.line((16 + 9 * math.cos(a), 16 + 9 * math.sin(a), 16 + 14 * math.cos(a), 16 + 14 * math.sin(a)),
               fill=(255, 120, 120, 255), width=2)
    d.ellipse((13, 13, 19, 19), fill=(255, 255, 120, 255) if i % 2 else (80, 30, 30, 255))


def _crystal(d, i):
    glow = 200 + 55 * (i % 2)
    d.polygon([(16, 2), (28, 14), (24, 30), (8, 30), (4, 14)], fill=(90, 220, 255, glow),
              outline=(230, 250, 255, 255))
    d.line((16, 2, 16, 30), fill=(230, 250, 255, 160), width=1)


def _pod(d, i):
    d.ellipse((6, 8, 34, 32), fill=(230, 230, 240, 255), outline=(255, 255, 255, 255), width=2)
    d.ellipse((14, 14, 26, 24), fill=(90, 160, 230, 255))
    lit = (255, 80, 80, 255) if i % 2 else (90, 30, 30, 255)
    d.ellipse((17, 3, 23, 9), fill=lit)


def _freighter(d, i):
    d.rectangle((26, 8, 70, 88), fill=(90, 130, 100, 255), outline=(190, 240, 200, 255), width=3)
    d.rectangle((30, 4, 66, 12), fill=(130, 180, 140, 255))
    for k in range(4):
        d.rectangle((32, 20 + k * 16, 64, 30 + k * 16), fill=(60, 95, 70, 255), outline=(150, 200, 160, 255))
    d.polygon([(38, 88), (48, 96), (58, 88)], fill=(255, 190, 80, 255))


def _bullet_phantom(d, i):
    d.rectangle((2, 0, 3, 39), fill=(130, 190, 255, 230))


def _bullet_skipper(d, i):
    d.ellipse((2, 2, 29, 29), outline=(255, 230, 120, 255), width=3)
    d.ellipse((10, 10, 21, 21), fill=(255, 245, 190, 255))


def _bullet_specter(d, i):
    d.rectangle((1, 0, 8, 55), fill=(170, 110, 255, 210))
    d.rectangle((4, 0, 5, 55), fill=(245, 235, 255, 255))


def _bullet_bulwark(d, i):
    d.ellipse((0, 0, 9, 9), fill=(255, 170, 60, 255), outline=(255, 235, 170, 255))


def _bullet_medic(d, i):
    d.rectangle((6, 1, 9, 14), fill=(90, 240, 140, 255))
    d.rectangle((1, 6, 14, 9), fill=(90, 240, 140, 255))


def _more_images():
    sheet = lambda fn, n, w, h: (lambda p: _sheet(p, fn, n, w, h))
    return {
        "ship_phantom.png": sheet(_ship_body(_phantom, None), 4, 64, 64),
        "ship_skipper.png": sheet(_ship_body(_skipper, None), 4, 64, 64),
        "ship_specter.png": sheet(_ship_body(_specter, None, (200, 150, 255, 255)), 4, 64, 64),
        "ship_bulwark.png": sheet(_ship_body(_bulwark, None, (120, 190, 255, 255)), 4, 64, 64),
        "ship_medic.png": sheet(_ship_body(_medic, None, (120, 255, 170, 255)), 4, 64, 64),
        "alien_seeker.png": sheet(_seeker, 4, 64, 64),
        "alien_teleporter.png": sheet(_teleporter, 4, 64, 64),
        "alien_minelayer.png": sheet(_minelayer, 4, 64, 64),
        "alien_mine.png": sheet(_alien_mine, 2, 32, 32),
        "objective_crystal.png": sheet(_crystal, 2, 32, 32),
        "objective_pod.png": sheet(_pod, 2, 40, 40),
        "objective_freighter.png": sheet(_freighter, 1, 96, 96),
        "bullet_phantom.png": sheet(_bullet_phantom, 1, 6, 40),
        "bullet_skipper.png": sheet(_bullet_skipper, 1, 32, 32),
        "bullet_specter.png": sheet(_bullet_specter, 1, 10, 56),
        "bullet_bulwark.png": sheet(_bullet_bulwark, 1, 10, 10),
        "bullet_medic.png": sheet(_bullet_medic, 1, 16, 16),
    }


# ---------------------------------------------------------------- sounds
def _write(path, samples):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))


def _tone(freq, dur, vol=0.35):
    n = int(RATE * dur)
    return [vol * min(1.0, i / (0.01 * RATE)) * (1 - i / n)
            * math.sin(2 * math.pi * freq * i / RATE) for i in range(n)]


def _noise(dur, vol=0.35):
    rnd = random.Random(3)
    n = int(RATE * dur)
    return [vol * rnd.uniform(-1, 1) * (1 - i / n) ** 2 for i in range(n)]


def _sweep(f0, f1, dur, vol=0.3):
    n, phase, out = int(RATE * dur), 0.0, []
    for i in range(n):
        phase += 2 * math.pi * (f0 + (f1 - f0) * i / n) / RATE
        out.append(vol * math.sin(phase) * math.sin(math.pi * i / n))
    return out


def _mix(*tracks):
    out = [0.0] * max(len(t) for t in tracks)
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def _music():
    notes = [220, 262, 330, 262, 196, 247, 294, 247, 220, 262, 330, 392, 330, 294, 262, 247]
    samples = []
    for f in notes:
        samples += _tone(f, 0.36, 0.22)
    return samples


SOUNDS = {
    "music.wav": _music,
    "thrust.wav": lambda: _noise(0.2, 0.3),
    "crash.wav": lambda: _mix(_noise(0.5, 0.5), _tone(70, 0.5, 0.4)),
    "powerup.wav": lambda: _tone(523, 0.08) + _tone(659, 0.08) + _tone(784, 0.14),
    "wormhole.wav": lambda: _sweep(200, 1200, 0.7),
    "split.wav": lambda: _noise(0.12, 0.4),
    # weapons
    "fire_blaster.wav": lambda: _sweep(1300, 500, 0.12),
    "fire_spread.wav": lambda: _mix(_sweep(900, 400, 0.18), _noise(0.18, 0.2)),
    "fire_rapid.wav": lambda: _tone(950, 0.04, 0.3),
    "fire_missile.wav": lambda: _mix(_sweep(200, 700, 0.35), _noise(0.35, 0.25)),
    "fire_laser.wav": lambda: _sweep(2200, 300, 0.25),
    "fire_mine.wav": lambda: _tone(150, 0.12) + _tone(100, 0.12),
    "weapon_switch.wav": lambda: _tone(660, 0.05) + _tone(880, 0.06),
    "no_ammo.wav": lambda: _tone(120, 0.12, 0.3),
    "explosion.wav": lambda: _mix(_noise(0.8, 0.6), _sweep(160, 40, 0.8, 0.4)),
    # aliens (each type sounds different)
    "drifter_spawn.wav": lambda: _sweep(300, 520, 0.35),
    "drifter_die.wav": lambda: _mix(_noise(0.3, 0.3), _sweep(500, 150, 0.3)),
    "chaser_spawn.wav": lambda: _sweep(900, 300, 0.3),
    "chaser_die.wav": lambda: _mix(_noise(0.3, 0.4), _tone(220, 0.3)),
    "sniper_spawn.wav": lambda: _tone(440, 0.08) + _tone(550, 0.08) + _tone(660, 0.12),
    "sniper_fire.wav": lambda: _sweep(1600, 700, 0.2),
    "sniper_die.wav": lambda: _mix(_noise(0.4, 0.4), _sweep(700, 100, 0.4)),
    "swarm_spawn.wav": lambda: _tone(1000, 0.04) + _tone(1200, 0.04) + _tone(1000, 0.04) + _tone(1400, 0.06),
    "swarm_fire.wav": lambda: _tone(1100, 0.05, 0.25),
    "swarm_die.wav": lambda: _mix(_noise(0.2, 0.35), _tone(800, 0.2, 0.2)),
    "mothership_spawn.wav": lambda: _sweep(70, 220, 1.1, 0.5),
    "mothership_fire.wav": lambda: _mix(_sweep(320, 140, 0.3, 0.35), _noise(0.3, 0.2)),
    "mothership_die.wav": lambda: _mix(_noise(1.2, 0.7), _sweep(200, 30, 1.2, 0.5)),
    # ships, abilities, objectives, hazards
    "fire_phantom.wav": lambda: _sweep(1800, 1400, 0.08, 0.2),
    "fire_skipper.wav": lambda: _mix(_sweep(500, 120, 0.3, 0.4), _noise(0.3, 0.25)),
    "fire_specter.wav": lambda: _sweep(500, 1500, 0.3, 0.3),
    "fire_bulwark.wav": lambda: _mix(_noise(0.25, 0.5), _tone(110, 0.25, 0.4)),
    "fire_medic.wav": lambda: _tone(880, 0.05) + _tone(1100, 0.07),
    "ability_cloak.wav": lambda: _sweep(900, 200, 0.5, 0.25),
    "ability_hyperjump.wav": lambda: _sweep(200, 2000, 0.25, 0.35) + _sweep(2000, 400, 0.2, 0.3),
    "ability_hyperspace.wav": lambda: _mix(_sweep(300, 900, 0.6, 0.3), _tone(150, 0.6, 0.2)),
    "ability_deflect.wav": lambda: _tone(1400, 0.08, 0.4) + _tone(900, 0.15, 0.35),
    "ability_repair.wav": lambda: _tone(440, 0.1) + _tone(554, 0.1) + _tone(659, 0.2),
    "shield_hit.wav": lambda: _mix(_tone(600, 0.15, 0.3), _noise(0.15, 0.15)),
    "crystal.wav": lambda: _tone(1200, 0.05, 0.3) + _tone(1600, 0.1, 0.3),
    "objective_done.wav": lambda: _tone(523, 0.1) + _tone(659, 0.1) + _tone(784, 0.1) + _tone(1047, 0.3),
    "perk_pick.wav": lambda: _tone(660, 0.08) + _tone(990, 0.15),
    "flare_warn.wav": lambda: _tone(700, 0.15, 0.4) + _tone(500, 0.15, 0.4) + _tone(700, 0.15, 0.4),
    "flare_hit.wav": lambda: _mix(_noise(0.8, 0.6), _sweep(900, 100, 0.8, 0.3)),
    "mine_blast.wav": lambda: _mix(_noise(0.5, 0.5), _tone(90, 0.5, 0.4)),
    "seeker_spawn.wav": lambda: _sweep(400, 900, 0.3, 0.3) + _sweep(900, 400, 0.3, 0.3),
    "seeker_fire.wav": lambda: _sweep(1000, 600, 0.15, 0.3),
    "seeker_die.wav": lambda: _mix(_noise(0.4, 0.4), _sweep(800, 120, 0.4, 0.3)),
    "teleporter_spawn.wav": lambda: _sweep(300, 1400, 0.4, 0.3),
    "teleporter_blink.wav": lambda: _sweep(1600, 300, 0.12, 0.35),
    "teleporter_fire.wav": lambda: _tone(1250, 0.05, 0.3),
    "teleporter_die.wav": lambda: _mix(_noise(0.3, 0.35), _sweep(1200, 200, 0.3, 0.3)),
    "minelayer_spawn.wav": lambda: _tone(180, 0.2, 0.4) + _tone(140, 0.3, 0.4),
    "minelayer_drop.wav": lambda: _tone(300, 0.06, 0.3) + _tone(200, 0.08, 0.3),
    "minelayer_die.wav": lambda: _mix(_noise(0.5, 0.5), _tone(100, 0.5, 0.35)),
}


def generate_missing():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    images = {
        "ship_sheet.png": _ship,
        "rock_sheet.png": _rock,
        "wormhole_sheet.png": _wormhole,
        "background_tiles.png": _background,
        "powerup_speed.png": _powerup((255, 220, 60, 255), "speed"),
        "powerup_health.png": _powerup((80, 230, 110, 255), "health"),
        "powerup_shield.png": _powerup((90, 220, 255, 255), "shield"),
    }
    images.update(_extra_images())
    images.update(_more_images())
    for name, build in images.items():
        if not (IMAGES_DIR / name).exists():
            build(IMAGES_DIR / name)
    for name, make in SOUNDS.items():
        if not (SOUNDS_DIR / name).exists():
            _write(SOUNDS_DIR / name, make())
