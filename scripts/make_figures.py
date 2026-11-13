"""Render every figure of the paper from results/data (no simulation here)."""
import os, json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'results', 'data'); FIG = os.path.join(ROOT, 'results', 'figures')
os.makedirs(FIG, exist_ok=True)
BLUE, ORANGE, AQUA, YELLOW, VIOLET = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#6250d6'
RAMP = ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281', '#0d366b']
INK, MUTED, GRID = '#1f1f1e', '#6b6a65', '#e4e3df'
plt.rcParams.update({'font.size': 9, 'font.family': 'DejaVu Sans', 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
                     'axes.spines.top': False, 'axes.spines.right': False, 'lines.linewidth': 1.8, 'legend.frameon': False,
                     'axes.titlesize': 9, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'savefig.dpi': 300,
                     'figure.dpi': 110, 'axes.axisbelow': True})
# digitised from the baseline paper (Alsheikhjader 2020, Figs. 3 and 6); approximate
P_F = np.array([1, 5, 10, 15, 20, 25, 28, 30, 35, 40, 45, 50.])
P_Z = np.array([203, 163, 157, 157, 147, 135, 118, 109, 85, 66, 53, 42.])
P_N = np.array([31.5, 14.14, 10, 16.32, 11.3, 4.4, 4.1, 4.6, 2.1, 2.0, 1.4, 3.2])

L = lambda n: np.genfromtxt(os.path.join(DATA, n), delimiter=',', names=True)
Jl = lambda n: json.load(open(os.path.join(DATA, n)))


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + '.png'), bbox_inches='tight')
    fig.savefig(os.path.join(FIG, name + '.pdf'), bbox_inches='tight')
    plt.close(fig); print('wrote', name)


def fig_baseline():
    b, b2 = L('ac_baseline.csv'), L('ac_baseline_vg_m1V.csv')
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    a = ax[0]
    a.plot(b['freq_Hz'] / 1e9, 10 ** (b['Zt_dBohm'] / 20), color=ORANGE, label='This work: BSIM4 re-simulation, M3b gate = 0 V')
    a.plot(b2['freq_Hz'] / 1e9, 10 ** (b2['Zt_dBohm'] / 20), color=ORANGE, ls='--', lw=1.3, label='BSIM4 re-simulation, M3b gate = −1 V')
    a.plot(P_F, P_Z, 'o', color=INK, ms=4, mfc='white', label='Published curve [1] (digitised)')
    a.set_xlim(0, 50); a.set_ylim(0, 520); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('|Z$_T$| (Ω)')
    a.set_title('(a) Baseline transimpedance'); a.legend(fontsize=7, loc='upper right')
    a = ax[1]
    a.plot(b['freq_Hz'] / 1e9, b['in_noise_pA_rtHz'], color=ORANGE, label='BSIM4 re-simulation, 0 V')
    a.plot(b2['freq_Hz'] / 1e9, b2['in_noise_pA_rtHz'], color=ORANGE, ls='--', lw=1.3, label='BSIM4 re-simulation, −1 V')
    a.plot(P_F, P_N, 'o', color=INK, ms=4, mfc='white', label='Published curve [1] (digitised)')
    a.set_xlim(0, 50); a.set_ylim(0, 130); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('Input-referred noise (pA/√Hz)')
    a.set_title('(b) Baseline input-referred noise'); a.legend(fontsize=7, loc='upper right')
    fig.tight_layout(); save(fig, 'fig_baseline_reproduction')


def fig_compare():
    b, p = L('ac_baseline.csv'), L('ac_proposed.csv'); n = Jl('nominal.json')
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    a = ax[0]
    a.semilogx(b['freq_Hz'] / 1e9, b['Zt_dBohm'], color=ORANGE, ls='--', label='Baseline (passive L$_f$ = 2.4 nH)')
    a.semilogx(p['freq_Hz'] / 1e9, p['Zt_dBohm'], color=BLUE, label='Proposed (active-inductor feedback)')
    a.set_xlim(0.01, 100); a.set_ylim(20, 60); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('Transimpedance (dBΩ)')
    f3 = n['proposed']['f3'] / 1e9
    a.axvline(f3, color=MUTED, lw=0.8, ls=':'); a.text(f3 * 0.92, 22, f'{f3:.1f} GHz', ha='right', color=MUTED, fontsize=7)
    a.text(0.012, n['proposed']['z0db'] + 1.2, f"{n['proposed']['z0db']:.1f} dBΩ", color=INK, fontsize=7)
    a.text(0.012, n['baseline']['z0db'] + 1.2, f"{n['baseline']['z0db']:.1f} dBΩ", color=INK, fontsize=7)
    a.set_title('(a) Transimpedance'); a.legend(fontsize=7, loc='lower left')
    a = ax[1]
    a.semilogx(b['freq_Hz'] / 1e9, b['in_noise_pA_rtHz'], color=ORANGE, ls='--', label='Baseline')
    a.semilogx(p['freq_Hz'] / 1e9, p['in_noise_pA_rtHz'], color=BLUE, label='Proposed')
    a.set_xlim(0.01, 30); a.set_ylim(0, 60); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('Input-referred noise (pA/√Hz)')
    a.set_title('(b) Input-referred noise current'); a.legend(fontsize=7)
    fig.tight_layout(); save(fig, 'fig_baseline_vs_proposed')


def fig_vtune():
    sw = Jl('vtune_sweep.json')
    vts = [0.0, 0.08, 0.16, 0.24, 0.28, 0.36]
    fig = plt.figure(figsize=(7.2, 3.4)); gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1])
    a = fig.add_subplot(gs[:, 0])
    for c, vt in zip(RAMP, vts):
        d = L(f'ac_proposed_vt{int(round(vt*1000)):03d}.csv')
        a.semilogx(d['freq_Hz'] / 1e9, d['Zt_dBohm'], color=c, label=f'{vt:.2f} V')
    a.axhline(sw[0]['z0db'] - 3, color=MUTED, lw=0.8, ls=':'); a.text(0.11, sw[0]['z0db'] - 3.9, '−3 dB', color=MUTED, fontsize=7)
    a.set_xlim(0.1, 40); a.set_ylim(40, 60); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('Transimpedance (dBΩ)')
    a.set_title('(a) Response versus V$_{tune}$'); a.legend(title='V$_{tune}$', fontsize=7, title_fontsize=7, loc='lower left')
    v = np.array([r['vtune'] for r in sw]); f3 = np.array([r['f3'] for r in sw]) / 1e9; pk = np.array([r['pk'] for r in sw])
    a = fig.add_subplot(gs[0, 1]); a.plot(v, f3, color=BLUE, marker='o', ms=3)
    a.set_ylabel('−3 dB bandwidth (GHz)'); a.set_title('(b) Tuning law'); a.set_ylim(4, 11); a.tick_params(labelbottom=False)
    a = fig.add_subplot(gs[1, 1]); a.plot(v, pk, color=BLUE, marker='o', ms=3)
    a.axhline(1, color=MUTED, lw=0.8, ls=':'); a.text(0.0, 1.15, '1 dB limit', color=MUTED, fontsize=7)
    a.set_ylabel('Peaking (dB)'); a.set_xlabel('V$_{tune}$ (V)')
    fig.tight_layout(); save(fig, 'fig_vtune_tuning')


def fig_ai():
    vts = [0.0, 0.2, 0.28, 0.32, 0.36, 0.4]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for c, vt in zip(RAMP, vts):
        d = L(f'ai_z_vt{int(round(vt*1000)):03d}.csv')
        ax[0].semilogx(d['freq_Hz'] / 1e9, d['Zmag_ohm'], color=c, label=f'{vt:.2f} V')
        ax[1].semilogx(d['freq_Hz'] / 1e9, d['phase_deg'], color=c, label=f'{vt:.2f} V')
    ax[0].set_xlim(0.1, 100); ax[0].set_xlabel('Frequency (GHz)'); ax[0].set_ylabel('|Z$_{AI}$| (Ω)'); ax[0].set_title('(a) Active-inductor impedance magnitude')
    ax[0].legend(title='V$_{tune}$', fontsize=7, title_fontsize=7)
    ax[1].axhline(0, color=MUTED, lw=0.8); ax[1].set_xlim(0.1, 100); ax[1].set_xlabel('Frequency (GHz)'); ax[1].set_ylabel('Phase of Z$_{AI}$ (deg)')
    ax[1].set_title('(b) Phase: inductive above 0°, capacitive below')
    fig.tight_layout(); save(fig, 'fig_active_inductor')


def fig_noise():
    nb = L('noise_breakdown_prop.csv'); sh = Jl('noise_breakdown.json')['prop']['share_at_5GHz']
    names = {'m1': 'M1 (CG input)', 'm2': 'M2 (mirror in)', 'm3': 'M3 (mirror out)', 'mf': 'Mf (active inductor)',
             'mt': 'Mt (tuning R)', 'm3b': 'M3b (load)', 'rn': 'R$_N$', 'mbp': 'Mbp (bias)'}
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    a = ax[0]
    a.semilogx(nb['freq_Hz'] / 1e9, nb['in_total_pA_rtHz'], color=INK, lw=2, label='Total')
    for c, k in zip([BLUE, ORANGE, AQUA, YELLOW, VIOLET], ['m1', 'm2', 'm3', 'mf', 'mt']):
        a.semilogx(nb['freq_Hz'] / 1e9, nb[k], color=c, lw=1.3, label=names[k])
    a.set_xlim(0.01, 30); a.set_ylim(0, 42); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('Input-referred noise (pA/√Hz)')
    a.set_title('(a) Proposed TIA: noise by device'); a.legend(fontsize=7, ncol=2, loc='upper center')
    a = ax[1]
    items = sorted(sh.items(), key=lambda kv: kv[1])
    items = [(k, v) for k, v in items if v > 0.003]
    a.barh([names.get(k, k) for k, _ in items], [100 * v for _, v in items], color=BLUE, height=0.6)
    for i, (_, v) in enumerate(items):
        a.text(100 * v + 0.6, i, f'{100*v:.0f} %', va='center', fontsize=7, color=INK)
    a.set_xlabel('Share of output noise power at 5 GHz (%)'); a.set_title('(b) Noise budget at 5 GHz'); a.grid(axis='y', visible=False)
    fig.tight_layout(); save(fig, 'fig_noise')


def fig_model():
    fig, ax = plt.subplots(figsize=(3.6, 2.9))
    for c, vt in zip([RAMP[0], RAMP[2], RAMP[4]], [0.0, 0.2, 0.28]):
        d = L(f'model_vt{int(round(vt*1000)):03d}.csv')
        ax.semilogx(d['freq_Hz'] / 1e9, d['Zt_sim_dBohm'], color=c, label=f'SPICE, {vt:.2f} V')
        ax.semilogx(d['freq_Hz'][::6] / 1e9, d['Zt_model_dBohm'][::6], 'o', color=c, ms=3, mfc='white')
    ax.plot([], [], 'o', color=MUTED, ms=3, mfc='white', label='4-node model')
    ax.set_xlim(0.1, 40); ax.set_ylim(40, 58); ax.set_xlabel('Frequency (GHz)'); ax.set_ylabel('Transimpedance (dBΩ)')
    ax.legend(fontsize=7, loc='lower left'); fig.tight_layout(); save(fig, 'fig_model_vs_spice')


def fig_loop():
    g, l = L('loopgain_global.csv'), L('loopgain_local.csv')
    fig, ax = plt.subplots(2, 1, figsize=(3.6, 3.6), sharex=True)
    ax[0].semilogx(g['freq_Hz'] / 1e9, g['T_dB'], color=BLUE, label='Global loop (through Mf)')
    ax[0].semilogx(l['freq_Hz'] / 1e9, l['T_dB'], color=ORANGE, ls='--', label='Local loop (M1–M2)')
    ax[0].axhline(0, color=MUTED, lw=0.8); ax[0].set_ylabel('|T| (dB)'); ax[0].set_ylim(-40, 20); ax[0].legend(fontsize=7, loc='lower left')
    ax[1].semilogx(g['freq_Hz'] / 1e9, g['phase_deg'], color=BLUE); ax[1].semilogx(l['freq_Hz'] / 1e9, l['phase_deg'], color=ORANGE, ls='--')
    ax[1].axhline(-180, color=MUTED, lw=0.8, ls=':'); ax[1].set_ylabel('Phase of T (deg)'); ax[1].set_xlabel('Frequency (GHz)'); ax[1].set_xlim(0.01, 300)
    fig.tight_layout(); save(fig, 'fig_loop_gain')


def fig_pvt():
    pv = Jl('pvt.json'); rows = pv['rows']; tgt = pv['target_f3'] / 1e9
    lab = [r['case'] for r in rows]; y = np.arange(len(rows))[::-1]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    f0 = [r['nominal']['f3'] / 1e9 for r in rows]; f1 = [r['trimmed']['f3'] / 1e9 for r in rows]
    for yy, a0, a1 in zip(y, f0, f1):
        ax[0].plot([a0, a1], [yy, yy], color=GRID, lw=2, zorder=1)
    ax[0].scatter(f0, y, color=ORANGE, marker='s', s=22, label='V$_{tune}$ = 0.28 V (fixed)', zorder=2)
    ax[0].scatter(f1, y, color=BLUE, s=24, label='V$_{tune}$ trimmed', zorder=3)
    ax[0].axvline(tgt, color=MUTED, lw=0.8, ls=':'); ax[0].set_yticks(y); ax[0].set_yticklabels(lab, fontsize=7)
    ax[0].set_xlabel('−3 dB bandwidth (GHz)'); ax[0].set_title('(a) Bandwidth'); ax[0].legend(fontsize=7, loc='lower left')
    p0 = [r['nominal']['pk'] for r in rows]; p1 = [r['trimmed']['pk'] for r in rows]
    for yy, a0, a1 in zip(y, p0, p1):
        ax[1].plot([a0, a1], [yy, yy], color=GRID, lw=2, zorder=1)
    ax[1].scatter(p0, y, color=ORANGE, marker='s', s=22, zorder=2); ax[1].scatter(p1, y, color=BLUE, s=24, zorder=3)
    ax[1].set_xlabel('Peaking (dB)'); ax[1].set_title('(b) Peaking')
    fig.tight_layout(); save(fig, 'fig_pvt')


def fig_mc():
    mc = Jl('montecarlo.json'); r = mc['rows']
    a_ = lambda k: np.array([x[k] for x in r], float)
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6))
    bins = np.linspace(min(np.nanmin(a_('f3')), np.nanmin(a_('f3_t'))) / 1e9 - .2, max(np.nanmax(a_('f3')), np.nanmax(a_('f3_t'))) / 1e9 + .2, 26)
    ax[0].hist(a_('f3') / 1e9, bins=bins, color=ORANGE, alpha=0.75, label='fixed V$_{tune}$', edgecolor='white', linewidth=0.4)
    ax[0].hist(a_('f3_t') / 1e9, bins=bins, color=BLUE, alpha=0.75, label='trimmed', edgecolor='white', linewidth=0.4)
    ax[0].set_xlabel('−3 dB bandwidth (GHz)'); ax[0].set_ylabel('Samples'); ax[0].set_title('(a) Bandwidth'); ax[0].legend(fontsize=7)
    bins = np.linspace(0, max(a_('pk').max(), 1.2), 26)
    ax[1].hist(a_('pk'), bins=bins, color=ORANGE, alpha=0.75, edgecolor='white', linewidth=0.4)
    ax[1].hist(a_('pk_t'), bins=bins, color=BLUE, alpha=0.75, edgecolor='white', linewidth=0.4)
    ax[1].set_xlabel('Peaking (dB)'); ax[1].set_title('(b) Peaking')
    ax[2].hist(a_('z0db'), bins=24, color=BLUE, edgecolor='white', linewidth=0.4)
    ax[2].set_xlabel('Low-frequency gain (dBΩ)'); ax[2].set_title('(c) Gain')
    fig.tight_layout(); save(fig, 'fig_monte_carlo')


def fig_eye():
    ey = Jl('eye.json')
    panels = [('eye_base_10g.csv', 10e9, 'Baseline, 10 Gb/s', ORANGE, 0), ('eye_prop_10g.csv', 10e9, 'Proposed, 10 Gb/s', BLUE, 1),
              ('eye_base_12g5.csv', 12.5e9, 'Baseline, 12.5 Gb/s', ORANGE, 3), ('eye_prop_12g5.csv', 12.5e9, 'Proposed, 12.5 Gb/s', BLUE, 2)]
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 4.6))
    for (fn, rate, title, col, k), a in zip(panels, ax.ravel()):
        d = L(fn); ui = 1 / rate; t, v = d['time_s'], d['vout_ac_V'] * 1e3
        n = int(round(2 * ui / (t[1] - t[0])))
        for i in range(0, len(t) - n, n // 2):
            a.plot((t[i:i + n] - t[i]) / ui, v[i:i + n], color=col, lw=0.35, alpha=0.5)
        e = ey[k]
        a.set_title(f"{title}: opening {e['eye_height_V']*1e3:.1f} mV ({e['eye_height_pct']:.0f} %), width {e['eye_width_pct']:.0f} % UI", fontsize=7.5)
        a.set_xlim(0, 2); a.set_xlabel('Time (UI)'); a.set_ylabel('V$_{out}$ (mV, AC)')
    fig.tight_layout(); save(fig, 'fig_eye_diagrams')


def fig_load():
    ld = Jl('load_study.json'); se = Jl('sensitivity.json')
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7))
    cl = [r['cl_fF'] for r in ld]
    ax[0].plot(cl, [r['resistive']['f3'] / 1e9 for r in ld], color=ORANGE, ls='--', marker='s', ms=3.5, label='Resistive follower feedback')
    ax[0].plot(cl, [r['f3_best'] / 1e9 for r in ld], color=BLUE, marker='o', ms=3.5, label='Active inductor, V$_{tune}$ re-tuned')
    ax[0].set_xlabel('Load capacitance C$_L$ (fF)'); ax[0].set_ylabel('−3 dB bandwidth (GHz)'); ax[0].set_title('(a) Load'); ax[0].legend(fontsize=6.5)
    cp = [r['cpd_fF'] for r in se['cpd']]
    ax[1].plot(cp, [r['nominal']['f3'] / 1e9 for r in se['cpd']], color=ORANGE, ls='--', marker='s', ms=3.5, label='fixed V$_{tune}$')
    ax[1].plot(cp, [r['trimmed']['f3'] / 1e9 for r in se['cpd']], color=BLUE, marker='o', ms=3.5, label='re-tuned')
    ax[1].set_xlabel('Photodiode capacitance C$_{PD}$ (fF)'); ax[1].set_ylabel('−3 dB bandwidth (GHz)'); ax[1].set_title('(b) Photodiode'); ax[1].legend(fontsize=6.5)
    ax[1].set_ylim(0, 12)
    idc = [r['idc_uA'] for r in se['idc']]
    ax[2].plot(idc, [r['prop']['z0db'] for r in se['idc']], color=BLUE, marker='o', ms=3.5)
    ax[2].set_xlabel('DC input current (µA)'); ax[2].set_ylabel('Gain at 100 MHz (dBΩ)'); ax[2].set_title('(c) Input overload')
    fig.tight_layout(); save(fig, 'fig_load_pd_overload')


def fig_baseline_diag():
    b = L('ac_baseline.csv'); h5 = L('diag_H5.csv'); h6 = L('diag_H6.csv')
    dg = {r['label']: r for r in Jl('baseline_diag.json')}; sc = Jl('baseline_lfscan.json')
    ro = Jl('baseline_reopt.json'); p = L('ac_proposed.csv')
    g1, g2 = L('ac_baseline_opt_gbw.csv'), L('ac_baseline_opt_gain.csv')
    fig, ax = plt.subplots(1, 3, figsize=(7.4, 2.75))
    a = ax[0]
    a.plot(P_F, P_Z, 'o', color=INK, ms=4, mfc='white', label='Published [1] (digitised)', zorder=5)
    a.plot(b['freq_Hz'] / 1e9, 10 ** (b['Zt_dBohm'] / 20), color=ORANGE, lw=1.3, label='As drawn, 50/30 fF')
    a.plot(h5['freq_Hz'] / 1e9, 10 ** (h5['Zt_fitted_caps_dBohm'] / 20), color=VIOLET, ls='--', lw=1.3,
           label='Best fit, L$_f$ = 2.4 nH (%.1f dB rms)' % dg['H5']['rms_db'])
    a.plot(h6['freq_Hz'] / 1e9, 10 ** (h6['Zt_fitted_caps_dBohm'] / 20), color=AQUA, lw=1.6,
           label='Best fit, L$_f$ → 0 (%.1f dB rms)' % dg['H6']['rms_db'])
    a.set_xlim(0, 50); a.set_ylim(0, 450); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('|Z$_T$| (Ω)')
    a.set_title('(a) Fits to the published curve'); a.legend(fontsize=5.8, loc='upper right')
    a = ax[1]
    lf = np.array([r['lf'] for r in sc]); e = np.array([r['rms_db'] for r in sc])
    a.semilogx(lf * 1e9, e, color=BLUE, marker='o', ms=3.5)
    i = np.argmin(abs(lf - 2.4e-9)); a.plot(lf[i] * 1e9, e[i], 'o', color=ORANGE, ms=6, mfc='none', mew=1.5)
    a.annotate('stated 2.4 nH', (lf[i] * 1e9, e[i]), xytext=(-62, 4), textcoords='offset points', fontsize=6.5, color=ORANGE)
    a.set_xlabel('Feedback inductance L$_f$ (nH)'); a.set_ylabel('Best rms fit error (dB)')
    a.set_ylim(0, 4.6); a.set_title('(b) Fit error versus L$_f$')
    a = ax[2]
    for d, lab, col, ls in ((b, 'As drawn', ORANGE, ':'), (g1, 'Re-optimised, max GBW', VIOLET, '--'),
                            (g2, 'Re-optimised, gain-matched', AQUA, '-.'), (p, 'Proposed', BLUE, '-')):
        a.semilogx(d['freq_Hz'] / 1e9, d['Zt_dBohm'], color=col, ls=ls, lw=1.5, label=lab)
    a.set_xlim(0.1, 60); a.set_ylim(25, 62); a.set_xlabel('Frequency (GHz)'); a.set_ylabel('Z$_T$ (dBΩ)')
    a.set_title('(c) Fair comparison (50/30 fF)'); a.legend(fontsize=5.8, loc='lower left')
    fig.tight_layout(); save(fig, 'fig_baseline_diagnosis')


def fig_dcc():
    d = Jl('dcc_idc.json'); st_p, st_d = L('dcc_step_prop.csv'), L('dcc_step_dcc.csv')
    fig, ax = plt.subplots(2, 2, figsize=(7.2, 5.0))
    i_p = [r['idc_uA'] for r in d['prop']]; i_d = [r['idc_uA'] for r in d['dcc']]
    a = ax[0, 0]
    a.plot(i_p, [r['f3'] / 1e9 for r in d['prop']], color=ORANGE, ls='--', marker='s', ms=3, label='Without DCC')
    a.plot(i_d, [r['f3'] / 1e9 for r in d['dcc']], color=BLUE, marker='o', ms=3, label='With DCC')
    a.set_xlabel('Average photocurrent (µA)'); a.set_ylabel('−3 dB bandwidth (GHz)'); a.set_ylim(0, 16)
    a.set_title('(a) Bandwidth'); a.legend(fontsize=7)
    a2 = a.twinx(); a2.spines['right'].set_visible(True)
    a2.plot(i_p, [r['z0db'] for r in d['prop']], color=ORANGE, ls=':', lw=1.1)
    a2.plot(i_d, [r['z0db'] for r in d['dcc']], color=BLUE, ls=':', lw=1.1)
    a2.set_ylabel('Gain at 100 MHz (dBΩ), dotted', color=MUTED); a2.set_ylim(25, 75); a2.grid(False)
    a = ax[0, 1]
    a.plot(i_p, [r['imf'] * 1e6 for r in d['prop']], color=ORANGE, ls='--', marker='s', ms=3, label='I(M$_f$), without DCC')
    a.plot(i_d, [r['imf'] * 1e6 for r in d['dcc']], color=BLUE, marker='o', ms=3, label='I(M$_f$), with DCC')
    a.plot(i_d, [r['idcc'] * 1e6 for r in d['dcc']], color=AQUA, marker='^', ms=3, label='I(M$_{dc}$), cancelled')
    a.plot([0, 1000], [0, 1000], color=GRID, lw=1, zorder=0)
    a.set_xlabel('Average photocurrent (µA)'); a.set_ylabel('Current (µA)'); a.set_ylim(0, 850)
    a.set_title('(b) Follower and cancellation currents'); a.legend(fontsize=7)
    a = ax[1, 0]
    a.plot(st_p['time_s'] * 1e6, st_p['vout_V'], color=ORANGE, lw=1.3, label='Without DCC')
    a.plot(st_d['time_s'] * 1e6, st_d['vout_V'], color=BLUE, lw=1.6, label='With DCC')
    a.set_xlabel('Time (µs)'); a.set_ylabel('V$_{OUT}$ (V)'); a.set_ylim(0.3, 0.75)
    a.set_title('(c) Photocurrent step 0 → 200 µA → 0'); a.legend(fontsize=7, loc='lower right')
    a = ax[1, 1]
    for k, col in zip((0, 100, 300, 500), RAMP[1:]):
        c = L(f'ac_dcc_idc{k}.csv')
        a.semilogx(c['freq_Hz'], c['Zt_dBohm'], color=col, label=f'{k} µA')
    c = L('ac_prop_idc100.csv')
    a.semilogx(c['freq_Hz'], c['Zt_dBohm'], color=ORANGE, ls='--', lw=1.2, label='100 µA, no DCC')
    a.set_xlim(1e3, 5e10); a.set_ylim(10, 70); a.set_xlabel('Frequency (Hz)'); a.set_ylabel('Z$_T$ (dBΩ)')
    a.set_title('(d) Response with DCC'); a.legend(fontsize=6.5, loc='lower center', ncol=2)
    fig.tight_layout(); save(fig, 'fig_dcc')


ALL = [fig_baseline_diag, fig_dcc, fig_baseline, fig_compare, fig_vtune, fig_ai, fig_noise, fig_model, fig_loop, fig_pvt, fig_mc, fig_eye, fig_load]
if __name__ == '__main__':
    want = sys.argv[1:]
    for f in ALL:
        if not want or f.__name__ in want:
            try:
                f()
            except Exception as e:
                print('SKIP', f.__name__, repr(e))
