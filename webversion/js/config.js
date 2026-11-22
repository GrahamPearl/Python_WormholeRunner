// All game data, mirroring game/config.py. Everything the editor changes lives in `settings`.
export const W = 1280, H = 720;
const G = (file, w, h, frames, fps, scale = 1) => ({ file, frame_w: w, frame_h: h, frames, fps, scale });
const weapon = (name, type, damage, speed, cooldown, range, ammo, ammo_pack, unlock, o = {}) => ({
  enabled: true, name, type, unlock_level: unlock, damage, speed, cooldown, range, ammo, ammo_pack, count: 1, spread: 0,
  pierce: 1, turn_rate: 0, blast_radius: 0, fuse: 0, sound: 'fire_w1', graphic: '', silent: false, heal: 0, ...o });
const ship = (name, price, desc, graphic, health, speed, accel, turn, o = {}) => ({
  name, price, desc, graphic, health, speed_mult: speed, accel_mult: accel, turn_mult: turn, ability: {}, passive: {}, weapon: {}, ...o });
const alien = (o) => ({ enabled: true, health: 30, speed: 100, contact_damage: 15, score: 100, min_level: 1, ...o });

const gfx = {
  ship: G('ship_sheet.png', 64, 64, 4, 12), rock: G('rock_sheet.png', 64, 64, 4, 3), wormhole: G('wormhole_sheet.png', 128, 128, 8, 12, 1.2),
  powerup_speed: G('powerup_speed.png', 32, 32, 1, 0), powerup_health: G('powerup_health.png', 32, 32, 1, 0),
  powerup_shield: G('powerup_shield.png', 32, 32, 1, 0), powerup_ammo: G('powerup_ammo.png', 32, 32, 1, 0),
  bullet_w1: G('bullet_w1.png', 12, 28, 1, 0), bullet_w2: G('bullet_w2.png', 12, 20, 1, 0), bullet_w3: G('bullet_w3.png', 8, 16, 1, 0),
  bullet_w4: G('bullet_w4.png', 16, 32, 2, 10), bullet_w5: G('bullet_w5.png', 8, 48, 1, 0), bullet_w6: G('bullet_w6.png', 32, 32, 2, 3),
  bullet_w7: G('bullet_w1.png', 12, 28, 1, 0), bullet_w8: G('bullet_w1.png', 12, 28, 1, 0), bullet_w9: G('bullet_w1.png', 12, 28, 1, 0),
  alien_drifter: G('alien_drifter.png', 64, 64, 4, 6, 0.9), alien_chaser: G('alien_chaser.png', 64, 64, 4, 12, 0.8),
  alien_sniper: G('alien_sniper.png', 64, 64, 4, 6, 0.9), alien_swarm: G('alien_swarm.png', 64, 64, 4, 10, 0.6),
  alien_mothership: G('alien_mothership.png', 128, 128, 4, 4, 1.6), alien_bullet: G('alien_bullet.png', 16, 16, 2, 8),
  alien_seeker: G('alien_seeker.png', 64, 64, 4, 8, 0.9), alien_teleporter: G('alien_teleporter.png', 64, 64, 4, 8, 0.9),
  alien_minelayer: G('alien_minelayer.png', 64, 64, 4, 5), alien_mine: G('alien_mine.png', 32, 32, 2, 3, 0.8),
  ship_phantom: G('ship_phantom.png', 64, 64, 4, 12), ship_skipper: G('ship_skipper.png', 64, 64, 4, 12), ship_specter: G('ship_specter.png', 64, 64, 4, 12),
  ship_bulwark: G('ship_bulwark.png', 64, 64, 4, 10, 1.1), ship_medic: G('ship_medic.png', 64, 64, 4, 12),
  bullet_phantom: G('bullet_phantom.png', 6, 40, 1, 0), bullet_skipper: G('bullet_skipper.png', 32, 32, 1, 0), bullet_specter: G('bullet_specter.png', 10, 56, 1, 0),
  bullet_bulwark: G('bullet_bulwark.png', 10, 10, 1, 0), bullet_medic: G('bullet_medic.png', 16, 16, 1, 0),
  objective_crystal: G('objective_crystal.png', 32, 32, 2, 3), objective_pod: G('objective_pod.png', 40, 40, 2, 2), objective_freighter: G('objective_freighter.png', 96, 96, 1, 0, 1.2),
  ship_comet: G('ship_comet.png', 64, 64, 4, 12), ship_lancer: G('ship_lancer.png', 64, 64, 4, 10), ship_prospector: G('ship_prospector.png', 64, 64, 4, 8),
  ship_nova: G('ship_nova.png', 64, 64, 4, 12), ship_juggernaut: G('ship_juggernaut.png', 64, 64, 4, 8, 1.1), ship_chronos: G('ship_chronos.png', 64, 64, 4, 10),
  ship_carrier: G('ship_carrier.png', 64, 64, 4, 6, 1.2),
  ally_wingman: G('ally_wingman.png', 64, 64, 4, 10, 0.8), ally_repair: G('ally_repair.png', 64, 64, 4, 8, 0.7), ally_cutter: G('ally_cutter.png', 64, 64, 4, 8, 0.9),
  ally_trader: G('ally_trader.png', 64, 64, 4, 4, 0.9), ally_stranded: G('ally_stranded.png', 64, 64, 4, 4, 0.9),
};

const events = {  // sound event -> volume (sounds are synthesized in audio.js)
  music: 1, thrust: .5, crash: 1, powerup: 1, wormhole: 1, split: .8, fire_w1: .6, fire_w2: .6, fire_w3: .5, fire_w4: .7, fire_w5: .6, fire_w6: .7,
  weapon_switch: .6, no_ammo: .6, explosion: 1, fire_phantom: .5, fire_skipper: .7, fire_specter: .6, fire_bulwark: .7, fire_medic: .5,
  ability_cloak: .7, ability_hyperjump: .8, ability_hyperspace: .8, ability_deflect: .7, ability_repair: .7, shield_hit: .7, crystal: .6,
  objective_done: .9, perk_pick: .8, flare_warn: .7, flare_hit: .9, mine_blast: .8, mothership_spawn: 1, mothership_fire: .7, mothership_die: 1,
  fire_comet: .5, fire_prospector: .5, fire_nova: .6, fire_juggernaut: .7, fire_chronos: .5, fire_carrier: .5, ability_afterburner: .7, ability_nova: .9,
  ability_ram: .8, ability_timeslip: .7, ability_launch: .7, ally_rescued: .8, ally_lost: .7, minelayer_drop: .5, teleporter_blink: .6,
};
for (const k of ['drifter', 'chaser', 'sniper', 'swarm', 'seeker', 'teleporter', 'minelayer']) { events[k + '_spawn'] = .6; events[k + '_die'] = .8; }
for (const k of ['sniper', 'swarm', 'seeker', 'teleporter']) events[k + '_fire'] = .5;
for (const k of Object.keys(events)) events[k] = { volume: events[k] };

export const DEFAULTS = {
  graphics: gfx,
  physics: { gravity: 600000, max_accel: 320, softening: 50, drift_damping: 0.8 },
  ship: { max_speed: 420, acceleration: 240, turn_rate: 170, max_health: 100, hit_damage: 25, health_gain: 35, grace_time: 1.5, boost_multiplier: 1.6 },
  rocks: { count: 6, min_speed: 50, max_speed: 130, split_angle: 35, split_speed: 1.2, split_on_rock_hit: true, max_rocks: 40, respawn_time: 6, alien_damage: 15 },
  timing: { powerup_interval: 8, powerup_lifetime: 10, wormhole_min_delay: 6, wormhole_max_delay: 14, wormhole_lifetime: 7, speed_boost_time: 6, invincible_time: 6 },
  difficulty: { extra_rocks_per_level: 1, speed_per_level: 0.08, gravity_per_level: 0.1, alien_health_per_level: 0.1, alien_drop_chance: 0.3 },
  game: { mode: 'classic', hangar_buying: true },
  credits: { start_credits: 700, alien_factor: 0.2, rock_per_size: 2, gold_rock: 30, powerup: 5, crystal: 8, rescue: 25, level_clear: 20, objective: 30 },
  rock_types: { ice: { min_level: 2, weight: 14 }, explosive: { min_level: 3, weight: 10 }, gold: { min_level: 2, weight: 8 }, metal: { min_level: 4, weight: 12 } },
  hazards: { nebula_from: 2, blackhole_from: 3, ion_from: 4, flare_from: 3, blackhole_strength: 7e6, flare_interval: 30, flare_damage: 25, cloak_detect: 140 },
  objectives: { enabled: true, crystals_base: 4, pods_base: 2, escort_seconds: 35, freighter_health: 150 },
  ships: {
    scout: ship('Scout', 0, 'Balanced starter ship.', 'ship', 100, 1, 1, 1),
    phantom: ship('Phantom', 600, 'Stealth. Cloak hides you from aliens for a few seconds.', 'ship_phantom', 80, 1.05, 1, 1.1, {
      ability: { type: 'cloak', name: 'Cloak', cooldown: 12, duration: 6, desc: 'Invisible to aliens. Firing (except the Silent Bolt) or being hit breaks it.' },
      weapon: weapon('Silent Bolt', 'bolt', 55, 1500, 1.1, 1600, -1, 0, 1, { silent: true, graphic: 'bullet_phantom', sound: 'fire_phantom' }) }),
    skipper: ship('Skipper', 800, 'Hit-and-run. Hyperjump to a random safe spot on the map.', 'ship_skipper', 90, 1, 1.15, 1, {
      ability: { type: 'hyperjump', name: 'Hyperjump', cooldown: 8, desc: 'Instantly jump to a random safe position with a moment of protection.' },
      weapon: weapon('Jump-blast', 'pulse', 35, 0, 2, 0, -1, 0, 1, { blast_radius: 170, graphic: 'bullet_skipper', sound: 'fire_skipper' }) }),
    specter: ship('Specter', 1000, 'Evasion. Hyperspace lets rocks and aliens pass straight through you.', 'ship_specter', 85, 1, 1, 1, {
      ability: { type: 'hyperspace', name: 'Hyperspace', cooldown: 14, duration: 3, desc: '3 seconds immune to rocks, aliens and bullets - but you cannot fire or collect.' },
      weapon: weapon('Phase Lance', 'bolt', 28, 1000, 0.7, 1200, -1, 0, 1, { pierce: 8, graphic: 'bullet_specter', sound: 'fire_specter' }) }),
    bulwark: ship('Bulwark', 1200, 'Tank. A rechargeable shield soaks up damage; Deflect throws shots back.', 'ship_bulwark', 130, 0.85, 0.9, 0.85, {
      ability: { type: 'deflect', name: 'Deflect', cooldown: 9, duration: 1.6, desc: 'Reflect alien bullets and shrug off rocks while active.' },
      passive: { shield_max: 60, shield_delay: 3, shield_rate: 14 },
      weapon: weapon('Flak Cannon', 'bolt', 7, 700, 0.8, 380, -1, 0, 1, { count: 7, spread: 36, graphic: 'bullet_bulwark', sound: 'fire_bulwark' }) }),
    medic: ship('Medic', 900, 'Support. Heals itself over time and repairs your partner.', 'ship_medic', 95, 0.95, 1, 1, {
      ability: { type: 'repair', name: 'Repair Burst', cooldown: 12, duration: 3, range: 360, self_rate: 8, ally_rate: 12, desc: 'For 3 seconds heal yourself and any ally within range.' },
      passive: { regen: 1.5, regen_delay: 2 },
      weapon: weapon('Repair Dart', 'bolt', 10, 800, 0.5, 700, -1, 0, 1, { heal: 15, graphic: 'bullet_medic', sound: 'fire_medic' }) }),
    comet: ship('Comet', 700, 'Interceptor. Very fast, thin hull. Afterburner gives a burst of speed.', 'ship_comet', 70, 1.25, 1.3, 1.2, {
      ability: { type: 'afterburner', name: 'Afterburner', cooldown: 9, duration: 3, desc: 'A 3 second burst of extra speed.' },
      weapon: weapon('Twin Pulse', 'bolt', 6, 900, 0.2, 800, -1, 0, 1, { count: 2, spread: 4, sound: 'fire_comet' }) }),
    lancer: ship('Lancer', 1100, 'Sniper. One powerful piercing shot. Slow to turn.', 'ship_lancer', 75, 0.95, 0.95, 0.85, {
      weapon: weapon('Rail Lance', 'bolt', 70, 1800, 1.6, 2000, -1, 0, 1, { pierce: 10, graphic: 'bullet_specter', sound: 'fire_specter' }) }),
    prospector: ship('Prospector', 850, 'Collector. Pulls pickups in and earns 25% more credits.', 'ship_prospector', 110, 0.9, 0.95, 0.9, {
      passive: { magnet: 220, credit_bonus: 0.25 },
      weapon: weapon('Ore Cutter', 'bolt', 12, 800, 0.35, 500, -1, 0, 1, { pierce: 3, sound: 'fire_prospector' }) }),
    nova: ship('Nova', 1000, 'Area damage. Nova Burst blasts everything around you.', 'ship_nova', 85, 1, 1, 1, {
      ability: { type: 'nova', name: 'Nova Burst', cooldown: 15, radius: 300, damage: 40, desc: 'An explosion ring that damages aliens and rocks nearby.' },
      weapon: weapon('Seeker Swarm', 'homing', 8, 500, 1, 1200, -1, 0, 1, { count: 3, spread: 30, turn_rate: 200, graphic: 'bullet_w4', sound: 'fire_nova' }) }),
    juggernaut: ship('Juggernaut', 1400, 'Heavy ram. Ram Drive smashes through rocks and aliens.', 'ship_juggernaut', 160, 0.8, 0.8, 0.75, {
      ability: { type: 'ram', name: 'Ram Drive', cooldown: 10, duration: 3, desc: '3 seconds of crashing through rocks and aliens, faster and unharmed.' },
      weapon: weapon('Mass Driver', 'bolt', 40, 500, 1.2, 700, -1, 0, 1, { pierce: 2, graphic: 'bullet_bulwark', sound: 'fire_juggernaut' }) }),
    chronos: ship('Chronos', 1500, 'Control. Time Slip makes aliens and rocks move at half speed.', 'ship_chronos', 90, 1, 1, 1.05, {
      ability: { type: 'timeslip', name: 'Time Slip', cooldown: 16, duration: 4, desc: 'Aliens, rocks and alien bullets move at half speed for 4 seconds.' },
      weapon: weapon('Chrono Dart', 'bolt', 18, 1000, 0.4, 1000, -1, 0, 1, { pierce: 2, graphic: 'bullet_phantom', sound: 'fire_chronos' }) }),
    carrier: ship('Carrier', 1800, 'Commander. Launches two wingmen that fight for you.', 'ship_carrier', 120, 0.85, 0.85, 0.8, {
      ability: { type: 'launch', name: 'Launch Drones', cooldown: 30, duration: 20, count: 2, desc: 'Two wingmen fight beside you for 20 seconds.' },
      weapon: weapon('Light Cannon', 'bolt', 14, 800, 0.4, 900, -1, 0, 1, { sound: 'fire_carrier' }) }),
  },
  world: { growth_per_level: 0.25, max_scale: 3, zoom_speed: 1.5 },
  weapons: {
    w1: weapon('Blaster', 'bolt', 10, 700, 0.25, 900, -1, 0, 1),
    w2: weapon('Spread', 'bolt', 8, 600, 0.5, 600, 30, 15, 1, { count: 3, spread: 24 }),
    w3: weapon('Rapid', 'bolt', 4, 800, 0.08, 700, 150, 75, 2),
    w4: weapon('Missile', 'homing', 25, 420, 0.9, 1400, 8, 4, 3, { turn_rate: 140, sound: 'fire_w4' }),
    w5: weapon('Laser', 'bolt', 15, 1100, 0.6, 1100, 20, 10, 4, { pierce: 4, sound: 'fire_w5' }),
    w6: weapon('Mine', 'mine', 40, 0, 1, 0, 6, 3, 5, { blast_radius: 130, fuse: 3, sound: 'fire_w6' }),
    w7: weapon('Custom 7', 'bolt', 10, 700, 0.25, 900, -1, 0, 1, { enabled: false }),
    w8: weapon('Custom 8', 'bolt', 10, 700, 0.25, 900, -1, 0, 1, { enabled: false }),
    w9: weapon('Custom 9', 'bolt', 10, 700, 0.25, 900, -1, 0, 1, { enabled: false }),
  },
  aliens: {
    drifter: { enabled: true, health: 20, speed: 90, contact_damage: 15, score: 50, min_level: 1, wave_amp: 80, wave_freq: 1.2 },
    chaser: { enabled: true, health: 30, speed: 170, contact_damage: 25, score: 100, min_level: 2, turn_rate: 90, dies_on_ram: true },
    sniper: { enabled: true, health: 40, speed: 120, contact_damage: 15, score: 150, min_level: 3, fire_interval: 2.2, bullet_speed: 520, bullet_damage: 15, keep_distance: 380 },
    swarm: { enabled: true, health: 15, speed: 170, contact_damage: 10, score: 60, min_level: 4, fire_interval: 3, bullet_speed: 400, bullet_damage: 8, orbit_radius: 220, orbit_speed: 60, group_size: 4 },
    seeker: alien({ health: 35, speed: 150, contact_damage: 20, score: 120, min_level: 3, fire_interval: 3, bullet_speed: 380, bullet_damage: 10, detect_range: 900 }),
    teleporter: alien({ health: 30, speed: 80, contact_damage: 15, score: 130, min_level: 4, blink_interval: 4, burst_count: 3, bullet_speed: 450, bullet_damage: 10, ring: 300 }),
    minelayer: alien({ health: 50, speed: 100, contact_damage: 15, score: 140, min_level: 5, mine_interval: 2.5, mine_damage: 25, mine_blast: 100 }),
    mothership: { enabled: true, health: 400, speed: 70, contact_damage: 30, score: 1000, min_level: 5, boss_every: 5, fire_interval: 1.6, bullet_speed: 380, bullet_damage: 12, keep_distance: 420, spawn_interval: 6, ring_bullets: 12 },
  },
  audio: { music_volume: 0.5, sfx_volume: 0.7, events },
  allies: {
    wingman: { name: 'Wingman', health: 40, speed: 380, damage: 6, fire_interval: 0.7, range: 600 },
    repair: { name: 'Repair Drone', health: 30, speed: 340, heal_rate: 6, heal_range: 220 },
    cutter: { name: 'Patrol Cutter', health: 120, speed: 160, damage: 9, fire_interval: 0.6, range: 650, patrol_radius: 220 },
    trader: { name: 'Trader', health: 60, speed: 70, bonus: 40 },
    stranded: { name: 'Stranded ship', health: 50, speed: 0 },
  },
  shop_items: {
    hull: { name: 'Hull Plating', price: 150, max_level: 5, desc: '+10 max health per level' },
    engines: { name: 'Engine Tuning', price: 200, max_level: 5, desc: '+5% speed and acceleration per level' },
    guns: { name: 'Weapon Coils', price: 250, max_level: 5, desc: '+5% weapon damage per level' },
    capacitor: { name: 'Capacitors', price: 300, max_level: 4, desc: 'Abilities recharge 5% faster per level' },
    tractor: { name: 'Tractor Beam', price: 200, max_level: 3, desc: 'Pickups pulled in from +40 px per level' },
    salvage: { name: 'Salvage Rights', price: 300, max_level: 4, desc: '+5% credits per level' },
  },
  services: { repair: { name: 'Repair hull', price_per_percent: 1 }, wingman: { name: 'Wingman contract', price: 150 }, ammo: { name: 'Ammo pack', price: 80 } },
  zones: {
    haven: { name: 'Haven Station', kind: 'station', pos: [0.06, 0.42], links: ['rocky_reach', 'verdant'], desc: 'A busy trading station. Safe harbour.',
      shop: ['ships', 'upgrades', 'services'], stock: ['phantom', 'skipper', 'comet', 'lancer'] },
    rocky_reach: { name: 'Rocky Reach', kind: 'combat', pos: [0.20, 0.42], links: ['haven', 'nebula_veil', 'ember_belt'], desc: 'A crowded rock field. Collect the crystals.',
      level: 2, reward: 120, objective: { type: 'crystals', need: 5 }, aliens: ['drifter', 'chaser'], alien_count: { drifter: 2, chaser: 1 }, gravity: 1.5, friendlies: [{ type: 'trader' }] },
    nebula_veil: { name: 'Nebula Veil', kind: 'combat', pos: [0.34, 0.42], links: ['rocky_reach', 'ion_narrows'], desc: 'A purple cloud hides things. Rescue the pods.',
      level: 3, reward: 200, objective: { type: 'rescue', need: 3 }, aliens: ['drifter', 'seeker'], alien_count: { drifter: 2, seeker: 1 }, hazards: { nebula: 3 }, friendlies: [{ type: 'stranded' }] },
    ion_narrows: { name: 'Ion Narrows', kind: 'combat', pos: [0.50, 0.42], links: ['nebula_veil', 'black_market', 'wreck_field'], desc: 'Ion storms jam your ship. Defend the station.',
      level: 4, reward: 300, objective: { type: 'defend', seconds: 40 }, aliens: ['chaser', 'sniper'], alien_count: { chaser: 2, sniper: 1 }, hazards: { ion: 3 }, friendlies: [{ type: 'cutter' }] },
    wreck_field: { name: 'Wreck Field', kind: 'combat', pos: [0.66, 0.42], links: ['ion_narrows', 'ironhold', 'singularity'], desc: 'Old wrecks and new mines. Hold out until help arrives.',
      level: 5, reward: 350, objective: { type: 'survive', seconds: 60 }, aliens: ['minelayer', 'teleporter', 'drifter'], alien_count: { minelayer: 1, teleporter: 1, drifter: 2 }, friendlies: [{ type: 'stranded' }] },
    singularity: { name: 'Singularity', kind: 'combat', pos: [0.80, 0.42], links: ['wreck_field', 'citadel'], desc: 'Black holes guard the beacon. Fly around them.',
      level: 6, reward: 400, objective: { type: 'beacon', need: 1 }, aliens: ['chaser', 'seeker'], alien_count: { chaser: 2, seeker: 2 }, hazards: { blackhole: 2 }, flares: true, friendlies: [{ type: 'repair' }] },
    citadel: { name: 'The Citadel', kind: 'boss', pos: [0.94, 0.42], links: ['singularity'], desc: 'The alien Mothership. End it.',
      level: 7, reward: 1000, boss: true, final: true, aliens: ['sniper', 'swarm'], alien_count: { sniper: 2, swarm: 1 }, hazards: { ion: 1 } },
    black_market: { name: 'Black Market', kind: 'station', pos: [0.50, 0.10], links: ['ion_narrows'], desc: 'Rare ships. High prices. No questions.', shop: ['ships'], stock: ['specter', 'chronos', 'carrier'] },
    verdant: { name: 'Verdant', kind: 'planet', pos: [0.06, 0.82], links: ['haven', 'ember_belt'], desc: 'A green planet with a repair yard.', shop: ['ships', 'services'], stock: ['medic', 'prospector'] },
    ember_belt: { name: 'Ember Belt', kind: 'combat', pos: [0.20, 0.82], links: ['rocky_reach', 'verdant', 'ironhold'], desc: 'Gold ore and solar flares. Break the gold rocks before time runs out.',
      level: 3, reward: 250, objective: { type: 'prospect', need: 6 }, rock_weights: { gold: 40 }, aliens: ['drifter', 'chaser'], alien_count: { drifter: 2, chaser: 1 }, flares: true, time_limit: 180, friendlies: [{ type: 'trader' }] },
    ironhold: { name: 'Ironhold', kind: 'station', pos: [0.40, 0.82], links: ['ember_belt', 'wreck_field'], desc: 'A forge station. Upgrades and heavy ships.', shop: ['ships', 'upgrades'], stock: ['bulwark', 'nova', 'juggernaut'] },
  },
};
export const ROCK_SIZE_SCALE = { 3: 1.6, 2: 1.0, 1: 0.6 };
export const ROCK_TINTS = { ice: '#96cdff', explosive: '#ff785a', gold: '#ffd746', metal: '#afb4c3' };
export const CLASSIC_ALIENS = ['drifter', 'chaser', 'sniper', 'swarm'];
export const EXPEDITION_ALIENS = [...CLASSIC_ALIENS, 'seeker', 'teleporter', 'minelayer'];
export const POWERUP_KINDS = ['speed', 'health', 'shield', 'ammo'];
export const COLORS = { white: '#fff', gold: '#ffd040', grey: '#96a0b9', red: '#eb4646', green: '#50dc78', cyan: '#5adcff', orange: '#ffa032', blue: '#3c5aaa' };

const clone = o => JSON.parse(JSON.stringify(o));
const isObj = v => v && typeof v === 'object' && !Array.isArray(v);
function merge(base, over) { for (const [k, v] of Object.entries(over)) { if (isObj(v) && isObj(base[k])) merge(base[k], v); else base[k] = clone(v); } }
function diff(cur, def) {
  const out = {};
  for (const [k, v] of Object.entries(cur)) {
    if (isObj(v) && isObj(def?.[k])) { const d = diff(v, def[k]); if (Object.keys(d).length) out[k] = d; }
    else if (JSON.stringify(v) !== JSON.stringify(def?.[k])) out[k] = v;
  }
  return out;
}

/** Dotted-name settings store (Config in config.py). Saves only what differs from DEFAULTS. */
export class Settings {
  constructor(key = 'wormholeRunner.settings.v1') { this.key = key; this.data = clone(DEFAULTS); this.load(); }
  load() { try { const s = localStorage.getItem(this.key); if (s) merge(this.data, JSON.parse(s)); } catch { /* broken save: use defaults */ } }
  save() { try { localStorage.setItem(this.key, JSON.stringify(diff(this.data, DEFAULTS))); return true; } catch { return false; } }
  static walk(tree, dotted) { let n = tree; for (const p of dotted.split('.')) n = n[p]; return n; }
  get(dotted, def) { try { const v = Settings.walk(this.data, dotted); return v === undefined ? def : v; } catch { return def; } }
  default(dotted) { return Settings.walk(DEFAULTS, dotted); }
  set(dotted, value) { const ps = dotted.split('.'), last = ps.pop(); let n = this.data; for (const p of ps) n = n[p]; n[last] = value; }
  reset(dotted) { try { this.set(dotted, clone(this.default(dotted))); } catch { /* unknown path */ } }
  resetAll() { this.data = clone(DEFAULTS); try { localStorage.removeItem(this.key); } catch { /* ignore */ } }
}
export const settings = new Settings();
