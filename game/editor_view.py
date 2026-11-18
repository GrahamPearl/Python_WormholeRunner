"""In-game editor: pick images (tile sequences), sounds and tune settings.

Keys: UP/DOWN select | LEFT/RIGHT change (hold SHIFT for x10) | ENTER next file
      TAB / PAGEDOWN next section | SHIFT+TAB / PAGEUP previous section
      T test sound | R reset field | S save | ESC save and exit
"""
from dataclasses import dataclass

import arcade

from .assets import list_files, load_frames
from .audio import AudioManager
from .config import settings
from .constants import BACKGROUND_COLOR, IMAGES_DIR, SCREEN_HEIGHT as H, SCREEN_WIDTH as W, SOUNDS_DIR
from .ui import BLUE, CYAN, GOLD, GREEN, GREY, ORANGE, WHITE, TextCache

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
SOUND_EXT = (".wav", ".ogg", ".mp3", ".flac")

ROW_H, TOP, VISIBLE = 26, H - 100, 21
LABEL_X, VALUE_X, VALUE_W = 50, 420, 320


@dataclass
class Header:
    title: str


@dataclass
class Field:
    label: str
    path: str
    kind: str = "float"            # float | int | bool | file
    step: float = 1
    lo: float = 0
    hi: float = 1e9
    folder: object = None
    exts: tuple = ()
    allow_none: bool = False
    options: tuple = ()


def _title(key):
    return key.replace("_", " ").title()


ALIEN_FIELDS = {
    "drifter": (("Wave width", "wave_amp", "float", 10, 0, 500),
                ("Wave speed", "wave_freq", "float", 0.1, 0.1, 10)),
    "chaser": (("Turn rate (deg/s)", "turn_rate", "float", 10, 10, 720),
               ("Dies when it rams you", "dies_on_ram", "bool")),
    "sniper": (("Fire interval (s)", "fire_interval", "float", 0.1, 0.2, 20),
               ("Bullet speed", "bullet_speed", "float", 20, 50, 2000),
               ("Bullet damage", "bullet_damage", "int", 1, 1, 200),
               ("Keep distance", "keep_distance", "float", 20, 50, 1500)),
    "swarm": (("Fire interval (s)", "fire_interval", "float", 0.1, 0.2, 20),
              ("Bullet speed", "bullet_speed", "float", 20, 50, 2000),
              ("Bullet damage", "bullet_damage", "int", 1, 1, 200),
              ("Orbit radius", "orbit_radius", "float", 20, 60, 1500),
              ("Orbit speed (deg/s)", "orbit_speed", "float", 5, -360, 360),
              ("Group size", "group_size", "int", 1, 1, 12)),
    "seeker": (("Fire interval (s)", "fire_interval", "float", 0.1, 0.2, 20),
               ("Bullet speed", "bullet_speed", "float", 20, 50, 2000),
               ("Bullet damage", "bullet_damage", "int", 1, 1, 200),
               ("Detect range (sees cloaked ships)", "detect_range", "float", 50, 100, 3000)),
    "teleporter": (("Blink every (s)", "blink_interval", "float", 0.5, 1, 30),
                   ("Shots per burst", "burst_count", "int", 1, 1, 10),
                   ("Bullet speed", "bullet_speed", "float", 20, 50, 2000),
                   ("Bullet damage", "bullet_damage", "int", 1, 1, 200),
                   ("Blink distance from you", "ring", "float", 20, 100, 1500)),
    "minelayer": (("Drop a mine every (s)", "mine_interval", "float", 0.5, 0.5, 30),
                  ("Mine damage", "mine_damage", "int", 5, 1, 300),
                  ("Mine blast radius", "mine_blast", "float", 10, 20, 400)),
    "mothership": (("Boss every N levels", "boss_every", "int", 1, 1, 50),
                   ("Fire interval (s)", "fire_interval", "float", 0.1, 0.2, 20),
                   ("Bullet speed", "bullet_speed", "float", 20, 50, 2000),
                   ("Bullet damage", "bullet_damage", "int", 1, 1, 200),
                   ("Keep distance", "keep_distance", "float", 20, 50, 1500),
                   ("Launch fighter every (s)", "spawn_interval", "float", 0.5, 1, 60),
                   ("Ring bullets", "ring_bullets", "int", 1, 3, 48)),
}


def build_rows():
    rows = []

    def head(title):
        rows.append(Header(title))

    def field(*args, **kw):
        rows.append(Field(*args, **kw))

    # ---- images (tile sequences): ship, rock, wormhole, background, power-ups,
    # ---- one bullet image per weapon slot, and one image per alien type
    for key in settings.get("graphics"):
        head(f"Graphics: {_title(key)}")
        p = f"graphics.{key}."
        field("Image file", p + "file", "file", folder=IMAGES_DIR, exts=IMAGE_EXT)
        field("Tile width (px)", p + "frame_w", "int", 1, 1, 2048)
        field("Tile height (px)", p + "frame_h", "int", 1, 1, 2048)
        field("Tile count", p + "frames", "int", 1, 1, 256)
        field("Animation speed (fps, 0 = still)", p + "fps", "float", 1, 0, 60)
        field("Scale", p + "scale", "float", 0.1, 0.1, 8)

    head("Multiplayer")
    field("Your player name", "net.player_name", "text")
    field("Network port (both players)", "net.port", "int", 1, 1024, 65535)
    field("World updates per second", "net.snapshot_rate", "int", 5, 10, 60)
    field("Drop a silent player after (s)", "net.timeout", "float", 1, 2, 60)

    head("Game mode and credits")
    field("Mode (classic / expedition)", "game.mode", "choice", options=("classic", "expedition"))
    field("Starting credits (new profile)", "credits.start_credits", "int", 100, 0, 100000)
    field("Credits per alien score point", "credits.alien_factor", "float", 0.05, 0, 5)
    field("Credits per rock size", "credits.rock_per_size", "int", 1, 0, 100)
    field("Gold rock bonus per size", "credits.gold_rock", "int", 5, 0, 1000)
    field("Credits per power-up", "credits.powerup", "int", 1, 0, 100)
    field("Credits per crystal", "credits.crystal", "int", 1, 0, 200)
    field("Credits per rescued pod", "credits.rescue", "int", 5, 0, 500)
    field("Credits per level cleared (x level)", "credits.level_clear", "int", 10, 0, 1000)
    field("Credits for objective (x level)", "credits.objective", "int", 10, 0, 1000)

    for sid, cfg in settings.get("ships").items():
        head(f"Ship: {cfg['name']}")
        p = f"ships.{sid}."
        field("Price (credits)", p + "price", "int", 50, 0, 100000)
        field("Hull strength", p + "health", "int", 5, 10, 1000)
        field("Speed multiplier", p + "speed_mult", "float", 0.05, 0.3, 3)
        field("Acceleration multiplier", p + "accel_mult", "float", 0.05, 0.3, 3)
        field("Turn multiplier", p + "turn_mult", "float", 0.05, 0.3, 3)
        if cfg.get("ability"):
            field("Ability recharge (s)", p + "ability.cooldown", "float", 0.5, 1, 120)
            if "duration" in cfg["ability"]:
                field("Ability duration (s)", p + "ability.duration", "float", 0.5, 0.5, 30)
        if cfg.get("weapon"):
            w = p + "weapon."
            field("Own weapon damage", w + "damage", "float", 1, 1, 1000)
            field("Own weapon delay (s)", w + "cooldown", "float", 0.05, 0.05, 10)

    head("Rock types")
    for kind in settings.get("rock_types"):
        field(f"{_title(kind)} rock: from level", f"rock_types.{kind}.min_level", "int", 1, 1, 99)
        field(f"{_title(kind)} rock: chance weight", f"rock_types.{kind}.weight", "int", 1, 0, 100)

    head("Hazards and objectives")
    field("Nebula from level", "hazards.nebula_from", "int", 1, 1, 99)
    field("Black hole from level", "hazards.blackhole_from", "int", 1, 1, 99)
    field("Ion storm from level", "hazards.ion_from", "int", 1, 1, 99)
    field("Solar flare from level", "hazards.flare_from", "int", 1, 1, 99)
    field("Solar flare every (s)", "hazards.flare_interval", "float", 2, 8, 300)
    field("Solar flare damage", "hazards.flare_damage", "int", 5, 1, 300)
    field("Aliens notice hidden ships within", "hazards.cloak_detect", "float", 20, 0, 1000)
    field("Objectives enabled", "objectives.enabled", "bool")
    field("Crystals to collect (base)", "objectives.crystals_base", "int", 1, 1, 30)
    field("Pods to rescue (base)", "objectives.pods_base", "int", 1, 1, 20)
    field("Escort time (s)", "objectives.escort_seconds", "float", 5, 10, 300)
    field("Freighter health", "objectives.freighter_health", "int", 10, 20, 2000)

    head("World and camera")
    field("World growth per level", "world.growth_per_level", "float", 0.05, 0, 2)
    field("Max world size (x screen)", "world.max_scale", "float", 0.25, 1, 6)
    field("Zoom-out speed", "world.zoom_speed", "float", 0.1, 0.1, 10)

    head("Gravity")
    field("Strength", "physics.gravity", "float", 25000, 0, 5e6)
    field("Max pull per rock", "physics.max_accel", "float", 20, 0, 2000)
    field("Softening distance", "physics.softening", "float", 5, 1, 300)
    field("Drift damping", "physics.drift_damping", "float", 0.1, 0, 5)

    head("Ship")
    field("Max speed", "ship.max_speed", "float", 20, 50, 1500)
    field("Acceleration", "ship.acceleration", "float", 10, 10, 1500)
    field("Turn rate (deg/s)", "ship.turn_rate", "float", 10, 30, 720)
    field("Max health", "ship.max_health", "int", 5, 10, 1000)
    field("Damage per rock hit", "ship.hit_damage", "int", 5, 1, 1000)
    field("Health power-up gain", "ship.health_gain", "int", 5, 1, 1000)
    field("Invincible after hit (s)", "ship.grace_time", "float", 0.1, 0, 10)
    field("Speed boost multiplier", "ship.boost_multiplier", "float", 0.1, 1, 4)

    head("Rocks")
    field("Starting count", "rocks.count", "int", 1, 1, 60)
    field("Min speed", "rocks.min_speed", "float", 5, 5, 600)
    field("Max speed", "rocks.max_speed", "float", 5, 5, 600)
    field("Split angle", "rocks.split_angle", "float", 5, 5, 85)
    field("Fragment speed factor", "rocks.split_speed", "float", 0.05, 0.5, 3)
    field("Split when rocks collide", "rocks.split_on_rock_hit", "bool")
    field("Max rocks on screen", "rocks.max_rocks", "int", 1, 2, 150)
    field("Replacement rock delay (s)", "rocks.respawn_time", "float", 0.5, 0.5, 60)
    field("Damage to aliens hitting rocks", "rocks.alien_damage", "int", 5, 0, 500)

    for slot in range(1, 10):
        head(f"Weapon {slot}: {settings.get(f'weapons.w{slot}.name')}")
        p = f"weapons.w{slot}."
        field("Enabled", p + "enabled", "bool")
        field("Type", p + "type", "choice", options=("bolt", "homing", "mine"))
        field("Unlocks at level", p + "unlock_level", "int", 1, 1, 99)
        field("Damage", p + "damage", "float", 1, 1, 1000)
        field("Shot speed", p + "speed", "float", 50, 0, 3000)
        field("Delay between shots (s)", p + "cooldown", "float", 0.05, 0.02, 10)
        field("Range (px)", p + "range", "float", 50, 50, 5000)
        field("Starting ammo (-1 = unlimited)", p + "ammo", "int", 5, -1, 999)
        field("Ammo per pickup", p + "ammo_pack", "int", 5, 0, 999)
        field("Shots per trigger", p + "count", "int", 1, 1, 15)
        field("Spread angle", p + "spread", "float", 2, 0, 180)
        field("Targets it passes through", p + "pierce", "int", 1, 1, 20)
        field("Homing turn rate (deg/s)", p + "turn_rate", "float", 10, 0, 720)
        field("Blast radius (mines)", p + "blast_radius", "float", 10, 0, 600)
        field("Mine fuse (s)", p + "fuse", "float", 0.5, 0.5, 30)

    for kind, extra in ALIEN_FIELDS.items():
        head(f"Alien: {_title(kind)}")
        p = f"aliens.{kind}."
        field("Enabled", p + "enabled", "bool")
        field("Appears from level", p + "min_level", "int", 1, 1, 99)
        field("Health", p + "health", "float", 5, 1, 5000)
        field("Speed", p + "speed", "float", 10, 10, 800)
        field("Damage when touching ship", p + "contact_damage", "int", 5, 0, 500)
        field("Score", p + "score", "int", 10, 0, 100000)
        for label, key, kind_, *rest in extra:
            step, lo, hi = rest if rest else (1, 0, 1e9)
            field(label, p + key, kind_, step, lo, hi)

    head("Timing")
    field("Power-up every (s)", "timing.powerup_interval", "float", 0.5, 1, 60)
    field("Power-up stays (s)", "timing.powerup_lifetime", "float", 0.5, 2, 60)
    field("Wormhole earliest (s)", "timing.wormhole_min_delay", "float", 0.5, 1, 120)
    field("Wormhole latest (s)", "timing.wormhole_max_delay", "float", 0.5, 1, 120)
    field("Wormhole stays (s)", "timing.wormhole_lifetime", "float", 0.5, 2, 60)
    field("Speed boost lasts (s)", "timing.speed_boost_time", "float", 0.5, 1, 60)
    field("Invincibility lasts (s)", "timing.invincible_time", "float", 0.5, 1, 60)

    head("Difficulty per level")
    field("Extra rocks", "difficulty.extra_rocks_per_level", "int", 1, 0, 10)
    field("Rock speed increase", "difficulty.speed_per_level", "float", 0.02, 0, 1)
    field("Gravity increase", "difficulty.gravity_per_level", "float", 0.02, 0, 2)
    field("Alien health increase", "difficulty.alien_health_per_level", "float", 0.02, 0, 2)
    field("Alien power-up drop chance", "difficulty.alien_drop_chance", "float", 0.05, 0, 1)

    head("Audio volume")
    field("Music volume", "audio.music_volume", "float", 0.05, 0, 1)
    field("Sound effects volume", "audio.sfx_volume", "float", 0.05, 0, 1)
    for event in settings.get("audio.events"):
        head(f"Sound event: {event}   (T = test)")
        field("File", f"audio.events.{event}.file", "file", folder=SOUNDS_DIR,
              exts=SOUND_EXT, allow_none=True)
        field("Volume", f"audio.events.{event}.volume", "float", 0.05, 0, 1)
    return rows


class EditorView(arcade.View):
    def __init__(self):
        super().__init__()
        self.rows = build_rows()
        self.sel = next(i for i, r in enumerate(self.rows) if isinstance(r, Field))
        self.scroll = 0
        self.text = TextCache()
        self.audio = AudioManager()
        self.dirty = False
        self.message = ""
        self.editing = False      # typing into a text field
        self.hold = None          # (direction, big) while LEFT/RIGHT is held
        self.hold_time = 0.0
        self.repeat_time = 0.0
        self.time = 0.0
        self.preview_key = "ship"
        self.preview_sig = None
        self.preview_frames = []
        self.preview_list = arcade.SpriteList()
        self._fix_scroll()

    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR

    def on_hide_view(self):
        self.audio.stop_music()

    # ------------------------------------------------------------ editing
    @property
    def field(self):
        return self.rows[self.sel]

    def _move(self, step):
        i = self.sel
        while True:
            i += step
            if i < 0 or i >= len(self.rows):
                return
            if isinstance(self.rows[i], Field):
                self.sel = i
                self._fix_scroll()
                return

    def _jump_section(self, step):
        """Move to the first field of the next (or current/previous) section."""
        starts = [k + 1 for k, r in enumerate(self.rows) if isinstance(r, Header)]
        if step > 0:
            later = [s for s in starts if s > self.sel]
            target = later[0] if later else None
        else:
            earlier = [s for s in starts if s < self.sel]
            target = earlier[-1] if earlier else None
        if target is not None:
            self.sel = target
            self._fix_scroll()

    def _fix_scroll(self):
        if self.sel - 1 < self.scroll:
            self.scroll = max(0, self.sel - 1)
        elif self.sel >= self.scroll + VISIBLE:
            self.scroll = self.sel - VISIBLE + 1

    def _change(self, direction, big=False):
        f = self.field
        cur = settings.get(f.path)
        if f.kind == "text":
            return
        if f.kind == "bool":
            new = not cur
        elif f.kind in ("file", "choice"):
            options = (list(f.options) if f.kind == "choice"
                       else ([""] if f.allow_none else []) + list_files(f.folder, f.exts))
            if not options:
                return
            idx = options.index(cur) if cur in options else -1
            new = options[(idx + direction) % len(options)]
        else:
            delta = direction * f.step * (10 if big else 1)
            new = max(f.lo, min(f.hi, (cur or 0) + delta))
            new = int(round(new)) if f.kind == "int" else round(new, 4)
        if new != cur:
            settings.set(f.path, new)
            self.dirty = True
            self.message = ""

    def _test_sound(self):
        path = self.field.path
        if not path.startswith("audio.events."):
            return
        event = path.split(".")[2]
        if event == "music":
            if self.audio.music_playing:
                self.audio.stop_music()
            else:
                self.audio.play_music()
        else:
            self.audio.play(event)

    def _save(self):
        try:
            settings.save()
            self.dirty = False
            self.message = "Saved to config.json"
        except OSError as exc:
            self.message = f"Could not save: {exc}"

    # ------------------------------------------------------------ events
    def on_text(self, text):
        if self.editing:
            cur = str(settings.get(self.field.path) or "")
            for ch in text:
                if ch.isprintable() and len(cur) < 16:
                    cur += ch
            settings.set(self.field.path, cur)
            self.dirty = True

    def on_key_press(self, symbol, modifiers):
        k, shift = arcade.key, bool(modifiers & arcade.key.MOD_SHIFT)
        if self.editing:
            if symbol == k.BACKSPACE:
                settings.set(self.field.path, str(settings.get(self.field.path) or "")[:-1])
                self.dirty = True
            elif symbol in (k.ENTER, k.NUM_ENTER, k.ESCAPE):
                if not str(settings.get(self.field.path)).strip():
                    settings.reset(self.field.path)
                self.editing = False
            return
        if symbol == k.UP:
            self._move(-1)
        elif symbol == k.DOWN:
            self._move(1)
        elif symbol in (k.LEFT, k.RIGHT):
            direction = -1 if symbol == k.LEFT else 1
            self._change(direction, shift)
            self.hold, self.hold_time, self.repeat_time = (direction, shift), 0.0, 0.0
        elif symbol in (k.ENTER, k.NUM_ENTER):
            if self.field.kind == "text":
                self.editing = True
            else:
                self._change(1)
        elif symbol == k.TAB:
            self._jump_section(-1 if shift else 1)
        elif symbol == k.PAGEDOWN:
            self._jump_section(1)
        elif symbol == k.PAGEUP:
            self._jump_section(-1)
        elif symbol == k.T:
            self._test_sound()
        elif symbol == k.R:
            settings.reset(self.field.path)
            self.dirty = True
        elif symbol == k.S:
            self._save()
        elif symbol == k.ESCAPE:
            self._save()
            from .menu_view import MenuView
            self.window.show_view(MenuView())

    def on_key_release(self, symbol, modifiers):
        if symbol in (arcade.key.LEFT, arcade.key.RIGHT):
            self.hold = None

    def on_mouse_scroll(self, x, y, sx, sy):
        self._move(-1 if sy > 0 else 1)

    def on_mouse_press(self, x, y, button, modifiers):
        i = int((TOP + ROW_H / 2 - y) // ROW_H)
        idx = self.scroll + i
        if not (0 <= i < VISIBLE and 0 <= idx < len(self.rows)):
            return
        if not isinstance(self.rows[idx], Field):
            return
        self.sel = idx
        if VALUE_X <= x <= VALUE_X + 40:
            self._change(-1)
        elif VALUE_X + VALUE_W - 40 <= x <= VALUE_X + VALUE_W:
            self._change(1)

    def on_update(self, delta_time):
        self.time += delta_time
        if self.hold and self.field.kind in ("float", "int"):
            self.hold_time += delta_time
            if self.hold_time > 0.4:
                self.repeat_time += delta_time
                while self.repeat_time > 0.06:
                    self.repeat_time -= 0.06
                    self._change(*self.hold)

    # ------------------------------------------------------------ drawing
    @staticmethod
    def _fmt(f, value):
        if f.kind == "bool":
            return "ON" if value else "OFF"
        if f.kind == "text":
            return str(value)
        if f.kind in ("file", "choice"):
            return str(value) if value else "(none)"
        if f.kind == "int":
            return str(int(value))
        return f"{value:g}"

    def _update_preview(self):
        f = self.field
        if f.path.startswith("graphics."):
            self.preview_key = f.path.split(".")[1]
        spec = settings.get(f"graphics.{self.preview_key}")
        sig = (spec["file"], spec["frame_w"], spec["frame_h"], spec["frames"])
        if sig != self.preview_sig:
            self.preview_sig = sig
            self.preview_frames = load_frames(spec)
            self.preview_sprite = arcade.Sprite(self.preview_frames[0])
            self.preview_sprite.center_x, self.preview_sprite.center_y = 1010, 440
            self.preview_list.clear()
            self.preview_list.append(self.preview_sprite)
        fps = float(spec["fps"]) or 6.0     # preview animates even when the game shows it still
        idx = int(self.time * fps) % len(self.preview_frames)
        sprite = self.preview_sprite
        sprite.texture = self.preview_frames[idx]
        sprite.scale = min(8.0, 260 / max(spec["frame_w"], spec["frame_h"]))
        return spec, idx

    def on_draw(self):
        self.clear()
        t = self.text
        t.draw("title", "GAME EDITOR", 40, H - 55, GOLD, 30, bold=True)
        t.draw("status", "Unsaved changes" if self.dirty else (self.message or "All changes saved"),
               W - 40, H - 50, ORANGE if self.dirty else GREEN, 14, "right")

        for n in range(VISIBLE):
            idx = self.scroll + n
            if idx >= len(self.rows):
                break
            row, y = self.rows[idx], TOP - n * ROW_H
            if isinstance(row, Header):
                t.draw(f"l{n}", row.title, 40, y, GOLD, 15, "left", "center", True)
                t.draw(f"v{n}", "", VALUE_X, y, WHITE, 14)
                continue
            if idx == self.sel:
                arcade.draw_lbwh_rectangle_filled(30, y - ROW_H / 2, 730, ROW_H, BLUE)
            t.draw(f"l{n}", row.label, LABEL_X, y, WHITE, 14, "left", "center")
            value = self._fmt(row, settings.get(row.path))
            if row.kind == "text" and idx == self.sel:
                value = value + ("_" if self.editing else "   (ENTER to edit)")
            t.draw(f"v{n}", f"<  {value}  >" if idx == self.sel else value,
                   VALUE_X + VALUE_W / 2 if idx == self.sel else VALUE_X, y,
                   CYAN if idx == self.sel else GREY, 14,
                   "center" if idx == self.sel else "left", "center")

        arcade.draw_lbwh_rectangle_filled(790, 110, 450, 520, (18, 22, 44, 255))
        arcade.draw_lbwh_rectangle_outline(790, 110, 450, 520, WHITE, 2)
        spec, idx = self._update_preview()
        t.draw("ptitle", f"Preview: {self.preview_key}", 1015, 600, GOLD, 16, "center", bold=True)
        self.preview_list.draw()
        t.draw("pinfo", f"tile {idx + 1}/{len(self.preview_frames)}   "
               f"{spec['frame_w']}x{spec['frame_h']} px   {spec['file']}", 1015, 150, GREY, 12, "center")
        t.draw("pnote", "Image changes apply when a new game starts", 1015, 126, GREY, 11, "center")

        t.draw("h1", "UP/DOWN select    LEFT/RIGHT change (SHIFT = x10)    ENTER next file    "
               "TAB next section", 40, 54, GREY, 12)
        t.draw("h2", "T test sound    R reset field    S save    ESC save & back to menu    "
               "Mouse: click row or < >, scroll wheel", 40, 32, GREY, 12)
