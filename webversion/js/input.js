/** Keeps a dictionary of held keys and queues one-shot presses. Blocks page scroll keys. */
const BLOCK = new Set(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space']);
export class InputHandler {
  constructor() {
    this.down = {}; this.pressed = [];
    addEventListener('keydown', e => {
      if (BLOCK.has(e.code)) e.preventDefault();
      if (!this.down[e.code]) this.pressed.push(e.code);
      this.down[e.code] = true;
    });
    addEventListener('keyup', e => { this.down[e.code] = false; });
    addEventListener('blur', () => { this.down = {}; });
  }
  held(code) { return !!this.down[code]; }
  takePresses() { const p = this.pressed; this.pressed = []; return p; }
}
