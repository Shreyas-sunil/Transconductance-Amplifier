"""Run every simulation behind the paper and store the raw results in results/data.

Usage:  python3 run_all.py [step ...]     (no arguments = all steps)
"""
import os, sys, json, re
import numpy as np
from multiprocessing import Pool
import sim, circuits as C, loopgain as lg

DATA = os.path.join(C.ROOT, 'results', 'data')
os.makedirs(DATA, exist_ok=True)
VT_NOM = C.PROP_P['vtune']
VT_GRID = np.round(np.arange(0.0, 0.4401, 0.02), 3)
SCAL = ('z0db', 'z0', 'pk', 'fpk', 'f3', 'pwr', 'in1', 'in5', 'in10', 'in15', 'irms', 'irms_tot', 'in_avg')


def J(name, obj):
    json.dump(obj, open(os.path.join(DATA, name), 'w'), indent=1, default=float)


def scal(d):
    o = {k: float(d[k]) for k in SCAL if k in d}
    o.update({k: float(v) for k, v in d.items() if k.startswith('v(') or k.startswith('@') or k.startswith('i(')})
    return o


def curves(name, d, noise=True):
    cols = [d['f'], d['zdb'], np.degrees(d['ph']), d['gd'] * 1e12, d['zin_db']]
    hdr = 'freq_Hz,Zt_dBohm,phase_deg,group_delay_ps,Zin_dBohm'
    if noise:
        cols += [d['inoise'] * 1e12]; hdr += ',in_noise_pA_rtHz'
    np.savetxt(os.path.join(DATA, name), np.column_stack(cols), delimiter=',', header=hdr, comments='')


# ------------------------------------------------------------------ nominal
def step_nominal():
    out = {}
    b = sim.acnoise('base'); curves('ac_baseline.csv', b); out['baseline'] = scal(b)
    b2 = sim.acnoise('base', {'vg3b': -1.0}); curves('ac_baseline_vg_m1V.csv', b2); out['baseline_vg_m1V'] = scal(b2)
    p = sim.acnoise('prop'); curves('ac_proposed.csv', p); out['proposed'] = scal(p)
    # peak-referenced numbers for the baseline (its response peaks strongly)
    for k, d in (('baseline', b), ('baseline_vg_m1V', b2)):
        f, z = d['f'], d['zdb']
        out[k]['f_1dB_flat'] = float(f[np.where(abs(z - d['z0db']) > 1)[0][0]])   # +-1 dB flatness limit
        ipk = z.argmax()
        idx = np.where((z < z.max() - 3) & (f > f[ipk]))[0]
        out[k]['f3_from_peak'] = float(f[idx[0]]) if len(idx) else float('nan')
    out['proposed']['f_1dB_flat'] = float(p['f'][np.where(abs(p['zdb'] - p['z0db']) > 1)[0][0]])
    J('nominal.json', out)
    print(json.dumps({k: {q: round(v[q], 4) for q in ('z0db', 'z0', 'pk', 'f3', 'pwr', 'in1', 'in5', 'in10', 'irms')} for k, v in out.items()}, indent=1))


# ------------------------------------------------------------------ Vtune sweep
def step_vtune():
    rows = []
    for vt in VT_GRID:
        d = sim.acnoise('prop', {'vtune': vt})
        r = scal(d); r['vtune'] = float(vt); r['rt'] = 1 / d['@mt[gds]']
        rows.append(r)
        if round(vt * 100) % 4 == 0 and vt <= 0.401:
            curves(f'ac_proposed_vt{int(round(vt*1000)):03d}.csv', d)
    J('vtune_sweep.json', rows)
    for r in rows:
        print('vt=%.2f Rt=%6.0f z0=%.2f pk=%.2f f3=%.2fG irms=%.2fuA' % (r['vtune'], r['rt'], r['z0db'], r['pk'], r['f3'] / 1e9, r['irms'] * 1e6))


# ------------------------------------------------------------------ active inductor alone
def step_ai():
    """One-port impedance of the active inductor seen from the TIA input node, with the
    VOUT side held at its DC value (AC ground), plus transadmittance from VOUT."""
    nom = json.load(open(os.path.join(DATA, 'nominal.json')))['proposed']
    vout, i_f = nom['v(out)'], nom['@mf[id]']
    wf, lf_ = C.PROP_SZ['Mf']; wt, lt = C.PROP_SZ['Mt']
    res = {}
    for vt in [0.0, 0.12, 0.2, 0.28, 0.32, 0.36, 0.4]:
        t = os.path.join(sim.TMP, f'ai{int(vt*100)}')
        elems = [('V', 'Vdd', 'vdd', '0', '1', None), ('V', 'Vo', 'o', '0', f'{vout}', None),
                 ('V', 'Vtune', 'vt', '0', f'{vt}', None),
                 ('M', 'Mf', 'vdd', 'g', 's', '0', 'n', wf, lf_),
                 ('M', 'Mt', 'g', 'vt', 'o', 'o', 'p', wt, lt),
                 ('C', 'Ca', 'g', 's', C.PROP_P['ca']),
                 ('I', 'Ib', 's', '0', f'{i_f}', None), ('I', 'Itest', '0', 's', '0', '1')]
        net = '\n'.join(['* active inductor test bench', f'.include {C.MODEL}', '.temp 35'] + C.spice_lines(elems) +
                        ['.control', 'set noaskquit', 'set wr_singlescale', 'op', 'print v(s) @mf[gm] @mt[gds] @mf[gds] @mf[gmbs]',
                         'ac dec 40 10meg 200g', f'wrdata {t}.txt v(s)', '.endc', '.end']) + '\n'
        o = sim.vals(sim.run(net))
        a = np.loadtxt(t + '.txt'); f = a[:, 0]; Z = a[:, 1] + 1j * a[:, 2]
        w = 2 * np.pi * f
        L = Z.imag / w; Q = Z.imag / Z.real
        k = np.where((Z.imag[:-1] > 0) & (Z.imag[1:] <= 0))[0]
        srf = float(f[k[0]]) if len(k) else float('nan')
        res[f'{vt:.2f}'] = dict(gm=o['@mf[gm]'], rt=1 / o['@mt[gds]'], vs=o['v(s)'], rs_lf=float(Z.real[0]),
                                L_1G=float(np.interp(1e9, f, L)), L_5G=float(np.interp(5e9, f, L)),
                                Qmax=float(Q.max()), fQmax=float(f[Q.argmax()]), srf=srf)
        np.savetxt(os.path.join(DATA, f'ai_z_vt{int(round(vt*1000)):03d}.csv'),
                   np.column_stack([f, abs(Z), np.degrees(np.angle(Z)), Z.real, L * 1e9, Q]), delimiter=',',
                   header='freq_Hz,Zmag_ohm,phase_deg,Re_ohm,Leq_nH,Q', comments='')
    J('active_inductor.json', res)
    for k, v in res.items():
        print(k, {a: (round(b, 3) if abs(b) < 1e3 else float('%.3g' % b)) for a, b in v.items()}, 'L(nH)=%.2f' % (v['L_1G'] * 1e9))


# ------------------------------------------------------------------ noise breakdown
def step_noise():
    out = {}
    for circ in ('base', 'prop'):
        ctl = 'op\nnoise v(out) iin dec 20 10meg 100g 1\nsetplot noise1\ndisplay'
        o = sim.run(sim.build(circ, control=ctl))
        names = sorted(set(re.findall(r'^\s*(onoise\.[a-z0-9]+|onoise_r[a-z0-9]+)\s*:', o, re.M)))
        t = os.path.join(sim.TMP, f'nb_{circ}.txt')
        ctl2 = ('op\nnoise v(out) iin dec 20 10meg 100g 1\nsetplot noise1\n'
                f'wrdata {t} onoise_spectrum inoise_spectrum ' + ' '.join(names))
        sim.run(sim.build(circ, control=ctl2))
        a = np.loadtxt(t); f = a[:, 0]; tot = a[:, 1]; inn = a[:, 2]
        nm = lambda n: n.replace('onoise.', '').replace('onoise_', '')
        hdr = 'freq_Hz,in_total_pA_rtHz,' + ','.join(nm(n) for n in names)
        gain = tot / inn                     # |Zt|
        cols = [f, inn * 1e12] + [a[:, 3 + i] / gain * 1e12 for i in range(len(names))]
        np.savetxt(os.path.join(DATA, f'noise_breakdown_{circ}.csv'), np.column_stack(cols), delimiter=',', header=hdr, comments='')
        share = {nm(n): float(np.interp(5e9, f, (a[:, 3 + i] / tot) ** 2)) for i, n in enumerate(names)}
        out[circ] = dict(share_at_5GHz=share, in5=float(np.interp(5e9, f, inn)) * 1e12)
        print(circ, {k: round(100 * v, 1) for k, v in sorted(share.items(), key=lambda kv: -kv[1])})
    J('noise_breakdown.json', out)


# ------------------------------------------------------------------ loop gains
def crossings(f, T):
    mag = 20 * np.log10(abs(T)); ph = np.degrees(np.unwrap(np.angle(T)))
    res = []
    for k in np.where(np.sign(mag[:-1]) != np.sign(mag[1:]))[0]:
        fu = 10 ** np.interp(0, sorted([mag[k], mag[k + 1]]), np.array([np.log10(f[k]), np.log10(f[k + 1])])[np.argsort([mag[k], mag[k + 1]])])
        p = np.interp(np.log10(fu), np.log10(f), ph)
        pm = ((p + 180 + 180) % 360) - 180      # distance of the phase from -180 deg
        res.append((float(fu), float(pm)))
    return mag, ph, res


def step_loop():
    out = {'global': [], 'local': []}
    for vt in [0.0, 0.12, 0.2, 0.28, 0.36]:
        for which in ('global', 'local'):
            f, T = lg.tia_loop({'vtune': vt}, which=which)
            mag, ph, cr = crossings(f, T)
            out[which].append(dict(vtune=vt, t0_db=float(mag[0]), tmax_db=float(mag.max()), crossings=cr,
                                   pm_min=float(min(abs(c[1]) for c in cr)) if cr else None))
            if abs(vt - VT_NOM) < 1e-6:
                np.savetxt(os.path.join(DATA, f'loopgain_{which}.csv'), np.column_stack([f, mag, ph]), delimiter=',',
                           header='freq_Hz,T_dB,phase_deg', comments='')
    out['local_cpd'] = []
    for cpd in ['25f', '50f', '100f', '150f', '200f']:
        f, T = lg.tia_loop({'cpd': cpd}, which='local'); mag, ph, cr = crossings(f, T)
        out['local_cpd'].append(dict(cpd=cpd, crossings=cr, pm_min=float(min(abs(c[1]) for c in cr))))
    J('loopgain.json', out)
    for k, v in out.items():
        for r in v:
            print(k, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in r.items() if a != 'crossings'}, [(round(a / 1e9, 2), round(b, 1)) for a, b in r['crossings']])


# ------------------------------------------------------------------ trimming helper
def trim(target_f3, pk_max=0.5, **kw):
    """Scan Vtune and pick the setting (peaking <= pk_max) whose -3 dB bandwidth is closest to target."""
    P0 = dict(kw.pop('P', {}) or {})
    best = None; rows = []
    for vt in VT_GRID:
        P = dict(P0); P['vtune'] = float(vt)
        d = sim.acnoise('prop', P, noise=False, ppd=30, **kw)
        rows.append((float(vt), d['z0db'], d['pk'], d['f3']))
        if d['pk'] <= pk_max and np.isfinite(d['f3']):
            c = abs(d['f3'] - target_f3)
            if best is None or c < best[0]:
                best = (c, float(vt), d['z0db'], d['pk'], d['f3'])
    return best, rows


def _pvt_case(args):
    name, P, kw, target = args
    d0 = sim.acnoise('prop', P, noise=True, **kw)
    best, _ = trim(target, P=P, **kw)
    P2 = dict(P); P2['vtune'] = best[1]
    d1 = sim.acnoise('prop', P2, noise=True, **kw)
    return dict(case=name, nominal=scal(d0), vt_trim=best[1], trimmed=scal(d1))


def step_pvt():
    target = json.load(open(os.path.join(DATA, 'nominal.json')))['proposed']['f3']
    cases = [(c, {}, dict(corner=c)) for c in sim.CORNERS]
    cases += [('VDD 0.9 V', {'vdd': 0.9}, {}), ('VDD 1.1 V', {'vdd': 1.1}, {}),
              ('T = -40 C', {'temp': -40}, {}), ('T = 85 C', {'temp': 85}, {}),
              ('R +15 %', {}, dict(rscale=1.15)), ('R -15 %', {}, dict(rscale=0.85)),
              ('Ca +10 %', {}, dict(cscale=1.10)), ('Ca -10 %', {}, dict(cscale=0.90)),
              ('SS, 0.9 V, 85 C', {'vdd': 0.9, 'temp': 85}, dict(corner='SS')),
              ('FF, 1.1 V, -40 C', {'vdd': 1.1, 'temp': -40}, dict(corner='FF'))]
    with Pool(2) as pool:
        rows = pool.map(_pvt_case, [(n, P, kw, target) for n, P, kw in cases])
    J('pvt.json', dict(target_f3=target, rows=rows))
    for r in rows:
        n, t = r['nominal'], r['trimmed']
        print('%-18s nominal: z0=%.2f pk=%.2f f3=%.2fG P=%.2fmW | trim vt=%.2f: z0=%.2f pk=%.2f f3=%.2fG in5=%.1f' % (
            r['case'], n['z0db'], n['pk'], n['f3'] / 1e9, n['pwr'] * 1e3, r['vt_trim'], t['z0db'], t['pk'], t['f3'] / 1e9, t['in5']))


# ------------------------------------------------------------------ Monte Carlo
AVT, ABETA = 3.5e-9, 0.01e-6      # Pelgrom coefficients: 3.5 mV*um, 1 %*um
SIG_VTH_G, SIG_MU_G, SIG_R, SIG_C = 0.010, 0.02, 0.05, 0.03   # global 1-sigma


def _mc_case(seed):
    rng = np.random.default_rng(1000 + seed)
    elems = C.proposed()
    mm = {}
    for e in elems:
        if e[0] == 'M':
            w, l = e[7] * 1e-6, e[8] * 1e-9
            s = 1 / np.sqrt(w * l)
            mm[e[1]] = (rng.normal(0, AVT * s / np.sqrt(2)), rng.normal(0, ABETA * s / np.sqrt(2)))
    corner = (rng.normal(0, SIG_VTH_G), rng.normal(0, SIG_VTH_G), 1 + rng.normal(0, SIG_MU_G), 1 + rng.normal(0, SIG_MU_G))
    kw = dict(corner=corner, mismatch=mm, rscale=1 + rng.normal(0, SIG_R), cscale=1 + rng.normal(0, SIG_C))
    d0 = sim.acnoise('prop', {}, noise=False, ppd=30, **kw)
    best, _ = trim(_mc_case.target, **kw)
    return dict(seed=seed, z0db=d0['z0db'], pk=d0['pk'], f3=d0['f3'], pwr=d0['pwr'], vout=d0['v(out)'], vin=d0['v(in)'],
                vt_trim=best[1], z0db_t=best[2], pk_t=best[3], f3_t=best[4])


def step_mc(n=200):
    _mc_case.target = json.load(open(os.path.join(DATA, 'nominal.json')))['proposed']['f3']
    with Pool(2) as pool:
        rows = pool.map(_mc_case, range(n))
    J('montecarlo.json', dict(n=n, avt=AVT, abeta=ABETA, sig_vth_global=SIG_VTH_G, sig_mu_global=SIG_MU_G, sig_r=SIG_R,
                              sig_c=SIG_C, target_f3=_mc_case.target, rows=rows))
    a = lambda k: np.array([r[k] for r in rows], float)
    for k in ('z0db', 'pk', 'f3', 'pwr', 'f3_t', 'pk_t', 'vt_trim'):
        v = a(k); print('%-8s mean=%.4g std=%.3g min=%.4g max=%.4g' % (k, np.nanmean(v), np.nanstd(v), np.nanmin(v), np.nanmax(v)))


# ------------------------------------------------------------------ C_PD and input-current sensitivity
def step_sens():
    target = json.load(open(os.path.join(DATA, 'nominal.json')))['proposed']['f3']
    out = {'cpd': [], 'idc': []}
    for c in [25, 50, 75, 100, 150, 200]:
        P = {'cpd': f'{c}f'}
        d = sim.acnoise('prop', P)
        best, _ = trim(target, pk_max=1.0, P=P)
        d2 = sim.acnoise('prop', dict(P, vtune=best[1]))
        b = sim.acnoise('base', P)
        out['cpd'].append(dict(cpd_fF=c, nominal=scal(d), vt_trim=best[1], trimmed=scal(d2), baseline=scal(b)))
        print('Cpd=%3d fF: prop f3=%.2fG pk=%.2f | trim vt=%.2f f3=%.2fG pk=%.2f | base pk=%.1f dB at %.1fG' % (
            c, d['f3'] / 1e9, d['pk'], best[1], d2['f3'] / 1e9, d2['pk'], b['pk'], b['fpk'] / 1e9))
    for idc in [0, 25, 50, 100, 150, 200, 300, 400, 500, 700, 1000]:
        elems = None
        def rep(el, idc=idc):
            return [(e[:4] + (f'{idc}u', e[5])) if e[1] == 'Iin' else e for e in el]
        d = sim.acnoise('prop', noise=False, replace=rep)
        b = sim.acnoise('base', noise=False, replace=rep)
        out['idc'].append(dict(idc_uA=idc, prop=scal(d), base=scal(b)))
        print('Idc=%4d uA: prop z0=%.2f f3=%.2fG vout=%.3f | base z0=%.2f' % (idc, d['z0db'], d['f3'] / 1e9, d['v(out)'], b['z0db']))
    J('sensitivity.json', out)


STEPS = dict(nominal=step_nominal, vtune=step_vtune, ai=step_ai, noise=step_noise, loop=step_loop,
             pvt=step_pvt, mc=step_mc, sens=step_sens)
# ------------------------------------------------------------------ resistive-feedback reference and load study
def _resistive(el):
    return [('R', 'Rshort', 'g', 'out', '1') if e[1] == 'Mt' else e for e in el]


def step_load():
    rows = []
    for cl in [30, 60, 100, 150, 200, 250]:
        P = {'cout': f'{cl}f'}
        r = sim.acnoise('prop', dict(P, ca='0f'), replace=_resistive)       # plain follower feedback, no RC network
        d = sim.acnoise('prop', P)                                          # AI network at nominal Vtune
        best = None
        for vt in VT_GRID:
            a = sim.acnoise('prop', dict(P, vtune=float(vt)), noise=False, ppd=30)
            if a['pk'] <= 1.0 and np.isfinite(a['f3']) and (best is None or a['f3'] > best[1]):
                best = (float(vt), a['f3'], a['pk'])
        rows.append(dict(cl_fF=cl, resistive=scal(r), ai_nominal=scal(d), vt_best=best[0], f3_best=best[1], pk_best=best[2]))
        print('CL=%3d fF: resistive f3=%.2fG pk=%.2f | AI nominal f3=%.2fG pk=%.2f | AI tuned vt=%.2f f3=%.2fG pk=%.2f (x%.2f)' % (
            cl, r['f3'] / 1e9, r['pk'], d['f3'] / 1e9, d['pk'], best[0], best[1] / 1e9, best[2], best[1] / r['f3']))
        if cl in (30, 250):
            curves(f'ac_resistive_cl{cl}.csv', r); ab = sim.acnoise('prop', dict(P, vtune=best[0])); curves(f'ac_ai_tuned_cl{cl}.csv', ab)
    J('load_study.json', rows)


# ------------------------------------------------------------------ small-signal model
def ss_model(p, caps, f):
    """4-node small-signal model (in, n, out, g). p: conductances, caps: [Cin, Cn, Co, Cg, Cm, Cgg]."""
    Cin, Cn, Co, Cg, Cm, Cgg = caps
    Z = np.zeros(len(f), complex)
    g1 = p['gm1'] + p['gmb1']; gf = p['gmf'] + p['gmbf'] + p['gdsf']
    for i, w in enumerate(2j * np.pi * f):
        Y = np.array([
            [w * Cin + p['gds2'] + g1 + p['gds1'] + gf + w * Cg, p['gm2'] - p['gds1'], 0, -p['gmf'] - w * Cg],
            [-(g1 + p['gds1']), p['gn'] + p['gds1'] + w * Cn + w * Cm, -w * Cm, 0],
            [0, p['gm3'] - w * Cm, p['go'] + w * Co + w * Cm + p['gt'], -p['gt']],
            [-w * Cg, 0, -p['gt'], p['gt'] + w * Cg + w * Cgg]], complex)
        Z[i] = np.linalg.solve(Y, np.array([1, 0, 0, 0], complex))[2]
    return Z


def op_params(d, rn):
    return dict(gm1=d['@m1[gm]'], gmb1=d['@m1[gmbs]'], gds1=d['@m1[gds]'], gm2=d['@m2[gm]'], gds2=d['@m2[gds]'],
                gm3=d['@m3[gm]'], go=d['@m3[gds]'] + d['@m3b[gds]'], gmf=d['@mf[gm]'], gmbf=d['@mf[gmbs]'],
                gdsf=d['@mf[gds]'], gt=d['@mt[gds]'], gn=1 / rn)


def step_model():
    from scipy.optimize import least_squares
    rn = 5e3
    d = sim.acnoise('prop', noise=False)
    p = op_params(d, rn)
    fitset = []
    for vt in (0.0, 0.28):                       # fit on two tuning settings, validate on the others
        dv = sim.acnoise('prop', {'vtune': vt}, noise=False)
        m = dv['f'] <= 40e9
        fitset.append((op_params(dv, rn), dv['f'][m], 10 ** (dv['zdb'][m] / 20) * np.exp(1j * dv['ph'][m])))
    def res(x):
        r_ = []
        for pv, f, zs in fitset:
            zm = ss_model(pv, x * 1e-15, f)
            r_ += [20 * np.log10(abs(zm) / abs(zs)), 0.1 * np.degrees(np.angle(zm / zs))]
        return np.concatenate(r_)
    fit = least_squares(res, [60, 25, 60, 34, 5, 5], bounds=([0, 0, 0, 30, 0, 0], [300, 300, 300, 50, 50, 50]))
    caps = fit.x * 1e-15
    out = dict(params=p, caps_fF=dict(zip(['Cin', 'Cn', 'Co', 'Cg', 'Cm', 'Cgg'], fit.x)), validation=[])
    # closed-form low-frequency gain
    A1 = (p['gm1'] + p['gmb1'] + p['gds1']) / (p['gn'] + p['gds1'])
    gf = p['gmf'] + p['gmbf'] + p['gdsf']
    z0_exact = (p['gm3'] / p['go']) * A1 / (p['gm2'] * A1 + p['gm1'] + p['gmb1'] + p['gds2'] - p['gds1'] * (A1 - 1) + gf + p['gmf'] * (p['gm3'] / p['go']) * A1)
    mr = p['gm3'] / p['gm2']; ro = 1 / p['go']
    out['z0_sim'] = d['z0']; out['z0_exact'] = z0_exact; out['z0_approx'] = mr * ro / (1 + mr * p['gmf'] * ro)
    out['T0_approx'] = mr * p['gmf'] * ro; out['A1'] = A1
    tau = caps[3] / p['gt']
    out['fz_GHz'] = 1 / (2 * np.pi * tau) / 1e9; out['fp_fb_GHz'] = p['gmf'] / (2 * np.pi * caps[3]) / 1e9
    for vt in [0.0, 0.12, 0.2, 0.28, 0.36]:
        dv = sim.acnoise('prop', {'vtune': vt}, noise=False)
        pv = op_params(dv, rn)
        zm = ss_model(pv, caps, dv['f'])
        err = 20 * np.log10(abs(zm)) - dv['zdb']
        mm = dv['f'] <= 30e9
        out['validation'].append(dict(vtune=vt, rms_db=float(np.sqrt(np.mean(err[mm] ** 2))), max_db=float(abs(err[mm]).max()),
                                      f3_sim=dv['f3'], f3_model=float(sim.f3db(dv['f'], 20 * np.log10(abs(zm))))))
        np.savetxt(os.path.join(DATA, f'model_vt{int(round(vt*1000)):03d}.csv'), np.column_stack([dv['f'], dv['zdb'], 20 * np.log10(abs(zm))]),
                   delimiter=',', header='freq_Hz,Zt_sim_dBohm,Zt_model_dBohm', comments='')
    J('model.json', out)
    print(json.dumps({k: v for k, v in out.items() if k != 'params'}, indent=1, default=float))


# ------------------------------------------------------------------ transient / eye diagrams
def prbs7(n=254):
    s = [1] * 7; out = []
    for _ in range(n):
        b = s[6] ^ s[5]; out.append(s[6]); s = [b] + s[:6]
    return out


def eye_run(circ, rate, P=None, ipp=100e-6, nbits=254, tag=''):
    ui = 1 / rate; tr = 0.25 * ui
    bits = prbs7(nbits)
    pts = ['0 0']; prev = 0
    for k, b in enumerate(bits):
        if b != prev:
            pts.append(f'{k*ui:.6e} {prev*ipp:.4e}'); pts.append(f'{k*ui+tr:.6e} {b*ipp:.4e}'); prev = b
    lines = ['Iin 0 in pwl('] + ['+ ' + ' '.join(pts[i:i + 6]) for i in range(0, len(pts), 6)] + ['+ )']
    t = os.path.join(sim.TMP, f'eye_{circ}{tag}.txt')
    ctl = f'tran {ui/100:.4e} {nbits*ui:.6e}\nwrdata {t} v(out)'
    rep = lambda el: [e for e in el if e[1] != 'Iin']
    sim.run(sim.build(circ, P, control=ctl, extra_lines=lines, replace=rep))
    a = np.loadtxt(t)
    tt = np.arange(0, nbits * ui, ui / 64)
    v = np.interp(tt, a[:, 0], a[:, 1])
    # skip the first 16 bits (settling), fold on 2 UI
    s0 = 16 * 64
    tt, v = tt[s0:], v[s0:]
    v = v - v.mean()
    nb = len(v) // 64
    seg = v[:nb * 64].reshape(nb, 64)
    best = None
    for ph in range(64):
        col = seg[:, ph]
        hi, lo = col[col > 0], col[col <= 0]
        if len(hi) and len(lo):
            h = hi.min() - lo.max()
            if best is None or h > best[0]:
                best = (h, ph, hi.mean() - lo.mean())
    # horizontal opening: spread of zero crossings
    zc = []
    for i in range(len(v) - 1):
        if (v[i] <= 0) != (v[i + 1] <= 0):
            tc = tt[i] + (tt[i + 1] - tt[i]) * (0 - v[i]) / (v[i + 1] - v[i])
            zc.append(tc % ui)
    zc = np.array(zc)
    ang = np.exp(2j * np.pi * zc / ui); mean_ph = np.angle(ang.mean())
    dev = np.angle(ang * np.exp(-1j * mean_ph)) / (2 * np.pi) * ui
    jpp = dev.max() - dev.min()
    np.savetxt(os.path.join(DATA, f'eye_{circ}{tag}.csv'), np.column_stack([tt, v]), delimiter=',', header='time_s,vout_ac_V', comments='')
    return dict(circ=circ, rate=rate, eye_height_V=float(best[0]), amp_V=float(best[2]), eye_height_pct=float(100 * best[0] / best[2]),
                jitter_pp_s=float(jpp), eye_width_pct=float(100 * (1 - jpp / ui)), vtune=(P or {}).get('vtune', None))


def step_eye():
    rows = [eye_run('base', 10e9, tag='_10g'), eye_run('prop', 10e9, tag='_10g'),
            eye_run('prop', 12.5e9, tag='_12g5'), eye_run('base', 12.5e9, tag='_12g5'),
            eye_run('prop', 5e9, {'vtune': 0.0}, tag='_5g_vt0')]
    J('eye.json', rows)
    for r in rows:
        print(r)


STEPS.update(load=step_load, model=step_model, eye=step_eye)


# ------------------------------------------------------------------ output impedance
def step_zout():
    out = {}
    for circ in ('base', 'prop'):
        t = os.path.join(sim.TMP, f'zout_{circ}.txt')
        rep = lambda el: [(e[:5] + (None,)) if e[1] == 'Iin' else e for e in el]
        ctl = f'op\nprint @m2[gm] @m2[gds] @m3[gm] @m3[gds] @m3b[gds]\nac dec 40 10meg 200g\nwrdata {t} v(out)'
        o = sim.vals(sim.run(sim.build(circ, control=ctl, extra_lines=['Itest 0 out dc 0 ac 1'], replace=rep)))
        a = np.loadtxt(t); f = a[:, 0]; z = abs(a[:, 1] + 1j * a[:, 2])
        np.savetxt(os.path.join(DATA, f'zout_{circ}.csv'), np.column_stack([f, z]), delimiter=',', header='freq_Hz,Zout_ohm', comments='')
        out[circ] = dict(zout_100M=float(np.interp(1e8, f, z)), zout_5G=float(np.interp(5e9, f, z)), zout_10G=float(np.interp(1e10, f, z)), zout_max=float(z.max()), f_max=float(f[z.argmax()]))
        if circ == 'base':
            out[circ]['formula_lf'] = 1 / (o['@m2[gm]'] + o['@m2[gds]'] + o['@m3[gm]'] + o['@m3[gds]'] + o['@m3b[gds]'])
    J('zout.json', out); print(out)


STEPS.update(zout=step_zout)


if __name__ == '__main__':
    for s in (sys.argv[1:] or list(STEPS)):
        print(f'===== {s} ====='); STEPS[s]()
