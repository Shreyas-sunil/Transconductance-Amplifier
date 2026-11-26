"""Build LTspice schematics (.asc) and netlists (.net) for every circuit of P1-P3, verify topology, and run ngspice twins."""
import os, re, json, shutil, subprocess, tempfile
import projA, projB, projC, projA2 as PA, tB5
from emit import resolve
exec(open('tB2.py').read().split("print('---sweep')")[0].replace("for a,R in []:","for a,R in []:\n    pass\nif 0:"))
OUT='lt'
NEW=dict(bias='tr',Rp='260k',mt=2,Ln='4u',Lp='4u',Wn='8u',Wp='8u')
# ---------------------------------------------------------------- circuits
def circuits():
    C={}
    projA.W='10u'; projA.WC='40u'
    P1={'A1_conventional_cascode_mirror':projA.ckt('cnv',vcn=0.42),'A2_plain_fvf_mirror':projA.ckt('fvf',vcn=0.42),
        'A3_base_fvf_mirror_reconstruction':projA.ckt('hp',vcn=0.42),'A4_v1_single_booster_mirror':projA.ckt('prop',vcn=0.42,wp='0.25u',lp='1u')}
    P1['A5_enhanced_core_cascoded_boosters']=PA.core('casc')
    P1['A6_proposed_dem_mirror_phase1']=PA.dem(PA.core('casc'),'1')
    P1['A3_base_with_dem_chopped']=PA.dem(PA.core('base'),'chop')
    P1['A6_proposed_dem_mirror_chopped']=PA.dem(PA.core('casc'),'chop')
    C['P1_current_mirror']={k:(v,['A_dc','A_ac','A_out'] if 'chopped' not in k else ['A_chop']) for k,v in P1.items()}
    P2={'B1_conventional_ota':projB.core('cnv'),'B2_base_rlcmfb_Rs3k':projB.core('rlc'),'B3_base_rlcmfb_Rs5k':projB.core('rlc',Rs='5k'),
        'B4_v1_ppf_rlcmfb':core2('ppf',extra=ppf(0.2,'100k'),Rs='5k')}
    import tB3; P2['B5_proposed_nmos_xc_ptat']=projB.core('tnf',extra=tB5.nxc(**NEW),Rs='5k')
    C['P2_rlcmfb_single_stage_ota']={k:(v,['B_ac','B_tr']) for k,v in P2.items()}
    b=projC.ckt()
    P3={'C1_base_reconstruction':b,'C2_proposed_dyn_qfg_W0p3':b+"Mpd g12 n3 x 0 nmos90 W=0.3u L=0.18u\n",'C3_proposed_dyn_qfg_W0p5':b+"Mpd g12 n3 x 0 nmos90 W=0.5u L=0.18u\n"}
    C['P3_bulk_driven_classAB_two_stage_ota']={k:(v,['C_ac','C_tr']) for k,v in P3.items()}
    return C
# ---------------------------------------------------------------- testbenches: (extra elements, LTspice directives, ngspice control)
TB={
 'A_dc':(["Iin 0 inn dc 10u ac 1"],
   [".dc Iin 0 20u 0.25u",".meas DC iout_10u FIND -I(Vo) AT=10u",".meas DC err_10u_pct PARAM 100*(iout_10u-10u)/10u",
    ".meas DC vin_10u FIND V(inn) AT=10u",".meas DC iout_2u FIND -I(Vo) AT=2u",".meas DC err_2u_pct PARAM 100*(iout_2u-2u)/2u"],
   """dc Iin 0 20u 0.25u
let iout=-i(Vo)
meas dc iout_10u find iout at=10u
meas dc vin_10u find v(inn) at=10u
meas dc iout_2u find iout at=2u""",
   "DC transfer: plot -I(Vo) and V(inn) against Iin; error in %% = 100*(-I(Vo)-Iin)/Iin."),
 'A_ac':(["Iin 0 inn dc 10u ac 1"],
   [".ac dec 40 1k 10G",".meas AC rin_1k FIND mag(V(inn)) AT=1k",".meas AC bw_3dB WHEN mag(I(Vo))=0.7071 FALL=1"],
   """ac dec 40 1k 10G
let rin=mag(v(inn))
let gi=mag(i(Vo))
meas ac rin_1k find rin at=1k
meas ac bw_3dB when gi=0.7071 fall=1""",
   "AC at Iin = 10 uA: input impedance = V(inn) for the 1 A AC source; current gain = I(Vo)."),
 'A_out':(["Iin 0 inn dc 10u ac 1"],
   [".dc Vo 0 1 5m",".meas DC iout_0p5 FIND -I(Vo) AT=0.5",".meas DC gout DERIV I(Vo) AT=0.5",".meas DC rout_ohm PARAM 1/abs(gout)"],
   """dc Vo 0 1 5m
let iout=-i(Vo)
meas dc iout_0p5 find iout at=0.5
meas dc gout deriv i(Vo) at=0.5""",
   "Output characteristic at Iin = 10 uA: plot -I(Vo) against Vo. Rout from the slope at 0.5 V (for a cleaner number use .ac on Vo)."),
 'A_chop':(["Iin 0 inn dc 10u"],
   [".tran 0 20u 0 5n uic",".meas TRAN iout_avg AVG -I(Vo) FROM=8u TO=20u",".meas TRAN err_avg_pct PARAM 100*(iout_avg-10u)/10u",
    ".meas TRAN vin_avg AVG V(inn) FROM=8u TO=20u"],
   """tran 5n 20u 0 5n uic
let iout=-i(Vo)
meas tran iout_avg avg iout from=8u to=20u
meas tran vin_avg avg v(inn) from=8u to=20u""",
   "Chopped (DEM) transient, 500 kHz clock: the averaged output current is the result; plot -I(Vo)."),
 'B_ac':(["Rf out inn 100Meg","Cf inn 0 1","Vin inp 0 dc 0 ac 1"],
   [".ac dec 50 1 10G",".meas AC a0 FIND mag(V(out)) AT=10",".meas AC ugf WHEN mag(V(out))=1",".meas AC v_at_ugf FIND V(out) AT=ugf"],
   """ac dec 50 1 10G
let g=mag(v(out))
let ph=180*cph(v(out))/pi
meas ac a0 find g at=10
meas ac ugf when g=1
meas ac ph_ugf find ph at=ugf""",
   "Open loop (RF = 100 MOhm, CF = 1 F set the DC point). Phase margin = 180 + phase of v_at_ugf (printed in the log as (dB, deg))."),
 'B_tr':(["Vin inp 0 dc 0 pulse(-0.2 0.2 20n 1n 1n 399n 800n)","Vsh inn out 0"],
   [".tran 0 900n 0 0.2n",".meas TRAN t_r20 WHEN V(oL)=-0.12 RISE=1",".meas TRAN t_r80 WHEN V(oL)=0.12 RISE=1",
    ".meas TRAN sr_rise_V_per_us PARAM 0.24/(t_r80-t_r20)/1e6",".meas TRAN t_f80 WHEN V(oL)=0.12 FALL=1",
    ".meas TRAN t_f20 WHEN V(oL)=-0.12 FALL=1",".meas TRAN sr_fall_V_per_us PARAM -0.24/(t_f20-t_f80)/1e6"],
   """tran 0.2n 900n
meas tran t_r20 when v(oL)=-0.12 rise=1
meas tran t_r80 when v(oL)=0.12 rise=1
meas tran t_f80 when v(oL)=0.12 fall=1
meas tran t_f20 when v(oL)=-0.12 fall=1""",
   "Unity-gain follower, +/-0.2 V step, CL = 2 pF behind Rs. Slew = 20-80 % slope of V(oL) (the load capacitor)."),
 'C_ac':(["Rf out inn 1G","Cf inn 0 10","Vin inp 0 dc 0.3 ac 1"],
   [".ac dec 40 0.1 100Meg",".meas AC a0 FIND mag(V(out)) AT=1",".meas AC ugf WHEN mag(V(out))=1",".meas AC v_at_ugf FIND V(out) AT=ugf"],
   """ac dec 40 0.1 100Meg
let g=mag(v(out))
let ph=180*cph(v(out))/pi
meas ac a0 find g at=1
meas ac ugf when g=1
meas ac ph_ugf find ph at=ugf""",
   "Open loop (RF = 1 GOhm, CF = 10 F set the DC point, inputs at 0.3 V). Phase margin = 180 + phase of v_at_ugf."),
 'C_tr':(["Vin inp 0 dc 0.1 pulse(0.1 0.5 2u 10n 10n 40u 80u)","Vsh inn out 0"],
   [".tran 0 82u 0 20n",".meas TRAN t_r20 WHEN V(out)=0.18 RISE=1",".meas TRAN t_r80 WHEN V(out)=0.42 RISE=1",
    ".meas TRAN sr_rise_V_per_us PARAM 0.24/(t_r80-t_r20)/1e6",".meas TRAN t_f80 WHEN V(out)=0.42 FALL=1",
    ".meas TRAN t_f20 WHEN V(out)=0.18 FALL=1",".meas TRAN sr_fall_V_per_us PARAM -0.24/(t_f20-t_f80)/1e6"],
   """tran 20n 82u
meas tran t_r20 when v(out)=0.18 rise=1
meas tran t_r80 when v(out)=0.42 rise=1
meas tran t_f80 when v(out)=0.42 fall=1
meas tran t_f20 when v(out)=0.18 fall=1""",
   "Unity-gain follower, 0.1 -> 0.5 V step, CL = 150 pF. Slew = 20-80 % slope of V(out)."),
}
# ---------------------------------------------------------------- parsing
def elements(core, tb_add):
    lines=[l for l in resolve(core) if not l.lstrip().startswith('*')]+tb_add
    el=[]
    for l in lines:
        t=l.split(); k=t[0][0].upper()
        if k=='M':
            d,g,s,b,mod=t[1:6]; el.append(('M',t[0],dict(D=d,G=g,S=s,B=b),mod,' '.join(t[6:])))
        elif k in 'RC': el.append((k,t[0],dict(A=t[1],B=t[2]),t[3],None))
        elif k in 'VI':
            a=' '.join(t[3:]); m=re.search(r'pulse\(([^)]*)\)',a,re.I)
            if m: val='PULSE('+m.group(1)+')'
            else:
                val=t[4] if t[3].lower()=='dc' else t[3]
                acm=re.search(r'\bac\s+([-+\d.]+)',a,re.I)
                if acm and float(acm.group(1))!=0: val+=f' AC {acm.group(1)}'
            el.append((k,t[0],{'+':t[1],'-':t[2]},val,None))
        else: raise ValueError(l)
    return el
# symbol pins: (dx,dy,stubx,stuby) in placed coordinates; nmos4 R0, pmos4 M180 (source on top), as in the user's own LTspice files
PINS={'nmos4':{'D':(48,0,0,-32),'G':(0,80,-32,0),'S':(48,96,0,32),'B':(48,48,32,0)},
      'pmos4':{'D':(48,0,0,32),'G':(0,-80,-32,0),'S':(48,-96,0,-32),'B':(48,-48,32,0)},
      'res':{'A':(16,16,0,-32),'B':(16,96,0,32)},'cap':{'A':(16,0,0,-32),'B':(16,64,0,32)},
      'voltage':{'+':(0,16,0,-32),'-':(0,96,0,32)},'current':{'+':(0,0,0,-32),'-':(0,80,0,32)}}
ORIENT={'nmos4':'R0','pmos4':'M180','res':'R0','cap':'R0','voltage':'R0','current':'R0'}
def sym_of(e):
    if e[0]=='M': return 'nmos4' if e[3]=='nmos90' else 'pmos4'
    return {'R':'res','C':'cap','V':'voltage','I':'current'}[e[0]]
def asc(name, el, tb, title):
    L=['Version 4','SHEET 1 3200 2400']; W=[]; F=[]; S=[]
    groups=[[e for e in el if e[0]=='M'],[e for e in el if e[0] in 'RC'],[e for e in el if e[0] in 'VI']]
    y0=0
    for gi,g in enumerate(groups):
        for i,e in enumerate(g):
            sym=sym_of(e); x=(i%8)*352; y=y0+(i//8)*352+(128 if sym=='pmos4' else 0)
            for pn,net in e[2].items():
                dx,dy,sx,sy=PINS[sym][pn]; x1,y1=x+dx,y+dy
                W.append(f'WIRE {x1} {y1} {x1+sx} {y1+sy}'); F.append(f'FLAG {x1+sx} {y1+sy} {net}')
            S+= [f'SYMBOL {sym} {x} {y} {ORIENT[sym]}',f'SYMATTR InstName {e[1]}',f'SYMATTR Value {e[3]}']
            if e[0]=='M' and e[4]: S.append(f'SYMATTR Value2 {e[4]}')
        if g: y0+=((len(g)-1)//8+1)*352+64
    L+=W+F+S
    ty=y0+64
    texts=[f';{title}',';Nets are joined by their labels (same name = same net). Open in LTspice and press Run.',f';{TB[tb][3]}',
           '!.include ptm90.lib']+['!'+d for d in TB[tb][1]]
    for t in texts: L.append(f'TEXT 0 {ty} Left 2 {t}'); ty+=40
    return '\n'.join(L)+'\n'
def asc_check(path, el):
    wires=[]; flags={}; syms=[]; cur=None
    for ln in open(path):
        t=ln.split()
        if not t: continue
        if t[0]=='WIRE': wires.append(tuple(map(int,t[1:5])))
        elif t[0]=='FLAG': flags[(int(t[1]),int(t[2]))]=t[3]
        elif t[0]=='SYMBOL': cur=[t[1],int(t[2]),int(t[3]),None]; syms.append(cur)
        elif t[0]=='SYMATTR' and t[1]=='InstName': cur[3]=t[2]
    got={}
    for sym,x,y,nm in syms:
        got[nm]={}
        for pn,(dx,dy,sx,sy) in PINS[sym].items():
            p=(x+dx,y+dy); ends=[w[2:] for w in wires if w[:2]==p]
            nets={flags[e] for e in ends if e in flags}; assert len(nets)==1,(path,nm,pn,nets); got[nm][pn]=nets.pop()
    want={e[1]:e[2] for e in el}
    assert got==want, path
    pts={}
    for w in wires:
        for p in (w[:2],w[2:]): pts[p]=pts.get(p,0)+1
    assert all(v==1 for v in pts.values()), 'overlap '+path
def net_text(el,tb,title):
    L=[f'* {title}','* LTspice netlist (PTM 90 nm). Open in LTspice (File > Open, all files) and Run.',f'* {TB[tb][3]}','.include ptm90.lib']
    for e in el:
        n=' '.join(e[2][p] for p in (['D','G','S','B'] if e[0]=='M' else (['A','B'] if e[0] in 'RC' else ['+','-'])))
        L.append(f'{e[1]} {n} {e[3]}'+(f' {e[4]}' if e[0]=='M' and e[4] else ''))
    return '\n'.join(L+TB[tb][1]+['.backanno','.end',''])
def ng_twin(el,tb):
    txt=net_text(el,tb,'twin').split('\n')
    body=[l for l in txt if l and not l.startswith(('.meas','.ac','.dc','.tran','.backanno','.end'))]
    return '\n'.join(body)+f"\n.control\nset noaskquit\n{TB[tb][2]}\n.endc\n.end\n"
def run_ng(net):
    d=tempfile.mkdtemp(); shutil.copy('ptm90.lib',d); f=os.path.join(d,'t.cir'); open(f,'w').write(net)
    o=subprocess.run(['ngspice','-b',f],capture_output=True,text=True,cwd=d,timeout=900).stdout
    return {m.group(1).lower():float(m.group(2)) for m in re.finditer(r'^\s*(\w+)\s*=\s*([-+0-9.eE]+)',o,re.M)}
if __name__=='__main__':
    shutil.rmtree(OUT,ignore_errors=True); ref={}
    for proj,cs in circuits().items():
        os.makedirs(f'{OUT}/{proj}',exist_ok=True); shutil.copy('ptm90.lib',f'{OUT}/{proj}/ptm90.lib'); ref[proj]={}
        for name,(core,tbs) in cs.items():
            for tb in tbs:
                el=elements(core,TB[tb][0]); fn=f'{name}_{tb}'; title=f'{name}, testbench {tb}'
                open(f'{OUT}/{proj}/{fn}.asc','w').write(asc(fn,el,tb,title)); asc_check(f'{OUT}/{proj}/{fn}.asc',el)
                open(f'{OUT}/{proj}/{fn}.net','w').write(net_text(el,tb,title))
                r=run_ng(ng_twin(el,tb)); ref[proj][fn]=r; print(fn,{k:'%.4g'%v for k,v in r.items()},flush=True)
    json.dump(ref,open(f'{OUT}/ngspice_reference.json','w'),indent=1)
