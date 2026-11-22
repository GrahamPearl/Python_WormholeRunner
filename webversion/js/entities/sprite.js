import { settings } from '../config.js';

/** Anything drawn from a sprite sheet. w/h are the on-screen size at creation (used for hit radii). */
export class Sprite {
  constructor(gfx, mult = 1) {
    const s = settings.get('graphics.' + gfx) || settings.get('graphics.ship');
    this.gfx = gfx; this.baseSc = (s.scale || 1) * mult; this.sc = this.baseSc;
    this.w = s.frame_w * this.sc; this.h = s.frame_h * this.sc;
    this.t = Math.random(); this.x = this.y = 0; this.angle = 0; this.alpha = 1; this.tint = null; this.dead = false;
  }
  animate(dt) { this.t += dt; }
}
