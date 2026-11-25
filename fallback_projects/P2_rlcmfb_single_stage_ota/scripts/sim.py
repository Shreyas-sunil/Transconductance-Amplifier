import subprocess, os, re, tempfile, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
MODEL=os.path.join(HERE,'ptm90.lib')
VAR=None
def run(net, tag='x'):
    if VAR is not None:
        from corners import vary
        net=vary(net, **VAR)
    d=tempfile.mkdtemp(dir=HERE+'/runs') if os.path.isdir(HERE+'/runs') else tempfile.mkdtemp()
    f=os.path.join(d,tag+'.cir'); open(f,'w').write(net.replace('@MODEL',MODEL).replace('@DIR',d))
    p=subprocess.run(['ngspice','-b',f],capture_output=True,text=True,cwd=d,timeout=600)
    return d,p.stdout+p.stderr
def wrdata(path):
    a=np.loadtxt(path); return a
def meas(out,name):
    m=re.search(r'^\s*%s\s*=\s*([-+0-9.eE]+)'%name,out,re.M|re.I)
    return float(m.group(1)) if m else None
