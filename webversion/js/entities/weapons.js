import { settings } from '../config.js';
import { rad, deg } from '../utils.js';
import { Sprite } from './sprite.js';

/** Every projectile. kind: 'bolt' flies straight, 'homing' steers, 'mine' sits still and explodes. */
export class Bullet extends Sprite {
  constructor(graphic, owner, x, y, vx, vy, damage, life, o = {}) {
    super(graphic);
    this.gfx = graphic; this.heal = 0; this.silent = false; this.playerId = 0; this.owner = owner;     // owner: 'player' | 'alien'
    this.vx = vx; this.vy = vy; this.damage = damage; this.life = life; this.pierce = Math.max(1, o.pierce | 0 || 1);
    this.kind = o.kind || 'bolt'; this.turnRate = o.turnRate || 0; this.blast = o.blast || 0; this.fuse = o.fuse || 0; this.arm = 0.5; this.hitIds = new Set();
    this.r = Math.max(4, 0.25 * (this.w + this.h)); this.x = x; this.y = y; this.point();
  }
  point() { if (this.kind !== 'mine' && (this.vx || this.vy)) this.angle = deg(Math.atan2(this.vx, this.vy)); }
  steer(dt, world, aliens, rocks) {
    let best = null, bd = 800;
    for (const group of [aliens, rocks]) {                  // prefer aliens, then rocks
      for (const t of group) { if (t.dead) continue; const [dx, dy] = world.delta(this.x, this.y, t.x, t.y), d = Math.hypot(dx, dy); if (d < bd) { best = [dx, dy]; bd = d; } }
      if (best) break;
    }
    if (!best) return;
    const speed = Math.hypot(this.vx, this.vy) || 1; let heading = Math.atan2(this.vx, this.vy);
    const wanted = Math.atan2(best[0], best[1]), diff = ((wanted - heading + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
    const lim = rad(this.turnRate) * dt; heading += Math.max(-lim, Math.min(lim, diff));
    this.vx = Math.sin(heading) * speed; this.vy = Math.cos(heading) * speed;
  }
  update(dt, world, aliens, rocks) {
    if (this.kind === 'mine') { this.fuse -= dt; this.arm -= dt; this.angle += 60 * dt; this.animate(dt); return; }
    if (this.kind === 'homing' && this.owner === 'player') this.steer(dt, world, aliens, rocks);
    this.x += this.vx * dt; this.y += this.vy * dt; world.wrap(this); this.life -= dt; this.point(); this.animate(dt);
  }
}

/** Weapon slots 1-9 (ammo, cooldown, unlock level). A ship's own weapon takes slot 7. */
export class WeaponSystem {
  constructor(overrides) {
    this.overrides = overrides || {}; this.slot = 1; this.cooldown = 0; this.ammo = {};
    for (let s = 1; s <= 9; s++) this.ammo[s] = +(this.cfg(s).ammo ?? -1);
  }
  cfg(slot) { return this.overrides[slot] || settings.get(`weapons.w${slot}`) || {}; }
  unlocked(slot, level) { const c = this.cfg(slot); return !!c.enabled && level >= (c.unlock_level || 1); }
  select(slot, level) { if (this.unlocked(slot, level)) { const ch = slot !== this.slot; this.slot = slot; return ch; } return false; }
  update(dt) { this.cooldown = Math.max(0, this.cooldown - dt); }
  addAmmo() { for (let s = 1; s <= 9; s++) { const c = this.cfg(s); if (c.ammo > 0) this.ammo[s] = Math.min(2 * c.ammo, this.ammo[s] + (c.ammo_pack || 0)); } }
  /** Returns [bullets, soundEvent]. Nothing is fired while cooling down. */
  fire(ship, dmgMult = 1) {
    const c = this.cfg(this.slot);
    if (this.cooldown > 0 || !c.name) return [[], null];
    if (this.ammo[this.slot] === 0) { this.cooldown = 0.3; return [[], 'no_ammo']; }
    if (this.ammo[this.slot] > 0) this.ammo[this.slot]--;
    this.cooldown = c.cooldown;
    const graphic = c.graphic || `bullet_w${this.slot}`, damage = c.damage * dmgMult, a = rad(ship.bearing), dx = Math.sin(a), dy = Math.cos(a), nose = ship.r + 14;
    const [svx, svy] = ship.velocity(), out = [];
    if (c.type === 'pulse') { const p = new Bullet(graphic, 'player', ship.x, ship.y, 0, 0, damage, 999, { kind: 'mine', blast: c.blast_radius, fuse: 0 }); p.arm = 0; out.push(p); }
    else if (c.type === 'mine') out.push(new Bullet(graphic, 'player', ship.x - dx * (nose + 16), ship.y - dy * (nose + 16), 0, 0, damage, 999, { kind: 'mine', blast: c.blast_radius, fuse: c.fuse }));
    else {
      const n = Math.max(1, c.count | 0), speed = Math.max(1, c.speed);
      for (let i = 0; i < n; i++) {
        const off = n === 1 ? 0 : -c.spread / 2 + c.spread * i / (n - 1), r = rad(ship.bearing + off), bx = Math.sin(r), by = Math.cos(r);
        out.push(new Bullet(graphic, 'player', ship.x + bx * nose, ship.y + by * nose, bx * speed + svx, by * speed + svy, damage, c.range / speed,
          { pierce: c.pierce, kind: c.type === 'homing' ? 'homing' : 'bolt', turnRate: c.turn_rate }));
      }
    }
    for (const b of out) { b.heal = c.heal || 0; b.silent = !!c.silent; }
    return [out, c.sound || null];
  }
}
