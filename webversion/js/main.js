import { Assets } from './assets.js';
import { AudioManager } from './audio.js';
import { InputHandler } from './input.js';
import { Game } from './game.js';
import { UI } from './ui.js';
import { Editor } from './editor.js';
import { draw } from './render.js';
import { prefs } from './utils.js';

const $ = id => document.getElementById(id), stage = $('stage'), g = $('game').getContext('2d');
const note = $('load-text');
const assets = await new Assets().load(f => { note.textContent = `Loading... ${Math.round(f * 100)}%`; });
const audio = new AudioManager(), input = new InputHandler(stage);
let ui;
const game = new Game(audio, input, {
  state: s => { if (s === 'paused') ui.open('pause'); else if (s === 'playing' && ui.name) ui.close(); },
  gameover: info => ui.open('gameover', info),
  perks: () => ui.open('perk'),
  perksDone: () => ui.close(),
  zoneDone: info => (info.final && info.won ? ui.open('victory', info) : ui.open('starmap', { message: info.message })),
  quit: () => ui.quit(),
});
ui = new UI({ game, audio, input, assets, editor: new Editor($('screen'), audio, assets), stage });
ui.open('menu');

// Pause when the player switches tab or window (web only).
const away = () => { if (prefs.data.autopause && game.state === 'playing') game.setState('paused'); input.clear(); };
document.addEventListener('visibilitychange', () => { if (document.hidden) away(); });
addEventListener('blur', away);
addEventListener('resize', () => input.applyTouchMode());

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  game.update(dt);                                  // dt in seconds keeps speed frame-rate independent
  draw(g, game, assets);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
