"""Settings store. Everything the editor changes lives here and in config.json."""
import copy
import json

from .constants import CONFIG_PATH


def _sprite(file, frame_w, frame_h, frames, fps, scale=1.0):
    return {"file": file, "frame_w": frame_w, "frame_h": frame_h,
            "frames": frames, "fps": fps, "scale": scale}


def _weapon(name, kind, damage, speed, cooldown, rng, ammo, ammo_pack, unlock,
            count=1, spread=0.0, pierce=1, turn_rate=0.0, blast=0.0, fuse=0.0,
            enabled=True, sound="fire_w1", graphic="", silent=False, heal=0):
    """kind: bolt (straight shot), homing (steers to a target), mine (stays put, explodes)
    or pulse (instant blast around the ship)."""
    return {"enabled": enabled, "name": name, "type": kind, "unlock_level": unlock,
            "damage": damage, "speed": speed, "cooldown": cooldown, "range": rng,
            "ammo": ammo, "ammo_pack": ammo_pack, "count": count, "spread": spread,
            "pierce": pierce, "turn_rate": turn_rate, "blast_radius": blast,
            "fuse": fuse, "sound": sound, "graphic": graphic, "silent": silent, "heal": heal}


def _ship(name, price, desc, graphic, health, speed, accel, turn,
          ability=None, passive=None, weapon=None):
    """A flyable ship. ability: one special move on the ability key (SHIFT);
    passive: always-on traits (shield bar, regeneration); weapon: the ship's own weapon (key 7)."""
    return {"name": name, "price": price, "desc": desc, "graphic": graphic,
            "health": health, "speed_mult": speed, "accel_mult": accel, "turn_mult": turn,
            "ability": ability or {}, "passive": passive or {}, "weapon": weapon or {}}


def _alien(**kw):
    base = {"enabled": True, "health": 30, "speed": 100, "contact_damage": 15,
            "score": 100, "min_level": 1}
    base.update(kw)
    return base


DEFAULTS = {
    # Every image is a "tile sequence": a sheet cut into frame_w x frame_h tiles,
    # read left-to-right, top-to-bottom, and played at `fps` (0 = static).
    "graphics": {
        "ship": _sprite("ship_sheet.png", 64, 64, 4, 12, 1.0),
        "rock": _sprite("rock_sheet.png", 64, 64, 4, 3, 1.0),
        "wormhole": _sprite("wormhole_sheet.png", 128, 128, 8, 12, 1.2),
        "background": _sprite("background_tiles.png", 256, 256, 4, 0, 1.0),
        "powerup_speed": _sprite("powerup_speed.png", 32, 32, 1, 0, 1.0),
        "powerup_health": _sprite("powerup_health.png", 32, 32, 1, 0, 1.0),
        "powerup_shield": _sprite("powerup_shield.png", 32, 32, 1, 0, 1.0),
        "powerup_ammo": _sprite("powerup_ammo.png", 32, 32, 1, 0, 1.0),
        "bullet_w1": _sprite("bullet_w1.png", 12, 28, 1, 0, 1.0),
        "bullet_w2": _sprite("bullet_w2.png", 12, 20, 1, 0, 1.0),
        "bullet_w3": _sprite("bullet_w3.png", 8, 16, 1, 0, 1.0),
        "bullet_w4": _sprite("bullet_w4.png", 16, 32, 2, 10, 1.0),
        "bullet_w5": _sprite("bullet_w5.png", 8, 48, 1, 0, 1.0),
        "bullet_w6": _sprite("bullet_w6.png", 32, 32, 2, 3, 1.0),
        "bullet_w7": _sprite("bullet_w1.png", 12, 28, 1, 0, 1.0),
        "bullet_w8": _sprite("bullet_w1.png", 12, 28, 1, 0, 1.0),
        "bullet_w9": _sprite("bullet_w1.png", 12, 28, 1, 0, 1.0),
        "alien_drifter": _sprite("alien_drifter.png", 64, 64, 4, 6, 0.9),
        "alien_chaser": _sprite("alien_chaser.png", 64, 64, 4, 12, 0.8),
        "alien_sniper": _sprite("alien_sniper.png", 64, 64, 4, 6, 0.9),
        "alien_swarm": _sprite("alien_swarm.png", 64, 64, 4, 10, 0.6),
        "alien_mothership": _sprite("alien_mothership.png", 128, 128, 4, 4, 1.6),
        "alien_bullet": _sprite("alien_bullet.png", 16, 16, 2, 8, 1.0),
        "alien_seeker": _sprite("alien_seeker.png", 64, 64, 4, 8, 0.9),
        "alien_teleporter": _sprite("alien_teleporter.png", 64, 64, 4, 8, 0.9),
        "alien_minelayer": _sprite("alien_minelayer.png", 64, 64, 4, 5, 1.0),
        "alien_mine": _sprite("alien_mine.png", 32, 32, 2, 3, 0.8),
        "ship_phantom": _sprite("ship_phantom.png", 64, 64, 4, 12, 1.0),
        "ship_skipper": _sprite("ship_skipper.png", 64, 64, 4, 12, 1.0),
        "ship_specter": _sprite("ship_specter.png", 64, 64, 4, 12, 1.0),
        "ship_bulwark": _sprite("ship_bulwark.png", 64, 64, 4, 10, 1.1),
        "ship_medic": _sprite("ship_medic.png", 64, 64, 4, 12, 1.0),
        "bullet_phantom": _sprite("bullet_phantom.png", 6, 40, 1, 0, 1.0),
        "bullet_skipper": _sprite("bullet_skipper.png", 32, 32, 1, 0, 1.0),
        "bullet_specter": _sprite("bullet_specter.png", 10, 56, 1, 0, 1.0),
        "bullet_bulwark": _sprite("bullet_bulwark.png", 10, 10, 1, 0, 1.0),
        "bullet_medic": _sprite("bullet_medic.png", 16, 16, 1, 0, 1.0),
        "objective_crystal": _sprite("objective_crystal.png", 32, 32, 2, 3, 1.0),
        "objective_pod": _sprite("objective_pod.png", 40, 40, 2, 2, 1.0),
        "objective_freighter": _sprite("objective_freighter.png", 96, 96, 1, 0, 1.2),
    },
    "physics": {
        "gravity": 600000.0,      # pull = gravity * rock_mass / distance^2
        "max_accel": 320.0,       # cap per rock (px/s^2)
        "softening": 50.0,        # avoids infinite pull at zero distance
        "drift_damping": 0.8,     # how quickly pulled drift fades (1/s)
    },
    "ship": {
        "max_speed": 420.0,
        "acceleration": 240.0,
        "turn_rate": 170.0,       # degrees per second
        "max_health": 100,
        "hit_damage": 25,
        "health_gain": 35,
        "grace_time": 1.5,        # brief invincibility after being hit
        "boost_multiplier": 1.6,
    },
    "rocks": {
        "count": 6,
        "min_speed": 50.0,
        "max_speed": 130.0,
        "split_angle": 35.0,
        "split_speed": 1.2,
        "split_on_rock_hit": True,
        "max_rocks": 40,          # scaled up with the world size
        "respawn_time": 6.0,
        "alien_damage": 15,       # damage an alien takes from hitting a rock
    },
    "timing": {
        "powerup_interval": 8.0,
        "powerup_lifetime": 10.0,
        "wormhole_min_delay": 6.0,
        "wormhole_max_delay": 14.0,
        "wormhole_lifetime": 7.0,
        "speed_boost_time": 6.0,
        "invincible_time": 6.0,
    },
    "difficulty": {
        "extra_rocks_per_level": 1,
        "speed_per_level": 0.08,
        "gravity_per_level": 0.10,
        "alien_health_per_level": 0.10,
        "alien_drop_chance": 0.30,
    },
    # The play area grows each level; the camera zooms out to keep it all in view.
    # classic = the original game; expedition adds smarter aliens, hazards, rock types,
    # objectives and between-level perks. Ships, abilities and credits work in both.
    "game": {"mode": "expedition"},
    "credits": {                # in-game currency only; saved in profile.json
        "start_credits": 700,
        "alien_factor": 0.2,    # credits = alien score * this
        "rock_per_size": 2,
        "gold_rock": 30,        # extra per size for gold ore rocks
        "powerup": 5,
        "crystal": 8,
        "rescue": 25,
        "level_clear": 20,      # x level
        "objective": 30,        # x level, for completing the objective
    },
    "rock_types": {             # chance weights and the level they start appearing
        "ice": {"min_level": 2, "weight": 14},
        "explosive": {"min_level": 3, "weight": 10},
        "gold": {"min_level": 2, "weight": 8},
        "metal": {"min_level": 4, "weight": 12},
    },
    "hazards": {
        "nebula_from": 2, "blackhole_from": 3, "ion_from": 4, "flare_from": 3,
        "blackhole_strength": 7_000_000.0, "flare_interval": 30.0, "flare_damage": 25,
        "cloak_detect": 140.0,  # aliens still notice a hidden ship this close
    },
    "objectives": {
        "enabled": True, "crystals_base": 4, "pods_base": 2, "escort_seconds": 35.0,
        "freighter_health": 150,
    },
    "ships": {
        "scout": _ship("Scout", 0, "Balanced starter ship.", "ship", 100, 1.0, 1.0, 1.0),
        "phantom": _ship(
            "Phantom", 600, "Stealth. Cloak hides you from aliens for a few seconds.",
            "ship_phantom", 80, 1.05, 1.0, 1.1,
            ability={"type": "cloak", "name": "Cloak", "cooldown": 12.0, "duration": 6.0,
                     "desc": "Invisible to aliens. Firing (except the Silent Bolt) or being hit breaks it."},
            weapon=_weapon("Silent Bolt", "bolt", 55, 1500, 1.1, 1600, -1, 0, 1,
                           silent=True, graphic="bullet_phantom", sound="fire_phantom")),
        "skipper": _ship(
            "Skipper", 800, "Hit-and-run. Hyperjump to a random safe spot on the map.",
            "ship_skipper", 90, 1.0, 1.15, 1.0,
            ability={"type": "hyperjump", "name": "Hyperjump", "cooldown": 8.0,
                     "desc": "Instantly jump to a random safe position with a moment of protection."},
            weapon=_weapon("Jump-blast", "pulse", 35, 0, 2.0, 0, -1, 0, 1, blast=170.0,
                           graphic="bullet_skipper", sound="fire_skipper")),
        "specter": _ship(
            "Specter", 1000, "Evasion. Hyperspace lets rocks and aliens pass straight through you.",
            "ship_specter", 85, 1.0, 1.0, 1.0,
            ability={"type": "hyperspace", "name": "Hyperspace", "cooldown": 14.0, "duration": 3.0,
                     "desc": "3 seconds immune to rocks, aliens and bullets - but you cannot fire or collect."},
            weapon=_weapon("Phase Lance", "bolt", 28, 1000, 0.7, 1200, -1, 0, 1, pierce=8,
                           graphic="bullet_specter", sound="fire_specter")),
        "bulwark": _ship(
            "Bulwark", 1200, "Tank. A rechargeable shield soaks up damage; Deflect throws shots back.",
            "ship_bulwark", 130, 0.85, 0.9, 0.85,
            ability={"type": "deflect", "name": "Deflect", "cooldown": 9.0, "duration": 1.6,
                     "desc": "Reflect alien bullets and shrug off rocks while active."},
            passive={"shield_max": 60.0, "shield_delay": 3.0, "shield_rate": 14.0},
            weapon=_weapon("Flak Cannon", "bolt", 7, 700, 0.8, 380, -1, 0, 1, count=7,
                           spread=36.0, graphic="bullet_bulwark", sound="fire_bulwark")),
        "medic": _ship(
            "Medic", 900, "Support. Heals itself over time and repairs your partner.",
            "ship_medic", 95, 0.95, 1.0, 1.0,
            ability={"type": "repair", "name": "Repair Burst", "cooldown": 12.0, "duration": 3.0,
                     "range": 360.0, "self_rate": 8.0, "ally_rate": 12.0,
                     "desc": "For 3 seconds heal yourself and any ally within range."},
            passive={"regen": 1.5, "regen_delay": 2.0},
            weapon=_weapon("Repair Dart", "bolt", 10, 800, 0.5, 700, -1, 0, 1, heal=15,
                           graphic="bullet_medic", sound="fire_medic")),
    },
    "net": {
        "player_name": "Pilot",
        "port": 5555,              # TCP (game) and UDP (discovery) - same number
        "last_ip": "192.168.1.2",
        "snapshot_rate": 30,       # world updates per second sent to the other player
        "timeout": 6.0,            # seconds of silence before a player is dropped
    },
    "world": {
        "growth_per_level": 0.25,
        "max_scale": 3.0,
        "zoom_speed": 1.5,
    },
    "weapons": {
        "w1": _weapon("Blaster", "bolt", 10, 700, 0.25, 900, -1, 0, 1),
        "w2": _weapon("Spread", "bolt", 8, 600, 0.5, 600, 30, 15, 1, count=3, spread=24.0),
        "w3": _weapon("Rapid", "bolt", 4, 800, 0.08, 700, 150, 75, 2),
        "w4": _weapon("Missile", "homing", 25, 420, 0.9, 1400, 8, 4, 3,
                      turn_rate=140.0, sound="fire_w4"),
        "w5": _weapon("Laser", "bolt", 15, 1100, 0.6, 1100, 20, 10, 4,
                      pierce=4, sound="fire_w5"),
        "w6": _weapon("Mine", "mine", 40, 0, 1.0, 0, 6, 3, 5,
                      blast=130.0, fuse=3.0, sound="fire_w6"),
        "w7": _weapon("Custom 7", "bolt", 10, 700, 0.25, 900, -1, 0, 1, enabled=False),
        "w8": _weapon("Custom 8", "bolt", 10, 700, 0.25, 900, -1, 0, 1, enabled=False),
        "w9": _weapon("Custom 9", "bolt", 10, 700, 0.25, 900, -1, 0, 1, enabled=False),
    },
    "aliens": {
        "drifter": {"enabled": True, "health": 20, "speed": 90, "contact_damage": 15,
                    "score": 50, "min_level": 1, "wave_amp": 80.0, "wave_freq": 1.2},
        "chaser": {"enabled": True, "health": 30, "speed": 170, "contact_damage": 25,
                   "score": 100, "min_level": 2, "turn_rate": 90.0, "dies_on_ram": True},
        "sniper": {"enabled": True, "health": 40, "speed": 120, "contact_damage": 15,
                   "score": 150, "min_level": 3, "fire_interval": 2.2, "bullet_speed": 520,
                   "bullet_damage": 15, "keep_distance": 380},
        "swarm": {"enabled": True, "health": 15, "speed": 170, "contact_damage": 10,
                  "score": 60, "min_level": 4, "fire_interval": 3.0, "bullet_speed": 400,
                  "bullet_damage": 8, "orbit_radius": 220, "orbit_speed": 60.0,
                  "group_size": 4},
        "seeker": _alien(health=35, speed=150, contact_damage=20, score=120, min_level=3,
                         fire_interval=3.0, bullet_speed=380, bullet_damage=10,
                         detect_range=900.0),
        "teleporter": _alien(health=30, speed=80, contact_damage=15, score=130, min_level=4,
                             blink_interval=4.0, burst_count=3, bullet_speed=450,
                             bullet_damage=10, ring=300.0),
        "minelayer": _alien(health=50, speed=100, contact_damage=15, score=140, min_level=5,
                            mine_interval=2.5, mine_damage=25, mine_blast=100.0),
        "mothership": {"enabled": True, "health": 400, "speed": 70, "contact_damage": 30,
                       "score": 1000, "min_level": 5, "boss_every": 5, "fire_interval": 1.6,
                       "bullet_speed": 380, "bullet_damage": 12, "keep_distance": 420,
                       "spawn_interval": 6.0, "ring_bullets": 12},
    },
    # Add any new event name here (or in config.json) and call audio.play("name").
    "audio": {
        "music_volume": 0.5,
        "sfx_volume": 0.7,
        "events": {
            "music": {"file": "music.wav", "volume": 1.0},
            "thrust": {"file": "thrust.wav", "volume": 0.5},
            "crash": {"file": "crash.wav", "volume": 1.0},
            "powerup": {"file": "powerup.wav", "volume": 1.0},
            "wormhole": {"file": "wormhole.wav", "volume": 1.0},
            "split": {"file": "split.wav", "volume": 0.8},
            "fire_w1": {"file": "fire_blaster.wav", "volume": 0.6},
            "fire_w2": {"file": "fire_spread.wav", "volume": 0.6},
            "fire_w3": {"file": "fire_rapid.wav", "volume": 0.5},
            "fire_w4": {"file": "fire_missile.wav", "volume": 0.7},
            "fire_w5": {"file": "fire_laser.wav", "volume": 0.6},
            "fire_w6": {"file": "fire_mine.wav", "volume": 0.7},
            "weapon_switch": {"file": "weapon_switch.wav", "volume": 0.6},
            "no_ammo": {"file": "no_ammo.wav", "volume": 0.6},
            "explosion": {"file": "explosion.wav", "volume": 1.0},
            "fire_phantom": {"file": "fire_phantom.wav", "volume": 0.5},
            "fire_skipper": {"file": "fire_skipper.wav", "volume": 0.7},
            "fire_specter": {"file": "fire_specter.wav", "volume": 0.6},
            "fire_bulwark": {"file": "fire_bulwark.wav", "volume": 0.7},
            "fire_medic": {"file": "fire_medic.wav", "volume": 0.5},
            "ability_cloak": {"file": "ability_cloak.wav", "volume": 0.7},
            "ability_hyperjump": {"file": "ability_hyperjump.wav", "volume": 0.8},
            "ability_hyperspace": {"file": "ability_hyperspace.wav", "volume": 0.8},
            "ability_deflect": {"file": "ability_deflect.wav", "volume": 0.7},
            "ability_repair": {"file": "ability_repair.wav", "volume": 0.7},
            "shield_hit": {"file": "shield_hit.wav", "volume": 0.7},
            "crystal": {"file": "crystal.wav", "volume": 0.6},
            "objective_done": {"file": "objective_done.wav", "volume": 0.9},
            "perk_pick": {"file": "perk_pick.wav", "volume": 0.8},
            "flare_warn": {"file": "flare_warn.wav", "volume": 0.7},
            "flare_hit": {"file": "flare_hit.wav", "volume": 0.9},
            "mine_blast": {"file": "mine_blast.wav", "volume": 0.8},
            "seeker_spawn": {"file": "seeker_spawn.wav", "volume": 0.6},
            "seeker_fire": {"file": "seeker_fire.wav", "volume": 0.5},
            "seeker_die": {"file": "seeker_die.wav", "volume": 0.8},
            "teleporter_spawn": {"file": "teleporter_spawn.wav", "volume": 0.6},
            "teleporter_blink": {"file": "teleporter_blink.wav", "volume": 0.6},
            "teleporter_fire": {"file": "teleporter_fire.wav", "volume": 0.5},
            "teleporter_die": {"file": "teleporter_die.wav", "volume": 0.8},
            "minelayer_spawn": {"file": "minelayer_spawn.wav", "volume": 0.6},
            "minelayer_drop": {"file": "minelayer_drop.wav", "volume": 0.5},
            "minelayer_die": {"file": "minelayer_die.wav", "volume": 0.8},
            "drifter_spawn": {"file": "drifter_spawn.wav", "volume": 0.6},
            "drifter_die": {"file": "drifter_die.wav", "volume": 0.8},
            "chaser_spawn": {"file": "chaser_spawn.wav", "volume": 0.6},
            "chaser_die": {"file": "chaser_die.wav", "volume": 0.8},
            "sniper_spawn": {"file": "sniper_spawn.wav", "volume": 0.6},
            "sniper_fire": {"file": "sniper_fire.wav", "volume": 0.6},
            "sniper_die": {"file": "sniper_die.wav", "volume": 0.8},
            "swarm_spawn": {"file": "swarm_spawn.wav", "volume": 0.6},
            "swarm_fire": {"file": "swarm_fire.wav", "volume": 0.4},
            "swarm_die": {"file": "swarm_die.wav", "volume": 0.7},
            "mothership_spawn": {"file": "mothership_spawn.wav", "volume": 1.0},
            "mothership_fire": {"file": "mothership_fire.wav", "volume": 0.7},
            "mothership_die": {"file": "mothership_die.wav", "volume": 1.0},
        },
    },
}


def _merge(base, new):
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value


class Config:
    def __init__(self, path=CONFIG_PATH):
        self.path = path
        self.data = copy.deepcopy(DEFAULTS)

    def load(self):
        if self.path.exists():
            try:
                _merge(self.data, json.loads(self.path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass  # a broken file falls back to defaults

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    @staticmethod
    def _walk(tree, dotted):
        node = tree
        for part in dotted.split("."):
            node = node[part]
        return node

    def get(self, dotted, default=None):
        try:
            return self._walk(self.data, dotted)
        except (KeyError, TypeError):
            return default

    def default(self, dotted):
        return self._walk(DEFAULTS, dotted)

    def set(self, dotted, value):
        *parents, last = dotted.split(".")
        node = self.data
        for part in parents:
            node = node[part]
        node[last] = value

    # The joiner plays by the host's gameplay rules for the length of a session.
    SYNCED = ("physics", "ship", "rocks", "timing", "difficulty", "world", "weapons", "aliens",
              "game", "ships", "rock_types", "hazards", "objectives", "credits")
    _backup = None

    def synced_sections(self):
        return {k: copy.deepcopy(self.data[k]) for k in self.SYNCED}

    def apply_overrides(self, sections):
        if self._backup is None:
            self._backup = {k: copy.deepcopy(self.data[k]) for k in self.SYNCED}
        for key, value in sections.items():
            if key in self.SYNCED:
                self.data[key] = copy.deepcopy(value)

    def restore(self):
        if self._backup is not None:
            self.data.update(self._backup)
            self._backup = None

    def reset(self, dotted):
        try:
            self.set(dotted, copy.deepcopy(self.default(dotted)))
        except KeyError:
            pass


settings = Config()
settings.load()
