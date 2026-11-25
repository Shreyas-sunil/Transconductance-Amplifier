"""Small ngspice driver + netlist emitters (ngspice, LTspice, Spectre/gpdk090).

A circuit is a list of element tuples:
  ('M', name, d, g, s, b, 'n'|'p', W_um, L_nm)
  ('R'|'C'|'L', name, a, b, value)            value: float (SI) or str
  ('V', name, p, n, dc)                       ideal DC voltage source
  ('I', name, p, n, dc, ac)                   current from p to n through the source
The photodiode is always Iin (0 -> in, ac 1) plus Cpd at node 'in'; output node 'out'.
"""
import os, re, subprocess, tempfile, itertools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL = os.path.join(ROOT, 'models', 'ptm90.lib')
TMP = tempfile.mkdtemp(prefix='tia25_')
_cnt = itertools.count()

# PTM has no foundry corners: emulate with threshold / mobility skews (same as the repo)
CORNERS = {'TT': (0, 0, 1, 1), 'FF': (-.03, -.03, 1.05, 1.05), 'SS': (.03, .03, .95, .95),
           'FS': (-.03, .03, 1.05, .95), 'SF': (.03, -.03, .95, 1.05)}


def fmt(v):
    if isinstance(v, str):
        return v
    for s, m in (('T', 1e12), ('G', 1e9), ('Meg', 1e6), ('k', 1e3), ('', 1), ('m', 1e-3),
                 ('u', 1e-6), ('n', 1e-9), ('p', 1e-12), ('f', 1e-15)):
        if abs(v) >= m * 0.9999:
            return f'{v / m:.5g}{s}'
    return f'{v:.5g}' if v == 0 else f'{v / 1e-18:.5g}a'


def geom(w):            # 0.2 um diffusion each side, as in the repo
    return w * 0.2, 2 * w + 0.4


def spice(elems, corner='TT', mismatch=None, nmod='nmos90', pmod='pmos90', ltspice=False):
    dvn, dvp, mun, mup = CORNERS[corner]
    out = []
    for e in elems:
        k, n = e[0], e[1]
        if k == 'M':
            _, _, d, g, s, b, t, w, l = e
            ad, pd = geom(w)
            line = f'{n} {d} {g} {s} {b} {nmod if t == "n" else pmod} W={w:.4g}u L={l:.4g}n AD={ad:.4g}p AS={ad:.4g}p PD={pd:.4g}u PS={pd:.4g}u'
            dv, mu = (dvn, mun) if t == 'n' else (-dvp, mup)
            if mismatch and n in mismatch:
                dv += mismatch[n][0]; mu *= 1 + mismatch[n][1]
            if (dv or mu != 1) and not ltspice:
                line += f' delvto={dv:.5g} mulu0={mu:.5g}'
        elif k in 'RCL':
            line = f'{n} {e[2]} {e[3]} {fmt(e[4])}'
        elif k == 'V':
            line = f'{n} {e[2]} {e[3]} dc {fmt(e[4])}'
        elif k == 'I':
            line = f'{n} {e[2]} {e[3]} dc {fmt(e[4])}' + (f' ac {e[5]}' if len(e) > 5 and e[5] else '')
        out.append(line)
    return out


def spectre(elems):
    """Spectre lines for gpdk090 (nmos1v / pmos1v, L >= 100 nm)."""
    out = []
    for e in elems:
        k, n = e[0], e[1]
        if k == 'M':
            _, _, d, g, s, b, t, w, l = e
            ad, pd = geom(w)
            out.append(f'{n} ({d} {g} {s} {b}) {"nmos1v" if t == "n" else "pmos1v"} w={w:.4g}u l={max(l, 100):.4g}n '
                       f'ad={ad:.4g}p as={ad:.4g}p pd={pd:.4g}u ps={pd:.4g}u')
        elif k == 'R':
            out.append(f'{n} ({e[2]} {e[3]}) resistor r={fmt(e[4])}')
        elif k == 'C':
            out.append(f'{n} ({e[2]} {e[3]}) capacitor c={fmt(e[4])}')
        elif k == 'L':
            out.append(f'{n} ({e[2]} {e[3]}) inductor l={fmt(e[4])}')
        elif k == 'V':
            out.append(f'{n} ({e[2]} {e[3]}) vsource dc={fmt(e[4])} type=dc')
        elif k == 'I':
            ac = f' mag={e[5]}' if len(e) > 5 and e[5] else ''
            out.append(f'{n} ({e[2]} {e[3]}) isource dc={fmt(e[4])} type=dc{ac}')
    return [l.replace('{', '').replace('}', '') for l in out]


def run(net):
    f = os.path.join(TMP, f'r{os.getpid()}_{next(_cnt)}.cir')
    open(f, 'w').write(net)
    r = subprocess.run(['ngspice', '-b', f], capture_output=True, text=True, cwd=TMP, timeout=300)
    return r.stdout + r.stderr


def vals(out):
    d = {}
    for m in re.finditer(r'^\s*([\w@\[\]\(\)\.#]+)\s*=\s*([-+0-9.eE]+)\s*$', out, re.M):
        d[m.group(1).lower()] = float(m.group(2))
    return d


def f3db(f, z, fref):
    z0 = np.interp(np.log10(fref), np.log10(f), z)
    idx = np.where((z < z0 - 3) & (f > fref))[0]
    if not len(idx):
        return np.nan
    k = idx[0]
    return 10 ** np.interp(z0 - 3, [z[k], z[k - 1]], [np.log10(f[k]), np.log10(f[k - 1])])


def measure(elems, vdd=1.0, temp=35, corner='TT', mismatch=None, noise=True, fref=1e7,
            fstart=1e6, fstop=1e11, ppd=30, extra=(), mos_ops=False, out_node='out'):
    t = os.path.join(TMP, f'd{os.getpid()}_{next(_cnt)}')
    mos = [e[1].lower() for e in elems if e[0] == 'M']
    ctl = ['op', 'print i(vdd) v(in) v(' + out_node + ')']
    if mos_ops:
        for o in ('id', 'gm', 'vds', 'vdsat', 'vgs', 'vth'):
            ctl.append('print ' + ' '.join(f'@{m}[{o}]' for m in mos))
    ctl += [f'ac dec {ppd} {fstart:g} {fstop:g}', f'wrdata {t}_ac.txt vdb({out_node}) vp({out_node})']
    if noise:
        ctl += [f'noise v({out_node}) iin dec {ppd} {fstart:g} {fstop:g}', 'setplot noise1',
                f'wrdata {t}_n.txt inoise_spectrum']
    net = '\n'.join(['* tia', f'.include {MODEL}', f'.temp {temp}'] + spice(elems, corner, mismatch)
                    + list(extra) + ['.control', 'set noaskquit', 'set wr_singlescale'] + ctl
                    + ['.endc', '.end']) + '\n'
    out = run(net)
    d = vals(out)
    try:
        a = np.loadtxt(t + '_ac.txt')
    except Exception:
        return dict(ok=False, stdout=out)
    f, z = a[:, 0], a[:, 1]
    d.update(ok=True, f=f, zdb=z, ph=np.unwrap(a[:, 2]), stdout=out)
    z0 = float(np.interp(np.log10(fref), np.log10(f), z))
    d['z0db'] = z0
    d['pk'] = float(max(0.0, z[f >= fref].max() - z0))
    d['f3'] = f3db(f, z, fref)
    d['pwr'] = -d.get('i(vdd)', np.nan) * vdd
    if noise:
        try:
            n = np.loadtxt(t + '_n.txt')
            d['fn'], d['inoise'] = n[:, 0], n[:, 1]
            fb = d['f3'] if np.isfinite(d['f3']) else 1e9
            m = (n[:, 0] <= fb) & (n[:, 0] >= 1e6)
            d['irms'] = float(np.sqrt(np.trapezoid(n[m, 1] ** 2, n[m, 0])))
            d['in_avg'] = d['irms'] / np.sqrt(fb) * 1e12     # pA/rtHz averaged over the bandwidth
            d['in1g'] = float(np.interp(1e9, n[:, 0], n[:, 1])) * 1e12
        except Exception:
            pass
    for k in ('f', 'zdb', 'ph', 'fn', 'inoise'):
        if k in d:
            d[k] = np.asarray(d[k])
    return d


def summary(d):
    if not d.get('ok'):
        return 'FAILED'
    return (f"Zt={d['z0db']:.2f} dBohm  pk={d['pk']:.2f} dB  f3={d['f3']/1e9:.3f} GHz  "
            f"P={d['pwr']*1e3:.3f} mW  in_avg={d.get('in_avg', np.nan):.2f} pA/rtHz  Vin={d.get('v(in)', np.nan):.3f} Vout={d.get('v(out)', np.nan):.3f}")
