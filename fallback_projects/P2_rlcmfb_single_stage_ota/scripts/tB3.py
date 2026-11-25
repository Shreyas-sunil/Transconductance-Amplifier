"""P2 v2: cross-coupled pair with its own (PTAT) tail current, so gmx is set by a bias current and not by a current split."""
import projB, sys, itertools
src=projB.core
def tnf(Ix=0.6e-6, Wx='4u', Lx='180n', R='100k', ptat=True, Wl='10u'):
    I=f"I={Ix/300.15:.5e}*(temper+273.15)" if ptat else f"I={Ix}"
    return f"""M3 a cm vdd vdd pmos90 W={Wl} L=180n
M4 b cm vdd vdd pmos90 W={Wl} L=180n
Mx3 a b tx vdd pmos90 W={Wx} L={Lx}
Mx4 b a tx vdd pmos90 W={Wx} L={Lx}
Bx vdd tx {I}
Ra a cm {R}
Rb b cm {R}
M3P out b vdd vdd pmos90 W=10u L=180n
M4P c a vdd vdd pmos90 W=10u L=180n
M5 c c vss vss nmos90 W=10u L=180n
M6 out c vss vss nmos90 W=10u L=180n
"""
def core3(v,**kw):
    if v!='tnf': return src(v,**kw)
    ex=kw.pop('extra'); n=src('prop',extra='',**kw)
    lines=[l for l in n.split('\n') if not l.startswith(('M3 ','M4 ','Ra ','Rb '))]
    return '\n'.join(lines).replace('Rs out',ex+'Rs out')
projB.core=core3
if __name__=='__main__':
    for Ix,Wx,R in itertools.product([0.4e-6,0.6e-6,0.8e-6],['4u','10u'],['100k','150k']):
        try:
            r=projB.ac_tran('tnf',extra=tnf(Ix,Wx,R=R),Rs='5k'); print(Ix,Wx,R,{k:round(float(v),2) for k,v in r.items() if k in('a0','ugf','pm','sr_p','sr_n','pwr')},flush=True)
        except Exception as e: print(Ix,Wx,R,'fail',e)
