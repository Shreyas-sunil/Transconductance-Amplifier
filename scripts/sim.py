"""ngspice driver: builds netlists from circuits.py, runs them, returns metrics."""
import os, re, subprocess, tempfile, itertools
import numpy as np
import circuits as C

TMP = tempfile.mkdtemp(prefix='tia_')
_cnt = itertools.count()

CORNERS = {  # (dVth_n [V], dVth_p [V] (|Vth| shift), mobility scale n, p)
    'TT': (0.0, 0.0, 1.00, 1.00),
    'FF': (-0.03, -0.03, 1.05, 1.05),
    'SS': (+0.03, +0.03, 0.95, 0.95),
    'FS': (-0.03, +0.03, 1.05, 0.95),
    'SF': (+0.03, -0.03, 0.95, 1.05),
}


def corner_extra(elems, corner='TT', mismatch=None):
    """Per-instance delvto / mulu0 for a process corner (+ optional mismatch dict
    name -> (dvth, dbeta_rel))."""
    dvn, dvp, mun, mup = CORNERS[corner] if isinstance(corner, str) else corner
    ex = {}
    for e in elems:
        if e[0] != 'M':
            continue
        name, typ = e[1], e[6]
        dv, mu = (dvn, mun) if typ == 'n' else (-dvp, mup)   # pmos: vth0<0, |Vth| up => delvto<0
        if mismatch and name in mismatch:
            mdv, mdb = mismatch[name]
            dv += mdv; mu *= (1 + mdb)
        if dv != 0 or mu != 1:
            ex[name] = f'delvto={dv:.6g} mulu0={mu:.6g}'
    return ex


def build(circ='prop', P=None, sz=None, corner='TT', mismatch=None, rscale=1.0,
          cscale=1.0, control='', extra_lines=(), replace=None):
    elems = {'prop': C.proposed, 'base': C.baseline, 'dcc': C.proposed_dcc}[circ](sz)
    if replace:
        elems = replace(elems)
    p = dict(C.BASE_P if circ == 'base' else C.PROP_P)
    if circ == 'dcc':
        p.update(C.DCC_P)
    p.update(P or {})
    ex = corner_extra(elems, corner, mismatch)
    lines = [f'* {circ} TIA (auto-generated)', f'.include {C.MODEL}', C.param_line(p),
             f".temp {p['temp']}"]
    lines += C.spice_lines(elems, ex, rscale, cscale)
    lines += list(extra_lines)
    lines += ['.control', 'set noaskquit', 'set wr_singlescale', control, '.endc', '.end']
    return '\n'.join(lines) + '\n'


def run(net, tag=None):
    tag = tag or f'r{os.getpid()}_{next(_cnt)}'
    f = os.path.join(TMP, tag + '.cir')
    open(f, 'w').write(net)
    r = subprocess.run(['ngspice', '-b', f], capture_output=True, text=True, cwd=TMP)
    return r.stdout + r.stderr


def vals(out):
    d = {}
    for m in re.finditer(r'^\s*([\w@\[\]\(\)\.#]+)\s*=\s*([-+0-9.eE]+)\s*$', out, re.M):
        d[m.group(1).lower()] = float(m.group(2))
    return d


def f3db(f, zdb, ref=None, fref=1e8):
    """First -3 dB crossing above fref, relative to gain at fref."""
    z0 = zdb[np.argmin(abs(f - fref))] if ref is None else ref
    idx = np.where((zdb < z0 - 3) & (f > fref))[0]
    if not len(idx):
        return np.nan
    k = idx[0]
    return 10 ** np.interp(z0 - 3, [zdb[k], zdb[k - 1]], [np.log10(f[k]), np.log10(f[k - 1])])


def acnoise(circ='prop', P=None, noise=True, fstart='10meg', fstop='200g', ppd=40,
            ops=None, **kw):
    """Operating point + AC transimpedance (+ input-referred noise)."""
    t = os.path.join(TMP, f'd{os.getpid()}_{next(_cnt)}')
    mos = {'prop': ['m1', 'm2', 'm3', 'm3b', 'mf', 'mt'], 'base': ['m1', 'm2', 'm3', 'm2b', 'm3b'],
           'dcc': ['m1', 'm2', 'm3', 'm3b', 'mf', 'mt', 'mdc', 'mr', 'mns', 'mtp', 'ma', 'mb']}[circ]
    ops = ops or ['id', 'gm', 'gds', 'vds', 'vdsat', 'vgs', 'vth', 'gmbs']
    ctl = ['op', 'print v(in) v(out) v(n) i(vdd)' + (' v(g) v(vb1) v(vbp)' if circ != 'base' else '') + (' v(vrep) v(ti) v(to) v(vx) v(tp) v(oa)' if circ == 'dcc' else '')]
    for o in ops:
        ctl.append('print ' + ' '.join(f'@{m}[{o}]' for m in mos))
    ctl += [f'ac dec {ppd} {fstart} {fstop}', f'wrdata {t}_ac.txt vdb(out) vp(out) vdb(in)']
    if noise:
        ctl += [f'noise v(out) iin dec {ppd} {fstart} {fstop}', 'setplot noise1',
                f'wrdata {t}_n.txt inoise_spectrum onoise_spectrum']
    out = run(build(circ, P, control='\n'.join(ctl), **kw))
    d = vals(out)
    a = np.loadtxt(t + '_ac.txt')
    f, z, ph = a[:, 0], a[:, 1], np.unwrap(a[:, 2])
    d.update(f=f, zdb=z, ph=ph, zin_db=a[:, 3], stdout=out)
    z0 = z[np.argmin(abs(f - 1e8))]
    d['z0db'] = z0; d['z0'] = 10 ** (z0 / 20)
    d['pk'] = z.max() - z0; d['fpk'] = f[z.argmax()]
    d['f3'] = f3db(f, z)
    # group delay
    gd = -np.gradient(ph, 2 * np.pi * f)
    d['gd'] = gd
    vdd = float((P or {}).get('vdd', 1.0))
    d['pwr'] = -d['i(vdd)'] * vdd
    if noise:
        n = np.loadtxt(t + '_n.txt')
        d['fn'], d['inoise'], d['onoise'] = n[:, 0], n[:, 1], n[:, 2]
        for fq, key in [(1e9, 'in1'), (5e9, 'in5'), (10e9, 'in10'), (15e9, 'in15')]:
            d[key] = float(np.interp(fq, n[:, 0], n[:, 1])) * 1e12
        fb = d['f3'] if np.isfinite(d['f3']) else 10e9
        m = n[:, 0] <= fb
        d['irms'] = float(np.sqrt(np.trapezoid(n[m, 1] ** 2, n[m, 0])))
        # output-referred noise integrated over everything, divided by midband gain
        d['irms_tot'] = float(np.sqrt(np.trapezoid(n[:, 2] ** 2, n[:, 0])) / d['z0'])
        d['in_avg'] = d['irms'] / np.sqrt(fb)
    return d
