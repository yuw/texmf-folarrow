#!/usr/bin/env python3
"""measure.pyの結果から，説明書に載せる検証表（folarrow-verify.tex）を作る．

読むもの：results.json（pdfLaTeX／LuaLaTeX），results-uplatex.json，results-xelatex.json
表の値は，folarrowの計算値と実測値のずれの最大（％）．大きさ（10pt，10.95pt，12pt）と
スタイル（本文・添字・添字の添字）のすべてにわたる最大値で，縦向きは\\Bigと
\\foldownarrowの土台の大きいほう．
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, '..', '..', 'doc', 'latex', 'folarrow', 'folarrow-verify.tex')

ENG = {'pdflatex': 'pdf', 'lualatex': 'Lua', 'uplatex': 'up', 'xelatex': 'Xe'}
# 実測に使ったフォントがMETAFONTのビットマップ（PK）で，ドットの段差（600dpiで0.12pt）が
# そのまま寸法の誤差になるもの
PK = {'boisik', 'computerconcrete', 'europeancomputerconcrete', 'drm'}

rows = []
for fn in ('results.json', 'results-uplatex.json', 'results-xelatex.json'):
    p = os.path.join(HERE, fn)
    if os.path.exists(p):
        rows += json.load(open(p))


def worst(pairs):
    v = [abs(a / b - 1) for a, b in pairs if a and b]
    return max(v) * 100 if v else None


def fmt(x):
    if x is None:
        return '--'
    return r'\textbf{%.0f}' % x if x > 3 else '%.0f' % x


def label(r):
    n = r['name']
    m = re.search(r'\\setmathfont\{([^}]*)\}', r.get('pre', ''))
    if n.startswith(('otf-', 'xfile-')) and m:
        return m.group(1)
    return re.sub(r'^x-', '', n)


out = []
for r in sorted(rows, key=lambda r: (label(r).lower(), r['engine'])):
    note = ''
    if not r.get('m'):
        e = r.get('error', '')
        note = '未インストール' if ('not found' in e or 'cannot open' in e or 'no pdf' in e) else 'エラー'
        out.append((label(r), ENG[r['engine']], '--', '--', '--', '--', '--', '--', note))
        continue
    m = r['m']
    hb = worst((x.get('b'), x.get('head')) for x in m.values())
    ht = worst((x.get('t'), x.get('shaft')) for x in m.values())
    vb = worst([(f.get('bigb'), f.get('big')) for f in r['f3'].values()] +
               [(f.get('inlb'), f.get('inl')) for f in r['f3'].values()])
    vt = worst([(f.get('bigt'), f.get('bigshaft')) for f in r['f3'].values()] +
               [(f.get('inlt'), f.get('inlshaft')) for f in r['f3'].values()])
    # 3本線の端の形：実測した尻の形（被覆率0.85未満なら丸）とfolarrowの選択が一致するか
    # 尻の形は大きさ（10pt，10.95pt，12pt）にわたる多数決で決める（mkdata.pyと同じ）
    def vote(k):
        v = ['r' if f[k] < 0.85 else 'b' for f in r['f3'].values() if f.get(k)]
        return max(set(v), key=v.count) if v else 'b'
    want = ''.join(vote(k) for k in ('lratail', 'filltail', 'bigtail', 'inltail'))
    caps = [f['caps'] for f in r['f3'].values() if f.get('caps')]
    capok = None if not caps else all(c == want for c in caps)
    if hb is None:
        note = '未インストール'
    elif r['name'] in PK:
        note = 'PKフォント'
    elif r['engine'] == 'xelatex' and max(hb or 0, ht or 0) > 3:
        note = '添字用字形'
    cap = '--' if capok is None else ('○' if capok else r'\textbf{×}')
    # 3本線の中心と矢印の字面の中心のずれ（pt，矢印の向きと直交方向の最大）
    cvals = [abs(f.get(k + d)) for f in r['f3'].values()
             for k in ('chr', 'chf', 'cbd', 'cbu', 'cid', 'ciu') for d in ('along', 'across')
             if f.get(k + d) is not None]
    cen = '--' if not cvals else (r'\textbf{%.2f}' % max(cvals) if max(cvals) > 0.05 else '%.2f' % max(cvals))
    out.append((label(r), ENG[r['engine']], fmt(hb), fmt(ht), fmt(vb), fmt(vt), cen, cap, note))

esc = lambda s: s.replace('_', r'\_').replace('&', r'\&')
with open(OUT, 'w') as f:
    f.write('% folarrow-verify.tex：矢印を実際に組んで測った結果から作成した検証表（手で直さない）\n')
    f.write('\\begin{longtable}{@{}lcrrrrrcl@{}}\n')
    f.write('書体（設定） & エンジン & \\multicolumn{2}{c}{横向き} & \\multicolumn{2}{c}{縦向き} & 中心 & 端 & 備考\\\\\n')
    f.write(' & & 幅 & 太さ & 幅 & 太さ & pt & & \\\\\\hline\\endhead\n')
    for row in out:
        f.write('\\texttt{%s} & %s & %s & %s & %s & %s & %s & %s & %s\\\\\n' % ((esc(row[0]),) + row[1:]))
    f.write('\\end{longtable}\n')
ok = sum(1 for x in out if not x[8] and '\\textbf' not in ''.join(x[2:8]))
print(f'{len(out)} rows, {ok} within 3% -> {OUT}')
