"""P2 v2: NMOS cross-coupled negative-conductance pair hung from a/b with its own PTAT tail (behavioral or beta multiplier)."""
import projB, tB3, itertools
def nxc(Ix=0.6e-6, Wx='2u', Lx='180n', R='150k', bias='beh', Kn=8, Rp='150k', mt=1, Wn='2u', Ln='1u', Wp='2u', Lp='1u'):
    s=f"""M3 a cm vdd vdd pmos90 W=10u L=180n
M4 b cm vdd vdd pmos90 W=10u L=180n
Mx3 a b tx vss nmos90 W={Wx} L={Lx}
Mx4 b a tx vss nmos90 W={Wx} L={Lx}
Ra a cm {R}
Rb b cm {R}
M3P out b vdd vdd pmos90 W=10u L=180n
M4P c a vdd vdd pmos90 W=10u L=180n
M5 c c vss vss nmos90 W=10u L=180n
M6 out c vss vss nmos90 W=10u L=180n
"""
    if bias=='beh': s+=f"Bx tx vss I={Ix/300.15:.5e}*(temper+273.15)\n"
    elif bias=='const': s+=f"Ix tx vss {Ix}\n"
    else:
        s+=f"""MPa ga gp vdd vdd pmos90 W={Wp} L={Lp}
MPb gp gp vdd vdd pmos90 W={Wp} L={Lp}
MRa ga ga vss vss nmos90 W={Wn} L={Ln}
MRb gp ga sr vss nmos90 W={Wn} L={Ln} m={Kn}
Rp sr vss {Rp}
Mtx tx ga vss vss nmos90 W={Wn} L={Ln} m={mt}
MSU gp vss vss vss nmos90 W=0.12u L=4u
"""
    return s
if __name__=='__main__':
    for Ix,Wx,R in itertools.product([0.4e-6,0.6e-6,0.8e-6],['2u','6u'],['100k','150k']):
        r=projB.ac_tran('tnf',extra=nxc(Ix,Wx,R=R),Rs='5k'); print(Ix,Wx,R,{k:round(float(v),2) for k,v in r.items() if k in('a0','ugf','pm','sr_p','sr_n','pwr')},flush=True)
