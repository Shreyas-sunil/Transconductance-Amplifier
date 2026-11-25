import json, numpy as np, projA2 as P
from sweep import pvt, mc
def full(kind):
    def f():
        n=P.core(kind); r=P.static(P.dem(n,'1')); c=P.chopped(P.dem(n,'chop')); r.update(c)
        s,_=P.step(P.dem(n,'1')); r.update(s); return r
    return f
out=json.load(open('resA2.json'))
f=full('casc'); out['casc']={'nom':f(),'pvt':pvt(f,'casc'),'mc':mc(f,'casc',40)}
out['base']['nom'].update(P.step(P.dem(P.core('base'),'1'))[0])
# extra DEM characterisation on the proposed core
n=P.core('casc')
out['dem_iin']={str(i):P.chopped(P.dem(n,'chop'),iin=i) for i in [1e-6,2e-6,5e-6,10e-6,15e-6,20e-6]}
out['dem_fch']={str(fc):P.chopped(P.dem(n,'chop',fch=fc),fch=fc) for fc in [100e3,500e3,1e6,2e6,5e6]}
def f2(): return P.chopped(P.dem(P.core('casc'),'chop'),iin=2e-6)
def f2s(): return P.chopped(P.dem(P.core('casc'),'1'),iin=2e-6)
out['mc_2u']={'dem':mc(f2,'dem2u',40),'static':mc(f2s,'st2u',40)}
json.dump(out,open('resA3.json','w'),indent=1)
print('done')
