# folarrow（日本語のREADME）

英語版は`README.md`を参照のこと．

版20261010.0，2026年10月10日．
作者：Yuwsuke Kieda

葉層束の射影を表す軸に3本の斜線が入った矢印を，amscd，xy-pic，tikz-cdの図式や本文の数式で使うためのLaTeXパッケージである．

ファイバー束`V → E → M`の射影`E → M`を表す矢印に3本線を加え，葉層束であることを示すものである．

## 使い方

```latex
\usepackage{amscd}      % 使うものだけ
\usepackage[all]{xy}
\usepackage{tikz-cd}
\usepackage{folarrow}
```

| 環境 | 書き方 |
|---|---|
| amscd | `@FVV{\pi}V`，`@FAAA`，`@F>f>>`，`@F<<g<`（通常の`@`の直後に`F`を付ける） |
| xy-pic | `\ar[d]\|@{fol}^{\folpad{\pi}}`（`fol`は矢印上の大きさ0の物体であり，`\folpad`はラベルと斜線の間に余白を付ける） |
| tikz-cd | `\arrow[d, foliated, "\pi"]` |
| 本文の数式 | `\folrightarrow`，`\folleftarrow`，`\foldownarrow`，`\foluparrow`，`\xfolrightarrow[下]{上}`，`\xfolleftarrow[下]{上}` |

図式用の矢印は各パッケージのものを使い，軸に斜線を重ねる方式である（pict2e，tikz-cdではPGFで描画する）．斜線の長さ・間隔・太さは，使用中の数式フォントに合わせて決まる．

本文用の4つの矢印（`\folrightarrow`など）は，3本線まで含めて1文字にした字形で組む．

- Type 1フォント：Computer Modern，Latin Modern，newtx，txfonts，newpx，pxfonts
- OpenTypeフォント：unicode-math（LuaLaTeX，XeLaTeX）で使うOpenTypeの数式フォント49書体

これらの字形はPDFから抽出すると→←↓↑（U+2192，U+2190，U+2193，U+2191）となる．その他の数式フォントでは3本線を描画する方式である．

ボールド数式（`\boldmath`，`\bm`）にも対応する．本文用の矢印には太字の記号フォントから作ったフォントを使い，描画する斜線も太字に合わせる．unicode-mathでは`\setmathfont{…}[version=bold]`で太字フォントを指定する仕様である．

斜線の形は`\folarrowsetup{span=, lean=, gap=, shift=, thickness=}`か，同じキーのパッケージオプションで変えられる．

### 簡易版：`lite`オプション

```latex
\usepackage[lite]{folarrow}
```

`lite`ではLuaモジュール，実測データ，矢印フォントを使わず，矢印をすべて描画する方式である．PDFに矢印フォントを埋め込みたくない場合などに適する．既定の動作に変更はない．

## 動作要件

- LaTeX 2022-06-01以降，pict2e，graphics．tikz-cdで使う場合はPGF／TikZ．
- pdfLaTeX，LuaLaTeX，XeLaTeX，upLaTeX+dvipdfmx（TeX Live 2026）で動作確認済み．dvipdfmxでは文書クラスに`dvipdfmx`オプションを指定する．
- 特別なフォントは不要である（矢印のフォントは同梱している）．
- TeX Live 2026のLuaLaTeXでは，xy-pic自体がエラーになる（folarrowとは無関係）．

## 説明書

- `doc/folarrow-ja.pdf`：完全版の説明書（検証表を含む）．
- `doc/folarrow-lite-ja.pdf`：`lite`オプションの説明書．各例はそのまま組める完全な文書．

## インストール

`folarrow.tds.zip`をTEXMFツリーに展開するか，次の場所に配置する．

| ファイル | 置き場所 |
|---|---|
| `tex/*` | `tex/latex/folarrow/` |
| `fonts/type1/*.pfb` | `fonts/type1/public/folarrow/` |
| `fonts/tfm/*.tfm` | `fonts/tfm/public/folarrow/` |
| `fonts/opentype/*.otf` | `fonts/opentype/public/folarrow/` |
| `fonts/map/folarrow.map` | `fonts/map/dvips/folarrow/` |
| `source/*` | `source/latex/folarrow/` |

pdfLaTeX，LuaLaTeX，dvipdfmx，xdvipdfmxでは`folarrow.map`を自動で読み込む．dvipsでは`updmap`による登録が必要である（TeX Live：`updmap-user --enable Map=folarrow.map`）．

## ファイル

- `tex/`：`folarrow.sty`（本体），`folarrow.lua`（LuaTeXモジュール），`folarrow-fonts.def`（Type 1数式フォントの実測データ），`folarrow-glyphs.def`，`folarrow-otf.def`（矢印フォントの表）．
- `fonts/`：矢印フォント（Type 1，TFM，OpenType）とマップファイルである．
- `doc/`：説明書（PDFとソース）および例である．
- `source/`：矢印フォントを生成するPythonスクリプト（次節を参照）である．
- `LICENSE`：本パッケージのMITライセンスである．
- `licenses/`：フォントのライセンス本文と，元フォント・著作権表示・ライセンスの一覧`FONTS.md`を収録するディレクトリである．
- `folarrow.tds.zip`：同じファイルをTDS形式に配置したものである．

## 矢印のフォントのソース

矢印フォントは，元の数式フォントから次のPythonスクリプトで生成するものである．

- `source/mkfolfonts.py`：Type 1のフォント，そのTFM，`folarrow.map`，`folarrow-glyphs.def`を作る．
- `source/mkfolotf.py`：OpenTypeのフォントと`folarrow-otf.def`を作る．

スクリプトはTeX Liveの元フォントから矢印のアウトラインを取り出し，3本線を加えるものである．Python 3のfontTools，skia-pathopsと，TeX Liveのkpsewhich，tftopl，vftovp，pltotf，t1asmが必要である．出力先は環境変数`FOLARROW_ROOT`で指定するTDSツリーであり，`tex/latex/folarrow/folarrow-fonts.def`がなければ停止する．`folarrow.tds.zip`を展開し，次のように実行する．

```sh
FOLARROW_ROOT=/path/to/the/tree python3 source/mkfolfonts.py
FOLARROW_ROOT=/path/to/the/tree python3 source/mkfolotf.py
```

`mkfolotf.py`は`mkfolfonts.py`を読み込むため，同じディレクトリに置く必要がある．通常の利用では実行不要である．

## ライセンス

- `folarrow.sty`，`folarrow.lua`，`.def`ファイル，説明書，`source/`のスクリプト：MITライセンス（`LICENSE`）．
- 矢印フォント（`fonts/`）は元フォントのライセンス（SIL Open Font License 1.1，GUST Font License，フォント例外付きGNU GPL）を引き継ぐ．詳細は`licenses/FONTS.md`を参照．派生フォント名に元フォントの予約フォント名は含まない．
