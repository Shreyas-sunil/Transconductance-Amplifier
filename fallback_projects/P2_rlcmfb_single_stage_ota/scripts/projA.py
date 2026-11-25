import sys, json, os, numpy as np
from sim import run, meas
# Low-voltage current mirrors, PTM90, VDD=1V. Iin injected into 'inn' (current into node), output held by Vo source.
W='5u'; L='360n'; WC='5u'
def ckt(v, ib=2e-6, k=10, cc='0.3p', wa='2u', vcn=0.55, wp="4u", wn="1u", lp="360n"):
    h=f"""
.include @MODEL
Vdd vdd 0 1
Vcn vcn 0 {vcn}
Vo out 0 dc 0.5 ac 0
"""
    if v=='cnv':   # wide-swing cascode
        b=f"""M1C y vcn x 0 nmos90 W={W} L={L}
M1 x y 0 0 nmos90 W={W} L={L}
M2C out vcn x2 0 nmos90 W={W} L={L}
M2 x2 y 0 0 nmos90 W={W} L={L}
.alias inn y
"""
        b=b.replace('.alias inn y\n','Vjoin inn y 0\n')
    else:          # FVF current mirror: Iin into x, Ib into y; output offset Ib removed by ideal source
        b=f"""Ibf vdd y {ib}
M1C y G1 x 0 nmos90 W={WC} L={L}
M1 x y 0 0 nmos90 W={W} L={L}
Vjoin inn x 0
M2C out G2 x2 0 nmos90 W={WC} L={L}
M2 x2 y 0 0 nmos90 W={W} L={L}
Ibo vdd out {ib}
"""
        if v=='fvf':
            b+="Vg1 G1 0 {0}\nVg2 G2 0 {0}\n".format(vcn)
        elif v=='prop':
            # input side: plain FVF (G1 fixed). output side: one differential booster forcing V(x2)=V(x)
            b+=f"""Vg1 G1 0 {vcn}
It vdd tl {ib/k}
MPa da x tl vdd pmos90 W={wp} L={lp}
MPb G2 x2 tl vdd pmos90 W={wp} L={lp}
MNa da da 0 0 nmos90 W={wn} L={L}
MNb G2 da 0 0 nmos90 W={wn} L={L}
Cc2 G2 0 {cc}
"""
        elif v=='hp':
            # regulated-cascode boosters (CS NMOS) on both cascodes; Ia = booster bias
            if True:
                b+=f"""Ia1 vdd G1 {ib/k}
Ia2 vdd G2 {ib/k}
"""
            b+=f"""MA1 G1 x 0 0 nmos90 W={wa} L={L}
MA2 G2 x2 0 0 nmos90 W={wa} L={L}
Cc1 G1 0 {cc}
Cc2 G2 0 {cc}
"""
    return h+b
def analyse(v, **kw):
    n=ckt(v,**kw)
    r={}
    dc=n+"""Iin 0 inn dc 0 ac 1
.control
set noaskquit
op
let pw = -i(Vdd)*1e6
print pw
dc Iin 0 20u 0.25u
let iout = -i(Vo)
let err = 100*(iout-v-sweep)/v-sweep
wrdata @DIR/dc.txt iout v(inn)
alter Iin dc=10u
ac dec 40 1k 10G
let rin = mag(v(inn))
meas ac rin_lf find rin at=1k
let tf = db(-i(Vo))
meas ac bw when tf=-3.0103
wrdata @DIR/ac.txt rin tf
.endc
.end
"""
    d,o=run(dc,'dc')
    r['pw0']=meas(o,'pw'); r['rin10u']=meas(o,'rin_lf'); r['bw10u']=meas(o,'bw')
    a=np.loadtxt(os.path.join(d,'dc.txt')); x=a[:,0]; io=a[:,1]; vin=a[:,3]
    m=x>=0.99e-6
    r['err_max_pct']=float(np.max(np.abs((io[m]-x[m])/x[m]))*100)
    r['err_10u_pct']=float((io[x==x[np.argmin(abs(x-10e-6))]][0]-10e-6)/10e-6*100)
    r['vin_0']=float(vin[0]); r['vin_20u']=float(vin[-1])
    # output resistance & compliance at Iin=10u
    ro=n+"""Iin 0 inn dc 10u
.control
set noaskquit
dc Vo 0 1 0.005
wrdata @DIR/vo.txt i(Vo)
.endc
.end
"""
    d2,o2=run(ro.replace('Vo out 0 dc 0.5 ac 0','Vo out 0 dc 0.5'),'ro')
    b=np.loadtxt(os.path.join(d2,'vo.txt')); vo=b[:,0]; io=b[:,1]
    i5=np.interp(0.5,vo,io); g=np.gradient(io,vo); io=-io; i5=-i5; r['rout_0p5V']=float(1/abs(np.interp(0.5,vo,g)))
    ok=np.abs(io-i5)<0.01*abs(i5); r['vout_min']=float(vo[np.argmax(ok)])
    r['dirs']=(d,d2)
    # power at 10u
    return r
if __name__=='__main__':
    for v in sys.argv[1:]:
        r=analyse(v); print(v,{k:(f'{x:.4g}' if isinstance(x,float) else '') for k,x in r.items()})
