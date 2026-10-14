#!/bin/sh
# テスト用：このリポジトリをTEXMFHOMEとして使い，3つのエンジンで組む
# 使い方：test/run.sh t1-all.tex
# upLaTeXでは，文書クラスにdvipdfmxオプションを加えた写し（*-up.tex）を組む．
# TeXのコマンドはPATHにあるものを使う．別のTeX Liveを使うときは，そのbinディレクトリを
# TEXBINに指定する（例：TEXBIN=/usr/local/texlive/2026/bin/universal-darwin test/run.sh t1-all.tex）．
if [ -n "$TEXBIN" ]; then export PATH="$TEXBIN:$PATH"; fi
cd "$(dirname "$0")"
export TEXMFHOME="$(cd .. && pwd)"
for f in "$@"; do
  b=$(basename "$f" .tex)
  pdflatex -interaction=nonstopmode -jobname="$b-pdf" "$f" >/dev/null || echo "pdflatex: $b failed"
  lualatex -interaction=nonstopmode -jobname="$b-lua" "$f" >/dev/null || echo "lualatex: $b failed"
  sed -e 's/^\\documentclass\[/\\documentclass[dvipdfmx,/' -e t -e 's/^\\documentclass{/\\documentclass[dvipdfmx]{/' "$f" > "$b-up.tex"
  uplatex -interaction=nonstopmode "$b-up.tex" >/dev/null && dvipdfmx -q "$b-up.dvi" || echo "uplatex: $b failed"
done
