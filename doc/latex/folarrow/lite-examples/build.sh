#!/bin/sh
# 簡易版の説明書（folarrow-lite-ja.tex）の例を組む．
# 簡易版がほかのファイルを使わないことを確かめるため，folarrow.styだけを置いた作業用ディレクトリで
# 組み（TEXMFHOMEはからにして，ほかのファイルが見えないようにする），結果を余白なしのPDF
# （〈名前〉-out.pdf）にしてここに置く．
# 使い方：sh build.sh（TeX Liveのコマンドはpdfcropも含めてPATHに通しておく）
set -e
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
# 途中で失敗しても作業用ディレクトリを消す
trap 'rm -rf "$work"' EXIT
# folarrow.styは，このリポジトリ（tex/latex/folarrow/），CTANの配布物を展開したもの（tex/），
# インストールしたもの（kpsewhich）の順に探す
for sty in "$here/../../../../tex/latex/folarrow/folarrow.sty" "$here/../../tex/folarrow.sty" \
           "$(kpsewhich folarrow.sty)"; do
  [ -f "$sty" ] && break
done
[ -f "$sty" ] || { echo "folarrow.sty not found"; exit 1; }
cp "$sty" "$work/"
cd "$work"
# 載せる例のソースは変えず，組むときだけページ番号を消す（余白を切り落とすため）
for f in "$here"/ex*.tex; do
  sed '/^\\documentclass/a\
\\pagestyle{empty}' "$f" > "$(basename "$f")"
done
export TEXMFHOME="$work/none"
engine() {
  case "$1" in
    ex08-*) echo uplatex ;;
    ex09-*) echo lualatex ;;
    ex10-*) echo xelatex ;;
    *) echo pdflatex ;;
  esac
}
for f in ex*.tex; do
  b=${f%.tex}
  e=$(engine "$b")
  "$e" -interaction=nonstopmode -halt-on-error "$f" >/dev/null || { echo "$b: $e failed"; exit 1; }
  if [ "$e" = uplatex ]; then dvipdfmx -q "$b.dvi"; fi
  pdfcrop --margins 2 "$b.pdf" "$here/$b-out.pdf" >/dev/null
  echo "$b: $e ok"
done
