import { settings } from './config.js';
import { rand } from './utils.js';
import { profile } from './profile.js';
import { Bullet } from './entities/weapons.js';
import { PowerUp, Freighter } from './entities/misc.js';
import { HAZARD_CLASSES, SolarFlare } from './entities/hazards.js';
import { PERKS, applyPerk } from './entities/perks.js';


/** Credits, rock types, hazards, objectives, ship abilities and perks (FeaturesMixin in game_features.py). */
export const featuresMixin = {
  // ---- credits
  earn(pid, amount) { for (const p of this.players) if (p.id === pid) p.creditsRun += amount * p.creditMult; },
  bank() {                                           // move this player's earned credits into the saved profile
    const delta = Math.floor(this.local.creditsRun) - this.banked;
    if (delta > 0) { profile.credits += delta; this.banked += delta; }
    profile.record(this.level, this.local.score); profile.save();
  },

  // ---- rock types
  pickRockKind() {
    const wz = this.zone?.rock_weights;
    if (!wz && !this.expedition) return 'normal';
    const pool = [['normal', 60]];
    if (wz) for (const [k, w] of Object.entries(wz)) { if (w > 0) pool.push([k, w]); }
    else for (const [k, c] of Object.entries(settings.get('rock_types'))) if (this.level >= c.min_level && c.weight > 0) pool.push([k, c.weight]);
    let r = Math.random() * pool.reduce((s, [, w]) => s + w, 0);
    for (const [k, w] of pool) if ((r -= w) <= 0) return k;
    return 'normal';
  },
  rockExplosion(x, y, radius, pid, depth = 0) {
    this.addEffect(x, y, radius, 0.5, [255, 110, 70]); this.sfx('explosion');
    for (const p of this.alivePlayers()) if (Math.hypot(...this.world.delta(x, y, p.ship.x, p.ship.y)) < radius + p.ship.r) this.damagePlayer(p, 20, x, y);
    for (const a of [...this.aliens]) if (!a.dead && Math.hypot(...this.world.delta(x, y, a.x, a.y)) < radius + a.r) this.hitAlien(a, 25, pid);
    if (depth < 4) for (const r of [...this.rocks]) if (!r.dead && Math.hypot(...this.world.delta(x, y, r.x, r.y)) < radius + r.r) this.breakRock(r, pid, depth + 1);
  },

  // ---- hazards
  spawnHazards() {
    this.hazards = []; this.flare = null; const h = settings.get('hazards'); this.flareTimer = h.flare_interval * rand(0.6, 1);
    if (!this.expedition) return;
    if (this.zone) {
      for (const [kind, n] of Object.entries(this.zone.hazards || {})) for (let i = 0; i < n; i++) { const [x, y] = this.farPos(420); this.hazards.push(new HAZARD_CLASSES[kind](x, y)); }
      return;
    }
    const lv = this.level, ws = this.worldScale, rows = [['nebula', h.nebula_from, 3], ['blackhole', h.blackhole_from, 2], ['ion', h.ion_from, 2]];
    for (const [kind, from, cap] of rows) {
      if (lv < from) continue;
      const n = 1 + Math.floor((lv - from) / 3);
      for (let i = 0; i < Math.min(cap + Math.floor(ws) - 1, Math.max(1, Math.round(n * Math.sqrt(ws)))); i++) { const [x, y] = this.farPos(420); this.hazards.push(new HAZARD_CLASSES[kind](x, y)); }
    }
  },
  updateHazards(dt) {
    for (const p of this.players) { p.ship.inNebula = false; p.ship.jammed = false; }
    if (!this.expedition) return;
    const cfg = settings.get('hazards');
    for (const hz of this.hazards) {
      hz.update(dt, this.world);
      for (const p of this.alivePlayers()) {
        const s = p.ship, [dx, dy] = this.world.delta(s.x, s.y, hz.x, hz.y), d = Math.hypot(dx, dy);
        if (hz.kind === 'nebula') { if (d < hz.radius) s.inNebula = true; }
        else if (hz.kind === 'ion') { if (d < hz.radius) { s.jammed = true; if (!s.phased) { s.driftX += rand(-1, 1) * 220 * dt; s.driftY += rand(-1, 1) * 220 * dt; } } }
        else if (hz.kind === 'blackhole' && !s.phased && d < hz.radius) {
          const [ax, ay] = this.pull(dx, dy, cfg.blackhole_strength, 420); s.driftX += ax * dt; s.driftY += ay * dt;
          if (d < hz.core + s.r) this.damagePlayer(p, 30, hz.x, hz.y);
        }
      }
      if (hz.kind === 'blackhole') for (const r of this.rocks) {
        if (r.dead) continue; const [dx, dy] = this.world.delta(r.x, r.y, hz.x, hz.y), d = Math.hypot(dx, dy);
        if (d < hz.core) { this.addEffect(r.x, r.y, 40, 0.4, [150, 100, 255]); r.dead = true; }
        else if (d < hz.radius) { const [ax, ay] = this.pull(dx, dy, cfg.blackhole_strength, 300); r.vx += ax * dt; r.vy += ay * dt; }
      }
    }
    this.updateFlare(dt, cfg);
  },
  pull(dx, dy, strength, cap) {
    const d2 = dx * dx + dy * dy + 70 * 70, d = Math.sqrt(d2), a = Math.min(strength / d2, cap); return [a * dx / d, a * dy / d];
  },
  updateFlare(dt, cfg) {
    if (this.zone && !this.zone.flares) return;
    if (!this.flare) {
      if (this.level >= cfg.flare_from && (this.flareTimer -= dt) <= 0) { this.flare = new SolarFlare(this.world); this.flareTimer = cfg.flare_interval * rand(0.8, 1.2); this.sfx('flare_warn'); }
      return;
    }
    const f = this.flare; f.t += dt;
    if (f.phase === 1 && !f.fired) { f.fired = true; this.flareBurst(f, cfg.flare_damage); }
    if (f.finished) this.flare = null;
  },
  flareBurst(f, damage) {
    this.sfx('flare_hit');
    for (const p of this.alivePlayers()) if (f.covers(this.world, p.ship.x, p.ship.y, p.ship.r)) this.damagePlayer(p, damage, f.x, f.y);
    for (const a of [...this.aliens]) if (!a.dead && f.covers(this.world, a.x, a.y, a.r)) this.hitAlien(a, 50);
    for (const r of [...this.rocks]) if (!r.dead && f.covers(this.world, r.x, r.y, r.r)) this.breakRock(r);
    const fr = this.freighter; if (fr && f.covers(this.world, fr.x, fr.y, fr.r)) fr.health -= damage * 2;
  },

  // ---- objectives
  blankObjective() { return { type: 'none', need: 0, got: 0, done: true, ok: false, time: 0, total: 0 }; },
  spawnObjectiveItems(kind, need) {
    for (let i = 0; i < need; i++) {
      if (kind === 'rescue') { const [x, y] = this.farPos(250); this.powerups.push(new PowerUp('pod', x, y, { permanent: true, vx: rand(-30, 30), vy: rand(-30, 30) })); }
      else { const [x, y] = this.farPos(kind === 'beacon' ? 900 : 200); this.powerups.push(new PowerUp('crystal', x, y, { permanent: true })); }
    }
  },
  setupObjective(boss) {
    this.freighter = null; const obj = this.blankObjective(), cfg = settings.get('objectives'), spec = this.zone?.objective;
    const addFreighter = (still) => { const [x, y] = this.farPos(300); this.freighter = new Freighter(x, y); if (still) { this.freighter.vx = this.freighter.vy = 0; obj.stationary = true; } };
    if (boss) Object.assign(obj, { type: 'boss', done: false });
    else if (this.zone) {
      if (spec) {
        const kind = spec.type; Object.assign(obj, { type: kind === 'defend' ? 'escort' : kind, done: false, need: +(spec.need || 0), total: +(spec.seconds || 0) });
        if (['crystals', 'beacon', 'rescue'].includes(kind)) this.spawnObjectiveItems(kind, obj.need);
        else if (kind === 'escort' || kind === 'defend') { obj.total = +(spec.seconds || 35); addFreighter(kind === 'defend'); }
      }
    } else if (this.expedition && cfg.enabled && this.level >= 2) {
      const kind = ['crystals', 'rescue', 'escort'][(this.level - 2) % 3]; Object.assign(obj, { type: kind, done: false });
      if (kind === 'crystals') { obj.need = Math.floor(cfg.crystals_base + Math.floor(this.level / 2)); this.spawnObjectiveItems('crystals', obj.need); }
      else if (kind === 'rescue') { obj.need = Math.floor(cfg.pods_base + Math.floor(this.level / 3)); this.spawnObjectiveItems('rescue', obj.need); }
      else { obj.total = +cfg.escort_seconds; addFreighter(false); }
    }
    this.objective = obj;
  },
  objectiveText() {
    const o = this.objective; let t;
    if (o.type === 'none') return '';
    if (o.type === 'boss') return o.done ? '' : 'OBJECTIVE: destroy the mothership';
    if (o.done) t = o.ok ? 'OBJECTIVE COMPLETE' : 'OBJECTIVE FAILED - find the wormhole';
    else if (o.type === 'crystals') t = `OBJECTIVE: collect crystals ${o.got}/${o.need}`;
    else if (o.type === 'rescue') t = `OBJECTIVE: rescue stranded pods ${o.got}/${o.need}`;
    else if (o.type === 'survive') t = `OBJECTIVE: survive ${Math.floor(o.time)}/${Math.floor(o.total)}s`;
    else if (o.type === 'hunt') t = `OBJECTIVE: destroy aliens ${o.got}/${o.need}`;
    else if (o.type === 'prospect') t = `OBJECTIVE: break gold rocks ${o.got}/${o.need}`;
    else if (o.type === 'beacon') t = 'OBJECTIVE: reach the beacon (the glowing crystal)';
    else t = `OBJECTIVE: ${o.stationary ? 'defend the station' : 'escort the freighter'} ${Math.floor(o.time)}/${Math.floor(o.total)}s`;
    if (this.zone && this.zoneTime > 0 && !o.done) t += `   TIME ${Math.ceil(this.zoneTime)}s`;
    return t;
  },
  objectiveItem(pu, p) {
    const o = this.objective; o.got++; this.earn(p.id, settings.get(pu.kind === 'crystal' ? 'credits.crystal' : 'credits.rescue')); this.sfx('crystal');
    this.addEffect(pu.x, pu.y, 50, 0.4, [120, 230, 255]); pu.dead = true; if (o.got >= o.need && !o.done) this.finishObjective(true);
  },
  finishObjective(ok) {
    const o = this.objective; o.done = true; o.ok = ok;
    if (ok) { for (const p of this.players) this.earn(p.id, settings.get('credits.objective') * this.level); this.sfx('objective_done'); this.toast('Objective complete! The wormhole is opening...', 3); }
    else this.toast('The freighter was lost - find the wormhole', 3);
    this.wormholeTimer = Math.min(this.wormholeTimer, 3);
  },
  updateObjective(dt) {
    const o = this.objective;
    if (o.type === 'boss' && !o.done && !this.bossAlive()) this.finishObjective(true);
    if (o.type === 'survive' && !o.done) { o.time += dt; if (o.time >= o.total) this.finishObjective(true); return; }
    const fr = this.freighter; if (o.type !== 'escort' || o.done || !fr) return;
    fr.update(dt, this.world); o.time += dt;
    if (fr.hitCd <= 0) for (const r of this.rocks) if (!r.dead && r.cooldown <= 0 && this.overlap(fr, r)) { fr.health -= 25; fr.hitCd = 0.8; this.breakRock(r); break; }
    if (fr.health <= 0) { this.addEffect(fr.x, fr.y, 120, 0.9, [255, 120, 60]); this.freighter = null; this.finishObjective(false); }
    else if (o.time >= o.total) { this.addEffect(fr.x, fr.y, 100, 0.8, [120, 255, 160]); this.freighter = null; this.finishObjective(true); }
  },
  countKill(alien) {
    const o = this.objective; if (this.zone && o.type === 'hunt' && !o.done && !alien.minion && ++o.got >= o.need) this.finishObjective(true);
  },
  countRock(rock) {
    const o = this.objective; if (this.zone && o.type === 'prospect' && !o.done && rock.kind === 'gold' && ++o.got >= o.need) this.finishObjective(true);
  },
  updateZone(dt) {
    if (this.zone && this.zone.time_limit && !this.objective.done && (this.zoneTime -= dt) <= 0) { this.toast('Out of time!', 3); this.gameOver(); }
  },

  // ---- ship abilities
  slowFactor() { return this.alivePlayers().some(p => p.ship.timeslip) ? 0.5 : 1; },
  tryAbility(p) {
    const s = p.ship, kind = s.abilityType;
    if (!kind || s.abilityCd > 0 || s.jammed || s.phased) { if (kind && s.jammed) this.toast('Ion storm - ability offline', 1.5); return; }
    const a = s.ability;
    if (kind === 'hyperjump') this.hyperjump(p);
    else { s.active = +(a.duration ?? 3); this.addEffect(s.x, s.y, 70, 0.5, [150, 220, 255]); }
    if (kind === 'afterburner') s.boost = s.active;
    else if (kind === 'ram') { s.shieldT = s.active; s.boost = s.active; }          // the invincibility power-up already smashes things
    else if (kind === 'nova') { s.active = 0; this.explode(s.x, s.y, +(a.radius ?? 300), +(a.damage ?? 40), p.id); }
    else if (kind === 'launch') for (let i = 0; i < (a.count ?? 2); i++) this.spawnAlly('wingman', s.x + (i % 2 ? -70 : 70), s.y, +(a.duration ?? 20));
    s.abilityCd = Math.max(a.cooldown * p.cdMult, s.active); this.sfx(`ability_${kind}`);
  },
  hyperjump(p) {
    const s = p.ship; this.addEffect(s.x, s.y, 90, 0.5, [200, 160, 255]); let best = null;
    for (let i = 0; i < 60; i++) {
      const [x, y] = this.world.random(); best = [x, y];
      const near = (list, f) => list.some(o => !o.dead && Math.hypot(...this.world.delta(x, y, o.x, o.y)) < f(o));
      if (near(this.rocks, r => r.r + 130) || near(this.aliens, () => 220)) continue;
      if (this.hazards.some(h => h.kind === 'blackhole' && Math.hypot(...this.world.delta(x, y, h.x, h.y)) < h.radius * 0.5)) continue;
      break;
    }
    [s.x, s.y] = best; s.driftX = s.driftY = 0; s.grace = Math.max(s.grace, 1); this.addEffect(s.x, s.y, 90, 0.5, [200, 160, 255]);
  },
  healTick(p, dt) {
    const s = p.ship; if (!s.healing) return; const a = s.ability;
    s.health = Math.min(s.maxHealth, s.health + (a.self_rate ?? 8) * dt);
    for (const q of this.alivePlayers()) if (q !== p && !q.ship.phased && this.world.dist(s, q.ship) < (a.range ?? 360)) q.ship.health = Math.min(q.ship.maxHealth, q.ship.health + (a.ally_rate ?? 12) * dt);
  },
  hiddenFrom(alien, ship, dist) {
    if (!(ship.cloaked || ship.inNebula)) return false;
    return dist > (alien.detectRange || settings.get('hazards.cloak_detect'));
  },
  dropAlienMine(alien) {
    const c = alien.cfg, mines = this.bullets.filter(b => !b.dead && b.owner === 'alien' && b.kind === 'mine'); if (mines.length >= 25) mines[0].dead = true;
    const m = new Bullet('alien_mine', 'alien', alien.x, alien.y, 0, 0, c.mine_damage, 999, { kind: 'mine', blast: c.mine_blast, fuse: 14 }); m.arm = 1; this.bullets.push(m); this.sfx('minelayer_drop');
  },

  // ---- perks (Expedition)
  beginPerks() {
    this.setState('perk'); this.perkTimer = 20; this.input.clear();
    for (const p of this.players) { p.perkOptions = Object.keys(PERKS).sort(() => Math.random() - 0.5).slice(0, 3); p.perkChoice = 0; }
    this.hooks.perks?.();
  },
  pickPerk(p, idx) {
    if (this.state !== 'perk' || p.perkChoice || idx < 1 || idx > 3) return;
    p.perkChoice = idx; applyPerk(p, p.perkOptions[idx - 1]); this.sfx('perk_pick');
    if (this.players.every(q => q.perkChoice)) { this.setState('playing'); this.banner = 1.5; this.hooks.perksDone?.(); }
  },
  updatePerks(dt) { if ((this.perkTimer -= dt) <= 0) for (const p of this.players) if (!p.perkChoice) this.pickPerk(p, 1 + Math.floor(Math.random() * 3)); },
};
