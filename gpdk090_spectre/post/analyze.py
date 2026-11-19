#!/usr/bin/env python3
"""Turns the GPDK090 Spectre CSVs into paper figures, LaTeX macros and tables.

    python3 analyze.py <csv_dir> <paper_dir>

Every number written to <paper_dir>/numbers_gpdk.tex comes from a CSV in <csv_dir>.
"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CSV, PAP = sys.argv[1], sys.argv[2]
FIG = os.path.join(PAP, 'figures')
os.makedirs(FIG, exist_ok=True)
rd = lambda n: pd.read_csv(os.path.join(CSV, n + '.csv'))
ex = lambda n: os.path.exists(os.path.join(CSV, n + '.csv'))

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['DejaVu Serif'], 'font.size': 7.5, 'axes.labelsize': 7.5,
                     'legend.fontsize': 6.0, 'xtick.labelsize': 6.8, 'ytick.labelsize': 6.8, 'lines.linewidth': 1.0,
                     'axes.grid': True, 'grid.alpha': 0.25, 'grid.linewidth': 0.4, 'savefig.bbox': 'tight',
                     'savefig.pad_inches': 0.015, 'pdf.fonttype': 42, 'axes.titlesize': 7.5, 'legend.handlelength': 1.6,
                     'legend.borderpad': 0.3, 'legend.labelspacing': 0.25})
W1, W2 = 3.45, 7.1
COL = {'base2020': '#7f7f7f', 'regain': '#d62728', 'regain_eqp': '#ff9896', 'pf_v1': '#2ca02c', 'pf_opt': '#98df8a',
       'v1': '#1f77b4', 'v2': '#9467bd'}
LBL = {'base2020': '2020 TIA as drawn', 'regain': 'Spiral, same gain (B1)', 'regain_eqp': 'Spiral, same gain, $\\geq$0.9 mA (B2)',
       'pf_v1': 'Plain follower (F1)', 'pf_opt': 'Plain follower, re-opt. (F2)', 'v1': 'Proposed v1', 'v2': 'Proposed v2'}
N = {}
close = lambda a, b: np.isclose(a, b, rtol=1e-6, atol=1e-18)


W = {'30': 'Thirty', '100': 'OneHundred', '150': 'OneFifty', '200': 'TwoHundred', '300': 'ThreeHundred'}


def m(k, v, f='%.2f'):
    import re
    k = re.sub(r'\d+', lambda g: W[g.group(0)], k)
    N[k] = (f % v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v)


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + '.pdf'))
    fig.savefig(os.path.join(FIG, name + '.png'), dpi=200)
    plt.close(fig)


nom = rd('nominal').set_index('cir')
D = {}
for nm in ['regain', 'regain_eqp', 'pf_opt', 'v2']:
    if ex('design_' + nm):
        D[nm] = rd('design_' + nm).iloc[0].to_dict()
json.dump(D, open(os.path.join(PAP, 'designs_gpdk.json'), 'w'), indent=1)
same_v2 = all(abs(D['v2'][k] - v) < 1e-9 for k, v in dict(w1=4.5, w2=3.5, w3=7.0, w3b=28.0, wf=3.5, wt=12.0, ca=30e-15).items()) if 'v2' in D else True
same_pf = all(abs(D['pf_opt'][k] - v) < 1e-9 for k, v in dict(w1=4.5, w2=3.5, w3=7.0, w3b=28.0, wf=3.5).items()) if 'pf_opt' in D else True
CIRS = ['base2020', 'regain', 'regain_eqp', 'pf_v1'] + ([] if same_pf else ['pf_opt']) + ['v1'] + ([] if same_v2 else ['v2'])
m('VtwoDistinct', 'no' if same_v2 else 'yes')
TAG = {'base2020': 'Base', 'regain': 'Bone', 'regain_eqp': 'Btwo', 'pf_v1': 'Fone', 'pf_opt': 'Ftwo', 'v1': 'Pone', 'v2': 'Ptwo'}

# ------------------------------------------------------------- nominal numbers
for c in nom.index:
    r = nom.loc[c]; t = TAG[c]
    m(t + 'Zt', r.zt_dB, '%.1f'); m(t + 'ZtOhm', r.zt_ohm, '%.0f'); m(t + 'Pk', r.pk_dB, '%.2f')
    m(t + 'Bw', r.f3_Hz / 1e9, '%.2f'); m(t + 'I', r.idd_A * 1e3, '%.2f'); m(t + 'P', r.idd_A * 1e3, '%.2f')
    m(t + 'InOne', r.in1G * 1e12, '%.1f'); m(t + 'InFive', r.in5G * 1e12, '%.1f'); m(t + 'InTen', r.in10G * 1e12, '%.1f')
    m(t + 'Irms', r.irms_bw * 1e6, '%.2f'); m(t + 'IrmsTen', r.irms_10G * 1e6, '%.2f')
    m(t + 'Gbw', r.gbw_ohmHz / 1e12, '%.2f')
    for k, kk in (('Tg0_dB', 'Tg'), ('Tl0_dB', 'Tl')):
        m(t + kk, r[k], '%.1f')
    for k, kk in (('PMg_deg', 'PMg'), ('PMl_deg', 'PMl')):
        m(t + kk, r[k], '%.0f') if r[k] == r[k] else m(t + kk, '--')
    for k, kk in (('fug_Hz', 'Fug'), ('ful_Hz', 'Ful')):
        m(t + kk, r[k] / 1e9, '%.2f') if r[k] == r[k] else m(t + kk, '--')
p1 = nom.loc['v1']
m('RatioBwPoneBone', p1.f3_Hz / nom.loc['regain'].f3_Hz); m('RatioIPoneBone', p1.idd_A / nom.loc['regain'].idd_A, '%.1f')
m('RatioBwFonePone', nom.loc['pf_v1'].f3_Hz / p1.f3_Hz); m('PctBwLoss', 100 * (1 - p1.f3_Hz / nom.loc['pf_v1'].f3_Hz), '%.0f')

# operating points and the DC-gain check of the Z_T expression
op = rd('op_v1').set_index('dev')
for d in ['M1', 'M2', 'M3', 'M3b', 'Mf']:
    m('Ov' + d.replace('3b', 'Threeb').replace('1', 'One').replace('2', 'Two').replace('3', 'Three'),
      (abs(op.loc[d, 'vds']) - abs(op.loc[d, 'vdsat'])) * 1e3, '%.0f')
mm = op.loc['M3', 'gm'] / op.loc['M2', 'gm']
ro = 1 / (op.loc['M3', 'gds'] + op.loc['M3b', 'gds'])
gf = op.loc['Mf', 'gm'] + op.loc['Mf', 'gmbs'] + op.loc['Mf', 'gds']
t0 = mm * op.loc['Mf', 'gm'] * ro
zt0 = mm * ro / (1 + t0)
m('Mratio', mm); m('Ro', ro, '%.0f'); m('Tzero', t0); m('ZtApprox', zt0, '%.0f'); m('ZtErr', 100 * (zt0 / p1.zt_ohm - 1), '%.0f')
m('GfInv', 1 / gf, '%.0f'); m('Gmf', op.loc['Mf', 'gm'] * 1e3); m('Imf', op.loc['Mf', 'ids'] * 1e6, '%.0f')
m('IOne', op.loc['M1', 'ids'] * 1e6, '%.0f'); m('IThree', op.loc['M3', 'ids'] * 1e6, '%.0f')
m('TzeroStb', 10 ** (p1.Tg0_dB / 20))
nodes = rd('nodes_v1').set_index('node')['V']
m('Vin', nodes['inp']); m('Vout', nodes['outp'])
opb = rd('op_base2020').set_index('dev')
m('BaseMoneI', opb.loc['M1', 'ids'] * 1e9, '%.2f'); m('BaseMoneGds', opb.loc['M1', 'gds'] * 1e3, '%.2f')

# ------------------------------------------------------------- active-inductor impedance
z = rd('zai_v1'); vt = rd('vtune_v1')
cg = 30e-15 + abs(op.loc['Mf', 'cgs'])
m('ZaiR', z.zmag.iloc[0], '%.0f')
rows = []
for v in [0.16, 0.24, 0.28, 0.32]:
    x = z[close(z.vtn, v)]; rt = vt[close(vt.vtn, v)].Rt_ohm.values[0]
    lsim = x.iloc[(x.f - 1e8).abs().argmin()].Leq_H; lpred = cg / gf * (rt - 1 / gf)
    rows.append((v, rt, lsim, lpred))
    k = {0.16: 'A', 0.24: 'B', 0.28: 'C', 0.32: 'D'}[v]
    m('ZaiRt' + k, rt, '%.0f'); m('ZaiL' + k, lsim * 1e9, '%.1f'); m('ZaiLp' + k, lpred * 1e9, '%.1f')
lsim = []
for v in sorted(z.vtn.unique()):
    x = z[close(z.vtn, v)]
    lsim.append((v, x.iloc[(x.f - 1e8).abs().argmin()].Leq_H))
lsim = np.array(lsim)
vcross = np.interp(0, lsim[:9, 1], lsim[:9, 0])
rtv = vt[['vtn', 'Rt_ohm']].values
vpred = np.interp(1 / gf, rtv[:, 1], rtv[:, 0])
m('VcrossSim', vcross, '%.3f'); m('VcrossPred', vpred, '%.3f')
qmax = np.tan(np.radians(z[close(z.vtn, 0.32)].zph_deg.max()))
m('QmaxD', qmax)

fig, ax = plt.subplots(1, 2, figsize=(W1, 1.55))
for v, cl in ((0.0, '#c6dbef'), (0.16, '#6baed6'), (0.24, '#2171b5'), (0.32, '#08306b')):
    x = z[close(z.vtn, v)]
    ax[0].semilogx(x.f / 1e9, x.zmag, color=cl, label='%.2f' % v)
    ax[1].semilogx(x.f / 1e9, x.zph_deg, color=cl)
ax[0].set_xlabel('f (GHz)'); ax[0].set_ylabel(r'$|Z_{AI}|$ ($\Omega$)'); ax[0].legend(title=r'$V_{tune}$ (V)', fontsize=5.5, title_fontsize=5.5)
ax[1].set_xlabel('f (GHz)'); ax[1].set_ylabel(r'$\angle Z_{AI}$ (deg)')
for a in ax:
    a.set_xlim(0.01, 100)
fig.tight_layout(w_pad=0.6)
save(fig, 'g_zai')

# ------------------------------------------------------------- AC and noise
fig, ax = plt.subplots(1, 2, figsize=(W2, 1.75))
for c in CIRS:
    a = rd('ac_' + c)
    ls = '--' if c in ('pf_v1', 'pf_opt') else (':' if c == 'base2020' else '-')
    ax[0].semilogx(a.f / 1e9, 20 * np.log10(a.zt_mag), color=COL[c], ls=ls, label=LBL[c])
    n = rd('noise_' + c)
    if c != 'regain_eqp':
        ax[1].semilogx(n.f / 1e9, n.in_A_rtHz * 1e12, color=COL[c], ls=ls, label=LBL[c])
ax[0].set_xlim(0.01, 100); ax[0].set_ylim(25, 62); ax[0].set_xlabel('Frequency (GHz)'); ax[0].set_ylabel(r'$|Z_T|$ (dB$\Omega$)')
ax[0].legend(loc='lower left', ncol=2, fontsize=5.4); ax[0].set_title('(a) Transimpedance')
ax[1].set_xlim(0.01, 30); ax[1].set_ylim(0, 40); ax[1].set_xlabel('Frequency (GHz)')
ax[1].set_ylabel(r'$i_{n,in}$ (pA/$\sqrt{\rm Hz}$)'); ax[1].set_title('(b) Input-referred noise current'); ax[1].legend(loc='upper left', ncol=2)
fig.tight_layout(w_pad=1.0)
save(fig, 'g_ac_noise')

# ------------------------------------------------------------- tuning law
fig, ax = plt.subplots(1, 2, figsize=(W1, 1.6))
for c in (['v1'] + ([] if same_v2 else ['v2'])):
    t = rd('vtune_' + c)
    ax[0].plot(t.vtn, t.f3_Hz / 1e9, 'o-', ms=2.2, color=COL[c], label=LBL[c])
    ax[1].plot(t.vtn, t.pk_dB, 's-', ms=2.2, color=COL[c])
    ok = t[t.pk_dB <= 1.0]
    tg = TAG[c]
    m(tg + 'TuneMin', ok.f3_Hz.min() / 1e9); m(tg + 'TuneMax', ok.f3_Hz.max() / 1e9); m(tg + 'TuneRatio', ok.f3_Hz.max() / ok.f3_Hz.min())
    m(tg + 'VtOk', ok.vtn.max()); m(tg + 'PMgMin', t.PMg_deg.min(), '%.0f'); m(tg + 'PkTop', t.pk_dB.max(), '%.1f')
    m(tg + 'IrmsLo', ok.irms_bw.min() * 1e6); m(tg + 'IrmsHi', ok.irms_bw.max() * 1e6)
    m(tg + 'ZtSpread', ok.zt_dB.max() - ok.zt_dB.min(), '%.2f')
    m(tg + 'FugLo', t.fug_Hz.min() / 1e9); m(tg + 'FugHi', t.fug_Hz.max() / 1e9)
ax[0].set_xlabel(r'$V_{tune}$ (V)'); ax[0].set_ylabel('BW$_{-3dB}$ (GHz)')
ax[1].set_xlabel(r'$V_{tune}$ (V)'); ax[1].set_ylabel('Peaking (dB)'); ax[1].axhline(1.0, color='k', lw=0.5, ls=':')
if not same_v2:
    ax[0].legend(fontsize=5.5)
fig.tight_layout(w_pad=0.6)
save(fig, 'g_tuning')

# ------------------------------------------------------------- loads, photodiode capacitance, decomposition
L = rd('loads')


def best(x):
    ok = x[x.pk_dB <= 1.0]
    return (ok.f3_Hz.max() if len(ok) else np.nan)


fig, ax = plt.subplots(1, 3, figsize=(W2, 1.7))
for c in ['regain', 'pf_v1', 'v1'] + ([] if same_v2 else ['v2']):
    for i, par in enumerate(['cl', 'cpd']):
        x = L[(L.cir == c) & (L.par == par)]
        vals = sorted(x.val.unique())
        bw = [best(x[close(x.val, v)]) for v in vals]
        mk = 'o' if c in ('v1', 'v2') else ('^' if c.startswith('pf') else 's')
        lab = LBL[c] + (' (re-tuned)' if c in ('v1', 'v2') else '')
        ax[i].plot(np.array(vals) * 1e15, np.array(bw) / 1e9, mk + '-', ms=2.5, color=COL[c], label=lab)
        if c == 'pf_v1' and par == 'cpd':
            # plain follower: show bandwidth where peaking exceeds 1 dB (no knob to correct it)
            pkv = x.pk_dB.values
            for v, pk, f3 in zip(x.val.values, pkv, x.f3_Hz.values):
                if pk > 1.0:
                    ax[i].plot(v * 1e15, f3 / 1e9, 'x', color=COL[c], ms=4)
                    ax[i].annotate('%.1f dB' % pk, (v * 1e15, f3 / 1e9), fontsize=5.2, xytext=(2, 2), textcoords='offset points', color=COL[c])
ax[0].set_xlabel('$C_L$ (fF)'); ax[0].set_ylabel('BW, peaking$\\leq$1 dB (GHz)'); ax[0].set_title('(a) Load ($C_{PD}$ = 50 fF)')
ax[1].set_xlabel('$C_{PD}$ (fF)'); ax[1].set_title('(b) Photodiode ($C_L$ = 30 fF)')
ax[0].legend(fontsize=5.4)
ax[0].set_yscale('log'); ax[0].set_yticks([1, 2, 5, 10]); ax[0].set_yticklabels(['1', '2', '5', '10'])
# decomposition
dc = rd('decomp')
x = dc[dc.cir == 'v1']
modes = [('pf', 'Plain follower'), ('pfca', '+ $C_a$ (OUT-IN)'), ('aint', '$M_t$ only, no $C_a$'), ('ai', 'Full gyrator-C')]
cls = sorted(x.cl.unique())
for j, (mo, lab) in enumerate(modes):
    y = [best(x[(x['mode'] == mo) & close(x.cl, c)]) / 1e9 for c in cls]
    ax[2].plot(np.array(cls) * 1e15, y, ['^-', 'v-', 'd-', 'o-'][j], ms=2.5, label=lab,
               color=['#2ca02c', '#bcbd22', '#17becf', '#1f77b4'][j])
ax[2].set_xlabel('$C_L$ (fF)'); ax[2].set_title('(c) Feedback network, v1 sizes'); ax[2].legend(fontsize=5.4)
ax[2].set_yscale('log'); ax[2].set_yticks([1, 2, 5, 10]); ax[2].set_yticklabels(['1', '2', '5', '10'])
fig.tight_layout(w_pad=0.8)
save(fig, 'g_loads')
for mo in ['pf', 'pfca', 'aint', 'ai']:
    for c in (30e-15, 150e-15, 300e-15):
        m('Dec%s%d' % (mo.capitalize(), round(c * 1e15)), best(x[(x['mode'] == mo) & close(x.cl, c)]) / 1e9)
for c in ['regain', 'pf_v1', 'v1', 'v2']:
    for par, vals in (('cl', (30e-15, 150e-15, 300e-15)), ('cpd', (100e-15, 200e-15, 300e-15))):
        for v in vals:
            xx = L[(L.cir == c) & (L.par == par) & close(L.val, v)]
            if len(xx):
                m('Ld%s%s%d' % (TAG[c], par.capitalize(), round(v * 1e15)), best(xx) / 1e9)
xf = L[(L.cir == 'pf_v1') & (L.par == 'cpd')]
for v in (100e-15, 200e-15, 300e-15):
    r = xf[close(xf.val, v)].iloc[0]
    m('PfPk%d' % round(v * 1e15), r.pk_dB, '%.1f'); m('PfBwRaw%d' % round(v * 1e15), r.f3_Hz / 1e9)
# cross-over load where re-tuned v1 overtakes the plain follower
xa = [best(x[(x['mode'] == 'ai') & close(x.cl, c)]) for c in cls]
xp = [best(x[(x['mode'] == 'pf') & close(x.cl, c)]) for c in cls]
r = np.array(xa) / np.array(xp)
cross = np.interp(1.0, r, np.array(cls)) if r[0] < 1 < r[-1] else np.nan
m('ClCross', cross * 1e15, '%.0f'); m('AiPfHeavy', r[-1])

# ------------------------------------------------------------- PVT
P = rd('pvt_all')


def trimmed(g):
    ok = g[g.pk_dB <= 1.0]
    return ok.loc[ok.f3_Hz.idxmax()] if len(ok) else g.loc[g.pk_dB.idxmin()]


pv = {}
for c in P.cir.unique():
    x = P[P.cir == c]
    if c in ('v1', 'v2'):
        vfix = 0.24 if c == 'v1' else D.get('v2', {}).get('vtn', 0.24)
        vg = np.array(sorted(x.vtn.unique())); vfix = vg[np.argmin(abs(vg - vfix))]
        fx = x[close(x.vtn, vfix)]
        tr = pd.DataFrame([trimmed(g) for _, g in x.groupby(['sec', 'temp', 'vdd'])])
    else:
        fx = x; tr = x
    pv[c] = (fx, tr)
    t = TAG[c]
    m(t + 'PvtZtLo', fx.zt_dB.min(), '%.1f'); m(t + 'PvtZtHi', fx.zt_dB.max(), '%.1f')
    m(t + 'PvtBwLo', fx.f3_Hz.min() / 1e9, '%.1f'); m(t + 'PvtBwHi', fx.f3_Hz.max() / 1e9, '%.1f')
    m(t + 'PvtPkHi', fx.pk_dB.max(), '%.1f'); m(t + 'PvtNpk', int((fx.pk_dB > 1).sum()), '%d')
    m(t + 'PvtIlo', fx.idd_A.min() * 1e3); m(t + 'PvtIhi', fx.idd_A.max() * 1e3)
    m(t + 'PvtNsat', int((fx.allsat == 1).sum()), '%d')
    m(t + 'PvtTrBwLo', tr.f3_Hz.min() / 1e9, '%.1f'); m(t + 'PvtTrBwHi', tr.f3_Hz.max() / 1e9, '%.1f')
    m(t + 'PvtTrPkHi', tr.pk_dB.max(), '%.2f')
    if c in ('v1', 'v2'):
        m(t + 'PvtTrVlo', tr.vtn.min()); m(t + 'PvtTrVhi', tr.vtn.max())
        w = fx.loc[fx.pk_dB.idxmax()]
        m(t + 'PvtWorst', '%s, %d\\,\\si{\\celsius}, %.1f\\,V' % (w.sec, w.temp, w.vdd))
        s = tr.loc[tr.f3_Hz.idxmin()]
        m(t + 'PvtSlow', '%s, %d\\,\\si{\\celsius}, %.1f\\,V' % (s.sec, s.temp, s.vdd))
m('NPvt', len(pv['v1'][0]), '%d')
m('BoneLf', D['regain']['lf'] * 1e9, '%.1f'); m('BtwoLf', D['regain_eqp']['lf'] * 1e9, '%.1f')
for k_ in ('w1', 'w2', 'w3', 'w3b', 'wf', 'wt'):
    m('Vtwo' + k_.upper().replace('1', 'a').replace('2', 'b').replace('3', 'c'), D['v2'][k_], '%.2f')
m('VtwoCa', D['v2']['ca'] * 1e15, '%.1f'); m('VtwoVt', D['v2']['vtn'], '%.2f'); m('VtwoRn', D['v2']['rn'] / 1e3, '%.2f'); m('VtwoIref', D['v2']['iref'] * 1e6, '%.1f')

fig, ax = plt.subplots(1, 2, figsize=(W1, 1.75))
for c, mk in (('regain', 's'), ('pf_v1', '^'), ('v1', 'o')):
    fx, tr = pv[c]
    ax[0].scatter(fx.f3_Hz / 1e9, fx.pk_dB, s=6, marker=mk, color=COL[c], label=LBL[c] + (' fixed' if c == 'v1' else ''), alpha=0.8, lw=0)
    if c == 'v1':
        ax[0].scatter(tr.f3_Hz / 1e9, tr.pk_dB, s=7, marker='*', color='k', label='Proposed v1 trimmed', lw=0)
ax[0].axhline(1, color='k', lw=0.5, ls=':'); ax[0].set_xscale('log')
ax[0].set_xlabel('BW (GHz)'); ax[0].set_ylabel('Peaking (dB)'); ax[0].set_title('(a) 45 PVT points'); ax[0].legend(fontsize=5.0, loc='upper left')
ax[0].set_xticks([1, 2, 5, 10, 20]); ax[0].set_xticklabels(['1', '2', '5', '10', '20'])

# ------------------------------------------------------------- Monte Carlo
mc = {}
for c in ['v1', 'v2', 'regain', 'pf_v1', 'pf_opt']:
    if not ex('mc_' + c):
        continue
    x = rd('mc_' + c)
    if c in ('v1', 'v2'):
        vfix = 0.24 if c == 'v1' else D.get('v2', {}).get('vtn', 0.24)
        vg = np.array(sorted(x.vtn.unique())); vfix = vg[np.argmin(abs(vg - vfix))]
        fx = x[close(x.vtn, vfix)]
        tr = pd.DataFrame([trimmed(g) for _, g in x.groupby('run')])
    else:
        fx = tr = x
    mc[c] = (fx, tr)
    t = TAG[c]
    m(t + 'McN', len(fx), '%d'); m(t + 'McBw', fx.f3_Hz.mean() / 1e9); m(t + 'McBwSd', fx.f3_Hz.std() / 1e9)
    m(t + 'McBwMin', fx.f3_Hz.min() / 1e9); m(t + 'McPkN', int((fx.pk_dB > 1).sum()), '%d'); m(t + 'McPkMax', fx.pk_dB.max())
    m(t + 'McZt', fx.zt_dB.mean(), '%.1f'); m(t + 'McZtSd', fx.zt_dB.std()); m(t + 'McIsd', fx.idd_A.std() * 1e6, '%.0f')
    m(t + 'McYield', 100.0 * (fx.pk_dB <= 1).mean(), '%.1f')
    m(t + 'McTrBw', tr.f3_Hz.mean() / 1e9); m(t + 'McTrBwSd', tr.f3_Hz.std() / 1e9); m(t + 'McTrPkMax', tr.pk_dB.max())
    m(t + 'McTrYield', 100.0 * (tr.pk_dB <= 1).mean(), '%.1f')
    if c in ('v1', 'v2'):
        m(t + 'McVlo', tr.vtn.min()); m(t + 'McVhi', tr.vtn.max())
bins = np.linspace(5.5, 11, 23)
for c, al in (('regain', 0.5), ('pf_v1', 0.5), ('v1', 0.6)):
    if c in mc:
        ax[1].hist(mc[c][1].f3_Hz / 1e9, bins=bins, color=COL[c], alpha=al, label=LBL[c] + (' trimmed' if c == 'v1' else ''))
ax[1].set_xlabel('BW (GHz)'); ax[1].set_ylabel('Count'); ax[1].set_title('(b) 200-run mismatch MC'); ax[1].legend(fontsize=5.0)
fig.tight_layout(w_pad=0.6)
save(fig, 'g_pvt_mc')

# ------------------------------------------------------------- DC cancellation and eyes
S = rd('dcc_sweep'); st = rd('dcc_stb'); nz = rd('dcc_noise')
x0 = S[(S.cir == 'v1') & (S.dcc == 'none') & (S.sec == 'NN')]
x1 = S[(S.cir == 'v1') & (S.dcc == 'dcc') & (S.sec == 'NN')]


def limit(x, z0, b0):
    ok = x[(abs(x.zt_dB - z0) <= 1.0) & (x.f3_Hz >= 0.9 * b0) & (x.pk_dB <= 1.5)]
    bad = x[~x.index.isin(ok.index)]
    return (bad.idc.min() if len(bad) else x.idc.max())


z0, b0 = x0.zt_dB.iloc[0], x0.f3_Hz.iloc[0]
m('DcNoLim', limit(x0, z0, b0) * 1e6, '%.0f')
gain1 = x0[abs(x0.zt_dB - z0) > 1.0].idc.min()
m('DcNoGainLim', gain1 * 1e6, '%.0f')
z1, b1 = x1.zt_dB.iloc[0], x1.f3_Hz.iloc[0]
m('DcZt', z1); m('DcBw', b1 / 1e9); m('DcPk', x1.pk_dB.iloc[0])
okd = x1[(abs(x1.zt_dB - z1) <= 1.0) & (x1.f3_Hz >= 0.9 * b1)]
m('DcLim', okd.idc.max() * 1e6, '%.0f')
m('DcPkMax', x1[x1.idc <= okd.idc.max()].pk_dB.max())
m('DcFloMax', x1[x1.idc <= okd.idc.max()].flo_Hz.max() / 1e6)
m('DcIadd', (x1.idd_A.iloc[0] - x0.idd_A.iloc[0]) * 1e6, '%.0f')
m('DcBwHund', x0[close(x0.idc, 100e-6)].f3_Hz.iloc[0] / 1e9)
s1 = st[st.cir == 'v1']; okst = s1[s1.idc <= okd.idc.max()]
m('DcPmMin', okst.PM_deg.min(), '%.0f'); m('DcFuMax', okst.fu_Hz.max() / 1e6)
n0 = nz[(nz.cir == 'v1') & (nz.dcc == 'none') & (nz.idc == 0)].in5G.iloc[0]
n1 = nz[(nz.cir == 'v1') & (nz.dcc == 'dcc') & (nz.idc == 0)].in5G.iloc[0]
m('DcNoisePct', 100 * (n1 / n0 - 1), '%.0f'); m('DcInFive', n1 * 1e12, '%.1f')
dsec = S[(S.cir == 'v1') & (S.dcc == 'dcc')]
okc = []
for sec, g in dsec.groupby('sec'):
    zz, bb = g.zt_dB.iloc[0], g.f3_Hz.iloc[0]
    okk = g[(abs(g.zt_dB - zz) <= 1.0) & (g.f3_Hz >= 0.9 * bb)]
    okc.append(okk.idc.max())
m('DcCornerLim', min(okc) * 1e6, '%.0f')

fig, ax = plt.subplots(1, 2, figsize=(W1, 1.65))
ax[0].plot(x0.idc * 1e6, x0.f3_Hz / 1e9, 'o-', ms=2.2, color='#7f7f7f', label='no loop')
ax[0].plot(x1.idc * 1e6, x1.f3_Hz / 1e9, 's-', ms=2.2, color='#1f77b4', label='with loop')
a2 = ax[0].twinx()
a2.plot(x0.idc * 1e6, x0.zt_dB, ':', color='#7f7f7f'); a2.plot(x1.idc * 1e6, x1.zt_dB, ':', color='#1f77b4')
a2.set_ylabel('Gain (dB$\\Omega$, dotted)', fontsize=6); a2.grid(False); a2.tick_params(labelsize=6)
ax[0].set_xlabel('$I_{avg}$ ($\\mu$A)'); ax[0].set_ylabel('BW (GHz)'); ax[0].legend(fontsize=5.4, loc='lower left')
ax[0].set_title('(a) Average photocurrent')
# eye diagram of v1 with the loop, 10 Gb/s, 0-100 uA
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye
ep = pd.read_csv(os.path.join(CSV, 'eye_post.csv')).set_index('case')
w = rd('eyewave_v1_dcc_uni_10')
tt, vv = eye.rebuild(w)
lat = ep.loc['v1_dcc_uni_10', 'lat']
for k in range(int(tt[0]) + 30, int(tt[-1]) - 4):
    sel = (tt >= k + lat - 0.5) & (tt <= k + lat + 1.5)
    ax[1].plot((tt[sel] - k - lat + 0.5) * 100, vv[sel] * 1e3, color='#1f77b4', lw=0.3, alpha=0.5)
ax[1].set_xlabel('Time (ps)'); ax[1].set_ylabel('$V_{OUT}$ (mV)'); ax[1].set_title('(b) 10 Gb/s, 0--100 $\\mu$A, loop on')
fig.tight_layout(w_pad=0.5)
save(fig, 'g_dcc_eye')
for case in ep.index:
    tg = case.replace('_nodcc', '').replace('_dcc', 'D').replace('_bip', 'B').replace('_uni', 'U').replace('_12p5', 'Tw').replace('_10', 'Te')
    tg = tg.replace('base2020', 'Base').replace('regain_eqp', 'Btwo').replace('regain', 'Bone').replace('pf_v1', 'Fone').replace('pf_opt', 'Ftwo').replace('v1', 'Pone').replace('v2', 'Ptwo')
    tg = ''.join(ch for ch in tg if ch.isalpha())
    m('Eye' + tg + 'V', ep.loc[case, 'vpct'], '%.0f'); m('Eye' + tg + 'H', ep.loc[case, 'hpct'], '%.0f')
    m('Eye' + tg + 'A', ep.loc[case, 'amp'] * 1e3, '%.0f')

# ------------------------------------------------------------- R/C spread
rc = rd('rc_sens'); r1 = rc[rc.cir == 'v1']
m('RcBwLo', r1.f3_Hz.min() / 1e9); m('RcBwHi', r1.f3_Hz.max() / 1e9); m('RcPkHi', r1.pk_dB.max()); m('RcZtLo', r1.zt_dB.min(), '%.1f'); m('RcZtHi', r1.zt_dB.max(), '%.1f')

# ------------------------------------------------------------- tables
tab = []
for c in CIRS:
    r = nom.loc[c]
    fb = {'base2020': '2.4\\,nH', 'regain': '%.1f\\,nH+%.0f\\,$\\Omega$' % (D['regain']['lf'] * 1e9, D['regain']['rsl']),
          'regain_eqp': '%.1f\\,nH+%.0f\\,$\\Omega$' % (D['regain_eqp']['lf'] * 1e9, D['regain_eqp']['rsl']),
          'pf_v1': 'follower', 'pf_opt': 'follower', 'v1': 'gyrator-C', 'v2': 'gyrator-C'}[c]
    short = {'base2020': '2020, drawn', 'regain': 'B1 spiral', 'regain_eqp': 'B2 spiral', 'pf_v1': 'F1 follower', 'pf_opt': 'F2 follower',
             'v1': 'Proposed v1', 'v2': 'Proposed v2'}[c]
    bw = '%.2f' % (r.f3_Hz / 1e9) if r.pk_dB < 3 else 'res.'
    tab.append('%s & %.1f & %.2f & %s & %.2f & %.1f & %.2f & %s \\\\' % (short, r.zt_dB, r.pk_dB, bw, r.idd_A * 1e3, r.in5G * 1e12,
                                                                       r.irms_bw * 1e6, fb))
open(os.path.join(PAP, 'table_nominal.tex'), 'w').write('\n'.join(tab) + '\n')

with open(os.path.join(PAP, 'numbers_gpdk.tex'), 'w') as f:
    f.write('% generated by gpdk090_spectre/post/analyze.py from GPDK090 Spectre CSVs - do not edit\n')
    for k in sorted(N):
        f.write('\\newcommand{\\%s}{%s}\n' % (k, N[k]))
json.dump(N, open(os.path.join(PAP, 'numbers_gpdk.json'), 'w'), indent=1, sort_keys=True)
print(len(N), 'macros;', 'CIRS', CIRS)

# ------------------------------------------------------------- loop gains (stability)
fig, ax = plt.subplots(1, 2, figsize=(W1, 1.6))
for c, ls in (('v1', '-'), ('pf_v1', '--')):
    for t, col, lab in (('lgg', '#1f77b4', 'global'), ('lgl', '#ff7f0e', 'local FVF')):
        g = rd('stb_%s_%s' % (t, c))
        ax[0].semilogx(g.f / 1e9, g.lg_mag_db, ls=ls, color=col, label='%s, %s' % ('v1' if c == 'v1' else 'F1', lab))
        ph = np.unwrap(np.radians(g.lg_ph_deg.values)); ph = np.degrees(ph - ph[0])
        ax[1].semilogx(g.f / 1e9, ph, ls=ls, color=col)
ax[0].axhline(0, color='k', lw=0.5); ax[0].set_ylim(-40, 20); ax[0].set_xlim(1e-3, 1e3)
ax[0].set_xlabel('f (GHz)'); ax[0].set_ylabel('Loop gain (dB)'); ax[0].legend(fontsize=5.0, loc='lower left')
ax[1].set_xlim(1e-3, 1e3); ax[1].set_xlabel('f (GHz)'); ax[1].set_ylabel('Phase from DC (deg)')
fig.tight_layout(w_pad=0.6)
save(fig, 'g_stb')
t = rd('vtune_v1')
m('PMgAtLo', t.PMg_deg.iloc[0], '%.0f'); m('PMgAtNom', t[close(t.vtn, 0.24)].PMg_deg.iloc[0], '%.0f')
with open(os.path.join(PAP, 'numbers_gpdk.tex'), 'w') as f:
    f.write('% generated by gpdk090_spectre/post/analyze.py from GPDK090 Spectre CSVs - do not edit\n')
    for k in sorted(N):
        f.write('\\newcommand{\\%s}{%s}\n' % (k, N[k]))
# tuning table
rows = []
for _, r in t.iterrows():
    rows.append('%.2f & %.0f & %.2f & %.2f & %.2f & %.2f & %.0f \\\\' % (r.vtn, r.Rt_ohm, r.f3_Hz / 1e9, r.pk_dB, r.in5G * 1e12, r.irms_bw * 1e6, r.PMg_deg))
open(os.path.join(PAP, 'table_tune.tex'), 'w').write('\n'.join(rows[::2] + []) + '\n')
