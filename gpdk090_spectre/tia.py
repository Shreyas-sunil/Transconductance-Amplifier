#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""GPDK090 / Spectre characterisation campaign for the CONECCT 2027 TIA paper.

Runs on the Cadence VM (python 2.6/2.7, no numpy).  Every circuit is written here as a
Spectre netlist, simulated with the GPDK090 v4.6 models (gpdk090_nmos1v / gpdk090_pmos1v,
sections NN/SS/FF/SF/FS, mismatch statistics from section stat_mis), and reduced to CSV.

    python2 tia.py all          # everything (about 30-60 min)
    python2 tia.py <task> ...   # single tasks, see TASKS at the bottom

Outputs go to $OUT (default ~/exchange/tia_results).  Raw PSF is deleted after parsing
to save disk space; the netlists of every run are kept in $OUT/netlists.
"""
import os, sys, re, math, random, time, glob, shutil, subprocess, traceback

HOME = os.path.expanduser('~')
MODELS = os.environ.get('GPDK_MODELS', HOME + '/cadence/gpdk090_v4.6/models/spectre')
OUT = os.environ.get('OUT', HOME + '/exchange/tia_results')
WORK = os.environ.get('WORK', '/tmp/tia_work')
for d in (OUT, WORK, OUT + '/netlists', OUT + '/csv', OUT + '/logs'):
    if not os.path.isdir(d):
        os.makedirs(d)
LOG = open(OUT + '/logs/campaign.log', 'a')


def log(*a):
    s = time.strftime('%H:%M:%S ') + ' '.join([str(x) for x in a])
    print(s)
    LOG.write(s + '\n')
    LOG.flush()


# --------------------------------------------------------------------------------------
# PSF-ASCII reader
# --------------------------------------------------------------------------------------
TOK = re.compile(r'"[^"]*"|\(|\)|[^\s()]+')


def _num(t):
    try:
        return float(t)
    except ValueError:
        if t.lower() in ('nan', 'inf', '-inf'):
            return float(t)
        return None


def read_psf(path):
    """Return dict name -> list of values (float or complex). Struct values are skipped."""
    txt = open(path).read()
    i = txt.find('\nVALUE')
    if i < 0:
        return {}
    toks = TOK.findall(txt[i + 6:])
    out = {}
    order = []
    k = 0
    n = len(toks)
    while k < n:
        t = toks[k]
        if t == 'END':
            break
        if t == 'PROP' and k + 1 < n and toks[k + 1] == '(':
            depth = 0
            while k < n:
                if toks[k] == '(':
                    depth += 1
                elif toks[k] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            k += 1
            continue
        if t.startswith('"'):
            name = t[1:-1]
            k += 1
            if k < n and toks[k].startswith('"'):      # type name of an unswept value
                k += 1
            if k >= n:
                break
            if toks[k] == '(':
                vals = []
                depth = 0
                while k < n:
                    if toks[k] == '(':
                        depth += 1
                    elif toks[k] == ')':
                        depth -= 1
                        if depth == 0:
                            break
                    else:
                        vals.append(toks[k])
                    k += 1
                k += 1
                nums = [_num(v) for v in vals]
                if len(nums) == 2 and None not in nums:
                    v = complex(nums[0], nums[1])
                else:
                    v = None                       # struct: ignore
            else:
                v = _num(toks[k])
                k += 1
            if v is not None:
                if name not in out:
                    out[name] = []
                    order.append(name)
                out[name].append(v)
            continue
        k += 1
    return out


# --------------------------------------------------------------------------------------
# Spectre runner
# --------------------------------------------------------------------------------------
RUNS = [0]


def spectre(name, body, section='NN', temp=35, keep=False, extra_inc=''):
    """Write netlist, run Spectre, return raw directory (psfascii)."""
    RUNS[0] += 1
    d = os.path.join(WORK, name)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    net = ('simulator lang=spectre\nglobal 0\n'
           'include "%s/gpdk090.scs" section=%s\n%s'
           'simOpts options temp=%g tnom=27 reltol=1e-4 vabstol=1e-7 iabstol=1e-13 gmin=1e-15\n'
           % (MODELS, section, extra_inc, temp)) + body
    nf = os.path.join(d, 'tb.scs')
    open(nf, 'w').write(net)
    shutil.copy(nf, os.path.join(OUT, 'netlists', name + '.scs'))
    raw = os.path.join(d, 'raw')
    cmd = 'cd %s && spectre -format psfascii -raw raw tb.scs > spectre.log 2>&1' % d
    t0 = time.time()
    rc = subprocess.call(cmd, shell=True)
    dt = time.time() - t0
    lg = open(os.path.join(d, 'spectre.log')).read()
    if rc != 0 or 'spectre completes with 0 errors' not in lg:
        errs = [l for l in lg.split('\n') if 'ERROR' in l or 'Error' in l][:10]
        shutil.copy(os.path.join(d, 'spectre.log'), os.path.join(OUT, 'logs', name + '.log'))
        log('SPECTRE FAIL', name, rc, ' | '.join(errs))
        raise RuntimeError('spectre failed: ' + name)
    if keep:
        shutil.copy(os.path.join(d, 'spectre.log'), os.path.join(OUT, 'logs', name + '.log'))
    log('spectre', name, '%.1fs' % dt)
    return raw


def files(raw, suffix):
    """Files of an analysis, sorted by the numeric indices in their names."""
    fs = [f for f in os.listdir(raw) if f.endswith(suffix)]

    def key(f):
        return [int(x) for x in re.findall(r'-(\d+)_', f)]
    fs.sort(key=key)
    return [os.path.join(raw, f) for f in fs]


def idx(f):
    return [int(x) for x in re.findall(r'-(\d+)_', os.path.basename(f))]


def cleanup(name):
    d = os.path.join(WORK, name)
    if os.path.isdir(d):
        shutil.rmtree(d)


# --------------------------------------------------------------------------------------
# Circuits
# --------------------------------------------------------------------------------------
def mos(name, d, g, s, b, typ, w, l):
    """w: number (um) or a parameter name."""
    if isinstance(w, str):
        W = '(%s)' % w
    else:
        W = '%.6g' % w
    return ('%s (%s %s %s %s) gpdk090_%s1v w=%s*1u l=%gn ad=%s*0.58*1p as=%s*0.58*1p pd=2*(%s+0.58)*1u ps=2*(%s+0.58)*1u\n'
            % (name, d, g, s, b, 'nmos' if typ == 'n' else 'pmos', W, l, W, W, W, W))


DEVS_P = ['M1', 'M2', 'M3', 'M3b', 'Mf', 'Mt', 'Mbp', 'Mbr', 'Mbn']
DEVS_B = ['M1', 'M2', 'M3', 'M3b', 'M2b']
DEVS_DCC = ['Mq', 'Mnq', 'Mr', 'Mns', 'Mtp', 'Ma', 'Mb', 'Mna', 'Mnb', 'Mdc']

# proposed v1: paper Table I with L = 100 nm (GPDK090 minimum) where the PTM design used 90 nm
V1 = dict(w1=4.5, w2=3.5, w3=7.0, w3b=28.0, wf=3.5, wt=12.0, rn=5e3, rb=4.2e3, ca=30e-15,
          iref=50e-6, wbn=0.4, vtn=0.24)


def proposed(P, mode='ai', dcc=None):
    """Proposed TIA.  mode: 'ai' (tunable gyrator-C feedback, the proposed circuit),
    'pf' plain source-follower feedback (Mf gate = OUT, no Mt, no Ca),
    'pfca' plain follower plus Ca from OUT to IN, 'aint' Mt present but Ca removed.
    Every design value is the Spectre parameter p_<key> (see pvals)."""
    s = ''
    s += 'Vdd (vdd 0) vsource dc=vdd\n'
    s += 'Iref (vbp 0) isource dc=p_iref\n'
    s += mos('Mbp', 'vbp', 'vbp', 'vdd', 'vdd', 'p', 2, 180)
    s += mos('Mbr', 'vb1', 'vbp', 'vdd', 'vdd', 'p', 2, 180)
    s += mos('Mbn', 'vb1', 'vb1', 'vr', '0', 'n', 'p_wbn', 100)
    s += 'Rb (vr 0) resistor r=p_rb*rsc\n'
    s += 'Cb (vb1 0) capacitor c=2p\n'
    s += 'Rn (vdd n) resistor r=p_rn*rsc\n'
    s += mos('M1', 'n', 'vb1', 'inp', '0', 'n', 'p_w1', 100)
    s += 'IPl (n g2) iprobe\n'
    s += mos('M2', 'inp', 'g2', '0', '0', 'n', 'p_w2', 100)
    s += mos('M3', 'outp', 'n', '0', '0', 'n', 'p_w3', 100)
    s += mos('M3b', 'outp', 'vbp', 'vdd', 'vdd', 'p', 'p_w3b', 180)
    if mode in ('ai', 'aint'):
        s += 'Vt (vt 0) vsource dc=vtn\n'
        s += mos('Mf', 'vdd', 'g', 'fs', '0', 'n', 'p_wf', 100)
        s += mos('Mt', 'g', 'vt', 'outp', 'outp', 'p', 'p_wt', 100)
        if mode == 'ai':
            s += 'Ca (g inp) capacitor c=p_ca*csc\n'
    else:
        s += mos('Mf', 'vdd', 'outp', 'fs', '0', 'n', 'p_wf', 100)
        if mode == 'pfca':
            s += 'Ca (outp inp) capacitor c=p_ca*csc\n'
    s += 'IPg (fs inp) iprobe\n'
    if dcc:
        s += dcc_block(P, dcc)
    s += 'Cpd (inp 0) capacitor c=cpd\n'
    s += 'Cl (outp 0) capacitor c=cl\n'
    s += 'Iin (0 inp) isource dc=idc mag=1 %s\n' % P.get('_isrc', '')
    return s


def dcc_block(P, D):
    """DC-cancellation loop (paper Fig. 5) on GPDK090: replica follower + PMOS-input OTA
    integrating on Cint + sink device Mdc.  D['wq'] sets the threshold current I_th."""
    s = ''
    s += mos('Mq', 'nq', 'vbp', 'vdd', 'vdd', 'p', D['wq'], 180)
    s += mos('Mnq', 'nq', 'nq', '0', '0', 'n', 2, 1440)
    s += 'Rt1 (outp to) resistor r=100k\nCt1 (to 0) capacitor c=0.2p\n'
    s += 'Rt2 (inp ti) resistor r=100k\nCt2 (ti 0) capacitor c=0.2p\n'
    s += mos('Mr', 'vdd', 'to', 'vrep', '0', 'n', 'p_wf/2', 100)
    s += mos('Mns', 'vrep', 'nq', '0', '0', 'n', 5.7, 1440)
    s += mos('Mtp', 'tp', 'vbp', 'vdd', 'vdd', 'p', 0.4, 720)
    s += mos('Ma', 'oa', 'ti', 'tp', 'vdd', 'p', 4, 720)
    s += mos('Mb', 'vx', 'vrep', 'tp', 'vdd', 'p', 4, 720)
    s += mos('Mna', 'oa', 'oa', '0', '0', 'n', 1, 1440)
    s += mos('Mnb', 'vx', 'oa', '0', '0', 'n', 1, 1440)
    s += 'Cint (vx 0) capacitor c=2p\n'
    s += 'IPd (vx vxg) iprobe\n'
    s += mos('Mdc', 'inp', 'vxg', '0', '0', 'n', 6, 180)
    return s


# 2020 baseline as drawn (Alsheikhjader 2020, Fig. 1): M1 and M2b gates at VDD, M3b gate at 0.
B0 = dict(w1=5, w2=5, w3=5, w3b=5, w2b=0.9, vg2b=None, vg3b=0.0, lf=2.4e-9, rsl=0.0)


def baseline(P):
    s = 'Vdd (vdd 0) vsource dc=vdd\n'
    s += 'Vg3b (g3b 0) vsource dc=p_vg3b\n'
    if P.get('vg2b') is None:
        s += mos('M2b', 'n', 'vdd', 'vdd', 'vdd', 'p', 'p_w2b', 100)
    else:
        s += 'Vg2b (g2b 0) vsource dc=p_vg2b\n'
        s += mos('M2b', 'n', 'g2b', 'vdd', 'vdd', 'p', 'p_w2b', 100)
    s += mos('M1', 'n', 'vdd', 'inp', '0', 'n', 'p_w1', 100)
    s += 'IPl (n g2) iprobe\n'
    s += mos('M2', 'inp', 'g2', '0', '0', 'n', 'p_w2', 100)
    s += mos('M3', 'outp', 'n', '0', '0', 'n', 'p_w3', 100)
    s += mos('M3b', 'outp', 'g3b', 'vdd', 'vdd', 'p', 'p_w3b', 100)
    s += 'Lf (outp xl) inductor l=p_lf\n'
    s += 'Rsl (xl fs) resistor r=max(p_rsl,1e-3)\n'
    s += 'IPg (fs inp) iprobe\n'
    s += 'Cpd (inp 0) capacitor c=cpd\n'
    s += 'Cl (outp 0) capacitor c=cl\n'
    s += 'Iin (0 inp) isource dc=idc mag=1 %s\n' % P.get('_isrc', '')
    return s


def pkeys(P):
    return sorted([k for k in P.keys() if not k.startswith('_') and P[k] is not None and k != 'vtn'])


def pvals(P):
    return 'parameters ' + ' '.join(['p_%s=%.8g' % (k, P[k]) for k in pkeys(P)]) + '\n'


def params(P, **kw):
    d = dict(vdd=1.0, cpd=50e-15, cl=30e-15, idc=0.0, rsc=1.0, csc=1.0, vtn=P.get('vtn', 0.24))
    d.update(kw)
    return ('parameters ' + ' '.join(['%s=%.8g' % (k, v) for k, v in sorted(d.items())]) + '\n') + pvals(P)


def saves(devs):
    q = ['ids', 'vgs', 'vds', 'vth', 'vdsat', 'gm', 'gds', 'gmbs', 'region', 'cgs', 'cgd']
    return 'save outp inp n Vdd:p ' + ' '.join(['%s:%s' % (d, x) for d in devs for x in q]) + '\n'


# --------------------------------------------------------------------------------------
# Measurements
# --------------------------------------------------------------------------------------
def db(x):
    return 20 * math.log10(max(abs(x), 1e-30))


def ac_metrics(f, z):
    """f list, z complex list -> dict(gain dBohm at 100 MHz, peak dB, f3dB Hz, fpk)."""
    m = [abs(v) for v in z]
    # reference: value at 100 MHz (log interpolation)
    z0 = interp(f, m, 1e8)
    ipk = max(range(len(m)), key=lambda i: m[i])
    pk = db(m[ipk] / z0)
    thr = z0 / math.sqrt(2)
    f3 = float('nan')
    for i in range(len(m) - 1):
        if f[i] > 9e7 and m[i] >= thr and m[i + 1] < thr:
            a = math.log10(f[i]); b = math.log10(f[i + 1])
            ya = db(m[i]); yb = db(m[i + 1]); yt = db(thr)
            f3 = 10 ** (a + (b - a) * (ya - yt) / (ya - yb))
            break
    # low-frequency corner (for DCC): first rise through thr below 100 MHz
    flo = float('nan')
    for i in range(0, len(m) - 1):
        if f[i + 1] > 1e8:
            break
        if m[i] < thr <= m[i + 1]:
            flo = f[i]
    return dict(zt=db(z0), zt_ohm=z0, pk=max(pk, 0.0), f3=f3, fpk=f[ipk], flo=flo)


def interp(f, y, x):
    for i in range(len(f) - 1):
        if f[i] <= x <= f[i + 1]:
            a = math.log10(f[i]); b = math.log10(f[i + 1]); t = (math.log10(x) - a) / (b - a)
            return y[i] + (y[i + 1] - y[i]) * t
    return y[0] if x < f[0] else y[-1]


def stb_metrics(f, lg):
    """Loop gain -> DC gain (dB), unity-gain frequency, phase margin = 180 + phase lag
    accumulated from DC to the crossover (independent of the sign convention)."""
    m = [abs(v) for v in lg]
    ph = unwrap([math.degrees(math.atan2(v.imag, v.real)) for v in lg])
    fu = float('nan'); pm = float('nan')
    for i in range(len(m) - 1):
        if m[i] >= 1 > m[i + 1]:
            t = math.log10(m[i]) / (math.log10(m[i]) - math.log10(m[i + 1]))
            fu = 10 ** (math.log10(f[i]) + t * (math.log10(f[i + 1]) - math.log10(f[i])))
            p = ph[i] + t * (ph[i + 1] - ph[i])
            pm = 180 + (p - ph[0])
            break
    return dict(t0=db(m[0]), fu=fu, pm=pm, ph0=ph[0])


def unwrap(p):
    o = [p[0]]
    for v in p[1:]:
        d = v - o[-1]
        while d > 180:
            v -= 360; d -= 360
        while d < -180:
            v += 360; d += 360
        o.append(v)
    return o


def integ(f, y2, f1, f2):
    """Integral of y^2 df from f1 to f2 (trapezoid on the given grid)."""
    s = 0.0
    for i in range(len(f) - 1):
        a, b = max(f[i], f1), min(f[i + 1], f2)
        if b <= a:
            continue
        ya = interp(f, y2, a); yb = interp(f, y2, b)
        s += 0.5 * (ya + yb) * (b - a)
    return s


def wcsv(name, header, rows):
    fh = open(os.path.join(OUT, 'csv', name + '.csv'), 'w')
    fh.write(','.join(header) + '\n')
    for r in rows:
        fh.write(','.join([fmt(x) for x in r]) + '\n')
    fh.close()
    log('wrote', name, len(rows), 'rows')


def fmt(x):
    if isinstance(x, float):
        if x != x:
            return 'nan'
        return '%.6g' % x
    return str(x)


AC = 'start=1e7 stop=1e11 dec=40'
NZ = 'start=1e7 stop=1e11 dec=20'


# --------------------------------------------------------------------------------------
# Circuit registry (filled by the optimisation tasks; reloaded from csv when present)
# --------------------------------------------------------------------------------------
CIR = {}


def reg_load():
    CIR['base2020'] = ('b', dict(B0))
    CIR['v1'] = ('p', dict(V1))
    CIR['pf_v1'] = ('pf', dict(V1))
    for nm in ('regain', 'regain_eqp', 'pf_opt', 'v2'):
        fn = os.path.join(OUT, 'csv', 'design_%s.csv' % nm)
        if os.path.exists(fn):
            l = open(fn).read().strip().split('\n')
            k = l[0].split(','); v = l[1].split(',')
            P = {}
            for a, b in zip(k, v):
                P[a] = None if b == 'None' else float(b)
            kind = {'regain': 'b', 'regain_eqp': 'b', 'pf_opt': 'pf', 'v2': 'p'}[nm]
            CIR[nm] = (kind, P)


def body(kind, P, mode=None, dcc=None):
    if kind == 'b':
        return baseline(P), DEVS_B
    if kind == 'pf':
        return proposed(P, mode or 'pf'), [d for d in DEVS_P if d != 'Mt']
    return proposed(P, mode or 'ai', dcc), DEVS_P + (DEVS_DCC if dcc else [])


# --------------------------------------------------------------------------------------
# Evaluation of many candidates in one Spectre run (paramset sweep)
# --------------------------------------------------------------------------------------
def evaluate(kind, cands, tag, mode=None, cl=30e-15, cpd=50e-15, section='NN', temp=35, vdd=1.0):
    """cands: list of parameter dicts (same keys).  One Spectre run, paramset sweep."""
    keys = pkeys(cands[0])
    txt, devs = body(kind, cands[0], mode)
    hdr = params(cands[0], cl=cl, cpd=cpd, vdd=vdd)
    cols = ['p_' + k for k in keys] + (['vtn'] if 'vtn' in cands[0] else [])
    ps = 'pset paramset {\n' + ' '.join(cols) + '\n'
    for c in cands:
        ps += ' '.join(['%.8g' % c[k] for k in keys] + (['%.8g' % c['vtn']] if 'vtn' in c else [])) + '\n'
    ps += '}\n'
    an = saves(devs)
    an += 'swp sweep paramset=pset {\n dcop dc\n acx ac %s\n}\n' % 'start=1e7 stop=1e11 dec=20'
    try:
        raw = spectre(tag, hdr + txt + ps + an, section=section, temp=temp)
    except RuntimeError:
        return [dict(zt=0, zt_ohm=1, pk=99, f3=1e7, fpk=0, flo=0, idd=1, sat=False, margin=-1) for c in cands]
    acs = files(raw, '_acx.ac')
    res = []
    if len(acs) != len(cands):
        log('paramset output mismatch', len(acs), len(cands))
    for f in acs:
        d = read_psf(f)
        fr = [v.real if isinstance(v, complex) else v for v in d['freq']]
        m = ac_metrics(fr, d['outp'])
        op = read_psf(f.replace('_acx.ac', '_dcop.dc'))
        m['idd'] = abs(op.get('Vdd:p', [float('nan')])[0])
        sat = True
        worst = 9.0
        for dv in devs:
            if dv == 'Mt':
                continue
            r = op.get('%s:region' % dv, [2])[0]
            vds = abs(op.get('%s:vds' % dv, [1])[0]); vdsat = abs(op.get('%s:vdsat' % dv, [0])[0])
            if int(round(r)) != 2:
                sat = False
            worst = min(worst, vds - vdsat)
        m['sat'] = sat
        m['margin'] = worst
        res.append(m)
    cleanup(tag)
    return res


# --------------------------------------------------------------------------------------
# Differential evolution
# --------------------------------------------------------------------------------------
def de(kind, bounds, fixed, score, tag, mode=None, pop=24, gens=22, seed=1, init=None):
    rnd = random.Random(seed)
    keys = sorted(bounds.keys())

    def mk(x):
        c = dict(fixed)
        for k, v in zip(keys, x):
            c[k] = v
        return c

    def clip(x):
        return [min(max(v, bounds[k][0]), bounds[k][1]) for k, v in zip(keys, x)]
    X = [[rnd.uniform(*bounds[k]) for k in keys] for _ in range(pop)]
    if init:
        X[0] = clip([init[k] for k in keys])
    M = evaluate(kind, [mk(x) for x in X], tag + '_g0', mode)
    S = [score(m) for m in M]
    hist = []
    for g in range(1, gens + 1):
        T = []
        for i in range(pop):
            a, b, c = rnd.sample([j for j in range(pop) if j != i], 3)
            F = 0.6; CR = 0.8
            jr = rnd.randrange(len(keys))
            t = []
            for j in range(len(keys)):
                if rnd.random() < CR or j == jr:
                    t.append(X[a][j] + F * (X[b][j] - X[c][j]))
                else:
                    t.append(X[i][j])
            T.append(clip(t))
        MT = evaluate(kind, [mk(x) for x in T], tag + '_g%d' % g, mode)
        for i in range(pop):
            s = score(MT[i])
            if s > S[i]:
                X[i], S[i], M[i] = T[i], s, MT[i]
        b = max(range(pop), key=lambda i: S[i])
        hist.append((g, S[b], M[b]['zt'], M[b]['f3'], M[b]['pk'], M[b]['idd']))
        log('DE', tag, g, 'best score %.3f zt %.2f f3 %.3g pk %.2f idd %.3g' % hist[-1][1:])
    b = max(range(pop), key=lambda i: S[i])
    return mk(X[b]), M[b], hist


def es(kind, bounds, P0, score, tag, mode=None, lam=24, gens=24, seed=7, s0=0.25, s1=0.02):
    """(1+lambda) evolution strategy in log space around the incumbent, step shrinking
    geometrically from s0 to s1.  Used after DE because the feasible region is narrow."""
    rnd = random.Random(seed)
    keys = sorted(bounds.keys())
    best = dict(P0)
    mb = evaluate(kind, [best], tag + '_e0', mode)[0]
    sb = score(mb)
    hist = []
    for g in range(1, gens + 1):
        sig = s0 * (s1 / s0) ** (float(g - 1) / max(gens - 1, 1))
        C = []
        for i in range(lam):
            c = dict(best)
            for k in keys:
                lo, hi = bounds[k]
                if lo > 0:
                    v = best[k] * math.exp(rnd.gauss(0, sig))
                else:
                    v = best[k] + rnd.gauss(0, sig) * (hi - lo) * 0.5
                c[k] = min(max(v, lo), hi)
            C.append(c)
        M = evaluate(kind, C, tag + '_e%d' % g, mode)
        for c, m_ in zip(C, M):
            sc = score(m_)
            if sc > sb:
                best, mb, sb = c, m_, sc
        hist.append((g, sb, mb['zt'], mb['f3'], mb['pk'], mb['idd']))
        log('ES', tag, g, 'sig %.3f best %.4f zt %.2f f3 %.3g pk %.2f idd %.3g' % ((sig,) + hist[-1][1:]))
    return best, mb, hist


GT = 53.8    # gain target (dBohm): proposed v1 on GPDK090


def sc_factory(gt=GT, pkmax=1.0, iddmax=1.2e-3, iddmin=0.0, need_sat=True):
    def sc(m):
        f3 = m['f3'] if m['f3'] == m['f3'] else 1e8
        s = math.log10(f3)
        pen = 0.0
        pen += max(0.0, gt - m['zt']) * 20.0
        pen += max(0.0, m['pk'] - pkmax) * 1.0
        pen += max(0.0, m['idd'] - iddmax) / 1e-4
        pen += max(0.0, iddmin - m['idd']) / 1e-4
        if need_sat and not m['sat']:
            pen += 0.5 + max(0.0, -m['margin']) * 10
        return s - pen
    return sc


# --------------------------------------------------------------------------------------
# Tasks
# --------------------------------------------------------------------------------------
def save_design(nm, P):
    keys = sorted(P.keys())
    keys = [k for k in keys if not k.startswith('_')]
    wcsv('design_' + nm, keys, [[P[k] for k in keys]])


def t_opt_regain():
    """Same-gain baseline: the 2020 topology with its own gate biases and a lossy spiral,
    re-optimised ON GPDK090 for maximum bandwidth at >= the proposed gain, <= 1 dB
    peaking, <= 1.2 mW, every device in saturation."""
    bounds = dict(w1=(0.2, 10), w2=(0.2, 15), w3=(0.2, 15), w3b=(0.2, 15), w2b=(0.2, 10),
                  vg2b=(0.2, 0.9), vg3b=(0.2, 0.9), lf=(0.2e-9, 6e-9), rsl=(0, 60))
    fixed = dict(B0)
    init = dict(w1=1.05, w2=7.22, w3=1.68, w3b=1.73, w2b=4.64, vg2b=0.781, vg3b=0.527, lf=5.036e-9, rsl=43)
    P, m, h = de('b', bounds, fixed, sc_factory(), 'de_regain', init=init, gens=25)
    P, m, h2 = es('b', bounds, P, sc_factory(), 'es_regain')
    h += h2
    save_design('regain', P)
    wcsv('de_hist_regain', ['gen', 'score', 'zt', 'f3', 'pk', 'idd'], h)
    # equal-power variant: same gain, supply current forced to >= 0.9 mA
    P2, m2, h2 = de('b', bounds, fixed, sc_factory(iddmin=0.9e-3), 'de_regeqp', init=P, gens=18, seed=3)
    P2, m2, h3 = es('b', bounds, P2, sc_factory(iddmin=0.9e-3), 'es_regeqp')
    h2 += h3
    save_design('regain_eqp', P2)
    wcsv('de_hist_regain_eqp', ['gen', 'score', 'zt', 'f3', 'pk', 'idd'], h2)


PBOUNDS = dict(w1=(1, 12), w2=(1, 10), w3=(2, 20), w3b=(5, 40), wf=(1, 10), rn=(2e3, 10e3), rb=(2e3, 8e3),
               iref=(30e-6, 70e-6))


def t_opt_pf():
    """Plain source-follower feedback, re-optimised for max bandwidth at the same gain,
    <= 1 dB peaking and no more supply current than proposed v1."""
    P1 = dict(V1)
    m1 = evaluate('p', [P1], 'v1_ref')[0]
    log('v1 reference', m1)
    fixed = dict(V1)
    P, m, h = de('pf', dict(PBOUNDS), fixed, sc_factory(iddmax=m1['idd'] * 1.001), 'de_pf', init=V1)
    P, m, h2 = es('pf', dict(PBOUNDS), P, sc_factory(iddmax=m1['idd'] * 1.001), 'es_pf')
    h += h2
    save_design('pf_opt', P)
    wcsv('de_hist_pf', ['gen', 'score', 'zt', 'f3', 'pk', 'idd'], h)


def t_opt_v2():
    """Proposed topology re-sized on GPDK090 (v2): max bandwidth at >= v1 gain, <= 1 dB
    peaking, supply current <= v1, all devices saturated; Vtune is a design variable."""
    m1 = evaluate('p', [dict(V1)], 'v1_ref2')[0]
    b = dict(PBOUNDS)
    b.update(wt=(2, 24), ca=(10e-15, 60e-15), vtn=(0.0, 0.40))
    P, m, h = de('p', b, dict(V1), sc_factory(pkmax=0.5, iddmax=m1['idd'] * 1.001), 'de_v2', init=V1, gens=25)
    P, m, h2 = es('p', b, P, sc_factory(pkmax=0.5, iddmax=m1['idd'] * 1.001), 'es_v2', gens=30)
    h += h2
    save_design('v2', P)
    wcsv('de_hist_v2', ['gen', 'score', 'zt', 'f3', 'pk', 'idd'], h)


def run_ac(kind, P, tag, mode=None, dcc=None, extra='', pkw=None, an=None, section='NN', temp=35, keep=False):
    txt, devs = body(kind, P, mode, dcc)
    hdr = params(P, **(pkw or {}))
    a = an if an is not None else ('dcop dc\nacx ac %s\n' % AC)
    raw = spectre(tag, hdr + txt + extra + saves(devs) + a, section=section, temp=temp, keep=keep)
    return raw, devs


def oprow(op, devs):
    rows = []
    for d in devs:
        g = lambda q: op.get('%s:%s' % (d, q), [float('nan')])[0]
        rows.append([d, g('ids'), g('vgs'), g('vds'), g('vth'), g('vdsat'), g('vds') - g('vdsat') if True else 0,
                     g('gm'), g('gds'), g('gmbs'), g('cgs'), g('cgd'), int(round(g('region'))) if g('region') == g('region') else -1])
    return rows


ALL = ['base2020', 'regain', 'regain_eqp', 'pf_v1', 'pf_opt', 'v1', 'v2']


def t_nominal():
    """DC operating point, AC transimpedance, input impedance, noise and both loop gains
    for every circuit at NN, 35 C, 1.0 V, CPD = 50 fF, CL = 30 fF."""
    reg_load()
    summ = []
    for nm in ALL:
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        an = ('dcop dc\nacx ac %s\nnz (outp 0) noise %s iprobe=Iin\n'
              'lgg stb %s probe=IPg\nlgl stb %s probe=IPl\n') % (AC, NZ, 'start=1e6 stop=1e12 dec=20',
                                                               'start=1e6 stop=1e12 dec=20')
        if kind == 'pf' or kind == 'p':
            pass
        raw, devs = run_ac(kind, P, 'nom_' + nm, an=an, keep=True)
        op = read_psf(os.path.join(raw, 'dcop.dc'))
        wcsv('op_' + nm, ['dev', 'ids', 'vgs', 'vds', 'vth', 'vdsat', 'vds_minus_vdsat', 'gm', 'gds', 'gmbs', 'cgs', 'cgd', 'region'],
             oprow(op, devs))
        nodes = [[k, op[k][0]] for k in sorted(op.keys()) if ':' not in k]
        wcsv('nodes_' + nm, ['node', 'V'], nodes)
        d = read_psf(os.path.join(raw, 'acx.ac'))
        fr = [x.real for x in d['freq']]
        z = d['outp']; zi = d['inp']
        m = ac_metrics(fr, z)
        wcsv('ac_' + nm, ['f', 'zt_mag', 'zt_ph_deg', 'zin_mag', 'zin_ph_deg'],
             [[fr[i], abs(z[i]), math.degrees(math.atan2(z[i].imag, z[i].real)), abs(zi[i]),
               math.degrees(math.atan2(zi[i].imag, zi[i].real))] for i in range(len(fr))])
        n = read_psf(os.path.join(raw, 'nz.noise'))
        fn = [x.real if isinstance(x, complex) else x for x in n['freq']]
        vin = [abs(x) for x in n.get('in', [])]
        vout = [abs(x) for x in n.get('out', [])]
        wcsv('noise_' + nm, ['f', 'in_A_rtHz', 'out_V_rtHz'], [[fn[i], vin[i], vout[i]] for i in range(len(fn))])
        f3 = m['f3'] if m['f3'] == m['f3'] else 1e10
        irms_bw = math.sqrt(integ(fn, [v * v for v in vin], 1e7, f3))
        irms_10 = math.sqrt(integ(fn, [v * v for v in vin], 1e7, 1e10))
        orms_bw = math.sqrt(integ(fn, [v * v for v in vout], 1e7, f3 * 1.0))
        lrow = []
        for t in ('lgg', 'lgl'):
            try:
                s = read_psf(os.path.join(raw, t + '.stb'))
                fs_ = [x.real if isinstance(x, complex) else x for x in s['freq']]
                lgv = s['loopGain']
                wcsv('stb_%s_%s' % (t, nm), ['f', 'lg_mag_db', 'lg_ph_deg'],
                     [[fs_[i], db(lgv[i]), math.degrees(math.atan2(lgv[i].imag, lgv[i].real))] for i in range(len(fs_))])
                sm = stb_metrics(fs_, lgv)
                lrow += [sm['t0'], sm['fu'], sm['pm']]
            except Exception:
                log('stb parse fail', nm, t, traceback.format_exc().split('\n')[-2])
                lrow += [float('nan')] * 3
        summ.append([nm, m['zt'], m['zt_ohm'], m['pk'], m['f3'], abs(op['Vdd:p'][0]),
                     interp(fn, vin, 1e9), interp(fn, vin, 5e9), interp(fn, vin, 1e10), irms_bw, irms_10, orms_bw,
                     m['zt_ohm'] * m['f3'] if m['f3'] == m['f3'] else float('nan')] + lrow)
        cleanup('nom_' + nm)
    wcsv('nominal', ['cir', 'zt_dB', 'zt_ohm', 'pk_dB', 'f3_Hz', 'idd_A', 'in1G', 'in5G', 'in10G', 'irms_bw', 'irms_10G',
                     'vout_rms_bw', 'gbw_ohmHz', 'Tg0_dB', 'fug_Hz', 'PMg_deg', 'Tl0_dB', 'ful_Hz', 'PMl_deg'], summ)


VT = [0.0, 0.04, 0.08, 0.12, 0.16, 0.20, 0.24, 0.28, 0.30, 0.32, 0.34, 0.36, 0.40]


def sweep_vt_block(an_inner, vals=VT, name='swv'):
    return '%s sweep param=vtn values=[%s] {\n%s}\n' % (name, ' '.join(['%g' % v for v in vals]), an_inner)


def t_vtune():
    """Tuning law for v1 and v2: AC, noise and global loop gain against Vtune; impedance of
    the gyrator-C element seen from the input with OUT at AC ground."""
    reg_load()
    for nm in ('v1', 'v2'):
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        inner = (' dcop dc\n acx ac %s\n nz (outp 0) noise %s iprobe=Iin\n lgg stb start=1e6 stop=1e12 dec=20 probe=IPg\n'
                 % (AC, NZ))
        raw, devs = run_ac(kind, P, 'vt_' + nm, an=sweep_vt_block(inner))
        rows = []; curves = []
        for f in files(raw, '_acx.ac'):
            k = idx(f)[0]
            d = read_psf(f)
            fr = [x.real for x in d['freq']]
            m = ac_metrics(fr, d['outp'])
            n = read_psf(f.replace('_acx.ac', '_nz.noise'))
            fn = [x.real if isinstance(x, complex) else x for x in n['freq']]
            vin = [abs(x) for x in n['in']]
            s = read_psf(f.replace('_acx.ac', '_lgg.stb'))
            fs_ = [x.real if isinstance(x, complex) else x for x in s['freq']]
            sm = stb_metrics(fs_, s['loopGain'])
            op = read_psf(f.replace('_acx.ac', '_dcop.dc'))
            rt = 1.0 / max(abs(op.get('Mt:gds', [1e-9])[0]), 1e-12)
            f3 = m['f3'] if m['f3'] == m['f3'] else 1e10
            rows.append([VT[k], rt, m['zt'], m['pk'], m['f3'], abs(op['Vdd:p'][0]),
                         interp(fn, vin, 5e9), math.sqrt(integ(fn, [v * v for v in vin], 1e7, f3)),
                         sm['t0'], sm['fu'], sm['pm']])
            for i in range(len(fr)):
                curves.append([VT[k], fr[i], abs(d['outp'][i])])
        wcsv('vtune_' + nm, ['vtn', 'Rt_ohm', 'zt_dB', 'pk_dB', 'f3_Hz', 'idd_A', 'in5G', 'irms_bw', 'Tg0_dB', 'fug_Hz', 'PMg_deg'], rows)
        wcsv('vtune_curves_' + nm, ['vtn', 'f', 'zt_mag'], curves)
        cleanup('vt_' + nm)
        # gyrator-C element alone, seen from the input: OUT is an AC ground held at its DC
        # value, IN is held at its DC value through a 1 H choke, 1 A AC current is injected.
        vin0, vout0 = read_node(nm, 'inp', 0.27), read_node(nm, 'outp', 0.66)
        z = 'Vdd (vdd 0) vsource dc=vdd\nVt (vt 0) vsource dc=vtn\nVo (outp 0) vsource dc=%g\n' % vout0
        z += mos('Mf', 'vdd', 'g', 'inp', '0', 'n', 'p_wf', 100)
        z += mos('Mt', 'g', 'vt', 'outp', 'outp', 'p', 'p_wt', 100)
        z += 'Ca (g inp) capacitor c=p_ca\nLh (inp ih) inductor l=1\nVih (ih 0) vsource dc=%g\n' % vin0
        z += 'Itest (0 inp) isource dc=0 mag=1\n'
        raw = spectre('zai_' + nm, params(P) + z + 'save inp Mf:ids Mf:gm Mt:gds\n' +
                      sweep_vt_block(' dcz dc\n acz ac start=1e7 stop=1e11 dec=20\n', name='swz'))
        rows = []
        for f in files(raw, '_acz.ac'):
            k = idx(f)[0]
            d = read_psf(f)
            fr = [x.real for x in d['freq']]
            for i in range(len(fr)):
                zz = d['inp'][i]
                rows.append([VT[k], fr[i], abs(zz), math.degrees(math.atan2(zz.imag, zz.real)), zz.real,
                             zz.imag / (2 * math.pi * fr[i])])
        wcsv('zai_' + nm, ['vtn', 'f', 'zmag', 'zph_deg', 'R', 'Leq_H'], rows)
        cleanup('zai_' + nm)


def read_node(nm, node, default):
    fn = os.path.join(OUT, 'csv', 'nodes_%s.csv' % nm)
    if os.path.exists(fn):
        for l in open(fn).read().split('\n')[1:]:
            p = l.split(',')
            if len(p) == 2 and p[0] == node:
                return float(p[1])
    return default


def read_vin(nm):
    fn = os.path.join(OUT, 'csv', 'nodes_%s.csv' % nm)
    if os.path.exists(fn):
        for l in open(fn).read().split('\n')[1:]:
            p = l.split(',')
            if len(p) == 2 and p[0] == 'inp':
                return float(p[1])
    return 0.27


SECS = ['NN', 'SS', 'FF', 'SF', 'FS']
TEMPS = [-40, 35, 125]
VDDS = [0.9, 1.0, 1.1]


def t_pvt():
    """45 conditions (5 sections x 3 temperatures x 3 supplies) for all circuits.
    Proposed circuits are swept over Vtune to give both fixed-Vtune and trimmed results.
    Trim rule: the Vtune on the grid with the highest bandwidth and <= 1 dB peaking."""
    reg_load()
    rows = []
    for nm in ALL:
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        tun = kind == 'p'
        for sec in SECS:
            inner = ' dcop dc\n acx ac start=1e7 stop=1e11 dec=20\n'
            if tun:
                inner = sweep_vt_block(inner, vals=VT, name='swv')
            an = ('swt sweep param=temp values=[%s] {\nswd sweep param=vdd values=[%s] {\n%s}\n}\n'
                  % (' '.join(map(str, TEMPS)), ' '.join(map(str, VDDS)), inner))
            raw, devs = run_ac(kind, P, 'pvt_%s_%s' % (nm, sec), an=an, section=sec)
            for f in files(raw, '_acx.ac'):
                ix = idx(f)
                ti, di = ix[0], ix[1]
                vt = VT[ix[2]] if tun else float('nan')
                d = read_psf(f)
                fr = [x.real for x in d['freq']]
                m = ac_metrics(fr, d['outp'])
                op = read_psf(f.replace('_acx.ac', '_dcop.dc'))
                sat = all([int(round(op.get('%s:region' % dv, [2])[0])) == 2 for dv in devs if dv != 'Mt'])
                rows.append([nm, sec, TEMPS[ti], VDDS[di], vt, m['zt'], m['pk'], m['f3'], abs(op['Vdd:p'][0]), int(sat)])
            cleanup('pvt_%s_%s' % (nm, sec))
        wcsv('pvt_all', ['cir', 'sec', 'temp', 'vdd', 'vtn', 'zt_dB', 'pk_dB', 'f3_Hz', 'idd_A', 'allsat'], rows)


def t_mc():
    """Monte Carlo (GPDK090 mismatch statistics, section stat_mis), NN 35 C 1 V.
    Proposed circuits: Vtune swept inside each run -> fixed and trimmed statistics."""
    reg_load()
    N = int(os.environ.get('MCN', '200'))
    for nm in ('v1', 'v2', 'regain', 'pf_opt', 'pf_v1'):
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        tun = kind == 'p'
        inner = '  dcm dc\n  acm ac start=1e7 stop=1e11 dec=20\n'
        if tun:
            inner = sweep_vt_block(inner, vals=VT, name='swm')
        an = ('mc1 montecarlo numruns=%d seed=%d variations=mismatch donominal=no savefamilyplots=yes {\n%s}\n'
              % (N, 4321, inner))
        txt, devs = body(kind, P)
        hdr = params(P)
        inc = 'include "%s/gpdk090_mos.scs" section=stat_mis\n' % MODELS
        try:
            raw = spectre('mc_' + nm, hdr + txt + 'save outp Vdd:p Mf:ids\n' + an, extra_inc=inc)
        except RuntimeError:
            raw = spectre('mc_' + nm, hdr + txt + 'save outp Vdd:p Mf:ids\n' + an)
        rows = []
        for f in files(raw, '_acm.ac'):
            ix = idx(f)
            run = ix[0]
            vt = VT[ix[1]] if tun and len(ix) > 1 else float('nan')
            d = read_psf(f)
            fr = [x.real for x in d['freq']]
            m = ac_metrics(fr, d['outp'])
            op = read_psf(f.replace('_acm.ac', '_dcm.dc'))
            rows.append([nm, run, vt, m['zt'], m['pk'], m['f3'], abs(op.get('Vdd:p', [float('nan')])[0]),
                         abs(op.get('Mf:ids', [float('nan')])[0])])
        wcsv('mc_' + nm, ['cir', 'run', 'vtn', 'zt_dB', 'pk_dB', 'f3_Hz', 'idd_A', 'imf_A'], rows)
        cleanup('mc_' + nm)


CLS = [30e-15, 60e-15, 100e-15, 150e-15, 200e-15, 250e-15, 300e-15]
CPDS = [25e-15, 50e-15, 100e-15, 150e-15, 200e-15, 300e-15]


def t_loads():
    """Bandwidth vs load and photodiode capacitance (Vtune re-chosen for v1/v2), and the
    decomposition of the feedback network at CL = 30 fF:
    pf (plain follower), pfca (+Ca from OUT to IN), aint (Mt, no Ca), ai (full)."""
    reg_load()
    rows = []
    for nm in ALL:
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        tun = kind == 'p'
        for par, vals in (('cl', CLS), ('cpd', CPDS)):
            inner = ' dcop dc\n acx ac start=1e7 stop=1e11 dec=20\n'
            if tun:
                inner = sweep_vt_block(inner)
            an = 'swc sweep param=%s values=[%s] {\n%s}\n' % (par, ' '.join(['%g' % v for v in vals]), inner)
            raw, devs = run_ac(kind, P, 'ld_%s_%s' % (nm, par), an=an)
            for f in files(raw, '_acx.ac'):
                ix = idx(f)
                vt = VT[ix[1]] if tun else float('nan')
                d = read_psf(f)
                fr = [x.real for x in d['freq']]
                m = ac_metrics(fr, d['outp'])
                rows.append([nm, par, vals[ix[0]], vt, m['zt'], m['pk'], m['f3']])
            cleanup('ld_%s_%s' % (nm, par))
    wcsv('loads', ['cir', 'par', 'val', 'vtn', 'zt_dB', 'pk_dB', 'f3_Hz'], rows)
    # decomposition
    rows = []
    for nm in ('v1', 'v2'):
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        for mode in ('pf', 'pfca', 'aint', 'ai'):
            inner = ' dcop dc\n acx ac start=1e7 stop=1e11 dec=40\n'
            if mode in ('aint', 'ai'):
                inner = sweep_vt_block(inner)
            an = 'swc sweep param=cl values=[%s] {\n%s}\n' % (' '.join(['%g' % v for v in CLS]), inner)
            txt, devs = body('p', P, mode)
            raw = spectre('dec_%s_%s' % (nm, mode), params(P) + txt + saves([d for d in devs if (mode in ('ai', 'aint') or d != 'Mt')]) + an)
            for f in files(raw, '_acx.ac'):
                ix = idx(f)
                vt = VT[ix[1]] if len(ix) > 1 else float('nan')
                d = read_psf(f)
                fr = [x.real for x in d['freq']]
                m = ac_metrics(fr, d['outp'])
                zi = d['inp']
                rows.append([nm, mode, CLS[ix[0]], vt, m['zt'], m['pk'], m['f3'], abs(interp(fr, [abs(v) for v in zi], 5e9))])
            cleanup('dec_%s_%s' % (nm, mode))
    wcsv('decomp', ['cir', 'mode', 'cl', 'vtn', 'zt_dB', 'pk_dB', 'f3_Hz', 'zin5G'], rows)


def t_rc_sens():
    """Sensitivity of v1/v2 to resistor (+-15 %) and Ca (+-10 %) spread, NN 35 C."""
    reg_load()
    rows = []
    for nm in ('v1', 'v2'):
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        an = ('swr sweep param=rsc values=[0.85 1 1.15] {\n swcs sweep param=csc values=[0.9 1 1.1] {\n'
              '  dcop dc\n  acx ac start=1e7 stop=1e11 dec=20\n }\n}\n')
        raw, devs = run_ac(kind, P, 'rc_' + nm, an=an)
        for f in files(raw, '_acx.ac'):
            ix = idx(f)
            d = read_psf(f); fr = [x.real for x in d['freq']]
            m = ac_metrics(fr, d['outp'])
            op = read_psf(f.replace('_acx.ac', '_dcop.dc'))
            rows.append([nm, [0.85, 1, 1.15][ix[0]], [0.9, 1, 1.1][ix[1]], m['zt'], m['pk'], m['f3'], abs(op['Vdd:p'][0])])
        cleanup('rc_' + nm)
    wcsv('rc_sens', ['cir', 'rscale', 'cscale', 'zt_dB', 'pk_dB', 'f3_Hz', 'idd_A'], rows)


# ---------------- transient / eye ----------------
def prbs7(n):
    s = 0x7f; out = []
    for _ in range(n):
        b = ((s >> 6) ^ (s >> 5)) & 1
        s = ((s << 1) | b) & 0x7f
        out.append(b)
    return out


def pwl_file(path, bits, rate, i0, i1, tr=10e-12):
    ui = 1.0 / rate
    fh = open(path, 'w')
    t = 0.0
    prev = bits[0]
    fh.write('0 %g\n' % (i1 if prev else i0))
    for k, b in enumerate(bits):
        t = k * ui
        if k and b != prev:
            fh.write('%g %g\n%g %g\n' % (t, i1 if prev else i0, t + tr, i1 if b else i0))
        prev = b
    fh.write('%g %g\n' % (len(bits) * ui, i1 if prev else i0))
    fh.close()


def eye_metrics(t, v, bits, rate, skip=20):
    ui = 1.0 / rate
    nb = len(bits)
    # find latency by maximising the opening over delays 0..3 UI in steps of UI/32
    best = None
    NPH = 32
    for dl in range(0, 3 * NPH):
        delay = dl * ui / NPH
        ones = []; zeros = []
        for k in range(skip, nb - 2):
            tt = (k + 0.5) * ui + delay
            vv = interp_lin(t, v, tt)
            (ones if bits[k] else zeros).append(vv)
        if not ones or not zeros:
            continue
        op = min(ones) - max(zeros)
        if best is None or op > best[0]:
            best = (op, delay, sum(ones) / len(ones) - sum(zeros) / len(zeros))
    op, delay, amp = best
    # horizontal opening: phases (relative to the best one) where vertical opening > 0
    good = 0
    for ph in range(-NPH // 2, NPH // 2):
        ones = []; zeros = []
        for k in range(skip, nb - 2):
            tt = (k + 0.5) * ui + delay + ph * ui / NPH
            vv = interp_lin(t, v, tt)
            (ones if bits[k] else zeros).append(vv)
        if min(ones) - max(zeros) > 0:
            good += 1
    return dict(vopen=op, amp=amp, vpct=100 * op / amp if amp else float('nan'), hpct=100.0 * good / NPH, delay=delay)


def interp_lin(t, v, x):
    lo, hi = 0, len(t) - 1
    if x <= t[0]:
        return v[0]
    if x >= t[-1]:
        return v[-1]
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if t[mid] <= x:
            lo = mid
        else:
            hi = mid
    a = (x - t[lo]) / (t[hi] - t[lo])
    return v[lo] + a * (v[hi] - v[lo])


def t_eye():
    """PRBS-7 eye diagrams, 100 uA pk-pk.  Bipolar (+-50 uA, AC-coupled source) for every
    circuit at 10 and 12.5 Gb/s; unipolar 0..100 uA (50 uA average) for v1/v2 with and
    without the DC-cancellation loop."""
    reg_load()
    rows = []
    bits = prbs7(127 * 2 + 20)
    for rate in (10e9, 12.5e9):
        pw = os.path.join(WORK, 'prbs_%g.pwl' % rate)
        pwl_file(pw, bits, rate, -50e-6, 50e-6)
        pwu = os.path.join(WORK, 'prbsu_%g.pwl' % rate)
        pwl_file(pwu, bits, rate, 0, 100e-6)
        stop = len(bits) / rate
        jobs = [(nm, None, pw, 'bip') for nm in ALL if nm in CIR or True]
        jobs += [('v1', None, pwu, 'uni'), ('v2', None, pwu, 'uni'), ('v1', 'dcc', pwu, 'uni'), ('v2', 'dcc', pwu, 'uni')]
        for nm, dcc, src, pol in jobs:
            reg_load()
            if nm not in CIR:
                continue
            kind, P = CIR[nm]
            P = dict(P)
            P['_isrc'] = 'type=pwl file="%s"' % src
            D = dcc_params(nm) if dcc else None
            txt, devs = body(kind, P, None, D)
            txt = txt.replace('isource dc=idc mag=1 type=pwl', 'isource type=pwl')
            an = 'tr tran stop=%g maxstep=%g\n' % (stop, 1.0 / rate / 40)
            tag = 'eye_%s_%s_%s_%g' % (nm, dcc or 'nodcc', pol, rate / 1e9)
            try:
                raw = spectre(tag, params(P) + txt + 'save outp inp\n' + an)
            except RuntimeError:
                continue
            d = read_psf(os.path.join(raw, 'tr.tran'))
            t = [x.real if isinstance(x, complex) else x for x in d['time']]
            v = d['outp']
            m = eye_metrics(t, v, bits, rate)
            rows.append([nm, dcc or 'none', pol, rate, m['amp'], m['vopen'], m['vpct'], m['hpct']])
            # folded waveform for plotting: 2 UI windows
            ui = 1 / rate
            w = []
            k0 = 20
            NS = 48
            for k in range(k0, len(bits) - 3):
                for j in range(NS + 1):
                    tt = k * ui + m['delay'] + j * 2 * ui / NS
                    w.append([k, j * 2.0 / NS, interp_lin(t, v, tt)])
            wcsv('eyewave_' + tag.replace('eye_', '').replace('.', 'p'), ['bit', 'ui', 'v'], w)
            cleanup(tag)
    wcsv('eye', ['cir', 'dcc', 'pol', 'rate', 'amp_V', 'vopen_V', 'vpct', 'hpct'], rows)


# ---------------- DC cancellation ----------------
DCC_CACHE = {}


def dcc_params(nm):
    """Choose Mq so that the held follower current I_th is 8 % above the dark I(Mf)."""
    if nm in DCC_CACHE:
        return DCC_CACHE[nm]
    fn = os.path.join(OUT, 'csv', 'op_%s.csv' % nm)
    imf = 100e-6
    if os.path.exists(fn):
        for l in open(fn).read().split('\n')[1:]:
            p = l.split(',')
            if p and p[0] == 'Mf':
                imf = abs(float(p[1]))
    kind, P = CIR[nm]
    # Iq = iref*Wq/2 ; I(Mns) = Iq*5.7/2 = I_th/2  ->  Wq = I_th/(2.85*iref)
    ith = 1.08 * imf
    wq = ith / (2.85 * P['iref'])
    D = dict(wq=wq)
    # one correction step with the simulated held current
    try:
        raw, devs = run_ac(kind, P, 'dccal_' + nm, dcc=D, an='dcop dc\n')
        op = read_psf(os.path.join(raw, 'dcop.dc'))
        ins = abs(op['Mns:ids'][0])
        D['wq'] = wq * (ith / 2) / ins
        cleanup('dccal_' + nm)
    except Exception:
        log('dcc calibration failed', nm)
    D['ith'] = ith
    DCC_CACHE[nm] = D
    log('DCC', nm, 'imf %.3g ith %.3g wq %.3g' % (imf, ith, D['wq']))
    return D


IDCS = [0, 5e-6, 10e-6, 25e-6, 50e-6, 75e-6, 100e-6, 150e-6, 200e-6, 300e-6, 400e-6, 500e-6]


def t_dcc():
    """Average photocurrent tolerance with and without the DC-cancellation loop; DCC loop
    gain; photocurrent step; noise penalty; DCC under the 5 process corners."""
    reg_load()
    rows = []; curves = []; stb_rows = []; nzr = []
    for nm in ('v1', 'v2'):
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        D = dcc_params(nm)
        for use in (None, 'dcc'):
            for sec in (SECS if use else ['NN']):
                inner = (' dcop dc\n acx ac start=1e3 stop=1e11 dec=20\n')
                if use and sec == 'NN':
                    inner += ' lgd stb start=1e2 stop=1e10 dec=20 probe=IPd\n'
                if sec == 'NN':
                    inner += ' nz (outp 0) noise start=1e9 stop=1e10 dec=5 iprobe=Iin\n'
                an = 'swi sweep param=idc values=[%s] {\n%s}\n' % (' '.join(['%g' % v for v in IDCS]), inner)
                tag = 'dcc_%s_%s_%s' % (nm, use or 'no', sec)
                raw, devs = run_ac(kind, P, tag, dcc=D if use else None, an=an, section=sec)
                for f in files(raw, '_acx.ac'):
                    k = idx(f)[0]
                    d = read_psf(f); fr = [x.real for x in d['freq']]
                    m = ac_metrics(fr, d['outp'])
                    op = read_psf(f.replace('_acx.ac', '_dcop.dc'))
                    imf = abs(op.get('Mf:ids', [float('nan')])[0])
                    idc_ = abs(op.get('Mdc:ids', [0])[0]) if use else 0
                    rows.append([nm, use or 'none', sec, IDCS[k], m['zt'], m['pk'], m['f3'], m['flo'], imf, idc_, abs(op['Vdd:p'][0])])
                    if sec == 'NN' and IDCS[k] in (0, 100e-6, 300e-6, 500e-6):
                        for i in range(0, len(fr)):
                            curves.append([nm, use or 'none', IDCS[k], fr[i], abs(d['outp'][i])])
                    if sec == 'NN':
                        try:
                            n = read_psf(f.replace('_acx.ac', '_nz.noise'))
                            fn = [x.real if isinstance(x, complex) else x for x in n['freq']]
                            nzr.append([nm, use or 'none', IDCS[k], interp(fn, [abs(x) for x in n['in']], 5e9)])
                        except Exception:
                            pass
                    if use and sec == 'NN':
                        try:
                            s = read_psf(f.replace('_acx.ac', '_lgd.stb'))
                            fs_ = [x.real if isinstance(x, complex) else x for x in s['freq']]
                            sm = stb_metrics(fs_, s['loopGain'])
                            stb_rows.append([nm, IDCS[k], sm['t0'], sm['fu'], sm['pm']])
                        except Exception:
                            log('dcc stb parse fail', traceback.format_exc().split('\n')[-2])
                cleanup(tag)
    wcsv('dcc_sweep', ['cir', 'dcc', 'sec', 'idc', 'zt_dB', 'pk_dB', 'f3_Hz', 'flo_Hz', 'imf_A', 'imdc_A', 'idd_A'], rows)
    wcsv('dcc_curves', ['cir', 'dcc', 'idc', 'f', 'zt_mag'], curves)
    wcsv('dcc_stb', ['cir', 'idc', 'T0_dB', 'fu_Hz', 'PM_deg'], stb_rows)
    wcsv('dcc_noise', ['cir', 'dcc', 'idc', 'in5G'], nzr)
    # photocurrent step 0 -> 300 uA at 1 us, with the loop
    rows = []
    for nm in ('v1', 'v2'):
        if nm not in CIR:
            continue
        kind, P = CIR[nm]
        P = dict(P)
        P['_isrc'] = 'type=pwl wave=[0 0 1u 0 1.001u 300u 20u 300u]'
        txt, devs = body(kind, P, None, dcc_params(nm))
        txt = txt.replace('isource dc=idc mag=1 type=pwl', 'isource type=pwl')
        raw = spectre('step_' + nm, params(P) + txt + 'save outp inp vx Mf:ids\n' + 'tr tran stop=20u maxstep=5n\n')
        d = read_psf(os.path.join(raw, 'tr.tran'))
        t = [x.real if isinstance(x, complex) else x for x in d['time']]
        last = -1
        for i in range(len(t)):
            if t[i] - last >= 20e-9 or i == len(t) - 1:
                rows.append([nm, t[i], d['outp'][i], d['inp'][i], d.get('Mf:ids', [0] * len(t))[i] if 'Mf:ids' in d else float('nan')])
                last = t[i]
        cleanup('step_' + nm)
    wcsv('dcc_step', ['cir', 't', 'vout', 'vin', 'imf'], rows)


TASKS = [('regain', t_opt_regain), ('pf', t_opt_pf), ('v2', t_opt_v2), ('nominal', t_nominal), ('vtune', t_vtune),
         ('pvt', t_pvt), ('loads', t_loads), ('rc', t_rc_sens), ('mc', t_mc), ('dcc', t_dcc), ('eye', t_eye)]


def selftest():
    """Small runs that check model names, PSF parsing, paramset, stb, noise, MC, tran."""
    reg_load()
    m = evaluate('p', [dict(V1), dict(V1, vtn=0.30)], 'st_pset')
    log('ST paramset', [(round(x['zt'], 2), round(x['pk'], 2), '%.3g' % x['f3'], '%.3g' % x['idd'], x['sat']) for x in m])
    m = evaluate('b', [dict(B0)], 'st_base')
    log('ST base', [(round(x['zt'], 2), round(x['pk'], 2), '%.3g' % x['f3'], '%.3g' % x['idd'], x['sat']) for x in m])
    an = ('dcop dc\nacx ac %s\nnz (outp 0) noise %s iprobe=Iin\nlgg stb start=1e6 stop=1e12 dec=20 probe=IPg\n' % (AC, NZ))
    raw, devs = run_ac('p', V1, 'st_nom', an=an, keep=True)
    log('ST files', sorted(os.listdir(raw)))
    op = read_psf(os.path.join(raw, 'dcop.dc'))
    log('ST op keys', len(op), sorted(op.keys())[:12], 'Vdd:p', op.get('Vdd:p'), 'M1:region', op.get('M1:region'))
    n = read_psf(os.path.join(raw, 'nz.noise')); log('ST noise keys', sorted(n.keys())[:8])
    s = read_psf(os.path.join(raw, 'lgg.stb')); log('ST stb keys', sorted(s.keys())[:8])
    try:
        fs_ = [x.real if isinstance(x, complex) else x for x in s['freq']]
        log('ST stb', stb_metrics(fs_, s['loopGain']))
        log('ST margin', read_psf(os.path.join(raw, 'lgg.margin.stb')))
    except Exception:
        log('ST stb fail', traceback.format_exc())
    an = ('mc1 montecarlo numruns=3 seed=1 variations=mismatch donominal=no savefamilyplots=yes {\n'
          + sweep_vt_block('  dcm dc\n  acm ac start=1e7 stop=1e11 dec=10\n', vals=[0.2, 0.3], name='swm') + '}\n')
    inc = 'include "%s/gpdk090_mos.scs" section=stat_mis\n' % MODELS
    for tag, ei in (('st_mc_inc', inc), ('st_mc', '')):
        try:
            raw = spectre(tag, params(V1) + proposed(V1) + 'save outp Vdd:p Mf:ids\n' + an, extra_inc=ei, keep=True)
            fl = files(raw, '_acm.ac')
            log('ST mc', tag, [os.path.basename(x) for x in fl])
            log('ST mc f3', [ac_metrics([x.real for x in read_psf(f)['freq']], read_psf(f)['outp'])['f3'] for f in fl])
        except Exception:
            log('ST mc fail', tag, traceback.format_exc().split('\n')[-2])
    P = dict(V1); P['_isrc'] = 'type=pwl wave=[0 0 1n 0 1.01n 50u 3n 50u]'
    txt = proposed(P).replace('isource dc=idc mag=1 type=pwl', 'isource type=pwl')
    raw = spectre('st_tran', params(P) + txt + 'save outp inp\ntr tran stop=3n maxstep=5p\n', keep=True)
    d = read_psf(os.path.join(raw, 'tr.tran'))
    log('ST tran keys', sorted(d.keys()), len(d.get('time', [])), d['outp'][0], d['outp'][-1])


if __name__ == '__main__':
    args = sys.argv[1:] or ['all']
    if args == ['selftest']:
        selftest()
        sys.exit(0)
    names = [t[0] for t in TASKS] if args == ['all'] else args
    for n in names:
        fn = dict(TASKS)[n]
        log('==== task', n)
        t0 = time.time()
        try:
            fn()
        except Exception:
            log('TASK FAILED', n, traceback.format_exc())
        log('==== done', n, '%.0fs' % (time.time() - t0))
    log('campaign finished, runs:', RUNS[0])
