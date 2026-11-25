import json, numpy as np, projA2 as P
from sweep import pvt, mc
def full(kind):
    def f():
        n=P.core(kind); r=P.static(P.dem(n,'1')); c=P.chopped(P.dem(n,'chop')); r.update(c); return r
    return f
out={}
for kind in ['base','casc']:
    f=full(kind)
    out[kind]={'nom':f(),'pvt':pvt(f,kind),'mc':mc(f,kind,40)}
    print(kind,'done',flush=True)
json.dump(out,open('resA2.json','w'),indent=1)
for kind in out:
    for sec in ['pvt','mc']:
        rows=out[kind][sec]
        for key in ['err_10u_pct','err_avg_pct','rin10u','rout_ac_0p5','vout_min','vin_20u']:
            v=np.array([r[key] for r in rows if r.get(key) is not None])
            print(kind,sec,key,len(v),'min %.4g max %.4g mean %.4g sd %.4g'%(v.min(),v.max(),v.mean(),v.std()))
