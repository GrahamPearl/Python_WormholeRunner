const OBJ = { crystals: 'Collect {need} crystals', rescue: 'Rescue {need} pods', defend: 'Defend the station for {seconds}s', survive: 'Survive {seconds}s', beacon: 'Reach the beacon', hunt: 'Destroy {need} aliens', prospect: 'Break {need} gold rocks', escort: 'Escort the freighter for {seconds}s' };
const HZ = { nebula: 'nebulae', blackhole: 'black holes', ion: 'ion storms' };
/** Short text lines about a zone for the star map. */
export function describeZone(z) {
  if (z.kind === 'station' || z.kind === 'planet') return [z.desc, `Safe harbour. Shop: ${(z.shop || []).map(t => t[0].toUpperCase() + t.slice(1)).join(', ')}`];
  const goal = z.boss ? 'Destroy the Mothership' : (OBJ[z.objective?.type] || '?').replace('{need}', z.objective?.need ?? 0).replace('{seconds}', z.objective?.seconds ?? 0), ex = [];
  if (z.gravity && z.gravity !== 1) ex.push(`gravity x${z.gravity}`); if (z.time_limit) ex.push(`time limit ${z.time_limit}s`);
  for (const [k, n] of Object.entries(z.hazards || {})) ex.push(`${n} ${HZ[k] || k}`); if (z.flares) ex.push('solar flares');
  return [z.desc, `Objective: ${goal}`, `Reward: ${z.reward || 0} credits`, ...(ex.length ? [`Challenge: ${ex.join(', ')}`] : [])];
}
