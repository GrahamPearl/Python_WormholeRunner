import { rad } from './utils.js';

const mk = (w, h, draw) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return c; };
const poly = (g, pts, fill, stroke) => { g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.closePath(); g.fillStyle = fill; g.fill(); if (stroke) { g.strokeStyle = stroke; g.lineWidth = 2; g.stroke(); } };
const disc = (g, x, y, r, fill) => { g.beginPath(); g.arc(x, y, r, 0, 7); g.fillStyle = fill; g.fill(); };

// Generated fallbacks, used when assets/images/<name>.png is missing.
const ART = {
  ship: () => mk(64, 64, g => { poly(g, [[27, 46], [32, 58], [37, 46]], '#ffaa28'); poly(g, [[32, 6], [52, 52], [32, 43], [12, 52]], '#bed2eb', '#fff'); disc(g, 32, 27, 5, '#468cdc'); }),
  rock: () => mk(64, 64, g => { let s = 7; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
    poly(g, Array.from({ length: 14 }, (_, k) => { const a = k / 14 * 6.283, d = 21 + r() * 8; return [32 + d * Math.cos(a), 32 + d * Math.sin(a)]; }), '#78695c', '#beafa0');
    for (let i = 0; i < 3; i++) disc(g, 20 + r() * 24, 20 + r() * 24, 3 + r() * 3, '#554a42'); }),
  drifter: () => mk(64, 64, g => { g.fillStyle = '#46aa5a'; g.beginPath(); g.ellipse(32, 36, 24, 10, 0, 0, 7); g.fill(); disc(g, 32, 24, 10, 'rgba(150,230,255,.8)'); }),
  chaser: () => mk(64, 64, g => { poly(g, [[27, 46], [32, 58], [37, 46]], '#ffc83c'); poly(g, [[32, 6], [48, 52], [32, 42], [16, 52]], '#d23c3c', '#ffc8c8'); disc(g, 32, 26, 4, '#fff078'); }),
  bullet: () => mk(12, 28, g => poly(g, [[6, 0], [11, 8], [11, 24], [6, 27], [1, 24], [1, 8]], '#ffe650')),
  wormhole: () => mk(128, 128, g => { for (let k = 0; k < 8; k++) { g.beginPath(); g.arc(64, 64, 60 - k * 7, 0, 7); g.strokeStyle = `rgb(${(255 - k * 22) / 2},${80 + k * 10},${255 - k * 22})`; g.lineWidth = 3; g.stroke(); }
    for (let a = 0; a < 4; a++) { g.beginPath(); g.arc(64, 64, 52, rad(a * 90), rad(a * 90 + 50)); g.strokeStyle = '#d2aaff'; g.lineWidth = 5; g.stroke(); } disc(g, 64, 64, 14, '#080019'); }),
  speed: () => pu('#ffdc3c', g => poly(g, [[18, 4], [8, 18], [15, 18], [13, 28], [24, 13], [17, 13]], '#ffdc3c')),
  health: () => pu('#50e66e', g => { g.fillStyle = '#50e66e'; g.fillRect(13, 7, 6, 18); g.fillRect(7, 13, 18, 6); }),
  shield: () => pu('#5adcff', g => { g.beginPath(); g.arc(16, 16, 8, 0, 7); g.strokeStyle = '#5adcff'; g.lineWidth = 3; g.stroke(); }),
  ammo: () => pu('#ff963c', g => { g.fillStyle = '#ff963c'; [8, 14, 20].forEach(x => g.fillRect(x, 8, 3, 16)); }),
};
const pu = (c, f) => mk(32, 32, g => { disc(g, 16, 16, 15, '#14192d'); g.beginPath(); g.arc(16, 16, 14, 0, 7); g.strokeStyle = c; g.lineWidth = 2; g.stroke(); f(g); });

/** Preloads every image with Promise.all; a missing file falls back to generated art. */
export class AssetLoader {
  constructor() { this.img = {}; }
  async load(onProgress = () => {}) {
    const names = Object.keys(ART); let n = 0;
    await Promise.all(names.map(name => new Promise(res => {
      const im = new Image();
      im.onload = () => { this.img[name] = im; done(); };
      im.onerror = () => { this.img[name] = ART[name](); done(); };
      im.src = `assets/images/${name}.png`;
      const done = () => { onProgress(++n / names.length); res(); };
    })));
    return this;
  }
}
