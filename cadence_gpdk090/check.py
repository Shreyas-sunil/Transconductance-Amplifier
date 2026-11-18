import re
src=open("build_gpdk090.il").read()
PINS={"nmos1v":{"G":(0,0),"D":(0.25,0.1875),"S":(0.25,-0.1875),"B":(0.25,0)},
      "pmos1v":{"G":(0,0),"S":(0.25,0.1875),"D":(0.25,-0.1875),"B":(0.25,0)}}
for c in ["res","cap","ind","vdc","idc"]: PINS[c]={"PLUS":(0,0),"MINUS":(0,-0.375)}
def tr(o,p):
    x,y=p
    return {"R0":(x,y),"MY":(-x,y),"R90":(-y,x),"R180":(-x,-y),"R270":(y,-x)}[o]
for cellname in ["TIA_2020_base_gpdk090","TIA_proposed_v1_gpdk090"]:
    body=src.split(f'tiaBuild_{cellname}(lib)')[1].split("schCheck")[0]
    pts={}; parent={}
    def f(a):
        while parent.setdefault(a,a)!=a: a=parent[a]
        return a
    def un(a,b): parent[f(a)]=f(b)
    R=lambda v:(round(float(v[0]),4),round(float(v[1]),4))
    inst={}
    for m in re.finditer(r'tI\(cv "\w+" "(\w+)" "(\w+)" (\S+) (\S+) "(\w+)"',body):
        cell,name,x,y,o=m.groups()
        for pn,pp in PINS[cell].items():
            q=tr(o,pp); P=R((float(x)+q[0],float(y)+q[1])); inst[(name,pn)]=P; f(P)
    segs=[]
    for m in re.finditer(r'tW\(cv list\((.*?)\)\)\n',body):
        L=[R(t) for t in re.findall(r'list\((\S+) (\S+)\)',m.group(1))]
        for a,b2 in zip(L,L[1:]): segs.append((a,b2)); un(a,b2)
    labels=[]
    for m in re.finditer(r'tL\(cv "(\w+)" list\((.*?)\)\)\n',body):
        L=[R(t) for t in re.findall(r'list\((\S+) (\S+)\)',m.group(2))]
        segs.append((L[0],L[1])); un(L[0],L[1]); labels.append((m.group(1),L[0]))
    for m in re.finditer(r'tG\(cv (\S+) (\S+)\)',body): labels.append(("0",R((m.group(1),m.group(2)))))
    for m in re.finditer(r'tV\(cv (\S+) (\S+)\)',body): labels.append(("vdd",R((m.group(1),m.group(2)))))
    # T-junction / overlap check: any point lying strictly inside a segment
    allp=set(inst.values())|{p for s in segs for p in s}
    for (a,b2) in segs:
        for p in allp:
            if p in (a,b2): continue
            if (a[0]==b2[0]==p[0] and min(a[1],b2[1])<p[1]<max(a[1],b2[1])) or (a[1]==b2[1]==p[1] and min(a[0],b2[0])<p[0]<max(a[0],b2[0])):
                print("  WARN point",p,"inside segment",a,b2)
    for n,p in labels: f(p)
    names={}
    for n,p in labels: names.setdefault(f(p),set()).add(n)
    # merge by label name
    byname={}
    for r,ns in names.items():
        for n in ns: byname.setdefault(n,[]).append(r)
    for n,rs in byname.items():
        for r in rs[1:]: un(r,rs[0])
    def netof(P):
        r=f(P); ns=set()
        for n,p in labels:
            if f(p)==r: ns.add(n)
        return "/".join(sorted(ns)) or f"?{P}"
    print(cellname)
    devs={}
    for (name,pn),P in inst.items(): devs.setdefault(name,{})[pn]=netof(P)
    for d in sorted(devs): print(" ",d,devs[d])
