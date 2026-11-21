import { W, H, CFG, WEAPONS, ALIENS, COLORS } from './config.js';
import { World, rand, pick, rad, store, SFX } from './utils.js';
import { Player } from './entities/ship.js';
import { Rock, gravityAccel } from './entities/rock.js';
import { ALIEN_CLASSES } from './entities/alien.js';
import { fire, POWERUPS, PowerUp, Wormhole } from './entities/misc.js';

const DIAG = Math.SQRT1_2;   // rocks start out travelling along exact diagonals

/** Core state machine (menu | playing | paused | gameover), the simulation and the renderer. */
export class Game {
  constructor(canvas, assets, input, ui) {
    this.ctx = canvas.getContext('2d'); this.img = assets.img; this.input = input; this.ui = ui;
    this.players = [new Player(1)]; this.player = this.players[0];   // single player; the array is the hook for a second pilot
    this.saved = store.load(); this.level = 1; this.time = 0; this.noticeT = 0;
    this.startLevel(true);                 // fills rocks/aliens/etc. so update() and draw() work behind the menu
    this.setState('menu');
  }
  setState(s) { this.state = s; this.ui.show(s === 'playing' ? null : s); if (s === 'menu') this.ui.best(this.saved); }

  // ------------------------------------------------------------------ setup
  newGame() { this.players.forEach(p => p.reset()); this.level = 1; this.time = 0; this.startLevel(true); this.setState('playing'); }
  startLevel(first = false) {
    const Wd = CFG.world; this.scale = Math.min(Wd.max, 1 + Wd.growth * (this.level - 1));
    this.world = new World(this.scale); this.zoomTarget = 1 / this.scale; if (first) this.zoom = this.zoomTarget;
    this.stars = Array.from({ length: Math.round(70 * this.scale * this.scale * 4) }, () => [rand(0, this.world.w), rand(0, this.world.h), rand(90, 255)]);
    this.rocks = []; this.aliens = []; this.bullets = []; this.powerups = []; this.effects = []; this.wormhole = null;
    for (const p of this.players) { const s = p.ship; [s.x, s.y] = [this.world.w / 2, this.world.h / 2]; s.driftX = s.driftY = 0; if (!first) s.grace = Math.max(s.grace, 1); }
    this.targetRocks = Math.round((CFG.rocks.count + CFG.diff.extraRocks * (this.level - 1)) * this.scale);
    for (let i = 0; i < this.targetRocks; i++) this.spawnRock(pick([3, 3, 2]));
    for (const [kind, c] of Object.entries(ALIENS)) {
      if (this.level < c.minLevel) continue;
      const n = Math.max(1, Math.round((1 + Math.floor((this.level - c.minLevel) / 3)) * this.scale));
      for (let i = 0; i < n; i++) { const [x, y] = this.farPos(350); this.aliens.push(new ALIEN_CLASSES[kind](x, y, this.level)); }
    }
    this.powerupTimer = this.powerupInterval(); this.wormholeTimer = rand(CFG.timing.whMin, CFG.timing.whMax);
    this.respawnTimer = CFG.rocks.respawn; this.banner = 2.5;
    this.bannerSub = this.level === 1 ? 'UP/DOWN speed  LEFT/RIGHT turn  SPACE fire  1-3 weapons' : `Play area x${this.scale.toFixed(2)}`;
  }
  powerupInterval() { return CFG.timing.powerupEvery / this.scale; }
  farPos(d) {
    let p; for (let i = 0; i < 50; i++) { p = this.world.random(); if (this.players.every(pl => Math.hypot(...this.world.delta(pl.ship.x, pl.ship.y, ...p)) > d)) break; }
    return p;
  }
  spawnRock(size) {
    const sp = rand(CFG.rocks.minSpeed, CFG.rocks.maxSpeed) * (1 + CFG.diff.speed * (this.level - 1)) * (size === 1 ? 1.3 : 1);
    const [x, y] = this.farPos(260);
    this.rocks.push(new Rock(size, x, y, pick([-1, 1]) * sp * DIAG, pick([-1, 1]) * sp * DIAG));
  }
  spawnPowerup(x, y, kind) {
    if (x === undefined) { if (this.powerups.length >= 3 + Math.floor(this.scale)) return; [x, y] = this.world.random(); }
    this.powerups.push(new PowerUp(kind || pick(POWERUPS), x, y));
  }
  ring(x, y, r, dur = 0.5, color = '255,190,80') { this.effects.push({ x, y, r, age: 0, dur, color }); }

  // ------------------------------------------------------------------ update
  handleKeys() {
    for (const code of this.input.takePresses()) {
      if (this.state === 'menu' && code === 'Enter') this.newGame();
      else if (this.state === 'gameover') { if (code === 'Enter') this.newGame(); else if (code === 'Escape') this.setState('menu'); }
      else if (this.state === 'paused' && code === 'KeyP') this.setState('playing');
      else if (this.state === 'playing') {
        if (code === 'KeyP') this.setState('paused');
        else if (code === 'Escape') { this.bank(); this.setState('menu'); }
        else if (/^(Digit|Numpad)[1-9]$/.test(code)) this.selectWeapon(+code.slice(-1));
      }
    }
  }
  selectWeapon(slot) {
    if (this.player.unlocked(slot, this.level) && this.player.slot !== slot) { this.player.slot = slot; SFX.switch(); }
    else if (WEAPONS[slot] && !this.player.unlocked(slot, this.level)) { this.notice = `${WEAPONS[slot].name} unlocks at level ${WEAPONS[slot].unlock}`; this.noticeT = 2; }
  }
  bank() { const s = this.saved; s.bestScore = Math.max(s.bestScore, Math.floor(this.player.score)); s.bestLevel = Math.max(s.bestLevel, this.level); store.save(s); }

  update(rawDt) {
    const dt = Math.min(rawDt, 1 / 20);
    this.handleKeys();
    this.zoom += (this.zoomTarget - this.zoom) * Math.min(1, dt * CFG.world.zoomSpeed);
    this.effects.forEach(e => e.age += dt); this.effects = this.effects.filter(e => e.age < e.dur);
    this.noticeT = Math.max(0, (this.noticeT || 0) - dt);
    if (this.state !== 'playing') return;
    this.time += dt; this.banner = Math.max(0, this.banner - dt);
    const inp = this.input, keys = { up: inp.held('ArrowUp'), down: inp.held('ArrowDown'), left: inp.held('ArrowLeft'), right: inp.held('ArrowRight') };
    for (const p of this.players.filter(p => p.alive)) {
      p.score += dt * 10; p.cooldown = Math.max(0, p.cooldown - dt);
      const [ax, ay] = this.gravityOn(p.ship);
      p.ship.update(dt, keys, ax, ay, this.world);
      if (inp.held('Space')) this.tryFire(p);
    }
    this.rocks.forEach(r => r.update(dt, this.world));
    this.aliens.forEach(a => a.update(dt, this));
    for (const b of this.bullets) b.update(dt, this.world);
    this.bullets = this.bullets.filter(b => b.life > 0);
    this.rockRock(); this.shipRock(); this.bulletHits(); this.alienHits();
    this.updatePowerups(dt); this.updateWormhole(dt);
    if (this.rocks.length < this.targetRocks && (this.respawnTimer -= dt) <= 0) { this.spawnRock(3); this.respawnTimer = CFG.rocks.respawn; }
  }
  gravityOn(ship) {
    const g = CFG.physics.gravity * (1 + CFG.diff.gravity * (this.level - 1)); let ax = 0, ay = 0;
    for (const r of this.rocks) {
      const [dx, dy] = this.world.delta(ship.x, ship.y, r.x, r.y), [a, b] = gravityAccel(dx, dy, r.mass, g, CFG.physics.soft, CFG.physics.maxAccel);
      ax += a; ay += b;
    }
    return [ax, ay];
  }
  tryFire(p) {
    const w = WEAPONS[p.slot];
    if (p.cooldown > 0) return;
    if (p.ammo[p.slot] === 0) { p.cooldown = 0.3; SFX.empty(); return; }
    if (p.ammo[p.slot] > 0) p.ammo[p.slot]--;
    p.cooldown = w.cd; this.bullets.push(...fire(p.ship, p.slot)); SFX.fire();
  }

  // ------------------------------------------------------------------ damage and collisions
  damagePlayer(p, amount, fx, fy) {
    const s = p.ship; if (!p.alive || s.invulnerable) return false;
    s.health -= amount; s.grace = CFG.ship.grace;
    const [dx, dy] = this.world.delta(fx, fy, s.x, s.y), d = Math.hypot(dx, dy);
    if (d > 0) { s.driftX += dx / d * 220; s.driftY += dy / d * 220; }          // knock the ship away
    SFX.crash();
    if (s.health <= 0) { s.health = 0; p.alive = false; this.ring(s.x, s.y, 90, 0.8, '255,120,60'); if (!this.players.some(q => q.alive)) this.gameOver(); }
    return true;
  }
  gameOver() { this.bank(); SFX.die(); this.ui.final(Math.floor(this.player.score), this.level); this.setState('gameover'); }
  breakRock(rock, scored = false) {
    const kids = this.rocks.length + 1 <= CFG.rocks.max * this.scale ? rock.split() : [];
    this.rocks.splice(this.rocks.indexOf(rock), 1); this.rocks.push(...kids); SFX.split();
    if (scored) this.player.score += 10 * rock.size;
  }
  killAlien(a, scored = true) {
    const i = this.aliens.indexOf(a); if (i < 0) return;
    this.aliens.splice(i, 1); this.ring(a.x, a.y, a.r * 2.5, 0.5, '255,200,90'); SFX.die();
    if (scored) { this.player.score += a.cfg.score; if (Math.random() < CFG.diff.dropChance) this.spawnPowerup(a.x, a.y); }
  }
  rockRock() {
    const rocks = [...this.rocks], dead = new Set();
    for (let i = 0; i < rocks.length; i++) {
      const a = rocks[i]; if (dead.has(a)) continue;
      for (let j = i + 1; j < rocks.length; j++) {
        const b = rocks[j]; if (dead.has(b) || !this.world.overlap(a, b) || a.cooldown > 0 || b.cooldown > 0) continue;
        const [dx, dy] = this.world.delta(a.x, a.y, b.x, b.y), d = Math.hypot(dx, dy) || 1;
        if ((b.vx - a.vx) * dx / d + (b.vy - a.vy) * dy / d >= 0) continue;    // already moving apart
        dead.add(a); dead.add(b); this.breakRock(a); this.breakRock(b); break;
      }
    }
  }
  shipRock() {
    for (const p of this.players.filter(p => p.alive)) for (const r of [...this.rocks]) {
      if (r.cooldown > 0 || !this.rocks.includes(r) || !this.world.overlap(p.ship, r)) continue;
      if (p.ship.shield > 0) { p.score += 25; this.breakRock(r, true); }           // ram while invincible
      else if (this.damagePlayer(p, CFG.ship.hitDamage, r.x, r.y)) this.breakRock(r, true);
      if (!p.alive) break;
    }
  }
  bulletHits() {
    for (const b of [...this.bullets]) {
      const al = this.aliens.find(a => this.world.overlap(b, a));
      if (al) { al.hit(b.dmg); if (al.health <= 0) this.killAlien(al); b.life = 0; continue; }
      const rk = this.rocks.find(r => this.world.overlap(b, r));
      if (rk) { this.player.score += 10 * rk.size; this.breakRock(rk, false); b.life = 0; }
    }
    this.bullets = this.bullets.filter(b => b.life > 0);
  }
  alienHits() {
    for (const a of [...this.aliens]) {
      for (const p of this.players.filter(p => p.alive)) {
        if (!this.world.overlap(a, p.ship)) continue;
        if (p.ship.shield > 0) { a.hit(60); if (a.health <= 0) this.killAlien(a); }
        else if (a.ramCd <= 0 && this.damagePlayer(p, a.cfg.contact, a.x, a.y)) { a.ramCd = 1; if (a.kind === 'chaser') this.killAlien(a, false); }
        if (!this.aliens.includes(a)) break;
      }
      if (!this.aliens.includes(a)) continue;
      const rk = this.rocks.find(r => r.cooldown <= 0 && this.world.overlap(a, r));
      if (rk) { this.breakRock(rk); a.hit(CFG.rocks.alienDamage); if (a.health <= 0) this.killAlien(a, false); }
    }
  }
  updatePowerups(dt) {
    if ((this.powerupTimer -= dt) <= 0) { this.spawnPowerup(); this.powerupTimer = this.powerupInterval() * rand(0.8, 1.2); }
    for (const pu of [...this.powerups]) {
      pu.update(dt); if (pu.expired) { this.powerups.splice(this.powerups.indexOf(pu), 1); continue; }
      for (const p of this.players.filter(p => p.alive)) if (this.world.dist(pu, p.ship) < pu.r + p.ship.r) {
        const s = p.ship, T = CFG.timing;
        if (pu.kind === 'health') s.health = Math.min(s.maxHealth, s.health + CFG.ship.healthGain);
        else if (pu.kind === 'speed') s.boost = T.boost; else if (pu.kind === 'ammo') p.addAmmo(); else s.shield = T.invincible;
        p.score += 50; SFX.power(); this.powerups.splice(this.powerups.indexOf(pu), 1); break;
      }
    }
  }
  updateWormhole(dt) {
    const wh = this.wormhole;
    if (!wh) { if ((this.wormholeTimer -= dt) <= 0) { const [x, y] = this.farPos(250); this.wormhole = new Wormhole(x, y, Math.sqrt(this.scale)); } return; }
    wh.update(dt);
    if (wh.expired) { this.wormhole = null; this.wormholeTimer = rand(CFG.timing.whMin, CFG.timing.whMax); }
    else if (wh.canEnter && this.players.some(p => p.alive && this.world.dist(wh, p.ship) < wh.full)) this.completeLevel();
  }
  completeLevel() {
    SFX.wormhole(); this.players.forEach(p => p.score += 200 * this.level);
    this.level++; this.bank(); this.startLevel();
  }

  // ------------------------------------------------------------------ drawing
  sprite(name, x, y, angle = 0, scale = 1, alpha = 1) {
    const im = this.img[name], g = this.ctx; g.save(); g.globalAlpha = alpha;
    g.translate(x, this.world.h - y); g.rotate(rad(angle)); g.scale(scale, scale); g.drawImage(im, -im.width / 2, -im.height / 2); g.restore();
  }
  draw() {
    const g = this.ctx, w = this.world;
    g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#060816'; g.fillRect(0, 0, W, H);
    g.save(); g.translate(W / 2, H / 2); g.scale(this.zoom, this.zoom); g.translate(-w.w / 2, -w.h / 2);
    g.strokeStyle = 'rgba(90,120,200,.35)'; g.lineWidth = 2 / this.zoom; g.strokeRect(0, 0, w.w, w.h);
    for (const [x, y, b] of this.stars) { g.fillStyle = `rgb(${b},${b},${Math.min(255, b + 20)})`; g.fillRect(x, w.h - y, 2 / this.zoom + 0.5, 2 / this.zoom + 0.5); }
    if (this.wormhole) { const wh = this.wormhole; this.sprite('wormhole', wh.x, wh.y, wh.angle, 1.2 * wh.grow); }
    for (const pu of this.powerups) this.sprite(pu.kind, pu.x, pu.y, 0, 1 + 0.12 * Math.sin(pu.age * 5), pu.life < 2 && Math.floor(pu.life * 6) % 2 === 0 ? 0.45 : 1);
    for (const r of this.rocks) this.sprite('rock', r.x, r.y, r.angle, r.scale);
    for (const a of this.aliens) {
      this.sprite(a.kind, a.x, a.y, a.angle, a.scale, a.flash > 0 && Math.floor(a.flash * 40) % 2 === 0 ? 0.55 : 1);
      if (a.health < a.maxHealth) { const bw = Math.max(30, a.r * 2), bx = a.x - bw / 2, by = w.h - (a.y + a.r + 8) - 5;
        g.fillStyle = '#3c1414'; g.fillRect(bx, by, bw, 5); g.fillStyle = COLORS.red; g.fillRect(bx, by, bw * Math.max(0, a.health / a.maxHealth), 5); }
    }
    for (const b of this.bullets) this.sprite('bullet', b.x, b.y, b.angle);
    for (const p of this.players.filter(p => p.alive)) {
      const s = p.ship; this.sprite('ship', s.x, s.y, s.bearing, 1, s.grace > 0 && Math.floor(s.grace * 12) % 2 === 0 ? 0.43 : 1);
      if (s.shield > 0) { g.beginPath(); g.arc(s.x, w.h - s.y, s.r + 12, 0, 7); g.strokeStyle = COLORS.cyan; g.lineWidth = 3 / this.zoom; g.stroke(); }
    }
    for (const e of this.effects) { const k = e.age / e.dur, r = e.r * (0.3 + 0.7 * k); g.beginPath(); g.arc(e.x, w.h - e.y, r, 0, 7);
      g.strokeStyle = `rgba(${e.color},${1 - k})`; g.lineWidth = 3 / this.zoom; g.stroke(); g.fillStyle = `rgba(${e.color},${(1 - k) / 4})`; g.fill(); }
    g.restore();
    if (this.state !== 'menu') this.hud();
  }
  hud() {
    const g = this.ctx, p = this.player, s = p.ship;
    const bar = (x, y, bw, bh, f, c) => { g.fillStyle = '#282c3e'; g.fillRect(x, y, bw, bh); g.fillStyle = c; g.fillRect(x, y, bw * Math.max(0, Math.min(1, f)), bh); g.strokeStyle = '#fff'; g.lineWidth = 2; g.strokeRect(x, y, bw, bh); };
    const text = (t, x, y, c = COLORS.white, size = 14, align = 'left') => { g.font = `${size}px "Courier New", monospace`; g.fillStyle = c; g.textAlign = align; g.fillText(t, x, y); };
    bar(20, 20, 240, 16, s.health / s.maxHealth, s.health / s.maxHealth > 0.35 ? COLORS.green : COLORS.red); text('HEALTH', 270, 33, COLORS.grey, 12);
    bar(20, 44, 240, 12, s.speed / (CFG.ship.maxSpeed * (s.boost > 0 ? CFG.ship.boost : 1)), COLORS.orange); text('SPEED', 270, 55, COLORS.grey, 12);
    let y = 80; if (s.boost > 0) { text(`SPEED BOOST ${s.boost.toFixed(1)}s`, 20, y, COLORS.orange); y += 20; }
    if (s.shield > 0) text(`INVINCIBLE ${s.shield.toFixed(1)}s`, 20, y, COLORS.cyan);
    text(`SCORE ${Math.floor(p.score)}`, W - 20, 36, COLORS.white, 18, 'right'); text(`LEVEL ${this.level}   AREA x${this.scale.toFixed(2)}`, W - 20, 60, COLORS.gold, 14, 'right');
    if (this.wormhole) text(`WORMHOLE OPEN  ${Math.max(0, this.wormhole.life - this.wormhole.age).toFixed(1)}s`, W / 2, 30, '#c896ff', 16, 'center');
    let x = 20;
    for (const [slot, w] of Object.entries(WEAPONS)) {
      const ok = p.unlocked(slot, this.level), sel = +slot === p.slot, ammo = p.ammo[slot];
      g.fillStyle = ok ? '#1c2038' : '#141622'; g.fillRect(x, H - 56, 112, 44); g.strokeStyle = sel ? COLORS.gold : COLORS.grey; g.lineWidth = sel ? 3 : 1; g.strokeRect(x, H - 56, 112, 44);
      const c = ok && ammo === 0 ? COLORS.red : ok ? COLORS.white : COLORS.grey;
      text(`${slot} ${w.name}`, x + 6, H - 34, c, 12); text(!ok ? `unlocks L${w.unlock}` : ammo < 0 ? 'ammo: inf' : `ammo: ${ammo}`, x + 6, H - 20, c, 11); x += 118;
    }
    if (this.noticeT > 0) text(this.notice, W / 2, H - 80, COLORS.white, 16, 'center');
    if (this.banner > 0) { text(`LEVEL ${this.level}`, W / 2, H / 2 - 120, COLORS.gold, 40, 'center'); text(this.bannerSub, W / 2, H / 2 - 85, COLORS.grey, 14, 'center'); }
  }
}
