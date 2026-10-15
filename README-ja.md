# folarrow（日本語のREADME）

英語のREADMEは`README.md`である．

これは開発用のリポジトリのREADMEである．CTANに出す配布物は，このリポジトリから`tools/ctan/mkctan.sh`で作る．
配布物には専用のREADME（`ctan/README.md`，`ctan/README-ja.md`）を入れる．`tools/`のスクリプトのうち，矢印のフォントを作る2本（`tools/fontbuild/mkfolfonts.py`，`mkfolotf.py`）だけを，フォントのソースとして`source/`に入れる．ほかのスクリプト，説明書の例を組むスクリプト，テストは入れない．

これはLaTeXパッケージのひとつで，葉層構造論における葉層束の射影を表す軸に3本の斜線が入った矢印を，amscd，xy-pic，tikz-cdの図式と本文の数式で使うためのものである．

ファイバー束`V → E → M`で射影`E → M`を縦向き（あるいは横向き）の矢印で描くとき，その軸に3本線を入れて特に葉層束であることを表すことがある．
これを実現する．

図式の矢印は各パッケージの通常の矢印をそのまま使い，軸の中ほどに斜線を重ねる（pict2eまたはPGFで描く）．
斜線の長さと太さは，その場の数式フォントの大きさに合わせて決まる．
本文用の4つの矢印（`\folrightarrow`，`\folleftarrow`，`\foldownarrow`，`\foluparrow`）は，主な数式フォント（Computer Modern，Latin Modern，newtx，txfonts，newpx，pxfonts）では3本線まで含めて1文字にしたType 1フォントで組み，PDFからテキストとして取り出すと→←↓↑になる．LuaLaTeX，XeLaTeXでunicode-mathを使うときは，OpenTypeの数式フォント49書体に対応するOTFで組む．

詳しくは`doc/latex/folarrow/folarrow-ja.pdf`（説明書．英語版は`folarrow-en.pdf`）を参照．

## 使い方

```latex
\usepackage{amscd}      % 使うものだけ
\usepackage[all]{xy}
\usepackage{tikz-cd}
\usepackage{folarrow}
```

| 環境 | 書き方 |
|---|---|
| amscd | `@FVV{\pi}V`，`@F>f>>`，`@F<<g<`，`@FAAA`（通常の指定の`@`の直後に`F`） |
| xy-pic | `\ar[d]\|@{fol}^{\folpad{\pi}}`（`fol`は矢印の途中に置く方向付き物体で，矢印は途切れない．`\folpad`はラベルが斜線にかからないよう余白を付ける） |
| tikz-cd | `\arrow[d, foliated, "\pi"]`（ラベルは自動で斜線を避ける） |
| 本文の数式 | `\folrightarrow`，`\folleftarrow`，`\foldownarrow`，`\foluparrow`，`\xfolrightarrow[下]{上}`，`\xfolleftarrow[下]{上}` |

例（amscd）：

```latex
\begin{CD}
V @>>> E\\
@.     @FVV{\pi}V\\
@.     M
\end{CD}
```

斜線の形は`\folarrowsetup{span=1.0, lean=0.25, gap=0.35, shift=0, thickness=}`か，同じキーのパッケージオプションで変えられる（値は既定値）．

## 本文用の矢印のフォント

| 数式フォント | 記号フォント | 矢印のフォント |
|---|---|---|
| Computer Modern | `cmsy5`〜`cmsy10` | `folcm5`〜`folcm10` |
| Latin Modern | `lmsy5`〜`lmsy10` | `follm5`〜`follm10` |
| newtxmath | `ntxsy`，`ntxsy7`，`ntxsy5` | `folntx`，`folntx7`，`folntx5` |
| txfonts | `txsy` | `foltx` |
| newpxmath | `zplsy` | `folzpl` |
| pxfonts | `pxsy` | `folpx` |
| Computer Modern（ボールド） | `cmbsy5`〜`cmbsy10` | `folcmb5`〜`folcmb10` |
| Latin Modern（ボールド） | `lmbsy5`，`lmbsy7`，`lmbsy10` | `follmb5`，`follmb7`，`follmb10` |
| newtxmath（ボールド） | `ntxbsy`，`ntxbsy7`，`ntxbsy5` | `folntxb`，`folntxb7`，`folntxb5` |
| txfonts（ボールド） | `txbsy` | `foltxb` |
| newpxmath（ボールド） | `zplbsy` | `folzplb` |
| pxfonts（ボールド） | `pxbsy` | `folpxb` |

ボールドの行は，数式をボールド（`\boldmath`，`\bm`）にしたときに使われる太字の記号フォントのもの．
描く3本線も，太字の記号フォントの実測データ（`folarrow-fonts.def`）で太字の矢印に合わせる．
unicode-mathでは，太字の数式フォントを`\setmathfont{…}[version=bold]`で指定する．

- 字形は記号フォントのマイナス記号と→（`\longrightarrow`と同じ組み方）の輪郭に3本線の輪郭を加えたもの．
  ←はマイナス記号と←，↓↑は→を回したもの．3本線は字面の中央にあり，端の形は矢印の尻の形に合わせる．
- ToUnicodeは→（U+2192），←（U+2190），↓（U+2193），↑（U+2191）．
- 形のキーが既定値でないとき，`glyphs=false`のとき，表にない数式フォント（unicode-mathなど）では，これまでどおり描く．
  伸びる矢印と図式の矢印は常に描く．
- マップファイル`folarrow.map`は，pdfLaTeX，LuaLaTeXではパッケージが読み込み，dvipdfmx，xdvipdfmxでは`\special{pdf:mapfile folarrow.map}`を出す．dvipsではupdmapで登録する．
- ライセンスは元のフォントを引き継ぐ：Computer Modern由来はSIL OFL 1.1（予約フォント名を避けて`folcm`，`FolArrow-CM`と命名），Latin Modern由来はGUST Font License，txfonts，pxfonts，newtx，newpx由来はGPL（フォントの例外付き）．

### OpenTypeの数式フォント（unicode-math）

LuaLaTeX，XeLaTeXでunicode-mathを使うときは，次の49書体に対応するOTF（`fonts/opentype/public/folarrow/folu-〈略号〉.otf`）で組む．

Latin Modern Math，New Computer Modern Math（Regular，Book，Bold），New Computer Modern Sans Math，STIX Two Math，STIX Math，XITS Math（Regular，Bold），TeX Gyre Termes／Pagella／Bonum／Schola／DejaVu Math，Libertinus Math，Fira Math，Asana Math，Erewhon Math（Regular，Bold），KpMath（Regular，Light，Semibold，Bold，Sans，SansBold），GFS Neohellenic Math，IBM Plex Math，Arsenal Math（Sans，SansBold），Concrete Math（Regular，Bold），Euler Math，Garamond Math，Lete Sans Math（Regular，Bold），Luciole Math（Regular，Bold），Old Standard Math，XCharter Math（Regular，Bold），Pennstander Math（Thin〜Blackの9つ）

- 字形は元のフォントのU+27F6，U+27F5の輪郭に3本線を加えたもの．
  ↓↑はU+27F6を回してMATH表のAxisHeightに中心を合わせる．
  軸の太さ・高さと尻の形は輪郭から求める．
- 矢印に添字用の字形（ssty）があるフォントでは，それぞれから作った字形とssty機能を持たせ，元のフォントと同じ`+ssty=0`などの指定で読む．
- 元のフォントは，`\fontname`のフォント名の部分が，ファイル名，PostScript名，フルネーム，ファミリー名のどれかと一致するかで見分ける．
- 文字はU+2192，U+2190，U+2193，U+2191にある．
- Pennstander Mathは↓の伸縮の部品がずれていて，大きな区切り記号の↓が崩れる（フォントの問題）．
  このファミリーでは，描いて組む縦向きの矢印（`glyphs=false`などのときの本文用と，amscdの`@FVVV`，`@FAAA`）の土台を，横向きの矢印を90°回したものにする．
  folarrowの命令を使わない部分（通常のamscdの`@VVV`，`@AAA`や`\Big\downarrow`など）の崩れはフォントの問題なので，サポート外とする．
- XCharter Math BoldのU+27F6，U+27F5は送り幅より字面が長い（フォントの問題）ので，OTFでは送り幅を字面に合わせて広げる．
- ライセンスは元のフォントを引き継ぐ（SIL OFL 1.1かGUST Font License）．ファイル名とフォント名（`FolArrowU-〈略号〉`）には元の名前を含めない．
  Minion Mathのように再配布できないフォントには用意していない（これまでどおり描く）．

```bash
python3 tools/fontbuild/mkfolotf.py
```

### 作り直し

Type 1のフォントは`tools/fontbuild/mkfolfonts.py`で作り直せる（fontTools，skia-pathopsと，TeX Liveのkpsewhich，tftopl，vftovp，pltotf，t1asmを使う）．

```bash
python3 tools/fontbuild/mkfolfonts.py
```

## スクリプトで生成するファイル

このパッケージの多くのファイルはスクリプトで生成する．手で直さず，スクリプトを直して作り直す．

| 生成するファイル | スクリプト |
|---|---|
| Type 1の矢印のフォント，TFM，`folarrow.map`，`folarrow-glyphs.def` | `tools/fontbuild/mkfolfonts.py` |
| OpenTypeの矢印のフォント，`folarrow-otf.def` | `tools/fontbuild/mkfolotf.py` |
| `folarrow-fonts.def`（実測データ） | `tools/fontdata/measure.py`のあと`tools/fontdata/mkdata.py` |
| `doc/latex/folarrow/folarrow-verify.tex`，`folarrow-verify-en.tex`（検証表） | `tools/fontdata/mkreport.py` |
| `licenses/FONTS.md` | `tools/ctan/mkfontlicenses.py` |
| 説明書の例の結果（`*-out.pdf`） | `doc/latex/folarrow/lite-examples/build.sh`，`doc/latex/folarrow/full-examples/build.sh` |
| CTANに出すアーカイブ`build/ctan/folarrow.zip` | `tools/ctan/mkctan.sh` |

フォントのスクリプトは，PythonのfontToolsとskia-pathops，TeX Liveのkpsewhich，tftopl，vftovp，pltotf，t1asmを使う．
矢印のフォントは，TeX Liveにインストールされている数式フォントから作る．

## 動作要件

- LaTeX 2022-06-01以降（`\fpeval`，`\DeclareKeys`を使う）
- pict2e（tikz-cdで使う場合はPGF／TikZ）
- pdfLaTeX，LuaLaTeX，upLaTeX＋dvipdfmx，XeLaTeXで確認（TeX Live 2025と2026）．dvipdfmxでは文書クラスに`dvipdfmx`オプションを付ける．
- TeX Live 2025と2026のLuaLaTeXでは，xy-pic自体がxypdfのエラーになる（folarrowとは無関係）．

## 数式フォントへの対応

斜線の長さ・間隔は矢頭の幅を，線の太さは矢印の軸の太さを基準にする．これらはフォントによって大きく異なるので，その場で使われている矢印のフォントについて次の順に求める．

1. LuaLaTeX＋OpenTypeの数式フォント：グリフの外接矩形を直接読む（`folarrow.lua`）．添字用の字形（ssty）と`\Big`の大きい字形も読む．
2. XeLaTeX＋OpenTypeの数式フォント：`\XeTeXglyphbounds`で読む（添字用の字形と`\Big`の大きい字形は読めない）．
3. Type 1の数式フォント：実測データ（`folarrow-fonts.def`，65フォント）を引く．矢印を持つフォントは`\rightarrow`と`\downarrow`の文字コードから求める．
4. どれにも当たらなければ，フォントの寸法から推定する．

[LaTeX Font Catalogueの数式フォント](https://tug.org/FontCatalogue/mathfonts.html)の全68書体，Computer Modern，Latin Modern，newtx，txfonts，newpx，pxfontsのボールド（`\boldmath`）と，OpenTypeの数式フォント16書体（Latin Modern Math，New Computer Modern Math，STIX Two Math，TeX Gyre各種，Libertinus Math，Fira Math，XITS Math，Asana Math，Erewhon Math，KpMath，GFS Neohellenic Math，Minion Math）で，矢印を実際に組んだ画像から矢頭の幅と軸の太さを測り，計算値と比べた．
190の組（書体×エンジン）のうち174で，10pt，10.95pt，12ptの本文・添字・添字の添字，`\Big`の縦矢印のすべてにわたってずれが3%以内だった．残りは次のとおり．

- PKフォント（boisik，Computer Concrete，drm）：ビットマップのドットの段差（0.12pt）による誤差．
- XeLaTeXのSTIX Two Math，Erewhon Math：添字用の字形を読めないため，添字の大きさで最大20%ずれる（LuaLaTeXでは正しい）．
- URW Garamond（mathdesign），garamondx：非フリーのため未インストールで，確認していない．

3本線の端は，矢印の尻（軸の端）の形に合わせる．尻が丸い矢印（Computer Modernの横向きの矢印，Latin Modern Mathなど）では丸い端，そうでない矢印では切りっぱなしにする．尻の形も実測データに持つ．
xy-picは線の端が丸いので丸い端，tikz-cdは矢印の線の端の設定（`line cap`）に従う．

書体ごとの結果は説明書の検証表にある．データと表は`tools/fontdata/`で作り直せる．

```bash
cd tools/fontdata
python3 measure.py            # 全書体を組んで測る（TeXはPATHに通しておく）
python3 mkdata.py             # tex/latex/folarrow/folarrow-fonts.defを作る
python3 mkreport.py           # doc/latex/folarrow/folarrow-verify.tex，folarrow-verify-en.texを作る
```

## 簡易版（`lite`オプション）

```latex
\usepackage[lite]{folarrow}
```

ほかのファイル（Luaのモジュール，実測データ，矢印のフォント）を使わず，すべての矢印を描いて組む簡易版．
矢印のフォントをPDFに埋め込まずに組みたいときなどに使う．既定（`lite`なし）の動作は変わらない．

- ほかのファイル（`folarrow.lua`，`folarrow-*.def`，矢印のフォントとマップファイル）は，インストールされていても一切使わず，すべての矢印を描いて組む．
- 矢頭の幅と線の太さは，XeLaTeX＋OpenTypeの数式フォントなら`\XeTeXglyphbounds`で読み，それ以外はフォントの寸法から推定する．
- 実測データを使わないので，3本線は矢印の箱の中央に置き，端はつねに切りっぱなしにする．CM，newtx，newpx，txfontsの本文用の矢印では，中央からのずれは最大0.3ptだった（書体によってはもっと大きい）．
- PDFからテキストとして取り出すと元の矢印の文字になる．
- 読み込み時にだけ指定できる．
- 簡易版だけの説明書`doc/latex/folarrow/folarrow-lite-ja.pdf`（英語版は`folarrow-lite-en.pdf`）がある．使い方の例は，`\documentclass`から`\end{document}`までの完全な文書（`doc/latex/folarrow/lite-examples/ex*.tex`）で，そのまま写して組める．例の結果は`lite-examples/build.sh`で，ほかのファイルを使わないことを確かめるため，`folarrow.sty`だけを置いたディレクトリで組んで作る．

## ライセンス

- `folarrow.sty`，`folarrow.lua`，`.def`ファイル，説明書，スクリプト，テスト：MITライセンス（`LICENSE`）．
- 矢印のフォント（`fonts/`）：元のフォントのライセンスを引き継ぐ（SIL OFL 1.1，GUST Font License，フォントの例外付きのGNU GPL）．
  フォントごとの元のフォント，元の著作権表示，ライセンスは`licenses/FONTS.md`にあり，ライセンスの本文も`licenses/`に置いた．

## インストール

`tex/latex/folarrow/`の`folarrow.sty`，`folarrow-fonts.def`，`folarrow-glyphs.def`，`folarrow.lua`と，`folarrow-otf.def`と，`fonts/`以下（`type1/public/folarrow/`，`tfm/public/folarrow/`，`map/dvips/folarrow/`，`opentype/public/folarrow/`）をTEXMFツリーに置く．
このリポジトリ自体をTEXMFHOMEとして使うこともできる．
CTANの配布物（`folarrow.zip`）には，TDSの形に並べた`folarrow.tds.zip`も入っているので，それをTEXMFツリーに展開してもよい．
dvipsで使うときは，`updmap`で`folarrow.map`を登録する（pdfLaTeX，LuaLaTeX，dvipdfmx，xdvipdfmxではパッケージが読み込むので要らない）．

```bash
export TEXMFHOME=/path/to/texmf-folto
```

## ファイル

- `tex/latex/folarrow/folarrow.sty`：パッケージ本体
- `tex/latex/folarrow/folarrow-fonts.def`：Type 1の数式フォントの実測データ（自動生成）
- `tex/latex/folarrow/folarrow.lua`：LuaLaTeXでOpenTypeのグリフを読むLuaモジュール
- `tex/latex/folarrow/folarrow-glyphs.def`：本文用の矢印のフォントがある記号フォントの表（自動生成）
- `fonts/type1/public/folarrow/*.pfb`，`fonts/tfm/public/folarrow/*.tfm`，`fonts/map/dvips/folarrow/folarrow.map`：本文用の矢印のフォント（自動生成）
- `tex/latex/folarrow/folarrow-otf.def`，`fonts/opentype/public/folarrow/*.otf`：OpenTypeの数式フォント用のOTFと，元のフォントとの対応表（自動生成）
- `tools/fontbuild/mkfolfonts.py`：本文用の矢印のType 1フォントを作る（CTANの配布物では`source/`に入る）
- `tools/fontbuild/mkfolotf.py`：本文用の矢印のOTFを作る（CTANの配布物では`source/`に入る）
- `tools/fontdata/`：実測と検証の道具（`measure.py`，`mkdata.py`，`mkreport.py`，書体の一覧`fonts.json`，結果`results*.json`）
- `doc/latex/folarrow/folarrow-lite-ja.tex`，`.pdf`：簡易版（`lite`）の説明書（upLaTeX＋dvipdfmxで組む．例は`lite-examples/`）
- `doc/latex/folarrow/folarrow-lite-en.tex`，`.pdf`：簡易版の説明書の英語版（同じくupLaTeX＋dvipdfmxで組む）
- `doc/latex/folarrow/folarrow-ja.tex`，`.pdf`：説明書（upLaTeX＋dvipdfmxで組む．検証表`folarrow-verify.tex`を読み込む）
- `doc/latex/folarrow/folarrow-en.tex`，`.pdf`：説明書の英語版（同じくupLaTeX＋dvipdfmxで組む．検証表`folarrow-verify-en.tex`を読み込む）
- `licenses/`：ライセンスの本文と，矢印のフォントのライセンスの一覧`FONTS.md`（`tools/ctan/mkfontlicenses.py`で作る）
- `tools/ctan/`：CTANに出すアーカイブを作る道具（`mkctan.sh`）
- `ctan/`：CTANに出す配布物のREADME（`README.md`，`README-ja.md`）
- `test/runall.sh`：すべてのテスト（既存のテスト，OpenTypeの49書体，組見本，説明書の例と説明書）をまとめて流し，エラーと字形の欠けの件数をまとめる
- `test/run.sh`，`test/t1-all.tex`：3つのエンジンで組むテスト
- `test/t3-labels.tex`：xy-pic，tikz-cdのラベルと斜線の重なりの確認
- `test/t5-glyphs.tex`：本文用の矢印のフォントと描いたものの比較（テキストとしての値も確認する）
- `test/t6-otf.tex`：unicode-mathの数式フォントでのOTFと描いたものの比較（LuaLaTeX，XeLaTeXで組む）
- `test/sample-cm.tex`，`sample-newtx.tex`，`sample-newpx.tex`，`sample-tx.tex`，`sample-px.tex`：Computer Modern，Times系（newtx，txfonts），Palatino系（newpx，pxfonts）の組見本（本文は`sample-body.tex`．upLaTeX＋dvipdfmxで組む）
- `test/compare-{cm,newtx,newpx,tx,px}.tex`：`\nrightarrow`との比較（本文は`compare-body.tex`．upLaTeX＋dvipdfmxで組む）
