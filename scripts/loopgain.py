"""Loop gain by Middlebrook's double-injection method (valid for bilateral loops)."""
import os, numpy as np
import sim

PROBE = ['Vam {a} lgj dc 0', 'Vz lgj {b} dc 0 ac {vac}', 'Iz 0 lgj dc 0 ac {iac}']


def middlebrook(make_net, a, b, fstart='10meg', fstop='300g', ppd=40):
    """make_net(extra_lines, control) -> netlist. a = driving-side node, b = receiving side."""
    res = {}
    for tag, vac, iac in [('v', 1, 0), ('i', 0, 1)]:
        f = os.path.join(sim.TMP, f'lg_{tag}_{next(sim._cnt)}.txt')
        ctl = f'ac dec {ppd} {fstart} {fstop}\nwrdata {f} v({a}) v({b}) i(vam) i(vz)'
        sim.run(make_net([p.format(a=a, b=b, vac=vac, iac=iac) for p in PROBE], ctl))
        d = np.loadtxt(f)
        res[tag] = (d[:, 0], d[:, 1] + 1j * d[:, 2], d[:, 3] + 1j * d[:, 4],
                    d[:, 5] + 1j * d[:, 6], d[:, 7] + 1j * d[:, 8])
    f, va, vb, _, _ = res['v']
    _, _, _, iam, iz = res['i']
    Tv = -va / vb
    Ti = -iam / iz
    T = (Tv * Ti - 1) / (Tv + Ti + 2)
    return f, T


def margins(f, T):
    mag = 20 * np.log10(abs(T)); ph = np.unwrap(np.angle(T)) * 180 / np.pi
    out = dict(t0_db=mag[0])
    k = np.where((mag[:-1] > 0) & (mag[1:] <= 0))[0]
    if len(k):
        k = k[0]
        fu = 10 ** np.interp(0, [mag[k + 1], mag[k]], [np.log10(f[k + 1]), np.log10(f[k])])
        out['fu'] = fu; out['pm'] = 180 + np.interp(np.log10(fu), np.log10(f), ph)
    else:
        out['fu'] = np.nan; out['pm'] = np.nan
    k = np.where((ph[:-1] > -180) & (ph[1:] <= -180))[0]
    if len(k):
        k = k[0]
        f180 = 10 ** np.interp(-180, [ph[k + 1], ph[k]], [np.log10(f[k + 1]), np.log10(f[k])])
        out['gm_db'] = -np.interp(np.log10(f180), np.log10(f), mag)
    else:
        out['gm_db'] = np.inf
    return out


def tia_loop(P=None, which='global', **kw):
    """Loop gains of the proposed TIA.
    'global': broken between VOUT and the active-inductor network (source/bulk of Mt).
    'local' : flipped-voltage-follower loop M1-M2, broken at the gate of M2."""
    def rep(elems):
        elems = [(e[:5] + (None,)) if e[1] == 'Iin' else e for e in elems]   # no input drive
        if which == 'global':
            return [(e[:4] + ('fb', 'fb') + e[6:]) if e[1] == 'Mt' else e for e in elems]
        return [(e[:3] + ('g2',) + e[4:]) if e[1] == 'M2' else e for e in elems]
    def mk(extra, ctl):
        return sim.build('prop', P, control=ctl, extra_lines=extra, replace=rep, **kw)
    return middlebrook(mk, *(('out', 'fb') if which == 'global' else ('n', 'g2')))


