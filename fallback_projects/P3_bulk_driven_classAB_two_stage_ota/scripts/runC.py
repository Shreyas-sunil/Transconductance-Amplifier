import json, projC
from sweep import pvt, mc
base=projC.ckt
def mk(ex):
    return lambda v='base',**kw: base(v,**kw)+ex
V={'base_reconstr':'', 'prop_dynQFG_W0p3':"Mpd g12 n3 x 0 nmos90 W=0.3u L=0.18u\n", 'prop_dynQFG_W0p5':"Mpd g12 n3 x 0 nmos90 W=0.5u L=0.18u\n"}
out={}
for k,ex in V.items():
    def f(ex=ex,st=0.4):
        projC.ckt=mk(ex); r=projC.analyse(step=st); projC.ckt=base; return r
    def f2(ex=ex): return f(ex,0.2)
    out[k]={'nom04':{kk:v for kk,v in f().items() if kk!='dirs'},'nom02':{kk:v for kk,v in f2().items() if kk!='dirs'},'pvt':pvt(f,k),'mc':mc(f,k,30)}; print(k,flush=True)
json.dump(out,open('resC.json','w'),indent=1)
