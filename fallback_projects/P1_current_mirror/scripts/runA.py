import json, projA
from sweep import pvt, mc
projA.W='10u'; projA.WC='40u'
kw=dict(vcn=0.42)
C={'conv_cascode':lambda: projA.analyse('cnv',**kw),'fvf':lambda: projA.analyse('fvf',**kw),
   'base_hp_reconstr':lambda: projA.analyse('hp',**kw),'prop_single_booster':lambda: projA.analyse('prop',wp='0.25u',lp='1u',**kw)}
out={}
for k,f in C.items():
    out[k]={'nom':{kk:v for kk,v in f().items() if kk!='dirs'},'pvt':pvt(f,k),'mc':mc(f,k,40)}; print(k,flush=True)
json.dump(out,open('resA.json','w'),indent=1)
