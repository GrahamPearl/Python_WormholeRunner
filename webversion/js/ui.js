import { settings, W } from './config.js';
import { profile } from './profile.js';
import { prefs } from './utils.js';
import { ACTIONS } from './input.js';
import { PERKS } from './entities/perks.js';
import { describeZone } from './zones.js';

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const keyName = c => c.replace(/^(Key|Digit|Numpad)/, '') || c;
const pretty = c => ({ ArrowUp: '↑', ArrowDown: '↓', ArrowLeft: '←', ArrowRight: '→', Space: 'Space', ShiftLeft: 'Shift', ShiftRight: 'Shift', Escape: 'Esc' }[c] || keyName(c));

/** All the menus and shop screens. They are plain HTML laid over the canvas (accessible, touch friendly). */
export class UI {
  constructor({ game, audio, input, assets, editor, stage }) {
    Object.assign(this, { game, audio, input, assets, editor, stage });
    this.el = stage.querySelector('#screen'); this.name = null; this.tab = 0; this.sel = null; this.cache = new Map();
    this.el.addEventListener('click', e => this.onClick(e)); this.el.addEventListener('input', e => this.onInput(e));
    addEventListener('keydown', e => { if (e.code === 'Escape' && this.name && !this.input.rebind) this.back(); });
    stage.querySelector('#topbar').addEventListener('click', e => this.onTop(e));
    this.refreshTop();
  }
  // ------------------------------------------------------------ plumbing
  open(name, arg) {
    if (this.name === 'editor' && name !== 'editor') this.editor.close();
    this.name = name; this.arg = arg; this.el.classList.remove('hidden'); this.render(); this.input.clear();
    this.el.querySelector('button:not(.alt), button')?.focus({ preventScroll: true });
  }
  close() { if (this.name === 'editor') this.editor.close(); this.name = null; this.el.classList.add('hidden'); this.el.innerHTML = ''; this.input.clear(); }
  render() { const f = this['s_' + this.name]; if (f) this.el.innerHTML = f.call(this, this.arg); }
  back() {
    const n = this.name;
    if (n === 'menu' || n === 'loading') return;
    if (n === 'pause') this.game.setState('playing');
    else if (n === 'gameover' || n === 'victory') this.quit();
    else if (n === 'perk') return;
    else if (n === 'station') this.open('starmap');
    else if (n === 'hangar' && this.arg?.from === 'starmap') this.open('starmap');
    else if (n === 'settings' && this.arg?.from === 'pause') this.open('pause');
    else if (n === 'settings' && this.arg?.from === 'starmap') this.open('starmap');
    else this.open('menu');
  }
  quit() {
    this.game.bank(); this.audio.stopMusic(); this.game.setState('menu');
    if (this.game.zone) this.open('starmap'); else this.open('menu');
  }
  thumb(gfx, size = 56) {
    const k = gfx + size; if (this.cache.has(k)) return this.cache.get(k);
    const c = document.createElement('canvas'); c.width = c.height = size; const sp = settings.get('graphics.' + gfx); let url = '';
    if (sp) { this.assets.draw(c.getContext('2d'), gfx, size / 2, size / 2, 0, Math.min(2, (size - 4) / Math.max(sp.frame_w, sp.frame_h)), 1, 0); url = c.toDataURL(); }
    if (this.assets.sheets.has(sp?.file)) this.cache.set(k, url); return url;
  }
  refreshTop() { const m = this.stage.querySelector('[data-top="mute"]'); if (m) { m.textContent = prefs.data.muted ? '🔇' : '🔊'; m.setAttribute('aria-pressed', prefs.data.muted); } }
  onTop(e) {
    const b = e.target.closest('[data-top]'); if (!b) return;
    if (b.dataset.top === 'mute') { this.audio.setMuted(!prefs.data.muted); if (!prefs.data.muted && this.game.state === 'playing') this.audio.playMusic(); this.refreshTop(); }
    else if (b.dataset.top === 'full') this.toggleFullscreen();
    else if (b.dataset.top === 'pause') { if (this.game.state === 'playing') this.game.setState('paused'); else if (this.game.state === 'paused') this.game.setState('playing'); }
    else if (b.dataset.top === 'settings') { if (this.game.state === 'playing') this.game.setState('paused'); this.open('settings', { from: this.game.state === 'paused' ? 'pause' : this.name === 'starmap' ? 'starmap' : 'menu' }); }
    b.blur();
  }
  toggleFullscreen() {
    const d = document; if (d.fullscreenElement) d.exitFullscreen?.(); else (this.stage.requestFullscreen?.() || Promise.resolve()).catch(() => {});
  }
  shipLine(c) {
    const ab = c.ability?.type ? `<b>${esc(c.ability.name)}</b>: ${esc(c.ability.desc || '')}` : 'No special ability', p = c.passive || [], notes = [];
    if (p.shield_max) notes.push(`Rechargeable shield ${p.shield_max}`); if (p.regen) notes.push(`Self-repair ${p.regen}/s`); if (p.magnet) notes.push('Pulls pickups in'); if (p.credit_bonus) notes.push(`+${Math.round(p.credit_bonus * 100)}% credits`);
    const w = c.weapon?.name ? `${esc(c.weapon.name)} (key 7): ${c.weapon.damage} dmg${c.weapon.count > 1 ? ` x${c.weapon.count}` : ''}${c.weapon.pierce > 1 ? `, pierces ${c.weapon.pierce}` : ''}` : 'Standard weapons only';
    return `<small>Hull ${c.health} · Speed ×${c.speed_mult.toFixed(2)} · Accel ×${c.accel_mult.toFixed(2)} · Turn ×${c.turn_mult.toFixed(2)}</small><small>${ab}</small>${notes.length ? `<small class="good">${notes.join(', ')}</small>` : ''}<small>${w}</small>`;
  }

  // ------------------------------------------------------------ screens
  s_loading() { return '<div class="panel"><h1>WORMHOLE RUNNER</h1><p id="load-text">Loading...</p></div>'; }
  s_menu() {
    const mode = settings.get('game.mode'), ship = settings.get(`ships.${profile.selected}.name`, 'Scout');
    return `<div class="panel"><h1>WORMHOLE RUNNER</h1><p>Dodge the rocks. Find the wormhole.</p>
      <button data-act="play">Play (${esc(mode)})</button><button data-act="voyage">Voyage (star map)</button><button data-act="hangar">Hangar (ships)</button>
      <button data-act="mode" class="alt">Mode: ${esc(mode)}</button><button data-act="editor" class="alt">Game Editor</button><button data-act="settings" class="alt">Settings</button>
      <p class="muted small">${mode === 'classic' ? 'Classic: rocks, aliens, weapons and wormholes' : 'Expedition: + smarter aliens, hazards, rock types, objectives and perks'}. Voyage: travel a star map of zones.</p>
      <p class="stats">Ship: ${esc(ship)} · Credits: ${profile.credits} · Best level ${profile.bestLevel} · Best score ${profile.bestScore}</p>
      <p class="help">${Object.keys(ACTIONS).slice(0, 6).map(a => `${ACTIONS[a]}: <kbd>${pretty(prefs.data.bindings[a])}</kbd>`).join(' · ')} · Weapons <kbd>1-9</kbd> · Pause <kbd>${pretty(prefs.data.bindings.pause)}</kbd></p></div>`;
  }
  s_pause() { return '<div class="panel small-panel"><h1>PAUSED</h1><button data-act="resume">Resume</button><button data-act="settings-pause" class="alt">Settings</button><button data-act="quit" class="alt">Quit to ' + (this.game.zone ? 'star map' : 'menu') + '</button></div>'; }
  s_gameover(i) {
    const z = this.game.zone;
    return `<div class="panel small-panel"><h1 class="red">GAME OVER</h1><p>Score ${i?.score ?? 0} · ${z ? esc(z.name) : 'Level ' + (i?.level ?? 1)}</p>
      <button data-act="retry">${z ? 'Try the zone again' : 'Play again'} (Enter)</button><button data-act="quit" class="alt">${z ? 'Star map' : 'Menu'} (Esc)</button></div>`;
  }
  s_victory(i) {
    const cleared = profile.zonesCleared.filter(z => ['combat', 'boss'].includes(settings.get(`zones.${z}.kind`))).length;
    return `<div class="panel small-panel"><h1>GALAXY SAVED!</h1><p>The Citadel has fallen and the wormholes are safe.</p><p class="stats">Score ${i?.score ?? 0} · Zones cleared ${cleared} · Credits ${profile.credits}</p><button data-act="starmap">Back to the star map</button></div>`;
  }
  s_perk() {
    const p = this.game.local;
    return `<div class="panel"><h1>CHOOSE A PERK</h1><p class="muted">Press 1, 2 or 3 (or click)</p><div class="cards">${p.perkOptions.map((k, i) => `<button class="card" data-act="perk" data-i="${i + 1}"><b>${i + 1}</b><strong>${esc(PERKS[k][0])}</strong><span>${esc(PERKS[k][1])}</span></button>`).join('')}</div></div>`;
  }
  row(it) {
    return `<div class="item ${it.cls || ''}">${it.gfx ? `<img alt="" src="${this.thumb(it.gfx)}" width="56" height="56">` : ''}<div class="grow"><strong>${esc(it.name)}</strong>${it.html || ''}</div>
      <span class="tag ${it.tagCls || ''}">${esc(it.tag)}</span>${it.btn ? `<button data-act="${it.act}" data-id="${esc(it.id)}" ${it.dis ? 'disabled' : ''}>${esc(it.btn)}</button>` : ''}</div>`;
  }
  shipItem(sid, canBuy) {
    const c = settings.get(`ships.${sid}`), own = profile.owned.includes(sid), cur = profile.selected === sid;
    return this.row({ id: sid, act: 'ship', gfx: c.graphic, name: c.name, html: `<small>${esc(c.desc)}</small>` + this.shipLine(c), tag: cur ? 'IN USE' : own ? 'OWNED' : `${c.price} cr`,
      tagCls: cur ? 'good' : own ? 'cyan' : profile.credits >= c.price ? 'gold' : 'bad', btn: cur ? '' : own ? 'Use' : canBuy ? 'Buy' : '', cls: cur ? 'sel' : '' });
  }
  s_hangar(a) {
    const buy = !a?.from && !!settings.get('game.hangar_buying', true);
    return `<div class="panel wide"><div class="bar"><h2>Hangar</h2><span class="gold">Credits: ${profile.credits}</span><button data-act="back" class="alt">Back</button></div>
      ${buy ? '' : '<p class="muted">Ships are bought at stations in Voyage mode. Here you can choose a ship you already own.</p>'}<div class="list">${Object.keys(settings.get('ships')).map(s => this.shipItem(s, buy)).join('')}</div>
      <p class="muted small">Credits exist only in the game. You earn them from kills, rocks (gold pays extra), power-ups, objectives and clearing levels or zones.</p></div>`;
  }
  s_starmap(a) {
    const zones = settings.get('zones'), ids = Object.keys(zones), sel = this.sel && zones[this.sel] ? this.sel : (zones[profile.location] ? profile.location : ids[0]); this.sel = sel;
    const z = zones[sel], unlocked = profile.isUnlocked(sel), safe = ['station', 'planet'].includes(z.kind);
    const lines = ids.flatMap(id => zones[id].links.filter(o => zones[o] && id < o).map(o => `<line x1="${zones[id].pos[0] * 100}%" y1="${zones[id].pos[1] * 100}%" x2="${zones[o].pos[0] * 100}%" y2="${zones[o].pos[1] * 100}%"/>`)).join('');
    const nodes = ids.map(id => {
      const q = zones[id], st = profile.zonesCleared.includes(id) ? 'done' : profile.isUnlocked(id) ? 'open' : 'locked', sh = ['station', 'planet'].includes(q.kind) ? 'sq' : q.kind === 'boss' ? 'boss' : 'circ';
      return `<button class="node ${st} ${sh} ${id === sel ? 'sel' : ''} ${id === profile.location ? 'here' : ''}" style="left:${q.pos[0] * 100}%;top:${q.pos[1] * 100}%" data-act="zone" data-id="${id}" aria-label="${esc(q.name)} (${st})"><span>${esc(q.name)}</span></button>`;
    }).join('');
    return `<div class="panel wide"><div class="bar"><h2>Star map</h2><span class="gold">Ship: ${esc(settings.get(`ships.${profile.selected}.name`))} · Credits ${profile.credits} · Hull ${Math.round(profile.hull * 100)}%</span>
      <button data-act="hangar-from-map" class="alt">Ships</button><button data-act="settings-map" class="alt">Settings</button><button data-act="menu" class="alt">Menu</button></div>
      ${a?.message ? `<p class="gold">${esc(a.message)}</p>` : ''}<div class="map"><svg aria-hidden="true">${lines}</svg>${nodes}</div>
      <div class="info"><h3>${esc(z.name)}${unlocked ? '' : ' <span class="bad">(out of range)</span>'}</h3>${describeZone(z).map(l => `<p>${esc(l)}</p>`).join('')}
      <button data-act="go" ${unlocked ? '' : 'disabled'}>${safe ? 'Dock' : 'Jump here'}</button></div>
      <p class="muted small">■ square = safe stop · ● circle = zone to fly · green = done · gold = in range · grey = out of range · ring = you are here</p></div>`;
  }
  s_station(zid) {
    const z = settings.get(`zones.${zid}`), tabs = (z.shop || []), kind = tabs[Math.min(this.tab, tabs.length - 1)];
    let items = '';
    if (kind === 'ships') { const stock = z.stock || [], others = profile.owned.filter(s => !stock.includes(s)); items = [...stock, ...others].map(s => this.shipItem(s, true)).join(''); }
    else if (kind === 'upgrades') items = Object.entries(settings.get('shop_items')).map(([u, it]) => { const l = profile.upgrades[u] || 0, p = profile.upgradePrice(u); return this.row({ id: u, act: 'upgrade', name: `${it.name}  ${l}/${it.max_level}`, html: `<small>${esc(it.desc)}</small>`, tag: p === null ? 'MAX' : `${p} cr`, tagCls: p === null ? 'good' : profile.credits >= p ? 'gold' : 'bad', btn: p === null ? '' : 'Buy' }); }).join('');
    else if (kind === 'services') {
      const c = profile.repairCost();
      items = this.row({ id: 'repair', act: 'service', name: `Repair hull (${Math.round(profile.hull * 100)}%)`, html: '<small>Restores your hull to 100%. Damage carries over between zones.</small>', tag: c <= 0 ? 'full' : `${c} cr`, tagCls: c <= 0 ? 'good' : profile.credits >= c ? 'gold' : 'bad', btn: c <= 0 ? '' : 'Repair' })
        + [['wingman', 'Your next zone starts with a wingman who fights for you.'], ['ammo', 'Your next zone starts with 50% more ammo.']].map(([k, d]) => { const p = settings.get(`services.${k}.price`); return this.row({ id: k, act: 'service', name: `${settings.get(`services.${k}.name`)} (have ${profile.supplies[k] || 0})`, html: `<small>${d}</small>`, tag: `${p} cr`, tagCls: profile.credits >= p ? 'gold' : 'bad', btn: 'Buy' }); }).join('');
    }
    return `<div class="panel wide"><div class="bar"><h2>${esc(z.name)}</h2><span class="gold">Credits: ${profile.credits}</span><button data-act="starmap" class="alt">Star map</button></div><p class="muted">${esc(z.desc)}</p>
      ${this.msg ? `<p class="${this.msg.ok ? 'good' : 'bad'}">${esc(this.msg.t)}</p>` : ''}<div class="tabs">${tabs.map((t, i) => `<button data-act="tab" data-id="${i}" class="${i === this.tab ? '' : 'alt'}">${t[0].toUpperCase() + t.slice(1)}</button>`).join('')}</div><div class="list">${items}</div></div>`;
  }
  s_settings() {
    const S = k => settings.get(k), b = prefs.data.bindings;
    return `<div class="panel wide"><div class="bar"><h2>Settings</h2><button data-act="back" class="alt">Back</button></div>
      <h3>Sound</h3><label>Music <input type="range" min="0" max="1" step="0.05" value="${S('audio.music_volume')}" data-set="audio.music_volume"></label>
      <label>Effects <input type="range" min="0" max="1" step="0.05" value="${S('audio.sfx_volume')}" data-set="audio.sfx_volume"></label>
      <label><input type="checkbox" data-pref="muted" ${prefs.data.muted ? 'checked' : ''}> Mute all sound</label>
      <h3>Play</h3><label>Touch controls <select data-pref="touch">${['auto', 'on', 'off'].map(o => `<option ${prefs.data.touch === o ? 'selected' : ''}>${o}</option>`).join('')}</select></label>
      <label><input type="checkbox" data-pref="autopause" ${prefs.data.autopause ? 'checked' : ''}> Pause automatically when this tab loses focus</label>
      <button data-act="fullscreen" class="alt">Toggle fullscreen</button>
      <h3>Keys</h3><div class="keys">${Object.entries(ACTIONS).map(([a, l]) => `<div class="krow"><span>${l}</span><button data-act="rebind" data-id="${a}" class="alt">${pretty(b[a])}</button></div>`).join('')}</div>
      <p class="muted small">Weapons use the number keys 1-9. Enter confirms. Click a key, then press the new one.</p><button data-act="resetkeys" class="alt">Reset keys</button>
      <h3>Save data</h3><p class="muted small">Everything is saved in this browser only.</p><button data-act="wipe" class="alt">Reset credits, ships and Voyage progress</button></div>`;
  }

  // ------------------------------------------------------------ events
  onInput(e) {
    const t = e.target;
    if (t.dataset.set) { settings.set(t.dataset.set, parseFloat(t.value)); settings.save(); }
    else if (t.dataset.pref) {
      const k = t.dataset.pref; prefs.data[k] = t.type === 'checkbox' ? t.checked : t.value; prefs.save();
      if (k === 'muted') { this.audio.setMuted(t.checked); this.refreshTop(); } if (k === 'touch') this.input.applyTouchMode();
    }
  }
  say(t, ok) { this.msg = { t, ok }; }
  onClick(e) {
    const b = e.target.closest('[data-act]'); if (!b) return; const id = b.dataset.id, g = this.game;
    switch (b.dataset.act) {
      case 'play': this.audio.ctx(); this.close(); g.start(null); break;
      case 'voyage': this.open('starmap'); break;
      case 'hangar': this.open('hangar'); break;
      case 'hangar-from-map': this.open('hangar', { from: 'starmap' }); break;
      case 'mode': settings.set('game.mode', settings.get('game.mode') === 'classic' ? 'expedition' : 'classic'); settings.save(); this.render(); break;
      case 'editor': this.name = 'editor'; this.el.classList.remove('hidden'); this.arg = { back: 'menu' }; this.editor.open(() => this.open('menu')); break;
      case 'settings': this.open('settings', { from: 'menu' }); break;
      case 'settings-pause': this.open('settings', { from: 'pause' }); break;
      case 'settings-map': this.open('settings', { from: 'starmap' }); break;
      case 'back': this.back(); break;
      case 'menu': this.open('menu'); break;
      case 'resume': g.setState('playing'); break;
      case 'quit': this.quit(); break;
      case 'retry': g.bank(); g.newGame(); this.audio.playMusic(); break;
      case 'starmap': this.open('starmap'); break;
      case 'perk': g.pickPerk(g.local, +b.dataset.i); break;
      case 'ship': this.msg = null; if (profile.owned.includes(id)) { profile.select(id); this.say(`${settings.get(`ships.${id}.name`)} selected`, true); } else if (profile.buy(id)) { profile.select(id); this.say(`Bought ${settings.get(`ships.${id}.name`)}!`, true); } else this.say('Not enough credits', false); this.render2(); break;
      case 'upgrade': if (profile.buyUpgrade(id)) this.say(`Upgraded ${settings.get(`shop_items.${id}.name`)}!`, true); else this.say('Not enough credits', false); this.render(); break;
      case 'service':
        if (id === 'repair') this.say(profile.repair() ? 'Hull repaired' : 'Not enough credits', profile.hull >= 1);
        else this.say(profile.buySupply(id) ? 'Bought! It is used up at the start of your next zone' : 'Not enough credits', profile.supplies[id] > 0);
        this.render(); break;
      case 'tab': this.tab = +id; this.msg = null; this.render(); break;
      case 'zone': if (this.sel === id && e.detail > 1) { this.go(); break; } this.sel = id; this.render(); break;
      case 'go': this.go(); break;
      case 'fullscreen': this.toggleFullscreen(); break;
      case 'rebind': b.textContent = 'Press a key...'; this.input.startRebind(code => { this.input.setBinding(id, code); this.render(); }); break;
      case 'resetkeys': this.input.resetBindings(); this.render(); break;
      case 'wipe': if (confirm('Reset your credits, owned ships and Voyage progress?')) { profile.wipe(); this.render(); } break;
    }
  }
  render2() { this.render(); }
  go() {
    const zid = this.sel, z = settings.get(`zones.${zid}`); if (!profile.isUnlocked(zid)) return;
    if (['station', 'planet'].includes(z.kind)) { profile.location = zid; profile.clearZone(zid); this.tab = 0; this.msg = null; this.open('station', zid); }
    else { this.audio.ctx(); this.close(); this.game.start(zid); }
  }
}
export { W, keyName };
