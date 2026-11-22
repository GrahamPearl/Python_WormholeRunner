import { prefs, DEFAULT_BINDINGS } from './utils.js';

export const ACTIONS = { up: 'Speed up', down: 'Slow down', left: 'Turn left', right: 'Turn right', fire: 'Fire', ability: 'Ship ability', pause: 'Pause', menu: 'Back / menu' };
const BLOCK = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space']);
const TOUCH = [   // [action or one-shot, label, css class]
  ['left', '◀', 'l'], ['right', '▶', 'r'], ['up', '▲', 'u'], ['down', '▼', 'd'],
  ['fire', 'FIRE', 'fire'], ['ability', 'ABILITY', 'abil'], ['@wprev', '◀W', 'wp'], ['@wnext', 'W▶', 'wn'],
];

/** Keyboard (remappable) + on-screen touch buttons. held(action) for movement, takePresses() for one-shots. */
export class InputHandler {
  constructor(root = document.body) {
    this.down = {}; this.touchDown = {}; this.queue = []; this.rebind = null;
    addEventListener('keydown', e => this.onKey(e, true));
    addEventListener('keyup', e => this.onKey(e, false));
    addEventListener('blur', () => { this.down = {}; this.touchDown = {}; });
    this.buildTouch(root); this.applyTouchMode();
  }
  get map() { const m = {}; for (const [a, c] of Object.entries(prefs.data.bindings)) m[c] = a; return m; }
  onKey(e, isDown) {
    if (isDown && this.rebind) { e.preventDefault(); const cb = this.rebind; this.rebind = null; cb(e.code); return; }
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'select' || tag === 'textarea') return;            // typing in the editor
    if (BLOCK.has(e.code)) e.preventDefault();
    if (e.code === 'ShiftRight' && prefs.data.bindings.ability === 'ShiftLeft') this.down.ShiftLeft = isDown;
    if (isDown && !this.down[e.code]) {
      const a = this.map[e.code];
      if (a === 'pause' || a === 'menu') this.queue.push(a);
      else if (e.code === 'Enter' || e.code === 'NumpadEnter') this.queue.push('confirm');
      else if (e.code === 'Escape') this.queue.push('menu');
      const m = /^(?:Digit|Numpad)([1-9])$/.exec(e.code); if (m) this.queue.push('w' + m[1]);
    }
    this.down[e.code] = isDown;
  }
  held(action) { return !!(this.down[prefs.data.bindings[action]] || this.touchDown[action]); }
  takePresses() { const q = this.queue; this.queue = []; return q; }
  clear() { this.down = {}; this.touchDown = {}; this.queue = []; }
  startRebind(cb) { this.rebind = cb; }
  setBinding(action, code) { prefs.data.bindings[action] = code; prefs.save(); }
  resetBindings() { prefs.data.bindings = { ...DEFAULT_BINDINGS }; prefs.save(); }

  buildTouch(root) {
    const el = this.touchEl = document.createElement('div'); el.id = 'touch'; el.className = 'hidden';
    for (const [act, label, cls] of TOUCH) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 't-' + cls; b.textContent = label; b.setAttribute('aria-label', act.replace('@', ''));
      const on = ev => { ev.preventDefault(); if (act[0] === '@') this.queue.push(act.slice(1)); else this.touchDown[act] = true; b.classList.add('on'); };
      const off = ev => { ev.preventDefault(); if (act[0] !== '@') this.touchDown[act] = false; b.classList.remove('on'); };
      b.addEventListener('pointerdown', on); b.addEventListener('pointerup', off); b.addEventListener('pointercancel', off); b.addEventListener('pointerleave', off);
      el.appendChild(b);
    }
    root.appendChild(el);
  }
  applyTouchMode() {
    const m = prefs.data.touch, coarse = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;
    this.touchEl.classList.toggle('hidden', !(m === 'on' || (m === 'auto' && coarse)));
  }
}
