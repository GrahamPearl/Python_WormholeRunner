"""The joining player's screen. It runs no simulation: it draws the snapshots the host
sends (interpolated), predicts its own ship locally so controls feel instant, and
sends its key presses to the host."""
import math
import time

import arcade

from .audio import AudioManager
from .config import settings
from .constants import ANGLE_SIGN, BACKGROUND_COLOR, SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from .game_view import INPUT_KEYS, WEAPON_KEYS
from .hud import draw_effects, draw_hazards, draw_hud, draw_ship_effects
from .player import TINTS
from .profile import profile
from .sprites import (POWERUP_KINDS, ROCK_SIZE_SCALE, ROCK_TINTS, AnimatedSprite, Background,
                      control_step)
from .ui import GREY, RED, TextCache
from .world import World

CATS = ("pups", "rocks", "aliens", "bullets", "ships")


class Ent:
    """A drawn object: its sprite plus previous/target pose for interpolation."""
    __slots__ = ("sprite", "px", "py", "pa", "tx", "ty", "ta", "row")

    def __init__(self, sprite, row):
        self.sprite, self.row = sprite, row
        self.px = self.tx = row[1]
        self.py = self.ty = row[2]
        self.pa = self.ta = row[3]


def _spec(key):
    return settings.get(f"graphics.{key}") or settings.get("graphics.ship")


class ClientView(arcade.View):
    def __init__(self, conn, welcome):
        super().__init__()
        self.conn = conn
        self.pid = welcome.get("pid", 2)
        self.host_name = welcome.get("name", "Host")
        settings.apply_overrides(welcome.get("settings", {}))     # play by the host's rules
        self.audio = AudioManager()
        self.text = TextCache()
        self.keys = set()
        self.world_camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        self.lists = {c: arcade.SpriteList() for c in CATS}
        self.wh_list = arcade.SpriteList()
        self.own_list = arcade.SpriteList()
        self.ents = {c: {} for c in CATS}
        self.wh_sprite = None
        self.effects = []
        self.hud = None
        self.world = None
        self.background = None
        self.ws = None
        self.zoom = self.zoom_target = 1.0
        self.snap_time, self.snap_dt = time.time(), 1 / 30
        self.host_ship = None
        self.want_slot = 1
        self.input_timer = 0.0
        self.thrust_cd = 0.0
        self.music_on = False
        self.notice, self.notice_timer = "", 0.0
        self.leaving = False
        self.haz_rows = []
        self.want_perk = 0
        self.banked = 0
        self.bank_dirty = False
        self.bank_timer = 0.0
        # predicted own ship (the sprite is made once we know which ship we fly)
        self.own_id = None
        self.own = None
        self.mults = (1.0, 1.0, 1.0)
        self.pred_ok = False
        self.px = self.py = self.pbearing = self.pspeed = 0.0

    # ------------------------------------------------------------ lifecycle
    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR

    def on_hide_view(self):
        self.audio.stop_music()
        self._shutdown()

    def _bank(self, me):
        """Credits earned in the host's game are added to this machine's profile."""
        credits = int(me.get("credits", 0))
        if credits < self.banked:            # the host started a new run
            self.banked = 0
        if credits > self.banked:
            profile.credits += credits - self.banked
            self.banked = credits
            self.bank_dirty = True

    def _shutdown(self):
        if self.bank_dirty:
            profile.save()
            self.bank_dirty = False
        if not self.leaving:
            self.leaving = True
            self.conn.close()
            settings.restore()

    def _leave(self, message=""):
        self._shutdown()
        from .menu_view import MenuView
        self.window.show_view(MenuView(message))

    # ------------------------------------------------------------ network in
    @staticmethod
    def _ship_sprite(ship_id, pid):
        cfg = settings.get(f"ships.{ship_id}") or settings.get("ships.scout")
        sprite = AnimatedSprite(_spec(cfg.get("graphic", "ship")))
        if TINTS.get(pid):
            sprite.color = TINTS[pid]
        return sprite

    def _new_sprite(self, cat, row):
        if cat == "rocks":
            sprite = AnimatedSprite(_spec("rock"), ROCK_SIZE_SCALE.get(row[4], 1.0))
            if row[5] in ROCK_TINTS:
                sprite.color = ROCK_TINTS[row[5]]
            return sprite
        if cat == "aliens":
            return AnimatedSprite(_spec(f"alien_{row[6]}"))
        if cat == "bullets":
            return AnimatedSprite(_spec(row[5]))
        if cat == "pups":
            kind = row[5]
            key = f"powerup_{kind}" if kind in POWERUP_KINDS else f"objective_{kind}"
            return AnimatedSprite(_spec(key))
        return self._ship_sprite(row[11], row[0])

    def _sync(self, cat, rows):
        ents, seen = self.ents[cat], set()
        for row in rows:
            key = row[0]
            if cat == "ships" and key == self.pid:
                self.host_ship = row
                continue
            seen.add(key)
            ent = ents.get(key)
            if ent is None:
                ent = ents[key] = Ent(self._new_sprite(cat, row), row)
                self.lists[cat].append(ent.sprite)
            else:
                ent.px, ent.py, ent.pa = ent.tx, ent.ty, ent.ta
                ent.tx, ent.ty, ent.ta = row[1], row[2], row[3]
                ent.row = row
        for key in [k for k in ents if k not in seen]:
            ents.pop(key).sprite.remove_from_sprite_lists()

    def _apply(self, m):
        now = time.time()
        self.snap_dt = max(0.01, min(0.25, 0.8 * self.snap_dt + 0.2 * (now - self.snap_time)))
        self.snap_time = now
        ws = m["ws"]
        if self.world is None or ws != self.ws:
            first = self.world is None
            self.ws = ws
            self.world = World(W * ws, H * ws)
            self.background = Background(self.world.width, self.world.height)
            self.zoom_target = 1.0 / ws
            if first:
                self.zoom = self.zoom_target
        self.host_ship = None
        for cat in CATS:
            self._sync(cat, m[cat])
        wh = m.get("wh")
        if wh is None:
            if self.wh_sprite:
                self.wh_sprite.remove_from_sprite_lists()
                self.wh_sprite = None
        else:
            if self.wh_sprite is None:
                self.wh_sprite = AnimatedSprite(_spec("wormhole"))
                self.wh_list.append(self.wh_sprite)
            self.wh_sprite.center_x, self.wh_sprite.center_y = wh[0], wh[1]
            self.wh_sprite.scale = self.wh_sprite.base_scale * wh[2]
            self.wh_sprite.angle = wh[3]
        self.haz_rows = m.get("haz", [])
        self.hud = m["hud"]
        me = self.hud["me"]
        self.mults = tuple(me.get("mult", (1.0, 1.0, 1.0)))
        self._bank(me)
        if self.own_id != me.get("ship"):
            if self.own is not None:
                self.own.remove_from_sprite_lists()
            self.own_id = me.get("ship", "scout")
            self.own = self._ship_sprite(self.own_id, self.pid)
        if self.hud["state"] != "perk":
            self.want_perk = 0
        if self.hud["state"] == "gameover":
            self.audio.stop_music()
            self.music_on = False
        elif not self.music_on:
            self.audio.play_music()
            self.music_on = True

    def _read_network(self):
        snaps = []
        for m in self.conn.poll():
            kind = m.get("t")
            if kind == "s":
                snaps.append(m)
            elif kind == "bye":
                self._leave("The host closed the game")
                return False
        for m in snaps:                       # sounds and effects must not be skipped
            for name in m.get("ev", []):
                self.audio.play(name)
            for x, y, r, dur, color in m.get("fx", []):
                self.effects.append([x, y, r, 0.0, dur, tuple(color)])
        if snaps:
            self._apply(snaps[-1])
        if not self.conn.alive or time.time() - self.conn.last_recv > settings.get("net.timeout"):
            self._leave("Lost connection to the host")
            return False
        return True

    # ------------------------------------------------------------ update
    def _mask(self):
        mask = 0
        for bit, key in INPUT_KEYS:
            if key in self.keys:
                mask |= bit
        return mask

    def _predict(self, dt):
        hs = self.host_ship
        if hs is None or self.world is None or self.own is None:
            self.pred_ok = False
            if self.own is not None:
                self.own.remove_from_sprite_lists()
            return
        if not self.own.sprite_lists:
            self.own_list.append(self.own)
        hx, hy, hspeed, hdx, hdy, hboost, hbear = hs[1], hs[2], hs[6], hs[7], hs[8], hs[9], hs[10]
        ww, wh = self.world.width, self.world.height
        age = time.time() - self.snap_time
        hrad = math.radians(hbear)       # where the host's ship is by now
        ex = (hx + (math.sin(hrad) * hspeed + hdx) * age) % ww
        ey = (hy + (math.cos(hrad) * hspeed + hdy) * age) % wh
        if not self.pred_ok:
            self.px, self.py, self.pbearing, self.pspeed = ex, ey, hbear, hspeed
            self.pred_ok = True
        k = self.keys
        self.pbearing, self.pspeed = control_step(
            self.pbearing, self.pspeed, dt, arcade.key.UP in k, arcade.key.DOWN in k,
            arcade.key.LEFT in k, arcade.key.RIGHT in k, bool(hboost), self.mults)
        rad = math.radians(self.pbearing)
        self.px = (self.px + (math.sin(rad) * self.pspeed + hdx) * dt) % ww
        self.py = (self.py + (math.cos(rad) * self.pspeed + hdy) * dt) % wh
        # ease toward the host's truth; big jumps (level change, knockback) snap
        dx, dy = self.world.delta(self.px, self.py, ex, ey)
        if math.hypot(dx, dy) > 200:
            self.px, self.py, self.pbearing, self.pspeed = ex, ey, hbear, hspeed
        else:
            f = min(1.0, 4 * dt)
            self.px = (self.px + dx * f) % ww
            self.py = (self.py + dy * f) % wh
        diff = (hbear - self.pbearing + 180) % 360 - 180
        if abs(diff) > 40:
            self.pbearing = (self.pbearing + diff * min(1.0, 6 * dt)) % 360
        if abs(hspeed - self.pspeed) > 120:
            self.pspeed += (hspeed - self.pspeed) * min(1.0, 6 * dt)
        s = self.own
        s.center_x, s.center_y = self.px, self.py
        s.angle = ANGLE_SIGN * self.pbearing
        s.alpha = int(hs[4])
        s.animate(dt)

    def on_update(self, delta_time):
        if self.leaving:
            return
        dt = min(delta_time, 1 / 20)
        if not self._read_network():
            return
        self.notice_timer = max(0.0, self.notice_timer - dt)
        self.input_timer -= dt
        if self.input_timer <= 0:               # tell the host what we are pressing
            self.input_timer = 1 / 30
            self.conn.send_latest({"t": "i", "k": self._mask(), "w": self.want_slot,
                                   "pk": self.want_perk})
        if self.world is None:
            return
        self.zoom += (self.zoom_target - self.zoom) * min(1.0, dt * settings.get("world.zoom_speed"))
        self.background.update(dt)
        for e in self.effects:
            e[3] += dt
        self.effects = [e for e in self.effects if e[3] < e[4]]

        f = min(1.0, (time.time() - self.snap_time) / self.snap_dt)
        ww, wh = self.world.width, self.world.height
        for cat in CATS:
            for e in self.ents[cat].values():
                dx, dy = self.world.delta(e.px, e.py, e.tx, e.ty)
                s = e.sprite
                s.center_x, s.center_y = (e.px + dx * f) % ww, (e.py + dy * f) % wh
                da = (e.ta - e.pa + 180) % 360 - 180
                s.angle = e.pa + da * f
                if cat == "ships":
                    s.alpha = int(e.row[4])
                elif cat == "pups" and e.row[5] in POWERUP_KINDS:
                    s.alpha = 120 if e.row[4] < 2 and int(e.row[4] * 6) % 2 == 0 else 255
                s.animate(dt)
        if self.wh_sprite:
            self.wh_sprite.animate(dt)
        self._predict(dt)
        self.thrust_cd -= dt
        if arcade.key.UP in self.keys and self.pspeed > 0 and self.pred_ok and self.thrust_cd <= 0:
            self.audio.play("thrust")
            self.thrust_cd = 0.3

    # ------------------------------------------------------------ drawing
    def on_draw(self):
        self.clear()
        if self.world is None or self.hud is None:
            self.gui_camera.use()
            self.text.draw("wait", f"Connected to {self.host_name} - waiting for the game...",
                           W / 2, H / 2, GREY, 20, "center")
            return
        cx, cy = self.world.center
        self.world_camera.position = (cx, cy)
        self.world_camera.zoom = self.zoom
        self.world_camera.use()
        self.background.draw()
        draw_hazards(self.haz_rows, time.time() % 1000)
        self.wh_list.draw()
        for cat in CATS:
            self.lists[cat].draw()
        self.own_list.draw()
        line = draw_effects(self.effects, self.zoom)
        for e in self.ents["ships"].values():
            sid = e.row[11]
            draw_ship_effects(e.sprite.center_x, e.sprite.center_y, 0.5 * e.sprite.height * 0.55,
                              e.row[5], settings.get(f"ships.{sid}.ability.range", 300), line)
        if self.host_ship is not None and self.own is not None:
            sid = self.host_ship[11]
            draw_ship_effects(self.own.center_x, self.own.center_y, 0.5 * self.own.height * 0.55,
                              self.host_ship[5], settings.get(f"ships.{sid}.ability.range", 300), line)
        for e in self.ents["bullets"].values():
            if e.row[4] > 0:
                arcade.draw_circle_outline(e.sprite.center_x, e.sprite.center_y, e.row[4],
                                           (255, 90, 90, 60), line * 0.6)
        for e in self.ents["pups"].values():
            if e.row[5] == "freighter":
                w = 70
                x, y = e.sprite.center_x - w / 2, e.sprite.center_y + e.sprite.height * 0.35 + 10
                arcade.draw_lbwh_rectangle_filled(x, y, w, 6, (20, 60, 30, 255))
                arcade.draw_lbwh_rectangle_filled(x, y, w * max(0.0, e.row[4]), 6, (90, 230, 120, 255))
        for e in self.ents["aliens"].values():
            frac, radius = e.row[4], e.row[5]
            if frac < 1.0:
                w = max(30.0, radius * 2)
                x, y = e.sprite.center_x - w / 2, e.sprite.center_y + radius + 8
                arcade.draw_lbwh_rectangle_filled(x, y, w, 5, (60, 20, 20, 255))
                arcade.draw_lbwh_rectangle_filled(x, y, w * max(0.0, frac), 5, RED)
        self.gui_camera.use()
        hud = dict(self.hud)
        if self.notice_timer > 0:
            hud["notice"] = self.notice
        draw_hud(self.text, hud)

    # ------------------------------------------------------------ input
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self._leave()
        elif self.hud and self.hud["state"] == "perk":
            if symbol in WEAPON_KEYS and WEAPON_KEYS[symbol] <= 3 and not self.hud["perk"]["chosen"]:
                self.want_perk = WEAPON_KEYS[symbol]
        elif symbol in WEAPON_KEYS:
            self._select_weapon(WEAPON_KEYS[symbol])
        elif symbol != arcade.key.P:
            self.keys.add(symbol)

    def _select_weapon(self, slot):
        if not self.hud:
            return
        for s, name, unlocked, unlock_level, _ammo in self.hud["weapons"]:
            if s == slot:
                if unlocked:
                    self.want_slot = slot
                else:
                    self.notice, self.notice_timer = f"{name} unlocks at level {unlock_level}", 2.0

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)
