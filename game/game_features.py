"""Gameplay systems added on top of the core loop: credits, rock types, hazards, objectives,
ship abilities and between-level perks. Mixed into GameView (which owns the world state)."""
import math
import random

from .config import settings
from .hazards import BlackHole, IonStorm, Nebula, SolarFlare
from .perks import PERKS, apply_perk
from .physics import gravity_accel
from .profile import profile
from .sprites import Freighter, PowerUp
from .weapons import Bullet

PERK_TIME = 20.0

# Ship flag bits (sent to the joiner so it can draw ability effects)
FLAG_POWER, FLAG_CLOAK, FLAG_PHASE, FLAG_HEAL, FLAG_DEFLECT, FLAG_BARRIER = 1, 2, 4, 8, 16, 32


class FeaturesMixin:
    @property
    def expedition(self):
        return settings.get("game.mode") == "expedition"

    # ------------------------------------------------------------ small helpers
    def effect_at(self, x, y, radius, color=(255, 190, 80)):
        self._add_effect(x, y, radius, 0.5, color)

    def play_sfx(self, name, who=None):
        self._sfx(name, who)

    def ship_flags(self, ship):
        flags = 0
        if ship.shield_timer > 0:
            flags |= FLAG_POWER
        if ship.cloaked:
            flags |= FLAG_CLOAK
        if ship.phased:
            flags |= FLAG_PHASE
        if ship.healing:
            flags |= FLAG_HEAL
        if ship.deflecting:
            flags |= FLAG_DEFLECT
        if ship.shield_max > 0 and ship.shield_hp > 1:
            flags |= FLAG_BARRIER
        return flags

    # ------------------------------------------------------------ credits
    def _earn(self, pid, amount):
        for p in self.players:
            if p.id == pid:
                p.credits_run += amount * p.credit_mult

    def _bank(self):
        """Move this machine's player's earned credits into the saved profile."""
        delta = int(self.local.credits_run) - self.banked
        if delta > 0:
            profile.credits += delta
            self.banked += delta
        profile.record(self.level, self.local.score)
        profile.save()

    # ------------------------------------------------------------ rock types
    def _pick_rock_kind(self):
        if not self.expedition:
            return "normal"
        pool = [("normal", 60)]
        for kind, c in settings.get("rock_types").items():
            if self.level >= c["min_level"] and c["weight"] > 0:
                pool.append((kind, c["weight"]))
        kinds, weights = zip(*pool)
        return random.choices(kinds, weights)[0]

    def _rock_explosion(self, x, y, radius, pid, depth=0):
        self._add_effect(x, y, radius, 0.5, (255, 110, 70))
        self._sfx("explosion")
        for p in self.alive_players():
            dx, dy = self.world.delta(x, y, p.ship.center_x, p.ship.center_y)
            if math.hypot(dx, dy) < radius + p.ship.hit_radius:
                self._damage_player(p, 20, x, y)
        for alien in list(self.alien_list):
            dx, dy = self.world.delta(x, y, alien.center_x, alien.center_y)
            if math.hypot(dx, dy) < radius + alien.hit_radius:
                self._hit_alien(alien, 25, pid)
        if depth < 4:
            for rock in list(self.rock_list):
                dx, dy = self.world.delta(x, y, rock.center_x, rock.center_y)
                if rock.sprite_lists and math.hypot(dx, dy) < radius + rock.hit_radius:
                    self._break_rock(rock, pid, depth + 1)

    # ------------------------------------------------------------ hazards
    def _spawn_hazards(self):
        self.hazards = []
        self.flare = None
        self.flare_timer = settings.get("hazards.flare_interval") * random.uniform(0.6, 1.0)
        if not self.expedition:
            return
        h, lv, ws = settings.get("hazards"), self.level, self.world_scale
        counts = (
            (Nebula, lv >= h["nebula_from"], 1 + (lv - h["nebula_from"]) // 3, 3),
            (BlackHole, lv >= h["blackhole_from"], 1 + (lv - h["blackhole_from"]) // 3, 2),
            (IonStorm, lv >= h["ion_from"], 1 + (lv - h["ion_from"]) // 3, 2),
        )
        for cls, ok, n, cap in counts:
            if ok:
                for _ in range(min(cap + int(ws) - 1, max(1, round(n * math.sqrt(ws))))):
                    x, y = self._far_pos(420)
                    self.hazards.append(cls(x, y))

    def _update_hazards(self, dt):
        for p in self.players:
            p.ship.in_nebula = False
            p.ship.jammed = False
        if not self.expedition:
            return
        cfg = settings.get("hazards")
        for hz in self.hazards:
            hz.update(dt, self.world)
            for p in self.alive_players():
                ship = p.ship
                dx, dy = self.world.delta(ship.center_x, ship.center_y, hz.x, hz.y)
                d = math.hypot(dx, dy)
                if hz.kind == "nebula":
                    if d < hz.radius:
                        ship.in_nebula = True
                elif hz.kind == "ion":
                    if d < hz.radius:
                        ship.jammed = True
                        if not ship.phased:
                            ship.drift_x += random.uniform(-1, 1) * 220 * dt
                            ship.drift_y += random.uniform(-1, 1) * 220 * dt
                elif hz.kind == "blackhole" and not ship.phased and d < hz.radius:
                    ax, ay = gravity_accel(dx, dy, 1.0, cfg["blackhole_strength"], 70.0, 420.0)
                    ship.drift_x += ax * dt
                    ship.drift_y += ay * dt
                    if d < hz.core + ship.hit_radius:
                        self._damage_player(p, 30, hz.x, hz.y)
            if hz.kind == "blackhole":
                for rock in list(self.rock_list):
                    dx, dy = self.world.delta(rock.center_x, rock.center_y, hz.x, hz.y)
                    d = math.hypot(dx, dy)
                    if d < hz.core:                        # swallowed
                        self._add_effect(rock.center_x, rock.center_y, 40, 0.4, (150, 100, 255))
                        rock.remove_from_sprite_lists()
                    elif d < hz.radius:
                        ax, ay = gravity_accel(dx, dy, 1.0, cfg["blackhole_strength"], 70.0, 300.0)
                        rock.vx += ax * dt
                        rock.vy += ay * dt
        self._update_flare(dt, cfg)

    def _update_flare(self, dt, cfg):
        if self.flare is None:
            if self.level >= cfg["flare_from"]:
                self.flare_timer -= dt
                if self.flare_timer <= 0:
                    self.flare = SolarFlare(self.world)
                    self.flare_timer = cfg["flare_interval"] * random.uniform(0.8, 1.2)
                    self._sfx("flare_warn")
            return
        f = self.flare
        f.t += dt
        if f.phase == 1 and not f.fired:
            f.fired = True
            self._flare_burst(f, cfg["flare_damage"])
        if f.finished:
            self.flare = None

    def _flare_burst(self, f, damage):
        self._sfx("flare_hit")
        for p in self.alive_players():
            if f.covers(self.world, p.ship.center_x, p.ship.center_y, p.ship.hit_radius):
                self._damage_player(p, damage, f.x, f.y)
        for alien in list(self.alien_list):
            if f.covers(self.world, alien.center_x, alien.center_y, alien.hit_radius):
                self._hit_alien(alien, 50)
        for rock in list(self.rock_list):
            if rock.sprite_lists and f.covers(self.world, rock.center_x, rock.center_y, rock.hit_radius):
                self._break_rock(rock)
        fr = self.freighter
        if fr and f.covers(self.world, fr.center_x, fr.center_y, fr.hit_radius):
            fr.health -= damage * 2

    def hazard_rows(self):
        rows = []
        for i, hz in enumerate(self.hazards):
            rows.append([i, hz.kind, round(hz.x, 1), round(hz.y, 1), round(hz.radius, 1),
                         round(hz.core, 1), 0, 0])
        f = self.flare
        if f:
            rows.append([99, "flare", round(f.x, 1), round(f.y, 1), round(f.w, 1), round(f.h, 1),
                         f.phase, round(f.t, 2)])
        return rows

    # ------------------------------------------------------------ objectives
    def _setup_objective(self, boss):
        self.freighter = None
        self.freighter_list.clear()
        obj = {"type": "none", "need": 0, "got": 0, "done": True, "ok": False,
               "time": 0.0, "total": 0.0}
        cfg = settings.get("objectives")
        if boss:
            obj.update(type="boss", done=False)
        elif self.expedition and cfg["enabled"] and self.level >= 2:
            kind = ("crystals", "rescue", "escort")[(self.level - 2) % 3]
            obj.update(type=kind, done=False)
            if kind == "crystals":
                obj["need"] = int(cfg["crystals_base"] + self.level // 2)
                for _ in range(obj["need"]):
                    x, y = self._far_pos(200)
                    self.powerup_list.append(PowerUp("crystal", x, y, permanent=True))
            elif kind == "rescue":
                obj["need"] = int(cfg["pods_base"] + self.level // 3)
                for _ in range(obj["need"]):
                    x, y = self._far_pos(250)
                    self.powerup_list.append(PowerUp(
                        "pod", x, y, permanent=True,
                        vx=random.uniform(-30, 30), vy=random.uniform(-30, 30)))
            else:
                obj["total"] = float(cfg["escort_seconds"])
                x, y = self._far_pos(300)
                self.freighter = Freighter(x, y)
                self.freighter_list.append(self.freighter)
        self.objective = obj

    def objective_text(self):
        o = self.objective
        if o["type"] == "none":
            return ""
        if o["type"] == "boss":
            return "OBJECTIVE: destroy the mothership" if not o["done"] else ""
        if o["done"]:
            return "OBJECTIVE COMPLETE" if o["ok"] else "OBJECTIVE FAILED - find the wormhole"
        if o["type"] == "crystals":
            return f"OBJECTIVE: collect crystals {o['got']}/{o['need']}"
        if o["type"] == "rescue":
            return f"OBJECTIVE: rescue stranded pods {o['got']}/{o['need']}"
        return f"OBJECTIVE: escort the freighter {int(o['time'])}/{int(o['total'])}s"

    def _objective_item(self, pu, p):
        o = self.objective
        o["got"] += 1
        self._earn(p.id, settings.get("credits.crystal" if pu.kind == "crystal" else "credits.rescue"))
        self._sfx("crystal", p.id)
        self._add_effect(pu.center_x, pu.center_y, 50, 0.4, (120, 230, 255))
        pu.remove_from_sprite_lists()
        if o["got"] >= o["need"] and not o["done"]:
            self._finish_objective(True)

    def _finish_objective(self, ok):
        o = self.objective
        o["done"], o["ok"] = True, ok
        if ok:
            for p in self.players:
                self._earn(p.id, settings.get("credits.objective") * self.level)
            self._sfx("objective_done")
            self.notice, self.notice_timer = "Objective complete! The wormhole is opening...", 3.0
        else:
            self.notice, self.notice_timer = "The freighter was lost - find the wormhole", 3.0
        self.wormhole_timer = min(self.wormhole_timer, 3.0)

    def _update_objective(self, dt):
        o = self.objective
        if o["type"] == "boss" and not o["done"] and not self._boss_alive():
            self._finish_objective(True)
        fr = self.freighter
        if o["type"] != "escort" or o["done"] or fr is None:
            return
        fr.update_freighter(dt, self.world)
        o["time"] += dt
        if fr.hit_cd <= 0:
            for rock in list(self.rock_list):
                if rock.cooldown <= 0 and rock.sprite_lists and self._overlap(fr, rock):
                    fr.health -= 25
                    fr.hit_cd = 0.8
                    self._break_rock(rock)
                    break
        if fr.health <= 0:
            self._add_effect(fr.center_x, fr.center_y, 120, 0.9, (255, 120, 60))
            fr.remove_from_sprite_lists()
            self.freighter = None
            self._finish_objective(False)
        elif o["time"] >= o["total"]:
            self._add_effect(fr.center_x, fr.center_y, 100, 0.8, (120, 255, 160))
            fr.remove_from_sprite_lists()
            self.freighter = None
            self._finish_objective(True)

    # ------------------------------------------------------------ abilities
    def _try_ability(self, p):
        ship = p.ship
        kind = ship.ability_type
        if not kind or ship.ability_cd > 0 or ship.jammed or ship.phased:
            if kind and ship.jammed:
                self.notice, self.notice_timer = "Ion storm - ability offline", 1.5
            return
        a = ship.ability
        if kind == "hyperjump":
            self._hyperjump(p)
        else:
            ship.active = float(a.get("duration", 3.0))
            self._add_effect(ship.center_x, ship.center_y, 70, 0.5, (150, 220, 255))
        ship.ability_cd = max(float(a["cooldown"]) * p.cd_mult, ship.active)
        self._sfx(f"ability_{kind}", p.id)

    def _hyperjump(self, p):
        ship = p.ship
        self._add_effect(ship.center_x, ship.center_y, 90, 0.5, (200, 160, 255))
        best = None
        for _ in range(60):
            x, y = self.world.random_pos()
            ok = True
            for rock in self.rock_list:
                dx, dy = self.world.delta(x, y, rock.center_x, rock.center_y)
                if math.hypot(dx, dy) < rock.hit_radius + 130:
                    ok = False
                    break
            if ok:
                for al in self.alien_list:
                    dx, dy = self.world.delta(x, y, al.center_x, al.center_y)
                    if math.hypot(dx, dy) < 220:
                        ok = False
                        break
            if ok:
                for hz in self.hazards:
                    if hz.kind == "blackhole":
                        dx, dy = self.world.delta(x, y, hz.x, hz.y)
                        if math.hypot(dx, dy) < hz.radius * 0.5:
                            ok = False
                            break
            best = (x, y)
            if ok:
                break
        ship.center_x, ship.center_y = best
        ship.drift_x = ship.drift_y = 0.0
        ship.grace_timer = max(ship.grace_timer, 1.0)
        self._add_effect(ship.center_x, ship.center_y, 90, 0.5, (200, 160, 255))

    def _heal_tick(self, p, dt):
        ship = p.ship
        if not ship.healing:
            return
        a = ship.ability
        ship.health = min(ship.max_health, ship.health + a.get("self_rate", 8.0) * dt)
        for q in self.alive_players():
            if q is p or q.ship.phased:
                continue
            dx, dy = self.world.delta(ship.center_x, ship.center_y, q.ship.center_x, q.ship.center_y)
            if math.hypot(dx, dy) < a.get("range", 360.0):
                q.ship.health = min(q.ship.max_health, q.ship.health + a.get("ally_rate", 12.0) * dt)

    def _hidden_from(self, alien, ship, dist):
        """Can this alien not see this ship right now?"""
        if not (ship.cloaked or ship.in_nebula):
            return False
        reach = alien.detect_range or settings.get("hazards.cloak_detect")
        return dist > reach

    # ------------------------------------------------------------ alien helpers
    def drop_alien_mine(self, alien):
        c = alien.cfg
        mines = [b for b in self.bullet_list if b.owner == "alien" and b.kind == "mine"]
        if len(mines) >= 25:
            mines[0].remove_from_sprite_lists()
        mine = Bullet("alien_mine", "alien", alien.center_x, alien.center_y, 0.0, 0.0,
                      c["mine_damage"], 999.0, kind="mine", blast=c["mine_blast"], fuse=14.0)
        mine.arm = 1.0
        self.bullet_list.append(mine)
        self._sfx("minelayer_drop")

    # ------------------------------------------------------------ perks
    def _begin_perks(self):
        self.state = "perk"
        self.perk_timer = PERK_TIME
        for p in self.players:
            p.perk_options = random.sample(list(PERKS), 3)
            p.perk_choice = 0
            p.last_pk = 0
            if p.local:
                self.keys.clear()          # do not carry held keys into the menu

    def _pick_perk(self, p, idx):
        if self.state != "perk" or p.perk_choice or not 1 <= idx <= 3:
            return
        p.perk_choice = idx
        apply_perk(p, p.perk_options[idx - 1])
        self._sfx("perk_pick", p.id)
        if all(q.perk_choice for q in self.players):
            self.state = "playing"
            self.banner_timer = 1.5

    def _update_perks(self, dt):
        self.perk_timer -= dt
        if self.perk_timer <= 0:
            for p in self.players:
                if not p.perk_choice:
                    self._pick_perk(p, random.randint(1, 3))

    def perk_hud(self, p):
        if self.state != "perk":
            return None
        return {"options": [list(PERKS[k]) for k in p.perk_options], "chosen": p.perk_choice,
                "left": round(max(0.0, self.perk_timer), 1),
                "waiting": [q.name for q in self.players if not q.perk_choice]}
