"""Characterise every optimised design: nominal + noise, CPD sweep, PVT, mismatch Monte Carlo,
PRBS7 eye.  Usage: python3 analyze.py name1 [name2 ...]  (reads ../results/opt/<name>_P1.5_F2.5.json)"""
import sys, os, json
import numpy as np
from multiprocessing import Pool
import lib, circuits as C

RES = os.path.join(lib.ROOT, 'results')
AVT, ABETA = 3.5e-3, 0.01        # Pelgrom: sigma(Vth) = AVT/sqrt(WL[um^2]), sigma(beta)/beta = ABETA/sqrt(WL)


def load(name, tag=os.environ.get('TAG', '_P1.5_F2.5')):
    return json.load(open(os.path.join(RES, 'opt', name + tag + '.json')))['x']


def el_of(name, x, cpd=0.45e-12, cl=50e-15, vdd=1.0):
    el = C.make(name, x, cpd=cpd, cl=cl)
    return [('V', 'Vdd', 'vdd', '0', vdd) if e[1] == 'Vdd' else e for e in el]


def m(name, x, **kw):
    cpd = kw.pop('cpd', 0.45e-12); vdd = kw.pop('vdd', 1.0)
    d = lib.measure(el_of(name, x, cpd=cpd, vdd=vdd), vdd=vdd, **kw)
    if not d.get('ok'):
        return None
    return {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in d.items()
            if k in ('z0db', 'pk', 'f3', 'pwr', 'in_avg', 'in1g', 'irms', 'v(in)', 'v(out)')}


def _pvt(a):
    name, x, cor, t, v = a
    r = m(name, x, corner=cor, temp=t, vdd=v, noise=False)
    return dict(corner=cor, temp=t, vdd=v, **(r or {}))


def _mc(a):
    name, x, seed = a
    rng = np.random.default_rng(seed)
    mm = {}
    for e in el_of(name, x):
        if e[0] == 'M':
            wl = e[7] * e[8] / 1000
            mm[e[1]] = (rng.normal(0, AVT / np.sqrt(wl)), rng.normal(0, ABETA / np.sqrt(wl)))
    r = m(name, x, mismatch=mm, noise=False)
    return r or {}


def eye(name, x, br=3e9, amp=20e-6, nbits=127):
    import emit
    bits, pts = emit.prbs7_file(br, amp, nbits)
    el = [e for e in el_of(name, x) if e[1] != 'Iin']
    pwl = ' '.join(f'{t:.6g} {v:.6g}' for t, v in pts)
    t = os.path.join(lib.TMP, f'eye_{name}_{os.getpid()}.txt')
    ui = 1 / br
    net = '\n'.join(['* eye', f'.include {lib.MODEL}', '.temp 35'] + lib.spice(el) +
                     [f'Ipr 0 in PWL({pwl})', '.control', 'set noaskquit', 'set wr_singlescale',
                      f'tran {ui/40:.4g} {nbits*ui:.4g} 0 {ui/40:.4g}', f'linearize v(out)', f'wrdata {t} v(out)', '.endc', '.end']) + '\n'
    lib.run(net)
    a = np.loadtxt(t)
    tt, v = a[:, 0], a[:, 1]
    # fold after 10 UI of settling; sample-phase sweep -> best vertical opening
    k = tt > 10 * ui
    ph = ((tt[k]) % ui) / ui
    bit_idx = np.floor(tt[k] / ui).astype(int)
    lvl = np.array([bits[min(i, len(bits) - 1)] for i in bit_idx])
    best = (-1, 0)
    for p0 in np.linspace(0, 1, 41)[:-1]:
        s = np.abs(ph - p0) < 0.02
        hi, lo = v[k][s & (lvl == 0)], v[k][s & (lvl == 1)]   # current into 'in' pulls 'out' down or up
        if len(hi) and len(lo):
            o1 = hi.min() - lo.max(); o2 = lo.min() - hi.max()
            o = max(o1, o2)
            if o > best[0]:
                best = (o, p0)
    swing = v[k].max() - v[k].min()
    return dict(eye_mV=1e3 * best[0], swing_mV=1e3 * swing, eye_frac=best[0] / swing if swing else np.nan,
                tt=tt.tolist(), v=v.tolist(), br=br)


def run(name, mc_n=200):
    x = load(name)
    out = dict(name=name, x=x)
    out['nom'] = m(name, x)
    out['cpd'] = [dict(cpd=c, **(m(name, x, cpd=c, noise=False) or {})) for c in (0.1e-12, 0.25e-12, 0.45e-12, 0.7e-12, 1.0e-12)]
    jobs = [(name, x, c, t, v) for c in lib.CORNERS for t in (-40, 35, 125) for v in (0.9, 1.0, 1.1)]
    with Pool(4) as p:
        out['pvt'] = p.map(_pvt, jobs)
        out['mc'] = p.map(_mc, [(name, x, s) for s in range(mc_n)])
    e = eye(name, x)
    out['eye'] = {k: e[k] for k in ('eye_mV', 'swing_mV', 'eye_frac', 'br')}
    np.save(os.path.join(RES, f'eye_{name}{os.environ.get("TAG", "")}.npy'), np.array([e['tt'], e['v']]))
    json.dump(out, open(os.path.join(RES, f'char_{name}{os.environ.get("TAG", "")}.json'), 'w'), indent=1, default=float)
    n = out['nom']
    pv = [r for r in out['pvt'] if 'f3' in r]
    mc = [r for r in out['mc'] if 'f3' in r]
    f = lambda L, k: (min(r[k] for r in L), max(r[k] for r in L))
    print(f"{name}: Zt {n['z0db']:.2f} dBohm, f3 {n['f3']/1e9:.2f} GHz, pk {n['pk']:.2f}, P {n['pwr']*1e3:.3f} mW, "
          f"in {n.get('in_avg', 0):.2f} pA/rtHz | PVT({len(pv)}/{len(jobs)}) Zt {f(pv,'z0db')} f3 {[round(a/1e9,2) for a in f(pv,'f3')]} pk max {max(r['pk'] for r in pv):.2f} | "
          f"MC f3 {np.mean([r['f3'] for r in mc])/1e9:.2f}+-{np.std([r['f3'] for r in mc])/1e9:.2f} GHz, pk>1dB {sum(r['pk']>1 for r in mc)}/{len(mc)} | "
          f"eye {out['eye']['eye_mV']:.1f} mV of {out['eye']['swing_mV']:.1f}")
    return out


if __name__ == '__main__':
    for nm in sys.argv[1:]:
        run(nm)
