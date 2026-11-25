import sys, json, numpy as np, sim
from corners import CORNERS
def pvt(fn, label):
    rows=[]
    for c,(dn,dp) in CORNERS.items():
        for T in [-40,27,125]:
            sim.VAR=dict(dn=dn,dp=dp,temp=T)
            try: r=fn()
            except Exception as e: r={'err':str(e)[:80]}
            r={k:(float(v) if isinstance(v,(float,int,np.floating)) else None) for k,v in r.items() if k!='dirs'}
            r.update(corner=c,temp=T,circuit=label); rows.append(r)
    sim.VAR=None; return rows
def mc(fn,label,n=50,seed=1):
    rng=np.random.default_rng(seed); rows=[]
    for i in range(n):
        sim.VAR=dict(mc=True,rng=rng,temp=27)
        try: r=fn()
        except Exception as e: r={'err':str(e)[:80]}
        r={k:(float(v) if isinstance(v,(float,int,np.floating)) else None) for k,v in r.items() if k!='dirs'}
        r.update(run=i,circuit=label); rows.append(r)
    sim.VAR=None; return rows
