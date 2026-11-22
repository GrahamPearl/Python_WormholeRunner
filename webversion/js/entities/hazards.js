import { rand } from '../utils.js';

/** Map hazards (Expedition and zones). Plain data; the game applies their effects. */
export class Hazard {
  static kind = 'hazard';
  constructor(x, y, radius) { this.kind = new.target.kind; this.x = x; this.y = y; this.radius = radius; this.vx = this.vy = 0; this.core = 0; }
  update(dt, world) { this.x = ((this.x + this.vx * dt) % world.w + world.w) % world.w; this.y = ((this.y + this.vy * dt) % world.h + world.h) % world.h; }
}
export class BlackHole extends Hazard { static kind = 'blackhole'; constructor(x, y) { super(x, y, 650); this.core = 34; } }
export class Nebula extends Hazard { static kind = 'nebula'; constructor(x, y) { super(x, y, rand(200, 300)); this.vx = rand(-8, 8); this.vy = rand(-8, 8); } }
export class IonStorm extends Hazard { static kind = 'ion'; constructor(x, y) { super(x, y, rand(170, 230)); this.vx = rand(-18, 18); this.vy = rand(-18, 18); } }
export class SolarFlare {
  static WARN = 2.5; static ACTIVE = 0.8;
  constructor(world, thickness = 140) {
    this.kind = 'flare'; this.vertical = Math.random() < 0.5; this.thickness = thickness;
    if (this.vertical) { this.x = rand(0, world.w); this.y = world.h / 2; this.w = thickness; this.h = world.h; }
    else { this.x = world.w / 2; this.y = rand(0, world.h); this.w = world.w; this.h = thickness; }
    this.t = 0; this.fired = false;
  }
  get phase() { return this.t < SolarFlare.WARN ? 0 : 1; }
  get finished() { return this.t >= SolarFlare.WARN + SolarFlare.ACTIVE; }
  covers(world, x, y, pad = 0) { const [dx, dy] = world.delta(this.x, this.y, x, y); return Math.abs(this.vertical ? dx : dy) < this.thickness / 2 + pad; }
}
export const HAZARD_CLASSES = { nebula: Nebula, blackhole: BlackHole, ion: IonStorm };
