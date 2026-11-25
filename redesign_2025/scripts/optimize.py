"""Same-rules re-optimisation of every circuit (differential evolution, ngspice + PTM90).

Rules: VDD 1 V, 35 C, Cpd 0.45 pF, CL 50 fF, total supply power <= PMAX, peaking <= 1 dB,
every MOSFET in saturation (Vds >= Vdsat + 20 mV), f3dB >= FMIN.  Objective: maximise
the transimpedance-bandwidth product Zt*f3dB.
Usage: python3 optimize.py <circuit> [maxiter] [pmax_mW] [fmin_GHz]
"""
import sys, json, os, re
import numpy as np
from scipy.optimize import differential_evolution
import lib, circuits as C

NAME = sys.argv[1]
MAXIT = int(sys.argv[2]) if len(sys.argv) > 2 else 60
PMAX = float(sys.argv[3]) * 1e-3 if len(sys.argv) > 3 else 1.5e-3
FMIN = float(sys.argv[4]) * 1e9 if len(sys.argv) > 4 else 2.5e9
B = C.BOUNDS[NAME]
KEYS = list(B)
SIGNAL_MOS = None


def decode(v):
    x = {}
    for k, u in zip(KEYS, v):
        lo, hi = B[k]
        x[k] = lo + u * (hi - lo) if k in C.LINEAR else lo * (hi / lo) ** u
    return x


def evaluate(x, noise=False, **kw):
    el = C.make(NAME, x, **kw)
    d = lib.measure(el, noise=noise, mos_ops=True, ppd=20, fstop=6e10)
    return el, d


def sat_margin(el, d):
    worst = 1.0
    for e in el:
        if e[0] != 'M' or e[1] in ('Mdn', 'Mdp'):
            continue
        n = e[1].lower()
        vds, vdsat = d.get(f'@{n}[vds]'), d.get(f'@{n}[vdsat]')
        if vds is None or vdsat is None:
            continue
        worst = min(worst, abs(vds) - abs(vdsat))
    return worst


ROBUST = os.environ.get('ROBUST') == '1'
# worst-case set: (corner, temp C, VDD)
CONDS = [('TT', 35, 1.0), ('SS', 125, 0.9), ('FF', -40, 1.1), ('FS', 35, 1.0), ('SF', 35, 1.0), ('SS', -40, 0.9), ('FF', 125, 1.1)]


def cost_robust(v):
    x = decode(v)
    zs, fs, pks, pw, sm = [], [], [], 0, 1.0
    for cor, t, vd in CONDS:
        try:
            el = C.make(NAME, x)
            el = [('V', 'Vdd', 'vdd', '0', vd) if e[1] == 'Vdd' else e for e in el]
            d = lib.measure(el, vdd=vd, temp=t, corner=cor, noise=False, mos_ops=True, ppd=15, fstop=6e10)
        except Exception:
            return 1e3
        if not d.get('ok') or not np.isfinite(d.get('pwr', np.nan)):
            return 1e3
        zs.append(10 ** (d['z0db'] / 20)); fs.append(d['f3'] if np.isfinite(d['f3']) else 1e8)
        pks.append(d['pk']); pw = max(pw, d['pwr'])
        if cor == 'TT':
            sm = sat_margin(el, d)
    pen = 20 * max(0, pw / PMAX - 1) + 2 * max(0, max(pks) - 1.0) + 10 * max(0, 0.02 - sm) \
        + 5 * max(0, np.log(FMIN / min(fs))) + 3 * max(0, np.log(max(fs) / min(fs)) - 0.5)
    return -np.log10(min(zs) * min(fs)) + pen


def cost(v):
    if ROBUST:
        return cost_robust(v)
    x = decode(v)
    try:
        el, d = evaluate(x)
    except Exception:
        return 1e3
    if not d.get('ok') or not np.isfinite(d.get('pwr', np.nan)):
        return 1e3
    f3 = d['f3'] if np.isfinite(d['f3']) else 1e8
    z = 10 ** (d['z0db'] / 20)
    pen = 0
    pen += 20 * max(0, d['pwr'] / PMAX - 1)
    pen += 2 * max(0, d['pk'] - 1.0)
    pen += 10 * max(0, 0.02 - sat_margin(el, d))
    pen += 5 * max(0, np.log(FMIN / f3))
    return -np.log10(z * f3) + pen


if __name__ == '__main__':
    r = differential_evolution(cost, [(0, 1)] * len(KEYS), maxiter=MAXIT, popsize=12, tol=1e-4,
                               mutation=(0.5, 1.0), recombination=0.8, seed=1, workers=4,
                               updating='deferred', polish=False)
    x = decode(r.x)
    el, d = evaluate(x, noise=True)
    res = dict(name=NAME, x=x, cost=r.fun, pmax=PMAX, fmin=FMIN, z0db=d['z0db'], f3=d['f3'],
               pk=d['pk'], pwr=d['pwr'], in_avg=d.get('in_avg'), sat=sat_margin(el, d),
               vin=d.get('v(in)'), vout=d.get('v(out)'))
    os.makedirs('../results/opt', exist_ok=True)
    tag = f"{NAME}_P{PMAX*1e3:g}_F{FMIN/1e9:g}" + ('_robust' if ROBUST else '')
    json.dump(res, open(f'../results/opt/{tag}.json', 'w'), indent=1)
    print(tag, lib.summary(d), 'sat', round(sat_margin(el, d), 3), 'GBW', round(10**(d['z0db']/20)*d['f3']/1e12, 3), 'THz-ohm')
    print(x)
