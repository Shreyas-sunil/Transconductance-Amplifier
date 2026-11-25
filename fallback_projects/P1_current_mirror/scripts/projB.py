import sys, numpy as np, json
from sim import run, meas
# Single-stage symmetrical OTA, conventional (cnv) vs resistive local CMFB (rlc) vs proposed (prop)
def core(v, W='10u', L='180n', R='300k', Rs='3k', IB='2.5u', CL='2p', vdd=0.45, extra=''):
    n=f"""
.include @MODEL
.param W={W} L={L}
Vdd vdd 0 {vdd}
Vss vss 0 {-vdd}
* bias: 2.5uA reference into NMOS diode
Ib vdd nb {IB}
Mb nb nb vss vss nmos90 W={{W}} L={{L}}
M0 t nb vss vss nmos90 W={{2*W}} L={{L}}
M1 a inn t vss nmos90 W={{W}} L={{L}}
M2 b inp t vss nmos90 W={{W}} L={{L}}
"""
    if v=='cnv':
        n+=f"""M3 a a vdd vdd pmos90 W={{W}} L={{L}}
M4 b b vdd vdd pmos90 W={{W}} L={{L}}
M3P out b vdd vdd pmos90 W={{W}} L={{L}}
M4P c a vdd vdd pmos90 W={{W}} L={{L}}
M5 c c vss vss nmos90 W={{W}} L={{L}}
M6 out c vss vss nmos90 W={{W}} L={{L}}
Vml out oL 0
Cl oL 0 {CL}
"""
    elif v in ('rlc','prop'):
        n+=f"""M3 a cm vdd vdd pmos90 W={{W}} L={{L}}
M4 b cm vdd vdd pmos90 W={{W}} L={{L}}
Ra a cm {R}
Rb b cm {R}
"""
        if v=='rlc':
            n+="""M3P out b vdd vdd pmos90 W={W} L={L}
M4P c a vdd vdd pmos90 W={W} L={L}
"""
            n+=f"""M5 c c vss vss nmos90 W={{W}} L={{L}}
M6 out c vss vss nmos90 W={{W}} L={{L}}
"""
        n+=extra
        n+=f"""Rs out o2 {Rs}
Vml o2 oL 0
Cl oL 0 {CL}
"""
    return n
def ac_tran(v, **kw):
    base=core(v,**kw)
    acn=base+"""
Rf out inn 100Meg
Cf inn 0 1
Vin inp 0 dc 0 ac 1
.control
set noaskquit
op
let pwr = -(i(Vdd)*0.45) + (i(Vss)*0.45)
print pwr
print v(out)
let pw = pwr*1e6
print pw
ac dec 50 1 10G
let g = db(v(out))
let ph = 180*cph(v(out))/pi
meas ac a0 find g at=10
meas ac ugf when g=0
meas ac phu find ph when g=0
wrdata @DIR/ac.txt g ph
.endc
.end
"""
    d,o=run(acn,'ac')
    r=dict(a0=meas(o,'a0'),ugf=meas(o,'ugf'),phu=meas(o,'phu'),pwr=meas(o,'pw'))
    if r['phu'] is not None:
        ph=r['phu']; ph=ph if ph<0 else ph-360
        r['pm']=180+ph
    trn=base+"""
Vin inp 0 dc 0 pulse(-0.2 0.2 20n 1n 1n 399n 800n)
Vsh inn out 0
.control
set noaskquit
tran 0.2n 900n
meas tran sr_p deriv v(out) when v(out)=0 rise=1
meas tran sr_n deriv v(out) when v(out)=0 fall=1
meas tran t_up when v(out)=0.12 rise=1
meas tran t_up0 when v(out)=-0.12 rise=1
meas tran t_dn when v(out)=-0.12 fall=1
meas tran t_dn0 when v(out)=0.12 fall=1
meas tran ipk max i(Vml)
meas tran imin min i(Vml)
wrdata @DIR/tr.txt v(oL) v(inp) i(Vml)
.endc
.end
"""
    d2,o2=run(trn,'tr')
    import numpy as np, os
    a=np.loadtxt(os.path.join(d2,'tr.txt')); t=a[:,0]; y=a[:,1]
    def slope(t0,t1,up):
        m=(t>t0)&(t<t1); tt=t[m]; yy=y[m]; y0=yy[0]; y1=yy[-1]; lo=y0+0.2*(y1-y0); hi=y0+0.8*(y1-y0)
        f=lambda lv: tt[np.argmax((yy-lv)*(1 if up else -1)>0)]
        return (hi-lo)/(f(hi)-f(lo))/1e6
    r['sr_p']=slope(19e-9,419e-9,True); r['sr_n']=slope(419e-9,819e-9,False)
    r['ipk']=meas(o2,'ipk'); r['imin']=meas(o2,'imin')
    r['dirs']=(d,d2)
    return r
if __name__=='__main__':
    for v in sys.argv[1:]:
        r=ac_tran(v); print(v, json.dumps({k:(round(x,3) if isinstance(x,float) else x) for k,x in r.items()}))
