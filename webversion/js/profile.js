import { settings } from './config.js';
import { store } from './utils.js';

/** Saved profile (localStorage): credits, ships, best scores and Voyage progress. Credits exist only in the game. */
export class Profile {
  static KEY = 'wormholeRunner.profile.v2';
  constructor() { this.reset(); this.load(); }
  reset() {
    Object.assign(this, { credits: +settings.get('credits.start_credits'), owned: ['scout'], selected: 'scout', bestLevel: 1, bestScore: 0,
      zonesCleared: [], location: 'haven', hull: 1, upgrades: {}, supplies: {} });
  }
  load() {
    const d = store.get(Profile.KEY, null) || {}, old = store.get('wormholeRunner.v1', null) || {};      // v1 held only best scores
    const ships = settings.get('ships'); this.credits = Math.max(0, +(d.credits ?? this.credits));
    this.owned = [...new Set([...(d.owned || []).filter(s => ships[s]), 'scout'])].sort((a, b) => Object.keys(ships).indexOf(a) - Object.keys(ships).indexOf(b));
    this.selected = this.owned.includes(d.selected) ? d.selected : 'scout';
    this.bestLevel = d.bestLevel ?? old.bestLevel ?? 1; this.bestScore = d.bestScore ?? old.bestScore ?? 0;
    this.zonesCleared = (d.zonesCleared || []).filter(z => typeof z === 'string'); this.location = d.location || 'haven';
    this.hull = Math.min(1, Math.max(0.2, +(d.hull ?? 1))); this.upgrades = { ...(d.upgrades || {}) }; this.supplies = { ...(d.supplies || {}) };
  }
  save() {
    store.set(Profile.KEY, { credits: this.credits, owned: this.owned, selected: this.selected, bestLevel: this.bestLevel, bestScore: this.bestScore,
      zonesCleared: this.zonesCleared, location: this.location, hull: +this.hull.toFixed(3), upgrades: this.upgrades, supplies: this.supplies });
  }
  wipe() { this.reset(); this.save(); }
  buy(id) {
    if (this.owned.includes(id)) return true;
    const price = +settings.get(`ships.${id}.price`, 1e9); if (this.credits < price) return false;
    this.credits -= price; this.owned.push(id); this.save(); return true;
  }
  select(id) { if (this.owned.includes(id)) { this.selected = id; this.save(); } }
  record(level, score) { this.bestLevel = Math.max(this.bestLevel, level | 0); this.bestScore = Math.max(this.bestScore, score | 0); }
  clearZone(z) { if (!this.zonesCleared.includes(z)) this.zonesCleared.push(z); this.save(); }
  isUnlocked(z) { return z === 'haven' || this.zonesCleared.includes(z) || (settings.get(`zones.${z}.links`, [])).some(n => n === 'haven' || this.zonesCleared.includes(n)); }
  upgradePrice(u) { const it = settings.get(`shop_items.${u}`), l = this.upgrades[u] || 0; return !it || l >= it.max_level ? null : it.price * (l + 1); }
  buyUpgrade(u) { const p = this.upgradePrice(u); if (p === null || this.credits < p) return false; this.credits -= p; this.upgrades[u] = (this.upgrades[u] || 0) + 1; this.save(); return true; }
  buySupply(k) { const p = +settings.get(`services.${k}.price`, 1e9); if (this.credits < p) return false; this.credits -= p; this.supplies[k] = (this.supplies[k] || 0) + 1; this.save(); return true; }
  useSupply(k) { if ((this.supplies[k] || 0) > 0) { this.supplies[k]--; this.save(); return true; } return false; }
  repairCost() { return Math.round((1 - this.hull) * 100 * +settings.get('services.repair.price_per_percent', 1)); }
  repair() { const c = this.repairCost(); if (c <= 0 || this.credits < c) return false; this.credits -= c; this.hull = 1; this.save(); return true; }
}
export const profile = new Profile();
