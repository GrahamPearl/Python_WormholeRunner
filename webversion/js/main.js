import { AssetLoader } from './assets.js';
import { InputHandler } from './input.js';
import { Game } from './game.js';

const $ = id => document.getElementById(id);
const ids = ['loading', 'menu', 'paused', 'gameover'];
const ui = {   // the only code that touches the HTML overlays
  show(name) { ids.forEach(i => $(i).classList.toggle('hidden', i !== name)); },
  best(s) { $('best').textContent = `Best score ${s.bestScore}   Best level ${s.bestLevel}`; },
  final(score, level) { $('final').textContent = `Score ${score}   Level ${level}`; },
};

const assets = await new AssetLoader().load(f => { $('loading').querySelector('p').textContent = `Loading... ${Math.round(f * 100)}%`; });
const game = new Game($('game'), assets, new InputHandler(), ui);
$('play').addEventListener('click', () => game.newGame());

let last = performance.now();
function frame(now) {
  game.update((now - last) / 1000); last = now;      // dt in seconds keeps speed frame-rate independent
  game.draw();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
