#!/usr/bin/env python3
"""results.json（measure.pyの実測）からfolarrow-fonts.defを作る．

\\fol@hdata{フォント名}{矢頭の幅/quad}{軸の太さ/quad}{\\longrightarrowの尻}{伸びる矢印の尻}
\\fol@vdata{フォント名}{\\Bigの矢頭の幅/quad}{\\Bigの軸の太さ/quad}{土台の矢頭の幅/quad}{土台の軸の太さ/quad}
            {\\Bigの尻}{土台の尻}
\\fol@otfcap{フォント名の鍵}{\\longrightarrowの尻}{伸びる矢印の尻}{\\Bigの尻}{土台の尻}：OpenTypeのフォント
尻の形はr（丸）かb（切りっぱなし）．矢印の尻（軸の端）の塗りの割合が0.85未満なら丸とする．
フォント名は\\fontnameの基本部分（「 at …」を除く）．末尾の数字を除いた名前の項目も作り，
実測していない大きさ（cmsy9など）のときに使う（値は本文サイズのもの）．
OpenTypeのフォント（LuaTeXではfolarrow.luaで直接測る）は入れない．
"""
import json, os, re, statistics, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'results.json')))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'tex', 'latex', 'folarrow', 'folarrow-fonts.def')

H = defaultdict(list)   # fname -> [(head/q, shaft/q, q, config)]
V = defaultdict(list)   # fname -> [(big/q, bigshaft/q, inl/q, inlshaft/q, q, config)]
for r in R:
    if r['engine'] != 'pdflatex' or not r.get('m'):
        continue
    for k, x in r['m'].items():
        if 'head' in x and 'fn' in x and not x.get('clip') and x['q'] > 0:
            H[x['fn']].append((x['head'] / x['q'], x['shaft'] / x['q'], x['q'], r['name']))
    for sz, f in r['f3'].items():
        need = ('big', 'bigshaft', 'inl', 'inlshaft', 'fn', 'q3')
        if all(f.get(n) for n in need) and not f.get('bigclip') and not f.get('inlclip'):
            q = f['q3']
            V[f['fn']].append((f['big'] / q, f['bigshaft'] / q, f['inl'] / q, f['inlshaft'] / q, q, r['name']))

TAIL = 0.85
def capof(v):
    return 'r' if v < TAIL else 'b'

def majority(xs):
    xs = [x for x in xs if x]
    return max(set(xs), key=xs.count) if xs else None

# 設定ごとの尻の形（大きさにわたる多数決）
def config_caps(r):
    f3 = r['f3'].values()
    pick = lambda k: majority([capof(f[k]) for f in f3 if f.get(k)])
    return pick('lratail'), pick('filltail'), pick('bigtail'), pick('inltail')

HCAP = defaultdict(list)   # 矢印のフォント名→[(capL, capF)]
VCAP = defaultdict(list)   # \\downarrowのフォント名→[(capBig, capInl)]
OTF = {}                   # 鍵 -> caps
for r in R:
    if not r.get('m'):
        continue
    cl, cf, cb, ci = config_caps(r)
    if r['engine'] == 'pdflatex':
        for x in r['m'].values():
            if x.get('fn'):
                HCAP[x['fn']].append((cl, cf))
        for f in r['f3'].values():
            if f.get('fn'):
                VCAP[f['fn']].append((cb, ci))
    elif r['engine'] == 'lualatex':
        m = re.search(r'\\setmathfont\{([^}]*)\}', r.get('pre', ''))
        key = None
        if m:
            key = re.sub(r'[^a-z0-9]', '', m.group(1).lower())
        elif 'firamath' in r.get('pre', ''):
            key = 'firamath'
        elif 'gfsneohellenicot' in r.get('pre', ''):
            key = 'gfsneohellenicmath'
        if key:
            key = re.sub(r'(regular|book|otf)+$', '', key)
            OTF.setdefault(key, []).append((cl, cf, cb, ci))

# 中心のずれ（補正前．矢頭の側が正．quadに対する比）：実測の残りのずれ＋かけた補正
# 並びは[\longrightarrow，伸びる矢印，\Bigの下向き，\Bigの上向き，土台の下向き，土台の上向き]
SIGN = {'chr': 1, 'chf': 1, 'cbd': 1, 'cbu': -1, 'cid': 1, 'ciu': -1, 'chl': -1, 'cfl': -1}
ORDER = ['chr', 'chf', 'cbd', 'cbu', 'cid', 'ciu']
LEFT = ['chl', 'cfl']   # 左向き：\\longleftarrow，伸びる矢印

def raw_offsets(r, sz):
    f = r['f3'].get(sz, {})
    ap = f.get('applied')
    q2 = r['m'].get(sz + 't', {}).get('q')
    q3 = f.get('q3')
    if not ap or not q2 or not q3:
        return None
    out = []
    for i, k in enumerate(ORDER):   # 矢印の向きのずれ（矢頭の側が正）
        a = f.get(k + 'along')
        q = q2 if i < 2 else q3
        out.append(None if a is None else (SIGN[k] * a + ap[i]) / q)
    for i, k in enumerate(ORDER):   # 直交方向のずれ（横向きは下，縦向きは右が正）
        a = f.get(k + 'across')
        q = q2 if i < 2 else q3
        apc = ap[6 + i] if len(ap) > 6 else 0
        out.append(None if a is None else (a + apc) / q)
    for i, k in enumerate(LEFT):    # 左向きの矢印の向きのずれ（矢頭の側が正）
        a = f.get(k + 'along')
        apl = ap[12 + i] if len(ap) > 12 else 0
        out.append(None if a is None else (SIGN[k] * a + apl) / q2)
    for i, k in enumerate(LEFT):    # 左向きの直交方向のずれ
        a = f.get(k + 'across')
        apl = ap[14 + i] if len(ap) > 14 else 0
        out.append(None if a is None else (a + apl) / q2)
    return out

# XeTeXで測ったOpenTypeのフォント（results-xelatex.json）
XR = []
_xp = os.path.join(HERE, 'results-xelatex.json')
if os.path.exists(_xp):
    XR = [r for r in json.load(open(_xp)) if r.get('engine') == 'xelatex']

def otfkey(r):
    m = re.search(r'\\setmathfont\{([^}]*)\}', r.get('pre', ''))
    key = None
    if m:
        key = re.sub(r'[^a-z0-9]', '', m.group(1).lower())
    elif 'firamath' in r.get('pre', ''):
        key = 'firamath'
    elif 'gfsneohellenicot' in r.get('pre', ''):
        key = 'gfsneohellenicmath'
    return re.sub(r'(regular|book|otf)+$', '', key) if key else None

HOFF = defaultdict(list)   # 矢印のフォント名→[(offL, offF)]
VOFF = defaultdict(list)   # \\downarrowのフォント名→[(offBd, offBu, offId, offIu)]
OTFOFF = defaultdict(list)
for r in R:
    if not r.get('m'):
        continue
    for sz in r['f3']:
        o = raw_offsets(r, sz)
        if not o:
            continue
        fn2 = r['m'].get(sz + 't', {}).get('fn')
        fn3 = r['f3'][sz].get('fn')
        if r['engine'] == 'pdflatex':
            if fn2:
                HOFF[fn2].append(o[0:2] + o[6:8] + o[12:16])
            if fn3:
                VOFF[fn3].append(o[2:6] + o[8:12])
        elif r['engine'] == 'lualatex':
            m = re.search(r'\\setmathfont\{([^}]*)\}', r.get('pre', ''))
            key = None
            if m:
                key = re.sub(r'[^a-z0-9]', '', m.group(1).lower())
            elif 'firamath' in r.get('pre', ''):
                key = 'firamath'
            elif 'gfsneohellenicot' in r.get('pre', ''):
                key = 'gfsneohellenicmath'
            if key:
                OTFOFF[re.sub(r'(regular|book|otf)+$', '', key)].append(o)

def offmean(rows, n):
    out = []
    for i in range(n):
        v = [x[i] for x in rows if x[i] is not None]
        out.append(statistics.mean(v) if v else 0.0)
    return out

def offstr(v):
    return ','.join('%.4f' % x for x in v)

def capvote(rows, i):
    return majority([x[i] for x in rows]) or 'b'

def agg(rows, n):
    vals = [statistics.mean(x[i] for x in rows) for i in range(n)]
    spread = max(max(x[i] for x in rows) / min(x[i] for x in rows) - 1 for i in range(n))
    return vals, spread

lines = []
warn = []
def stem(n):
    return re.sub(r'[0-9]+$', '', n)

hvals = {}
for fn, rows in sorted(H.items()):
    vals, sp = agg(rows, 2)
    hvals[fn] = (vals, max(x[2] for x in rows))
    if sp > 0.03:
        warn.append(f'H {fn}: spread {sp:.1%} over {sorted(set(x[3] for x in rows))}')
vvals = {}
for fn, rows in sorted(V.items()):
    vals, sp = agg(rows, 4)
    vvals[fn] = (vals, max(x[4] for x in rows))
    if sp > 0.03:
        warn.append(f'V {fn}: spread {sp:.1%} over {sorted(set(x[5] for x in rows))}')

def stems(vals):
    """末尾の数字を除いた名前→最も大きいquadで測った項目の値（その名前自体が実測済みなら作らない）"""
    out = {}
    for fn, (v, q) in vals.items():
        s = stem(fn)
        if s == fn or s in vals:
            continue
        if s not in out or q > out[s][1]:
            out[s] = (v, q)
    return out

with open(OUT, 'w') as f:
    f.write('%% folarrow-fonts.def：数式フォントごとの矢頭の幅と軸の太さ（実測）\n')
    f.write('%% 各フォントの矢印を実際に組んで字面の範囲を測った結果から作成した．\n')
    f.write('%% 値はそのフォントのquad（\\fontdimen6）に対する比．\n')
    f.write('%% \\fol@hdata{フォント名}{矢頭の幅}{軸の太さ}{\\longrightarrowの尻}{伸びる矢印の尻}{中心のずれ}：\\rightarrowを持つフォント\n')
    f.write('%% \\fol@vdata{フォント名}{\\Bigの矢頭の幅}{\\Bigの軸の太さ}{土台の矢頭の幅}{土台の軸の太さ}{\\Bigの尻}{土台の尻}{中心のずれ}：\n')
    f.write('%%   \\downarrowの大きい字形を持つフォント（土台は\\foldownarrowの\\left\\downarrow）\n')
    f.write('%% \\fol@otfcap{鍵}{\\longrightarrowの尻}{伸びる矢印の尻}{\\Bigの尻}{土台の尻}{中心のずれ}：OpenTypeのフォント．\n')
    f.write('%%   鍵はフォント名を小文字の英数字だけにしたもの（末尾のregular，book，otfを除く）の一部\n')
    f.write('%% 尻の形はr（丸）かb（切りっぱなし）\n')
    f.write('%% 中心のずれは，箱の中心に置いた3本線が矢印の字面の中心から矢頭の側へずれる量（quadに対する比）．\n')
    f.write('%%   並びは\\fol@hdataが「\\longrightarrow，伸びる矢印」，\\fol@vdataが「\\Bigの下向き，\\Bigの上向き，\n')
    f.write('%%   土台の下向き，土台の上向き」，\\fol@otfcapはこの6つ．そのあとに同じ並びで直交方向のずれ\n')
    f.write('%%   （横向きは下，縦向きは右が正）が続く．最後に左向きの矢印（\\longleftarrow，伸びる矢印）の\n')
    f.write('%%   矢印の向きのずれと直交方向のずれが続く\n')
    hc = lambda n: (capvote(HCAP.get(n, []), 0), capvote(HCAP.get(n, []), 1))
    vc = lambda n: (capvote(VCAP.get(n, []), 0), capvote(VCAP.get(n, []), 1))
    hstem = {stem(n): n for n in hvals}
    vstem = {stem(n): n for n in vvals}
    ho = lambda n: offstr(offmean(HOFF.get(n, []), 8))
    vo = lambda n: offstr(offmean(VOFF.get(n, []), 8))
    for fn, (v, q) in sorted(hvals.items()):
        f.write('\\fol@hdata{%s}{%.4f}{%.4f}{%s}{%s}{%s}\n' % (fn, *v, *hc(fn), ho(fn)))
    for s, (v, q) in sorted(stems(hvals).items()):
        f.write('\\fol@hdata{%s}{%.4f}{%.4f}{%s}{%s}{%s}%% 末尾の数字を除いた名前（実測していない大きさ用）\n' % (s, *v, *hc(hstem[s]), ho(hstem[s])))
    for fn, (v, q) in sorted(vvals.items()):
        f.write('\\fol@vdata{%s}{%.4f}{%.4f}{%.4f}{%.4f}{%s}{%s}{%s}\n' % (fn, *v, *vc(fn), vo(fn)))
    for s, (v, q) in sorted(stems(vvals).items()):
        f.write('\\fol@vdata{%s}{%.4f}{%.4f}{%.4f}{%.4f}{%s}{%s}{%s}%% 末尾の数字を除いた名前\n' % (s, *v, *vc(vstem[s]), vo(vstem[s])))
    for k, rows in sorted(OTF.items()):
        f.write('\\fol@otfcap{%s}{%s}{%s}{%s}{%s}{%s}\n' % (k, *(capvote(rows, i) for i in range(4)), offstr(offmean(OTFOFF.get(k, []), 16))))
    # XeTeXで測った値（LuaTeX用のあとに書き，XeTeXではこちらが優先される）
    XCAP = defaultdict(list); XOFF = defaultdict(list)
    for r in XR:
        if not r.get('m'):
            continue
        k = otfkey(r)
        if not k:
            continue
        XCAP[k].append(config_caps(r))
        for sz in r['f3']:
            o = raw_offsets(r, sz)
            if o:
                XOFF[k].append(o)
    for k, rows in sorted(XCAP.items()):
        f.write('\\fol@otfcapxe{%s}{%s}{%s}{%s}{%s}{%s}\n' % (k, *(capvote(rows, i) for i in range(4)), offstr(offmean(XOFF.get(k, []), 16))))
    f.write('\\endinput\n')

print(f'H: {len(hvals)} fonts, V: {len(vvals)} fonts -> {OUT}')
for w in warn:
    print('WARN', w)
