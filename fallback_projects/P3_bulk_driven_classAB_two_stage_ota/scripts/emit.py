import re
GPDK='/home/buet/cadence/gpdk090_v4.6/models/spectre/gpdk090.scs'
def resolve(core):
    core=core.replace('{{2*W}}','20u').replace('{2*W}','20u').replace('{{W}}','10u').replace('{W}','10u').replace('{{L}}','180n').replace('{L}','180n')
    lines=[l for l in core.split('\n') if l.strip() and not l.startswith(('.include','.param','.alias'))]
    return lines
def to_ngspice(title, lines, tb):  # tb: dict with 'ng' text
    return f"* {title}\n* PTM 90 nm BSIM4 (ptm90.lib). Run: ngspice -b <file>\n.include ptm90.lib\n" + '\n'.join(lines) + '\n' + tb['ng'] + '\n.end\n'
def to_ltspice(title, lines, tb):
    return f"* {title}\n* LTspice, PTM 90 nm BSIM4. Open in LTspice and Run. If LTspice rejects 'level = 54' in ptm90.lib, change it to 'level = 14' (both are BSIM4).\n.include ptm90.lib\n" + '\n'.join(lines) + '\n' + tb['lt'] + '\n.backanno\n.end\n'
def spec_line(l):
    if l.lstrip().startswith('*'): return '// '+l.lstrip()[1:].strip()
    t=l.split()
    n=t[0]; k=n[0].upper()
    if k=='M':
        d,g,s,b,mod=t[1:6]; mod={'nmos90':'nmos1v','pmos90':'pmos1v'}[mod]
        rest=' '.join(x.replace('W=','w=').replace('L=','l=') for x in t[6:])
        return f"{n} ({d} {g} {s} {b}) {mod} {rest}"
    if k=='R': return f"{n} ({t[1]} {t[2]}) resistor r={t[3].replace('Meg','M')}"
    if k=='C': return f"{n} ({t[1]} {t[2]}) capacitor c={t[3]}"
    if k=='V':
        a=' '.join(t[3:]); dc=re.search(r'(?:dc\s+)?([-\d.]+[a-zA-Z]*)',a)
        s=f"{n} ({t[1]} {t[2]}) vsource dc={t[3] if t[3]!='dc' else t[4]}"
        m=re.search(r'pulse\(([^)]*)\)',a)
        if m:
            p=m.group(1).split(); s=f"{n} ({t[1]} {t[2]}) vsource type=pulse dc={p[0]} val0={p[0]} val1={p[1]} delay={p[2]} rise={p[3]} fall={p[4]} width={p[5]} period={p[6]}"
        if re.search(r'\bac\s+1',a): s+=' mag=1'
        return s
    if k=='I':
        a=' '.join(t[3:]); v=t[3] if t[3]!='dc' else t[4]
        s=f"{n} ({t[1]} {t[2]}) isource dc={v}"
        if re.search(r'\bac\s+1',a): s+=' mag=1'
        return s
    raise ValueError(l)
def to_spectre(title, lines, tb, temp=27):
    body='\n'.join(spec_line(l) for l in lines)
    return f"""// {title}
// Cadence Spectre, gpdk090 (nmos1v/pmos1v). Device sizes are the PTM90 design copied over;
// re-tune bias/sizes in GPDK090 before quoting numbers (thresholds differ).
simulator lang=spectre
global 0
include "{GPDK}" section=NN
{body}
simOpts options temp={temp} tnom=27 reltol=1e-5 gmin=1e-15
{tb['sp']}
"""
