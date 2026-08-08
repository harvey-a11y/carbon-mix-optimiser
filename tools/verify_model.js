// Independent Node re-implementation of the carbonmix model.
//
// WHY THIS EXISTS. Python is blocked by Application Control on the machine this was
// written on, so the Python package could not be executed locally. Rather than quote
// numbers nobody had computed, the model was re-implemented from the module docstrings
// and used to produce the figures in the technical note.
//
// That makes this a genuine second implementation, not a wrapper: it was written from
// the documented equations, not by translating the Python line by line. If the two ever
// disagree, one of them has a bug and that is worth knowing.
//
//   node tools/verify_model.js
//   node tools/verify_model.js --draws 500
'use strict';

// ---- constants, mirroring carbonmix.data ----------------------------------
const CF = { cem1: 0.91, ggbs: 0.08, fly_ash: 0.01, coarse_agg: 0.005, sand: 0.005, water: 0.0003 };
const RHO = { cem1: 3150, ggbs: 2900, fly_ash: 2300, water: 1000, aggregate: 2650 };
const AIR = 0.02, SAND_F = 0.40, COARSE_F = 0.60;
const LIMITS = {
  XC1: { max_wc: 0.65, min_binder: 260 },
  XC3_XC4: { max_wc: 0.55, min_binder: 300 },
  XD3: { max_wc: 0.45, min_binder: 360 },
  XS3: { max_wc: 0.45, min_binder: 380 },
};
const MAX_GGBS = 0.70, MAX_FA = 0.35, MAX_SCM = 0.70;
const K_GGBS = 0.6, K_FA = 0.4, MARGIN = 8.0;
const CLASSES = { 'C25/30': 25, 'C28/35': 28, 'C32/40': 32, 'C35/45': 35, 'C40/50': 40 };
const TOL = 1e-9;

// ---- model ----------------------------------------------------------------
function proportions(binder, wc, gf, ff) {
  const cement = binder * (1 - gf - ff), ggbs = binder * gf, fa = binder * ff;
  const water = wc * binder;
  const paste = cement / RHO.cem1 + ggbs / RHO.ggbs + fa / RHO.fly_ash + water / RHO.water;
  const aggVol = 1 - AIR - paste;
  if (aggVol <= 0) return null;
  const agg = aggVol * RHO.aggregate;
  return { cem1: cement, ggbs, fly_ash: fa, water, sand: SAND_F * agg, coarse_agg: COARSE_F * agg };
}
const carbonOf = (m, cf) => Object.keys(m).reduce((s, k) => s + m[k] * cf[k], 0);

function gridSearch(cls, exp, k1, k2, cf) {
  const target = CLASSES[cls], lim = LIMITS[exp];
  let best = null, base = null, n = 0;
  for (let g = 0; g <= 70; g += 5) {
    for (let f = 0; f <= 35; f += 5) {
      const gf = g / 100, ff = f / 100;
      if (gf > MAX_GGBS + TOL || ff > MAX_FA + TOL || gf + ff > MAX_SCM + TOL) continue;
      const effFrac = (1 - gf - ff) + K_GGBS * gf + K_FA * ff;
      for (let w = 35; w <= 65; w++) {
        const wc = w / 100, wcEff = wc / effFrac;
        const fcm = k1 / Math.pow(k2, wcEff);
        const fck = fcm - MARGIN;
        const strengthOk = fck >= target - TOL;
        for (let b = 260; b <= 450; b += 10) {
          n++;
          if (!strengthOk) continue;
          if (wcEff > lim.max_wc + TOL || b < lim.min_binder - TOL) continue;
          const m = proportions(b, wc, gf, ff);
          if (!m) continue;
          const c = carbonOf(m, cf);
          const cand = { binder: b, wc, gf, ff, wcEff, fck, carbon: c, masses: m };
          if (!best || c < best.carbon) best = cand;
          if (g === 0 && f === 0 && (!base || c < base.carbon)) base = cand;
        }
      }
    }
  }
  return { best, base, n };
}

// ---- deterministic run ----------------------------------------------------
const CLS = 'C32/40', EXP = 'XC3_XC4';
const det = gridSearch(CLS, EXP, 110, 10, CF);
const saving = 100 * (det.base.carbon - det.best.carbon) / det.base.carbon;

console.log('=== deterministic, package defaults ===');
console.log(`  ${CLS} / ${EXP}   ${det.n} combinations evaluated`);
console.log(`  baseline (CEM I only): binder ${det.base.binder} kg/m3, w/c ${det.base.wc.toFixed(2)}, ` +
            `${det.base.carbon.toFixed(1)} kgCO2e/m3`);
console.log(`  best: binder ${det.best.binder} kg/m3, ${(det.best.gf * 100).toFixed(0)}% GGBS, ` +
            `${(det.best.ff * 100).toFixed(0)}% FA, w/c ${det.best.wc.toFixed(2)}, ` +
            `${det.best.carbon.toFixed(1)} kgCO2e/m3`);
console.log(`  SAVING: ${saving.toFixed(1)}%`);

// ---- Monte Carlo ----------------------------------------------------------
const RANGES = {
  cem1: [0.75, 0.95], ggbs: [0.05, 0.13], fly_ash: [0.004, 0.030],
  coarse_agg: [0.003, 0.008], sand: [0.003, 0.008], water: [0.0002, 0.0005],
};
const K1R = [95, 130], K2R = [8, 13];

// deterministic LCG so the figures are reproducible without a seeded RNG library
let seed = 12345;
const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
const uni = ([lo, hi]) => lo + (hi - lo) * rnd();

const drawsArg = process.argv.indexOf('--draws');
const DRAWS = drawsArg > -1 ? parseInt(process.argv[drawsArg + 1], 10) : 400;

const savings = [];
let infeasible = 0;
for (let d = 0; d < DRAWS; d++) {
  const cf = {};
  for (const k in RANGES) cf[k] = uni(RANGES[k]);
  const r = gridSearch(CLS, EXP, uni(K1R), uni(K2R), cf);
  if (!r.best || !r.base) { infeasible++; continue }
  savings.push(100 * (r.base.carbon - r.best.carbon) / r.base.carbon);
}
savings.sort((a, b) => a - b);
const pct = p => {
  const k = (savings.length - 1) * p / 100;
  const lo = Math.floor(k), hi = Math.min(lo + 1, savings.length - 1);
  return savings[lo] + (savings[hi] - savings[lo]) * (k - lo);
};
const median = pct(50), mean = savings.reduce((a, b) => a + b, 0) / savings.length;

console.log(`\n=== Monte Carlo, ${DRAWS} draws ===`);
console.log(`  feasible draws: ${savings.length}${infeasible ? `, infeasible: ${infeasible}` : ''}`);
console.log(`  median  ${median.toFixed(1)}%`);
console.log(`  mean    ${mean.toFixed(1)}%`);
console.log(`  90% interval  ${pct(5).toFixed(1)}%  to  ${pct(95).toFixed(1)}%`);
console.log(`  full range    ${savings[0].toFixed(1)}%  to  ${savings[savings.length - 1].toFixed(1)}%`);

// ---- transport sensitivity ------------------------------------------------
const HAUL = { cem1: 'cem1', ggbs: 'ggbs', fly_ash: 'fly_ash', coarse_agg: 'aggregate', sand: 'aggregate' };
const a4 = (m, dist, f) => Object.keys(m).reduce((s, k) => {
  const key = HAUL[k]; return key ? s + (m[k] / 1000) * (dist[key] || 0) * f : s;
}, 0);

console.log('\n=== module A4 transport, 0.11 kgCO2e/tonne-km ===');
[
  ['cement near, GGBS far', { cem1: 80, ggbs: 300, aggregate: 40, fly_ash: 150 }],
  ['both local', { cem1: 80, ggbs: 80, aggregate: 40, fly_ash: 80 }],
  ['GGBS very far', { cem1: 80, ggbs: 500, aggregate: 40, fly_ash: 150 }],
].forEach(([label, dist]) => {
  const bA4 = a4(det.best.masses, dist, 0.11), zA4 = a4(det.base.masses, dist, 0.11);
  const s14 = 100 * ((det.base.carbon + zA4) - (det.best.carbon + bA4)) / (det.base.carbon + zA4);
  console.log(`  ${label.padEnd(22)} A1-A3 ${saving.toFixed(1)}%  ->  A1-A4 ${s14.toFixed(1)}%  ` +
              `(best +${bA4.toFixed(1)}, baseline +${zA4.toFixed(1)} kgCO2e/m3)`);
});

// ---- early age ------------------------------------------------------------
const earlyRatio = (gf, ff) => Math.max(0.05, 0.65 * (1 - (0.45 * gf + 0.35 * ff)));
console.log('\n=== early age, indicative f(7)/f(28) ===');
console.log(`  best mix (${(det.best.gf * 100).toFixed(0)}% GGBS, ${(det.best.ff * 100).toFixed(0)}% FA): ` +
            `${(100 * earlyRatio(det.best.gf, det.best.ff)).toFixed(0)}%  ` +
            `(~${(det.best.fck * earlyRatio(det.best.gf, det.best.ff)).toFixed(0)} MPa)`);
console.log(`  CEM I baseline: ${(100 * earlyRatio(0, 0)).toFixed(0)}%  ` +
            `(~${(det.base.fck * earlyRatio(0, 0)).toFixed(0)} MPa)`);

// ---- variance decomposition: which uncertainty actually drives the spread? -
// Vary ONE group at a time, holding the other at its default, and compare the
// resulting spread with the all-varying case above.
function mc(varyFactors, varyStrength, n) {
  seed = 999;
  const out = [];
  for (let d = 0; d < n; d++) {
    const cf = {};
    for (const k in RANGES) cf[k] = varyFactors ? uni(RANGES[k]) : CF[k];
    const k1 = varyStrength ? uni(K1R) : 110;
    const k2 = varyStrength ? uni(K2R) : 10;
    const r = gridSearch(CLS, EXP, k1, k2, cf);
    if (r.best && r.base) out.push(100 * (r.base.carbon - r.best.carbon) / r.base.carbon);
  }
  out.sort((a, b) => a - b);
  const q = p => { const k = (out.length - 1) * p / 100, lo = Math.floor(k), hi = Math.min(lo + 1, out.length - 1);
                   return out[lo] + (out[hi] - out[lo]) * (k - lo) };
  return { n: out.length, med: q(50), lo: q(5), hi: q(95), width: q(95) - q(5) };
}
console.log('\n=== which input drives the spread? (400 draws each) ===');
[['carbon factors only', true, false], ['strength calibration only', false, true], ['both', true, true]]
  .forEach(([label, a, b]) => {
    const r = mc(a, b, 400);
    console.log(`  ${label.padEnd(26)} median ${r.med.toFixed(1)}%  90% CI ${r.lo.toFixed(1)}-${r.hi.toFixed(1)}%  width ${r.width.toFixed(1)} pts`);
  });
