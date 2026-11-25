# Testbenches in three dialects
TB={}
TB['B_ac']=dict(
 add=["Rf out inn 100Meg","Cf inn 0 1","Vin inp 0 dc 0 ac 1"],
 ng=""".control
op
ac dec 50 1 10G
let g=db(v(out))
let ph=180*cph(v(out))/pi
meas ac A0_dB find g at=10
meas ac UGF when g=0
meas ac PH_UGF find ph when g=0
wrdata ac_out.txt g ph
.endc""",
 lt=""".ac dec 50 1 10G
.meas AC A0_dB FIND dB(V(out)) AT=10
.meas AC UGF WHEN mag(V(out))=1
.meas AC PH_UGF FIND ph(V(out)) WHEN mag(V(out))=1""",
 sp="""dcop dc
olac ac start=1 stop=10G dec=50""")
TB['B_tr']=dict(
 add=["Vin inp 0 dc 0 pulse(-0.2 0.2 20n 1n 1n 399n 800n)","Vsh inn out 0"],
 ng=""".control
tran 0.2n 900n
wrdata tr_out.txt v(oL) v(inp)
.endc""",
 lt=".tran 0 900n 0 0.2n",
 sp="tr tran stop=900n maxstep=0.2n")
TB['A_dc']=dict(
 add=["Iin 0 inn dc 10u ac 1"],
 ng=""".control
op
dc Iin 0 20u 0.25u
let iout=-i(Vo)
let err_pct=100*(iout-v-sweep)/(v-sweep+1e-12)
wrdata dc_out.txt iout err_pct v(inn)
ac dec 40 1k 10G
meas ac Rin_1k find mag(v(inn)) at=1k
let tf=db(-i(Vo))
meas ac BW when tf=-3.0103
dc Vo 0 1 0.005
wrdata vo_out.txt -i(Vo)
.endc""",
 lt=""".dc Iin 0 20u 0.25u
* for input resistance / bandwidth use instead:  .ac dec 40 1k 10G   (Rin = V(inn) per 1 A, BW from I(Vo))
* for output compliance / Rout use instead:     .dc Vo 0 1 5m""",
 sp="""dcop dc
dcIin dc dev=Iin param=dc start=0 stop=20u step=0.25u
acRin ac start=1k stop=10G dec=40
dcVo dc dev=Vo param=dc start=0 stop=1 step=5m""")
TB['C_ac']=dict(
 add=["Rf out inn 1G","Cf inn 0 10","Vin inp 0 dc 0.3 ac 1"],
 ng=""".control
op
ac dec 40 0.1 100Meg
let g=db(v(out))
let ph=180*cph(v(out))/pi
meas ac A0_dB find g at=1
meas ac UGF when g=0
meas ac PH_UGF find ph when g=0
wrdata ac_out.txt g ph
.endc""",
 lt=""".ac dec 40 0.1 100Meg
.meas AC A0_dB FIND dB(V(out)) AT=1
.meas AC UGF WHEN mag(V(out))=1
.meas AC PH_UGF FIND ph(V(out)) WHEN mag(V(out))=1""",
 sp="""dcop dc
olac ac start=0.1 stop=100M dec=40""")
TB['C_tr']=dict(
 add=["Vin inp 0 dc 0.1 pulse(0.1 0.5 2u 10n 10n 40u 80u)","Vsh inn out 0"],
 ng=""".control
tran 20n 82u
wrdata tr_out.txt v(out) v(inp)
.endc""",
 lt=".tran 0 82u 0 20n",
 sp="tr tran stop=82u maxstep=20n")
TB['A_chop']=dict(
 add=["Iin 0 inn dc 10u"],
 ng=""".control
tran 5n 20u 0 5n uic
let iout=-i(Vo)
meas tran Iout_avg avg iout from=8u to=20u
meas tran Vin_avg avg v(inn) from=8u to=20u
wrdata chop_out.txt iout v(inn)
.endc""",
 lt=""".tran 0 20u 0 5n uic
.meas TRAN Iout_avg AVG -I(Vo) FROM=8u TO=20u""",
 sp="""tr tran stop=20u maxstep=5n""")
