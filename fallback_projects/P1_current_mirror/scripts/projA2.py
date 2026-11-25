"""Project 1, version 2: enhanced FVF mirror (cascoded boosters) + dynamic element matching (DEM) of the mirror pair."""
import os, numpy as np, projA
from sim import run, meas
ORIG=projA.ckt
W='10u'; L='360n'
def core(kind, WC=None, wa=None, vcb=0.45, k=10, cc='0.3p', vcn=0.42):
    """kind: 'base' = reconstruction of the paper (CS boosters), 'casc' = cascoded CS boosters."""
    projA.W=W; projA.WC=WC or ('40u' if kind=='base' else '10u')
    wa=wa or ('2u' if kind=='base' else '8u')
    n=ORIG('hp',ib=2e-6,k=k,cc=cc,wa=wa,vcn=vcn)
    if kind=='casc':
        n=n.replace(f"MA1 G1 x 0 0 nmos90 W={wa}", f"MA1 a1 x 0 0 nmos90 W={wa}").replace(f"MA2 G2 x2 0 0 nmos90 W={wa}", f"MA2 a2 x2 0 0 nmos90 W={wa}")
        n+=f"Vcb vcb 0 {vcb}\nMK1 G1 vcb a1 0 nmos90 W=2u L=360n\nMK2 G2 vcb a2 0 nmos90 W=2u L=360n\n"
    return n
def dem(n, mode='chop', fch=500e3, ws='4u', ls='0.1u', tr=1e-9):
    """Replace mirror pair M1/M2 by MA/MB whose drains are swapped every half period. mode: 'chop', '1', '2', or 'none'."""
    if mode=='none': return n
    n=n.replace(f"M1 x y 0 0 nmos90 W={W} L={L}\n", f"MA da y 0 0 nmos90 W={W} L={L}\n")
    n=n.replace(f"M2 x2 y 0 0 nmos90 W={W} L={L}\n", f"MB db y 0 0 nmos90 W={W} L={L}\n")
    T=1/fch
    if mode=='1': ck="Vp1 p1 0 1\nVp2 p2 0 0\n"
    elif mode=='2': ck="Vp1 p1 0 0\nVp2 p2 0 1\n"
    else: ck=f"Vp1 p1 0 pulse(0 1 0 {tr} {tr} {T/2-tr:.4e} {T:.4e})\nVp2 p2 0 pulse(1 0 0 {tr} {tr} {T/2-tr:.4e} {T:.4e})\n"
    return n+ck+f"""MS1 da p1 x 0 nmos90 W={ws} L={ls}
MS2 db p1 x2 0 nmos90 W={ws} L={ls}
MS3 da p2 x2 0 nmos90 W={ws} L={ls}
MS4 db p2 x 0 nmos90 W={ws} L={ls}
"""
def rout_ac(n, vo):
    n=n.replace('Vo out 0 dc 0.5 ac 0',f'Vo out 0 dc {vo} ac 1')
    d,o=run(n+"""Iin 0 inn dc 10u
.options reltol=1e-6 abstol=1e-16 vntol=1e-9
.control
set noaskquit
ac dec 5 0.1 10
let ro = 1/mag(i(Vo))
meas ac rout find ro at=1
.endc
.end
""",'ro'); return meas(o,'rout')
def static(n):
    """DC/AC metrics with switches held in phase 1."""
    sv=projA.ckt; projA.ckt=lambda v,**k: n
    try: r=projA.analyse('hp')
    finally: projA.ckt=sv
    r={k:v for k,v in r.items() if k!='dirs'}
    ro=[rout_ac(n,v) for v in (0.3,0.5,0.8)]
    r['rout_0p3']=ro[0]; r['rout_ac_0p5']=ro[1]; r['rout_0p8']=ro[2]
    return r
def chopped(n, iin=10e-6, fch=500e3, nper=6):
    T=1/fch; t0=4*T; t1=t0+nper*T
    d,o=run(n+f"""Iin 0 inn dc {iin}
.control
set noaskquit
tran {T/400:.3e} {t1:.4e} 0 {T/400:.3e} uic
let iout=-i(Vo)
meas tran iavg avg iout from={t0:.4e} to={t1:.4e}
meas tran vavg avg v(inn) from={t0:.4e} to={t1:.4e}
meas tran pavg avg i(Vdd) from={t0:.4e} to={t1:.4e}
.endc
.end
""",'tr')
    ia=meas(o,'iavg')
    return dict(err_avg_pct=(ia-iin)/iin*100 if ia is not None else None, vin_avg=meas(o,'vavg'))
def step(n, i0=1e-6, i1=20e-6):
    d,o=run(n+f"""Iin 0 inn dc 0 pulse({i0} {i1} 1u 5n 5n 2u 4u)
.control
set noaskquit
tran 0.2n 5u
let iout=-i(Vo)
wrdata @DIR/st.txt iout v(inn)
.endc
.end
""",'st')
    a=np.loadtxt(os.path.join(d,'st.txt')); t=a[:,0]; i=a[:,1]
    m=(t>1e-6)&(t<3e-6); up=i[m]; ov=(up.max()-i1)/(i1-i0)*100
    tt=t[m]; ok=np.abs(up-i1)<0.01*(i1-i0); last_bad=tt[~ok].max() if (~ok).any() else 1e-6
    return dict(overshoot_pct=float(ov), ts1pct_ns=float((last_bad-1e-6)*1e9)), a
