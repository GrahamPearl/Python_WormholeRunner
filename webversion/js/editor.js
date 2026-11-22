import { settings, DEFAULTS } from './config.js';

const ALIEN_FIELDS = {
  drifter: [['Wave width', 'wave_amp', 'float', 10, 0, 500], ['Wave speed', 'wave_freq', 'float', 0.1, 0.1, 10]],
  chaser: [['Turn rate (deg/s)', 'turn_rate', 'float', 10, 10, 720], ['Dies when it rams you', 'dies_on_ram', 'bool']],
  sniper: [['Fire interval (s)', 'fire_interval', 'float', 0.1, 0.2, 20], ['Bullet speed', 'bullet_speed', 'float', 20, 50, 2000], ['Bullet damage', 'bullet_damage', 'int', 1, 1, 200], ['Keep distance', 'keep_distance', 'float', 20, 50, 1500]],
  swarm: [['Fire interval (s)', 'fire_interval', 'float', 0.1, 0.2, 20], ['Bullet speed', 'bullet_speed', 'float', 20, 50, 2000], ['Bullet damage', 'bullet_damage', 'int', 1, 1, 200], ['Orbit radius', 'orbit_radius', 'float', 20, 60, 1500], ['Orbit speed (deg/s)', 'orbit_speed', 'float', 5, -360, 360], ['Group size', 'group_size', 'int', 1, 1, 12]],
  seeker: [['Fire interval (s)', 'fire_interval', 'float', 0.1, 0.2, 20], ['Bullet speed', 'bullet_speed', 'float', 20, 50, 2000], ['Bullet damage', 'bullet_damage', 'int', 1, 1, 200], ['Detect range (sees cloaked ships)', 'detect_range', 'float', 50, 100, 3000]],
  teleporter: [['Blink every (s)', 'blink_interval', 'float', 0.5, 1, 30], ['Shots per burst', 'burst_count', 'int', 1, 1, 10], ['Bullet speed', 'bullet_speed', 'float', 20, 50, 2000], ['Bullet damage', 'bullet_damage', 'int', 1, 1, 200], ['Blink distance from you', 'ring', 'float', 20, 100, 1500]],
  minelayer: [['Drop a mine every (s)', 'mine_interval', 'float', 0.5, 0.5, 30], ['Mine damage', 'mine_damage', 'int', 5, 1, 300], ['Mine blast radius', 'mine_blast', 'float', 10, 20, 400]],
  mothership: [['Boss every N levels', 'boss_every', 'int', 1, 1, 50], ['Fire interval (s)', 'fire_interval', 'float', 0.1, 0.2, 20], ['Bullet speed', 'bullet_speed', 'float', 20, 50, 2000], ['Bullet damage', 'bullet_damage', 'int', 1, 1, 200], ['Keep distance', 'keep_distance', 'float', 20, 50, 1500], ['Launch fighter every (s)', 'spawn_interval', 'float', 0.5, 1, 60], ['Ring bullets', 'ring_bullets', 'int', 1, 3, 48]],
};
const title = k => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

/** Builds the list of editable sections (build_rows in editor_view.py). Each row: [label, path, kind, step, lo, hi, options]. */
export function buildSections() {
  const S = [], sec = (name, rows = [], extra = {}) => { const s = { name, rows, ...extra }; S.push(s); return s.rows; };
  const f = (rows, ...a) => rows.push(a);
  let r;
  r = sec('Game mode, credits and sound'); f(r, 'Mode (classic / expedition)', 'game.mode', 'choice', 0, 0, 0, ['classic', 'expedition']); f(r, 'Buy ships in the main-menu Hangar', 'game.hangar_buying', 'bool');
  f(r, 'Starting credits (new profile)', 'credits.start_credits', 'int', 100, 0, 100000);
  for (const [k, lab, st, mx] of [['alien_factor', 'Credits per alien score point', 0.05, 5], ['rock_per_size', 'Credits per rock size', 1, 100], ['gold_rock', 'Gold rock bonus per size', 5, 1000], ['powerup', 'Credits per power-up', 1, 100], ['crystal', 'Credits per crystal', 1, 200], ['rescue', 'Credits per rescued pod', 5, 500], ['level_clear', 'Credits per level cleared (x level)', 10, 1000], ['objective', 'Credits for objective (x level)', 10, 1000]])
    f(r, lab, `credits.${k}`, st < 1 ? 'float' : 'int', st, 0, mx);
  f(r, 'Music volume', 'audio.music_volume', 'float', 0.05, 0, 1); f(r, 'Sound effects volume', 'audio.sfx_volume', 'float', 0.05, 0, 1);
  for (const [sid, c] of Object.entries(settings.get('ships'))) {
    r = sec(`Ship: ${c.name}`, [], { gfx: c.graphic }); const p = `ships.${sid}.`;
    f(r, 'Price (credits)', p + 'price', 'int', 50, 0, 100000); f(r, 'Hull strength', p + 'health', 'int', 5, 10, 1000);
    f(r, 'Speed multiplier', p + 'speed_mult', 'float', 0.05, 0.3, 3); f(r, 'Acceleration multiplier', p + 'accel_mult', 'float', 0.05, 0.3, 3); f(r, 'Turn multiplier', p + 'turn_mult', 'float', 0.05, 0.3, 3);
    if (c.ability?.type) { f(r, 'Ability recharge (s)', p + 'ability.cooldown', 'float', 0.5, 1, 120); if ('duration' in c.ability) f(r, 'Ability duration (s)', p + 'ability.duration', 'float', 0.5, 0.5, 30); }
    if (c.weapon?.name) { f(r, 'Own weapon damage', p + 'weapon.damage', 'float', 1, 1, 1000); f(r, 'Own weapon delay (s)', p + 'weapon.cooldown', 'float', 0.05, 0.05, 10); }
  }
  r = sec('Rock types'); for (const k of Object.keys(settings.get('rock_types'))) { f(r, `${title(k)} rock: from level`, `rock_types.${k}.min_level`, 'int', 1, 1, 99); f(r, `${title(k)} rock: chance weight`, `rock_types.${k}.weight`, 'int', 1, 0, 100); }
  r = sec('Hazards and objectives');
  for (const [k, lab] of [['nebula_from', 'Nebula from level'], ['blackhole_from', 'Black hole from level'], ['ion_from', 'Ion storm from level'], ['flare_from', 'Solar flare from level']]) f(r, lab, `hazards.${k}`, 'int', 1, 1, 99);
  f(r, 'Solar flare every (s)', 'hazards.flare_interval', 'float', 2, 8, 300); f(r, 'Solar flare damage', 'hazards.flare_damage', 'int', 5, 1, 300); f(r, 'Aliens notice hidden ships within', 'hazards.cloak_detect', 'float', 20, 0, 1000);
  f(r, 'Objectives enabled', 'objectives.enabled', 'bool'); f(r, 'Crystals to collect (base)', 'objectives.crystals_base', 'int', 1, 1, 30); f(r, 'Pods to rescue (base)', 'objectives.pods_base', 'int', 1, 1, 20);
  f(r, 'Escort time (s)', 'objectives.escort_seconds', 'float', 5, 10, 300); f(r, 'Freighter health', 'objectives.freighter_health', 'int', 10, 20, 2000);
  r = sec('World and camera'); f(r, 'World growth per level', 'world.growth_per_level', 'float', 0.05, 0, 2); f(r, 'Max world size (x screen)', 'world.max_scale', 'float', 0.25, 1, 6); f(r, 'Zoom-out speed', 'world.zoom_speed', 'float', 0.1, 0.1, 10);
  r = sec('Gravity'); f(r, 'Strength', 'physics.gravity', 'float', 25000, 0, 5e6); f(r, 'Max pull per rock', 'physics.max_accel', 'float', 20, 0, 2000); f(r, 'Softening distance', 'physics.softening', 'float', 5, 1, 300); f(r, 'Drift damping', 'physics.drift_damping', 'float', 0.1, 0, 5);
  r = sec('Ship (default numbers)');
  for (const [k, lab, t, st, lo, hi] of [['max_speed', 'Max speed', 'float', 20, 50, 1500], ['acceleration', 'Acceleration', 'float', 10, 10, 1500], ['turn_rate', 'Turn rate (deg/s)', 'float', 10, 30, 720], ['max_health', 'Max health', 'int', 5, 10, 1000], ['hit_damage', 'Damage per rock hit', 'int', 5, 1, 1000], ['health_gain', 'Health power-up gain', 'int', 5, 1, 1000], ['grace_time', 'Invincible after hit (s)', 'float', 0.1, 0, 10], ['boost_multiplier', 'Speed boost multiplier', 'float', 0.1, 1, 4]]) f(r, lab, `ship.${k}`, t, st, lo, hi);
  r = sec('Rocks');
  for (const [k, lab, t, st, lo, hi] of [['count', 'Starting count', 'int', 1, 1, 60], ['min_speed', 'Min speed', 'float', 5, 5, 600], ['max_speed', 'Max speed', 'float', 5, 5, 600], ['split_angle', 'Split angle', 'float', 5, 5, 85], ['split_speed', 'Fragment speed factor', 'float', 0.05, 0.5, 3], ['max_rocks', 'Max rocks on screen', 'int', 1, 2, 150], ['respawn_time', 'Replacement rock delay (s)', 'float', 0.5, 0.5, 60], ['alien_damage', 'Damage to aliens hitting rocks', 'int', 5, 0, 500]]) f(r, lab, `rocks.${k}`, t, st, lo, hi);
  f(r, 'Split when rocks collide', 'rocks.split_on_rock_hit', 'bool');
  for (let n = 1; n <= 9; n++) {
    const p = `weapons.w${n}.`; r = sec(`Weapon ${n}: ${settings.get(p + 'name')}`, [], { gfx: `bullet_w${n}` }); f(r, 'Enabled', p + 'enabled', 'bool'); f(r, 'Type', p + 'type', 'choice', 0, 0, 0, ['bolt', 'homing', 'mine', 'pulse']);
    for (const [k, lab, t, st, lo, hi] of [['unlock_level', 'Unlocks at level', 'int', 1, 1, 99], ['damage', 'Damage', 'float', 1, 1, 1000], ['speed', 'Shot speed', 'float', 50, 0, 3000], ['cooldown', 'Delay between shots (s)', 'float', 0.05, 0.02, 10], ['range', 'Range (px)', 'float', 50, 50, 5000], ['ammo', 'Starting ammo (-1 = unlimited)', 'int', 5, -1, 999], ['ammo_pack', 'Ammo per pickup', 'int', 5, 0, 999], ['count', 'Shots per trigger', 'int', 1, 1, 15], ['spread', 'Spread angle', 'float', 2, 0, 180], ['pierce', 'Targets it passes through', 'int', 1, 1, 20], ['turn_rate', 'Homing turn rate (deg/s)', 'float', 10, 0, 720], ['blast_radius', 'Blast radius (mines)', 'float', 10, 0, 600], ['fuse', 'Mine fuse (s)', 'float', 0.5, 0.5, 30]]) f(r, lab, p + k, t, st, lo, hi);
  }
  for (const [kind, extra] of Object.entries(ALIEN_FIELDS)) {
    const p = `aliens.${kind}.`; r = sec(`Alien: ${title(kind)}`, [], { gfx: `alien_${kind}` }); f(r, 'Enabled', p + 'enabled', 'bool'); f(r, 'Appears from level', p + 'min_level', 'int', 1, 1, 99);
    f(r, 'Health', p + 'health', 'float', 5, 1, 5000); f(r, 'Speed', p + 'speed', 'float', 10, 10, 800); f(r, 'Damage when touching ship', p + 'contact_damage', 'int', 5, 0, 500); f(r, 'Score', p + 'score', 'int', 10, 0, 100000);
    for (const [lab, key, t, st = 1, lo = 0, hi = 1e9] of extra) f(r, lab, p + key, t, st, lo, hi);
  }
  r = sec('Friendly ships'); for (const [k, c] of Object.entries(settings.get('allies'))) { f(r, `${c.name}: health`, `allies.${k}.health`, 'float', 5, 5, 1000); f(r, `${c.name}: speed`, `allies.${k}.speed`, 'float', 10, 0, 800); if ('damage' in c) f(r, `${c.name}: damage`, `allies.${k}.damage`, 'float', 1, 1, 200); }
  r = sec('Voyage: shop and services');
  for (const [u, it] of Object.entries(settings.get('shop_items'))) { f(r, `${it.name}: base price`, `shop_items.${u}.price`, 'int', 10, 10, 5000); f(r, `${it.name}: max level`, `shop_items.${u}.max_level`, 'int', 1, 1, 10); }
  f(r, 'Repair: credits per 1% hull', 'services.repair.price_per_percent', 'float', 0.25, 0, 20); f(r, 'Wingman contract price', 'services.wingman.price', 'int', 10, 0, 2000); f(r, 'Ammo pack price', 'services.ammo.price', 'int', 10, 0, 2000);
  for (const [zid, z] of Object.entries(settings.get('zones'))) if (z.kind === 'combat' || z.kind === 'boss') {
    r = sec(`Zone: ${z.name}`); f(r, 'Difficulty level', `zones.${zid}.level`, 'int', 1, 1, 30); f(r, 'Reward (credits)', `zones.${zid}.reward`, 'int', 10, 0, 10000);
    if (z.time_limit) f(r, 'Time limit (s)', `zones.${zid}.time_limit`, 'int', 10, 20, 900); if (z.gravity) f(r, 'Gravity factor', `zones.${zid}.gravity`, 'float', 0.1, 0.2, 4);
    if (z.objective?.need !== undefined) f(r, 'Objective: how many', `zones.${zid}.objective.need`, 'int', 1, 1, 30); if (z.objective?.seconds) f(r, 'Objective: seconds', `zones.${zid}.objective.seconds`, 'int', 5, 5, 300);
  }
  r = sec('Timing');
  for (const [k, lab, st, lo, hi] of [['powerup_interval', 'Power-up every (s)', 0.5, 1, 60], ['powerup_lifetime', 'Power-up stays (s)', 0.5, 2, 60], ['wormhole_min_delay', 'Wormhole earliest (s)', 0.5, 1, 120], ['wormhole_max_delay', 'Wormhole latest (s)', 0.5, 1, 120], ['wormhole_lifetime', 'Wormhole stays (s)', 0.5, 2, 60], ['speed_boost_time', 'Speed boost lasts (s)', 0.5, 1, 60], ['invincible_time', 'Invincibility lasts (s)', 0.5, 1, 60]]) f(r, lab, `timing.${k}`, 'float', st, lo, hi);
  r = sec('Difficulty per level');
  for (const [k, lab, t, st, lo, hi] of [['extra_rocks_per_level', 'Extra rocks', 'int', 1, 0, 10], ['speed_per_level', 'Rock speed increase', 'float', 0.02, 0, 1], ['gravity_per_level', 'Gravity increase', 'float', 0.02, 0, 2], ['alien_health_per_level', 'Alien health increase', 'float', 0.02, 0, 2], ['alien_drop_chance', 'Alien power-up drop chance', 'float', 0.05, 0, 1]]) f(r, lab, `difficulty.${k}`, t, st, lo, hi);
  r = sec('Sound volumes (press play to test)'); for (const ev of Object.keys(settings.get('audio.events'))) f(r, ev, `audio.events.${ev}.volume`, 'float', 0.05, 0, 1, null, true);
  r = sec('Images (sprite sheets)');
  for (const [g, sp] of Object.entries(settings.get('graphics'))) { f(r, `${g}: image file`, `graphics.${g}.file`, 'text', 0, 0, 0, null, false, g); for (const [k, lab, t, st, lo, hi] of [['frame_w', 'tile width (px)', 'int', 1, 1, 2048], ['frame_h', 'tile height (px)', 'int', 1, 1, 2048], ['frames', 'tile count', 'int', 1, 1, 256], ['fps', 'animation fps (0 = still)', 'float', 1, 0, 60], ['scale', 'scale', 'float', 0.1, 0.1, 8]]) f(r, `${g}: ${lab}`, `graphics.${g}.${k}`, t, st, lo, hi, null, false, g); void sp; }
  return S;
}

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmt = v => (typeof v === 'number' ? +v.toPrecision(6) : v);

/** The live editor: change any number, see it in the next game. Saves to localStorage. */
export class Editor {
  constructor(root, audio, assets) { this.root = root; this.audio = audio; this.assets = assets; this.dirty = false; this.preview = null; this.raf = 0; }
  open(onClose) {
    this.onClose = onClose; this.sections = buildSections(); this.dirty = false;
    const body = this.sections.map((s, i) => `<details data-sec="${i}"><summary>${esc(s.name)} <span class="muted">(${s.rows.length})</span></summary>${s.gfx ? `<canvas class="pv" width="64" height="64" data-gfx="${esc(s.gfx)}"></canvas>` : ''}<div class="rows">${s.rows.map((row, j) => this.rowHtml(row, i, j)).join('')}</div></details>`).join('');
    this.root.innerHTML = `<div class="panel wide"><div class="bar"><h2>Game Editor</h2><input type="search" id="ed-filter" placeholder="Search settings..." aria-label="Search settings">
      <button data-ed="save">Save</button><button data-ed="resetall" class="alt">Reset all</button><button data-ed="close" class="alt">Back</button><span id="ed-status" class="muted">All changes saved</span></div>
      <p class="muted">Changes apply to the next game you start. Image files must be PNG sheets in <code>assets/images/</code>.</p><canvas id="ed-pv" width="96" height="96" class="pv big"></canvas><div id="ed-body">${body}</div></div>`;
    this.root.onclick = e => this.click(e); this.root.oninput = e => this.input(e); this.root.onchange = e => this.input(e, true);
    this.root.querySelector('#ed-filter').oninput = e => this.filter(e.target.value);
    this.loop();
  }
  close() { cancelAnimationFrame(this.raf); this.root.onclick = this.root.oninput = this.root.onchange = null; }
  rowHtml([label, path, kind, step, lo, hi, opts, snd, gfx], i, j) {
    const v = settings.get(path), id = `ed-${i}-${j}`; let inp;
    if (kind === 'bool') inp = `<input type="checkbox" id="${id}" data-path="${path}" ${v ? 'checked' : ''}>`;
    else if (kind === 'choice') inp = `<select id="${id}" data-path="${path}">${opts.map(o => `<option ${o === v ? 'selected' : ''}>${o}</option>`).join('')}</select>`;
    else if (kind === 'text') inp = `<input type="text" id="${id}" data-path="${path}" value="${esc(v ?? '')}" ${gfx ? `data-gfx="${gfx}"` : ''}>`;
    else inp = `<input type="number" id="${id}" data-path="${path}" data-kind="${kind}" step="${step}" min="${lo}" max="${hi}" value="${fmt(v)}" ${gfx ? `data-gfx="${gfx}"` : ''}>`;
    return `<div class="row" data-label="${esc((label + ' ' + path).toLowerCase())}"><label for="${id}">${esc(label)}</label>${inp}${snd ? `<button data-snd="${esc(path.split('.')[2])}" class="mini" aria-label="Play sound">▶</button>` : ''}<button data-reset="${path}" data-for="${id}" class="mini alt" title="Reset to default">↺</button></div>`;
  }
  status(t, dirty) { this.dirty = dirty; const el = this.root.querySelector('#ed-status'); if (el) { el.textContent = t; el.className = dirty ? 'warn' : 'muted'; } }
  input(e, commit = false) {
    const t = e.target, path = t.dataset?.path; if (!path) return;
    let v; if (t.type === 'checkbox') v = t.checked; else if (t.type === 'number') { v = parseFloat(t.value); if (!Number.isFinite(v)) return; v = Math.max(+t.min, Math.min(+t.max, v)); if (t.dataset.kind === 'int') v = Math.round(v); } else v = t.value;
    settings.set(path, v); this.status('Unsaved changes', true); if (t.dataset.gfx) this.preview = t.dataset.gfx; if (commit && t.type === 'number') t.value = fmt(v);
  }
  click(e) {
    const t = e.target.closest('button'); if (!t) { const pv = e.target.closest('[data-gfx]'); if (pv) this.preview = pv.dataset.gfx; return; }
    if (t.dataset.reset) { settings.reset(t.dataset.reset); const el = this.root.querySelector('#' + t.dataset.for), v = settings.get(t.dataset.reset); if (el.type === 'checkbox') el.checked = !!v; else el.value = fmt(v); this.status('Unsaved changes', true); }
    else if (t.dataset.snd) this.audio.play(t.dataset.snd);
    else if (t.dataset.ed === 'save') this.status(settings.save() ? 'Saved' : 'Could not save (storage blocked)', false);
    else if (t.dataset.ed === 'resetall') { if (confirm('Reset every setting to the defaults?')) { settings.resetAll(); this.open(this.onClose); } }
    else if (t.dataset.ed === 'close') { if (this.dirty) settings.save(); this.close(); this.onClose?.(); }
  }
  filter(q) {
    q = q.trim().toLowerCase();
    for (const d of this.root.querySelectorAll('details[data-sec]')) {
      let any = false; for (const r of d.querySelectorAll('.row')) { const show = !q || r.dataset.label.includes(q) || d.firstChild.textContent.toLowerCase().includes(q); r.classList.toggle('hidden', !show); any ||= show; }
      d.classList.toggle('hidden', !any); if (q && any) d.open = true;
    }
  }
  loop() {
    const c = this.root.querySelector('#ed-pv'); if (!c) return; const g = c.getContext('2d'), t = performance.now() / 1000;
    g.clearRect(0, 0, 96, 96); const sp = this.preview && settings.get('graphics.' + this.preview);
    if (sp) { const sc = Math.min(8, 80 / Math.max(sp.frame_w, sp.frame_h)); this.assets.draw(g, this.preview, 48, 48, 0, sc, 1, t); g.fillStyle = '#96a0b9'; g.font = '10px monospace'; g.fillText(this.preview, 2, 92); }
    for (const pv of this.root.querySelectorAll('canvas.pv:not(.big)')) { const g2 = pv.getContext('2d'); g2.clearRect(0, 0, 64, 64); if (pv.closest('details')?.open) this.assets.draw(g2, pv.dataset.gfx, 32, 32, 0, Math.min(2, 56 / Math.max(...[settings.get(`graphics.${pv.dataset.gfx}.frame_w`) || 1, settings.get(`graphics.${pv.dataset.gfx}.frame_h`) || 1])), 1, t); }
    this.raf = requestAnimationFrame(() => this.loop());
  }
}
export { DEFAULTS };
