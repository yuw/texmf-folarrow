#!/bin/sh
# 完全版の説明書（folarrow-ja.tex）の例を組む．完全版のファイルが見える状態で組み，結果を余白なしのPDF（〈名前〉-out.pdf）にしてここに置く．
# 使い方：sh build.sh（TeX Liveのコマンドはpdfcropも含めてPATHに通しておく）
set -e
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
# 途中で失敗しても作業用ディレクトリを消す
trap 'rm -rf "$work"' EXIT
# このリポジトリの中なら，リポジトリをTEXMFHOMEにする（そうでなければインストールしたものを使う）
repo="$(cd "$here/../../../.." && pwd)"
if [ -f "$repo/tex/latex/folarrow/folarrow.sty" ]; then export TEXMFHOME="$repo"; fi
cd "$work"
# 載せる例のソースは変えず，組むときだけページ番号を消す（余白を切り落とすため）
for f in "$here"/ex*.tex; do
  sed '/^\\documentclass/a\
\\pagestyle{empty}' "$f" > "$(basename "$f")"
done
for f in ex*.tex; do
  b=${f%.tex}
  pdflatex -interaction=nonstopmode -halt-on-error "$f" >/dev/null || { echo "$b: pdflatex failed"; exit 1; }
  pdfcrop --margins 2 "$b.pdf" "$here/$b-out.pdf" >/dev/null
  echo "$b: pdflatex ok"
done
