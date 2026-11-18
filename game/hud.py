"""HUD and overlay drawing from plain data, so the host and the joiner draw identical screens.

The HUD state is a dict (it is also what the host sends to the joiner):
  level, ws, state ("playing"|"paused"|"gameover"), can_restart, banner [title, subtitle] | None,
  notice, wh_left, boss (0-1) | None, net (status text),
  me {id, health, hp, max, speed, boost, shield, slot, alive},
  weapons [[slot, name, unlocked, unlock_level, ammo]], players [[id, name, score, health, alive]]
"""
import arcade

from .constants import SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from .ui import CYAN, GOLD, GREEN, GREY, ORANGE, RED, WHITE, draw_bar

PLAYER_COLORS = {1: WHITE, 2: (130, 255, 160, 255)}

# ship flag bits (see game_features.py)
FLAG_POWER, FLAG_CLOAK, FLAG_PHASE, FLAG_HEAL, FLAG_DEFLECT, FLAG_BARRIER = 1, 2, 4, 8, 16, 32


def draw_ship_effects(x, y, radius, flags, heal_range, line):
    """Rings around a ship for power-ups and abilities (world coordinates)."""
    if flags & FLAG_POWER:
        arcade.draw_circle_outline(x, y, radius + 12, CYAN, line)
    if flags & FLAG_DEFLECT:
        arcade.draw_circle_filled(x, y, radius + 16, (255, 255, 255, 40))
        arcade.draw_circle_outline(x, y, radius + 16, (255, 255, 255, 230), line * 1.5)
    if flags & FLAG_HEAL:
        arcade.draw_circle_filled(x, y, heal_range, (90, 255, 140, 22))
        arcade.draw_circle_outline(x, y, heal_range, (90, 255, 140, 120), line)
    if flags & FLAG_BARRIER:
        arcade.draw_circle_outline(x, y, radius + 7, (110, 150, 255, 150), line)


def draw_hazards(rows, t):
    """rows: [id, kind, x, y, a, b, phase, progress] (see GameView.hazard_rows)."""
    import math
    for _id, kind, x, y, a, b, phase, prog in rows:
        if kind == "nebula":
            for k in (1.0, 0.75, 0.5):
                arcade.draw_circle_filled(x, y, a * k, (150, 90, 210, 26))
            arcade.draw_circle_outline(x, y, a, (190, 140, 255, 70), 3)
        elif kind == "ion":
            arcade.draw_circle_filled(x, y, a, (90, 150, 255, 22))
            pulse = 0.85 + 0.15 * math.sin(t * 6)
            arcade.draw_circle_outline(x, y, a * pulse, (140, 200, 255, 160), 3)
            arcade.draw_circle_outline(x, y, a * 0.55 * pulse, (140, 200, 255, 90), 2)
        elif kind == "blackhole":
            arcade.draw_circle_outline(x, y, a, (150, 100, 255, 35), 2)       # reach of the pull
            for k in (0.55, 0.35, 0.2):
                arcade.draw_circle_outline(x, y, a * k, (170, 120, 255, 60), 2)
            arcade.draw_circle_filled(x, y, b + 6, (120, 70, 200, 200))
            arcade.draw_circle_filled(x, y, b, (0, 0, 0, 255))
        elif kind == "flare":
            if phase == 0:
                alpha = int(40 + 40 * abs(math.sin(prog * 8)))
                arcade.draw_lbwh_rectangle_filled(x - a / 2, y - b / 2, a, b, (255, 170, 40, alpha))
                arcade.draw_lbwh_rectangle_outline(x - a / 2, y - b / 2, a, b, (255, 200, 80, 200), 4)
            else:
                arcade.draw_lbwh_rectangle_filled(x - a / 2, y - b / 2, a, b, (255, 240, 180, 190))


def draw_effects(effects, zoom):
    """effects: [x, y, radius, age, duration, (r, g, b)] in world coordinates."""
    line = 3.0 / max(zoom, 0.2)
    for x, y, radius, age, dur, color in effects:
        k = age / dur
        alpha = int(255 * (1 - k))
        r = radius * (0.3 + 0.7 * k)
        arcade.draw_circle_filled(x, y, r * 0.7, (*color, alpha // 4))
        arcade.draw_circle_outline(x, y, r, (*color, alpha), line)
    return line


def draw_hud(t, s):
    me = s["me"]
    multi = len(s["players"]) > 1
    draw_bar(20, H - 36, 240, 16, me["health"], GREEN if me["health"] > 0.35 else RED)
    t.draw("hl", "HEALTH", 270, H - 35, GREY, 12)
    draw_bar(20, H - 60, 240, 12, me["speed"], ORANGE)
    t.draw("sl", "SPEED", 270, H - 59, GREY, 12)
    y = H - 84
    for p in s["players"]:
        if multi and p[0] != me["id"]:
            draw_bar(20, y, 140, 8, p[3] if p[4] else 0, PLAYER_COLORS.get(p[0], WHITE))
            t.draw(f"pb{p[0]}", p[1] + ("" if p[4] else "  (down)"), 168, y - 2, GREY, 11)
            y -= 16
    y -= 6
    if me["boost"] > 0:
        t.draw("boost", f"SPEED BOOST {me['boost']:0.1f}s", 20, y, ORANGE, 13)
        y -= 20
    if me["shield"] > 0:
        t.draw("shield", f"INVINCIBLE {me['shield']:0.1f}s", 20, y, CYAN, 13)

    if multi:
        yy = H - 36
        for p in s["players"]:
            t.draw(f"sc{p[0]}", f"{p[1]}: {int(p[2])}", W - 20, yy,
                   PLAYER_COLORS.get(p[0], WHITE), 16, "right")
            yy -= 22
        t.draw("level", f"LEVEL {s['level']}   AREA x{s['ws']:.2f}", W - 20, yy - 4, GOLD, 14, "right")
    else:
        t.draw("score", f"SCORE {int(s['players'][0][2])}", W - 20, H - 36, WHITE, 18, "right")
        t.draw("level", f"LEVEL {s['level']}   AREA x{s['ws']:.2f}", W - 20, H - 62, GOLD, 14, "right")

    if s["mode"] == "expedition" or me.get("credits"):
        t.draw("credits", f"CREDITS +{me['credits']}", W - 20, 124 if me.get("ability") else 70,
               GOLD, 14, "right")
    if s.get("obj"):
        t.draw("obj", s["obj"], W / 2, H - 92, (140, 230, 255, 255), 15, "center")
    if s.get("net"):
        t.draw("net", s["net"], W / 2, H - 16, GREY, 12, "center")
    if s.get("wh_left") is not None:
        t.draw("wh", f"WORMHOLE OPEN  {s['wh_left']:0.1f}s", W / 2, H - 38,
               (200, 150, 255, 255), 16, "center")
    if s.get("boss") is not None:
        draw_bar(W / 2 - 220, H - 72, 440, 14, s["boss"], RED)
        t.draw("boss", "MOTHERSHIP", W / 2, H - 54, RED, 13, "center")

    _ability_bar(t, me)
    _weapon_bar(t, s)
    if s.get("notice"):
        t.draw("notice", s["notice"], W / 2, 80, WHITE, 16, "center")
    if s.get("banner"):
        t.draw("banner", s["banner"][0], W / 2, H / 2 + 120, GOLD, 40, "center", bold=True)
        t.draw("banner2", s["banner"][1], W / 2, H / 2 + 85, GREY, 14, "center")
    if not me["alive"] and s["state"] == "playing":
        t.draw("down", "YOUR SHIP IS DOWN - you return at the next level", W / 2, H / 2 - 120,
               RED, 20, "center")
    if s["state"] == "perk" and s.get("perk"):
        _perk_overlay(t, s["perk"])
    if s["state"] == "paused":
        t.draw("pause", "PAUSED  (P to resume)", W / 2, H / 2, WHITE, 32, "center")
    elif s["state"] == "gameover":
        arcade.draw_lbwh_rectangle_filled(0, 0, W, H, (0, 0, 0, 150))
        t.draw("go1", "GAME OVER", W / 2, H / 2 + 40, RED, 52, "center", bold=True)
        t.draw("go2", "   ".join(f"{p[1]} {int(p[2])}" for p in s["players"]) + f"   Level {s['level']}",
               W / 2, H / 2 - 10, WHITE, 22, "center")
        msg = ("ENTER = play again     ESC = menu" if s.get("can_restart")
               else "Waiting for the host to restart     ESC = leave")
        t.draw("go3", msg, W / 2, H / 2 - 50, GREY, 16, "center")


def _ability_bar(t, me):
    """Ship ability (SHIFT) and rechargeable shield, bottom right."""
    ab = me.get("ability")
    if me.get("barrier") is not None:
        draw_bar(W - 290, 84, 270, 10, me["barrier"], (110, 150, 255, 255))
        t.draw("barl", "SHIELD", W - 296, 84, GREY, 11, "right")
    if not ab:
        return
    ready = ab["cd"] <= 0
    draw_bar(W - 290, 58, 270, 16, 1.0 - ab["cd"], GREEN if ready else ORANGE)
    label = (f"[SHIFT] {ab['name']}  READY" if ready else f"[SHIFT] {ab['name']}")
    if ab["active"] > 0:
        label = f"{ab['name']} ACTIVE {ab['active']:0.1f}s"
    if ab["jam"]:
        label = f"{ab['name']} - ION STORM, OFFLINE"
    t.draw("abl", label, W - 20, 36, CYAN if ready else GREY, 13, "right")


def _perk_overlay(t, perk):
    arcade.draw_lbwh_rectangle_filled(0, 0, W, H, (0, 0, 0, 170))
    t.draw("pk1", "CHOOSE A PERK", W / 2, H / 2 + 190, GOLD, 40, "center", bold=True)
    t.draw("pk2", f"Press 1, 2 or 3   ({perk['left']:0.0f}s)", W / 2, H / 2 + 150, GREY, 16, "center")
    for i, (name, desc) in enumerate(perk["options"]):
        x = W / 2 - 400 + i * 280
        chosen = perk["chosen"] == i + 1
        arcade.draw_lbwh_rectangle_filled(x, H / 2 - 110, 260, 220, (30, 36, 70, 255))
        arcade.draw_lbwh_rectangle_outline(x, H / 2 - 110, 260, 220, GOLD if chosen else GREY,
                                           4 if chosen else 1)
        t.draw(f"pkn{i}", f"{i + 1}", x + 130, H / 2 + 70, GOLD, 34, "center", bold=True)
        t.draw(f"pkt{i}", name, x + 130, H / 2 + 20, WHITE, 17, "center", bold=True)
        t.draw(f"pkd{i}", desc, x + 130, H / 2 - 20, GREY, 13, "center")
    if perk["chosen"]:
        waiting = ", ".join(perk["waiting"])
        t.draw("pkw", f"Waiting for {waiting}..." if waiting else "", W / 2, H / 2 - 150, WHITE, 18, "center")


def _weapon_bar(t, s):
    x = 20
    for slot, name, unlocked, unlock_level, ammo in s["weapons"]:
        selected = slot == s["me"]["slot"]
        arcade.draw_lbwh_rectangle_filled(x, 12, 112, 44, (28, 32, 56, 255) if unlocked else (20, 22, 34, 255))
        arcade.draw_lbwh_rectangle_outline(x, 12, 112, 44, GOLD if selected else GREY, 3 if selected else 1)
        sub = (f"unlocks L{unlock_level}" if not unlocked
               else "ammo: inf" if ammo < 0 else f"ammo: {ammo}")
        color = RED if unlocked and ammo == 0 else (WHITE if unlocked else GREY)
        t.draw(f"wn{slot}", f"{slot} {name}", x + 6, 38, color, 12)
        t.draw(f"wa{slot}", sub, x + 6, 20, color, 11)
        x += 118
