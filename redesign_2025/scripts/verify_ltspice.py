"""Check the LTspice files without LTspice.
 (a) .asc: rebuild the netlist from the schematic geometry (symbol pins, wires, flags) and simulate it with ngspice;
 (b) .net: simulate the shipped netlist text with ngspice (meas/backanno lines removed);
 (c) _eye.net: run the transient and compare the swing with the optimiser-side eye run.
Both are compared with the verified .cir results.  This proves connectivity, values and syntax shape;
it does NOT prove that LTspice itself accepts the BSIM4 card or converges."""
import os, re, json, subprocess, tempfile
import numpy as np
import lib, build, emit

R = lib.ROOT; LT = os.path.join(R, 'netlists', 'ltspice'); NG = os.path.join(R, 'netlists', 'ngspice')


def run_ac(netlist_lines, cwd):
    f = os.path.join(tempfile.mkdtemp(), 'v.cir')
    out = os.path.join(os.path.dirname(f), 'ac.txt')
    open(f, 'w').write('\n'.join(netlist_lines + ['.control', 'set noaskquit', 'set wr_singlescale', 'op', 'print i(vdd)',
                                                  'ac dec 40 1Meg 100G', f'wrdata {out} vdb(out)', '.endc', '.end']) + '\n')
    o = subprocess.run(['ngspice', '-b', f], capture_output=True, text=True, cwd=cwd).stdout
    a = np.loadtxt(out); d = lib.vals(o)
    return float(np.interp(np.log10(1e7), np.log10(a[:, 0]), a[:, 1])), lib.f3db(a[:, 0], a[:, 1], 1e7), -d['i(vdd)'] * 1e3


def asc_to_spice(path):
    wires, flags, syms, cur = [], {}, [], None
    for ln in open(path):
        t = ln.split(None, 4)
        if not t: continue
        if t[0] == 'WIRE': wires.append(tuple(map(int, t[1:5])))
        elif t[0] == 'FLAG': flags[(int(t[1]), int(t[2]))] = t[3].strip()
        elif t[0] == 'SYMBOL': cur = dict(sym=t[1], x=int(t[2]), y=int(t[3])); syms.append(cur)
        elif t[0] == 'SYMATTR': cur[t[1]] = ln.split(None, 2)[2].strip()
    directives = [m.group(1).strip() for m in (re.match(r'TEXT \S+ \S+ \S+ \S+ !(.*)', ln) for ln in open(path)) if m]
    lines, seen = [], {}
    for s in syms:
        pins = {}
        for pn, (dx, dy, sx, sy) in emit.PINS[s['sym']].items():
            p = (s['x'] + dx, s['y'] + dy)
            ends = [w[2:] for w in wires if w[:2] == p] + [w[:2] for w in wires if w[2:] == p]
            nets = {flags[e] for e in ends if e in flags}
            assert len(nets) == 1, (s['InstName'], pn, nets)
            pins[pn] = nets.pop()
        n, v = s['InstName'], s['Value']
        if s['sym'].startswith('tia_'):
            lines.append(f"{n} {pins['D']} {pins['G']} {pins['S']} {pins['B']} {v} {s['Value2']}")
        elif s['sym'] in ('res', 'ind', 'cap'):
            lines.append(f"{n} {pins['A']} {pins['B']} {v}")
        elif s['sym'] == 'voltage':
            lines.append(f"{n} {pins['+']} {pins['-']} dc {v}")
        elif s['sym'] == 'current':
            lines.append(f"{n} {pins['+']} {pins['-']} dc " + v.replace(' AC ', ' ac '))
    # no two different nets share a wire endpoint
    pts = {}
    for (x1, y1, x2, y2) in wires:
        for p in ((x1, y1), (x2, y2)): pts[p] = pts.get(p, 0) + 1
    assert all(v == 1 for v in pts.values()), 'overlapping wire ends in ' + path
    keep = [d for d in directives if d.startswith(('.include', '.temp', '.param'))]
    return keep + lines


def main():
    res = {}
    for fn in build.FINAL:
        ref = json.load(open(os.path.join(R, 'results', 'netlist_verification.json')))[fn]
        z0, f3 = ref['file_zt0'], ref['file_f3']
        out = {}
        ok = True
        # (a) asc
        a = run_ac(asc_to_spice(os.path.join(LT, fn + '.asc')), LT)
        out['asc'] = a
        # (b) net
        txt = [l for l in open(os.path.join(LT, fn + '.net')).read().splitlines()
               if not l.lower().startswith(('.meas', '.backanno', '.ac', '.end')) and not l.startswith(';')]
        b = run_ac(txt, LT); out['net'] = b
        for k, v in (('asc', a), ('net', b)):
            good = abs(v[0] - z0) < 0.05 and abs(v[1] / f3 - 1) < 0.01
            out[k + '_ok'] = bool(good); ok &= good
        # (c) eye
        lines = [l for l in open(os.path.join(LT, fn + '_eye.net')).read().splitlines() if not l.lower().startswith(('.backanno', '.end', '.tran'))]
        ui = 1 / 3e9
        f = os.path.join(tempfile.mkdtemp(), 'e.cir'); o = os.path.join(os.path.dirname(f), 'e.txt')
        open(f, 'w').write('\n'.join(lines + [f'.tran {ui/40:.4g} {254*ui:.5g}', '.control', 'set noaskquit', 'set wr_singlescale', 'run',
                                              f'wrdata {o} v(out)', '.endc', '.end']) + '\n')
        subprocess.run(['ngspice', '-b', f], capture_output=True, text=True, cwd=LT)
        tt, v = np.loadtxt(o).T
        k = tt > 10 * ui
        swing = (v[k].max() - v[k].min()) * 1e3
        cname, tag = build.FINAL[fn][0], build.FINAL[fn][1]
        ch = build.charfile(cname, tag)['eye']['swing_mV']
        out['eye_swing_mV'] = float(swing); out['eye_swing_ref_mV'] = float(ch)
        out['eye_ok'] = bool(abs(swing - ch) / ch < 0.1); ok &= out['eye_ok']
        out['all_ok'] = bool(ok); res[fn] = out
        print(fn, 'OK' if ok else 'MISMATCH', {k: (round(x, 3) if isinstance(x, float) else x) for k, x in out.items() if k.endswith(('ok', 'mV'))})
    json.dump(res, open(os.path.join(R, 'results', 'ltspice_verification.json'), 'w'), indent=1)
    assert all(r['all_ok'] for r in res.values()), 'LTspice-file mismatch'


if __name__ == '__main__':
    main()
