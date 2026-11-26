import json, math, os
R=json.load(open('lt/ngspice_reference.json'))
def fmt(fn,r):
    tb=fn.rsplit('_',2); tb='_'.join(fn.split('_')[-2:])
    if tb=='A_dc': return f"error at 10 µA {100*(r['iout_10u']-10e-6)/10e-6:+.4f} %, at 2 µA {100*(r['iout_2u']-2e-6)/2e-6:+.4f} %, V(inn) at 10 µA {r['vin_10u']:.3f} V"
    if tb=='A_ac': return f"Rin at 1 kHz {r['rin_1k']:.4g} Ω, −3 dB bandwidth {r.get('bw_3db',float('nan'))/1e6:.0f} MHz"
    if tb=='A_out': return f"-I(Vo) at 0.5 V {r['iout_0p5']*1e6:.4f} µA (Rout: see README)"
    if tb=='A_chop': return f"averaged error {100*(r['iout_avg']-10e-6)/10e-6:+.4f} %, V(inn) {r['vin_avg']:.3f} V"
    if tb in('B_ac','C_ac'): return f"A0 {20*math.log10(r['a0']):.1f} dB, UGF {r['ugf']/1e6:.3g} MHz, PM {180+r['ph_ugf']:.1f}°"
    if tb=='B_tr': return f"SR+ {0.24/(r['t_r80']-r['t_r20'])/1e6:.1f} V/µs, SR− {-0.24/(r['t_f20']-r['t_f80'])/1e6:.1f} V/µs"
    if tb=='C_tr': return f"SR+ {0.24/(r['t_r80']-r['t_r20'])/1e6:.3g} V/µs, SR− {-0.24/(r['t_f20']-r['t_f80'])/1e6:.3g} V/µs"
TBD={'A_dc':'DC sweep of Iin, 0–20 µA','A_ac':'AC, input impedance and current-gain bandwidth','A_out':'DC sweep of the output voltage Vo, 0–1 V',
     'A_chop':'Transient with the 500 kHz DEM clock, averaged output','B_ac':'Open-loop AC','B_tr':'Unity-gain follower, ±0.2 V step',
     'C_ac':'Open-loop AC','C_tr':'Unity-gain follower, 0.1→0.5 V step'}
for proj,rs in R.items():
    L=[f"# LTspice simulations ({proj})","",
"Every circuit of this project as a ready-to-run LTspice schematic (`.asc`) and the same deck as a netlist (`.net`). Both use",
"`ptm90.lib` (PTM 90 nm BSIM4, the same file as your TIA LTspice runs) from this folder.","",
"**How to run:** keep the whole folder together, open an `.asc`, press Run. The `.meas` results appear in the error log",
"(View > SPICE Error Log). Each file holds one analysis; one circuit has one file per testbench.","",
"**How the schematics are drawn:** each device is placed on a grid and its pins carry net labels. Pins with the same label",
"are connected. This keeps the files exact copies of the simulated netlists. Move parts and draw wires if you want a",
"textbook-style drawing for the paper; the labels keep it connected while you do.","",
"**Checks done here:** the connectivity of every `.asc` was read back from its geometry and compared with the netlist, and",
"every deck was simulated in ngspice with the same model. The right-hand column is that ngspice result. LTspice itself",
"could not be run in the cloud, so expect small differences (solver tolerances) and tell me if a file does not open or run.","",
"| File | Testbench | ngspice reference result |","|---|---|---|"]
    for fn,r in rs.items():
        tb='_'.join(fn.split('_')[-2:])
        try: v=fmt(fn,r)
        except Exception as e: v='see README'
        L.append(f"| `{fn}.asc` / `.net` | {TBD[tb]} | {v} |")
    if proj.startswith('P1'):
        L+=["","Notes: the `_A_ac` deck gives Rin and bandwidth; for the chopped DEM decks the averaged current is the result and the",
            "output shows short glitches at each clock edge. Rout values in the README come from an `.ac` drive on Vo with tight",
            "tolerances; the `_A_out` slope (`rout_ohm`) is coarser."]
    if proj.startswith('P3'):
        L+=["","Note: C3 shows the large-signal limit cycle described in the README (its falling edge comes right after the rise)."]
    open(f'lt/{proj}/README_LTspice.md','w').write('\n'.join(L)+'\n')
print('ok')
