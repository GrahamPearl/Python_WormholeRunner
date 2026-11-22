import { settings } from './config.js';
import { clamp } from './utils.js';

const mk = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, w); c.height = Math.max(1, h); return c; };
const hue = s => { let h = 0; for (const ch of s) h = (h * 31 + ch.charCodeAt(0)) % 360; return h; };

/** Built-in drawing used when a PNG is missing: a simple coloured shape per kind of sprite. */
function fallback(file, fw, fh, frames) {
  const c = mk(fw * frames, fh), g = c.getContext('2d'), col = `hsl(${hue(file)},70%,60%)`;
  for (let i = 0; i < frames; i++) {
    g.save(); g.translate(i * fw + fw / 2, fh / 2); g.fillStyle = col; g.strokeStyle = '#fff'; g.lineWidth = 2; g.beginPath();
    const r = Math.min(fw, fh) * 0.42;
    if (/ship|ally|chaser|sniper|seeker/.test(file)) { g.moveTo(0, -r); g.lineTo(r * .7, r); g.lineTo(0, r * .6); g.lineTo(-r * .7, r); g.closePath(); }
    else if (/bullet|powerup|crystal|pod/.test(file)) g.arc(0, 0, r * (/bullet/.test(file) ? .4 : 1), 0, 7);
    else g.ellipse(0, 0, r, r * (/rock/.test(file) ? 1 : .7), 0, 0, 7);
    g.fill(); g.stroke(); g.restore();
  }
  return c;
}

/** Loads sprite sheets (PNG rows of frames) with Promise.all; missing files use generated shapes. */
export class Assets {
  constructor() { this.sheets = new Map(); this.tints = new Map(); }
  files() { return [...new Set(Object.values(settings.get('graphics')).map(s => s.file))]; }
  loadFile(file) {
    return new Promise(res => {
      const im = new Image();
      im.onload = () => { this.sheets.set(file, im); this.tints.clear(); res(); };
      im.onerror = () => res();
      im.src = `assets/images/${file}`;
    });
  }
  async load(progress = () => {}) {
    const files = this.files(); let n = 0;
    await Promise.all(files.map(f => this.loadFile(f).then(() => progress(++n / files.length))));
    return this;
  }
  sheet(file, spec) {
    const s = this.sheets.get(file);
    if (s) return s;
    const key = `fb:${file}:${spec.frame_w}x${spec.frame_h}x${spec.frames}`;
    if (!this.sheets.has(key)) this.sheets.set(key, fallback(file, spec.frame_w, spec.frame_h, spec.frames));
    if (!this.sheets.has('req:' + file)) { this.sheets.set('req:' + file, 1); this.loadFile(file); }   // pick up files added in the editor
    return this.sheets.get(key);
  }
  tinted(file, spec, tint) {
    const key = `${file}|${tint}|${spec.frame_w}`;
    let c = this.tints.get(key); if (c) return c;
    const src = this.sheet(file, spec); c = mk(src.width, src.height); const g = c.getContext('2d');
    g.drawImage(src, 0, 0); g.globalCompositeOperation = 'multiply'; g.fillStyle = tint; g.fillRect(0, 0, c.width, c.height);
    g.globalCompositeOperation = 'destination-in'; g.drawImage(src, 0, 0);
    this.tints.set(key, c); return c;
  }
  /** Draw sprite `name` at world-pixel (x, y) with the y-axis already flipped by the caller. */
  draw(g, name, x, y, angle, scale, alpha, t, tint) {
    const sp = settings.get('graphics.' + name); if (!sp) return;
    const frames = Math.max(1, sp.frames | 0), f = sp.fps > 0 && frames > 1 ? Math.floor(t * sp.fps) % frames : 0;
    const im = tint ? this.tinted(sp.file, sp, tint) : this.sheet(sp.file, sp), fw = sp.frame_w, fh = sp.frame_h;
    g.save(); g.globalAlpha = clamp(alpha, 0, 1); g.translate(x, y); g.rotate(angle * Math.PI / 180); g.scale(scale, scale);
    g.drawImage(im, f * fw, 0, fw, fh, -fw / 2, -fh / 2, fw, fh); g.restore();
  }
}
