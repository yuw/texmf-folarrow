#!/bin/sh
# CTANに出すアーカイブを作る．
#   build/ctan/folarrow.zip（展開するとfolarrow/．その中にfolarrow.tds.zipも入れる）
# 生成スクリプトのうち，矢印のフォントを作る2本（tools/fontbuild/mkfolfonts.py，mkfolotf.py）だけを
# フォントのソースとしてsource/に入れる．ほかのスクリプト（tools/），説明書の例を組むスクリプト
# （*/build.sh），テスト（test/）は入れない．READMEはこのリポジトリのREADME.md，README-ja.mdではなく，
# CTAN用のctan/README.md，ctan/README-ja.mdを入れる（source/の2本のスクリプトについて書いてある）．
# 使い方：sh tools/ctan/mkctan.sh
#   目印（TODO-）が残っている，版番号や日付が食い違う，などの問題があれば止まる．
#   試しに作るだけなら，ALLOW_TODO=1を付けると目印が残っていても作る（CTANには出さないこと）．
# 中身はgitに登録したファイルだけから作る．配る範囲にgitに登録していないファイルがあれば止まる
# （置いたままのメモや下書きを配らないため．配るならgit addしてから作る）．
set -e
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
out="$root/build/ctan"
stage="$out/stage"
rm -rf "$stage" "$out/folarrow.zip"
mkdir -p "$stage/folarrow" "$stage/tds"
pkg="$stage/folarrow"
tds="$stage/tds"

fail() { echo "mkctan: $*" >&2; exit 1; }

# 1. 版番号と日付（folarrow.styの\ProvidesPackageが基準）
provides=$(sed -n 's/^\\ProvidesPackage{folarrow}\[\([0-9/]*\) v\([0-9.]*\) .*/\1 \2/p' tex/latex/folarrow/folarrow.sty)
date=${provides% *}; ver=${provides#* }
[ -n "$date" ] && [ -n "$ver" ] || fail "cannot read \\ProvidesPackage"
isodate=$(echo "$date" | tr / -)
jdate=$(echo "$date" | awk -F/ '{printf "%d年%d月%d日", $1, $2, $3}')
for r in README.md ctan/README.md; do
  grep -q "^Version $ver, $isodate\.$" "$r" || fail "$r: version/date is not 'Version $ver, $isodate.'"
done
grep -q "^版$ver，$jdate．$" ctan/README-ja.md || fail "ctan/README-ja.md: version/date is not '版$ver，$jdate．'"
# CTAN用のREADMEは，配布物に入れるsource/の2本のスクリプトについて書き，ほかのスクリプトには触れない
for r in ctan/README.md ctan/README-ja.md; do
  for s in source/mkfolfonts.py source/mkfolotf.py; do
    grep -q "$s" "$r" || fail "$r does not mention $s"
  done
done
scr=$(grep -n -E 'tools/|\.sh|measure\.py|mkdata\.py|mkreport\.py|mkfontlicenses\.py' ctan/README.md ctan/README-ja.md || true)
[ -z "$scr" ] || fail "CTAN README mentions scripts not in the package: $scr"
for d in doc/latex/folarrow/folarrow-ja.tex doc/latex/folarrow/folarrow-lite-ja.tex; do
  grep -q "\\\\date{$jdate　v$ver}" "$d" || fail "$d: \\date is not '$jdate　v$ver'"
done
for d in doc/latex/folarrow/folarrow-en.tex doc/latex/folarrow/folarrow-lite-en.tex; do
  grep -q "\\\\date{$isodate\\\\quad v$ver}" "$d" || fail "$d: \\date is not '$isodate\\quad v$ver'"
done
echo "version $ver, $isodate"

# 2. 配る対象のファイル（gitに登録したもの）
#    生成スクリプト（フォントを作る2本を除く），例を組むスクリプト，テスト，このリポジトリのREADMEは除く
pick() {
  while read -r f; do [ -f "$f" ] && echo "$f"; done \
  | grep -v -e '^\.' -e '/\.' -e '^build/' -e '^folto\.pdf$' -e '^rfolto\.pdf$' \
           -e '^tools/[^f]' -e '^tools/fontdata/' -e '^test/' -e '/build\.sh$' -e '^README\.md$' -e '^README-ja\.md$' \
           -e '^ctan/upload-form\.md$' || true
}
untracked=$(git ls-files --others --exclude-standard | pick)
[ -z "$untracked" ] || fail "files not added to git: $(echo $untracked)"
files=$(git ls-files --cached | sort -u | pick)
# ファイル名は英数字と/._+-だけ（以下でファイル名を空白で区切って扱うため，並べる前に確かめる）
bad=$(echo "$files" | grep -v -E '^[A-Za-z0-9/._+-]+$' || true)
[ -z "$bad" ] || fail "bad file names: $bad"

# 3. 目印
if [ -z "$ALLOW_TODO" ]; then
  todo=$(echo "$files" | xargs grep -l 'TODO-' 2>/dev/null || true)
  [ -z "$todo" ] || fail "placeholders (TODO-) remain in: $(echo $todo)"
fi
# メールアドレス：配布物には書かない．元のフォントの著作権表示（fonts/，licenses/）にある
# 元の作者のものだけを認める（テキストのファイルだけを見る．PDFの中の圧縮した文字は見ない）
mail=$(echo "$files" | grep -v -e '^fonts/' -e '^licenses/' \
  | xargs grep -I -n -E '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' 2>/dev/null || true)
[ -z "$mail" ] || fail "e-mail addresses in: $mail"

# 4. 並べる（CTANの展開した形と，TDSの形）
put() { # put 元 先
  mkdir -p "$(dirname "$2")"; cp "$1" "$2"
}
for f in $files; do
  case "$f" in
    tex/latex/folarrow/*)            put "$f" "$pkg/tex/${f#tex/latex/folarrow/}";        put "$f" "$tds/$f" ;;
    fonts/type1/public/folarrow/*)   put "$f" "$pkg/fonts/type1/${f##*/}";                put "$f" "$tds/$f" ;;
    fonts/tfm/public/folarrow/*)     put "$f" "$pkg/fonts/tfm/${f##*/}";                  put "$f" "$tds/$f" ;;
    fonts/opentype/public/folarrow/*) put "$f" "$pkg/fonts/opentype/${f##*/}";            put "$f" "$tds/$f" ;;
    fonts/map/dvips/folarrow/*)      put "$f" "$pkg/fonts/map/${f##*/}";                  put "$f" "$tds/$f" ;;
    doc/latex/folarrow/*)            put "$f" "$pkg/doc/${f#doc/latex/folarrow/}";        put "$f" "$tds/$f" ;;
    licenses/*)                      put "$f" "$pkg/$f";                                  put "$f" "$tds/doc/latex/folarrow/$f" ;;
    ctan/README.md|ctan/README-ja.md) put "$f" "$pkg/${f#ctan/}";                         put "$f" "$tds/doc/latex/folarrow/${f#ctan/}" ;;
    tools/fontbuild/mkfolfonts.py|tools/fontbuild/mkfolotf.py)
                                     put "$f" "$pkg/source/${f##*/}";                     put "$f" "$tds/source/latex/folarrow/${f##*/}" ;;
    LICENSE)                         put "$f" "$pkg/$f";                                  put "$f" "$tds/doc/latex/folarrow/$f" ;;
    *) fail "no place for $f" ;;
  esac
done

# 5. 検査：ファイル名，重複，改行コード，説明書のPDF
cd "$stage"
bad=$(find folarrow tds | grep -v -E '^[A-Za-z0-9/._+-]+$' || true)
[ -z "$bad" ] || fail "bad file names: $bad"
dup=$(find folarrow -type f | awk -F/ '{print tolower($NF)}' | sort | uniq -d \
  | grep -v -i -e '^readme' || true)
[ -z "$dup" ] || fail "duplicate file names: $dup"
crlf=$(find folarrow -type f \( -name '*.tex' -o -name '*.sty' -o -name '*.lua' -o -name '*.def' -o -name '*.md' \
  -o -name '*.txt' -o -name '*.py' -o -name '*.sh' -o -name '*.json' -o -name '*.map' \) -exec grep -l "$(printf '\r')" {} + || true)
[ -z "$crlf" ] || fail "CRLF line endings: $crlf"
scripts=$(find folarrow tds -type f \( -name '*.py' -o -name '*.sh' \) \
  | grep -v -E '^(folarrow/source|tds/source/latex/folarrow)/mkfol(fonts|otf)\.py$' || true)
[ -z "$scripts" ] || fail "scripts in the package: $scripts"
for p in folarrow-ja.pdf folarrow-lite-ja.pdf folarrow-en.pdf folarrow-lite-en.pdf; do
  [ -f "folarrow/doc/$p" ] || fail "missing doc/$p"
done

# 6. パーミッション：ディレクトリとスクリプトは755，ほかは644
find folarrow tds -type d -exec chmod 755 {} +
find folarrow tds -type f -exec chmod 644 {} +
find folarrow tds -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod 755 {} +

# 7. まとめる
(cd tds && zip -q -r -X ../folarrow/folarrow.tds.zip tex fonts doc source)
chmod 644 folarrow/folarrow.tds.zip
zip -q -r -X "$out/folarrow.zip" folarrow
cd "$root"
echo "$out/folarrow.zip: $(unzip -l "$out/folarrow.zip" | tail -1 | awk '{print $2}') files"
