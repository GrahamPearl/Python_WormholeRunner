import { settings } from './config.js';
import { prefs } from './utils.js';

// op: [kind, f0, f1, dur, vol, at]   kind: s = sweep, t = tone, n = noise
const R = {
  thrust: [['n', 0, 0, .2, .3]], crash: [['n', 0, 0, .5, .5], ['t', 70, 70, .5, .4]], split: [['n', 0, 0, .12, .4]],
  powerup: [['t', 523, 523, .08, .3], ['t', 659, 659, .08, .3, .08], ['t', 784, 784, .14, .3, .16]],
  wormhole: [['s', 200, 1200, .7, .3]], fire_w1: [['s', 1300, 500, .12, .3]], fire_w2: [['s', 900, 400, .18, .3], ['n', 0, 0, .18, .2]],
  fire_w3: [['t', 950, 950, .04, .3]], fire_w4: [['s', 200, 700, .35, .3], ['n', 0, 0, .35, .25]], fire_w5: [['s', 2200, 300, .25, .3]],
  fire_w6: [['t', 150, 150, .12, .35], ['t', 100, 100, .12, .35, .12]], weapon_switch: [['t', 660, 660, .05, .3], ['t', 880, 880, .06, .3, .05]],
  no_ammo: [['t', 120, 120, .12, .3]], explosion: [['n', 0, 0, .8, .6], ['s', 160, 40, .8, .4]],
  ability_cloak: [['s', 900, 200, .5, .25]], ability_hyperjump: [['s', 200, 2000, .25, .35], ['s', 2000, 400, .2, .3, .25]],
  ability_hyperspace: [['s', 300, 900, .6, .3], ['t', 150, 150, .6, .2]], ability_deflect: [['t', 1400, 1400, .08, .4], ['t', 900, 900, .15, .35, .08]],
  ability_repair: [['t', 440, 440, .1, .3], ['t', 554, 554, .1, .3, .1], ['t', 659, 659, .2, .3, .2]],
  ability_afterburner: [['s', 200, 1400, .4, .3]], ability_nova: [['n', 0, 0, .5, .5], ['s', 900, 100, .5, .4]], ability_ram: [['t', 110, 110, .4, .5], ['n', 0, 0, .4, .3]],
  ability_timeslip: [['s', 1500, 150, .6, .3]], ability_launch: [['t', 400, 400, .08, .3], ['t', 600, 600, .08, .3, .08], ['t', 800, 800, .12, .3, .16]],
  shield_hit: [['t', 600, 600, .15, .3], ['n', 0, 0, .15, .15]], crystal: [['t', 1200, 1200, .05, .3], ['t', 1600, 1600, .1, .3, .05]],
  objective_done: [['t', 523, 523, .1, .3], ['t', 659, 659, .1, .3, .1], ['t', 784, 784, .1, .3, .2], ['t', 1047, 1047, .3, .3, .3]],
  perk_pick: [['t', 660, 660, .08, .3], ['t', 990, 990, .15, .3, .08]], flare_warn: [['t', 700, 700, .15, .4], ['t', 500, 500, .15, .4, .15], ['t', 700, 700, .15, .4, .3]],
  flare_hit: [['n', 0, 0, .8, .6], ['s', 900, 100, .8, .3]], mine_blast: [['n', 0, 0, .5, .5], ['t', 90, 90, .5, .4]],
  mothership_spawn: [['s', 70, 220, 1.1, .5]], mothership_fire: [['s', 320, 140, .3, .35], ['n', 0, 0, .3, .2]], mothership_die: [['n', 0, 0, 1.2, .7], ['s', 200, 30, 1.2, .5]],
  teleporter_blink: [['s', 1600, 300, .12, .35]], minelayer_drop: [['t', 300, 300, .06, .3], ['t', 200, 200, .08, .3, .06]],
  ally_rescued: [['t', 523, 523, .1, .3], ['t', 784, 784, .1, .3, .1], ['t', 1047, 1047, .2, .3, .2]], ally_lost: [['s', 600, 120, .4, .3]],
};
function recipe(name) {
  if (R[name]) return R[name];
  if (name.startsWith('fire_')) return [['s', 1500, 700, .12, .25]];
  if (name.endsWith('_spawn')) return [['s', 300, 700, .35, .3]];
  if (name.endsWith('_die')) return [['n', 0, 0, .35, .35], ['s', 600, 120, .35, .3]];
  if (name.endsWith('_fire')) return [['t', 1100, 1100, .05, .25]];
  return [['t', 600, 600, .08, .25]];
}
const NOTES = [220, 262, 330, 262, 196, 247, 294, 247, 220, 262, 330, 392, 330, 294, 262, 247];

/** Event name -> synthesized sound (the web version of audio.py). Silent if audio is unavailable. */
export class AudioManager {
  constructor() { this.ac = null; this.noise = null; this.timer = null; this.step = 0; this.musicOn = false; }
  ctx() {
    if (!this.ac) { try { this.ac = new (window.AudioContext || window.webkitAudioContext)(); } catch { return null; } }
    if (this.ac.state === 'suspended') this.ac.resume().catch(() => {});
    return this.ac;
  }
  get muted() { return prefs.data.muted; }
  setMuted(m) { prefs.data.muted = m; prefs.save(); if (m) this.stopMusic(); }
  vol(event, bus) { return (settings.get(`audio.events.${event}.volume`, 1)) * settings.get(bus === 'music' ? 'audio.music_volume' : 'audio.sfx_volume', 0.7); }
  play(event) {
    if (this.muted) return;
    const ac = this.ctx(); if (!ac) return;
    const v = this.vol(event, 'sfx'); if (v <= 0) return;
    try {
      for (const [k, f0, f1, dur, vol, at = 0] of recipe(event)) {
        const t = ac.currentTime + at, g = ac.createGain();
        g.gain.setValueAtTime(vol * v * 0.6, t); g.gain.linearRampToValueAtTime(0, t + dur); g.connect(ac.destination);
        if (k === 'n') {
          if (!this.noise) { this.noise = ac.createBuffer(1, ac.sampleRate, ac.sampleRate); const d = this.noise.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
          const s = ac.createBufferSource(); s.buffer = this.noise; s.connect(g); s.start(t); s.stop(t + dur);
        } else {
          const o = ac.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f0, t); o.frequency.linearRampToValueAtTime(f1, t + dur);
          o.connect(g); o.start(t); o.stop(t + dur);
        }
      }
    } catch { /* ignore */ }
  }
  playMusic() {
    this.stopMusic(); if (this.muted) return; const ac = this.ctx(); if (!ac) return;
    this.musicOn = true;
    const tick = () => {
      const v = this.vol('music', 'music') * 0.12; if (v > 0 && !this.muted) {
        const o = ac.createOscillator(), g = ac.createGain(), t = ac.currentTime, f = NOTES[this.step++ % NOTES.length];
        o.type = 'triangle'; o.frequency.value = f; g.gain.setValueAtTime(v, t); g.gain.linearRampToValueAtTime(0, t + 0.34); o.connect(g).connect(ac.destination); o.start(t); o.stop(t + 0.36);
      }
    };
    tick(); this.timer = setInterval(tick, 360);
  }
  stopMusic() { if (this.timer) clearInterval(this.timer); this.timer = null; this.musicOn = false; }
}
