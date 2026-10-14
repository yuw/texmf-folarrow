#!/usr/bin/env python3
"""folarrowの本文用の矢印（→←↓↑に3本線）のType 1フォントを作る．

使い方：python3 mkfolfonts.py
  必要なもの：fontTools，skia-pathops（重なりの除去），TeX Liveのkpsewhich，tftopl，vftovp，
  pltotf，t1asm（PATHに通しておく）．

対象の数式フォント（記号フォント）ごとに，次の4文字のフォントを1本ずつ作る．
  文字0 arrowright：\\longrightarrow（マイナス記号＋→を\\joinrelで組んだもの）に3本線
  文字1 arrowleft ：\\longleftarrow（←＋マイナス記号）に3本線
  文字2 arrowdown ：文字0（3本線を入れる前）を時計回りに90°回し，数式の軸に中心を合わせたもの
  文字3 arrowup   ：同じものを反時計回りに90°回したもの
元のフォントの字形（アウトライン）をそのまま使い，3本線だけを足す．3本線の寸法はfolarrowの
描画と同じ（長さ＝矢頭の幅，間隔＝0.35×矢頭の幅，傾き0.25，太さ＝軸の太さ）．3本線の中心は
字面の中心（軸の上の，矢印の長さの中央）に置き，矢印の尻が丸ければ3本線の端も丸くする．

出力（このリポジトリのTDSの中．環境変数FOLARROW_ROOTを与えると，その下のTDSの中．
  そこにはtex/latex/folarrow/folarrow-fonts.defが要る）：
  fonts/type1/public/folarrow/<名前>.pfb
  fonts/tfm/public/folarrow/<名前>.tfm
  fonts/map/dvips/folarrow/folarrow.map
  tex/latex/folarrow/folarrow-glyphs.def（記号フォントの名前→このフォントの名前の表）
"""
import math, os, re, subprocess, sys, tempfile
from fontTools.t1Lib import T1Font
from fontTools.pens.recordingPen import RecordingPen
import pathops

HERE = os.path.dirname(os.path.abspath(__file__))
# 読み書きするTDSの根．既定はこのリポジトリ（tools/fontbuild/の2つ上）．
# 環境変数FOLARROW_ROOTで別のTDSの木（folarrow.tds.zipを展開したものなど）を指せる．
ROOT = os.path.abspath(os.environ.get('FOLARROW_ROOT') or os.path.join(HERE, '..', '..'))
OUT_PFB = os.path.join(ROOT, 'fonts', 'type1', 'public', 'folarrow')
OUT_TFM = os.path.join(ROOT, 'fonts', 'tfm', 'public', 'folarrow')
OUT_MAP = os.path.join(ROOT, 'fonts', 'map', 'dvips', 'folarrow')
OUT_DEF = os.path.join(ROOT, 'tex', 'latex', 'folarrow', 'folarrow-glyphs.def')
FONTDEF = os.path.join(ROOT, 'tex', 'latex', 'folarrow', 'folarrow-fonts.def')
# 書き出す先がfolarrowのTDSの木でなければ，何も書かずに止める（配布物の中で動かしたとき，
# 配布物の外に書き出さないため）．mkfolotf.pyもこのファイルを読み込むので同じ確認を通る．
if not os.path.isfile(FONTDEF):
    sys.exit('%s: %s not found.\nSet FOLARROW_ROOT to a TDS tree of folarrow '
             '(for example, folarrow.tds.zip unpacked).' % (os.path.basename(sys.argv[0]), FONTDEF))

# 斜線の形（folarrow.styの既定値と同じ）
SPAN, LEAN, GAP = 1.0, 0.25, 0.35
SIDE = 0.05         # 縦向きの矢印の3本線の左右のアキ（quadに対する比）

# 対象：記号フォントの名前→（作るフォントのファイル名，PostScript名）
# 元フォントの予約フォント名（OFLのReserved Font Name）を使わないよう，名前を付け替える
TARGETS = {}
for sz in (5, 6, 7, 8, 9, 10):
    TARGETS['cmsy%d' % sz] = ('folcm%d' % sz, 'FolArrow-CM%d' % sz)
    TARGETS['lmsy%d' % sz] = ('follm%d' % sz, 'FolArrow-LM%d' % sz)
TARGETS.update({
    'ntxsy': ('folntx', 'FolArrow-NTX'), 'ntxsy7': ('folntx7', 'FolArrow-NTX7'),
    'ntxsy5': ('folntx5', 'FolArrow-NTX5'),
    'txsy': ('foltx', 'FolArrow-TX'), 'pxsy': ('folpx', 'FolArrow-PX'),
    'zplsy': ('folzpl', 'FolArrow-ZPL'),
})
# 太字の記号フォント（\boldmathや\bmのとき使われる）
for sz in (5, 6, 7, 8, 9, 10):
    TARGETS['cmbsy%d' % sz] = ('folcmb%d' % sz, 'FolArrow-CMB%d' % sz)
for sz in (5, 7, 10):
    TARGETS['lmbsy%d' % sz] = ('follmb%d' % sz, 'FolArrow-LMB%d' % sz)
TARGETS.update({
    'ntxbsy': ('folntxb', 'FolArrow-NTXB'), 'ntxbsy7': ('folntxb7', 'FolArrow-NTXB7'),
    'ntxbsy5': ('folntxb5', 'FolArrow-NTXB5'),
    'txbsy': ('foltxb', 'FolArrow-TXB'), 'pxbsy': ('folpxb', 'FolArrow-PXB'),
    'zplbsy': ('folzplb', 'FolArrow-ZPLB'),
})
NAMES = ['arrowright', 'arrowleft', 'arrowdown', 'arrowup']


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def kpse(name):
    r = subprocess.run(['kpsewhich', name], capture_output=True, text=True)
    return r.stdout.strip() or None


# ---------- TFM / VF ----------
def parse_pl(text):
    """tftopl／vftovpの出力から，設計サイズ，パラメーター，文字の寸法とVFの写像を読む"""
    info = {'chars': {}, 'params': {}, 'mapfont': {}}
    m = re.search(r'\(DESIGNSIZE R ([0-9.]+)\)', text)
    info['ds'] = float(m.group(1))
    for k in ('SLANT', 'QUAD', 'AXISHEIGHT', 'XHEIGHT'):
        m = re.search(r'\(%s R (-?[0-9.]+)\)' % k, text)
        if m:
            info['params'][k] = float(m.group(1))
    for m in re.finditer(r'\(MAPFONT D (\d+)\s*\(FONTNAME ([^)]+)\)(.*?)\n   \)', text, re.S):
        at = re.search(r'\(FONTAT R ([0-9.]+)\)', m.group(3))
        info['mapfont'][int(m.group(1))] = (m.group(2).strip(), float(at.group(1)) if at else 1.0)
    for m in re.finditer(r'\n\(CHARACTER (C|O) (\S+)\n(.*?)\n   \)', text, re.S):
        code = ord(m.group(2)) if m.group(1) == 'C' else int(m.group(2), 8)
        body = m.group(3)
        g = lambda k: float(re.search(r'\(%s R (-?[0-9.]+)\)' % k, body).group(1)) if re.search(r'\(%s R' % k, body) else 0.0
        ch = {'wd': g('CHARWD'), 'ht': g('CHARHT'), 'dp': g('CHARDP'), 'map': None}
        mm = re.search(r'\(MAP(.*)', body, re.S)
        if mm:
            ops = re.findall(r'\((SELECTFONT D (\d+)|SETCHAR (C|O) (\S+)|MOVERIGHT R (-?[0-9.]+)|MOVEUP R (-?[0-9.]+))\)', mm.group(1))
            ch['map'] = ops
        info['chars'][code] = ch
    return info


def load_tfm(name):
    vf = kpse(name + '.vf')
    tfm = kpse(name + '.tfm')
    if vf:
        return parse_pl(run('vftovp', vf, tfm)), True
    return parse_pl(run('tftopl', tfm)), False


def resolve(name, code):
    """記号フォントの文字→（実フォントの名前，文字コード，dx，dy，倍率）．dx，dyは設計サイズ単位"""
    info, isvf = load_tfm(name)
    if not isvf:
        return name, code, 0.0, 0.0, 1.0
    font, dx, dy, sc = 0, 0.0, 0.0, 1.0
    for op in info['chars'][code]['map']:
        if op[0].startswith('SELECTFONT'):
            font = int(op[1])
        elif op[0].startswith('MOVERIGHT'):
            dx += float(op[4])
        elif op[0].startswith('MOVEUP'):
            dy += float(op[5])
        elif op[0].startswith('SETCHAR'):
            c = ord(op[3]) if op[2] == 'C' else int(op[3], 8)
            base, at = info['mapfont'][font]
            bn, bc, bdx, bdy, bsc = resolve(base, c)
            return bn, bc, dx + bdx, dy + bdy, at * bsc
    raise RuntimeError('no SETCHAR for %s %d' % (name, code))


_maplines = None
def maplookup(tfmname):
    global _maplines
    if _maplines is None:
        _maplines = open(kpse('pdftex.map'), errors='ignore').read().split('\n')
    for l in _maplines:
        if l.split(' ')[0] == tfmname:
            enc = re.search(r'<\[?\s*([^\s<]+\.enc)', l)
            pfb = re.search(r'<<?\s*([^\s<]+\.pf[ab])', l)
            return (enc.group(1) if enc else None), pfb.group(1)
    raise RuntimeError('map line not found: ' + tfmname)


def encoding(encfile):
    t = open(kpse(encfile), errors='ignore').read()
    t = re.sub(r'%.*', '', t)
    return re.findall(r'/([^\s/\[\]]+)', t[t.index('['):])


_t1cache = {}
def glyph_path(tfmname, code):
    """実フォントの文字のアウトライン（フォント単位＝設計サイズの1/1000）"""
    enc, pfb = maplookup(tfmname)
    if pfb not in _t1cache:
        f = T1Font(kpse(pfb))
        f.parse()
        _t1cache[pfb] = f
    f = _t1cache[pfb]
    gname = encoding(enc)[code] if enc else f['Encoding'][code]
    pen = RecordingPen()
    f['CharStrings'][gname].draw(pen)
    fm = f['FontMatrix'][0] * 1000
    return pen.value, fm


# ---------- 図形 ----------
def xform(rec, fn):
    out = []
    for op, pts in rec:
        out.append((op, tuple(fn(*p) for p in pts)))
    return out


def bbox(rec):
    xs = [p[0] for op, pts in rec for p in pts]
    ys = [p[1] for op, pts in rec for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def component(name, code, x0, units):
    """記号フォントの文字codeのアウトラインを，x0（設計サイズ単位）だけ右に置いたもの"""
    bn, bc, dx, dy, sc = resolve(name, code)
    rec, fm = glyph_path(bn, bc)
    k = fm * sc
    return xform(rec, lambda x, y: (x * k + (x0 + dx) * units, y * k + dy * units))


def stroke(p1, p2, t, cap):
    """p1からp2への太さtの線（capはr：丸，b：切りっぱなし）のアウトライン"""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy * t / 2, ux * t / 2
    a = (p1[0] + nx, p1[1] + ny); b = (p2[0] + nx, p2[1] + ny)
    c = (p2[0] - nx, p2[1] - ny); d = (p1[0] - nx, p1[1] - ny)
    rec = [('moveTo', (a,)), ('lineTo', (b,))]
    if cap == 'r':
        r, K = t / 2, 0.5522847498 * t / 2
        # p2のまわりの半円（bからc，外側を回る）
        m = (p2[0] + ux * r, p2[1] + uy * r)
        rec.append(('curveTo', ((b[0] + ux * K, b[1] + uy * K), (m[0] + nx / r * K, m[1] + ny / r * K), m)))
        rec.append(('curveTo', ((m[0] - nx / r * K, m[1] - ny / r * K), (c[0] + ux * K, c[1] + uy * K), c)))
    else:
        rec.append(('lineTo', (c,)))
    rec.append(('lineTo', (d,)))
    if cap == 'r':
        r, K = t / 2, 0.5522847498 * t / 2
        m = (p1[0] - ux * r, p1[1] - uy * r)
        rec.append(('curveTo', ((d[0] - ux * K, d[1] - uy * K), (m[0] - nx / r * K, m[1] - ny / r * K), m)))
        rec.append(('curveTo', ((m[0] + nx / r * K, m[1] + ny / r * K), (a[0] - ux * K, a[1] - uy * K), a)))
    rec.append(('closePath', ()))
    return rec


def slashes(cx, cy, ux, uy, b, t, cap):
    """folarrow.styの\\fol@strokesと同じ3本線"""
    s = SPAN * b
    k = max(0.0, s - t) / s if cap == 'r' else 1.0
    sg = 1 if (LEAN * ux - uy) * (LEAN * uy + ux) >= 0 else -1
    vx = 0.5 * k * s * (sg * LEAN * ux - uy)
    vy = 0.5 * k * s * (sg * LEAN * uy + ux)
    out = []
    for i in (-1, 0, 1):
        px, py = cx + i * GAP * b * ux, cy + i * GAP * b * uy
        out += stroke((px - vx, py - vy), (px + vx, py + vy), t, cap)
    return out


def topath(rec):
    path = pathops.Path()
    pen = path.getPen()
    for op, pts in rec:
        getattr(pen, op)(*pts)
    return path


def union(rec, add=None):
    """重なりを除いた輪郭（外側を反時計回り）．addを与えると，recとaddを別々の図形として合わせる
    （それぞれの中で重なりを解いてから合わせるので，recとaddの輪郭の向きが逆でも穴にならない）．"""
    path = topath(rec)
    if add:
        path = pathops.op(path, topath(add), pathops.PathOp.UNION, fix_winding=True)
    else:
        path.simplify(fix_winding=True)
    out = RecordingPen()
    path.draw(out)
    # 輪郭ごとの向きをType 1の慣習（外側を反時計回り）にそろえる
    contours, cur = [], []
    for op, pts in out.value:
        cur.append((op, pts))
        if op in ('closePath', 'endPath'):
            contours.append(cur); cur = []
    def area(c):
        pts = [p for op, ps in c for p in ps]
        return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2
    big = max(contours, key=lambda c: abs(area(c)))
    if area(big) < 0:
        contours = [reverse(c) for c in contours]
    return [x for c in contours for x in c]


def reverse(c):
    """1つの輪郭の向きを逆にする"""
    segs, start, cur = [], None, None
    for op, pts in c:
        if op == 'moveTo':
            start = cur = pts[0]
        elif op in ('lineTo', 'curveTo', 'qCurveTo'):
            segs.append((op, cur, pts)); cur = pts[-1]
    if cur != start:
        segs.append(('lineTo', cur, (start,)))
    out = [('moveTo', (start,))]
    for op, p0, pts in reversed(segs):
        if op == 'lineTo':
            out.append(('lineTo', (p0,)))
        elif op == 'curveTo':
            out.append(('curveTo', (pts[1], pts[0], p0)))
        else:
            out.append(('qCurveTo', tuple(reversed(pts[:-1])) + (p0,)))
    out.append(('closePath', ()))
    return out


# ---------- Type 1とTFMの書き出し ----------
def charstring(rec, width):
    lines = ['0 %d hsbw' % round(width)]
    cx = cy = 0
    for op, pts in rec:
        if op == 'qCurveTo':
            raise RuntimeError('quadratic curve')
        pts = [(round(x), round(y)) for x, y in pts]
        if op == 'moveTo':
            lines.append('%d %d rmoveto' % (pts[0][0] - cx, pts[0][1] - cy)); cx, cy = pts[0]
        elif op == 'lineTo':
            lines.append('%d %d rlineto' % (pts[0][0] - cx, pts[0][1] - cy)); cx, cy = pts[0]
        elif op == 'curveTo':
            a, b, c = pts
            lines.append('%d %d %d %d %d %d rrcurveto' % (a[0] - cx, a[1] - cy, b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]))
            cx, cy = c
        elif op == 'closePath':
            lines.append('closepath')
    lines.append('endchar')
    return '\n\t'.join(lines)


def write_type1(path, psname, glyphs, bb, notice, weight='Medium'):
    enc = ''.join('dup %d /%s put\n' % (i, n) for i, n in enumerate(NAMES))
    cs = ''.join('/%s {\n\t%s\n\t} ND\n' % (n, charstring(rec, w)) for n, (rec, w) in glyphs.items())
    t1 = f"""%!PS-AdobeFont-1.0: {psname} 1.0
%%Title: {psname}
%Notice: {notice}
%%EndComments
11 dict begin
/FontType 1 def
/FontMatrix [0.001 0 0 0.001 0 0 ]readonly def
/FontName /{psname} def
/FontBBox {{{bb[0]} {bb[1]} {bb[2]} {bb[3]} }}readonly def
/PaintType 0 def
/FontInfo 6 dict dup begin
 /version (1.0) readonly def
 /Notice ({notice}) readonly def
 /FullName ({psname}) readonly def
 /FamilyName (FolArrow) readonly def
 /Weight ({weight}) readonly def
 /ItalicAngle 0 def
end readonly def
/Encoding 256 array
 0 1 255 {{ 1 index exch /.notdef put}} for
{enc}readonly def
currentdict end
currentfile eexec
dup /Private 8 dict dup begin
/RD{{string currentfile exch readstring pop}}executeonly def
/ND{{noaccess def}}executeonly def
/NP{{noaccess put}}executeonly def
/BlueValues [] def
/MinFeature {{16 16}} def
/password 5839 def
/lenIV 4 def
/Subrs 4 array
dup 0 {{
\t3 0 callothersubr
\tpop
\tpop
\tsetcurrentpoint
\treturn
\t}} NP
dup 1 {{
\t0 1 callothersubr
\treturn
\t}} NP
dup 2 {{
\t0 2 callothersubr
\treturn
\t}} NP
dup 3 {{
\treturn
\t}} NP
ND
2 index /CharStrings {len(glyphs) + 1} dict dup begin
/.notdef {{
\t0 0 hsbw
\tendchar
\t}} ND
{cs}end
end
readonly put
noaccess put
dup/FontName get exch definefont pop
mark currentfile closefile

cleartomark
"""
    with tempfile.NamedTemporaryFile('w', suffix='.t1', delete=False) as f:
        f.write(t1)
    subprocess.run(['t1asm', '-b', f.name, path], check=True)
    os.remove(f.name)


def write_tfm(path, ds, quad, metrics):
    pl = ['(FAMILY FOLARROW)', '(DESIGNSIZE R %.6f)' % ds,
          '(FONTDIMEN', '   (SLANT R 0)', '   (SPACE R 0)', '   (QUAD R %.6f)' % (quad / 1000), '   )']
    for i, (w, h, d) in enumerate(metrics):
        pl.append('(CHARACTER O %o (CHARWD R %.6f) (CHARHT R %.6f) (CHARDP R %.6f))' % (i, w / 1000, h / 1000, d / 1000))
    with tempfile.NamedTemporaryFile('w', suffix='.pl', delete=False) as f:
        f.write('\n'.join(pl) + '\n')
    r = subprocess.run(['pltotf', f.name, path], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr + open(f.name).read())
    os.remove(f.name)


# ---------- 尻の形（実測データ） ----------
def tail_caps():
    caps = {}
    if os.path.exists(FONTDEF):
        for m in re.finditer(r'\\fol@hdata\{([^}]+)\}\{[^}]*\}\{[^}]*\}\{([rb])\}\{([rb])\}', open(FONTDEF).read()):
            caps[m.group(1)] = m.group(2)
    return caps


# 元のフォントのライセンス（生成したフォントの/Noticeに，元のフォントの著作権表示と一緒に書く．
# 詳しくはlicenses/FONTS.mdと同梱のライセンス本文を参照）
LICENSES = {
    'cm': 'SIL Open Font License 1.1',
    'lm': 'GUST Font License',
    'ntx': 'GNU GPL with font exception (txfonts)',
    'tx': 'GNU GPL with font exception (txfonts)',
    'px': 'GNU GPL with font exception (pxfonts)',
    'zpl': 'GNU GPL with font exception (pxfonts/newpx)',
}
for _k in list(LICENSES):          # 太字（folcmb10など）は元と同じ
    LICENSES[_k + 'b'] = LICENSES[_k]


def source_notice(name):
    """記号フォントの→（文字0x21）の実体のType 1フォントのファイル名と/Notice"""
    bn, _, _, _, _ = resolve(name, 0o41)
    enc, pfb = maplookup(bn)
    if pfb not in _t1cache:
        f = T1Font(kpse(pfb))
        f.parse()
        _t1cache[pfb] = f
    info = _t1cache[pfb]['FontInfo']
    t = (info.get('Notice') or info.get('Copyright') or '').strip()
    # PostScriptの8進表記（\\050など）と逃がした文字（\\(など）を元の文字に戻す
    t = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), t)
    t = re.sub(r'\\(.)', r'\1', t)
    return pfb, t.rstrip('.')


def ps_string(t):
    """PostScriptの文字列の中に置けるようにする（ASCIIだけにし，括弧と\\を逃がす）"""
    t = t.encode('ascii', 'replace').decode()
    return t.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')




def build(name, fname, psname, caps):
    info, _ = load_tfm(name)
    ds = info['ds']
    U = 1000.0                                   # 設計サイズあたりのフォント単位
    quad = info['params']['QUAD'] * U
    axis = info['params'].get('AXISHEIGHT', 0.25) * U
    ch = info['chars']
    wM, wR, wL, wD = ch[0]['wd'], ch[0o41]['wd'], ch[0o40]['wd'], ch[0o43]['wd']
    mu3 = 3 / 18 * info['params']['QUAD']        # \joinrelの-3mu（設計サイズ単位）
    M = component(name, 0, 0, U)
    bM = bbox(M)
    t = bM[3] - bM[1]                            # 軸の太さ
    cy = (bM[1] + bM[3]) / 2                     # 軸の中心の高さ
    Rarr = component(name, 0o41, 0, U)
    b = bbox(Rarr)[3] - bbox(Rarr)[1]            # 矢頭の幅
    cap = caps.get(name) or caps.get(re.sub(r'\d+$', '', name)) or 'b'
    glyphs, metrics = {}, []

    def finish(rec, width, ux, uy, center):
        full = union(rec, slashes(center[0], center[1], ux, uy, b, t, cap))
        return full, width

    # → ：マイナス記号＋（\joinrel）＋→
    R = M + component(name, 0o41, wM - mu3, U)
    bb = bbox(R)
    W = (wM - mu3 + wR) * U
    glyphs['arrowright'] = finish(R, W, 1, 0, ((bb[0] + bb[2]) / 2, cy))
    # ← ：←＋（\joinrel）＋マイナス記号
    Lft = component(name, 0o40, 0, U) + component(name, 0, wL - mu3, U)
    bb = bbox(Lft)
    W = (wL - mu3 + wM) * U
    glyphs['arrowleft'] = finish(Lft, W, -1, 0, ((bb[0] + bb[2]) / 2, cy))
    # ↓↑ ：→（\longrightarrow）の字形をそのまま回す
    H = R
    hb = bbox(H)
    hx = (hb[0] + hb[2]) / 2
    # 幅は↓の幅と，3本線の横の広がり（斜線の長さ＋太さ）に左右のアキを足したものの大きいほう
    Wv = max(wD * U, SPAN * b + t + 2 * SIDE * quad)
    for gname, sgn in (('arrowdown', -1), ('arrowup', 1)):
        # 軸の中心(hx, cy)を原点に移して回す：下向きは(x,y)→(y,-x)，上向きは(x,y)→(-y,x)
        if sgn < 0:
            V = xform(H, lambda x, y: (y - cy + Wv / 2, -(x - hx) + axis))
        else:
            V = xform(H, lambda x, y: (-(y - cy) + Wv / 2, (x - hx) + axis))
        glyphs[gname] = finish(V, Wv, 0, sgn, (Wv / 2, axis))
    # 寸法（TFM）：幅は組み方どおり，高さ・深さは3本線を含む字面の範囲
    for n in NAMES:
        rec, w = glyphs[n]
        x0, y0, x1, y1 = bbox(rec)
        metrics.append((w, max(0.0, y1), max(0.0, -y0)))
    allb = [bbox(r) for r, w in glyphs.values()]
    fb = (round(min(a[0] for a in allb)), round(min(a[1] for a in allb)),
          round(max(a[2] for a in allb)), round(max(a[3] for a in allb)))
    fam = re.match(r'fol([a-z]+)', fname).group(1)
    pfb, srcnotice = source_notice(name)
    # txfonts，pxfonts（とそれを受け継ぐnewtx，newpx）の/Noticeは「Version 3.0, GPL」などだけで
    # 著作権者の名前がないので，txfonts，pxfontsの著作権の告知（licenses/TXFONTS-PXFONTS-COPYRIGHT.txt）
    # にある名前を補う
    if fam.rstrip('b') in ('ntx', 'tx', 'px', 'zpl') and 'Copyright' not in srcnotice:
        srcnotice = 'Copyright (c) Young Ryu (txfonts/pxfonts); ' + srcnotice
    notice = ps_string('Derived from %s by the folarrow package. Original notice: %s. License: %s.'
                       % (pfb, srcnotice, LICENSES[fam]))
    write_type1(os.path.join(OUT_PFB, fname + '.pfb'), psname, glyphs, fb, notice,
                'Bold' if 'bsy' in name else 'Medium')
    write_tfm(os.path.join(OUT_TFM, fname + '.tfm'), ds, quad, metrics)
    return {'b': b / U, 't': t / U, 'cap': cap}


def main():
    for d in (OUT_PFB, OUT_TFM, OUT_MAP):
        os.makedirs(d, exist_ok=True)
    caps = tail_caps()
    maplines, deflines = [], []
    only = sys.argv[1:]
    for name, (fname, psname) in sorted(TARGETS.items()):
        if only and name not in only:
            continue
        if not kpse(name + '.tfm'):
            print('skip (not installed):', name); continue
        r = build(name, fname, psname, caps)
        maplines.append('%s %s <%s.pfb' % (fname, psname, fname))
        deflines.append('\\fol@glyphfont{%s}{%s}' % (name, fname))
        print('%-8s -> %-8s b=%.3f t=%.3f cap=%s' % (name, fname, r['b'], r['t'], r['cap']))
    if not only:
        with open(os.path.join(OUT_MAP, 'folarrow.map'), 'w') as f:
            f.write('% folarrow.map：folarrowの本文用の矢印のフォント（元のフォントから作成した）\n')
            f.write('\n'.join(maplines) + '\n')
        with open(OUT_DEF, 'w') as f:
            f.write('%% folarrow-glyphs.def：本文用の矢印のフォントがある記号フォント\n')
            f.write('%% 矢印のフォントは元のフォントから作成した．\\fol@glyphfont{記号フォントの名前}{このフォントのファイル名}\n')
            f.write('\n'.join(deflines) + '\n\\endinput\n')


if __name__ == '__main__':
    main()
