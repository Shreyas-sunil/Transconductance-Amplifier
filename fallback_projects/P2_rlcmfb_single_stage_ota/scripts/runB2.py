import json, numpy as np, projB, tB3, tB5, p2extra
from sweep import pvt, mc
NEW=dict(bias='tr',Rp='260k',mt=2,Ln='4u',Lp='4u',Wn='8u',Wp='8u')
def mk(v,**kw):
    def f():
        r=projB.ac_tran(v,**kw); r.pop('dirs',None); r.update(p2extra.extra(v,**kw)); return r
    return f
C={'B2_rlcmfb_Rs3k':mk('rlc'),'B3_rlcmfb_Rs5k':mk('rlc',Rs='5k'),
   'B5_new_nxc_ptat':mk('tnf',extra=tB5.nxc(**NEW),Rs='5k'),
   'B5i_ideal_ptat':mk('tnf',extra=tB5.nxc(Ix=6e-7,R='150k'),Rs='5k'),
   'B5c_const_tail':mk('tnf',extra=tB5.nxc(Ix=5.67e-7,R='150k',bias='const'),Rs='5k')}
out={}
for k,f in C.items():
    out[k]={'nom':{a:(float(b) if b is not None else None) for a,b in f().items()}}
    if k in('B2_rlcmfb_Rs3k','B3_rlcmfb_Rs5k','B5_new_nxc_ptat','B5c_const_tail'):
        out[k]['pvt']=pvt(f,k); out[k]['mc']=mc(f,k,40)
    print(k,'done',flush=True)
json.dump(out,open('resB2.json','w'),indent=1)
