"""Collect the final designs, write all netlists, verify them with ngspice, make figures + tables."""
import os, json, re, subprocess, glob
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import lib, circuits as C, analyze as A, emit

R = lib.ROOT; RES = os.path.join(R, 'results')
# file name -> (circuit, opt-result tag, role, title)
FINAL = {
 'base_mdfrgc_robust': ('mdfrgc', '_P1.5_F2.5_robust', 'BASE PAPER (reconstructed from equations), worst-case sized', 'Abdollahi 2025 modified dual-feedback RGC with negative-RC network, re-sized for 1 V / PTM90 against 7 PVT conditions'),
 'base_mdfrgc_nominal': ('mdfrgc', '_P1.5_F2.5', 'BASE PAPER, nominal-sized', 'Abdollahi 2025 MDFRGC re-sized for the nominal corner only (higher gain, corner-sensitive)'),
 'ref_rgc_robust': ('rgc', '_P1.5_F2.5_robust', 'Reference: conventional RGC, worst-case sized', 'Conventional regulated-cascode TIA (Park-Yoo style), worst-case sized'),
 'prop_mdfrgc_trim': ('mdfrgc_t', '_P1.5_F2.5', 'PROPOSED: voltage-trimmable negative-RC TIA', 'Base-paper MDFRGC with the A2 degeneration resistor shunted by a triode NMOS (control voltage vc)'),
 'var_cmnrc_robust': ('cm_nrc_d1', '_P1.5_F2.5_robust', 'Tested variant (negative result): current-mirror + negative-RC, worst-case sized', 'RGC with PMOS current-mirror output and a negative-RC path from the mirror node'),
 'var_cmnrc_nominal': ('cm_nrc_d1', '_P1.5_F2.5', 'Tested variant, nominal-sized', 'Same, sized for the nominal corner only'),
 'var_cmrgc_robust': ('cm_rgc', '_P1.5_F2.5_robust', 'Tested variant: current-mirror RGC, worst-case sized', 'RGC with PMOS current-mirror output (no negative-RC path)'),
 'ref_shaaban_L': ('shaaban_L', '_P1.5_F2.5', 'Shaaban 2025, passive inductor (RECONSTRUCTION from abstract)', 'Current-mirror TIA, shunt feedback, passive shunt-peaking inductor - reconstruction'),
 'ref_shaaban_AN': ('shaaban_AN', '_P1.5_F2.5', 'Shaaban 2025, active inductor type 1 (RECONSTRUCTION)', 'Current-mirror TIA with NMOS source-follower active inductor - reconstruction'),
 'ref_shaaban_AP': ('shaaban_AP', '_P1.5_F2.5', 'Shaaban 2025, active inductor type 2 (RECONSTRUCTION)', 'Current-mirror TIA with PMOS gate-resistor active inductor - reconstruction'),
 'ref_pftia_earlier': ('pf_tia', '_P1.5_F2.5', 'Earlier work of this project: FVF + current mirror + follower feedback', 'PF-TIA re-sized under the same rules'),
}


def design(fn):
    cname, tag, role, title = FINAL[fn]
    x = A.load(cname, tag)
    el = C.make(cname, x, cpd=0.45e-12, cl=50e-15)
    return cname, tag, x, el


def charfile(cname, tag):
    base = os.path.join(RES, f'char_{cname}{tag if "robust" in tag else ""}.json')
    return json.load(open(base))


def main():
    designs = {}
    for fn, (cname, tag, role, title) in FINAL.items():
        _, _, x, el = design(fn)
        designs[fn] = (title, el)
    emit.emit(designs, br=3e9)
    # the proposed design gets a vc parameter and a sweep
    fn = 'prop_mdfrgc_trim'; vc = A.load('mdfrgc_t', FINAL[fn][1])['vc']
    for sub, ext in (('ngspice', '.cir'), ('ltspice', '.net')):
        p = os.path.join(R, 'netlists', sub, fn + ext); t = open(p).read()
        t = re.sub(r'(?m)^Vc vc 0 dc \S+$', f'.param vcv={vc:.4g}\nVc vc 0 dc {{vcv}}', t)
        if sub == 'ltspice':
            t = t.replace('.ac dec 40 1Meg 100G', '.ac dec 40 1Meg 100G\n;.step param vcv 0 1 0.05   ; trimming sweep: bandwidth/peaking vs control voltage')
        else:
            t = t.replace('ac dec 40 1Meg 100G', 'ac dec 40 1Meg 100G', 1)
        open(p, 'w').write(t)
    p = os.path.join(R, 'netlists', 'ltspice', fn + '.asc'); t = open(p).read()
    t = re.sub(r'(SYMATTR InstName Vc\nSYMATTR Value )\S+', r'\1{vcv}', t)
    t = t.replace('TEXT 0 ', f'TEXT 0 ', 1)
    last = max(int(m) for m in re.findall(r'(?m)^TEXT 0 (\d+)', t))
    t += f'\nTEXT 0 {last + 32} Left 2 !.param vcv={vc:.4g}\nTEXT 0 {last + 64} Left 2 ;.step param vcv 0 1 0.05   ; trimming sweep: bandwidth / peaking vs control voltage vc\n'
    open(p, 'w').write(t)
    p = os.path.join(R, 'netlists', 'ltspice', fn + '_eye.net'); t = open(p).read()
    t = re.sub(r'(?m)^Vc vc 0 dc \S+$', f'Vc vc 0 dc {vc:.4g}', t); open(p, 'w').write(t)
    for sub in ('cadence_ptm', 'cadence_gpdk'):
        p = os.path.join(R, 'netlists', sub, fn + '.scs'); t = open(p).read()
        t = re.sub(r'(?m)^Vc \(vc 0\) vsource dc=\S+ type=dc$', 'Vc (vc 0) vsource dc=vcv type=dc', t)
        t = t.replace('Vdd (vdd 0)', f'parameters vcv={vc:.4g}\nVdd (vdd 0)', 1)
        t += '// trimming sweep of the control voltage: bandwidth and peaking vs vc\nswVc sweep param=vcv start=0 stop=1 step=0.05 {\n    acVc ac start=1M stop=100G dec=40\n}\n'
        open(p, 'w').write(t)
    # verification: the emitted ngspice netlists reproduce the optimiser's numbers
    ver = {}
    for fn in FINAL:
        p = os.path.join(R, 'netlists', 'ngspice')
        out = subprocess.run(['ngspice', '-b', f'{fn}.cir'], capture_output=True, text=True, cwd=p).stdout
        d = lib.vals(out)
        ch = charfile(FINAL[fn][0], FINAL[fn][1])['nom']
        ver[fn] = dict(file_f3=d.get('f3db'), file_zt0=d.get('zt0'),
                       opt_f3=ch['f3'], opt_zt=ch['z0db'])
        print(fn, ver[fn])
    json.dump(ver, open(os.path.join(RES, 'netlist_verification.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
