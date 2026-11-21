// Constants copied from the Python settings (game/config.py, constants.py).
export const W = 1280, H = 720;
export const CFG = {
  ship: { maxSpeed: 420, accel: 240, turn: 170, maxHealth: 100, hitDamage: 25, healthGain: 35, grace: 1.5, boost: 1.6 },
  physics: { gravity: 600000, maxAccel: 320, soft: 50, damping: 0.8 },
  rocks: { count: 6, minSpeed: 50, maxSpeed: 130, splitAngle: 35, splitSpeed: 1.2, max: 40, respawn: 6, alienDamage: 15 },
  timing: { powerupEvery: 8, powerupLife: 10, whMin: 6, whMax: 14, whLife: 7, boost: 6, invincible: 6 },
  diff: { extraRocks: 1, speed: 0.08, gravity: 0.1, alienHealth: 0.1, dropChance: 0.3 },
  world: { growth: 0.25, max: 3, zoomSpeed: 1.5 },
};
export const ROCK_SCALE = { 3: 1.6, 2: 1.0, 1: 0.6 };
export const WEAPONS = {   // key -> weapon (bolt types only in this build)
  1: { name: 'Blaster', dmg: 10, speed: 700, cd: 0.25, range: 900, ammo: -1, pack: 0, count: 1, spread: 0, unlock: 1 },
  2: { name: 'Spread', dmg: 8, speed: 600, cd: 0.5, range: 600, ammo: 30, pack: 15, count: 3, spread: 24, unlock: 1 },
  3: { name: 'Rapid', dmg: 4, speed: 800, cd: 0.08, range: 700, ammo: 150, pack: 75, count: 1, spread: 0, unlock: 2 },
};
export const ALIENS = {
  drifter: { health: 20, speed: 90, contact: 15, score: 50, minLevel: 1, scale: 0.9, waveAmp: 80, waveFreq: 1.2 },
  chaser: { health: 30, speed: 170, contact: 25, score: 100, minLevel: 2, scale: 0.8, turn: 90 },
};
export const COLORS = { white: '#fff', gold: '#ffd040', grey: '#96a0b9', red: '#eb4646', green: '#50dc78', cyan: '#5adcff', orange: '#ffa032' };
