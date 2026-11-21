import { ALIENS, CFG } from '../config.js';
import { rand, pick, rad, deg } from '../utils.js';

export class Alien {
  constructor(kind, x, y, level) {
    const c = this.cfg = ALIENS[kind]; this.kind = kind; this.x = x; this.y = y;
    this.maxHealth = c.health * (1 + CFG.diff.alienHealth * Math.max(0, level - c.minLevel)); this.health = this.maxHealth;
    this.speed = c.speed; this.r = 0.5 * 64 * c.scale * 0.75; this.scale = c.scale;
    this.vx = this.vy = 0; this.heading = rand(0, 360); this.t = rand(0, 10); this.angle = 0; this.ramCd = 0; this.flash = 0;
  }
  hit(dmg) { this.health -= dmg; this.flash = 0.15; }
  think() {}
  update(dt, game) {
    this.t += dt; this.think(dt, game);
    this.x += this.vx * dt; this.y += this.vy * dt; game.world.wrap(this);
    this.ramCd = Math.max(0, this.ramCd - dt); this.flash = Math.max(0, this.flash - dt);
  }
}
export class Drifter extends Alien {           // wanders along a sine-wave path, never shoots
  constructor(...a) { super('drifter', ...a); this.base = rad(pick([45, 135, 225, 315])); }
  think(dt) {
    const c = this.cfg, bx = Math.sin(this.base), by = Math.cos(this.base), wob = c.waveAmp * c.waveFreq * Math.cos(c.waveFreq * this.t);
    this.vx = bx * this.speed - by * wob; this.vy = by * this.speed + bx * wob; this.angle += 30 * dt;
  }
}
export class Chaser extends Alien {            // turns toward the ship at a limited rate, then rams it
  constructor(...a) { super('chaser', ...a); }
  think(dt, game) {
    const s = game.player.ship, [dx, dy] = game.world.delta(this.x, this.y, s.x, s.y);
    const diff = ((deg(Math.atan2(dx, dy)) - this.heading + 180) % 360 + 360) % 360 - 180, turn = this.cfg.turn * dt;
    this.heading += Math.max(-turn, Math.min(turn, diff));
    this.vx = Math.sin(rad(this.heading)) * this.speed; this.vy = Math.cos(rad(this.heading)) * this.speed;
    this.angle = this.heading;
  }
}
export const ALIEN_CLASSES = { drifter: Drifter, chaser: Chaser };
