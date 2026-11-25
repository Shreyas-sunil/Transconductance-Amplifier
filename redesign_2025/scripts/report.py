"""Figures and results tables from results/*.json."""
import os, json
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import lib, build

R = lib.ROOT; RES = os.path.join(R, 'results'); FIG = os.path.join(RES, 'figures'); os.makedirs(FIG, exist_ok=True)
F = build.FINAL
CH = {fn: build.charfile(F[fn][0], F[fn][1]) for fn in F}
COL = {'base_mdfrgc_robust': '#1b6ca8', 'base_mdfrgc_nominal': '#7fb2e5', 'ref_rgc_robust': '#777777',
       'prop_mdfrgc_trim': '#c1272d', 'var_cmnrc_robust': '#e08a00', 'var_cmnrc_nominal': '#f2c46d',
       'var_cmrgc_robust': '#8a5ea8', 'ref_shaaban_L': '#2e8b57', 'ref_shaaban_AN': '#6fbf8d', 'ref_shaaban_AP': '#a8d8b9',
       'ref_pftia_earlier': '#444444'}
plt.rcParams.update({'font.size': 9, 'axes.grid': True, 'grid.alpha': .3})


def fig_ac():
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for fn in F:
        d = np.loadtxt(os.path.join(R, 'netlists', 'ngspice', fn + '_ac.txt'))
        ax[0].semilogx(d[:, 0] / 1e9, d[:, 1], color=COL[fn], label=fn, lw=1.4)
    ax[0].set_xlim(0.01, 30); ax[0].set_ylim(30, 78); ax[0].set_xlabel('f (GHz)'); ax[0].set_ylabel('Zt (dBohm)')
    ax[0].set_title('Transimpedance, nominal (TT, 35 C, 1 V, Cpd 0.45 pF)'); ax[0].legend(fontsize=6, ncol=2)
    for fn in F:
        d = np.loadtxt(os.path.join(R, 'netlists', 'ngspice', fn + '_noise.txt'))
        ax[1].semilogx(d[:, 0] / 1e9, d[:, 1] * 1e12, color=COL[fn], lw=1.4)
    ax[1].set_xlim(0.01, 10); ax[1].set_ylim(0, 60); ax[1].set_xlabel('f (GHz)'); ax[1].set_ylabel('input-referred noise (pA/rtHz)')
    ax[1].set_title('Input-referred current noise')
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'ac_noise.png'), dpi=160); plt.close(fig)


def fig_pvt():
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    names = list(F)
    for i, fn in enumerate(names):
        pv = [r for r in CH[fn]['pvt'] if 'f3' in r]
        f = np.array([r['f3'] for r in pv]) / 1e9; pk = np.array([r['pk'] for r in pv])
        ax[0].scatter([i] * len(f), f, s=10, color=COL[fn]); ax[1].scatter([i] * len(pk), pk, s=10, color=COL[fn])
    for a, t in zip(ax, ('-3 dB bandwidth over 45 PVT conditions (GHz)', 'peaking over 45 PVT conditions (dB)')):
        a.set_xticks(range(len(names))); a.set_xticklabels(names, rotation=70, ha='right', fontsize=7); a.set_title(t)
    ax[1].axhline(1, color='k', lw=.8, ls='--'); ax[1].set_yscale('symlog', linthresh=1)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'pvt.png'), dpi=160); plt.close(fig)


def fig_trim():
    T = json.load(open(os.path.join(RES, 'trim_mdfrgc_t.json')))
    import analyze as A, circuits as C
    x0 = T['x']
    vcs = np.round(np.arange(0, 1.0001, 0.05), 3)
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    f3, pk, zt = [], [], []
    for vc in vcs:
        r = A.m('mdfrgc_t', dict(x0, vc=float(vc)), noise=False)
        f3.append(r['f3'] / 1e9); pk.append(r['pk']); zt.append(r['z0db'])
    ax[0].plot(vcs, f3, 'o-', color='#c1272d'); ax[0].set_xlabel('vc (V)'); ax[0].set_ylabel('-3 dB bandwidth (GHz)')
    a2 = ax[0].twinx(); a2.plot(vcs, pk, 's--', color='k', ms=3); a2.set_ylabel('peaking (dB)'); a2.set_yscale('symlog', linthresh=1)
    ax[0].set_title('Nominal tuning curve (gain stays 67.6-67.9 dBohm)')
    rows = T['rows']; idx = np.arange(len(rows))
    ax[1].plot(idx, [r['fixed']['f3'] / 1e9 for r in rows], 'o', color='#999999', label=f"fixed vc = {x0['vc']:.2f} V")
    ax[1].plot(idx, [r['trim']['f3'] / 1e9 for r in rows], 'o', color='#c1272d', label='vc trimmed per condition')
    ax[1].set_xlabel('PVT condition #'); ax[1].set_ylabel('bandwidth (GHz)'); ax[1].legend(fontsize=7); ax[1].set_title('Bandwidth over 45 conditions')
    ax[2].plot(idx, [r['fixed']['pk'] for r in rows], 'o', color='#999999'); ax[2].plot(idx, [r['trim']['pk'] for r in rows], 'o', color='#c1272d')
    ax[2].axhline(1, color='k', ls='--', lw=.8); ax[2].set_yscale('symlog', linthresh=1)
    ax[2].set_xlabel('PVT condition #'); ax[2].set_ylabel('peaking (dB)'); ax[2].set_title('Peaking over 45 conditions')
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'trim.png'), dpi=160); plt.close(fig)


def fig_eye():
    sel = ['base_mdfrgc_robust', 'prop_mdfrgc_trim', 'ref_rgc_robust']
    import emit
    bits, _ = emit.prbs7_file(3e9, 20e-6, 127)
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.4)); ui = 1 / 3e9
    for a, fn in zip(ax, sel):
        tag = F[fn][1] if 'robust' in F[fn][1] else ''
        tt, v = np.load(os.path.join(RES, f'eye_{F[fn][0]}{tag}.npy'))
        k = tt > 10 * ui
        ph = (tt[k] % ui) / ui; seg = np.floor(tt[k] / ui)
        for s in np.unique(seg):
            m = seg == s
            a.plot(ph[m], v[k][m] * 1e3, color=COL[fn], lw=.3, alpha=.5)
        a.set_title(f"{fn}\nopening {CH[fn]['eye']['eye_mV']:.1f} of {CH[fn]['eye']['swing_mV']:.1f} mV", fontsize=8)
        a.set_xlabel('UI'); a.set_ylabel('Vout (mV)')
    fig.suptitle('3 Gb/s NRZ PRBS7, 20 uA pk-pk photocurrent (folded, not clock-recovered)', fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'eye.png'), dpi=160); plt.close(fig)


def dip(fn):
    """In-band dip: depth of the first local minimum of Zt below the 10 MHz gain (0 for a monotonic roll-off), dB."""
    d = np.loadtxt(os.path.join(R, 'netlists', 'ngspice', fn + '_ac.txt')); f, z = d[:, 0], d[:, 1]
    z0 = np.interp(np.log10(1e7), np.log10(f), z)
    m = np.where(f > 1e7)[0]; zz = z[m]
    dz = np.diff(zz)
    for i in range(1, len(dz)):
        if dz[i - 1] < -1e-4 and dz[i] > 1e-4 and zz[i] < z0 - 0.05:
            return float(z0 - zz[i])
    return 0.0


def tables():
    L = ['| Design | Gain dBΩ | BW GHz | Power mW | Noise (avg over BW) pA/√Hz | Gain×BW THz·Ω | Worst peaking 45 PVT dB | BW range 45 PVT GHz | MC σ(BW) GHz, samples >1 dB | Eye opening mV | In-band dip (local min below DC gain), dB |', '|' + '---|' * 11]
    for fn in F:
        c = CH[fn]; n = c['nom']; pv = [r for r in c['pvt'] if 'f3' in r]; mc = [r for r in c['mc'] if 'f3' in r]
        L.append(f"| `{fn}` | {n['z0db']:.1f} | {n['f3']/1e9:.2f} | {n['pwr']*1e3:.2f} | {n['in_avg']:.1f} | {10**(n['z0db']/20)*n['f3']/1e12:.2f} | "
                 f"{max(r['pk'] for r in pv):.2f} | {min(r['f3'] for r in pv)/1e9:.2f} to {max(r['f3'] for r in pv)/1e9:.2f} | "
                 f"{np.std([r['f3'] for r in mc])/1e9:.2f}, {sum(r['pk']>1 for r in mc)}/{len(mc)} | {c['eye']['eye_mV']:.1f} of {c['eye']['swing_mV']:.1f} | {dip(fn):.1f} |")
    L2 = ['| Design | Cpd 0.1 pF | 0.25 pF | 0.45 pF | 0.7 pF | 1.0 pF |', '|---|---|---|---|---|---|']
    for fn in F:
        cp = CH[fn]['cpd']
        L2.append(f'| `{fn}` | ' + ' | '.join(f"{r['f3']/1e9:.2f} GHz / {r['pk']:.1f} dB" for r in cp) + ' |')
    T = json.load(open(os.path.join(RES, 'trim_mdfrgc_t.json'))); rows = T['rows']
    fx = [r['fixed'] for r in rows]; tr = [r['trim'] for r in rows]
    L3 = ['| prop_mdfrgc_trim, 45 conditions | Bandwidth GHz | Worst peaking dB | Gain dBΩ |', '|---|---|---|---|',
          f"| vc fixed at {T['x']['vc']:.2f} V | {min(r['f3'] for r in fx)/1e9:.2f} to {max(r['f3'] for r in fx)/1e9:.2f} | {max(r['pk'] for r in fx):.2f} | {min(r['z0db'] for r in fx):.1f} to {max(r['z0db'] for r in fx):.1f} |",
          f"| vc trimmed per condition (0.05 V grid) | {min(r['f3'] for r in tr)/1e9:.2f} to {max(r['f3'] for r in tr)/1e9:.2f} | {max(r['pk'] for r in tr):.2f} | {min(r['z0db'] for r in tr):.1f} to {max(r['z0db'] for r in tr):.1f} |"]
    open(os.path.join(RES, 'tables.md'), 'w').write('## Main table\n\n' + '\n'.join(L) + '\n\n## Bandwidth / peaking vs photodiode capacitance (nominal corner)\n\n' + '\n'.join(L2) + '\n\n## Trimming\n\n' + '\n'.join(L3) + '\n')
    print('\n'.join(L)); print('\n'.join(L2)); print('\n'.join(L3))


if __name__ == '__main__':
    fig_ac(); fig_pvt(); fig_trim(); fig_eye(); tables()
