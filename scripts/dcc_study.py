"""Characterise the DC-cancellation (DCC) loop added to the proposed TIA.

Usage:  python3 dcc_study.py [idc noise loop step eye pvt mc]   (no arguments = all)
"""
import os, sys, json
import numpy as np
from multiprocessing import Pool
import sim, circuits as C
import run_all as R

DATA = R.DATA
IDC = [0, 10, 25, 50, 75, 100, 150, 200, 300, 400, 500, 600, 700, 850, 1000]


def with_idc(idc, extra=None):
    def rep(el):
        el = [(e[:4] + (f'{idc}u', e[5])) if e[1] == 'Iin' else e for e in el]
        return extra(el) if extra else el
    return rep


def lf_corner(f, z, z0):
    """Lower -3 dB frequency (the high-pass corner set by the DCC loop)."""
    idx = np.where((z < z0 - 3) & (f < 1e8))[0]
    if not len(idx):
        return 0.0
    k = idx[-1]
    return float(10 ** np.interp(z0 - 3, [z[k], z[k + 1]], [np.log10(f[k]), np.log10(f[k + 1])]))


def metrics(circ, idc, P=None, noise=False, fstart='1k', **kw):
    d = sim.acnoise(circ, P, noise=noise, fstart=fstart, replace=with_idc(idc), **kw)
    r = R.scal(d)
    f, z = d['f'], d['zdb']
    r['pk_hf'] = float(z[f >= 3e8].max() - d['z0db'])        # peaking in the signal band
    r['pk_lf'] = float(z[f <= 1e8].max() - d['z0db'])        # bump near the DCC corner
    r.update(idc_uA=idc, f_lo=lf_corner(d['f'], d['zdb'], d['z0db']), imf=d['@mf[id]'],
             idcc=d.get('@mdc[id]', 0.0), vout=d['v(out)'])
    return r, d


def step_idc():
    out = {'prop': [], 'dcc': []}
    for idc in IDC:
        for c in ('prop', 'dcc'):
            r, d = metrics(c, idc)
            out[c].append(r)
            if idc in (0, 100, 300, 500):
                np.savetxt(os.path.join(DATA, f'ac_{c}_idc{idc}.csv'), np.column_stack([d['f'], d['zdb']]), delimiter=',',
                           header='freq_Hz,Zt_dBohm', comments='')
        p, q = out['prop'][-1], out['dcc'][-1]
        print('Idc=%4d uA | prop: Z0=%.2f f3=%.2fG pk=%.2f Imf=%.1fu | dcc: Z0=%.2f f3=%.2fG pk=%.2f Imf=%.1fu Idcc=%.1fu flo=%.3gHz P=%.3fmW' % (
            idc, p['z0db'], p['f3'] / 1e9, p['pk'], p['imf'] * 1e6, q['z0db'], q['f3'] / 1e9, q['pk'], q['imf'] * 1e6,
            q['idcc'] * 1e6, q['f_lo'], q['pwr'] * 1e3), flush=True)
    R.J('dcc_idc.json', out)


def step_noise():
    rows = []
    for c, idc in [('prop', 0), ('dcc', 0), ('dcc', 100), ('dcc', 300), ('dcc', 500)]:
        r, d = metrics(c, idc, noise=True, fstart='10meg')
        r['circ'] = c
        rows.append(r)
        np.savetxt(os.path.join(DATA, f'noise_{c}_idc{idc}.csv'), np.column_stack([d['fn'], d['inoise'] * 1e12]),
                   delimiter=',', header='freq_Hz,in_noise_pA_rtHz', comments='')
        print('%s Idc=%d: in5=%.2f pA/rtHz irms=%.3f uA shot(5G)=%.2f pA/rtHz' % (
            c, idc, r['in5'], r['irms'] * 1e6, np.sqrt(2 * 1.602e-19 * idc * 1e-6) * 1e12))
    R.J('dcc_noise.json', rows)


def loop_gain(idc):
    """DCC loop gain from the closed- and open-loop transimpedance:  Z_c = Z_o/(1+T).
    Open loop = same circuit and operating point with the gate of Mdc held by a DC
    source at its closed-loop value (OTA output left loaded by Cint only)."""
    t = os.path.join(sim.TMP, f'dccloop_{idc}')
    out = sim.run(sim.build('dcc', control=f'op\nprint v(vx)\nac dec 40 10 10g\nwrdata {t}c.txt v(out)',
                            replace=with_idc(idc)))
    vx = sim.vals(out)['v(vx)']
    def brk(el):
        return [(e[:3] + ('vxg',) + e[4:]) if e[1] == 'Mdc' else e for e in el]
    sim.run(sim.build('dcc', control=f'ac dec 40 10 10g\nwrdata {t}o.txt v(out)', replace=with_idc(idc, brk),
                      extra_lines=[f'Vfrz vxg 0 dc {vx:.9g}']))
    c = np.loadtxt(t + 'c.txt'); o = np.loadtxt(t + 'o.txt')
    f = c[:, 0]
    T = (o[:, 1] + 1j * o[:, 2]) / (c[:, 1] + 1j * c[:, 2]) - 1
    mag = 20 * np.log10(abs(T)); ph = np.degrees(np.unwrap(np.angle(T)))
    i = np.where(mag < 0)[0]
    fu = pm = np.nan
    if len(i) and i[0] > 0:
        k = i[0]
        fu = 10 ** np.interp(0, [mag[k], mag[k - 1]], [np.log10(f[k]), np.log10(f[k - 1])])
        p = np.interp(np.log10(fu), np.log10(f), ph)
        pm = 180 + ((p + 180) % 360 - 180)
    np.savetxt(os.path.join(DATA, f'dcc_loop_idc{idc}.csv'), np.column_stack([f, mag, ph]), delimiter=',',
               header='freq_Hz,T_dB,T_phase_deg', comments='')
    return dict(idc_uA=idc, T0_db=float(mag[0]), f_unity=float(fu), pm_deg=float(pm), vx=float(vx))


def step_loop():
    rows = [loop_gain(i) for i in (0, 25, 50, 100, 200, 300, 500, 700)]
    for r in rows:
        print(r)
    R.J('dcc_loop.json', rows)


def step_step():
    """Photocurrent step 0 -> 200 uA (and back) with a 10 Gb/s data pattern on top
    removed: shows the settling of the cancellation loop."""
    out = {}
    for c in ('prop', 'dcc'):
        t = os.path.join(sim.TMP, f'dccstep_{c}.txt')
        lines = ['Iin 0 in pwl(0 0 1u 0 1.001u 200u 6u 200u 6.001u 0 11u 0)']
        rep = lambda el: [e for e in el if e[1] != 'Iin']
        ctl = f'tran 2n 11u\nwrdata {t} v(out) @mdc[id] @mf[id]' if c == 'dcc' else f'tran 2n 11u\nwrdata {t} v(out) @mf[id]'
        ex = ['.save v(out) @mf[id]' + (' @mdc[id]' if c == 'dcc' else '')]
        sim.run(sim.build(c, control=ctl, extra_lines=lines + ex, replace=rep))
        a = np.loadtxt(t)
        tt, v = a[:, 0], a[:, 1]
        cols = [tt, v] + ([a[:, 2], a[:, 3]] if c == 'dcc' else [a[:, 2]])
        np.savetxt(os.path.join(DATA, f'dcc_step_{c}.csv'), np.column_stack(cols), delimiter=',',
                   header='time_s,vout_V,' + ('Imdc_A,Imf_A' if c == 'dcc' else 'Imf_A'), comments='')
        v0 = np.interp(0.9e-6, tt, v); v1 = np.interp(5.9e-6, tt, v)
        m = (tt > 1e-6) & (tt < 6e-6)
        dv = v[m] - v1
        settle = tt[m][np.where(abs(dv) > 0.1 * abs(v[m][0] - v1) + 1e-3)[0][-1]] - 1e-6 if (abs(dv) > 1e-3).any() else 0
        out[c] = dict(v_before=float(v0), v_after=float(v1), dip=float(v[m].min() - v0), settle_s=float(settle))
        print(c, out[c])
    R.J('dcc_step.json', out)


def step_eye():
    rows = []
    for c in ('prop', 'dcc'):
        for idc in (0, 100, 300):
            r = R.eye_run(c, 10e9, tag=f'_10g_idc{idc}', idc=idc * 1e-6)
            r['idc_uA'] = idc
            rows.append(r); print(r, flush=True)
    R.J('dcc_eye.json', rows)


def _pvt(args):
    name, P, kw = args
    res = {'case': name}
    for idc in (0, 300):
        r, _ = metrics('dcc', idc, P, **kw)
        res[f'idc{idc}'] = r
    rp, _ = metrics('prop', 0, P, **kw)
    res['prop0'] = rp
    return res


def pvt_cases():
    cases = [(c, {}, dict(corner=c)) for c in sim.CORNERS]
    cases += [('VDD 0.9 V', {'vdd': 0.9}, {}), ('VDD 1.1 V', {'vdd': 1.1}, {}),
              ('T = -40 C', {'temp': -40}, {}), ('T = 85 C', {'temp': 85}, {}),
              ('R +15 %', {}, dict(rscale=1.15)), ('R -15 %', {}, dict(rscale=0.85)),
              ('SS, 0.9 V, 85 C', {'vdd': 0.9, 'temp': 85}, dict(corner='SS')),
              ('FF, 1.1 V, -40 C', {'vdd': 1.1, 'temp': -40}, dict(corner='FF'))]
    return cases


def step_pvt():
    with Pool(2) as p:
        rows = p.map(_pvt, pvt_cases())
    for r in rows:
        a, b, q = r['idc0'], r['idc300'], r['prop0']
        print('%-18s dark: Idcc=%5.1fu Imf=%5.1fu (prop Imf=%5.1fu) f3=%.2fG | 300uA: Imf=%5.1fu Idcc=%5.1fu f3=%.2fG pk=%.2f' % (
            r['case'], a['idcc'] * 1e6, a['imf'] * 1e6, q['imf'] * 1e6, a['f3'] / 1e9, b['imf'] * 1e6, b['idcc'] * 1e6,
            b['f3'] / 1e9, b['pk']))
    R.J('dcc_pvt.json', rows)


def _mc(seed):
    """Local mismatch (Pelgrom) on every device; the proposed core without the loop is
    evaluated with the same draws for comparison."""
    rng = np.random.default_rng(1000 + seed)
    el = C.proposed_dcc()
    mm = {}
    for e in el:
        if e[0] == 'M':
            w, l = e[7] * 1e-6, e[8] * 1e-9
            mm[e[1]] = (rng.normal(0, R.AVT / np.sqrt(w * l)), rng.normal(0, R.ABETA / np.sqrt(w * l)))
    out = {'seed': seed}
    rp, _ = metrics('prop', 0, mismatch={k: v for k, v in mm.items() if k in dict.fromkeys(e[1] for e in C.proposed())})
    out['prop0'] = dict(imf=rp['imf'], f3=rp['f3'], pk=rp['pk_hf'], z0db=rp['z0db'])
    for idc in (0, 300):
        r, _ = metrics('dcc', idc, mismatch=mm)
        out[f'idc{idc}'] = dict(idcc=r['idcc'], imf=r['imf'], f3=r['f3'], pk=r['pk_hf'], z0db=r['z0db'])
    return out


def step_mc(n=100):
    with Pool(2) as p:
        rows = p.map(_mc, range(n))
    for k in ('prop0', 'idc0', 'idc300'):
        g = lambda q: np.array([r[k][q] for r in rows])
        if k == 'prop0':
            rows_ = rows
        print('%s: Idcc median %.1f max %.1f uA | Imf mean %.1f sd %.1f min %.1f uA | f3 mean %.2f sd %.2f min %.2f GHz | pk max %.2f dB | Z0 mean %.2f sd %.2f dBohm' % (
            k, np.median(g('idcc')) * 1e6 if k != 'prop0' else 0, g('idcc').max() * 1e6 if k != 'prop0' else 0, g('imf').mean() * 1e6, g('imf').std() * 1e6, g('imf').min() * 1e6,
            g('f3').mean() / 1e9, g('f3').std() / 1e9, g('f3').min() / 1e9, g('pk').max(), g('z0db').mean(), g('z0db').std()))
    R.J('dcc_mc.json', rows)


STEPS = dict(idc=step_idc, noise=step_noise, loop=step_loop, step=step_step, eye=step_eye, pvt=step_pvt, mc=step_mc)

if __name__ == '__main__':
    for s in sys.argv[1:] or list(STEPS):
        print(f'===== {s} =====', flush=True); STEPS[s]()
