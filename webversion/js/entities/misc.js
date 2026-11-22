import { settings } from '../config.js';
import { rand, deg, rad } from '../utils.js';
import { Sprite } from './sprite.js';

/** Power-ups plus the objective items (crystal, pod) which never expire. */
export class PowerUp extends Sprite {
  constructor(kind, x, y, o = {}) {
    super(settings.get(`graphics.powerup_${kind}`) ? `powerup_${kind}` : `objective_${kind}`);
    this.kind = kind; this.permanent = !!o.permanent; this.vx = o.vx || 0; this.vy = o.vy || 0; this.r = 0.5 * Math.min(this.w, this.h);
    this.life = +settings.get('timing.powerup_lifetime'); this.age = 0; this.x = x; this.y = y;
  }
  update(dt, world) {
    this.age += dt;
    if (this.vx || this.vy) { this.x += this.vx * dt; this.y += this.vy * dt; if (world) world.wrap(this); }
    this.sc = this.baseSc * (1 + 0.12 * Math.sin(this.age * 5));
    if (this.permanent) this.alpha = 1; else { this.life -= dt; this.alpha = this.life < 2 && Math.floor(this.life * 6) % 2 === 0 ? 0.47 : 1; }
    this.animate(dt);
  }
  get expired() { return !this.permanent && this.life <= 0; }
}
/** The ship you escort (or the station you defend: speed 0). */
export class Freighter extends Sprite {
  constructor(x, y) {
    super('objective_freighter'); this.maxHealth = +settings.get('objectives.freighter_health'); this.health = this.maxHealth;
    this.r = 0.5 * Math.min(this.w, this.h) * 0.7; const d = Math.SQRT1_2 * 55; this.vx = Math.random() < .5 ? -d : d; this.vy = Math.random() < .5 ? -d : d; this.hitCd = 0; this.x = x; this.y = y;
  }
  update(dt, world) { this.x += this.vx * dt; this.y += this.vy * dt; world.wrap(this); this.hitCd = Math.max(0, this.hitCd - dt); this.angle = deg(Math.atan2(this.vx, this.vy)); }
}
export class Wormhole extends Sprite {
  static FADE = 0.7;
  constructor(x, y, lifeScale = 1) {
    super('wormhole'); this.full = 0.5 * Math.min(this.w, this.h) * 0.45; this.lifetime = +settings.get('timing.wormhole_lifetime') * lifeScale; this.age = 0; this.x = x; this.y = y; this.sc = this.baseSc * 0.01;
  }
  get grow() { return Math.max(0.01, Math.min(1, this.age / Wormhole.FADE, (this.lifetime - this.age) / Wormhole.FADE)); }
  update(dt) { this.age += dt; this.sc = this.baseSc * this.grow; this.angle += 40 * dt; this.animate(dt); }
  get expired() { return this.age >= this.lifetime; }
  get canEnter() { return this.grow >= 0.6; }
}
