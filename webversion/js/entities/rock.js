import { settings, ROCK_SIZE_SCALE, ROCK_TINTS } from '../config.js';
import { rand, rad } from '../utils.js';
import { Sprite } from './sprite.js';

export class Rock extends Sprite {
  constructor(size, x, y, vx, vy, kind = 'normal') {
    super('rock', ROCK_SIZE_SCALE[size]);
    this.kind = kind; this.hp = kind === 'metal' ? 3 : 1; this.tint = ROCK_TINTS[kind] || null;
    this.size = size; this.mass = ROCK_SIZE_SCALE[size] ** 2;                 // bigger rock, stronger pull
    this.r = 0.5 * Math.min(this.w, this.h) * 0.8; this.vx = vx; this.vy = vy; this.spin = rand(-50, 50); this.cooldown = 0; this.x = x; this.y = y;
  }
  update(dt, world) { this.x += this.vx * dt; this.y += this.vy * dt; world.wrap(this); this.angle += this.spin * dt; this.cooldown = Math.max(0, this.cooldown - dt); this.animate(dt); }
  split() {                                       // smaller rocks (none for the smallest). Ice shatters into three.
    if (this.size <= 1) return [];
    const ang = settings.get('rocks.split_angle'), f = settings.get('rocks.split_speed'), kids = [];
    for (const off of this.kind === 'ice' ? [ang, 0, -ang] : [ang, -ang]) {
      const a = rad(off), c = Math.cos(a), s = Math.sin(a), vx = this.vx * c - this.vy * s, vy = this.vx * s + this.vy * c, len = Math.hypot(vx, vy) || 1;
      const k = new Rock(this.size - 1, this.x + vx / len * this.r * 0.5, this.y + vy / len * this.r * 0.5, vx * f, vy * f, this.kind === 'ice' ? 'ice' : 'normal');
      k.cooldown = 0.6; kids.push(k);
    }
    return kids;
  }
}
/** Pull toward a rock: grows with mass, falls with distance squared (physics.py). */
export function gravityAccel(dx, dy, mass, strength, soft, cap) {
  const d2 = dx * dx + dy * dy + soft * soft, d = Math.sqrt(d2), a = Math.min(strength * mass / d2, cap);
  return [a * dx / d, a * dy / d];
}
