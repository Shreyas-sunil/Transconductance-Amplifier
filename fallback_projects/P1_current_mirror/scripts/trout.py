import projA, tcasc
from sim import run, meas
projA.W='10u'; projA.WC='40u'; orig=projA.ckt
def rout_ac(n):
    n=n.replace('Vo out 0 dc 0.5 ac 0','Vo out 0 dc 0.5 ac 1')
    net=n+"""Iin 0 inn dc 10u
.options reltol=1e-6 abstol=1e-16 vntol=1e-9
.control
set noaskquit
ac dec 5 0.1 1k
let ro = 1/mag(i(Vo))
meas ac rout find ro at=1
.endc
.end
"""
    d,o=run(net,'ro'); return meas(o,'rout')
print('base hp', rout_ac(orig('hp',vcn=0.42)))
print('casc 8u', rout_ac(tcasc.casc(0.45,'8u')('hp',vcn=0.42)))
print('fvf', rout_ac(orig('fvf',vcn=0.42)))
for vo in [0.3,0.5,0.8]:
    print('vo',vo, rout_ac(tcasc.casc(0.45,'8u')('hp',vcn=0.42).replace('Vo out 0 dc 0.5','Vo out 0 dc %g'%vo)))
