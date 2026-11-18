# Same-gain re-optimised 2020 baseline in GPDK090 (sizes from the LTspice/PTM re-optimisation, L = 100 nm).
exec(open("gen.py").read())
def sub(key, new):
    i = [k for k, s in enumerate(b2) if key in s]
    assert len(i) == 1, (key, i)
    b2[i[0]] = new
b2 = list(b)
sub('"M2b"', mos("pmos1v","M2b",0.5,2.5,"R0",4.64,0.1))
sub('"M1" ',  mos("nmos1v","M1",0.5,1.75,"R0",1.05,0.1))
sub('"M2" ',  mos("nmos1v","M2",1.0,0.75,"MY",7.22,0.1))
sub('"M3" ',  mos("nmos1v","M3",2.5,0.75,"R0",1.68,0.1))
sub('"M3b"',  mos("pmos1v","M3b",2.5,2.5,"R0",1.73,0.1))
sub('"Vg3b"', ana("vdc","Vg3b",2.0,2.25,"R0",[("vdc","0.527")]))
sub('"Lf"',   ana("ind","Lf",1.5,3.375,"R90",[("l","5.036n")]))
sub(W((0.5,2.5),(0.125,2.5),(0.125,2.875)),
    "\n  ".join([L("g2b",(0.5,2.5),(0.0,2.5)), W((0.0,2.5),(-0.25,2.5),(-0.25,2.25)),
                 ana("vdc","Vg2b",-0.25,2.25,"R0",[("vdc","0.781")]), G(-0.25,1.875)]))
b2.remove(V(0.125,2.875))
sub(W((1.5,3.375),(-0.375,3.375),(-0.375,1.25)),
    "\n  ".join([ana("res","Rsl",0.75,3.375,"R90",[("r","43")]), W((1.125,3.375),(1.5,3.375)),
                 W((0.75,3.375),(-0.375,3.375),(-0.375,1.25))]))
b2 = [s for s in b2 if "tNote" not in s]
b2 += ['tNote(cv -2.75 4.0 "2020 TIA topology re-optimised for the proposed gain (same-gain baseline) - GPDK090, VDD = 1 V" 0.12)',
       'tNote(cv -2.75 3.8 "Sizes from the LTspice/PTM re-optimisation; L = 100 nm. M2b gate on Vg2b, Rsl = 43 ohm in series with Lf = 5.036 nH." 0.08)']
name = "TIA_2020_regain_gpdk090"
with open("build_regain.il", "w") as f:
    f.write(hdr); f.write(cell(name, b2)); f.write(f'tiaBuild_{name}("TIA_Proj")\n')
