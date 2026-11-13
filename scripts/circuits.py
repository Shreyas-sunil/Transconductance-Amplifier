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


# DC-cancellation (DCC) loop added to the proposed TIA.  What collapses under a large
# average photocurrent is the follower current I(Mf): every microampere of photocurrent
# is taken from Mf, until the feedback path turns off.  I(Mf) sets V_GS(Mf) = V_OUT - V_IN.
# A replica follower Mr (half of Mf) driven from V_OUT and biased by I_th/2 gives
# V_R = V_OUT - V_GS(I_th).  A PMOS-input OTA compares V_R with V_IN (both through RC
# taps that isolate the signal path above ~8 MHz) and integrates the difference on Cint;
# its output drives Mdc, which sinks current from the input.  The loop therefore holds
# I(Mf) at I_th whatever the average photocurrent.  I_th (about 105 uA) is set slightly
# above the nominal dark value of I(Mf) (99 uA), so the loop is engaged in the dark as
# well; this makes the held current insensitive to mismatch in the core (see dcc_study).
DCC_P = dict(rtap='100k', ctap='0.2p', cint='2p', vtune=0.26)   # Vtune re-centred: the loop holds I(Mf) slightly above its dark value
DCC_SZ = {'Mq': (0.8, 180), 'Mnq': (2, 1440), 'Mns': (5.7, 1440), 'Mr': (1.75, 90),
          'Mtp': (0.4, 720), 'Ma': (4, 720), 'Mb': (4, 720), 'Mna': (1, 1440), 'Mnb': (1, 1440),
          'Mdc': (6, 180)}


def proposed_dcc(sz=None):
    """Proposed TIA with the DC-cancellation loop."""
    s = dict(PROP_SZ); s.update(DCC_SZ); s.update(sz or {})
    el = list(proposed(sz))
    i = [k for k, e in enumerate(el) if e[1] == 'Cpd'][0]
    el[i:i] = [
        # reference current from the bias generator (I_th/2 in Mns)
        ('M', 'Mq', 'nq', 'vbp', 'vdd', 'vdd', 'p') + s['Mq'],
        ('M', 'Mnq', 'nq', 'nq', '0', '0', 'n') + s['Mnq'],
        # RC taps on V_OUT and V_IN
        ('R', 'Rt1', 'out', 'to', '{rtap}'),
        ('C', 'Ct1', 'to', '0', '{ctap}'),
        ('R', 'Rt2', 'in', 'ti', '{rtap}'),
        ('C', 'Ct2', 'ti', '0', '{ctap}'),
        # replica follower: V_R = V_OUT - V_GS(I_th)
        ('M', 'Mr', 'vdd', 'to', 'vrep', '0', 'n') + s['Mr'],
        ('M', 'Mns', 'vrep', 'nq', '0', '0', 'n') + s['Mns'],
        # PMOS-input OTA integrating on Cint
        ('M', 'Mtp', 'tp', 'vbp', 'vdd', 'vdd', 'p') + s['Mtp'],
        ('M', 'Ma', 'oa', 'ti', 'tp', 'vdd', 'p') + s['Ma'],
        ('M', 'Mb', 'vx', 'vrep', 'tp', 'vdd', 'p') + s['Mb'],
        ('M', 'Mna', 'oa', 'oa', '0', '0', 'n') + s['Mna'],
        ('M', 'Mnb', 'vx', 'oa', '0', '0', 'n') + s['Mnb'],
        ('C', 'Cint', 'vx', '0', '{cint}'),
        # cancellation device
        ('M', 'Mdc', 'in', 'vx', '0', '0', 'n') + s['Mdc'],
    ]
    return el


# Re-optimised baselines (fair comparison, results/data/baseline_reopt.json).  Same
# topology as Fig. 1 of the 2020 paper, but the M2b gate gets its own bias, the spiral has
# a series loss Rsl, and widths, both PMOS gate biases, Lf and Rsl were chosen by a
# differential-evolution search under the constraints used for the proposed TIA
# (C_PD = 50 fF, C_L = 30 fF, <= 1 dB peaking, <= 1.2 mW).
BASE_REOPT = {
    # maximum gain-bandwidth product
    'gbw': dict(sz={'M1': (1.8, 90), 'M2': (12.37, 90), 'M3': (1.69, 90), 'M3b': (4.34, 90), 'M2b': (5.35, 90)},
                P=dict(vg3b=0.596, lf='1.251n'), vg2b=0.591, rsl=42.8),
    # maximum bandwidth at the proposed TIA's gain (>= 53.87 dBohm)
    'gain': dict(sz={'M1': (1.05, 90), 'M2': (7.22, 90), 'M3': (1.68, 90), 'M3b': (1.73, 90), 'M2b': (4.64, 90)},
                 P=dict(vg3b=0.527, lf='5.036n'), vg2b=0.781, rsl=43.0),
}


def baseline_reopt(kind):
    """Element list of a re-optimised baseline (kind = 'gbw' or 'gain')."""
    r = BASE_REOPT[kind]
    out = [('V', 'Vg2b', 'g2b', '0', '{vg2b}', None)]
    for e in baseline(r['sz']):
        if e[0] == 'M' and e[1] == 'M2b':
            e = e[:3] + ('g2b',) + e[4:]
        if e[0] == 'L':
            out += [('L', 'Lf', 'out', 'xl', e[4]), ('R', 'Rsl', 'xl', 'in', '{rsl}')]
            continue
        out.append(e)
    return out


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
