import { settings } from '../config.js';
import { rand, pick, rad, deg } from '../utils.js';
import { Sprite } from './sprite.js';

/** Friendly ships. Each kind writes its own think(); the base class does the shared work. */
export class Ally extends Sprite {
  static kind = 'wingman';
  constructor(x, y, life = null) {
    const kind = new.target.kind, cfg = { ...settings.get(`allies.${kind}`) };
    super(`ally_${kind}`); this.kind = kind; this.cfg = cfg; this.maxHealth = +cfg.health; this.health = this.maxHealth; this.speed = +(cfg.speed || 0);
    this.r = 0.5 * Math.min(this.w, this.h) * 0.6; this.vx = this.vy = 0; this.fireTimer = rand(0, .5); this.at = rand(0, 10); this.life = life; this.home = [x, y]; this.x = x; this.y = y;
  }
  steerTo(ctx, tx, ty) {
    const [dx, dy] = ctx.world.delta(this.x, this.y, tx, ty), d = Math.hypot(dx, dy) || 1, s = Math.min(this.speed, d * 3);
    this.vx = dx / d * s; this.vy = dy / d * s;
  }
  nearestAlien(ctx, reach) {
    let best = null, bd = reach;
    for (const a of ctx.aliens) { if (a.dead) continue; const [dx, dy] = ctx.world.delta(this.x, this.y, a.x, a.y), d = Math.hypot(dx, dy); if (d < bd) { best = [dx, dy]; bd = d; } }
    return best;
  }
  shootNearest(ctx) {
    const t = this.nearestAlien(ctx, +(this.cfg.range || 600));
    if (t) { const aim = deg(Math.atan2(t[0], t[1])); this.angle = aim; if (this.fireTimer <= 0) { this.fireTimer = +this.cfg.fire_interval; ctx.fireAllyBullet(this, aim); } return true; }
    if (this.vx || this.vy) this.angle = deg(Math.atan2(this.vx, this.vy));
    return false;
  }
  think() {}
  update(dt, ctx) {
    this.at += dt; this.fireTimer = Math.max(0, this.fireTimer - dt);
    if (this.life !== null && (this.life -= dt) <= 0) { this.dead = true; return; }
    this.think(dt, ctx); this.x += this.vx * dt; this.y += this.vy * dt; ctx.world.wrap(this); this.animate(dt);
  }
}
export class Wingman extends Ally {
  static kind = 'wingman';
  think(dt, ctx) { const s = ctx.refShip(), a = rad(this.at * 40); this.steerTo(ctx, s.x + Math.sin(a) * 150, s.y + Math.cos(a) * 150); this.shootNearest(ctx); }
}
export class RepairDrone extends Ally {
  static kind = 'repair';
  think(dt, ctx) {
    const s = ctx.refShip(), a = rad(this.at * 70); this.steerTo(ctx, s.x + Math.sin(a) * 90, s.y + Math.cos(a) * 90); this.angle += 60 * dt;
    for (const p of ctx.alivePlayers()) if (ctx.world.dist(this, p.ship) < this.cfg.heal_range) p.ship.health = Math.min(p.ship.maxHealth, p.ship.health + this.cfg.heal_rate * dt);
  }
}
export class PatrolCutter extends Ally {
  static kind = 'cutter';
  think(dt, ctx) { const a = rad(this.at * 25), r = +this.cfg.patrol_radius; this.steerTo(ctx, this.home[0] + Math.sin(a) * r, this.home[1] + Math.cos(a) * r); this.shootNearest(ctx); }
}
export class Trader extends Ally {
  static kind = 'trader';
  constructor(...a) { super(...a); this.base = rad(pick([45, 135, 225, 315])); }
  think() { const bx = Math.sin(this.base), by = Math.cos(this.base), w = 40 * Math.cos(0.8 * this.at); this.vx = bx * this.speed - by * w; this.vy = by * this.speed + bx * w; this.angle = deg(Math.atan2(this.vx, this.vy)); }
}
export class Stranded extends Ally {
  static kind = 'stranded';
  think(dt) { this.vx = this.vy = 0; this.angle += 20 * dt; this.alpha = Math.floor(this.at * 3) % 2 ? 0.5 : 1; }
}
export const ALLY_CLASSES = { wingman: Wingman, repair: RepairDrone, cutter: PatrolCutter, trader: Trader, stranded: Stranded };
