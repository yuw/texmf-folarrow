# folarrow

A LaTeX package providing arrows with three slanted shaft strokes to denote foliated-bundle
projections, for amscd, xy-pic, tikz-cd and inline math.

Version 20261010.0, 2026-10-10.
Author: Yuwsuke Kieda

A Japanese README is in `README-ja.md`.

## Description

In a fiber-bundle diagram `V -> E -> M`, the projection `E -> M` is usually a vertical or
horizontal arrow. Three slanted strokes across its shaft can indicate a foliated bundle.
This package provides such arrows:

| Environment | Syntax |
|---|---|
| amscd | `@FVV{\pi}V`, `@FAAA`, `@F>f>>`, `@F<<g<` (add `F` right after `@`) |
| xy-pic | `\ar[d]\|@{fol}^{\folpad{\pi}}` (`fol` is a zero-size object placed on the arrow; `\folpad` keeps the label clear of the strokes) |
| tikz-cd | `\arrow[d, foliated, "\pi"]` |
| inline math | `\folrightarrow`, `\folleftarrow`, `\foldownarrow`, `\foluparrow`, `\xfolrightarrow[below]{above}`, `\xfolleftarrow[below]{above}` |

Diagram-package arrows are unchanged; strokes are overlaid using pict2e (or PGF for
tikz-cd). Their length, spacing and thickness follow the current math font's arrowhead
and shaft in every math style.

The four inline arrows (`\folrightarrow` etc.) use single glyphs with the strokes:

- Type 1 fonts for Computer Modern, Latin Modern, newtx, txfonts, newpx and pxfonts;
- OpenType fonts for 49 OpenType math fonts used with unicode-math (LuaLaTeX, XeLaTeX).

These glyphs copy from PDFs as U+2192, U+2190, U+2193 and U+2191. Other math fonts use
drawn strokes.

Arrows follow bold math (`\boldmath`, `\bm`): inline arrows use fonts made from the bold
symbol fonts, and drawn strokes follow bold arrows. With unicode-math, set the bold math
font using `\setmathfont{...}[version=bold]`.

The shape of the strokes can be changed with `\folarrowsetup{span=, lean=, gap=, shift=, thickness=}`
or the same package options.

### Light version: the `lite` option

```latex
\usepackage[lite]{folarrow}
```

With `lite`, all arrows are drawn and no Lua module, measured data or arrow fonts are
needed. Use it to avoid embedding arrow fonts in PDFs. Default behaviour is unchanged.

## Requirements

- LaTeX 2022-06-01 or later, pict2e, graphics; PGF/TikZ for tikz-cd.
- Tested with pdfLaTeX, LuaLaTeX, XeLaTeX and upLaTeX+dvipdfmx (TeX Live 2026).
  For dvipdfmx, pass the `dvipdfmx` option to the document class.
- No special fonts are required; the arrow fonts are included.
- In TeX Live 2026, xy-pic itself fails with LuaLaTeX (unrelated to this package).

## Documentation

All documentation is in Japanese.

- `doc/folarrow-ja.pdf`: the full manual, with verification tables.
- `doc/folarrow-lite-ja.pdf`: `lite` manual; each example is a compilable, complete
  document.

## Installation

Unpack `folarrow.tds.zip` into a TEXMF tree, or install the files as follows:

| Files | Location |
|---|---|
| `tex/*` | `tex/latex/folarrow/` |
| `fonts/type1/*.pfb` | `fonts/type1/public/folarrow/` |
| `fonts/tfm/*.tfm` | `fonts/tfm/public/folarrow/` |
| `fonts/opentype/*.otf` | `fonts/opentype/public/folarrow/` |
| `fonts/map/folarrow.map` | `fonts/map/dvips/folarrow/` |
| `source/*` | `source/latex/folarrow/` |

pdfLaTeX, LuaLaTeX, dvipdfmx and xdvipdfmx load `folarrow.map` automatically.
For dvips, enable it with `updmap` (in TeX Live: `updmap-user --enable Map=folarrow.map`).

## Files

- `tex/`: `folarrow.sty` (the package), `folarrow.lua` (LuaTeX module),
  `folarrow-fonts.def` (measured data of Type 1 math fonts),
  `folarrow-glyphs.def`, `folarrow-otf.def` (tables of the arrow fonts).
- `fonts/`: the arrow fonts (Type 1, TFM, OpenType) and the map file.
- `doc/`: the manuals (PDF and source) and the examples.
- `source/`: Python scripts for generating arrow fonts (see below).
- `LICENSE`: the MIT License of the package.
- `licenses/`: license texts of the arrow fonts, and `FONTS.md`, the list of the arrow
  fonts with their original fonts, original copyright notices and licenses.
- `folarrow.tds.zip`: the same files in the TDS layout.

## Sources of the arrow fonts

The arrow fonts are generated from the original math fonts by two Python scripts:

- `source/mkfolfonts.py`: the Type 1 fonts, their TFM files, `folarrow.map` and
  `folarrow-glyphs.def`;
- `source/mkfolotf.py`: the OpenType fonts and `folarrow-otf.def`.

The scripts add three strokes to arrow outlines from the original TeX Live fonts. They
require Python 3 with fontTools and skia-pathops, plus TeX Live's kpsewhich, tftopl,
vftovp, pltotf and t1asm. Output goes to the TDS tree specified by `FOLARROW_ROOT`,
which must contain `tex/latex/folarrow/folarrow-fonts.def`; otherwise, the scripts stop
without writing. For example, unpack `folarrow.tds.zip` into a directory and run

```sh
FOLARROW_ROOT=/path/to/the/tree python3 source/mkfolfonts.py
FOLARROW_ROOT=/path/to/the/tree python3 source/mkfolotf.py
```

`mkfolotf.py` imports `mkfolfonts.py`, so keep both scripts together. Package users need
not run them.

## License

- `folarrow.sty`, `folarrow.lua`, the `.def` files, the documentation and the scripts
  in `source/`: MIT License (`LICENSE`).
- Arrow fonts in `fonts/` retain their source licenses: SIL Open Font License 1.1, GUST
  Font License, or GNU GPL with font exception. See `licenses/FONTS.md`. Derived font
  names do not use the originals' Reserved Font Names.
