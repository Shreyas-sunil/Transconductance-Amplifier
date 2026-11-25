import sys, os, json, numpy as np
from sim import run, meas
# Bulk-driven non-tailed two-stage class-AB OTA (reconstruction of Ballo et al. 2023), PTM90, VDD=0.6 V
L='180n'
def ckt(v='base', ib='180n', ib3='180n', cc='500f', rc='100k', cb='800f', rb='1Meg', cl='150p', m11=8, m12=15, beta=15, extra=''):
    n=f"""
.include @MODEL
Vdd vdd 0 0.6
* analog ground from R1-R2, also the bulk bias of MB1
R1 vdd ag 300k
R2 ag 0 300k
Ib vb1 0 {ib}
MB1 vb1 vb1 vdd ag pmos90 W=3u L={L} m=2
* bulk-driven non-tailed input pair (PMOS, gates at VB1, bulks are the inputs)
M1 n1 vb1 vdd inp pmos90 W=3u L={L} m=2
M2 n2 vb1 vdd inn pmos90 W=3u L={L} m=2
* NMOS diode loads + cross-coupled positive feedback (alpha = 5/6)
M3 n1 n1 0 0 nmos90 W=6u L={L}
M5 n2 n2 0 0 nmos90 W=6u L={L}
M7 n1 n2 0 0 nmos90 W=5u L={L}
M8 n2 n1 0 0 nmos90 W=5u L={L}
* current gain beta and differential-to-single-ended mirror
M4 n3 n1 0 0 nmos90 W=6u L={L} m={beta}
M6 x n2 0 0 nmos90 W=6u L={L} m={beta}
M9 n3 n3 vdd vdd pmos90 W=6u L={L} m=4
M10 x n3 vdd vdd pmos90 W=6u L={L} m=4
* class-AB second stage: M11 CS, M12 quasi-floating-gate load
M11 out x 0 0 nmos90 W=6u L={L} m={m11}
Ib3 g12b 0 {ib3}
MB3 g12b g12b vdd vdd pmos90 W=6u L={L}
Rbatt g12b g12 {rb}
Cbatt x g12 {cb}
M12 out g12 vdd vdd pmos90 W=6u L={L} m={m12}
* Miller compensation via current buffer node n1
Cc out cm1 {cc}
Rc cm1 n1 {rc}
Cl out 0 {cl}
"""
    return n+extra
def analyse(v='base', vcm=0.3, step=0.2, **kw):
    n=ckt(v,**kw); r={}
    ac=n+f"""Rf out inn 1G
Cf inn 0 10
Vin inp 0 dc {vcm} ac 1
.control
set noaskquit
op
let pw = -i(Vdd)*0.6*1e6
print pw
print v(out)
ac dec 40 0.1 100Meg
let g = db(v(out))
let ph = 180*cph(v(out))/pi
meas ac a0 find g at=1
meas ac ugf when g=0
meas ac phu find ph when g=0
wrdata @DIR/ac.txt g ph
.endc
.end
"""
    d,o=run(ac,'ac'); r.update(pw=meas(o,'pw'),a0=meas(o,'a0'),ugf=meas(o,'ugf'),phu=meas(o,'phu'))
    if r['phu'] is not None: p=r['phu']; p=p if p<0 else p-360; r['pm']=180+p
    lo=vcm-step/2; hi=vcm+step/2
    tr=n+f"""Vin inp 0 dc {lo} pulse({lo} {hi} 2u 10n 10n 40u 80u)
Vsh inn out 0
.control
set noaskquit
tran 20n 82u
wrdata @DIR/tr.txt v(out)
.endc
.end
"""
    d2,o2=run(tr,'tr')
    a=np.loadtxt(os.path.join(d2,'tr.txt')); t=a[:,0]; y=a[:,1]
    def slope(t0,t1,up):
        m=(t>t0)&(t<t1); tt=t[m]; yy=y[m]; y0=yy[0]; y1=yy[-1]; lo_=y0+0.2*(y1-y0); hi_=y0+0.8*(y1-y0)
        f=lambda lv: tt[np.argmax((yy-lv)*(1 if up else -1)>0)]
        return (hi_-lo_)/(f(hi_)-f(lo_))/1e6
    def settle(t0,t1,tol=0.01):
        m=(t>t0)&(t<t1); tt=t[m]; yy=y[m]; yf=yy[-1]; dy=abs(yy[-1]-yy[0])
        bad=np.where(abs(yy-yf)>tol*dy)[0]; return (tt[bad[-1]]-t0)*1e6 if len(bad) else 0
    r['sr_p']=slope(2e-6,42e-6,True); r['sr_n']=slope(42e-6,82e-6,False)
    r['ts_p_us']=settle(2e-6,42e-6); r['ts_n_us']=settle(42e-6,82e-6)
    r['osc_hi']=float(np.ptp(y[(t>32e-6)&(t<42e-6)])); r['osc_lo']=float(np.ptp(y[t>72e-6]))
    r['dirs']=(d,d2); return r
if __name__=='__main__':
    r=analyse(); print({k:(f'{x:.4g}' if isinstance(x,float) else '') for k,x in r.items()})
