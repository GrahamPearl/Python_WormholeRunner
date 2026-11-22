import { settings } from './config.js';
import { rad } from './utils.js';
import { profile } from './profile.js';
import { Bullet } from './entities/weapons.js';
import { ALLY_CLASSES } from './entities/ally.js';

/** Permanent upgrades bought at stations (upgrades.py). */
export function applyUpgrades(p, levels) {
  const s = p.ship;
  for (const [id, l] of Object.entries(levels)) {
    if (l <= 0) continue;
    if (id === 'hull') { s.maxHealth += 10 * l; s.health = s.maxHealth; }
    else if (id === 'engines') { s.speedMult *= 1 + 0.05 * l; s.accelMult *= 1 + 0.05 * l; }
    else if (id === 'guns') p.dmgMult *= 1 + 0.05 * l;
    else if (id === 'capacitor') p.cdMult *= 0.95 ** l;
    else if (id === 'tractor') p.magnet += 40 * l;
    else if (id === 'salvage') p.creditMult *= 1 + 0.05 * l;
  }
}

/** Voyage mode: zones, friendly ships, upgrades and the jump back to the star map (voyage.py). */
export const voyageMixin = {
  beginZoneRun() { this.contractWingman = !!this.zone && profile.useSupply('wingman'); this.ammoBonus = !!this.zone && profile.useSupply('ammo'); },
  prepareLocal(p) {                         // upgrades, carried-over hull and ammo packs (zones, local pilot only)
    if (!this.zone || !p.local) return;
    applyUpgrades(p, profile.upgrades); p.ship.health = Math.max(1, p.ship.maxHealth * profile.hull);
    if (this.ammoBonus) for (let k = 1; k <= 9; k++) if (p.weapons.ammo[k] > 0) p.weapons.ammo[k] = Math.floor(p.weapons.ammo[k] * 1.5);
  },
  spawnAlly(kind, x, y, life = null) { const a = new ALLY_CLASSES[kind](x, y, life); this.allies.push(a); return a; },
  spawnFriendlies() {
    if (!this.zone) return;
    const specs = [...(this.zone.friendlies || [])]; if (this.contractWingman) specs.push({ type: 'wingman', near: true });
    const [cx, cy] = this.world.center;
    for (const sp of specs) for (let n = 0; n < (sp.count || 1); n++) {
      const near = sp.near || sp.type === 'wingman' || sp.type === 'repair', [x, y] = near ? [cx + 60 + 40 * n, cy + 60] : this.farPos(300);
      this.spawnAlly(sp.type, x, y);
    }
  },
  fireAllyBullet(ally, bearing) {
    const a = rad(bearing), dx = Math.sin(a), dy = Math.cos(a), st = ally.r + 10;
    const b = new Bullet('bullet_w1', 'player', ally.x + dx * st, ally.y + dy * st, dx * 800, dy * 800, ally.cfg.damage, 1); b.playerId = this.local.id; this.bullets.push(b);
  },
  hurtAlly(ally, amount) {
    ally.health -= amount;
    if (ally.health <= 0 && !ally.dead) { this.addEffect(ally.x, ally.y, 60, 0.5, [120, 200, 255]); ally.dead = true; this.toast(`${ally.cfg.name} lost!`); this.sfx('ally_lost'); }
  },
  allyBulletHit(b) {
    for (const a of this.allies) if (!a.dead && this.overlap(b, a)) { b.dead = true; this.hurtAlly(a, b.damage); return true; }
    return false;
  },
  updateAllies(dt) {
    for (const a of this.allies) {
      if (a.dead) continue; a.update(dt, this); if (a.dead) continue;
      for (const r of this.rocks) if (!r.dead && r.cooldown <= 0 && this.overlap(a, r)) { this.breakRock(r); this.hurtAlly(a, 15); break; }    // rocks hurt allies too
      if (a.dead || a.kind !== 'stranded') continue;
      for (const p of this.alivePlayers()) if (this.overlap(a, p.ship)) {                                                                  // touch to rescue
        a.dead = true; this.spawnAlly('wingman', a.x, a.y); this.earn(p.id, settings.get('credits.rescue')); this.toast('Rescued! A wingman joins you.', 3); this.sfx('ally_rescued'); break;
      }
    }
  },
  saveHull() { if (this.zone) { const s = this.local.ship; profile.hull = Math.max(0.2, Math.min(1, s.health / s.maxHealth)); } },
  finishZone() {                            // the wormhole took us: pay out, remember progress, return to the star map
    const z = this.zone, o = this.objective, won = o.ok || o.type === 'none', reward = +(z.reward || 0);
    const traders = this.allies.filter(a => !a.dead && a.kind === 'trader').length, bonus = traders * +settings.get('allies.trader.bonus', 40);
    let message;
    if (won) {
      for (const p of this.players) this.earn(p.id, reward + bonus); profile.clearZone(this.zoneId);
      message = `${z.name} cleared!  +${Math.floor((reward + bonus) * this.local.creditMult)} credits` + (bonus ? `  (trader bonus +${bonus})` : '');
    } else message = `${z.name}: mission failed. You can try again.`;
    this.saveHull(); profile.location = this.zoneId; this.bank(); this.audio?.stopMusic(); this.setState('menu');
    this.hooks.zoneDone?.({ won, message, final: !!z.final, score: Math.floor(this.local.score) });
  },
};
