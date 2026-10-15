#!/bin/sh
# すべてのテストをまとめて流す．最後に，組んだ文書ごとのエラーと字形の欠け（Missing character）
# の件数をまとめ，1件でもあれば終了コード1で終わる．
# 使い方：test/runall.sh
#   TeXのコマンドはPATHにあるものを使う（TEXBINにbinディレクトリを指定してもよい）．
#   OpenTypeの49書体を切り替えて組むt6-otf.texは時間がかかる（LuaLaTeXで数分）．
#   SKIP_T6=1を付けると省く．
if [ -n "$TEXBIN" ]; then export PATH="$TEXBIN:$PATH"; fi
cd "$(dirname "$0")"
here=$(pwd)
root=$(cd .. && pwd)
export TEXMFHOME="$root"
logs=""

# 1. 既存のテスト：pdfLaTeX，LuaLaTeX，upLaTeX＋dvipdfmx（run.sh）とXeLaTeX
sh ./run.sh t1-all.tex t3-labels.tex t4-caps.tex t5-glyphs.tex
for t in t1-all t3-labels t4-caps t5-glyphs; do
  xelatex -interaction=nonstopmode -jobname="$t-xe" "$t.tex" >/dev/null 2>&1
  logs="$logs $t-pdf.log $t-lua.log $t-up.log $t-xe.log"
done
# （t1-allは，LuaLaTeXのときxy-picを読まない．TeX Live 2025と2026ではxy-pic自体がLuaLaTeXでエラーになるため）

# 2. OpenTypeの数式フォント（LuaLaTeX，XeLaTeX）
if [ -z "$SKIP_T6" ]; then
  for e in lualatex xelatex; do
    "$e" -interaction=nonstopmode -jobname="t6-otf-$e" t6-otf.tex >/dev/null 2>&1
    logs="$logs t6-otf-$e.log"
  done
fi

# 3. 組見本と比較文書（upLaTeX＋dvipdfmx）
for b in sample-cm sample-newtx sample-newpx sample-tx sample-px \
         compare-cm compare-newtx compare-newpx compare-tx compare-px; do
  uplatex -interaction=nonstopmode "$b.tex" >/dev/null 2>&1 && dvipdfmx -q "$b.dvi" 2>/dev/null
  logs="$logs $b.log"
done

# 4. 説明書の例と説明書
doc="$root/doc/latex/folarrow"
sh "$doc/lite-examples/build.sh" >/dev/null || echo "lite-examples/build.sh failed"
sh "$doc/full-examples/build.sh" >/dev/null || echo "full-examples/build.sh failed"
for d in folarrow-ja folarrow-lite-ja folarrow-en folarrow-lite-en; do
  (cd "$doc" && uplatex -interaction=nonstopmode "$d.tex" >/dev/null 2>&1 \
     && uplatex -interaction=nonstopmode "$d.tex" >/dev/null 2>&1 && dvipdfmx -q "$d.dvi" 2>/dev/null)
  logs="$logs $doc/$d.log"
done

# 5. まとめ
fail=0
printf '%-28s %6s %8s\n' 文書 エラー 字形の欠け
for l in $logs; do
  if [ ! -f "$l" ]; then printf '%-28s %s\n' "$(basename "$l" .log)" 'ログなし'; fail=1; continue; fi
  e=$(grep -c '^!' "$l"); m=$(grep -c 'Missing character' "$l")
  printf '%-28s %6s %8s\n' "$(basename "$l" .log)" "$e" "$m"
  [ "$e" = 0 ] && [ "$m" = 0 ] || fail=1
done
if [ "$fail" = 0 ]; then echo 'すべて問題なし'; else echo '問題あり'; fi
exit $fail
