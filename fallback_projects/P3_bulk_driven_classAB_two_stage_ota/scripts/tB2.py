from projB import ac_tran
def ppf(alpha,R):
    Wl=10*(1-alpha); Wx=10*alpha
    return f"""M3 a cm vdd vdd pmos90 W={Wl}u L=180n
M4 b cm vdd vdd pmos90 W={Wl}u L=180n
Mx3 a b vdd vdd pmos90 W={Wx}u L=180n
Mx4 b a vdd vdd pmos90 W={Wx}u L=180n
Ra a cm {R}
Rb b cm {R}
M3P out b vdd vdd pmos90 W=10u L=180n
M4P c a vdd vdd pmos90 W=10u L=180n
M5 c c vss vss nmos90 W=10u L=180n
M6 out c vss vss nmos90 W=10u L=180n
"""
import projB
src=projB.core
def core2(v,**kw):
    if v!='ppf': return src(v,**kw)
    ex=kw.pop('extra'); n=src('prop',extra='',**kw)
    # strip default load/resistors from prop core
    lines=[l for l in n.split('\n') if not l.startswith(('M3 ','M4 ','Ra ','Rb '))]
    n='\n'.join(lines).replace('Rs out',ex+'Rs out')
    return n
projB.core=core2
for a,R in []:
    try:
        r=ac_tran('ppf',extra=ppf(a,R)); print(a,R,{k:round(float(v),2) for k,v in r.items() if k not in('dirs','phu')})
    except Exception as e: print(a,R,'fail',e)
print('---sweep')
import itertools
for a,R,Rs in itertools.product([0.15,0.2,0.25],['80k','100k','150k'],['3k','5k']):
    r=ac_tran('ppf',extra=ppf(a,R),Rs=Rs); print(a,R,Rs,{k:round(float(v),2) for k,v in r.items() if k in('a0','ugf','pm','sr_p','sr_n')})
