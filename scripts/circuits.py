"""Circuit definitions (single source of truth) for the baseline and proposed TIAs.

Every netlist in netlists/ (ngspice, LTspice, Spectre, SKILL) is emitted from the
element lists defined here, so all tools simulate the same circuit.
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, 'models', 'ptm90.lib')

# ---- default parameters ------------------------------------------------------
BASE_P = dict(vdd=1.0, cpd='50f', cout='30f', lf='2.4n', vg3b=0.0, temp=35)
PROP_P = dict(vdd=1.0, cpd='50f', cout='30f', iref='50u', vtune=0.28,
              rn='5k', rb='4.2k', ca='30f', cb='2p', temp=35)
# device sizes: name -> (W in um, L in nm)
BASE_SZ = {'M1': (5, 90), 'M2': (5, 90), 'M3': (5, 90), 'M2b': (0.9, 90), 'M3b': (5, 90)}
PROP_SZ = {'M1': (4.5, 90), 'M2': (3.5, 90), 'M3': (7, 90),
           'M3b': (28, 180), 'Mbp': (2, 180), 'Mbr': (2, 180), 'Mbn': (0.4, 90),
           'Mf': (3.5, 90), 'Mt': (12, 90)}


def baseline(sz=None):
    """Alsheikhjader 2020, Fig. 1, as drawn: gates of M1 and M2b tied to VDD."""
    s = dict(BASE_SZ); s.update(sz or {})
    return [
        ('V', 'Vdd', 'vdd', '0', '{vdd}', None),
        ('V', 'Vg3b', 'g3b', '0', '{vg3b}', None),
        ('M', 'M2b', 'n', 'vdd', 'vdd', 'vdd', 'p') + s['M2b'],
        ('M', 'M1', 'n', 'vdd', 'in', '0', 'n') + s['M1'],
        ('M', 'M2', 'in', 'n', '0', '0', 'n') + s['M2'],
        ('M', 'M3', 'out', 'n', '0', '0', 'n') + s['M3'],
        ('M', 'M3b', 'out', 'g3b', 'vdd', 'vdd', 'p') + s['M3b'],
        ('L', 'Lf', 'out', 'in', '{lf}'),
        ('C', 'Cpd', 'in', '0', '{cpd}'),
        ('C', 'Cout', 'out', '0', '{cout}'),
        ('I', 'Iin', '0', 'in', '0', '1'),
    ]


def proposed(sz=None):
    """Proposed TIA: FVF/common-gate input, current mirror, and a tunable
    source-follower active inductor (Mf, Mt, Ca) from VOUT back to the input."""
    s = dict(PROP_SZ); s.update(sz or {})
    return [
        ('V', 'Vdd', 'vdd', '0', '{vdd}', None),
        ('V', 'Vtune', 'vt', '0', '{vtune}', None),
        # bias generator
        ('I', 'Iref', 'vbp', '0', '{iref}', None),
        ('M', 'Mbp', 'vbp', 'vbp', 'vdd', 'vdd', 'p') + s['Mbp'],
        ('M', 'Mbr', 'vb1', 'vbp', 'vdd', 'vdd', 'p') + s['Mbr'],
        ('M', 'Mbn', 'vb1', 'vb1', 'vr', '0', 'n') + s['Mbn'],
        ('R', 'Rb', 'vr', '0', '{rb}'),
        ('C', 'Cb', 'vb1', '0', '{cb}'),
        # signal path
        ('R', 'Rn', 'vdd', 'n', '{rn}'),
        ('M', 'M1', 'n', 'vb1', 'in', '0', 'n') + s['M1'],
        ('M', 'M2', 'in', 'n', '0', '0', 'n') + s['M2'],
        ('M', 'M3', 'out', 'n', '0', '0', 'n') + s['M3'],
        ('M', 'M3b', 'out', 'vbp', 'vdd', 'vdd', 'p') + s['M3b'],
        # tunable active-inductor feedback
        ('M', 'Mf', 'vdd', 'g', 'in', '0', 'n') + s['Mf'],
        ('M', 'Mt', 'g', 'vt', 'out', 'out', 'p') + s['Mt'],
        ('C', 'Ca', 'g', 'in', '{ca}'),
        # source / loads
        ('C', 'Cpd', 'in', '0', '{cpd}'),
        ('C', 'Cout', 'out', '0', '{cout}'),
        ('I', 'Iin', '0', 'in', '0', '1'),
    ]


def mos_geom(w_um):
    """Source/drain junction geometry assumed for every device (0.2 um diffusion)."""
    ad = w_um * 0.2          # pm^2 (um * um)
    pd = 2 * w_um + 0.4      # um
    return ad, pd


def spice_lines(elems, extra=None, rscale=1.0, cscale=1.0):
    """Emit SPICE element lines (ngspice / LTspice dialect)."""
    extra = extra or {}
    out = []
    for e in elems:
        k, name = e[0], e[1]
        if k == 'M':
            _, _, d, g, s_, b, typ, w, l = e
            ad, pd = mos_geom(w)
            line = (f"{name} {d} {g} {s_} {b} {'nmos90' if typ == 'n' else 'pmos90'} "
                    f"W={w:g}u L={l:g}n AD={ad:g}p AS={ad:g}p PD={pd:g}u PS={pd:g}u")
            if name in extra:
                line += ' ' + extra[name]
        elif k == 'R':
            v = e[4] if rscale == 1.0 else '{%s*%g}' % (e[4].strip('{}'), rscale)
            line = f"{name} {e[2]} {e[3]} {v}"
        elif k == 'C':
            v = e[4]
            if cscale != 1.0 and name == 'Ca':
                v = '{%s*%g}' % (e[4].strip('{}'), cscale)
            line = f"{name} {e[2]} {e[3]} {v}"
        elif k == 'L':
            line = f"{name} {e[2]} {e[3]} {e[4]}"
        elif k == 'V':
            line = f"{name} {e[2]} {e[3]} dc {e[4]}"
        elif k == 'I':
            line = f"{name} {e[2]} {e[3]} dc {e[4]}" + (f" ac {e[5]}" if e[5] else '')
        out.append(line)
    return out


def param_line(P):
    return '.param ' + ' '.join(f'{k}={v}' for k, v in P.items() if k != 'temp')
