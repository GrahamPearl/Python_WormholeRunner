"""The Hangar: spend credits on ships and pick the one you fly."""
import arcade

from .config import settings
from .constants import BACKGROUND_COLOR, SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from .profile import profile
from .sprites import AnimatedSprite, Background
from .ui import CYAN, GOLD, GREEN, GREY, RED, WHITE, TextCache


def _weapon_line(w):
    if not w:
        return "Standard weapons only"
    kind = {"bolt": "shot", "homing": "homing shot", "mine": "mine", "pulse": "blast"}.get(w["type"], w["type"])
    extra = []
    if w.get("silent"):
        extra.append("silent")
    if w.get("heal"):
        extra.append(f"heals ally +{w['heal']}")
    if w.get("count", 1) > 1:
        extra.append(f"x{w['count']} pellets")
    if w.get("pierce", 1) > 1:
        extra.append(f"pierces {w['pierce']}")
    return f"{w['name']} (key 7): {kind}, {w['damage']} dmg" + (", " + ", ".join(extra) if extra else "")


class HangarView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ids = list(settings.get("ships"))
        self.sel = max(0, self.ids.index(profile.selected)) if profile.selected in self.ids else 0
        self.text = TextCache()
        self.background = Background(W, H)
        self.time = 0.0
        self.message, self.msg_color = "", GREY
        self.preview_id = None
        self.preview_list = arcade.SpriteList()

    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR

    def _ship(self):
        return settings.get(f"ships.{self.ids[self.sel]}")

    def on_update(self, dt):
        self.time += dt
        self.background.update(dt)
        sid = self.ids[self.sel]
        if sid != self.preview_id:
            self.preview_id = sid
            self.preview_sprite = AnimatedSprite(settings.get(f"graphics.{self._ship()['graphic']}"))
            self.preview_sprite.scale = 3.0
            self.preview_sprite.center_x, self.preview_sprite.center_y = 1010, 470
            self.preview_list.clear()
            self.preview_list.append(self.preview_sprite)
        self.preview_sprite.animate(dt)
        self.preview_sprite.angle = (self.time * 25) % 360

    def on_draw(self):
        self.clear()
        self.background.draw()
        t = self.text
        t.draw("title", "HANGAR", 60, H - 70, GOLD, 40, bold=True)
        t.draw("cr", f"Credits: {profile.credits}", W - 60, H - 62, GOLD, 24, "right", bold=True)
        for i, sid in enumerate(self.ids):
            cfg = settings.get(f"ships.{sid}")
            y = H - 150 - i * 60
            on = i == self.sel
            if on:
                arcade.draw_lbwh_rectangle_filled(40, y - 26, 560, 52, (50, 70, 130, 255))
            if sid == profile.selected:
                tag, color = "IN USE", GREEN
            elif sid in profile.owned:
                tag, color = "OWNED", CYAN
            else:
                tag, color = f"{cfg['price']} cr", (GOLD if profile.credits >= cfg["price"] else RED)
            t.draw(f"n{i}", cfg["name"], 60, y, WHITE if on else GREY, 22, "left", "center", on)
            t.draw(f"p{i}", tag, 580, y, color, 18, "right", "center", True)

        cfg = self._ship()
        arcade.draw_lbwh_rectangle_filled(660, 120, 580, 560, (18, 22, 44, 255))
        arcade.draw_lbwh_rectangle_outline(660, 120, 580, 560, WHITE, 2)
        self.preview_list.draw()
        t.draw("sn", cfg["name"], 950, 630, GOLD, 28, "center", bold=True)
        t.draw("sd", cfg["desc"][:70], 950, 600, GREY, 13, "center")
        t.draw("s1", f"Hull {int(cfg['health'])}    Speed x{cfg['speed_mult']:.2f}    "
               f"Accel x{cfg['accel_mult']:.2f}    Turn x{cfg['turn_mult']:.2f}", 950, 350, WHITE, 14, "center")
        ab = cfg.get("ability")
        if ab:
            t.draw("a1", f"Ability [SHIFT]: {ab['name']}  (recharge {ab['cooldown']:g}s)", 950, 312, CYAN, 15, "center", bold=True)
            t.draw("a2", ab["desc"][:78], 950, 288, GREY, 12, "center")
        else:
            t.draw("a1", "No special ability", 950, 312, GREY, 15, "center")
            t.draw("a2", "", 950, 288, GREY, 12, "center")
        passive = cfg.get("passive") or {}
        notes = []
        if passive.get("shield_max"):
            notes.append(f"Rechargeable shield {int(passive['shield_max'])}")
        if passive.get("regen"):
            notes.append(f"Self-repair {passive['regen']:g}/s")
        t.draw("pa", ", ".join(notes), 950, 258, GREEN, 13, "center")
        t.draw("w1", _weapon_line(cfg.get("weapon")), 950, 226, WHITE, 13, "center")

        t.draw("msg", self.message, 950, 170, self.msg_color, 16, "center")
        sid = self.ids[self.sel]
        if sid == profile.selected:
            action = "This is your current ship"
        elif sid in profile.owned:
            action = "ENTER: use this ship"
        else:
            action = f"ENTER: buy for {cfg['price']} credits"
        t.draw("act", action, 950, 140, GOLD, 16, "center", bold=True)
        t.draw("help", "UP/DOWN choose    ENTER buy / use    ESC back      "
               "Credits are earned in-game only", 40, 36, GREY, 13)

    def on_key_press(self, symbol, modifiers):
        k = arcade.key
        if symbol == k.UP:
            self.sel = (self.sel - 1) % len(self.ids)
            self.message = ""
        elif symbol == k.DOWN:
            self.sel = (self.sel + 1) % len(self.ids)
            self.message = ""
        elif symbol in (k.ENTER, k.NUM_ENTER):
            self._activate()
        elif symbol == k.ESCAPE:
            from .menu_view import MenuView
            self.window.show_view(MenuView())

    def on_mouse_press(self, x, y, button, modifiers):
        for i in range(len(self.ids)):
            if abs(y - (H - 150 - i * 60)) < 26 and 40 < x < 600:
                self.sel = i
                self._activate()

    def _activate(self):
        sid = self.ids[self.sel]
        cfg = self._ship()
        if sid in profile.owned:
            profile.select(sid)
            self.message, self.msg_color = f"{cfg['name']} selected", GREEN
        elif profile.buy(sid):
            profile.select(sid)
            self.message, self.msg_color = f"Bought {cfg['name']}!", GREEN
        else:
            self.message, self.msg_color = f"Not enough credits - you need {cfg['price'] - profile.credits} more", RED
