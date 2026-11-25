"""Per-condition trimming of the control voltage vc of mdfrgc_t.
For each corner x temperature x VDD: fixed vc (nominal) vs vc trimmed on a 0.05 V grid to the largest
bandwidth that keeps peaking <= 1 dB and gain within 1 dB of the nominal gain."""
import sys, os, json
import numpy as np
from multiprocessing import Pool
import lib, circuits as C, analyze as A

NAME = 'mdfrgc_t'
TAG = os.environ.get('TAG', '_P1.5_F2.5')
x0 = A.load(NAME, TAG)
GRID = np.round(np.arange(0, 1.0001, 0.05), 3)


def one(a):
    cor, t, v, vc = a
    x = dict(x0, vc=float(vc))
    r = A.m(NAME, x, corner=cor, temp=t, vdd=v, noise=False)
    return (cor, t, v, float(vc), r)


if __name__ == '__main__':
    conds = [(c, t, v) for c in lib.CORNERS for t in (-40, 35, 125) for v in (0.9, 1.0, 1.1)]
    nom = A.m(NAME, x0)
    jobs = [(c, t, v, vc) for (c, t, v) in conds for vc in GRID]
    with Pool(4) as p:
        res = p.map(one, jobs)
    rows = []
    z_nom = nom['z0db']
    for (c, t, v) in conds:
        sel = [r for r in res if r[:3] == (c, t, v) and r[4]]
        fixed = [r for r in sel if abs(r[3] - x0['vc']) < 1e-6]
        fx = min(sel, key=lambda r: abs(r[3] - x0['vc']))
        ok = [r for r in sel if r[4]['pk'] <= 1.0 and abs(r[4]['z0db'] - z_nom) <= 1.0 and np.isfinite(r[4]['f3'])]
        best = max(ok, key=lambda r: r[4]['f3']) if ok else None
        rows.append(dict(corner=c, temp=t, vdd=v, fixed_vc=fx[3], fixed=fx[4],
                         trim_vc=best[3] if best else None, trim=best[4] if best else None))
    json.dump(dict(x=x0, nominal=nom, rows=rows, vc_range=[float(GRID[0]), float(GRID[-1])]),
              open(os.path.join(A.RES, f'trim_{NAME}.json'), 'w'), indent=1, default=float)
    # tuning range at nominal
    tun = [(r[3], r[4]['f3'] / 1e9, r[4]['pk'], r[4]['z0db']) for r in res if r[:3] == ('TT', 35, 1.0) and r[4]]
    print('nominal vc sweep (vc, f3 GHz, pk dB, Zt):')
    for t in tun:
        print('  %.2f %.3f %.2f %.2f' % t)
    f = lambda L, k: (min(r[k] for r in L), max(r[k] for r in L))
    fx = [r['fixed'] for r in rows]; tr = [r['trim'] for r in rows if r['trim']]
    print('fixed: f3 %s GHz, worst pk %.2f dB, Zt %s' % ([round(a / 1e9, 2) for a in f(fx, 'f3')], max(r['pk'] for r in fx), [round(a, 1) for a in f(fx, 'z0db')]))
    print('trimmed (%d/%d feasible): f3 %s GHz, worst pk %.2f dB, Zt %s' % (len(tr), len(rows), [round(a / 1e9, 2) for a in f(tr, 'f3')], max(r['pk'] for r in tr), [round(a, 1) for a in f(tr, 'z0db')]))
