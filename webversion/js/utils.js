import { W, H } from './config.js';
export const rand = (a, b) => a + Math.random() * (b - a);
export const pick = a => a[Math.floor(Math.random() * a.length)];
export const rad = d => d * Math.PI / 180;
export const deg = r => r * 180 / Math.PI;
export const mod = (a, n) => ((a % n) + n) % n;

/** The play area. It wraps: leaving one edge re-enters on the opposite one (world.py). */
export class World {
  constructor(scale) { this.scale = scale; this.w = W * scale; this.h = H * scale; }
  wrap(o) { o.x = mod(o.x, this.w); o.y = mod(o.y, this.h); }
  delta(ax, ay, bx, by) {            // shortest vector from a to b on the wrapped world
    let dx = mod(bx - ax, this.w), dy = mod(by - ay, this.h);
    if (dx > this.w / 2) dx -= this.w;
    if (dy > this.h / 2) dy -= this.h;
    return [dx, dy];
  }
  dist(a, b) { return Math.hypot(...this.delta(a.x, a.y, b.x, b.y)); }
  overlap(a, b) { return this.dist(a, b) < a.r + b.r; }
  random() { return [rand(0, this.w), rand(0, this.h)]; }
}

/** localStorage wrapper for best score / level. */
export const store = {
  key: 'wormholeRunner.v1',
  load() { try { return JSON.parse(localStorage.getItem(this.key)) || { bestScore: 0, bestLevel: 1 }; } catch { return { bestScore: 0, bestLevel: 1 }; } },
  save(d) { try { localStorage.setItem(this.key, JSON.stringify(d)); } catch { /* storage blocked: ignore */ } },
};

/** Tiny synthesized sound effects (Web Audio); silent if audio is unavailable. */
let ac = null;
export function sfx(f0, f1 = f0, dur = 0.1, vol = 0.12, type = 'square') {
  try {
    ac = ac || new (window.AudioContext || window.webkitAudioContext)();
    const o = ac.createOscillator(), g = ac.createGain(), t = ac.currentTime;
    o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.linearRampToValueAtTime(f1, t + dur);
    g.gain.setValueAtTime(vol, t); g.gain.linearRampToValueAtTime(0, t + dur);
    o.connect(g).connect(ac.destination); o.start(t); o.stop(t + dur);
  } catch { /* ignore */ }
}
export const SFX = {
  fire: () => sfx(1300, 500, 0.1), crash: () => sfx(120, 40, 0.35, 0.2, 'sawtooth'), split: () => sfx(300, 100, 0.08, 0.1, 'sawtooth'),
  power: () => { sfx(523, 523, 0.07); setTimeout(() => sfx(784, 784, 0.1), 70); }, wormhole: () => sfx(200, 1200, 0.6, 0.15, 'sine'),
  empty: () => sfx(120, 120, 0.1), die: () => sfx(300, 60, 0.4, 0.15, 'sawtooth'), switch: () => sfx(660, 880, 0.06),
};
