import { W, H } from './config.js';
export const rand = (a, b) => a + Math.random() * (b - a);
export const pick = a => a[Math.floor(Math.random() * a.length)];
export const rad = d => d * Math.PI / 180;
export const deg = r => r * 180 / Math.PI;
export const mod = (a, n) => ((a % n) + n) % n;
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const angDiff = (to, from) => mod(to - from + 180, 360) - 180;     // shortest turn, degrees (-180..180)

/** The play area. It wraps: leaving one edge re-enters on the opposite one (world.py). */
export class World {
  constructor(scale = 1) { this.scale = scale; this.w = W * scale; this.h = H * scale; }
  get center() { return [this.w / 2, this.h / 2]; }
  wrap(o) { o.x = mod(o.x, this.w); o.y = mod(o.y, this.h); }
  delta(ax, ay, bx, by) {
    let dx = mod(bx - ax, this.w), dy = mod(by - ay, this.h);
    if (dx > this.w / 2) dx -= this.w;
    if (dy > this.h / 2) dy -= this.h;
    return [dx, dy];
  }
  dist(a, b) { const [dx, dy] = this.delta(a.x, a.y, b.x, b.y); return Math.hypot(dx, dy); }
  overlap(a, b) { return this.dist(a, b) < a.r + b.r; }
  random() { return [rand(0, this.w), rand(0, this.h)]; }
}

/** JSON in localStorage that never throws. */
export const store = {
  get(key, def) { try { const s = localStorage.getItem(key); return s ? JSON.parse(s) : def; } catch { return def; } },
  set(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); return true; } catch { return false; } },
};

/** Player preferences that are about this device, not the game rules. */
export const DEFAULT_BINDINGS = { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight', fire: 'Space', ability: 'ShiftLeft', pause: 'KeyP', menu: 'Escape' };
export const prefs = {
  key: 'wormholeRunner.prefs.v1',
  data: { muted: false, touch: 'auto', autopause: true, bindings: { ...DEFAULT_BINDINGS } },
  load() { const d = store.get(this.key, {}); Object.assign(this.data, d, { bindings: { ...DEFAULT_BINDINGS, ...(d.bindings || {}) } }); return this; },
  save() { store.set(this.key, this.data); },
};
prefs.load();
