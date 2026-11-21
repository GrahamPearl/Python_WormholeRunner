import { CFG, WEAPONS } from '../config.js';
import { rad } from '../utils.js';

export class Ship {
  constructor() {
    this.r = 0.5 * 64 * 0.55;               // hit radius (sprites.py)
    this.maxHealth = CFG.ship.maxHealth; this.health = this.maxHealth;
    this.x = this.y = 0; this.bearing = 0; this.speed = 0;   // bearing: degrees clockwise from up
    this.driftX = this.driftY = 0;          // velocity added by gravity
    this.grace = this.shield = this.boost = 0;
  }
  velocity() { const a = rad(this.bearing); return [Math.sin(a) * this.speed + this.driftX, Math.cos(a) * this.speed + this.driftY]; }
  update(dt, keys, ax, ay, world) {
    const S = CFG.ship, b = this.boost > 0 ? S.boost : 1;
    if (keys.left) this.bearing -= S.turn * dt;
    if (keys.right) this.bearing += S.turn * dt;
    if (keys.up) this.speed += S.accel * b * dt;
    if (keys.down) this.speed -= S.accel * b * 1.5 * dt;
    this.speed = Math.max(0, Math.min(this.speed, S.maxSpeed * b));
    this.bearing = ((this.bearing % 360) + 360) % 360;
    this.driftX += ax * dt; this.driftY += ay * dt;                 // gravity changes the drift...
    const damp = Math.max(0, 1 - CFG.physics.damping * dt);        // ...which slowly fades away
    this.driftX *= damp; this.driftY *= damp;
    const [vx, vy] = this.velocity();
    this.x += vx * dt; this.y += vy * dt; world.wrap(this);
    for (const k of ['grace', 'shield', 'boost']) this[k] = Math.max(0, this[k] - dt);
  }
  get invulnerable() { return this.grace > 0 || this.shield > 0; }
}

/** One pilot: ship + weapons + score. Kept separate from Game so a second player can be added later. */
export class Player {
  constructor(id = 1) { this.id = id; this.keys = {}; this.reset(); }
  reset() {
    this.ship = new Ship(); this.score = 0; this.alive = true;
    this.slot = 1; this.cooldown = 0;
    this.ammo = Object.fromEntries(Object.entries(WEAPONS).map(([k, w]) => [k, w.ammo]));
  }
  unlocked(slot, level) { return WEAPONS[slot] && level >= WEAPONS[slot].unlock; }
  addAmmo() { for (const [k, w] of Object.entries(WEAPONS)) if (w.ammo > 0) this.ammo[k] = Math.min(2 * w.ammo, this.ammo[k] + w.pack); }
}
