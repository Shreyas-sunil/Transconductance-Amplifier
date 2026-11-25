import json, numpy as np, sys
def stats(rows,key):
    v=np.array([r.get(key) for r in rows if r.get(key) is not None and np.isfinite(r.get(key))],float)
    return (v.min(),v.max(),v.mean(),v.std(),len(v)) if len(v) else None
def summarize(res, keys):
    for c,d in res.items():
        print('==',c)
        for k in keys:
            n=[d[x].get(k) for x in d if x.startswith('nom')]
            p=stats(d['pvt'],k); m=stats(d['mc'],k)
            fmt=lambda t: 'NA' if t is None else f'{t[0]:.4g}..{t[1]:.4g}'
            fm=lambda t: 'NA' if t is None else f'mu={t[2]:.4g} sd={t[3]:.3g} n={t[4]}'
            print(f'  {k:12s} nom={n} | PVT {fmt(p)} | MC {fm(m)}')
if __name__=='__main__':
    f=sys.argv[1]; keys=sys.argv[2].split(',')
    summarize(json.load(open(f)),keys)
