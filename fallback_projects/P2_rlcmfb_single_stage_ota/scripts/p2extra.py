"""Extra P2 metrics: follower offset, CMRR, PSRR+, input noise."""
import projB, numpy as np
from sim import run, meas
def extra(v, **kw):
    base=projB.core(v,**kw); r={}
    d,o=run(base+"""Vin inp 0 dc 0
Vsh inn out 0
.control
set noaskquit
op
let vos = v(out)*1e3
print vos
.endc
.end
""",'os'); r['vos_mV']=meas(o,'vos')
    # open-loop with DC servo: differential gain Ad (inp ac), common-mode gain Acm (both inputs via servo), supply gain
    ol=base.replace(f"Vdd vdd 0 {0.45}",f"Vdd vdd 0 dc 0.45 ac 0")
    net=ol+"""Rf out fb 100Meg
Cf fb 0 1
Ecm inn fb icm 0 1
Vcm icm 0 dc 0 ac 0
Vin inp icm dc 0 ac 1
.control
set noaskquit
ac dec 10 1 100Meg
let ad = mag(v(out))
meas ac ad10 find ad at=10
alter Vin ac=0
alter Vcm ac=1
ac dec 10 1 100Meg
let acm = mag(v(out))
meas ac acm10 find acm at=10
alter Vcm ac=0
alter Vdd ac=1
ac dec 10 1 100Meg
let aps = mag(v(out))
meas ac aps10 find aps at=10
.endc
.end
"""
    d,o=run(net,'ex')
    ad=meas(o,'ad10'); acm=meas(o,'acm10'); aps=meas(o,'aps10')
    r['cmrr_dB']=20*np.log10(ad/acm) if ad and acm else None
    r['psrrp_dB']=20*np.log10(ad/aps) if ad and aps else None
    import os
    d,o=run(base+'''Vin inp 0 dc 0 ac 1
Rf out inn 100Meg
Cf inn 0 1
.control
set noaskquit
noise v(out) Vin dec 20 10 100Meg
setplot noise1
wrdata @DIR/n.txt inoise_spectrum
.endc
.end
''','n')
    try:
        a=np.loadtxt(os.path.join(d,'n.txt')); f=a[:,0]; vn=a[:,1]
        r['vn_1k_nV']=float(np.interp(3,np.log10(f),vn))*1e9; r['vn_1M_nV']=float(np.interp(6,np.log10(f),vn))*1e9
    except Exception as e: r['vn_err']=str(e)[:60]
    return r
if __name__=='__main__':
    import tB3, tB5, sys
    print('rlc 3k', extra('rlc'))
    print('rlc 5k', extra('rlc',Rs='5k'))
    print('new', extra('tnf',extra=tB5.nxc(bias='tr',Rp='260k',mt=2,Ln='4u',Lp='4u',Wn='8u',Wp='8u'),Rs='5k'))
