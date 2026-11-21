import { CFG, WEAPONS } from '../config.js';
import { rad, rand } from '../utils.js';

export class Bullet {
  constructor(x, y, vx, vy, dmg, life) { this.x = x; this.y = y; this.vx = vx; this.vy = vy; this.dmg = dmg; this.life = life; this.r = 10; this.angle = Math.atan2(vx, vy) * 180 / Math.PI; }
  update(dt, world) { this.x += this.vx * dt; this.y += this.vy * dt; world.wrap(this); this.life -= dt; }
}
/** Builds the bullets for one shot (weapons.py WeaponSystem.fire, bolt types). */
export function fire(ship, slot, mult = 1) {
  const w = WEAPONS[slot], out = [], [svx, svy] = ship.velocity(), nose = ship.r + 14;
  for (let i = 0; i < w.count; i++) {
    const off = w.count === 1 ? 0 : -w.spread / 2 + w.spread * i / (w.count - 1), a = rad(ship.bearing + off);
    const bx = Math.sin(a), by = Math.cos(a);
    out.push(new Bullet(ship.x + bx * nose, ship.y + by * nose, bx * w.speed + svx, by * w.speed + svy, w.dmg * mult, w.range / w.speed));
  }
  return out;
}
export const POWERUPS = ['speed', 'health', 'shield', 'ammo'];
export class PowerUp {
  constructor(kind, x, y) { this.kind = kind; this.x = x; this.y = y; this.r = 16; this.life = CFG.timing.powerupLife; this.age = 0; }
  update(dt) { this.age += dt; this.life -= dt; }
  get expired() { return this.life <= 0; }
}
export class Wormhole {
  static FADE = 0.7;
  constructor(x, y, lifeScale) { this.x = x; this.y = y; this.life = CFG.timing.whLife * lifeScale; this.age = 0; this.angle = 0; this.full = 0.5 * 128 * 1.2 * 0.45; }
  get grow() { return Math.max(0.01, Math.min(1, this.age / Wormhole.FADE, (this.life - this.age) / Wormhole.FADE)); }
  update(dt) { this.age += dt; this.angle += 40 * dt; }
  get expired() { return this.age >= this.life; }
  get canEnter() { return this.grow >= 0.6; }
}
