import json, numpy as np, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import projA2 as P, projB, tB3, tB5
from sim import run
A=json.load(open('resA3.json')); B=json.load(open('resB2.json')); Bold=json.load(open('resB.json'))
def col(rows,k): return np.array([r[k] for r in rows if r.get(k) is not None])
# ---- P1 figure
fig,ax=plt.subplots(2,2,figsize=(11,8))
st=col(A['casc']['mc'],'err_10u_pct'); dm=col(A['casc']['mc'],'err_avg_pct')
ax[0,0].hist(st,bins=20,alpha=.6,label=f'static (σ={st.std():.2f} %)'); ax[0,0].hist(dm,bins=20,alpha=.8,label=f'DEM chopped (σ={dm.std():.2f} %)')
ax[0,0].set_xlabel('gain error at 10 µA (%)'); ax[0,0].set_ylabel('runs'); ax[0,0].set_title('Monte Carlo, 40 runs'); ax[0,0].legend()
n=P.dem(P.core('casc'),'chop')
d,o=run(n+"""Iin 0 inn dc 10u
.control
set noaskquit
tran 1n 10u 0 1n uic
wrdata @DIR/w.txt -i(Vo)
.endc
.end
""",'w'); a=np.loadtxt(os.path.join(d,'w.txt'))
ax[0,1].plot(a[:,0]*1e6,a[:,1]*1e6,lw=.8); ax[0,1].set_xlim(4,10); ax[0,1].set_ylim(9,11)
ax[0,1].set_xlabel('time (µs)'); ax[0,1].set_ylabel('Iout (µA)'); ax[0,1].set_title('Chopped output, 500 kHz clock (nominal)')
ii=sorted(A['dem_iin'],key=float); ax[1,0].plot([float(i)*1e6 for i in ii],[A['dem_iin'][i]['err_avg_pct'] for i in ii],'o-')
ax[1,0].set_xlabel('Iin (µA)'); ax[1,0].set_ylabel('averaged gain error (%)'); ax[1,0].set_title('DEM mirror, nominal')
ff=sorted(A['dem_fch'],key=float); ax[1,1].semilogx([float(f) for f in ff],[A['dem_fch'][f]['err_avg_pct'] for f in ff],'o-')
ax[1,1].set_xlabel('clock frequency (Hz)'); ax[1,1].set_ylabel('averaged gain error (%)'); ax[1,1].set_title('Charge-injection error vs clock')
for x in ax.flat: x.grid(alpha=.3)
fig.tight_layout(); fig.savefig('out2/A_dem_mirror.png',dpi=130)
# ---- P2 figure
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
NEW=dict(bias='tr',Rp='260k',mt=2,Ln='4u',Lp='4u',Wn='8u',Wp='8u')
for lab,v,kw in [('Base RLCMFB, Rs=5k','rlc',dict(Rs='5k')),('New: NMOS cross-coupled + PTAT tail','tnf',dict(extra=tB5.nxc(**NEW),Rs='5k'))]:
    r=projB.ac_tran(v,**kw); g=np.loadtxt(os.path.join(r['dirs'][0],'ac.txt'))
    ax[0].semilogx(g[:,0],g[:,1],label=lab)
    np.savetxt(f'out2/B_ac_{v}.csv',g[:,[0,1,3]],delimiter=',',header='f_Hz,gain_dB,phase_deg',comments='')
ax[0].set_xlabel('frequency (Hz)'); ax[0].set_ylabel('open-loop gain (dB)'); ax[0].legend(); ax[0].grid(alpha=.3); ax[0].set_ylim(-20,80)
for lab,rows in [('Base RLCMFB',B['B3_rlcmfb_Rs5k']['mc']),('Earlier PPF version',Bold['ppf_a020_R100k']['mc']),('New (PTAT tail)',B['B5_new_nxc_ptat']['mc'])]:
    g=col(rows,'a0'); ax[1].hist(g,bins=np.arange(45,100,1),alpha=.6,label=f'{lab}: {g.mean():.1f} ± {g.std():.2f} dB')
ax[1].set_xlabel('DC gain (dB)'); ax[1].set_ylabel('runs'); ax[1].set_title('Monte Carlo, 40 runs'); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig('out2/B_new_ota.png',dpi=130)
print('plots ok')
