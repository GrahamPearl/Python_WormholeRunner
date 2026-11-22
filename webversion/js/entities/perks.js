export const PERKS = {
  firepower: ['Firepower', '+20% weapon damage'], armor: ['Hull Plating', '+25 max health and repair 25'], engines: ['Overdrive Engines', '+12% speed and acceleration'],
  cooldown: ['Quick Cycle', 'Abilities recharge 20% faster'], magnet: ['Tractor Field', 'Pickups are drawn toward your ship'], scavenger: ['Scavenger', '+25% credits earned'],
  resupply: ['Resupply', 'Refill all ammunition now'], barrier: ['Barrier Cell', '+30 rechargeable shield'],
};
export function applyPerk(p, id) {
  const s = p.ship; p.perks[id] = (p.perks[id] || 0) + 1;
  if (id === 'firepower') p.dmgMult *= 1.2;
  else if (id === 'armor') { s.maxHealth += 25; s.health = Math.min(s.maxHealth, s.health + 25); }
  else if (id === 'engines') { s.speedMult *= 1.12; s.accelMult *= 1.12; }
  else if (id === 'cooldown') p.cdMult *= 0.8;
  else if (id === 'magnet') p.magnet += 170;
  else if (id === 'scavenger') p.creditMult *= 1.25;
  else if (id === 'resupply') { for (let k = 1; k <= 9; k++) { const a = +(p.weapons.cfg(k).ammo ?? -1); if (a > 0) p.weapons.ammo[k] = a; } }
  else if (id === 'barrier') { s.shieldMax += 30; s.shieldHp = Math.min(s.shieldMax, s.shieldHp + 30); s.shieldRate = s.shieldRate || 12; s.shieldDelay = s.shieldDelay || 3; }
}
