#!/usr/bin/env python3
"""数式フォントごとに矢印の矢頭の幅・軸の太さを実測し，folarrowの計算値と比べる．

使い方：
  python3 measure.py                 fonts.jsonの全設定を測る（結果はresults.json）
  python3 measure.py 名前 ...        指定した設定だけ測る（結果の同じ設定の行だけ差し替える）
  FOLOUT=results-uplatex.json ...    結果を書き出すファイルを変える
  python3 measure.py --report        results.jsonの内容を表にする
  FOLENGINE=uplatex python3 measure.py ...    Type 1系をupLaTeX＋dvipdfmxで組む
  FOLOTFENGINE=xelatex python3 measure.py ... OpenType系をXeLaTeXで組む
  FOLWORK=ディレクトリ python3 measure.py ...  作業用ディレクトリを指定する（既定では毎回新しく作る）

各設定で60pt角の小さなページに矢印を1つずつ組み，2400dpiのグレー画像にして字面の
範囲を測る．矢頭の幅は字面の外接矩形から，軸の太さは塗りの量から求める
（しきい値による量子化誤差を避けるため）．大きさは10pt，10.95pt，12pt，スタイルは
本文・添字・添字の添字．縦向きは\Big\downarrowと\foldownarrowの土台を測る．
folarrowが計算した値（\fol@b，\fol@t）と，矢印を持つフォントの名前・quadはログから読む．
表は「計算値／実測値」の比で，1.00が理想．
"""
import json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))   # このリポジトリ（TEXMFHOMEとして使う）
ENV = dict(os.environ, TEXMFHOME=ROOT)
# 作業用ディレクトリ（main()で決める）．TeXはカレントディレクトリのファイルを先に読むので，
# 決まった名前の共有の場所は使わず，FOLWORKの指定がなければ毎回新しく作る（ほかの利用者が
# 置いたファイルを読まないため）
WORK = None
DPI = 2400
PT = 72.27 / DPI


def configs():
    """fonts.json：[{"name": 設定名, "preamble": 数式フォントを読み込むプリアンブル}]．
    TeX Font Catalogueの「Fonts with Math Support」の各書体の使い方（Usage）と，
    OpenTypeの数式フォントをunicode-mathで読み込む設定などからなる．"""
    return [(c['name'], c['preamble']) for c in json.load(open(os.path.join(HERE, 'fonts.json')))]


SIZES = [('10', r'\normalsize'), ('11', r'\fontsize{10.95}{13}\selectfont'),
         ('12', r'\fontsize{12}{14}\selectfont')]
STYLES = [('t', r'\textstyle'), ('s', r'\scriptstyle'), ('ss', r'\scriptscriptstyle')]


def make_doc(pre):
    head = r'''\documentclass{article}
\usepackage[paperwidth=60pt,paperheight=60pt,margin=4pt]{geometry}
\usepackage{amsmath}
%s
\usepackage{folarrow}
\makeatletter\providecommand\rightarrowfill@{\arrowfill@\relbar\relbar\rightarrow}
\newcommand\folfill{\hbox to 30pt{\rightarrowfill@\displaystyle}}
\newcommand\folBigdown{\fol@Bigv\downarrow{-1}}\newcommand\folBigup{\fol@Bigv\uparrow{1}}\makeatother
\pagestyle{empty}\parindent0pt
\begin{document}
$x$\makeatletter
''' % pre
    body = []
    pages = []
    # ログ：各（大きさ，スタイル）で\rightarrowを持つフォントの名前とquad，folarrowの計算値
    for sz, szcmd in SIZES:
        for st, stcmd in STYLES:
            body.append(r'{%s$%s\fol@setff%s\fol@hfamily\fol@fam\fol@basename{\fol@ff\fol@fam}'
                        r'\edef\folq{\the\fontdimen6\fol@ff\fol@fam}\fol@hmetrics%s'
                        r'\typeout{FOL|%s|%s|\fol@fname|\folq|\fol@b|\fol@t}$}'
                        % (szcmd, stcmd, stcmd, stcmd, sz, st))
        # 縦向き：\downarrowの大きい字形のフォント
        body.append(r'{%s$\fol@setff\textstyle\fol@vfamily\fol@fam\fol@basename{\fol@ff\fol@fam}'
                    r'\edef\folq{\the\fontdimen6\fol@ff\fol@fam}\let\folfn\fol@fname'
                    r'\setbox0\hbox{$\Big\downarrow$}\fol@vmetrics\textstyle0{big}\let\bigb\fol@b\let\bigt\fol@t'
                    r'\fol@vbase\textstyle\downarrow\setbox0\box\z@\fol@vmetrics\textstyle0{inl}'
                    r'\let\capi\fol@cap\let\inlb\fol@b\let\inlt\fol@t'
                    r'\setbox0\hbox{$\Big\downarrow$}\fol@vmetrics\textstyle0{big}\let\capb\fol@cap'
                    r'\chardef\fol@hkindnum=0 \fol@hmetrics\textstyle\let\capl\fol@cap'
                    r'\chardef\fol@hkindnum=1 \fol@hmetrics\textstyle\let\capf\fol@cap\chardef\fol@hkindnum=0 '
                    r'\def\fol@vdir{-1}\setbox0\hbox{$\Big\downarrow$}\fol@vmetrics\textstyle0{big}\let\offbd\fol@off\let\acrbd\fol@acr'
                    r'\def\fol@vdir{1}\setbox0\hbox{$\Big\uparrow$}\fol@vmetrics\textstyle0{big}\let\offbu\fol@off\let\acrbu\fol@acr'
                    r'\def\fol@vdir{-1}\fol@vbase\textstyle\downarrow\setbox0\box\z@\fol@vmetrics\textstyle0{inl}\let\offid\fol@off\let\acrid\fol@acr'
                    r'\def\fol@vdir{1}\fol@vbase\textstyle\uparrow\setbox0\box\z@\fol@vmetrics\textstyle0{inl}\let\offiu\fol@off\let\acriu\fol@acr'
                    r'\chardef\fol@hkindnum=0 \fol@hmetrics\textstyle\let\offl\fol@off\let\acrl\fol@acr'
                    r'\chardef\fol@hkindnum=1 \fol@hmetrics\displaystyle\let\offf\fol@off\let\acrf\fol@acr\chardef\fol@hkindnum=0 '
                    r'\def\fol@hdir{-1}\chardef\fol@hkindnum=0 \fol@hmetrics\textstyle\let\offll\fol@off\let\acrll\fol@acr'
                    r'\chardef\fol@hkindnum=1 \fol@hmetrics\displaystyle\let\offfl\fol@off\let\acrfl\fol@acr\chardef\fol@hkindnum=0 \def\fol@hdir{1}'
                    r'\typeout{FOLOFF|%s|\offl|\offf|\offbd|\offbu|\offid|\offiu|\acrl|\acrf|\acrbd|\acrbu|\acrid|\acriu|\offll|\offfl|\acrll|\acrfl|}'
                    r'\typeout{FOLCAP|%s|\capl\capf\capb\capi|}'
                    r'\typeout{FOL3|%s|\folfn|\folq|\bigb|\bigt|\inlb|\inlt}$}' % (szcmd, sz, sz, sz))
    body.append(r'\makeatother')
    for sz, szcmd in SIZES:
        for st, stcmd in STYLES:
            pages.append(('ra', sz, st, r'{%s$%s\rightarrow$}' % (szcmd, stcmd)))
        pages.append(('big', sz, 't', r'{%s$\Big\downarrow$}' % szcmd))
        pages.append(('inl', sz, 't', r'{%s\makeatletter\fol@vbase\textstyle\downarrow\makeatother\box0}' % szcmd))
        pages.append(('minus', sz, 't', r'{%s$-$}' % szcmd))
        pages.append(('lra', sz, 't', r'{%s$\longrightarrow$}' % szcmd))
        pages.append(('fill', sz, 't', r'{%s$\folfill$}' % szcmd))
        # 斜線入りの矢印：斜線の中心と矢印の字面の中心の差を測る
        pages.append(('cbd', sz, 't', r'{%s$\folBigdown$}' % szcmd))
        pages.append(('cbu', sz, 't', r'{%s$\folBigup$}' % szcmd))
        pages.append(('cid', sz, 't', r'{%s$\foldownarrow$}' % szcmd))
        pages.append(('ciu', sz, 't', r'{%s$\foluparrow$}' % szcmd))
        pages.append(('chr', sz, 't', r'{%s$\folrightarrow$}' % szcmd))
        pages.append(('chf', sz, 't', r'{%s$\xfolrightarrow{\hphantom{MMM}}$}' % szcmd))
        pages.append(('chl', sz, 't', r'{%s$\folleftarrow$}' % szcmd))
        pages.append(('cfl', sz, 't', r'{%s$\xfolleftarrow{\hphantom{MMM}}$}' % szcmd))
    doc = head + '\n'.join(body) + '\n' + ''.join(
        r'\newpage\vspace*{8pt}\hspace*{4pt}' + p[3] + '\n' for p in pages) + r'\end{document}' + '\n'
    return doc, pages


def read_pgm(path):
    data = open(path, 'rb').read()
    m = re.match(rb'P5\s+(\d+)\s+(\d+)\s+(\d+)\s', data)
    return int(m.group(1)), int(m.group(2)), data[m.end():]


def ink(w, h, px, thr=128):
    rows = [y for y in range(h) if min(px[y * w:(y + 1) * w]) < thr]
    if not rows:
        return None
    cols = [x for x in range(w) if min(px[x::w]) < thr]
    return min(cols), min(rows), max(cols), max(rows)


def col_run(w, h, px, x, thr=128):
    ys = [y for y in range(h) if px[y * w + x] < thr]
    return max(ys) - min(ys) + 1 if ys else 0


def col_cov(w, h, px, xs):
    """列ごとの塗りの量（画素単位）の平均．しきい値による量子化誤差がない．"""
    return sum(sum(255 - v for v in px[x::w]) / 255 for x in xs) / len(xs)


def row_cov(w, h, px, ys):
    return sum(sum(255 - v for v in px[y * w:(y + 1) * w]) / 255 for y in ys) / len(ys)


def run(name, pre):
    d = WORK
    os.makedirs(d, exist_ok=True)
    otf = any(k in pre for k in ('fontspec', 'unicode-math', 'firamath-otf',
                                 'gfsneohellenicot', 'setmathfont'))
    engine = os.environ.get('FOLOTFENGINE', 'lualatex') if otf else os.environ.get('FOLENGINE', 'pdflatex')
    doc, pages = make_doc(pre)
    if engine == 'uplatex':
        doc = doc.replace(r'\documentclass{article}', r'\documentclass[dvipdfmx]{article}')
    open(os.path.join(d, name + '.tex'), 'w').write(doc)
    try:
        subprocess.run([engine, '-interaction=nonstopmode', name + '.tex'], cwd=d,
                       env=ENV, capture_output=True, timeout=300)
        if engine == 'uplatex':
            subprocess.run(['dvipdfmx', '-q', name + '.dvi'], cwd=d, env=ENV,
                           capture_output=True, timeout=300)
    except subprocess.TimeoutExpired:
        return {'name': name, 'engine': engine, 'error': 'timeout'}
    log = open(os.path.join(d, name + '.log'), errors='ignore').read()
    logj = re.sub(r'\n(?!FOL)', '', log)   # 79桁で折り返された行をつなぐ
    pdf = os.path.join(d, name + '.pdf')
    err = re.search(r'\n(!.*)', log)
    res = {'name': name, 'engine': engine, 'pre': pre, 'm': {}, 'f3': {}}
    if err:
        res['error'] = err.group(1)[:120]
    if not os.path.exists(pdf):
        res.setdefault('error', 'no pdf')
        return res
    for m in re.finditer(r'FOL\|(\w+)\|(\w+)\|(.*?)\|([0-9.]+)pt\|([0-9.]+)\|([0-9.]+)', logj):
        sz, st, fn, q, b, t = m.groups()
        res['m'][sz + st] = {'fn': fn.strip(), 'q': float(q), 'b': float(b), 't': float(t)}
    for m in re.finditer(r'FOL3\|(\w+)\|(.*?)\|([0-9.]+)pt\|([0-9.]+)\|([0-9.]+)\|([0-9.]+)\|([0-9.]+)', logj):
        sz, fn, q3, bb, bt, ib, it = m.groups()
        res['f3'][sz] = {'fn': fn.strip(), 'q3': float(q3), 'bigb': float(bb), 'bigt': float(bt),
                         'inlb': float(ib), 'inlt': float(it)}
    for m in re.finditer(r'FOLOFF\|(\w+)\|' + r'([-0-9.e]+)\|' * 16, logj):
        res['f3'].setdefault(m.group(1), {})['applied'] = [float(v) for v in m.groups()[1:]]
    for m in re.finditer(r'FOLCAP\|(\w+)\|([rb]{4})\|', logj):
        res['f3'].setdefault(m.group(1), {})['caps'] = m.group(2)
    for i, (kind, sz, st, _) in enumerate(pages):
        page = i + 2
        base = os.path.join(d, f'{name}-p{page}')
        subprocess.run(['pdftoppm', '-r', str(DPI), '-gray', '-f', str(page),
                        '-l', str(page), '-singlefile', pdf, base], env=ENV,
                       capture_output=True)
        if not os.path.exists(base + '.pgm'):
            continue
        w, h, px = read_pgm(base + '.pgm')
        box = ink(w, h, px)
        os.remove(base + '.pgm')
        if not box:
            continue
        x0, y0, x1, y1 = box
        key = sz + st
        if kind == 'ra':
            res['m'].setdefault(key, {})
            res['m'][key]['head'] = (y1 - y0 + 1) * PT
            xs = range(x0 + max(3, (x1 - x0) // 20), x0 + max(4, (x1 - x0) // 4))
            sh = col_cov(w, h, px, xs)
            res['m'][key]['shaft'] = sh * PT
            # 尻（左端）の形：端から軸の太さの半分の範囲の被覆率．切りっぱなしなら約1，丸なら約0.79
            n = max(2, int(round(sh / 2)))
            res['m'][key]['tail'] = col_cov(w, h, px, range(x0, x0 + n)) / sh
            res['m'][key]['clip'] = x0 == 0 or y0 == 0 or x1 == w - 1 or y1 == h - 1
        else:
            res['f3'].setdefault(sz, {})
            if kind in ('cbd', 'cbu', 'cid', 'ciu', 'chr', 'chf', 'chl', 'cfl'):
                # 縦向きは行，横向きは列ごとの字面の幅から，軸だけの部分と斜線の部分を分ける
                if kind in ('chr', 'chf', 'chl', 'cfl'):
                    lines = list(range(x0, x1 + 1))
                    wid = {x: sum(1 for y in range(y0, y1 + 1) if px[y * w + x] < 128) for x in lines}
                    lo, hi = x0, x1
                else:
                    lines = list(range(y0, y1 + 1))
                    wid = {y: sum(1 for x in range(x0, x1 + 1) if px[y * w + x] < 128) for y in lines}
                    lo, hi = y0, y1
                # 矢頭と尻を除き，矢印の長さの中央25～75%で，軸だけの部分と斜線の部分を分ける
                mid = [l for l in lines if lo + (hi - lo) * 0.25 < l < lo + (hi - lo) * 0.75 and wid[l]]
                thin = sorted(wid[l] for l in mid)[len(mid) // 4]
                shaft = [l for l in mid if wid[l] <= thin * 1.3]
                slash = [l for l in mid if wid[l] > thin * 3]
                def cen(ls):  # 軸の直交方向の重心
                    if kind in ('chr', 'chf', 'chl', 'cfl'):
                        t = sum(255 - px[y * w + x] for x in ls for y in range(y0, y1 + 1))
                        return sum(y * (255 - px[y * w + x]) for x in ls for y in range(y0, y1 + 1)) / t
                    t = sum(255 - px[y * w + x] for y in ls for x in range(x0, x1 + 1))
                    return sum(x * (255 - px[y * w + x]) for y in ls for x in range(x0, x1 + 1)) / t
                def span(ls):  # 斜線の直交方向の両端の中点
                    if kind in ('chr', 'chf', 'chl', 'cfl'):
                        ys = [y for x in ls for y in range(y0, y1 + 1) if px[y * w + x] < 128]
                    else:
                        ys = [x for y in ls for x in range(x0, x1 + 1) if px[y * w + x] < 128]
                    return (min(ys) + max(ys)) / 2
                if shaft and slash:
                    # along：斜線の中心－字面の中心（矢印の向きの座標，ページの右・下が正）
                    # across：斜線の両端の中点－軸の中心（直交方向）
                    res['f3'][sz][kind + 'along'] = (sum(slash) / len(slash) - (lo + hi) / 2) * PT
                    res['f3'][sz][kind + 'across'] = (span(slash) - cen(shaft)) * PT
            elif kind in ('lra', 'fill'):
                # 尻（左端）の形．軸の太さは左寄りの列の被覆量
                xs = range(x0 + max(3, (x1 - x0) // 20), x0 + max(4, (x1 - x0) // 6))
                sh = col_cov(w, h, px, xs)
                n = max(2, int(round(sh / 2)))
                res['f3'][sz][kind + 'tail'] = col_cov(w, h, px, range(x0, x0 + n)) / sh
            elif kind == 'minus':
                res['f3'][sz]['minus'] = col_cov(w, h, px, range(x0 + (x1 - x0) // 3, x0 + 2 * (x1 - x0) // 3)) * PT
            else:
                res['f3'][sz][kind] = (x1 - x0 + 1) * PT
                # 縦の軸の太さ：上端から25%の行の字面の幅
                ys = range(y0 + (y1 - y0) // 10, y0 + (y1 - y0) // 3)
                sh = row_cov(w, h, px, ys)
                res['f3'][sz][kind + 'shaft'] = sh * PT
                # 尻（上端）の形
                n = max(2, int(round(sh / 2)))
                res['f3'][sz][kind + 'tail'] = row_cov(w, h, px, range(y0, y0 + n)) / sh
                res['f3'][sz][kind + 'clip'] = x0 == 0 or y0 == 0 or x1 == w - 1 or y1 == h - 1
    return res


def main():
    global WORK
    WORK = os.environ.get('FOLWORK') or tempfile.mkdtemp(prefix='folarrow-fontdata-')
    print('work directory:', WORK)
    only = sys.argv[1:]
    cfg = [c for c in configs() if not only or c[0] in only]
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(lambda c: run(*c), cfg))
    # 結果は既存のファイルに合わせる（同じ設定・エンジンの行だけ差し替え，ほかは残す）．
    # 書き出すファイルはFOLOUTで変えられる（既定はresults.json）．
    out = os.path.join(HERE, os.environ.get('FOLOUT', 'results.json'))
    old = json.load(open(out)) if os.path.exists(out) else []
    new = {(r['name'], r['engine']): r for r in rows}
    merged = [new.pop((r['name'], r['engine']), r) for r in old] + list(new.values())
    json.dump(merged, open(out, 'w'), indent=1, ensure_ascii=False)
    report(rows)


def report(rows):
    """計算値／実測値の比（1.00が理想）を表示する．"""
    print(f"{'config':30s} {'eng':3s} | head: b/head (10t 10s 10ss 11t 11s 12t 12s) | shaft: t/shaft (10t 10s 12t) | big B/big T/sh | inl I/inl | fn2(10t)")
    for r in rows:
        if not r.get('m'):
            print(f"{r['name']:30s} {r['engine'][:3]} ERROR {r.get('error')}")
            continue
        m = r['m']
        def rb(k):
            x = m.get(k, {})
            return f"{x['b'] / x['head']:4.2f}" if x.get('head') and x.get('b') else '   -'
        def rt(k):
            x = m.get(k, {})
            return f"{x['t'] / x['shaft']:4.2f}" if x.get('shaft') and x.get('t') else '   -'
        f3 = r['f3'].get('10', {})
        big = f"{f3['bigb'] / f3['big']:4.2f}" if f3.get('big') and f3.get('bigb') else '   -'
        inl = f"{f3['inlb'] / f3['inl']:4.2f}" if f3.get('inl') and f3.get('inlb') else '   -'
        bigt = f"{f3['bigt'] / f3['bigshaft']:4.2f}" if f3.get('bigshaft') and f3.get('bigt') else '   -'
        print(f"{r['name']:30s} {r['engine'][:3]} | " + ' '.join(rb(k) for k in ('10t', '10s', '10ss', '11t', '11s', '12t', '12s'))
              + ' | ' + ' '.join(rt(k) for k in ('10t', '10s', '12t')) + f" | {big} {bigt} | {inl} | {m.get('10t', {}).get('fn', '')[:22]}"
              + ('  !' + r['error'][:50] if r.get('error') else ''))


if __name__ == '__main__':
    if sys.argv[1:2] == ['--report']:
        report(json.load(open(os.path.join(HERE, 'results.json'))))
    else:
        main()
