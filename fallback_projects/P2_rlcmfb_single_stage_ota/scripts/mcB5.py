import sys, json, numpy as np, projB, tB3, tB5
from sweep import pvt, mc
cands=json.loads(sys.argv[1]); n=int(sys.argv[2])
out={}
for k,c in cands.items():
    f=lambda c=c: projB.ac_tran('tnf',extra=tB5.nxc(**c),Rs=c.get('Rs','5k')) if 'Rs' not in c else projB.ac_tran('tnf',extra=tB5.nxc(**{x:y for x,y in c.items() if x!='Rs'}),Rs=c['Rs'])
    out[k]={'nom':f(),'pvt':pvt(f,k),'mc':mc(f,k,n)}
    out[k]['nom'].pop('dirs',None)
    print(k,'nom',{x:round(float(y),2) for x,y in out[k]['nom'].items() if x in('a0','ugf','pm','sr_p','sr_n','pwr')})
    for s in ['pvt','mc']:
        g=lambda key: np.array([r[key] for r in out[k][s] if r.get(key) is not None])
        a=g('a0'); pm=g('pm'); u=g('ugf')
        print(' ',s,'a0 %.1f-%.1f mean %.1f sd %.2f | pm min %.1f | ugf %.0f-%.0f MHz'%(a.min(),a.max(),a.mean(),a.std(),pm.min(),u.min()/1e6,u.max()/1e6),flush=True)
json.dump(out,open(sys.argv[3] if len(sys.argv)>3 else 'resB5_try.json','w'))
