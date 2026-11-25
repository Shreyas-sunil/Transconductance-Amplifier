import re, numpy as np
CORNERS={'TT':(0,0),'SS':(0.03,-0.03),'FF':(-0.03,0.03),'SF':(0.03,0.03),'FS':(-0.03,-0.03)}  # (dVth n, dVth p as delvto: p negative = slower)
def vary(net, dn=0.0, dp=0.0, temp=27, mc=None, rng=None, avt=3.5e-3):
    out=[]
    for l in net.split('\n'):
        if re.match(r'^M\w*\s',l) and ('nmos90' in l or 'pmos90' in l):
            isn='nmos90' in l; d=dn if isn else dp
            if mc is not None:
                mw=re.search(r'W=([\d.]+)u',l); W=float(mw.group(1)) if mw else 10.0
                L=re.search(r'L=([\d.]+)(u|n)',l)
                Lu=float(L.group(1))*(1 if L.group(2)=='u' else 1e-3) if L else 0.18
                m=re.search(r'\bm=(\d+)',l); mm=int(m.group(1)) if m else 1
                d+= rng.normal(0, avt/np.sqrt(W*Lu*mm))*(1 if isn else -1)
            l+=f' delvto={d:.5f}'
        out.append(l)
    s='\n'.join(out)
    return s.replace('.include @MODEL', f'.include @MODEL\n.temp {temp}',1)
