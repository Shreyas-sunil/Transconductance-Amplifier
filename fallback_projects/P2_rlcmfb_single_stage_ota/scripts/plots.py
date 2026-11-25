import os, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import projA, projB, projC
from projB_prop import *
exec(open('tB2.py').read().split("print('---sweep')")[0].replace("for a,R in []:","for a,R in []:\n    pass\nif 0:"))
def save(fig,path): fig.tight_layout(); fig.savefig(path,dpi=150); plt.close(fig)
def plotB(out):
    C={'Conventional':('cnv',{}),'RLCMFB base (Rs=3k)':('rlc',{}),'RLCMFB base (Rs=5k)':('rlc',dict(Rs='5k')),'Proposed PPF-RLCMFB (a=0.2, R=100k, Rs=5k)':('ppf',dict(extra=ppf(0.2,'100k'),Rs='5k'))}
    f1,(a1,a2)=plt.subplots(2,1,figsize=(7,6),sharex=True); f2,b=plt.subplots(figsize=(7,4))
    for lab,(v,kw) in C.items():
        r=projB.ac_tran(v,**kw); d,d2=r['dirs']
        a=np.loadtxt(os.path.join(d,'ac.txt')); a1.semilogx(a[:,0],a[:,1],label=lab); a2.semilogx(a[:,0],a[:,3])
        t=np.loadtxt(os.path.join(d2,'tr.txt')); b.plot(t[:,0]*1e9,t[:,1],label=lab)
        np.savetxt(os.path.join(out,f"B_ac_{v}_{kw.get('Rs','3k')}.csv"),a[:,[0,1,3]],delimiter=',',header='freq_Hz,gain_dB,phase_deg')
        np.savetxt(os.path.join(out,f"B_tran_{v}_{kw.get('Rs','3k')}.csv"),t[:,[0,1,3]],delimiter=',',header='t_s,v_load,v_in')
    b.plot(t[:,0]*1e9,t[:,3],'k:',label='input'); a1.set_ylabel('Open-loop gain (dB)'); a2.set_ylabel('Phase (deg)'); a2.set_xlabel('Frequency (Hz)'); a1.legend(fontsize=7); a1.grid(alpha=.3); a2.grid(alpha=.3)
    b.set_xlabel('time (ns)'); b.set_ylabel('V(load) (V)'); b.legend(fontsize=7); b.grid(alpha=.3); b.set_title('Unity-gain follower, 0.4 Vpp step, CL = 2 pF')
    save(f1,os.path.join(out,'B_open_loop_ac.png')); save(f2,os.path.join(out,'B_follower_transient.png'))
def plotA(out):
    projA.W='10u'; projA.WC='40u'
    C={'Conventional cascode':('cnv',{}),'Plain FVF':('fvf',{}),'Base HP reconstruction (2 boosters)':('hp',{}),'Proposed (1 differential booster)':('prop',dict(wp='0.25u',lp='1u'))}
    f,ax=plt.subplots(2,2,figsize=(10,7))
    for lab,(v,kw) in C.items():
        r=projA.analyse(v,vcn=0.42,**kw); d,d2=r['dirs']
        a=np.loadtxt(os.path.join(d,'dc.txt')); x=a[:,0]; io=a[:,1]; vin=a[:,3]; m=x>0.5e-6
        ax[0,0].plot(x[m]*1e6,(io[m]-x[m])/x[m]*100,label=lab); ax[0,1].plot(x*1e6,vin,label=lab)
        c=np.loadtxt(os.path.join(d,'ac.txt')); ax[1,0].loglog(c[:,0],c[:,1],label=lab)
        o=np.loadtxt(os.path.join(d2,'vo.txt')); ax[1,1].plot(o[:,0],-o[:,1]*1e6,label=lab)
        np.savetxt(os.path.join(out,f'A_dc_{v}.csv'),np.c_[x,io,vin],delimiter=',',header='Iin_A,Iout_A,Vin_V')
        np.savetxt(os.path.join(out,f'A_rin_{v}.csv'),c[:,[0,1]],delimiter=',',header='freq_Hz,Rin_ohm')
        np.savetxt(os.path.join(out,f'A_vout_sweep_{v}.csv'),np.c_[o[:,0],-o[:,1]],delimiter=',',header='Vout_V,Iout_A')
    ax[0,0].set_ylabel('Gain error (%)'); ax[0,0].set_xlabel('Iin (uA)'); ax[0,0].set_ylim(-5,1)
    ax[0,1].set_ylabel('Input voltage (V)'); ax[0,1].set_xlabel('Iin (uA)')
    ax[1,0].set_ylabel('Input impedance (ohm), Iin=10 uA'); ax[1,0].set_xlabel('Frequency (Hz)')
    ax[1,1].set_ylabel('Iout (uA), Iin=10 uA'); ax[1,1].set_xlabel('Vout (V)'); ax[1,1].set_ylim(9,10.5)
    for a in ax.flat: a.grid(alpha=.3)
    ax[0,0].legend(fontsize=7); save(f,os.path.join(out,'A_mirror_characteristics.png'))
def plotC(out):
    base=projC.ckt
    C={'Base reconstruction':'', 'Proposed dyn-QFG (W=0.3u)':"Mpd g12 n3 x 0 nmos90 W=0.3u L=0.18u\n", 'Proposed dyn-QFG (W=0.5u)':"Mpd g12 n3 x 0 nmos90 W=0.5u L=0.18u\n"}
    f1,(a1,a2)=plt.subplots(2,1,figsize=(7,6),sharex=True); f2,b=plt.subplots(figsize=(8,4))
    for lab,ex in C.items():
        projC.ckt=lambda v='base',**kw: base(v,**kw)+ex
        r=projC.analyse(step=0.4); d,d2=r['dirs']; tag=lab.split()[0]+ex[19:23].replace('.','p').replace('=','')
        a=np.loadtxt(os.path.join(d,'ac.txt')); a1.semilogx(a[:,0],a[:,1],label=lab); a2.semilogx(a[:,0],a[:,3])
        t=np.loadtxt(os.path.join(d2,'tr.txt')); b.plot(t[:,0]*1e6,t[:,1],label=lab)
        np.savetxt(os.path.join(out,f'C_ac_{tag}.csv'),a[:,[0,1,3]],delimiter=',',header='freq_Hz,gain_dB,phase_deg')
        np.savetxt(os.path.join(out,f'C_tran_{tag}.csv'),t[:,[0,1]],delimiter=',',header='t_s,v_out')
    projC.ckt=base
    a1.set_ylabel('Open-loop gain (dB)'); a2.set_ylabel('Phase (deg)'); a2.set_xlabel('Frequency (Hz)'); a1.legend(fontsize=7)
    for a in (a1,a2,b): a.grid(alpha=.3)
    b.set_xlabel('time (us)'); b.set_ylabel('Vout (V)'); b.set_title('Unity-gain follower, 0.1 to 0.5 V step, CL = 150 pF'); b.legend(fontsize=7)
    save(f1,os.path.join(out,'C_open_loop_ac.png')); save(f2,os.path.join(out,'C_follower_transient.png'))
if __name__=='__main__':
    import sys
    os.makedirs('out',exist_ok=True)
    for p in sys.argv[1:]: globals()['plot'+p]('out')
