import { settings, CLASSIC_ALIENS, EXPEDITION_ALIENS, POWERUP_KINDS } from './config.js';
import { World, rand, pick, rad, deg } from './utils.js';
import { profile } from './profile.js';
import { Player } from './entities/ship.js';
import { Rock, gravityAccel } from './entities/rock.js';
import { Bullet } from './entities/weapons.js';
import { ALIEN_CLASSES, Chaser, Swarm } from './entities/alien.js';
import { PowerUp, Wormhole } from './entities/misc.js';
import { featuresMixin } from './features.js';
import { voyageMixin } from './voyage.js';

const DIAG = Math.SQRT1_2;   // rocks start out travelling along exact diagonals
const alive = o => !o.dead;

/** The whole simulation (GameView in game_view.py). No drawing and no HTML in here: render.js and ui.js do that. */
export class Game {
  constructor(audio, input, hooks = {}) {
    this.audio = audio; this.input = input; this.hooks = hooks;
    this.state = 'menu'; this.zone = null; this.zoneId = null; this.players = [new Player(1, 'Pilot', true, 'scout')];
    this.zoom = 1; this.slow = 1; this.zoneTime = 0; this.notice = ''; this.noticeT = 0; this.banner = 0; this.bannerText = this.bannerSub = '';
    this.contractWingman = this.ammoBonus = false; this.banked = 0; this.perkTimer = 0; this.flare = null; this.flareTimer = 30;
    this.level = 1; this.time = 0; this.objective = this.blankObjective(); this.freighter = null;
    this.startLevel(true);                       // fills the lists so update() and draw() work behind the menu
  }
  get expedition() { return settings.get('game.mode') === 'expedition' || !!this.zone; }
  get local() { return this.players[0]; }
  setState(s) { this.state = s; this.hooks.state?.(s); }
  sfx(name) { this.audio?.play(name); }
  toast(msg, t = 2) { this.notice = msg; this.noticeT = t; }

  // ------------------------------------------------------------ setup
  /** Begin a game: zoneId = a Voyage zone, or null for a Classic / Expedition run. */
  start(zoneId = null) {
    this.zoneId = zoneId; this.zone = zoneId ? settings.get(`zones.${zoneId}`) : null;
    this.players = [new Player(1, 'Pilot', true, profile.selected)]; this.newGame(); this.audio?.playMusic();
  }
  newGame() {
    this.level = this.zone ? this.zone.level : 1; this.time = 0; this.banked = 0; this.setState('playing'); this.beginZoneRun();
    for (const p of this.players) { p.reset(); this.prepareLocal(p); }
    this.startLevel(true);
  }
  startLevel(first = false) {
    const S = k => settings.get(k);
    this.worldScale = Math.min(S('world.max_scale'), 1 + S('world.growth_per_level') * (this.level - 1));
    this.world = new World(this.worldScale); this.zoomTarget = 1 / this.worldScale; if (first) this.zoom = this.zoomTarget;
    this.stars = Array.from({ length: Math.round(70 * this.worldScale * this.worldScale * 4) }, () => [rand(0, this.world.w), rand(0, this.world.h), rand(90, 255)]);
    this.rocks = []; this.aliens = []; this.bullets = []; this.powerups = []; this.allies = []; this.effects = []; this.wormhole = null;
    const [cx, cy] = this.world.center, n = this.players.length;
    this.players.forEach((p, i) => {
      if (!p.alive) p.revive();
      const s = p.ship; s.x = cx + (i - (n - 1) / 2) * 80; s.y = cy; s.driftX = s.driftY = 0; s.active = 0; if (!first) s.grace = Math.max(s.grace, 1);
    });
    this.targetRocks = Math.round((S('rocks.count') + S('difficulty.extra_rocks_per_level') * (this.level - 1)) * this.worldScale);
    for (let i = 0; i < this.targetRocks; i++) this.spawnRock(pick([3, 3, 2]));
    const boss = this.spawnAliens(); this.spawnHazards(); this.setupObjective(boss);
    this.zoneTime = this.zone ? +(this.zone.time_limit || 0) : 0; this.spawnFriendlies();
    this.powerupTimer = this.powerupInterval(); this.wormholeTimer = this.nextWormholeDelay(); this.respawnTimer = S('rocks.respawn_time');
    this.banner = 2.5; this.bannerText = this.zone ? this.zone.name.toUpperCase() : `LEVEL ${this.level}`;
    this.bannerSub = boss ? 'MOTHERSHIP DETECTED - destroy it to open a wormhole' : this.objective.type !== 'none' ? this.objectiveText()
      : this.level === 1 ? 'UP/DOWN speed   LEFT/RIGHT turn   SPACE fire   SHIFT ability   1-9 weapons' : `Play area x${this.worldScale.toFixed(2)}`;
  }
  powerupInterval() { return settings.get('timing.powerup_interval') / this.worldScale; }
  nextWormholeDelay() { const lo = settings.get('timing.wormhole_min_delay'); return rand(lo, Math.max(lo, settings.get('timing.wormhole_max_delay'))); }
  speedFactor() { return (1 + settings.get('difficulty.speed_per_level') * (this.level - 1)) * (this.zone?.rock_speed ?? 1); }
  gravityFactor() { return (1 + settings.get('difficulty.gravity_per_level') * (this.level - 1)) * (this.zone?.gravity ?? 1); }
  maxRocks() { return Math.floor(settings.get('rocks.max_rocks') * this.worldScale); }
  alivePlayers() { return this.players.filter(p => p.alive); }
  refShip() { return (this.alivePlayers()[0] || this.local).ship; }

  // ------------------------------------------------------------ spawning
  farPos(d) {
    let p; for (let i = 0; i < 50; i++) { p = this.world.random(); if (this.players.every(pl => Math.hypot(...this.world.delta(pl.ship.x, pl.ship.y, p[0], p[1])) > d)) break; }
    return p;
  }
  spawnRock(size) {
    let sp = rand(settings.get('rocks.min_speed'), settings.get('rocks.max_speed')) * this.speedFactor(); if (size === 1) sp *= 1.3;
    const [x, y] = this.farPos(260); this.rocks.push(new Rock(size, x, y, pick([-1, 1]) * sp * DIAG, pick([-1, 1]) * sp * DIAG, this.pickRockKind()));
  }
  spawnAliens() {                                  // returns true if a boss was spawned
    const a = settings.get('aliens'), kinds = this.zone ? (this.zone.aliens || []) : this.expedition ? EXPEDITION_ALIENS : CLASSIC_ALIENS;
    for (const kind of kinds) {
      const cfg = a[kind]; if (!cfg || !cfg.enabled || (this.level < cfg.min_level && !this.zone)) continue;
      const count = this.zone ? Math.max(1, this.zone.alien_count?.[kind] ?? 1) : Math.max(1, Math.round((1 + Math.floor((this.level - cfg.min_level) / 3)) * this.worldScale));
      for (let i = 0; i < count; i++) {
        const [x, y] = this.farPos(350);
        if (kind === 'swarm') { const size = Math.max(1, cfg.group_size | 0), ph = rand(0, 360); for (let s = 0; s < size; s++) this.aliens.push(new Swarm(x, y, this.level, s, size, ph)); }
        else this.aliens.push(new ALIEN_CLASSES[kind](x, y, this.level));
      }
      this.sfx(`${kind}_spawn`);
    }
    const bc = a.mothership;
    const want = this.zone ? !!this.zone.boss : bc.enabled && this.level >= bc.min_level && this.level % Math.max(1, bc.boss_every | 0) === 0;
    if (want) { const [x, y] = this.farPos(450); this.aliens.push(new ALIEN_CLASSES.mothership(x, y, this.level)); this.sfx('mothership_spawn'); return true; }
    return false;
  }
  spawnMinion(boss) {
    if (this.aliens.filter(a => a.minion).length >= 6) return;
    const m = new Chaser(boss.x, boss.y, this.level, { health: 10, score: 0, speed: 200 }); m.minion = true; this.aliens.push(m); this.sfx('chaser_spawn');
  }
  fireAlienBullet(alien, bearing, playSound = true) {
    const c = alien.cfg, a = rad(bearing), dx = Math.sin(a), dy = Math.cos(a), sp = +c.bullet_speed, st = alien.r + 8;
    this.bullets.push(new Bullet('alien_bullet', 'alien', alien.x + dx * st, alien.y + dy * st, dx * sp, dy * sp, c.bullet_damage, 3));
    if (playSound) this.sfx(`${alien.kind}_fire`);
  }
  spawnPowerup(x, y, kind) {
    if (x === undefined) { if (this.powerups.filter(p => !p.permanent).length >= 3 + Math.floor(this.worldScale)) return; [x, y] = this.world.random(); }
    this.powerups.push(new PowerUp(kind || pick(POWERUP_KINDS), x, y));
  }
  spawnWormhole() { const [x, y] = this.farPos(250); this.wormhole = new Wormhole(x, y, Math.sqrt(this.worldScale)); }
  addEffect(x, y, radius, dur = 0.5, color = [255, 190, 80]) { this.effects.push({ x, y, r: radius, age: 0, dur, color }); }
  effectAt(x, y, r, color) { this.addEffect(x, y, r, 0.5, color); }
  playSfx(n) { this.sfx(n); }

  nearestShip(x, y, alien = null) {
    let best = null, bd = 1e18;
    for (const p of this.alivePlayers()) {
      const s = p.ship, d = Math.hypot(...this.world.delta(x, y, s.x, s.y));
      if (alien && this.hiddenFrom(alien, s, d)) continue;
      if (d < bd) { best = s; bd = d; }
    }
    return best === null && alien === null ? this.refShip() : best;
  }

  // ------------------------------------------------------------ input
  handlePresses() {
    for (const a of this.input.takePresses()) {
      if (this.state === 'perk') { const m = /^w([1-3])$/.exec(a); if (m) this.pickPerk(this.local, +m[1]); else if (a === 'menu') this.hooks.quit?.(); continue; }
      if (this.state === 'gameover') { if (a === 'confirm') { this.bank(); this.newGame(); this.audio?.playMusic(); } else if (a === 'menu') this.hooks.quit?.(); continue; }
      if (this.state === 'paused') { if (a === 'pause') this.setState('playing'); else if (a === 'menu') this.hooks.quit?.(); continue; }
      if (this.state !== 'playing') continue;
      if (a === 'menu') this.hooks.quit?.();
      else if (a === 'pause') this.setState('paused');
      else if (a === 'wnext' || a === 'wprev') this.cycleWeapon(a === 'wnext' ? 1 : -1);
      else if (/^w[1-9]$/.test(a)) this.selectWeapon(+a[1]);
    }
  }
  selectWeapon(slot) {
    const p = this.local, c = p.weapons.cfg(slot); if (!c.enabled) return;
    if (p.weapons.select(slot, this.level)) this.sfx('weapon_switch'); else if (!p.weapons.unlocked(slot, this.level)) this.toast(`${c.name} unlocks at level ${c.unlock_level}`);
  }
  cycleWeapon(dir) { const p = this.local; for (let i = 1; i <= 9; i++) { const s = ((p.weapons.slot - 1 + dir * i + 90) % 9) + 1; if (p.weapons.unlocked(s, this.level)) { this.selectWeapon(s); return; } } }

  // ------------------------------------------------------------ update
  update(rawDt) {
    const dt = Math.min(rawDt, 1 / 20);
    this.handlePresses();
    this.zoom += (this.zoomTarget - this.zoom) * Math.min(1, dt * settings.get('world.zoom_speed'));
    for (const e of this.effects) e.age += dt; this.effects = this.effects.filter(e => e.age < e.dur);
    this.noticeT = Math.max(0, this.noticeT - dt);
    if (this.state === 'perk') { this.updatePerks(dt); return; }
    if (this.state !== 'playing') return;
    this.time += dt; this.banner = Math.max(0, this.banner - dt);
    this.updateHazards(dt); this.slow = this.slowFactor();
    const inp = this.input, keys = { up: inp.held('up'), down: inp.held('down'), left: inp.held('left'), right: inp.held('right') };
    for (const p of this.alivePlayers()) {
      p.score += dt * 10; p.weapons.update(dt); const s = p.ship, [ax, ay] = this.gravityOn(s);
      const pressed = inp.held('ability'); if (pressed && !p.abilityPrev) this.tryAbility(p); p.abilityPrev = pressed;
      s.update(dt, keys, ax, ay, this.world); this.healTick(p, dt);
      if (keys.up && s.speed > 0 && (p.thrustCd = (p.thrustCd || 0) - dt) <= 0) { this.sfx('thrust'); p.thrustCd = 0.3; }
      if (inp.held('fire') && !s.phased) {
        const [bs, ev] = p.weapons.fire(s, p.dmgMult);
        for (const b of bs) { b.playerId = p.id; this.bullets.push(b); }
        if (bs.length && s.cloaked && !bs[0].silent) s.active = 0;           // firing gives away a cloaked ship
        if (ev) this.sfx(ev);
      }
    }
    for (const r of this.rocks) r.update(dt * this.slow, this.world);
    this.updateAllies(dt);
    for (const a of [...this.aliens]) a.update(dt * this.slow, this);
    const aliens = [...this.aliens], rocks = [...this.rocks];
    for (const b of this.bullets) { b.update(dt * (b.owner === 'alien' ? this.slow : 1), this.world, aliens, rocks); if (b.kind !== 'mine' && b.life <= 0) b.dead = true; }
    this.rockRock(); this.shipRock(); this.bulletCollisions(); this.alienCollisions();
    this.updatePowerups(dt); this.updateObjective(dt); this.updateWormhole(dt); this.updateRespawns(dt); this.updateZone(dt);
    this.sweep();
  }
  sweep() { this.rocks = this.rocks.filter(alive); this.aliens = this.aliens.filter(alive); this.bullets = this.bullets.filter(alive); this.powerups = this.powerups.filter(alive); this.allies = this.allies.filter(alive); }
  gravityOn(ship) {
    const g = settings.get('physics.gravity') * this.gravityFactor(), soft = settings.get('physics.softening'), cap = settings.get('physics.max_accel'); let ax = 0, ay = 0;
    for (const r of this.rocks) { if (r.dead) continue; const [dx, dy] = this.world.delta(ship.x, ship.y, r.x, r.y), [a, b] = gravityAccel(dx, dy, r.mass, g, soft, cap); ax += a; ay += b; }
    return [ax, ay];
  }

  // ------------------------------------------------------------ damage helpers
  award(pid, pts) { for (const p of this.players) if (p.id === pid) p.score += pts; }
  breakRock(rock, pid = null, depth = 0) {
    if (rock.dead) return [];
    const kids = this.rocks.filter(alive).length + 1 <= this.maxRocks() ? rock.split() : [];
    rock.dead = true; this.rocks.push(...kids); this.sfx('split'); this.countRock(rock);
    if (pid) { const c = settings.get('credits'); this.earn(pid, c.rock_per_size * rock.size + (rock.kind === 'gold' ? c.gold_rock * rock.size : 0)); }
    if (rock.kind === 'explosive') this.rockExplosion(rock.x, rock.y, 80 + 25 * rock.size, pid, depth);
    return kids;
  }
  damagePlayer(p, amount, fx, fy) {
    const s = p.ship; if (!p.alive || s.phased || s.shieldT > 0 || s.grace > 0) return false;
    s.sinceHit = 0; if (s.cloaked) s.active = 0;
    const [dx, dy] = this.world.delta(fx, fy, s.x, s.y), d = Math.hypot(dx, dy);
    if (s.shieldMax > 0 && s.shieldHp > 0) {                      // rechargeable shield soaks it up
      const ab = Math.min(s.shieldHp, amount); s.shieldHp -= ab; amount -= ab; s.shieldWait = s.shieldDelay; this.sfx('shield_hit');
      if (amount <= 0.01) { s.grace = 0.4; return true; }
    }
    s.health -= amount; s.grace = settings.get('ship.grace_time');
    if (d > 0) { s.driftX += dx / d * 220; s.driftY += dy / d * 220; }          // knock the ship away
    this.sfx('crash');
    if (s.health <= 0) { s.health = 0; p.alive = false; this.addEffect(s.x, s.y, 90, 0.8, [255, 120, 60]); if (!this.alivePlayers().length) this.gameOver(); }
    return true;
  }
  gameOver() {
    this.audio?.stopMusic(); this.saveHull(); this.bank(); this.setState('gameover');
    this.hooks.gameover?.({ score: Math.floor(this.local.score), level: this.level, zone: this.zone });
  }
  hitAlien(alien, dmg, pid = null) { alien.takeDamage(dmg); if (alien.health <= 0) this.killAlien(alien, pid); }
  killAlien(alien, pid = null, score = true) {
    if (alien.dead) return; alien.dead = true; this.countKill(alien);
    if (score && pid) { this.award(pid, alien.cfg.score || 0); this.earn(pid, (alien.cfg.score || 0) * settings.get('credits.alien_factor')); }
    const big = alien.kind === 'mothership'; this.addEffect(alien.x, alien.y, alien.r * (big ? 4 : 2.5), big ? 0.9 : 0.5, big ? [255, 120, 60] : [255, 200, 90]); this.sfx(`${alien.kind}_die`);
    if (!alien.minion) { const drops = big ? 2 : Math.random() < settings.get('difficulty.alien_drop_chance') ? 1 : 0; for (let i = 0; i < drops; i++) this.spawnPowerup(alien.x + i * 40, alien.y); }
  }
  explode(x, y, radius, damage, pid) {
    this.addEffect(x, y, radius, 0.6, [255, 150, 60]); this.sfx('explosion');
    for (const a of [...this.aliens]) if (!a.dead && Math.hypot(...this.world.delta(x, y, a.x, a.y)) < radius + a.r) this.hitAlien(a, damage, pid);
    for (const r of [...this.rocks]) if (!r.dead && Math.hypot(...this.world.delta(x, y, r.x, r.y)) < radius + r.r) { this.award(pid, 10 * r.size); this.breakRock(r, pid); }
  }

  // ------------------------------------------------------------ collisions
  overlap(a, b) { return this.world.overlap(a, b); }
  shipDist(ship, o) { return Math.hypot(...this.world.delta(ship.x, ship.y, o.x, o.y)); }
  rockRock() {
    const rocks = this.rocks.filter(alive), split = !!settings.get('rocks.split_on_rock_hit');
    for (let i = 0; i < rocks.length; i++) {
      const a = rocks[i]; if (a.dead) continue;
      for (let j = i + 1; j < rocks.length; j++) {
        const b = rocks[j]; if (b.dead) continue;
        const [dx, dy] = this.world.delta(a.x, a.y, b.x, b.y), dist = Math.hypot(dx, dy);
        if (dist === 0 || dist >= a.r + b.r) continue;
        const nx = dx / dist, ny = dy / dist, rel = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny;
        if (rel >= 0) continue;                                       // already moving apart
        if (split) { if (a.cooldown > 0 || b.cooldown > 0) continue; this.breakRock(a); this.breakRock(b); break; }
        const imp = 2 * rel / (a.mass + b.mass);                       // elastic bounce
        a.vx += imp * b.mass * nx; a.vy += imp * b.mass * ny; b.vx -= imp * a.mass * nx; b.vy -= imp * a.mass * ny;
      }
    }
  }
  shipRock() {
    for (const p of this.alivePlayers()) {
      const s = p.ship; if (s.phased) continue;
      for (const r of [...this.rocks]) {
        if (r.dead || r.cooldown > 0 || !this.overlap(s, r)) continue;
        if (s.shieldT > 0 || s.deflecting) { this.award(p.id, 25); this.breakRock(r, p.id); }       // ram / deflect
        else if (this.damagePlayer(p, settings.get('ship.hit_damage'), r.x, r.y)) this.breakRock(r, p.id);
        if (!p.alive) break;
      }
    }
  }
  alienBulletHit(b) {                                   // an alien bullet or mine: ships, allies and the freighter
    if (b.kind === 'mine') {
      const near = this.alivePlayers().some(p => !p.ship.phased && this.shipDist(p.ship, b) < b.blast * 0.45 + p.ship.r);
      if (b.fuse > 0 && !(b.arm <= 0 && near)) return;
      b.dead = true; this.addEffect(b.x, b.y, b.blast, 0.5, [255, 90, 90]); this.sfx('mine_blast');
      for (const p of this.alivePlayers()) if (this.shipDist(p.ship, b) < b.blast + p.ship.r) this.damagePlayer(p, b.damage, b.x, b.y);
      return;
    }
    for (const p of this.alivePlayers()) {
      const s = p.ship; if (s.phased || !this.overlap(b, s)) continue;
      if (s.deflecting) { b.owner = 'player'; b.playerId = p.id; b.vx *= -1.2; b.vy *= -1.2; b.life = 3; b.damage *= 2; this.addEffect(b.x, b.y, 30, 0.3, [255, 255, 255]); return; }
      b.dead = true; this.damagePlayer(p, b.damage, b.x, b.y); return;
    }
    if (this.allyBulletHit(b)) return;
    const fr = this.freighter; if (fr && this.overlap(b, fr)) { b.dead = true; fr.health -= b.damage; }
  }
  mineTriggered(m) { const trig = m.blast * 0.45; return [...this.aliens, ...this.rocks].some(t => !t.dead && Math.hypot(...this.world.delta(m.x, m.y, t.x, t.y)) < trig + t.r); }
  bulletCollisions() {
    for (const b of [...this.bullets]) {
      if (b.dead) continue;
      if (b.owner === 'alien') { this.alienBulletHit(b); continue; }
      const pid = b.playerId;
      if (b.kind === 'mine') { if (b.fuse <= 0 || (b.arm <= 0 && this.mineTriggered(b))) { b.dead = true; this.explode(b.x, b.y, b.blast, b.damage, pid); } continue; }
      if (b.heal > 0) {                                  // repair dart: heals a teammate
        for (const q of this.alivePlayers()) if (q.id !== pid && !q.ship.phased && this.overlap(b, q.ship)) { q.ship.health = Math.min(q.ship.maxHealth, q.ship.health + b.heal); this.addEffect(q.ship.x, q.ship.y, 60, 0.4, [120, 255, 160]); b.dead = true; break; }
        if (b.dead) continue;
      }
      for (const a of [...this.aliens]) { if (b.pierce <= 0) break; if (a.dead || b.hitIds.has(a) || !this.overlap(b, a)) continue; b.hitIds.add(a); b.pierce--; this.hitAlien(a, b.damage, pid); }
      for (const r of [...this.rocks]) {
        if (b.pierce <= 0) break; if (r.dead || b.hitIds.has(r) || !this.overlap(b, r)) continue; b.hitIds.add(r); b.pierce--;
        if (r.hp > 1) { r.hp--; this.addEffect(r.x, r.y, 30, 0.25, [220, 220, 240]); continue; }        // armoured rock needs several hits
        this.award(pid, 10 * r.size); for (const k of this.breakRock(r, pid)) b.hitIds.add(k);
      }
      if (b.pierce <= 0) b.dead = true;
    }
  }
  alienCollisions() {
    for (const a of [...this.aliens]) {
      if (a.dead) continue;
      for (const p of this.alivePlayers()) {
        if (p.ship.phased || !this.overlap(a, p.ship)) continue;
        if (p.ship.shieldT > 0) this.hitAlien(a, 60, p.id);
        else if (a.ramCd <= 0 && this.damagePlayer(p, a.cfg.contact_damage, a.x, a.y)) { a.ramCd = 1; if (a.cfg.dies_on_ram) this.killAlien(a, null, false); }
        if (a.dead) break;
      }
      if (a.dead) continue;
      for (const r of [...this.rocks]) if (!r.dead && r.cooldown <= 0 && this.overlap(a, r)) { this.breakRock(r); a.takeDamage(settings.get('rocks.alien_damage')); if (a.health <= 0) { this.killAlien(a, null, false); break; } }
    }
  }

  // ------------------------------------------------------------ pickups, wormholes, respawns
  updatePowerups(dt) {
    if ((this.powerupTimer -= dt) <= 0) { this.spawnPowerup(); this.powerupTimer = this.powerupInterval() * rand(0.8, 1.2); }
    for (const pu of this.powerups) {
      if (pu.dead) continue; pu.update(dt, this.world); if (pu.expired) { pu.dead = true; continue; }
      for (const p of this.alivePlayers()) {
        const s = p.ship; if (s.phased) continue;
        const [dx, dy] = this.world.delta(pu.x, pu.y, s.x, s.y), d = Math.hypot(dx, dy);
        if (p.magnet > 0 && d > 0 && d < p.magnet) { pu.x += dx / d * 260 * dt; pu.y += dy / d * 260 * dt; }          // Tractor Field
        if (d < pu.r + s.r) { this.collect(pu, p); break; }
      }
    }
  }
  collect(pu, p) {
    if (pu.kind === 'crystal' || pu.kind === 'pod') { this.objectiveItem(pu, p); return; }
    const s = p.ship;
    if (pu.kind === 'health') s.health = Math.min(s.maxHealth, s.health + settings.get('ship.health_gain'));
    else if (pu.kind === 'speed') s.boost = settings.get('timing.speed_boost_time');
    else if (pu.kind === 'ammo') p.weapons.addAmmo(); else s.shieldT = settings.get('timing.invincible_time');
    p.score += 50; this.earn(p.id, settings.get('credits.powerup')); this.sfx('powerup'); pu.dead = true;
  }
  bossAlive() { return this.aliens.some(a => !a.dead && a.kind === 'mothership'); }
  updateWormhole(dt) {
    const wh = this.wormhole;
    if (!wh) { if (this.bossAlive() || !this.objective.done) return; if ((this.wormholeTimer -= dt) <= 0) this.spawnWormhole(); return; }
    wh.update(dt);
    if (wh.expired) { this.wormhole = null; this.wormholeTimer = this.nextWormholeDelay(); }
    else if (wh.canEnter) for (const p of this.alivePlayers()) if (this.world.dist(wh, p.ship) < wh.full) { this.completeLevel(); return; }
  }
  completeLevel() {
    this.sfx('wormhole');
    if (this.zone) { this.finishZone(); return; }
    for (const p of this.players) { p.score += 200 * this.level; this.earn(p.id, settings.get('credits.level_clear') * this.level); }
    this.level++; this.bank(); this.startLevel(); if (this.expedition) this.beginPerks();
  }
  updateRespawns(dt) {
    if (this.rocks.filter(alive).length < this.targetRocks && (this.respawnTimer -= dt) <= 0) { this.spawnRock(3); this.respawnTimer = settings.get('rocks.respawn_time'); }
  }
}
Object.assign(Game.prototype, featuresMixin, voyageMixin);
