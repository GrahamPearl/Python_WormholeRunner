"""The playable view. It runs the whole simulation - for single player, and for the
host of a LAN game (the remote player's ship is just another ship driven by network input)."""
import math
import random

import arcade

from . import net
from .aliens import ALIEN_CLASSES, Chaser, Swarm
from .audio import AudioManager
from .config import settings
from .constants import ANGLE_SIGN, BACKGROUND_COLOR, SCREEN_HEIGHT as H, SCREEN_WIDTH as W
from .game_features import FeaturesMixin
from .hud import draw_effects, draw_hazards, draw_hud, draw_ship_effects
from .perks import PERKS
from .physics import gravity_accel
from .player import Player
from .profile import profile
from .sprites import POWERUP_KINDS, Background, PowerUp, Rock, Wormhole
from .ui import RED, TextCache
from .weapons import Bullet
from .world import World

DIAG = math.sqrt(0.5)   # rocks start out travelling along exact diagonals

WEAPON_KEYS = {}
for _n in range(1, 10):
    WEAPON_KEYS[getattr(arcade.key, f"KEY_{_n}")] = _n
    WEAPON_KEYS[getattr(arcade.key, f"NUM_{_n}")] = _n

# Bit flags the joiner sends for its held keys (SHIFT = ship ability)
IN_UP, IN_DOWN, IN_LEFT, IN_RIGHT, IN_FIRE, IN_ABILITY = 1, 2, 4, 8, 16, 32
INPUT_KEYS = ((IN_UP, arcade.key.UP), (IN_DOWN, arcade.key.DOWN), (IN_LEFT, arcade.key.LEFT),
              (IN_RIGHT, arcade.key.RIGHT), (IN_FIRE, arcade.key.SPACE),
              (IN_ABILITY, arcade.key.LSHIFT), (IN_ABILITY, arcade.key.RSHIFT))
ABILITY_KEYS = (arcade.key.LSHIFT, arcade.key.RSHIFT)

CLASSIC_ALIENS = ("drifter", "chaser", "sniper", "swarm")
EXPEDITION_ALIENS = CLASSIC_ALIENS + ("seeker", "teleporter", "minelayer")


class GameView(FeaturesMixin, arcade.View):
    def __init__(self, host=False):
        super().__init__()
        self.audio = AudioManager()
        self.text = TextCache()
        self.keys = set()
        self.world_camera = arcade.Camera2D()    # follows the (zoomed) world
        self.gui_camera = arcade.Camera2D()      # fixed HUD
        self.ship_list = arcade.SpriteList()
        self.rock_list = arcade.SpriteList()
        self.alien_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.powerup_list = arcade.SpriteList()
        self.wormhole_list = arcade.SpriteList()
        self.freighter_list = arcade.SpriteList()
        self.zoom = 1.0

        self.local = Player(1, settings.get("net.player_name") or "Pilot", local=True,
                            ship_id=profile.selected)
        self.local.keys = self.keys
        self.players = [self.local]
        self.remote = None
        self.server = None
        self.net_note = ""
        self.pending_events, self.new_effects = [], []
        self.snap_timer, self.seq, self.next_id = 0.0, 0, 1
        self.notice, self.notice_timer = "", 0.0
        self.banked = 0
        self.hazards, self.flare, self.flare_timer = [], None, 30.0
        self.freighter = None
        self.perk_timer = 0.0
        self.objective = {"type": "none", "need": 0, "got": 0, "done": True, "ok": False,
                          "time": 0.0, "total": 0.0}
        if host:
            self._start_server()
        self.new_game()

    # ------------------------------------------------------------ networking (host side)
    def _start_server(self):
        port = int(settings.get("net.port"))
        try:
            self.server = net.GameServer(port, f"{self.local.name}'s game")
        except OSError as exc:
            self.net_note = f"Could not host on port {port}: {exc.strerror or exc}"
            return
        ips = net.lan_ipv4_addresses() or ["<this PC's IP>"]
        self.host_addr = f"{ips[0]}:{port}"
        self.discover_note = "" if self.server.discoverable else "  (LAN discovery unavailable - share the address)"

    def _net_status(self):
        if self.server is None:
            return self.net_note
        if self.remote:
            return f"Multiplayer: {self.remote.name} is connected"
        return (f"Hosting on {self.host_addr} - waiting for a second player "
                f"(they can join at any time){self.discover_note}")

    def _network_tick(self, dt):
        srv = self.server
        if srv is None:
            return
        joined = srv.poll_join()
        if joined:
            self._add_remote(*joined)
        if self.remote:
            for msg in srv.client_messages():
                kind = msg.get("t")
                if kind == "i":
                    self._remote_input(msg)
                elif kind == "bye":
                    self._remove_remote("left the game")
                    break
        if self.remote and srv.client_lost(settings.get("net.timeout")):
            self._remove_remote("lost connection")
        if self.remote:
            self.snap_timer += dt
            if self.snap_timer >= 1.0 / max(5, settings.get("net.snapshot_rate")):
                self.snap_timer = 0.0
                self.seq += 1
                srv.info.update(players=len(self.players), level=self.level)
                srv.client.send_latest(self._snapshot(self.remote))
                self.pending_events, self.new_effects = [], []

    def _add_remote(self, conn, hello):
        name = str(hello.get("name") or "Player 2")[:16]
        if name == self.local.name:
            name += " 2"
        self.remote = Player(2, name, local=False, ship_id=str(hello.get("ship", "scout")))
        self.players.append(self.remote)
        ship = self.remote.ship
        ref = self.local.ship
        ship.center_x, ship.center_y = ref.center_x + 70, ref.center_y
        ship.grace_timer = 2.0
        self.ship_list.append(ship)
        conn.send({"t": "welcome", "v": net.PROTO_VERSION, "pid": 2, "name": self.local.name,
                   "settings": settings.synced_sections()})
        self.notice, self.notice_timer = f"{name} joined the game", 3.0
        self.pending_events, self.new_effects = [], []
        if self.state == "perk":               # joined during a perk pick: give them options
            self.remote.perk_options = random.sample(list(PERKS), 3)

    def _remove_remote(self, why):
        if not self.remote:
            return
        self.notice, self.notice_timer = f"{self.remote.name} {why}", 3.0
        self.remote.ship.remove_from_sprite_lists()
        self.players.remove(self.remote)
        self.remote = None
        if self.server:
            self.server.drop_client()
            self.server.info.update(players=1)
        if self.state == "playing" and not any(p.alive for p in self.players):
            self._game_over()
        elif self.state == "perk" and all(q.perk_choice for q in self.players):
            self.state = "playing"

    def _remote_input(self, msg):
        p = self.remote
        mask = int(msg.get("k", 0))
        p.keys = {key for bit, key in INPUT_KEYS if mask & bit}
        want = int(msg.get("w", 1))
        if want != p.last_want:
            p.last_want = want
            if p.weapons.select(want, self.level):
                self._sfx("weapon_switch", p.id)
        pk = int(msg.get("pk", 0))
        if pk != p.last_pk:
            p.last_pk = pk
            self._pick_perk(p, pk)

    def _sfx(self, name, who=None):
        """Play a sound for everyone (who=None) or for one player."""
        if who is None or who == self.local.id:
            self.audio.play(name)
        if self.remote and (who is None or who == self.remote.id):
            self.pending_events.append(name)

    def _nid(self, sprite):
        nid = getattr(sprite, "net_id", None)
        if nid is None:
            self.next_id += 1
            nid = sprite.net_id = self.next_id
        return nid

    def _snapshot(self, to):
        r1 = lambda v: round(v, 1)
        ships = []
        for p in self.players:
            if p.alive:
                s = p.ship
                ships.append([p.id, r1(s.center_x), r1(s.center_y), round(ANGLE_SIGN * s.bearing, 1),
                              int(s.alpha), self.ship_flags(s), r1(s.speed),
                              r1(s.drift_x), r1(s.drift_y), 1 if s.boost_timer > 0 else 0,
                              round(s.bearing, 1), p.ship_id])
        pups = [[self._nid(p), r1(p.center_x), r1(p.center_y), 0, round(p.life, 1), p.kind]
                for p in self.powerup_list]
        if self.freighter:
            f = self.freighter
            pups.append([self._nid(f), r1(f.center_x), r1(f.center_y), int(f.angle) % 360,
                         round(max(0, f.health) / f.max_health, 2), "freighter"])
        wh = self.wormhole
        return {
            "t": "s", "n": self.seq, "lvl": self.level, "ws": self.world_scale,
            "ships": ships,
            "rocks": [[self._nid(r), r1(r.center_x), r1(r.center_y), int(r.angle) % 360,
                       r.size_class, r.kind] for r in self.rock_list],
            "aliens": [[self._nid(a), r1(a.center_x), r1(a.center_y), int(a.angle) % 360,
                        round(max(0, a.health) / a.max_health, 2), r1(a.hit_radius), a.kind]
                       for a in self.alien_list],
            "bullets": [[self._nid(b), r1(b.center_x), r1(b.center_y), int(b.angle) % 360,
                         r1(b.blast * 0.45) if b.kind == "mine" and b.arm <= 0 else 0, b.gfx]
                        for b in self.bullet_list],
            "pups": pups,
            "haz": self.hazard_rows(),
            "wh": ([r1(wh.center_x), r1(wh.center_y), round(wh._grow(), 2), int(wh.angle) % 360,
                    round(max(0.0, wh.lifetime - wh.age), 1)] if wh else None),
            "fx": self.new_effects,
            "ev": self.pending_events,
            "hud": self._hud_for(to),
        }

    def _hud_for(self, p):
        ship = p.ship
        boost = settings.get("ship.boost_multiplier") if ship.boost_timer > 0 else 1.0
        boss = next((a for a in self.alien_list if a.kind == "mothership"), None)
        banner = [self.banner_text, self.banner_sub] if self.banner_timer > 0 else None
        net_text = self._net_status() if (self.server or self.net_note) else ""
        ability = None
        if ship.ability_type:
            cd_max = max(0.1, float(ship.ability["cooldown"]) * p.cd_mult)
            ability = {"name": ship.ability["name"], "cd": round(min(1.0, ship.ability_cd / cd_max), 3),
                       "active": round(ship.active, 1), "jam": bool(ship.jammed)}
        obj_text = self.objective_text()
        return {
            "level": self.level, "ws": round(self.world_scale, 2), "state": self.state,
            "mode": settings.get("game.mode"),
            "can_restart": p.local, "banner": banner,
            "notice": self.notice if self.notice_timer > 0 else "",
            "wh_left": (round(max(0.0, self.wormhole.lifetime - self.wormhole.age), 1)
                        if self.wormhole else None),
            "boss": round(max(0, boss.health) / boss.max_health, 3) if boss else None,
            "obj": obj_text or None,
            "net": net_text,
            "perk": self.perk_hud(p),
            "me": {"id": p.id, "health": round(ship.health / ship.max_health, 3),
                   "speed": round(ship.speed / (settings.get("ship.max_speed") * ship.speed_mult * boost), 3),
                   "boost": round(ship.boost_timer, 1), "shield": round(ship.shield_timer, 1),
                   "slot": p.weapons.slot, "alive": p.alive, "ship": p.ship_id,
                   "mult": [round(m, 3) for m in ship.mults], "credits": int(p.credits_run),
                   "ability": ability,
                   "barrier": (round(ship.shield_hp / ship.shield_max, 3) if ship.shield_max > 0 else None)},
            "weapons": [[s, c["name"], 1 if p.weapons.unlocked(s, self.level) else 0,
                         c["unlock_level"], p.weapons.ammo[s]]
                        for s in range(1, 10) if (c := p.weapons.cfg(s)).get("enabled")],
            "players": [[q.id, q.name, round(q.score), round(q.ship.health / q.ship.max_health, 3),
                         q.alive] for q in self.players],
        }

    # ------------------------------------------------------------ setup
    def new_game(self):
        self.level = 1
        self.time = 0.0
        self.state = "playing"        # playing | paused | perk | gameover
        self.banked = 0
        self.ship_list.clear()
        for p in self.players:
            p.reset()
            self.ship_list.append(p.ship)
        self._start_level(first=True)

    def alive_players(self):
        return [p for p in self.players if p.alive]

    def ref_ship(self):
        alive = self.alive_players()
        return (alive[0] if alive else self.local).ship

    def nearest_ship(self, x, y, alien=None):
        """Closest ship the alien can see (cloaked / nebula-hidden ships are skipped unless
        very close). Returns None when it sees nobody."""
        best, best_d = None, 1e18
        for p in self.alive_players():
            ship = p.ship
            dx, dy = self.world.delta(x, y, ship.center_x, ship.center_y)
            d = math.hypot(dx, dy)
            if alien is not None and self._hidden_from(alien, ship, d):
                continue
            if d < best_d:
                best, best_d = ship, d
        if best is None and alien is None:
            return self.ref_ship()
        return best

    def _start_level(self, first=False):
        self.world_scale = min(settings.get("world.max_scale"),
                               1.0 + settings.get("world.growth_per_level") * (self.level - 1))
        self.world = World(W * self.world_scale, H * self.world_scale)
        self.background = Background(self.world.width, self.world.height)
        self.zoom_target = 1.0 / self.world_scale
        if first:
            self.zoom = self.zoom_target
        for sprite_list in (self.rock_list, self.alien_list, self.bullet_list,
                            self.powerup_list, self.wormhole_list):
            sprite_list.clear()
        self.effects = []
        self.wormhole = None
        cx, cy = self.world.center
        n = len(self.players)
        for i, p in enumerate(self.players):
            if not p.alive:
                p.revive()
            if not p.ship.sprite_lists:
                self.ship_list.append(p.ship)
            p.ship.center_x, p.ship.center_y = cx + (i - (n - 1) / 2) * 80, cy
            p.ship.drift_x = p.ship.drift_y = 0.0
            p.ship.active = 0.0
            if not first:
                p.ship.grace_timer = max(p.ship.grace_timer, 1.0)

        extra = settings.get("difficulty.extra_rocks_per_level") * (self.level - 1)
        self.target_rocks = int(round((settings.get("rocks.count") + extra) * self.world_scale))
        for _ in range(self.target_rocks):
            self._spawn_rock(random.choice((3, 3, 2)))
        boss = self._spawn_aliens()
        self._spawn_hazards()
        self._setup_objective(boss)

        self.powerup_timer = self._powerup_interval()
        self.wormhole_timer = self._next_wormhole_delay()
        self.respawn_timer = settings.get("rocks.respawn_time")
        self.banner_timer = 2.5
        self.banner_text = f"LEVEL {self.level}"
        if boss:
            self.banner_sub = "MOTHERSHIP DETECTED - destroy it to open a wormhole"
        elif self.objective["type"] != "none":
            self.banner_sub = self.objective_text()
        elif self.level == 1:
            self.banner_sub = ("UP/DOWN speed   LEFT/RIGHT turn   SPACE fire   SHIFT ability   "
                               "1-9 weapons")
        else:
            self.banner_sub = f"Play area x{self.world_scale:.2f}"

    def _powerup_interval(self):
        return settings.get("timing.powerup_interval") / self.world_scale

    def _next_wormhole_delay(self):
        lo = settings.get("timing.wormhole_min_delay")
        hi = max(lo, settings.get("timing.wormhole_max_delay"))
        return random.uniform(lo, hi)

    def _speed_factor(self):
        return 1.0 + settings.get("difficulty.speed_per_level") * (self.level - 1)

    def _gravity_factor(self):
        return 1.0 + settings.get("difficulty.gravity_per_level") * (self.level - 1)

    def _max_rocks(self):
        return int(settings.get("rocks.max_rocks") * self.world_scale)

    # ------------------------------------------------------------ spawning
    def _far_pos(self, distance):
        ships = [p.ship for p in self.players]
        for _ in range(50):
            x, y = self.world.random_pos()
            if all(math.hypot(*self.world.delta(s.center_x, s.center_y, x, y)) > distance
                   for s in ships):
                break
        return x, y

    def _spawn_rock(self, size_class):
        speed = random.uniform(settings.get("rocks.min_speed"),
                               settings.get("rocks.max_speed")) * self._speed_factor()
        if size_class == 1:
            speed *= 1.3
        sx, sy = random.choice((-1, 1)), random.choice((-1, 1))
        x, y = self._far_pos(260)
        self.rock_list.append(Rock(size_class, x, y, sx * speed * DIAG, sy * speed * DIAG,
                                   self._pick_rock_kind()))

    def _spawn_aliens(self):
        """Populate the level. Returns True if a boss was spawned."""
        a = settings.get("aliens")
        kinds = EXPEDITION_ALIENS if self.expedition else CLASSIC_ALIENS
        for kind in kinds:
            cfg = a[kind]
            if not cfg.get("enabled") or self.level < cfg["min_level"]:
                continue
            count = max(1, round((1 + (self.level - cfg["min_level"]) // 3) * self.world_scale))
            for _ in range(count):
                x, y = self._far_pos(350)
                if kind == "swarm":
                    size = max(1, int(cfg["group_size"]))
                    phase = random.uniform(0, 360)
                    for slot in range(size):
                        self.alien_list.append(Swarm(x, y, self.level, slot, size, phase))
                else:
                    self.alien_list.append(ALIEN_CLASSES[kind](x, y, self.level))
            self._sfx(f"{kind}_spawn")
        boss_cfg = a["mothership"]
        if (boss_cfg.get("enabled") and self.level >= boss_cfg["min_level"]
                and self.level % max(1, int(boss_cfg["boss_every"])) == 0):
            x, y = self._far_pos(450)
            self.alien_list.append(ALIEN_CLASSES["mothership"](x, y, self.level))
            self._sfx("mothership_spawn")
            return True
        return False

    def spawn_minion(self, boss):
        if sum(1 for al in self.alien_list if al.minion) >= 6:
            return
        minion = Chaser(boss.center_x, boss.center_y, self.level,
                        overrides={"health": 10, "score": 0, "speed": 200})
        minion.minion = True
        self.alien_list.append(minion)
        self._sfx("chaser_spawn")

    def fire_alien_bullet(self, alien, bearing, play_sound=True):
        c = alien.cfg
        rad = math.radians(bearing)
        dx, dy = math.sin(rad), math.cos(rad)
        speed = float(c["bullet_speed"])
        start = alien.hit_radius + 8
        self.bullet_list.append(Bullet(
            "alien_bullet", "alien", alien.center_x + dx * start, alien.center_y + dy * start,
            dx * speed, dy * speed, c["bullet_damage"], 3.0))
        if play_sound:
            self._sfx(f"{alien.kind}_fire")

    def _spawn_powerup(self, x=None, y=None, kind=None):
        if x is None:
            if sum(1 for p in self.powerup_list if not p.permanent) >= 3 + int(self.world_scale):
                return
            x, y = self.world.random_pos()
        self.powerup_list.append(PowerUp(kind or random.choice(POWERUP_KINDS), x, y))

    def _spawn_wormhole(self):
        x, y = self._far_pos(250)
        self.wormhole = Wormhole(x, y, math.sqrt(self.world_scale))
        self.wormhole_list.append(self.wormhole)

    def _add_effect(self, x, y, radius, dur=0.5, color=(255, 190, 80)):
        self.effects.append([x, y, radius, 0.0, dur, color])
        if self.remote:
            self.new_effects.append([round(x, 1), round(y, 1), round(radius, 1), dur, list(color)])

    # ------------------------------------------------------------ update
    def on_show_view(self):
        self.window.background_color = BACKGROUND_COLOR
        if self.state != "gameover":
            self.audio.play_music()

    def on_hide_view(self):
        self.audio.stop_music()
        self._bank()
        if self.server:
            self.server.stop()
            self.server = None

    def on_update(self, delta_time):
        dt = min(delta_time, 1 / 20)
        self._network_tick(dt)
        self.zoom += (self.zoom_target - self.zoom) * min(1.0, dt * settings.get("world.zoom_speed"))
        self.background.update(dt)
        for e in self.effects:
            e[3] += dt
        self.effects = [e for e in self.effects if e[3] < e[4]]
        self.notice_timer = max(0.0, self.notice_timer - dt)
        if self.state == "perk":
            self._update_perks(dt)
            return
        if self.state != "playing":
            return
        self.time += dt
        self.banner_timer = max(0.0, self.banner_timer - dt)

        self._update_hazards(dt)
        for p in self.alive_players():
            p.score += dt * 10
            p.weapons.update(dt)
            ship = p.ship
            ax, ay = self._gravity_on(ship)
            keys = p.keys
            pressed = any(k in keys for k in ABILITY_KEYS)
            if pressed and not p.ability_prev:
                self._try_ability(p)
            p.ability_prev = pressed
            up = arcade.key.UP in keys
            ship.update_ship(dt, up, arcade.key.DOWN in keys, arcade.key.LEFT in keys,
                             arcade.key.RIGHT in keys, ax, ay, self.world)
            self._heal_tick(p, dt)
            p.thrust_cooldown -= dt
            if up and ship.speed > 0 and p.thrust_cooldown <= 0 and p.local:
                self.audio.play("thrust")
                p.thrust_cooldown = 0.3
            if arcade.key.SPACE in keys and not ship.phased:
                bullets, event = p.weapons.fire(ship, p.dmg_mult)
                for b in bullets:
                    b.player_id = p.id
                    self.bullet_list.append(b)
                if bullets and ship.cloaked and not bullets[0].silent:
                    ship.active = 0.0                  # firing gives away a cloaked ship
                if event:
                    self._sfx(event, p.id)

        for rock in self.rock_list:
            rock.update_rock(dt, self.world)
        for alien in list(self.alien_list):
            alien.update_alien(dt, self)
        aliens, rocks = list(self.alien_list), list(self.rock_list)
        for b in list(self.bullet_list):
            b.update_bullet(dt, self.world, aliens, rocks)
            if b.kind != "mine" and b.life <= 0:
                b.remove_from_sprite_lists()

        self._rock_rock_collisions()
        self._ship_rock_collisions()
        self._bullet_collisions()
        self._alien_collisions()
        self._update_powerups(dt)
        self._update_objective(dt)
        self._update_wormhole(dt)
        self._update_respawns(dt)

    def _gravity_on(self, ship):
        g = settings.get("physics.gravity") * self._gravity_factor()
        soft = settings.get("physics.softening")
        cap = settings.get("physics.max_accel")
        ax = ay = 0.0
        for rock in self.rock_list:
            dx, dy = self.world.delta(ship.center_x, ship.center_y, rock.center_x, rock.center_y)
            dax, day = gravity_accel(dx, dy, rock.mass, g, soft, cap)
            ax += dax
            ay += day
        return ax, ay

    # ---- damage helpers
    def _award(self, pid, points):
        for p in self.players:
            if p.id == pid:
                p.score += points

    def _break_rock(self, rock, pid=None, depth=0):
        """Remove a rock, replacing it with smaller ones if there is room. Gold pays credits,
        explosive rocks blow up."""
        kids = []
        if len(self.rock_list) + 1 <= self._max_rocks():
            kids = rock.split()
        rock.remove_from_sprite_lists()
        for kid in kids:
            self.rock_list.append(kid)
        self._sfx("split")
        if pid:
            c = settings.get("credits")
            self._earn(pid, c["rock_per_size"] * rock.size_class
                       + (c["gold_rock"] * rock.size_class if rock.kind == "gold" else 0))
        if rock.kind == "explosive":
            self._rock_explosion(rock.center_x, rock.center_y, 80 + 25 * rock.size_class, pid, depth)
        return kids

    def _damage_player(self, p, amount, from_x, from_y):
        ship = p.ship
        if not p.alive or ship.phased or ship.shield_timer > 0 or ship.grace_timer > 0:
            return False
        ship.since_hit = 0.0
        if ship.cloaked:
            ship.active = 0.0
        dx, dy = self.world.delta(from_x, from_y, ship.center_x, ship.center_y)
        d = math.hypot(dx, dy)
        if ship.shield_max > 0 and ship.shield_hp > 0:      # rechargeable shield soaks it up
            absorbed = min(ship.shield_hp, amount)
            ship.shield_hp -= absorbed
            amount -= absorbed
            ship.shield_wait = ship.shield_delay
            self._sfx("shield_hit", p.id)
            if amount <= 0.01:
                ship.grace_timer = 0.4
                return True
        ship.health -= amount
        ship.grace_timer = settings.get("ship.grace_time")
        if d > 0:                                   # knock the ship away
            ship.drift_x += dx / d * 220
            ship.drift_y += dy / d * 220
        self._sfx("crash", p.id)
        if ship.health <= 0:
            ship.health = 0
            p.alive = False
            ship.remove_from_sprite_lists()
            self._add_effect(ship.center_x, ship.center_y, 90, 0.8, (255, 120, 60))
            if not self.alive_players():
                self._game_over()
        return True

    def _game_over(self):
        self.state = "gameover"
        self.audio.stop_music()
        self._bank()

    def _hit_alien(self, alien, damage, pid=None):
        alien.take_damage(damage)
        if alien.health <= 0:
            self._kill_alien(alien, pid)

    def _kill_alien(self, alien, pid=None, score=True):
        if not alien.sprite_lists:
            return
        alien.remove_from_sprite_lists()
        if score and pid:
            self._award(pid, alien.cfg.get("score", 0))
            self._earn(pid, alien.cfg.get("score", 0) * settings.get("credits.alien_factor"))
        big = alien.kind == "mothership"
        self._add_effect(alien.center_x, alien.center_y, alien.hit_radius * (4 if big else 2.5),
                         0.9 if big else 0.5, (255, 120, 60) if big else (255, 200, 90))
        self._sfx(f"{alien.kind}_die")
        if not alien.minion:
            drops = 2 if big else (1 if random.random() < settings.get("difficulty.alien_drop_chance") else 0)
            for i in range(drops):
                self._spawn_powerup(alien.center_x + i * 40, alien.center_y)

    def _explode(self, x, y, radius, damage, pid):
        self._add_effect(x, y, radius, 0.6, (255, 150, 60))
        self._sfx("explosion")
        for alien in list(self.alien_list):
            dx, dy = self.world.delta(x, y, alien.center_x, alien.center_y)
            if math.hypot(dx, dy) < radius + alien.hit_radius:
                self._hit_alien(alien, damage, pid)
        for rock in list(self.rock_list):
            dx, dy = self.world.delta(x, y, rock.center_x, rock.center_y)
            if rock.sprite_lists and math.hypot(dx, dy) < radius + rock.hit_radius:
                self._award(pid, 10 * rock.size_class)
                self._break_rock(rock, pid)

    # ---- collisions
    def _overlap(self, a, b):
        dx, dy = self.world.delta(a.center_x, a.center_y, b.center_x, b.center_y)
        return math.hypot(dx, dy) < a.hit_radius + b.hit_radius

    def _rock_rock_collisions(self):
        rocks = list(self.rock_list)
        split_mode = bool(settings.get("rocks.split_on_rock_hit"))
        dead = set()
        for i, a in enumerate(rocks):
            if id(a) in dead or not a.sprite_lists:
                continue
            for b in rocks[i + 1:]:
                if id(b) in dead or not b.sprite_lists:
                    continue
                dx, dy = self.world.delta(a.center_x, a.center_y, b.center_x, b.center_y)
                dist = math.hypot(dx, dy)
                if dist == 0 or dist >= a.hit_radius + b.hit_radius:
                    continue
                nx, ny = dx / dist, dy / dist
                rel = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                if rel >= 0:          # already moving apart
                    continue
                if split_mode:
                    if a.cooldown > 0 or b.cooldown > 0:
                        continue
                    dead.update((id(a), id(b)))
                    self._break_rock(a)
                    self._break_rock(b)
                    break
                impulse = 2 * rel / (a.mass + b.mass)       # elastic bounce
                a.vx += impulse * b.mass * nx
                a.vy += impulse * b.mass * ny
                b.vx -= impulse * a.mass * nx
                b.vy -= impulse * a.mass * ny

    def _ship_rock_collisions(self):
        for p in self.alive_players():
            ship = p.ship
            if ship.phased:
                continue
            for rock in list(self.rock_list):
                if rock.cooldown > 0 or not rock.sprite_lists or not self._overlap(ship, rock):
                    continue
                if ship.shield_timer > 0 or ship.deflecting:       # ram / deflect
                    self._award(p.id, 25)
                    self._break_rock(rock, p.id)
                elif self._damage_player(p, settings.get("ship.hit_damage"),
                                         rock.center_x, rock.center_y):
                    self._break_rock(rock, p.id)
                if not p.alive:
                    break

    def _alien_bullet_hit(self, b):
        """An alien bullet or mine: ships (deflect / damage) and the escorted freighter."""
        if b.kind == "mine":
            near = any(not p.ship.phased and self._ship_dist(p.ship, b) < b.blast * 0.45 + p.ship.hit_radius
                       for p in self.alive_players())
            if b.fuse > 0 and not (b.arm <= 0 and near):
                return
            b.remove_from_sprite_lists()
            self._add_effect(b.center_x, b.center_y, b.blast, 0.5, (255, 90, 90))
            self._sfx("mine_blast")
            for p in self.alive_players():
                if self._ship_dist(p.ship, b) < b.blast + p.ship.hit_radius:
                    self._damage_player(p, b.damage, b.center_x, b.center_y)
            return
        for p in self.alive_players():
            ship = p.ship
            if ship.phased or not self._overlap(b, ship):
                continue
            if ship.deflecting:                       # throw it back
                b.owner, b.player_id = "player", p.id
                b.vx, b.vy = -b.vx * 1.2, -b.vy * 1.2
                b.life = 3.0
                b.damage *= 2
                self._add_effect(b.center_x, b.center_y, 30, 0.3, (255, 255, 255))
                return
            b.remove_from_sprite_lists()
            self._damage_player(p, b.damage, b.center_x, b.center_y)
            return
        fr = self.freighter
        if fr and self._overlap(b, fr):
            b.remove_from_sprite_lists()
            fr.health -= b.damage

    def _ship_dist(self, ship, other):
        dx, dy = self.world.delta(ship.center_x, ship.center_y, other.center_x, other.center_y)
        return math.hypot(dx, dy)

    def _bullet_collisions(self):
        for b in list(self.bullet_list):
            if not b.sprite_lists:
                continue
            if b.owner == "alien":
                self._alien_bullet_hit(b)
                continue
            pid = b.player_id
            if b.kind == "mine":
                if b.fuse <= 0 or (b.arm <= 0 and self._mine_triggered(b)):
                    b.remove_from_sprite_lists()
                    self._explode(b.center_x, b.center_y, b.blast, b.damage, pid)
                continue
            if b.heal > 0:                                # repair dart: heals a teammate
                for q in self.alive_players():
                    if q.id != pid and not q.ship.phased and self._overlap(b, q.ship):
                        q.ship.health = min(q.ship.max_health, q.ship.health + b.heal)
                        self._add_effect(q.ship.center_x, q.ship.center_y, 60, 0.4, (120, 255, 160))
                        b.remove_from_sprite_lists()
                        break
                if not b.sprite_lists:
                    continue
            for alien in list(self.alien_list):
                if b.pierce <= 0:
                    break
                if id(alien) in b.hit_ids or not alien.sprite_lists or not self._overlap(b, alien):
                    continue
                b.hit_ids.add(id(alien))
                b.pierce -= 1
                self._hit_alien(alien, b.damage, pid)
            for rock in list(self.rock_list):
                if b.pierce <= 0:
                    break
                if id(rock) in b.hit_ids or not rock.sprite_lists or not self._overlap(b, rock):
                    continue
                b.hit_ids.add(id(rock))
                b.pierce -= 1
                if rock.hp > 1:                          # armoured rock: needs several hits
                    rock.hp -= 1
                    self._add_effect(rock.center_x, rock.center_y, 30, 0.25, (220, 220, 240))
                    continue
                self._award(pid, 10 * rock.size_class)
                for kid in self._break_rock(rock, pid):
                    b.hit_ids.add(id(kid))
            if b.pierce <= 0:
                b.remove_from_sprite_lists()

    def _mine_triggered(self, mine):
        trigger = mine.blast * 0.45
        for target in list(self.alien_list) + list(self.rock_list):
            dx, dy = self.world.delta(mine.center_x, mine.center_y, target.center_x, target.center_y)
            if math.hypot(dx, dy) < trigger + target.hit_radius:
                return True
        return False

    def _alien_collisions(self):
        for alien in list(self.alien_list):
            if not alien.sprite_lists:
                continue
            for p in self.alive_players():
                if p.ship.phased or not self._overlap(alien, p.ship):
                    continue
                if p.ship.shield_timer > 0:
                    self._hit_alien(alien, 60, p.id)
                elif alien.ram_cd <= 0 and self._damage_player(
                        p, alien.cfg["contact_damage"], alien.center_x, alien.center_y):
                    alien.ram_cd = 1.0
                    if alien.cfg.get("dies_on_ram"):
                        self._kill_alien(alien, score=False)
                if not alien.sprite_lists:
                    break
            if not alien.sprite_lists:
                continue
            for rock in list(self.rock_list):
                if rock.cooldown <= 0 and rock.sprite_lists and self._overlap(alien, rock):
                    self._break_rock(rock)
                    alien.take_damage(settings.get("rocks.alien_damage"))
                    if alien.health <= 0:
                        self._kill_alien(alien, score=False)
                        break

    # ---- pickups, wormholes, rock respawn
    def _update_powerups(self, dt):
        self.powerup_timer -= dt
        if self.powerup_timer <= 0:
            self._spawn_powerup()
            self.powerup_timer = self._powerup_interval() * random.uniform(0.8, 1.2)
        for pu in list(self.powerup_list):
            pu.update_powerup(dt, self.world)
            if pu.expired:
                pu.remove_from_sprite_lists()
                continue
            for p in self.alive_players():
                ship = p.ship
                if ship.phased:
                    continue
                dx, dy = self.world.delta(pu.center_x, pu.center_y, ship.center_x, ship.center_y)
                d = math.hypot(dx, dy)
                if p.magnet > 0 and 0 < d < p.magnet:       # Tractor Field perk
                    pu.center_x += dx / d * 260 * dt
                    pu.center_y += dy / d * 260 * dt
                if d < pu.hit_radius + ship.hit_radius:
                    self._collect(pu, p)
                    break

    def _collect(self, pu, p):
        if pu.kind in ("crystal", "pod"):
            self._objective_item(pu, p)
            return
        ship = p.ship
        if pu.kind == "health":
            ship.health = min(ship.max_health, ship.health + settings.get("ship.health_gain"))
        elif pu.kind == "speed":
            ship.boost_timer = settings.get("timing.speed_boost_time")
        elif pu.kind == "ammo":
            p.weapons.add_ammo()
        else:
            ship.shield_timer = settings.get("timing.invincible_time")
        p.score += 50
        self._earn(p.id, settings.get("credits.powerup"))
        self._sfx("powerup", p.id)
        pu.remove_from_sprite_lists()

    def _boss_alive(self):
        return any(a.kind == "mothership" for a in self.alien_list)

    def _update_wormhole(self, dt):
        wh = self.wormhole
        if wh is None:
            if self._boss_alive() or not self.objective["done"]:   # finish the objective first
                return
            self.wormhole_timer -= dt
            if self.wormhole_timer <= 0:
                self._spawn_wormhole()
            return
        wh.update_wormhole(dt)
        if wh.expired:
            wh.remove_from_sprite_lists()
            self.wormhole = None
            self.wormhole_timer = self._next_wormhole_delay()
        elif wh.can_enter:
            for p in self.alive_players():    # either player entering takes both through
                dx, dy = self.world.delta(wh.center_x, wh.center_y,
                                          p.ship.center_x, p.ship.center_y)
                if math.hypot(dx, dy) < wh.full_radius:
                    self._complete_level()
                    return

    def _complete_level(self):
        self._sfx("wormhole")
        for p in self.players:
            p.score += 200 * self.level
            self._earn(p.id, settings.get("credits.level_clear") * self.level)
        self.level += 1
        self._bank()
        self._start_level()
        if self.expedition:
            self._begin_perks()

    def _update_respawns(self, dt):
        if len(self.rock_list) < self.target_rocks:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self._spawn_rock(3)
                self.respawn_timer = settings.get("rocks.respawn_time")

    # ------------------------------------------------------------ drawing
    def on_draw(self):
        self.clear()
        cx, cy = self.world.center
        self.world_camera.position = (cx, cy)
        self.world_camera.zoom = self.zoom
        self.world_camera.use()
        self.background.draw()
        draw_hazards(self.hazard_rows(), self.time)
        self.wormhole_list.draw()
        self.powerup_list.draw()
        self.rock_list.draw()
        self.freighter_list.draw()
        self.alien_list.draw()
        self.bullet_list.draw()
        self.ship_list.draw()
        line = draw_effects(self.effects, self.zoom)
        for p in self.alive_players():
            draw_ship_effects(p.ship.center_x, p.ship.center_y, p.ship.hit_radius,
                              self.ship_flags(p.ship), p.ship.ability.get("range", 300), line)
        for b in self.bullet_list:
            if b.kind == "mine" and b.blast and b.arm <= 0:   # faint trigger zone
                arcade.draw_circle_outline(b.center_x, b.center_y, b.blast * 0.45,
                                           (255, 90, 90, 60), line * 0.6)
        for al in self.alien_list:
            if al.health < al.max_health:
                w = max(30.0, al.hit_radius * 2)
                x, y = al.center_x - w / 2, al.center_y + al.hit_radius + 8
                arcade.draw_lbwh_rectangle_filled(x, y, w, 5, (60, 20, 20, 255))
                arcade.draw_lbwh_rectangle_filled(x, y, w * max(0, al.health / al.max_health), 5, RED)
        fr = self.freighter
        if fr:
            w = 70
            arcade.draw_lbwh_rectangle_filled(fr.center_x - w / 2, fr.center_y + fr.hit_radius + 10, w, 6,
                                              (20, 60, 30, 255))
            arcade.draw_lbwh_rectangle_filled(fr.center_x - w / 2, fr.center_y + fr.hit_radius + 10,
                                              w * max(0, fr.health / fr.max_health), 6, (90, 230, 120, 255))
        self.gui_camera.use()
        draw_hud(self.text, self._hud_for(self.local))

    # ------------------------------------------------------------ input
    def on_key_press(self, symbol, modifiers):
        if self.state == "gameover":
            if symbol == arcade.key.ENTER:
                self._bank()
                self.new_game()
                self.audio.play_music()
            elif symbol == arcade.key.ESCAPE:
                self._to_menu()
            return
        if symbol == arcade.key.ESCAPE:
            self._to_menu()
            return
        if self.state == "perk":
            if symbol in WEAPON_KEYS and WEAPON_KEYS[symbol] <= 3:
                self._pick_perk(self.local, WEAPON_KEYS[symbol])
            return
        if symbol == arcade.key.P:
            if self.remote:
                self.notice, self.notice_timer = "Can't pause while another player is connected", 2.0
            else:
                self.state = "paused" if self.state == "playing" else "playing"
        elif symbol in WEAPON_KEYS:
            self._select_weapon(WEAPON_KEYS[symbol])
        else:
            self.keys.add(symbol)

    def _select_weapon(self, slot):
        c = self.local.weapons.cfg(slot)
        if not c.get("enabled"):
            return
        if self.local.weapons.select(slot, self.level):
            self.audio.play("weapon_switch")
        elif not self.local.weapons.unlocked(slot, self.level):
            self.notice = f"{c['name']} unlocks at level {c['unlock_level']}"
            self.notice_timer = 2.0

    def on_key_release(self, symbol, modifiers):
        self.keys.discard(symbol)

    def _to_menu(self):
        from .menu_view import MenuView
        self.window.show_view(MenuView())
