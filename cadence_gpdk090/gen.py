def u(x): return f"{x:g}u"
def mos(cell,name,x,y,ori,W,L):
    ad=W*0.58; pd=2*(W+0.58)
    p=[("w",u(W)),("fw",u(W)),("l",f"{int(L*1000)}n"),("fingers","1"),("m","1"),
       ("ad",f"{ad:.4g}p"),("as",f"{ad:.4g}p"),("pd",f"{pd:.4g}u"),("ps",f"{pd:.4g}u")]
    ps=" ".join(f'list("{k}" "string" "{v}")' for k,v in p)
    return f'tI(cv "gpdk090" "{cell}" "{name}" {x} {y} "{ori}" list({ps}))'
def ana(cell,name,x,y,ori,params):
    ps=" ".join(f'list("{k}" "string" "{v}")' for k,v in params)
    return f'tI(cv "analogLib" "{cell}" "{name}" {x} {y} "{ori}" list({ps}))'
def W(*pts): return "tW(cv list("+" ".join(f"list({a} {b})" for a,b in pts)+"))"
def L(name,*pts): return f'tL(cv "{name}" list('+" ".join(f"list({a} {b})" for a,b in pts)+"))"
def G(x,y): return f"tG(cv {x} {y})"
def V(x,y): return f"tV(cv {x} {y})"

hdr = r'''
procedure(tI(cv lib cell name x y ori params)
  let((m) m=dbOpenCellViewByType(lib cell "symbol")
    unless(m error("no master %s %s" lib cell))
    dbCreateParamInst(cv m name list(x y) ori 1 params)))
procedure(tW(cv pts)
  let((i) i=0
    while(i < length(pts)-1
      schCreateWire(cv "draw" "full" list(nth(i pts) nth(i+1 pts)) 0.0625 0.0625 0.0)
      i=i+1)))
procedure(tL(cv name pts)
  let((w p1 p2) w=car(schCreateWire(cv "draw" "full" pts 0.0625 0.0625 0.0))
    p1=car(pts) p2=cadr(pts)
    schCreateWireLabel(cv w list((xCoord(p1)+xCoord(p2))/2.0 (yCoord(p1)+yCoord(p2))/2.0+0.03)
       name "lowerCenter" "R0" "stick" 0.0625 nil)))
procedure(tG(cv x y) dbCreateInst(cv dbOpenCellViewByType("analogLib" "gnd" "symbol") nil list(x y) "R0"))
procedure(tV(cv x y) dbCreateInst(cv dbOpenCellViewByType("analogLib" "vdd" "symbol") nil list(x y) "R0"))
procedure(tNote(cv x y txt h)
  dbCreateLabel(cv list("text" "drawing") list(x y) txt "lowerLeft" "R0" "stick" h))
'''

# ---------- base 2020 TIA, as published (Fig.1) ----------
b=[]
b+= [mos("pmos1v","M2b",0.5,2.5,"R0",0.9,0.1)]
b+= [W((0.75,2.6875),(0.75,2.75)), W((0.75,2.75),(0.75,2.875)), V(0.75,2.875)]
b+= [W((0.5,2.5),(0.125,2.5),(0.125,2.875)), V(0.125,2.875)]   # G -> vdd (as published)
b+= [W((0.75,2.5),(1.0,2.5),(1.0,2.75),(0.75,2.75))]
b+= [mos("nmos1v","M1",0.5,1.75,"R0",5,0.1)]
b+= [W((0.75,1.9375),(0.75,2.125)), W((0.75,2.125),(0.75,2.3125))]   # n
b+= [W((0.5,1.75),(0.125,1.75),(0.125,1.9375)), V(0.125,1.9375)]     # M1 gate -> vdd (as published)
b+= [W((0.75,1.75),(1.0,1.75)), G(1.0,1.75)]
b+= [W((0.75,1.5625),(0.75,1.25)), W((0.75,1.25),(0.75,0.9375))]     # in
b+= [mos("nmos1v","M2",1.0,0.75,"MY",5,0.1)]
b+= [G(0.75,0.5625), W((0.75,0.75),(0.5,0.75)), G(0.5,0.75)]
b+= [L("n",(0.75,2.125),(1.5,2.125)), W((1.5,2.125),(1.5,0.75)), W((1.5,0.75),(1.0,0.75)), W((1.5,0.75),(2.5,0.75))]
b+= [mos("nmos1v","M3",2.5,0.75,"R0",5,0.1)]
b+= [G(2.75,0.5625), W((2.75,0.75),(3.0,0.75)), G(3.0,0.75)]
b+= [mos("pmos1v","M3b",2.5,2.5,"R0",5,0.1)]
b+= [V(2.75,2.6875), W((2.75,2.5),(3.0,2.5),(3.0,2.875)), V(3.0,2.875)]
b+= [L("g3b",(2.5,2.5),(2.0,2.5)), W((2.0,2.5),(2.0,2.25))]
b+= [ana("vdc","Vg3b",2.0,2.25,"R0",[("vdc","0")]), G(2.0,1.875)]
b+= [W((2.75,2.3125),(2.75,1.625)), W((2.75,1.625),(2.75,0.9375))]
b+= [L("out",(2.75,1.625),(3.75,1.625)), W((3.75,1.625),(3.75,1.25)), W((3.75,1.625),(4.5,1.625))]
b+= [ana("cap","Cout",3.75,1.25,"R0",[("c","30f")]), G(3.75,0.875)]
b+= [ana("ind","Lf",1.5,3.375,"R90",[("l","2.4n")])]
b+= [W((4.5,1.625),(4.5,3.375),(1.875,3.375))]
b+= [W((1.5,3.375),(-0.375,3.375),(-0.375,1.25))]
b+= [L("in",(-0.375,1.25),(0.75,1.25)), W((-0.375,1.25),(-1.0,1.25))]
b+= [ana("cap","Cpd",-1.0,1.25,"R0",[("c","50f")]), G(-1.0,0.875)]
b+= [W((-1.0,1.25),(-1.75,1.25))]
b+= [ana("idc","Iin",-1.75,0.875,"R180",[("idc","0"),("acm","1")]), G(-1.75,0.875)]
b+= [ana("vdc","Vdd",-2.75,1.25,"R0",[("vdc","1")]), W((-2.75,1.25),(-2.75,1.5)), V(-2.75,1.5), G(-2.75,0.875)]
b+= ['tNote(cv -2.75 4.0 "2020 current-mirror TIA as published (Alsheikhjader 2020, Fig. 1) - GPDK090, VDD = 1 V" 0.12)',
     'tNote(cv -2.75 3.8 "M1 and M2b gates tied to VDD as drawn in the paper. L = 100 nm (GPDK090 minimum; paper used 90 nm)." 0.08)',
     'tNote(cv -2.75 3.65 "Iin: AC 1 A photodiode current, Cpd = 50 fF, CL = 30 fF, Lf = 2.4 nH ideal spiral" 0.08)']

# ---------- proposed TIA v1 ----------
p=[]
p+= [ana("res","Rn",0.75,2.6875,"R0",[("r","5k")]), W((0.75,2.6875),(0.75,2.875)), V(0.75,2.875)]
p+= [mos("nmos1v","M1",0.5,1.75,"R0",4.5,0.1)]
p+= [W((0.75,1.9375),(0.75,2.125)), W((0.75,2.125),(0.75,2.3125))]
p+= [L("vb1",(0.5,1.75),(0.125,1.75))]
p+= [W((0.75,1.75),(1.0,1.75)), G(1.0,1.75)]
p+= [W((0.75,1.5625),(0.75,1.25)), W((0.75,1.25),(0.75,0.9375))]
p+= [mos("nmos1v","M2",1.0,0.75,"MY",3.5,0.1)]
p+= [G(0.75,0.5625), W((0.75,0.75),(0.5,0.75)), G(0.5,0.75)]
p+= [L("n",(0.75,2.125),(1.5,2.125)), W((1.5,2.125),(1.5,0.75)), W((1.5,0.75),(1.0,0.75)), W((1.5,0.75),(2.5,0.75))]
p+= [mos("nmos1v","M3",2.5,0.75,"R0",7,0.1)]
p+= [G(2.75,0.5625), W((2.75,0.75),(3.0,0.75)), G(3.0,0.75)]
p+= [mos("pmos1v","M3b",2.5,2.5,"R0",28,0.18)]
p+= [V(2.75,2.6875), W((2.75,2.5),(3.0,2.5),(3.0,2.875)), V(3.0,2.875)]
p+= [L("vbp",(2.5,2.5),(2.0,2.5))]
p+= [W((2.75,2.3125),(2.75,1.625)), W((2.75,1.625),(2.75,0.9375))]
p+= [L("out",(2.75,1.625),(3.75,1.625)), W((3.75,1.625),(3.75,1.25)), W((3.75,1.625),(4.5,1.625))]
p+= [ana("cap","Cout",3.75,1.25,"R0",[("c","30f")]), G(3.75,0.875)]
# tunable active inductor: Mf, Mt, Ca
p+= [mos("nmos1v","Mf",-0.625,2.5,"R0",3.5,0.1)]
p+= [V(-0.375,2.6875), W((-0.375,2.5),(-0.125,2.5)), G(-0.125,2.5)]
p+= [W((-0.375,2.3125),(-0.375,1.75)), W((-0.375,1.75),(-0.375,1.25))]
p+= [L("g",(-0.625,2.5),(-1.0,2.5)), W((-1.0,2.5),(-1.0,2.125)), W((-1.0,2.5),(-1.0,3.375))]
p+= [ana("cap","Ca",-1.0,2.125,"R0",[("c","30f")]), W((-1.0,1.75),(-0.375,1.75))]
p+= [mos("pmos1v","Mt",2.0,3.625,"R270",12,0.1)]
p+= [L("vt",(2.0,3.625),(2.0,3.875))]
p+= [W((-1.0,3.375),(1.8125,3.375))]
p+= [W((2.1875,3.375),(2.375,3.375)), W((2.375,3.375),(4.5,3.375),(4.5,1.625))]
p+= [W((2.0,3.375),(2.0,3.125),(2.375,3.125),(2.375,3.375))]
p+= [L("in",(-0.375,1.25),(0.75,1.25)), W((-0.375,1.25),(-1.0,1.25))]
p+= [ana("cap","Cpd",-1.0,1.25,"R0",[("c","50f")]), G(-1.0,0.875)]
p+= [W((-1.0,1.25),(-1.75,1.25))]
p+= [ana("idc","Iin",-1.75,0.875,"R180",[("idc","0"),("acm","1")]), G(-1.75,0.875)]
# bias generator
p+= [mos("pmos1v","Mbp",-4.5,2.5,"R0",2,0.18), W((-4.25,2.6875),(-4.25,2.75)), W((-4.25,2.75),(-4.25,2.875)), V(-4.25,2.875)]
p+= [W((-4.25,2.5),(-4.0,2.5),(-4.0,2.75),(-4.25,2.75))]
p+= [W((-4.25,2.3125),(-4.25,2.125)), W((-4.25,2.125),(-4.25,2.0)), W((-4.25,2.125),(-4.75,2.125),(-4.75,2.5),(-4.5,2.5))]
p+= [L("vbp",(-4.25,2.0),(-3.5,2.0)), W((-3.5,2.0),(-3.5,2.5),(-3.0,2.5))]
p+= [W((-4.25,2.0),(-4.25,1.625))]
p+= [ana("idc","Iref",-4.25,1.625,"R0",[("idc","50u")]), G(-4.25,1.25)]
p+= [mos("pmos1v","Mbr",-3.0,2.5,"R0",2,0.18), W((-2.75,2.6875),(-2.75,2.75)), W((-2.75,2.75),(-2.75,2.875)), V(-2.75,2.875)]
p+= [W((-2.75,2.5),(-2.5,2.5),(-2.5,2.75),(-2.75,2.75))]
p+= [W((-2.75,2.3125),(-2.75,2.125)), W((-2.75,2.125),(-2.75,2.0)), W((-2.75,2.0),(-2.75,1.875))]
p+= [mos("nmos1v","Mbn",-3.0,1.6875,"R0",0.4,0.1)]
p+= [W((-2.75,1.6875),(-2.5,1.6875)), G(-2.5,1.6875)]
p+= [W((-3.0,1.6875),(-3.25,1.6875),(-3.25,2.125),(-2.75,2.125))]
p+= [L("vb1",(-2.75,2.0),(-2.0,2.0))]
p+= [ana("cap","Cb",-2.0,2.0,"R0",[("c","2p")]), G(-2.0,1.625)]
p+= [L("vr",(-2.75,1.5),(-2.75,1.25))]
p+= [ana("res","Rb",-2.75,1.25,"R0",[("r","4.2k")]), G(-2.75,0.875)]
p+= [ana("vdc","Vdd",-5.5,1.625,"R0",[("vdc","1")]), W((-5.5,1.625),(-5.5,1.875)), V(-5.5,1.875), G(-5.5,1.25)]
p+= [ana("vdc","Vtune",-6.25,1.625,"R0",[("vdc","vtn")]), L("vt",(-6.25,1.625),(-6.25,2.0)), G(-6.25,1.25)]
p+= ['tNote(cv -6.25 4.3 "Proposed TIA v1: FVF input + current mirror + voltage-tuned gyrator-C feedback (Mf, Mt, Ca) - GPDK090, VDD = 1 V" 0.12)',
     'tNote(cv -6.25 4.1 "Sizes = paper Table I (v1). L = 100 nm where the paper used 90 nm (GPDK090 minimum); 180 nm devices unchanged." 0.08)',
     'tNote(cv -6.25 3.95 "Bias generator (left) drives the core through labelled nets vbp and vb1; Vtune drives net vt." 0.08)',
     'tNote(cv -5.0 3.0 "BIAS GENERATOR" 0.1)', 'tNote(cv -1.25 3.55 "TUNABLE ACTIVE INDUCTOR (Mf, Mt, Ca)" 0.1)',
     'tNote(cv 0.0 0.2 "FVF INPUT STAGE + MIRROR" 0.1)']

def cell(name, body):
    s=f'procedure(tiaBuild_{name}(lib)\n let((cv)\n  cv=dbOpenCellViewByType(lib "{name}" "schematic" "schematic" "w")\n'
    s+="".join("  "+x+"\n" for x in body)
    s+=f'  schCheck(cv)\n  printf("BUILT {name}: errors/warnings %L\\n" schCheck(cv))\n  dbSave(cv)\n  dbClose(cv)\n  t))\n'
    return s
with open("build_gpdk090.il","w") as f:
    f.write(";; Builds GPDK090 schematics of the 2020 base TIA and the proposed TIA v1 in a library.\n")
    f.write(hdr); f.write(cell("TIA_2020_base_gpdk090",b)); f.write(cell("TIA_proposed_v1_gpdk090",p))
    f.write('tiaBuild_TIA_2020_base_gpdk090("TIA_Proj")\ntiaBuild_TIA_proposed_v1_gpdk090("TIA_Proj")\n')
