import { settings } from '../config.js';
import { rand, pick, rad, deg, angDiff } from '../utils.js';
import { Sprite } from './sprite.js';

/** Alien ships. Each type has its own movement + AI in think(); update() is shared. */
export class Alien extends Sprite {
  static kind = 'drifter'; facesHeading = true; needsTarget = true; detectRange = 0;
  constructor(x, y, level, overrides) {
    const kind = new.target.kind, cfg = { ...settings.get(`aliens.${kind}`), ...(overrides || {}) };
    super(`alien_${kind}`);
    this.kind = kind; this.cfg = cfg;
    const grow = 1 + settings.get('difficulty.alien_health_per_level') * Math.max(0, level - cfg.min_level);
    this.maxHealth = cfg.health * grow; this.health = this.maxHealth; this.speed = +cfg.speed;
    this.r = 0.5 * Math.min(this.w, this.h) * 0.75; this.vx = this.vy = 0; this.heading = rand(0, 360); this.at = rand(0, 10);
    const iv = +(cfg.fire_interval || 0); this.fireTimer = iv > 0 ? rand(0.5, Math.max(0.6, iv)) : 1e9;
    this.flash = 0; this.ramCd = 0; this.minion = false; this.charging = false; this.target = null; this.x = x; this.y = y;
  }
  toShip(ctx) { const [dx, dy] = ctx.world.delta(this.x, this.y, this.target.x, this.target.y); return [dx, dy, Math.hypot(dx, dy)]; }
  takeDamage(a) { this.health -= a; this.flash = 0.15; }
  setVelocityToward(dx, dy, speed) { const d = Math.hypot(dx, dy) || 1; this.vx = dx / d * speed; this.vy = dy / d * speed; }
  think() {}
  wander(dt) {                                   // nothing to chase (everyone hidden): drift about
    this.charging = false; this.heading = (this.heading + rand(-40, 40) * dt + 360) % 360;
    this.vx = Math.sin(rad(this.heading)) * this.speed * 0.5; this.vy = Math.cos(rad(this.heading)) * this.speed * 0.5;
  }
  update(dt, ctx) {
    this.at += dt; this.target = ctx.nearestShip(this.x, this.y, this);
    if (!this.target && this.needsTarget) this.wander(dt); else this.think(dt, ctx);
    this.x += this.vx * dt; this.y += this.vy * dt; ctx.world.wrap(this);
    this.ramCd = Math.max(0, this.ramCd - dt); this.flash = Math.max(0, this.flash - dt);
    if (this.facesHeading && (this.vx || this.vy)) this.angle = deg(Math.atan2(this.vx, this.vy));
    const hit = this.flash > 0 && Math.floor(this.flash * 40) % 2 === 0, chg = this.charging && Math.floor(this.at * 20) % 2 === 0;
    this.alpha = hit || chg ? 0.55 : 1; this.animate(dt);
  }
}
export class Drifter extends Alien {
  static kind = 'drifter'; facesHeading = false; needsTarget = false;
  constructor(...a) { super(...a); this.base = rad(pick([45, 135, 225, 315])); }
  think(dt) {
    const c = this.cfg, bx = Math.sin(this.base), by = Math.cos(this.base), wob = c.wave_amp * c.wave_freq * Math.cos(c.wave_freq * this.at);
    this.vx = bx * this.speed - by * wob; this.vy = by * this.speed + bx * wob; this.angle += 30 * dt;
  }
}
export class Chaser extends Alien {
  static kind = 'chaser';
  think(dt, ctx) {
    const [dx, dy] = this.toShip(ctx), turn = this.cfg.turn_rate * dt;
    this.heading += Math.max(-turn, Math.min(turn, angDiff(deg(Math.atan2(dx, dy)), this.heading)));
    this.vx = Math.sin(rad(this.heading)) * this.speed; this.vy = Math.cos(rad(this.heading)) * this.speed;
  }
}
export class Sniper extends Alien {
  static kind = 'sniper'; facesHeading = false;
  constructor(...a) { super(...a); this.strafe = pick([-1, 1]); this.strafeT = rand(2, 4); }
  think(dt, ctx) {
    const [dx, dy, dist] = this.toShip(ctx), ux = dist ? dx / dist : 0, uy = dist ? dy / dist : 1, keep = this.cfg.keep_distance;
    const radial = dist > keep + 40 ? 1 : dist < keep - 40 ? -1 : 0;
    if ((this.strafeT -= dt) <= 0) { this.strafe = -this.strafe; this.strafeT = rand(2, 4); }
    this.setVelocityToward(ux * radial - uy * this.strafe * 0.7, uy * radial + ux * this.strafe * 0.7, this.speed);
    this.angle = deg(Math.atan2(dx, dy));
    this.fireTimer -= dt; this.charging = this.fireTimer < 0.4;
    if (this.fireTimer <= 0) {
      this.fireTimer = this.cfg.fire_interval;
      const t = dist / Math.max(1, this.cfg.bullet_speed), [svx, svy] = this.target.velocity();      // lead the target
      ctx.fireAlienBullet(this, deg(Math.atan2(dx + svx * t, dy + svy * t)));
    }
  }
}
export class Swarm extends Alien {
  static kind = 'swarm'; facesHeading = false;
  constructor(x, y, level, slot = 0, group = 1, phase = 0, overrides) { super(x, y, level, overrides); this.slot = slot; this.group = Math.max(1, group); this.phase = phase; }
  think(dt, ctx) {
    const c = this.cfg, ang = rad(c.orbit_speed * ctx.time + this.phase + this.slot * 360 / this.group), [dx, dy] = this.toShip(ctx);
    const tx = dx + Math.sin(ang) * c.orbit_radius, ty = dy + Math.cos(ang) * c.orbit_radius;
    this.setVelocityToward(tx, ty, Math.min(this.speed, Math.hypot(tx, ty) * 3)); this.angle = deg(Math.atan2(dx, dy));
    if ((this.fireTimer -= dt) <= 0) { this.fireTimer = c.fire_interval * rand(0.8, 1.3); ctx.fireAlienBullet(this, deg(Math.atan2(dx, dy))); }
  }
}
export class Mothership extends Alien {
  static kind = 'mothership'; facesHeading = false;
  constructor(...a) { super(...a); this.spawnT = +this.cfg.spawn_interval; this.volley = 0; this.ringOffset = 0; }
  think(dt, ctx) {
    const [dx, dy, dist] = this.toShip(ctx), keep = this.cfg.keep_distance, radial = dist > keep + 60 ? 1 : dist < keep - 60 ? -1 : 0;
    this.setVelocityToward(dx, dy, this.speed * radial); this.angle += 12 * dt;
    if ((this.spawnT -= dt) <= 0) { this.spawnT = this.cfg.spawn_interval; ctx.spawnMinion(this); }
    if ((this.fireTimer -= dt) <= 0) {
      this.fireTimer = this.cfg.fire_interval; this.volley++; const aim = deg(Math.atan2(dx, dy));
      if (this.volley % 2) for (const off of [-14, 0, 14]) ctx.fireAlienBullet(this, aim + off, off === 0);        // aimed triple burst
      else { const n = Math.max(3, this.cfg.ring_bullets | 0); this.ringOffset += 11; for (let i = 0; i < n; i++) ctx.fireAlienBullet(this, this.ringOffset + i * 360 / n, i === 0); }   // rotating ring
    }
  }
}
export class Seeker extends Alien {
  static kind = 'seeker'; facesHeading = false;
  constructor(...a) { super(...a); this.detectRange = +this.cfg.detect_range; this.locked = false; }
  wander(dt) { super.wander(dt); this.locked = false; this.angle += 90 * dt; }
  think(dt, ctx) {
    const [dx, dy, dist] = this.toShip(ctx); this.locked = true; const wanted = deg(Math.atan2(dx, dy)), turn = 200 * dt;
    this.heading += Math.max(-turn, Math.min(turn, angDiff(wanted, this.heading)));
    const boost = dist < 500 ? 1.4 : 1;
    this.vx = Math.sin(rad(this.heading)) * this.speed * boost; this.vy = Math.cos(rad(this.heading)) * this.speed * boost; this.angle = this.heading;
    this.fireTimer -= dt; this.charging = this.fireTimer < 0.4;
    if (this.fireTimer <= 0) { this.fireTimer = this.cfg.fire_interval; ctx.fireAlienBullet(this, wanted); }
  }
}
export class Teleporter extends Alien {
  static kind = 'teleporter'; facesHeading = false;
  constructor(...a) { super(...a); this.blinkT = rand(1.5, +this.cfg.blink_interval); this.burstLeft = 0; this.burstT = 0; }
  think(dt, ctx) {
    const [dx, dy, dist] = this.toShip(ctx); this.setVelocityToward(dx, dy, dist > 200 ? this.speed : 0); this.angle = deg(Math.atan2(dx, dy));
    this.blinkT -= dt; this.charging = this.blinkT > 0 && this.blinkT < 0.6;
    if (this.blinkT <= 0) {                                   // blink to a spot on a ring around the target
      const a = rand(0, 2 * Math.PI), ring = this.cfg.ring * rand(0.8, 1.2);
      this.x = this.target.x + Math.sin(a) * ring; this.y = this.target.y + Math.cos(a) * ring; ctx.world.wrap(this);
      ctx.effectAt(this.x, this.y, this.r * 2.5, [200, 120, 255]); ctx.playSfx('teleporter_blink');
      this.blinkT = this.cfg.blink_interval * rand(0.8, 1.3); this.burstLeft = this.cfg.burst_count | 0; this.burstT = 0.3;
    }
    if (this.burstLeft > 0 && (this.burstT -= dt) <= 0) {
      this.burstLeft--; this.burstT = 0.18; const [bx, by] = this.toShip(ctx); ctx.fireAlienBullet(this, deg(Math.atan2(bx, by)));
    }
  }
}
export class Minelayer extends Alien {
  static kind = 'minelayer'; needsTarget = false;
  constructor(...a) { super(...a); this.dropT = +this.cfg.mine_interval; }
  think(dt, ctx) {
    this.heading = (this.heading + 25 * Math.sin(this.at * 0.7) * dt + 360) % 360;
    this.vx = Math.sin(rad(this.heading)) * this.speed; this.vy = Math.cos(rad(this.heading)) * this.speed;
    if ((this.dropT -= dt) <= 0) { this.dropT = +this.cfg.mine_interval; ctx.dropAlienMine(this); }
  }
}
export const ALIEN_CLASSES = { drifter: Drifter, chaser: Chaser, sniper: Sniper, swarm: Swarm, seeker: Seeker, teleporter: Teleporter, minelayer: Minelayer, mothership: Mothership };
