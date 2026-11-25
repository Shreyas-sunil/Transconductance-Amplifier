import sys, json
from projB import ac_tran
def sc_extra(nb, Lb='180n', Wt='10u', Wb=None):
    Wb = Wb or f'{10/nb}u'
    # self-cascode output branches: top device in saturation, bottom (narrow) in triode, gates common
    return f"""M3Pt out b s3 vdd pmos90 W={Wt} L=180n
M3Pb s3 b vdd vdd pmos90 W={Wb} L={Lb}
M4Pt c a s4 vdd pmos90 W={Wt} L=180n
M4Pb s4 a vdd vdd pmos90 W={Wb} L={Lb}
M5t c c s5 vss nmos90 W={Wt} L=180n
M5b s5 c vss vss nmos90 W={Wb} L={Lb}
M6t out c s6 vss nmos90 W={Wt} L=180n
M6b s6 c vss vss nmos90 W={Wb} L={Lb}
"""
