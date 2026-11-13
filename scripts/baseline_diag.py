"""Diagnose why the published baseline (Alsheikhjader 2020) cannot be reproduced.

Each hypothesis is a modification of the as-drawn circuit. For every hypothesis the
free, unpublished quantities (photodiode and load capacitance) are fitted to the
digitised published curve, and the residual error tells whether that hypothesis can
explain the published response at all.

Usage:  python3 baseline_diag.py [screen fit fitlf lfscan optnoise]
        python3 baseline_diag.py opt              (max gain-bandwidth re-optimisation)
        python3 baseline_diag.py optgain 53.87    (max bandwidth at >= 53.87 dBohm)
"""
import os, sys, json, itertools
import numpy as np
from multiprocessing import Pool
from scipy.optimize import minimize
import sim, circuits as C

DATA = os.path.join(C.ROOT, 'results', 'data')
# digitised from Alsheikhjader 2020, Fig. 3 (V_OUT/I_PD in ohm)
P_F = np.array([1, 5, 10, 15, 20, 25, 28, 30, 35, 40, 45, 50.]) * 1e9
P_Z = np.array([203, 163, 157, 157, 147, 135, 118, 109, 85, 66, 53, 42.])


def variant(vg2b=None, rs=0.0, rp=None):
    """Element-list transform: M2b gate to its own source, series R in the spiral,
    optional parallel R across the spiral (a lossy spiral is modelled as series R)."""
    def rep(el):
        out = []
        for e in el:
            e = list(e)
            if e[0] == 'M' and e[1] == 'M2b' and vg2b is not None:
                e[3] = 'g2b'
            if e[0] == 'L' and rs > 0:
                out.append(('L', 'Lf', 'out', 'xl', e[4]))
                out.append(('R', 'Rsl', 'xl', 'in', '%g' % rs))
                continue
            out.append(tuple(e))
        if vg2b is not None:
            out.insert(1, ('V', 'Vg2b', 'g2b', '0', '%g' % vg2b, None))
        return out
    return rep


def zt(P, vg2b=None, rs=0.0, op=False):
    ctl = []
    if op:
        ctl += ['op', 'print v(in) v(n) v(out) i(vdd)',
                'print @m1[id] @m1[vds] @m1[vdsat] @m1[gm] @m1[gds] @m2[id] @m2[gm] @m3[gm] @m2b[id] @m3b[id]']
    t = os.path.join(sim.TMP, f'diag{os.getpid()}_{np.random.randint(1e9)}')
    ctl += ['ac dec 30 0.5g 60g', f'wrdata {t}.txt vdb(out)']
    out = sim.run(sim.build('base', P, control='\n'.join(ctl), replace=variant(vg2b, rs)))
    a = np.loadtxt(t + '.txt')
    f, z = a[:, 0], 10 ** (a[:, 1] / 20)
    d = sim.vals(out) if op else {}
    return f, z, d


def err_db(f, z):
    zi = np.interp(np.log10(P_F), np.log10(f), z)
    return float(np.sqrt(np.mean((20 * np.log10(zi / P_Z)) ** 2)))


# hypotheses: (label, vg2b, vg3b, rs, description)
HYP = [
    ('H0', None, 0.0, 0, 'As drawn ($V_{G,2b}=V_{DD}$, $V_{G,3b}=0$), ideal spiral'),
    ('H1', None, -1.0, 0, 'As drawn with $V_{G,3b}=-1$\\,V (published label)'),
    ('H2', 0.0, 0.0, 0, '$M_{2b}$ gate grounded (drawing error), ideal spiral'),
    ('H3', None, 0.0, 15, 'As drawn, lossy spiral ($R_s=15\\,\\Omega$)'),
]


def fit_caps(vg2b, vg3b, rs, free_bias=False, free_lf=False):
    """Fit Cpd, Cout (and optionally Vg3b, Rs) to the published curve."""
    def cost(x):
        cpd, cout = np.exp(x[0]), np.exp(x[1])
        v3 = x[2] if free_bias else vg3b
        r = np.exp(x[3]) if free_bias else rs
        if free_bias and not (-1.0 <= v3 <= 0.75):
            return 50.0
        if not (5 <= cpd <= 2000 and 5 <= cout <= 2000):
            return 50.0
        P = {'cpd': f'{cpd:.3f}f', 'cout': f'{cout:.3f}f', 'vg3b': v3}
        if free_lf:
            lf = np.exp(x[-1])
            if not (1e-14 <= lf <= 1e-8):
                return 50.0
            P['lf'] = f'{lf:.4g}'
        f, z, _ = zt(P, vg2b, r)
        return err_db(f, z)
    best = None
    starts = [(50, 30), (150, 80), (400, 200), (40, 300)]
    for c0 in starts:
        x0 = [np.log(c0[0]), np.log(c0[1])] + ([vg3b, np.log(max(rs, 1.0))] if free_bias else [])
        if free_lf:
            x0.append(np.log(2.4e-9) if c0 == starts[0] else np.log(2.4e-12) if c0 == starts[1] else np.log(2.4e-10))
        r = minimize(cost, x0, method='Nelder-Mead', options=dict(maxfev=160 if not (free_bias or free_lf) else 400, xatol=1e-3, fatol=1e-3))
        if best is None or r.fun < best.fun:
            best = r
    x = best.x
    res = dict(cpd_fF=float(np.exp(x[0])), cout_fF=float(np.exp(x[1])), rms_db=float(best.fun))
    if free_bias:
        res.update(vg3b=float(x[2]), rs=float(np.exp(x[3])))
    if free_lf:
        res.update(lf=float(np.exp(x[-1])))
    return res


def _fit(args):
    lab, vg2b, vg3b, rs, desc, free = args[:6]
    free_lf = len(args) > 6 and args[6]
    r = fit_caps(vg2b, vg3b, rs, free, free_lf)
    v3 = r.get('vg3b', vg3b); rr = r.get('rs', rs)
    P = {'cpd': f"{r['cpd_fF']:.3f}f", 'cout': f"{r['cout_fF']:.3f}f", 'vg3b': v3}
    if free_lf:
        P['lf'] = '%.4g' % r['lf']
    f, z, d = zt(P, vg2b, rr, op=True)
    f0, z0, d0 = zt({'vg3b': v3, **({'lf': P['lf']} if free_lf else {})}, vg2b, rr, op=True)    # same bias with the paper's assumed 50/30 fF
    zdb = 20 * np.log10(z)
    r.update(label=lab, desc=desc, vg2b=vg2b, vg3b=v3, rs=rr,
             z1g=float(np.interp(1e9, f, z)), pk_db=float(zdb.max() - zdb[0]), fpk=float(f[zdb.argmax()]),
             id_m1=d.get('@m1[id]'), vds_m1=d.get('@m1[vds]'), vdsat_m1=d.get('@m1[vdsat]'),
             id_m2=d.get('@m2[id]'), gm2=d.get('@m2[gm]'), id_m3b=d.get('@m3b[id]'), pwr=-d.get('i(vdd)', 0),
             rms_db_5030=err_db(f0, z0))
    np.savetxt(os.path.join(DATA, f'diag_{lab}.csv'), np.column_stack([f, zdb, 20 * np.log10(z0)]), delimiter=',',
               header='freq_Hz,Zt_fitted_caps_dBohm,Zt_50f_30f_dBohm', comments='')
    print(lab, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != 'desc'}), flush=True)
    return r


def step_fit_lf():
    jobs = [('H6', None, 0.4, 1, 'As drawn, $V_{G,3b}$, spiral loss and $L_f$ free', True, True)]
    rows = [_fit(j) for j in jobs]
    old = json.load(open(os.path.join(DATA, 'baseline_diag.json')))
    old = [o for o in old if o['label'] not in ('H6',)] + rows
    json.dump(old, open(os.path.join(DATA, 'baseline_diag.json'), 'w'), indent=1, default=float)


def step_fit():
    jobs = [h + (False,) for h in HYP]
    jobs.append(('H4', 0.0, 0.3, 5, '$M_{2b}$ on, $V_{G,3b}$ and spiral loss free', True))
    jobs.append(('H5', None, 0.3, 5, 'As drawn, $V_{G,3b}$ and spiral loss free', True))
    with Pool(2) as p:
        rows = p.map(_fit, jobs)
    json.dump(rows, open(os.path.join(DATA, 'baseline_diag.json'), 'w'), indent=1, default=float)


def step_screen():
    """Coarse map: low-frequency gain and peaking vs the two PMOS gate biases."""
    rows = []
    for vg2b in (None, 0.6, 0.4, 0.2, 0.0):
        for vg3b in (-1.0, 0.0, 0.2, 0.3, 0.4, 0.5):
            f, z, d = zt({'vg3b': vg3b}, vg2b, 0, op=True)
            zdb = 20 * np.log10(z)
            rows.append(dict(vg2b=vg2b, vg3b=vg3b, z1g=float(np.interp(1e9, f, z)), pk=float(zdb.max() - zdb[0]),
                             fpk=float(f[zdb.argmax()]), id_m1=d['@m1[id]'], vds_m1=d['@m1[vds]'], vdsat_m1=d['@m1[vdsat]'],
                             id_m2=d['@m2[id]'], pwr=-d['i(vdd)'], err=err_db(f, z)))
            print(rows[-1], flush=True)
    json.dump(rows, open(os.path.join(DATA, 'baseline_screen.json'), 'w'), indent=1, default=float)




# ------------------------------------------------------------------ fair baseline
# Re-design the baseline topology under the constraints used for the proposed TIA:
# same supply, C_PD = 50 fF, C_L = 30 fF, <= 1 dB peaking, <= 1.2 mW. Free: device
# widths, both PMOS gate biases, the inductance and its series loss.
OPT_B = [(1, 20), (1, 20), (1, 20), (0.5, 20), (0.5, 10), (-1.0, 0.7), (0.0, 1.0), (0.2e-9, 6e-9), (0, 60)]
OPT_N = ['W1', 'W2', 'W3', 'W3b', 'W2b', 'vg3b', 'vg2b', 'lf', 'rs']


ZMIN = None   # if set: maximise bandwidth subject to Z0 >= ZMIN (dBohm)


def opt_eval(x, full=False):
    w1, w2, w3, w3b, w2b, vg3b, vg2b, lf, rs = x
    sz = {'M1': (round(w1, 2), 90), 'M2': (round(w2, 2), 90), 'M3': (round(w3, 2), 90),
          'M3b': (round(w3b, 2), 90), 'M2b': (round(w2b, 2), 90)}
    P = {'vg3b': round(vg3b, 3), 'lf': '%.4g' % lf}
    t = os.path.join(sim.TMP, f'opt{os.getpid()}_{np.random.randint(1e9)}')
    ctl = ['op', 'print i(vdd) @m1[vds] @m1[vdsat]', 'ac dec 30 10meg 100g', f'wrdata {t}.txt vdb(out)']
    out = sim.run(sim.build('base', P, sz=sz, control='\n'.join(ctl), replace=variant(round(vg2b, 3), rs)))
    try:
        a = np.loadtxt(t + '.txt')
    except Exception:
        return (1e3, {}) if full else 1e3
    d = sim.vals(out)
    f, z = a[:, 0], a[:, 1]
    z0 = z[np.argmin(abs(f - 1e8))]
    pk = z.max() - z0
    f3 = sim.f3db(f, z)
    pwr = -d.get('i(vdd)', 1)
    if not np.isfinite(f3):
        f3 = 1e8
    if ZMIN is None:
        cost = -np.log10(10 ** (z0 / 20) * f3) + 3 * max(0, pk - 1) + 20 * max(0, pwr - 1.2e-3) / 1e-3
    else:
        cost = -np.log10(f3) + 3 * max(0, pk - 1) + 20 * max(0, pwr - 1.2e-3) / 1e-3 + 2 * max(0, ZMIN - z0)
    if full:
        return cost, dict(z0db=float(z0), pk=float(pk), f3=float(f3), pwr=float(pwr), gbw=float(10 ** (z0 / 20) * f3),
                          vds_m1=d.get('@m1[vds]'), vdsat_m1=d.get('@m1[vdsat]'))
    return cost


def _init_zmin(z):
    global ZMIN
    ZMIN = z


def step_opt(zmin=None, name='baseline_opt_gbw.json', workers=2):
    from scipy.optimize import differential_evolution
    global ZMIN
    ZMIN = zmin
    from multiprocessing import Pool
    with Pool(workers, initializer=_init_zmin, initargs=(zmin,)) as p:
        r = differential_evolution(opt_eval, OPT_B, popsize=12, maxiter=40, tol=1e-4, seed=7, workers=p.map,
                                   updating='deferred', polish=False)
    c, m = opt_eval(r.x, full=True)
    res = dict(zip(OPT_N, map(float, r.x)), **m, cost=float(c), zmin=zmin)
    print(json.dumps(res, indent=1))
    json.dump(res, open(os.path.join(DATA, name), 'w'), indent=1, default=float)




def step_lfscan():
    """Best achievable fit to the published curve as a function of L_f (M3b gate bias,
    C_PD and C_L free; M2b as drawn; ideal inductor)."""
    rows = []
    for lf in [1e-12, 1e-11, 3e-11, 1e-10, 3e-10, 1e-9, 2.4e-9, 5e-9]:
        def cost(x):
            cpd, cout, v3 = np.exp(x[0]), np.exp(x[1]), x[2]
            if not (5 <= cpd <= 2000 and 5 <= cout <= 2000 and -1 <= v3 <= 0.75):
                return 50.0
            f, z, _ = zt({'cpd': f'{cpd:.3f}f', 'cout': f'{cout:.3f}f', 'vg3b': v3, 'lf': f'{lf:.4g}'}, None, 0)
            return err_db(f, z)
        best = None
        for c in [(50, 30, 0.5), (150, 60, 0.45), (300, 150, 0.5), (30, 100, 0.4), (50, 30, 0.0)]:
            r = minimize(cost, [np.log(c[0]), np.log(c[1]), c[2]], method='Nelder-Mead', options=dict(maxfev=250))
            best = r if best is None or r.fun < best.fun else best
        rows.append(dict(lf=lf, rms_db=float(best.fun), cpd_fF=float(np.exp(best.x[0])), cout_fF=float(np.exp(best.x[1])),
                         vg3b=float(best.x[2])))
        print(rows[-1], flush=True)
    json.dump(rows, open(os.path.join(DATA, 'baseline_lfscan.json'), 'w'), indent=1)


def step_optnoise():
    """Full metrics (with noise) of the two re-optimised baselines."""
    out = {}
    for name in ('baseline_opt_gbw', 'baseline_opt_gain'):
        o = json.load(open(os.path.join(DATA, name + '.json')))
        sz = {'M1': (round(o['W1'], 2), 90), 'M2': (round(o['W2'], 2), 90), 'M3': (round(o['W3'], 2), 90),
              'M3b': (round(o['W3b'], 2), 90), 'M2b': (round(o['W2b'], 2), 90)}
        P = {'vg3b': round(o['vg3b'], 3), 'lf': '%.4g' % o['lf']}
        d = sim.acnoise('base', P, sz=sz, replace=variant(round(o['vg2b'], 3), o['rs']))
        out[name] = dict(z0db=d['z0db'], f3=d['f3'], pk=d['pk'], pwr=d['pwr'], in5=d['in5'], in1=d['in1'],
                         irms=d['irms'], vds_m1=d['@m1[vds]'], vdsat_m1=d['@m1[vdsat]'], sizes=sz, P=P,
                         vg2b=round(o['vg2b'], 3), rs=o['rs'])
        np.savetxt(os.path.join(DATA, f'ac_{name}.csv'), np.column_stack([d['f'], d['zdb'], np.interp(d['f'], d['fn'], d['inoise']) * 1e12]),
                   delimiter=',', header='freq_Hz,Zt_dBohm,in_noise_pA_rtHz', comments='')
        print(name, {k: v for k, v in out[name].items() if k not in ('sizes', 'P')})
    json.dump(out, open(os.path.join(DATA, 'baseline_reopt.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    args = sys.argv[1:] or ['screen', 'fit', 'fitlf', 'lfscan']
    if args[0] == 'opt':
        step_opt()
    elif args[0] == 'optgain':
        step_opt(float(args[1]), 'baseline_opt_gain.json', workers=1)
    else:
        for a in args:
            {'screen': step_screen, 'fit': step_fit, 'fitlf': step_fit_lf, 'lfscan': step_lfscan,
             'optnoise': step_optnoise}[a]()
