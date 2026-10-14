# folarrow（日本語のREADME）

英語のREADMEは`README.md`である．

版20261010.0，2026年10月10日．
作者：Yuwsuke Kieda

これはLaTeXパッケージのひとつで，葉層構造論における葉層束の射影を表す軸に3本の斜線が入った矢印を，amscd，xy-pic，tikz-cdの図式と本文の数式で使うためのものである．

ファイバー束`V → E → M`で射影`E → M`を縦向き（あるいは横向き）の矢印で描くとき，その軸に3本線を入れて特に葉層束であることを表すことがある．
これを実現する．

## 使い方

```latex
\usepackage{amscd}      % 使うものだけ
\usepackage[all]{xy}
\usepackage{tikz-cd}
\usepackage{folarrow}
```

| 環境 | 書き方 |
|---|---|
| amscd | `@FVV{\pi}V`，`@FAAA`，`@F>f>>`，`@F<<g<`（通常の指定の`@`の直後に`F`） |
| xy-pic | `\ar[d]\|@{fol}^{\folpad{\pi}}`（`fol`は矢印の途中に置く大きさ0の物体．`\folpad`はラベルが斜線にかからないよう余白を付ける） |
| tikz-cd | `\arrow[d, foliated, "\pi"]` |
| 本文の数式 | `\folrightarrow`，`\folleftarrow`，`\foldownarrow`，`\foluparrow`，`\xfolrightarrow[下]{上}`，`\xfolleftarrow[下]{上}` |

図式の矢印は各パッケージの通常の矢印をそのまま使い，軸の中ほどに斜線を重ねる（pict2e，tikz-cdではPGFで描く）．
斜線の長さ・間隔・太さは，その場の数式フォントの矢頭と軸に合わせて決まる．

本文用の4つの矢印（`\folrightarrow`など）は，3本線まで含めて1文字にした字形で組む．

- Type 1フォント：Computer Modern，Latin Modern，newtx，txfonts，newpx，pxfonts
- OpenTypeフォント：unicode-math（LuaLaTeX，XeLaTeX）で使うOpenTypeの数式フォント49書体

これらの字形は，PDFからテキストとして取り出すと→←↓↑（U+2192，U+2190，U+2193，U+2191）になる．
ほかの数式フォントでは3本線を描いて組む．

数式をボールド（`\boldmath`，`\bm`）にしたときも追従する．本文用の矢印は太字の記号フォントから作ったフォントで組み，描く3本線も太字の矢印に合わせる．unicode-mathでは，太字の数式フォントを`\setmathfont{…}[version=bold]`で指定する．

斜線の形は`\folarrowsetup{span=, lean=, gap=, shift=, thickness=}`か，同じキーのパッケージオプションで変えられる．

### 簡易版：`lite`オプション

```latex
\usepackage[lite]{folarrow}
```

`lite`を付けると，ほかのファイル（Luaのモジュール，実測データ，矢印のフォント）を使わず，すべての矢印を描いて組む．
矢印のフォントをPDFに埋め込まずに組みたいときなどに使う．付けなければ（既定）これまでどおりである．

## 動作要件

- LaTeX 2022-06-01以降，pict2e，graphics．tikz-cdで使う場合はPGF／TikZ．
- pdfLaTeX，LuaLaTeX，XeLaTeX，upLaTeX＋dvipdfmxで確認した（TeX Live 2026）．dvipdfmxでは文書クラスに`dvipdfmx`オプションを付ける．
- 特別なフォントは要らない（矢印のフォントは同梱している）．
- TeX Live 2026のLuaLaTeXでは，xy-pic自体がエラーになる（folarrowとは無関係）．

## 説明書

- `doc/folarrow-ja.pdf`：完全版の説明書（検証表を含む）．
- `doc/folarrow-lite-ja.pdf`：簡易版（`lite`オプション）の説明書．例はどれも`\documentclass`から`\end{document}`までの完全な文書で，そのまま組める．

## インストール

`folarrow.tds.zip`をTEXMFツリーに展開するか，次のように置く．

| ファイル | 置き場所 |
|---|---|
| `tex/*` | `tex/latex/folarrow/` |
| `fonts/type1/*.pfb` | `fonts/type1/public/folarrow/` |
| `fonts/tfm/*.tfm` | `fonts/tfm/public/folarrow/` |
| `fonts/opentype/*.otf` | `fonts/opentype/public/folarrow/` |
| `fonts/map/folarrow.map` | `fonts/map/dvips/folarrow/` |
| `source/*` | `source/latex/folarrow/` |

pdfLaTeX，LuaLaTeX，dvipdfmx，xdvipdfmxでは，`folarrow.map`をパッケージが読み込む．
dvipsで使うときは，`updmap`で登録する（TeX Liveでは`updmap-user --enable Map=folarrow.map`）．

## ファイル

- `tex/`：`folarrow.sty`（パッケージ本体），`folarrow.lua`（LuaTeXのモジュール），`folarrow-fonts.def`（Type 1の数式フォントの実測データ），`folarrow-glyphs.def`，`folarrow-otf.def`（矢印のフォントの表）．
- `fonts/`：矢印のフォント（Type 1，TFM，OpenType）とマップファイル．
- `doc/`：説明書（PDFとソース）と例．
- `source/`：矢印のフォントを作るPythonのスクリプト（次の節を参照）．
- `LICENSE`：このパッケージのMITライセンス．
- `licenses/`：矢印のフォントのライセンスの本文と，フォントごとの元のフォント・元の著作権表示・ライセンスの一覧`FONTS.md`．
- `folarrow.tds.zip`：同じファイルをTDSの形に並べたもの．

## 矢印のフォントのソース

矢印のフォントは，元の数式フォントから2本のPythonのスクリプトで作る．

- `source/mkfolfonts.py`：Type 1のフォント，そのTFM，`folarrow.map`，`folarrow-glyphs.def`を作る．
- `source/mkfolotf.py`：OpenTypeのフォントと`folarrow-otf.def`を作る．

どちらも，TeX Liveに入っている元のフォントから矢印の字形（アウトライン）を取り出し，3本線を加える．
Python 3のfontToolsとskia-pathops，TeX Liveのkpsewhich，tftopl，vftovp，pltotf，t1asmを使う．
書き出す先は環境変数`FOLARROW_ROOT`で指すTDSの木で，そこには`tex/latex/folarrow/folarrow-fonts.def`が要る（なければ何も書かずに止まる）．
たとえば`folarrow.tds.zip`をあるディレクトリに展開して，次のように動かす．

```sh
FOLARROW_ROOT=/path/to/the/tree python3 source/mkfolfonts.py
FOLARROW_ROOT=/path/to/the/tree python3 source/mkfolotf.py
```

`mkfolotf.py`は`mkfolfonts.py`を読み込むので，2本は同じディレクトリに置く．
パッケージを使うだけなら，動かす必要はない．

## ライセンス

- `folarrow.sty`，`folarrow.lua`，`.def`ファイル，説明書，`source/`のスクリプト：MITライセンス（`LICENSE`）．
- 矢印のフォント（`fonts/`）は元のフォントから作ったもので，元のフォントのライセンス（SIL Open Font License 1.1，GUST Font License，フォントの例外付きのGNU GPL）を引き継ぐ．`licenses/FONTS.md`を参照．ファイル名とフォント名には，元のフォントの予約フォント名を含めていない．
