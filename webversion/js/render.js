import { W, H, COLORS, settings } from './config.js';

const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

/** Draws one frame: the world (zoomed so it all fits) and then the HUD. */
export function draw(g, game, assets) {
  const w = game.world, z = game.zoom, Y = y => w.h - y;
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#060816'; g.fillRect(0, 0, W, H);
  g.save(); g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-w.w / 2, -w.h / 2);
  const line = 3 / Math.max(z, 0.2), spr = o => assets.draw(g, o.gfx, o.x, Y(o.y), o.angle, o.sc, o.alpha, o.t, o.tint);
  g.strokeStyle = 'rgba(90,120,200,.35)'; g.lineWidth = line; g.strokeRect(0, 0, w.w, w.h);
  for (const [x, y, b] of game.stars) { g.fillStyle = `rgb(${b},${b},${Math.min(255, b + 20)})`; g.fillRect(x, Y(y), line, line); }
  hazards(g, game, Y, line);
  if (game.wormhole) spr(game.wormhole);
  game.powerups.forEach(spr); game.rocks.forEach(spr); if (game.freighter) spr(game.freighter);
  for (const a of game.aliens) { spr(a); bar(g, a.x, Y(a.y) - a.r - 13, Math.max(30, a.r * 2), 5, a.health / a.maxHealth, '#3c1414', COLORS.red); }
  for (const a of game.allies) { spr(a); bar(g, a.x, Y(a.y) - a.r - 13, Math.max(30, a.r * 2), 5, a.health / a.maxHealth, '#14324a', '#5ac8ff'); }
  game.bullets.forEach(spr);
  for (const b of game.bullets) if (b.kind === 'mine' && b.blast && b.arm <= 0) { g.beginPath(); g.arc(b.x, Y(b.y), b.blast * 0.45, 0, 7); g.strokeStyle = 'rgba(255,90,90,.25)'; g.lineWidth = line * 0.6; g.stroke(); }
  const fr = game.freighter; if (fr) bar(g, fr.x, Y(fr.y) - fr.r - 16, 70, 6, fr.health / fr.maxHealth, '#143c1e', '#5ae678');
  for (const p of game.alivePlayers()) { const s = p.ship; spr(s); shipFx(g, s, Y, line); }
  for (const e of game.effects) {
    const k = e.age / e.dur, r = e.r * (0.3 + 0.7 * k); g.beginPath(); g.arc(e.x, Y(e.y), r, 0, 7);
    g.strokeStyle = rgba(e.color, 1 - k); g.lineWidth = line; g.stroke(); g.fillStyle = rgba(e.color, (1 - k) / 4); g.fill();
  }
  g.restore();
  hud(g, game);
}
function bar(g, cx, y, bw, bh, f, back, front) { g.fillStyle = back; g.fillRect(cx - bw / 2, y, bw, bh); g.fillStyle = front; g.fillRect(cx - bw / 2, y, bw * Math.max(0, Math.min(1, f)), bh); }
function circle(g, x, y, r, fill, stroke, lw) { g.beginPath(); g.arc(x, y, r, 0, 7); if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw; g.stroke(); } }
function shipFx(g, s, Y, line) {
  const y = Y(s.y);
  if (s.shieldT > 0) circle(g, s.x, y, s.r + 12, null, COLORS.cyan, line);
  if (s.deflecting) circle(g, s.x, y, s.r + 16, 'rgba(255,255,255,.16)', 'rgba(255,255,255,.9)', line * 1.5);
  if (s.healing) { const hr = s.ability.range || 360; circle(g, s.x, y, hr, 'rgba(90,255,140,.09)', 'rgba(90,255,140,.47)', line); }
  if (s.shieldMax > 0 && s.shieldHp > 1) circle(g, s.x, y, s.r + 7, null, 'rgba(110,150,255,.6)', line);
}
function hazards(g, game, Y, line) {
  const t = game.time;
  for (const h of game.hazards) {
    const y = Y(h.y);
    if (h.kind === 'nebula') { for (const k of [1, .75, .5]) circle(g, h.x, y, h.radius * k, 'rgba(150,90,210,.1)'); circle(g, h.x, y, h.radius, null, 'rgba(190,140,255,.28)', line); }
    else if (h.kind === 'ion') { const p = .85 + .15 * Math.sin(t * 6); circle(g, h.x, y, h.radius, 'rgba(90,150,255,.09)'); circle(g, h.x, y, h.radius * p, null, 'rgba(140,200,255,.63)', line); circle(g, h.x, y, h.radius * .55 * p, null, 'rgba(140,200,255,.35)', line * .7); }
    else if (h.kind === 'blackhole') { circle(g, h.x, y, h.radius, null, 'rgba(150,100,255,.14)', line * .7); for (const k of [.55, .35, .2]) circle(g, h.x, y, h.radius * k, null, 'rgba(170,120,255,.24)', line * .7); circle(g, h.x, y, h.core + 6, '#7846c8'); circle(g, h.x, y, h.core, '#000'); }
  }
  const f = game.flare; if (f) {
    const top = Y(f.y) - f.h / 2;
    if (f.phase === 0) { g.fillStyle = `rgba(255,170,40,${0.16 + 0.16 * Math.abs(Math.sin(f.t * 8))})`; g.fillRect(f.x - f.w / 2, top, f.w, f.h); g.strokeStyle = 'rgba(255,200,80,.8)'; g.lineWidth = line * 1.3; g.strokeRect(f.x - f.w / 2, top, f.w, f.h); }
    else { g.fillStyle = 'rgba(255,240,180,.75)'; g.fillRect(f.x - f.w / 2, top, f.w, f.h); }
  }
}

// ---------------------------------------------------------------- HUD (screen space)
function hud(g, game) {
  const p = game.local, s = p.ship, S = k => settings.get(k);
  const T = (t, x, y, c = COLORS.white, size = 14, al = 'left', bold = false) => { g.font = `${bold ? 'bold ' : ''}${size}px "Courier New", monospace`; g.fillStyle = c; g.textAlign = al; g.fillText(t, x, y); };
  const B = (x, y, bw, bh, f, c) => { g.fillStyle = '#282c3e'; g.fillRect(x, y, bw, bh); g.fillStyle = c; g.fillRect(x, y, bw * Math.max(0, Math.min(1, f)), bh); g.strokeStyle = '#fff'; g.lineWidth = 2; g.strokeRect(x, y, bw, bh); };
  const hf = s.health / s.maxHealth; B(20, 20, 240, 16, hf, hf > 0.35 ? COLORS.green : COLORS.red); T('HEALTH', 270, 33, COLORS.grey, 12);
  const boost = s.boost > 0 ? S('ship.boost_multiplier') : 1; B(20, 44, 240, 12, s.speed / (S('ship.max_speed') * s.speedMult * boost), COLORS.orange); T('SPEED', 270, 55, COLORS.grey, 12);
  let y = 80; if (s.boost > 0) { T(`SPEED BOOST ${s.boost.toFixed(1)}s`, 20, y, COLORS.orange, 13); y += 20; } if (s.shieldT > 0) T(`INVINCIBLE ${s.shieldT.toFixed(1)}s`, 20, y, COLORS.cyan, 13);
  T(`SCORE ${Math.floor(p.score)}`, W - 20, 36, COLORS.white, 18, 'right'); T(game.zone ? `${game.zone.name.toUpperCase()}   AREA x${game.worldScale.toFixed(2)}` : `LEVEL ${game.level}   AREA x${game.worldScale.toFixed(2)}`, W - 20, 60, COLORS.gold, 14, 'right');
  if (game.expedition || p.creditsRun) T(`CREDITS +${Math.floor(p.creditsRun)}`, W - 20, 90, COLORS.gold, 14, 'right');
  const ot = game.objectiveText(); if (ot) T(ot, W / 2, 92, '#8ce6ff', 15, 'center');
  if (game.wormhole) T(`WORMHOLE OPEN  ${Math.max(0, game.wormhole.lifetime - game.wormhole.age).toFixed(1)}s`, W / 2, 38, '#c896ff', 16, 'center');
  const boss = game.aliens.find(a => a.kind === 'mothership'); if (boss) { B(W / 2 - 220, 58, 440, 14, boss.health / boss.maxHealth, COLORS.red); T('MOTHERSHIP', W / 2, 54, COLORS.red, 13, 'center'); }
  const ab = s.abilityType && s.ability; if (ab) {
    if (s.shieldMax > 0) { B(W - 290, 110, 270, 10, s.shieldHp / s.shieldMax, '#6e96ff'); T('SHIELD', W - 296, 120, COLORS.grey, 11, 'right'); }
    const cd = s.abilityCd / Math.max(0.1, ab.cooldown * p.cdMult), ready = cd <= 0; B(W - 290, H - 62, 270, 16, 1 - Math.min(1, cd), ready ? COLORS.green : COLORS.orange);
    let label = `[ABILITY] ${ab.name}` + (ready ? '  READY' : ''); if (s.active > 0) label = `${ab.name} ACTIVE ${s.active.toFixed(1)}s`; if (s.jammed) label = `${ab.name} - ION STORM, OFFLINE`;
    T(label, W - 20, H - 74, ready ? COLORS.cyan : COLORS.grey, 13, 'right');
  } else if (s.shieldMax > 0) { B(W - 290, H - 62, 270, 10, s.shieldHp / s.shieldMax, '#6e96ff'); T('SHIELD', W - 296, H - 53, COLORS.grey, 11, 'right'); }
  let x = 20;
  for (let k = 1; k <= 9; k++) {
    const c = p.weapons.cfg(k); if (!c.enabled) continue; const ok = p.weapons.unlocked(k, game.level), sel = k === p.weapons.slot, am = p.weapons.ammo[k];
    g.fillStyle = ok ? '#1c2038' : '#141622'; g.fillRect(x, H - 56, 112, 44); g.strokeStyle = sel ? COLORS.gold : COLORS.grey; g.lineWidth = sel ? 3 : 1; g.strokeRect(x, H - 56, 112, 44);
    const col = ok && am === 0 ? COLORS.red : ok ? COLORS.white : COLORS.grey; T(`${k} ${c.name}`, x + 6, H - 34, col, 12); T(!ok ? `unlocks L${c.unlock_level}` : am < 0 ? 'ammo: inf' : `ammo: ${am}`, x + 6, H - 20, col, 11); x += 118;
  }
  if (game.noticeT > 0) T(game.notice, W / 2, H - 84, COLORS.white, 16, 'center');
  if (game.banner > 0) { T(game.bannerText, W / 2, H / 2 - 120, COLORS.gold, 40, 'center', true); T(game.bannerSub, W / 2, H / 2 - 85, COLORS.grey, 14, 'center'); }
  if (!p.alive && game.state === 'playing') T('YOUR SHIP IS DOWN', W / 2, H / 2 - 120, COLORS.red, 20, 'center');
  if (game.state === 'perk') { g.fillStyle = 'rgba(0,0,0,.5)'; g.fillRect(0, 0, W, 80); T(`CHOOSE A PERK  (${Math.ceil(game.perkTimer)}s)`, W / 2, 50, COLORS.gold, 28, 'center', true); }
}
