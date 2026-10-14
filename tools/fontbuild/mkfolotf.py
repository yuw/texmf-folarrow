#!/usr/bin/env python3
"""folarrowの本文用の矢印（→←↓↑に3本線）の，OpenTypeの数式フォント用のOTFを作る．

使い方：python3 mkfolotf.py [略号 ...]
  必要なもの：fontTools，skia-pathops，TeX Liveのkpsewhich（PATHに通しておく）．
  略号を並べるとその書体だけ作る（folarrow-otf.defは書き換えない）．

unicode-mathで使うOpenTypeの数式フォントごとに，次の4文字のOTFを1本ずつ作る．
  U+2192 arrowright：U+27F6（\\longrightarrow）の字形に3本線
  U+2190 arrowleft ：U+27F5（\\longleftarrow）の字形に3本線
  U+2193 arrowdown ：U+27F6の字形を時計回りに90°回し，数式の軸（MATH表のAxisHeight）に中心を合わせたもの
  U+2191 arrowup   ：同じものを反時計回りに90°回したもの
元のフォントが矢印に添字用の字形（sstyの代替字形）を持つときは，それぞれから同じように作った字形を
arrowright.ssty1などの名前で加え，同じ並びのssty機能（代替字形の置き換え）を持たせる．
TeXでは元のフォントと同じ「+ssty=0」などの指定で読むので，同じ字形が選ばれる．

3本線の寸法はType 1版（mkfolfonts.py）と同じ：長さ＝矢頭の幅，間隔＝0.35×矢頭の幅，傾き0.25，
太さ＝軸の太さ．軸の太さと高さは矢印の輪郭を縦に切って測り，3本線の中心は字面の中央（軸の上）に置く．
矢印の尻が丸ければ3本線の端も丸くする（尻の形も輪郭から判定する）．

出力（このリポジトリのTDSの中．環境変数FOLARROW_ROOTを与えると，その下のTDSの中）：
  fonts/opentype/public/folarrow/folu-<略号>.otf
  tex/latex/folarrow/folarrow-otf.def（元のフォントを見分ける文字列→このフォントのファイル名の表．
    見分ける文字列は，ファイル名，PostScript名，フルネーム，ファミリー名を小文字にして英数字だけ残したもの）
ファイル名とフォント名には，元のフォントの予約フォント名（OFLのReserved Font Name）を含めない．
"""
import math, os, subprocess, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkfolfonts import slashes, union, bbox, xform, SPAN, SIDE, ROOT

OUT_OTF = os.path.join(ROOT, 'fonts', 'opentype', 'public', 'folarrow')
OUT_DEF = os.path.join(ROOT, 'tex', 'latex', 'folarrow', 'folarrow-otf.def')
BULGE = 0.35    # 尻の丸みの判定（analyseを参照）

# 略号：元のフォントのファイル．略号には元のフォントの名前（予約フォント名）を含めない．
FONTS = {
    'lmm': 'latinmodern-math.otf',
    'ncm': 'NewCMMath-Regular.otf', 'ncmb': 'NewCMMath-Bold.otf', 'ncmk': 'NewCMMath-Book.otf',
    'nsm': 'NewCMSansMath-Regular.otf',
    's2m': 'STIXTwoMath-Regular.otf', 's1m': 'STIXMath-Regular.otf',
    'tgt': 'texgyretermes-math.otf', 'tgp': 'texgyrepagella-math.otf', 'tgb': 'texgyrebonum-math.otf',
    'tgs': 'texgyreschola-math.otf', 'tgd': 'texgyredejavu-math.otf',
    'lbm': 'LibertinusMath-Regular.otf',
    'frm': 'FiraMath-Regular.otf',
    'xtm': 'XITSMath-Regular.otf', 'xtmb': 'XITSMath-Bold.otf',
    'asm': 'Asana-Math.otf',
    'erm': 'Erewhon-Math.otf', 'ermb': 'Erewhon-Math-Bold.otf',
    'kmt': 'KpMath-Regular.otf', 'kmtb': 'KpMath-Bold.otf', 'kmtl': 'KpMath-Light.otf',
    'kmtm': 'KpMath-Semibold.otf', 'kmts': 'KpMath-Sans.otf', 'kmtsb': 'KpMath-SansBold.otf',
    'gnm': 'GFSNeohellenicMath.otf',
    'ipm': 'IBMPlexMath-Regular.otf',
    'arm': 'ArsenalMath-Sans.otf', 'armb': 'ArsenalMath-SansBold.otf',
    'ccm': 'Concrete-Math.otf', 'ccmb': 'Concrete-Math-Bold.otf',
    'eum': 'Euler-Math.otf',
    'gam': 'Garamond-Math.otf',
    'lsm': 'LeteSansMath.otf', 'lsmb': 'LeteSansMath-Bold.otf',
    'lcm': 'Luciole-Math.otf', 'lcmb': 'Luciole-Math-Bold.otf',
    'osm': 'OldStandard-Math.otf',
    'pnm': 'PennstanderMath-Regular.otf', 'pnmt': 'PennstanderMath-Thin.otf',
    'pnmxl': 'PennstanderMath-ExtraLight.otf', 'pnml': 'PennstanderMath-Light.otf',
    'pnmm': 'PennstanderMath-Medium.otf', 'pnmsb': 'PennstanderMath-SemiBold.otf',
    'pnmb': 'PennstanderMath-Bold.otf', 'pnmxb': 'PennstanderMath-ExtraBold.otf',
    'pnmk': 'PennstanderMath-Black.otf',
    'xcm': 'XCharter-Math.otf', 'xcmb': 'XCharter-Math-Bold.otf',
}


def norm(x):
    return ''.join(c for c in x.lower() if c.isalnum())


def match_keys(src, f):
    """元のフォントを見分ける文字列：ファイル名（拡張子あり・なし），PostScript名，フルネーム，
    標準の太さ（typographic subfamilyがRegular）ならファミリー名．TeXでは\fontnameからフォント名の部分を取り出し，小文字にして
    英数字だけ残したものと比べる（完全一致）．"""
    nm = f['name']
    g = lambda i: nm.getDebugName(i) or ''
    keys = {norm(src), norm(os.path.splitext(src)[0]), norm(g(6)), norm(g(4))}
    if (g(17) or g(2)).lower() == 'regular':
        keys |= {norm(g(1)), norm(g(16))}
    return {k for k in keys if k}


# フォントの中の表示からライセンスを読めないもの（TeX Liveのパッケージ情報で確かめたもの）
LICENSE_OVERRIDE = {
    'ccmb': 'SIL Open Font License 1.1',   # concmath-otf
    'gnm': 'SIL Open Font License 1.1',    # gfsneohellenicmath
    'tgd': 'GUST Font License',            # tex-gyre-math（DejaVu由来．元はBitstream Vera）
    'xtmb': 'SIL Open Font License 1.1',   # xits
}


def license_of(f):
    t = ' '.join((f['name'].getDebugName(i) or '') for i in (0, 13, 14))
    if 'Open Font License' in t or 'OFL' in t:
        return 'SIL Open Font License 1.1'
    if 'GUST' in t:
        return 'GUST Font License'
    return 'the license of the source font'


UNI = {'arrowright': 0x2192, 'arrowleft': 0x2190, 'arrowdown': 0x2193, 'arrowup': 0x2191}


def kpse(name):
    return subprocess.run(['kpsewhich', name], capture_output=True, text=True).stdout.strip() or None


def flatten(rec, n=16):
    """輪郭を折れ線の列にする"""
    polys, cur = [], []
    for op, pts in rec:
        if op == 'moveTo':
            cur = [pts[0]]
        elif op == 'lineTo':
            cur.append(pts[0])
        elif op == 'curveTo':
            a = cur[-1]; b, c, d = pts
            for i in range(1, n + 1):
                s = i / n; u = 1 - s
                cur.append((u**3*a[0] + 3*u*u*s*b[0] + 3*u*s*s*c[0] + s**3*d[0],
                            u**3*a[1] + 3*u*u*s*b[1] + 3*u*s*s*c[1] + s**3*d[1]))
        elif op == 'qCurveTo':
            a = cur[-1]
            for q in range(len(pts) - 1):
                c = pts[q]
                d = pts[q + 1] if q == len(pts) - 2 else ((pts[q][0] + pts[q+1][0]) / 2, (pts[q][1] + pts[q+1][1]) / 2)
                for i in range(1, n + 1):
                    s = i / n; u = 1 - s
                    cur.append((u*u*a[0] + 2*u*s*c[0] + s*s*d[0], u*u*a[1] + 2*u*s*c[1] + s*s*d[1]))
                a = d
        elif op in ('closePath', 'endPath'):
            if cur:
                polys.append(cur)
            cur = []
    return polys


def vslice(rec, x0):
    """縦の線x=x0と輪郭の交点のyを，下から順に（字面の区間の組で）返す"""
    ys = []
    for poly in flatten(rec):
        for i in range(len(poly)):
            (xa, ya), (xb, yb) = poly[i], poly[(i + 1) % len(poly)]
            if (xa <= x0 < xb) or (xb <= x0 < xa):
                ys.append(ya + (x0 - xa) * (yb - ya) / (xb - xa))
    ys.sort()
    return [(ys[i], ys[i + 1]) for i in range(0, len(ys) - 1, 2)]


def shaft(rec, x0, ymid):
    """x=x0で，ymidにいちばん近い字面の区間（軸の断面）"""
    segs = vslice(rec, x0)
    return min(segs, key=lambda s: 0 if s[0] <= ymid <= s[1] else min(abs(s[0] - ymid), abs(s[1] - ymid)))


def draw(gs, gname):
    pen = RecordingPen()
    gs[gname].draw(pen)
    return union(pen.value)


def analyse(rec, tail_left):
    """矢印の輪郭から，矢頭の幅b，軸の太さt，軸の中心の高さcy，尻の形capを求める"""
    x0, y0, x1, y1 = bbox(rec)
    b = y1 - y0
    ymid = (y0 + y1) / 2
    # 軸を尻の側から35%の位置で切る
    xs = x0 + 0.35 * (x1 - x0) if tail_left else x1 - 0.35 * (x1 - x0)
    lo, hi = shaft(rec, xs, ymid)
    t, cy = hi - lo, (lo + hi) / 2
    # 尻の形：端から軸が全幅（太さの98%）になるまでの距離．半円の尻なら太さの0.5倍，切りっぱなしなら0．
    # 太さのBULGE倍以上なら丸い尻とする（浅い弧のLibertinus Mathは切りっぱなしになる．
    # 画像から判定した実測データ（folarrow-fonts.def）と同じ結果）．
    d = 0.0
    while d < t:
        xe = x0 + d if tail_left else x1 - d
        if vslice(rec, xe):
            lo2, hi2 = shaft(rec, xe, cy)
            if hi2 - lo2 >= 0.98 * t:
                break
        d += 0.01 * t
    cap = 'r' if d >= BULGE * t else 'b'
    return b, t, cy, cap


def misaligned_vertical(f, gs, cmap):
    """↓↑の伸縮の部品（MATH表のGlyphAssembly）で，軸の部品と矢頭の部品の軸の位置がずれているか．
    ずれている（Pennstander Mathの↓）と，大きな区切り記号として組んだ矢印が崩れる．"""
    from fontTools.pens.boundsPen import BoundsPen
    upm = f['head'].unitsPerEm
    mv = f['MATH'].table.MathVariants
    cov = mv.VertGlyphCoverage.glyphs if mv.VertGlyphCoverage else []
    for u in (0x2193, 0x2191):
        g = cmap.get(u)
        if g not in cov:
            continue
        asm = mv.VertGlyphConstruction[cov.index(g)].GlyphAssembly
        if not asm:
            continue
        heads, shafts = [], []
        for part in asm.PartRecords:
            bp = BoundsPen(gs); gs[part.glyph].draw(bp)
            x0, y0, x1, y1 = bp.bounds
            (heads if x1 - x0 > 0.3 * upm else shafts).append((x0 + x1) / 2)
        if heads and shafts and max(abs(h - c) for h in heads for c in shafts) > 0.05 * upm:
            return True
    return False


def broken_vertical(f):
    """↓↑の伸縮の部品の寸法が壊れているか（負の値を符号なしで書いたような，ありえない大きさ）．
    New Computer Modern Math Boldの↓がそうで，XeTeXは大きな区切り記号を作ろうとして止まらなくなる．"""
    upm = f['head'].unitsPerEm
    mv = f['MATH'].table.MathVariants
    cov = mv.VertGlyphCoverage.glyphs if mv.VertGlyphCoverage else []
    cmap = f.getBestCmap()
    for u in (0x2193, 0x2191):
        g = cmap.get(u)
        if g not in cov:
            continue
        asm = mv.VertGlyphConstruction[cov.index(g)].GlyphAssembly
        for part in (asm.PartRecords if asm else []):
            if (part.FullAdvance > 10 * upm or part.StartConnectorLength > part.FullAdvance
                    or part.EndConnectorLength > part.FullAdvance):
                return True
    return False


def build(code):
    src = FONTS[code]
    path = kpse(src)
    if not path:
        print('skip (not installed):', src)
        return None
    f = TTFont(path)
    lic = LICENSE_OVERRIDE.get(code) or license_of(f)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    upm = f['head'].unitsPerEm
    axis = f['MATH'].table.MathConstants.AxisHeight.Value
    hmtx = f['hmtx']
    # sstyの代替字形
    alts = {}
    for fr in f['GSUB'].table.FeatureList.FeatureRecord:
        if fr.FeatureTag != 'ssty':
            continue
        for li in fr.Feature.LookupListIndex:
            lk = f['GSUB'].table.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 7:
                    st = st.ExtSubTable
                m = getattr(st, 'alternates', None)
                if m:
                    for k, v in m.items():
                        alts.setdefault(k, list(v))
                m = getattr(st, 'mapping', None)
                if m and not hasattr(st, 'alternates'):
                    for k, v in m.items():
                        alts.setdefault(k, [v])
    # U+27F6，U+27F5（長い矢印）がないフォント（XITS Math Bold）では，\longrightarrowを
    # \relbar\joinrel\rightarrowで組むのと同じく，マイナス記号と→（←とマイナス記号）を
    # 3/18 em重ねて並べたものにする
    composed = 0x27F6 not in cmap or 0x27F5 not in cmap
    if composed:
        gR, gL, gM = cmap[0x2192], cmap[0x2190], cmap[0x2212]
    else:
        gR, gL = cmap[0x27F6], cmap[0x27F5]
    gD = cmap[0x2193]
    levels = 1 + max(len(alts.get(gR, [])), len(alts.get(gL, [])))
    glyphs, info = {}, []
    for lv in range(levels):
        sfx = '' if lv == 0 else '.ssty%d' % lv
        pick = lambda g: g if lv == 0 else (alts.get(g, [])[lv - 1] if len(alts.get(g, [])) >= lv else g)
        R, L = pick(gR), pick(gL)
        recR, recL = draw(gs, R), draw(gs, L)
        if composed:
            M = pick(gM)
            recM, j = draw(gs, M), 3 * upm / 18
            shift = lambda rec, dx: xform(rec, lambda x, y: (x + dx, y))
            advR = hmtx[M][0] - j + hmtx[R][0]
            advL = hmtx[L][0] - j + hmtx[M][0]
            recR = union(recM, shift(recR, hmtx[M][0] - j))
            recL = union(recL, shift(recM, hmtx[L][0] - j))
        # 送り幅：字面が送り幅からはみ出す字形（XCharter Math BoldのU+27F6，U+27F5は送り幅1000に
        # 対して字面が1524まで伸びる）は，字面の右端に左の余白を足した幅にする
        def advance(g, rec):
            x0, _, x1, _ = bbox(rec)
            return x1 + max(0, x0) if x1 > hmtx[g][0] else hmtx[g][0]
        # → と ←
        b, t, cy, cap = analyse(recR, True)
        bb = bbox(recR)
        glyphs['arrowright' + sfx] = (union(recR, slashes((bb[0] + bb[2]) / 2, cy, 1, 0, b, t, cap)),
                                      advR if composed else advance(R, recR))
        bL, tL, cyL, capL = analyse(recL, False)
        bb = bbox(recL)
        glyphs['arrowleft' + sfx] = (union(recL, slashes((bb[0] + bb[2]) / 2, cyL, -1, 0, bL, tL, capL)),
                                     advL if composed else advance(L, recL))
        # ↓ と ↑：→を回す
        bb = bbox(recR)
        hx = (bb[0] + bb[2]) / 2
        Wv = max(hmtx[pick(gD)][0], SPAN * b + t + 2 * SIDE * upm)
        down = xform(recR, lambda x, y: (y - cy + Wv / 2, -(x - hx) + axis))
        up = xform(recR, lambda x, y: (-(y - cy) + Wv / 2, (x - hx) + axis))
        glyphs['arrowdown' + sfx] = (union(down, slashes(Wv / 2, axis, 0, -1, b, t, cap)), Wv)
        glyphs['arrowup' + sfx] = (union(up, slashes(Wv / 2, axis, 0, 1, b, t, cap)), Wv)
        info.append('%s%s b=%.0f t=%.1f cap=%s/%s%s' % (code, sfx, b, t, cap, capL, ' (composed)' if composed else ''))
    write_otf(code, src, lic, f, glyphs, levels)
    family = f['name'].getDebugName(16) or f['name'].getDebugName(1)
    return info, match_keys(src, f), family, misaligned_vertical(f, gs, cmap), broken_vertical(f)


def write_otf(code, src, lic, f, glyphs, levels):
    # spaceは中身のない字形．XeTeXはフォントを読むときに空白（U+0020）の幅を調べ，なければ
    # 「Missing character」と記録するので入れておく
    order = ['.notdef', 'space'] + list(glyphs)
    psname = 'FolArrowU-' + code.upper()
    fb = FontBuilder(f['head'].unitsPerEm, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({**{u: n for n, u in UNI.items()}, 0x20: 'space'})
    charstrings, metrics = {}, {}
    p = T2CharStringPen(0, None)
    charstrings['.notdef'] = p.getCharString(); metrics['.notdef'] = (0, 0)
    sw = round(f['head'].unitsPerEm / 4)
    p = T2CharStringPen(sw, None)
    charstrings['space'] = p.getCharString(); metrics['space'] = (sw, 0)
    for n, (rec, w) in glyphs.items():
        p = T2CharStringPen(round(w), None)
        for op, pts in rec:
            getattr(p, op)(*[(round(x), round(y)) for x, y in pts])
        charstrings[n] = p.getCharString()
        x0 = bbox(rec)[0]
        metrics[n] = (round(w), round(x0))
    copyright = (f['name'].getDebugName(0) or '').strip()
    # CFFのNoticeには派生の旨とライセンスを，Copyrightには元の著作権表示の全文を入れる（途中で切らない）
    ascii_ = lambda t: t.encode('ascii', 'replace').decode()
    fb.setupCFF(psname, {'FullName': psname,
                         'Notice': ascii_('Derived from %s by the folarrow package. License: %s.' % (src, lic)),
                         'Copyright': ascii_(copyright)}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    ys = [v for rec, w in glyphs.values() for v in (bbox(rec)[1], bbox(rec)[3])]
    fb.setupHorizontalHeader(ascent=round(max(ys)), descent=round(min(ys)))
    fb.setupNameTable({
        'copyright': copyright or 'See %s' % src,
        'familyName': 'FolArrowU %s' % code.upper(),
        'styleName': 'Regular',
        'uniqueFontIdentifier': psname + ' 1.0',
        'fullName': psname,
        'psName': psname,
        'version': 'Version 1.0',
        'description': 'Arrows with three strokes for the folarrow LaTeX package, made from the glyphs of %s.' % src,
        'licenseDescription': 'This font is derived from %s and is licensed under the same license: %s.' % (src, lic),
        'licenseInfoURL': ('https://openfontlicense.org' if 'Open Font' in lic
                           else 'https://www.gust.org.pl/projects/e-foundry/licenses'),
    })
    # fsType=0：埋め込みなどに制限を付けない（OFL，GUSTの派生フォント）．fsSelection=0x40：Regular
    fb.setupOS2(fsType=0, fsSelection=0x40, achVendID='NONE',
                sTypoAscender=round(max(ys)), sTypoDescender=round(min(ys)),
                usWinAscent=max(0, round(max(ys))), usWinDescent=max(0, -round(min(ys))))
    fb.setupPost()
    if levels > 1:
        fea = ['languagesystem DFLT dflt;', 'languagesystem math dflt;', 'languagesystem latn dflt;',
               'feature ssty {']
        for n in UNI:
            fea.append('  sub %s from [%s];' % (n, ' '.join('%s.ssty%d' % (n, i) for i in range(1, levels))))
        fea.append('} ssty;')
        addOpenTypeFeaturesFromString(fb.font, '\n'.join(fea))
    fb.save(os.path.join(OUT_OTF, 'folu-%s.otf' % code))


def main():
    os.makedirs(OUT_OTF, exist_ok=True)
    only = sys.argv[1:]
    owner, families, badfam, brokenfonts = {}, {}, set(), set()
    for code in FONTS:
        if only and code not in only:
            continue
        r = build(code)
        if r:
            info, keys, family, bad, broken = r
            print('  '.join(info) + ('  (vertical assembly misaligned)' if bad else '')
                  + ('  (vertical assembly broken)' if broken else ''))
            if broken:
                brokenfonts.add(code)
            for k in keys:
                owner.setdefault(k, set()).add(code)
            families[code] = family
            if bad:
                badfam.add(family)
    if not only:
        lines = []
        for k in sorted(owner):
            if len(owner[k]) > 1:
                print('ambiguous key dropped:', k, sorted(owner[k]))
                continue
            code = next(iter(owner[k]))
            lines.append('\\fol@otfglyphfont{%s}{folu-%s.otf}' % (k, code))
            if families[code] in badfam:
                lines.append('\\fol@otfrotv{%s}' % k)
            elif code in brokenfonts:
                lines.append('\\fol@otfrotvxe{%s}' % k)
        with open(OUT_DEF, 'w') as fh:
            fh.write('%% folarrow-otf.def：本文用の矢印のOTFがあるOpenTypeの数式フォント\n')
            fh.write('%% 矢印のフォントは元のフォントから作成した．\\fol@otfglyphfont{見分ける文字列}{このフォントのファイル名}\n')
            fh.write('%% 見分ける文字列は，元のフォントのファイル名，PostScript名，フルネーム，ファミリー名を\n')
            fh.write('%% 小文字にして英数字だけ残したもの．\n')
            fh.write('%% \\fol@otfrotv{見分ける文字列}：↓↑の伸縮の部品がずれているフォント（とその同じファミリー）．\n')
            fh.write('%% 描いて組む縦向きの矢印の土台を，区切り記号ではなく横向きの矢印を回したものにする．\n')
            fh.write('%% \\fol@otfrotvxe{見分ける文字列}：↓↑の伸縮の部品の寸法が壊れていて，XeTeXが大きな区切り記号を\n')
            fh.write('%% 作れないフォント．XeTeXのときだけ，同じように横向きの矢印を回したものにする．\n')
            fh.write('\n'.join(lines) + '\n\\endinput\n')


if __name__ == '__main__':
    main()
