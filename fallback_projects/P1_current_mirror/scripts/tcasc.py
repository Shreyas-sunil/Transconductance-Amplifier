import projA, itertools, sys
projA.W='10u'; projA.WC='40u'; orig=projA.ckt
def casc(vcb=0.45, wa='2u', wc='2u', cc='0.3p', k=10):
    def f(v,**kk):
        n=orig('hp',**{**kk,'wa':wa,'cc':cc,'k':k})
        n=n.replace(f"MA1 G1 x 0 0 nmos90 W={wa}", f"MA1 a1 x 0 0 nmos90 W={wa}").replace(f"MA2 G2 x2 0 0 nmos90 W={wa}", f"MA2 a2 x2 0 0 nmos90 W={wa}")
        n+=f"Vcb vcb 0 {vcb}\nMK1 G1 vcb a1 0 nmos90 W={wc} L=360n\nMK2 G2 vcb a2 0 nmos90 W={wc} L=360n\n"
        return n
    return f
if __name__=='__main__':
  for vcb,wa,cc in itertools.product([0.4,0.45,0.5],['2u','8u'],['0.3p']):
    projA.ckt=casc(vcb,wa,cc=cc)
    r=projA.analyse('hp',vcn=0.42)
    print(vcb,wa,cc,'Rin %.3f Rout %.3g err %.4f errmax %.4f vin %.3f vmin %.3f bw %.3g P %.2f'%(r['rin10u'],r['rout_0p5V'],r['err_10u_pct'],r['err_max_pct'],r['vin_20u'],r['vout_min'],r['bw10u'] or 0,r['pw0']))
