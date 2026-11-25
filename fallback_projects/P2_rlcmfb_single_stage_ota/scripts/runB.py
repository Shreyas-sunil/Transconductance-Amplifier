import json, projB, sys
sys.argv=['x']
exec(open('tB2.py').read().split("print('---sweep')")[0].replace("for a,R in []:","for a,R in []:\n    pass\nif 0:"))
from sweep import pvt, mc
C={'conv':lambda: projB.ac_tran('cnv'),
   'rlcmfb_base':lambda: projB.ac_tran('rlc'),
   'ppf_a020_R100k':lambda: projB.ac_tran('ppf',extra=ppf(0.2,'100k'),Rs='5k'),
   'ppf_a015_R100k':lambda: projB.ac_tran('ppf',extra=ppf(0.15,'100k'),Rs='5k')}
out={}
for k,f in C.items():
    out[k]={'nom':{kk:(float(v) if not isinstance(v,tuple) else None) for kk,v in f().items() if kk!='dirs'},'pvt':pvt(f,k),'mc':mc(f,k,40)}
    print(k,'done',flush=True)
json.dump(out,open('resB.json','w'),indent=1)
