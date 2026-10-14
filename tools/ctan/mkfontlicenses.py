#!/usr/bin/env python3
"""生成した矢印のフォントの一覧（元のフォント，元の著作権表示，ライセンス）を
licenses/FONTS.mdに書く（CTAN向けに英語で書く）．
使い方：python3 mkfontlicenses.py（fontToolsを使う）
"""
import glob, os, re
from fontTools.t1Lib import T1Font
from fontTools.ttLib import TTFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
TEXT = {
    'SIL Open Font License 1.1': 'OFL-1.1.txt',
    'GUST Font License': 'GUST-FONT-LICENSE.txt, LPPL-1.3c.txt',
    'GNU GPL with font exception': 'GPL-2.0.txt, TXFONTS-PXFONTS-COPYRIGHT.txt',
}


def textfile(lic):
    for k, v in TEXT.items():
        if lic.startswith(k):
            return v
    return '?'


rows = []
for p in sorted(glob.glob(os.path.join(ROOT, 'fonts/type1/public/folarrow/*.pfb'))):
    f = T1Font(p); f.parse()
    n = f['FontInfo']['Notice']
    m = re.match(r'Derived from (\S+) by the folarrow package\. Original notice: (.*)\. License: (.*)\.$', n)
    src, orig, lic = (re.sub(r'\\(.)', r'\1', g) for g in m.groups())
    rows.append((os.path.basename(p), f['FontName'], src, orig, lic))
for p in sorted(glob.glob(os.path.join(ROOT, 'fonts/opentype/public/folarrow/*.otf'))):
    f = TTFont(p); nm = f['name']
    d = nm.getDebugName(13)
    m = re.match(r'This font is derived from (\S+) and is licensed under the same license: (.*)\.$', d)
    src, lic = m.groups()
    rows.append((os.path.basename(p), nm.getDebugName(6), src, nm.getDebugName(0).replace('\n', ' '), lic))

out = ['# Licenses of the arrow fonts',
       '',
       'The fonts in `fonts/` were made from the original math fonts listed below: the',
       'arrow glyphs of the original font with three strokes added.',
       'Each generated font is distributed under the license of its original font.',
       'The license texts are in this directory. The file names and font names of the',
       'generated fonts do not contain the Reserved Font Names of the original fonts.',
       'TeX Gyre DejaVu Math is based on DejaVu, which is based on Bitstream Vera; the',
       'name of the generated font does not contain "Bitstream" or "Vera".',
       '',
       '| File | Font name | Original font | Original copyright notice | License | License text |',
       '|---|---|---|---|---|---|']
for r in rows:
    out.append('| `%s` | %s | `%s` | %s | %s | %s |' % (r[0], r[1], r[2], r[3].replace('|', '/'), r[4], textfile(r[4])))
open(os.path.join(ROOT, 'licenses', 'FONTS.md'), 'w').write('\n'.join(out) + '\n')
print(len(rows), 'fonts')
