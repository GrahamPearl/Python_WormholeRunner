import { CFG, ROCK_SCALE } from '../config.js';
import { rand, rad } from '../utils.js';

export class Rock {
  constructor(size, x, y, vx, vy) {
    this.size = size; this.x = x; this.y = y; this.vx = vx; this.vy = vy;
    this.scale = ROCK_SCALE[size]; this.mass = this.scale ** 2;        // bigger rock, stronger pull
    this.r = 0.5 * 64 * this.scale * 0.8; this.angle = rand(0, 360); this.spin = rand(-50, 50); this.cooldown = 0;
  }
  update(dt, world) {
    this.x += this.vx * dt; this.y += this.vy * dt; world.wrap(this);
    this.angle += this.spin * dt; this.cooldown = Math.max(0, this.cooldown - dt);
  }
  split() {                                  // two smaller rocks; none for the smallest size
    if (this.size <= 1) return [];
    const R = CFG.rocks, kids = [];
    for (const off of [R.splitAngle, -R.splitAngle]) {
      const a = rad(off), c = Math.cos(a), s = Math.sin(a);
      const vx = this.vx * c - this.vy * s, vy = this.vx * s + this.vy * c, len = Math.hypot(vx, vy) || 1;
      const k = new Rock(this.size - 1, this.x + vx / len * this.r * 0.5, this.y + vy / len * this.r * 0.5, vx * R.splitSpeed, vy * R.splitSpeed);
      k.cooldown = 0.6; kids.push(k);
    }
    return kids;
  }
}

/** Newtonian-style pull toward a rock (physics.py): grows with mass, falls with distance squared. */
export function gravityAccel(dx, dy, mass, strength, soft, cap) {
  const d2 = dx * dx + dy * dy + soft * soft, d = Math.sqrt(d2), a = Math.min(strength * mass / d2, cap);
  return [a * dx / d, a * dy / d];
}
