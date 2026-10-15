# folarrow

A LaTeX package that provides arrows with three slanted strokes on the shaft, which
denote the projection of a foliated bundle in foliation theory, for amscd, xy-pic and
tikz-cd diagrams and for inline math.

Version 20261010.0, 2026-10-10.
Author: Yuwsuke Kieda

A Japanese README is in `README-ja.md`.

This is the README of the development repository. The CTAN package is built from this
repository by `tools/ctan/mkctan.sh`; it has its own README (`ctan/README.md`,
`ctan/README-ja.md`). Of the scripts in `tools/`, it contains only the two that generate
the arrow fonts (`tools/fontbuild/mkfolfonts.py` and `mkfolotf.py`, in `source/`), as the
sources of the fonts; it does not contain the other scripts, the build scripts of the
examples, or the tests.

## Description

When a fiber bundle `V -> E -> M` is drawn as a diagram, the projection `E -> M` is
drawn as a vertical (or horizontal) arrow. Three slanted strokes are sometimes drawn
across the shaft of that arrow to indicate, in particular, that the bundle is a foliated
bundle. This package makes such arrows available:

| Environment | Syntax |
|---|---|
| amscd | `@FVV{\pi}V`, `@FAAA`, `@F>f>>`, `@F<<g<` (add `F` right after `@`) |
| xy-pic | `\ar[d]\|@{fol}^{\folpad{\pi}}` (`fol` is a zero-size object placed on the arrow; `\folpad` keeps the label clear of the strokes) |
| tikz-cd | `\arrow[d, foliated, "\pi"]` |
| inline math | `\folrightarrow`, `\folleftarrow`, `\foldownarrow`, `\foluparrow`, `\xfolrightarrow[below]{above}`, `\xfolleftarrow[below]{above}` |

The arrows of the diagram packages are used as they are, and the strokes are drawn over
them (with pict2e, or PGF for tikz-cd). The length, spacing and thickness of the strokes
follow the arrowhead and the shaft of the current math font, in every math style.

The four inline arrows (`\folrightarrow` etc.) are typeset with single glyphs that
include the strokes:

- Type 1 fonts for Computer Modern, Latin Modern, newtx, txfonts, newpx and pxfonts;
- OpenType fonts for 49 OpenType math fonts used with unicode-math (LuaLaTeX, XeLaTeX).

These glyphs copy from the PDF as U+2192, U+2190, U+2193 and U+2191.
For other math fonts the strokes are drawn.

The arrows follow bold math (`\boldmath`, `\bm`): the inline arrows use fonts made from
the bold symbol fonts, and the drawn strokes follow the bold arrows. With unicode-math,
specify the bold math font with `\setmathfont{...}[version=bold]`.

The shape of the strokes can be changed with `\folarrowsetup{span=, lean=, gap=, shift=, thickness=}`
or the same package options.

### Light version: the `lite` option

```latex
\usepackage[lite]{folarrow}
```

With `lite`, the package uses no other files (no Lua module, measured data or arrow
fonts) and draws all arrows. Use it, for example, when you do not want the arrow fonts
embedded in the PDF. The default behaviour without `lite` does not change.

## Requirements

- LaTeX 2022-06-01 or later, pict2e, graphics; PGF/TikZ for tikz-cd.
- Tested with pdfLaTeX, LuaLaTeX, XeLaTeX and upLaTeX+dvipdfmx (TeX Live 2025 and 2026).
  With dvipdfmx, give the `dvipdfmx` option to the document class.
- No special fonts are required; the arrow fonts are included.
- In TeX Live 2025 and 2026, xy-pic itself fails with LuaLaTeX (unrelated to this package).

## Documentation

The manuals are in English and Japanese, with the same contents.

- `doc/latex/folarrow/folarrow-en.pdf`, `folarrow-ja.pdf`: the full manual, with verification tables.
- `doc/latex/folarrow/folarrow-lite-en.pdf`, `folarrow-lite-ja.pdf`: the manual of the `lite` option.
  Every example is a complete document from `\documentclass` to `\end{document}` that compiles as it is.

## Installation

This repository is in the TDS layout; it can be used as `TEXMFHOME` as it is.
From the CTAN package, unpack `folarrow.tds.zip` into a TEXMF tree, or put the files as follows:

| Files | Location |
|---|---|
| `tex/*` | `tex/latex/folarrow/` |
| `fonts/type1/*.pfb` | `fonts/type1/public/folarrow/` |
| `fonts/tfm/*.tfm` | `fonts/tfm/public/folarrow/` |
| `fonts/opentype/*.otf` | `fonts/opentype/public/folarrow/` |
| `fonts/map/folarrow.map` | `fonts/map/dvips/folarrow/` |

pdfLaTeX, LuaLaTeX, dvipdfmx and xdvipdfmx load `folarrow.map` automatically.
For dvips, enable it with `updmap` (in TeX Live: `updmap-user --enable Map=folarrow.map`).

## Files (in this repository, in the TDS layout)

- `tex/latex/folarrow/`: `folarrow.sty` (the package), `folarrow.lua` (LuaTeX module),
  `folarrow-fonts.def` (measured data of Type 1 math fonts),
  `folarrow-glyphs.def`, `folarrow-otf.def` (tables of the arrow fonts).
- `fonts/`: the arrow fonts (Type 1, TFM, OpenType) and the map file.
- `doc/latex/folarrow/`: the manuals (PDF and source) and the examples.
- `LICENSE`: the MIT License of the package.
- `licenses/`: license texts of the arrow fonts, and `FONTS.md`, the list of the arrow
  fonts with their original fonts, original copyright notices and licenses.
- `ctan/`: the README files of the CTAN package.
- `tools/`: scripts (only `tools/fontbuild/mkfolfonts.py` and `mkfolotf.py` are in the CTAN
  package, in `source/`).
- `test/`: test documents, `run.sh`, and `runall.sh`, which runs all tests and reports
  the numbers of errors and missing characters (not in the CTAN package).

## Generated files

Many files of the package are generated by scripts. Do not edit them by hand;
change the scripts and run them again.

| Generated files | Script |
|---|---|
| Type 1 arrow fonts, TFM, `folarrow.map`, `folarrow-glyphs.def` | `tools/fontbuild/mkfolfonts.py` |
| OpenType arrow fonts, `folarrow-otf.def` | `tools/fontbuild/mkfolotf.py` |
| `folarrow-fonts.def` (measured data) | `tools/fontdata/measure.py`, then `tools/fontdata/mkdata.py` |
| `doc/latex/folarrow/folarrow-verify.tex`, `folarrow-verify-en.tex` (verification tables) | `tools/fontdata/mkreport.py` |
| `licenses/FONTS.md` | `tools/ctan/mkfontlicenses.py` |
| results of the examples in the manuals (`*-out.pdf`) | `doc/latex/folarrow/lite-examples/build.sh`, `doc/latex/folarrow/full-examples/build.sh` |
| the CTAN archive `build/ctan/folarrow.zip` | `tools/ctan/mkctan.sh` |

The font scripts use fontTools and skia-pathops (Python) and kpsewhich, tftopl, vftovp,
pltotf and t1asm of TeX Live. The arrow fonts are made from the math fonts installed in
TeX Live.

## License

- `folarrow.sty`, `folarrow.lua`, the `.def` files, the documentation, the scripts and
  the tests: MIT License (`LICENSE`).
- The arrow fonts in `fonts/` are derived from other fonts and keep their licenses:
  SIL Open Font License 1.1, GUST Font License, or GNU GPL with font exception.
  See `licenses/FONTS.md`. The names of the derived fonts do not contain the Reserved
  Font Names of the original fonts.
