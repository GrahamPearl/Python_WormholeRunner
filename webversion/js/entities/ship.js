import { settings } from '../config.js';
import { rad, clamp } from '../utils.js';
import { Sprite } from './sprite.js';
import { WeaponSystem } from './weapons.js';

/** Turning and throttle (control_step in sprites.py). */
export function controlStep(bearing, speed, dt, k, boosted, m) {
  const g = p => settings.get(p), boost = boosted ? g('ship.boost_multiplier') : 1;
  if (k.left) bearing -= g('ship.turn_rate') * m[2] * dt;
  if (k.right) bearing += g('ship.turn_rate') * m[2] * dt;
  if (k.up) speed += g('ship.acceleration') * m[1] * boost * dt;
  if (k.down) speed -= g('ship.acceleration') * m[1] * boost * 1.5 * dt;
  speed = Math.max(0, Math.min(speed, g('ship.max_speed') * m[0] * boost));
  return [((bearing % 360) + 360) % 360, speed];
}

export class Ship extends Sprite {
  constructor(cfg, tint) {
    cfg = cfg || settings.get('ships.scout');
    super(cfg.graphic || 'ship');
    if (tint) this.tint = tint;
    this.cfg = cfg; this.r = 0.5 * Math.min(this.w, this.h) * 0.55;
    this.maxHealth = +cfg.health || settings.get('ship.max_health'); this.health = this.maxHealth;
    this.speedMult = cfg.speed_mult ?? 1; this.accelMult = cfg.accel_mult ?? 1; this.turnMult = cfg.turn_mult ?? 1;
    this.bearing = 0; this.speed = 0; this.driftX = this.driftY = 0;
    this.grace = this.shieldT = this.boost = 0;                          // grace: after a hit; shieldT: invincibility power-up; boost: speed
    this.ability = { ...(cfg.ability || {}) }; this.abilityType = this.ability.type || ''; this.abilityCd = 0; this.active = 0;
    const p = cfg.passive || {};
    this.shieldMax = +p.shield_max || 0; this.shieldHp = this.shieldMax; this.shieldRate = +p.shield_rate || 0; this.shieldDelay = +p.shield_delay || 0; this.shieldWait = 0;
    this.regen = +p.regen || 0; this.regenDelay = p.regen_delay ?? 2; this.sinceHit = 99; this.inNebula = false; this.jammed = false;
  }
  on(kind) { return this.abilityType === kind && this.active > 0; }
  get cloaked() { return this.on('cloak'); } get phased() { return this.on('hyperspace'); } get deflecting() { return this.on('deflect'); }
  get healing() { return this.on('repair'); } get timeslip() { return this.on('timeslip'); }
  get mults() { return [this.speedMult, this.accelMult, this.turnMult]; }
  get invulnerable() { return this.grace > 0 || this.shieldT > 0; }
  velocity() { const a = rad(this.bearing); return [Math.sin(a) * this.speed + this.driftX, Math.cos(a) * this.speed + this.driftY]; }
  update(dt, k, ax, ay, world) {
    [this.bearing, this.speed] = controlStep(this.bearing, this.speed, dt, k, this.boost > 0, this.mults);
    this.driftX += ax * dt; this.driftY += ay * dt;                        // gravity changes the drift, which fades
    const damp = Math.max(0, 1 - settings.get('physics.drift_damping') * dt); this.driftX *= damp; this.driftY *= damp;
    const [vx, vy] = this.velocity(); this.x += vx * dt; this.y += vy * dt; world.wrap(this);
    this.angle = this.bearing;
    for (const f of ['grace', 'shieldT', 'boost', 'active']) this[f] = Math.max(0, this[f] - dt);
    this.sinceHit += dt;
    if (!this.jammed) {                                                    // ion storms stop all recharging
      this.abilityCd = Math.max(0, this.abilityCd - dt); this.shieldWait = Math.max(0, this.shieldWait - dt);
      if (this.shieldMax > 0 && this.shieldWait <= 0) this.shieldHp = Math.min(this.shieldMax, this.shieldHp + this.shieldRate * dt);
      if (this.regen > 0 && this.sinceHit >= this.regenDelay) this.health = Math.min(this.maxHealth, this.health + this.regen * dt);
    }
    this.alpha = this.grace > 0 && Math.floor(this.grace * 12) % 2 === 0 ? 0.43 : 1;
    if (this.cloaked) this.alpha = 0.4; else if (this.phased) this.alpha = 0.27;
    this.animate(dt);
  }
}

const TINTS = { 1: null, 2: '#82ffa0' };
export class Player {
  constructor(id = 1, name = 'Pilot', local = true, shipId = 'scout') {
    this.id = id; this.name = name; this.local = local;
    this.shipId = settings.get(`ships.${shipId}`) ? shipId : 'scout'; this.abilityPrev = false; this.reset();
  }
  reset() {
    const cfg = settings.get(`ships.${this.shipId}`), p = cfg.passive || {};
    this.ship = new Ship(cfg, TINTS[this.id]);
    this.weapons = new WeaponSystem(cfg.weapon && cfg.weapon.name ? { 7: cfg.weapon } : null);
    this.score = 0; this.creditsRun = 0; this.alive = true; this.perks = {}; this.perkOptions = []; this.perkChoice = 0;
    this.dmgMult = 1; this.cdMult = 1; this.creditMult = 1 + (+p.credit_bonus || 0); this.magnet = +p.magnet || 0;
  }
  revive() { this.alive = true; this.ship.health = Math.max(this.ship.health, this.ship.maxHealth * 0.5); this.ship.grace = 1.5; }
}
export { clamp };
