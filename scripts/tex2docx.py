r"""Convert paper/main.tex to paper/Paper_ActiveInductor_TIA.docx with pandoc.
Resolves the number macros, \input files, \ref/\cite numbers and equation numbers first,
because pandoc does not number LaTeX cross-references in Word output."""
import os, re, subprocess
import circuits as C

P = os.path.join(C.ROOT, 'paper')
tex = open(os.path.join(P, 'main.tex')).read()
# 1. inline \input files
tex = re.sub(r'\\makeatletter.*?\n', '\n', tex)
tex = re.sub(r'\\tableinput (table_\w+\.tex) ', lambda m: open(os.path.join(P, m.group(1))).read(), tex)
tex = re.sub(r'\\input\{([^}]+)\}', lambda m: open(os.path.join(P, m.group(1))).read() if 'numbers' not in m.group(1) else '', tex)
# 2. expand number macros (longest names first)
macros = dict(re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}', open(os.path.join(P, 'numbers.tex')).read()))
for k in sorted(macros, key=len, reverse=True):
    tex = re.sub(r'\\%s(?![A-Za-z])(\\ )?' % k, lambda m, v=macros[k]: v + (' ' if m.group(1) else ''), tex)
# siunitx -> plain text (pandoc does not expand \SI inside math or captions)
def unit(u):
    for a, b in (('\\micro ', 'µ'), ('\\micro', 'µ'), ('\\ohm', 'Ω'), ('\\celsius', '°C'), ('\\percent', '\\%'), ('\\degree', '°'), ('^2', '²'), ('.', '·')):
        u = u.replace(a, b)
    return u.strip()
tex = re.sub(r'\\SI\{([^}]*)\}\{([^}]*)\}', lambda m: '\\mbox{%s\u00a0%s}' % (m.group(1).replace('-', '−'), unit(m.group(2))), tex)
tex = re.sub(r'\\si\{([^}]*)\}', lambda m: '\\mbox{%s}' % unit(m.group(1)), tex)
# 3. numbering: sections, figures, tables, equations, citations
labels = {}
body = tex[tex.index('\\begin{document}'):]
sec = sub = 0
for m in re.finditer(r'\\(section|subsection)\{[^}]*\}(\\label\{([^}]+)\})?', body):
    if m.group(1) == 'section':
        sec += 1; sub = 0; num = f'{sec}'
    else:
        sub += 1; num = f'{sec}.{sub}'
    if m.group(3): labels[m.group(3)] = num
for env, pref in (('figure', 'fig'), ('table', 'tab'), ('equation', 'eq')):
    n = 0
    for m in re.finditer(r'\\begin\{%s\}.*?\\end\{%s\}' % (env, env), body, re.S):
        for lab in re.findall(r'\\label\{([^}]+)\}', m.group(0)):
            n += 1; labels[lab] = str(n)
cites = {k: str(i + 1) for i, k in enumerate(re.findall(r'\\bibitem\{([^}]+)\}', tex))}
tex = re.sub(r'\\eqref\{([^}]+)\}', lambda m: '(' + labels[m.group(1)] + ')', tex)
tex = re.sub(r'~?\\ref\{([^}]+)\}', lambda m: ('~' if m.group(0).startswith('~') else '') + labels[m.group(1)], tex)
tex = re.sub(r'\\cite\{([^}]+)\}', lambda m: '{[}' + ', '.join(cites[k.strip()] for k in m.group(1).split(',')) + '{]}', tex)
# equations: add explicit numbers
def eqn(m):
    lab = re.search(r'\\label\{([^}]+)\}', m.group(1))
    inner = re.sub(r'\\label\{[^}]+\}', '', m.group(1)).strip()
    return '\\[\n' + inner + ('\\qquad (%s)' % labels[lab.group(1)] if lab else '') + '\n\\]'
tex = re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}', eqn, tex, flags=re.S)
# captions: explicit numbers, then drop labels
def cap(env, word):
    global tex
    n = [0]
    def fix(m):
        def c(mm):
            n[0] += 1
            return '\\caption{%s %d. ' % (word, n[0])
        return re.sub(r'\\caption\{', c, m.group(0))
    tex = re.sub(r'\\begin\{%s\}.*?\\end\{%s\}' % (env, env), fix, tex, flags=re.S)
cap('figure', 'Fig.'); cap('table', 'Table')
tex = re.sub(r'\\label\{[^}]+\}', '', tex)
tex = re.sub(r'\\cmidrule\([a-z]+\)\{[^}]+\}', '', tex)
tex = tex.replace('\\,$^\\circ$C', '\u00a0°C').replace('mm$^2$', 'mm²')
tex = re.sub(r'\\begin\{minipage\}\{[^}]*\}\\centering', '', tex).replace('\\end{minipage}\\hfill', '').replace('\\end{minipage}', '')
tex = re.sub(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', r'\\includegraphics[width=0.9\\linewidth]{\1.png}', tex)
tex = tex.replace('\\hfill', '')
# bibliography -> numbered list
def bib(m):
    items = re.split(r'\\bibitem\{[^}]+\}', m.group(1))[1:]
    return '\\section*{References}\n' + '\n\n'.join('[%d] %s' % (i + 1, it.strip()) for i, it in enumerate(items))
tex = re.sub(r'\\begin\{thebibliography\}\{\d+\}(.*?)\\end\{thebibliography\}', bib, tex, flags=re.S)
tmp = os.path.join(P, '_docx_src.tex')
open(tmp, 'w').write(tex)
out = os.path.join(P, 'Paper_ActiveInductor_TIA.docx')
r = subprocess.run(['pandoc', tmp, '-f', 'latex', '-t', 'docx', '-o', out, '--number-sections', '--resource-path', P], capture_output=True, text=True, cwd=P)
print(r.stderr[:2000]); assert r.returncode == 0, "pandoc failed"; os.remove(tmp); print('wrote', out)
